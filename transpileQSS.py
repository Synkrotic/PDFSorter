from PySide6.QtCore import Qt
from RuleSet.rulesets import psml_widgets
import globals
import re

def loadStyleSheet(filePath) -> None:
    if filePath is None:
        return;

    if not "styling/" in filePath:
        filePath = "styling/" + filePath

    with open(filePath, "r") as file:
        style = file.read()


    # Set screen sizing in style
    screen = globals.app.primaryScreen()
    screenGeometry = screen.geometry()
    screenGeometryAvai = screen.availableGeometry()
    screenWidth = screenGeometryAvai.width()
    screenHeight = screenGeometryAvai.height()
    taskbarHeight = screenGeometry.height() - screenHeight

    style = re.sub(r"vh", str(screenHeight), style)
    style = re.sub(r"vw", str(screenWidth), style)
    style = re.sub(r"tbh", str(taskbarHeight), style)
    style = re.sub(r"calc\((.*?)\)", lambda m: str(round(eval(m.group(1)))), style)


    # Set colour vars
    lines = style.splitlines()
    cleaned_lines = []
    colour_vars = {} 
    for line in lines:
        if line.startswith("--"):
            var_name = line.split(":")[0].strip()
            var_value = line.split(":")[1].strip().split(";")[0]
            colour_vars[var_name] = var_value
        else:
            cleaned_lines.append(line)
    style = "\n".join(cleaned_lines)
    for var_name, var_value in colour_vars.items():
        style = style.replace(var_name, var_value)


    blocks = {}
    pattern = re.compile(r'([^{\s]+)\s*\{([^}]+)\}', re.MULTILINE)
    for selector, body in pattern.findall(style):
        props = body.strip().split(';')
        props = [p.strip() for p in props if p.strip()]
        blocks[selector] = props

    updated_css = ""
    for selector, props in blocks.items():
        new_props = []
        for prop in props:
            match = re.match(r'include\(([^)]+)\)', prop)
            if match:
                included_selector = match.group(1)
                included_props = blocks.get(included_selector, [])
                new_props.extend(included_props)
            else:
                new_props.append(prop)
        updated_css += f"{selector} {{\n"
        for p in new_props:
            updated_css += f"    {p};\n"
        updated_css += "}\n"
    style = updated_css


    # Set positions
    if not globals.transpiler is None:
        tempStyle = re.sub(r"\[[^\[\]]+?\]", "", style)
        pattern = r'(?P<selector>\w+(?:[#.][\w-]+)?)\s*\{[^}]*?position:\s*\((?P<position>[\d\s,]+)\);'
        matches = re.finditer(pattern, tempStyle)
        for match in matches:
            selector = match.group('selector')
            selector = re.sub(r"\[[^\[\]]+?\]", "", selector)
            position = match.group('position').split(',')
            x, y = int(position[0]), int(position[1])
            splitter = "." if "." in selector else "#"
            elements = globals.transpiler.root.getChildrenBySelector(selector.split(splitter)[:2])
            for element in elements:
                if element is not None:
                    element.setPosition(x, y)
            style = style.replace(f"position: ({x}, {y});", "")


        # Set size
        pattern = r'(?P<selector>\w+(?:[#.][\w-]+)?)\s*\{[^}]*?size:\s*\((?P<size>[\d\s,]+)\);'
        matches = re.finditer(pattern, tempStyle)
        for match in matches:
            selector = match.group('selector')
            size = match.group('size').split(',')
            w, h = int(size[0]), int(size[1])
            splitter = "." if "." in selector else "#"
            elements = globals.transpiler.root.getChildrenBySelector(selector.split(splitter)[:2])
            for element in elements:
                if element is not None:
                    element.widget.setFixedSize(w, h)
                    if globals.export: print(f"        {f"{element.parent.tag}_" if element.parent else ""}{element.tag}_{element.uuid}.setFixedHeight({h})")
                    if globals.export: print(f"        {f"{element.parent.tag}_" if element.parent else ""}{element.tag}_{element.uuid}.setFixedWidth({w})")
            style = style.replace(f"size: ({w}, {h});", "")
        

        # Change alignment
        pattern = r'(?P<selector>\w+(?:[#.][\w-]+)?)\s*\{[^}]*?alignment:\s*(?P<align>[\w\s,]+);'
        matches = re.finditer(pattern, tempStyle)
        for match in matches:
            selector = match.group('selector')
            align = match.group('align').split(' ')
            align = [a.strip() for a in align if a.strip() and a in ["left", "right", "top", "bottom"]]
            alignment = []
            for a in align:
                match a:
                    case "top": alignment.append("Qt.AlignTop")
                    case "bottom": alignment.append("Qt.AlignBottom")
                    case "center": alignment.append("Qt.AlignCenter")
                    case "left": alignment.append("Qt.AlignLeft")
                    case "right": alignment.append("Qt.AlignRight")
            splitter = "." if "." in selector else "#"
            elements = globals.transpiler.root.getChildrenBySelector(selector.split(splitter)[:2])
            for element in elements:
                if element is not None:
                    element.widget.layout().setAlignment(eval(" | ".join(alignment)))
                    if globals.export: print(f"        {f"{element.parent.tag}_" if element.parent else ""}{element.tag}_{element.uuid}.setAlignment({" | ".join(alignment)})")


    # Use PSML Element names
    for element, widget in psml_widgets.items():
        pattern = rf"(?m)^\s*{re.escape(element)}\b"
        if isinstance(widget, list):
            for w in widget:
                style = re.sub(pattern, w.__name__, style)
        else:
            style = re.sub(pattern, widget.__name__, style)

    # Make classes work
    classes = re.findall(r"\.(\w+)\s*{", style)
    for class_name in classes:
        style = style.replace(f".{class_name}", f"[class='{class_name}']")

    if globals.export: print(style)

    return style
