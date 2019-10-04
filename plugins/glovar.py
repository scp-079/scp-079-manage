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
backup: Union[str, bool] = ""
project_link: str = ""
project_name: str = ""
date_reset: str = ""
zh_cn: Union[str, bool] = ""

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
    backup = config["custom"].get("backup", backup)
    backup = eval(backup)
    date_reset = config["custom"].get("date_reset", date_reset)
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    zh_cn = config["custom"].get("zh_cn", zh_cn)
    zh_cn = eval(zh_cn)
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
        or backup not in {False, True}
        or date_reset in {"", "[DATA EXPUNGED]"}
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or zh_cn not in {False, True}
        or key in {b"", b"[DATA EXPUNGED]", "", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

# Languages
lang: Dict[str, str] = {
    # Admin
    "admin": (zh_cn and "管理员") or "Admin",
    "admin_project": (zh_cn and "项目管理员") or "Project Admin",
    # Basic
    "colon": (zh_cn and "：") or ": ",
    "reason": (zh_cn and "原因") or "Reason",
    "action": (zh_cn and "执行操作") or "Action",
    # Emergency
    "issue": (zh_cn and "发现状况") or "Issue",
    "exchange_invalid": (zh_cn and "数据交换频道失效") or "Exchange Channel Invalid",
    "auto_fix": (zh_cn and "自动处理") or "Auto Fix",
    "protocol_1": (zh_cn and "启动 1 号协议") or "Initiate Protocol 1",
    "transfer_channel": (zh_cn and "频道转移") or "Transfer Channel",
    "emergency_channel": (zh_cn and "应急频道") or "Emergency Channel",
    # Manage
    "level_error": (zh_cn and "错误等级") or "Error Level",
    "time_content": (zh_cn and "内容收录") or "Content Record Time",
    "time_except": (zh_cn and "内容例外") or "Content Whitelist Time",
    "channel_id": (zh_cn and "频道 ID") or "Channel ID",
    "record_origin": (zh_cn and "原始记录") or "Original Record",
    "record_error": (zh_cn and "错误存档") or "Error Record",
    "group_id": (zh_cn and "群组 ID") or "Group ID",
    # Record
    "project": (zh_cn and "项目编号") or "Project",
    "project_origin": (zh_cn and "原始项目") or "Original Project",
    "status": (zh_cn and "状态") or "Status",
    "user_id": (zh_cn and "用户 ID") or "User ID",
    "level": (zh_cn and "操作等级") or "Level",
    "rule": (zh_cn and "规则") or "Rule",
    "message_type": (zh_cn and "消息类别") or "Message Type",
    "message_game": (zh_cn and "游戏标识") or "Game Short Name",
    "message_lang": (zh_cn and "消息语言") or "Message Language",
    "message_len": (zh_cn and "消息长度") or "Message Length",
    "message_freq": (zh_cn and "消息频率") or "Message Frequency",
    "user_score": (zh_cn and "用户得分") or "User Score",
    "user_bio": (zh_cn and "用户简介") or "User Bio",
    "user_name": (zh_cn and "用户昵称") or "User Name",
    "from_name": (zh_cn and "来源名称") or "Forward Name",
    "more": (zh_cn and "附加信息") or "Extra Info",
}

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

version: str = "0.0.8"

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

actions_pure: Dict[str, Dict[str, Union[bool, int]]] = {}
# actions = {
#     "random": {
#         "lock": False,
#         "time": 15112345678,
#         "mid": 123
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
