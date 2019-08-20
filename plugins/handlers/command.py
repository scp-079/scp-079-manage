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
from ..functions.channel import send_debug
from ..functions.etc import bold, code, code_block, general_link, get_callback_data, get_command_context
from ..functions.etc import message_link, thread, user_mention
from ..functions.filters import manage_group, test_group
from ..functions.manage import action_answer, get_admin
from ..functions.telegram import send_message
from ..functions.user import remove_bad_subject

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group
                   & Filters.command(["action"], glovar.prefix))
def action(client: Client, message: Message):
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = f"管理：{user_mention(uid)}\n"
        command_type, reason = get_command_context(message)
        if command_type and command_type in {"proceed", "delete", "cancel"}:
            if message.reply_to_message:
                r_message = message.reply_to_message
                aid = get_admin(r_message)
                if uid == aid:
                    callback_data_list = get_callback_data(r_message)
                    if r_message.from_user.is_self and callback_data_list:
                        r_mid = r_message.message_id
                        action_key = callback_data_list[0]["d"]
                        thread(action_answer, (client, uid, r_mid, action_key, command_type, reason))
                        text += (f"状态：{code('已操作')}\n"
                                 f"查看：{general_link(r_mid, message_link(r_message))}\n")
                    else:
                        text += (f"状态：{code('未操作')}\n"
                                 f"原因：{code('来源有误')}\n")
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('权限有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('用法有误')}\n")
        else:
            text += (f"状态：{code('未操作')}\n"
                     f"原因：{code('格式有误')}\n")

        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Action error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & manage_group
                   & Filters.command(["remove_bad"], glovar.prefix))
def remove_bad(client: Client, message: Message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = f"管理：{user_mention(aid)}\n"
        command_type, reason = get_command_context(message)
        if command_type:
            id_text = command_type
            try:
                the_id = int(id_text)
                if the_id > 0:
                    action_text = "解禁用户"
                    id_type = "users"
                else:
                    action_text = "解禁频道"
                    id_type = "channels"

                text += f"操作：{code(action_text)}\n"
                if the_id in glovar.bad_ids[id_type]:
                    remove_bad_subject(client, id_type, the_id)
                    text += f"结果：{code('操作成功')}\n"
                    send_debug(client, aid, action_text, None, command_type, None, None, reason)
                else:
                    text += f"结果：{code('对象不在列表中')}\n"

                if reason:
                    text += f"原因：{code(reason)}\n"
            except Exception as e:
                text += (f"错误：" + "-" * 24 + "\n\n"
                         f"{code_block(e)}\n")
                thread(send_message, (client, cid, text, mid))
                return

        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Remove bad error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
