# Telegram File Upload Bot

Bot Telegram untuk upload file ke berbagai hosting gratis (PixelDrain, GoFile, Catbox, dll) menggunakan GitHub Actions.

## Fitur

✅ Multi-service upload (PixelDrain, GoFile, Catbox, AnonFiles, File.io)
✅ Support file besar via Telegram userbot
✅ Real-time progress tracking (update setiap 5 detik)
✅ Multi-file upload
✅ Cancel upload kapan saja
✅ UI dengan tombol interaktif
✅ Unique ID untuk setiap file

## Instalasi

### 1. Persiapan Telegram

#### A. Buat Bot Telegram
1. Chat [@BotFather](https://t.me/BotFather)
2. Ketik `/newbot`
3. Ikuti instruksi, dapatkan `BOT_TOKEN`

#### B. Dapatkan API Credentials
1. Buka https://my.telegram.org/auth
2. Login dan buka "API development tools"
3. Buat app baru, dapatkan:
   - `API_ID`
   - `API_HASH`

#### C. Generate String Session
```bash
pip install telethon
python generate_session.py
```
Masukkan `API_ID` dan `API_HASH`, login, simpan `STRING_SESSION`

### 2. Setup GitHub Repository

#### A. Fork/Create Repository
1. Buat repository baru di GitHub
2. Upload semua file dari project ini

#### B. Setup GitHub Secrets
Buka Settings → Secrets and variables → Actions → New repository secret

**Required Secrets:**
- `TELEGRAM_BOT_TOKEN` - Token dari BotFather
- `TELEGRAM_API_ID` - API ID dari my.telegram.org
- `TELEGRAM_API_HASH` - API Hash dari my.telegram.org
- `TELEGRAM_STRING_SESSION` - String session dari generate_session.py
- `GITHUB_TOKEN` - GitHub Personal Access Token (buat di Settings → Developer settings → Personal access tokens → Generate new token)

**Optional (API Keys untuk services):**
- `PIXELDRAIN_API_KEY` - https://pixeldrain.com/user/api_keys
- `GOFILE_API_KEY` - https://gofile.io/myProfile
- `CATBOX_USER_HASH` - https://catbox.moe/user/manage.php

#### C. Enable GitHub Actions
1. Buka repository Settings
2. Actions → General
3. Pilih "Allow all actions and reusable workflows"
4. Save

### 3. Setup Environment Variables

Buat file `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
GITHUB_TOKEN=your_github_token
GITHUB_REPO=username/repo-name
AUTHORIZED_USERS=123456789,987654321
```

### 4. Deploy Bot

#### Opsi 1: Local (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan bot
python bot_improved.py
```

#### Opsi 2: VPS/Server
```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan dengan screen/tmux
screen -S telegram-bot
python bot_improved.py
# Ctrl+A+D untuk detach
```

#### Opsi 3: Docker
```bash
docker build -t telegram-upload-bot .
docker run -d --env-file .env telegram-upload-bot
```

### 5. Setup GitHub Actions Workflow

File `.github/workflows/upload.yml` sudah siap, pastikan:
1. File ada di repository
2. GitHub Secrets sudah diisi
3. Actions sudah enabled

## Cara Penggunaan

### Upload File

**Metode 1: Reply ke file**
```
/pixeldrain
```
(reply ke pesan yang berisi file)

**Metode 2: Link Telegram**
```
/pixeldrain https://t.me/c/1234567890/123
```

### Commands

- `/start` - Mulai bot & lihat info
- `/help` - Panduan penggunaan
- `/status` - Lihat sesi upload aktif
- `/pixeldrain` - Upload ke PixelDrain
- `/gofile` - Upload ke GoFile
- `/catbox` - Upload ke Catbox
- `/anonfiles` - Upload ke AnonFiles
- `/fileio` - Upload ke File.io
- `/cancel_[id]` - Cancel upload

### Cancel Upload

Ketika upload dimulai, bot akan memberi Session ID:
```
/cancel_abc12345
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token dari BotFather |
| `TELEGRAM_API_ID` | ✅ | API ID dari my.telegram.org |
| `TELEGRAM_API_HASH` | ✅ | API Hash dari my.telegram.org |
| `TELEGRAM_STRING_SESSION` | ✅ | String session untuk userbot |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token |
| `GITHUB_REPO` | ✅ | Format: username/repo-name |
| `AUTHORIZED_USERS` | ❌ | User IDs yang diizinkan (comma separated) |
| `PIXELDRAIN_API_KEY` | ❌ | PixelDrain API key |
| `GOFILE_API_KEY` | ❌ | GoFile API token |
| `CATBOX_USER_HASH` | ❌ | Catbox user hash |

## GitHub Secrets (Required)

Setup di Repository Settings → Secrets:

```
TELEGRAM_BOT_TOKEN
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_STRING_SESSION
PIXELDRAIN_API_KEY (optional)
GOFILE_API_KEY (optional)
CATBOX_USER_HASH (optional)
```

## Troubleshooting

### Bot tidak respond
- Cek `TELEGRAM_BOT_TOKEN` benar
- Pastikan bot sudah dijalankan
- Cek authorized users

### GitHub Actions tidak jalan
- Pastikan Actions enabled di repository
- Cek semua secrets sudah diisi
- Lihat logs di Actions tab

### Upload gagal
- Cek API keys untuk service yang digunakan
- Pastikan file tidak terlalu besar (limit per service berbeda)
- Cek logs GitHub Actions

### String session invalid
- Generate ulang dengan `generate_session.py`
- Pastikan tidak ada spasi atau newline di string session

## Limitations

- File size tergantung limit Telegram (2GB untuk bot, unlimited untuk userbot)
- Upload speed tergantung GitHub Actions runner
- Free tier GitHub Actions: 2000 menit/bulan
- Beberapa service punya limit file size

## License

MIT License

## Support

Jika ada masalah, buka issue di GitHub repository.
