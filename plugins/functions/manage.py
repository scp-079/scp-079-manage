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
from typing import Optional

from pyrogram import Client, Message

from .. import glovar
from .channel import edit_evidence, send_debug, send_error
from .etc import code, thread, user_mention
from ..functions.ids import add_except_context
from ..functions.image import get_file_id
from ..functions.telegram import edit_message_text
from ..functions.user import remove_bad_user

# Enable logging
logger = logging.getLogger(__name__)


def error_answer(client: Client, cid: int, uid: int, mid: int, result: str, key: str, reason: str = None) -> bool:
    # Answer the error ask
    try:
        text = (f"管理员：{user_mention(uid)}\n"
                f"执行操作：{code('解除错误')}\n")
        if glovar.errors.get(key):
            aid = glovar.errors[key]["aid"]
            if uid == aid or not aid:
                if result == "process":
                    thread(error_process, (client, key, reason))
                    status = "已处理"
                else:
                    glovar.errors.pop(key, {})
                    status = "已取消"
            else:
                return False
        else:
            status = "已失效"

        text += f"状态：{code(status)}"
        thread(edit_message_text, (client, cid, mid, text))
        return True
    except Exception as e:
        logger.warning(f"Error answer error: {e}", exc_info=True)

    return False


def error_process(client: Client, key: str, reason: str = None) -> bool:
    # Process the error
    if not glovar.errors[key]["lock"]:
        try:
            glovar.errors[key]["lock"] = True
            message = glovar.errors[key]["message"]
            aid = glovar.errors[key]["aid"]
            # Get origin report message's full record
            record = {
                "project": "",
                "uid": "",
                "level": "",
                "rule": "",
                "name": "",
                "more": ""
            }
            record_list = message.text.split("\n")
            for r in record_list:
                if re.search("^项目编号：", r):
                    record_type = "project"
                elif re.search("^用户 ID：", r):
                    record_type = "uid"
                elif re.search("^操作等级：", r):
                    record_type = "level"
                elif re.search("^规则：", r):
                    record_type = "rule"
                elif re.search("^用户昵称", r):
                    record_type = "name"
                else:
                    record_type = "more"

                record[record_type] = r.split("：")[-1]

            # Remove the bad user if possible
            if "封禁" in record["level"]:
                action = "解禁"
                remove_bad_user(client, int(record["uid"]))
            else:
                action = "解明"

            if record["project"] in {"NOPORN", "RECHECK"}:
                # Get the file id as except context
                file_id = get_file_id(message.reply_to_message)
                if file_id:
                    # Add the except context
                    if message.reply_to_message.sticker:
                        except_type = "sticker"
                        time = "长期"
                    else:
                        except_type = "tmp"
                        time = "临时"

                    add_except_context(client, file_id, except_type, record["project"])
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
                                  record["rule"], result, record["more"], reason)
                        )
                        thread(
                            target=send_debug,
                            args=(client, aid, action, file_id, time, record["uid"], message, result, reason)
                        )

            return True
        except Exception as e:
            logger.warning(f"Process error error: {e}", exc_info=True)
        finally:
            glovar.errors.pop(key, {})

    return False


def get_admin(message: Message) -> Optional[int]:
    # Get message's origin commander
    try:
        aid = int(message.text.split("\n")[0].split("：")[-1])
        return aid
    except Exception as e:
        logger.warning(f"Get admin error: {e}", exc_info=True)

    return None
