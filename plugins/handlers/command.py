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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import share_data
from ..functions.command import command_error, get_command, get_command_context, get_command_type
from ..functions.etc import bold, code, general_link, get_admin, get_callback_data, get_int, get_now, get_subject
from ..functions.etc import italic, lang, message_link, thread, mention_id
from ..functions.filters import from_user, manage_group, test_group
from ..functions.manage import answer_action, answer_leave, list_page_ids
from ..functions.receive import receive_clear_data
from ..functions.telegram import edit_message_text, send_message
from ..functions.timers import backup_files
from ..functions.user import add_channel, check_subject
from ..functions.user import remove_bad_user, remove_channel, remove_score, remove_watch_user, remove_white_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["action"], glovar.prefix)
                   & manage_group
                   & from_user)
def action_command(client: Client, message: Message) -> bool:
    # Deal with report messages
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Generate the report message's text
        text = f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"

        # Proceed
        the_type, reason = get_command_context(message)

        if the_type in {"proceed", "delete", "cancel"} and r_message and r_message.from_user.is_self:
            aid = get_admin(r_message)

            if uid == aid:
                callback_data_list = get_callback_data(r_message)

                if callback_data_list and callback_data_list[0]["t"] in {"proceed", "delete"}:
                    key = callback_data_list[0]["d"]
                    thread(answer_action, (client, the_type, uid, rid, key, reason))
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                             f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Action command error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["check"], glovar.prefix)
                   & manage_group
                   & from_user)
def check(client: Client, message: Message) -> bool:
    # Check a user's status
    try:
        check_subject(client, message)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["clear_bad_channels",
                                                                       "clear_bad_users",
                                                                       "clear_bad_contents",
                                                                       "clear_bad_contacts",
                                                                       "clear_except_channels",
                                                                       "clear_except_contacts",
                                                                       "clear_except_temp",
                                                                       "clear_except_long",
                                                                       "clear_user_all",
                                                                       "clear_user_new",
                                                                       "clear_watch_all",
                                                                       "clear_watch_ban",
                                                                       "clear_watch_delete"], glovar.prefix)
                   & manage_group
                   & from_user)
def clear(client: Client, message: Message) -> bool:
    # Clear data
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        command = message.command[0]
        data_type = command.split("_")[1]
        the_type = command.split("_")[2]
        receivers = get_command_type(message).upper()

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clear'))}\n")

        # Proceed
        if receivers:
            available = {
                "bad_channels": glovar.receivers["bad"],
                "bad_users": glovar.receivers["bad"],
                "bad_contents": ["NOSPAM"],
                "bad_contacts": ["NOSPAM"],
                "except_channels": glovar.receivers["except"],
                "except_contacts": ["NOSPAM"],
                "except_temp": glovar.receivers["except"],
                "except_long": glovar.receivers["except"],
                "user_all": glovar.receivers["score"],
                "user_new": ["AVATAR", "CLEAN", "LANG", "NOSPAM", "WATCH"],
                "watch_all": glovar.receivers["watch"],
                "watch_ban": glovar.receivers["watch"],
                "watch_delete": glovar.receivers["watch"],
            }

            if receivers == "ALL":
                receivers = available[f"{data_type}_{the_type}"]
            else:
                receivers = receivers.split()

            if all(receiver in available[f"{data_type}_{the_type}"] for receiver in receivers):
                # Create data
                data = {
                    "admin_id": aid,
                    "type": the_type
                }

                # Check MANAGE itself
                if glovar.sender in receivers:
                    receive_clear_data(client, data_type, data)

                # Share clear command
                share_data(
                    client=client,
                    receivers=receivers,
                    action="clear",
                    action_type=data_type,
                    data=data
                )

                # Text
                text += f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n"
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Clear error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["config"], glovar.prefix)
                   & manage_group
                   & from_user)
def config(client: Client, message: Message) -> bool:
    # Let other bots show config of a group
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        receiver, id_text = get_command_context(message)
        receiver = receiver.upper()
        gid = get_int(id_text)

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n")

        # Proceed
        if receiver in glovar.receivers["config"] and gid < 0:
            share_data(
                client=client,
                receivers=[receiver],
                action="config",
                action_type="show",
                data={
                    "admin_id": aid,
                    "message_id": mid,
                    "group_id": gid
                }
            )
            text += f"{lang('status')}{lang('colon')}{code(lang('status_requested'))}\n"
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["flood", "flood_force"], glovar.prefix)
                   & manage_group
                   & from_user)
def flood(client: Client, message: Message) -> bool:
    # Manually kick flood users
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        now = get_now()

        # Get the command
        command_type, command_context = get_command_context(message)

        # Check the command
        if not command_type or len(command_context.split()) != 2:
            return command_error(client, message, lang("手动清除炸群成员"), lang("command_usage"), report=False)

        # Get data
        gid = get_int(command_type)
        begin = get_int(command_context.split()[0])
        end = get_int(command_context.split()[1]) or (command_context.split()[1] == "now" and now)
        force = get_command(message).endswith("_force")

        # Check the command
        if not gid or not begin or not end or begin >= end:
            return command_error(client, message, lang("手动清除炸群成员"), lang("command_usage"), report=False)
        elif begin + 48 * 3600 < now:
            return command_error(client, message, lang("手动清除炸群成员"), lang("command_para"),
                                 lang("开始时间超过 48 小时以前"), False)
        elif end > now:
            return command_error(client, message, lang("手动清除炸群成员"), lang("command_para"),
                                 lang("结束时间超过当前时间"), False)

        # Share the data
        share_data(
            client=client,
            receivers=["CAPTCHA"],
            action="flood",
            action_type="check",
            data={
                "admin_id": aid,
                "message_id": mid,
                "group_id": gid,
                "begin": begin,
                "end": end,
                "force": force
            }
        )

        # Generate the report text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('手动清除炸群成员'))}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('开始时间')}{lang('colon')}{code(begin)}\n"
                f"{lang('结束时间')}{lang('colon')}{code(end)}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Flood error: {e}", exc_info=True)

    return result


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["hide"], glovar.prefix)
                   & manage_group
                   & from_user)
def hide(client: Client, message: Message) -> bool:
    # Let bots hide
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        command_type = get_command_type(message)

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n")

        # Proceed
        if command_type and command_type in {"off", "on"}:
            # Local
            data = (lambda x: True if x == "on" else False)(command_type)
            glovar.should_hide = data

            # Share the command
            share_data(
                client=client,
                receivers=["EMERGENCY"],
                action="backup",
                action_type="hide",
                data=data
            )

            # Generate the report message's text
            data_text = (lambda x: lang("enabled") if x else lang("disabled"))(data)
            text += (f"{lang('emergency_channel')}{lang('colon')}{code(data_text)}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")

            # Send debug message
            debug_text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                          f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                          f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                          f"{lang('emergency_channel')}{lang('colon')}{code(data_text)}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Hide error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["leave"], glovar.prefix)
                   & manage_group
                   & from_user)
def leave(client: Client, message: Message) -> bool:
    # Let other bots leave a group
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Generate the report message's text
        text = f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"

        # Proceed
        if message.reply_to_message:
            text += f"{lang('action')}{lang('colon')}{code(lang('leave_handle'))}\n"
            action_type, reason = get_command_context(message)

            if action_type in {"approve", "reject"} and r_message and r_message.from_user.is_self:
                callback_data_list = get_callback_data(r_message)

                if callback_data_list and callback_data_list[0]["t"] in {"approve"}:
                    action_key = callback_data_list[0]["d"]
                    thread(answer_leave, (client, action_type, aid, rid, action_key, reason))
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                             f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code('status_failed')}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
        else:
            text += f"{lang('action')}{lang('colon')}{code(lang('leave_manual'))}\n"
            id_text, reason, _ = get_subject(message)

            # Check force
            force = False

            if re.search("force$", reason):
                force = True
                reason = re.sub("force$", "", reason).strip()

            if id_text:
                the_id = get_int(id_text)

                if the_id < 0:
                    share_data(
                        client=client,
                        receivers=glovar.receivers["leave"],
                        action="leave",
                        action_type="approve",
                        data={
                            "admin_id": aid,
                            "group_id": the_id,
                            "force": force,
                            "reason": reason
                        }
                    )
                    text += (f"{lang('group_id')}{lang('colon')}{code(the_id)}\n"
                             f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n")

                    if reason:
                        text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Leave error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["list", "ls"], glovar.prefix)
                   & manage_group
                   & from_user)
def list_ids(client: Client, message: Message) -> bool:
    # List IDs
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        action_type = get_command_type(message)

        # Get the text and markup
        text, markup = list_page_ids(aid, action_type, 1)

        # Send the report message
        thread(send_message, (client, cid, text, mid, markup))

        return True
    except Exception as e:
        logger.warning(f"List ids error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["add_bad",
                                                                       "add_except",
                                                                       "remove_bad",
                                                                       "remove_except",
                                                                       "remove_score",
                                                                       "remove_watch",
                                                                       "remove_white"], glovar.prefix)
                   & manage_group & from_user)
def modify_subject(client: Client, message: Message) -> bool:
    # Add or remove user and channel
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        id_text, reason, from_check = get_subject(message)
        force = False
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Check force
        if re.search("force$", reason):
            force = True
            reason = re.sub("force$", "", reason).strip()

        # Generate the report message's text
        text = f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"

        # Proceed
        if id_text:
            # Get the admin ID
            if from_check:
                aid = get_admin(r_message)
            else:
                aid = uid

            # Check permission
            if aid == uid:
                # Get the target ID
                the_id = get_int(id_text)

                # Add or Remove
                if the_id:
                    if "add_bad" in message.command:
                        result = add_channel(client, "bad", the_id, aid, reason, force)
                    elif "add_except" in message.command:
                        result = add_channel(client, "except", the_id, aid, reason, force)
                    elif "remove_bad" in message.command:
                        if the_id < 0:
                            result = remove_channel(client, "bad", the_id, aid, reason, force)
                        else:
                            result = remove_bad_user(client, the_id, aid, True, reason, force)
                    elif "remove_except" in message.command:
                        result = remove_channel(client, "except", the_id, aid, reason, force)
                    elif "remove_score" in message.command:
                        result = remove_score(client, the_id, aid, reason, force)
                    elif "remove_watch" in message.command:
                        result = remove_watch_user(client, the_id, True, aid, reason, force)
                    elif "remove_white" in message.command:
                        result = remove_white_user(client, the_id, True, aid, reason, force)
                    else:
                        result = ""

                    # Text
                    text += result

                    if reason and result and lang("status_succeeded") in result:
                        text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        if from_check:
            thread(edit_message_text, (client, cid, r_message.message_id, text))
            text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                    f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
            thread(send_message, (client, cid, text, mid))
        else:
            thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Modify subject error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["now"], glovar.prefix)
                   & manage_group
                   & from_user)
def backup_now(client: Client, message: Message) -> bool:
    # Backup now
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        receivers = get_command_type(message).upper()

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_now'))}\n")

        # Proceed
        if receivers:
            if receivers == "ALL":
                receivers = glovar.receivers["now"]
            else:
                receivers = receivers.split()

            if all(receiver in glovar.receivers["now"] for receiver in receivers):
                # Check MANAGE itself
                if glovar.sender in receivers:
                    thread(backup_files, (client,))

                # Share now command
                share_data(
                    client=client,
                    receivers=receivers,
                    action="backup",
                    action_type="now",
                    data=None
                )

                # Text
                text += f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n"
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Backup now error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["page"], glovar.prefix)
                   & manage_group
                   & from_user)
def page_command(client: Client, message: Message) -> bool:
    # Change page
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        the_type = get_command_type(message)
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_page'))}\n")

        # Proceed
        if the_type in {"previous", "next"} and r_message and r_message.from_user.is_self:
            aid = get_admin(r_message)

            if uid == aid:
                callback_data_list = get_callback_data(r_message)
                i = (lambda x: 0 if x == "previous" else -1)(the_type)

                if callback_data_list and callback_data_list[i]["a"] == "list":
                    action_type = callback_data_list[i]["t"]
                    page = callback_data_list[i]["d"]
                    page_text, markup = list_page_ids(aid, action_type, page)
                    thread(edit_message_text, (client, cid, rid, page_text, markup))
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                             f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Page command error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["refresh"], glovar.prefix)
                   & manage_group
                   & from_user)
def refresh(client: Client, message: Message) -> bool:
    # Refresh admins
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        receivers = get_command_type(message).upper()

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('refresh'))}\n")

        # Proceed
        if receivers:
            if receivers == "ALL":
                receivers = glovar.receivers["refresh"]
            else:
                receivers = receivers.split()

            if all(receiver in glovar.receivers["refresh"] for receiver in receivers):
                share_data(
                    client=client,
                    receivers=receivers,
                    action="update",
                    action_type="refresh",
                    data=aid
                )
                text += f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n"
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Refresh error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["remove_contact"], glovar.prefix)
                   & manage_group
                   & from_user)
def remove_contact(client: Client, message: Message) -> bool:
    # Let NOSPAM remove a contact
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        command_type = get_command_type(message).lower()

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_contact'))}\n")

        # Proceed
        if command_type:
            share_data(
                client=client,
                receivers=["NOSPAM"],
                action="remove",
                action_type="bad",
                data={
                    "id": command_type,
                    "type": "contact"
                }
            )
            text += f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n"
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        # Send debug message
        debug_text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                      f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                      f"{lang('action')}{lang('colon')}{code(lang('action_contact'))}\n"
                      f"{lang('contact')}{lang('colon')}{code(f'{command_type[0]}███{command_type[-1]}')}\n")
        thread(send_message, (client, glovar.debug_channel_id, debug_text))

    except Exception as e:
        logger.warning(f"Remove contact error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["status"], glovar.prefix)
                   & manage_group
                   & from_user)
def status(client: Client, message: Message) -> bool:
    # Check bots' status
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        receivers = get_command_type(message).upper()

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_status'))}\n")

        # Proceed
        if receivers:
            if receivers == "ALL":
                receivers = glovar.receivers["status"]
            else:
                receivers = receivers.split()

            if all(receiver in glovar.receivers["status"] for receiver in receivers):
                share_data(
                    client=client,
                    receivers=receivers,
                    action="status",
                    action_type="ask",
                    data={
                        "admin_id": aid,
                        "message_id": mid
                    }
                )
                text += f"{lang('status')}{lang('colon')}{code(lang('status_requested'))}\n"
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_para'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_lack'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Status error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["time"], glovar.prefix)
                   & manage_group
                   & from_user)
def time(client: Client, message: Message) -> bool:
    # Show the message's timestamp
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        r_message = message.reply_to_message

        # Check the command usage
        if not r_message or not r_message.date:
            return command_error(client, message, lang("查看消息时间"), lang("command_usage"),
                                 lang("请用命令回复一条有效的消息"), False)

        # Generate the report text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('查看消息时间'))}\n"
                f"{lang('消息发送时间')}{lang('colon')}{code(r_message.date)}\n")

        if r_message.forward_date:
            text += f"{lang('转发源消息时间')}{lang('colon')}{code(r_message.forward_date)}\n"

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Time error: {e}", exc_info=True)

    return result


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["version"], glovar.prefix)
                   & test_group
                   & from_user)
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('version')}{lang('colon')}{bold(glovar.version)}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False


# @Client.on_message(Filters.incoming & Filters.group & Filters.command(["join"], glovar.prefix)
#                    & manage_group
#                    & from_user)
# def join(client: Client, message: Message) -> bool:
#     # Check bots' status
#     result = False
#
#     try:
#         result = True
#     except Exception as e:
#         logger.warning(f"Join error: {e}", exc_info=True)
#
#     return result


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["invite"], glovar.prefix)
                   & manage_group
                   & from_user)
def invite(client: Client, message: Message) -> bool:
    # Check bots' status
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get gid and bots
        gid, bots = get_command_context(message)
        gid = get_int(gid)
        bots = bots.upper()

        # Check the command
        if not gid or gid >= 0 or not bots:
            return command_error(client, message, lang("邀请机器人"), lang("command_usage"), report=False)

        # Get valid bot
        valid_list = {"CAPTCHA", "CLEAN", "LANG", "LONG", "NOFLOOD", "NOPORN", "NOSPAM", "TIP", "WARN"}
        bots = {b for b in bots.split() if b in valid_list}
        bots = list(bots)
        bots.sort()

        # Check the bots again
        if not bots:
            return command_error(client, message, lang("邀请机器人"), lang("command_para"),
                                 lang("命令未指定任何有效的机器人"), False)

        # Share the data
        share_data(
            client=client,
            receivers=["USER"],
            action="invite",
            action_type="try",
            data={
                "admin_id": aid,
                "message_id": mid,
                "group_id": gid,
                "bots": bots
            }
        )

        # Generate the report text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('邀请机器人'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_commanded'))}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('机器人')}{lang('colon')}" + code("-") * 16 + "\n")
        text += "\n".join("\t" * 4 + italic(b) for b in bots)

        # Send the report text
        thread(send_message, (client, cid, text, mid))

        # Send debug message
        debug_text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                      f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                      f"{lang('action')}{lang('colon')}{code(lang('邀请机器人'))}\n"
                      f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                      f"{lang('机器人')}{lang('colon')}{code(' / '.join(bots))}\n")
        thread(send_message, (client, glovar.debug_channel_id, debug_text))

        result = True
    except Exception as e:
        logger.warning(f"Invite error: {e}", exc_info=True)

    return result
