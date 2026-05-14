from datetime import datetime, timedelta
from typing import Callable, Optional

from bsp2stk.core.ephemeris import BspEphemeris
from bsp2stk.core.stk_writer import StkFormat, StkHeader, StkWriter

# Module-level constants are derived from StkFormat.default() so the
# single source of truth lives in stk_writer.py. Kept as named values
# for back-compat with imports like `from ... import DEFAULT_STEP_SECONDS`.
_DEFAULT_FORMAT: StkFormat = StkFormat.default()
DEFAULT_STEP_SECONDS: float = _DEFAULT_FORMAT.step_seconds
INTERPOLATION_SAMPLES_M1: int = _DEFAULT_FORMAT.interpolation_samples_m1
CENTRAL_BODY: str = _DEFAULT_FORMAT.central_body
COORDINATE_SYSTEM: str = _DEFAULT_FORMAT.coordinate_system
INTERPOLATION_METHOD: str = _DEFAULT_FORMAT.interpolation_method


def convert_bsp_to_stk(
    bsp_path: str,
    stk_path: str,
    segment_index: int = 0,
    step_seconds: Optional[float] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
    ephemeris_name: Optional[str] = None,
    interpolation_method: Optional[str] = None,
    interpolation_order: Optional[int] = None,
    central_body: Optional[str] = None,
    coordinate_system: Optional[str] = None,
    stk_format: Optional[StkFormat] = None,
) -> None:
    """将 BSP 文件转换为 STK v9.0 格式。

    ``stk_format`` 为 STK 头参数包；为 ``None`` 时使用 :meth:`StkFormat.default`。
    其余五个可选参数（``step_seconds``、``interpolation_method``、
    ``interpolation_order``、``central_body``、``coordinate_system``）为向后
    兼容的覆盖项，非 ``None`` 时会合并到 ``stk_format`` 之上。
    """
    base_format = stk_format if stk_format is not None else StkFormat.default()
    effective_format = base_format.with_overrides(
        step_seconds=step_seconds,
        interpolation_method=interpolation_method,
        interpolation_samples_m1=interpolation_order,
        central_body=central_body,
        coordinate_system=coordinate_system,
    )

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
        step_jd = effective_format.step_seconds / 86400.0
        num_points = int((seg.end_jd - seg.start_jd) / step_jd) + 1
        header = StkHeader.from_format(effective_format, num_points, seg.start_jd)
        coords = effective_format.coordinate_system
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
