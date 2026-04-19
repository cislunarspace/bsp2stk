# BSP2STK 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 构建 bsp2stk CLI/GUI 工具，实现 BSP 星历文件读取和 STK 格式转换。

**架构:** 标准 Python 包结构 + PyQt6 GUI，CLI 和 GUI 独立入口。核心逻辑与界面分离。

**技术栈:** Python 3.13, jplephem (BSP读取), PyQt6 (GUI), numpy, scipy

---

## 文件结构

```
src/bsp2stk/
├── __init__.py
├── __main__.py       # 入口选择
├── cli/
│   ├── __init__.py
│   └── menu.py       # 交互式菜单
├── core/
│   ├── __init__.py
│   ├── convert.py   # BSP → STK
│   └── info.py      # 星历信息
├── io/
│   ├── __init__.py
│   └── handlers.py  # 文件读写
└── gui/
    ├── __init__.py
    ├── main_window.py
    ├── convert_view.py
    └── info_view.py
```

---

## Task 1: 项目基础结构

**Files:**
- Create: `src/bsp2stk/__init__.py`
- Create: `src/bsp2stk/__main__.py`
- Create: `src/bsp2stk/cli/__init__.py`
- Create: `src/bsp2stk/core/__init__.py`
- Create: `src/bsp2stk/io/__init__.py`
- Create: `src/bsp2stk/gui/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: 创建包目录和 `__init__.py` 文件**

创建所有 `__init__.py` 空文件。

- [ ] **Step 2: 编写 `__main__.py`**

```python
def main_cli():
    from bsp2stk.cli.menu import run_menu
    run_menu()

def main_gui():
    from PyQt6.QtWidgets import QApplication
    from bsp2stk.gui.main_window import MainWindow
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        main_gui()
    else:
        main_cli()
```

- [ ] **Step 3: 更新 `pyproject.toml`**

修改包名和入口配置：

```toml
[project]
name = "bsp2stk"
version = "0.1.0"
description = "BSP to STK ephemeris converter"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "numpy>=2.4.4",
    "scipy>=1.17.1",
    "jplephem>=2.18",
    "PyQt6>=6.6",
]

[project.scripts]
bsp2stk = "bsp2stk.__main__:main_cli"
bsp2stk-gui = "bsp2stk.__main__:main_gui"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatchling.build.targets.wheel]
packages = ["src/bsp2stk"]
```

- [ ] **Step 4: 安装包**

```bash
cd /home/ouyangjiahong/codes/atk-demo && uv pip install -e .
```

- [ ] **Step 5: 提交**

```bash
git add src/bsp2stk/__init__.py src/bsp2stk/__main__.py src/bsp2stk/cli/__init__.py src/bsp2stk/core/__init__.py src/bsp2stk/io/__init__.py src/bsp2stk/gui/__init__.py pyproject.toml && git commit -m "feat: scaffold bsp2stk package structure"
```

---

## Task 2: CLI 菜单

**Files:**
- Create: `src/bsp2stk/cli/menu.py`
- Create: `tests/cli/test_menu.py`

- [ ] **Step 1: 编写 CLI 菜单骨架**

```python
def run_menu():
    while True:
        print("\n=== BSP2STK ===")
        print("1. 转换 BSP → STK")
        print("2. 查看星历信息")
        print("q. 退出")
        choice = input("选择: ").strip()
        if choice == "1":
            convert_flow()
        elif choice == "2":
            info_flow()
        elif choice == "q":
            break

def convert_flow():
    print("转换功能待实现")

def info_flow():
    print("信息功能待实现")
```

- [ ] **Step 2: 编写测试占位**

```python
def test_menu_quits():
    # 测试 q 退出
    pass
```

- [ ] **Step 3: 提交**

```bash
git add src/bsp2stk/cli/menu.py && git commit -m "feat: add CLI menu skeleton"
```

---

## Task 3: 核心 — BSP 读取

**Files:**
- Create: `src/bsp2stk/io/handlers.py`
- Create: `tests/io/test_handlers.py`

- [ ] **Step 1: 实现 BSP 读取**

```python
from jplephem.spk import SPK
from pathlib import Path

def load_bsp(file_path: str) -> SPK:
    """加载 BSP 文件，返回 SPK 对象"""
    return SPK.open(file_path)

def list_segments(file_path: str) -> list:
    """列出 BSP 文件中所有 segment 的信息"""
    kernel = load_bsp(file_path)
    segments = []
    for segment in kernel.segments:
        segments.append({
            "center": segment.center,
            "target": segment.target,
            "start": segment.start_jd,
            "end": segment.end_jd,
        })
    return segments
```

- [ ] **Step 2: 编写测试**

```python
def test_load_bsp_voyager():
    bsp_path = Path(__file__).parent.parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    kernel = load_bsp(str(bsp_path))
    assert kernel is not None

def test_list_segments():
    bsp_path = Path(__file__).parent.parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    segments = list_segments(str(bsp_path))
    assert len(segments) > 0
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/io/test_handlers.py -v
```

- [ ] **Step 4: 提交**

```bash
git add src/bsp2stk/io/handlers.py tests/io/test_handlers.py && git commit -m "feat: add BSP file reading with jplephem"
```

---

## Task 4: 核心 — 星历信息展示

**Files:**
- Create: `src/bsp2stk/core/info.py`
- Create: `tests/core/test_info.py`

- [ ] **Step 1: 实现星历信息读取**

```python
from typing import dict
from datetime import datetime, timedelta
from jplephem import JulianDate

def get_segment_info(segment) -> dict:
    """获取单个 segment 的详细信息"""
    start_jd = segment.start_jd
    end_jd = segment.end_jd
    start_dt = jd_to_datetime(start_jd)
    end_dt = jd_to_datetime(end_jd)
    return {
        "center": segment.center,
        "target": segment.target,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "duration_days": end_jd - start_jd,
    }

def jd_to_datetime(jd: float) -> datetime:
    """将儒略日转换为 datetime"""
    # jplephem 使用简化的儒略日
    return datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)

def format_ephemeris_info(bsp_path: str) -> str:
    """格式化输出星历文件信息"""
    from bsp2stk.io.handlers import load_bsp
    kernel = load_bsp(bsp_path)
    lines = []
    lines.append(f"文件: {bsp_path}")
    lines.append(f"Segments: {len(list(kernel.segments))}")
    for i, seg in enumerate(kernel.segments):
        info = get_segment_info(seg)
        lines.append(f"\nSegment {i+1}:")
        lines.append(f"  Center: {info['center']}")
        lines.append(f"  Target: {info['target']}")
        lines.append(f"  Start: {info['start_time']}")
        lines.append(f"  End: {info['end_time']}")
    return "\n".join(lines)
```

- [ ] **Step 2: 编写测试**

```python
def test_jd_to_datetime():
    from bsp2stk.core.info import jd_to_datetime
    dt = jd_to_datetime(2451545.0)
    assert dt.year == 2000 and dt.month == 1 and dt.day == 1
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/core/test_info.py -v
```

- [ ] **Step 4: 提交**

```bash
git add src/bsp2stk/core/info.py tests/core/test_info.py && git commit -m "feat: add ephemeris info reading"
```

---

## Task 5: 核心 — BSP → STK 转换

**Files:**
- Create: `src/bsp2stk/core/convert.py`
- Create: `tests/core/test_convert.py`

- [ ] **Step 1: 研究 STK 格式**

STK (Satellite Tool Kit) 星历文件格式为文本格式，包含表头和数据行。需要确认具体格式规范（Agilio STK documentation）。

- [ ] **Step 2: 实现转换函数骨架**

```python
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
```

- [ ] **Step 3: 编写测试**

```python
def test_convert_produces_file(tmp_path):
    bsp_path = Path(__file__).parent.parent.parent.parent / "bsp" / "Voyager_1_merged.bsp"
    stk_path = tmp_path / "output.stk"
    convert_bsp_to_stk(str(bsp_path), str(stk_path))
    assert stk_path.exists()
    content = stk_path.read_text()
    assert "BEGIN Ephemeris" in content
    assert "END Ephemeris" in content
```

- [ ] **Step 4: 运行测试验证**

```bash
pytest tests/core/test_convert.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/bsp2stk/core/convert.py tests/core/test_convert.py && git commit -m "feat: add BSP to STK conversion"
```

---

## Task 6: CLI 菜单 — 连接核心功能

**Files:**
- Modify: `src/bsp2stk/cli/menu.py`

- [ ] **Step 1: 更新菜单，连接核心功能**

```python
import os
from pathlib import Path
from bsp2stk.core.convert import convert_bsp_to_stk
from bsp2stk.core.info import format_ephemeris_info
from bsp2stk.io.handlers import list_segments

BSP_DIR = Path(__file__).parent.parent.parent.parent / "bsp"
STK_DIR = Path(__file__).parent.parent.parent.parent / "stk"

def convert_flow():
    files = list(BSP_DIR.glob("*.bsp"))
    if not files:
        print("bsp/ 目录中没有找到 .bsp 文件")
        return
    print("\n可用 BSP 文件:")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f.name}")
    choice = input("选择文件编号: ").strip()
    try:
        idx = int(choice) - 1
        bsp_file = files[idx]
    except (ValueError, IndexError):
        print("无效选择")
        return

    segments = list_segments(str(bsp_file))
    print(f"\n可用 Segment ({len(segments)}):")
    for i, seg in enumerate(segments):
        print(f"  {i+1}. Target={seg['target']}, Center={seg['center']}")
    seg_choice = input("选择 Segment 编号 (默认 0): ").strip()
    seg_idx = int(seg_choice) if seg_choice else 0

    stk_file = STK_DIR / f"{bsp_file.stem}.stk"
    convert_bsp_to_stk(str(bsp_file), str(stk_file), seg_idx)
    print(f"转换完成: {stk_file}")

def info_flow():
    files = list(BSP_DIR.glob("*.bsp"))
    if not files:
        print("bsp/ 目录中没有找到 .bsp 文件")
        return
    print("\n可用 BSP 文件:")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f.name}")
    choice = input("选择文件编号: ").strip()
    try:
        idx = int(choice) - 1
        bsp_file = files[idx]
    except (ValueError, IndexError):
        print("无效选择")
        return
    print(format_ephemeris_info(str(bsp_file)))
```

- [ ] **Step 2: 测试 CLI 流程**

```bash
cd /home/ouyangjiahong/codes/atk-demo && python -m bsp2stk
# 手动测试各菜单项
```

- [ ] **Step 3: 提交**

```bash
git add src/bsp2stk/cli/menu.py && git commit -m "feat: wire CLI menu to core functions"
```

---

## Task 7: GUI — 主窗口

**Files:**
- Create: `src/bsp2stk/gui/main_window.py`

- [ ] **Step 1: 实现主窗口**

```python
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BSP2STK")
        self.setGeometry(100, 100, 800, 600)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # 左侧导航
        nav = QWidget()
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        btn_convert = QPushButton("转换")
        btn_info = QPushButton("查看信息")

        nav_layout.addWidget(btn_convert)
        nav_layout.addWidget(btn_info)
        nav_layout.addStretch()

        # 右侧内容区
        self.content = QStackedWidget()

        from bsp2stk.gui.convert_view import ConvertView
        from bsp2stk.gui.info_view import InfoView
        self.content.addWidget(ConvertView())
        self.content.addWidget(InfoView())

        btn_convert.clicked.connect(lambda: self.content.setCurrentIndex(0))
        btn_info.clicked.connect(lambda: self.content.setCurrentIndex(1))

        layout.addWidget(nav, 1)
        layout.addWidget(self.content, 4)
```

- [ ] **Step 2: 提交**

```bash
git add src/bsp2stk/gui/main_window.py && git commit -m "feat: add PyQt6 main window"
```

---

## Task 8: GUI — 转换视图

**Files:**
- Create: `src/bsp2stk/gui/convert_view.py`

- [ ] **Step 1: 实现转换视图**

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from PyQt6.QtCore import Qt
from pathlib import Path

BSP_DIR = Path(__file__).parent.parent.parent.parent / "bsp"
STK_DIR = Path(__file__).parent.parent.parent.parent / "stk"

class ConvertView(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_bsp = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 文件选择
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        btn_select = QPushButton("选择 BSP 文件")
        btn_select.clicked.connect(self._select_file)
        file_layout.addWidget(QLabel("BSP 文件:"))
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        layout.addLayout(file_layout)

        # 转换按钮
        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.clicked.connect(self._do_convert)
        self.btn_convert.setEnabled(False)
        layout.addWidget(self.btn_convert)

        # 结果显示
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(QLabel("输出:"))
        layout.addWidget(self.result)

    def _select_file(self):
        files = list(BSP_DIR.glob("*.bsp"))
        if not files:
            self.result.setText("bsp/ 目录中没有找到 .bsp 文件")
            return
        # 简化：直接打开文件对话框
        path, _ = QFileDialog.getOpenFileName(self, "选择 BSP 文件", str(BSP_DIR), "BSP Files (*.bsp)")
        if path:
            self.selected_bsp = path
            self.file_label.setText(Path(path).name)
            self.btn_convert.setEnabled(True)

    def _do_convert(self):
        if not self.selected_bsp:
            return
        from bsp2stk.core.convert import convert_bsp_to_stk
        bsp_path = self.selected_bsp
        stk_path = STK_DIR / f"{Path(bsp_path).stem}.stk"
        try:
            convert_bsp_to_stk(bsp_path, str(stk_path))
            self.result.setText(f"转换成功: {stk_path}")
        except Exception as e:
            self.result.setText(f"转换失败: {e}")
```

- [ ] **Step 2: 提交**

```bash
git add src/bsp2stk/gui/convert_view.py && git commit -m "feat: add convert view"
```

---

## Task 9: GUI — 信息视图

**Files:**
- Create: `src/bsp2stk/gui/info_view.py`

- [ ] **Step 1: 实现信息视图**

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
from pathlib import Path

BSP_DIR = Path(__file__).parent.parent.parent.parent / "bsp"

class InfoView(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_bsp = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        btn_select = QPushButton("选择 BSP 文件")
        btn_select.clicked.connect(self._select_file)
        file_layout.addWidget(QLabel("BSP 文件:"))
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        layout.addLayout(file_layout)

        self.btn_show = QPushButton("显示信息")
        self.btn_show.clicked.connect(self._show_info)
        self.btn_show.setEnabled(False)
        layout.addWidget(self.btn_show)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(QLabel("星历信息:"))
        layout.addWidget(self.result)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 BSP 文件", str(BSP_DIR), "BSP Files (*.bsp)")
        if path:
            self.selected_bsp = path
            self.file_label.setText(Path(path).name)
            self.btn_show.setEnabled(True)

    def _show_info(self):
        if not self.selected_bsp:
            return
        from bsp2stk.core.info import format_ephemeris_info
        try:
            info = format_ephemeris_info(self.selected_bsp)
            self.result.setText(info)
        except Exception as e:
            self.result.setText(f"读取失败: {e}")
```

- [ ] **Step 2: 提交**

```bash
git add src/bsp2stk/gui/info_view.py && git commit -m "feat: add info view"
```

---

## Task 10: 清理并验证

- [ ] **Step 1: 更新 `pyproject.toml` 依赖**

确保 `jplephem` 已添加:

```toml
dependencies = [
    "numpy>=2.4.4",
    "scipy>=1.17.1",
    "jplephem>=2.18",
    "PyQt6>=6.6",
]
```

- [ ] **Step 2: 安装所有依赖**

```bash
uv pip install -e .
```

- [ ] **Step 3: 验证 CLI**

```bash
bsp2stk
# 测试转换和信息功能
```

- [ ] **Step 4: 验证 GUI**

```bash
bsp2stk-gui
# 验证窗口启动
```

- [ ] **Step 5: 最终提交**

```bash
git add -A && git commit -m "feat: complete bsp2stk with CLI and GUI"
```
