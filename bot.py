
import os
import random
import time
import telebot
import pymongo

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BUFFER_CHANNEL_ID = -1002963301599   # आपका video channel
PHOTO_URL = os.getenv("PHOTO_URL", "https://envs.sh/hA0.jpg")
FORCE_JOIN_IDS = [-1002547586103]

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://user:pass@cluster/db")
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
videos_col = db["videos"]
users_col = db["users"]

PRIVACY_MESSAGE = """Privacy Policy for 18+ Bots

1️⃣ Age Restriction: 18+ only
2️⃣ No Personal Data Collection
3️⃣ User Responsibility
...
🔟 Policy Changes can occur without notice.
"""

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# === Save user ===
def save_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id})
        try:
            total = users_col.count_documents({})
            bot.send_message(ADMIN_ID, f"👤 New user: {user_id}\n📊 Total users: {total}")
        except:
            pass

# === Save video when posted in BUFFER_CHANNEL_ID ===
@bot.channel_post_handler(content_types=["video"])
def save_channel_video(message):
    file_id = message.video.file_id
    if not videos_col.find_one({"file_id": file_id}):
        videos_col.insert_one({"file_id": file_id})
        print(f"✅ Saved video {file_id} in MongoDB")

# === /start handler ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    save_user(user_id)

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
    except:
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
        bot.send_message(user_id, "🎉 You have joined all required channels!", reply_markup=markup)

    elif call.data == "get_videos":
        videos = list(videos_col.find())
        if not videos:
            bot.send_message(user_id, "⚠️ No videos available currently.")
            return

        random.shuffle(videos)
        sent = 0
        for v in videos[:5]:
            try:
                bot.send_video(user_id, v["file_id"])
                time.sleep(0.3)
                sent += 1
            except Exception as e:
                print("send_video error:", e)

        if sent:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("📥 Get More Videos", callback_data="get_videos"))
            bot.send_message(user_id, f"📁 Sent {sent} videos 🎬", reply_markup=markup)

    elif call.data == "privacy":
        bot.send_message(user_id, PRIVACY_MESSAGE)

# === Broadcast ===
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ You are not authorized.")
        return

    if not message.reply_to_message:
        bot.send_message(ADMIN_ID, "⚠️ Reply to any message with /broadcast to send to all users.")
        return

    users = users_col.find()
    sent = 0
    for u in users:
        try:
            bot.copy_message(u["user_id"], message.chat.id, message.reply_to_message.message_id)
            time.sleep(0.05)
            sent += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {sent} users.")

# === Start polling ===
def start_bot():
    print("Starting Telegram bot polling...")
    bot.polling(none_stop=True, interval=0, timeout=20)
