import shutil
import time
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QTimer
from transpileQSS import loadStyleSheet
from functools import partial
import pyautogui as pag
import pymupdf, globals, os, platform, subprocess, threading



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
        QTimer.singleShot(0, lambda: dialog.widget.open())





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

    def load():
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
    thread = threading.Thread(target=load)
    thread.start()

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
        pdfDoc.close()

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
                "class": "list_selection_option",
                "expand": "w",
                "id": f"{"selected" if f'{globals.inputDirectory}/{pdf}' == globals.selectedPDF else ""}",
                "onclick": f"setSelectedPDF('{pdf}')",
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

def setSelectedPDF(pdf):
    globals.selectedPDF = pdf
    loadPDF("pdf_viewer", f"{globals.inputDirectory}/{pdf}")

    btn = globals.transpiler.root.getChildrenBySelector(["btn", "choose_pdf_action_btn"])[0]
    btn.attributes["class"] = "action_button"
    btn.widget.setProperty("class", "action_button")
    btn.widget.setStyleSheet(globals.window.style)
    
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
    time.sleep(5)
    pag.hotkey('ctrl', 'p')


# Reset full application
def resetApp():
    globals.selectedPDF = ""
    globals.selectedFolder = ""
    container = globals.transpiler.root.getChildrenBySelector(["nd", "pdf_selections_container"])[0]
    
    if container is None:
        print("PDF selection container not found")
        return
    
    container.deleteChildren()


# Sorting dialog
def sortPDF():
    if globals.selectedPDF == "":
        btn = globals.transpiler.root.getChildrenBySelector(["btn", "choose_pdf_action_btn"])[0]
        btn.attributes["class"] = "action_btn_red"
        btn.widget.setProperty("class", "action_btn_red")
        btn.widget.setStyleSheet(globals.window.style)
        return

    pdf = globals.selectedPDF
    folder = globals.selectedFolder
    
    pages = globals.transpiler.root.getChildrenBySelector(["loader", "pdf_page"])
    for page in pages:
        try:
            page.doc.close()
        except Exception as e:
            print(f"Error closing PDF document: {e}")

    try:
       print("Sorting PDF...")
       src = f"{globals.inputDirectory}/{pdf}"
       shutil.move(src, folder)
       resetApp()

    except WindowsError as e:
       resetApp()
       QTimer.singleShot(0, lambda: os.remove(src))
       return

    except Exception as e:
        print(f"Error sorting PDF: {e}")
        return


def setSelectedFolder(folderPath, clickedFolder):
    globals.selectedFolder = folderPath

    if clickedFolder.widget.objectName() == "selected":
        toggleDialog("folder_management_dialog")
        sortPDF()

    folders = globals.transpiler.root.getChildrenBySelector(["btn", "folder_selection_option"])
    for folder in folders:
        if folder.widget.objectName() == "selected":
            folder.widget.setObjectName("")
            folder.widget.setStyleSheet(globals.window.style)
    
    clickedFolder.widget.setObjectName("selected")
    clickedFolder.widget.setStyleSheet(globals.window.style)
    selFldrLbl = globals.transpiler.root.getChildrenBySelector(["lbl", "selected_folder_detail"])[0]
    selFldrLbl.widget.setText(f"{globals.selectedFolder.split('/')[-1] if globals.selectedFolder else 'Geen map geselecteerd!'}")


def loadFolderOptions(wrapper, dir=f"{globals.outputDirectory}"):
    folders = [str(f) for f in os.listdir(dir) if os.path.isdir(os.path.join(dir, f))]
    
    if wrapper is None:
        print("PDF selection wrapper not found")
        return
    
    wrapper.deleteChildren()
    loadSubFolders(dir, folders, wrapper)

def toggleSubFolders(btn):
    btn.widget.setText("⮞" if btn.widget.text() == "⮟" else "⮟")
    container = btn.parent.parent
    subFolderContainer = container.getChildrenBySelector(["nd", "sub_folders_container"])[0]
    if subFolderContainer:
        subFolderContainer.widget.setVisible(not subFolderContainer.widget.isVisible())

def loadSubFolders(path, folders, wrapper):
    for folder in folders:
        containerData = {
            "tag": "cont",
            "parent": wrapper,
            "attributes": {
                "class": "folder_selection_container",
                "expand": "w",
            },
            "content": "",
        }
        container = globals.transpiler.createElement(containerData)
        container.path = path
        container.load(wrapper)
        wrapper.children.append(container)
        if path != globals.outputDirectory:
            container.widget.layout().setContentsMargins((globals.window.screenGeometry.width() // 40), 0, 0, 0)
        else:
            container.widget.layout().setContentsMargins(0, 0, 0, 0)
        container.widget.layout().setSpacing(0)

        btnContainerData = {
            "tag": "container",
            "parent": container,
            "attributes": {
                "class": "folder_selection_btn_container",
                "expand": "w",
                "horizontal": "true",
            },
            "content": "",
        }
        btnContainer = globals.transpiler.createElement(btnContainerData)
        btnContainer.load(container)
        btnContainer.widget.layout().setContentsMargins(0, 0, 0, 0)
        btnContainer.widget.layout().setSpacing(0)
        container.children.append(btnContainer)

        subFolders = []
        if globals.allowSubFolders:
            subFolders = [str(f) for f in os.listdir(f"{path}/{folder}") if os.path.isdir(os.path.join(path, folder, f))]
            if subFolders != []:
                showSubsBtnData = {
                    "tag": "btn",
                    "parent": btnContainer,
                    "attributes": {
                        "class": "folder_show_subs",
                    },
                    "content": "⮞",
                }
                showSubsBtn = globals.transpiler.createElement(showSubsBtnData)
                showSubsBtn.load(btnContainer)
                showSubsBtn.widget.clicked.connect(partial(toggleSubFolders, showSubsBtn))
                btnContainer.children.append(showSubsBtn)

        selBtnData = {
            "tag": "btn",
            "parent": btnContainer,
            "attributes": {
                "class": f"folder_selection_option",
                "id": f"{"selected" if f"{container.path}/{folder}" == globals.selectedFolder else ""}",
                "expand": "w",
            },
            "content": folder,
        }
        selBtn = globals.transpiler.createElement(selBtnData)
        selBtn.load(btnContainer)
        selBtn.widget.clicked.connect(partial(setSelectedFolder, f"{path}/{selBtn.content}", selBtn))
        btnContainer.children.append(selBtn)

        if subFolders != []:
            subFolderContainerData = {
                "tag": "nd",
                "parent": container,
                "attributes": {
                    "class": "sub_folders_container",
                    "expand": "w",
                },
                "content": "",
            }
            subFolderContainer = globals.transpiler.createElement(subFolderContainerData)
            subFolderContainer.load(container)
            subFolderContainer.widget.setVisible(False)
            container.children.append(subFolderContainer)
            container.widget.layout().setContentsMargins(0, 0, 0, 0)
            loadFolderOptions(subFolderContainer, f"{path}/{folder}")

        container.widget.style = globals.window.style
        container.widget.setStyleSheet(globals.window.style)


def loadSortingDialog():
    toggleDialog("folder_management_dialog")

    # Create folder options
    wrapper = globals.transpiler.root.getChildrenBySelector(["nd", "folder_list"])[0]
    loadFolderOptions(wrapper)

    # Set details
    selPDFLbl = globals.transpiler.root.getChildrenBySelector(["lbl", "selected_pdf_detail"])[0]
    selFldrLbl = globals.transpiler.root.getChildrenBySelector(["lbl", "selected_folder_detail"])[0]
    selPDFLbl.widget.setText(f"{globals.selectedPDF.split('/')[-1] if globals.selectedPDF else 'Geen PDF geselecteerd!'}")
    selFldrLbl.widget.setText(f"{globals.selectedFolder.split('/')[-1] if globals.selectedFolder else 'Geen map geselecteerd!'}")


# Create new folder
def createFolder():
    input = globals.transpiler.root.getChildrenBySelector(["input", "new_folder_name"])[0]
    folderName = input.widget.text()
    if folderName == "":
        print("Folder name cannot be empty")
        return
    
    destination = globals.selectedFolder if globals.selectedFolder != "" else globals.outputDirectory
    os.makedirs(f"{destination}/{folderName}", exist_ok=True)

    wrapper = globals.transpiler.root.getChildrenBySelector(["nd", "folder_list"])[0]
    loadFolderOptions(wrapper)






# Config
