from pathlib import Path
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
    # Use segment 9 (Earth Barycenter -> Earth) which is Type 2 and works with jplephem
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9)
    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content