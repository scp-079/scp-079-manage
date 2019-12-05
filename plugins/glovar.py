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
from threading import Lock
from typing import Dict, List, Set, Union

from pyrogram import Message

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename="log",
    filemode="w"
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
ticket_id: int = 0

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
aio: Union[bool, str] = ""
backup: Union[bool, str] = ""
date_reset: str = ""
per_page: int = 0
project_link: str = ""
project_name: str = ""
zh_cn: Union[bool, str] = ""

# [encrypt]
key: Union[bytes, str] = ""
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [basic]
    bot_token = config["basic"].get("bot_token", bot_token)
    prefix = list(config["basic"].get("prefix", prefix_str))
    # [bots]
    ticket_id = int(config["bots"].get("ticket_id", ticket_id))
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
    aio = config["custom"].get("aio", aio)
    aio = eval(aio)
    backup = config["custom"].get("backup", backup)
    backup = eval(backup)
    date_reset = config["custom"].get("date_reset", date_reset)
    per_page = int(config["custom"].get("per_page", per_page))
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
        or ticket_id == 0
        or critical_channel_id == 0
        or debug_channel_id == 0
        or error_channel_id == 0
        or exchange_channel_id == 0
        or hide_channel_id == 0
        or logging_channel_id == 0
        or manage_group_id == 0
        or test_group_id == 0
        or watch_channel_id == 0
        or aio not in {False, True}
        or backup not in {False, True}
        or date_reset in {"", "[DATA EXPUNGED]"}
        or per_page == 0
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
    "action": (zh_cn and "执行操作") or "Action",
    "action_page": (zh_cn and "翻页") or "Change Page",
    "clear": (zh_cn and "清空数据") or "Clear Data",
    "colon": (zh_cn and "：") or ": ",
    "disabled": (zh_cn and "禁用") or "Disabled",
    "enabled": (zh_cn and "启用") or "Enabled",
    "page": (zh_cn and "第 {} 页") or "Page {}",
    "reason": (zh_cn and "原因") or "Reason",
    "reset": (zh_cn and "重置数据") or "Reset Data",
    "result": (zh_cn and "结果") or "Result",
    "rollback": (zh_cn and "数据回滚") or "Rollback",
    "see": (zh_cn and "查看") or "See",
    "status_failed": (zh_cn and "未执行") or "Failed",
    "status_succeeded": (zh_cn and "成功执行") or "Succeeded",
    "version": (zh_cn and "版本") or "Version",
    # Command
    "command_lack": (zh_cn and "命令参数缺失") or "Lack of Parameter",
    "command_para": (zh_cn and "命令参数有误") or "Incorrect Command Parameter",
    "command_permission": (zh_cn and "权限有误") or "Permission Error",
    "command_reply": (zh_cn and "来源有误") or "Reply to Message Error",
    "command_type": (zh_cn and "命令类别有误") or "Incorrect Command Type",
    "command_usage": (zh_cn and "用法有误") or "Incorrect Usage",
    # Config
    "config_show": (zh_cn and "查看设置") or "Show Config",
    # Emergency
    "issue": (zh_cn and "发现状况") or "Issue",
    "exchange_invalid": (zh_cn and "数据交换频道失效") or "Exchange Channel Invalid",
    "auto_fix": (zh_cn and "自动处理") or "Auto Fix",
    "protocol_1": (zh_cn and "启动 1 号协议") or "Initiate Protocol 1",
    "transfer_channel": (zh_cn and "频道转移") or "Transfer Channel",
    "emergency_channel": (zh_cn and "应急频道") or "Emergency Channel",
    # Group
    "group_id": (zh_cn and "群组 ID") or "Group ID",
    "group_name": (zh_cn and "群组名称") or "Group Name",
    "leave_approve": (zh_cn and "已批准退出群组") or "Approved to Leave the Group",
    "reason_none": (zh_cn and "无数据") or "No Data",
    "reason_permissions": (zh_cn and "权限缺失") or "Missing Permissions",
    "reason_user": (zh_cn and "缺失 USER") or "Missing USER",
    "refresh": (zh_cn and "刷新群管列表") or "Refresh Admin Lists",
    # Manage
    "approve": (zh_cn and "批准") or "Approve",
    "proceed": (zh_cn and "处理") or "Proceed",
    "delete": (zh_cn and "删除") or "Delete",
    "redact": (zh_cn and "清除") or "Redact",
    "reject": (zh_cn and "拒绝") or "Reject",
    "cancel": (zh_cn and "取消") or "Cancel",

    "ban": (zh_cn and "封禁") or "Ban",
    "channel_id": (zh_cn and "频道 ID") or "Channel ID",
    "ban_watch": (zh_cn and "封禁追踪") or "Ban Watch",
    "delete_watch": (zh_cn and "删除追踪") or "Delete Watch",
    "error_level": (zh_cn and "错误等级") or "Error Level",
    "error_rule": (zh_cn and "错误规则") or "Error Rule",
    "project_target": (zh_cn and "针对项目") or "Target Project",
    "restricted_channel": (zh_cn and "受限频道") or "Restricted Channel",
    "score_total": (zh_cn and "总分") or "Total Score",

    "action_rollback": (zh_cn and "数据回滚") or "Rollback",
    "action_error": (zh_cn and "解除错误") or "Fix Error",
    "action_bad": (zh_cn and "收录消息") or "Contain",
    "action_mole": (zh_cn and "移除例外") or "Remove from Whitelist",
    "action_innocent": (zh_cn and "取消收录") or "Breach",
    "action_delete": (zh_cn and "删除存档") or "Delete Evidence",
    "action_redact": (zh_cn and "清除信息") or "Redact Data",
    "action_recall": (zh_cn and "撤回判误") or "Recall Error",
    "action_approve": (zh_cn and "批准请求") or "Approve Request",
    "action_reject": (zh_cn and "拒绝请求") or "Reject Request",
    "action_unban": (zh_cn and "解禁用户") or "Unban the User",
    "action_forgive": (zh_cn and "清空评分") or "Forgive the User",
    "action_unwatch": (zh_cn and "移除追踪") or "Unwatch the User",
    "action_contact": (zh_cn and "移除联系方式") or "Remove Contact",
    "action_status": (zh_cn and "查询状态") or "Request the Status",
    "action_now": (zh_cn and "立即备份") or "Backup Now",

    "status_error": (zh_cn and "已解明") or "Explained",
    "status_bad": (zh_cn and "已收录") or "Contained",
    "status_mole": (zh_cn and "已移除例外") or "Reset Whitelist",
    "status_innocent": (zh_cn and "已移除收录") or "Reset Containment",
    "status_delete": (zh_cn and "已删除") or "Deleted",
    "status_redact": (zh_cn and "已清除") or "Redacted",
    "status_recall": (zh_cn and "已撤回") or "Recalled",
    "status_proceed": (zh_cn and "已处理") or "Proceeded",
    "status_cancel": (zh_cn and "已取消") or "Cancelled",
    "status_unban": (zh_cn and "已解禁") or "Unbanned",
    "status_commanded": (zh_cn and "已下达指令") or "Commanded",
    "status_requested": (zh_cn and "已发出请求") or "Requested",
    "status_wait": (zh_cn and "等待操作") or "Wait",

    "leave_auto": (zh_cn and "已自动退出群组") or "Leave the Group Automatically",
    "leave_reject": (zh_cn and "已拒绝退群请求") or "Rejected to Leave the Group",
    "leave_request": (zh_cn and "请求退出该群组") or "Request to Leave the Group",
    "leave_handle": (zh_cn and "处理退群请求") or "Deal with the Leave Request",
    "leave_manual": (zh_cn and "手动退群") or "Leave Manually",

    "list_bad": (zh_cn and "查看频道黑名单") or "List Channel Blacklist",
    "list_except": (zh_cn and "查看频道白名单") or "List Channel Whitelist",

    "time_content": (zh_cn and "短期") or "Short Term",
    "time_long": (zh_cn and "长期") or "Long Term",
    "time_temp": (zh_cn and "短期") or "Short Temp",
    "type_content": (zh_cn and "内容收录") or "Contain the Content",
    "type_long": (zh_cn and "内容例外") or "Whitelist the Content",
    "type_temp": (zh_cn and "内容例外") or "Content Whitelist",

    "record_error": (zh_cn and "错误存档") or "Error Record",
    "record_origin": (zh_cn and "原始记录") or "Original Record",

    "add_bad": (zh_cn and "添加频道黑名单") or "Add Bad Channel",
    "add_except": (zh_cn and "添加频道白名单") or "Add Whitelist Channel",
    "in_bad": (zh_cn and "频道已在黑名单中") or "Channel Already Added",
    "in_except": (zh_cn and "频道已在白名单中") or "Channel Already Added",
    "remove_bad": (zh_cn and "移除频道黑名单") or "Remove Bad Channel",
    "remove_except": (zh_cn and "移除频道黑名单") or "Remove Whitelist Channel",
    "no_bad": (zh_cn and "未在黑名单中") or "Not in the Blacklist",
    "no_except": (zh_cn and "未在白名单中") or "Not in the Whitelist",
    "no_score": (zh_cn and "用户未获得评分") or "User Does Not Have Score",
    "no_watch": (zh_cn and "用户未被追踪") or "Not Watched",

    "user_unban": (zh_cn and "解禁用户") or "Unban",
    "user_forgive": (zh_cn and "清空评分") or "Forgive",
    "user_unwatch": (zh_cn and "移除追踪") or "Unwatch",

    "blacklist": (zh_cn and "黑名单") or "Blacklisted",
    "blacklist_add": (zh_cn and "添加黑名单") or "Add to Blacklist",
    "blacklist_remove": (zh_cn and "移除黑名单") or "Remove from Blacklist",
    "whitelist": (zh_cn and "白名单") or "Whitelisted",
    "whitelist_add": (zh_cn and "添加白名单") or "Add to Whitelist",
    "whitelist_remove": (zh_cn and "移除白名单") or "Remove from Whitelist",

    "chat_id": (zh_cn and "对话 ID") or "Chat ID",
    "to_id": (zh_cn and "发送至 ID") or "Delivered to ID",

    # Message Types
    "gam": (zh_cn and "游戏") or "Game",
    "ser": (zh_cn and "服务消息") or "Service",
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
    "contact": (zh_cn and "联系方式") or "Contact Info",
    "more": (zh_cn and "附加信息") or "Extra Info",
    # Terminate
    "auto_ban": (zh_cn and "自动封禁") or "Auto Ban",
    "auto_delete": (zh_cn and "自动删除") or "Auto Delete",
    "name_ban": (zh_cn and "名称封禁") or "Ban by Name",
    "name_examine": (zh_cn and "名称检查") or "Name Examination",
    "op_downgrade": (zh_cn and "操作降级") or "Operation Downgrade",
    "op_upgrade": (zh_cn and "操作升级") or "Operation Upgrade",
    "rule_custom": (zh_cn and "群组自定义") or "Custom Rule",
    "rule_global": (zh_cn and "全局规则") or "Global Rule",
    "score_ban": (zh_cn and "评分封禁") or "Ban by Score",
    "score_user": (zh_cn and "用户评分") or "High Score",
    "watch_ban": (zh_cn and "追踪封禁") or "Watch Ban",
    "watch_delete": (zh_cn and "追踪删除") or "Watch Delete",
    "watch_user": (zh_cn and "敏感追踪") or "Watched User"
}

# Init

all_commands: List[str] = [
    "action",
    "add_bad",
    "add_except",
    "check",
    "clear_bad_channels",
    "clear_bad_users",
    "clear_bad_contents",
    "clear_bad_contacts",
    "clear_except_channels",
    "clear_except_temp",
    "clear_except_long",
    "clear_user_all",
    "clear_user_new",
    "clear_watch_all",
    "clear_watch_ban",
    "clear_watch_delete"
    "config",
    "hide",
    "join",
    "leave",
    "list",
    "ls",
    "now",
    "page",
    "refresh",
    "remove_bad",
    "remove_contact",
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
#             "game": "",
#             "lang": "",
#             "length": "",
#             "freq": "",
#             "score": "",
#             "bio": "",
#             "name": "",
#             "from": "",
#             "contact": "",
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

locks: Dict[str, Lock] = {
    "callback": Lock(),
    "message": Lock(),
    "receive": Lock()
}

receivers: Dict[str, List[str]] = {
    "bad": ["ANALYZE", "APPLY", "AVATAR", "CAPTCHA", "CLEAN", "LANG", "LONG", "MANAGE",
            "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TICKET", "TIP", "USER", "WARN", "WATCH"],
    "config": ["CLEAN", "LANG", "LONG", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN"],
    "except": ["CLEAN", "LANG", "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "WATCH"],
    "leave": ["CAPTCHA", "CLEAN", "LANG", "LONG",
              "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN"],
    "now": ["ANALYZE", "APPLY", "AVATAR", "CLEAN", "CONFIG", "LANG", "LONG", "MANAGE",
            "NOFLOOD", "NOPORN", "NOSPAM", "PM", "RECHECK", "TICKET", "TIP", "USER", "WARN", "WATCH"],
    "refresh": ["AVATAR", "CAPTCHA", "CLEAN", "LANG", "LONG",
                "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN"],
    "score": ["ANALYZE", "CAPTCHA", "CLEAN", "LANG", "LONG", "MANAGE",
              "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN", "WATCH"],
    "status": ["NOSPAM", "REGEX", "USER", "WATCH"],
    "watch": ["ANALYZE", "CAPTCHA", "CLEAN", "LANG", "LONG", "MANAGE",
              "NOFLOOD", "NOPORN", "NOSPAM", "RECHECK", "TIP", "USER", "WARN", "WATCH"]
}

sender: str = "MANAGE"

should_hide: bool = False

usernames: Dict[str, Dict[str, Union[int, str]]] = {}
# usernames = {
#     "SCP_079": {
#         "peer_type": "channel",
#         "peer_id": -1001196128009
#     }
# }

version: str = "0.1.6"

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

records: Dict[str, Dict[str, Union[bool, int, str]]] = {}
# records = {
#     "random_1": {
#         "lock": False,
#         "time": 15112345678,
#         "mid": 123
#     },
#     "random_2": {
#         "lock": False,
#         "time": 15112345678,
#         "mid": 123,
#         "the_id": 12345678
#     },
#     "random_3": {
#         "lock": False,
#         "time": 15112345679,
#         "mid": 124,
#         "project": "USER",
#         "group_id": -10012345678,
#         "group_name": "SCP-079-CHAT",
#         "group_link": "https://t.me/SCP_079_CHAT",
#         "reason": ""
#     }
# }

# Load data
file_list: List[str] = ["bad_ids", "except_ids", "user_ids", "watch_ids", "records"]
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
