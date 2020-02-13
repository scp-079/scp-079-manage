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

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .channel import send_debug, share_data
from .etc import button_data, code, get_int, get_now, get_subject, italic, lang, mention_id, random_str, thread
from .file import save
from .telegram import get_chat, resolve_username, send_message

# Enable logging
logger = logging.getLogger(__name__)


def add_channel(client: Client, the_type: str, the_id: int, aid: int, reason: str = None,
                force: bool = False) -> str:
    # Add channel
    result = ""
    try:
        opposite = {
            "bad": "except",
            "except": "bad"
        }

        result += (f"{lang('action')}{lang('colon')}{code(lang(f'add_{the_type}'))}\n"
                   f"{lang('channel_id')}{lang('colon')}{code(the_id)}\n")

        if the_id not in eval(f"glovar.{the_type}_ids")["channels"] or force:
            # Local
            eval(f"glovar.{the_type}_ids")["channels"].add(the_id)
            save(f"{the_type}_ids")
            eval(f"glovar.{opposite[the_type]}_ids")["channels"].discard(the_id)
            save(f"{opposite[the_type]}_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers[the_type],
                action="add",
                action_type=the_type,
                data={
                    "id": the_id,
                    "type": "channel"
                }
            )

            # Send debug message
            result += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
            send_debug(
                client=client,
                aid=aid,
                action=lang(f"add_{the_type}"),
                the_id=the_id,
                reason=reason
            )
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang(f'in_{the_type}'))}\n")
    except Exception as e:
        logger.warning(f"Add channel error: {e}", exc_info=True)

    return result


def check_subject(client: Client, message: Message) -> bool:
    # Check the subject's status
    try:
        # Init
        text = ""
        markup = None
        now = get_now()

        # Basic Data
        aid = message.from_user.id
        cid = message.chat.id
        mid = message.message_id

        # Get the subject's ID
        the_id = 0
        id_text, _, _ = get_subject(message)

        if id_text:
            the_id = get_int(id_text)

            if not the_id:
                _, the_id = resolve_username(client, id_text, False)
        elif message.forward_from:
            the_id = message.forward_from.id
        elif message.forward_from_chat:
            the_id = message.forward_from_chat.id

        # No Valid ID
        if not the_id:
            if not message.forward_date:
                text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                        f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                        f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

            thread(send_message, (client, cid, text, mid, markup))
            return True

        # Check
        key = random_str(8)

        while glovar.records.get(key):
            key = random_str(8)

        glovar.records[key] = {
            "lock": True,
            "time": now,
            "mid": 0,
            "the_id": the_id
        }

        if the_id > 0:
            is_bad = the_id in glovar.bad_ids["users"]
            is_watch_ban = now < glovar.watch_ids["ban"].get(the_id, 0)
            is_watch_delete = now < glovar.watch_ids["delete"].get(the_id, 0)
            total_score = sum(glovar.user_ids.get(the_id, glovar.default_user_status).values())

            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                    f"{lang('user_id')}{lang('colon')}{code(the_id)}\n"
                    f"{lang('blacklist')}{lang('colon')}{code(is_bad)}\n"
                    f"{lang('ban_watch')}{lang('colon')}{code(is_watch_ban)}\n"
                    f"{lang('delete_watch')}{lang('colon')}{code(is_watch_delete)}\n"
                    f"{lang('score_total')}{lang('colon')}{code(f'{total_score:.1f}')}\n\n")

            for project in glovar.default_user_status:
                project_score = glovar.user_ids.get(the_id, glovar.default_user_status)[project]

                if not project_score:
                    continue

                text += "\t" * 4
                text += (f"{italic(project.upper())}    "
                         f"{code(f'{project_score:.1f}')}\n")

            if is_bad or total_score or is_watch_ban or is_watch_delete:
                glovar.records[key]["lock"] = False

                bad_data = button_data("check", "bad", key)
                score_data = button_data("check", "score", key)
                watch_data = button_data("check", "watch", key)
                cancel_data = button_data("check", "cancel", key)
                markup_list = [
                    [],
                    [
                        InlineKeyboardButton(
                            text=lang("cancel"),
                            callback_data=cancel_data
                        )
                    ]
                ]

                if is_bad:
                    markup_list[0].append(
                        InlineKeyboardButton(
                            text=lang("user_unban"),
                            callback_data=bad_data
                        )
                    )

                if total_score:
                    markup_list[0].append(
                        InlineKeyboardButton(
                            text=lang("user_forgive"),
                            callback_data=score_data
                        )
                    )

                if is_watch_delete or is_watch_ban:
                    markup_list[0].append(
                        InlineKeyboardButton(
                            text=lang("user_unwatch"),
                            callback_data=watch_data
                        )
                    )

                markup = InlineKeyboardMarkup(markup_list)
        else:
            glovar.records[key]["lock"] = False

            is_bad = the_id in glovar.bad_ids["channels"]
            is_except = the_id in glovar.except_ids["channels"]

            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                    f"{lang('channel_id')}{lang('colon')}{code(the_id)}\n")

            if id_text and id_text != str(the_id):
                chat = get_chat(client, id_text)
                text += f"{lang('restricted_channel')}{lang('colon')}{code(bool(chat and chat.restrictions))}\n"

            text += (f"{lang('blacklist')}{lang('colon')}{code(is_bad)}\n"
                     f"{lang('whitelist')}{lang('colon')}{code(is_except)}\n")

            bad_data = button_data("check", "bad", key)
            except_data = button_data("check", "except", key)
            cancel_data = button_data("check", "cancel", key)
            bad_text = lang(f"blacklist_{(lambda x: 'remove' if x else 'add')(is_bad)}")
            except_text = lang(f"whitelist_{(lambda x : 'remove' if x else 'add')(is_except)}")
            markup_list = [
                [
                    InlineKeyboardButton(
                        text=bad_text,
                        callback_data=bad_data
                    ),
                    InlineKeyboardButton(
                        text=except_text,
                        callback_data=except_data
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=lang("cancel"),
                        callback_data=cancel_data
                    )
                ]
            ]
            markup = InlineKeyboardMarkup(markup_list)

        result = send_message(client, cid, text, mid, markup)
        glovar.records[key]["mid"] = result and result.message_id
        save("records")

        return True
    except Exception as e:
        logger.warning(f"Check subject error: {e}", exc_info=True)

    return False


def remove_bad_user(client: Client, the_id: int, aid: int, debug: bool = False, reason: str = None,
                    force: bool = False) -> str:
    # Remove bad user
    result = ""
    try:
        # Generate the report message's text
        result += (f"{lang('action')}{lang('colon')}{code(lang('action_unban'))}\n"
                   f"{lang('user_id')}{lang('colon')}{code(the_id)}\n")

        # Proceed
        if the_id in glovar.bad_ids["users"] or force:
            # Local
            glovar.bad_ids["users"].discard(the_id)
            save("bad_ids")

            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)
            save("watch_ids")

            glovar.user_ids.pop(the_id, {})
            save("user_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["bad"],
                action="remove",
                action_type="bad",
                data={
                    "id": the_id,
                    "type": "user"
                }
            )

            # Text
            result += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send debug message
            if debug:
                send_debug(
                    client=client,
                    aid=aid,
                    action=lang("action_unban"),
                    the_id=the_id,
                    reason=reason
                )
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang('no_bad'))}\n")
    except Exception as e:
        logger.warning(f"Remove bad object error: {e}", exc_info=True)

    return result


def remove_channel(client: Client, the_type: str, the_id: int, aid: int, reason: str = None,
                   force: bool = False) -> str:
    # Remove channel
    result = ""
    try:
        # Generate the report message's text
        result += (f"{lang('action')}{lang('colon')}{code(lang(f'remove_{the_type}'))}\n"
                   f"{lang('channel_id')}{lang('colon')}{code(the_id)}\n")

        # Proceed
        if the_id in eval(f"glovar.{the_type}_ids")["channels"] or force:
            # Local
            eval(f"glovar.{the_type}_ids")["channels"].discard(the_id)
            save(f"{the_type}_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers[the_type],
                action="remove",
                action_type=the_type,
                data={
                    "id": the_id,
                    "type": "channel"
                }
            )

            # Text
            result += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send debug message
            send_debug(
                client=client,
                aid=aid,
                action=lang(f"remove_{the_type}"),
                the_id=the_id,
                reason=reason
            )
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang(f'no_{the_type}'))}\n")
    except Exception as e:
        logger.warning(f"Remove channel error: {e}", exc_info=True)

    return result


def remove_score(client: Client, the_id: int, aid: int = None, reason: str = None,
                 force: bool = False) -> str:
    # Remove watched user
    result = ""
    try:
        # Generate the report message's text
        result += (f"{lang('action')}{lang('colon')}{code(lang('action_forgive'))}\n"
                   f"{lang('user_id')}{lang('colon')}{code(the_id)}\n")

        # Proceed
        if (glovar.user_ids.get(the_id, {}) and sum(glovar.user_ids[the_id].values())) or force:
            # Local
            glovar.user_ids.pop(the_id, {})
            save("user_ids")

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["score"],
                action="remove",
                action_type="score",
                data=the_id
            )

            # Text
            result += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send debug message
            send_debug(
                client=client,
                aid=aid,
                action=lang("action_forgive"),
                the_id=the_id,
                reason=reason
            )
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang('no_score'))}\n")
    except Exception as e:
        logger.warning(f"Remove score error: {e}", exc_info=True)

    return result


def remove_watch_user(client: Client, the_id: int, debug: bool = False, aid: int = None, reason: str = None,
                      force: bool = False) -> str:
    # Remove watched user
    result = ""
    try:
        # Generate the report message's text
        result += (f"{lang('action')}{lang('colon')}{code(lang('action_unwatch'))}\n"
                   f"{lang('user_id')}{lang('colon')}{code(the_id)}\n")

        # Proceed
        if glovar.watch_ids["ban"].get(the_id, 0) or glovar.watch_ids["delete"].get(the_id, 0) or force:
            # Local
            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)
            save("watch_ids")

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

            # Text
            result += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send debug message
            if debug:
                send_debug(
                    client=client,
                    aid=aid,
                    action=lang("action_unwatch"),
                    the_id=the_id,
                    reason=reason
                )
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang('no_watch'))}\n")
    except Exception as e:
        logger.warning(f"Remove watch user error: {e}", exc_info=True)

    return result
