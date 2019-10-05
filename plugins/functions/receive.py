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
import pickle
from json import loads
from typing import Any

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .etc import button_data, code, crypt_str, general_link, get_int, get_now, get_text, lang
from .etc import random_str, thread, user_mention
from .file import crypt_file, delete_file, get_downloaded_path, get_new_path, save
from .ids import init_user_id
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_bad(data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        the_id = data["id"]
        the_type = data["type"]
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_clear_data(client: Client, data_type: str, data: dict) -> bool:
    # Receive clear data command
    try:
        aid = data["admin_id"]
        the_type = data["type"]
        if data_type == "bad":
            if the_type == "channels":
                glovar.bad_ids["channels"] = set()
            elif the_type == "users":
                glovar.bad_ids["users"] = set()

            save("bad_ids")
        elif data_type == "except":
            if the_type == "channels":
                glovar.except_ids["channels"] = set()

            save("except_ids")
        elif data_type == "user":
            if the_type == "all":
                glovar.user_ids = {}

            save("user_ids")
        elif data_type == "watch":
            if the_type == "all":
                glovar.watch_ids = {
                    "ban": {},
                    "delete": {}
                }
            elif the_type == "ban":
                glovar.watch_ids["ban"] = {}
            elif the_type == "delete":
                glovar.watch_ids["delete"] = {}

            save("watch_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{user_mention(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clear'))}\n"
                f"{lang('more')}{lang('colon')}{code(f'{data_type} {the_type}')}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive clear data: {e}", exc_info=True)

    return False


def receive_config_show(client: Client, message: Message, data: dict) -> bool:
    # Receive config show reply
    try:
        # Basic Data
        cid = glovar.manage_group_id
        mid = data["message_id"]

        # Send the config text
        text = receive_file_data(client, message)
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Receive config show error: {e}", exc_info=True)

    return False


def receive_file_data(client: Client, message: Message, decrypt: bool = True) -> Any:
    # Receive file's data from exchange channel
    data = None
    try:
        if message.document:
            file_id = message.document.file_id
            file_ref = message.document.file_ref
            path = get_downloaded_path(client, file_id, file_ref)
            if path:
                if decrypt:
                    # Decrypt the file, save to the tmp directory
                    path_decrypted = get_new_path()
                    crypt_file("decrypt", path, path_decrypted)
                    path_final = path_decrypted
                else:
                    # Read the file directly
                    path_decrypted = ""
                    path_final = path

                with open(path_final, "rb") as f:
                    data = pickle.load(f)

                for f in {path, path_decrypted}:
                    thread(delete_file, (f,))
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return data


def receive_leave_info(client: Client, project: str, data: dict) -> bool:
    # Info left group
    try:
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]
        text = (f"{lang('project')}{lang('colon')}{code(project)}\n"
                f"{lang('group_name')}{lang('colon')}{general_link(name, link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('status')}{lang('colon')}{code(lang('leave_auto'))}\n")
        thread(send_message, (client, glovar.manage_group_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive leave info error: {e}", exc_info=True)

    return False


def receive_leave_request(client: Client, project: str, data: dict) -> bool:
    # Request leave group
    try:
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]
        reason = data["reason"]

        key = random_str(8)
        while glovar.records.get(key):
            key = random_str(8)

        glovar.records[key] = {
            "lock": False,
            "time": get_now(),
            "mid": 0,
            "project": project,
            "group_id": gid,
            "group_name": name,
            "group_link": link,
            "reason": reason
        }
        if reason in {"permissions", "user"}:
            reason = lang(f"reason_{reason}")

        text = (f"{lang('project')}{lang('colon')}{code(project)}\n"
                f"{lang('group_name')}{lang('colon')}{general_link(name, link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('status')}{lang('colon')}{code(lang('leave_request'))}\n"
                f"{lang('reason')}{lang('colon')}{code(reason)}\n")
        data_approve = button_data("leave", "approve", key)
        data_cancel = button_data("leave", "cancel", key)
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=lang("approve"),
                        callback_data=data_approve
                    ),
                    InlineKeyboardButton(
                        text=lang("cancel"),
                        callback_data=data_cancel
                    )
                ]
            ]
        )
        result = send_message(client, glovar.manage_group_id, text, None, markup)
        glovar.records[key]["mid"] = result and result.message_id
        save("records")

        return True
    except Exception as e:
        logger.warning(f"Receive leave request error: {e}", exc_info=True)

    return False


def receive_remove_bad(data: dict) -> bool:
    # Receive bad users that shall be removed
    try:
        uid = data["id"]
        the_type = data["type"]
        if the_type == "user":
            glovar.bad_ids["users"].discard(uid)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove user error: {e}", exc_info=True)

    return False


def receive_rollback(client: Client, message: Message, data: dict) -> bool:
    # Receive rollback data
    try:
        aid = data["admin_id"]
        the_type = data["type"]
        the_data = receive_file_data(client, message)
        if the_data:
            exec(f"glovar.{the_type} = the_data")
            save(the_type)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{user_mention(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('rollback'))}\n"
                f"{lang('more')}{lang('colon')}{code(the_type)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive rollback error: {e}", exc_info=True)

    return False


def receive_status_reply(client: Client, message: Message, sender: str, data: dict) -> bool:
    # Receive status reply
    try:
        aid = data["admin_id"]
        mid = data["message_id"]
        status = receive_file_data(client, message)
        if not status:
            return True

        text = (f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('status_request'))}\n"
                f"{lang('project')}{lang('colon')}{code(sender)}\n")
        for name in status:
            text += f"{name}{lang('colon')}{code(status[name])}\n"

        thread(send_message, (client, glovar.manage_group_id, text, mid))
    except Exception as e:
        logger.warning(f"Receive status reply error: {e}", exc_info=True)

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def receive_user_score(project: str, data: dict) -> bool:
    # Receive and update user's score
    try:
        project = project.lower()
        uid = data["id"]
        if init_user_id(uid):
            score = data["score"]
            glovar.user_ids[uid][project] = score
            save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive user score error: {e}", exc_info=True)

    return False


def receive_watch_user(data: dict) -> bool:
    # Receive watch users that other bots shared
    try:
        the_type = data["type"]
        uid = data["id"]
        until = data["until"]

        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = get_int(until)

        # Add to list
        if the_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif the_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return False
