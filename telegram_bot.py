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
import asyncio
from aiohttp import web

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


# Health check endpoint for Render
async def health_check(request):
    """Simple health check endpoint"""
    return web.Response(text='Bot is running!', status=200)


async def start_health_server():
    """Start a simple HTTP server for health checks"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Health check server started on port {port}")


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
    application.add_handler(CallbackQueryHandler(admin_view_registrations, pattern='^admin_view_registrations$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot started...")
    
    # Create event loop and run both bot and health server
    loop = asyncio.get_event_loop()
    
    # Start health check server
    loop.create_task(start_health_server())
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()