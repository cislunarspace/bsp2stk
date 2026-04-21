from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QFrame,
    QButtonGroup,
)

from bsp2stk.gui.convert_view import ConvertView
from bsp2stk.gui.info_view import InfoView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BSP2STK")
        self.setMinimumSize(QSize(720, 600))
        self.resize(880, 680)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        nav_frame = QFrame()
        nav_frame.setFrameShape(QFrame.Shape.StyledPanel)
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(8)

        btn_convert = QPushButton("转换")
        btn_info = QPushButton("查看信息")
        for btn in (btn_convert, btn_info):
            btn.setCheckable(True)

        nav_group = QButtonGroup(self)
        nav_group.setExclusive(True)
        nav_group.addButton(btn_convert, 0)
        nav_group.addButton(btn_info, 1)
        btn_convert.setChecked(True)

        nav_layout.addWidget(btn_convert)
        nav_layout.addWidget(btn_info)
        nav_layout.addStretch()

        self.content = QStackedWidget()
        self.convert_view = ConvertView()
        self.info_view = InfoView()
        self.content.addWidget(self.convert_view)
        self.content.addWidget(self.info_view)

        self.convert_view.bsp_path_changed.connect(
            lambda p: self._propagate_shared_bsp(p, self.convert_view)
        )
        self.info_view.bsp_path_changed.connect(
            lambda p: self._propagate_shared_bsp(p, self.info_view)
        )

        nav_group.idClicked.connect(self.content.setCurrentIndex)

        def on_page_changed(index: int) -> None:
            btn_convert.setChecked(index == 0)
            btn_info.setChecked(index == 1)

        self.content.currentChanged.connect(on_page_changed)

        layout.addWidget(nav_frame, 0)
        layout.addWidget(self.content, 1)

    def _propagate_shared_bsp(self, path: str, origin: QWidget) -> None:
        if origin is not self.convert_view:
            self.convert_view.set_shared_bsp(path)
        if origin is not self.info_view:
            self.info_view.set_shared_bsp(path)
