def main_cli():
    from bsp2stk.cli.menu import run_menu
    run_menu()

def main_gui():
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtWidgets import QApplication
    from bsp2stk.gui.main_window import MainWindow

    # Windows 常见 125%/150% 缩放下，默认取整会让整窗以非整数倍缩放，文字发糊。
    # PassThrough 与物理像素对齐更好，Ubuntu 上行为也一致。
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

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
