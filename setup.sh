#!/bin/bash

# Telegram Upload Bot - Setup Script
# Author: Claude
# Description: Automated setup for Telegram upload bot

echo "================================="
echo "Telegram Upload Bot - Setup"
echo "================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 tidak terinstall!"
    exit 1
fi

echo "✅ Python3 detected"

# Install requirements
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Gagal install dependencies!"
    exit 1
fi

echo "✅ Dependencies installed"

# Check .env file
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  File .env tidak ditemukan"
    echo "📝 Membuat .env dari template..."
    cp .env.example .env
    echo ""
    echo "⚙️  Silakan edit file .env dengan credentials kamu:"
    echo "   nano .env"
    echo ""
    echo "Credentials yang dibutuhkan:"
    echo "1. TELEGRAM_BOT_TOKEN (dari @BotFather)"
    echo "2. TELEGRAM_API_ID (dari my.telegram.org)"
    echo "3. TELEGRAM_API_HASH (dari my.telegram.org)"
    echo "4. TELEGRAM_STRING_SESSION (generate dengan: python generate_session.py)"
    echo "5. GITHUB_TOKEN (dari GitHub Settings)"
    echo "6. GITHUB_REPO (format: username/repo-name)"
    echo ""
    read -p "Apakah kamu sudah mengisi .env? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup dibatalkan. Silakan isi .env terlebih dahulu."
        exit 1
    fi
fi

# Load .env
export $(cat .env | grep -v '^#' | xargs)

# Check required variables
REQUIRED_VARS=("TELEGRAM_BOT_TOKEN" "TELEGRAM_API_ID" "TELEGRAM_API_HASH" "TELEGRAM_STRING_SESSION")

echo ""
echo "🔍 Checking environment variables..."

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ $var tidak diset!"
        exit 1
    fi
    echo "✅ $var"
done

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p downloads
mkdir -p temp
echo "✅ Directories created"

# Test bot token
echo ""
echo "🤖 Testing bot token..."
TEST_RESULT=$(python3 -c "
import requests
import os
token = os.environ.get('TELEGRAM_BOT_TOKEN')
response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
if response.status_code == 200:
    data = response.json()
    if data['ok']:
        print(f\"✅ Bot: @{data['result']['username']}\")
    else:
        print('❌ Token invalid')
        exit(1)
else:
    print('❌ Cannot connect to Telegram')
    exit(1)
" 2>&1)

if [ $? -ne 0 ]; then
    echo "$TEST_RESULT"
    exit 1
fi

echo "$TEST_RESULT"

echo ""
echo "================================="
echo "✅ Setup Complete!"
echo "================================="
echo ""
echo "🚀 Langkah selanjutnya:"
echo ""
echo "1. Setup GitHub Repository:"
echo "   - Upload file project ke GitHub"
echo "   - Setup Secrets di Settings → Secrets → Actions"
echo "   - Enable Actions"
echo ""
echo "2. Jalankan bot:"
echo "   python bot.py"
echo ""
echo "3. Test bot di Telegram:"
echo "   /start"
echo ""
echo "📚 Dokumentasi lengkap: README.md"
echo "⚡ Quick guide: QUICKSTART.md"
echo ""

read -p "Jalankan bot sekarang? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🤖 Starting bot..."
    python bot.py
fi
