def run_menu():
    while True:
        print("\n=== BSP2STK ===")
        print("1. 转换 BSP → STK")
        print("2. 查看星历信息")
        print("q. 退出")
        choice = input("选择: ").strip()
        if choice == "1":
            convert_flow()
        elif choice == "2":
            info_flow()
        elif choice == "q":
            break

import os
from pathlib import Path
from bsp2stk.core.convert import convert_bsp_to_stk
from bsp2stk.core.info import format_ephemeris_info
from bsp2stk.io.handlers import list_segments

BSP_DIR = Path(__file__).parent.parent.parent.parent / "bsp"
STK_DIR = Path(__file__).parent.parent.parent.parent / "stk"

def convert_flow():
    files = list(BSP_DIR.glob("*.bsp"))
    if not files:
        print("bsp/ 目录中没有找到 .bsp 文件")
        return
    print("\n可用 BSP 文件:")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f.name}")
    choice = input("选择文件编号: ").strip()
    try:
        idx = int(choice) - 1
        bsp_file = files[idx]
    except (ValueError, IndexError):
        print("无效选择")
        return

    segments = list_segments(str(bsp_file))
    print(f"\n可用 Segment ({len(segments)}):")
    for i, seg in enumerate(segments):
        print(f"  {i+1}. Target={seg['target']}, Center={seg['center']}")
    seg_choice = input("选择 Segment 编号 (默认 0): ").strip()
    seg_idx = int(seg_choice) if seg_choice else 0

    stk_file = STK_DIR / f"{bsp_file.stem}.stk"
    convert_bsp_to_stk(str(bsp_file), str(stk_file), seg_idx)
    print(f"转换完成: {stk_file}")

def info_flow():
    files = list(BSP_DIR.glob("*.bsp"))
    if not files:
        print("bsp/ 目录中没有找到 .bsp 文件")
        return
    print("\n可用 BSP 文件:")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f.name}")
    choice = input("选择文件编号: ").strip()
    try:
        idx = int(choice) - 1
        bsp_file = files[idx]
    except (ValueError, IndexError):
        print("无效选择")
        return
    print(format_ephemeris_info(str(bsp_file)))