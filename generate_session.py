from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 50)
print("Telegram String Session Generator")
print("=" * 50)

api_id = input("\nEnter your API ID: ")
api_hash = input("Enter your API HASH: ")

print("\nGenerating session...")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    string_session = client.session.save()
    print("\n" + "=" * 50)
    print("STRING SESSION:")
    print("=" * 50)
    print(string_session)
    print("=" * 50)
    print("\nSave this string session safely!")
    print("You'll need it for the bot configuration.")
