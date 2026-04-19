from pathlib import Path
from bsp2stk.io.handlers import load_bsp


def convert_bsp_to_stk(bsp_path: str, stk_path: str, segment_index: int = 0):
    """将 BSP 文件转换为 STK 格式"""
    kernel = load_bsp(bsp_path)
    segment = list(kernel.segments)[segment_index]

    # 获取时间范围内的采样点
    start_jd = segment.start_jd
    end_jd = segment.end_jd

    # 生成 STK 格式数据
    with open(stk_path, "w") as f:
        f.write(f"stk.v.4.0\n")
        f.write(f"BEGIN Ephemeris\n")
        f.write(f" EphemerisName     {Path(bsp_path).stem}\n")
        f.write(f" ScenarioEpoch     {jd_to_stk_epoch(start_jd)}\n")
        f.write(f" Duration          {end_jd - start_jd:.6f}\n")
        f.write(f" Step              60.0\n")  # 每60秒一个点
        f.write(f" Interpolation      Lagrange\n")
        f.write(f" InterpolationOrder 5\n")
        f.write(f" CentralBody        Earth\n")
        f.write(f" CoordinateSystem    J2000\n")
        f.write(f" EphemerisTimePosVel\n")

        # 采样输出位置速度
        jd = start_jd
        while jd <= end_jd:
            pos, vel = segment.compute_and_differentiate(jd)
            f.write(f"  {jd:.6f}  {pos[0]:.6f}  {pos[1]:.6f}  {pos[2]:.6f}  {vel[0]:.10f}  {vel[1]:.10f}  {vel[2]:.10f}\n")
            jd += 60.0 / 86400.0  # 60秒

        f.write(f"END Ephemeris\n")


def jd_to_stk_epoch(jd: float) -> str:
    """儒略日转换为 STK 时代字符串"""
    from datetime import datetime, timedelta
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return dt.strftime("%d %b %Y %H:%M:%S")