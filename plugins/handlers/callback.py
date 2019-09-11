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
from ..functions.etc import get_admin, thread, user_mention
from ..functions.filters import manage_group
from ..functions.manage import action_answer, leave_answer
from ..functions.telegram import answer_callback, edit_message_text, edit_message_reply_markup
from ..functions.user import add_channel, remove_bad_user, remove_channel, remove_score, remove_watch_user

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
            if action in {"error", "bad", "mole", "innocent", "delete", "redact"}:
                action_key = data
                thread(action_answer, (client, action_type, uid, mid, action_key))
            elif action == "check":
                the_id = data
                text = ""
                if action_type == "cancel":
                    thread(edit_message_reply_markup, (client, cid, mid, None))
                elif action_type == "score":
                    text = remove_score(client, the_id, uid)
                elif action_type == "watch":
                    text = remove_watch_user(client, the_id, True, uid)
                else:
                    # Modify channel lists
                    if the_id < 0:
                        if the_id not in eval(f"glovar.{action_type}_ids")["channels"]:
                            text = add_channel(client, action_type, the_id, uid)
                        else:
                            text = remove_channel(client, action_type, the_id, uid)
                    # Remove bad user
                    elif action_type == "bad":
                        if the_id in glovar.bad_ids["users"]:
                            text = remove_bad_user(client, the_id, uid, True)

                if text:
                    text = f"管理：{user_mention(uid)}\n" + text
                    thread(edit_message_text, (client, cid, mid, text))
            elif action == "join":
                pass
            elif action == "leave":
                action_key = data
                thread(leave_answer, (client, action_type, uid, mid, action_key))

            thread(answer_callback, (client, callback_query.id, ""))

        return True
    except Exception as e:
        logger.warning(f"Answer callback error: {e}", exc_info=True)

    return False
