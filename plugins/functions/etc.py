# SCP-079-MANAGE - One ring to rule them all
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-MANAGE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from html import escape
from json import dumps, loads
from random import choice, uniform
from string import ascii_letters, digits
from threading import Thread
from time import sleep, time
from typing import Any, Callable, Dict, List, Optional, Union

from cryptography.fernet import Fernet
from pyrogram import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors import FloodWait

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def bold(text: Any) -> str:
    # Get a bold text
    try:
        text = str(text).strip()
        if text:
            return f"<b>{escape(text)}</b>"
    except Exception as e:
        logger.warning(f"Bold error: {e}", exc_info=True)

    return ""


def button_data(action: str, action_type: str = None, data: Union[int, str] = None) -> Optional[bytes]:
    # Get a button's bytes data
    result = None
    try:
        button = {
            "a": action,
            "t": action_type,
            "d": data
        }
        result = dumps(button).replace(" ", "").encode("utf-8")
    except Exception as e:
        logger.warning(f"Button data error: {e}", exc_info=True)

    return result


def code(text: Any) -> str:
    # Get a code text
    try:
        text = str(text).strip()
        if text:
            return f"<code>{escape(text)}</code>"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return ""


def code_block(text: Any) -> str:
    # Get a code block text
    try:
        text = str(text).rstrip()
        if text:
            return f"<pre>{escape(text)}</pre>"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return ""


def crypt_str(operation: str, text: str, key: str) -> str:
    # Encrypt or decrypt a string
    result = ""
    try:
        f = Fernet(key)
        text = text.encode("utf-8")
        if operation == "decrypt":
            result = f.decrypt(text)
        else:
            result = f.encrypt(text)

        result = result.decode("utf-8")
    except Exception as e:
        logger.warning(f"Crypt str error: {e}", exc_info=True)

    return result


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general link
    result = ""
    try:
        text = str(text).strip()
        link = link.strip()
        if text and link:
            result = f'<a href="{link}">{escape(text)}</a>'
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_admin(message: Message) -> int:
    # Get message's origin commander
    result = 0
    try:
        text = get_text(message)
        if not text.strip():
            return 0

        first_line_list = text.split("\n")[0].split(lang("colon"))
        if lang("admin") in first_line_list[0]:
            result = get_int(first_line_list[-1])
    except Exception as e:
        logger.warning(f"Get admin error: {e}", exc_info=True)

    return result


def get_channel_link(message: Union[int, Message]) -> str:
    # Get a channel reference link
    text = ""
    try:
        text = "https://t.me/"
        if isinstance(message, int):
            text += f"c/{str(message)[4:]}"
        else:
            if message.chat.username:
                text += f"{message.chat.username}"
            else:
                cid = message.chat.id
                text += f"c/{str(cid)[4:]}"
    except Exception as e:
        logger.warning(f"Get channel link error: {e}", exc_info=True)

    return text


def get_callback_data(message: Message) -> List[dict]:
    # Get a message's inline button's callback data
    callback_data_list = []
    try:
        if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
            reply_markup = message.reply_markup
            if reply_markup.inline_keyboard:
                inline_keyboard = reply_markup.inline_keyboard
                if inline_keyboard:
                    for button_row in inline_keyboard:
                        for button in button_row:
                            if button.callback_data:
                                callback_data = button.callback_data
                                callback_data = loads(callback_data)
                                callback_data_list.append(callback_data)
    except Exception as e:
        logger.warning(f"Get callback data error: {e}", exc_info=True)

    return callback_data_list


def get_command_context(message: Message) -> (str, str):
    # Get the type "a" and the context "b" in "/command a b"
    command_type = ""
    command_context = ""
    try:
        text = get_text(message)
        command_list = text.split(" ")
        if len(list(filter(None, command_list))) > 1:
            i = 1
            command_type = command_list[i]
            while command_type == "" and i < len(command_list):
                i += 1
                command_type = command_list[i]

            command_context = text[1 + len(command_list[0]) + i + len(command_type):].strip()
    except Exception as e:
        logger.warning(f"Get command context error: {e}", exc_info=True)

    return command_type, command_context


def get_command_type(message: Message) -> str:
    # Get the command type "a" in "/command a"
    result = ""
    try:
        text = get_text(message)
        command_list = list(filter(None, text.split(" ")))
        result = text[len(command_list[0]):].strip()
    except Exception as e:
        logger.warning(f"Get command type error: {e}", exc_info=True)

    return result


def get_int(text: str) -> Optional[int]:
    # Get a int from a string
    result = None
    try:
        result = int(text)
    except Exception as e:
        logger.info(f"Get int error: {e}", exc_info=True)

    return result


def get_list_page(the_list: list, action: str, action_type: str, page: int) -> (list, InlineKeyboardMarkup):
    # Generate a list for elements and markup buttons
    markup = None
    try:
        per_page = glovar.per_page
        quo = int(len(the_list) / per_page)
        if quo == 0:
            return the_list, None

        page_count = quo + 1

        if len(the_list) % per_page == 0:
            page_count = page_count - 1

        if page != page_count:
            the_list = the_list[(page - 1) * per_page:page * per_page]
        else:
            the_list = the_list[(page - 1) * per_page:len(the_list)]

        if page_count == 1:
            return the_list, markup

        if page == 1:
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=lang("page").format(page),
                            callback_data=button_data("none")
                        ),
                        InlineKeyboardButton(
                            text=">>",
                            callback_data=button_data(action, action_type, page + 1)
                        )
                    ]
                ]
            )
        elif page == page_count:
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="<<",
                            callback_data=button_data(action, action_type, page - 1)
                        ),
                        InlineKeyboardButton(
                            text=lang("page").format(page),
                            callback_data=button_data("none")
                        )
                    ]
                ]
            )
        else:
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="<<",
                            callback_data=button_data(action, action_type, page - 1)
                        ),
                        InlineKeyboardButton(
                            text=lang("page").format(page),
                            callback_data=button_data("none")
                        ),
                        InlineKeyboardButton(
                            text=">>",
                            callback_data=button_data(action, action_type, page + 1)
                        )
                    ]
                ]
            )
    except Exception as e:
        logger.warning(f"Get list page error: {e}", exc_info=True)

    return the_list, markup


def get_now() -> int:
    # Get time for now
    result = 0
    try:
        result = int(time())
    except Exception as e:
        logger.warning(f"Get now error: {e}", exc_info=True)

    return result


def get_report_record(message: Message) -> Dict[str, str]:
    # Get report message's full record
    record = {
        "project": "",
        "origin": "",
        "status": "",
        "uid": "",
        "level": "",
        "rule": "",
        "type": "",
        "game": "",
        "lang": "",
        "length": "",
        "freq": "",
        "score": "",
        "bio": "",
        "name": "",
        "from": "",
        "more": "",
        "unknown": ""
    }
    try:
        if not message.text:
            return record

        record_list = message.text.split("\n")
        for r in record_list:
            if re.search(f"^{lang('project')}{lang('colon')}", r):
                record_type = "project"
            elif re.search(f"^{lang('project_origin')}{lang('colon')}", r):
                record_type = "origin"
            elif re.search(f"^{lang('status')}{lang('colon')}", r):
                record_type = "status"
            elif re.search(f"^{lang('user_id')}{lang('colon')}", r):
                record_type = "uid"
            elif re.search(f"^{lang('level')}{lang('colon')}", r):
                record_type = "level"
            elif re.search(f"^{lang('rule')}{lang('colon')}", r):
                record_type = "rule"
            elif re.search(f"^{lang('message_type')}{lang('colon')}", r):
                record_type = "type"
            elif re.search(f"^{lang('message_game')}{lang('colon')}", r):
                record_type = "game"
            elif re.search(f"^{lang('message_lang')}{lang('colon')}", r):
                record_type = "lang"
            elif re.search(f"^{lang('message_len')}{lang('colon')}", r):
                record_type = "length"
            elif re.search(f"^{lang('message_freq')}{lang('colon')}", r):
                record_type = "freq"
            elif re.search(f"^{lang('user_score')}{lang('colon')}", r):
                record_type = "score"
            elif re.search(f"^{lang('user_bio')}{lang('colon')}", r):
                record_type = "bio"
            elif re.search(f"^{lang('user_name')}{lang('colon')}", r):
                record_type = "name"
            elif re.search(f"^{lang('from_name')}{lang('colon')}", r):
                record_type = "from"
            elif re.search(f"^{lang('more')}{lang('colon')}", r):
                record_type = "more"
            else:
                record_type = "unknown"

            record[record_type] = r.split(f"{lang('colon')}")[-1]
    except Exception as e:
        logger.warning(f"Get report record error: {e}", exc_info=True)

    return record


def get_subject(message: Message) -> (str, str, bool):
    # Get the subject from the message's text
    id_text = ""
    reason = ""
    from_check = False
    try:
        # Do not treat this message as a valid command
        if (message.forward_from or message.forward_from_chat) and not message.reply_to_message:
            return id_text, reason, from_check

        # Read command
        id_text, reason = get_command_context(message)

        # Override command result if there is a reply_to_message
        if message.reply_to_message:
            # /command reason
            if not reason:
                reason = id_text

            if message.reply_to_message.from_user.is_self:
                from_check = True

            text = get_text(message.reply_to_message)
            # Check if the message includes object ID
            if re.search(f"^({lang('user_id')}|{lang('channel_id')}|{lang('group_id')}){lang('colon')}", text, re.M):
                text_list = text.split("\n")
                # Check line by line
                for t in text_list:
                    # Check if the line includes object ID
                    if re.search(f"^({lang('user_id')}|{lang('channel_id')}|{lang('group_id')}){lang('colon')}", t):
                        # Get the right object ID
                        if (re.search(f"^{lang('group_id')}{lang('colon')}", t)
                                and (re.search(f"^({lang('user_id')}|{lang('group_id')}){lang('colon')}", text, re.M)
                                     or message.forward_from_chat)):
                            continue
                        else:
                            id_text = t.split(lang("colon"))[1]
                            return id_text, reason, from_check
    except Exception as e:
        logger.warning(f"Get subject error: {e}", exc_info=True)

    return id_text, reason, from_check


def get_text(message: Message) -> str:
    # Get message's text
    text = ""
    try:
        if not message:
            return ""

        the_text = message.text or message.caption
        if the_text:
            text += the_text
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def italic(text: Any) -> str:
    # Get italic text
    try:
        text = str(text).strip()
        if text:
            return f"<i>{escape(text)}</i>"
    except Exception as e:
        logger.warning(f"Italic error: {e}", exc_info=True)

    return ""


def lang(text: str) -> str:
    # Get the text
    result = ""
    try:
        result = glovar.lang.get(text, text)
    except Exception as e:
        logger.warning(f"Lang error: {e}", exc_info=True)

    return result


def message_link(message: Message) -> str:
    # Get a message link in a channel
    text = ""
    try:
        mid = message.message_id
        text = f"{get_channel_link(message)}/{mid}"
    except Exception as e:
        logger.warning(f"Message link error: {e}", exc_info=True)

    return text


def random_str(i: int) -> str:
    # Get a random string
    text = ""
    try:
        text = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return text


def thread(target: Callable, args: tuple) -> bool:
    # Call a function using thread
    try:
        t = Thread(target=target, args=args)
        t.daemon = True
        t.start()

        return True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)

    return False


def user_mention(uid: int) -> str:
    # Get a mention text
    text = ""
    try:
        text = general_link(f"{uid}", f"tg://user?id={uid}")
    except Exception as e:
        logger.warning(f"User mention error: {e}", exc_info=True)

    return text


def wait_flood(e: FloodWait) -> bool:
    # Wait flood secs
    try:
        sleep(e.x + uniform(0.5, 1.0))

        return True
    except Exception as e:
        logger.warning(f"Wait flood error: {e}", exc_info=True)

    return False
