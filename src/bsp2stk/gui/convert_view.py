from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from pathlib import Path

BSP_DIR = Path(__file__).parent.parent.parent.parent / "bsp"
STK_DIR = Path(__file__).parent.parent.parent.parent / "stk"


class ConvertWorker(QObject):
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, bsp_path: str, stk_path: str):
        super().__init__()
        self.bsp_path = bsp_path
        self.stk_path = stk_path

    def run(self):
        from bsp2stk.core.convert import convert_bsp_to_stk
        try:
            convert_bsp_to_stk(self.bsp_path, self.stk_path, progress_callback=self._on_progress)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, progress: float):
        self.progress.emit(progress)


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

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

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
        path, _ = QFileDialog.getOpenFileName(self, "选择 BSP 文件", str(BSP_DIR), "BSP Files (*.bsp)")
        if path:
            self.selected_bsp = path
            self.file_label.setText(Path(path).name)
            self.btn_convert.setEnabled(True)

    def _do_convert(self):
        if not self.selected_bsp:
            return

        bsp_path = self.selected_bsp
        STK_DIR.mkdir(parents=True, exist_ok=True)
        stk_path = STK_DIR / f"{Path(bsp_path).stem}.stk"

        self.btn_convert.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.result.setText("转换中...")

        self._worker = ConvertWorker(bsp_path, str(stk_path))
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    def _on_progress(self, progress: float):
        self.progress_bar.setValue(int(progress * 100))

    def _on_finished(self):
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.result.setText(f"转换成功: {self._worker.stk_path}")
        self._cleanup_thread()

    def _on_error(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_convert.setEnabled(True)
        self.result.setText(f"转换失败: {error_msg}")
        self._cleanup_thread()

    def _cleanup_thread(self):
        self._worker_thread.quit()
        self._worker_thread.wait()
        self._worker_thread.deleteLater()
