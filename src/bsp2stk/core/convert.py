from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple

import numpy as np

from bsp2stk.core.ephemeris import BspEphemeris

# Module-level constants
DEFAULT_STEP_SECONDS: float = 60.0
INTERPOLATION_SAMPLES_M1: int = 5
CENTRAL_BODY: str = "Earth"
COORDINATE_SYSTEM: str = "J2000"
INTERPOLATION_METHOD: str = "Lagrange"


def compute_ephemeris(
    bsp_path: str,
    target: int,
    center: int,
    et: float,
    coordinate_system: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute position and velocity using spiceypy.

    .. deprecated::
        This function opens and closes a ``BspEphemeris`` on every call,
        which is wasteful in tight sampling loops. ``convert_bsp_to_stk``
        will be migrated to hold a single ``BspEphemeris`` across the
        whole conversion in a follow-up refactor (#10). Until then this
        thin wrapper preserves the existing call shape.

    Args:
        bsp_path: Path to BSP file
        target: NAIF target ID (e.g., -31 for Voyager 1)
        center: NAIF center ID (e.g., 10 for Sun)
        et: Ephemeris time in seconds past J2000
        coordinate_system: SPICE 坐标系名；默认使用模块常量 COORDINATE_SYSTEM

    Returns:
        Tuple of (position, velocity) in km and km/s
    """
    frame = coordinate_system if coordinate_system is not None else COORDINATE_SYSTEM
    with BspEphemeris.open(bsp_path) as eph:
        return eph.sample(target=target, center=center, et=et, frame=frame)


def convert_bsp_to_stk(
    bsp_path: str,
    stk_path: str,
    segment_index: int = 0,
    step_seconds: float = DEFAULT_STEP_SECONDS,
    progress_callback: Optional[Callable[[float], None]] = None,
    ephemeris_name: Optional[str] = None,
    interpolation_method: Optional[str] = None,
    interpolation_order: Optional[int] = None,
    central_body: Optional[str] = None,
    coordinate_system: Optional[str] = None,
) -> None:
    """将 BSP 文件转换为 STK 格式

    Args:
        bsp_path: BSP 文件路径
        stk_path: STK 输出文件路径
        segment_index: 要使用的 segment 索引
        step_seconds: 采样间隔（秒），默认 60.0
        progress_callback: 进度回调函数，接收 0-1 的进度值
        ephemeris_name: STK 头中的 EphemerisName；默认使用 BSP 文件名（不含扩展名）
        interpolation_method: STK 头插值方法；默认 INTERPOLATION_METHOD
        interpolation_order: v9 头中 InterpolationSamplesM1；默认 INTERPOLATION_SAMPLES_M1
        central_body: CentralBody 字段；默认 CENTRAL_BODY
        coordinate_system: CoordinateSystem 字段，并用于 SPICE spkezr；默认 COORDINATE_SYSTEM

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
    interp_method = interpolation_method if interpolation_method is not None else INTERPOLATION_METHOD
    interp_order = interpolation_order if interpolation_order is not None else INTERPOLATION_SAMPLES_M1
    body = central_body if central_body is not None else CENTRAL_BODY
    coords = coordinate_system if coordinate_system is not None else COORDINATE_SYSTEM

    # 生成 STK 格式数据
    step_jd = step_seconds / 86400.0
    num_points = int((end_jd - start_jd) / step_jd) + 1

    from bsp2stk.core.stk_writer import StkHeader, StkWriter

    header = StkHeader(
        num_points=num_points,
        epoch_jd=start_jd,
        interpolation_method=interp_method,
        interpolation_samples_m1=interp_order,
        central_body=body,
        coordinate_system=coords,
    )

    try:
        with StkWriter.open(stk_path, header) as writer:
            # 采样输出位置速度
            jd = start_jd
            current_step = 0
            while jd <= end_jd:
                # Convert JD to ET (seconds past J2000)
                et = (jd - 2451545.0) * 86400.0
                pos, vel = compute_ephemeris(bsp_path, target, center, et, coordinate_system=coords)
                seconds = jd_to_seconds_since_epoch(jd, start_jd)
                writer.write_sample(seconds, pos, vel)
                jd += step_jd
                current_step += 1
                if progress_callback and num_points > 0:
                    progress_callback(current_step / num_points)
    except OSError as e:
        raise OSError(f"Failed to write STK file '{stk_path}': {e}") from e


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
