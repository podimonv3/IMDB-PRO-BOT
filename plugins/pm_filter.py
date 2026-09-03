import asyncio
lock = asyncio.Lock()
import re
import random
import ast
import math
import urllib.parse
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, QueryIdInvalid
from utils import get_size, is_subscribed, temp, get_settings, save_group_settings, is_requested_one, is_requested_two
from database.users_chats_db import db
from database.ia_filterdb import Media, Mediaa, get_bad_files, get_file_details, get_search_results, db as clientDB, db1 as clientDB2, db2 as clientDB3
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import find_gfilter, get_gfilters
import logging
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# --- 🛠️ TELEGRAM QUERY ID ERROR FIX START 🛠️ ---
_original_answer = CallbackQuery.answer
async def _patched_answer(self, *args, **kwargs):
    try:
        return await _original_answer(self, *args, **kwargs)
    except QueryIdInvalid:
        pass
CallbackQuery.answer = _patched_answer
# --- 🛠️ TELEGRAM QUERY ID ERROR FIX END 🛠️ ---




BUTTON_COOLDOWNS = {}
BUTTONS = {}
SPELL_CHECK = {}
RATING = ["5.1 | IMDB", "6.2 | IMDB", "7.3 | IMDB", "8.4 | IMDB", "9.5 | IMDB", "8.3 | IMDB", "6.3 | IMDB"]
GENRES = ["fun, fact",
          "Thriller, Comedy",
          "Drama, Comedy",
          "Family, Drama",
          "Action, Adventure",
          "Film Noir",
          "Documentary"]


# =====================================================================
# 1. USER SIDE: HANDLES INCOMING PM MESSAGES (TEXT, PHOTO, VIDEO, STICKER)
# =====================================================================
@Client.on_message(filters.private & (filters.text | filters.photo | filters.video | filters.sticker) & filters.incoming)
async def pm_text(bot: Client, message):
    user_id = message.from_user.id
    user = message.from_user.first_name or "User"
    
    # മെസ്സേജിന്റെ ടൈപ്പ് അനുസരിച്ച് ഉള്ളടക്കം വേർതിരിക്കുന്നു (Text/Caption/Sticker)
    content = message.text or message.caption or (f"Sent a Sticker [{message.sticker.emoji}]" if message.sticker else "Media File")
    
    # കമാൻഡുകളും അഡ്മിൻ മെസ്സേജുകളും ഇഗ്നോർ ചെയ്യുന്നു
    if message.text and (message.text.startswith("/") or message.text.startswith("#")): return  
    if user_id in ADMINS: return 
    
    # യൂസർക്ക് മറുപടി അയക്കുന്നതിന് മുൻപ് 'Typing...' ആനിമേഷൻ കാണിക്കുന്നു (enums.ChatAction ഉപയോഗിച്ചു)
    await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    await asyncio.sleep(0.5)
    
    # യൂസർക്ക് ലഭിക്കുന്ന ഇൻസ്റ്റന്റ് റിപ്ലൈ മെസ്സേജ്
    reply_msg = await message.reply_text(
         text=f"<b>Your Request Has Been Submitted✅\n\nOTT Available Add Files With In 24Hrs.. Please Wait\n\nനിങ്ങളുടെ request അഡ്മിൻ അയച്ചിട്ടുണ്ട് ഫയൽസ് ഉണ്ടെങ്കിൽ 24മണിക്കൂറിനുള്ളിൽ ആഡ് ചെയ്യുന്നതാണ്</b>",   
         reply_markup=InlineKeyboardMarkup([
             [InlineKeyboardButton("🚫 ANY ERROR REPORT 🚫 ", url="https://t.me/Adhityan_edavattom")],
             [InlineKeyboardButton("🚸 MUST READ 🚸", url="https://telegra.ph/Request-അയകക-മനന-വയകകണടനനത-08-19")] 
         ])
    )    
    
    # അഡ്മിന് ലഭിക്കുന്ന ലോഗ് മെസ്സേജിനുള്ള ഡയറക്റ്റ് ബട്ടൺ
    log_reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 MESSAGE USER (DIRECT)", url=f"tg://user?id={user_id}")]
    ])
    
    log_text = f"<b># can_PM_MSG\n\nNᴀᴍᴇ : <a href='tg://user?id={user_id}'>{user}</a>\n\nID : <code>{user_id}</code>\n\nMᴇssᴀɢᴇ :</b> <code>{content}</code>\n\n#id{user_id}"
    
    # ഫയലിന്റെ തരം അനുസരിച്ച് അനിമേഷൻ സ്റ്റാറ്റസ് കാണിച്ചുകൊണ്ട് ലോഗ് ചാനലിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
    if message.photo:
        await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.UPLOAD_PHOTO)
        await bot.send_photo(chat_id=LOG_CHANNEL, photo=message.photo.file_id, caption=log_text, reply_markup=log_reply_markup)
    elif message.video:
        await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.UPLOAD_VIDEO)
        await bot.send_video(chat_id=LOG_CHANNEL, video=message.video.file_id, caption=log_text, reply_markup=log_reply_markup)
    elif message.sticker:
        # സ്റ്റിക്കർ ആണെങ്കിൽ ചാനലിൽ ഡീറ്റെയിൽസ് അയച്ച ശേഷം തൊട്ടുതാഴെ സ്റ്റിക്കർ അയക്കും
        await bot.send_message(chat_id=LOG_CHANNEL, text=log_text, reply_markup=log_reply_markup, disable_web_page_preview=True)
        await bot.send_sticker(chat_id=LOG_CHANNEL, sticker=message.sticker.file_id)
    else:
        await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.TYPING)
        await bot.send_message(chat_id=LOG_CHANNEL, text=log_text, reply_markup=log_reply_markup, disable_web_page_preview=True)    
    
    # 30 സെക്കൻഡ് കാത്തുനിൽക്കുന്നു
    await asyncio.sleep(30)    
    try:
        # ബോട്ടിന്റെ താത്കാലിക കൺഫർമേഷൻ മറുപടി മാത്രം ഡിലീറ്റ് ചെയ്യുന്നു
        await bot.delete_messages(
            chat_id=message.chat.id, 
            message_ids=[reply_msg.id]
        )    
    except Exception as e:
        print(f"Error deleting messages: {e}")


# =====================================================================
# 2. ADMIN SIDE: HANDLES REPLIES FROM LOG CHANNEL (TEXT, PHOTO, VIDEO, STICKER)
# =====================================================================
@Client.on_message(filters.chat(LOG_CHANNEL) & filters.reply)
async def admin_reply_to_user(bot: Client, message):
    parent_message = message.reply_to_message
    parent_text = parent_message.text or parent_message.caption
    
    if not parent_text:
        return
        
    pattern = r"#id(\d+)"
    match = re.search(pattern, parent_text)
    
    if match:
        user_id = int(match.group(1))
        reply_caption = f"<b>💬 Message From Admin:\n\n{message.caption}</b>" if message.caption else "<b>💬 Message From Admin</b>"
        
        try:
            if message.photo:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.UPLOAD_PHOTO)
                await bot.send_photo(chat_id=user_id, photo=message.photo.file_id, caption=reply_caption)
            elif message.video:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.UPLOAD_VIDEO)
                await bot.send_video(chat_id=user_id, video=message.video.file_id, caption=reply_caption)
            elif message.sticker:
                await bot.send_sticker(chat_id=user_id, sticker=message.sticker.file_id)
            elif message.text:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.TYPING)
                await bot.send_message(
                    chat_id=user_id,
                    text=f"<b>💬 Message From Admin:\n\n{message.text}</b>"
                )
            else:
                return
                
            await message.reply_text("<b>✅ മറുപടി യൂസർക്ക് വിജയകരമായി അയച്ചു!</b>")
            
        except UserIsBlocked:
            # യൂസർ ബോട്ട് ബ്ലോക്ക് ചെയ്തിട്ടുണ്ടെങ്കിൽ അഡ്മിന് ഈ മെസ്സേജ് കാണിക്കും
            await message.reply_text("<b>❌ മറുപടി അയക്കാൻ കഴിഞ്ഞില്ല! ഈ യൂസർ ബോട്ടിനെ ബ്ലോക്ക് ചെയ്തിരിക്കുകയാണ്.</b>")
            
        except Exception as e:
            await message.reply_text(f"<b>❌ മെസ്സേജ് അയക്കാൻ കഴിഞ്ഞില്ല!\nError: {e}</b>")




@Client.on_message(filters.text & filters.incoming)
async def give_filters(client, message):
    # രണ്ട് ഫങ്ക്ഷനുകളും ഒരേ സമയം ബാക്ക്ഗ്രൗണ്ടിൽ റൺ ചെയ്യാൻ ടാസ്കുകൾ ഉണ്ടാക്കുന്നു
    task1 = asyncio.create_task(global_filters(client, message))
    task2 = asyncio.create_task(auto_filter(client, message))
    
    try:
        # രണ്ട് ടാസ്കുകളും ഒരുമിച്ച് (Parallel ആയി) എക്സിക്യൂട്ട് ചെയ്യുന്നു
        await asyncio.gather(task1, task2)
    except Exception:
        # ഏതെങ്കിലും ഒന്നിൽ എറർ വന്നാൽ ബോട്ട് ക്രാഷ് ആകാതിരിക്കാൻ അവഗണിക്കുന്നു
        pass


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    
    # 1. ബട്ടൺ അമർത്തിയത് സെർച്ച് ചെയ്ത ആൾ തന്നെയാണോ എന്ന് നോക്കുന്നു
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("Search for Yourself", show_alert=True)

    # 2. കൂൾഡൗൺ പരിശോധന (സ്പാം ക്ലിക്ക് തടയാൻ)
    user_id = query.from_user.id
    now = datetime.now()
    if user_id in BUTTON_COOLDOWNS and now < BUTTON_COOLDOWNS[user_id]:
        return await query.answer("ദയവായി കുറച്ചു സമയം കാത്തിരിക്കൂ... (Slow Down)", show_alert=False)
    
    # 1 സെക്കൻഡ് കൂൾഡൗൺ നൽകുന്നു
    BUTTON_COOLDOWNS[user_id] = now + timedelta(seconds=1)

    # 3. ലോഡിങ് സ്പിന്നർ മാറ്റാൻ ഉടൻ തന്നെ ആൻസർ ചെയ്യുക
    await query.answer()

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    # ഡാറ്റാബേസ് സെർച്ച്
    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)

    if not files:
        await query.answer("no files", show_alert=True)
        return

    settings = await get_settings(query.message.chat.id)

    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}►{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if 0 < offset < 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10

    if n_offset == '':
        btn.append(
            [InlineKeyboardButton("↵ Bᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("↵ Bᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )

    # 4. ഫ്ലഡ് വെയ്റ്റ് കൂടി മാനേജ് ചെയ്യുന്ന മെസ്സേജ് എഡിറ്റിങ് ഭാഗം
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    except FloodWait as e:
        # റേറ്റ് ലിമിറ്റ് വന്നാൽ ബോട്ട് ക്രാഷാകാതെ അത്രയും സമയം വെയ്റ്റ് ചെയ്യും
        await asyncio.sleep(e.value)
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
            
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.file_name
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption, mention=query.from_user.mention)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        buttons = [[
            InlineKeyboardButton('⚙ ഉർവശി തീയറ്റേഴ്‌സ് ⚙', url='https://t.me/+RBNuafky0to1NDc1')            
         ]]
        try:
            if settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
        except QueryIdInvalid:
            await query.answer("This query is no longer valid.", show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if REQ_CHANNEL1 and not await is_requested_one(client, query):
            await query.answer("Click 🚸 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ I&II🚸 Buttons Then Click 🔃 ᴛʀʏ ᴀɢᴀɪɴ 🔃", show_alert=True)
            return
        if REQ_CHANNEL2 and not await is_requested_two(client, query):
            await query.answer("Click 🚸 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ II🚸 🍃𝖩𝗈𝗂𝗇 𝖥𝗂𝗋𝗌𝗍 & 𝖲𝖾𝖼𝗈𝗇𝖽 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 𝗔𝗳𝘁𝗲𝗿 3𝘀𝗲𝗰🍃", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.file_name
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption, mention=query.from_user.mention)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        buttons = [[
            InlineKeyboardButton('⚙ ഉർവശി തീയറ്റേഴ്‌സ് ⚙', url='https://t.me/+RBNuafky0to1NDc1')
         ]]
        await query.answer()
        xd = await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == "checksubp" else False,
            reply_markup=InlineKeyboardMarkup(
               [[
                InlineKeyboardButton('⚙ ഉർവശി തീയറ്റേഴ്‌സ് ⚙', url='https://t.me/+xlFmD30B2b9jNjQ1')            
               ]]
            )  
        )
        k = await xd.reply(text=f"<blockquote><b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\n📘ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ <b><u>10 mins</u> 🫥 <i></b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs)</i>.\n\n<b><i>ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ᴏʀ ᴀɴʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ.\n\n📘ഈ ഫയൽ 10 മിനുട്ടിനുള്ളിൽ ഇവിടെ നിന്നും ഡിലീറ്റ് ആകുന്നതാണ്... ഫയൽ എവിടെങ്കിലും Forward ചെയ്ത് Download ചെയ്യുക 🤌</i></b></blockquote>")  
        # ടൈറ്റിൽ പ്രീ-ഡിവിഡി ആണോ എന്ന് നോക്കി സമയം മാറ്റുന്നു
        if title and any(keyword in title.lower() for keyword in ['predvd', 'predvdrip']):
            f_caption += "\n⚠️<b><i>ഈ മൂവിയുടെ ഫയൽ എവിടെയെങ്കിലും ഫോർവേഡ് ചെയ്തു വെക്കുക എന്നിട്ട് ഡൗൺലോഡ് ചെയ്യുക\n\n3 മിനിറ്റിൽ ഇവിടുന്ന് ഡിലീറ്റ് ആവും🗑\n\n⚠️Forward the file of this Movie somewhere and download it\n\nWill be deleted from here in 3 minutes🗑</i></b>"
            inline_keyboard = [[
                InlineKeyboardButton('⚙ ഉർവശി തീയറ്റേഴ്‌സ് ⚙', url='https://t.me/+xlFmD30B2b9jNjQ1')
            ]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            
            # ഡിലീറ്റ് ചെയ്യുന്നതിന് മുൻപ് ക്യാപ്ഷൻ എഡിറ്റ് ചെയ്യുന്നു
            try:
                await xd.edit_caption(caption=f_caption, reply_markup=reply_markup)
            except Exception as e:
                print(f"Caption edit error: {e}")
                
            # പ്രീ-ഡിവിഡി ആണെങ്കിൽ 3 മിനിറ്റ് (180 സെക്കൻഡ്) മാത്രം വെയിറ്റ് ചെയ്യുന്നു
            await asyncio.sleep(180)                   
        else:
            # സാധാരണ ഫയൽ ആണെങ്കിൽ 10 മിനിറ്റ് (600 സെക്കൻഡ്) വെയിറ്റ് ചെയ്യുന്നു
            await asyncio.sleep(600)
            
        # അവസാനമായി രണ്ട് മെസ്സേജുകളും ഡിലീറ്റ് ചെയ്യുന്നു (ഒരു തവണ മാത്രം)
        try:
            await xd.delete()
        except Exception:
            pass
            
        try:
            await k.delete()
        except Exception:
            pass

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fᴇᴛᴄʜɪɴɢ Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} ᴏɴ DB... Pʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        files_media1, files_media2, total_media = await get_bad_files(keyword)        
        await query.message.edit_text(f"<b>Fᴏᴜɴᴅ {total_media} Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nFɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇss ᴡɪʟʟ sᴛᴀʀᴛ ɪɴ 5 sᴇᴄᴏɴᴅs!</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                # Delete files from Media collection
                for file in files_media1:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
                # Delete files from Mediaa collection
                for file in files_media2:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Mediaa.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception
                await query.message.edit_text(f'Eʀʀᴏʀ: {e}')
            else:
                await query.message.edit_text(f"<b>Pʀᴏᴄᴇss Cᴏᴍᴘʟᴇᴛᴇᴅ ғᴏʀ ғɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ !\n\nSᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}.</b>")
            
    elif query.data == "pages":
        await query.answer()
    
    elif query.data == "start":
        buttons = [
               InlineKeyboardButton('⚙ ഉർവശി തീയറ്റേഴ്‌സ് ⚙', url=f'https://t.me/+xlFmD30B2b9jNjQ1')               
        ]       
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)        
        tot = await Media.count_documents()
        tota = await Mediaa.count_documents()
        total = tot + tota
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        stats = await clientDB.command('dbStats')
        used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))        
        free_dbSize = 512-used_dbSize
        stats2 = await clientDB2.command('dbStats')
        used_dbSize2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_dbSize2 = 512-used_dbSize2
        stats3 = await clientDB3.command('dbStats')
        used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_dbSize3 = 512-used_dbSize3        
        await query.message.edit_text(
            text=script.STATUS_TXT2.format(total, tot, round(used_dbSize2, 2), round(free_dbSize2, 2), tota, round(used_dbSize3, 2), round(free_dbSize3, 2), users, chats, round(used_dbSize, 2), round(free_dbSize, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        if query.from_user.id in ADMINS:
            await query.message.edit_text(text=script.STATUS_TXT.format(total, users, chats, monsize, free), reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nIᴛꜱ ᴏɴʟʏ ғᴏʀ ᴍʏ ADMINS\n\n©MCU MOVIES", show_alert=True)
            await query.message.edit_text(text="നോക്കി നിന്നോ ഇപ്പോൾ കിട്ടും 😏", reply_markup=reply_markup)
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        tot = await Media.count_documents()
        tota = await Mediaa.count_documents()
        total = tot + tota
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        stats = await clientDB.command('dbStats')
        used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))        
        free_dbSize = 512-used_dbSize
        stats2 = await clientDB2.command('dbStats')
        used_dbSize2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_dbSize2 = 512-used_dbSize2
        stats3 = await clientDB3.command('dbStats')
        used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_dbSize3 = 512-used_dbSize3        
        await query.message.edit_text(
            text=script.STATUS_TXT2.format(total, tot, round(used_dbSize2, 2), round(free_dbSize2, 2), tota, round(used_dbSize3, 2), round(free_dbSize3, 2), users, chats, round(used_dbSize, 2), round(free_dbSize, 2)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Piracy Is Crime')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Bot PM', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],                
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('Piracy Is Crime')


async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        
        # 0. ടെക്സ്റ്റ് മെസ്സേജ് ആണെന്ന് ഉറപ്പാക്കുന്നു (മീഡിയ ഫയലുകൾ വന്നാൽ ക്രാഷ് ആകില്ല)
        if not message.text or message.text.startswith("/"): 
            return  # ignore commands
            
        if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
            
        if 0 < len(message.text) < 100:
            search = message.text.lower()                       

            # 1. കണ്ണിൽ കാണാത്ത എല്ലാ  ഹിഡൻ യുണികോഡ് ക്യാരക്റ്ററുകളും നീക്കം ചെയ്യുന്നു
            search = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', search)
            
            # 2. നോൺ-ബ്രേക്കിംഗ് സ്പേസുകൾ ഉൾപ്പെടെയുള്ള എല്ലാ പ്രത്യേക സ്പേസുകളെയും സാധാരണ സ്പേസ് ആക്കുന്നു
            search = re.sub(r'[\s\u00a0\u2000-\u200a\u202f\u205f\u3000]+', ' ', search)
            
            # 3. അപ്പോസ്ട്രോഫിയും വളഞ്ഞ സിംഗിൾ കോമകളും പൂർണ്ണമായി നീക്കം ചെയ്യുന്നു (Newton's -> Newtons)
            search = re.sub(r"['‘’]", "", search)
            
            # 4. അക്കങ്ങൾ വേർതിരിക്കുന്നു (kgf2 -> kgf 2, പക്ഷെ 3rd, 2nd, 1st എന്നിവ മാറ്റില്ല)
            if not re.search(r"\b\d+(st|nd|rd|th)\b", search, re.IGNORECASE):
                search = re.sub(r"([a-zA-Z]+)([0-9]+)", r"\1 \2", search)
                search = re.sub(r"([0-9]+)([a-zA-Z]+)", r"\1 \2", search)
                                    
            # 5. ബാക്കി ചിഹ്നങ്ങളും ബ്രാക്കറ്റുകളും മാറ്റി സ്പേസ് ആക്കുന്നു
            search = re.sub(r"[-_,#&?/( )\[\]\\\":\.¡%“”]", " ", search)
                         
            # 6. ഒട്ടിനിൽക്കുന്ന സിനിമ വാക്കുകൾ മാറ്റുന്നു (\b ചേർത്തതു കൊണ്ട് വാക്ക് പൂർണ്ണമാണെങ്കിൽ മാത്രമേ മാറൂ)
            search = re.sub(r"\b(movie(s)?|hd|full|print|file)\b", "", search, flags=re.IGNORECASE)                       
                                   
            # 7 & 8. [വേഗത കൂട്ടിയ ഭാഗം] വലിയ ലൂപ്പും വലിയ Regex-ും ഒഴിവാക്കി, ഒരൊറ്റ സെറ്റ് (Set) വഴി വാക്കുകൾ ফിൽട്ടർ ചെയ്യുന്നു
            find = search.split(" ")
            removes = {
                "pls", "plz", "please", "send", "snd", 
                "gib", "veno", 
                "undo", "ayakkumo", "ayakkamo", "und", "move", 
                "multi", "dubb", "dub", "bro", "bruh", "broh", "dubbed", "link", 
                "venum", "iruka", "pannunga", "pannungga", "anuppunga", "anupunga", "anuppungga", 
                "anupungga", "subtile", "kitti", "kitty", "tharu", "kittumo", "kittum"              
            }
            search = " ".join([w for w in find if w not in removes])
            
            # 9. അനാവശ്യ സ്പേസുകൾ കളയുന്നു
            search = re.sub(r"\s+", " ", search).strip()                                                
            
            # ഫിൽട്ടറിംഗിന് ശേഷം വാക്കുകൾ ഒന്നും ബാക്കിയില്ലെങ്കിൽ ഡാറ്റാബേസ് സെർച്ച് ഒഴിവാക്കുന്നു
            if not search:
                return

            # 10. ഡാറ്റാബേസിൽ തിരയുന്നു
            files, offset, total_results = await get_search_results(search, offset=0, filter=True)
            if not files:
                # === CUSTOM CODE: ഗ്രൂപ്പുകളിൽ നിന്നുള്ള കിട്ടാത്ത ഫയലുകൾ മാത്രം സേവ് ചെയ്യുന്നു ===
                from pyrogram import enums
                if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    try:
                        from datetime import datetime, timedelta
                        from database.ia_filterdb import db as clientDB
                        log_db = clientDB.search_logs
                        current_time = datetime.now()

                        # 24 മണിക്കൂർ കഴിഞ്ഞ പഴയ ലോഗുകൾ നീക്കം ചെയ്യുന്നു
                        time_limit = current_time - timedelta(hours=24)
                        await log_db.delete_many({"timestamp": {"$lt": time_limit}})

                        # വാക്ക് നിലവിലുണ്ടോ എന്ന് നോക്കുന്നു (Case-insensitive)
                        search_query_lower = search.lower()
                        existing = await log_db.find_one({"word_lower": search_query_lower})

                        if existing:
                            # കൗണ്ട് 1 കൂട്ടുന്നു
                            await log_db.update_one(
                                {"_id": existing["_id"]},
                                {"$inc": {"count": 1}, "$set": {"timestamp": current_time}}
                            )
                        else:
                            # പുതുതായി ഡാറ്റാബേസിലേക്ക് ചേർക്കുന്നു
                            await log_db.insert_one({
                                "word": search,
                                "word_lower": search_query_lower,
                                "count": 1,
                                "timestamp": current_time
                            })
                    except Exception as log_error:
                        if 'logger' in locals() or 'logger' in globals():
                            logger.error(f"Error in search logging: {log_error}")
                        else:
                            print(f"Error in search logging: {log_error}")
                # === CUSTOM CODE END ===

                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)      
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        # ഇതിന് താഴോട്ട് നിങ്ങളുടെ ഫയലിലുള്ള ബാക്കി കോഡ് (ബട്ടണുകൾ നിർമ്മിക്കുന്ന ഭാഗം) അതുപോലെ തന്നെ വെക്കുക.
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}►{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        try:
            offset = int(offset)
        except ValueError:
            offset = 0
    else:
        offset = 0
    
    if offset == 0:
        btn.append(
            [InlineKeyboardButton(text="🍃 ഉർവശി തീയറ്റേഴ്‌സ് 🍃", url="https://t.me/+eb__Eg3RS2IyZWQ1")]
        )
    else:
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
            InlineKeyboardButton(text="Nᴇxᴛ ⤷", callback_data=f"next_{req}_{key}_{offset}")]
        )
        
    # IMDb പൂർണ്ണമായും ഒഴിവാക്കി, നേരിട്ട് സാധാരണ ടെക്സ്റ്റ് ക്യാപ്ഷൻ സെറ്റ് ചെയ്യുന്നു
    cap = f"<b><i><blockquote>►Film : {search}\n►Rating : {random.choice(RATING)}\n►Genre : {random.choice(GENRES)}</i></blockquote></b>\n<b><i>©𝐓𝐞𝐚𝐦 𝐔𝐫𝐯𝐚𝐬𝐡𝐢 𝐓𝐡𝐞𝐚𝐭𝐞𝐫𝐬™️</i></b>"         
    
    # ഫയലുകളുടെ ബട്ടണുകളോടൊപ്പം മെസ്സേജ് ഗ്രൂപ്പിലേക്ക് അയക്കുന്നു
    fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
       
    await asyncio.sleep(300)
    await fmsg.delete()
        


# യൂസർ 'Close 🚫' ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ ബോട്ടിന്റെ മെസ്സേജ് മാത്രം ഡിലീറ്റ് ചെയ്യും
@Client.on_callback_query(filters.regex(r'^close_data$'))
async def close_callback_handler(client, query: CallbackQuery):
    try:
        # ബോട്ട് അയച്ച മെസ്സേജ് മാത്രം ഡിലീറ്റ് ചെയ്യുന്നു
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error in close button callback: {e}")



async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text    
    
    # 1. മെസ്സേജിലെ ആവശ്യമില്ലാത്ത വാക്കുകൾ ഒഴിവാക്കുന്നു
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", mv_rqst, flags=re.IGNORECASE
    )    
    clean_title = query.strip()
    
    # ഡാറ്റാബേസ് സെർച്ചിങ് പൂർണ്ണമായി ഒഴിവാക്കാൻ സിനിമകൾ ഇല്ല (None) എന്ന് നേരിട്ട് ഉറപ്പിക്കുന്നു
    movies = None        
    
    # ----------------------------------------------------
    # സിനിമ ഇല്ലെങ്കിൽ നേരിട്ട് (Direct Reply) പുതിയ ബട്ടണുകൾ നൽകുന്നു
    # ----------------------------------------------------
    if not movies:
        encoded_title = urllib.parse.quote_plus(clean_title)
        
        # നിങ്ങൾ ആവശ്യപ്പെട്ട 5 ബട്ടണുകൾ ഇവിടെ കൃത്യമായി ക്രമീകരിച്ചിരിക്കുന്നു
        button = [
            [
                InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ ᴏɴ ɢᴏᴏɢʟᴇ 🔎', url=f"https://www.google.com/search?q={encoded_title}")
            ],
            [
                InlineKeyboardButton('🎬 IMDb Search', url=f"https://imdb.com/find?q={encoded_title}"),
                InlineKeyboardButton('🎥 TMDb Search', url=f"https://themoviedb.org/search?query={encoded_title}")
            ],
            [         
                InlineKeyboardButton('🗣️ RequestAdmin', url="http://t.me/Promoviesearcherbot"), # ഇവിടെ നിങ്ങളുടെ മെയിൻ ചാനൽ ലിങ്ക് നൽകാം
                InlineKeyboardButton('🚫 Close', callback_data='close_data')
            ]
        ]        
        
        k = await msg.reply_text(
            text=script.MOVREQ_TXT,
            reply_markup=InlineKeyboardMarkup(button),
            reply_to_message_id=mv_id
        )
        
        # 60 സെക്കന്റിന് ശേഷം മെസ്സേജ് തനിയെ ഡിലീറ്റ് ചെയ്യും
        await asyncio.sleep(60)
        try:
            await k.delete()
        except Exception:
            pass
        return



async def global_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            knd3 = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(120)
                            await knd3.delete()                           

                        else:
                            button = eval(btn)
                            knd2 = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            await asyncio.sleep(120)
                            await knd2.delete()                    

                    elif btn == "[]":
                        knd1 = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(120)
                        await knd1.delete()                        

                    else:
                        button = eval(btn)
                        knd = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        await asyncio.sleep(120)
                        await knd.delete()
                        
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
        
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
