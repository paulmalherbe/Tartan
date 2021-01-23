#!/usr/bin/env python

import getopt
import glob
import os
import shutil
import subprocess
import sys
import time

bd = os.path.expanduser("~")  # Base directory
sv = "root@mail"              # ftp login@server
vv = 6                        # Version number
bv = "Tartan-%s" % vv         # Version directory
vd = os.path.join(bd, bv)
if not os.path.isdir(vd):
    print("Invalid Version Directory: %s" % vd)
    sys.exit()
sys.path.append(vd)
from tartanFunctions import findFile, sendMail
from ms0000 import VERSION

def exeCmd(cmd):
    ret = 1
    cnt = 0
    while ret and cnt < 3:
        cnt += 1
        ret = os.system(cmd)
    if ret and ret < 256:
        print("%s Command Failed" % cmd, ret)
        sys.exit()

def addPage(doc, fle, last=False):
    exeCmd("aspell -c %s --lang en_GB" % fle)
    data = open(fle, "r")
    for d in data.readlines():
        doc.write(d)
    if not last:
        doc.write("\n")
        doc.write(".. raw:: pdf\n")
        doc.write("\n")
        doc.write("    PageBreak\n")
        doc.write("\n")
    data.close()

print("Packaging...")
email = False
mkcd = False
pipupd = False
newver = None
publish = False
test = False
verinc = False
windows = False
opts, args = getopt.getopt(sys.argv[1:], "b:cehiptv:w")
for o, v in opts:
    if o == "-h":
        print("Usage: pkgprg [-b base directory] [-c create cd] [-d pipupd] "\
                "[-e email] [-h help] [-i increment] [-p publish] [-t test] "\
                "[-v new version] [-w windows]")
        sys.exit()
    elif o == "-b":
        bd = v
    elif o == "-c":
        mkcd = True
    elif o == "-d":
        pipupd = True
    elif o == "-e":
        email = True
    elif o == "-i":
        verinc = True
    elif o == "-p":
        publish = True
        windows = True
    elif o == "-t":
        test = True
    elif o == "-v":
        newver = v
    elif o == "-w":
        windows = True
if publish:
    mkcd = True
if not os.path.exists(bd):
    print("Invalid Base Directory (%s)" % bd)
    sys.exit()
pypath = findFile(start=[bd], name=bv, ftyp="d")
if not pypath:
    print("%s/%s directory not found" % (bd, bv))
    sys.exit()
for d in ("TartanExe", "TartanOld", "TartanSve"):
    if not os.path.exists(os.path.join(bd, d)):
        os.makedirs(os.path.join(bd, d))
csys = "Tartan"
cver = list(VERSION)
if not newver:
    if verinc:
        vinc = input("Increment Version (y/n): ")
    else:
        vinc = "n"
    if vinc.lower() == "y":
        cver[1] += 1
        newver = "%s.%s" % (cver[0], cver[1])
else:
    cver = list(newver.split("."))
    if len(cver) != 2:
        print("Invalid -v option (%s)" % newver)
        sys.exit()
    for x in range(2):
        cver[x] = int(cver[x])
# Change to pypath directory
os.chdir(pypath)
if newver and newver != "%s.%s" % VERSION:
    if not os.path.isfile("changes.txt"):
        input("changes.txt File Not Found! Ctl-C to Abort")
    try:
        if pipupd:
            # Update sependancies
            exeCmd("sh %s/uty/dopip.bat")
            if windows:
                exeCmd("wine %s/uty/dopip.bat")
        # Change version number in ms0000.py, SYS.rst, Downloads.rst
        old = open("ms0000.py", "r")
        lin = old.readlines()
        old.close()
        new = open("ms0000.py", "w")
        for l in lin:
            s = l.split()
            if len(s) > 1 and s[0] == "VERSION" and not l.count("int"):
                l = "    VERSION = %s\n" % str(tuple(cver))
            new.write(l)
        new.close()
        os.chmod("ms0000.py", 0o755)
        old = open("doc/SYS.rst", "r")
        lin = old.readlines()
        old.close()
        new = open("doc/SYS.rst", "w")
        oldver = None
        for l in lin:
            if l[:9] == ":Version:":
                oldver = l.split()[1].strip()
                l = ":Version:   %s\n" % newver
            elif oldver:
                l = l.replace(oldver, newver)
            new.write(l)
        new.close()
        old = open("doc/Downloads.rst", "r")
        lin = old.readlines()
        old.close()
        new = open("doc/Downloads.rst", "w")
        oldver = None
        for l in lin:
            if l.count("The latest version of Tartan is"):
                oldver = l.split()[6]
                date = time.strftime("%d %B, %Y", time.localtime())
                part = date.split()
                day = int(part[0])
                if day in (1, 21, 31):
                    day = "%sst" % day
                elif day in (2, 22):
                    day = "%snd" % day
                elif day in (3, 23):
                    day = "%srd" % day
                elif day > 3 and day < 21:
                    day = "%sth" % day
                elif day > 23 and day < 31:
                    day = "%sth" % day
                newdte = "%s%s" % (day, date[2:])
                l = "The latest version of Tartan is %s and was "\
                    "released on the %s.\n" % (newver, newdte)
            elif oldver:
                l = l.replace(oldver, newver)
            new.write(l)
        new.close()
        # Update repository version control
        if vv == 5:
            sta = "/usr/bin/bzr status"
            dif = "/usr/bin/bzr diff"
        else:
            sta = "/usr/bin/git status"
            dif = "/usr/bin/git diff"
        sta += " > ver/ver_%s.%s.status" % tuple(cver)
        exeCmd(sta)
        dif += " > ver/ver_%s.%s.diff" % tuple(cver)
        exeCmd(dif)
        if os.path.isfile("changes.txt"):
            exeCmd("mv changes.txt ver/ver_%s.%s.changes" % (cver[0], cver[1]))
        # Create changes module
        chg = open("tarchg.py", "w")
        chg.write('changes = """')
        for x in range(9, 1, -1):
            for y in range(99, -1, -1):
                nam = "ver_%s.%s" % (x, y)
                fle = os.path.join("ver", "%s.changes" % nam)
                if os.path.isfile(fle):
                    chg.write(nam + "\n")
                    chg.write(("=" * len(nam)) + "\n")
                    lines = open(fle, "r")
                    for line in lines:
                        chg.write(line)
                    chg.write("\n")
            for y in range(999, -1, -1):
                for z in range(99, 0, -1):
                    nam = "ver_%s.%s.%s" % (x, y, z)
                    fle = os.path.join("ver", "%s.changes" % nam)
                    if os.path.isfile(fle):
                        chg.write(nam + "\n")
                        chg.write(("=" * len(nam)) + "\n")
                        lines = open(fle, "r")
                        for line in lines:
                            chg.write(line)
                        chg.write("\n")
        chg.write('"""')
        chg.close()
        # Create changes rst
        rst = open("doc/Changes.rst", "w")
        chg = __import__("tarchg")
        rst.write(chg.changes)
        rst.close()
        # Create current file
        cur = open("%s/TartanExe/current" % bd, "w")
        cur.write("%s\n" % newver)
        cur.close()
        # Commit repository
        if vv == 5:
            exeCmd("/usr/bin/bzr commit -m 'ver_%s.%s'" % tuple(cver))
            exeCmd("/usr/bin/bzr log > ver/ver_%s.%s.log" % tuple(cver))
        else:
            exeCmd("/usr/bin/git add ver")
            exeCmd("/usr/bin/git commit -am 'ver_%s.%s'" % tuple(cver))
            if not test:
                push = input("Push Version (y/n): ")
                if push == "y":
                    exeCmd("/usr/bin/git push -u origin master")
    except:
        print("Error Creating New Version")
        sys.exit()
# Create a zip of the repository
if os.path.exists("%s/tarzip.zip" % bd):
    os.remove("%s/tarzip.zip" % bd)
if vv == 5:
    exeCmd("/usr/bin/bzr export --format=zip --root= %s/tarzip.zip" % bd)
else:
    exeCmd("/usr/bin/git archive --format=zip HEAD -o %s/tarzip.zip" % bd)
# Update the zip with tarchg.py tartan.ico and uncommitted files
exeCmd("zip -qr %s/tarzip tarchg.py tartan.ico ass/*.py bkm/*.py bks/*.py bwl/*.py crs/*.py csh/*.py drs/*.py gen/*.py lon/*.py mem/*.py mst/*.py pos/*.py rca/*.py rtl/*.py scp/*.py sls/*.py str/*.py tab/*.py ms0000.py TartanClasses.py tartanFunctions.py tartanImages.py tartanWork.py uty/*.py wag/*.py" % bd)
# Create a new system directory
if os.path.exists("%s/tartan" % bd):
    shutil.rmtree("%s/tartan" % bd)
os.mkdir(os.path.join(bd, "tartan"))
# Change directory to system directory
os.chdir("%s/tartan" % bd)
# Unzip the repository into the system directory
exeCmd("unzip -qq %s/tarzip" % bd)
os.remove("%s/tarzip.zip" % bd)
# Rename and/or Remove paths and files
if os.path.isdir("ver"):
    shutil.rmtree("ver")
# Create tarimp module for pyinstaller
ofl = open("tarimp.py", "w")
ofl.write("# Tartan Modules to Include with Pyinstaller Exe\n")
ofl.write("import pkg_resources.py2_warn\n")
ofl.write("import sys\n")
for fle in glob.iglob("*.py"):
    if fle.count("__pycache__"):
        continue
    ofl.write("import %s\n" % fle.replace("/", ".").replace(".py", ""))
for fle in glob.iglob("???/*.py"):
    if fle.count("__pycache__"):
        continue
    ofl.write("import %s\n" % fle.replace("/", ".").replace(".py", ""))
ofl.close()
print("")
# Change to Base Directory
os.chdir(bd)
# Create zip file for pyinstaller
zipfle = "tartan-%s" % vv
print("Creating %s.zip in TartanSve directory ..... Please Wait" % zipfle)
if os.path.exists("%s/TartanSve/%s.zip" % (bd, zipfle)):
    os.remove("%s/TartanSve/%s.zip" % (bd, zipfle))
if vv == 5:
    exeCmd("zip -qr %s/TartanSve/%s tartan --exclude \.bzr\*" % (bd, zipfle))
else:
    exeCmd("zip -qr %s/TartanSve/%s tartan --exclude \.git\*" % (bd, zipfle))
if windows:
    # Python windows executable
    if vv == 5:
        dd = "%s/.wine2/drive_c/PyInstall" % bd
        exeCmd("wine2 cmd /c %s/maker.bat tartan" % dd)
    else:
        names = []
        proc = subprocess.Popen("/usr/bin/virsh list --name --state-running",
            shell=True, bufsize=0, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, close_fds=True)
        for l in proc.stdout:
            names.append(l.strip().decode("utf-8"))
        if "win10" in names:
            os.system("ssh windows PyInstall\\\\maker.bat tartan")
        else:
            dd = "%s/.wine3/drive_c/PyInstall" % bd
            exeCmd("wine3 cmd /c %s/maker.bat tartan" % dd)
if publish:
    # Publish
    # Change to pypath directory
    os.chdir(pypath)
    # Documentation
    man = "doc/Manual.rst"
    fles = ["doc/SYS.rst", "doc/CTL.rst", "doc/GEN.rst", "doc/ASS.rst",
            "doc/BKM.rst", "doc/CRS.rst", "doc/DRS.rst", "doc/LON.rst",
            "doc/MEM.rst", "doc/RTL.rst", "doc/RCA.rst", "doc/STR.rst",
            "doc/SLS.rst", "doc/POS.rst", "doc/WAG.rst", "doc/SLN.rst",
            "doc/BKS.rst", "doc/BWL.rst", "doc/CSH.rst", "doc/SCP.rst",
            "doc/UTY.rst", "doc/HLP.rst"]
    doc = open(man, "w")
    for fle in fles:
        if fle == fles[-1]:
            addPage(doc, fle, True)
        else:
            addPage(doc, fle)
    doc.close()
    # Move Current to Old
    exeCmd("mv %s/TartanExe/%s_%s.* %s/TartanOld/" % (bd, csys, vv, bd))
    # Create Source tgz and zip
    exeCmd("tar -czf %s/TartanExe/%s_%s.%s.tgz %s/tartan" %
        (bd, csys, cver[0], cver[1], bd))
    exeCmd("cp -p %s/TartanSve/tartan-%s.zip %s/TartanSve/%s_%s.%s.zip" %
        (bd, vv, bd, csys, cver[0], cver[1]))
    # Rename Windows exe's
    exeCmd("cp -p %s/TartanExe/tartan-%s.exe %s/TartanExe/%s_%s.%s.exe" %
        (bd, vv, bd, csys, cver[0], cver[1]))
    print("")
    print("Version Number is %s.%s" % tuple(cver))
    print("")
    if not test:
        # Dropbox
        exeCmd("rm /home/paul/Dropbox/Updates/%s*" % csys)
        exeCmd("cp -p %s/TartanExe/%s_%s.%s.tgz "\
            "/home/paul/Dropbox/Updates/" % (bd, csys, cver[0], cver[1]))
        exeCmd("cp -p %s/TartanExe/%s_%s.%s.exe "\
            "/home/paul/Dropbox/Updates/" % (bd, csys, cver[0], cver[1]))
        # FTP Server
        exeCmd("ssh %s rm /srv/ftp/%s*" % (sv, csys))
        exeCmd("rsync -az %s/TartanOld/Tartan_2.5.29.* %s:/srv/ftp/ "\
            "--progress" % (bd, sv))
        exeCmd("rsync -az %s/TartanOld/Tartan_3.4.51.* %s:/srv/ftp/ "\
            "--progress" % (bd, sv))
        exeCmd("rsync -az %s/TartanOld/Tartan_4.1.14.* %s:/srv/ftp/ "\
            "--progress" % (bd, sv))
        exeCmd("rsync -az %s/TartanOld/Tartan_5.5.* %s:/srv/ftp/ "\
            "--progress" % (bd, sv))
        exeCmd("rsync -az %s/TartanExe/current %s:/srv/ftp/ "\
            "--progress" % (bd, sv))
        exeCmd("rsync -az %s/TartanExe/%s* %s:/srv/ftp/ "\
            "--progress" % (bd, csys, sv))
        exeCmd("ssh %s chmod a+r /srv/ftp/*" % sv)
        exeCmd("ssh %s chown paul:paul /srv/ftp/*" % sv)
        # Web documents
        exeCmd("rsync -az %s/%s/doc/Manual.rst "\
            "%s:/var/www/tartan.co.za/htdocs/Manual/Manual.rst "\
            "--progress" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/QST.rst "\
            "%s:/var/www/tartan.co.za/htdocs/QuickStart/QST.rst "\
            "--progress" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/Downloads.rst "\
            "%s:/var/www/tartan.co.za/htdocs/Downloads/ "\
            "--progress" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/Changes.rst "\
            "%s:/var/www/tartan.co.za/htdocs/Changes/ "\
            "--progress" % (bd, bv, sv))
        # Create CD
        if os.path.isdir("%s/TartanCD" % bd):
            shutil.rmtree("%s/TartanCD" % bd)
            exeCmd("mkdir %s/TartanCD" % bd)
        if os.path.isdir("%s/tempcd" % bd):
            shutil.rmtree("%s/tempcd" % bd)
        # Executables
        exeCmd("mkdir %s/tempcd" % bd)
        exeCmd("mkdir %s/tempcd/Other" % bd)
        exeCmd("cp -p %s/TartanExe/Tartan* %s/tempcd/" % (bd, bd))
        exeCmd("cp -pr %s/TartanExe/* %s/tempcd/Other/" % (bd, bd))
        exeCmd("rm %s/tempcd/Other/Tartan*" % bd)
        exeCmd("rm %s/tempcd/Other/Rnehol*" % bd)
        exeCmd("rm %s/tempcd/Other/??????-[5,6].exe" % bd)
        auto = open("%s/tempcd/AUTORUN.INF" % bd, "w")
        auto.write("""[autorun]
    shell\install=&Install
    shell\install\command=Tartan_%s.%s.exe
""" % (cver[0], cver[1]))
        auto.close()
        exeCmd("todos -o %s/tempcd/AUTORUN.INF" % bd)
        exeCmd("chmod a+x %s/tempcd/AUTORUN.INF" % bd)
        # Add Documentation
        exeCmd("rst2pdf %s/%s/doc/Manual.rst -o %s/tempcd/Manual.pdf "\
            "-s %s/%s/doc/mystylesheet" % (bd, bv, bd, bd, bv))
        # Make CD iso
        exeCmd("mkisofs -r -J -l -D -V 'Tartan Systems %s.%s' "\
            "-p 'Paul Malherbe paul@tartan.co.za' -copyright 'Paul Malherbe' "\
            "-o %s/TartanCD/Tartan.iso -graft-points /\=%s/tempcd" %
            (cver[0], cver[1], bd, bd))
        shutil.rmtree("%s/tempcd" % bd)
        #if verinc and windows:
        #    # Sourceforge
        #    os.chdir("%s/TartanExe" % bd)
        #    exeCmd("cp -p %s/doc/readme.md ." % pypath)
        #    exeCmd("%s/uty/upload.sh %s" % (pypath, newver))
if email and not test:
    # Email Users
    chgfle = "%s/ver/ver_%s.%s.changes" % (pypath, cver[0], cver[1])
    if os.path.isfile(chgfle):
        serv = ["mail", 465, 2, 1, "paul", "Pakati!@"]
        mfrm = "paul@tartan.co.za"
        subj = "Tartan Update %s.%s is Available" % tuple(cver)
        info = open(chgfle, "r")
        data = info.readlines()
        info.close()
        text = ""
        html = ""
        for dat in data:
            if not text:
                text = dat
            else:
                text = "%s%s" % (text, dat)
        html = "<pre>%s</pre>" % text
        mess = (text, html)
        addrs = [
            "admin@amadlelo.co.za",
            "admin@blueberry.co.za",
            "alickbb@iafrica.com",
            "cnurrish@telkomsa.net",
            "deonk@spargs.co.za",
            "frikkie@lando.co.za",
            "galloway@awe.co.za",
            "jane@acsconsulting.co.za",
            "joannej@buildinn-el.co.za",
            "keith@barrowdale.co.za",
            "lawrence@hawcweb.co.za",
            "liezelstroud@gmail.com",
            "lorraine@acsaccounting.co.za",
            "lorraine@multitrust.net",
            "marindag@buildinn-el.co.za",
            "marlene@acsonline.co.za",
            "mcbagro@gmail.com",
            "mel@acsaccounting.co.za",
            "mike@annettelaing.co.za",
            "no2pigstash@hotmail.com",
            "paul@tartan.co.za",
            "paulabergh@mweb.co.za",
            "rob@itennis.co.za",
            "rene@agfin.co.za",
            "ruthmiles52@gmail.com",
            "tyron@i-volt.net",
            "yolande@acsaccounting.co.za"]
        for addr in addrs:
            if addr == "deonk@spargs.co.za":
                sendMail(serv, mfrm, addr, subj)
            else:
                sendMail(serv, mfrm, addr, subj, mess=(text, html))
shutil.rmtree("%s/tartan" % bd)
print("DONE")
# END
