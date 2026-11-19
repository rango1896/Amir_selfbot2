import asyncio
import random
import json
import os
from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from flask import Flask
import threading

# ================= تنظیمات اکانت اصلی (خودت) =================
API_ID = 17349
API_HASH = "344583e45741c457fe1862106095a5eb"
MASTER_SESSION = "1AZWarzwBuzqZoUfmXGW56eumhA2hG6yn_LNVH4Trw3iBRdAhYIVQqwF3e6wVJNLjzZfshSVnXSWrs0-8dZw2tYciZwZKCfxN3ZIObGaVzqm8hfOwfY-RFFKfbu1bWPtX0ZdC05a98jjC6-QoIT1142Idk5uT6IBLyT6wPT5BvNMi_PtBHSIPKEzknagaJTngntZJaynwUxoPuZiLr_ZFQrMKoIBvaL-UQCdGTwAMgkPCXn6hsg0qvJeo19xuXuuQZnbAjRUHM1cj0SIamBRt5rEwjjVE1VZhIUHWy6q9H5OQ79FOo0tO5fi46Lyb3MiBIBrVFnjOlejEOjU91RdC6SvDUk4txNE="
# ==========================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "ربات واکنش چندگانه زنده است! 🚀"

def run_web():
    app.run(host='0.0.0.0', port=8080)

master_client = TelegramClient(StringSession(MASTER_SESSION), API_ID, API_HASH)

worker_sessions = []
if os.path.exists('accounts.json'):
    with open('accounts.json', 'r') as f:
        worker_sessions = json.load(f)

worker_clients = [TelegramClient(StringSession(s), API_ID, API_HASH) for s in worker_sessions]
active_reactions = {}

def clean_target_string(target_str):
    if "t.me/" in target_str:
        parts = target_str.split("t.me/")[-1].split("/")
        if parts[0]: return parts[0]
    return target_str.replace("@", "")

# هندلر دستورات (فقط پیام‌هایی که خودت می‌فرستی رو می‌خونه)
@master_client.on(events.NewMessage(outgoing=True, pattern=r'^واکنش\s+([0-9۰-۹]+|مختلف)\s+(\S+)\s+(.+)$'))
async def add_react(event):
    count_str = event.pattern_match.group(1)
    target_str = event.pattern_match.group(2)
    emojis_str = event.pattern_match.group(3)
    
    emojis = emojis_str.split()
    clean_target = clean_target_string(target_str)
    
    try:
        ent = await master_client.get_entity(clean_target)
        chat_id = utils.get_peer_id(ent)
        
        if count_str == "مختلف":
            count = "all"
        else:
            count = int(count_str)
            
        active_reactions[chat_id] = {"count": count, "emojis": emojis}
        await event.reply(f"✅ واکنش تنظیم شد.\nچنل: `{clean_target}`\nتعداد: {count_str}\nایموجی‌ها: {' '.join(emojis)}")
    except Exception as e:
        print(f"خطا در ثبت: {e}")
        await event.reply(f"❗ چنل پیدا نشد. ارور: {e}")

@master_client.on(events.NewMessage(outgoing=True, pattern=r'^حذف واکنش\s+(\S+)$'))
async def rem_react(event):
    target_str = event.pattern_match.group(1).strip()
    clean_target = clean_target_string(target_str)
    try:
        ent = await master_client.get_entity(clean_target)
        chat_id = utils.get_peer_id(ent)
        
        if chat_id in active_reactions:
            del active_reactions[chat_id]
            await event.reply(f"❌ واکنش برای `{clean_target}` پاک شد.")
        else:
            await event.reply("❗ این چنل تو لیست واکنش‌ها نیست.")
    except:
        await event.reply("❗ پیدا نشد.")

# هندلر واکنش خودکار
@master_client.on(events.NewMessage())
async def auto_react_handler(event):
    chat_id = event.chat_id
    if chat_id in active_reactions:
        config = active_reactions[chat_id]
        count = config["count"]
        emojis = config["emojis"]
        
        # واکنش اکانت اصلی
        emoji = random.choice(emojis)
        try:
            reaction = [ReactionEmoji(emoticon=emoji)]
            await master_client(SendReactionRequest(peer=chat_id, msg_id=event.id, reaction=reaction))
            print(f"✅ اکانت اصلی واکنش {emoji} گذاشت.")
        except Exception as e:
            print(f"❌ خطا اکانت اصلی: {e}")
        
        # واکنش سنیورها
        if count != 1:
            workers_to_use = worker_clients if count == "all" else worker_clients[:count-1]
            
            for w_client in workers_to_use:
                await asyncio.sleep(random.randint(1, 3))
                try:
                    emoji = random.choice(emojis)
                    reaction = [ReactionEmoji(emoticon=emoji)]
                    await w_client(SendReactionRequest(peer=chat_id, msg_id=event.id, reaction=reaction))
                    print(f"✅ یه سنیور واکنش {emoji} گذاشت.")
                except Exception as e:
                    print(f"❌ خطا سنیور: {e}")

async def start_workers():
    for i, w_client in enumerate(worker_clients):
        try:
            await w_client.connect()
            if await w_client.is_user_authorized():
                print(f"✅ سنیور شماره {i+1} وصل شد.")
            else:
                print(f"❌ سنیور شماره {i+1} لاگین نیست!")
        except Exception as e:
            print(f"❌ خطا در اتصال سنیور {i+1}: {e}")

async def main():
    await master_client.start()
    me = await master_client.get_me()
    print(f"✅ ربات روشن شد! وارد اکانت {me.first_name} شدیم.")
    await start_workers()
    print("در حال شنود پیام‌های چنل‌ها...")
    await master_client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    with master_client:
        master_client.loop.run_until_complete(main())
