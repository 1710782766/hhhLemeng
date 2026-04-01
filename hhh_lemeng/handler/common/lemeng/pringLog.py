import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "ts": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)


def shorten_str(s: str, max_len: int = 50) -> str:
    if len(s) <= max_len:
        return s
    # 保留开头和结尾，长度大约一半一半
    keep = max_len // 2
    return f"{s[:keep]}...{s[-keep:]}"


def _json_str(data: str) -> str:
    """将字符串转为标准 JSON 格式（双引号包裹，特殊字符转义）"""
    return json.dumps(data, ensure_ascii=False)


def shorten_json(data, max_items: int = 20, depth: int = 0) -> str:
    """
    简化大 JSON，截断过长数组和嵌套对象，保持可读性

    Args:
        data: 要简化的数据
        max_items: 数组最多显示元素数
        depth: 当前递归深度（用于控制嵌套层数）

    Returns:
        简化后的字符串
    """
    if depth > 3:
        # 嵌套超过3层，直接用占位符
        if isinstance(data, dict):
            return "{...}"
        elif isinstance(data, list):
            return "[...]"
        elif isinstance(data, bool):
            return "true" if data else "false"
        elif data is None:
            return "null"
        elif isinstance(data, str):
            return _json_str(data)
        else:
            return repr(data)

    if isinstance(data, dict):
        if not data:
            return "{}"
        items = []
        for k, v in data.items():
            items.append(f"{_json_str(k)}: {shorten_json(v, max_items, depth + 1)}")
        if depth == 0 and len(items) > 20:
            # 顶层对象，字段太多也截断
            return "{ " + ", ".join(items[:20]) + f", ... 共{len(data)}个字段 }}"
        return "{ " + ", ".join(items) + " }"

    elif isinstance(data, list):
        if not data:
            return "[]"
        if len(data) > max_items:
            shown = [
                shorten_json(item, max_items, depth + 1) for item in data[:max_items]
            ]
            return "[" + ", ".join(shown) + f", ... 共{len(data)}个]"
        return (
            "["
            + ", ".join(shorten_json(item, max_items, depth + 1) for item in data)
            + "]"
        )

    elif isinstance(data, str):
        if len(data) > 100:
            return f'"{data[:50]}...{data[-30:]}"'
        return _json_str(data)

    elif isinstance(data, bool):
        return "true" if data else "false"

    elif data is None:
        return "null"

    else:
        return repr(data)


class Base64ShortenFilter(logging.Filter):
    """自动截断过长的 Base64 字符串"""

    pattern = re.compile(r"[A-Za-z0-9+/=]{100,}")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        record.msg = self.pattern.sub(
            lambda m: shorten_str(m.group(0), 60),
            msg,
        )
        return True


def get_log(base_dir: Path) -> logging.Logger:
    APP_ENV = os.environ.get("APP_ENV", "dev")

    logger = logging.getLogger("pringLog")

    if logger.handlers:
        return logger

    # ========= 全局最低级别 =========
    logger.setLevel(logging.INFO)

    # ========= formatter =========
    verbose_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | "
        "%(filename)s:%(lineno)d | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    simple_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # ========= dev：文件 =========
    if APP_ENV == "dev":
        handler = RotatingFileHandler(
            filename=base_dir / "logging.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(verbose_fmt)
        logger.addHandler(handler)

    # ========= staging：stdout =========
    elif APP_ENV == "staging":
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(verbose_fmt)
        logger.addHandler(handler)

    # ========= prod：stdout（最小日志） =========
    elif APP_ENV == "prod":
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        handler.setFormatter(simple_fmt)
        # handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    else:
        raise RuntimeError(f"Unknown APP_ENV: {APP_ENV}")

    logger.propagate = False
    return logger
