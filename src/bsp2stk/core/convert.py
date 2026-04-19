from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from bsp2stk.io.handlers import load_bsp

# Module-level constants
DEFAULT_STEP_SECONDS: float = 60.0
INTERPOLATION_ORDER: int = 5
CENTRAL_BODY: str = "Earth"
COORDINATE_SYSTEM: str = "J2000"
INTERPOLATION_METHOD: str = "Lagrange"


def convert_bsp_to_stk(
    bsp_path: str,
    stk_path: str,
    segment_index: int = 0,
    step_seconds: float = DEFAULT_STEP_SECONDS,
) -> None:
    """将 BSP 文件转换为 STK 格式

    Args:
        bsp_path: BSP 文件路径
        stk_path: STK 输出文件路径
        segment_index: 要使用的 segment 索引
        step_seconds: 采样间隔（秒），默认 60.0

    Raises:
        FileNotFoundError: BSP 文件不存在或无法读取
        IndexError: segment_index 超出范围
        OSError: 写入 STK 文件时出错
    """
    try:
        kernel = load_bsp(bsp_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"BSP file not found: {bsp_path}") from e
    except OSError as e:
        raise OSError(f"Failed to read BSP file '{bsp_path}': {e}") from e

    segments_list = list(kernel.segments)
    if segment_index < 0 or segment_index >= len(segments_list):
        raise IndexError(
            f"segment_index {segment_index} out of range: "
            f"valid range is 0 to {len(segments_list) - 1}"
        )

    segment = segments_list[segment_index]

    # 获取时间范围内的采样点
    start_jd = segment.start_jd
    end_jd = segment.end_jd

    # 生成 STK 格式数据
    try:
        with open(stk_path, "w") as f:
            f.write("stk.v.4.0\n")
            f.write("BEGIN Ephemeris\n")
            f.write(f" EphemerisName     {Path(bsp_path).stem}\n")
            f.write(f" ScenarioEpoch     {jd_to_stk_epoch(start_jd)}\n")
            f.write(f" Duration          {end_jd - start_jd:.6f}\n")
            f.write(f" Step              {step_seconds:.1f}\n")
            f.write(f" Interpolation      {INTERPOLATION_METHOD}\n")
            f.write(f" InterpolationOrder {INTERPOLATION_ORDER}\n")
            f.write(f" CentralBody        {CENTRAL_BODY}\n")
            f.write(f" CoordinateSystem    {COORDINATE_SYSTEM}\n")
            f.write(" EphemerisTimePosVel\n")

            # 采样输出位置速度
            jd = start_jd
            step_jd = step_seconds / 86400.0
            while jd <= end_jd:
                pos, vel = segment.compute_and_differentiate(jd)
                _write_ephemeris_line(f, jd, pos, vel)
                jd += step_jd

            f.write("END Ephemeris\n")
    except OSError as e:
        raise OSError(f"Failed to write STK file '{stk_path}': {e}") from e


def _write_ephemeris_line(f, jd: float, pos: Tuple[float, float, float], vel: Tuple[float, float, float]) -> None:
    """写入单行星历数据"""
    f.write(
        f"  {jd:.6f}  {pos[0]:.6f}  {pos[1]:.6f}  {pos[2]:.6f}  "
        f"{vel[0]:.10f}  {vel[1]:.10f}  {vel[2]:.10f}\n"
    )


def jd_to_stk_epoch(jd: float) -> str:
    """儒略日转换为 STK 时代字符串"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return dt.strftime("%d %b %Y %H:%M:%S")