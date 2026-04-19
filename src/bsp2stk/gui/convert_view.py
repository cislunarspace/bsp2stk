from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
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
        STK_DIR.mkdir(parents=True, exist_ok=True)
        stk_path = STK_DIR / f"{Path(bsp_path).stem}.stk"
        try:
            convert_bsp_to_stk(bsp_path, str(stk_path))
            self.result.setText(f"转换成功: {stk_path}")
        except Exception as e:
            self.result.setText(f"转换失败: {e}")