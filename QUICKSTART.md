# Quick Start Guide

## Setup Cepat (5 Menit)

### 1. Generate String Session
```bash
pip install telethon
python generate_session.py
```
Simpan output STRING_SESSION

### 2. Setup GitHub Repository
1. Buat repo baru di GitHub
2. Upload semua file dari folder ini
3. Buka Settings → Secrets → Actions
4. Tambahkan secrets berikut:

```
TELEGRAM_BOT_TOKEN=<dari @BotFather>
TELEGRAM_API_ID=<dari my.telegram.org>
TELEGRAM_API_HASH=<dari my.telegram.org>
TELEGRAM_STRING_SESSION=<dari generate_session.py>
```

5. Settings → Actions → Enable "Allow all actions"

### 3. Jalankan Bot
```bash
# Copy .env.example ke .env
cp .env.example .env

# Edit .env dengan credentials kamu
nano .env

# Install dependencies
pip install -r requirements.txt

# Jalankan bot
python bot.py
```

### 4. Test Bot
1. Chat bot kamu di Telegram
2. Kirim `/start`
3. Upload file dengan `/pixeldrain` (reply ke file)
4. Tunggu hasil upload!

## Cara Dapatkan Credentials

### Bot Token
1. Chat [@BotFather](https://t.me/BotFather)
2. `/newbot`
3. Ikuti instruksi
4. Copy token

### API ID & Hash
1. https://my.telegram.org/auth
2. Login
3. "API development tools"
4. Buat app
5. Copy API_ID dan API_HASH

### GitHub Token
1. GitHub Settings
2. Developer settings
3. Personal access tokens
4. Generate new token (classic)
5. Pilih scope: `repo`, `workflow`
6. Copy token

## Environment Variables

Edit `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...
TELEGRAM_STRING_SESSION=1BVt...
GITHUB_TOKEN=ghp_...
GITHUB_REPO=username/repo-name
AUTHORIZED_USERS=123456789
```

## Test Commands

```bash
/start          # Info bot
/pixeldrain     # Upload (reply ke file)
/status         # Lihat upload aktif
/help           # Bantuan
```

## Troubleshooting

**Bot tidak respond:**
- Cek token benar
- Pastikan bot running

**Actions tidak jalan:**
- Enable Actions di repo settings
- Cek semua secrets terisi

**String session error:**
- Generate ulang
- Pastikan no spasi/newline

## Support

Issues: GitHub repository
