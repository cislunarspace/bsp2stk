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