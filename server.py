from flask import Flask
import threading
import bot  # apna main bot.py import karna

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running fine ✅"

def run_bot():
    bot.bot.polling(none_stop=True, interval=0, timeout=20)

if __name__ == "__main__":
    # Bot alag thread me chalega
    t = threading.Thread(target=run_bot)
    t.start()
    # Flask server port 10000 par chalega (Render ke liye)
    app.run(host="0.0.0.0", port=10000)
