# Author: w2422 <z242235718@163.com>
# Copyright (C) 2026 w2422. All rights reserved.

"""
SessionID 管理器
===============
管理 SessionID 的生成、活动追踪和过期清理。
持久化到 temp/.sessions.json，支持服务重启后恢复。
"""

import json
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, List

from config import TEMP_DIR, SESSION_TIMEOUT_HOURS

SESSION_FILE = TEMP_DIR / ".sessions.json"
COOKIE_NAME = "session_id"
SESSION_TIMEOUT = SESSION_TIMEOUT_HOURS * 3600  # 8小时转为秒


def _load_sessions() -> Dict[str, float]:
    """从磁盘加载所有 session 活动时间"""
    try:
        with open(SESSION_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_sessions(sessions: Dict[str, float]):
    """持久化 session 活动时间到磁盘"""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f)


def generate_session_id() -> str:
    """生成一个随机的 SessionID（16 位 hex，128 位随机性）"""
    return uuid.uuid4().hex[:16]


def touch_session(session_id: str):
    """更新 session 的最后活动时间"""
    sessions = _load_sessions()
    sessions[session_id] = time.time()
    _save_sessions(sessions)


def get_expired_sessions() -> List[str]:
    """返回所有超过 SESSION_TIMEOUT 未活动的 session_id 列表"""
    sessions = _load_sessions()
    now = time.time()
    cutoff = now - SESSION_TIMEOUT
    return [sid for sid, last_ts in sessions.items() if last_ts < cutoff]


def remove_session_index(session_ids: List[str]):
    """从索引中移除指定的 session_id"""
    if not session_ids:
        return
    sessions = _load_sessions()
    for sid in session_ids:
        sessions.pop(sid, None)
    _save_sessions(sessions)


def delete_session_directories(session_id: str):
    """删除某个 session 的全部数据目录（input/output/temp 下的子目录）"""
    from config import INPUT_DIR, OUTPUT_DIR, TEMP_DIR
    for base_dir in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR]:
        session_dir = base_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)


def cleanup_expired_sessions() -> int:
    """清理所有过期 session 的文件和索引，返回清理数量"""
    expired = get_expired_sessions()
    if not expired:
        return 0
    for sid in expired:
        delete_session_directories(sid)
    remove_session_index(expired)
    return len(expired)
