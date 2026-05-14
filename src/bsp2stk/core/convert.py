from datetime import datetime, timedelta
from typing import Callable, Optional

from bsp2stk.core.ephemeris import BspEphemeris

DEFAULT_STEP_SECONDS: float = 60.0
INTERPOLATION_SAMPLES_M1: int = 5
CENTRAL_BODY: str = "Earth"
COORDINATE_SYSTEM: str = "J2000"
INTERPOLATION_METHOD: str = "Lagrange"


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
    """将 BSP 文件转换为 STK v9.0 格式。"""
    from bsp2stk.core.stk_writer import StkHeader, StkWriter

    try:
        eph_cm = BspEphemeris.open(bsp_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"BSP file not found: {bsp_path}") from e
    except OSError as e:
        raise OSError(f"Failed to read BSP file '{bsp_path}': {e}") from e

    with eph_cm as eph:
        segments = eph.segments
        if not 0 <= segment_index < len(segments):
            raise IndexError(
                f"segment_index {segment_index} out of range: "
                f"valid range is 0 to {len(segments) - 1}"
            )
        seg = segments[segment_index]
        interp_method = interpolation_method if interpolation_method is not None else INTERPOLATION_METHOD
        interp_order = interpolation_order if interpolation_order is not None else INTERPOLATION_SAMPLES_M1
        body = central_body if central_body is not None else CENTRAL_BODY
        coords = coordinate_system if coordinate_system is not None else COORDINATE_SYSTEM
        step_jd = step_seconds / 86400.0
        num_points = int((seg.end_jd - seg.start_jd) / step_jd) + 1
        header = StkHeader(num_points, seg.start_jd, interp_method, interp_order, body, coords)
        try:
            with StkWriter.open(stk_path, header) as writer:
                jd, step = seg.start_jd, 0
                while jd <= seg.end_jd:
                    pos, vel = eph.sample(seg.target, seg.center, (jd - 2451545.0) * 86400.0, frame=coords)
                    writer.write_sample(jd_to_seconds_since_epoch(jd, seg.start_jd), pos, vel)
                    jd += step_jd
                    step += 1
                    if progress_callback and num_points > 0:
                        progress_callback(step / num_points)
        except OSError as e:
            raise OSError(f"Failed to write STK file '{stk_path}': {e}") from e


def jd_to_stk_epoch(jd: float) -> str:
    """儒略日转换为 STK v9.0 时间字符串（英文月名 + 微秒）。"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return dt.strftime("%d %b %Y %H:%M:%S.%f")


def jd_to_yyddd(jd: float) -> str:
    """儒略日转换为 YYDDD 格式字符串。"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return f"{int(dt.strftime('%y')):02d}{dt.timetuple().tm_yday:03d}.00000000000000"


def jd_to_seconds_since_epoch(jd: float, epoch_jd: float) -> float:
    """将儒略日转换为相对于 epoch 的秒数。"""
    return (jd - epoch_jd) * 86400.0
