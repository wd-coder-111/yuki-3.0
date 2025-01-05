import os
import asyncio
import sys
import time
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from bot import Bot
from config import ADMINS, OWNER_ID
from helper_func import encode, decode
from database.database import add_user, del_user, full_userbase, present_user, is_admin


#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    text = message.text
    user_id = message.from_user.id
    
    await add_user(user_id)  # Adding user to the database
    
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]

            if base64_string.startswith("req_"):
                invite_link = await decode(base64_string[4:])
                button_text = "🛎️ Request to Join"
            else:
                invite_link = await decode(base64_string)
                button_text = "🔗 Join Channel"

            button = InlineKeyboardMarkup(
                [[InlineKeyboardButton(button_text, url=invite_link)]]
            )
            
            await message.reply_text(
                "Here is your link! Click the button below to proceed:",
                reply_markup=button
            )
        except Exception as e:
            await message.reply_text("Invalid or expired link.")
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("About Me", callback_data="help"),
                InlineKeyboardButton("Close", callback_data="close")]
            ]
        )
        
        await message.reply_text(
            "<b><i>Welcome to the advanced links sharing bot.\nWith this bot, you can share links and keep your channels safe from copyright issues</i></b>",
            reply_markup=inline_buttons
        )

        
#=====================================================================================##

WAIT_MSG = """"<b>Processing ....</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message with out any spaces.</code>"""

#=====================================================================================##

@Bot.on_message(filters.command('users') & filters.user(OWNER_ID))
async def get_users(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")


#=====================================================================================##

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(OWNER_ID))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time </i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

@Bot.on_callback_query(filters.regex("help"))
async def help_callback(client: Bot, callback_query):
    # Define the inline keyboard with the "Close" button
    inline_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
    )
    
    
    await callback_query.answer()
    await callback_query.message.edit_text("<b><i>About Us..\n\n‣ Made for : @Anime_X_Hunters\n‣ Owned by : @Okabe_xRintarou\n‣ Developer : @The_Seishiro_Nagi\n\n Adios !!</i></b>", reply_markup=inline_buttons)

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()