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

from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from ..functions.channel import receive_text_data
from ..functions.etc import code, button_data, get_report_record, get_text, random_str, thread, user_mention
from ..functions.filters import exchange_channel, hide_channel, logging_channel, manage_group
from ..functions.group import get_message
from ..functions.manage import info_left_group, request_leave_group
from ..functions.telegram import send_message
from ..functions.user import check_object, receive_bad_user, receive_remove_user, receive_user_score, receive_watch_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group & Filters.forwarded & logging_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def action_ask(client: Client, message: Message):
    # Ask how to deal with the report message
    try:
        cid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id
        rid = message.forward_from_message_id
        report_message = get_message(client, glovar.logging_channel_id, rid)
        report_text = get_text(report_message)
        if (report_message and report_text
                and not report_message.forward_date
                and re.search("^项目编号：", report_text)
                and not re.search("^状态：已删除$", report_text, re.M)):
            record = get_report_record(report_message)
            action = ""
            action_key = random_str(8)
            if record["project"] in glovar.receivers["except"]:
                action = "error"
            elif record["project"] == "WARN":
                action = "bad"
            elif record["project"] == "MANAGE":
                if record["status"] == "已重置":
                    if record["origin"] in glovar.receivers["except"]:
                        action = "error"
                    elif record["origin"] == "WARN":
                        action = "bad"
                elif record["status"] == "已解禁" or record["status"] == "已解明":
                    action = "mole"
                elif record["status"] == "已收录":
                    action = "innocent"

            if action:
                action_text = glovar.names[action]
                glovar.actions[action_key] = {
                    "lock": False,
                    "aid": aid,
                    "action": action,
                    "message": report_message,
                    "record": record
                }
                text = (f"管理员：{user_mention(aid)}\n"
                        f"执行操作：{code(action_text)}\n"
                        f"状态：{code('等待操作')}\n")
                data_proceed = button_data(action, "proceed", action_key)
                data_cancel = button_data(action, "cancel", action_key)
                markup_list = [
                    [
                        InlineKeyboardButton(
                            text="处理",
                            callback_data=data_proceed
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="取消",
                            callback_data=data_cancel
                        )
                    ]
                ]
                if report_message.reply_to_message:
                    data_delete = button_data(action, "delete", action_key)
                    markup_list[0].append(
                        InlineKeyboardButton(
                            text="删除",
                            callback_data=data_delete
                        )
                    )

                markup = InlineKeyboardMarkup(markup_list)
                thread(send_message, (client, cid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Check error error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & manage_group & Filters.forwarded & ~logging_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def check_forwarded(client: Client, message: Message):
    # Check forwarded messages
    try:
        # Read basic information
        cid = message.chat.id
        mid = message.message_id
        text, markup = check_object(client, message)
        if text:
            thread(send_message, (client, cid, text, mid, markup))
    except Exception as e:
        logger.warning(f"Check object error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix), group=-1)
def exchange_emergency(_: Client, message: Message):
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)
        if data:
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            if "EMERGENCY" in receivers:
                if action == "backup":
                    if action_type == "hide":
                        if data is True:
                            glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message):
    # Process the data in exchange channel
    try:
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            # This will look awkward,
            # seems like it can be simplified,
            # but this is to ensure that the permissions are clear,
            # so it is intentionally written like this
            if glovar.sender in receivers:
                if sender == "CAPTCHA":

                    if action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "CLEAN":
                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "LANG":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "LONG":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "NOFLOOD":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "NOPORN":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "NOSPAM":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "RECHECK":

                    if action == "add":
                        if action_type == "bad":
                            receive_bad_user(data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "USER":
                    if action == "leave":
                        if action_type == "info":
                            info_left_group(client, sender, data)
                        elif action_type == "request":
                            request_leave_group(client, sender, data)
                    elif action == "remove":
                        if action_type == "bad":
                            receive_remove_user(data)

                elif sender == "WARN":

                    if action == "update":
                        if action_type == "score":
                            receive_user_score(data)

                elif sender == "WATCH":

                    if action == "add":
                        if action_type == "watch":
                            receive_watch_user(data)
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
