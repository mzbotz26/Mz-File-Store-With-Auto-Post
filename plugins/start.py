import time, requests, secrets
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    IS_VERIFY, VERIFY_STEP_TIME,
    SHORTLINK_URL, SHORTLINK_API,
    SHORTLINK_URL2, SHORTLINK_API2,
    VERIFY_TUT_1, VERIFY_TUT_2,
    MOVIE_GROUP, UPDATE_CHANNEL, OWNER_USERNAME,
    START_MSG, START_PIC,
    CHANNEL_ID,
    FORCESUB_CHANNEL, FORCESUB_CHANNEL2, FORCESUB_CHANNEL3
)

# ================= VERIFY SYSTEM =================

verify_db = {}

def short1(url):
    api = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={url}"
    return requests.get(api).json().get("shortenedUrl", url)

def short2(url):
    api = f"https://{SHORTLINK_URL2}/api?api={SHORTLINK_API2}&url={url}"
    return requests.get(api).json().get("shortenedUrl", url)

def get_status(uid):
    data = verify_db.get(uid, {})
    step = data.get("step")
    timev = data.get("time", 0)

    if step and time.time() - timev < VERIFY_STEP_TIME:
        return step
    return None

def set_status(uid, step):
    verify_db[uid] = {"step": step, "time": time.time()}

# ================= TOKEN SYSTEM (OPTIONAL) =================

TOKEN_DB = {}
TOKEN_EXPIRY = 3600

def generate_token(msg_id, user_id):
    token = secrets.token_hex(8)
    TOKEN_DB[token] = {"msg_id": msg_id, "user_id": user_id, "time": time.time()}
    return token

def verify_token(token, user_id):
    data = TOKEN_DB.get(token)
    if not data:
        return None
    if data["user_id"] != user_id:
        return None
    if time.time() - data["time"] > TOKEN_EXPIRY:
        del TOKEN_DB[token]
        return None
    msg_id = data["msg_id"]
    del TOKEN_DB[token]
    return msg_id

# ================= FORCE SUB =================

async def is_joined(client, channel_id, user_id):
    try:
        m = await client.get_chat_member(channel_id, user_id)
        return m.status not in ["left", "kicked"]
    except:
        return False

def forcesub_buttons(client):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel 1", url=client.invitelink)],
        [InlineKeyboardButton("📢 Join Channel 2", url=client.invitelink2)],
        [InlineKeyboardButton("📢 Join Channel 3", url=client.invitelink3)],
        [InlineKeyboardButton("🔄 Try Again", callback_data="checksub")]
    ])

# ================= UI BUTTONS =================

def start_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Movie Group", url=MOVIE_GROUP)],
        [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL)],
        [InlineKeyboardButton("👤 Owner", callback_data="owner")]
    ])

def back_home_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

# ================= VERIFY UI =================

async def send_verify_buttons(client, message, step):
    bot = await client.get_me()
    start = f"https://t.me/{bot.username}?start=verify"

    if step == "step1":
        s = short1(start)
        tut = VERIFY_TUT_1
        text = "🔐 Please complete Step-1 verification"
    else:
        s = short2(start)
        tut = VERIFY_TUT_2
        text = "🔐 Please complete Step-2 verification"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Verify Now", url=s)],
        [InlineKeyboardButton("📖 How To Use", url=tut)]
    ])

    await message.reply_text(text, reply_markup=buttons)

# ================= START HANDLER =================

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    # ----- VERIFY BUTTON CALLBACK -----
    if len(message.command) > 1 and message.command[1] == "verify":
        return await message.reply_text("✅ Verification done.\nNow open your file link again.")

    # ----- FORCE SUB CHECK -----
    uid = message.from_user.id

    j1 = await is_joined(client, FORCESUB_CHANNEL, uid)
    j2 = await is_joined(client, FORCESUB_CHANNEL2, uid)
    j3 = await is_joined(client, FORCESUB_CHANNEL3, uid)

    if not j1 or not j2 or not j3:
        return await message.reply_text(
            "🔔 Please join all our channels first.",
            reply_markup=forcesub_buttons(client)
        )

    # ----- NORMAL START -----
    if len(message.command) == 1:
        text = START_MSG.format(first=message.from_user.first_name)
        if START_PIC:
            await message.reply_photo(START_PIC, caption=text, reply_markup=start_buttons())
        else:
            await message.reply_text(text, reply_markup=start_buttons())
        return

    data = message.command[1]

    # -------- FILE LINK --------
    if data.startswith("file_"):
        parts = data.replace("file_", "").split("_")
        msg_id = int(parts[0])

        # VERIFY SYSTEM
        if IS_VERIFY:
            status = get_status(uid)
            if not status:
                return await send_verify_buttons(client, message, "step1")
            if status == "step1":
                return await send_verify_buttons(client, message, "step2")

        try:
            await client.forward_messages(message.chat.id, CHANNEL_ID, msg_id)
        except:
            await message.reply_text("❌ File not found.")

    # -------- BATCH --------
    elif data.startswith("batch_"):
        data = data.replace("batch_", "")
        start, end = map(int, data.split("-"))

        await message.reply_text("📦 Sending batch files...")

        for i in range(start, end + 1):
            try:
                await client.forward_messages(message.chat.id, CHANNEL_ID, i)
            except:
                pass

# ================= FORCE SUB CALLBACK =================

@Client.on_callback_query(filters.regex("checksub"))
async def check_sub_again(client, query):
    uid = query.from_user.id

    j1 = await is_joined(client, FORCESUB_CHANNEL, uid)
    j2 = await is_joined(client, FORCESUB_CHANNEL2, uid)
    j3 = await is_joined(client, FORCESUB_CHANNEL3, uid)

    if j1 and j2 and j3:
        await query.message.delete()
        await query.answer("✅ Joined successfully!")
    else:
        await query.answer("❌ Please join all channels first!", show_alert=True)

# ================= VERIFY COMMANDS =================

@Client.on_message(filters.private & filters.command("verify1"))
async def verify1(client, message):
    set_status(message.from_user.id, "step1")
    await message.reply_text("✅ Step-1 Verified!\nYou have 12 hours access.")

@Client.on_message(filters.private & filters.command("verify2"))
async def verify2(client, message):
    set_status(message.from_user.id, "step2")
    await message.reply_text("✅ Step-2 Verified!\nYou have 12 hours access.")

# ================= CALLBACKS =================

@Client.on_callback_query(filters.regex("owner"))
async def owner_callback(client, query):
    await query.answer()
    await query.message.edit_caption(
        f"👤 <b>Bot Owner:</b> @{OWNER_USERNAME}\n📩 Contact for help.",
        reply_markup=back_home_buttons()
    )

@Client.on_callback_query(filters.regex("home|back"))
async def home_back_callback(client, query):
    await query.answer()
    text = START_MSG.format(first=query.from_user.first_name)
    await query.message.edit_caption(text, reply_markup=start_buttons())
