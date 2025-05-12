from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy, QDialog
from PySide6.QtCore import QTimer, Qt
from software_actions.button_actions import *
from RuleSet.rulesets import psml_widgets
import xml.etree.ElementTree as ET, uuid, globals, threading



class PSMLElement:
    tag = None
    parent = None
    attributes = None
    children = None
    content = None
    widget = None
    uuid = None

    def __init__(self, tag, parent=None, attributes=None, children=None, content=None) -> None:
        self.tag = tag
        self.parent = parent
        self.attributes = attributes if attributes else {}
        self.children = children if children else []
        self.content = content if content else ""
        self.uuid = str(uuid.uuid4()).replace("-", "_")


    def __str__(self) -> str:
        selector = f"{self.tag}{f"#{self.attributes.get('id')}" if self.attributes.get('id') else ''}{f".{self.attributes.get('class')}" if self.attributes.get('class') else ''}"
        return f"{selector}"
    
    def printDebug(self) -> str:
        selector = self.__str__()
        return f"{str(type(self.widget)).split('.')[-1].replace("'>", "") if self.widget else ""} | {selector}{[f"{attr}:{val}" for attr, val in self.attributes.items() if attr not in ["class", "id"]]}"


    def getChildrenBySelector(self, selector=None, parent=None, indent=0) -> list:
        if parent is None:
            parent = self
        
        matching = []

        for child in parent.children:
            if selector and hasattr(child, "widget") and hasattr(child.widget, "objectName"):
                if child.tag == selector[0] and (child.widget.objectName() == selector[1] or child.attributes.get("class") == selector[1]):
                    matching.append(child)
            else: matching.append(child)
            
            matching.extend(self.getChildrenBySelector(selector, child, indent + 1))
        if indent == 0:
            for dialog in globals.transpiler.dialogs:
                if selector and hasattr(dialog, "widget") and hasattr(dialog.widget, "objectName"):
                    if dialog.tag == selector[0] and (dialog.widget.objectName() == selector[1] or dialog.attributes.get("class") == selector[1]):
                        matching.append(dialog)
                else: matching.append(dialog)

                matching.extend(self.getChildrenBySelector(selector, dialog, indent + 1))
        return matching


    def load(self, parent=None) -> None:
        if not self.tag in psml_widgets.keys(): return

        if self.tag == "root":
            self.widget = QVBoxLayout()
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = QVBoxLayout()")

            for child in self.children:
                childElem = child.load(self)
                child_widget = childElem.widget
                if child_widget is not None:
                    if childElem.parent:
                        self.widget.addWidget(child_widget)
                    if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.addWidget({f"{self.tag}"}_{child.tag}_{child.uuid})")

            for dialog in globals.transpiler.dialogs:
                self.children.remove(dialog)

            self.setAttributes()
            if globals.export: print(f"        self.setLayout({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")
            return self

        pyside_widget = psml_widgets.get(self.tag)
        if pyside_widget is None:
            raise ValueError(f"Unknown widget type: {self.tag}")
        self.widget = pyside_widget()
        if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = {type(self.widget).__name__}()")
        
        self.manageContainers()
            
        if self.content != "" and not self.content is None:
            if isinstance(self.widget, (QLabel, QPushButton)):
                self.widget.setText(self.content)
                if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setText('{self.content}')")
        
        self.setParent(parent)
        self.setAttributes()
        self.setSizePolicy()

        for child in self.children:
            childElem = child.load(self)

        if globals.export: print("")
        return self


    def manageContainers(self):
        if self.tag in ["node", "nd", "container", "cont", "box", "dialog", "popup"]:
            layout = None
            for key, value in self.attributes.items():
                if "horizontal" in key.lower() and not "f" in value.lower():
                    layout = QHBoxLayout()
                else:
                    layout = QVBoxLayout()


                if "scrollable" in key.lower() and not "f" in value.lower():
                    self.container = self.widget
                    self.widget = QScrollArea()
                    self.widget.setWidgetResizable(True)
                    self.widget.setWidget(self.container)
                    self.container.setLayout(layout)
                
                    if globals.export:
                        print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = QScrollArea()")
                        print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setWidgetResizable(True)")
                        print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.container)")
                        print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.container.setLayout({type(layout).__name__}())")
                    if not self.tag in ["dialog", "popup"]:
                        self.container.layout().setAlignment(Qt.AlignLeft | Qt.AlignTop)
                        if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.layout().setAlignment(Qt.AlignLeft | Qt.AlignTop)")
                    else:
                        self.container.layout().setAlignment(Qt.AlignCenter)
                        if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.layout().setAlignment(Qt.AlignCenter)")
                    return
            self.widget.setLayout(layout)
            self.layout = layout
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setLayout({type(layout).__name__}())")
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.layout().setAlignment(Qt.AlignLeft | Qt.AlignTop)")
        else:
            self.layout = None


    def setAttributes(self):
        self.widget.setObjectName("")
        for attr, value in self.attributes.items():
            if "id" in attr:
                self.widget.setObjectName(value)
                if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setObjectName('{value}')")

            elif "onclick" in attr:
                if isinstance(self.widget, QPushButton):
                    self.widget.clicked.connect(lambda: eval(value))
                    if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.clicked.connect(lambda: {value.replace("'", '"')})")

                else:
                    raise ValueError(f"onclick attribute is only valid for QPushButton widgets | Not for {self.tag}")
            
            elif "type" in attr:
                if "loader" in self.tag or "embed" in self.tag:
                    if "pdf" in value.lower():
                        self.doc = None
                        self.currentPage = 0
                        if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = None")
                        if "src" in self.attributes.keys():
                            self.src = self.attributes.get("src")
                            pageNum = 0
                            if ".pdf:" in self.src:
                                pageNum = int(self.src.split(".pdf:")[-1])
                                self.src = self.src.split(".pdf:")[0] + ".pdf"
                            QTimer.singleShot(0, lambda: loadPDFPage(self.attributes.get("id"), self.src, pageNum))
                    else:
                        raise ValueError(f"Unknown type for {self.tag} widget: {value}")
            elif "shown" in attr:
                if "dialog" in self.tag or "popup" in self.tag:
                    if "t" in value.lower(): self.widget.exec()
            elif "title" in attr:
                if "dialog" in self.tag or "popup" in self.tag:
                    self.widget.setWindowTitle(value)
                    if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setWindowTitle('{value}')")
            self.widget.setProperty(attr, value)
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setProperty('{attr}', '{value.replace("'", '"')}')")


    def setParent(self, parent):
        if not parent: return
        if self.tag in ["dialog", "popup"]:
            self.parent = None
            globals.transpiler.dialogs.append(self)
            return

        if "scrollable" in parent.attributes.keys() and not "f" in parent.attributes["scrollable"].lower():
            parent.children.append(self)
            parent.container.layout().addWidget(self.widget)
            if globals.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.container.addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

        elif hasattr(parent, 'layout') and parent.layout is not None:
            parent.layout.addWidget(self.widget)
            if globals.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.layout().addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

        elif hasattr(parent.widget, 'addWidget'):
            parent.widget.addWidget(self.widget)
            if globals.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

        else:
            raise ValueError(f"Parent {parent.tag} cannot contain child widgets")


    def setSizePolicy(self):
        if "expand" in self.attributes or "prefer" in self.attributes:
            width = None
            height = None
            if "expand" in self.attributes:
                value = self.attributes["expand"]
                if "false" in value.lower(): return

                width = QSizePolicy.Expanding if "w" in value else QSizePolicy.Fixed
                height = QSizePolicy.Expanding if "h" in value else QSizePolicy.Fixed
            if "prefer" in self.attributes:
                value = self.attributes["prefer"]
                if "false" in value.lower(): return

                width = QSizePolicy.Preferred if "w" in value else QSizePolicy.Fixed
                height = QSizePolicy.Preferred if "h" in value else QSizePolicy.Fixed
            self.widget.setSizePolicy(width, height)
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setSizePolicy(QSize{width}, QSize{height})")
        else:
            self.widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if globals.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)")


    def setPosition(self, x, y):
        if hasattr(self.widget, 'setGeometry'):
            self.parent.widget.layout().removeWidget(self.widget)
            self.widget.setGeometry(x, y, self.widget.width(), self.widget.height())
            if globals.export:
                print(f"        {f"{self.parent.parent.tag}_" if self.parent.parent else ""}{self.parent.tag}_{self.parent.uuid}.layout().removeWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")
                print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setGeometry({x}, {y}, {self.widget.width()}, {self.widget.height()})")
        else:
            raise ValueError(f"setPosition is not valid for {self.tag} widgets")


    def deleteChildren(self):
        if len(self.children) > 0:
            for child in self.children:
                child.widget.setFixedHeight(0)
                child.widget.deleteLater()
                child.widget.close()
            self.children.clear()



class Transpiler:
    root: PSMLElement = None
    ids = []
    dialogs = []

    def generatePSElements(self, et_element, parent: None | PSMLElement = None) -> PSMLElement:
        if not et_element.tag in psml_widgets.keys():
            raise ValueError(f"Unknown element type: {et_element.tag}")
        if "id" in et_element.attrib:
            id = et_element.attrib["id"]
            if id in self.ids:
                raise ValueError(f"Duplicate ID found: {id}")
            self.ids.append(id)
        data = {
            "tag": et_element.tag,
            "parent": parent,
            "attributes": et_element.attrib,
            "content": et_element.text or ""
        }
        elem = self.createElement(data)
        for child in et_element:
            child_elem = self.generatePSElements(child, parent=elem)
            if not child_elem in elem.children:
                elem.children.append(child_elem)
        if elem.tag == "root":
            self.root = elem
        return elem


    def readPSML(self, filename) -> str:
        if not "templates/" in filename:
            filename = "templates/" + filename
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
        return "Unable to read file!"


    def getStringStructure(self, containerElement, indent=0) -> str:
        if containerElement is None:
            raise ValueError(f"{containerElement.tag} element is not set.")
        result = f"{"  " * indent} => {containerElement.printDebug()}\n"
        for child in containerElement.children:
            result += self.getStringStructure(child, indent + 1)
        else: result.rstrip("\n")
        if indent == 0:
            result += "\n"
            for dialog in self.dialogs:
                result += f" => {dialog.printDebug()}\n"
                for child in dialog.children:
                    result += self.getStringStructure(child, 1)
                result += "\n"
        return result


    def createElement(self, data):
        elem = None
        try:
            elem = PSMLElement(
                tag=data.get("tag"),
                parent=data.get("parent"),
                attributes=data.get("attributes"),
                content=data.get("content"),
            )
        except Exception as e:
            print(f"Unable to create element: {e}")
        return elem
    

    def run(self, filename: str=None, pageText=None):
        if filename is None and pageText is None:
            raise ValueError("Either filename or pageText must be provided.")
        mainPage: str = self.readPSML(filename) if filename else pageText
        try:
            root_et = ET.fromstring(mainPage)
            if root_et.tag != "root":
                page: str = '<root>' + mainPage + "</root>"
                root_et = ET.fromstring(page)

        except ET.ParseError:
            page: str = '<root>' + mainPage + "</root>"
            root_et = ET.fromstring(page)
        self.root = root_et
        
        self.generatePSElements(self.root)