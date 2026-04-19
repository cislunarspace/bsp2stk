from bsp2stk.core.info import jd_to_datetime, get_segment_info, format_ephemeris_info


def test_jd_to_datetime():
    dt = jd_to_datetime(2451545.0)
    assert dt.year == 2000 and dt.month == 1 and dt.day == 1


def test_get_segment_info():
    """测试 get_segment_info 能正确提取 segment 信息"""
    bsp_path = "bsp/Voyager_1_merged.bsp"
    from bsp2stk.io.handlers import load_bsp
    kernel = load_bsp(bsp_path)
    segment = kernel.segments[0]
    info = get_segment_info(segment)
    assert "center" in info
    assert "target" in info
    assert "start_time" in info
    assert "end_time" in info
    assert "duration_days" in info
    assert info["duration_days"] > 0


def test_format_ephemeris_info():
    """测试 format_ephemeris_info 能正确格式化星历文件信息"""
    bsp_path = "bsp/Voyager_1_merged.bsp"
    result = format_ephemeris_info(bsp_path)
    assert "文件:" in result
    assert "Segments:" in result
    assert "Segment 1:" in result
    assert "Center:" in result
    assert "Target:" in result
    assert "Start:" in result
    assert "End:" in result