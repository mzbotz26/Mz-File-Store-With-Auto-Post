from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, CHANNEL_ID
from database import Database
import asyncio
from datetime import datetime

db = Database()

# ───────── START ─────────

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    db.add_user(message.from_user.id)

    await message.reply_text(
        "👋 Welcome!\n\n"
        "Available Commands:\n"
        "/link - Generate file link\n"
        "/batch - Batch link info\n"
        "/users - Total users\n"
        "/stats - Bot stats\n"
        "/broadcast - Admin broadcast"
    )

# ───────── LINK ─────────

@Client.on_message(filters.command("link") & filters.private)
async def link_cmd(client, message):
    await message.reply_text(
        "📥 Send me any file and I will generate your direct download link."
    )

# ───────── BATCH ─────────

@Client.on_message(filters.command("batch") & filters.private)
async def batch_cmd(client, message):
    await message.reply_text(
        "📦 Send multiple files one by one.\n"
        "After some seconds, you will get one batch link."
    )

# ───────── USERS (ADMIN) ─────────

@Client.on_message(filters.command("users") & filters.private)
async def users_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return

    total = db.total_users()
    await message.reply_text(f"👥 Total Users: {total}")

# ───────── STATS (ADMIN) ─────────

@Client.on_message(filters.command("stats") & filters.private)
async def stats_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return

    uptime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    total = db.total_users()

    await message.reply_text(
        f"📊 Bot Stats\n\n"
        f"👥 Users: {total}\n"
        f"⏰ Time: {uptime}"
    )

# ───────── BROADCAST (ADMIN) ─────────

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return

    if not message.reply_to_message:
        return await message.reply_text("Reply to any message to broadcast it.")

    sent = 0
    failed = 0

    for user in db.users.find({}):
        try:
            await message.reply_to_message.copy(user["_id"])
            sent += 1
            await asyncio.sleep(0.3)
        except:
            failed += 1

    await message.reply_text(
        f"📢 Broadcast Completed\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )
