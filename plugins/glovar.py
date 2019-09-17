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
import pickle
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from typing import Dict, List, Set, Union

from pyrogram import Message

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    filename='log',
    filemode='w'
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [channels]
critical_channel_id: int = 0
debug_channel_id: int = 0
error_channel_id: int = 0
exchange_channel_id: int = 0
hide_channel_id: int = 0
logging_channel_id: int = 0
manage_group_id: int = 0
test_group_id: int = 0
watch_channel_id: int = 0

# [custom]
project_link: str = ""
project_name: str = ""
reset_day: str = ""

# [encrypt]
key: Union[str, bytes] = ""
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    bot_token = config["basic"].get("bot_token", bot_token)
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [channels]
    critical_channel_id = int(config["channels"].get("critical_channel_id", critical_channel_id))
    debug_channel_id = int(config["channels"].get("debug_channel_id", debug_channel_id))
    error_channel_id = int(config["channels"].get("error_channel_id", error_channel_id))
    exchange_channel_id = int(config["channels"].get("exchange_channel_id", exchange_channel_id))
    hide_channel_id = int(config["channels"].get("hide_channel_id", hide_channel_id))
    logging_channel_id = int(config["channels"].get("logging_channel_id", logging_channel_id))
    manage_group_id = int(config["channels"].get("manage_group_id", manage_group_id))
    test_group_id = int(config["channels"].get("test_group_id", test_group_id))
    watch_channel_id = int(config["channels"].get("watch_channel_id", watch_channel_id))
    # [custom]
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    reset_day = config["custom"].get("reset_day", reset_day)
    # [encrypt]
    key = config["encrypt"].get("key", key)
    key = key.encode("utf-8")
    password = config["encrypt"].get("password", password)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (bot_token in {"", "[DATA EXPUNGED]"}
        or prefix == []
        or critical_channel_id == 0
        or debug_channel_id == 0
        or error_channel_id == 0
        or exchange_channel_id == 0
        or hide_channel_id == 0
        or logging_channel_id == 0
        or manage_group_id == 0
        or test_group_id == 0
        or watch_channel_id == 0
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or reset_day in {"", "[DATA EXPUNGED]"}
        or key in {b"", b"[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

# Init

all_commands: List[str] = [
    "action",
    "add_bad",
    "add_except",
    "check",
    "hide",
    "join",
    "leave",
    "refresh",
    "remove_bad",
    "remove_except",
    "remove_score",
    "remove_watch",
    "status",
    "version"
]

default_user_status: Dict[str, float] = {
    "captcha": 0.0,
    "clean": 0.0,
    "lang": 0.0,
    "long": 0.0,
    "noflood": 0.0,
    "noporn": 0.0,
    "nospam": 0.0,
    "recheck": 0.0,
    "warn": 0.0
}

leaves: Dict[str, Dict[str, Union[bool, int, str]]] = {}
# leaves = {
#     "random": {
#         "lock": False,
#         "project": "USER",
#         "group_id": -10012345678,
#         "group_name": "SCP-079-CHAT",
#         "group_link": "https://t.me/SCP_079_CHAT",
#         "reason": ""
#     }
# }

names: Dict[str, str] = {
    "bad": "收录消息",
    "delete": "删除存档",
    "error": "解除错误",
    "innocent": "取消收录",
    "mole": "移除例外",
    "redact": "清除信息",
    "recall": "撤回判误"
}

receivers: Dict[str, List[str]] = {
    "bad": ["ANALYZE", "APPLY", "APPEAL", "AVATAR", "CAPTCHA", "CLEAN", "LANG", "LONG",
            "MANAGE", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WATCH"],
    "except": ["CLEAN", "LANG", "NOPORN", "NOSPAM", "RECHECK", "WATCH"],
    "leave": ["CAPTCHA", "CLEAN", "LANG", "LONG",
              "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN"],
    "refresh": ["AVATAR", "CAPTCHA", "CLEAN", "LANG", "LONG",
                "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "USER", "WARN"],
    "score": ["ANALYZE", "CAPTCHA", "CLEAN", "LANG", "LONG",
              "MANAGE", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK"],
    "status": ["NOSPAM", "USER", "WATCH"],
    "watch": ["ANALYZE", "CAPTCHA", "CLEAN", "LANG", "LONG",
              "MANAGE", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "WATCH"]
}

sender: str = "MANAGE"

should_hide: bool = False

version: str = "0.0.7"

# Load data from pickle

# Init dir
try:
    rmtree("tmp")
except Exception as e:
    logger.info(f"Remove tmp error: {e}")

for path in ["data", "tmp"]:
    if not exists(path):
        mkdir(path)

# Init ids variables

bad_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# bad_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

except_ids: Dict[str, Set[int]] = {
    "channels": set()
}
# except_ids = {
#     "channels": {-10012345678}
# }

user_ids: Dict[int, Dict[str, float]] = {}
# user_ids = {
#     12345678: {
#         "captcha": 0,
#         "clean": 0,
#         "lang": 0,
#         "long": 0,
#         "noflood": 0,
#         "noporn": 0,
#         "nospam": 0,
#         "recheck": 0,
#         "warn": 0
#     }
# }

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 0
#     },
#     "delete": {
#         12345678: 0
#     }
# }

# Init data variables

actions: Dict[str, Dict[str, Union[bool, int, str, Dict[str, str], Message]]] = {}
# actions = {
#     "random": {
#         "lock": False,
#         "time": 15112345678,
#         "mid": 123,
#         "aid": 12345678,
#         "action": "error",
#         "message": Message,
#         "record" = {
#             "project": "",
#             "origin": "",
#             "status": "",
#             "uid": "",
#             "level": "",
#             "rule": "",
#             "type": "",
#             "lang": "",
#             "freq": "",
#             "score": "",
#             "bio": "",
#             "name": "",
#             "from": "",
#             "more": ""
#         }
#     }
# }

actions_pure: Dict[str, Dict[str, Union[bool, int, str, Dict[str, str]]]] = {}
# actions = {
#     "random": {
#         "lock": False,
#         "time": 15112345678,
#         "mid": 123,
#         "aid": 12345678,
#         "action": "error",
#         "record" = {
#             "project": "",
#             "origin": "",
#             "status": "",
#             "uid": "",
#             "level": "",
#             "rule": "",
#             "type": "",
#             "lang": "",
#             "freq": "",
#             "score": "",
#             "bio": "",
#             "name": "",
#             "from": "",
#             "more": ""
#         }
#     }
# }

# Load data
file_list: List[str] = ["bad_ids", "except_ids", "user_ids", "watch_ids", "actions_pure"]
for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", 'rb') as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", 'wb') as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}", exc_info=True)
            with open(f"data/.{file}", 'rb') as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}", exc_info=True)
        raise SystemExit("[DATA CORRUPTION]")

# Start program
copyright_text = (f"SCP-079-{sender} v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
