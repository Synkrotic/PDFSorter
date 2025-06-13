from PySide6.QtWidgets import QApplication
import sys, configparser

app = QApplication(sys.argv)
transpiler = None
window = None

config = configparser.ConfigParser()
config.read("config.cfg")


# Config
export = config.getboolean("Settings", "export")
fullscreen = config.getboolean("Settings", "fullscreen")
allowSubFolders = config.getboolean("Settings", "allowSubFolders")

selectedPDF = config.get("Settings", "selectedPDF")
selectedFolder = config.get("Settings", "selectedFolder")

inputDirectory = config.get("Settings", "inputDirectory")
outputDirectory = config.get("Settings", "outputDirectory")

def reload():
  global export, fullscreen, allowSubFolders, selectedPDF, selectedFolder, inputDirectory, outputDirectory
  export = config.getboolean("Settings", "export")
  fullscreen = config.getboolean("Settings", "fullscreen")
  allowSubFolders = config.getboolean("Settings", "allowSubFolders")

  selectedPDF = config.get("Settings", "selectedPDF")
  selectedFolder = config.get("Settings", "selectedFolder")

  inputDirectory = config.get("Settings", "inputDirectory")
  outputDirectory = config.get("Settings", "outputDirectory")