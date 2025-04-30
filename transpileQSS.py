from RuleSet.rulesets import psml_widgets
import globals
import re

def loadStyleSheet(filePath, app, export=False) -> None:
    if filePath is None:
        return;

    if not "styling/" in filePath:
        filePath = "styling/" + filePath

    with open(filePath, "r") as file:
        style = file.read().lower()


    # Set screen sizing in style
    screen = app.primaryScreen()
    screenGeometry = screen.availableGeometry()
    screenWidth = screenGeometry.width()
    screenHeight = screenGeometry.height()

    style = re.sub(r"vh", str(screenHeight), style)
    style = re.sub(r"vw", str(screenWidth), style)
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


    # Set positions
    if not globals.transpiler is None:
        pattern = r'(?P<selector>\w+(?:[#.][\w-]+)?)\s*\{[^}]*?position:\s*\((?P<position>[\d\s,]+)\);'
        matches = re.finditer(pattern, style)
        for match in matches:
            selector = match.group('selector')
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
        matches = re.finditer(pattern, style)
        for match in matches:
            selector = match.group('selector')
            size = match.group('size').split(',')
            w, h = int(size[0]), int(size[1])
            splitter = "." if "." in selector else "#"
            elements = globals.transpiler.root.getChildrenBySelector(selector.split(splitter)[:2])
            for element in elements:
                if element is not None:
                    element.widget.setFixedWidth(w)
                    element.widget.setFixedHeight(h)
                    if export: print(f"        {f"{element.parent.tag}_" if element.parent else ""}{element.tag}_{element.uuid}.setFixedHeight({h})")
                    if export: print(f"        {f"{element.parent.tag}_" if element.parent else ""}{element.tag}_{element.uuid}.setFixedWidth({w})")
            style = style.replace(f"size: ({w}, {h});", "")


    # Use PSML Element names
    for element, widget in psml_widgets.items():
        pattern = rf"(?m)^\s*{element}\b"
        if isinstance(widget, list):
            for w in widget:
                style = re.sub(pattern, w.__name__, style)
        else:
            style = re.sub(pattern, widget.__name__, style)
    style = style.replace("PDFViewer", "QWidget")


    # Make classes work
    classes = re.findall(r"\.(\w+)\s*{", style)
    for class_name in classes:
        style = style.replace(f".{class_name}", f"[class='{class_name}']")

    if export: print(style)

    return style