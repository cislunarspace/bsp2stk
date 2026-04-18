def test_jd_to_datetime():
    from bsp2stk.core.info import jd_to_datetime
    dt = jd_to_datetime(2451545.0)
    assert dt.year == 2000 and dt.month == 1 and dt.day == 1