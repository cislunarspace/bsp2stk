from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

from bsp2stk.core.convert import convert_bsp_to_stk, jd_to_stk_epoch, jd_to_yyddd, jd_to_seconds_since_epoch


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
    # Use segment 0 (Voyager 1 relative to Sun) which has full data coverage
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=0)
    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content


def test_convert_v9_format_structure(tmp_path):
    """Verify the output file has stk.v.9.0 structure fields."""
    bsp_path = str(tmp_path / "fake.bsp")
    stk_path = str(tmp_path / "output.stk")

    # Mock load_bsp to return a fake kernel with one segment
    mock_segment = MagicMock()
    mock_segment.start_jd = 2459988.5
    mock_segment.end_jd = 2459989.5
    mock_segment.target = 399
    mock_segment.center = 3

    mock_kernel = MagicMock()
    mock_kernel.segments = [mock_segment]

    # Mock compute_ephemeris to return fixed position/velocity
    fake_pos = np.array([1000.0, 2000.0, 3000.0])
    fake_vel = np.array([1.0, 2.0, 3.0])

    with patch("bsp2stk.io.handlers.load_bsp", return_value=mock_kernel), \
         patch("bsp2stk.core.convert.compute_ephemeris", return_value=(fake_pos, fake_vel)):
        from bsp2stk.core.convert import convert_bsp_to_stk
        convert_bsp_to_stk(bsp_path, stk_path, step_seconds=86400.0)

    content = open(stk_path).read()

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

    mock_segment = MagicMock()
    mock_segment.start_jd = 2459988.5
    mock_segment.end_jd = 2459989.5
    mock_segment.target = 399
    mock_segment.center = 3

    mock_kernel = MagicMock()
    mock_kernel.segments = [mock_segment]

    fake_pos = np.array([4114447.563, 3811772.068, 3026587.540])
    fake_vel = np.array([-277.951, 299.537, 6.104])

    with patch("bsp2stk.io.handlers.load_bsp", return_value=mock_kernel), \
         patch("bsp2stk.core.convert.compute_ephemeris", return_value=(fake_pos, fake_vel)):
        from bsp2stk.core.convert import convert_bsp_to_stk
        convert_bsp_to_stk(bsp_path, stk_path, step_seconds=86400.0)

    content = open(stk_path).read()
    lines = content.split("\n")
    data_lines = [
        l for l in lines
        if l.startswith(" ") and "e+" in l and not l.strip().startswith("#")
    ]
    assert len(data_lines) > 0, "Expected scientific notation data lines"
    # Verify first column is relative seconds (small number near 0, not a JD like 2459988)
    first_value = data_lines[0].split()[0]
    first_float = float(first_value)
    assert first_float < 1.0, f"First time value should be ~0 (relative seconds), got {first_float}"