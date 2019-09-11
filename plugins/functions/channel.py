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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, general_link, message_link, thread, user_mention, wait_flood
from .file import crypt_file, delete_file, get_new_path
from .telegram import edit_message_text, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def edit_evidence(client: Client, message: Message, record: dict, action_text: str,
                  reason: str = None) -> Optional[Union[bool, Message]]:
    # Edit the evidence's report message
    result = None
    try:
        cid = message.chat.id
        mid = message.message_id
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"原始项目：{code(record['origin'] or record['project'])}\n"
                f"状态：{code(f'已{action_text}')}\n")

        if reason:
            text += f"原因：{code(reason)}\n"

        text += (f"用户 ID：{code(record['uid'])}\n"
                 f"操作等级：{code(record['level'])}\n"
                 f"规则：{code(record['rule'])}\n")

        if record["type"]:
            text += f"消息类别：{code(record['type'])}\n"

        if record["lang"]:
            text += f"消息语言：{code(record['lang'])}\n"

        if record["freq"]:
            text += f"消息频率：{code(record['freq'])}\n"

        if record["score"]:
            text += f"用户得分：{code(record['score'])}\n"

        if record["bio"]:
            text += f"用户简介：{code(record['bio'])}\n"

        if record["name"]:
            text += f"用户昵称：{code(record['name'])}\n"

        if record["from"]:
            text += f"来源名称：{code(record['from'])}\n"

        if record["more"]:
            text += f"附加信息：{code(record['more'])}\n"

        result = edit_message_text(client, cid, mid, text)
    except Exception as e:
        logger.warning(f"Edit evidence error: {e}", exc_info=True)

    return result


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    try:
        glovar.should_hide = True
        share_data(
            client=client,
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )
        text = (f"项目编号：{code(glovar.sender)}\n"
                f"发现状况：{code('数据交换频道失效')}\n"
                f"自动处理：{code('启用 1 号协议')}\n")
        thread(send_message, (client, glovar.critical_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return False


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def send_error(client: Client, message: Message, project: str, aid: int, action_text: str, level: str,
               reason: str = None) -> Optional[Union[bool, Message]]:
    # Send the error record message
    result = None
    try:
        # Get the right message
        message = message.reply_to_message or message

        # Attention: project admin can make a fake operator name, so keep showing the ID
        text = (f"原始项目：{code(project)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(glovar.names[action_text])}\n"
                f"错误等级：{code(level)}\n")
        if reason:
            text += f"原因：{code(reason)}\n"

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(glovar.error_channel_id)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except Exception as e:
                logger.info(f"Forward error message error: {e}", exc_info=True)
                return False

        result = result.message_id
        result = send_message(client, glovar.error_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Send error: {e}", exc_info=True)

    return result


def send_debug(client: Client, aid: int, action_text: str, time_text: str = None,
               id_text: Union[int, str] = None, em: Message = None, err_m: Message = None, reason: str = None) -> bool:
    # Send the debug message
    try:
        # Attention: project admin can make a fake operator name, so keep showing the ID
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code(action_text)}\n")

        if time_text:
            text += f"操作时效：{code(time_text)}\n"

        if id_text:
            id_text = str(id_text)
            if "-100" not in id_text:
                text += f"用户 ID：{code(id_text)}\n"
            else:
                text += f"频道 ID：{code(id_text)}\n"

        if em:
            text += f"原始记录：{general_link(em.message_id, message_link(em))}\n"

        if err_m:
            text += f"错误存档：{general_link(err_m.message_id, message_link(err_m))}\n"

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
            receivers=glovar.receivers["bad"],
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


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[bool, dict, int, str],
               file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if receivers:
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
                if encrypt:
                    # Encrypt the file, save to the tmp directory
                    file_path = get_new_path()
                    crypt_file("encrypt", file, file_path)
                else:
                    # Send directly
                    file_path = file

                result = send_document(client, channel_id, file_path, text)
                # Delete the tmp file
                if result:
                    for f in {file, file_path}:
                        if "tmp/" in f:
                            thread(delete_file, (f,))
            else:
                text = format_data(
                    sender=glovar.sender,
                    receivers=receivers,
                    action=action,
                    action_type=action_type,
                    data=data
                )
                result = send_message(client, channel_id, text)

            # Sending failed due to channel issue
            if result is False and not glovar.should_hide:
                # Use hide channel instead
                exchange_to_hide(client)
                thread(share_data, (client, receivers, action, action_type, data, file, encrypt))

            return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_id(client: Client, action_type: str, id_type: str, the_id: int, the_type: str, receiver: str) -> bool:
    # Add bad or except id
    try:
        share_data(
            client=client,
            receivers=[receiver],
            action=action_type,
            action_type=id_type,
            data={
                "id": the_id,
                "type": the_type
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Share id error: {e}", exc_info=True)

    return False
