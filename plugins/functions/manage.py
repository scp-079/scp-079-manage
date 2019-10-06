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

from pyrogram import Client, InlineKeyboardMarkup

from .. import glovar
from .channel import edit_evidence, format_data, send_debug, send_error, share_data, share_id
from .etc import code, general_link, get_int, get_list_page, lang, thread, user_mention
from .file import save
from .group import delete_message
from .receive import receive_rollback
from .telegram import edit_message_reply_markup, edit_message_text, send_document
from .user import add_channel, remove_bad_user, remove_channel, remove_score, remove_watch_user

# Enable logging
logger = logging.getLogger(__name__)


def answer_action(client: Client, action_type: str, uid: int, mid: int, key: str, reason: str = None) -> bool:
    # Answer the error ask
    try:
        # Check the data
        if not glovar.actions.get(key, {}):
            return True

        # Check the lock
        if not glovar.actions[key]["lock"]:
            # Lock the session
            glovar.actions[key]["lock"] = True
            glovar.records[key]["lock"] = True

            # Proceed
            if action_type == "proceed":
                thread(action_proceed, (client, key, reason))
            elif action_type in {"delete", "redact", "recall"}:
                glovar.actions[key]["action"] = action_type
                thread(action_delete, (client, key, reason))

            # Edit the original report message
            action = glovar.actions[key]["action"]
            text = (f"{lang('admin')}{lang('colon')}{user_mention(uid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang(f'action_{action}'))}\n"
                    f"{lang('status')}{lang('colon')}{code(lang(f'status_{action_type}'))}\n")
            if reason:
                text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

            thread(edit_message_text, (client, glovar.manage_group_id, mid, text))
        else:
            glovar.records[key]["lock"] = True
            thread(edit_message_reply_markup, (client, glovar.manage_group_id, mid, None))

        save("records")

        return True
    except Exception as e:
        logger.warning(f"Error answer error: {e}", exc_info=True)

    return False


def answer_check(client: Client, action_type: str, uid: int, mid: int, key: str) -> bool:
    # Answer the check ask
    try:
        # Check the data
        if not glovar.records.get(key, {}):
            return True

        # Check lock
        if not glovar.records[key]["lock"]:
            # Lock the session
            glovar.records[key]["lock"] = True

            # Basic data
            the_id = glovar.records[key]["the_id"]

            # Proceed
            text = ""
            if action_type == "cancel":
                thread(edit_message_reply_markup, (client, glovar.manage_group_id, mid, None))
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
                    text = remove_bad_user(client, the_id, uid, True)

            if not text:
                return True

            text = f"{lang('admin')}{lang('colon')}{user_mention(uid)}\n" + text
            thread(edit_message_text, (client, glovar.manage_group_id, mid, text))
        else:
            glovar.records[key]["lock"] = True
            thread(edit_message_reply_markup, (client, glovar.manage_group_id, mid, None))

        return False
    except Exception as e:
        logger.warning(f"Answer check error: {e}", exc_info=True)

    return True


def answer_leave(client: Client, action_type: str, uid: int, mid: int, key: str, reason: str = None):
    # Answer leaving request
    try:
        # Check the data
        if not glovar.records.get(key, {}):
            return True

        # Check lock
        if not glovar.records[key]["lock"]:
            # Lock the session
            glovar.records[key]["lock"] = True

            # Basic data
            project = glovar.records[key]["project"]
            gid = glovar.records[key]["group_id"]
            name = glovar.records[key]["group_name"]
            link = glovar.records[key]["group_link"]
            reason = reason or glovar.records[key]["reason"]

            # Generate the report message's text
            text = (f"{lang('admin')}{lang('colon')}{user_mention(uid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang(f'action_{action_type}'))}\n"
                    f"{lang('project')}{lang('colon')}{code(project)}\n"
                    f"{lang('group_name')}{lang('colon')}{general_link(name, link)}\n"
                    f"{lang('group_id')}{lang('colon')}{code(gid)}\n")

            # Proceed
            if action_type == "approve":
                share_data(
                    client=client,
                    receivers=[project],
                    action="leave",
                    action_type="approve",
                    data={
                        "admin_id": uid,
                        "group_id": gid,
                        "reason": reason
                    }
                )
                if reason in {"permissions", "user"}:
                    reason = lang(f"reason_{reason}")

                text += (f"{lang('status')}{lang('colon')}{code(lang('leave_approve'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang(reason))}\n")
            else:
                text += f"{lang('status')}{lang('colon')}{code(lang('leave_reject'))}\n"
                if reason not in {"permissions", "user"}:
                    text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

            # Edit the original report message
            thread(edit_message_text, (client, glovar.manage_group_id, mid, text))
        else:
            glovar.records[key]["lock"] = True
            thread(edit_message_reply_markup, (client, glovar.manage_group_id, mid, None))

        return True
    except Exception as e:
        logger.warning(f"Answer leave error: {e}", exc_info=True)

    return False


def action_delete(client: Client, key: str, reason: str = None) -> bool:
    # Delete the evidence message
    try:
        # Basic data
        message = glovar.actions[key]["message"]
        r_message = message.reply_to_message
        record = glovar.actions[key]["record"]
        action = glovar.actions[key]["action"]

        # ID
        aid = glovar.actions[key]["aid"]
        cid = message.chat.id
        mid = message.message_id
        rid = (r_message and r_message.message_id) or mid

        # Proceed
        if action == "recall":
            # Delete the error reports
            delete_message(client, cid, mid)
            delete_message(client, cid, rid)
        elif r_message and not r_message.empty:
            # Delete the evidence
            delete_message(client, cid, rid)
            edit_evidence(
                client=client,
                message=message,
                record=record,
                status=lang("status_delete"),
                reason=reason
            )
        else:
            # Redact the report message
            for r in record:
                if record[r] and r in {"game", "bio", "name", "from", "more"}:
                    record[r] = int(len(record[r]) / 2 + 1) * "█"

            edit_evidence(
                client=client,
                message=message,
                record=record,
                status=lang("status_redact"),
                reason=reason
            )

        # Send debug message
        send_debug(
            client=client,
            aid=aid,
            action=lang(f"action_{action}"),
            em=message,
            reason=reason
        )

        return True
    except Exception as e:
        logger.warning(f"Action delete error: {e}", exc_info=True)

    return False


def action_rollback(client: Client, key: str) -> bool:
    # Rollback the data
    try:
        # Basic data
        aid = glovar.actions[key]["aid"]
        message = glovar.actions[key]["message"]
        receiver = glovar.actions[key]["sender"]
        the_type = glovar.actions[key]["type"]

        # Check MANAGE itself
        if receiver == "MANAGE":
            receive_rollback(
                client=client,
                message=message,
                data={
                    "admin_id": aid,
                    "type": the_type
                }
            )
            return True

        # Proceed
        file_id = message.document.file_id
        file_ref = message.document.file_ref
        text = format_data(
            sender=glovar.sender,
            receivers=[receiver],
            action="backup",
            action_type="rollback",
            data={
                "admin_id": aid,
                "type": the_type
            }
        )
        thread(send_document, (client, glovar.exchange_channel_id, file_id, file_ref, text))

        return True
    except Exception as e:
        logger.warning(f"Action rollback error: {e}", exc_info=True)

    return False


def action_proceed(client: Client, key: str, reason: str = None) -> bool:
    # Proceed the action
    try:
        # Basic Data
        action = glovar.actions[key]["action"]
        message = glovar.actions[key]["message"]
        r_message = message.reply_to_message
        record = glovar.actions[key]["record"]

        # ID
        aid = glovar.actions[key]["aid"]
        cid = message.chat.id
        mid = message.message_id

        # Init
        action_type = ""
        id_type = ""
        status = lang(f"status_{action}")
        result = None

        # Define the receiver
        if record["project"] == "MANAGE":
            receiver = record["origin"]
        else:
            receiver = record["project"]

        # Choose proper time type
        if ((r_message and (r_message.animation or r_message.sticker))
                or record["type"] in {lang("gam"), lang("ser")}):
            the_type = "long"
        else:
            the_type = "temp"

        # Proceed
        if action == "error":
            action_type = "add"
            id_type = "except"
            if cid == glovar.watch_channel_id:
                remove_watch_user(client, get_int(record["uid"]))
            elif cid == glovar.logging_channel_id:
                # Remove the bad user if possible
                if lang("ban") in record["level"] and cid:
                    status = lang("status_unban")
                    remove_bad_user(client, get_int(record["uid"]), aid)

                # Send the message to the error channel
                result = send_error(
                    client=client,
                    message=message,
                    project=receiver,
                    aid=aid,
                    action=lang("action_error"),
                    level=record["level"],
                    reason=reason
                )
        elif action == "bad":
            action_type = "add"
            id_type = "bad"
            receiver = "NOSPAM"
            the_type = "content"
        elif action == "mole":
            action_type = "remove"
            id_type = "except"
        elif action == "innocent":
            action_type = "remove"
            id_type = "bad"
            receiver = "NOSPAM"
            the_type = "content"
        elif action in {"delete", "redact", "recall"}:
            return action_delete(client, key, reason)
        elif action == "rollback":
            return action_rollback(client, key)

        # Share the report message's id
        if action_type:
            share_id(
                client=client,
                action_type=action_type,
                id_type=id_type,
                the_id=mid,
                the_type=the_type,
                receiver=receiver
            )

        edit_evidence(
            client=client,
            message=message,
            record=record,
            status=status,
            reason=reason
        )
        send_debug(
            client=client,
            aid=aid,
            action=lang(f"action_{action}"),
            the_type=the_type,
            the_id=record["uid"],
            em=message,
            err_m=result,
            reason=reason
        )

        return True
    except Exception as e:
        logger.warning(f"Action proceed error: {e}", exc_info=True)

    return False


def list_page_ids(aid: int, action_type: str, page: int) -> (str, InlineKeyboardMarkup):
    # Generate a ids list page
    text = ""
    markup = None
    try:
        # Prefix
        text = f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n"

        # Generate
        if action_type in {"bad", "except"}:
            # Action text
            text += f"{lang('action')}{lang('colon')}{code(lang(f'list_{action_type}'))}\n"

            # Generate the page
            the_list = eval(f"glovar.{action_type}_ids")["channels"]
            if the_list:
                page_list, markup = get_list_page(the_list, "list", action_type, page)
                text += (f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n" +
                         f"\n".join("\t" * 4 + code(the_id) for the_id in page_list))
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
    except Exception as e:
        logger.warning(f"List page ids error: {e}", exc_info=True)

    return text, markup
