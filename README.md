# bsp2stk

BSP 星历文件转 STK 格式转换工具，同时提供 CLI 交互界面和 PyQt6 图形界面。

## 安装

```bash
uv pip install -e .
```

## 使用

### CLI 模式

```bash
bsp2stk
```

交互式菜单：
- `1` — 转换 BSP → STK
- `2` — 查看星历信息
- `q` — 退出

### GUI 模式

```bash
bsp2stk-gui
```

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
