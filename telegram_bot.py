#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot for Test Management
Admin Channel: @IshtixonKimyo
Mandatory Subscription Channel: @untoldies
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.request import HTTPXRequest
from telegram.error import TelegramError
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token - use environment variable for security
BOT_TOKEN = os.getenv('BOT_TOKEN', "8534371752:AAFGZkSU_h20PU2E4x93HThRvBXVl1gN-Nw")

# Channel IDs
MANDATORY_CHANNEL = "@untoldies"  # Mandatory subscription channel
ADMIN_CHANNEL = "@IshtixonKimyo"  # Admin notifications channel

# Admin user IDs - can be set via environment variable
ADMIN_IDS_ENV = os.getenv('ADMIN_IDS', '8004724563')
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_ENV.split(',')]

# Conversation states
WAITING_NAME, WAITING_SURNAME, WAITING_TEST_ANSWERS, WAITING_USER_ANSWERS = range(4)
ADMIN_WAITING_TEST_NUMBER, ADMIN_WAITING_ANSWERS, ADMIN_WAITING_DEADLINE, ADMIN_WAITING_CHECK_TIME = range(4, 8)

# Data file paths
DATA_DIR = "bot_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TESTS_FILE = os.path.join(DATA_DIR, "tests.json")
REGISTRATIONS_FILE = os.path.join(DATA_DIR, "registrations.json")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


# Data management functions
def load_data(filename):
    """Load data from JSON file"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_data(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Check channel subscription
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is subscribed to the mandatory channel"""
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=MANDATORY_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking subscription: {e}")
        # Return False to require subscription (user must subscribe to continue)
        return False


# Notify admin about new user
async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, source_channel=None):
    """Send notification to admin channel about new user"""
    user = update.effective_user
    
    message = f"""
🆕 Yangi foydalanuvchi!

👤 Foydalanuvchi: {user.full_name}
🆔 User ID: {user.id}
📝 Username: @{user.username if user.username else 'Mavjud emas'}
"""
    
    if source_channel:
        message += f"📢 Kanal: {source_channel}\n"
    
    message += f"🕐 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHANNEL, text=message)
    except TelegramError as e:
        logger.error(f"Admin notification error: {e}")


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command"""
    user_id = update.effective_user.id
    
    # Check subscription first
    is_subscribed = await check_subscription(update, context)
    
    if not is_subscribed:
        keyboard = [[InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/untoldies")],
                   [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ Botdan foydalanish uchun avval kanalga obuna bo'lishingiz kerak!\n\n"
            "Iltimos, quyidagi kanalga obuna bo'ling va 'Obunani tekshirish' tugmasini bosing.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Notify admin about new user
    await notify_admin(update, context)
    
    # Check if user already registered
    users = load_data(USERS_FILE)
    
    if str(user_id) in users:
        # User already registered, show main menu
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    # New user - ask for name
    await update.message.reply_text(
        "✅ Obuna tasdiqlandi!\n\n"
        "Iltimos, ismingizni kiriting:"
    )
    return WAITING_NAME


# Check subscription callback
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription check button"""
    query = update.callback_query
    await query.answer()
    
    is_subscribed = await check_subscription(update, context)
    
    if not is_subscribed:
        # Only edit if message would be different
        try:
            await query.edit_message_text(
                "❌ Siz hali kanalga obuna bo'lmadingiz!\n\n"
                "Iltimos, kanalga obuna bo'ling va qayta urinib ko'ring.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/untoldies")],
                    [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")]
                ])
            )
        except TelegramError:
            # Message is the same, just ignore
            pass
        return ConversationHandler.END
    
    # Subscription confirmed
    await notify_admin(update, context)
    
    # Check if user already registered
    user_id = update.effective_user.id
    users = load_data(USERS_FILE)
    
    if str(user_id) in users:
        # User already registered
        await query.edit_message_text("✅ Siz allaqachon ro'yxatdan o'tgansiz!")
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    await query.edit_message_text(
        "✅ Obuna tasdiqlandi!\n\n"
        "Iltimos, ismingizni kiriting:"
    )
    return WAITING_NAME


# Name input handler
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's name"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Familiyangizni kiriting:")
    return WAITING_SURNAME


# Surname input handler
async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's surname and complete registration"""
    surname = update.message.text
    user_id = update.effective_user.id
    
    # Save user data
    users = load_data(USERS_FILE)
    users[str(user_id)] = {
        'name': context.user_data['name'],
        'surname': surname,
        'username': update.effective_user.username,
        'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    save_data(USERS_FILE, users)
    
    await update.message.reply_text(
        f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        f"Ism: {context.user_data['name']}\n"
        f"Familiya: {surname}"
    )
    
    await show_main_menu(update, context)
    return ConversationHandler.END


# Show main menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu with available tests"""
    tests = load_data(TESTS_FILE)
    
    if not tests:
        keyboard = [[KeyboardButton("🔄 Yangilash")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        message = update.message if update.message else update.callback_query.message
        await message.reply_text(
            "📋 Hozirda mavjud testlar yo'q.",
            reply_markup=reply_markup
        )
        return
    
    # Show available tests
    keyboard = []
    now = datetime.now()
    available_count = 0
    
    for test_id, test_data in tests.items():
        deadline = datetime.strptime(test_data['deadline'], '%Y-%m-%d %H:%M:%S')
        if now < deadline:
            # Count questions in the test
            answers = test_data['answers'].replace(' ', '').lower()
            question_count = len([c for c in answers if c.isalpha()])
            
            keyboard.append([KeyboardButton(f"📝 Test #{test_id} ({question_count} ta savol)")])
            available_count += 1
    
    if available_count == 0:
        keyboard = [[KeyboardButton("🔄 Yangilash")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        message = update.message if update.message else update.callback_query.message
        await message.reply_text(
            "📋 Hozirda mavjud testlar yo'q (barcha testlar deadline o'tgan).",
            reply_markup=reply_markup
        )
        return
    
    keyboard.append([KeyboardButton("🔄 Yangilash")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message = update.message if update.message else update.callback_query.message
    await message.reply_text(
        f"📋 Mavjud testlar: {available_count} ta\n\n"
        "Test tanlash uchun tugmani bosing:",
        reply_markup=reply_markup
    )


# Handle test selection
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check if user is subscribed
    is_subscribed = await check_subscription(update, context)
    if not is_subscribed:
        await start(update, context)
        return
    
    if text == "🔄 Yangilash":
        await show_main_menu(update, context)
        return
    
    if text.startswith("📝 Test #"):
        # Extract test_id from "📝 Test #123 (10 ta savol)" format
        test_id = text.split("(")[0].replace("📝 Test #", "").strip()
        tests = load_data(TESTS_FILE)
        
        if test_id in tests:
            test_data = tests[test_id]
            context.user_data['selected_test'] = test_id
            
            # Count questions
            correct_answers = test_data['answers'].replace(' ', '').lower()
            question_count = len([c for c in correct_answers if c.isalpha()])
            
            await update.message.reply_text(
                f"✅ Siz Test #{test_id} uchun ro'yxatdan o'tdingiz!\n\n"
                f"📝 Savollar soni: {question_count} ta\n"
                f"📅 Deadline: {test_data['deadline']}\n"
                f"🕐 Tekshirish vaqti: {test_data['check_time']}\n\n"
                f"📝 Javoblaringizni yuboring (Format: 1a2b3c yoki abc):"
            )
            
            # Save registration
            registrations = load_data(REGISTRATIONS_FILE)
            if test_id not in registrations:
                registrations[test_id] = {}
            
            registrations[test_id][str(user_id)] = {
                'name': load_data(USERS_FILE)[str(user_id)]['name'],
                'surname': load_data(USERS_FILE)[str(user_id)]['surname'],
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'answers': None,
                'score': None
            }
            save_data(REGISTRATIONS_FILE, registrations)
            
            return WAITING_USER_ANSWERS
    
    # If user has selected a test, this is their answer
    if 'selected_test' in context.user_data:
        test_id = context.user_data['selected_test']
        user_answers = text.strip().replace(' ', '').lower()
        
        # Get test data to validate
        tests = load_data(TESTS_FILE)
        if test_id not in tests:
            await update.message.reply_text("❌ Test topilmadi. Qaytadan urinib ko'ring.")
            del context.user_data['selected_test']
            await show_main_menu(update, context)
            return
        
        correct_answers = tests[test_id]['answers'].replace(' ', '').lower()
        correct_count = len([c for c in correct_answers if c.isalpha()])
        user_count = len([c for c in user_answers if c.isalpha()])
        
        # Validate answer count
        if user_count != correct_count:
            if user_count < correct_count:
                await update.message.reply_text(
                    f"❌ Javoblar sonida xatolik!\n\n"
                    f"Kerakli javoblar soni: {correct_count} ta\n"
                    f"Siz yuborgan javoblar soni: {user_count} ta\n\n"
                    f"⚠️ Siz {correct_count - user_count} ta kam javob yubordingiz!\n\n"
                    f"Iltimos, {correct_count} ta javob yuboring (Format: 1a2b3c yoki abc):"
                )
            else:
                await update.message.reply_text(
                    f"❌ Javoblar sonida xatolik!\n\n"
                    f"Kerakli javoblar soni: {correct_count} ta\n"
                    f"Siz yuborgan javoblar soni: {user_count} ta\n\n"
                    f"⚠️ Siz {user_count - correct_count} ta ko'p javob yubordingiz!\n\n"
                    f"Iltimos, {correct_count} ta javob yuboring (Format: 1a2b3c yoki abc):"
                )
            return
        
        # Save user's answers
        registrations = load_data(REGISTRATIONS_FILE)
        registrations[test_id][str(user_id)]['answers'] = user_answers
        registrations[test_id][str(user_id)]['submitted_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_data(REGISTRATIONS_FILE, registrations)
        
        await update.message.reply_text(
            f"✅ Javoblaringiz qabul qilindi!\n\n"
            f"Sizning javobingiz: {user_answers}\n"
            f"Javoblar soni: {user_count} ta\n\n"
            f"Natijalar tekshirish vaqtida e'lon qilinadi."
        )
        
        del context.user_data['selected_test']
        await show_main_menu(update, context)


# Admin commands
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sizda bu buyruqni ishlatish huquqi yo'q.")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Test qo'shish", callback_data="admin_add_test")],
        [InlineKeyboardButton("📊 Javoblarni tekshirish", callback_data="admin_check_answers")],
        [InlineKeyboardButton("📈 Rasch Analysis", callback_data="admin_rasch_analysis")],
        [InlineKeyboardButton("📋 Ro'yxatlar", callback_data="admin_view_registrations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 Admin Panel\n\n"
        "Tanlang:",
        reply_markup=reply_markup
    )


# Admin add test
async def admin_add_test_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start adding a new test"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("📝 Test raqamini kiriting:")
    return ADMIN_WAITING_TEST_NUMBER


async def admin_get_test_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get test number"""
    context.user_data['admin_test_number'] = update.message.text
    await update.message.reply_text(
        "📝 Test javoblarini kiriting (Format: 1a2b3c yoki abc):"
    )
    return ADMIN_WAITING_ANSWERS


async def admin_get_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get test answers"""
    context.user_data['admin_test_answers'] = update.message.text
    await update.message.reply_text(
        "📅 Ro'yxatdan o'tish deadline ni kiriting (Format: YYYY-MM-DD HH:MM:SS):\n"
        "Masalan: 2025-02-15 23:59:59"
    )
    return ADMIN_WAITING_DEADLINE


async def admin_get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get registration deadline"""
    try:
        deadline = datetime.strptime(update.message.text, '%Y-%m-%d %H:%M:%S')
        context.user_data['admin_test_deadline'] = update.message.text
        
        await update.message.reply_text(
            "🕐 Tekshirish vaqtini kiriting (Format: YYYY-MM-DD HH:MM:SS):\n"
            "Masalan: 2025-02-16 10:00:00"
        )
        return ADMIN_WAITING_CHECK_TIME
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, qaytadan kiriting (YYYY-MM-DD HH:MM:SS):"
        )
        return ADMIN_WAITING_DEADLINE


async def admin_get_check_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get check time and save test"""
    try:
        check_time = datetime.strptime(update.message.text, '%Y-%m-%d %H:%M:%S')
        
        # Save test
        tests = load_data(TESTS_FILE)
        test_id = context.user_data['admin_test_number']
        
        tests[test_id] = {
            'answers': context.user_data['admin_test_answers'],
            'deadline': context.user_data['admin_test_deadline'],
            'check_time': update.message.text,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data(TESTS_FILE, tests)
        
        await update.message.reply_text(
            f"✅ Test #{test_id} muvaffaqiyatli qo'shildi!\n\n"
            f"Javoblar: {tests[test_id]['answers']}\n"
            f"Deadline: {tests[test_id]['deadline']}\n"
            f"Tekshirish vaqti: {tests[test_id]['check_time']}"
        )
        
        # Clear user data
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Noto'g'ri format! Iltimos, qaytadan kiriting (YYYY-MM-DD HH:MM:SS):"
        )
        return ADMIN_WAITING_CHECK_TIME


# Admin check answers
async def admin_check_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check and grade all submitted answers"""
    query = update.callback_query
    await query.answer()
    
    tests = load_data(TESTS_FILE)
    registrations = load_data(REGISTRATIONS_FILE)
    
    keyboard = []
    for test_id in tests.keys():
        if test_id in registrations:
            keyboard.append([InlineKeyboardButton(f"Test #{test_id}", callback_data=f"check_{test_id}")])
    
    if not keyboard:
        await query.edit_message_text("❌ Hech qanday javob topilmadi.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 Qaysi testni tekshirmoqchisiz?",
        reply_markup=reply_markup
    )


async def admin_check_specific_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check specific test answers and send results to all participants"""
    query = update.callback_query
    await query.answer()
    
    test_id = query.data.replace("check_", "")
    
    tests = load_data(TESTS_FILE)
    registrations = load_data(REGISTRATIONS_FILE)
    
    if test_id not in tests or test_id not in registrations:
        await query.edit_message_text("❌ Test topilmadi.")
        return
    
    correct_answers = tests[test_id]['answers'].lower().replace(" ", "")
    # Extract only letters (answer options: a, b, c, d, e)
    correct_letters = [c for c in correct_answers if c.isalpha()]
    total_questions = len(correct_letters)
    
    results = []
    
    for user_id, user_data in registrations[test_id].items():
        if user_data['answers']:
            user_answers = user_data['answers'].lower().replace(" ", "")
            # Extract only letters from user answers
            user_letters = [c for c in user_answers if c.isalpha()]
            
            # Calculate score by comparing letter by letter
            score = 0
            for i in range(min(len(user_letters), len(correct_letters))):
                if user_letters[i] == correct_letters[i]:
                    score += 1
            
            # Update score in registrations
            registrations[test_id][user_id]['score'] = f"{score}/{total_questions}"
            
            # Send result to user
            try:
                result_message = (
                    f"📊 Test #{test_id} natijalari:\n\n"
                    f"👤 {user_data['name']} {user_data['surname']}\n"
                    f"✅ To'g'ri javoblar: {tests[test_id]['answers']}\n"
                    f"📝 Sizning javobingiz: {user_data['answers']}\n"
                    f"🎯 Ball: {score}/{total_questions}\n"
                    f"📊 Foiz: {round(score/total_questions*100, 1)}%"
                )
                await context.bot.send_message(chat_id=int(user_id), text=result_message)
            except Exception as e:
                logger.error(f"Error sending result to user {user_id}: {e}")
            
            results.append(
                f"👤 {user_data['name']} {user_data['surname']}\n"
                f"   Javob: {user_data['answers']}\n"
                f"   Ball: {score}/{total_questions} ({round(score/total_questions*100, 1)}%)\n"
            )
        else:
            results.append(
                f"👤 {user_data['name']} {user_data['surname']}\n"
                f"   ⚠️ Javob yuborilmagan\n"
            )
    
    save_data(REGISTRATIONS_FILE, registrations)
    
    if not results:
        await query.edit_message_text(f"❌ Test #{test_id} uchun javoblar yo'q.")
        return
    
    # Sort results by score (highest first)
    sorted_results = sorted(
        [(r, int(r.split("Ball: ")[1].split("/")[0]) if "Ball:" in r else -1) for r in results],
        key=lambda x: x[1],
        reverse=True
    )
    
    result_text = f"📊 Test #{test_id} natijalari:\n\n"
    result_text += f"✅ To'g'ri javoblar: {tests[test_id]['answers']}\n"
    result_text += f"👥 Ishtirokchilar: {len(results)} ta\n\n"
    result_text += "🏆 Natijalar (tartib bo'yicha):\n\n"
    result_text += "\n".join([r[0] for r in sorted_results])
    result_text += "\n\n✅ Barcha ishtirokchilarga natijalar yuborildi!"
    
    await query.edit_message_text(result_text)


# Admin view registrations
async def admin_view_registrations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all registrations"""
    query = update.callback_query
    await query.answer()
    
    registrations = load_data(REGISTRATIONS_FILE)
    
    if not registrations:
        await query.edit_message_text("❌ Hech qanday ro'yxat topilmadi.")
        return
    
    result_text = "📋 Barcha ro'yxatlar:\n\n"
    
    for test_id, users in registrations.items():
        result_text += f"📝 Test #{test_id} ({len(users)} ta foydalanuvchi):\n"
        for user_id, user_data in users.items():
            result_text += f"   • {user_data['name']} {user_data['surname']}\n"
        result_text += "\n"
    
    await query.edit_message_text(result_text)


# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await update.message.reply_text("❌ Amal bekor qilindi.")
    return ConversationHandler.END


# Rasch Analysis Functions
def perform_rasch_analysis(test_id: str, registrations: dict, tests: dict) -> tuple:
    """
    Perform Rasch analysis on test results
    Returns: (result_df, items_info_df, graph_buffer)
    """
    try:
        # Prepare data
        data = []
        user_ids = []
        
        correct_answers = tests[test_id]['answers'].lower().replace(" ", "")
        correct_letters = [c for c in correct_answers if c.isalpha()]
        num_questions = len(correct_letters)
        
        for user_id, user_data in registrations[test_id].items():
            if user_data['answers']:
                user_answers = user_data['answers'].lower().replace(" ", "")
                user_letters = [c for c in user_answers if c.isalpha()]
                
                # Create binary response vector (1=correct, 0=wrong)
                responses = []
                for i in range(num_questions):
                    if i < len(user_letters):
                        responses.append(1 if user_letters[i] == correct_letters[i] else 0)
                    else:
                        responses.append(0)
                
                data.append(responses)
                user_ids.append(f"{user_data['name']} {user_data['surname']}")
        
        if not data:
            return None, None, None
        
        # Create DataFrame
        df = pd.DataFrame(data, index=user_ids, 
                         columns=[f"S{i+1}" for i in range(num_questions)])
        
        # Rasch difficulty calculation
        p_values = df.mean().clip(lower=0.01, upper=0.99)
        difficulty_logits = np.log((1 - p_values) / p_values)
        
        # Item weights (1.0 to 4.0)
        min_l, max_l = difficulty_logits.min(), difficulty_logits.max()
        if max_l == min_l:
            item_weights = np.ones(len(difficulty_logits)) * 2.5
        else:
            item_weights = (difficulty_logits - min_l) / (max_l - min_l) * 3.0 + 1.0
        
        # Calculate scores
        raw_weighted_scores = df.dot(item_weights)
        max_possible_raw = item_weights.sum()
        target_max = 90.5
        p = 0.75
        final_scores = ((raw_weighted_scores / max_possible_raw) ** p) * target_max
        rounded_scores = final_scores.round(2)
        
        # Certificate levels
        def get_certificate(score):
            if score >= 70: return "A+"
            elif 65 <= score < 70: return "A"
            elif 60 <= score < 65: return "B+"
            elif 55 <= score < 60: return "B"
            elif 50 <= score < 55: return "C+"
            elif 46 <= score < 50: return "C"
            else: return "Sertifikat berilmaydi"
        
        # Results DataFrame
        result_df = pd.DataFrame({
            'Ishtirokchi': user_ids,
            'Togri_Javoblar': df.sum(axis=1),
            'Rasch_Ball_90.5': rounded_scores,
            'Sertifikat': rounded_scores.apply(get_certificate)
        })
        
        # Items info for graph
        items_info = pd.DataFrame({
            'Savol': df.columns,
            'Savol_Bali': item_weights.values.round(2)
        }).sort_values(by='Savol_Bali', ascending=True)
        
        # Create graph
        plt.figure(figsize=(12, 6))
        sns.set_style("white")
        palette = sns.color_palette("Blues_d", len(items_info))
        
        ax = sns.barplot(x='Savol', y='Savol_Bali', data=items_info, palette=palette)
        
        plt.title(f'Test #{test_id} - Savollar Qiyinlik Darajasi (Rasch Analysis)', 
                 fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Savollar', fontsize=11, fontweight='bold')
        plt.ylabel('Ball (1.0 - 4.0)', fontsize=11, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 4.5)
        
        # Add values on bars
        for p in ax.patches:
            ax.annotate(format(p.get_height(), '.2f'),
                       (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='center',
                       xytext=(0, 8),
                       textcoords='offset points',
                       fontsize=9, fontweight='bold', color='black')
        
        sns.despine()
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return result_df, items_info, buf
        
    except Exception as e:
        logger.error(f"Rasch analysis error: {e}")
        return None, None, None


async def admin_rasch_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available tests for Rasch analysis"""
    query = update.callback_query
    await query.answer()
    
    tests = load_data(TESTS_FILE)
    registrations = load_data(REGISTRATIONS_FILE)
    
    keyboard = []
    for test_id in tests.keys():
        if test_id in registrations and registrations[test_id]:
            # Count how many submitted answers
            submitted = sum(1 for u in registrations[test_id].values() if u.get('answers'))
            if submitted > 0:
                keyboard.append([InlineKeyboardButton(
                    f"Test #{test_id} ({submitted} ta ishtirokchi)", 
                    callback_data=f"rasch_{test_id}"
                )])
    
    if not keyboard:
        await query.edit_message_text("❌ Rasch analysis uchun javoblar yo'q.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📈 Rasch Analysis\n\nQaysi testni tahlil qilmoqchisiz?",
        reply_markup=reply_markup
    )


async def admin_rasch_specific_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform Rasch analysis on specific test"""
    query = update.callback_query
    await query.answer("📊 Rasch analysis bajarilmoqda...")
    
    test_id = query.data.replace("rasch_", "")
    
    tests = load_data(TESTS_FILE)
    registrations = load_data(REGISTRATIONS_FILE)
    
    if test_id not in tests or test_id not in registrations:
        await query.edit_message_text("❌ Test topilmadi.")
        return
    
    # Perform analysis
    result_df, items_info, graph_buf = perform_rasch_analysis(test_id, registrations, tests)
    
    if result_df is None:
        await query.edit_message_text("❌ Rasch analysis amalga oshirilmadi. Javoblar yo'q.")
        return
    
    # Send graph
    await query.message.reply_photo(
        photo=graph_buf,
        caption=f"📈 Test #{test_id} - Savollar qiyinlik darajasi (Rasch Analysis)"
    )
    
    # Send results as formatted message
    result_text = f"📊 Test #{test_id} - Rasch Analysis Natijalari\n\n"
    result_text += f"👥 Ishtirokchilar: {len(result_df)} ta\n\n"
    result_text += "🏆 Natijalar:\n\n"
    
    # Sort by score
    result_df_sorted = result_df.sort_values('Rasch_Ball_90.5', ascending=False)
    
    for idx, row in result_df_sorted.iterrows():
        result_text += f"{row['Ishtirokchi']}\n"
        result_text += f"  ✓ To'g'ri: {row['Togri_Javoblar']} | "
        result_text += f"Ball: {row['Rasch_Ball_90.5']:.2f} | "
        result_text += f"{row['Sertifikat']}\n\n"
    
    # Send results to chat
    await query.message.reply_text(result_text)
    
    # Send individual results to participants
    for user_id, user_data in registrations[test_id].items():
        if user_data.get('answers'):
            try:
                # Find user's result
                user_name = f"{user_data['name']} {user_data['surname']}"
                user_result = result_df[result_df['Ishtirokchi'] == user_name].iloc[0]
                
                personal_message = (
                    f"📊 Test #{test_id} - Rasch Analysis Natijasi\n\n"
                    f"👤 {user_name}\n"
                    f"✅ To'g'ri javoblar: {int(user_result['Togri_Javoblar'])}\n"
                    f"🎯 Rasch Ball: {user_result['Rasch_Ball_90.5']:.2f} / 90.5\n"
                    f"🏆 Sertifikat: {user_result['Sertifikat']}\n\n"
                    f"📈 Rasch Analysis - professional baholash usuli orqali "
                    f"savollar qiyin ligi hisobga olingan holda ball hisobla ndi."
                )
                
                await context.bot.send_message(chat_id=int(user_id), text=personal_message)
                
                # Send graph to user as well
                graph_buf.seek(0)
                await context.bot.send_photo(
                    chat_id=int(user_id),
                    photo=graph_buf,
                    caption="📈 Test savollarining qiyinlik darajasi"
                )
                
            except Exception as e:
                logger.error(f"Error sending Rasch result to user {user_id}: {e}")
    
    await query.edit_message_text(
        f"✅ Rasch Analysis yakunlandi!\n\n"
        f"📊 {len(result_df)} ta ishtirokchiga shaxsiy natijalar yuborildi.\n"
        f"📈 Grafik va batafsil natijalar yuqorida ko'rsatilgan."
    )


# Main function
def main():
    """Start the bot"""
    # Create application with increased timeout for slow connections
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,  # 60 seconds to connect
        read_timeout=60.0,     # 60 seconds to read
        write_timeout=60.0,    # 60 seconds to write
        pool_timeout=60.0      # 60 seconds to get connection from pool
    )
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    
    # User conversation handler
    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Admin conversation handler for adding tests
    admin_test_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_test_start, pattern='^admin_add_test$')],
        states={
            ADMIN_WAITING_TEST_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_test_number)],
            ADMIN_WAITING_ANSWERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_answers)],
            ADMIN_WAITING_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_deadline)],
            ADMIN_WAITING_CHECK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_check_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(user_conv_handler)
    application.add_handler(admin_test_conv_handler)
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(admin_check_answers, pattern='^admin_check_answers$'))
    application.add_handler(CallbackQueryHandler(admin_check_specific_test, pattern='^check_'))
    application.add_handler(CallbackQueryHandler(admin_rasch_analysis, pattern='^admin_rasch_analysis$'))
    application.add_handler(CallbackQueryHandler(admin_rasch_specific_test, pattern='^rasch_'))
    application.add_handler(CallbackQueryHandler(admin_view_registrations, pattern='^admin_view_registrations$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()