import os
import json
import asyncio
import aiohttp
import requests
import traceback
from pathlib import Path
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot
from telegram.constants import ParseMode

# --- Configuration ---
SESSION_ID = os.environ.get('SESSION_ID')
SERVICE = os.environ.get('SERVICE', 'pixeldrain')
RAW_DATA = os.environ.get('WORKFLOW_DATA', '{}')

# Parsing data dengan proteksi
try:
    WORKFLOW_DATA = json.loads(RAW_DATA)
except Exception as e:
    print(f"❌ Error parsing WORKFLOW_DATA JSON: {e}")
    WORKFLOW_DATA = {}

TELEGRAM_API_ID = os.environ.get('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
TELEGRAM_STRING_SESSION = os.environ.get('TELEGRAM_STRING_SESSION')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# API Keys
PIXELDRAIN_API_KEY = os.environ.get('PIXELDRAIN_API_KEY')
GOFILE_API_KEY = os.environ.get('GOFILE_API_KEY')
CATBOX_USER_HASH = os.environ.get('CATBOX_USER_HASH')

DOWNLOAD_DIR = Path('downloads')
DOWNLOAD_DIR.mkdir(exist_ok=True)

class ProgressTracker:
    def __init__(self, bot, chat_id, message_id, session_id, total_size, filename):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.session_id = session_id
        self.total_size = total_size
        self.filename = filename
        self.downloaded = 0
        self.last_update = datetime.now()
        self.start_time = datetime.now()
    
    def create_progress_bar(self, percentage):
        filled = int(percentage / 10)
        bar = '█' * filled + '░' * (10 - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    async def update_progress(self, current, total=None):
        if total: self.total_size = total
        self.downloaded = current
        
        now = datetime.now()
        if (now - self.last_update).total_seconds() < 5 and current < self.total_size:
            return
        
        self.last_update = now
        percentage = (self.downloaded / self.total_size * 100) if self.total_size > 0 else 0
        
        elapsed = (now - self.start_time).total_seconds()
        speed = self.downloaded / elapsed if elapsed > 0 else 0
        remaining = (self.total_size - self.downloaded) / speed if speed > 0 else 0
        
        status_text = (
            f"📥 <b>Downloading</b>\n\n"
            f"📄 <b>File:</b> {self.filename}\n"
            f"📊 <b>Progress:</b> {self.create_progress_bar(percentage)}\n"
            f"💾 <b>Size:</b> {self.downloaded/(1024*1024):.2f}MB / {self.total_size/(1024*1024):.2f}MB\n"
            f"⚡ <b>Speed:</b> {speed/(1024*1024):.2f} MB/s\n"
            f"⏱ <b>ETA:</b> {int(remaining)}s"
        )
        
        try:
            await self.bot.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=status_text, parse_mode=ParseMode.HTML)
        except: pass

class FileUploader:
    def __init__(self, service, api_key=None):
        self.service = service.lower()
        self.api_key = api_key
    
    async def upload(self, file_path):
        print(f"DEBUG: Memulai upload {file_path.name} ke {self.service}")
        try:
            if self.service == 'pixeldrain':
                url = "https://pixeldrain.com/api/file"
                auth = ('', self.api_key) if self.api_key else None
                with open(file_path, 'rb') as f:
                    r = requests.post(url, files={'file': f}, auth=auth)
                    if r.status_code == 201: return f"https://pixeldrain.com/u/{r.json()['id']}"
            
            elif self.service == 'gofile':
                s_res = requests.get('https://api.gofile.io/getServer').json()
                server = s_res['data']['server']
                url = f"https://{server}.gofile.io/uploadFile"
                data = {'token': self.api_key} if self.api_key else {}
                with open(file_path, 'rb') as f:
                    r = requests.post(url, files={'file': f}, data=data).json()
                    if r['status'] == 'ok': return r['data']['downloadPage']
            
            # Tambahkan service lain di sini jika perlu
        except Exception as e:
            print(f"DEBUG: Upload error: {e}")
        return None

async def main():
    print(f"--- Workflow Start: {SESSION_ID} ---")
    
    try:
        # 1. Validasi Data
        if not WORKFLOW_DATA or 'chat_id' not in WORKFLOW_DATA:
            print("❌ ERROR: WORKFLOW_DATA kosong atau tidak lengkap!")
            print(f"Isi WORKFLOW_DATA saat ini: {RAW_DATA}")
            return

        chat_id = WORKFLOW_DATA['chat_id']
        message_id = WORKFLOW_DATA['message_id']
        files_to_process = WORKFLOW_DATA.get('files', [])

        print(f"✅ Data Diterima: Chat {chat_id}, Message {message_id}, Files: {len(files_to_process)}")

        # 2. Inisialisasi Bot & Client
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        client = TelegramClient(StringSession(TELEGRAM_STRING_SESSION), int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
        
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ ERROR: String Session Telethon tidak valid!")
            return
        
        print("✅ Telegram Client Terhubung")

        # 3. Proses Files
        uploaded_results = []
        uploader = FileUploader(SERVICE, PIXELDRAIN_API_KEY if SERVICE == 'pixeldrain' else GOFILE_API_KEY)

        for idx, file_info in enumerate(files_to_process, 1):
            print(f"--- Memproses File {idx}/{len(files_to_process)} ---")
            
            # Progress tracker awal
            tracker = ProgressTracker(bot, chat_id, message_id, SESSION_ID, 0, f"File {idx}")
            
            # Download
            msg = await client.get_messages(file_info['chat_id'], ids=file_info['message_id'])
            if not msg or not msg.media:
                print(f"⚠️ File {idx} tidak ditemukan atau bukan media.")
                continue
            
            filename = msg.file.name or f"file_{idx}_{SESSION_ID}"
            path = DOWNLOAD_DIR / filename
            tracker.filename = filename
            
            print(f"Downloading: {filename}...")
            await client.download_media(msg, file=str(path), 
                                        progress_callback=lambda c, t: asyncio.create_task(tracker.update_progress(c, t)))
            
            # Upload
            print(f"Uploading: {filename}...")
            link = await uploader.upload(path)
            
            if link:
                uploaded_results.append({'name': filename, 'link': link})
                print(f"✅ Sukses: {link}")
            else:
                print(f"❌ Gagal Upload: {filename}")
            
            if path.exists(): path.unlink()

        # 4. Kirim Hasil Akhir
        if uploaded_results:
            text = f"✅ <b>Mirror Berhasil!</b>\n\n🆔 <code>{SESSION_ID}</code>\n\n"
            for res in uploaded_results:
                text += f"📄 {res['name']}\n🔗 <code>{res['link']}</code>\n\n"
        else:
            text = "❌ <b>Proses Selesai</b>\n\nTidak ada file yang berhasil diupload."

        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML)
        print("--- Workflow Finished Successfully ---")

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        traceback.print_exc()
    finally:
        if 'client' in locals(): await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
