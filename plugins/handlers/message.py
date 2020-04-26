# SCP-079-MANAGE - One ring to rule them all
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from ..functions.channel import forward_evidence
from ..functions.etc import code, button_data, general_link, get_now, get_report_record, get_text, lang, random_str
from ..functions.etc import thread, mention_id, message_link
from ..functions.file import save
from ..functions.filters import exchange_channel, error_channel, from_user, hide_channel, is_exchange_channel
from ..functions.filters import is_error_channel, logging_channel, manage_group, watch_channel
from ..functions.group import get_message
from ..functions.receive import receive_add_bad, receive_config_show, receive_leave_info, receive_leave_request
from ..functions.receive import receive_remove_white, receive_status_reply, receive_text_data, receive_user_score
from ..functions.receive import receive_watch_user, receive_white_users
from ..functions.telegram import send_message
from ..functions.user import check_subject

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.forwarded
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & manage_group
                   & (exchange_channel | error_channel | logging_channel | watch_channel)
                   & from_user)
def action_ask(client: Client, message: Message) -> bool:
    # Ask how to deal with the report message
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id
        fid = message.forward_from_message_id
        channel_id = message.forward_from_chat.id
        report_message = get_message(client, channel_id, fid)
        r_message = report_message.reply_to_message
        report_text = get_text(report_message)
        record = get_report_record(report_message)

        # Init
        action = ""

        # Rollback
        if is_exchange_channel(None, message):
            data = receive_text_data(report_message)

            if not data:
                return True

            data_action = data["action"]
            data_action_type = data["type"]

            if data_action == "backup":
                if data_action_type == "data":
                    action = "rollback"

        # Recall ERROR
        elif is_error_channel(None, message):
            action = "recall"

        # Actions about LOGGING
        elif re.search(f"^{lang('project')}{lang('colon')}", report_text):
            if record["status"] == lang("status_redact"):
                action = ""
            elif record["project"] in glovar.receivers["except"]:
                if r_message or record["type"] in {lang("gam"), lang("ser")}:
                    action = "error"
            elif record["project"] == "WARN":
                if r_message or record["type"] in {lang("gam"), lang("ser")}:
                    action = "bad"
            elif record["project"] == "MANAGE" and record["status"] != lang("status_delete"):
                if record["status"] == lang("status_mole"):
                    action = "error"
                elif record["status"] == lang("status_innocent"):
                    action = "bad"
                elif record["status"] in {lang("status_error"), lang("status_unban")}:
                    action = "mole"
                elif record["status"] == lang("status_bad"):
                    action = "innocent"
            elif not r_message or record["status"] == lang("status_delete"):
                action = "redact"
            else:
                action = "delete"

        # Check the action
        if not action:
            return True

        # Generate key
        key = random_str(8)

        while glovar.actions.get(key):
            key = random_str(8)

        # Log data
        glovar.actions[key] = {
            "lock": False,
            "time": get_now(),
            "mid": 0,
            "aid": aid,
            "action": action,
            "message": report_message,
            "record": record
        }

        if action == "rollback":
            data = receive_text_data(report_message)
            glovar.actions[key]["sender"] = data["from"]
            glovar.actions[key]["type"] = data["data"]

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang(f'action_{action}'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_wait'))}\n")

        # Generate the report message's markup
        data_proceed = button_data(action, "proceed", key)
        data_cancel = button_data(action, "cancel", key)
        markup_list = [
            [
                InlineKeyboardButton(
                    text=lang("proceed"),
                    callback_data=data_proceed
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang("cancel"),
                    callback_data=data_cancel
                )
            ]
        ]

        if action not in {"delete", "redact", "recall", "rollback"}:
            if r_message and not r_message.empty:
                data_delete = button_data(action, "delete", key)
                markup_list[0].append(
                    InlineKeyboardButton(
                        text=lang("delete"),
                        callback_data=data_delete
                    )
                )
            else:
                data_delete = button_data("redact", "delete", key)
                markup_list[0].append(
                    InlineKeyboardButton(
                        text=lang("redact"),
                        callback_data=data_delete
                    )
                )

        markup = InlineKeyboardMarkup(markup_list)

        # Send the report message
        result = send_message(client, cid, text, mid, markup)

        # Save data
        if result:
            glovar.actions[key]["mid"] = result.message_id
            glovar.records[key] = {}

            for item in glovar.actions[key]:
                if item in {"lock", "time", "mid"}:
                    glovar.records[key][item] = deepcopy(glovar.actions[key][item])

            save("records")
        else:
            glovar.actions.pop(key, {})
                
        return True
    except Exception as e:
        logger.warning(f"Check error error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.forwarded
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & manage_group & ~error_channel & ~exchange_channel & ~logging_channel & ~watch_channel
                   & from_user)
def check_forwarded(client: Client, message: Message) -> bool:
    # Check forwarded messages
    try:
        # Do not check hidden forwarder
        if message.forward_sender_name:
            return True

        # Forward evidence
        if message.forward_from_chat and message.forward_from_chat.id != glovar.debug_channel_id:
            m = forward_evidence(client, message)

            if not m:
                return True

            m = general_link(m.message_id, message_link(m))
        else:
            m = ""

        # Check DEBUG message automatically without using "/check" reply to that message
        if message.forward_from_chat and message.forward_from_chat.id == glovar.debug_channel_id:
            message.reply_to_message = message
        # Check TICKET message automatically without using "/check" reply to that message
        elif message.forward_from and message.forward_from.id == glovar.ticket_id:
            message.reply_to_message = message

        # Check subject
        check_subject(client, message, m)

        return True
    except Exception as e:
        logger.warning(f"Check forwarded error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message((Filters.incoming or glovar.aio) & Filters.channel & ~Filters.forwarded
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    glovar.locks["receive"].acquire()
    try:
        data = receive_text_data(message)

        if not data:
            return True

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

            if sender == "AVATAR":

                if action == "add":
                    if action_type == "white":
                        receive_white_users(client, message)

                elif action == "remove":
                    if action_type == "white":
                        receive_remove_white(data)

                elif action == "status":
                    if action_type == "reply":
                        receive_status_reply(client, message, sender, data)

            elif sender == "CAPTCHA":

                if action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                if action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CLEAN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "LONG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "status":
                    if action_type == "reply":
                        receive_status_reply(client, message, sender, data)

                elif action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "REGEX":

                if action == "status":
                    if action_type == "reply":
                        receive_status_reply(client, message, sender, data)

            elif sender == "TIP":
                if action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

            elif sender == "USER":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "status":
                    if action_type == "reply":
                        receive_status_reply(client, message, sender, data)

            elif sender == "WARN":

                if action == "config":
                    if action_type == "show":
                        receive_config_show(client, message, data)

                elif action == "leave":
                    if action_type == "info":
                        receive_leave_info(client, sender, data)
                    elif action_type == "request":
                        receive_leave_request(client, sender, data)

                elif action == "update":
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
    finally:
        glovar.locks["receive"].release()

    return False
