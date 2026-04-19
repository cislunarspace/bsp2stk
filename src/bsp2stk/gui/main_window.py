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
