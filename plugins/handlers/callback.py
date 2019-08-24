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

from .. import glovar
from ..functions.etc import get_admin, thread
from ..functions.filters import manage_group
from ..functions.manage import action_answer
from ..functions.telegram import answer_callback, edit_message_reply_markup
from ..functions.user import add_channel, remove_bad_user, remove_channel

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(manage_group)
def answer(client: Client, callback_query: CallbackQuery):
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
        if uid == aid:
            # Answer
            if action == "action":
                action_key = data
                thread(action_answer, (client, aid, mid, action_key, action_type))
            elif action == "check":
                the_id = data
                if action_type == "cancel":
                    thread(edit_message_reply_markup, (client, cid, mid, None))
                else:
                    if the_id > 0:
                        if the_id not in eval(f"glovar.{action_type}_ids")["channels"]:
                            add_channel(client, action_type, the_id, aid)
                        else:
                            remove_channel(client, action_type, the_id, aid)
                    elif action_type == "bad":
                        if the_id in glovar.bad_ids["users"]:
                            remove_bad_user(client, the_id, True, aid)

            thread(answer_callback, (client, callback_query.id, ""))
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)
