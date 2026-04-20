# STK 输出格式升级：v4.0 → v9.0

## 背景

当前 `bsp2stk` 输出 stk.v.4.0 格式的星历文件，使用儒略日作为时间列。实际需求是输出 stk.v.9.0 格式（参考 `LaunchVehicle.e`），使用相对秒数作为时间列，并包含额外的元数据字段和注释行。

## 目标格式

参考文件 `LaunchVehicle.e` 的 stk.v.9.0 格式：

```
stk.v.9.0

# WrittenBy    STK_v9.2.0

BEGIN Ephemeris

    NumberOfEphemerisPoints		 121

    ScenarioEpoch		 13 Feb 2023 00:00:00.000000

# Epoch in JDate format: 2459988.50000000000000
# Epoch in YYDDD format:   23044.00000000000000


    InterpolationMethod		 Lagrange

    InterpolationSamplesM1		 5

    CentralBody		 Earth

    CoordinateSystem		 J2000

# Time of first point: 14 Feb 2023 00:00:00.000000000 UTCG = 2459989.50000000000000 JDate = 23045.00000000000000 YYDDD

    EphemerisTimePosVel

 8.6400000000000000e+04  4.1144475636834656e+06  ...  (7 columns: time x y z vx vy vz)


END Ephemeris
```

## 设计

### 方案：直接替换（方案 A）

将 `convert.py` 中的输出格式直接从 stk.v.4.0 替换为 stk.v.9.0，不保留旧格式支持。

### 改动范围

#### 1. `src/bsp2stk/core/convert.py`

**版本头**：`stk.v.4.0` → `stk.v.9.0`

**删除的字段**：
- `EphemerisName`
- `Duration`
- `Step`

**新增/修改字段**：
- `NumberOfEphemerisPoints` — 需预计算数据点总数
- `ScenarioEpoch` — 格式改为 `DD Mon YYYY HH:MM:SS.ffffff`（英文月名 + 微秒）
- 注释行 `# Epoch in JDate format: {jdate}`
- 注释行 `# Epoch in YYDDD format: {yyddd}`
- `InterpolationMethod`（原 `Interpolation`）
- `InterpolationSamplesM1`（原 `InterpolationOrder`，值 = 5）
- `CentralBody` — 不变
- `CoordinateSystem` — 不变
- 注释行 `# Time of first point: {datetime} UTCG = {jdate} JDate = {yyddd} YYDDD`
- `EphemerisTimePosVel` — 不变

**时间列**：从儒略日改为相对秒数（相对 ScenarioEpoch），格式 `%23.16e`

**数值列**：全部改为 `%23.16e` 科学计数法

**修改的函数**：
- `convert_bsp_to_stk()` — 重写文件输出逻辑，预计算点数
- `_write_ephemeris_line()` — 改用相对秒数和科学计数法
- `jd_to_stk_epoch()` — 改为英文月名格式

**新增辅助函数**：
- `jd_to_seconds_since_epoch(jd, epoch_jd)` — 儒略日转相对秒数
- `jd_to_yyddd(jd)` — 儒略日转 YYDDD 格式

**常量变更**：
- `INTERPOLATION_ORDER` 重命名为 `INTERPOLATION_SAMPLES_M1`（值不变）

#### 2. `README.md`

- 将示例格式从 stk.v.4.0 替换为 stk.v.9.0
- 更新常量说明

#### 3. 不改动

- `compute_ephemeris()` — 核心计算不变
- `_ensure_kernel_loaded()` — 不变
- CLI/GUI 界面 — 不变
- `io/handlers.py` — 不变

### 数据流

1. 加载 BSP 文件，获取 segment 信息
2. 计算 start_jd 到 end_jd 的采样点总数 → `NumberOfEphemerisPoints`
3. 写入文件头（版本、元数据字段、注释行）
4. 遍历采样点，计算相对秒数和位置速度，以科学计数法写入
5. 写入文件尾 `END Ephemeris`

### YYDDD 格式说明

YYDDD 是 STK 使用的一种时间格式：
- YY = 年份后两位
- DDD = 一年中的第几天（001-366）
- 例如 `23044` 表示 2023 年第 44 天（2 月 13 日）

### ScenarioEpoch 格式

- 英文格式：`13 Feb 2023 00:00:00.000000`
- 使用 Python `strftime("%d %b %Y %H:%M:%S.%f")` 生成
