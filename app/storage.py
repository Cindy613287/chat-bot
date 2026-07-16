from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any


PASSWORD_ITERATIONS = 260_000
PASSWORD_SCHEME = "pbkdf2_sha256"
LEGACY_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LOCK = threading.RLock()


def empty_user() -> dict[str, Any]:
    return {"密码": None, "用户信息": {}, "待办任务": []}


def validate_username(username: str) -> str:
    normalized = " ".join(username.strip().split())
    if not 1 <= len(normalized) <= 32:
        raise ValueError("用户名需为 1–32 个字符")
    if any(ord(char) < 32 for char in normalized):
        raise ValueError("用户名不能包含控制字符")
    return normalized


def hash_password(password: str, *, salt: str | None = None) -> str:
    if len(password) < 8:
        raise ValueError("密码至少需要 8 位字符")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False

    if LEGACY_HASH_PATTERN.fullmatch(encoded):
        legacy_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_digest, encoded)

    try:
        scheme, iterations, salt, expected = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


class UserStore:
    """使用原子写入保存本地用户数据，并兼容旧版数据格式。"""

    def __init__(self, path: Path):
        self.path = Path(path)

    def _load_unlocked(self) -> dict[str, dict[str, Any]]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

        if not isinstance(data, dict):
            return {}
        if "用户信息" in data or "待办任务" in data:
            data = {"默认用户": data}
        return data

    def _save_unlocked(self, data: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def get(self, username: str, *, create: bool = False) -> dict[str, Any]:
        username = validate_username(username)
        with _LOCK:
            data = self._load_unlocked()
            if username not in data:
                if not create:
                    return empty_user()
                data[username] = empty_user()
                self._save_unlocked(data)
            return deepcopy(data[username])

    def save(self, username: str, user_data: dict[str, Any]) -> None:
        username = validate_username(username)
        normalized = empty_user()
        normalized.update(deepcopy(user_data))
        normalized["用户信息"] = normalized.get("用户信息") or {}
        normalized["待办任务"] = normalized.get("待办任务") or []
        with _LOCK:
            data = self._load_unlocked()
            data[username] = normalized
            self._save_unlocked(data)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        username = validate_username(username)
        encoded = hash_password(password)
        with _LOCK:
            data = self._load_unlocked()
            if username in data:
                return False, "该用户名已存在"
            user_data = empty_user()
            user_data["密码"] = encoded
            data[username] = user_data
            self._save_unlocked(data)
        return True, "注册成功"

    def authenticate(self, username: str, password: str) -> bool:
        username = validate_username(username)
        with _LOCK:
            data = self._load_unlocked()
            user_data = data.get(username)
            if not user_data or not verify_password(password, user_data.get("密码")):
                return False

            encoded = user_data.get("密码", "")
            if LEGACY_HASH_PATTERN.fullmatch(encoded):
                user_data["密码"] = hash_password(password)
                data[username] = user_data
                self._save_unlocked(data)
            return True
