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

from ..functions.etc import get_admin, thread
from ..functions.filters import manage_group
from ..functions.manage import answer_action, answer_check, answer_leave, list_page_ids
from ..functions.telegram import answer_callback, edit_message_text

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(manage_group)
def answer(client: Client, callback_query: CallbackQuery) -> bool:
    # Answer the callback query
    try:
        # Basic callback data
        cid = callback_query.message.chat.id
        uid = callback_query.from_user.id
        aid = get_admin(callback_query.message)
        mid = callback_query.message.message_id
        callback_data = loads(callback_query.data)
        action = callback_data["a"]
        action_type = callback_data["t"]
        data = callback_data["d"]
        # Check permission
        if uid == aid or not aid:
            # Answer
            if action in {"error", "bad", "mole", "innocent", "delete", "redact", "recall"}:
                key = data
                thread(answer_action, (client, action_type, uid, mid, key))
            elif action == "check":
                key = data
                thread(answer_check, (client, action_type, uid, mid, key))
            elif action == "leave":
                key = data
                thread(answer_leave, (client, action_type, uid, mid, key))
            elif action == "list":
                page = data
                text, markup = list_page_ids(aid, action_type, page)
                edit_message_text(client, cid, mid, text, markup)

            thread(answer_callback, (client, callback_query.id, ""))

        return True
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)

    return False
