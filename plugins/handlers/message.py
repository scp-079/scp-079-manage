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
from copy import deepcopy

from pyrogram import Client, Filters, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from ..functions.etc import code, button_data, general_link, get_now, get_report_record, get_text, random_str
from ..functions.etc import thread, user_mention
from ..functions.file import save
from ..functions.filters import exchange_channel, error_channel, from_user, hide_channel, is_error_channel
from ..functions.filters import logging_channel, manage_group, watch_channel
from ..functions.group import get_message
from ..functions.receive import receive_add_bad, receive_leave_info, receive_leave_request, receive_remove_bad
from ..functions.receive import receive_status_reply, receive_text_data, receive_user_score, receive_watch_user
from ..functions.telegram import send_message
from ..functions.user import check_subject

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user & Filters.forwarded
                   & (error_channel | logging_channel | watch_channel)
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def action_ask(client: Client, message: Message) -> bool:
    # Ask how to deal with the report message
    try:
        cid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id
        rid = message.forward_from_message_id
        channel_id = message.forward_from_chat.id
        report_message = get_message(client, channel_id, rid)
        report_text = get_text(report_message)
        action = ""
        key = random_str(8)
        while glovar.actions.get(key):
            key = random_str(8)

        record = get_report_record(report_message)
        if is_error_channel(None, message) and report_message.reply_to_message:
            action = "recall"
        elif (report_message and report_text
              and not report_message.forward_date
              and re.search("^项目编号：", report_text)):
            if record["project"] in glovar.receivers["except"]:
                # TODO 解决无具体证据的问题
                if report_message.reply_to_message or record["type"] in {"服务"}:
                    action = "error"
            elif record["project"] == "LANG" and "名称" in record["rule"]:
                action = "error"
            elif record["project"] == "WARN":
                if report_message.reply_to_message or record["type"] == "服务消息":
                    action = "bad"
            elif record["project"] == "MANAGE" and not re.search("^状态：已删除$", report_text, re.M):
                if record["status"] == "已重置":
                    if record["origin"] in glovar.receivers["except"]:
                        action = "error"
                    elif record["origin"] == "WARN":
                        action = "bad"
                elif record["status"] == "已解禁" or record["status"] == "已解明":
                    action = "mole"
                elif record["status"] == "已收录":
                    action = "innocent"
            elif record["status"] != "已清除":
                if record["status"] == "已删除":
                    action = "redact"
                else:
                    action = "delete"

        if action:
            action_text = glovar.names[action]
            glovar.actions[key] = {
                "lock": False,
                "time": get_now(),
                "mid": 0,
                "aid": aid,
                "action": action,
                "message": report_message,
                "record": record
            }
            text = (f"管理员：{user_mention(aid)}\n"
                    f"执行操作：{code(action_text)}\n"
                    f"状态：{code('等待操作')}\n")
            data_proceed = button_data(action, "proceed", key)
            data_cancel = button_data(action, "cancel", key)
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
            if action not in {"delete", "redact", "recall"}:
                data_delete = button_data(action, "delete", key)
                markup_list[0].append(
                    InlineKeyboardButton(
                        text="删除",
                        callback_data=data_delete
                    )
                )
            elif action == "bad" and not report_message.reply_to_message:
                data_delete = button_data("redact", "delete", key)
                markup_list[0].append(
                    InlineKeyboardButton(
                        text="清除",
                        callback_data=data_delete
                    )
                )

            markup = InlineKeyboardMarkup(markup_list)
            result = send_message(client, cid, text, mid, markup)
            if result:
                glovar.actions[key]["mid"] = result.message_id
                glovar.actions_pure[key] = {}
                for item in glovar.actions[key]:
                    if item in {"lock", "time", "mid"}:
                        glovar.actions_pure[key][item] = deepcopy(glovar.actions[key][item])

                save("actions_pure")
            else:
                glovar.actions.pop(key, {})
                
        return True
    except Exception as e:
        logger.warning(f"Check error error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user & Filters.forwarded
                   & ~error_channel & ~logging_channel & ~watch_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def check_forwarded(client: Client, message: Message) -> bool:
    # Check forwarded messages
    try:
        # Read basic information
        cid = message.chat.id
        mid = message.message_id
        # Check debug message automatically without using "/check" reply to that message
        if message.forward_from_chat and message.forward_from_chat.id == glovar.debug_channel_id:
            message.reply_to_message = message

        text, markup = check_subject(client, message)
        if text:
            thread(send_message, (client, cid, text, mid, markup))

        return True
    except Exception as e:
        logger.warning(f"Check forwarded error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix), group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
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

                        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                                f"执行操作：{code('频道转移')}\n"
                                f"应急频道：{code((lambda x: '启用' if x else '禁用')(glovar.should_hide))}\n")
                        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message) -> bool:
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
                            receive_user_score(sender, data)

                elif sender == "CLEAN":
                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "LANG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "LONG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "NOFLOOD":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "NOPORN":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "NOSPAM":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "status":
                        if action_type == "reply":
                            receive_status_reply(client, message, sender, data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "RECHECK":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "watch":
                            receive_watch_user(data)

                    elif action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "USER":
                    if action == "leave":
                        if action_type == "info":
                            receive_leave_info(client, sender, data)
                        elif action_type == "request":
                            receive_leave_request(client, sender, data)

                    elif action == "remove":
                        if action_type == "bad":
                            receive_remove_bad(data)

                    elif action == "status":
                        if action_type == "reply":
                            receive_status_reply(client, message, sender, data)

                elif sender == "WARN":

                    if action == "update":
                        if action_type == "score":
                            receive_user_score(sender, data)

                elif sender == "WATCH":

                    if action == "add":
                        if action_type == "watch":
                            receive_watch_user(data)

                    elif action == "status":
                        if action_type == "reply":
                            receive_status_reply(client, message, sender, data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)

    return False
