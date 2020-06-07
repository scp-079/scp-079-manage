import logging

from pyrogram import Client, Message

from .etc import code, get_text, lang, thread
from .group import delete_message
from .telegram import send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


def delete_normal_command(client: Client, message: Message) -> bool:
    # Delete normal command
    result = False

    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id

        # Delete the command
        result = delete_message(client, gid, mid)
    except Exception as e:
        logger.warning(f"Delete normal command error: {e}", exc_info=True)

    return result


def command_error(client: Client, message: Message, action: str, error: str,
                  detail: str = "", report: bool = True) -> bool:
    # Command error
    result = False

    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id

        # Generate the text
        text = (f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(action)}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                f"{lang('reason')}{lang('colon')}{code(error)}\n")

        if detail:
            text += f"{lang('detail')}{lang('colon')}{code(detail)}\n"

        # Send the message
        if report:
            thread(send_report_message, (10, client, cid, text))
        else:
            thread(send_message, (client, cid, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Command error: {e}", exc_info=True)

    return result


def get_command_context(message: Message) -> (str, str):
    # Get the type "a" and the context "b" in "/command a b"
    command_type = ""
    command_context = ""

    try:
        text = get_text(message)
        command_list = text.split()

        if len(list(filter(None, command_list))) <= 1:
            return "", ""

        i = 1
        command_type = command_list[i]

        while command_type == "" and i < len(command_list):
            i += 1
            command_type = command_list[i]

        command_context = text[1 + len(command_list[0]) + i + len(command_type):].strip()
    except Exception as e:
        logger.warning(f"Get command context error: {e}", exc_info=True)

    return command_type, command_context


def get_command_type(message: Message) -> str:
    # Get the command type "a" in "/command a"
    result = ""

    try:
        text = get_text(message)
        command_list = list(filter(None, text.split()))
        result = text[len(command_list[0]):].strip()
    except Exception as e:
        logger.warning(f"Get command type error: {e}", exc_info=True)

    return result
