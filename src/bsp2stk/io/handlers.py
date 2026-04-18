from jplephem.spk import SPK
from pathlib import Path


def load_bsp(file_path: str) -> SPK:
    """加载 BSP 文件，返回 SPK 对象"""
    return SPK.open(file_path)


def list_segments(file_path: str) -> list:
    """列出 BSP 文件中所有 segment 的信息"""
    kernel = load_bsp(file_path)
    segments = []
    for segment in kernel.segments:
        segments.append({
            "center": segment.center,
            "target": segment.target,
            "start": segment.start_jd,
            "end": segment.end_jd,
        })
    return segments