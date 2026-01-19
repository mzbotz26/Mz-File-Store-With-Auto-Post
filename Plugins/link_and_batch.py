from pyrogram import Client, filters
from config import CHANNEL_ID
import asyncio

user_batches = {}

# ───────────── SINGLE FILE LINK ─────────────

@Client.on_message(filters.private & (filters.document | filters.video))
async def save_file(client, message):

    user_id = message.from_user.id

    # Forward to DB Channel
    msg = await message.forward(CHANNEL_ID)

    # Save for batch
    if user_id not in user_batches:
        user_batches[user_id] = []
    user_batches[user_id].append(msg.id)

    # Generate direct link
    channel_part = str(CHANNEL_ID)[4:]
    link = f"https://t.me/c/{channel_part}/{msg.id}"

    await message.reply_text(
        f"✅ File Saved!\n\n🔗 Your Link:\n{link}",
        disable_web_page_preview=True
    )

    # Wait for batch collect
    await asyncio.sleep(10)

    if user_id in user_batches and len(user_batches[user_id]) > 1:
        ids = user_batches[user_id]
        start = ids[0]
        end = ids[-1]

        bot_username = (await client.get_me()).username
        batch_link = f"https://t.me/{bot_username}?start=batch_{start}-{end}"

        await message.reply_text(
            f"📦 Batch Ready!\n\n🔗 Your Batch Link:\n{batch_link}",
            disable_web_page_preview=True
        )

        del user_batches[user_id]


# ───────────── BATCH START HANDLER ─────────────

@Client.on_message(filters.command("start") & filters.private)
async def batch_start(client, message):

    if len(message.command) > 1 and message.command[1].startswith("batch_"):

        data = message.command[1].replace("batch_", "")
        start, end = data.split("-")

        start = int(start)
        end = int(end)

        await message.reply_text("📦 Sending your batch files...")

        for i in range(start, end + 1):
            try:
                await client.forward_messages(
                    message.chat.id,
                    CHANNEL_ID,
                    i
                )
            except:
                pass
