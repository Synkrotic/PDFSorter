from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import pymupdf
import globals



def quitSoftware():
    globals.app.quit()

def minimizeSoftware():
    window = globals.app.activeWindow()
    if window is not None:
        window.showMinimized()


def loadPDF(viewerID, filePath=None, pageNumber=0):
    pdfViewer = globals.transpiler.root.getChildrenBySelector(["loader", viewerID])[0]
    
    try:
        if pdfViewer is None: raise ValueError(f"PDF viewer with ID {viewerID} not found or not initialized")
        if filePath: pdfViewer.doc = pymupdf.open(filePath)

        pageIndex = pdfViewer.currentPage + pageNumber

        if pdfViewer.doc is None: raise ValueError("PDF document not loaded")
        if pageIndex < 0 or pageIndex >= pdfViewer.doc.page_count:
            raise ValueError(f"Page index out of range {pageIndex} for {pdfViewer.doc.page_count} pages")
        pdfViewer.currentPage = pageIndex
        page = pdfViewer.doc[pageIndex]
    except Exception as e:
        raise ValueError(f"Error loading PDF: {e}")

    pix = page.get_pixmap()
    mode = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
    image = QImage(pix.samples, pix.width, pix.height, pix.stride, mode)
    
    pixmap = QPixmap.fromImage(image)
    scaled_pixmap = pixmap.scaled(
        pdfViewer.widget.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    pdfViewer.widget.setAlignment(Qt.AlignCenter)
    pdfViewer.widget.setPixmap(scaled_pixmap)





