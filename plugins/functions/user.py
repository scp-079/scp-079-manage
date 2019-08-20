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
from .channel import send_debug, share_data
from .etc import code, crypt_str
from .file import save

# Enable logging
logger = logging.getLogger(__name__)


def receive_watch_user(watch_type: str, uid: int, until: str) -> bool:
    # Receive watch users that other bots shared
    try:
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


def remove_bad_subject(client: Client, the_id: int, debug: bool = False, aid: int = None, reason: str = None) -> str:
    # Remove bad user or bad channel from list, and share it
    result = ""
    try:
        if the_id > 0:
            action_text = "解禁用户"
            id_type = "users"
        else:
            action_text = "解禁频道"
            id_type = "channels"

        result += f"操作：{code(action_text)}\n"
        if the_id in glovar.bad_ids[id_type]:
            # Local
            glovar.bad_ids[id_type].discard(the_id)
            save("bad_ids")

            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)

            # Share
            id_type = id_type[:-1]
            share_data(
                client=client,
                receivers=glovar.receivers["bad"],
                action="remove",
                action_type="bad",
                data={
                    "id": the_id,
                    "type": id_type
                }
            )
            result += f"结果：{code('操作成功')}\n"
            if debug:
                send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += f"结果：{code('对象不在列表中')}\n"
    except Exception as e:
        logger.warning(f"Remove bad subject error: {e}", exc_info=True)

    return result


def remove_watch_user(client: Client, the_id: int, aid: int = None, reason: str = None) -> str:
    # Remove watched user
    result = ""
    try:
        action_text = "移除追踪"
        result += f"操作：{code(action_text)}\n"
        if glovar.watch_ids["ban"].get(the_id, 0) and glovar.watch_ids["delete"].get(the_id, 0):
            # Local
            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["watch"],
                action="remove",
                action_type="watch",
                data={
                    "id": the_id,
                    "type": "all"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += f"结果：{code('对象不在列表中')}\n"
    except Exception as e:
        logger.warning(f"Remove watch user error: {e}", exc_info=True)

    return result
