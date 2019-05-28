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

from pyrogram import Client, Filters

from .. import glovar
from ..functions.channel import edit_evidence, send_debug, send_error
from ..functions.etc import bold, get_reason, thread, user_mention
from ..functions.filters import logging_channel, test_group
from ..functions.group import delete_message, get_message
from ..functions.ids import add_except_context
from ..functions.image import get_file_id
from ..functions.telegram import send_message
from ..functions.user import remove_bad_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.channel & logging_channel
                   & Filters.command(["error"], glovar.prefix))
def error(client, message):
    try:
        cid = message.chat.id
        if message.reply_to_message:
            r_message = message.reply_to_message
            # Get the message that be replied by /error command
            r_message = get_message(client, cid, r_message.message_id)
            if (r_message
                    and not r_message.forward_date
                    and r_message.reply_to_message
                    and r_message.reply_to_message.forward_date
                    and r_message.text
                    and re.search("^项目编号：", r_message.text)):
                # Get admin's name by signature
                admin = message.author_signature
                # Get origin report message's full record
                record = {
                    "project": "",
                    "uid": "",
                    "level": "",
                    "rule": "",
                    "more": ""
                }
                record_list = r_message.text.split("\n")
                for r in record_list:
                    if re.search("^项目编号：", r):
                        record_type = "project"
                    elif re.search("^用户 ID：", r):
                        record_type = "uid"
                    elif re.search("^操作等级：", r):
                        record_type = "level"
                    elif re.search("^规则：", r):
                        record_type = "rule"
                    else:
                        record_type = "more"

                    record[record_type] = r.split("：")[-1]

                if record["project"] in {"CLEAN", "LANG", "NOPORN", "NOSPAM", "RECHECK"}:
                    # Remove the bad user if possible
                    if "封禁" in record["level"]:
                        action = "解禁"
                        remove_bad_user(client, int(record["uid"]))
                    else:
                        action = "解明"

                    if record["project"] in {"NOPORN", "RECHECK"}:
                        # Get the file id as except context
                        file_id = get_file_id(r_message.reply_to_message)
                        if file_id:
                            # Add the except context
                            if r_message.reply_to_message.sticker:
                                except_type = "sticker"
                            else:
                                except_type = "tmp"

                            add_except_context(client, file_id, except_type, record["project"])
                            reason = get_reason(message)
                            # Send messages to the error channel
                            result = send_error(
                                client,
                                r_message.reply_to_message,
                                record["project"],
                                admin,
                                action,
                                reason
                            )
                            # If send the error report successfully, edit the origin report and send debug message
                            if result:
                                thread(
                                    target=edit_evidence,
                                    args=(client, r_message, record["project"], action, record["level"],
                                          record["rule"], result, record["more"], reason)
                                )
                                thread(send_debug, (client, admin, action, file_id, record["uid"], result, reason))
    except Exception as e:
        logger.warning(f"Error error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client, message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
