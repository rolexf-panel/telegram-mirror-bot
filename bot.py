import os
import json
import asyncio
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GH_PAT = os.environ.get('GH_PAT')
GITHUB_REPO = os.environ.get('GITHUB_REPO')  # format: username/repo
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS', '').split(',')

# File upload sessions
upload_sessions = {}

async def animate_loading(chat_id: int, message_id: int, session_id: str, service: str, file_count: int, context):
    """Animate loading dots while initializing"""
    from telegram import Bot
    
    bot = context.bot
    dots_states = [".", "..", "..."]
    counter = 0
    max_updates = 60  # Max 60 updates (about 1 minute)
    
    try:
        while counter < max_updates:
            # Check if session still exists and is processing
            if session_id not in upload_sessions:
                break
            
            if upload_sessions[session_id]['status'] != 'processing':
                break
            
            dots = dots_states[counter % 3]
            
            status_text = f"""
🚀 <b>Upload Dimulai!</b>

🆔 <b>Session:</b> <code>{session_id}</code>
🎯 <b>Service:</b> {service.upper()}
📦 <b>Files:</b> {file_count}

⏳ <b>Status:</b> Initializing{dots}
📊 <b>Progress:</b> [░░░░░░░░░░] 0%

🔄 GitHub Actions sedang memproses request...
⚡ Menunggu workflow dimulai{dots}

💡 Cancel: <code>/cancel_{session_id}</code>
"""
            
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=status_text,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                # Ignore telegram errors (rate limit, message not modified, etc)
                pass
            
            await asyncio.sleep(1)  # Update every 1 second
            counter += 1
            
    except Exception as e:
        print(f"Error in loading animation: {e}")

def generate_file_id():
    """Generate unique file ID"""
    return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:8]

def parse_message_link(link: str):
    """Parse Telegram message link to get chat_id and message_id"""
    try:
        parts = link.rstrip('/').split('/')
        if '/c/' in link:
            chat_id = -int('100' + parts[-2])
            message_id = int(parts[-1])
        else:
            chat_id = '@' + parts[-2]
            message_id = int(parts[-1])
        return chat_id, message_id
    except:
        return None, None

def trigger_github_workflow(session_id: str, service: str, workflow_data: dict):
    """Trigger GitHub Actions workflow via API"""
    if not GH_PAT or not GITHUB_REPO:
        print("GitHub credentials not configured")
        print(f"GH_PAT exists: {bool(GH_PAT)}")
        print(f"GITHUB_REPO: {GITHUB_REPO}")
        return False
    
    # Get default branch
    repo_url = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {GH_PAT}',
        'Content-Type': 'application/json'
    }
    
    try:
        repo_response = requests.get(repo_url, headers=headers)
        if repo_response.status_code == 200:
            default_branch = repo_response.json().get('default_branch', 'main')
            print(f"✅ Detected default branch: {default_branch}")
        else:
            # Fallback: try both main and master
            default_branch = 'main'
            print(f"⚠️ Could not detect branch, using: {default_branch}")
    except:
        default_branch = 'main'
        print(f"⚠️ Error detecting branch, using: {default_branch}")
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/upload.yml/dispatches"
    
    payload = {
        'ref': default_branch,
        'inputs': {
            'session_id': session_id,
            'service': service,
            'workflow_data': json.dumps(workflow_data)
        }
    }
    
    try:
        print(f"🔄 Triggering workflow at: {url}")
        print(f"📦 Branch: {default_branch}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 204:
            print("✅ Workflow triggered successfully!")
            return True
        elif response.status_code == 422 and default_branch == 'main':
            # Try with master branch
            print("⚠️ Trying with 'master' branch...")
            payload['ref'] = 'master'
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 204:
                print("✅ Workflow triggered successfully with 'master' branch!")
                return True
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"Error: {response.text}")
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering workflow: {e}")
        import traceback
        traceback.print_exc()
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = str(update.effective_user.id)
    
    if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Kamu tidak diizinkan menggunakan bot ini.")
        return
    
    welcome_text = """
🤖 <b>File Upload Bot</b>

<b>📤 Commands Yang Tersedia:</b>
• /pixeldrain - Upload ke PixelDrain
• /gofile - Upload ke GoFile  
• /catbox - Upload ke Catbox
• /anonfiles - Upload ke AnonFiles
• /fileio - Upload ke File.io
• /status - Lihat sesi aktif
• /help - Bantuan

<b>📝 Cara Penggunaan:</b>
1. Reply ke file: <code>/pixeldrain</code>
2. Atau dengan link: <code>/pixeldrain https://t.me/c/...</code>

<b>✨ Fitur:</b>
✅ Multi-file upload
✅ Real-time progress tracking
✅ Support file besar (via userbot)
✅ Cancel kapan saja: <code>/cancel_[id]</code>

💡 <b>Tips:</b> Bot ini menggunakan GitHub Actions untuk processing, jadi upload akan tetap berjalan meskipun bot offline!

Made with ❤️
"""
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """
📖 <b>Panduan Penggunaan</b>

<b>1️⃣ Upload File Biasa:</b>
• Reply ke file dengan command
• Contoh: <code>/pixeldrain</code> (reply ke file)

<b>2️⃣ Upload Dari Link Telegram:</b>
• Copy link pesan yang berisi file
• Gunakan: <code>/pixeldrain https://t.me/c/1234/567</code>

<b>3️⃣ Cek Status Upload:</b>
• Ketik: <code>/status</code>

<b>4️⃣ Cancel Upload:</b>
• Ketik: <code>/cancel_[session_id]</code>
• Session ID ada di pesan konfirmasi

<b>⚙️ Services:</b>
• PixelDrain - Fast, reliable
• GoFile - Unlimited storage
• Catbox - Simple, no registration
• AnonFiles - Anonymous upload
• File.io - One-time download

<b>⚠️ Catatan:</b>
• Progress update setiap 5 detik
• File besar butuh waktu lebih lama
• Gunakan /status untuk cek semua upload
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def handle_upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str):
    """Handle file upload commands"""
    user_id = str(update.effective_user.id)
    
    if AUTHORIZED_USERS and user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ Kamu tidak diizinkan menggunakan bot ini.")
        return
    
    message = update.message
    files_to_upload = []
    
    # Check if replying to a message with file
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        
        if replied_msg.document:
            files_to_upload.append({
                'type': 'document',
                'file_id': replied_msg.document.file_id,
                'file_name': replied_msg.document.file_name,
                'file_size': replied_msg.document.file_size,
                'message_id': replied_msg.message_id,
                'chat_id': replied_msg.chat_id
            })
        elif replied_msg.photo:
            photo = replied_msg.photo[-1]
            files_to_upload.append({
                'type': 'photo',
                'file_id': photo.file_id,
                'file_name': f'photo_{photo.file_unique_id}.jpg',
                'file_size': photo.file_size,
                'message_id': replied_msg.message_id,
                'chat_id': replied_msg.chat_id
            })
        elif replied_msg.video:
            files_to_upload.append({
                'type': 'video',
                'file_id': replied_msg.video.file_id,
                'file_name': replied_msg.video.file_name or f'video_{replied_msg.video.file_unique_id}.mp4',
                'file_size': replied_msg.video.file_size,
                'message_id': replied_msg.message_id,
                'chat_id': replied_msg.chat_id
            })
        elif replied_msg.audio:
            files_to_upload.append({
                'type': 'audio',
                'file_id': replied_msg.audio.file_id,
                'file_name': replied_msg.audio.file_name or f'audio_{replied_msg.audio.file_unique_id}.mp3',
                'file_size': replied_msg.audio.file_size,
                'message_id': replied_msg.message_id,
                'chat_id': replied_msg.chat_id
            })
    
    # Check if message link provided
    elif context.args:
        link = context.args[0]
        chat_id, message_id = parse_message_link(link)
        
        if chat_id and message_id:
            files_to_upload.append({
                'type': 'link',
                'chat_id': chat_id,
                'message_id': message_id
            })
        else:
            await message.reply_text(
                f"❌ <b>Link Telegram tidak valid!</b>\n\n"
                f"<b>Format yang benar:</b>\n"
                f"<code>/{service} https://t.me/c/1234567890/123</code>",
                parse_mode=ParseMode.HTML
            )
            return
    else:
        await message.reply_text(
            f"❌ <b>Cara penggunaan salah!</b>\n\n"
            f"<b>Opsi 1:</b> Reply ke file\n"
            f"<code>/{service}</code> (reply ke file)\n\n"
            f"<b>Opsi 2:</b> Gunakan link Telegram\n"
            f"<code>/{service} https://t.me/c/...</code>\n\n"
            f"Ketik /help untuk panduan lengkap.",
            parse_mode=ParseMode.HTML
        )
        return
    
    if not files_to_upload:
        await message.reply_text("❌ File tidak ditemukan!")
        return
    
    # Generate unique session ID
    session_id = generate_file_id()
    
    # Create upload session
    upload_sessions[session_id] = {
        'user_id': user_id,
        'service': service,
        'files': files_to_upload,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    # Get file info for display
    if files_to_upload[0].get('file_name'):
        file_display = files_to_upload[0]['file_name']
        size_mb = files_to_upload[0].get('file_size', 0) / (1024 * 1024)
        size_info = f"💾 <b>Ukuran:</b> {size_mb:.2f} MB\n"
    else:
        file_display = "File dari link Telegram"
        size_info = ""
    
    # Send confirmation message
    keyboard = [
        [
            InlineKeyboardButton("✅ Mulai Upload", callback_data=f"confirm_{session_id}"),
            InlineKeyboardButton("❌ Batal", callback_data=f"cancel_{session_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_text = f"""
📤 <b>Konfirmasi Upload</b>

🆔 <b>Session ID:</b> <code>{session_id}</code>
🎯 <b>Service:</b> {service.upper()}
📦 <b>Jumlah File:</b> {len(files_to_upload)}
📄 <b>File:</b> {file_display}
{size_info}
⏰ <b>Waktu:</b> {datetime.now().strftime('%H:%M:%S')}

⚡ Tekan tombol untuk melanjutkan.
💡 Cancel: <code>/cancel_{session_id}</code>
"""
    
    await message.reply_text(status_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, session_id = data.split('_', 1)
    
    if session_id not in upload_sessions:
        await query.edit_message_text("❌ Session expired atau tidak ditemukan!")
        return
    
    session = upload_sessions[session_id]
    user_id = str(update.effective_user.id)
    
    if session['user_id'] != user_id:
        await query.answer("❌ Ini bukan sesi upload kamu!", show_alert=True)
        return
    
    if action == 'confirm':
        session['status'] = 'processing'
        
        # Prepare workflow data
        workflow_data = {
            'session_id': session_id,
            'service': session['service'],
            'files': session['files'],
            'user_id': user_id,
            'chat_id': query.message.chat_id,
            'message_id': query.message.message_id
        }
        
        # Show initial status
        status_text = f"""
🚀 <b>Upload Dimulai!</b>

🆔 <b>Session:</b> <code>{session_id}</code>
🎯 <b>Service:</b> {session['service'].upper()}
📦 <b>Files:</b> {len(session['files'])}

⏳ <b>Status:</b> Initializing.
📊 <b>Progress:</b> [░░░░░░░░░░] 0%

🔄 GitHub Actions sedang memproses request...

💡 Cancel: <code>/cancel_{session_id}</code>
"""
        
        await query.edit_message_text(status_text, parse_mode=ParseMode.HTML)
        
        # Trigger GitHub Actions
        success = trigger_github_workflow(session_id, session['service'], workflow_data)
        
        if success:
            # Start loading animation
            asyncio.create_task(animate_loading(
                query.message.chat_id,
                query.message.message_id,
                session_id,
                session['service'],
                len(session['files']),
                context
            ))
        else:
            status_text = f"""
❌ <b>Gagal Memulai Upload</b>

🆔 <b>Session:</b> <code>{session_id}</code>

GitHub Actions gagal di-trigger.
Silakan coba lagi atau hubungi admin.
"""
            await query.edit_message_text(status_text, parse_mode=ParseMode.HTML)
        
    elif action == 'cancel':
        del upload_sessions[session_id]
        await query.edit_message_text(
            f"❌ <b>Upload Dibatalkan</b>\n\n"
            f"🆔 Session: <code>{session_id}</code>\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}",
            parse_mode=ParseMode.HTML
        )

async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel an upload session"""
    message_text = update.message.text
    session_id = message_text.replace('/cancel_', '').strip()
    
    if not session_id:
        await update.message.reply_text(
            "❌ <b>Format salah!</b>\n\n"
            "Gunakan: <code>/cancel_[session_id]</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    if session_id not in upload_sessions:
        await update.message.reply_text(
            f"❌ Session <code>{session_id}</code> tidak ditemukan!\n\n"
            f"Gunakan /status untuk melihat sesi aktif.",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = str(update.effective_user.id)
    session = upload_sessions[session_id]
    
    if session['user_id'] != user_id:
        await update.message.reply_text("❌ Kamu hanya bisa cancel upload milikmu sendiri!")
        return
    
    # Create cancellation signal
    os.makedirs('/tmp/cancel_queue', exist_ok=True)
    with open(f'/tmp/cancel_queue/{session_id}.cancel', 'w') as f:
        f.write(datetime.now().isoformat())
    
    del upload_sessions[session_id]
    
    await update.message.reply_text(
        f"✅ <b>Upload Dibatalkan</b>\n\n"
        f"🆔 Session: <code>{session_id}</code>\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"GitHub Actions akan menghentikan proses.",
        parse_mode=ParseMode.HTML
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active upload sessions"""
    user_id = str(update.effective_user.id)
    
    user_sessions = {k: v for k, v in upload_sessions.items() if v['user_id'] == user_id}
    
    if not user_sessions:
        await update.message.reply_text(
            "📭 <b>Tidak Ada Sesi Aktif</b>\n\n"
            "Kamu belum memiliki upload yang sedang berjalan.\n"
            "Gunakan /help untuk melihat cara upload.",
            parse_mode=ParseMode.HTML
        )
        return
    
    status_text = "📊 <b>Sesi Upload Aktif</b>\n\n"
    
    for session_id, session in user_sessions.items():
        created = datetime.fromisoformat(session['created_at'])
        elapsed = (datetime.now() - created).seconds
        
        status_icon = {
            'pending': '⏸',
            'processing': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(session['status'], '❓')
        
        status_text += f"""
{status_icon} <code>{session_id}</code>
🎯 Service: {session['service'].upper()}
📦 Files: {len(session['files'])}
⏱ Status: {session['status']}
⏰ Elapsed: {elapsed}s
━━━━━━━━━━━━━━
"""
    
    status_text += f"\n💡 Cancel: <code>/cancel_[session_id]</code>"
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)

def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN tidak ditemukan!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Upload service handlers
    services = ['pixeldrain', 'gofile', 'catbox', 'anonfiles', 'fileio']
    for service in services:
        application.add_handler(
            CommandHandler(service, lambda u, c, s=service: handle_upload_command(u, c, s))
        )
    
    # Cancel handler
    application.add_handler(
        MessageHandler(filters.Regex(r'^/cancel_[a-f0-9]{8}'), cancel_upload)
    )
    
    # Button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    print("🤖 Bot started!")
    print(f"📝 Authorized users: {AUTHORIZED_USERS}")
    print(f"🔧 GitHub Repo: {GITHUB_REPO}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
