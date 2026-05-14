from pathlib import Path
from bsp2stk.io.handlers import load_bsp


def test_load_bsp_voyager():
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    kernel = load_bsp(str(bsp_path))
    assert kernel is not None
