# STK v9.0 Format Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace STK output format from stk.v.4.0 to stk.v.9.0, matching the `LaunchVehicle.e` reference file.

**Architecture:** Modify `convert.py` to output stk.v.9.0 format with relative seconds (not Julian Date) as the time column, scientific notation for all numeric values, and new metadata fields (NumberOfEphemerisPoints, InterpolationSamplesM1, YYDDD/JDate comment lines). Update test and README to match.

**Tech Stack:** Python 3.13, spiceypy, numpy

---

### Task 1: Add helper functions `jd_to_yyddd` and `jd_to_seconds_since_epoch`

**Files:**
- Modify: `src/bsp2stk/core/convert.py:130-142`
- Test: `tests/core/test_convert.py`

- [ ] **Step 1: Write failing tests for the two new helper functions**

Add to `tests/core/test_convert.py`:

```python
from bsp2stk.core.convert import jd_to_stk_epoch, jd_to_yyddd, jd_to_seconds_since_epoch


def test_jd_to_stk_epoch_english_format():
    # JD 2459988.5 = 2023-02-13 00:00:00 UTC
    result = jd_to_stk_epoch(2459988.5)
    assert result == "13 Feb 2023 00:00:00.000000"


def test_jd_to_yyddd():
    # JD 2459988.5 = 2023-02-13, which is day 44 of 2023
    result = jd_to_yyddd(2459988.5)
    assert result == "23044.00000000000000"


def test_jd_to_yyddd_day_one():
    # JD 2459945.5 = 2023-01-01, day 1 of 2023
    result = jd_to_yyddd(2459945.5)
    assert result == "23001.00000000000000"


def test_jd_to_seconds_since_epoch():
    # 1 day = 86400 seconds
    result = jd_to_seconds_since_epoch(2459989.5, 2459988.5)
    assert abs(result - 86400.0) < 1e-10


def test_jd_to_seconds_since_epoch_zero():
    # Same JD = 0 seconds
    result = jd_to_seconds_since_epoch(2459988.5, 2459988.5)
    assert result == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:/Users/ouyan/codes/bsp2stk && uv run pytest tests/core/test_convert.py::test_jd_to_stk_epoch_english_format tests/core/test_convert.py::test_jd_to_yyddd tests/core/test_convert.py::test_jd_to_yyddd_day_one tests/core/test_convert.py::test_jd_to_seconds_since_epoch tests/core/test_convert.py::test_jd_to_seconds_since_epoch_zero -v`
Expected: FAIL — `ImportError` (functions don't exist yet)

- [ ] **Step 3: Implement the helper functions**

Replace `jd_to_stk_epoch` and add the two new functions in `src/bsp2stk/core/convert.py` after line 128 (after `_write_ephemeris_line`):

```python
def jd_to_stk_epoch(jd: float) -> str:
    """儒略日转换为 STK v9.0 时间字符串（英文月名 + 微秒）"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    return dt.strftime("%d %b %Y %H:%M:%S.%f")


def jd_to_yyddd(jd: float) -> str:
    """儒略日转换为 YYDDD 格式字符串"""
    dt = datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)
    yy = dt.strftime("%y")
    ddd = dt.timetuple().tm_yday
    return f"{int(yy):02d}{ddd:03d}.00000000000000"


def jd_to_seconds_since_epoch(jd: float, epoch_jd: float) -> float:
    """将儒略日转换为相对于 epoch 的秒数"""
    return (jd - epoch_jd) * 86400.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Users/ouyan/codes/bsp2stk && uv run pytest tests/core/test_convert.py::test_jd_to_stk_epoch_english_format tests/core/test_convert.py::test_jd_to_yyddd tests/core/test_convert.py::test_jd_to_yyddd_day_one tests/core/test_convert.py::test_jd_to_seconds_since_epoch tests/core/test_convert.py::test_jd_to_seconds_since_epoch_zero -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd C:/Users/ouyan/codes/bsp2stk
git add src/bsp2stk/core/convert.py tests/core/test_convert.py
git commit -m "feat: add jd_to_yyddd and jd_to_seconds_since_epoch helpers"
```

---

### Task 2: Rewrite `convert_bsp_to_stk` output to stk.v.9.0 format

**Files:**
- Modify: `src/bsp2stk/core/convert.py:8-13,50-128`

- [ ] **Step 1: Update constants**

In `src/bsp2stk/core/convert.py`, replace lines 8-13 with:

```python
# Module-level constants
DEFAULT_STEP_SECONDS: float = 60.0
INTERPOLATION_SAMPLES_M1: int = 5
CENTRAL_BODY: str = "Earth"
COORDINATE_SYSTEM: str = "J2000"
INTERPOLATION_METHOD: str = "Lagrange"
```

- [ ] **Step 2: Rewrite `convert_bsp_to_stk` function body**

Replace the body of `convert_bsp_to_stk` (lines 50-128) with:

```python
def convert_bsp_to_stk(
    bsp_path: str,
    stk_path: str,
    segment_index: int = 0,
    step_seconds: float = DEFAULT_STEP_SECONDS,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> None:
    """将 BSP 文件转换为 STK v9.0 格式

    Args:
        bsp_path: BSP 文件路径
        stk_path: STK 输出文件路径
        segment_index: 要使用的 segment 索引
        step_seconds: 采样间隔（秒），默认 60.0
        progress_callback: 进度回调函数，接收 0-1 的进度值

    Raises:
        FileNotFoundError: BSP 文件不存在或无法读取
        IndexError: segment_index 超出范围
        OSError: 写入 STK 文件时出错
    """
    from bsp2stk.io.handlers import load_bsp

    try:
        kernel = load_bsp(bsp_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"BSP file not found: {bsp_path}") from e
    except OSError as e:
        raise OSError(f"Failed to read BSP file '{bsp_path}': {e}") from e

    segments_list = list(kernel.segments)
    if segment_index < 0 or segment_index >= len(segments_list):
        raise IndexError(
            f"segment_index {segment_index} out of range: "
            f"valid range is 0 to {len(segments_list) - 1}"
        )

    segment = segments_list[segment_index]

    # 获取时间范围
    start_jd = segment.start_jd
    end_jd = segment.end_jd
    target = segment.target
    center = segment.center

    # 预计算数据点总数
    step_jd = step_seconds / 86400.0
    num_points = int((end_jd - start_jd) / step_jd) + 1

    # 生成 STK v9.0 格式
    try:
        with open(stk_path, "w") as f:
            f.write("stk.v.9.0\n")
            f.write("\n")
            f.write("BEGIN Ephemeris\n")
            f.write("\n")
            f.write(f"    NumberOfEphemerisPoints\t\t {num_points}\n")
            f.write("\n")
            epoch_str = jd_to_stk_epoch(start_jd)
            f.write(f"    ScenarioEpoch\t\t {epoch_str}\n")
            f.write("\n")
            f.write(f"# Epoch in JDate format: {start_jd:.14f}\n")
            f.write(f"# Epoch in YYDDD format:   {jd_to_yyddd(start_jd)}\n")
            f.write("\n")
            f.write("\n")
            f.write(f"    InterpolationMethod\t\t {INTERPOLATION_METHOD}\n")
            f.write("\n")
            f.write(f"    InterpolationSamplesM1\t\t {INTERPOLATION_SAMPLES_M1}\n")
            f.write("\n")
            f.write(f"    CentralBody\t\t {CENTRAL_BODY}\n")
            f.write("\n")
            f.write(f"    CoordinateSystem\t\t {COORDINATE_SYSTEM}\n")
            f.write("\n")

            # 注释行：第一个数据点的时间信息
            first_point_str = jd_to_stk_epoch(start_jd)
            first_point_jdate = f"{start_jd:.14f}"
            first_point_yyddd = jd_to_yyddd(start_jd)
            f.write(f"# Time of first point: {first_point_str}.000000000 UTCG = {first_point_jdate} JDate = {first_point_yyddd} YYDDD\n")
            f.write("\n")
            f.write("    EphemerisTimePosVel\t\t\n")
            f.write("\n")

            # 采样输出位置速度
            jd = start_jd
            current_step = 0
            while jd <= end_jd:
                et = (jd - 2451545.0) * 86400.0
                pos, vel = compute_ephemeris(bsp_path, target, center, et)
                _write_ephemeris_line(f, jd, start_jd, pos, vel)
                jd += step_jd
                current_step += 1
                if progress_callback and num_points > 0:
                    progress_callback(current_step / num_points)

            f.write("\n")
            f.write("\n")
            f.write("END Ephemeris\n")
    except OSError as e:
        raise OSError(f"Failed to write STK file '{stk_path}': {e}") from e
```

- [ ] **Step 3: Update `_write_ephemeris_line` to use relative seconds and scientific notation**

Replace `_write_ephemeris_line` with:

```python
def _write_ephemeris_line(
    f,
    jd: float,
    epoch_jd: float,
    pos: Tuple[float, float, float],
    vel: Tuple[float, float, float],
) -> None:
    """写入单行星历数据（相对秒数 + 科学计数法）"""
    seconds = jd_to_seconds_since_epoch(jd, epoch_jd)
    f.write(
        f" {seconds:%23.16e}  {pos[0]:%23.16e}  {pos[1]:%23.16e}  {pos[2]:%23.16e}  "
        f"{vel[0]:%23.16e}  {vel[1]:%23.16e}  {vel[2]:%23.16e}\n"
    )
```

- [ ] **Step 4: Run existing test to verify basic conversion still works**

Run: `cd C:/Users/ouyan/codes/bsp2stk && uv run pytest tests/core/test_convert.py::test_convert_produces_file -v`
Expected: PASS (the test only checks for `BEGIN Ephemeris` / `END Ephemeris`)

- [ ] **Step 5: Commit**

```bash
cd C:/Users/ouyan/codes/bsp2stk
git add src/bsp2stk/core/convert.py
git commit -m "feat: output STK v9.0 format with relative seconds and scientific notation"
```

---

### Task 3: Update test to verify v9.0 format output

**Files:**
- Modify: `tests/core/test_convert.py`

- [ ] **Step 1: Update the existing test and add v9.0 format assertions**

Replace `tests/core/test_convert.py` entirely with:

```python
from pathlib import Path
from bsp2stk.core.convert import convert_bsp_to_stk, jd_to_stk_epoch, jd_to_yyddd, jd_to_seconds_since_epoch


def test_convert_produces_file(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9)
    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content


def test_convert_v9_format_structure(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9)
    content = stk_path.read_text()

    # Header
    assert content.startswith("stk.v.9.0\n")

    # Metadata fields present
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
    bsp_path = Path(__file__).parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    convert_bsp_to_stk(str(bsp_path), str(stk_path), segment_index=9)
    content = stk_path.read_text()

    # Data lines should use scientific notation (e+XX or e-XX)
    lines = content.split("\n")
    data_lines = [
        l for l in lines
        if l.startswith(" ") and "e+" in l and not l.strip().startswith("#")
    ]
    assert len(data_lines) > 0, "Expected scientific notation data lines"


def test_jd_to_stk_epoch_english_format():
    # JD 2459988.5 = 2023-02-13 00:00:00 UTC
    result = jd_to_stk_epoch(2459988.5)
    assert result == "13 Feb 2023 00:00:00.000000"


def test_jd_to_yyddd():
    # JD 2459988.5 = 2023-02-13, day 44 of 2023
    result = jd_to_yyddd(2459988.5)
    assert result == "23044.00000000000000"


def test_jd_to_yyddd_day_one():
    # JD 2459945.5 = 2023-01-01, day 1 of 2023
    result = jd_to_yyddd(2459945.5)
    assert result == "23001.00000000000000"


def test_jd_to_seconds_since_epoch():
    result = jd_to_seconds_since_epoch(2459989.5, 2459988.5)
    assert abs(result - 86400.0) < 1e-10


def test_jd_to_seconds_since_epoch_zero():
    result = jd_to_seconds_since_epoch(2459988.5, 2459988.5)
    assert result == 0.0
```

- [ ] **Step 2: Run all tests**

Run: `cd C:/Users/ouyan/codes/bsp2stk && uv run pytest tests/core/test_convert.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
cd C:/Users/ouyan/codes/bsp2stk
git add tests/core/test_convert.py
git commit -m "test: add v9.0 format assertions for STK output"
```

---

### Task 4: Update README.md

**Files:**
- Modify: `README.md:1-23`

- [ ] **Step 1: Replace STK format example and constants description**

Replace lines 5-23 of `README.md` with:

```markdown
STK 格式为：
```
stk.v.9.0

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

 8.6400000000000000e+04  4.1144475636834656e+06  3.8117720687725376e+06  3.0265875408293619e+06 -2.7795146794637697e+02  2.9953764501686993e+02  6.1042717849106232e-01


END Ephemeris

```
> 如果需要修改 STK 格式，可以修改 [`src/bsp2stk/core/convert.py`](src/bsp2stk/core/convert.py) 文件中的常量定义（第 9-13 行），包括时间步长（`DEFAULT_STEP_SECONDS`）、插值方法（`INTERPOLATION_METHOD`）、插值阶数（`INTERPOLATION_SAMPLES_M1`）、中心天体（`CENTRAL_BODY`）和坐标系（`COORDINATE_SYSTEM`）。
```

- [ ] **Step 2: Commit**

```bash
cd C:/Users/ouyan/codes/bsp2stk
git add README.md
git commit -m "docs: update README with stk.v.9.0 format example"
```

---

### Task 5: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd C:/Users/ouyan/codes/bsp2stk && uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 2: Commit (only if any fix was needed)**

If fixes were needed:
```bash
cd C:/Users/ouyan/codes/bsp2stk
git add -A
git commit -m "fix: resolve test failures after v9.0 format upgrade"
```
