# BSP2STK 设计文档

## 1. 项目概述

- **项目名称**: bsp2stk
- **项目类型**: CLI + GUI 工具
- **核心功能**: 读取 BSP 星历文件，转换为 STK 格式输出，并支持查看星历文件信息
- **目标用户**: 航天轨道分析相关人员

## 2. 目录结构

```
bsp2stk-demo/
├── bsp/                    # 原始 BSP 星历文件（测试数据）
├── stk/                    # 转换后的 STK 星历文件（测试输出）
├── src/
│   └── bsp2stk/            # 可安装的 Python 包
│       ├── __init__.py
│       ├── __main__.py     # 入口选择（CLI/GUI）
│       ├── cli/
│       │   ├── __init__.py
│       │   └── menu.py     # 交互式菜单
│       ├── core/
│       │   ├── __init__.py
│       │   ├── convert.py  # BSP → STK 转换
│       │   └── info.py    # 星历文件信息读取
│       ├── io/
│       │   ├── __init__.py
│       │   └── handlers.py # 文件读写封装
│       └── gui/
│           ├── __init__.py
│           ├── main_window.py   # 主窗口
│           ├── convert_view.py  # 转换界面
│           └── info_view.py     # 信息查看界面
├── pyproject.toml
└── uv.lock
```

## 3. 功能设计

### 3.1 CLI 模式 (`bsp2stk`)

交互式菜单，循环运行：

1. **转换** — 从 `bsp/` 选择文件，输出到 `stk/`
2. **查看信息** — 显示星历文件详情（卫星名称、时间范围等）
3. **退出** — 输入 q 退出

### 3.2 GUI 模式 (`bsp2stk-gui`)

使用 PyQt6 实现，包含：

- **主窗口** — 左侧导航，右侧内容区
- **转换视图** — 文件选择 → 转换按钮 → 进度/结果
- **信息视图** — 文件选择 → 显示星历信息

### 3.3 核心转换逻辑

- 使用 `jplephem` 读取 BSP 星历
- 解析星历数据（卫星名称、时间范围、位置/速度）
- 生成 STK 格式文件

## 4. 依赖

```toml
dependencies = [
    "numpy>=2.4.4",
    "scipy>=1.17.1",
    "jplephem>=2.18",
    "PyQt6>=6.6",
]
```

## 5. 入口配置

```toml
[project.scripts]
bsp2stk = "bsp2stk.__main__:main_cli"
bsp2stk-gui = "bsp2stk.__main__:main_gui"
```

## 6. 数据流

```
BSP 文件 → jplephem 读取 → core.convert/info 处理 → STK 文件 或 GUI 显示
```

## 7. 测试

- `bsp/` 目录放置 `.bsp` 测试文件
- `stk/` 目录验证转换输出
