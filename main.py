from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QLabel, QScrollArea
from PySide6.QtCore import QTimer, Qt
from software_actions.button_actions import loadPDF, quitSoftware, minimizeSoftware
from transpileQSS import loadStyleSheet
from transpiler import Transpiler
import globals
import sys


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Sorter")
        self.centerWindow()
        self.fullscreenWindow()
        self.setObjectName("main_window")
        globals.transpiler = Transpiler(True)

        pageText = f"""{globals.transpiler.readPSML('main.psml')}
            {globals.transpiler.readPSML('choose_pdf.psml')}
            {globals.transpiler.readPSML('top_menu.psml')}"""

        globals.transpiler.run(pageText=pageText)
        if globals.transpiler.root is None:
            raise ValueError("Root element not found in the PSML file.")

        layout = globals.transpiler.root.load()
        self.setLayout(layout)

        self.style = loadStyleSheet("style.qss", globals.app, True)
        self.setStyleSheet(self.style)


    def centerWindow(self):
        screen = globals.app.primaryScreen()
        screenGeometry = screen.geometry()
        x = (screenGeometry.width() - self.width()) // 2
        y = (screenGeometry.height() - self.height()) // 2
        self.move(x, y)


    def fullscreenWindow(self):
        screen = globals.app.primaryScreen()
        screenGeometry = screen.geometry()
        self.setGeometry(screenGeometry)
        self.showFullScreen()





if __name__ == "__main__":
    globals.window = Window()
    globals.window.show()
    sys.exit(globals.app.exec())
