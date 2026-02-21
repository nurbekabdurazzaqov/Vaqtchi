import os
import sqlite3
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, ContextTypes, ChatMemberHandler
import asyncio

TOKEN = os.getenv("TOKEN")  # Telegram bot token
conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

# Foydalanuvchilar jadvali
cursor.execute("""
CREATE TABLE IF NOT EXISTS members (
    admin_id INTEGER,
    chat_id INTEGER,
    user_id INTEGER,
    expire_date TEXT,
    type TEXT,
    status TEXT,
    PRIMARY KEY(admin_id, chat_id, user_id)
)
""")
conn.commit()

async def new_member(update: ContextTypes.DEFAULT_TYPE, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        admin_id = update.chat_member.from_user.id
        chat_id = update.chat_member.chat.id
        expire_date = (datetime.now() + timedelta(days=4)).isoformat()  # Free 4 kun
        cursor.execute(
            "INSERT OR REPLACE INTO members VALUES (?, ?, ?, ?, ?, ?)",
            (admin_id, chat_id, member.id, expire_date, "free", "active")
        )
        conn.commit()

async def check_members(app):
    while True:
        cursor.execute("SELECT admin_id, chat_id, user_id, expire_date FROM members WHERE status='active'")
        rows = cursor.fetchall()
        for admin_id, chat_id, user_id, expire_date in rows:
            if datetime.now() > datetime.fromisoformat(expire_date):
                try:
                    await app.bot.ban_chat_member(chat_id, user_id)
                    await app.bot.unban_chat_member(chat_id, user_id)
                    cursor.execute(
                        "UPDATE members SET status='removed' WHERE admin_id=? AND chat_id=? AND user_id=?",
                        (admin_id, chat_id, user_id)
                    )
                    conn.commit()
                except:
                    pass
        await asyncio.sleep(3600)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))
    asyncio.create_task(check_members(app))
    await app.run_polling()

asyncio.run(main())
