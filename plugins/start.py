from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import MOVIE_GROUP, UPDATE_CHANNEL, OWNER_USERNAME, START_MSG, START_PIC


def start_buttons():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎬 Movie Group", url=MOVIE_GROUP)],
            [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL)],
            [InlineKeyboardButton("👤 Owner", callback_data="owner")]
        ]
    )


def back_home_buttons():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⬅️ Back", callback_data="back"),
                InlineKeyboardButton("🏠 Home", callback_data="home")
            ]
        ]
    )


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):

    text = START_MSG.format(first=message.from_user.first_name)

    if START_PIC:
        await message.reply_photo(
            photo=START_PIC,
            caption=text,
            reply_markup=start_buttons()
        )
    else:
        await message.reply_text(
            text=text,
            reply_markup=start_buttons()
        )


@Client.on_callback_query(filters.regex("owner"))
async def owner_callback(client, query):
    await query.answer()

    await query.message.edit_caption(
        f"👤 <b>Bot Owner:</b> @{OWNER_USERNAME}\n📩 Contact for any help.",
        reply_markup=back_home_buttons()
    )


@Client.on_callback_query(filters.regex("home|back"))
async def home_back_callback(client, query):
    await query.answer()

    text = START_MSG.format(first=query.from_user.first_name)

    await query.message.edit_caption(
        text,
        reply_markup=start_buttons()
                )
