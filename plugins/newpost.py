import asyncio
from pyrogram import Client as Bot, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, FloodWait, ChatAdminRequired, RPCError
from pyrogram.errors import InviteHashExpired, InviteRequestSent
from database.database import save_channel, delete_channel, get_channels
from config import ADMINS, OWNER_ID
from helper_func import encode
from datetime import datetime, timedelta


##----------------------------------------------------------------------------------------------------

# Revoke invite link after 10 minutes
async def revoke_invite_after_10_minutes(client: Bot, channel_id: int, invite_link: str):
    await asyncio.sleep(600)  # 600 seconds = 10 minutes
    try:
        await client.revoke_chat_invite_link(chat_id=channel_id, invite_link=invite_link)
        print(f"Invite link for channel {channel_id} has been revoked.")
    except Exception as e:
        print(f"Error revoking invite for channel {channel_id}: {e}")

##----------------------------------------------------------------------------------------------------        
##----------------------------------------------------------------------------------------------------

@Bot.on_message(filters.command('setchannel') & filters.private & filters.user(OWNER_ID))
async def set_channel(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("You are not an admin.")
    
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("Channel id check karo chacha. Example: /setchannel <channel_id>")
    
    try:
        chat = await client.get_chat(channel_id)

        if chat.permissions and not (chat.permissions.can_post_messages or chat.permissions.can_edit_messages):
            return await message.reply(f"Me hoon isme-{chat.title} lekin permission tumhare chacha denge.")
        
        await save_channel(channel_id)
        return await message.reply(f"✅ Channel-({chat.title})-({channel_id}) add ho gya ha maharaj.")
    
    except UserNotParticipant:
        return await message.reply("I am not a member of this channel. Please add me and try again.")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await set_channel(client, message)
    except RPCError as e:
        return await message.reply(f"RPC Error: {str(e)}")
    except Exception as e:
        return await message.reply(f"Unexpected Error: {str(e)}")

##----------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------        

@Bot.on_message(filters.command('delchannel') & filters.private & filters.user(OWNER_ID))
async def del_channel(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("You are not an admin.")
    
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("Channel id galat ha mere aaka.")
    
    await delete_channel(channel_id)
    return await message.reply(f"❌ Channel {channel_id} hata dia gaya ha maharaj.")

##----------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------

@Bot.on_message(filters.command('channelpost') & filters.private & filters.user(OWNER_ID))
async def channel_post(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("Tere baap ka bot ha kya")
    
    channels = await get_channels()
    if not channels:
        return await message.reply("No channels are available to post please use /setchannel first.")

    buttons = []
    
    for channel_id in channels:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title

            # Create a new invite link
            invite = await client.create_chat_invite_link(chat_id=channel_id)
            base64_invite = await encode(invite.invite_link)
            button_link = f"https://t.me/{client.username}?start={base64_invite}"
            
            buttons.append(InlineKeyboardButton(text=f"{channel_name}", url=button_link))

            asyncio.create_task(revoke_invite_after_10_minutes(client, channel_id, invite.invite_link))

        except Exception as e:
            print(f"Error generating invite for {channel_id}: {e}")
            continue

    if buttons:
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        await message.reply("📢 Select a channel to generate an invite:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply("No channels available to post.")

##----------------------------------------------------------------------------------------------------
##----------------------------------------------------------------------------------------------------        

@Bot.on_message(filters.command('reqpost') & filters.private & filters.user(OWNER_ID))
async def req_post(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("Tere baap ka bot ha kya")
    
    channels = await get_channels()
    if not channels:
        return await message.reply("No channels are available to post please use /setchannel first.")

    buttons = []
    expire_time = datetime.now() + timedelta(minutes=10)  # Set to expire in 10 minutes
    
    for channel_id in channels:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title

            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                creates_join_request=True,
                expire_date=expire_time
            )

            base64_request = await encode(invite.invite_link)
            button_link = f"https://t.me/{client.username}?start=req_{base64_request}"

            buttons.append(InlineKeyboardButton(text=f"{channel_name}", url=button_link))

        except Exception as e:
            print(f"Error generating request link for {channel_id}: {e}")
            continue

    if buttons:
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        await message.reply("📢 Select a channel to request access:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply("No channels available to request access.")