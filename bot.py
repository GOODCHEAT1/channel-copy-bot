import telebot
import random
import os

# === CONFIG ===
BOT_TOKEN = 'YOUR_BOT_TOKEN'
BUFFER_CHANNEL_ID = -1002608751179
FORCE_JOIN_IDS = [-1002569411232]
ADMIN_ID = 1209978813
PHOTO_URL = 'https://envs.sh/hA0.jpg'

PRIVACY_MESSAGE = """Privacy Policy for 18+ Bots

1️⃣ Age Restriction: 18+ only
2️⃣ No Personal Data Collection
3️⃣ User Responsibility
...
🔟 Policy Changes can occur without notice.
"""

bot = telebot.TeleBot(BOT_TOKEN)

# === Ensure required files exist ===
for file in ["users.txt", "video_ids.txt", "referrals.txt", "user_points.txt"]:
    if not os.path.exists(file):
        open(file, "w").close()

# === Save New Users ===
def save_user(user_id, referred_by=None):
    with open("users.txt", "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")
            bot.send_message(ADMIN_ID, f"👤 New user: {user_id}\n📊 Total users: {len(users)+1}")
            if referred_by:
                save_referral(user_id, referred_by)

# === Save Referrals ===
def save_referral(user_id, referred_by):
    with open("referrals.txt", "a+") as f:
        f.write(f"{user_id} referred_by {referred_by}\n")
    update_points(referred_by)

# === Update Points ===
def update_points(referred_by):
    with open("user_points.txt", "a+") as f:
        f.seek(0)
        points_data = f.read().splitlines()
        referrer_points = {line.split()[0]: int(line.split()[1]) for line in points_data if len(line.split()) == 2}
        referrer_points[referred_by] = referrer_points.get(referred_by, 0) + 10

    with open("user_points.txt", "w") as f:
        for user_id, points in referrer_points.items():
            f.write(f"{user_id} {points}\n")

# === Get Random Video IDs ===
def get_random_video_ids(n=5):
    with open("video_ids.txt") as f:
        all_ids = f.read().splitlines()
    return random.sample(all_ids, min(n, len(all_ids)))

# === Save video ID from BUFFER_CHANNEL_ID ===
@bot.channel_post_handler(content_types=['video', 'document'])
def save_video_id(message):
    if message.chat.id == BUFFER_CHANNEL_ID:
        with open("video_ids.txt", "a") as f:
            f.write(str(message.message_id) + "\n")
        print(f"✅ Saved video ID: {message.message_id}")

# === /start handler ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    referred_by = None

    if 'ref=' in message.text:
        referred_by = message.text.split('ref=')[1]

    save_user(user_id, referred_by)

    referral_link = f"https://t.me/YOUR_BOT_USERNAME?start=ref={user_id}"

    caption = (
        f"🥵 *Welcome to Pom Hub* 🙈!\n"
        f"Here you'll get the most unseen 💦 videos.\n\n"
        f"📢 *Join required channels below:*\n\n"
        f"💥 *Refer friends to earn rewards!*\nYour referral link:\n`{referral_link}`"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📣 Join Channel 1", url="https://t.me/+ZUXtxXBzR_VkMjU1"))
    markup.add(telebot.types.InlineKeyboardButton("📣 Join Channel 2", url="https://t.me/+h9nxPe7_KAs3NGY1"))
    markup.add(telebot.types.InlineKeyboardButton("📣 Join Channel 3", url="https://t.me/insta_mmsvip_videos_clips"))
    markup.add(telebot.types.InlineKeyboardButton("✅ Joined Channels", callback_data="check_join"))

    bot.send_photo(
        user_id,
        PHOTO_URL,
        caption=caption,
        parse_mode='Markdown',
        reply_markup=markup
    )

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
            except:
                not_joined.append(channel)

        if not_joined:
            bot.answer_callback_query(call.id, "❗ Please join all required channels first.", show_alert=True)
        else:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("📹 Get Videos", callback_data="get_videos"))
            markup.add(telebot.types.InlineKeyboardButton("🔒 Privacy Policy", callback_data="privacy"))

            bot.edit_message_caption(
                chat_id=user_id,
                message_id=call.message.message_id,
                caption="🎉 You have joined all required channels!\nNow you can access features below:",
                reply_markup=markup
            )

    elif call.data == "get_videos":
        try:
            video_ids = get_random_video_ids()
            for vid in video_ids:
                try:
                    bot.copy_message(user_id, BUFFER_CHANNEL_ID, int(vid))
                except Exception as e:
                    bot.send_message(user_id, f"⚠️ Couldn't fetch video {vid} — {e}")

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("📹 Get More Videos", callback_data="get_videos"))
            bot.send_message(user_id, "🥳 Here are your videos 🎬", reply_markup=markup)

        except:
            bot.send_message(user_id, "❗ Error while sending videos.")

    elif call.data == "privacy":
        bot.send_message(user_id, PRIVACY_MESSAGE)

# === Admin Broadcast ===
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id == ADMIN_ID:
        if not message.reply_to_message:
            bot.send_message(ADMIN_ID, "⚠️ Reply to a message (text/photo/video/voice) with /broadcast to send.")
            return

        sent = 0
        with open("users.txt") as f:
            users = f.read().splitlines()

        for user in users:
            try:
                bot.copy_message(int(user), ADMIN_ID, message.reply_to_message.message_id)
                sent += 1
            except:
                pass

        bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {sent} users.")

# === Polling ===
bot.polling(none_stop=True)
