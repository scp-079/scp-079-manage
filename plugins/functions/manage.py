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

from pyrogram import Client

from .. import glovar
from .channel import edit_evidence, send_debug, send_error, share_data, share_id
from .etc import code, general_link, thread, user_mention
from .group import delete_message
from .telegram import edit_message_text
from .user import remove_bad_user

# Enable logging
logger = logging.getLogger(__name__)


def action_answer(client: Client, action_type: str, uid: int, mid: int, key: str, reason: str = None) -> bool:
    # Answer the error ask
    try:
        text = f"管理员：{user_mention(uid)}\n"
        if glovar.actions.get(key) and not glovar.actions[key]["lock"]:
            glovar.actions[key]["lock"] = True
            action = glovar.actions[key]["action"]
            text += f"执行操作：{code(glovar.names[action])}\n"
            if action_type == "proceed":
                thread(action_proceed, (client, key, reason))
                status = "已处理"
            elif action_type == "delete":
                thread(action_delete, (client, key, reason))
                status = "已删除"
            else:
                status = "已取消"

            glovar.actions.pop(key, {})
        else:
            status = "已失效"

        text += f"状态：{code(status)}\n"
        thread(edit_message_text, (client, glovar.manage_group_id, mid, text))

        return True
    except Exception as e:
        logger.warning(f"Error answer error: {e}", exc_info=True)

    return False


def action_delete(client: Client, key: str, reason: str = None) -> bool:
    # Delete the evidence message
    try:
        aid = glovar.actions[key]["aid"]
        message = glovar.actions[key]["message"]
        record = glovar.actions[key]["record"]
        action_text = "删除"
        time_text = ""
        result = None

        delete_message(client, glovar.logging_channel_id, message.reply_to_message.message_id)
        thread(edit_evidence, (client, message, record, action_text, reason))
        send_debug(client, aid, action_text, time_text, record["uid"], message, result, reason)

        return True
    except Exception as e:
        logger.warning(f"Action delete error: {e}", exc_info=True)

    return False


def action_proceed(client: Client, key: str, reason: str = None) -> bool:
    # Proceed the action
    try:
        aid = glovar.actions[key]["aid"]
        action = glovar.actions[key]["action"]
        message = glovar.actions[key]["message"]
        record = glovar.actions[key]["record"]
        action_type = ""
        action_text = ""
        id_type = ""
        the_id = message.message_id
        result = None

        # Define the receiver
        if record["project"] == "MANAGE":
            receiver = record["origin"]
        else:
            receiver = record["project"]

        # Choose proper time type
        if message.reply_to_message and message.reply_to_message.sticker:
            time_type = "long"
            time_text = "长期"
        else:
            time_type = "temp"
            time_text = "临时"

        if action == "error":
            action_type = "add"
            id_type = "except"

            # Remove the bad user if possible
            if "封禁" in record["level"]:
                action_text = "解禁"
                remove_bad_user(client, int(record["uid"]))
            else:
                action_text = "解明"

            # Send messages to the error channel
            result = send_error(client, message.reply_to_message, receiver, aid, action, reason)
        elif action == "bad":
            action_type = "add"
            id_type = "bad"
            action_text = "收录"
            receiver = "NOSPAM"
        elif action == "mole":
            action_type = "remove"
            id_type = "except"
            action_text = "重置"
        elif action == "innocent":
            action_type = "remove"
            id_type = "bad"
            action_text = "重置"
            receiver = "NOSPAM"
        elif action == "delete":
            action_delete(client, key, reason)
            return True

        # Share report message's id
        if action_type:
            share_id(client, action_type, id_type, the_id, time_type, receiver)

        thread(edit_evidence, (client, message, record, action_text, reason))
        thread(send_debug, (client, aid, action_text, time_text, record["uid"], message, result, reason))

        return True
    except Exception as e:
        logger.warning(f"Action proceed error: {e}", exc_info=True)

    return False


def leave_answer(client: Client, action_type: str, uid: int, mid: int, key: str, reason: str = None):
    # Answer leaving request
    try:
        text = f"管理员：{user_mention(uid)}\n"
        if action_type == "approve":
            action_text = "批准请求"
        else:
            action_text = "取消请求"

        text += f"执行操作：{code(action_text)}\n"
        # Check lock
        if glovar.leaves.get(key, {}) and not glovar.leaves[key]["lock"]:
            glovar.leaves[key]["lock"] = True
            project = glovar.leaves[key]["project"]
            gid = glovar.leaves[key]["group_id"]
            name = glovar.leaves[key]["group_name"]
            link = glovar.leaves[key]["group_link"]
            if not reason:
                reason = glovar.leaves[key]["reason"]

            text = (f"项目编号：{code(project)}\n"
                    f"群组名称：{general_link(name, link)}\n"
                    f"群组 ID：{code(gid)}\n")
            if action_type == "approve":
                share_data(
                    client=client,
                    receivers=[project],
                    action="leave",
                    action_type="approve",
                    data={
                        "admin_id": uid,
                        "group_id": gid,
                        "reason": reason
                    }
                )
                if reason == "permissions":
                    reason = "权限缺失"
                elif reason == "user":
                    reason = "缺失 USER"

                text += (f"状态：{code('已批准退出该群组')}\n"
                         f"原因：{code(reason)}\n")
            else:
                text += f"状态：{code('已取消该退群请求')}\n"
                if reason not in {"permissions", "user"}:
                    text += f"原因：{code(reason)}\n"

            glovar.leaves.pop(key, {})
        else:
            text += f"状态：{code('已失效')}\n"

        thread(edit_message_text, (client, glovar.manage_group_id, mid, text))

        return True
    except Exception as e:
        logger.warning(f"Leave answer error: {e}", exc_info=True)
