"""BSP ephemeris access module.

封装 jplephem 与 spiceypy 双库访问，提供统一的 BSP 文件读取入口：

- 使用 ``jplephem.SPK.open`` 枚举 segment 元数据（时间范围、目标/中心）。
- 使用 ``spiceypy.furnsh`` / ``spkezr`` 在指定历元上采样位置与速度。
- 作为上下文管理器使用，退出时 ``spiceypy.unload`` 显式卸载内核，
  避免污染全局 SPICE 内核池。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import spiceypy
from jplephem.spk import SPK


DEFAULT_FRAME: str = "J2000"


@dataclass(frozen=True)
class SegmentInfo:
    """单个 SPK segment 的元数据。

    字段命名与 ``jplephem.spk.Segment`` 对齐，便于 ``core/info`` 等
    既有调用方零修改地继续使用 ``segment.start_jd`` 等属性。
    """

    start_jd: float
    end_jd: float
    target: int
    center: int


class BspEphemeris:
    """封装一个 BSP 内核的元数据枚举 + 状态采样。

    典型用法::

        with BspEphemeris.open("path/to/file.bsp") as eph:
            for seg in eph.segments:
                ...
            pos, vel = eph.sample(target=-31, center=10, et=0.0)
    """

    def __init__(self, bsp_path: str) -> None:
        self._bsp_path = bsp_path
        self._spk: SPK | None = None
        self._segments: tuple[SegmentInfo, ...] | None = None
        self._kernel_loaded: bool = False

    # ------------------------------------------------------------------ #
    # construction / context management
    # ------------------------------------------------------------------ #
    @classmethod
    def open(cls, bsp_path: str) -> "BspEphemeris":
        """打开 BSP 文件并完成 jplephem + spiceypy 双重加载。"""
        instance = cls(bsp_path)
        instance._open()
        return instance

    def _open(self) -> None:
        # jplephem: 用于枚举 segment 元数据
        self._spk = SPK.open(self._bsp_path)
        try:
            self._segments = tuple(
                SegmentInfo(
                    start_jd=seg.start_jd,
                    end_jd=seg.end_jd,
                    target=seg.target,
                    center=seg.center,
                )
                for seg in self._spk.segments
            )
        except Exception:
            # 元数据读取失败时清理 jplephem 句柄
            self._close_spk()
            raise

        # spiceypy: 用于状态采样；失败时把已加载的内核回退掉
        try:
            spiceypy.furnsh(self._bsp_path)
            self._kernel_loaded = True
        except Exception:
            self._close_spk()
            raise

    def __enter__(self) -> "BspEphemeris":
        if self._spk is None:
            self._open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        """显式卸载 spiceypy 内核并关闭 jplephem 句柄。"""
        if self._kernel_loaded:
            try:
                spiceypy.unload(self._bsp_path)
            finally:
                self._kernel_loaded = False
        self._close_spk()

    def _close_spk(self) -> None:
        if self._spk is not None:
            close = getattr(self._spk, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
            self._spk = None

    # ------------------------------------------------------------------ #
    # data access
    # ------------------------------------------------------------------ #
    @property
    def segments(self) -> list[SegmentInfo]:
        """返回该 BSP 的所有 segment 元数据（不可变快照的列表副本）。"""
        if self._segments is None:
            raise RuntimeError("BspEphemeris is not open; call .open() or use a 'with' block.")
        return list(self._segments)

    @property
    def path(self) -> str:
        """打开的 BSP 文件路径。"""
        return self._bsp_path

    def sample(
        self,
        target: int,
        center: int,
        et: float,
        frame: str = DEFAULT_FRAME,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """在指定历元（ET 秒 past J2000）采样位置/速度。

        Args:
            target: NAIF 目标 ID（如 -31 表示 Voyager 1）。
            center: NAIF 中心 ID（如 10 表示太阳）。
            et: Ephemeris Time（J2000 起秒）。
            frame: SPICE 坐标系名，默认 ``J2000``。

        Returns:
            ``(position_km, velocity_km_s)``，两个 ``np.ndarray``，
            形状均为 ``(3,)``。
        """
        if not self._kernel_loaded:
            raise RuntimeError("BspEphemeris is not open; call .open() or use a 'with' block.")
        state, _light_time = spiceypy.spkezr(str(target), et, frame, "NONE", str(center))
        position = np.asarray(state[:3])
        velocity = np.asarray(state[3:])
        return position, velocity
