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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import share_data
from ..functions.etc import bold, code, general_link, get_admin, get_callback_data, get_command_context
from ..functions.etc import get_command_type, get_int, get_subject, lang, message_link, thread, user_mention
from ..functions.filters import from_user, manage_group, test_group
from ..functions.manage import answer_action, answer_leave
from ..functions.telegram import edit_message_text, send_message
from ..functions.user import add_channel, check_subject
from ..functions.user import remove_bad_user, remove_channel, remove_score, remove_watch_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["action"], glovar.prefix))
def action(client: Client, message: Message) -> bool:
    # Deal with report messages
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id

        # Generate the report message's text
        text = f"{lang('admin')}{lang('colon')}{user_mention(uid)}\n"

        # Proceed
        action_type, reason = get_command_context(message)
        if action_type and action_type in {"proceed", "delete", "cancel"}:
            if message.reply_to_message:
                r_message = message.reply_to_message
                aid = get_admin(r_message)
                if uid == aid:
                    callback_data_list = get_callback_data(r_message)
                    if r_message.from_user.is_self and callback_data_list:
                        r_mid = r_message.message_id
                        action_key = callback_data_list[0]["d"]
                        thread(answer_action, (client, action_type, uid, r_mid, action_key, reason))
                        text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeed'))}\n"
                                 f"{lang('see')}{lang('colon')}{general_link(r_mid, message_link(r_message))}\n")
                    else:
                        text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                                 f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('status')}{lang('colon')}{code(lang('command_usage'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code('command_usage')}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Action error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["check"], glovar.prefix))
def check(client: Client, message: Message) -> bool:
    # Check a user's status
    try:
        check_subject(client, message)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["hide"], glovar.prefix))
def hide(client: Client, message: Message) -> bool:
    # Let bots hide
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = (f"管理：{user_mention(uid)}\n"
                f"操作：{code('频道转移')}\n")
        command_type = get_command_type(message)
        if command_type and command_type in {"off", "on"}:
            if command_type == "off":
                data = False
            else:
                data = True

            glovar.should_hide = data
            share_data(
                client=client,
                receivers=["EMERGENCY"],
                action="backup",
                action_type="hide",
                data=data
            )
            text += (f"应急：{code((lambda d: '启用' if d else '禁用')(data))}\n"
                     f"状态：{code('已下达指令')}\n")

            # Send debug
            debug_text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                          f"项目管理员：{user_mention(uid)}\n"
                          f"执行操作：{code('频道转移')}\n"
                          f"应急频道：{code((lambda x: '启用' if x else '禁用')(glovar.should_hide))}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))
        else:
            text += (f"状态：{code('未下达指令')}\n"
                     f"原因：{code('格式有误')}\n")

        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Hide error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["leave"], glovar.prefix))
def leave(client: Client, message: Message) -> bool:
    # Let other bots leave a group
    try:
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        text = f"管理：{user_mention(uid)}\n"
        if message.reply_to_message:
            text += f"操作：{code('处理退群请求')}\n"
            command_type, reason = get_command_context(message)
            if command_type and command_type in {"approve", "cancel"}:
                r_message = message.reply_to_message
                callback_data_list = get_callback_data(r_message)
                if r_message.from_user.is_self and callback_data_list:
                    r_mid = r_message.message_id
                    action_key = callback_data_list[0]["d"]
                    thread(answer_leave, (client, command_type, uid, r_mid, action_key, reason))
                    text += (f"状态：{code('已操作')}\n"
                             f"查看：{general_link(r_mid, message_link(r_message))}\n")
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('来源有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('格式有误')}\n")
        else:
            text += f"操作：{code('主动退群')}\n"
            id_text, reason, _ = get_subject(message)
            if id_text:
                text += f"群组 ID：{code(id_text)}\n"
                the_id = get_int(id_text)
                if the_id:
                    share_data(
                        client=client,
                        receivers=glovar.receivers["leave"],
                        action="leave",
                        action_type="approve",
                        data={
                            "admin_id": uid,
                            "group_id": the_id,
                            "reason": reason
                        }
                    )
                    text += f"状态：{code('已通知所有机器人退出该群组')}\n"
                else:
                    text += f"结果：{code('输入有误')}\n"
            else:
                text += f"结果：{code('缺少参数')}\n"

        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Leave error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["add_bad", "add_except",
                                      "remove_bad", "remove_except", "remove_score", "remove_watch"], glovar.prefix))
def modify_object(client: Client, message: Message) -> bool:
    # Add or remove user and channel
    try:
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        text = f"管理：{user_mention(uid)}\n"
        id_text, reason, from_check = get_subject(message)
        if "force" in reason:
            reason = reason.replace("force", "").strip()
            force = True
        else:
            force = False

        if id_text:
            aid = uid
            if from_check:
                aid = get_admin(message.reply_to_message)

            if aid == uid:
                the_id = get_int(id_text)
                if the_id:
                    if "add_bad" in message.command:
                        result = add_channel(client, "bad", the_id, aid, reason, force)
                    elif "add_except" in message.command:
                        result = add_channel(client, "except", the_id, aid, reason, force)
                    elif "remove_bad" in message.command:
                        if the_id < 0:
                            result = remove_channel(client, "bad", the_id, aid, reason, force)
                        else:
                            result = remove_bad_user(client, the_id, aid, True, reason, force)
                    elif "remove_except" in message.command:
                        result = remove_channel(client, "except", the_id, aid, reason, force)
                    elif "remove_score" in message.command:
                        result = remove_score(client, the_id, aid, reason, force)
                    else:
                        result = remove_watch_user(client, the_id, True, aid, reason, force)

                    text += result
                    if reason and result and "成功" in result:
                        text += f"原因：{code(reason)}\n"
                else:
                    text += (f"针对：{code(id_text)}\n"
                             f"结果：{code('输入有误')}\n")
            else:
                text += f"结果：{code('权限错误')}\n"
        else:
            text += f"结果：{code('缺少参数')}\n"

        if from_check:
            r_message = message.reply_to_message
            thread(edit_message_text, (client, cid, r_message.message_id, text))
            text = (f"管理：{user_mention(uid)}\n"
                    f"状态：{code('已操作')}\n"
                    f"查看：{general_link(r_message.message_id, message_link(r_message))}\n")
            thread(send_message, (client, cid, text, mid))
        else:
            thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Modify object error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["refresh"], glovar.prefix))
def refresh(client: Client, message: Message) -> bool:
    # Refresh admins
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = (f"管理：{user_mention(uid)}\n"
                f"操作：{code('刷新群管列表')}\n")
        command_type = get_command_type(message)
        project_list = ["all"] + [p.lower() for p in glovar.receivers["refresh"]]
        if command_type and command_type in project_list:
            if command_type == "all":
                receivers = glovar.receivers["refresh"]
            else:
                receivers = [command_type.upper()]

            share_data(
                client=client,
                receivers=receivers,
                action="update",
                action_type="refresh",
                data=uid
            )
            text += (f"项目：{code((lambda t: t.upper() if t != 'all' else '全部')(command_type))}\n"
                     f"状态：{code('已请求')}\n")
        else:
            text += (f"项目：{code(command_type or '未知')}\n"
                     f"状态：{code('未请求')}\n"
                     f"原因：{code('格式有误')}\n")

        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Refresh error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & manage_group & from_user
                   & Filters.command(["status"], glovar.prefix))
def status(client: Client, message: Message) -> bool:
    # Check bots' status
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = (f"管理：{user_mention(uid)}\n"
                f"操作：{code('查询状态')}\n")
        command_type = get_command_type(message)
        if command_type and command_type.upper() in ["ALL"] + glovar.receivers["status"]:
            if command_type.upper() == "ALL":
                receivers = glovar.receivers["status"]
            else:
                receivers = [command_type.upper()]

            share_data(
                client=client,
                receivers=receivers,
                action="status",
                action_type="ask",
                data={
                    "admin_id": uid,
                    "message_id": mid
                }
            )
            text += (f"项目：{code((lambda t: t.upper() if t != 'all' else '全部')(command_type))}\n"
                     f"状态：{code('已请求')}\n")
        else:
            text += (f"项目：{code(command_type or '未知')}\n"
                     f"状态：{code('未请求')}\n"
                     f"原因：{code('格式有误')}\n")

        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Status error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"{lang('admin')}{lang('colon')}{user_mention(aid)}\n\n"
                f"{lang('version')}{lang('colon')}{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False
