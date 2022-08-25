#!/usr/bin/env python
import getopt, glob, os, pathlib, shutil, subprocess, sys
from zipfile import ZipFile

"""
Use this module to create a pyinstaller executable for linux
"""
# Generate Tartan Executable

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
            os.system("pip -q install %s --user "\
                "--no-warn-script-location --upgrade" % mod)
            print("Upgraded", mod)
        except Exception as err:
            print(err)

HOM = str(pathlib.Path.home())
DPT = os.path.join(HOM, "Tartan", "prg")        # Directory for pyinstaller exe
EXE = os.path.join(HOM, "TartanExe")            # Destination of installer
SRC = os.path.join(HOM, "TartanSve")            # Repository of tartan.zip
TMP = os.path.join(HOM, "Temp")                 # Working Directory
onefle = False                                  # Generate a single file
UPG = False                                     # Upgrade python modules
opts, args = getopt.getopt(sys.argv[1:], "a:d:e:fhs:t:u")
for o, v in opts:
    if o == "-a":
        PFX = v
    elif o == "-d":
        DPT = v
    elif o == "-e":
        EXE = v
    elif o == "-f":
        onefle = True
    elif o == "-h":
        print("""
Usage: python mklinux.py [options]

    -d The Installed Path e.g. /home/paul/Tartan\prg
    -e The Destination Path e.g. /home/paul/TartanExe
    -f Generate Onefile
    -s The Source path e.g. /home/paul/TartanSve
    -t Temporary Work Directory e.g. /home/paul/Temp
    -u Upgrade python modules
""")
        sys.exit()
    elif o == "-s":
        SRC = v
    elif o == "-t":
        TMP = v
    elif o == "-u":
        UPG = True
# Set default variables
fle = open(os.path.join(EXE, "current"), "r")
VER = fle.read().strip()
fle.close()
# Open the log file
out = open("%s/log" % HOM, "w")
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
# Create tarimp module for pyinstaller
ofl = open("%s/tartan/tarimp.py" % TMP, "w")
ofl.write("# Tartan Modules to Include with Pyinstaller Exe\n")
ofl.write("import sys\n")
for fle in glob.iglob("tartan/*.py"):
    if fle.count("__pycache__"):
        continue
    ofl.write("import %s\n" % os.path.basename(fle).replace(".py", ""))
for fle in glob.iglob("tartan/???/*.py"):
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
if onefle:
    os.rename("ms0000.fle", "ms0000.spec")
else:
    os.rename("ms0000.dir", "ms0000.spec")
subprocess.call(["pyinstaller", "ms0000.spec"], stdout=out, stderr=out)
# Copy files to DPT
shutil.copy("tartan.ico", DPT)
if onefle:
    shutil.copy(os.path.join("dist", "ms0000"), DPT)
else:
    shutil.copytree(os.path.join("dist", "ms0000"), DPT, dirs_exist_ok=True)
os.chdir(HOM)
# Create tar file
subprocess.call(["zip", "-rq", os.path.join(EXE, "tartan-6-lnx.zip"), "Tartan"])
shutil.rmtree(TMP)
shutil.rmtree(DPT)
out.close()
