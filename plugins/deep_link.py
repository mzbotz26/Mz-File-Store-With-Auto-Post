from pyrogram import Client, filters
from config import CHANNEL_ID

# ───────── FILE DEEP LINK HANDLER ─────────

@Client.on_message(filters.command("start") & filters.private)
async def deep_link_handler(client, message):

    if len(message.command) > 1 and message.command[1].startswith("file_"):

        msg_id = int(message.command[1].replace("file_", ""))

        try:
            await client.forward_messages(
                message.chat.id,
                CHANNEL_ID,
                msg_id
            )
        except:
            await message.reply_text("❌ File not found or deleted.")
