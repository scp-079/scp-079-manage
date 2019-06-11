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
from json import loads

from pyrogram import Client, CallbackQuery

from ..functions.etc import thread
from ..functions.filters import manage_group
from ..functions.manage import error_answer
from ..functions.telegram import answer_callback

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(manage_group)
def answer(client: Client, callback_query: CallbackQuery):
    try:
        # Basic callback data
        gid = callback_query.message.chat.id
        aid = callback_query.from_user.id
        mid = callback_query.message.message_id
        callback_data = loads(callback_query.data)
        action = callback_data["a"]
        action_type = callback_data["t"]
        data = callback_data["d"]
        if action == "error":
            thread(error_answer, (client, gid, aid, mid, action_type, data))
            thread(answer_callback, (client, callback_query.id, ""))
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)
