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
