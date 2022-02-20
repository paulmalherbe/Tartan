#!/usr/bin/env python
import getopt, os, pathlib, shutil, subprocess, sys
from zipfile import ZipFile

# Generate Tartan Executable
def doFind(name=None, path="C:\\"):
    found = None
    for ddd in ("Program Files", "Program Files (x86)"):
        temp = os.path.join(path, ddd)
        for root, dirs, files in os.walk(temp):
            for fle in files:
                if fle.lower() == name.lower():
                    found = os.path.join(root, name)
                    break
        if found:
            break
    return found

def doUpgrade():
    for mod in [
            "pip",
            "beepy",
            "docutils",
            "fpdf",
            "importlib_metadata",
            "markdown",
            "ofxtools",
            "openpyxl",
            "pillow",
            "progress",
            "psycopg2",
            "pyaes",
            "pycryptodome",
            "pyexcel-ods",
            "pyexcel-xls",
            "pygal",
            "pymupdf",
            "pysmb",
            "pywin32",
            "reportlab",
            "requests",
            "send2trash",
            "svglib",
            "tkcolorpicker",
            "tkinterhtml",
            "pyinstaller==4.5.1"]:
        try:
            os.system("pip -q install %s --upgrade" % mod)
        except:
            pass

HOM = str(pathlib.Path.home())
if "WINEPREFIX" in os.environ:
    MAP = "x:"
else:
    MAP = "\\\\192.168.0.1\\paul"
PFX = None                                      # Windows version
DPT = os.path.join("c:\\", "Tartan", "prg")     # Directory for pyinstaller exe
EXE = os.path.join("%s\\" % MAP, "TartanExe")   # Destination of installer
SRC = os.path.join("%s\\" % MAP, "TartanSve")   # Repository of tartan.zip
TMP = os.path.join("%s\\" % HOM, "Temp")        # Working Directory
UPG = False                                     # Upgrade python modules
opts, args = getopt.getopt(sys.argv[1:], "a:d:e:hs:t:u")
for o, v in opts:
    if o == "-a":
        PFX = v
    elif o == "-d":
        DPT = v
    elif o == "-e":
        EXE = v
    elif o == "-h":
        print("""
Usage: python mkwins.py [options]

    -a Architecture as in 7, 8, 32 and 64
    -d The Installed Path e.g. c:\Tartan\prg
    -e The Destination Path e.g. x:\TartanExe
    -s The Source path e.g. x:\TartanSve
    -t Temporary Work Directory e.g. x:\Temp
    -u Upgrade python modules
""")
        sys.exit()
    elif o == "-s":
        SRC = v
    elif o == "-t":
        TMP = v
    elif o == "-u":
        UPG = True
# Test Architecture
if PFX is None:
    if "WINEPREFIX" in os.environ:
        PFX = os.environ["WINEPREFIX"].split("wine")[1]
    else:
        PFX = input("Archtecture: ")
# Set default variables
ISC = doFind("iscc.exe")
ISS = "tartan.iss"
fle = open(os.path.join(EXE, "current"), "r")
VER = fle.read().strip()
fle.close()
# Open the log file
out = open("%s\\log" % HOM, "w")
# Upgrade
if UPG:
    doUpgrade()
# Delete installation directories
shutil.rmtree(DPT, ignore_errors=True)
shutil.rmtree(TMP, ignore_errors=True)
# Create new installation directories
os.makedirs(TMP)
os.chmod(HOM, 0o777)
for pth in ("fnt", "thm", "uty"):
    os.makedirs(os.path.join(DPT, pth))
# Enter source directory
os.chdir(TMP)
# Unzip sources
with ZipFile(os.path.join(SRC, "tartan-6.zip"), "r") as zipObj:
   zipObj.extractall()
# Generate pygal css directory
try:
    import pygal
    pth = os.path.dirname(pygal.__file__)
    shutil.copytree(os.path.join(pth, "css"), "pygal/css")
except:
    print("Missing pygal module")
    sys.exit()
# Run pyinstaller
os.chdir(os.path.join(TMP, "tartan"))
#shutil.copy(SPC, ".")
subprocess.call(["pyinstaller", "windows.spec"], stdout=out, stderr=out)
# Copy files to DPT
shutil.copy("tartan.ico", DPT)
shutil.copytree(os.path.join("dist", "ms0000"), DPT, dirs_exist_ok=True)
# Create installers and Copy installers to EXE
if "WINEPREFIX" in os.environ:
    if PFX == "7":
        shutil.copy("ucrtbase.7", os.path.join(DPT, "ucrtbase.dll"))
    elif PFX == "8":
        shutil.copy("ucrtbase.8", os.path.join(DPT, "ucrtbase.dll"))
subprocess.call([ISC, ISS], stdout=out, stderr=out)
shutil.copy(os.path.join("Output", "Tartan.exe"),
    os.path.join(EXE, "tartan-6-%s.exe" % PFX))
os.chdir(HOM)
shutil.rmtree(TMP)
shutil.rmtree(DPT)
out.close()
