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

from pyrogram import Client, Filters

from .. import glovar
from ..functions.etc import receive_data
from ..functions.file import save
from ..functions.filters import exchange_channel, hide_channel
from ..functions.ids import init_user_id
from ..functions.user import receive_watch_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def exchange_emergency(_, message):
    try:
        # Read basic information
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        if "EMERGENCY" in receivers:
            if sender == "EMERGENCY":
                if action == "backup":
                    if action_type == "hide":
                        glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client, message):
    try:
        data = receive_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            # This will look awkward,
            # seems like it can be simplified,
            # but this is to ensure that the permissions are clear,
            # so it is intentionally written like this
            if glovar.sender in receivers:
                if sender == "CAPTCHA":

                    if action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["captcha"] = score
                            save("user_ids")

                elif sender == "CLEAN":
                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["clean"] = score
                            save("user_ids")

                elif sender == "LANG":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["lang"] = score
                            save("user_ids")

                elif sender == "NOFLOOD":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["noflood"] = score
                            save("user_ids")

                elif sender == "NOPORN":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["noporn"] = score
                            save("user_ids")

                elif sender == "NOSPAM":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["nospam"] = score
                            save("user_ids")

                elif sender == "RECHECK":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")
                        elif action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])

                    elif action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["recheck"] = score
                            save("user_ids")

                elif sender == "WARN":

                    if action == "update":
                        if action_type == "score":
                            uid = data["id"]
                            init_user_id(uid)
                            score = data
                            glovar.user_ids[uid]["warn"] = score
                            save("user_ids")

                elif sender == "WATCH":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "watch":
                            receive_watch_user(the_type, the_id, data["until"])
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
