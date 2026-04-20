from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple

import numpy as np
import spiceypy

# Module-level constants
DEFAULT_STEP_SECONDS: float = 60.0
INTERPOLATION_SAMPLES_M1: int = 5
CENTRAL_BODY: str = "Earth"
COORDINATE_SYSTEM: str = "J2000"
INTERPOLATION_METHOD: str = "Lagrange"

# spiceypy cache for loaded kernels
_loaded_kernels: dict[str, bool] = {}


def _ensure_kernel_loaded(bsp_path: str) -> None:
    """Ensure the BSP kernel is loaded in spiceypy."""
    if bsp_path not in _loaded_kernels:
        spiceypy.furnsh(bsp_path)
        _loaded_kernels[bsp_path] = True


def compute_ephemeris(
    bsp_path: str,
    target: int,
    center: int,
    et: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute position and velocity using spiceypy.

    Args:
        bsp_path: Path to BSP file
        target: NAIF target ID (e.g., -31 for Voyager 1)
        center: NAIF center ID (e.g., 10 for Sun)
        et: Ephemeris time in seconds past J2000

    Returns:
        Tuple of (position, velocity) in km and km/s
    """
    _ensure_kernel_loaded(bsp_path)
    state, _ = spiceypy.spkezr(str(target), et, COORDINATE_SYSTEM, 'NONE', str(center))
    position = state[:3]
    velocity = state[3:]
    return position, velocity


def convert_bsp_to_stk(
    bsp_path: str,
    stk_path: str,
    segment_index: int = 0,
    step_seconds: float = DEFAULT_STEP_SECONDS,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> None:
    """将 BSP 文件转换为 STK 格式

    Args:
        bsp_path: BSP 文件路径
        stk_path: STK 输出文件路径
        segment_index: 要使用的 segment 索引
        step_seconds: 采样间隔（秒），默认 60.0
        progress_callback: 进度回调函数，接收 0-1 的进度值

    Raises:
        FileNotFoundError: BSP 文件不存在或无法读取
        IndexError: segment_index 超出范围
        OSError: 写入 STK 文件时出错
    """
    from bsp2stk.io.handlers import load_bsp

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
    target = segment.target
    center = segment.center

    # 生成 STK 格式数据
    step_jd = step_seconds / 86400.0
    num_points = int((end_jd - start_jd) / step_jd) + 1

    try:
        with open(stk_path, "w") as f:
            f.write("stk.v.9.0\n")
            f.write("\n")
            f.write("BEGIN Ephemeris\n")
            f.write("\n")
            f.write(f"    NumberOfEphemerisPoints\t\t {num_points}\n")
            f.write("\n")
            f.write(f"    ScenarioEpoch\t\t {jd_to_stk_epoch(start_jd)}\n")
            f.write("\n")
            f.write(f"# Epoch in JDate format: {start_jd:.14f}\n")
            f.write(f"# Epoch in YYDDD format:   {jd_to_yyddd(start_jd)}\n")
            f.write("\n")
            f.write("\n")
            f.write(f"    InterpolationMethod\t\t {INTERPOLATION_METHOD}\n")
            f.write("\n")
            f.write(f"    InterpolationSamplesM1\t\t {INTERPOLATION_SAMPLES_M1}\n")
            f.write("\n")
            f.write(f"    CentralBody\t\t {CENTRAL_BODY}\n")
            f.write("\n")
            f.write(f"    CoordinateSystem\t\t {COORDINATE_SYSTEM}\n")
            f.write("\n")
            epoch_str = jd_to_stk_epoch(start_jd)
            f.write(
                f"# Time of first point: {epoch_str}.000000000 UTCG"
                f" = {start_jd:.14f} JDate"
                f" = {jd_to_yyddd(start_jd)} YYDDD\n"
            )
            f.write("\n")
            f.write("    EphemerisTimePosVel\t\t\n")
            f.write("\n")

            # 采样输出位置速度
            jd = start_jd
            current_step = 0
            while jd <= end_jd:
                # Convert JD to ET (seconds past J2000)
                et = (jd - 2451545.0) * 86400.0
                pos, vel = compute_ephemeris(bsp_path, target, center, et)
                _write_ephemeris_line(f, jd, start_jd, pos, vel)
                jd += step_jd
                current_step += 1
                if progress_callback and num_points > 0:
                    progress_callback(current_step / num_points)

            f.write("\n")
            f.write("\n")
            f.write("END Ephemeris\n")
    except OSError as e:
        raise OSError(f"Failed to write STK file '{stk_path}': {e}") from e


def _write_ephemeris_line(
    f,
    jd: float,
    epoch_jd: float,
    pos: Tuple[float, float, float],
    vel: Tuple[float, float, float],
) -> None:
    """写入单行星历数据（相对秒数 + 科学计数法）"""
    seconds = jd_to_seconds_since_epoch(jd, epoch_jd)
    f.write(
        f" {seconds:%23.16e}  {pos[0]:%23.16e}  {pos[1]:%23.16e}  {pos[2]:%23.16e}  "
        f"{vel[0]:%23.16e}  {vel[1]:%23.16e}  {vel[2]:%23.16e}\n"
    )


def jd_to_stk_epoch(jd: float) -> str:
    """儒略日转换为 STK v9.0 时间字符串（英文月名 + 微秒）"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return dt.strftime("%d %b %Y %H:%M:%S.%f")


def jd_to_yyddd(jd: float) -> str:
    """儒略日转换为 YYDDD 格式字符串"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    yy = dt.strftime("%y")
    ddd = dt.timetuple().tm_yday
    return f"{int(yy):02d}{ddd:03d}.00000000000000"


def jd_to_seconds_since_epoch(jd: float, epoch_jd: float) -> float:
    """将儒略日转换为相对于 epoch 的秒数"""
    return (jd - epoch_jd) * 86400.0
