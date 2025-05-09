from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer
from transpileQSS import loadStyleSheet
import pymupdf, globals, os, platform, subprocess



# Built in actions
def quitSoftware():
    globals.app.quit()

def minimizeSoftware():
    window = globals.app.activeWindow()
    if window is not None:
        window.showMinimized()


def toggleDialog(dialogID):
    dialog = [dialog for dialog in globals.transpiler.dialogs if dialogID in dialog.attributes.get("id")][0]
    if dialog.widget.isVisible():
        QTimer.singleShot(0, lambda: dialog.widget.reject())
    else:
        QTimer.singleShot(0, lambda: dialog.widget.exec())





# Maybe built in?
def loadPDFPage(loaderID, filePath=None, pageNumber=0):
    pdfLoader = globals.transpiler.root.getChildrenBySelector(["loader", loaderID])[0]

    try:
        if pdfLoader is None:
            print(f"PDF loader with ID {loaderID} not found or not initialized")
            return
        if filePath: pdfLoader.doc = pymupdf.open(filePath)

        pageIndex = pdfLoader.currentPage + pageNumber

        if pdfLoader.doc is None: raise ValueError("PDF document not loaded")
        if pageIndex < 0 or pageIndex >= pdfLoader.doc.page_count:
            print(f"Page index out of range {pageIndex} for {pdfLoader.doc.page_count} pages")
            return
        pdfLoader.currentPage = pageIndex
        page = pdfLoader.doc[pageIndex]
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return

    pix = page.get_pixmap()
    mode = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
    image = QImage(pix.samples, pix.width, pix.height, pix.stride, mode)
    
    pixmap = QPixmap.fromImage(image)

    size = pdfLoader.widget.size()
    if pixmap.height() > pixmap.width(): size *= 2
    scaled_pixmap = pixmap.scaled(
        size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    pdfLoader.widget.setAlignment(Qt.AlignCenter)
    pdfLoader.widget.setPixmap(scaled_pixmap)
    pdfLoader.widget.setFixedSize(scaled_pixmap.size())

def loadPDF(viewerID, filePath):
    pdfViewer = globals.transpiler.root.getChildrenBySelector(["box", viewerID])[0]
    pdfViewer.container.layout().setAlignment(Qt.AlignCenter)

    try:
        if pdfViewer is None:
            print(f"PDF viewer with ID {viewerID} not found or not initialized")
            return

        pdfViewer.deleteChildren()

        pdfDoc = pymupdf.open(filePath)
        pageCount = pdfDoc.page_count
        for pageNum in range(pageCount):
            data = {
                "tag": "loader",
                "parent": pdfViewer,
                "attributes": {
                    "id": f"pdf{pageNum}",
                    "class": "pdf_page",
                    "src": f"{filePath}:{pageNum}",
                    "type": "pdf"
                },
                "content": ""
            }
            elem = globals.transpiler.createElement(data)
            elem.parent.children.append(elem)
            elem.load(elem.parent)
        globals.window.style = loadStyleSheet("style.qss")
        globals.window.setStyleSheet(globals.window.style)

    except Exception as e:
        print(f"Error loading PDF: {e}")
        return
    




# Custom button actions
def loadPDFOptions():
    pdfs = [str(f) for f in os.listdir(globals.inputDirectory) if f.endswith('.pdf')]
    container = globals.transpiler.root.getChildrenBySelector(["nd", "pdf_selections_container"])[0]
    
    if container is None:
        print("PDF selection container not found")
        return
    
    container.deleteChildren()

    for pdf in pdfs:
        elementData = {
            "tag": "btn",
            "parent": container,
            "attributes": {
                "class": "pdf_selection",
                "id": f"{"selected_pdf" if pdf in globals.selectedPDF else ""}",
                "onclick": f"setSelectedPDF('{globals.inputDirectory}/{pdf}')",
            },
            "content": pdf,
        }
        elem = globals.transpiler.createElement(elementData)
        elem.parent.children.append(elem)
        elem.load(container)
        elem.widget.style = globals.window.style
        elem.widget.setStyleSheet(globals.window.style)
    globals.window.style = loadStyleSheet("style.qss")
    globals.window.setStyleSheet(globals.window.style)

def setSelectedPDF(pdfPath):
    globals.selectedPDF = pdfPath
    loadPDF("pdf_viewer", pdfPath)
    dialog = globals.transpiler.root.getChildrenBySelector(["dialog", "choose_pdf_dialog"])[0]
    dialog.widget.accept()


def printFile(path):
    try:
        system = platform.system()
        if not os.path.exists(path):
            print(f"File does not exist: {path}")
            return
        if system == "Windows":
            os.startfile(path)

        elif system == "Darwin":  # MacOS
            subprocess.run(["lpr", path])

        elif system == "Linux":
            subprocess.run(["lpr", path])

        else:
            raise NotImplementedError(f"Printing not supported on: {system}")
    except Exception as e:
        print(f"Error printing file: {e}")
        return
    

# Load sorting dialog
def loadSortingDialog():
    toggleDialog("folder_management_dialog")

    # Create folder options
    

    # Set details
    selPDFLbl = globals.transpiler.root.getChildrenBySelector(["lbl", "selected_pdf_detail"])[0]
    selFldrLbl = globals.transpiler.root.getChildrenBySelector(["lbl", "selected_folder_detail"])[0]
    selPDFLbl.widget.setText(f"{globals.selectedPDF.split('/')[-1] if globals.selectedPDF else 'Geen PDF geselecteerd!'}")
    selFldrLbl.widget.setText(f"{globals.selectedFolder.split('/')[-1] if globals.selectedFolder else 'Geen map geselecteerd!'}")