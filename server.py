# server.py
from flask import Flask
import threading
import os
import bot  # import your bot module

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

def run_bot_thread():
    try:
        bot.start_bot()
    except Exception as e:
        print("Bot thread error:", e)

if __name__ == "__main__":
    # Start bot in background thread
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()

    # Use Render's PORT env var (Render sets this automatically)
    port = int(os.getenv("PORT", "10000"))
    # Bind to 0.0.0.0 so external connections (Render) can reach it
    app.run(host="0.0.0.0", port=port)
