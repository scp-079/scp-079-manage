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
from .channel import share_data
from .etc import crypt_str
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


def remove_bad_subject(client: Client, id_type: str, the_id: int) -> bool:
    # Remove bad user or bad channel from list, and share it
    try:
        # Local
        glovar.bad_ids[id_type].discard(the_id)
        save("bad_ids")

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

        return True
    except Exception as e:
        logger.warning(f"Remove bad subject error: {e}", exc_info=True)

    return False
