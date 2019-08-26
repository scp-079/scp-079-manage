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
from json import loads

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .etc import button_data, code, crypt_str, general_link, get_text, random_str, thread
from .file import save
from .ids import init_user_id
from .telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


def receive_bad_user(data: dict) -> bool:
    # Receive bad users that other bots shared
    try:
        uid = data["id"]
        bad_type = data["type"]
        if bad_type == "user":
            glovar.bad_ids["users"].add(uid)
            save("bad_ids")
            return True
    except Exception as e:
        logger.warning(f"Receive bad user error: {e}", exc_info=True)

    return False


def receive_leave_info(client: Client, project: str, data: dict) -> bool:
    # Info left group
    try:
        gid = data["group_id"]
        name = data["group_name"]
        link = data["group_link"]
        text = (f"项目编号：{code(project)}\n"
                f"群组名称：{general_link(name, link)}\n"
                f"群组 ID：{code(gid)}\n"
                f"状态：{code('已自动退出该群组')}\n")
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
        glovar.leaves[key] = {
            "lock": False,
            "project": project,
            "group_id": gid,
            "group_name": name,
            "group_link": link,
            "reason": reason
        }
        text = (f"项目编号：{code(project)}\n"
                f"群组名称：{general_link(name, link)}\n"
                f"群组 ID：{code(gid)}\n"
                f"状态：{code('请求退出该群组')}\n"
                f"原因：{code(reason)}\n")
        data_approve = button_data("leave", "approve", gid)
        data_cancel = button_data("leave", "cancel", gid)
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="批准",
                        callback_data=data_approve
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="取消",
                        callback_data=data_cancel
                    )
                ]
            ]
        )
        thread(send_message, (client, glovar.manage_group_id, text, None, markup))

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
        init_user_id(uid)
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
        watch_type = data["type"]
        uid = data["id"]
        until = data["until"]

        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = int(until)

        # Add to list
        if watch_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif watch_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        return True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return False
