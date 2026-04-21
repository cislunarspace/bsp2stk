"""仓库内 BSP/STK 目录及文件对话框起始路径。"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BSP_DIR = _REPO_ROOT / "bsp"
STK_DIR = _REPO_ROOT / "stk"


def bsp_open_dialog_start() -> str:
    """用于 QFileDialog 的起始目录：优先项目 bsp/，否则用户主目录。"""
    if BSP_DIR.is_dir():
        return str(BSP_DIR)
    return str(Path.home())
