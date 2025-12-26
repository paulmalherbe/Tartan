#!usr/bin/env python

"""
Use this module to package Tartan and to make linux and/or windows Executables.
"""

import getopt
import os
import pathlib
import shutil
import subprocess
import sys
import time
import traceback


def exeCmd(cmd):
    try:
        os.system(cmd)
    except Exception as err:
        print("%s Command Failed:" % cmd, err)
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
    if "%s.%s" % (x, y) == newver:
        return "%s %s" % (nam, time.strftime("%Y-%m-%d", time.localtime()))
    for src in (bo, bx):
        dd = os.path.join(bd, src)
        if z is None:
            tgz = "%s/Tartan_%s.%s.tgz" % (dd, x, y)
        else:
            tgz = "%s/Tartan_%s.%s.%s.tgz" % (dd, x, y, z)
        if os.path.isfile(tgz):
            dt = time.localtime(os.path.getmtime(tgz))
            nam = "%s %04i-%02i-%02i" % (nam, dt.tm_year, dt.tm_mon, dt.tm_mday)
            break
    return nam

dist = "tartan"                                 # Distribition
cs = dist.capitalize()                          # Tartan
bd = os.path.expanduser("~")                    # Base directory
sv = "root@server"                              # http login@server
vv = 6                                          # Version number
bv = "%s-%s" % (cs, vv)                         # Version base name
bx = "TartanExe"                                # Executable directory
bo = "TartanOld"                                # Old directory
bs = "TartanSve"                                # Save directory
vd = os.path.join(bd, bv)                       # Source directory
if not os.path.isdir(vd):
    print("Invalid Source Directory: %s" % vd)
    sys.exit()
sys.path.append(vd)
from tartanFunctions import findFile, sendMail
from ms0000 import VERSION

bits = []
home = str(pathlib.Path.home())
email = False
mkcd = False
newver = None
publish = False
incunc = True
upgpip = False
verinc = False
windows = False
linux = False
onefle = False
tmpfle = None
try:
    opts, args = getopt.getopt(sys.argv[1:], "b:ceghilopt:uv:w:")
except:
    print("Required arguments missing", sys.argv[1:])
    sys.exit()
for o, v in opts:
    if o == "-h":
        if os.name == "posix":
            os.system("clear")
        else:
            os.system("cls")
        print("""
Usage: python pkgprg.py [options]

    -b Base Directory (%s)
    -c Create a cd (%s)
    -e Email changes (%s)
    -g Include Uncommitted (%s)
    -h This Help
    -o Generate Onefile (%s)
    -i Increment Version (%s)
    -l Linux Executable (%s)
    -p Publish Version (%s)
    -t Temporary Work Directory (%s)
    -u Upgrade python modules (%s)
    -v New Version Number
    -w Windows Installer for Architecture 0=all, 7, 8, 32 and 64 (False)""" % (bd, mkcd, email, incunc, verinc, linux, onefle, publish, tmpfle, upgpip))
        exeCmd("python uty/mkwindows.py -h")
        sys.exit()
    elif o == "-b":
        bd = v
    elif o == "-c":
        mkcd = True
    elif o == "-e":
        email = True
    elif o == "-g":
        incunc = False
    elif o == "-i":
        verinc = True
    elif o == "-l":
        linux = True
    elif o == "-o":
        onefle = True
    elif o == "-p":
        publish = True
        windows = True
    elif o == "-t":
        tmpfle = v
    elif o == "-u":
        upgpip = True
    elif o == "-v":
        newver = v
    elif o == "-w":
        windows = True
        if v == "0":
            bits = ["7", "8", "32", "64"]
        else:
            bits = v.split(",")

if windows:
    names = []
    # Check if wine or windows
    proc = subprocess.Popen("/usr/bin/virsh list --name --state-running",
        shell=True, bufsize=0, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, close_fds=True)
    for l in proc.stdout:
        name = l.strip().decode("utf-8")
        if name and name != "Server":
            names.append(name)
    if names:
        vcheck = input("Use Virtual Machines (y/n): ")
        if vcheck.lower() == "n":
            names = []
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
    try:
        # Create changes.txt
        sys.path.insert(0, pypath)
        from tartanWork import allsys, pkgs, tarmen
        ofle = open("changes.txt", "w")
        ofle.write("""
Tartan Systems Upgrade
----------------------\n""")
        new = {}
        for p in pkgs:
            new[pkgs[p]] = p
        proc = subprocess.Popen("git status", shell=True, bufsize=0,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True)
        prt = proc.stdout.readlines()
        skp = ["ding.wav", "doc", "ms0000", "pkgprg", "readme.md",
            "tartan", "uty"]
        cnt = 0
        for line in prt:
            line = line.decode("utf-8").replace("\n", "")
            if line.count("modified"):
                mtyp = "Modified"
            elif line.count("new file"):
                mtyp = "Added"
            else:
                continue
            skip = False
            for s in skp:
                if line.lower().count(s):
                    skip = True
                    break
            if skip:
                continue
            mod = line.split()[1].split("/")
            sss = new[mod[0]]
            if mod[0] == "sls":
                ttt = ["Sales Invoicing"]
            else:
                ttt = allsys[mod[0].upper()]
            for l in tarmen["%smod" % sss]:
                if l[2] == mod[1].replace(".py", ""):
                    cnt += 1
                    for mmm in tarmen["%smen" % sss]:
                        if mmm[2] == l[1]:
                            ofle.write("%2s) %s %s, %s - %s\n" % \
                                (cnt, mtyp, ttt[0], mmm[3], l[4]))
                    break
        cnt += 1
        ofle.write("""%2s) Other minor changes, fixes and enhancements.

NB:
--
You can only upgrade to this version if your current version is 5.5 or later.
If you have an older version than 5.5 please contact me for assistance.\n""" % cnt)
        ofle.close()
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
        # Create current file
        cur = open("%s/%s/current" % (bd, bx), "w")
        cur.write("%s\n" % newver)
        cur.close()
        # Commit repository
        exeCmd("/usr/bin/git add ver")
        exeCmd("/usr/bin/git commit -am 'ver_%s.%s'" % tuple(cver))
        push = input("Push Version (y/n): ")
        if push == "y":
            exeCmd("/usr/bin/git push -fu origin main")
    except Exception as err:
        err = "%s\n\n%s" % (err, traceback.format_exc())
        print("Error Creating New Version (%s)" % err)
        sys.exit()
# Create a zip of the repository
if os.path.exists("%s/tarzip.zip" % bd):
    os.remove("%s/tarzip.zip" % bd)
exeCmd("/usr/bin/git archive --format=zip HEAD -o %s/tarzip.zip" % bd)
if incunc:
    # Update the zip with tarchg.py and tartan.ico
    exeCmd("zip -qr %s/tarzip tarchg.py tartan.ico" % bd)
    # Update the zip with uncommitted files
    exeCmd("zip -qr %s/tarzip ass/*0.py bkm/*0.py bks/*0.py bwl/*0.py "\
        "crs/*0.py csh/*0.py drs/*0.py gen/*0.py lon/*0.py mem/*0.py "\
        "mst/*0.py rca/*0.py rtl/*0.py scp/*0.py sls/*0.py str/*0.py "\
        "tab/*0.py ms0000.py TartanClasses.py tartanFunctions.py "\
        "tartanImages.py tartanWork.py uty/*0.py wag/*0.py" % bd)
# Create a new system directory
if os.path.exists("%s/%s" % (bd, dist)):
    shutil.rmtree("%s/%s" % (bd, dist))
os.mkdir(os.path.join(bd, dist))
# Change directory to system directory
os.chdir("%s/%s" % (bd, dist))
# Copy file
if windows:
    fles = ["%s.iss" % dist]
    if "7" in bits:
        fles.append("ucrtbase.7")
    if "8" in bits:
        fles.append("ucrtbase.8")
else:
    fles = []
if onefle:
    fles.append("onefle.spec")
else:
    fles.append("onedir.spec")
for fle in fles:
    shutil.copy(os.path.join(vd, "uty", fle), ".")
# Unzip the repository into the system directory
exeCmd("unzip -qq %s/tarzip" % bd)
os.remove("%s/tarzip.zip" % bd)
# Rename and/or Remove paths and files
if os.path.isdir("ver"):
    shutil.rmtree("ver")
# Change to Base Directory
os.chdir(bd)
# Create zip file for pyinstaller
zipfle = "%s-%s" % (dist, vv)
if os.path.exists("%s/%s/%s.zip" % (bd, bs, zipfle)):
    os.remove("%s/%s/%s.zip" % (bd, bs, zipfle))
exeCmd("zip -qr %s/%s/%s %s --exclude \.git\*" % (bd, bs, zipfle, dist))
if windows:
    # Python windows executable
    if names:
        for name in ("win10", "win8", "win7"):
            if name in names and name == "win10":
                bitw = ["64"]
            elif name in names and name == "win8":
                bitw = ["8"]
            elif name in names and name == "win7":
                bitw = ["7"]
            else:
                continue
            exeCmd("scp Tartan-6/uty/mkwindows.py paul@%s:." % name)
            exeCmd("scp TartanSve/tartan-6.zip paul@%s:." % name)
            for bit in bitw:
                print("Packaging %s bit" % bit)
                if bit in bits:
                    bits.remove(bit)
                cmd = "mkwindows.py -a%s" % bit
                if onefle:
                    cmd += " -o"
                if upgpip:
                    # Update dependancies
                    cmd += " -u"
                exeCmd("ssh paul@%s python %s" % (name, cmd))
                exeCmd("scp paul@%s:tartan-6-%s.exe %s/%s" % (bit, bd, bx))
    for bit in bits:
        print("Packaging %s bit" % bit)
        WPFX = "%s/.wine%s" % (bd, bit)
        if bit in ("7", "8", "32"):
            cmd = "WINEARCH=win32 WINEPREFIX=%s /usr/bin/wine" % WPFX
        else:
            cmd = "WINEARCH=win64 WINEPREFIX=%s /usr/bin/wine64" % WPFX
        xpth = "%s/dosdevices/x:" % WPFX
        if not os.path.exists(xpth):
            os.symlink(home, xpth)
        cmd = "%s cmd /c python %s/uty/mkwindows.py -a%s" % (cmd, bv, bit)
        if onefle:
            cmd += " -o"
        if upgpip:
            cmd += " -u"
        if tmpfle:
            cmd += " -t%s" % tmpfle
        exeCmd(cmd)
if linux:
    cmd = "python %s/uty/mklinux.py" % bv
    if onefle:
        cmd += " -o"
    if upgpip:
        cmd += " -u"
    exeCmd(cmd)
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
    exeCmd("rst2pdf %s/%s/doc/Manual.rst -o /tmp/Manual.pdf" % (bd, bv))
    # Create changes rst
    rst = open("doc/Changes.txt", "w")
    chg = __import__("tarchg")
    rst.write(chg.changes)
    rst.close()
    # Move Current tgz to Old
    exeCmd("mv %s/%s/%s_%s.%s.tgz %s/%s/" %
        (bd, bx, cs, VERSION[0], VERSION[1], bd, bo))
    # Create Source tgz
    os.chdir(bd)
    exeCmd("tar -czf %s/%s/%s_%s.%s.tgz %s" %
        (bd, bx, cs, cver[0], cver[1], dist))
    # Create Source zip
    os.chdir(pypath)
    exeCmd("cp -p %s/%s/%s-%s.zip %s/%s/%s_%s.%s.zip" %
        (bd, bs, dist, vv, bd, bs, cs, cver[0], cver[1]))
    if windows:
        # Rename Windows exe's
        if "32" in bits:
            exeCmd("mv %s/%s/%s_%s.%s-32.exe %s/%s/" %
                (bd, bx, cs, VERSION[0], VERSION[1], bd, bo))
            exeCmd("mv %s/%s/%s-%s-32.exe %s/%s/%s_%s.%s-32.exe" %
                (bd, bx, dist, vv, bd, bx, cs, cver[0], cver[1]))
        if "64" in bits:
            exeCmd("mv %s/%s/%s_%s.%s-64.exe %s/%s/" %
                (bd, bx, cs, VERSION[0], VERSION[1], bd, bo))
            exeCmd("mv %s/%s/%s-%s-64.exe %s/%s/%s_%s.%s-64.exe" %
                (bd, bx, dist, vv, bd, bx, cs, cver[0], cver[1]))
        if "8" in bits:
            exeCmd("mv %s/%s/%s_%s.%s-8.exe %s/%s/" %
                (bd, bx, cs, VERSION[0], VERSION[1], bd, bo))
            exeCmd("mv %s/%s/%s-%s-8.exe %s/%s/%s_%s.%s-8.exe" %
                (bd, bx, dist, vv, bd, bx, cs, cver[0], cver[1]))
        if "7" in bits:
            exeCmd("mv %s/%s/%s_%s.%s-7.exe %s/%s/" %
                (bd, bx, cs, VERSION[0], VERSION[1], bd, bo))
            exeCmd("mv %s/%s/%s-%s-7.exe %s/%s/%s_%s.%s-7.exe" %
                (bd, bx, dist, vv, bd, bx, cs, cver[0], cver[1]))
    print("Version Number is %s.%s" % tuple(cver))
    # Dropbox
    exeCmd("rm %s/Dropbox/Apps/%s/%s_%s*" % (home, cs, cs, vv))
    exeCmd("rsync -az %s/%s/%s_%s* "\
        "%s/Dropbox/Apps/Tartan/" % (bd, bx, cs, vv, home))
    exeCmd("rsync -az /tmp/Manual.pdf %s/Dropbox/Apps/Tartan/" % home)
    # Web Server
    exeCmd("rsync -az %s/%s/doc/Manual.rst "\
        "%s:/var/www/tartan.co.za/htdocs/Manual/Manual.rst" % (bd, bv, sv))
    exeCmd("rsync -az %s/%s/doc/QST.rst "\
        "%s:/var/www/tartan.co.za/htdocs/QuickStart/QST.rst" % (bd, bv, sv))
    exeCmd("rsync -az %s/%s/doc/Downloads.rst "\
        "%s:/var/www/tartan.co.za/htdocs/Downloads/" % (bd, bv, sv))
    exeCmd("rsync -az %s/%s/doc/Changes.txt "\
        "%s:/var/www/tartan.co.za/htdocs/Changes/" % (bd, bv, sv))
    exeCmd("ssh %s rm /var/www/tartan.co.za/Updates/%s_%s*" % (sv, cs, vv))
    exeCmd("rsync -az %s/%s/current "\
        "%s:/var/www/tartan.co.za/Updates/" % (bd, bx, sv))
    exeCmd("rsync -az %s/%s/%s_%s* "\
        "%s:/var/www/tartan.co.za/Updates/" % (bd, bx, cs, vv, sv))
    exeCmd("rsync -az /tmp/Manual.pdf "\
        "%s:/var/www/tartan.co.za/Updates/" % sv)
    exeCmd("ssh %s chmod a+rx /var/www/tartan.co.za/Updates/*" % sv)
    exeCmd("ssh %s chown paul:paul /var/www/tartan.co.za/Updates/*" % sv)
    if verinc and windows:
        # Sourceforge
        os.chdir("%s/%s" % (bd, bx))
        exeCmd("cp -p %s/readme.md ." % pypath)
        exeCmd("%s/uty/upload.sh %s" % (pypath, newver))
    if mkcd:
        # Create CD
        if os.path.isdir("%s/TartanCD" % bd):
            shutil.rmtree("%s/TartanCD" % bd)
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
if email:
    # Email Users
    from emladd import addrs
    chgfle = "%s/ver/ver_%s.%s.changes" % (pypath, cver[0], cver[1])
    if os.path.isfile(chgfle):
        serv = ["tartan-co-za-smtp.dynu.com", 465, 2, 1,
                        "paul@tartan.co.za", "Pakati1@"]
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
        for addr in addrs:
            sendMail(serv, mfrm, addr, subj, mess=(text, html))
#shutil.rmtree("%s/%s" % (bd, dist))
print("DONE")
# END
