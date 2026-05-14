from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from bsp2stk.core.convert import (
    convert_bsp_to_stk,
    jd_to_seconds_since_epoch,
    jd_to_stk_epoch,
    jd_to_yyddd,
)


def make_fake_ephemeris(segments_data, pos=None, vel=None):
    """Create a BspEphemeris.open-shaped context manager fake."""
    fake_eph = MagicMock()
    fake_eph.segments = [
        MagicMock(
            start_jd=s["start_jd"],
            end_jd=s["end_jd"],
            target=s["target"],
            center=s["center"],
        )
        for s in segments_data
    ]
    fake_eph.sample.return_value = (
        pos if pos is not None else np.zeros(3),
        vel if vel is not None else np.zeros(3),
    )
    cm = MagicMock()
    cm.__enter__.return_value = fake_eph
    cm.__exit__.return_value = False
    return cm


def make_segment(start_jd=2459988.5, end_jd=2459989.5, target=399, center=3):
    return {
        "start_jd": start_jd,
        "end_jd": end_jd,
        "target": target,
        "center": center,
    }


def test_jd_to_stk_epoch_english_format():
    # JD 2459989.0 = 2023-02-13 00:00:00
    result = jd_to_stk_epoch(2459989.0)
    assert result == "13 Feb 2023 00:00:00.000000"


def test_jd_to_yyddd():
    # JD 2459989.0 = 2023-02-13, which is day 44 of 2023
    result = jd_to_yyddd(2459989.0)
    assert result == "23044.00000000000000"


def test_jd_to_yyddd_day_one():
    # JD 2459946.0 = 2023-01-01, day 1 of 2023
    result = jd_to_yyddd(2459946.0)
    assert result == "23001.00000000000000"


def test_jd_to_seconds_since_epoch():
    # 1 day = 86400 seconds
    result = jd_to_seconds_since_epoch(2459989.5, 2459988.5)
    assert abs(result - 86400.0) < 1e-10


def test_jd_to_seconds_since_epoch_zero():
    # Same JD = 0 seconds
    result = jd_to_seconds_since_epoch(2459988.5, 2459988.5)
    assert result == 0.0


def test_convert_produces_file(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    segments = [make_segment() for _ in range(10)]

    with patch("bsp2stk.core.convert.BspEphemeris") as mock_cls:
        mock_cls.open.return_value = make_fake_ephemeris(segments)
        convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9, step_seconds=1e12)

    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content


def test_convert_v9_format_structure(tmp_path):
    """Verify the output file has stk.v.9.0 structure fields."""
    bsp_path = str(tmp_path / "fake.bsp")
    stk_path = str(tmp_path / "output.stk")
    fake_pos = np.array([1000.0, 2000.0, 3000.0])
    fake_vel = np.array([1.0, 2.0, 3.0])

    with patch("bsp2stk.core.convert.BspEphemeris") as mock_cls:
        mock_cls.open.return_value = make_fake_ephemeris(
            [make_segment()],
            pos=fake_pos,
            vel=fake_vel,
        )
        convert_bsp_to_stk(bsp_path, stk_path, step_seconds=86400.0)

    content = Path(stk_path).read_text()

    # Header
    assert content.startswith("stk.v.9.0\n")

    # v9.0 metadata fields present
    assert "NumberOfEphemerisPoints" in content
    assert "ScenarioEpoch" in content
    assert "InterpolationMethod" in content
    assert "InterpolationSamplesM1" in content
    assert "CentralBody" in content
    assert "CoordinateSystem" in content
    assert "EphemerisTimePosVel" in content

    # Old v4.0 fields absent
    assert "stk.v.4.0" not in content
    assert "EphemerisName" not in content
    assert "Duration" not in content
    assert "InterpolationOrder" not in content

    # Comment lines present
    assert "# Epoch in JDate format:" in content
    assert "# Epoch in YYDDD format:" in content
    assert "# Time of first point:" in content


def test_convert_v9_scientific_notation(tmp_path):
    """Verify data lines use scientific notation and relative seconds."""
    bsp_path = str(tmp_path / "fake.bsp")
    stk_path = str(tmp_path / "output.stk")
    fake_pos = np.array([4114447.563, 3811772.068, 3026587.540])
    fake_vel = np.array([-277.951, 299.537, 6.104])

    with patch("bsp2stk.core.convert.BspEphemeris") as mock_cls:
        mock_cls.open.return_value = make_fake_ephemeris(
            [make_segment()],
            pos=fake_pos,
            vel=fake_vel,
        )
        convert_bsp_to_stk(bsp_path, stk_path, step_seconds=86400.0)

    content = Path(stk_path).read_text()
    lines = content.split("\n")
    data_lines = [
        l for l in lines if l.startswith(" ") and "e+" in l and not l.strip().startswith("#")
    ]
    assert len(data_lines) > 0, "Expected scientific notation data lines"
    # Verify first column is relative seconds (small number near 0, not a JD like 2459988)
    first_value = data_lines[0].split()[0]
    first_float = float(first_value)
    assert first_float < 1.0, f"First time value should be ~0 (relative seconds), got {first_float}"


def test_convert_stk_header_custom_format_options(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "opts.stk"
    segments = [make_segment() for _ in range(10)]

    with patch("bsp2stk.core.convert.BspEphemeris") as mock_cls:
        mock_cls.open.return_value = make_fake_ephemeris(segments)
        convert_bsp_to_stk(
            str(bsp_path),
            str(stk_path),
            segment_index=9,
            step_seconds=1e12,
            central_body="Moon",
            coordinate_system="J2000",
            interpolation_method="Lagrange",
            interpolation_order=7,
        )

    text = stk_path.read_text()
    assert "    CentralBody\t\t Moon\n" in text
    assert "    CoordinateSystem\t\t J2000\n" in text
    assert "    InterpolationMethod\t\t Lagrange\n" in text
    assert "    InterpolationSamplesM1\t\t 7\n" in text
