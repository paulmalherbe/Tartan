#!/usr/bin/env python
import getopt, glob, os, pathlib, shutil, subprocess, sys
from zipfile import ZipFile

"""
Use this module to create a pyinstaller executable for windows
"""
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
    print("Upgrading python modules")
    sys.path.insert(0, os.path.join(TMP, "tartan"))
    from tartanWork import pymoda, pymodb
    mods = ["pip", "docutils", "pyinstaller"]
    for mod in pymoda + pymodb:
        if len(mod) == 4 and mod[3] != "win32":
            continue
        mods.append(mod[1])
    for mod in mods:
        try:
            os.system("python -m pip -q install %s --user "\
                "--no-warn-script-location --upgrade" % mod)
            print("Upgraded", mod)
        except Exception as err:
            print(err)

HOM = str(pathlib.Path.home())
if "WINEPREFIX" in os.environ:
    MAP = "x:"
else:
    MAP = "\\\\home\\paul"
if sys.maxsize > 2**32:
    PFX = "64"
else:
    PFX = "32"
DPT = os.path.join("c:\\", "Tartan", "prg")     # Directory for pyinstaller exe
EXE = os.path.join("%s\\" % MAP, "TartanExe")   # Destination of installer
if "WINEPREFIX" in os.environ:
    SRC = os.path.join("%s\\" % MAP, "TartanSve")   # Repository of tartan.zip
else:
    SRC = HOM
TMP = os.path.join("%s\\" % HOM, "Temp")        # Working Directory
onefle = False                                  # Generate a single file
UPG = False                                     # Upgrade python modules
opts, args = getopt.getopt(sys.argv[1:], "a:d:e:hos:t:u")
for o, v in opts:
    if o == "-a":
        PFX = v
    elif o == "-d":
        DPT = v
    elif o == "-e":
        EXE = v
    elif o == "-h":
        print("""
Usage: python mkwindows.py [options]

    -a Architecture as in 7, 8, 32 and 64
    -d The Installed Path e.g. c:\Tartan\prg
    -e The Destination Path e.g. x:\TartanExe
    -h Print this Usage
    -o Generate Onefile
    -s The Source path e.g. x:\TartanSve
    -t Temporary Work Directory e.g. x:\Temp
    -u Upgrade python modules
""")
        sys.exit()
    elif o == "-o":
        onefle = True
    elif o == "-s":
        SRC = v
    elif o == "-t":
        TMP = v
    elif o == "-u":
        UPG = True
# Set default variables
ISC = doFind("iscc.exe")
ISS = "tartan.iss"
# Open the log file
out = open("%s\\log" % HOM, "w")
# Delete installation directories
shutil.rmtree(DPT, ignore_errors=True)
shutil.rmtree(TMP, ignore_errors=True)
# Create new installation directories
os.makedirs(TMP)
os.chmod(HOM, 0o777)
for pth in ("fnt", "thm", "uty"):
    os.makedirs(os.path.join(DPT, pth))
# Enter TMP directory
os.chdir(TMP)
# Unzip sources
with ZipFile(os.path.join(SRC, "tartan-6.zip"), "r") as zipObj:
   zipObj.extractall()
# Create tarimp module for pyinstaller
ofl = open("%s\\tartan\\tarimp.py" % TMP, "w")
ofl.write("# Tartan Modules to Include with Pyinstaller Exe\n")
ofl.write("import sys\n")
for fle in glob.iglob("tartan\\*.py"):
    if fle.count("__pycache__"):
        continue
    ofl.write("import %s\n" % os.path.basename(fle).replace(".py", ""))
for fle in glob.iglob("tartan\\???\\*.py"):
    if fle.count("__pycache__"):
        continue
    imp = os.path.basename(os.path.dirname(fle))
    imp = "%s.%s" % (imp, os.path.basename(fle).replace(".py", ""))
    ofl.write("import %s\n" % imp)
ofl.close()
# Generate pygal css directory
try:
    import pygal
    pth = os.path.dirname(pygal.__file__)
    shutil.copytree(os.path.join(pth, "css"), "pygal/css")
except:
    print("Missing pygal module")
    sys.exit()
# Upgrade
if UPG:
    doUpgrade()
# Run pyinstaller
os.chdir(os.path.join(TMP, "tartan"))
cmd = ["python", "-m", "PyInstaller"]
if onefle:
    cmd.append("onefle.spec")
else:
    cmd.append("onedir.spec")
subprocess.call(cmd, stdout=out, stderr=out)
# Copy files to DPT
shutil.copy("tartan.ico", DPT)
if onefle:
    shutil.copy(os.path.join("dist", "ms0000.exe"), DPT)
else:
    shutil.copytree(os.path.join("dist", "ms0000"), DPT, dirs_exist_ok=True)
# Create installers and Copy installers to EXE
if "WINEPREFIX" in os.environ:
    if PFX == "7":
        shutil.copy("ucrtbase.7", os.path.join(DPT, "ucrtbase.dll"))
    elif PFX == "8":
        shutil.copy("ucrtbase.8", os.path.join(DPT, "ucrtbase.dll"))
subprocess.call([ISC, ISS], stdout=out, stderr=out)
if "WINEPREFIX" in os.environ:
    shutil.copy(os.path.join("Output", "Tartan.exe"),
        os.path.join(EXE, "tartan-6-%s.exe" % PFX))
else:
    shutil.copy(os.path.join("Output", "Tartan.exe"),
        os.path.join(HOM, "tartan-6-%s.exe" % PFX))
os.chdir(HOM)
shutil.rmtree(TMP)
shutil.rmtree(DPT)
out.close()
