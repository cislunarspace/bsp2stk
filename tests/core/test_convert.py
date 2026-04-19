from pathlib import Path
from bsp2stk.core.convert import convert_bsp_to_stk


def test_convert_produces_file(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    # Use segment 9 (Earth Barycenter -> Earth) which is Type 2 and works with jplephem
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9)
    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content