"""BSP/STK 目录解析。

提供与运行位置无关的目录解析：环境变量 → 当前工作目录下的约定目录 → 回退。

环境变量：
- ``BSP2STK_BSP_DIR``：输入 BSP 文件所在目录。
- ``BSP2STK_STK_DIR``：输出 STK 文件所在目录。
"""

from __future__ import annotations

import os
from pathlib import Path


_BSP_ENV = "BSP2STK_BSP_DIR"
_STK_ENV = "BSP2STK_STK_DIR"


def default_bsp_dir() -> Path | None:
    """解析默认的 BSP 输入目录。

    优先级:
    1. 环境变量 ``BSP2STK_BSP_DIR``（仅当其指向已存在的目录时采用）
    2. ``<cwd>/bsp``（仅当其存在时采用）
    3. 返回 ``None``

    返回 ``None`` 表示无法定位默认目录，调用方应自行处理（例如让
    用户从任意路径选择文件）。
    """
    env_value = os.environ.get(_BSP_ENV)
    if env_value:
        env_path = Path(env_value)
        if env_path.is_dir():
            return env_path

    cwd_candidate = Path.cwd() / "bsp"
    if cwd_candidate.is_dir():
        return cwd_candidate

    return None


def default_stk_dir() -> Path:
    """解析默认的 STK 输出目录。

    优先级:
    1. 环境变量 ``BSP2STK_STK_DIR``（不要求目录已存在；调用方负责 ``mkdir``）
    2. ``<cwd>/stk``（若存在则采用）
    3. ``<cwd>/stk``（兜底；调用方负责 ``mkdir``）

    与 :func:`default_bsp_dir` 不同，本函数始终返回一个 :class:`Path`，
    因为输出目录在转换时总是需要被创建。
    """
    env_value = os.environ.get(_STK_ENV)
    if env_value:
        return Path(env_value)

    return Path.cwd() / "stk"


def bsp_open_dialog_start() -> str:
    """为 QFileDialog 提供起始目录字符串。

    若 :func:`default_bsp_dir` 解析到真实存在的目录则使用之，否则回退
    到用户主目录。
    """
    bsp_dir = default_bsp_dir()
    if bsp_dir is not None and bsp_dir.is_dir():
        return str(bsp_dir)
    return str(Path.home())
