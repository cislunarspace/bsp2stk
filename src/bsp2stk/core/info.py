"""BSP星历文件信息读取模块

提供星历文件解析、时间转换和信息格式化功能。
"""
from datetime import datetime, timedelta
from typing import Any

from jplephem.spk import Segment


def get_segment_info(segment: Segment) -> dict[str, Any]:
    """获取单个 segment 的详细信息"""
    start_jd = segment.start_jd
    end_jd = segment.end_jd
    start_dt = jd_to_datetime(start_jd)
    end_dt = jd_to_datetime(end_jd)
    return {
        "center": segment.center,
        "target": segment.target,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "duration_days": end_jd - start_jd,
    }

def jd_to_datetime(jd: float) -> datetime:
    """将儒略日转换为 datetime"""
    # jplephem 使用简化的儒略日
    return datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)

def format_ephemeris_info(bsp_path: str) -> str:
    """格式化输出星历文件信息"""
    from bsp2stk.io.handlers import load_bsp
    kernel = load_bsp(bsp_path)
    segments = list(kernel.segments)
    lines = []
    lines.append(f"文件: {bsp_path}")
    lines.append(f"Segments: {len(segments)}")
    for i, seg in enumerate(segments):
        info = get_segment_info(seg)
        lines.append(f"\nSegment {i+1}:")
        lines.append(f"  Center: {info['center']}")
        lines.append(f"  Target: {info['target']}")
        lines.append(f"  Start: {info['start_time']}")
        lines.append(f"  End: {info['end_time']}")
    return "\n".join(lines)