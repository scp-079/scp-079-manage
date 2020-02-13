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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Client, Message
from pyrogram.errors import FloodWait

from .. import glovar
from .etc import code, code_block, delay, general_link, lang, mention_id, message_link, thread, wait_flood
from .file import crypt_file, delete_file, get_new_path
from .telegram import edit_message_text, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def edit_evidence(client: Client, message: Message, record: dict, status: str,
                  reason: str = None, delay_secs: int = 0) -> bool:
    # Edit the evidence's report message
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('project_origin')}{lang('colon')}{code(record['origin'] or record['project'])}\n"
                f"{lang('status')}{lang('colon')}{code(status)}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        text += (f"{lang('user_id')}{lang('colon')}{code(record['uid'])}\n"
                 f"{lang('level')}{lang('colon')}{code(record['level'])}\n"
                 f"{lang('rule')}{lang('colon')}{code(record['rule'])}\n")

        if record["type"]:
            text += f"{lang('message_type')}{lang('colon')}{code(record['type'])}\n"

        if record["game"]:
            text += f"{lang('message_game')}{lang('colon')}{code(record['game'])}\n"

        if record["lang"]:
            text += f"{lang('message_lang')}{lang('colon')}{code(record['lang'])}\n"

        if record["length"]:
            text += f"{lang('message_len')}{lang('colon')}{code(record['length'])}\n"

        if record["freq"]:
            text += f"{lang('message_freq')}{lang('colon')}{code(record['freq'])}\n"

        if record["score"]:
            text += f"{lang('user_score')}{lang('colon')}{code(record['score'])}\n"

        if record["bio"]:
            text += f"{lang('user_bio')}{lang('colon')}{code(record['bio'])}\n"

        if record["name"]:
            text += f"{lang('user_name')}{lang('colon')}{code(record['name'])}\n"

        if record["from"]:
            text += f"{lang('from_name')}{lang('colon')}{code(record['from'])}\n"

        if record["contact"]:
            text += f"{lang('contact')}{lang('colon')}{code(record['contact'])}\n"

        if record["more"]:
            text += f"{lang('more')}{lang('colon')}{code(record['more'])}\n"

        if delay_secs:
            delay(delay_secs, edit_message_text, [client, cid, mid, text])
        else:
            thread(edit_message_text, (client, cid, mid, text))

        return True
    except Exception as e:
        logger.warning(f"Edit evidence error: {e}", exc_info=True)

    return False


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

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('issue')}{lang('colon')}{code(lang('exchange_invalid'))}\n"
                f"{lang('auto_fix')}{lang('colon')}{code(lang('protocol_1'))}\n")
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


def forward_evidence(client: Client, message: Message) -> Optional[Union[bool, Message]]:
    # Forward the message to the channel as evidence
    result = None
    try:
        # Basic information
        uid = message.from_user.id
        text = (f"{lang('admin')}{lang('colon')}{code(uid)}\n"
                f"{lang('time_send')}{lang('colon')}{code(message.date)}\n")

        if message.contact or message.location or message.venue or message.video_note or message.voice:
            text += f"{lang('more')}{lang('colon')}{code(lang('privacy'))}\n"
        elif message.game or message.service:
            text += f"{lang('more')}{lang('colon')}{code(lang('cannot_forward'))}\n"

        # DO NOT try to forward these types of message
        if (message.contact
                or message.location
                or message.venue
                or message.video_note
                or message.voice
                or message.game
                or message.service):
            result = send_message(client, glovar.manage_channel_id, text)
            return result

        # Try to forward the evidence
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = message.forward(
                    chat_id=glovar.manage_channel_id,
                    disable_notification=True
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except Exception as e:
                logger.warning(f"Forward evidence message error: {e}", exc_info=True)
                return False

        # Attach report message
        result = result.message_id
        result = send_message(client, glovar.manage_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def send_error(client: Client, message: Message, project: str, aid: int, action: str, level: str, rule: str,
               reason: str = None) -> Optional[Union[bool, Message]]:
    # Send the error record message
    result = None
    try:
        # Report text
        text = (f"{lang('project_origin')}{lang('colon')}{code(project)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(action)}\n"
                f"{lang('error_level')}{lang('colon')}{code(level)}\n"
                f"{lang('error_rule')}{lang('colon')}{code(rule)}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        # Get the evidence message
        message = message.reply_to_message or message

        # Forward the message
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


def send_debug(client: Client, aid: int, action: str, project: str = None, the_type: str = None,
               the_id: int = None, em: Message = None, err_m: Message = None, reason: str = None) -> bool:
    # Send the debug message
    try:
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(action)}\n")

        if project:
            text += f"{lang('project_target')}{lang('colon')}{code(project)}\n"

        if the_type:
            text += f"{lang(f'type_{the_type}')}{lang('colon')}{code(lang(f'time_{the_type}'))}\n"

        if the_id:
            text += f"{lang((lambda x: 'user_id' if x else 'channel_id')(the_id > 0))}{lang('colon')}{code(the_id)}\n"

        if em:
            text += f"{lang('record_origin')}{lang('colon')}{general_link(em.message_id, message_link(em))}\n"

        if err_m:
            text += f"{lang('record_error')}{lang('colon')}{general_link(err_m.message_id, message_link(err_m))}\n"

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

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


def share_data(client: Client, receivers: List[str], action: str, action_type: str,
               data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the channel
    try:
        thread(
            target=share_data_thread,
            args=(client, receivers, action, action_type, data, file, encrypt)
        )

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_data_thread(client: Client, receivers: List[str], action: str, action_type: str,
                      data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Share data thread
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if not receivers:
            return True

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

            result = send_document(client, channel_id, file_path, None, text)

            # Delete the tmp file
            if result:
                for f in {file, file_path}:
                    f.startswith("tmp/") and thread(delete_file, (f,))
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
        logger.warning(f"Share data thread error: {e}", exc_info=True)

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
