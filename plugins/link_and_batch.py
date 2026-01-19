from pyrogram import Client, filters
from config import CHANNEL_ID
import asyncio
import re

user_batches = {}

# ───────── CLEAN HELPERS ─────────

def clean_filename(name):
    name = re.sub(r"\.(mkv|mp4|avi|webm)", "", name, flags=re.I)
    name = re.sub(r"480p|720p|1080p|2160p|x264|x265|webrip|webdl|bluray|hdrip|dual|multi|hindi|tamil|telugu|english", "", name, flags=re.I)
    name = name.replace(".", " ").replace("_", " ")
    return re.sub(" +", " ", name).strip()

def detect_language(text):
    t = text.lower()
    if "dual" in t or "multi" in t: return "Hindi Dual Audio"
    if "hindi" in t: return "Hindi"
    if "tamil" in t: return "Tamil"
    if "telugu" in t: return "Telugu"
    if "english" in t or "eng" in t: return "English"
    return "Hindi"

def detect_quality(text):
    t = text.lower()
    res = "1080p" if "1080" in t else "720p" if "720" in t else "480p"
    codec = "x265" if "x265" in t else "x264"
    source = "WEBDL" if "webdl" in t or "web-dl" in t else "WEBRIP" if "webrip" in t else "BLURAY" if "bluray" in t else "WEBDL"
    return f"{res} {codec} {source}"

def detect_audio(text):
    t = text.lower()
    if "ddp" in t or "dd+" in t: return "DDP"
    if "aac" in t: return "AAC"
    if "mp3" in t: return "MP3"
    return "AAC"

# ───────── SINGLE FILE LINK ─────────

@Client.on_message(filters.private & (filters.document | filters.video))
async def save_file(client, message):

    user_id = message.from_user.id
    file = message.document or message.video

    # Forward to DB channel
    msg = await message.forward(CHANNEL_ID)

    # Clean caption in DB channel also
    title = clean_filename(file.file_name or "File")
    lang = detect_language(file.file_name or "")
    quality = detect_quality(file.file_name or "")
    audio = detect_audio(file.file_name or "")

    clean_caption = f"""🎬 Title: {title}
🌐 Language: {lang}
📺 Quality: {quality}
🔊 Audio: {audio}

💪 Powered By : MzMoviiez
"""

    try:
        await msg.edit_caption(clean_caption)
    except:
        pass

    # Batch save
    if user_id not in user_batches:
        user_batches[user_id] = []
    user_batches[user_id].append(msg.id)

    # Generate direct link
    channel_part = str(CHANNEL_ID)[4:]
    link = f"https://t.me/{bot.username}?start=file_{msg.id}"

    # Reply to user
    await message.reply_text(
        f"""{clean_caption}

🔗 Download Link:
{link}
""",
        disable_web_page_preview=True
    )

    # Batch wait
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

# ───────── BATCH START HANDLER ─────────

@Client.on_message(filters.command("start") & filters.private)
async def batch_start(client, message):

    if len(message.command) > 1 and message.command[1].startswith("batch_"):

        data = message.command[1].replace("batch_", "")
        start, end = data.split("-")

        start = int(start)
        end = int(end)

        await message.reply_text("📦 Sending your batch files with clean caption...")

        for i in range(start, end + 1):
            try:
                msg = await client.get_messages(CHANNEL_ID, i)
                file = msg.document or msg.video

                title = clean_filename(file.file_name or "File")
                lang = detect_language(file.file_name or "")
                quality = detect_quality(file.file_name or "")
                audio = detect_audio(file.file_name or "")

                caption = f"""🎬 Title: {title}
🌐 Language: {lang}
📺 Quality: {quality}
🔊 Audio: {audio}

💪 Powered By : MzMoviiez
"""

                await client.send_document(
                    message.chat.id,
                    file.file_id,
                    file_name=f"{title}.mkv",
                    caption=caption
                )

            except:
                pass
