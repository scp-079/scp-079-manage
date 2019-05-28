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
from copy import deepcopy

from pyrogram import Client

from .. import glovar
from .channel import share_data
from .file import save

# Enable logging
logger = logging.getLogger(__name__)


def init_user_id(uid: int) -> bool:
    # Init user data
    try:
        if glovar.user_ids.get(uid) is None:
            glovar.user_ids[uid] = deepcopy(glovar.default_user_status)
            save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Init user id {uid} error: {e}", exc_info=True)

    return False


def add_except_context(client: Client, context: str, except_type: str, project: str = None) -> bool:
    # Add except context
    try:
        if project:
            project_list = [project]
        else:
            project_list = glovar.receivers_except

        share_data(
            client=client,
            receivers=project_list,
            action="add",
            action_type="except",
            data={
                "id": context,
                "type": except_type
            }
        )
        if except_type == "sticker":
            except_type = "stickers"

        if not glovar.except_ids[except_type].get(context):
            glovar.except_ids[except_type][context] = set()

        for project in project_list:
            glovar.except_ids[except_type][context].add(project)

        save("except_ids")
        return True
    except Exception as e:
        logger.warning(f"Add except context error: {e}", exc_info=True)

    return False
