# Project Structure

```
telegram-upload-bot/
│
├── bot.py                      # Bot Telegram utama
├── workflow_handler.py         # Handler untuk GitHub Actions
├── workflow_trigger.py         # Trigger GitHub Actions dari bot
├── generate_session.py         # Generate Telegram string session
│
├── .github/
│   └── workflows/
│       └── upload.yml          # GitHub Actions workflow
│
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container
├── .env.example               # Template environment variables
├── .gitignore                 # Git ignore file
│
├── README.md                   # Dokumentasi lengkap
├── QUICKSTART.md              # Panduan cepat
├── STRUCTURE.md               # File ini
└── setup.sh                   # Setup script otomatis
```

## File Descriptions

### Core Files

**bot.py**
- Bot Telegram utama
- Handle commands: /pixeldrain, /gofile, /catbox, dll
- UI dengan tombol interaktif
- Session management
- Cancel upload support

**workflow_handler.py**
- Dijalankan oleh GitHub Actions
- Download file dari Telegram (via userbot)
- Upload ke file hosting
- Real-time progress update
- Multi-file support

**workflow_trigger.py**
- Trigger GitHub Actions workflow via API
- Digunakan oleh bot.py

**generate_session.py**
- Generate Telegram string session
- Diperlukan untuk userbot (download file besar)

### Configuration

**.env.example**
Template environment variables:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_API_ID
- TELEGRAM_API_HASH
- TELEGRAM_STRING_SESSION
- GITHUB_TOKEN
- GITHUB_REPO
- AUTHORIZED_USERS

### Deployment

**Dockerfile**
- Container untuk deploy bot
- Base: Python 3.10

**setup.sh**
- Automated setup script
- Check dependencies
- Validate credentials
- Create directories

### GitHub Actions

**.github/workflows/upload.yml**
- Workflow untuk handle upload
- Triggered via GitHub API
- Run workflow_handler.py

## How It Works

1. **User sends file** → Bot (bot.py)
2. **Bot creates session** → Unique ID generated
3. **User confirms** → Trigger GitHub Actions
4. **GitHub Actions** → workflow_handler.py runs
5. **Download from Telegram** → Using userbot (string session)
6. **Upload to service** → PixelDrain/GoFile/etc
7. **Update progress** → Real-time (every 5s)
8. **Send result** → Download link to user

## Data Flow

```
Telegram User
    ↓
Bot (bot.py)
    ↓
GitHub API
    ↓
GitHub Actions
    ↓
workflow_handler.py
    ↓
Telegram API (userbot) → Download file
    ↓
File Hosting API → Upload file
    ↓
Bot → Send link to user
```

## Setup Order

1. Generate string session: `python generate_session.py`
2. Setup GitHub repository + Secrets
3. Configure .env file
4. Run setup: `./setup.sh` or `bash setup.sh`
5. Start bot: `python bot.py`

## Environment

### Development
```bash
pip install -r requirements.txt
python bot.py
```

### Production (VPS)
```bash
screen -S telegram-bot
python bot.py
# Ctrl+A+D to detach
```

### Docker
```bash
docker build -t telegram-upload-bot .
docker run -d --env-file .env telegram-upload-bot
```

## Features

✅ Multi-service upload
✅ Large file support (userbot)
✅ Real-time progress
✅ Multi-file upload
✅ Cancel anytime
✅ Interactive UI
✅ Unique session IDs

## Services Supported

- PixelDrain (API key recommended)
- GoFile (API key recommended)
- Catbox (User hash recommended)
- AnonFiles (free)
- File.io (free, one-time download)

## Requirements

- Python 3.10+
- Telegram Bot Token
- Telegram API credentials
- GitHub repository
- GitHub Personal Access Token

## Limitations

- GitHub Actions: 2000 minutes/month (free)
- File size: depends on service
- Upload speed: depends on GitHub runners
- Concurrent uploads: depends on Actions runners

## Security

- Authorized users only (optional)
- API keys in GitHub Secrets
- String session encrypted
- No public file access

## Support

- README.md - Full documentation
- QUICKSTART.md - Quick setup guide
- GitHub Issues - Bug reports
