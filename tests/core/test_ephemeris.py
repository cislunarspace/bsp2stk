"""Unit tests for ``bsp2stk.core.ephemeris.BspEphemeris``."""
from pathlib import Path

import numpy as np
import pytest
import spiceypy

from bsp2stk.core.ephemeris import BspEphemeris, SegmentInfo


BSP_PATH = str(Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp")


def test_open_returns_ephemeris():
    with BspEphemeris.open(BSP_PATH) as eph:
        assert eph.path == BSP_PATH


def test_segments_enumeration():
    with BspEphemeris.open(BSP_PATH) as eph:
        segments = eph.segments
        assert len(segments) > 0
        first = segments[0]
        assert isinstance(first, SegmentInfo)
        # 字段命名与 jplephem.spk.Segment 对齐
        assert first.start_jd < first.end_jd
        assert isinstance(first.target, int)
        assert isinstance(first.center, int)


def test_segments_match_jplephem_directly():
    """``BspEphemeris.segments`` 与 ``jplephem`` 直读的元数据一致。"""
    from jplephem.spk import SPK

    spk = SPK.open(BSP_PATH)
    try:
        expected = [
            (s.start_jd, s.end_jd, s.target, s.center) for s in spk.segments
        ]
    finally:
        spk.close()

    with BspEphemeris.open(BSP_PATH) as eph:
        actual = [(s.start_jd, s.end_jd, s.target, s.center) for s in eph.segments]

    assert actual == expected


def test_sample_returns_position_velocity():
    """对 Earth (399) 相对 Earth Barycenter (3) 采样应返回有限值。"""
    with BspEphemeris.open(BSP_PATH) as eph:
        # 使用 segment 9: target=399, center=3
        seg = eph.segments[9]
        # 选段中点对应的 ET（J2000 起秒）
        mid_jd = 0.5 * (seg.start_jd + seg.end_jd)
        et = (mid_jd - 2451545.0) * 86400.0
        pos, vel = eph.sample(target=seg.target, center=seg.center, et=et)

    assert isinstance(pos, np.ndarray)
    assert isinstance(vel, np.ndarray)
    assert pos.shape == (3,)
    assert vel.shape == (3,)
    assert np.all(np.isfinite(pos))
    assert np.all(np.isfinite(vel))
    # Earth 相对 EMB 的距离应为几千 km（地月质心偏移）
    assert 0.0 < np.linalg.norm(pos) < 1e6


def test_context_manager_unloads_spice_kernel():
    """``__exit__`` 之后 spiceypy 内核池中不应残留该 BSP。"""
    before = spiceypy.ktotal("ALL")
    with BspEphemeris.open(BSP_PATH):
        during = spiceypy.ktotal("ALL")
        assert during == before + 1
    after = spiceypy.ktotal("ALL")
    assert after == before, "spiceypy kernel was not unloaded on __exit__"


def test_open_twice_in_sequence_does_not_leak_state():
    """连续两次打开/关闭同一个 BSP 应保持内核池干净。"""
    before = spiceypy.ktotal("ALL")
    for _ in range(2):
        with BspEphemeris.open(BSP_PATH) as eph:
            _ = eph.segments
        assert spiceypy.ktotal("ALL") == before


def test_sample_outside_open_raises():
    eph = BspEphemeris(BSP_PATH)
    with pytest.raises(RuntimeError):
        eph.sample(target=399, center=3, et=0.0)


def test_segments_outside_open_raises():
    eph = BspEphemeris(BSP_PATH)
    with pytest.raises(RuntimeError):
        _ = eph.segments
