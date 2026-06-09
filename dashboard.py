from flask import Flask, request
import sqlite3

app = Flask(__name__)

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

# ================= HOME =================
@app.route("/")
def home():
    return """
    <h1>🎛 Bot Dashboard</h1>
    <p>Welkom bij je control panel</p>
    <a href='/settings'>Settings</a>
    """

# ================= SETTINGS =================
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        guild_id = request.form["guild_id"]
        channel = request.form["channel"]

        cursor.execute(
            "REPLACE INTO config (guild_id, welcome_channel) VALUES (?, ?)",
            (guild_id, channel)
        )
        db.commit()

        return "✅ Opgeslagen!"

    return """
    <h2>Settings</h2>
    <form method='POST'>
        Guild ID: <input name='guild_id'><br>
        Welcome channel: <input name='channel'><br>
        <button type='submit'>Save</button>
    </form>
    """

# ================= START =================
app.run(host="0.0.0.0", port=3000)