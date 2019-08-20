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

from pyrogram import Client, Message

from .. import glovar
from .channel import edit_evidence, send_debug, send_error, share_id
from .etc import code, get_command_context, get_text, thread, user_mention
from .group import delete_message
from .telegram import edit_message_text
from .user import remove_bad_subject

# Enable logging
logger = logging.getLogger(__name__)


def action_answer(client: Client, uid: int, mid: int, key: str, action_type: str, reason: str = None) -> bool:
    # Answer the error ask
    try:
        text = f"管理员：{user_mention(uid)}\n"
        if glovar.actions.get(key):
            aid = glovar.actions[key]["aid"]
            if uid == aid or not aid:
                action = glovar.actions[key]["action"]
                text += f"执行操作：{code(glovar.names[action])}\n"
                if action_type == "proceed":
                    thread(action_proceed, (client, key, reason))
                    status = "已处理"
                elif action_type == "delete":
                    thread(action_delete, (client, key, reason))
                    status = "已删除"
                else:
                    glovar.actions.pop(key, {})
                    status = "已取消"
            else:
                return False
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
    if glovar.actions.get(key, {}) and not glovar.actions[key]["lock"]:
        try:
            glovar.actions[key]["lock"] = True
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
        finally:
            glovar.actions.pop(key, {})

    return False


def action_proceed(client: Client, key: str, reason: str = None) -> bool:
    # Proceed the action
    if glovar.actions.get(key, {}) and not glovar.actions[key]["lock"]:
        try:
            glovar.actions[key]["lock"] = True
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
            if message.reply_to_message.sticker:
                time_type = "long"
                time_text = "长期"
            else:
                time_type = "tmp"
                time_text = "临时"

            if action == "error":
                action_type = "add"
                id_type = "except"

                # Remove the bad user if possible
                if "封禁" in record["level"]:
                    action_text = "解禁"
                    remove_bad_subject(client, int(record["uid"]))
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

            # Share report message's id
            if action_type:
                share_id(client, action_type, id_type, the_id, time_type, receiver)

            thread(edit_evidence, (client, message, record, action_text, reason))
            thread(send_debug, (client, aid, action_text, time_text, record["uid"], message, result, reason))

            return True
        except Exception as e:
            logger.warning(f"Action proceed error: {e}", exc_info=True)
        finally:
            glovar.actions.pop(key, {})

    return False


def get_admin(message: Message) -> int:
    # Get message's origin commander
    result = 0
    try:
        text = get_text(message)
        if text:
            result = int(text.split("\n")[0].split("：")[-1])
    except Exception as e:
        logger.warning(f"Get admin error: {e}", exc_info=True)

    return result


def get_subject(message: Message) -> (str, str, bool):
    # Get message's target
    id_text = ""
    reason = ""
    from_check = False
    try:
        id_text, reason = get_command_context(message)
        if message.reply_to_message and message.reply_markup:
            text = get_text(message.reply_to_message)
            if text:
                if re.search("^查询：", text):
                    if not reason:
                        reason = id_text

                    id_text = text.split("\n")[1].split("：")[1]
                    from_check = True
    except Exception as e:
        logger.warning(f"Get subject error: {e}", exc_info=True)

    return id_text, reason, from_check
