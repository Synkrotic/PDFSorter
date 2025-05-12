from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QLabel, QScrollArea, QDialog
from PySide6.QtCore import QTimer, Qt
from software_actions.button_actions import *
from transpileQSS import loadStyleSheet
from transpiler import Transpiler
import globals, sys, os


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Sorter")
        self.setObjectName("main_window")
        self.screen = globals.app.primaryScreen()
        self.screenGeometry = self.screen.geometry()
        self.centerWindow()
        self.fullscreenWindow()

        globals.transpiler = Transpiler()

        pageText = ""
        template_folder = os.path.join(os.path.dirname(__file__), "templates")
        for filename in os.listdir(template_folder):
            filepath = os.path.join(template_folder, filename)
            if os.path.isfile(filepath) and filename.endswith(".psml"):
                pageText += f"{globals.transpiler.readPSML(filename)}\n"
                

        globals.transpiler.run(pageText=pageText)
        if globals.transpiler.root is None:
            raise ValueError("Root element not found in the PSML file.")

        layout = globals.transpiler.root.load().widget
        self.setLayout(layout)

        print(globals.transpiler.getStringStructure(globals.transpiler.root))
        self.setStyling()


    def centerWindow(self):
        x = (self.screenGeometry.width() - self.width()) // 2
        y = (self.screenGeometry.height() - self.height()) // 2
        self.move(x, y)


    def fullscreenWindow(self):
        self.setGeometry(self.screenGeometry)
        if globals.fullscreen: self.showFullScreen()

    
    def setStyling(self):
        self.style = loadStyleSheet("style.qss")
        self.setStyleSheet(self.style)
        for dialog in globals.transpiler.dialogs:
            dialog.widget.setStyleSheet(self.style)





if __name__ == "__main__":
    globals.window = Window()
    globals.window.show()
    sys.exit(globals.app.exec())
