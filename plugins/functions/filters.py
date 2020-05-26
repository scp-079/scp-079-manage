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
from typing import Union

from pyrogram import CallbackQuery, Filters, Message

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def is_aio(_, __) -> bool:
    # Check if the program is under all-in-one mode
    result = False

    try:
        result = glovar.aio
    except Exception as e:
        logger.warning(f"Is aio error: {e}", exc_info=True)

    return result


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        if message.chat:
            cid = message.chat.id

            if glovar.should_hide:
                if cid == glovar.hide_channel_id:
                    return True
            elif cid == glovar.exchange_channel_id:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id

            if cid == glovar.exchange_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_error_channel(_, message: Message) -> bool:
    # Check if the message is forwarded from the error channel
    try:
        if not message.forward_from_chat:
            return False

        cid = message.forward_from_chat.id

        if cid == glovar.error_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is error channel error: {e}", exc_info=True)

    return False


def is_from_user(_, message: Message) -> bool:
    # Check if the message is sent from a user
    try:
        if message.from_user and message.from_user.id != 777000:
            return True
    except Exception as e:
        logger.warning(f"Is from user error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.hide_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_logging_channel(_, message: Message) -> bool:
    # Check if the message is forwarded from the logging channel
    try:
        if not message.forward_from_chat:
            return False

        cid = message.forward_from_chat.id

        if cid == glovar.logging_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is logging channel error: {e}", exc_info=True)

    return False


def is_manage_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is sent from the manage group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.manage_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is manage group error: {e}", exc_info=True)

    return False


def is_test_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is sent from the test group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.test_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


def is_watch_channel(_, message: Message) -> bool:
    # Check if the message is forwarded from the watch channel
    try:
        if not message.forward_from_chat:
            return False

        cid = message.forward_from_chat.id

        if cid == glovar.watch_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is watch channel error: {e}", exc_info=True)

    return False


aio = Filters.create(
    func=is_aio,
    name="AIO"
)

exchange_channel = Filters.create(
    func=is_exchange_channel,
    name="Exchange Channel"
)

error_channel = Filters.create(
    func=is_error_channel,
    name="Error Channel"
)

from_user = Filters.create(
    func=is_from_user,
    name="From User"
)

hide_channel = Filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)

logging_channel = Filters.create(
    func=is_logging_channel,
    name="Logging Channel"
)

manage_group = Filters.create(
    func=is_manage_group,
    name="Manage Group"
)

test_group = Filters.create(
    func=is_test_group,
    name="Test Group"
)

watch_channel = Filters.create(
    func=is_watch_channel,
    name="Watch Channel"
)
