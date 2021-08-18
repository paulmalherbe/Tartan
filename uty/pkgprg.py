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
bv = "Tartan-%s" % vv         # Version base name
bx = "TartanExe"              # Executable directory
bo = "TartanOld"              # Old directory
bs = "TartanSve"              # Save directory
vd = os.path.join(bd, bv)     # Version directory
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

def getName(nam, x, y, z=None):
    dd = os.path.join(bd, bo)
    if z is None:
        if x > 5:
            exe = "%s/Tartan_%s.%s-32.exe" % (dd, x, y)
        else:
            exe = "%s/Tartan_%s.%s.exe" % (dd, x, y)
    else:
        exe = "%s/Tartan_%s.%s.%s.exe" % (dd, x, y, z)
    if os.path.isfile(exe):
        dt = time.localtime(os.path.getmtime(exe))
        nam = "%s %04i-%02i-%02i" % (nam, dt.tm_year, dt.tm_mon, dt.tm_mday)
    return nam

print("Packaging...")
bits = ("32", "64")
email = False
mkcd = False
newver = None
publish = False
test = False
upgpip = False
verinc = False
windows = False
opts, args = getopt.getopt(sys.argv[1:], "a:b:cehiptuv:w")
for o, v in opts:
    if o == "-h":
        print("Usage: pkgprg [-a arch] [-b base directory] [-c create cd] "\
                "[-e email] [-h help] [-i increment] [-p publish] "\
                "[-t test] [-u upgpip] [-v new version] [-w windows]")
        sys.exit()
    elif o == "-a":
        if v in ("32", "64"):
            bits = (v,)
        else:
            print("Invalid Architecture")
            sys.exit()
    elif o == "-b":
        bd = v
    elif o == "-c":
        mkcd = True
    elif o == "-e":
        email = True
    elif o == "-i":
        verinc = True
    elif o == "-p":
        publish = True
        windows = True
    elif o == "-t":
        test = True
    elif o == "-u":
        upgpip = True
    elif o == "-v":
        newver = v
    elif o == "-w":
        windows = True
if windows:
    names = []
    # Check if wine or windows
    proc = subprocess.Popen("/usr/bin/virsh list --name --state-running",
        shell=True, bufsize=0, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, close_fds=True)
    for l in proc.stdout:
        names.append(l.strip().decode("utf-8"))
if not os.path.exists(bd):
    print("Invalid Base Directory (%s)" % bd)
    sys.exit()
pypath = findFile(start=[bd], name=bv, ftyp="d")
if not pypath:
    print("%s/%s directory not found" % (bd, bv))
    sys.exit()
for dd in (bx, bo, bs):
    if not os.path.exists(os.path.join(bd, dd)):
        os.makedirs(os.path.join(bd, dd))
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
                    nam = getName(nam, x, y)
                    chg.write(nam + "\n")
                    chg.write(("=" * len(nam)) + "\n")
                    lines = open(fle, "r")
                    skip = False
                    for line in lines:
                        if skip:
                            skip = False
                            continue
                        if line.count("Tartan Systems Upgrade"):
                            skip = True
                            continue
                        chg.write(line)
                    chg.write("\n")
            for y in range(999, -1, -1):
                for z in range(99, 0, -1):
                    nam = "ver_%s.%s.%s" % (x, y, z)
                    fle = os.path.join("ver", "%s.changes" % nam)
                    if os.path.isfile(fle):
                        nam = getName(nam, x, y, z)
                        chg.write(nam + "\n")
                        chg.write(("=" * len(nam)) + "\n")
                        lines = open(fle, "r")
                        skip = False
                        for line in lines:
                            if skip:
                                skip = False
                                continue
                            if line.count("Tartan Systems Upgrade"):
                                skip = True
                                continue
                            chg.write(line)
                        chg.write("\n")
        chg.write('"""')
        chg.close()
        # Create changes rst
        rst = open("doc/Changes.txt", "w")
        chg = __import__("tarchg")
        rst.write(chg.changes)
        rst.close()
        # Create current file
        cur = open("%s/%s/current" % (bd, bx), "w")
        cur.write("%s\n" % newver)
        cur.close()
        # Commit repository
        exeCmd("/usr/bin/git add ver")
        exeCmd("/usr/bin/git commit -am 'ver_%s.%s'" % tuple(cver))
        if not test:
            push = input("Push Version (y/n): ")
            if push == "y":
                exeCmd("/usr/bin/git push -u origin main")
    except Exception as err:
        print("Error Creating New Version (%s)" % err)
        sys.exit()
# Create a zip of the repository
if os.path.exists("%s/tarzip.zip" % bd):
    os.remove("%s/tarzip.zip" % bd)
exeCmd("/usr/bin/git archive --format=zip HEAD -o %s/tarzip.zip" % bd)
# Update the zip with tarchg.py tartan.ico
exeCmd("zip -qr %s/tarzip tarchg.py tartan.ico" % bd)
# Update the zip with uncommitted files
exeCmd("zip -qr %s/tarzip ass/*.py bkm/*.py bks/*.py bwl/*.py crs/*.py "\
    "csh/*.py drs/*.py gen/*.py lon/*.py mem/*.py mst/*.py rca/*.py "\
    "rtl/*.py scp/*.py sls/*.py str/*.py tab/*.py ms0000.py "\
    "TartanClasses.py tartanFunctions.py tartanImages.py tartanWork.py "\
    "uty/*.py wag/*.py" % bd)
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
print("Creating %s.zip in %s directory ..... Please Wait" % (zipfle, bs))
if os.path.exists("%s/%s/%s.zip" % (bd, bs, zipfle)):
    os.remove("%s/%s/%s.zip" % (bd, bs, zipfle))
exeCmd("zip -qr %s/%s/%s tartan --exclude \.git\*" % (bd, bs, zipfle))
if windows:
    # Python windows executable
    if "Windows10" in names:
        if upgpip:
            # Update dependancies
            exeCmd("ssh windows PyInstall\\\\dopip.bat")
        exeCmd("ssh windows PyInstall\\\\maker.bat tartan")
        os.rename("%s/%s/tartan-%s.exe" % (bd, bx, vv),
            "%s/%s/tartan-%s-64.exe" % (bd, bx, vv))
    else:
        for bit in bits:
            print("Packaging %s bit" % bit)
            if upgpip:
                # Update dependancies
                exeCmd("wine%s cmd /c %s/uty/dopip.bat" % (bit, bv))
            xpth = "/home/paul/.wine%s/dosdevices/x:" % bit
            if not os.path.exists(xpth):
                os.symlink("/home/paul", xpth)
            dd = "%s/.wine%s/drive_c/PyInstall" % (bd, bit)
            exeCmd("wine%s cmd /c %s/maker.bat tartan" % (bit, dd))
            os.rename("%s/%s/tartan-%s.exe" % (bd, bx, vv),
                "%s/%s/tartan-%s-%s.exe" % (bd, bx, vv, bit))
if publish:
    # Publish
    # Change to pypath directory
    os.chdir(pypath)
    # Documentation
    man = "doc/Manual.rst"
    fles = ["doc/SYS.rst", "doc/CTL.rst", "doc/GEN.rst", "doc/ASS.rst",
            "doc/BKM.rst", "doc/CRS.rst", "doc/DRS.rst", "doc/LON.rst",
            "doc/MEM.rst", "doc/RTL.rst", "doc/RCA.rst", "doc/STR.rst",
            "doc/SLS.rst", "doc/WAG.rst", "doc/SLN.rst", "doc/BKS.rst",
            "doc/BWL.rst", "doc/CSH.rst", "doc/SCP.rst", "doc/UTY.rst",
            "doc/HLP.rst"]
    doc = open(man, "w")
    for fle in fles:
        if fle == fles[-1]:
            addPage(doc, fle, True)
        else:
            addPage(doc, fle)
    doc.close()
    exeCmd("rst2pdf %s/%s/doc/Manual.rst -o /tmp/Manual.pdf "\
            "-s %s/%s/doc/mystylesheet" % (bd, bv, bd, bv))
    # Move Current to Old
    exeCmd("mv %s/%s/%s_%s.* %s/%s/" %
        (bd, bx, csys, vv, bd, bo))
    # Create Source tgz and zip
    os.chdir(bd)
    exeCmd("tar -czf %s/%s/%s_%s.%s.tgz tartan" %
        (bd, bx, csys, cver[0], cver[1]))
    os.chdir(pypath)
    exeCmd("cp -p %s/%s/tartan-%s.zip %s/%s/%s_%s.%s.zip" %
        (bd, bs, vv, bd, bs, csys, cver[0], cver[1]))
    # Rename Windows exe's
    exeCmd("cp -p %s/%s/tartan-%s-32.exe %s/%s/%s_%s.%s-32.exe" %
        (bd, bx, vv, bd, bx, csys, cver[0], cver[1]))
    exeCmd("cp -p %s/%s/tartan-%s-64.exe %s/%s/%s_%s.%s-64.exe" %
        (bd, bx, vv, bd, bx, csys, cver[0], cver[1]))
    print("")
    print("Version Number is %s.%s" % tuple(cver))
    print("")
    if not test:
        # Dropbox
        exeCmd("rm /home/paul/Dropbox/Apps/%s/%s_6*" % (csys, csys))
        exeCmd("rsync -az %s/%s/%s* "\
            "/home/paul/Dropbox/Apps/Tartan/" % (bd, bx, csys))
        exeCmd("rsync -az /tmp/Manual.pdf /home/paul/Dropbox/Apps/Tartan/")
        # FTP Server
        exeCmd("ssh %s rm /srv/ftp/%s*" % (sv, csys))
        exeCmd("rsync -az %s/%s/%s* %s:/srv/ftp/" % (bd, bx, csys, sv))
        exeCmd("ssh %s chmod a+rx /srv/ftp/*" % sv)
        exeCmd("ssh %s chown paul:paul /srv/ftp/*" % sv)
        # Web documents
        exeCmd("rsync -az %s/%s/doc/Manual.rst "\
            "%s:/var/www/tartan.co.za/htdocs/Manual/Manual.rst" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/QST.rst "\
            "%s:/var/www/tartan.co.za/htdocs/QuickStart/QST.rst" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/Downloads.rst "\
            "%s:/var/www/tartan.co.za/htdocs/Downloads/" % (bd, bv, sv))
        exeCmd("rsync -az %s/%s/doc/Changes.txt "\
            "%s:/var/www/tartan.co.za/htdocs/Changes/" % (bd, bv, sv))
        exeCmd("ssh %s rm /var/www/tartan.co.za/Updates/%s_6*" % (sv, csys))
        exeCmd("rsync -az %s/%s/Tartan_4.1.14.* "\
            "%s:/var/www/tartan.co.za/Updates/" % (bd, bo, sv))
        exeCmd("rsync -az %s/%s/Tartan_5.5.* "\
            "%s:/var/www/tartan.co.za/Updates/" % (bd, bo, sv))
        exeCmd("rsync -az %s/%s/Tartan_5.13.* "\
            "%s:/var/www/tartan.co.za/Updates/" % (bd, bo, sv))
        exeCmd("rsync -az %s/%s/current "\
            "%s:/var/www/tartan.co.za/Updates/" % (bd, bx, sv))
        exeCmd("rsync -az %s/%s/%s* "\
            "%s:/var/www/tartan.co.za/Updates/" % (bd, bx, csys, sv))
        exeCmd("rsync -az /tmp/Manual.pdf "\
            "%s:/var/www/tartan.co.za/Updates/" % sv)
        exeCmd("ssh %s chmod a+rx /var/www/tartan.co.za/Updates/*" % sv)
        exeCmd("ssh %s chown paul:paul /var/www/tartan.co.za/Updates/*" % sv)
        if os.path.isdir("%s/TartanCD" % bd):
            shutil.rmtree("%s/TartanCD" % bd)
        if mkcd:
            # Create CD
            exeCmd("mkdir %s/TartanCD" % bd)
            if os.path.isdir("%s/tempcd" % bd):
                shutil.rmtree("%s/tempcd" % bd)
            # Executables
            exeCmd("mkdir -p %s/tempcd/Other" % bd)
            exeCmd("cp -p %s/%s/Tartan* %s/tempcd/" % (bd, bx, bd))
            exeCmd("cp -pr %s/%s/* %s/tempcd/Other/" % (bd, bx, bd))
            exeCmd("rm %s/tempcd/Other/Tartan*" % bd)
            exeCmd("rm %s/tempcd/Other/Rnehol*" % bd)
            exeCmd("rm %s/tempcd/Other/??????-[5,6]*.exe" % bd)
            auto = open("%s/tempcd/AUTORUN.INF" % bd, "w")
            auto.write("""[autorun]
    shell\install=&Install
    shell\install\command=Tartan_%s.%s-64.exe
""" % (cver[0], cver[1]))
            auto.close()
            exeCmd("todos -o %s/tempcd/AUTORUN.INF" % bd)
            exeCmd("chmod a+x %s/tempcd/AUTORUN.INF" % bd)
            # Add Documentation
            exeCmd("cp /tmp/Manual.pdf %s/tempcd/Manual.pdf" % bd)
            # Make CD iso
            exeCmd("mkisofs -r -J -l -D -V 'Tartan Systems %s.%s' "\
                "-p 'Paul Malherbe paul@tartan.co.za' -copyright 'Paul "\
                "Malherbe' -o %s/TartanCD/Tartan.iso -graft-points "\
                "/\=%s/tempcd" % (cver[0], cver[1], bd, bd))
            shutil.rmtree("%s/tempcd" % bd)
        if verinc and windows:
            # Sourceforge
            os.chdir("%s/%s" % (bd, bx))
            exeCmd("cp -p %s/readme.md ." % pypath)
            exeCmd("%s/uty/upload.sh %s" % (pypath, newver))
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
            "marlene@fourthquadrant.co.za",
            "mcbagro@gmail.com",
            "mel@acsaccounting.co.za",
            "mike@annettelaing.co.za",
            "no2pigstash@hotmail.com",
            "paul@tartan.co.za",
            "paulabergh@mweb.co.za",
            "pevensey@futurenet.co.za",
            "rob@itennis.co.za",
            "rene@agfin.co.za",
            "ruthmiles52@gmail.com",
            "tyron@i-volt.net",
            "yolande@acsaccounting.co.za"]
        for addr in addrs:
            sendMail(serv, mfrm, addr, subj, mess=(text, html))
shutil.rmtree("%s/tartan" % bd)
print("DONE")
# END
