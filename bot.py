import os
import random
import time
import telebot
import asyncio
from telethon import TelegramClient

# === CONFIG from ENV ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))         # my.telegram.org से लो
API_HASH = os.getenv("API_HASH", "")          # my.telegram.org से लो
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BUFFER_CHANNEL_ID = -1002963301599            # आपका video channel
PHOTO_URL = os.getenv("PHOTO_URL", "https://envs.sh/hA0.jpg")
FORCE_JOIN_IDS = [-1002547586103]

# Files
USERS_FILE = "users.txt"
REFERRALS_FILE = "referrals.txt"
POINTS_FILE = "user_points.txt"

PRIVACY_MESSAGE = """Privacy Policy for 18+ Bots

1️⃣ Age Restriction: 18+ only
2️⃣ No Personal Data Collection
3️⃣ User Responsibility
...
🔟 Policy Changes can occur without notice.
"""

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# === Ensure required files exist ===
for file in [USERS_FILE, REFERRALS_FILE, POINTS_FILE]:
    if not os.path.exists(file):
        open(file, "w").close()

# --- Utility functions ---
def read_lines(path):
    with open(path, "r") as f:
        return [line.strip() for line in f.read().splitlines() if line.strip()]

def append_line(path, line):
    with open(path, "a") as f:
        f.write(str(line) + "\n")

# === Save New Users ===
def save_user(user_id, referred_by=None):
    users = read_lines(USERS_FILE)
    if str(user_id) not in users:
        append_line(USERS_FILE, user_id)
        try:
            bot.send_message(ADMIN_ID, f"👤 New user: {user_id}\n📊 Total users: {len(users)+1}")
        except Exception:
            pass
        if referred_by:
            save_referral(user_id, referred_by)

# === Save Referrals ===
def save_referral(user_id, referred_by):
    append_line(REFERRALS_FILE, f"{user_id} referred_by {referred_by}")
    update_points(referred_by)

# === Update Points ===
def update_points(referred_by):
    points = {}
    for line in read_lines(POINTS_FILE):
        parts = line.split()
        if len(parts) == 2:
            points[parts[0]] = int(parts[1])
    points[str(referred_by)] = points.get(str(referred_by), 0) + 10
    with open(POINTS_FILE, "w") as f:
        for uid, pts in points.items():
            f.write(f"{uid} {pts}\n")

# === /start handler ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    referred_by = None
    if message.text and 'ref=' in message.text:
        try:
            referred_by = message.text.split('ref=')[1]
        except:
            referred_by = None

    save_user(user_id, referred_by)

    referral_link = f"https://t.me/{bot.get_me().username}?start=ref={user_id}"

    caption = (
        f"🥵 *Welcome to Pom Hub* 🙈!\n"
        f"Here you'll get the most unseen videos.\n\n"
        f"📢 *Join required channels to continue:*\n\n"
        f"💥 *Refer friends to earn rewards!*\nYour referral link:\n`{referral_link}`"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📣 Join Channel 1", url="https://t.me/promoters_botse"))
    markup.add(telebot.types.InlineKeyboardButton("📣 Join Channel 2", url="https://t.me/+DDOMcEbYh8RiZWFl"))
    markup.add(telebot.types.InlineKeyboardButton("✅ Joined Channels", callback_data="check_join"))

    try:
        bot.send_photo(user_id, PHOTO_URL, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except Exception:
        bot.send_message(user_id, caption, reply_markup=markup)

# === Callback handler ===
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id

    if call.data == "check_join":
        not_joined = []
        for channel in FORCE_JOIN_IDS:
            try:
                member = bot.get_chat_member(channel, user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    not_joined.append(channel)
            except Exception as e:
                print("check_join err:", e)
                not_joined.append(channel)

        if not_joined:
            bot.answer_callback_query(call.id, "❗ Please join all required channels first.", show_alert=True)
            return

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📹 Get Videos", callback_data="get_videos"))
        markup.add(telebot.types.InlineKeyboardButton("🔒 Privacy Policy", callback_data="privacy"))
        try:
            bot.edit_message_caption(chat_id=user_id, message_id=call.message.message_id,
                                     caption="🎉 You have joined all required channels!\nNow you can access features below:",
                                     reply_markup=markup)
        except Exception:
            bot.send_message(user_id, "🎉 You have joined all required channels!", reply_markup=markup)

    elif call.data == "get_videos":

        async def fetch_all_videos():
            client = TelegramClient("session", API_ID, API_HASH)
            await client.start(bot_token=BOT_TOKEN)
            ids = []
            async for msg in client.iter_messages(BUFFER_CHANNEL_ID, reverse=True):  # पुराने से नए तक
                if msg.video:
                    ids.append(msg.id)
            await client.disconnect()
            return ids

        try:
            video_ids = asyncio.run(fetch_all_videos())
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Error fetching videos: {e}")
            return

        if not video_ids:
            bot.send_message(user_id, "⚠️ No videos found in channel.")
            return

        random.shuffle(video_ids)
        sent = 0
        for vid in video_ids[:5]:
            try:
                bot.copy_message(user_id, BUFFER_CHANNEL_ID, vid)
                time.sleep(0.3)
                sent += 1
            except Exception as e:
                print("copy_message error:", e)

        if sent:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("📥 Get More Videos", callback_data="get_videos"))
            bot.send_message(user_id, f"📁 Sent {sent} videos 🎬", reply_markup=markup)

    elif call.data == "privacy":
        bot.send_message(user_id, PRIVACY_MESSAGE)

# === Admin Broadcast ===
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not authorized.")
        return

    if not message.reply_to_message:
        bot.send_message(ADMIN_ID, "⚠️ Reply to any message with /broadcast to send to all users.")
        return

    users = read_lines(USERS_FILE)
    sent = 0
    for u in users:
        try:
            bot.copy_message(int(u), message.chat.id, message.reply_to_message.message_id)
            time.sleep(0.05)
            sent += 1
        except Exception:
            pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {sent} users.")

# === Start function (for Render) ===
def start_bot():
    print("Starting Telegram bot polling...")
    bot.polling(none_stop=True, interval=0, timeout=20)
