import pymupdf
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QPushButton
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt



class PDFViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.pageIndex = 0

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        self.setLayout(layout)


    def loadPDF(self, filePath):
        self.doc = pymupdf.open(filePath)
        self.pageIndex = 0
        self.showPage(self.pageIndex)


    def showPage(self, index):
        page = self.doc[index]
        pix = page.get_pixmap()

        mode = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, mode)

        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)
        self.label.adjustSize()


    def nextPage(self):
        if self.pageIndex + 1 < len(self.doc):
            self.pageIndex += 1
            self.showPage(self.pageIndex)
    

    def pageBack(self):
        if self.pageIndex - 1 >= 0:
            self.pageIndex -= 1
            self.showPage(self.pageIndex)
