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
import pickle
from json import loads
from typing import Any

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .channel import share_data
from .etc import button_data, code, crypt_str, general_link, get_int, get_now, get_text, lang, mention_id
from .etc import random_str, thread
from .file import crypt_file, delete_file, get_downloaded_path, get_new_path, save
from .ids import init_user_id
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_bad(data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive bad user
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_clear_data(client: Client, data_type: str, data: dict) -> bool:
    # Receive clear data command
    glovar.locks["message"].acquire()
    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]

        # Clear bad data
        if data_type == "bad":
            if the_type == "channels":
                glovar.bad_ids["channels"] = set()
            elif the_type == "users":
                glovar.bad_ids["users"] = set()

            save("bad_ids")

        # Clear except data
        if data_type == "except":
            if the_type == "channels":
                glovar.except_ids["channels"] = set()

            save("except_ids")

        # Clear user data
        if data_type == "user":
            if the_type == "all":
                glovar.user_ids = {}

            save("user_ids")

        # Clear watch data
        if data_type == "watch":
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
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clear'))}\n"
                f"{lang('more')}{lang('colon')}{code(f'{data_type} {the_type}')}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive clear data: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

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
        if not message.document:
            return None

        file_id = message.document.file_id
        file_ref = message.document.file_ref
        path = get_downloaded_path(client, file_id, file_ref)

        if not path:
            return None

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


def receive_flood_reply(client: Client, data: dict) -> bool:
    # Receive flood reply
    result = False

    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]
        gid = data["group_id"]
        begin = data["begin"]
        end = data["end"]
        force = data["force"]
        alert = data["alert"]
        invalid = data["invalid"]

        # Generate the report text
        if not invalid:
            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('手动清理炸群成员'))}\n"
                    f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        else:
            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('手动清理炸群成员'))}\n"
                    f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                    f"{lang('reason')}{lang('colon')}{code(lang('无效的群组'))}\n")

        if not force and alert:
            text += (f"{lang('开始时间')}{lang('colon')}{code(begin)}\n"
                     f"{lang('结束时间')}{lang('colon')}{code(end)}\n"
                     f"{lang('警告')}{lang('colon')}{code(lang('此时间段内进行了数据重置操作，因此开始时间被自动修改'))}\n")

        # Send the report message
        thread(send_message, (client, glovar.manage_group_id, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Receive flood reply error: {e}", exc_info=True)

    return result


def receive_invite_result(client: Client, data: dict) -> bool:
    # Receive invite result
    result = False

    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]
        gid = data["group_id"]
        bots = data["bots"]
        status = data["status"]
        status_text = lang("status_succeeded") if data["status"] else lang("status_failed")
        reason = data.get("reason")

        # Generate the report text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('邀请机器人'))}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('status')}{lang('colon')}{code(status_text)}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Refresh admin lists
        status and share_data(
            client=client,
            receivers=bots,
            action="update",
            action_type="refresh",
            data=aid
        )

        # Send the report message
        thread(send_message, (client, glovar.manage_group_id, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Receive invite result error: {e}", exc_info=True)

    return result


def receive_leave_info(client: Client, project: str, data: dict) -> bool:
    # Info left group
    try:
        # Basic data
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]

        # Send the report message
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
        # Basic data
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]
        reason = data["reason"]

        # Generate the key
        key = random_str(8)

        while glovar.records.get(key):
            key = random_str(8)

        # Log data
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

        # Generate the report message's text
        text = (f"{lang('project')}{lang('colon')}{code(project)}\n"
                f"{lang('group_name')}{lang('colon')}{general_link(name, link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('status')}{lang('colon')}{code(lang('leave_request'))}\n"
                f"{lang('reason')}{lang('colon')}{code(reason)}\n")

        # Generate the report message's markup
        data_approve = button_data("leave", "approve", key)
        data_reject = button_data("leave", "reject", key)
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=lang("approve"),
                        callback_data=data_approve
                    ),
                    InlineKeyboardButton(
                        text=lang("reject"),
                        callback_data=data_reject
                    )
                ]
            ]
        )

        # Send the report message
        result = send_message(client, glovar.manage_group_id, text, None, markup)

        # Save data
        glovar.records[key]["mid"] = result and result.message_id
        save("records")

        return True
    except Exception as e:
        logger.warning(f"Receive leave request error: {e}", exc_info=True)

    return False


def receive_join_info(client: Client, data: dict) -> bool:
    # Info joined group
    result = False

    try:
        # Basic data
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]

        # Add to joined group ids
        glovar.joined_ids.add(gid)

        # Generate the text
        text = (f"{lang('project')}{lang('colon')}{code('USER')}\n"
                f"{lang('group_name')}{lang('colon')}{general_link(name, link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('status')}{lang('colon')}{code(lang('已加入该群组'))}\n")

        # Generate the markup
        # data_approve = button_data("joined", "leave", gid)
        # data_cancel = button_data("joined", "cancel")
        # markup = InlineKeyboardMarkup(
        #     [
        #         [
        #             InlineKeyboardButton(
        #                 text=lang("退出群组"),
        #                 callback_data=data_approve
        #             ),
        #             InlineKeyboardButton(
        #                 text=lang("cancel"),
        #                 callback_data=data_cancel
        #             )
        #         ]
        #     ]
        # )
        markup = None

        # Send the message
        thread(send_message, (client, glovar.manage_group_id, text, None, markup))

        result = True
    except Exception as e:
        logger.warning(f"Receive join info error: {e}", exc_info=True)

    return result


def receive_remove_white(data: int) -> bool:
    # Receive removed withe users
    try:
        # Basic data
        uid = data

        if not init_user_id(uid):
            return True

        # White ids
        glovar.white_ids.discard(uid)
        save("white_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove white error: {e}", exc_info=True)

    return False


def receive_rollback(client: Client, message: Message, data: dict) -> bool:
    # Receive rollback data
    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]
        the_data = receive_file_data(client, message)

        if not the_data:
            return True

        exec(f"glovar.{the_type} = the_data")
        save(the_type)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('rollback'))}\n"
                f"{lang('more')}{lang('colon')}{code(the_type)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive rollback error: {e}", exc_info=True)

    return False


def receive_status_reply(client: Client, message: Message, sender: str, data: dict) -> bool:
    # Receive status reply
    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]
        status = receive_file_data(client, message)

        if not status:
            return True

        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_status'))}\n"
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

        if not text:
            return {}

        data = loads(text)
    except Exception as e:
        logger.warning(f"Receive text data error: {e}")

    return data


def receive_user_score(project: str, data: dict) -> bool:
    # Receive and update user's score
    glovar.locks["message"].acquire()
    try:
        # Basic data
        project = project.lower()
        uid = data["id"]

        if not init_user_id(uid):
            return True

        score = data["score"]
        glovar.user_ids[uid][project] = score
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive user score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_watch_user(data: dict) -> bool:
    # Receive watch users that other bots shared
    try:
        # Basic data
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


def receive_white_users(client: Client, message: Message) -> bool:
    # Receive white users
    try:
        the_data = receive_file_data(client, message)

        if not the_data:
            return True

        glovar.white_ids = the_data
        save("white_ids")
    except Exception as e:
        logger.warning(f"Receive white users error: {e}", exc_info=True)

    return False
