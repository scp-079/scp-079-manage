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
from time import sleep
from typing import List, Optional, Union

from pyrogram import Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, general_link, format_data, message_link, thread, user_mention
from .file import crypt_file
from .telegram import edit_message_text, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def edit_evidence(client: Client, message: Message, project: str, action: str, uid: str, level: str, rule: str,
                  em: Message, more: str = None, reason: str = None) -> Optional[Union[bool, Message]]:
    # Edit the evidence's report message
    result = None
    try:
        cid = message.chat.id
        mid = message.message_id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"原始项目：{code(project)}\n"
                f"状态：{code(f'已{action}')}\n"
                f"用户 ID：{code(uid)}\n"
                f"操作等级：{code(level)}\n"
                f"规则：{code(rule)}\n")
        if more:
            text += f"附加信息：{code(more)}\n"

        text += f"记录转存：{general_link(em.message_id, message_link(em))}\n"
        if reason:
            text += f"原因：{code(reason)}\n"

        result = edit_message_text(client, cid, mid, text)
    except Exception as e:
        logger.warning(f"Edit evidence error: {e}", exc_info=True)

    return result


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        text = format_data(
            sender="EMERGENCY",
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        thread(send_message, (client, glovar.hide_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def send_error(client: Client, message: Message, project: str, aid: int, action: str,
               reason: str = None) -> Optional[Union[bool, Message]]:
    # Send the error record message
    result = None
    try:
        # Attention: project admin can make a fake operator name
        text = (f"原始项目：{code(project)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(action)}\n")
        if reason:
            text += f"原因：{code(reason)}\n"

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(glovar.error_channel_id)
            except FloodWait as e:
                flood_wait = True
                sleep(e.x + 1)
            except Exception as e:
                logger.info(f"Forward error message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.error_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Send error: {e}", exc_info=True)

    return result


def send_debug(client: Client, aid: int, action: str, context: Union[int, str], time: str = None,
               uid: int = None, em: Message = None, reason: str = None) -> bool:
    # Send the debug message
    try:
        # Attention: project admin can make a fake operator name
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(action)}\n"
                f"操作内容：{code(context)}\n")

        if time:
            text += f"例外时效：{code(time)}\n"

        if uid:
            text += f"原用户 ID：{code(uid)}\n"

        if em:
            text += f"原始记录：{general_link(em.message_id, message_link(em))}\n"

        if reason:
            text += f"原因：{code(reason)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))
        return True
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return False


def share_bad_channel(client: Client, cid: int) -> bool:
    # Share a bad channel with other bots
    try:
        share_data(
            client=client,
            receivers=glovar.receivers_bad,
            action="add",
            action_type="bad",
            data={
                "id": cid,
                "type": "channel"
            }
        )
        return True
    except Exception as e:
        logger.warning(f"Share bad channel error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[dict, int, str],
               file: str = None) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            crypt_file("encrypt", f"data/{file}", f"tmp/{file}")
            result = send_document(client, channel_id, f"tmp/{file}", text)
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        if result is False:
            exchange_to_hide(client)
            thread(share_data, (client, receivers, action, action_type, data, file))

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False
