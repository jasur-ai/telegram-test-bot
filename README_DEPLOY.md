# Telegram Test Bot - O'quv Test Boshqaruv Boti

Test topshirish va natijalarni tekshirish uchun Telegram bot.

## 🚀 Xususiyatlar

- ✅ Majburiy kanal obunasi (@untoldies)
- ✅ Foydalanuvchi ro'yxatdan o'tish
- ✅ Test yaratish va boshqarish
- ✅ Javoblarni avtomatik tekshirish
- ✅ Natijalarni barcha ishtirokchilarga yuborish
- ✅ Javoblar sonini validatsiya qilish
- ✅ Tartib bo'yicha natijalar

## 📋 Talablar

- Python 3.8+
- python-telegram-bot 20.7

## 🔧 Lokal Ishga Tushirish

### 1. Repository ni clone qiling

```bash
git clone https://github.com/yourusername/telegram-test-bot.git
cd telegram-test-bot
```

### 2. Virtual environment yarating

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Paketlarni o'rnating

```bash
pip install -r requirements.txt
```

### 4. Environment o'zgaruvchilarni sozlang

```bash
cp .env.example .env
# .env faylini tahrirlang va o'z tokeningizni kiriting
```

### 5. Botni ishga tushiring

```bash
python telegram_bot.py
```

## ☁️ Cloud Deployment

### Render.com (BEPUL, KREDIT KARTA KERAK EMAS)

1. **GitHub ga yuklang:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/telegram-test-bot.git
   git push -u origin main
   ```

2. **Render.com da:**
   - https://render.com ga kiring
   - GitHub bilan login qiling
   - New → Web Service
   - Repository tanlang
   - Sozlamalar:
     ```
     Name: telegram-test-bot
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: python telegram_bot.py
     Instance Type: Free
     ```

3. **Environment Variables qo'shing:**
   ```
   BOT_TOKEN=8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4
   ADMIN_IDS=8004724563
   ```

4. **Deploy!**

### Railway.app

1. **Railway.app ga kiring:** https://railway.app
2. **New Project → Deploy from GitHub**
3. **Repository tanlang**
4. **Environment Variables:**
   ```
   BOT_TOKEN=your_token
   ADMIN_IDS=your_id
   ```

### Oracle Cloud (FOREVER FREE)

1. **VM yarating:**
   - https://cloud.oracle.com/compute/instances
   - Shape: VM.Standard.E2.1.Micro
   - Image: Ubuntu 22.04

2. **SSH ulanish:**
   ```bash
   ssh ubuntu@your_vm_ip
   ```

3. **Bot o'rnatish:**
   ```bash
   sudo apt update && sudo apt install python3 python3-pip python3-venv git -y
   git clone https://github.com/yourusername/telegram-test-bot.git
   cd telegram-test-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment sozlash:**
   ```bash
   nano .env
   # BOT_TOKEN va ADMIN_IDS kiriting
   ```

5. **Systemd service yaratish:**
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
   
   Fayl ichiga:
   ```ini
   [Unit]
   Description=Telegram Test Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/telegram-test-bot
   Environment="PATH=/home/ubuntu/telegram-test-bot/venv/bin"
   ExecStart=/home/ubuntu/telegram-test-bot/venv/bin/python /home/ubuntu/telegram-test-bot/telegram_bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

6. **Service ni yoqish:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   sudo systemctl status telegram-bot
   ```

## 📱 Ishlatish

### Foydalanuvchilar uchun:

1. `/start` - Botni boshlash
2. Kanalga obuna bo'lish
3. Ism va familiya kiriting
4. Testni tanlang
5. Javoblaringizni yuboring

### Adminlar uchun:

1. `/admin` - Admin panel
2. **Test qo'shish:**
   - Test raqami
   - Javoblar (1a2b3c yoki abc)
   - Deadline
   - Tekshirish vaqti
3. **Javoblarni tekshirish:**
   - Test tanlang
   - Avtomatik baholash
   - Hammaga natija yuboriladi

## 🔒 Xavfsizlik

- ⚠️ Bot tokenini hech qachon GitHub ga yuklamang!
- ✅ `.env` faylidan foydalaning
- ✅ Environment variables orqali tokenni server ga kiriting
- ✅ `.gitignore` da bot_data/ va .env mavjud

## 📊 Ma'lumotlar

Bot quyidagi fayllarni saqlaydi:

- `bot_data/users.json` - Foydalanuvchilar
- `bot_data/tests.json` - Testlar
- `bot_data/registrations.json` - Ro'yxatlar va javoblar

## 🐛 Muammolarni Hal Qilish

### Bot javob bermayapti:
```bash
# Loglarni tekshiring
sudo journalctl -u telegram-bot -f  # systemd
# yoki
cat bot.log  # agar logging sozlangan bo'lsa
```

### Timeout xatolari:
- Internet aloqasini tekshiring
- VPN kerak bo'lishi mumkin
- Timeout oshirilgan (60 soniya)

### Module topilmadi:
```bash
pip install -r requirements.txt
```

## 📞 Yordam

- Admin kanal: @IshtixonKimyo
- Bot: @RASH_model_KIMYO_bot

## 📄 License

MIT License

---

**Made with ❤️ for education**
