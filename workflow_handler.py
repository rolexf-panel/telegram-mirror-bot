import os
import json
import asyncio
import aiohttp
import requests
from pathlib import Path
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot
from telegram.constants import ParseMode

# Configuration
SESSION_ID = os.environ.get('SESSION_ID')
SERVICE = os.environ.get('SERVICE')
WORKFLOW_DATA = json.loads(os.environ.get('WORKFLOW_DATA', '{}'))

TELEGRAM_API_ID = os.environ.get('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
TELEGRAM_STRING_SESSION = os.environ.get('TELEGRAM_STRING_SESSION')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# API Keys
PIXELDRAIN_API_KEY = os.environ.get('PIXELDRAIN_API_KEY')
GOFILE_API_KEY = os.environ.get('GOFILE_API_KEY')
CATBOX_USER_HASH = os.environ.get('CATBOX_USER_HASH')

# Directories
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
        self.last_update = 0
        self.start_time = datetime.now()
    
    def create_progress_bar(self, percentage):
        filled = int(percentage / 10)
        bar = '█' * filled + '░' * (10 - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    async def update_progress(self, current, total=None):
        self.downloaded = current
        if total:
            self.total_size = total
        
        current_time = datetime.now()
        if (current_time - self.last_update).total_seconds() < 5 and current < self.total_size:
            return
        
        self.last_update = current_time
        percentage = (self.downloaded / self.total_size * 100) if self.total_size > 0 else 0
        progress_bar = self.create_progress_bar(percentage)
        
        elapsed = (current_time - self.start_time).total_seconds()
        speed = self.downloaded / elapsed if elapsed > 0 else 0
        remaining = (self.total_size - self.downloaded) / speed if speed > 0 else 0
        
        downloaded_mb = self.downloaded / (1024 * 1024)
        total_mb = self.total_size / (1024 * 1024)
        speed_mb = speed / (1024 * 1024)
        
        status_text = f"""
📥 <b>Downloading</b>

🆔 <b>Session:</b> <code>{self.session_id}</code>
📄 <b>File:</b> {self.filename}

📊 <b>Progress:</b> {progress_bar}
💾 <b>Size:</b> {downloaded_mb:.2f} MB / {total_mb:.2f} MB
⚡ <b>Speed:</b> {speed_mb:.2f} MB/s
⏱ <b>ETA:</b> {int(remaining)}s

🔄 Downloading from Telegram...
"""
        try:
            await self.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=status_text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error updating progress: {e}")

class FileUploader:
    def __init__(self, service, api_key=None):
        self.service = service
        self.api_key = api_key
    
    async def upload_pixeldrain(self, file_path):
        url = "https://pixeldrain.com/api/file"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Basic {self.api_key}'
            response = requests.post(url, files=files, headers=headers)
            if response.status_code == 201:
                data = response.json()
                return f"https://pixeldrain.com/u/{data['id']}"
        return None
    
    async def upload_gofile(self, file_path):
        server_response = requests.get('https://api.gofile.io/getServer')
        server = server_response.json()['data']['server']
        url = f"https://{server}.gofile.io/uploadFile"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'token': self.api_key} if self.api_key else {}
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'ok':
                    return result['data']['downloadPage']
        return None

    async def upload_catbox(self, file_path):
        url = "https://catbox.moe/user/api.php"
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            if self.api_key:
                data['userhash'] = self.api_key
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                return response.text.strip()
        return None

    async def upload_anonfiles(self, file_path):
        url = "https://api.anonfiles.com/upload"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                data = response.json()
                if data['status']:
                    return data['data']['file']['url']['full']
        return None

    async def upload_fileio(self, file_path):
        url = "https://file.io"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    return data['link']
        return None

    async def upload(self, file_path):
        upload_methods = {
            'pixeldrain': self.upload_pixeldrain,
            'gofile': self.upload_gofile,
            'catbox': self.upload_catbox,
            'anonfiles': self.upload_anonfiles,
            'fileio': self.upload_fileio
        }
        method = upload_methods.get(self.service.lower())
        if method:
            return await method(file_path)
        return None

async def download_from_telegram(client, file_info, progress_tracker):
    try:
        message = await client.get_messages(file_info['chat_id'], ids=file_info['message_id'])
        if not message or not message.media:
            return None
        
        if hasattr(message.media, 'document'):
            filename = message.file.name or f"file_{SESSION_ID}"
            file_size = message.file.size
        else:
            filename = f"file_{SESSION_ID}"
            file_size = 0
            
        progress_tracker.filename = filename
        progress_tracker.total_size = file_size
        file_path = DOWNLOAD_DIR / filename
        
        await client.download_media(
            message,
            file=str(file_path),
            progress_callback=lambda c, t: asyncio.create_task(progress_tracker.update_progress(c, t))
        )
        return file_path
    except Exception as e:
        print(f"Error downloading from Telegram: {e}")
        return None

async def check_cancellation():
    cancel_file = Path(f'/tmp/cancel_queue/{SESSION_ID}.cancel')
    return cancel_file.exists()

async def main():
    print(f"Starting upload workflow for session: {SESSION_ID}")
    
    try:
        print("Initializing Telegram bot...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        chat_id = WORKFLOW_DATA['chat_id']
        message_id = WORKFLOW_DATA['message_id']
        files = WORKFLOW_DATA['files']
        
        client = TelegramClient(StringSession(TELEGRAM_STRING_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            error_text = f"❌ <b>Upload Failed</b>\n\n🆔 <b>Session:</b> <code>{SESSION_ID}</code>\n\nString session tidak valid."
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=error_text, parse_mode=ParseMode.HTML)
            await client.disconnect()
            return
            
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return

    # Mulai proses Upload
    try:
        api_key = None
        if SERVICE.lower() == 'pixeldrain': api_key = PIXELDRAIN_API_KEY
        elif SERVICE.lower() == 'gofile': api_key = GOFILE_API_KEY
        elif SERVICE.lower() == 'catbox': api_key = CATBOX_USER_HASH
        
        uploader = FileUploader(SERVICE, api_key)
        uploaded_files = []
        
        for idx, file_info in enumerate(files, 1):
            if await check_cancellation():
                break
            
            progress_tracker = ProgressTracker(bot, chat_id, message_id, SESSION_ID, 0, f"File {idx}")
            file_path = await download_from_telegram(client, file_info, progress_tracker)
            
            if file_path:
                status_text = f"📤 <b>Uploading</b>\n\n🆔 <b>Session:</b> <code>{SESSION_ID}</code>\n📄 <b>File:</b> {file_path.name}\n🎯 <b>Service:</b> {SERVICE.upper()}\n\n⏳ Uploading to {SERVICE}..."
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=status_text, parse_mode=ParseMode.HTML)
                
                upload_url = await uploader.upload(file_path)
                if upload_url:
                    uploaded_files.append({'filename': file_path.name, 'url': upload_url})
                
                if file_path.exists():
                    file_path.unlink()
        
        # Hasil Akhir
        if uploaded_files:
            result_text = f"✅ <b>Upload Complete</b>\n\n🆔 <b>Session:</b> <code>{SESSION_ID}</code>\n🎯 <b>Service:</b> {SERVICE.upper()}\n📦 <b>Files:</b> {len(uploaded_files)}/{len(files)}\n\n📎 <b>Links:</b>\n"
            for f in uploaded_files:
                result_text += f"📄 <b>{f['filename']}</b>\n🔗 <code>{f['url']}</code>\n\n"
        else:
            result_text = "❌ <b>Upload Failed</b>\n\nTidak ada file yang berhasil diupload."
            
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=result_text, parse_mode=ParseMode.HTML)
        await client.disconnect()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if 'client' in locals(): await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
