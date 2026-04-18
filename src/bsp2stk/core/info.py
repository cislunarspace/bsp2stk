from datetime import datetime, timedelta

def get_segment_info(segment) -> dict:
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
    lines = []
    lines.append(f"文件: {bsp_path}")
    lines.append(f"Segments: {len(list(kernel.segments))}")
    for i, seg in enumerate(kernel.segments):
        info = get_segment_info(seg)
        lines.append(f"\nSegment {i+1}:")
        lines.append(f"  Center: {info['center']}")
        lines.append(f"  Target: {info['target']}")
        lines.append(f"  Start: {info['start_time']}")
        lines.append(f"  End: {info['end_time']}")
    return "\n".join(lines)