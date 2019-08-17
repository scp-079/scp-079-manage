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
from typing import Optional

from pyrogram import Client, Message

from .. import glovar
from .channel import edit_evidence, send_debug, send_error
from .etc import code, thread, user_mention
from .ids import add_except_id
from .telegram import edit_message_text
from .user import remove_bad_user

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
                if action == "error":
                    text += f"执行操作：{code('解除错误')}\n"

                if action_type == "proceed":
                    thread(action_proceed, (client, key, reason))
                    status = "已处理"
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


def add_except(client: Client, message: Message, record: dict, aid: int, action: str, reason: str) -> bool:
    try:
        # Add the except context
        if message.sticker:
            except_type = "long"
            time = "长期"
        else:
            except_type = "tmp"
            time = "临时"

        rid = message.message_id
        add_except_id(client, rid, except_type, record["project"])
        # Send messages to the error channel
        result = send_error(
            client,
            message.reply_to_message,
            record["project"],
            aid,
            action,
            reason
        )
        # If send the error report successfully, edit the origin report and send debug message
        if result:
            thread(
                target=edit_evidence,
                args=(client, message, record["project"], action, record["uid"], record["level"],
                      record["rule"], record["name"], record["more"], reason)
            )
            thread(
                target=send_debug,
                args=(client, aid, action, time, record["uid"], message, result, reason)
            )

        return True
    except Exception as e:
        logger.warning(f"Add except error: {e}", exc_info=True)

    return False


def action_proceed(client: Client, key: str, reason: str = None) -> bool:
    # Process the error
    if not glovar.actions[key]["lock"]:
        try:
            glovar.actions[key]["lock"] = True
            aid = glovar.actions[key]["aid"]
            message = glovar.actions[key]["message"]
            record = glovar.actions[key]["record"]
            # Remove the bad user if possible
            if "封禁" in record["level"]:
                action = "解禁"
                remove_bad_user(client, int(record["uid"]))
            else:
                action = "解明"

            if record["project"] in glovar.receivers["except"]:
                add_except(client, message.reply_to_message, record, aid, action, reason)

            return True
        except Exception as e:
            logger.warning(f"Action proceed error: {e}", exc_info=True)
        finally:
            glovar.actions.pop(key, {})

    return False


def get_admin(message: Message) -> Optional[int]:
    # Get message's origin commander
    try:
        aid = int(message.text.split("\n")[0].split("：")[-1])
        return aid
    except Exception as e:
        logger.warning(f"Get admin error: {e}", exc_info=True)

    return None
