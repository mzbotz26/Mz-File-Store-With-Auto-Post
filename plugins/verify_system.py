import time, requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    IS_VERIFY, VERIFY_STEP_TIME,
    SHORTLINK_URL, SHORTLINK_API,
    SHORTLINK_URL2, SHORTLINK_API2,
    VERIFY_TUT_1, VERIFY_TUT_2
)

verify_db = {}

# ---------- SHORT LINK ----------

def short1(url):
    api = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={url}"
    return requests.get(api).json().get("shortenedUrl", url)

def short2(url):
    api = f"https://{SHORTLINK_URL2}/api?api={SHORTLINK_API2}&url={url}"
    return requests.get(api).json().get("shortenedUrl", url)

# ---------- VERIFY STATUS ----------

def get_status(uid):
    data = verify_db.get(uid, {})
    step = data.get("step")
    timev = data.get("time", 0)

    if step and time.time() - timev < VERIFY_STEP_TIME:
        return step

    return None

def set_status(uid, step):
    verify_db[uid] = {
        "step": step,
        "time": time.time()
    }

# ---------- VERIFY COMMANDS ----------

@Client.on_message(filters.private & filters.command("verify1"))
async def verify1(client, message):
    set_status(message.from_user.id, "step1")
    await message.reply_text("✅ Step-1 Verified!\nYou have 12 hours access now.")

@Client.on_message(filters.private & filters.command("verify2"))
async def verify2(client, message):
    set_status(message.from_user.id, "step2")
    await message.reply_text("✅ Step-2 Verified!\nYou have 12 hours access now.")

# ---------- VERIFY BUTTON ----------

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

# ---------- MAIN GATE ----------

@Client.on_message(filters.private & (filters.document | filters.video))
async def verify_gate(client, message):

    if not IS_VERIFY:
        return

    uid = message.from_user.id
    status = get_status(uid)

    # No verify yet → Step 1
    if not status:
        await send_verify_buttons(client, message, "step1")
        return

    # Step1 expired → Step2
    if status == "step1":
        await send_verify_buttons(client, message, "step2")
        return

    # Step2 expired → Step1 again
    if status == "step2":
        await send_verify_buttons(client, message, "step1")
        return
