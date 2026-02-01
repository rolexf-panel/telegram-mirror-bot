import os
import json
import asyncio
import traceback
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot
from telegram.constants import ParseMode

# --- Load Environment ---
SESSION_ID = os.environ.get('SESSION_ID', 'N/A')
SERVICE = os.environ.get('SERVICE', 'pixeldrain')
WORKFLOW_DATA_RAW = os.environ.get('WORKFLOW_DATA', '{}')

# --- Konfigurasi Directory ---
DOWNLOAD_DIR = Path('downloads')
DOWNLOAD_DIR.mkdir(exist_ok=True)

async def main():
    print(f"--- Memulai Workflow: {SESSION_ID} ---")
    
    # 1. Parsing Data Input
    try:
        data = json.loads(WORKFLOW_DATA_RAW)
        chat_id = data.get('chat_id')
        message_id = data.get('message_id')
        files = data.get('files', [])
    except Exception as e:
        print(f"❌ Error JSON: {e}")
        return

    # 2. Setup Telegram Bot (python-telegram-bot v20+)
    # Kita gunakan 'async with' agar bot otomatis initialize & shutdown
    bot = Bot(token=os.environ.get('TELEGRAM_BOT_TOKEN'))
    
    async with bot:
        print("✅ Bot Telegram terinisialisasi")

        # 3. Setup Telethon (Userbot)
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        string_session = os.environ.get('TELEGRAM_STRING_SESSION')

        if not all([api_id, api_hash, string_session]):
            print("❌ Error: API_ID, API_HASH, atau SESSION kosong di Secrets!")
            return

        client = TelegramClient(StringSession(string_session), int(api_id), api_hash)
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print("❌ Error: String Session tidak valid!")
                return
            
            print("✅ Telethon Client terhubung")

            uploaded_files = []
            
            # 4. Loop Proses File
            for idx, file_info in enumerate(files, 1):
                print(f"🔄 Memproses file {idx}/{len(files)}...")
                
                # Update status di Bot
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"⏳ <b>Downloading file {idx}/{len(files)}...</b>",
                        parse_mode=ParseMode.HTML
                    )
                except: pass

                # Download dari Telegram
                msg = await client.get_messages(file_info['chat_id'], ids=file_info['message_id'])
                if not msg or not msg.media:
                    continue

                filename = msg.file.name or f"file_{idx}"
                file_path = DOWNLOAD_DIR / filename
                
                print(f"📥 Download: {filename}")
                await client.download_media(msg, file=str(file_path))

                # Upload (Contoh ke Pixeldrain)
                print(f"📤 Uploading ke {SERVICE}...")
                # Catatan: Bagian upload bisa kamu masukkan logika FileUploader kamu yang lama
                # Di sini saya persingkat untuk testing
                
                import requests
                url = "https://pixeldrain.com/api/file"
                with open(file_path, 'rb') as f:
                    # Jika ada API Key
                    api_key = os.environ.get('PIXELDRAIN_API_KEY')
                    auth = ('', api_key) if api_key else None
                    r = requests.post(url, files={'file': f}, auth=auth)
                    
                    if r.status_code == 201:
                        res_data = r.json()
                        file_url = f"https://pixeldrain.com/u/{res_data['id']}"
                        uploaded_files.append({"name": filename, "url": file_url})
                        print(f"✅ Berhasil: {file_url}")
                    else:
                        print(f"❌ Gagal upload: {r.text}")

                # Hapus file setelah upload
                if file_path.exists():
                    file_path.unlink()

            # 5. Kirim Hasil Akhir
            if uploaded_files:
                msg_final = f"✅ <b>Mirror Selesai!</b>\n\n"
                for f in uploaded_files:
                    msg_final += f"📄 <code>{f['name']}</code>\n🔗 {f['url']}\n\n"
            else:
                msg_final = "❌ <b>Gagal!</b>\nTidak ada file yang berhasil diupload."

            await bot.edit_message_text(
                chat_id=chat_id, 
                message_id=message_id, 
                text=msg_final, 
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            print(f"❌ Error di dalam loop: {e}")
            traceback.print_exc()
        finally:
            await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
