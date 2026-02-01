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
        
        # Update every 5 seconds
        current_time = datetime.now()
        if (current_time - self.last_update).total_seconds() < 5 and current < self.total_size:
            return
        
        self.last_update = current_time
        
        # Calculate progress
        percentage = (self.downloaded / self.total_size * 100) if self.total_size > 0 else 0
        progress_bar = self.create_progress_bar(percentage)
        
        # Calculate speed and ETA
        elapsed = (current_time - self.start_time).total_seconds()
        speed = self.downloaded / elapsed if elapsed > 0 else 0
        remaining = (self.total_size - self.downloaded) / speed if speed > 0 else 0
        
        # Format sizes
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
        """Upload to PixelDrain"""
        url = "https://pixeldrain.com/api/file"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Basic {self.api_key}'
            
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                file_id = data['id']
                return f"https://pixeldrain.com/u/{file_id}"
        
        return None
    
    async def upload_gofile(self, file_path):
        """Upload to GoFile"""
        # Get server
        server_response = requests.get('https://api.gofile.io/getServer')
        server = server_response.json()['data']['server']
        
        url = f"https://{server}.gofile.io/uploadFile"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if self.api_key:
                data['token'] = self.api_key
            
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'ok':
                    return result['data']['downloadPage']
        
        return None
    
    async def upload_catbox(self, file_path):
        """Upload to Catbox"""
        url = "https://catbox.moe/user/api.php"
        
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {
                'reqtype': 'fileupload',
            }
            if self.api_key:
                data['userhash'] = self.api_key
            
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                return response.text.strip()
        
        return None
    
    async def upload_anonfiles(self, file_path):
        """Upload to AnonFiles"""
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
        """Upload to File.io"""
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
        """Upload file to specified service"""
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
    """Download file from Telegram using userbot"""
    try:
        # Get message
        message = await client.get_messages(file_info['chat_id'], ids=file_info['message_id'])
        
        if not message or not message.media:
            return None
        
        # Get file name
        if hasattr(message.media, 'document'):
            filename = message.file.name or f"file_{SESSION_ID}"
            file_size = message.file.size
        else:
            filename = f"file_{SESSION_ID}"
            file_size = 0
        
        # Update tracker
        progress_tracker.filename = filename
        progress_tracker.total_size = file_size
        
        # Download with progress
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
    """Check if upload was cancelled"""
    cancel_file = Path(f'/tmp/cancel_queue/{SESSION_ID}.cancel')
    return cancel_file.exists()

async def main():
    """Main workflow handler"""
    print(f"Starting upload workflow for session: {SESSION_ID}")
    
    try:
        # Initialize bot
        print("Initializing Telegram bot...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        chat_id = WORKFLOW_DATA['chat_id']
        message_id = WORKFLOW_DATA['message_id']
        files = WORKFLOW_DATA['files']
        
        print(f"Chat ID: {chat_id}")
        print(f"Message ID: {message_id}")
        print(f"Files to process: {len(files)}")
        
        # Initialize Telegram client (userbot) with string session
        print("Initializing Telegram userbot client...")
        client = TelegramClient(
            StringSession(TELEGRAM_STRING_SESSION),
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH
        )
        
        # Connect without interactive login
        print("Connecting to Telegram...")
        await client.connect()
        
        # Check if authorized
        if not await client.is_user_authorized():
            print("❌ String session is invalid or expired!")
            error_text = f"""
❌ <b>Upload Failed</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>

String session tidak valid atau expired.
Silakan generate ulang string session.
"""
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=error_text,
                parse_mode=ParseMode.HTML
            )
            await client.disconnect()
            return
        
        print("✅ Telegram client connected and authorized")
    
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            error_text = f"""
❌ <b>Upload Failed</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>

Initialization error: {str(e)}
"""
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.edit_message_text(
                chat_id=WORKFLOW_DATA['chat_id'],
                message_id=WORKFLOW_DATA['message_id'],
                text=error_text,
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        return
    
    try:
    
    try:
        # Get API key based on service
        api_key = None
        if SERVICE.lower() == 'pixeldrain':
            api_key = PIXELDRAIN_API_KEY
        elif SERVICE.lower() == 'gofile':
            api_key = GOFILE_API_KEY
        elif SERVICE.lower() == 'catbox':
            api_key = CATBOX_USER_HASH
        
        print(f"Service: {SERVICE}")
        print(f"API Key configured: {bool(api_key)}")
        
        uploader = FileUploader(SERVICE, api_key)
        
        uploaded_files = []
        
        for idx, file_info in enumerate(files, 1):
            print(f"\n{'='*50}")
            print(f"Processing file {idx}/{len(files)}")
            print(f"{'='*50}")
            
            # Check cancellation
            if await check_cancellation():
                status_text = f"""
❌ <b>Upload Cancelled</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>
📦 <b>Files processed:</b> {len(uploaded_files)}/{len(files)}

Upload was cancelled by user.
"""
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=status_text,
                    parse_mode=ParseMode.HTML
                )
                break
            
            # Create progress tracker
            progress_tracker = ProgressTracker(
                bot, chat_id, message_id, SESSION_ID, 0, f"File {idx}"
            )
            
            # Download from Telegram
            print(f"Downloading file {idx}/{len(files)}")
            try:
                file_path = await download_from_telegram(client, file_info, progress_tracker)
                
                if not file_path:
                    print(f"Failed to download file {idx}")
                    continue
                
                print(f"✅ Downloaded: {file_path}")
            except Exception as e:
                print(f"❌ Error downloading file {idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # Upload to service
            print(f"Uploading to {SERVICE}")
            
            status_text = f"""
📤 <b>Uploading</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>
📄 <b>File:</b> {file_path.name}
🎯 <b>Service:</b> {SERVICE.upper()}

📊 <b>Progress:</b> [██████████] 100%
⏳ Uploading to {SERVICE}...

File {idx}/{len(files)}
"""
            
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=status_text,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                print(f"Error updating status: {e}")
            
            try:
                upload_url = await uploader.upload(file_path)
                
                if upload_url:
                    uploaded_files.append({
                        'filename': file_path.name,
                        'url': upload_url,
                        'service': SERVICE
                    })
                    print(f"✅ Uploaded: {upload_url}")
                else:
                    print(f"❌ Upload failed for {file_path.name}")
            except Exception as e:
                print(f"❌ Error uploading file {idx}: {e}")
                import traceback
                traceback.print_exc()
            
            # Cleanup
            try:
                file_path.unlink()
                print(f"✅ Cleaned up: {file_path}")
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
        
        # Send final result
        print(f"\n{'='*50}")
        print(f"Upload process completed")
        print(f"Successful uploads: {len(uploaded_files)}/{len(files)}")
        print(f"{'='*50}")
        
        if uploaded_files:
            result_text = f"""
✅ <b>Upload Complete</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>
🎯 <b>Service:</b> {SERVICE.upper()}
📦 <b>Files:</b> {len(uploaded_files)}/{len(files)}

📎 <b>Download Links:</b>

"""
            
            for file in uploaded_files:
                result_text += f"📄 <b>{file['filename']}</b>\n"
                result_text += f"🔗 <code>{file['url']}</code>\n\n"
            
            result_text += "✨ Upload completed successfully!"
            
        else:
            result_text = f"""
❌ <b>Upload Failed</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>
🎯 <b>Service:</b> {SERVICE.upper()}

No files were uploaded successfully.
Check GitHub Actions logs for details.
"""
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result_text,
            parse_mode=ParseMode.HTML
        )
        
        await client.disconnect()
        print("Workflow completed successfully")
        
    except Exception as e:
        print(f"❌ FATAL ERROR in upload process: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            error_text = f"""
❌ <b>Upload Failed</b>

🆔 <b>Session:</b> <code>{SESSION_ID}</code>
🎯 <b>Service:</b> {SERVICE.upper()}

Error: {str(e)[:200]}

Check GitHub Actions logs for full details.
"""
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=error_text,
                parse_mode=ParseMode.HTML
            )
        except Exception as send_error:
            print(f"Could not send error message: {send_error}")
        
        try:
            await client.disconnect()
        except:
            pass

if __name__ == '__main__':
    asyncio.run(main())
