from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
from PySide6.QtCore import QTimer, Qt
from software_actions.button_actions import *
from RuleSet.rulesets import psml_widgets
import xml.etree.ElementTree as ET
import uuid



class PSMLElement:
    tag = None
    parent = None
    attributes = None
    children = None
    content = None
    widget = None
    uuid = None
    export = False

    def __init__(self, tag, parent=None, attributes=None, children=None, content=None, export=False) -> None:
        self.tag = tag
        self.parent = parent
        self.attributes = attributes if attributes else {}
        self.children = children if children else []
        self.content = content if content else ""
        self.uuid = str(uuid.uuid4()).replace("-", "_")
        self.export = export


    def __str__(self) -> str:
        parent_tag = self.parent.tag if self.parent else "None"
        children_tags = [child.tag for child in self.children]
        return f"Tag: {self.tag}\nParent: {parent_tag}\nChildren: {children_tags}\nContent: {self.content}\nAttributes: {self.attributes}\n"


    def getChildrenBySelector(self, selector, parent=None) -> list:
        if parent is None:
            parent = self
        
        matching = []

        for child in parent.children:
            if child.tag == selector[0] and (child.widget.objectName() == selector[1] or child.attributes.get("class") == selector[1]):
                matching.append(child)
            
            matching.extend(self.getChildrenBySelector(selector, child))
        return matching


    def load(self, parent=None) -> None:
        if not self.tag in psml_widgets.keys(): return

        if self.tag == "root":
            self.widget = QVBoxLayout()
            if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = QVBoxLayout()")

            for child in self.children:
                child_widget = child.load(self)
                if child_widget is not None:
                    self.widget.addWidget(child_widget)
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.addWidget({f"{self.tag}"}_{child.tag}_{child.uuid})")

            self.setAttributes()
            if self.export: print(f"        self.setLayout({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")
            return self.widget

        pyside_widget = psml_widgets.get(self.tag)
        if pyside_widget is None:
            raise ValueError(f"Unknown widget type: {self.tag}")
        self.widget = pyside_widget()
        if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = {type(self.widget).__name__}()")

        self.manageContainers()
            
        if self.content != "" and not self.content is None:
            if isinstance(self.widget, (QLabel, QPushButton)):
                self.widget.setText(self.content)
                if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setText('{self.content}')")
        
        self.setParent(parent)
        self.setAttributes()
        self.setSizePolicy()

        for child in self.children:
            child_widget = child.load(self)

        if self.export: print("")
        return self.widget


    def manageContainers(self):
        if self.tag in ["node", "nd", "container", "cont", "box"]:
            for key, value in self.attributes.items():
                if "horizontal" in key.lower() and not "f" in value.lower():
                    layout = QHBoxLayout()
                elif isinstance(self.widget, QWidget):
                    layout = QVBoxLayout()

                if "scrollable" in key.lower() and not "f" in value.lower():
                    self.container = self.widget
                    self.widget = QScrollArea()
                    self.widget.setWidgetResizable(True)
                    self.widget.setWidget(self.container)
                    self.container.setLayout(layout)
                    self.container.layout().setAlignment(Qt.AlignCenter)
                
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.layout().setAlignment(Qt.AlignCenter)")
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = QScrollArea()")
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setWidgetResizable(True)")
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.container)")
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.container.setLayout({type(layout).__name__}())")
                    return
                
            self.widget.setLayout(layout)
            if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setLayout({type(layout).__name__}())")
            self.layout = layout
        else:
            self.layout = None


    def setAttributes(self):
        for attr, value in self.attributes.items():
            if "id" in attr:
                self.widget.setObjectName(value)
                if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setObjectName('{value}')")

            elif "onclick" in attr:
                if isinstance(self.widget, QPushButton):
                    self.widget.clicked.connect(lambda: eval(value))
                    if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.clicked.connect(lambda: {value.replace("'", '"')})")

                else:
                    raise ValueError(f"onclick attribute is only valid for QPushButton widgets | Not for {self.tag}")
            
            elif "type" in attr:
                if "loader" in self.tag or "embed" in self.tag:
                    if "pdf" in value.lower():
                        self.doc = None
                        self.currentPage = 0
                        if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid} = None")
                        if "src" in self.attributes.keys():
                            self.src = self.attributes.get("src")
                            pageNum = 0
                            if ".pdf:" in self.src:
                                pageNum = int(self.src.split(".pdf:")[-1])
                                self.src = self.src.split(".pdf:")[0] + ".pdf"
                            
                            QTimer.singleShot(0, lambda: loadPDFPage(self.attributes.get("id"), self.src, pageNum))
                    else:
                        raise ValueError(f"Unknown type for {self.tag} widget: {value}")
            self.widget.setProperty(attr, value)
            if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setProperty('{attr}', '{value.replace("'", '"')}')")


    def setParent(self, parent):
        if not parent: return

        if "scrollable" in parent.attributes.keys() and not "f" in parent.attributes["scrollable"].lower():
            parent.container.layout().addWidget(self.widget)
            if self.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.container.addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

        elif hasattr(parent, 'layout') and parent.layout is not None:
            parent.layout.addWidget(self.widget)
            if self.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.layout().addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

        elif hasattr(parent.widget, 'addWidget'):
            parent.widget.addWidget(self.widget)
            if self.export: print(f"        {f"{parent.parent.tag}_" if parent.parent else ""}{parent.tag}_{parent.uuid}.addWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")

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
            if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setSizePolicy(QSize{width}, QSize{height})")
        else:
            self.widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if self.export: print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)")


    def setPosition(self, x, y):
        if hasattr(self.widget, 'setGeometry'):
            self.parent.widget.layout().removeWidget(self.widget)
            self.widget.setGeometry(x, y, self.widget.width(), self.widget.height())
            if self.export:
                print(f"        {f"{self.parent.parent.tag}_" if self.parent.parent else ""}{self.parent.tag}_{self.parent.uuid}.layout().removeWidget({f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid})")
                print(f"        {f"{self.parent.tag}_" if self.parent else ""}{self.tag}_{self.uuid}.setGeometry({x}, {y}, {self.widget.width()}, {self.widget.height()})")
        else:
            raise ValueError(f"setPosition is not valid for {self.tag} widgets")




class Transpiler:
    root: PSMLElement = None
    exportLang = False
    ids = []

    def __init__(self, export=False) -> None:
        self.exportLang = export


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
            elem.children.append(child_elem)
        if elem.tag == "root":
            self.root = elem
        return elem


    def readPSML(self, filename) -> str:
        if not "templates/" in filename:
            filename = "templates/" + filename
        with open(filename, 'r') as file:
            return file.read()
        return "Unable to read file!"


    def getStringStructure(self, containerElement, indent=0) -> str:
        if containerElement is None:
            raise ValueError(f"{containerElement.tag} element is not set.")
        result = f"{"  " * indent} => {containerElement.tag} | {containerElement.attributes.get("id") or ""} | {containerElement.attributes.get("class") or ""}\n"
        for child in containerElement.children:
            result += self.getStringStructure(child, indent + 1)
        else: result.rstrip("\n")
        return result


    def createElement(self, data):
        elem = None
        try:
            elem = PSMLElement(
                tag=data.get("tag"),
                parent=data.get("parent"),
                attributes=data.get("attributes"),
                content=data.get("content"),
                export=self.exportLang
            )
        except Exception as e:
            print(f"Unable to create element: {e}")
        
        return elem
    

    def run(self, filename: str=None, pageText=None):
        if filename is None and pageText is None:
            raise ValueError("Either filename or pageText must be provided.")
        mainPage: str = self.readPSML(filename).strip() if filename else pageText.strip()
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
        print(self.getStringStructure(self.root))