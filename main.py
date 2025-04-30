from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QTimer, Qt
from transpileQSS import loadStyleSheet
from transpiler import Transpiler
import pymupdf
import globals
import sys


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Sorter")
        self.centerWindow()
        self.fullscreenWindow()
        self.setObjectName("main_window")
        globals.transpiler = Transpiler()

        pageText = f"""{globals.transpiler.readPSML('main.psml')}
            {globals.transpiler.readPSML('choose_pdf.psml')}
            {globals.transpiler.readPSML('top_menu.psml')}"""
        
        globals.transpiler.run(pageText=pageText)
        if globals.transpiler.root is None:
            raise ValueError("Root element not found in the PSML file.")
        
        layout = globals.transpiler.root.load()
        self.setLayout(layout)

        self.style = loadStyleSheet("style.qss", globals.app)
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
    window = Window()
    window.show()
    sys.exit(globals.app.exec())
