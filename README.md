# bsp2stk

BSP 星历文件转 STK 格式转换工具，同时提供 CLI 交互界面和 PyQt6 图形界面，支持 Winodws 和 Linux 。

STK 格式为：
```
stk.v.4.0
BEGIN Ephemeris
 EphemerisName     Voyager_1_merged
 ScenarioEpoch     20 12月 1980 04:45:19
 Duration          1837.301854
 Step              60.0
 Interpolation      Lagrange
 InterpolationOrder 5
 CentralBody        Earth
 CoordinateSystem    J2000
 EphemerisTimePosVel
  2444594.198146  -1442280879.977760  -138839108.340589  45691527.004220  -6.1662299481  -20.0995235459  4.4562592413
  2444594.198841  -1442281249.951409  -138840314.311898  45691794.379741  -6.1662257676  -20.0995225097  4.4562586337
END Ephemeris

```
> 如果需要修改 STK 格式，可以修改 [`src/bsp2stk/core/convert.py`](src/bsp2stk/core/convert.py) 文件中的常量定义（第 8-13 行），包括时间步长（`DEFAULT_STEP_SECONDS`）、插值方法（`INTERPOLATION_METHOD`）、插值阶数（`INTERPOLATION_ORDER`）、中心天体（`CENTRAL_BODY`）和坐标系（`COORDINATE_SYSTEM`）。

## 安装

```bash
uv pip install -e .
```

## 使用

### CLI 模式

```bash
uv run bsp2stk
```

交互式菜单：
- `1` — 转换 BSP → STK
- `2` — 查看星历信息
- `q` — 退出

![bsp2stk](bsp2stk.png)

### GUI 模式

```bash
uv run bsp2stk-gui
```

![bsp2stk-gui](bsp2stk-gui.png)

## 目录结构

```
bsp/        # 原始 BSP 星历文件（测试数据）
stk/        # 转换后的 STK 星历文件（输出）
src/bsp2stk/  # Python 包源码
```

## 依赖

- Python >= 3.13
- jplephem — BSP 星历读取
- numpy, scipy — 数据处理
- PyQt6 — 图形界面
