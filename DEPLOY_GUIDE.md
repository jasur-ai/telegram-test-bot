# 🚀 TEZKOR DEPLOY QO'LLANMASI

## ⚡ 5 DAQIQADA SERVERGA JOYLASHTIRISH

### 📋 KERAKLI NARSALAR:
- ✅ GitHub account
- ✅ Bot token: `8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4`
- ✅ Admin ID: `8004724563`

---

## 🌟 ENG OSON USUL: RENDER.COM (KREDIT KARTA KERAK EMAS!)

### 1️⃣ GitHub ga yuklash

```bash
# 1. GitHub da yangi repository yarating
#    https://github.com/new
#    Nomi: telegram-test-bot

# 2. O'z kompyuteringizda (bot papkasida)
cd /path/to/bot

# Git init
git init
git add .
git commit -m "Initial commit"

# GitHub ga push
git remote add origin https://github.com/USERNAME/telegram-test-bot.git
git branch -M main
git push -u origin main
```

### 2️⃣ Render.com da deploy

1. **Saytga kiring:** https://render.com
2. **GitHub bilan login qiling**
3. **New → Web Service**
4. **Repository tanlang:** telegram-test-bot
5. **Sozlamalar:**
   ```
   Name: telegram-test-bot
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python telegram_bot.py
   Instance Type: Free
   ```

6. **Environment Variables qo'shing:**
   - Click "Advanced" → "Add Environment Variable"
   ```
   BOT_TOKEN = 8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4
   ADMIN_IDS = 8004724563
   ```

7. **Create Web Service tugmasini bosing**

### ✅ TAYYOR! Bot 2-3 daqiqada ishga tushadi!

---

## 🔥 ALTERNATIV: RAILWAY.APP

1. **Saytga kiring:** https://railway.app
2. **GitHub bilan login**
3. **New Project → Deploy from GitHub**
4. **Repository tanlang**
5. **Environment variables:**
   ```
   BOT_TOKEN = 8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4
   ADMIN_IDS = 8004724563
   ```
6. **Deploy!**

---

## 💎 ENG YAXSHISI: ORACLE CLOUD (FOREVER FREE!)

### 1️⃣ Oracle Cloud Account

1. **Ro'yxatdan o'ting:** https://www.oracle.com/cloud/free/
2. Email, telefon, kredit karta (to'lov olmaydi!)

### 2️⃣ VM yarating

1. **Compute → Instances → Create Instance**
2. **Sozlamalar:**
   ```
   Name: telegram-bot
   Image: Ubuntu 22.04
   Shape: VM.Standard.E2.1.Micro (Always Free)
   Add SSH Keys: (yangi key yarating yoki mavjudni ishlating)
   ```
3. **Create tugmasi**

### 3️⃣ SSH ulanish

```bash
# Public IP ni oling (Instance details sahifasida)
ssh ubuntu@YOUR_PUBLIC_IP
```

### 4️⃣ Botni o'rnatish (AVTOMATIK SKRIPT)

```bash
# 1. Deploy skriptini yuklab oling
wget https://raw.githubusercontent.com/USERNAME/telegram-test-bot/main/deploy.sh

# 2. Executable qiling
chmod +x deploy.sh

# 3. Ishga tushiring
./deploy.sh

# Keyin:
# - GitHub repository URL kiriting
# - Bot token kiriting: 8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4
# - Admin ID kiriting: 8004724563
```

### ✅ TAYYOR! Bot avtomatik ishga tushadi!

---

## 🛠️ QO'LDA O'RNATISH (Oracle Cloud)

```bash
# 1. Sistema yangilash
sudo apt update && sudo apt upgrade -y

# 2. Python va Git o'rnatish
sudo apt install python3 python3-pip python3-venv git -y

# 3. Bot yuklab olish
cd ~
git clone https://github.com/USERNAME/telegram-test-bot.git
cd telegram-test-bot

# 4. Virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Paketlar
pip install -r requirements.txt

# 6. Environment sozlash
nano .env
```

`.env` ichiga:
```
BOT_TOKEN=8534371752:AAFDjc0nMbBSuFGtGl7s_sIUEn1A6Uz-9c4
ADMIN_IDS=8004724563
```

```bash
# 7. Test
python telegram_bot.py
# Ctrl+C bilan to'xtating

# 8. Systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

Service fayli:
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

```bash
# 9. Service yoqish
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# 10. Holat ko'rish
sudo systemctl status telegram-bot
```

---

## 📊 FOYDALI BUYRUQLAR

### Service boshqaruvi:
```bash
sudo systemctl status telegram-bot    # Holat
sudo systemctl start telegram-bot     # Ishga tushirish
sudo systemctl stop telegram-bot      # To'xtatish
sudo systemctl restart telegram-bot   # Qayta ishga tushirish
```

### Loglar:
```bash
sudo journalctl -u telegram-bot -f         # Jonli loglar
sudo journalctl -u telegram-bot --since today  # Bugungi
```

### Yangilanishlar:
```bash
cd ~/telegram-test-bot
git pull
sudo systemctl restart telegram-bot
```

---

## 🎯 QAYSI BIRINI TANLASH?

| Platform | Osonlik | Narx | Ishonchlilik | Tavsiya |
|----------|---------|------|--------------|---------|
| **Render.com** | ⭐⭐⭐⭐⭐ | Bepul | ⭐⭐⭐⭐ | Test uchun |
| **Railway.app** | ⭐⭐⭐⭐⭐ | $5/oy | ⭐⭐⭐⭐⭐ | Eng yaxshi |
| **Oracle Cloud** | ⭐⭐⭐ | BEPUL! | ⭐⭐⭐⭐⭐ | Production |

**Tavsiya:**
- 🎓 **O'rganish uchun:** Render.com (eng oson)
- 💼 **Real loyiha:** Oracle Cloud (forever free)
- ⚡ **Tez start:** Railway.app

---

## ❓ MUAMMOLAR?

### Bot ishlamayapti:
```bash
# Loglarni ko'ring
sudo journalctl -u telegram-bot -n 50

# Internetni tekshiring
ping api.telegram.org

# Qayta ishga tushiring
sudo systemctl restart telegram-bot
```

### "Module not found":
```bash
cd ~/telegram-test-bot
source venv/bin/activate
pip install -r requirements.txt
```

### Timeout xatolari:
- VPN yoqing (agar Telegram bloklangan bo'lsa)
- Internet aloqasini tekshiring

---

## 🎉 MUVAFFAQIYAT!

Bot endi 24/7 ishlaydi! PC ni o'chirsangiz ham davom etadi!

**Sinab ko'ring:** @RASH_model_KIMYO_bot
