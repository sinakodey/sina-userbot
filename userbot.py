# userbot_final_working.py
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
import os
import json
import asyncio
from pathlib import Path

# نصب خودکار کتابخونه‌ها
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

try:
    import telethon
except ImportError:
    print("نصب telethon...")
    install('telethon')

try:
    import google.generativeai as genai
except ImportError:
    print("نصب google-generativeai...")
    install('google-generativeai')

try:
    import nest_asyncio
    nest_asyncio.apply()
except Exception:
    pass

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeFilename

# ---------- تنظیمات اولیه ----------
API_ID = 23006689
API_HASH = 'e72b3e1a3ff9d2d0d1458ffecac1745c'

# 🔴 سشن جدید اینجا قرار بگیره
SESSION_STRING = "1BJWap1sBuz9N5WpXH9IDWrdAyP-UsETri-53On0sh_E8PzPXTquFd75FKuzGRZ6EXw3OEZQRQdfvqJn7-m8GZ1cK10_6Nn6Yz1zcbq9INBsnpKFlM5VP4Kwz-oIsRZt0lQgQLTvB2_ogoCta_gaS0aCHLnMuyaONml4dlxY20hF0y-RsRKjaJAA7KZYAHUwES4A2ocH5ZrDXQrRa58mSi-E5hR5lxTNCvvsz4Bj_JwqhYXsOWT77puAG8ARpuedHnlnnWu4d9Kl49JM-p4zZ7huDGGeg7Qlqnl6R-K1ndaDT4zYtdBDQKbNwQW6gNPQQ9bSANcayfR1u2qnfgfyMXGdCfeC3cRw="

# کانال مقصد
TARGET_CHANNEL_ID = -1001908794408

# کاربران پیش‌فرض فعال
DEFAULT_ACTIVE_USERS = {'6701288219', '1864596769'}

GOOGLE_API_KEY_1 = "AIzaSyBJB9JAxgGvTPT-bAqnbMFfpcw-RwBExXg"
GOOGLE_API_KEY_2 = "AIzaSyCbjWf8Wel59bgUD0a0T3WZNkH9lIS3LF0"

CURRENT_API_KEY = GOOGLE_API_KEY_1
genai.configure(api_key=CURRENT_API_KEY)

# ایجاد کلاینت
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# فایل‌های ذخیره سازی
ACTIVE_USERS_FILE = 'active_users.json'
MEDIA_CACHE_DIR = 'media_cache'
Path(MEDIA_CACHE_DIR).mkdir(exist_ok=True)

# ---------- توابع کمکی ----------
def get_iran_time():
    """دریافت زمان ایران (UTC+3:30)"""
    utc_now = datetime.now(timezone.utc)
    iran_time = utc_now + timedelta(hours=3, minutes=30)
    return iran_time

def load_active_users():
    default_users = DEFAULT_ACTIVE_USERS
    if os.path.exists(ACTIVE_USERS_FILE):
        try:
            with open(ACTIVE_USERS_FILE, 'r', encoding='utf-8') as f:
                saved_users = set(json.load(f))
                return default_users.union(saved_users)
        except Exception:
            return default_users
    return default_users

def save_active_users(users):
    users_to_save = users - DEFAULT_ACTIVE_USERS
    with open(ACTIVE_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(users_to_save), f)

def switch_api_key():
    global CURRENT_API_KEY
    if CURRENT_API_KEY == GOOGLE_API_KEY_1:
        CURRENT_API_KEY = GOOGLE_API_KEY_2
    else:
        CURRENT_API_KEY = GOOGLE_API_KEY_1
    genai.configure(api_key=CURRENT_API_KEY)
    print(f"API Key تغییر کرد به: {CURRENT_API_KEY[:10]}...")

def sanitize_no_corporate_mentions(text: str) -> str:
    if not text:
        return text
    banned = ['گوگل', 'Google', 'Gemini', 'gemini', 'google']
    for b in banned:
        text = text.replace(b, '')
    return text.replace('  ', ' ').strip()

def persona_final_reply(original_message: str, ai_generated: str) -> str:
    text = (original_message or "").strip().lower()

    who_queries = ['کی هستی', 'تو کی هستی', 'who are you', 'who r u']
    maker_queries = ['کی ساختت', 'کی ساختت؟', 'خالق کیه', 'کی ساخته ات', 'who made you', 'who created you']

    for q in who_queries:
        if q in text:
            return "من محمدسینا ساکی‌ام؛ محقق و پژوهشگری که هدفش روشن کردن راه حق و بیداری دل‌هاست."

    for q in maker_queries:
        if q in text:
            return "ارباب سینا مرا آفرید — انسانی مؤمن و پیگیر که خواست انگیزه و آگاهی را میان آدم‌ها گسترش دهد."

    safe = sanitize_no_corporate_mentions(ai_generated or "")
    if not safe:
        safe = "سلام؛ من اینجام تا کمک کنم. بپرس هر چی می‌خوای دربارهٔ رشد، عزم و مسیر آدمی — با دل و ایمان."

    return f"{safe}\n\n— محمدسینا ساکی (پاسخگر معنوی و راستگو)."

async def is_allowed_chat(event):
    try:
        if event.is_private:
            return True
        chat = await event.get_chat()
        if hasattr(chat, 'username') and chat.username and 'tajroby113' in chat.username.lower():
            return True
        if hasattr(chat, 'title') and chat.title and 'tajroby113' in chat.title.lower():
            return True
        return False
    except Exception:
        return False

async def get_user_info(event):
    try:
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'username', '') or 'نامشخص'
        sender_username = getattr(sender, 'username', '') or 'بدون یوزرنیم'
        sender_id = getattr(sender, 'id', 'نامشخص')
        
        return {
            'name': sender_name,
            'username': sender_username,
            'id': sender_id
        }
    except Exception:
        return {'name': 'نامشخص', 'username': 'نامشخص', 'id': 'نامشخص'}

async def download_and_send_media(event, user_info, action_type):
    try:
        if not event.message.media:
            return False
            
        media_path = await event.message.download_media(file=MEDIA_CACHE_DIR)
        if not media_path:
            return False
        
        media_type = "فایل"
        if isinstance(event.message.media, MessageMediaPhoto):
            media_type = "عکس"
        elif isinstance(event.message.media, MessageMediaDocument):
            doc = event.message.media.document
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    if file_name:
                        if any(ext in file_name.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv']):
                            media_type = "ویدیو"
                        elif any(ext in file_name.lower() for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                            media_type = "صدا"
        
        iran_time = get_iran_time().strftime('%H:%M:%S %Y/%m/%d')
        
        caption = (
            f"🔹 {action_type} ({media_type})\n"
            f"👤 کاربر: {user_info['name']}\n"
            f"📱 یوزرنیم: @{user_info['username']}\n"
            f"🆔 ID: {user_info['id']}\n"
            f"⏰ زمان: {iran_time}\n"
            f"💬 چت ID: {event.chat_id}"
        )
        
        await client.send_file(TARGET_CHANNEL_ID, media_path, caption=caption)
        print(f"✅ {media_type} زماندار ارسال شد")
        return True
        
    except Exception as e:
        print(f"❌ خطا در ارسال رسانه: {e}")
        return False

async def forward_to_channel(event, user_info, action_type="پیام جدید"):
    try:
        iran_time = get_iran_time().strftime('%H:%M:%S %Y/%m/%d')
        
        if event.message.media:
            # برای پیام‌های زماندار
            success = await download_and_send_media(event, user_info, action_type)
            if not success:
                # اگر ارسال مستقیم شکست خورد، فوروارد کن
                try:
                    await event.message.forward_to(TARGET_CHANNEL_ID)
                    caption = f"🔹 {action_type}\n👤 {user_info['name']}\n⏰ {iran_time}"
                    await client.send_message(TARGET_CHANNEL_ID, caption)
                    print(f"✅ پیام رسانه‌ای فوروارد شد: {action_type}")
                except Exception as e:
                    print(f"❌ خطا در فوروارد رسانه: {e}")
        else:
            # برای پیام‌های متنی
            await event.message.forward_to(TARGET_CHANNEL_ID)
            caption = (
                f"🔹 {action_type}\n"
                f"👤 کاربر: {user_info['name']}\n"
                f"📱 یوزرنیم: @{user_info['username']}\n"
                f"⏰ زمان: {iran_time}"
            )
            await client.send_message(TARGET_CHANNEL_ID, caption)
            print(f"✅ پیام متنی فوروارد شد: {action_type}")
            
        return True
        
    except Exception as e:
        print(f"❌ خطا در فوروارد: {e}")
        return False

# ---------- هندلرها ----------
@client.on(events.NewMessage)
async def handle_new_message(event):
    if not await is_allowed_chat(event):
        return
    
    print(f"📩 پیام جدید در چت: {event.chat_id}")
    user_info = await get_user_info(event)
    await forward_to_channel(event, user_info, "پیام جدید")

@client.on(events.MessageEdited)
async def handle_edited_message(event):
    if not await is_allowed_chat(event):
        return
    
    print(f"✏️ پیام ادیت شده در چت: {event.chat_id}")
    user_info = await get_user_info(event)
    await forward_to_channel(event, user_info, "پیام ویرایش شده")

@client.on(events.NewMessage(chats='me'))
async def handler(event):
    text = (event.message.message or "").strip()
    users = load_active_users()
    
    try:
        if text.lower().startswith('هوش @'):
            username = text.split('@', 1)[1].split()[0].lower()
            if username not in {u.lower() for u in DEFAULT_ACTIVE_USERS}:
                users.add(username)
                save_active_users(users)
                await event.reply(f"هوش برای @{username} فعال شد.")
            else:
                await event.reply(f"@{username} از کاربران پیش‌فرض است.")
                
        elif text.lower().startswith('خاموش @'):
            username = text.split('@', 1)[1].split()[0].lower()
            if username not in {u.lower() for u in DEFAULT_ACTIVE_USERS}:
                if username in {u.lower() for u in users}:
                    users = {u for u in users if u.lower() != username}
                    save_active_users(users)
                    await event.reply(f"هوش برای @{username} خاموش شد.")
                else:
                    await event.reply(f"@{username} فعال نبود.")
            else:
                await event.reply(f"@{username} از کاربران پیش‌فرض است و غیرفعال نمی‌شود.")
                
        elif text.lower() == 'لیست کاربران':
            active_users = load_active_users()
            default_users = DEFAULT_ACTIVE_USERS
            custom_users = active_users - default_users
            
            response = "👥 کاربران فعال:\n\n"
            response += "🔹 کاربران پیش‌فرض (همیشه فعال):\n"
            for user in default_users:
                response += f"• {user}\n"
            
            response += "\n🔸 کاربران دستی:\n"
            for user in custom_users:
                response += f"• {user}\n"
                
            await event.reply(response)
                
    except Exception as e:
        await event.reply(f"ارور: {e}")

@client.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    if not event.is_private:
        return

    try:
        sender = await event.get_sender()
    except Exception:
        return

    user_id = str(getattr(sender, 'id', ''))
    username = getattr(sender, 'username', '').lower()
    active_users = load_active_users()
    
    is_active = (user_id in active_users) or (username in {u.lower() for u in active_users})
    
    if not is_active:
        return

    original_text = (event.message.message or event.message.text or "").strip()
    normalized = original_text.lower()

    who_triggers = ['کی هستی', 'تو کی هستی', 'who are you', 'who r u']
    maker_triggers = ['کی ساختت', 'خالق کیه', 'who made you', 'who created you']

    for t in who_triggers:
        if t in normalized:
            await event.reply("من محمدسینا ساکی‌ام؛ محقق و پژوهشگری که با ایمان و تلاش سعی دارد راه روشن‌تری برای آدم‌ها بسازد. خوش اومدی؛ هر چی خواستی بپرس.")
            await client.send_message('me', f"پاسخ ثابت 'کی هستی' به {user_id} ارسال شد.")
            return

    for t in maker_triggers:
        if t in normalized:
            await event.reply("ارباب سینا مرا آفرید — انسانی مؤمن که خواست ابزار کوچکی برای بیداری و رشد دل‌ها فراهم کند.")
            await client.send_message('me', f"پاسخ ثابت 'کی ساختت' به {user_id} ارسال شد.")
            return

    ai_text = ""
    for attempt in range(2):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"Be concise and helpful. User asked (in Persian): {original_text}\nRespond in Persian."
            response = model.generate_content(prompt)
            ai_text = getattr(response, 'text', '') or ''
            break
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print("ارور 429 - تعویض API Key...")
                switch_api_key()
                continue
            else:
                print(f"خطا در تماس با AI: {e}")
                ai_text = ""

    final = persona_final_reply(original_text, ai_text)
    await event.reply(final)
    await client.send_message('me', f"پاسخ به {user_id}: {final[:120]}...")

async def update_bio_clock():
    while True:
        try:
            iran_time = get_iran_time().strftime("%H:%M")
            bio_text = f"ساعت: {iran_time} | Userbot فعال"
            await client(UpdateProfileRequest(about=bio_text))
            print(f"🕒 بیو آپدیت شد: {bio_text}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"ارور آپدیت بیو: {e}")
            await asyncio.sleep(60)

async def main():
    await client.start()
    print("✅ Userbot در حال اجراست...")
    print(f"🎯 ارسال پیام‌ها به کانال: {TARGET_CHANNEL_ID}")
    print(f"👥 کاربران پیش‌فرض فعال: {DEFAULT_ACTIVE_USERS}")
    
    # بررسی وضعیت کانال
    try:
        channel_entity = await client.get_entity(TARGET_CHANNEL_ID)
        print(f"✅ کانال پیدا شد: {getattr(channel_entity, 'title', 'Unknown')}")
    except Exception as e:
        print(f"⚠️  توجه به کانال: {e}")
        print("مطمئن شوید اکانت به کانال دسترسی دارد")
    
    await asyncio.gather(
        client.run_until_disconnected(),
        update_bio_clock()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("در حال خاموش شدن...")