#!/bin/bash

# Telegram Bot Deployment Script
# Bu skript botni serverga o'rnatadi

echo "🚀 Telegram Bot Deployment Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Iltimos, root sifatida ishlatmang!"
   echo "Oddiy foydalanuvchi sifatida ishga tushiring."
   exit 1
fi

# Update system
echo "📦 Sistema yangilanmoqda..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 Kerakli paketlar o'rnatilmoqda..."
sudo apt install python3 python3-pip python3-venv git -y

# Create bot directory
BOT_DIR="$HOME/telegram-test-bot"
if [ -d "$BOT_DIR" ]; then
    echo "⚠️  $BOT_DIR allaqachon mavjud!"
    read -p "O'chirish va qayta o'rnatish? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$BOT_DIR"
    else
        echo "❌ O'rnatish bekor qilindi."
        exit 1
    fi
fi

# Clone repository
echo "📥 Bot yuklab olinmoqda..."
read -p "GitHub repository URL: " REPO_URL
git clone "$REPO_URL" "$BOT_DIR"
cd "$BOT_DIR"

# Create virtual environment
echo "🔧 Virtual environment yaratilmoqda..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Python paketlar o'rnatilmoqda..."
pip install -r requirements.txt

# Setup environment
echo ""
echo "🔐 Environment sozlamalari"
echo "=========================="
cp .env.example .env
read -p "Bot token kiriting: " BOT_TOKEN
read -p "Admin ID kiriting: " ADMIN_ID

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_ID
EOF

echo "✅ .env fayli yaratildi!"

# Create systemd service
echo ""
echo "⚙️  Systemd service yaratilmoqda..."
SERVICE_FILE="/etc/systemd/system/telegram-bot.service"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Telegram Test Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Service yoqilmoqda..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
echo ""
echo "✅ O'rnatish tugadi!"
echo ""
echo "📊 Bot holati:"
sudo systemctl status telegram-bot --no-pager

echo ""
echo "🎉 Bot muvaffaqiyatli o'rnatildi!"
echo ""
echo "📝 Foydali buyruqlar:"
echo "  sudo systemctl status telegram-bot   - Holat ko'rish"
echo "  sudo systemctl restart telegram-bot  - Qayta ishga tushirish"
echo "  sudo systemctl stop telegram-bot     - To'xtatish"
echo "  sudo journalctl -u telegram-bot -f   - Loglarni ko'rish"
echo ""
echo "🌐 Bot ishlayapti! Telegram da sinab ko'ring."
