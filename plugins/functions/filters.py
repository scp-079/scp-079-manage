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
from typing import Union

from pyrogram import CallbackQuery, Filters, Message

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        cid = message.chat.id
        if glovar.should_hide:
            if cid == glovar.hide_channel_id:
                return True
        elif cid == glovar.exchange_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        cid = message.chat.id
        if cid == glovar.hide_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_logging_channel(_, message: Message) -> bool:
    # Check if the message is forwarded from the logging channel
    try:
        if message.forward_from_chat:
            if glovar.logging_channel_id == message.forward_from_chat.id:
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

        cid = message.chat.id
        if cid == glovar.manage_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is manage group error: {e}", exc_info=True)

    return False


def is_test_group(_, message: Message) -> bool:
    # Check if the message is sent from the test group
    try:
        cid = message.chat.id
        if cid == glovar.test_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


exchange_channel = Filters.create(
    name="Exchange Channel",
    func=is_exchange_channel
)

hide_channel = Filters.create(
    name="Hide Channel",
    func=is_hide_channel
)

logging_channel = Filters.create(
    name="Logging Channel",
    func=is_logging_channel
)

manage_group = Filters.create(
    name="Manage Group",
    func=is_manage_group
)

test_group = Filters.create(
    name="Test Group",
    func=is_test_group
)
