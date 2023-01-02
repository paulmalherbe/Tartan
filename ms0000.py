#! /usr/bin/env python
"""
SYNOPSIS
    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2022 Paul Malherbe.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import getpass, gc, glob, io, os, platform, shutil, sys, time
try:
    # Check that required modules are installed
    from tartanWork import pymoda
except:
    print("tartanWork cannot be imported")
    sys.exit(0)
errs = []
for mod in pymoda:
    if len(mod) == 4 and sys.platform != mod[3]:
        continue
    try:
        mod = __import__(mod[0])
    except:
        errs.append(mod[1])
if errs:
    for err in errs:
        print("%-16s: Not Installed" % err)
    sys.exit(0)
from TartanClasses import Dbase, ViewPDF, FileDialog, FITZ, GUI, GetCtl
from TartanClasses import MainFrame, MakeManual, MkWindow, PwdConfirm
from TartanClasses import ScrollText, SelectChoice, SplashScreen, Sql
from TartanClasses import TartanConfig, TartanDialog, TartanMenu, TartanUser
from tartanFunctions import askQuestion, askChoice, b64Convert, chkMod
from tartanFunctions import copyList, dateDiff, httpDownload, getPeriods
from tartanFunctions import getPrgPath, loadRcFile, projectDate
from tartanFunctions import runModule, showError, showException, showInfo
from tartanWork import allsys, pymodb, tabdic, tarmen
try:
    from send2trash import send2trash
    TRASH = True
except:
    TRASH = False

# Set the version of Tartan
if "TARVER" in os.environ:
    # Allow override
    temp = tuple(os.environ["TARVER"].split("."))
    VERSION = (int(temp[0]), int(temp[1].rstrip()))
else:
    VERSION = (6, 13)
    os.environ["TARVER"] = "%s.%s" % VERSION

class ms0000(object):
    def __init__(self, opts, args):
        self.cv = [VERSION, "%s.%s" % VERSION]
        default = [
            ("altered", True),
            ("bpwd", ""),
            ("conum", None),
            ("debug", False),
            ("exclude", []),
            ("finper", None),
            ("help", False),
            ("itoggle", False),
            ("loader", False),
            ("imods", False),
            ("output", False),
            ("program", None),
            ("query", None),
            ("rcfdir", None),
            ("rcfile", None),
            ("script", False),
            ("tcode", 0),
            ("user", {}),
            ("version", False),
            ("xdisplay", True),
            ("zerobar", False)]
        for arg, val in default:
            setattr(self, arg, val)
        for o, v in opts:
            if o in ("-a", "--altered"):
                self.altered = False
            if o in ("-b", "--bpwd"):
                self.bpwd = v
            elif o in ("-c", "--conum"):
                self.conum = int(v)
            elif o in ("-d", "--debug"):
                self.debug = True
            elif o in ("-e", "--exclude"):
                self.exclude = v.split(",")
            elif o in ("-f", "--finper"):
                self.finper = int(v)
            elif o in ("-h", "--help"):
                self.help = True
            elif o in ("-i", "--image"):
                self.itoggle = True
            elif o in ("-l", "--loader"):
                self.loader = True
            elif o in ("-m", "--imods"):
                self.imods = True
            elif o in ("-o", "--output"):
                self.output = True
            elif o in ("-p", "--program"):
                self.program = v
            elif o in ("-q", "--query"):
                if not args:
                    if len(v.split()) == 1:
                        # Execute sql commands in a file
                        self.query = v
                    else:
                        self.query = [v.replace("\\", "")]
                else:
                    self.query = []
                    for a in args:
                        if a.count(";"):
                            b = a.split(";")
                            v = "%s %s" % (v, b[0].replace("\\", ""))
                            self.query.append(v)
                            v = b[1]
                            continue
                        if not v:
                            v = a
                        else:
                            v = "%s %s" % (v, a.replace("\\", ""))
                    self.query.append(v)
            elif o in ("-R", "--rcfdir"):
                self.rcfdir = v
            elif o in ("-r", "--rcfile"):
                self.rcfile = v
            elif o in ("-s", "--script"):
                self.script = v
            elif o in ("-t", "--tcode"):
                try:
                    self.tcode = int(v)
                except:
                    print("Invalid value for -t")
                    self.doExit(dbm=False)
            elif o in ("-u", "--user"):
                user = v.split(":")
                self.user["name"] = user[0]
                if len(user) == 2:
                    self.user["pwd"] = user[1]
                else:
                    self.user["pwd"] = ""
            elif o in ("-v", "--version"):
                self.version = True
            elif o in ("-x", "--xdisplay"):
                self.xdisplay = False
            elif o in ("-z", "--zerobar"):
                self.zerobar = True
            elif o in ("-P", "--pdf") and v.endswith("pdf"):
                if FITZ:
                    ViewPDF(pdfnam=v)
                sys.exit()
        if self.output:
            # Redirect stdout
            for pid in range(1000):
                if self.debug:
                    name = "tracer_%s.txt" % pid
                else:
                    name = "stdout_%s.txt" % pid
                self.stdout = os.path.join(getPrgPath()[0], name)
                try:
                    if not os.path.exists(self.stdout):
                        sys.stdout = io.open(self.stdout, "w")
                        os.chmod(self.stdout, 0o777)
                        break
                except:
                    pass
        if self.help:
            print("""
Tartan Systems Help

Usage:      python ms0000.py [options]

Options:
            -a, --altered           Toggle Check for Altered Tables
            -b, --bpwd=             The backup password
            -c, --conum=            The company number
            -d, --debug             Enter debug/trace mode
            -e, --exclude=          Modules to ignore in debug/trace mode
            -f, --finper=           The financial period
            -h, --help              This Help Message
            -i, --image             Toggle the Tartan image option.
            -l, --loader            Try and remove module before importing
            -m, --imods             Try to install missing modules using pip
            -o, --output            Toggle stdout redirection to stdout.txt
            -P, --pdf=              View a pdf file using built in viewer
            -p, --program=          Execute program directly bypassing the menu
            -q, --query=            Execute a sql query
            -R, --rcfdir=           Directory of Available Tartan RC Files
            -r, --rcfile=           Path of Tartan RC File to use
            -s, --script=           Python script in the program directory
            -t, --tcode=            Transaction code
            -u, --user=             User name and password i.e. name:password
            -v, --version           Display Version Details
            -x, --xdisplay          Do not have a mainframe with -ptarBck
            -z, --zerobar           Do not have a progressbar with -ptarBck
""")
            self.doExit(dbm=False)
        if self.script:
            if getattr(sys, "frozen", False):
                sys.path.append(getPrgPath()[1])
            try:
                exec("import %s" % self.script)
            except Exception as err:
                print(err)
            self.doExit(dbm=False)
        if not self.version and not self.xdisplay:
            nodisp = ("tarBck", "tarUpd")
            if not self.query and self.program not in nodisp:
                print("xdisplay False but module not in %s" % str(nodisp))
                self.doExit(dbm=False)
            elif not self.user:
                print("xdisplay False but No User Name")
                self.doExit(dbm=False)
        if self.imods:
            # Import/Upgrade All modules
            if getattr(sys, "frozen", False):
                print("Tartan is frozen, Upgrades not Possible.")
                sys.exit()
            try:
                # Upgrade pip
                from subprocess import check_call as chke
                import importlib.util as chki
                if chki.find_spec("pip") is None:
                    raise Exception("pip Not Found")
                cmd = [sys.executable, "-m", "pip", "install", "-qU"]
                chke(cmd + ["pip"])
                # Install and or Upgrade all modules
                for mod in pymoda + pymodb:
                    if len(mod) == 4 and sys.platform != mod[3]:
                        continue
                    print("Installing/Upgrading", mod[1])
                    try:
                        if mod[1] == "psycopg2":
                            chke(cmd + [mod[1] + "-binary"])
                        else:
                            chke(cmd + [mod[1]])
                    except:
                        print("Module Not Found")
            except Exception as err:
                print(err)
            sys.exit()
        # Check that required modules are installed
        if not self.version and self.xdisplay and not GUI:
            print("Tkinter/ttk not Available or Installed")
            self.doExit(dbm=False)
        elif self.version:
            # Print/Display all dependancies
            nm = platform.uname()
            print("%-16s: %s" % ("Tartan", self.cv[1]))
            print("%-16s: %s, %s, %s" % ("O/System", nm[0], nm[2], nm[4]))
            if sys.maxsize > 2**32:
                py = "python 64bit"
            else:
                py = "python 32bit"
            print("%-16s: %s" % (py, sys.version.split()[0]))
            from TartanClasses import tk
            print("%-16s: %s" % ("tcl/tk",
                tk.Tcl().eval("info patchlevel")))
            for mod in pymoda + pymodb:
                if len(mod) == 4 and sys.platform != mod[3]:
                    continue
                ver = chkMod(mod[0])
                if not ver:
                    print("%-16s: Not Installed" % mod[1])
                else:
                    try:
                        if not mod[2]:
                            raise Exception
                        if type(mod[2]) == tuple:
                            ver = getattr(ver, mod[2][0])
                            ver = getattr(ver, mod[2][1])
                        else:
                            ver = getattr(ver, mod[2])
                        if type(ver) == list:
                            ver = "%s.%s.%s" % tuple(ver)
                        elif type(ver) == tuple:
                            ver = ver[0]
                        ver = ver.split()[0]
                        print("%-16s: %s" % (mod[1], ver))
                    except:
                        print("%-16s: Installed" % mod[1])
            self.doExit(dbm=False)
        if self.debug:
            # Set trace mode
            import trace
            igd = [sys.prefix, sys.exec_prefix]
            igm = ["__init__"]
            if self.exclude:
                igm.extend(self.exclude)
            os.environ["TARTANDB"] = "1"
            self.tracer = trace.Trace(ignoredirs=igd, ignoremods=igm,
                trace=1, count=0)
        self.setVariables()
        if self.rcfdir:
            if not os.path.isdir(self.rcfdir):
                showError(None, "Directory Error",
                    "Invalid -R Directory: %s" % self.rcfdir)
                self.doExit(dbm=False)
            scrn = MkWindow(icon="tartan").newwin
            dialog = FileDialog(**{"parent": scrn, "initd": self.rcfdir})
            self.rcfile = dialog.askopenfilename()
            scrn.destroy()
            if not self.rcfile:
                self.doExit(dbm=False)
        self.mf = None
        self.loop = False
        self.rcdic = None
        main = "Tartan Systems - Copyright %s 2004-2022 Paul Malherbe" % \
            chr(0xa9)
        while not self.rcdic:
            self.rcdic = loadRcFile(self.rcfile, default=True)
            if not type(self.rcdic) == dict:
                showError(None, "Error", "Invalid Preferences File (%s)\n\n%s"
                    % (self.rcfile, self.rcdic))
                self.doExit(dbm=False)
            elif not os.path.isfile(self.rcdic["name"]):
                self.mf = MainFrame(title=main, rcdic=self.rcdic)
                if self.mf.rcdic == "error":
                    self.doExit(dbm=False)
                self.mf.dbm = None
                cfg = TartanConfig(self.mf, rcfile=self.rcfile,
                    rcdic=self.rcdic, level=9)
                if not cfg.rcfile:
                    self.doExit(dbm=False)
                self.rcfile = self.mf.rcfile = cfg.rcfile
                self.rcdic = self.mf.rcdic = loadRcFile(self.rcfile)
        if not self.mf:
            # Create MainFrame if not already existing
            self.mf = MainFrame(rcdic=self.rcdic, xdisplay=self.xdisplay)
            if self.mf.rcdic == "error":
                self.doExit(dbm=False)
        if self.xdisplay:
            # Display the main title
            titl = "%s - (%s - %s@%s)" % (main, self.rcdic["dbase"],
                self.rcdic["dbname"], self.rcdic["dbhost"])
            self.mf.window.title(titl)
            self.mf.head.configure(text="Tartan Systems")
        # Try connecting to the database and create if missing
        self.dbm = Dbase(rcdic=self.rcdic, screen=self.mf.body)
        if self.dbm.err:
            self.doExit(dbm=False)
        self.mf.dbm = self.dbm
        chk = self.dbm.checkDbase()
        if chk not in (True, False):
            showError(self.mf.window, "Database", chk)
            self.doExit()
        elif chk is False:
            if self.rcdic["dbase"] == "PgSQL":
                mes = "%s@%s" % (self.rcdic["dbname"], self.rcdic["dbhost"])
            else:
                mes = os.path.join(self.rcdic["dbdir"], self.rcdic["dbname"])
            ok = askQuestion(self.mf.window, "Database",
                "Create the Database?\n\n%s" % mes)
            if ok == "no":
                self.doExit()
            else:
                from TartanClasses import DBCreate
                opts = [
                    ("-c", "i"),
                    ("-l", self.mf.body),
                    ("-u", self.rcdic["dbuser"]),
                    ("-p", self.rcdic["dbpwd"]),
                    ("-v", self.cv[1]),
                    ("-x", True)]
                DBCreate(dbm=self.dbm, opts=opts)
                self.tarUpd(True)
        # Open the database
        self.dbm.openDbase()
        # Check for ctlsys and if missing call msc110
        err = self.doCheckSys()
        if not err:
            # Check for ctlmst and if missing call ms1010
            err = self.doCheckMst()
        if err:
            # If error, exit
            self.doExit()
        # Close dbase
        self.dbm.closeDbase()
        if not self.program or self.program != "tarUpd":
            # Check Tartan Version and File Formats
            self.doVersionCheck()
        if self.user:
            # Check if user details supplied are valid
            self.userReadCheck(user=self.user["name"], pwd=self.user["pwd"],
                pwdchk=True)
            if not self.user:
                showError(self.mf.window, "Error",
                    "Invalid User or User Password")
        else:
            # Login user
            self.userLogin()
        if not self.user:
            # Exit if not valid user
            self.doExit()
        if self.query:
            # Excecute sql query
            if self.user["lvl"] > 6:
                err = self.doSqlCmd()
            else:
                err = "Invalid Security Level"
            if err:
                if self.xdisplay:
                    showError(self.mf.window, "Data Base Error",
                        "\nDbCommand Error: %s\n" % err)
                else:
                    print("Data Base Error", "DbCommand Error: %s\n" % err)
            self.doExit()
        if self.program:
            # Excecute module without the menu
            mods = copyList(self.usrmod)
            mods.append(["PNNN", "mm_sy", "tb1010", 9, "Amend Tables"])
            mods.append(["PNNN", "mm_sy", "tb1030", 9, "Edit Tables"])
            mods.append(["PNNN", "mm_sy", "tb1050", 9, "Delete Trans"])
            mods.append(["PNNN", "mm_sy", "tb3010", 9, "Print Tables"])
            found = False
            for mod in mods:
                if mod[2] == self.program:
                    if len(mod) == 5:
                        found = True
                        break
                    if len(mod) > 5:
                        if mod[5] is None or mod[5] == self.tcode:
                            found = True
                            break
            if found:
                self.execCommand(mod[0], self.program, mod[4], rtn=self.tcode,
                    menu=False)
            else:
                print("Invalid Module (%s) or Missing Options e.g. "\
                    "(-c, -f or -t)" % self.program)
            self.doExit()
        if self.itoggle:
            # Toggle the display of the tartan image
            if self.mf.rcdic["img"].lower() == "y":
                self.image = False
            else:
                self.image = True
        elif self.mf.rcdic["img"].lower() == "y":
            # Display the tartan image
            self.image = True
        else:
            # Do not display the tartan image
            self.image = False
        # Create the tartan menu
        self.tarmen = TartanMenu(mf=self.mf, usr=self.user["name"],
            men=self.usrmen, mod=self.usrmod, lvl=self.user["lvl"],
            cmd=self.execCommand, img=self.image)
        # Check for notes
        self.checkNotes()
        # Display the tartan menu
        self.tarmen.drawMenu()

    def setVariables(self):
        self.vop = []
        self.sss = {}
        self.men = []
        self.mod = []
        self.acoy = []
        self.dcoy = []
        self.fsys = ("ms1020", "ms1040", "ms3010", "msy010", "msy020")
        for s in sorted(list(allsys.items()), key=lambda kv: kv[1][3]):
            try:
                self.men.extend(tarmen["%2smen" % s[1][1].lower()])
                self.mod.extend(tarmen["%2smod" % s[1][1].lower()])
                self.sss[s[1][1].lower()] = s[1][0]
            except:
                pass
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.direct = False
        self.tarmen = None
        self.email = None

    def doVersionCheck(self):
        if self.xdisplay:
            scrn = self.mf.window
        else:
            scrn = "text"
        self.dbm.openDbase()
        sql = Sql(self.dbm, ["ftable", "ffield", "verupd"])
        chk = sql.getRec("verupd", limit=1)
        if not chk:
            showError(scrn, "Version Error", "Missing verupd Table")
            self.doExit()
        v = chk[0].split(".")
        ov = (int(v[0]), int(v[1].rstrip()))
        if ov < (5, 5):
            showError(scrn, "Version Error",
                """The Version of the Data, %s.%s, is too Old.

Please follow the upgrade instructions at https://www.tartan.co.za/Downloads

or

Email paul@tartan.co.za, with your version number, for assistance.""" % ov)
            self.doExit()
        if ov > self.cv[0]:
            self.dbm.closeDbase()
            ok = askQuestion(scrn, "Version Error",
                """Your Version of TARTAN (%s) Is Older than the File Formats!

Do You Want to Upgrade TARTAN Now?""" % self.cv[1], default="yes")
            if ok == "yes":
                self.sysUpd()
            self.doExit()
        err = bool(ov != self.cv[0])
        chg = False
        if not err and self.altered:
            # Check for Altered Tables
            if self.xdisplay:
                self.mf.window.deiconify()
                sp = SplashScreen(self.mf.body,
                    "Checking for Updates ... Please Wait")
            for tb in tabdic:
                for ext in ("fld", "idx"):
                    lines = tabdic[tb][ext]
                    f1 = []
                    for line in lines:
                        f1.append(line)
                    if ext == "fld":
                        fle = sql.getRec("ffield", where=[("ff_tabl",
                            "=", tb)], order="ff_seq")
                        f2 = []
                        for f in fle:
                            tp = [int(f[1]), f[2], f[3], float(f[4])]
                            tp.extend(f[5:])
                            f2.append(tp)
                    else:
                        fle = sql.getRec("ftable", where=[("ft_tabl",
                            "=", tb)], order="ft_seq")
                        f2 = []
                        for f in fle:
                            tp = [f[1], int(f[2]), f[3]]
                            for t in f[4:]:
                                if t:
                                    tp.append(t)
                            f2.append(tp)
                    if f1 != f2:
                        chg = True
                        break
            if self.xdisplay:
                sp.closeSplash()
        self.dbm.closeDbase()
        if chg or err:
            ok = askQuestion(scrn, "Version Error",
                """Your File Formats Need Updating,

Do You Want to Update Your Files?""", default="yes")
            if ok == "yes":
                self.tarUpd(True)
            else:
                self.doExit()

    def userLogin(self):
        if not self.dbm.dbopen:
            self.dbm.openDbase()
            dbopend = True
        else:
            dbopend = False
        if not self.user:
            self.userReadCheck()
            if self.user and not self.user["pwd"]:
                if dbopend:
                    self.dbm.closeDbase()
                return
        if self.user:
            login = self.user["name"]
        else:
            try:
                login = getpass.getuser()
                if not self.userReadCheck(login, userchk=True):
                    raise Exception
            except:
                login = ""
        tit = ("User Login and Validation",)
        fld = (
            (("T",0,0,0),"INA",30,"Name","Your User Name",
                login,"N",self.usrNam,None,None,None,None,
                "Your log-in Name"),
            (("T",0,1,0),"IHA",30,"Password","Your Password",
                "","N",self.usrPwd,None,None,None,None,
                "Your password. You are allowed a Maximum of 3 attempts."))
        but = (("Quit", None, self.noUser, 1, None, None),)
        self.li = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=((self.endUser, "n"),), txit=(self.noUser,))
        self.loop = True
        self.mf.startLoop()
        if dbopend:
            self.dbm.closeDbase()

    def usrNam(self, frt, pag, r, c, p, i, w):
        self.userReadCheck(w)
        if not self.user:
            return "Invalid User"
        if not self.user["pwd"]:
            return "sk1"
        self.times = 0

    def usrPwd(self, frt, pag, r, c, p, i, w):
        err = self.userCheckPwd(w)
        if not err:
            return "nc"
        elif err == "Expired Password" or self.times == 2:
            return "xt"
        else:
            self.times += 1
            return "Invalid Password"

    def noUser(self):
        self.user = {}
        self.endUser()

    def endUser(self):
        self.loop = False
        self.li.closeProcess()
        self.mf.closeLoop()

    def userReadCheck(self, user=None, userchk=False, pwd=None, pwdchk=False):
        if not self.dbm.dbopen:
            self.dbm.openDbase()
            dbopend = True
        else:
            dbopend = False
        sql = Sql(self.dbm, ["ctlmst", "ctlpwu", "ctlpwm"], prog="ms0000")
        if not user:
            chk = sql.getRec("ctlpwu")
            if len(chk) == 1:
                user = chk[0][sql.ctlpwu_col.index("usr_name")]
        usrd = sql.getRec("ctlpwu", where=[("usr_name", "=", user)], limit=1)
        if userchk:
            if dbopend:
                self.dbm.closeDbase()
            return usrd
        if not usrd:
            self.user = {}
        else:
            self.user = {
                "name": user,
                "pwd":  usrd[sql.ctlpwu_col.index("usr_pwd")]}
            if "usr_last" in sql.ctlpwu_col:
                self.user["last"] = usrd[sql.ctlpwu_col.index("usr_last")]
            else:
                self.user["last"] = 0
            if "usr_coy" in sql.ctlpwu_dic:
                self.user["acoy"] = usrd[sql.ctlpwu_col.index("usr_coy")]
                self.user["dcoy"] = ""
            else:
                self.user["acoy"] = usrd[sql.ctlpwu_col.index("usr_acoy")]
                self.user["dcoy"] = usrd[sql.ctlpwu_col.index("usr_dcoy")]
            self.user["lvl"] = usrd[sql.ctlpwu_col.index("usr_lvl")]
            if pwdchk and self.user["pwd"] and self.userCheckPwd(pwd):
                self.user = {}
        if self.user:
            nos = []
            nop = []
            self.acoy = []
            self.dcoy = []
            self.usrnam = self.user["name"]
            self.pwd = self.user["pwd"]
            acoy = self.user["acoy"]
            dcoy = self.user["dcoy"]
            self.lvl = self.user["lvl"]
            if acoy:
                acoy = acoy.split(",")
            else:
                acoy = []
            for co in acoy:
                if int(co):
                    self.acoy.append(int(co))
            if dcoy:
                dcoy = dcoy.split(",")
            else:
                dcoy = []
            for co in dcoy:
                if int(co):
                    self.dcoy.append(int(co))
            # All systems not in the company and phone modules - nos
            for sss in self.sss:
                if sss not in ("ms", "td"):
                    nos.append(sss)
            # Remove enabled systems
            self.mods = sql.getRec("ctlmst", cols=["ctm_modules"],
                group="ctm_modules")
            for mod in self.mods:
                for x in range(0, len(mod[0]), 2):
                    m = mod[0][x:x+2]
                    if m.lower() in nos:
                        nos.remove(m.lower())
            # All systems excluded for the user - ctlpwm - nos
            tmp = sql.getRec("ctlpwm", cols=["mpw_sys"],
                where=[("mpw_usr", "=", self.user["name"]),
                ("mpw_prg", "=", "")])
            if tmp:
                for s in tmp:
                    if s not in nos:
                        nos.append(s[0])
            # All modules excluded for the user - ctlpwm - nop
            nop = sql.getRec("ctlpwm", cols=["mpw_sys",
                "mpw_prg"], where=[("mpw_usr", "=", self.user["name"]),
                ("mpw_prg", "<>", ""), ("mpw_pwd", "=", "")])
            # All modules enabled for the user - self.vop
            self.vop = sql.getRec("ctlpwm", cols=["mpw_sys",
                "mpw_prg", "mpw_coy", "mpw_pwd"], where=[("mpw_usr",
                "=", self.user["name"]), ("mpw_prg", "<>", ""),
                ("mpw_pwd", "<>", "")])
            if self.vop:
                for sss, mod, coy, ppp in self.vop:
                    if sss in nos:
                        # System in nos, remove system from nos
                        nos.remove(sss)
                        for prg in self.mod:
                            # Add all modules in sss to nop
                            if prg[2][:2] == sss:
                                nop.append([prg[2][:2], prg[2][2:]])
                for sss, mod, coy, ppp in self.vop:
                    # Remove all enabled modules from nop
                    if [sss, mod] in nop:
                        nop.remove([sss, mod])
            # Generate dictionary of financial companies
            self.fcoy = {}
            sql = Sql(self.dbm, ["ctlmst", "ctlynd"], prog="ms0000")
            jon = "Left outer join ctlynd on cye_cono=ctm_cono"
            col = ["ctm_cono", "max(cye_period)"]
            grp = "ctm_cono"
            chk = sql.getRec("ctlmst", join=jon, cols=col, group=grp)
            for coy in chk:
                self.fcoy[coy[0]] = coy[1]
            # Create usrmen and usrmod
            self.usrmen = []
            self.usrmod = []
            for men in self.men:
                if not men:
                    continue
                add = True
                for sss in nos:
                    if men[1][3:] == sss:
                        add = False
                if add:
                    self.usrmen.append(men)
            # List of financial modules
            fmod = ["ms1020", "ms1040", "ms3010", "msy010", "msy020"]
            mods = copyList(self.mod)
            for mod in mods:
                add = True
                if len(self.fcoy) == 1 and not self.fcoy[1]:
                    if mod[0][0] == "P" and mod[2] in fmod:
                        continue
                    if mod[2] == "ms1010":
                        mod[4] = "Club Record Maintenance"
                for sss in nos:
                    if mod[1][3:] == sss:
                        add = False
                    elif mod[2][:2] == sss:
                        add = False
                for sss, prg in nop:
                    if mod[2] == "%s%s" % (sss, prg):
                        add = False
                if add:
                    self.usrmod.append(mod)
        if dbopend:
            self.dbm.closeDbase()

    def userCheckPwd(self, pwd):
        try:
            crypt = b64Convert("decode", self.user["pwd"])
        except:
            crypt = self.user["pwd"]
        if pwd == self.mf.override:
            return
        elif pwd in (self.user["pwd"], crypt):
            pwlife = self.getCtlSys(["sys_pwlife"])
            if not pwlife or not self.user["last"]:
                return
            t = time.localtime()
            dte = (t[0] * 10000) + (t[1] * 100) + t[2]
            chk = projectDate(self.user["last"], pwlife)
            dif = dateDiff(dte, chk, ptype="days")
            if not dif:
                chg = askQuestion(self.mf.window, "Password Expired",
                    "Your Password Has Expired.\n\nDo You Want to Renew It?")
                tx = "Expired Password"
            elif dif < 8:
                chg = askQuestion(self.mf.window, "Password Expiring",
                    "Your Password Expires in %s Day(s)!!!\n\nDo You Want "\
                    "to Renew It Now?" % dif)
                tx = None
            else:
                chg = "no"
                tx = None
            if chg == "yes":
                self.chgPwd()
                if self.new:
                    return self.userCheckPwd(self.new)
                else:
                    return self.userCheckPwd(self.user["pwd"])
            else:
                return tx
        else:
            return "Invalid Password"

    def userLogout(self):
        self.user = {}

    def execCommand(self, typ, prg, tit="", rtn=None, menu=True, pwd=True):
        if menu:
            self.tarmen.closeMenu()
        if rtn is not None:
            try:
                rtn = int(rtn)
            except:
                rtn = None
        if not self.dbm.dbopen:
            self.dbm.openDbase()
            dbopend = True
        else:
            dbopend = False
        if pwd and self.getCtlSys(["sys_pwmust"]) == "Y" and not \
                self.user["pwd"] and prg not in ("chgPwd", "chgUsr", "sysEnd"):
            showError(self.mf.window, "Missing Password",
                """Passwords are Enforced.

Please Create a Password by going to:

System --> Change Password""")
        elif typ[0] == "F":
            if self.xdisplay:
                self.mf.head.configure(text="%s (%s)" % (tit, prg))
                self.mf.updateStatus("")
            try:
                if prg[:8] == "doManual":
                    sss = prg.split()[1]
                    self.doManual(sss, tit)
                else:
                    getattr(self, prg)()
            except SystemExit:
                os._exit(0)
            except Exception as err:
                if self.xdisplay:
                    for wgt in self.mf.window.winfo_children():
                        if wgt not in (
                                self.mf.head, self.mf.body, self.mf.status):
                            wgt.destroy()
                    showException(self.mf.body, self.rcdic["wrkdir"],
                        "Function %s Error %s" % (prg, err), dbm=self.dbm)
                else:
                    showException(None, self.rcdic["wrkdir"],
                        "Function %s Error" % prg, dbm=self.dbm)
                if dbopend:
                    self.dbm.closeDbase()
                self.doExit()
        elif typ[0] == "P":
            self.mf.updateStatus("")
            mcoy = None
            error = False
            if self.vop:
                sss = prg[:2]
                mmm = prg[2:]
                if rtn:
                    mmm = mmm[:3] + str(rtn)
                for vvv in self.vop:
                    if vvv[0] == sss and vvv[1] == mmm:
                        mcoy, self.mpwd = vvv[2:]
                        error = self.pwdCheck()
            if not error:
                popt = {"mf": self.mf}
                if typ[1] == "Y":
                    if typ[2] in ("L", "Y"):
                        if self.program and self.conum:
                            error = self.conoCheck(self.conum, prg=prg)
                            if not error and typ[2] == "L":
                                self.getLastPeriod()
                        else:
                            self.getCompany(prg=prg, period=typ[2])
                        if not self.conum:
                            error = True
                        if not error:
                            # Check if period is up to date
                            check = bool(prg in ("gl3030", "gl3040",
                                "gl3050", "gl3080", "gl4010", "gl4020",
                                "gl6030", "gl6040", "gl6070"))
                            per = getPeriods(self.mf, self.conum, self.finper,
                                check=check)
                            if per == (None, None, None):
                                error = True
                            elif rtn and per[2] == "Y":
                                showError(self.mf.window, "Period Error",
                                    "This Period Has Already Been Finalised")
                                error = True
                            else:
                                popt["period"] = (self.finper, (per[0].work,
                                    per[0].disp), (per[1].work, per[1].disp))
                    else:
                        if self.program and self.conum:
                            error = self.conoCheck(self.conum, prg=prg)
                        else:
                            self.getCompany(prg=prg, period=False)
                        if not self.conum:
                            error = True
                    if mcoy and self.conum != mcoy:
                        showError(self.mf.window, "Company Error",
                            "This Company, Module Combination "\
                            "is Not Allowed for This User")
                        error = True
                    if not error:
                        popt["conum"] = self.conum
                        popt["conam"] = self.conam
                        text = "%-s for %s (%s)" % (tit, self.conam, prg)
                else:
                    text = "%-s for All Companies (%s)" % (tit, prg)
            if not error:
                if typ[3] == "Y":
                    popt["capnm"] = self.user["name"]
                if prg == "ml1010":
                    popt["level"] = self.user["lvl"]
                if rtn:
                    popt["rtn"] = int(rtn)
                if self.xdisplay:
                    self.mf.head.configure(text=text)
                    self.mf.updateStatus("")
                if self.debug:
                    self.tracer.runfunc(self.doRunModule, prg, **popt)
                else:
                    self.doRunModule(prg, **popt)
        if dbopend:
            try:
                # Rollback any uncommitted transactions
                self.dbm.rollbackDbase()
            except:
                pass
            try:
                # Close the database
                self.dbm.closeDbase()
            except:
                pass
        if menu:
            # Display the menu
            if prg == "ms1010":
                self.userReadCheck(user=self.user["name"])
                self.tarmen.lvl = self.user["lvl"]
                self.tarmen.men = self.usrmen
                self.tarmen.mod = self.usrmod
                self.tarmen.setVariables()
            # Check for Notes
            self.checkNotes()
            # Draw the Menu
            self.tarmen.drawMenu()
        elif self.xdisplay:
            self.mf.head.configure(text="Tartan Systems")

    def pwdCheck(self):
        tit = ("Password Validation",)
        fld = ((("T",0,0,0),"IHA",30,"Password","Password",
            "","N", self.doPGet,None,None,None,None),)
        but = (("Cancel", None, self.doPCancel, 1, None, None),)
        self.df = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=((self.doPEnd, "n"),), txit=(self.doPCancel,))
        self.mf.startLoop()
        return self.pwderr

    def doPGet(self, frt, pag, r, c, p, i, w):
        if w not in (b64Convert("decode", self.mpwd), self.mf.override):
            return "Invalid Password"
        self.pwderr = False

    def doPCancel(self):
        self.pwderr = True
        self.doPEnd()

    def doPEnd(self):
        self.df.closeProcess()
        self.mf.closeLoop()

    def getCompany(self, prg=None, period=None):
        self.prg = prg
        self.pertyp = period
        sql = Sql(self.dbm, "ctlmst", prog="ms0000")
        if self.acoy:
            whr = [("ctm_cono", "in", tuple(self.acoy))]
        else:
            whr = None
        coy = sql.getRec("ctlmst", where=whr, order="ctm_cono")
        if not coy:
            showError(self.mf.window, "Error", "No Valid Company Records.")
            return
        self.coys = len(coy)
        if self.coys == 1:
            # Single Company
            if prg in self.fsys and not self.fcoy[1]:
                return
            self.conum = coy[0][sql.ctlmst_col.index("ctm_cono")]
            self.conam = coy[0][sql.ctlmst_col.index("ctm_name")].rstrip()
            self.email = coy[0][sql.ctlmst_col.index("ctm_email")].rstrip()
            self.modul = coy[0][sql.ctlmst_col.index("ctm_modules")].rstrip()
            if not self.pertyp:
                self.finper = None
                return
        if not self.conum:
            if self.acoy:
                self.conum = self.acoy[0]
            else:
                self.conum = 1
        csel = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Com"),
                ("ctm_name", "", 0, "Name", "Y")),
            "order": "ctm_cono"}
        if self.acoy:
            csel["where"] = [("ctm_cono", "in", tuple(self.acoy))]
        if self.coys == 1:
            # Single Company
            tit = ("Period Details",)
            fld = []
        else:
            tit = ("Company Details",)
            fld = [
                [("T",0,0,0),"IUI",3,"Company Number","",
                    self.conum,"N",self.coNum,csel,None,("notzero",)],
                [("T",0,1,0),"ONA",30,"Company Name","",
                    "","N",None,None,None,None]]
        if self.pertyp == "Y":
            self.psel = {
                "stype": "R",
                "tables": ("ctlynd",),
                "cols": (
                    ("cye_period", "", 0, "Prd"),
                    ("cye_start", "", 0, "Start"),
                    ("cye_end", "", 0, "End"),
                    ("cye_final", "", 0, "F")),
                "where": []}
            fld.append(
                [["T",0,2,0],"IUI",3,"Financial Period","",
                    0,"N",self.finPeriod,self.psel,None,None])
            if self.coys == 1:
                self.psel["where"] = [("cye_cono", "=", self.conum)]
                fld[0][0][2] = 0
                self.getLastPeriod()
                fld[0][5] = self.finper
        elif self.pertyp == "L":
            self.getLastPeriod()
            if self.coys == 1:
                return
        else:
            self.finper = None
            if self.coys == 1:
                return
        but = (("Cancel", None, self.coExit, 1, ("T",0,1), ("T",0,0)),)
        self.cp = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=((self.coEnd, "y"),), txit=(self.coExit,))
        if self.conum:
            try:
                self.cp.loadEntry("T", 0, 0, data=self.conum)
                self.cp.loadEntry("T", 0, 1, data=self.conam)
                if self.pertyp == "Y" and self.finper is not None:
                    self.cp.topf[0][2][5] = self.finper
                    self.cp.loadEntry("T", 0, 2, data=self.finper)
            except:
                pass
        self.cp.focusField("T", 0, 1)
        self.mf.startLoop()

    def coNum(self, frt, pag, r, c, p, i, w):
        err = self.conoCheck(w, prg=self.prg)
        if err:
            return err
        self.cp.loadEntry("T", pag, p+1, data=self.conam)
        if not self.pertyp or self.pertyp == "L":
            return "ok"
        self.psel["where"] = [("cye_cono", "=", self.conum)]
        if self.finper is None:
            self.getLastPeriod()
        self.cp.topf[0][2][5] = self.finper

    def getLastPeriod(self):
        sql = Sql(self.dbm, "ctlynd", prog="ms0000")
        p = sql.getRec("ctlynd", cols=["max(cye_period)"],
            where=[("cye_cono", "=", self.conum)])
        self.finper = int(p[0][0])

    def finPeriod(self, frt, pag, r, c, p, i, w):
        sql = Sql(self.dbm, "ctlynd", prog="ms0000")
        r = sql.getRec("ctlynd", cols=["cye_period"],
            where=[("cye_cono", "=", self.conum), ("cye_period", "=", w)],
            limit=1)
        if not r:
            return "Invalid Financial Period"
        self.finper = w

    def coExit(self):
        self.conum = None
        self.coEnd()

    def coEnd(self):
        self.cp.closeProcess()
        self.mf.closeLoop()

    def doRunModule(self, *prg, **popt):
        if not self.debug and self.loader:
            try:
                for mod in sys.modules:
                    if mod.count(prg[0]):
                        del(sys.modules[mod])
                        gc.collect()
            except:
                pass
        try:
            rtn = popt.get("rtn", 0)
            sql = Sql(self.dbm, ["ffield", "ctllog"], prog="ms0000")
            if not sql.error:
                chk = sql.getRec("ffield", where=[("ff_tabl", "=", "ctllog")])
            if not sql.error and len(chk) == 8:
                if not self.user:
                    name = "admin"
                else:
                    name = self.user["name"]
                try:
                    logd = [getpass.getuser(), name, prg[0], rtn]
                except:
                    logd = [name, name, prg[0], rtn]
                if "conum" in popt:
                    logd.append(popt["conum"])
                else:
                    logd.append(0)
                if "period" in popt:
                    logd.append(popt["period"][0])
                else:
                    logd.append(0)
                logd.append(int(
                    "%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3]))
                sql.insRec("ctllog", data=logd)
                self.dbm.commitDbase()
            runModule(prg[0], **popt)
        except Exception as err:
            if self.xdisplay:
                for wgt in self.mf.window.winfo_children():
                    if wgt not in (self.mf.head, self.mf.body, self.mf.status):
                        wgt.destroy()
                showException(self.mf.body, self.rcdic["wrkdir"],
                    "%s\n\nMod: %s\nArg: %s" % (err, prg, popt), dbm=self.dbm)
            else:
                showException(None, self.rcdic["wrkdir"],
                    "%s\nMod: %s\nArg: %s" % (err, prg, popt), dbm=self.dbm)

    def checkNotes(self):
        if not self.dbm.dbopen:
            self.dbm.openDbase()
            dbopend = True
        else:
            dbopend = False
        t = time.localtime()
        self.cdate = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.sql = Sql(self.dbm, ["ctlnot", "ctlpwu"], prog="ms0000")
        chk = self.sql.getRec("ctlnot", where=[("(", "not_user", "=",
            self.user["name"], "or", "not_auser", "=", self.user["name"],
            ")"), ("not_adate", ">", 0), ("not_adate", "<=", self.cdate),
            ("not_aflag", "<>", "C")])
        if chk:
            ok = askQuestion(self.mf.window, "Notes", "There are Notes "\
                "Flagged for Action Still Outstanding, do You want to "\
                "View them?")
            if ok == "yes":
                self.showNotes(chk)
        if dbopend:
            self.dbm.closeDbase()

    def showNotes(self, notes):
        data = []
        for note in notes:
            nte = note[:4]
            nte.append(note[6])
            nte.append(note[7])
            nte.append(note[8])
            nte.append(note[5])
            nte.append(note[10])
            data.append(nte)
        tits = "Today's Notes"
        cols = [
            ("not_cono", "Coy", 3, "UI", "N"),
            ("not_sys", "Sys", 3, "UA", "N"),
            ("not_key", "Key", 30, "NA", "N"),
            ("not_date", "Entry-Date", 10, "D1", "N"),
            ("not_aflag", "F", 1, "UA", "N"),
            ("not_adate", "Action-Dte", 10, "d1", "N"),
            ("not_auser", "Action-User", 20, "NA", "N"),
            ("not_desc", "Description", 50, "TX", "N"),
            ("not_seq", "Sequence", 10, "US", "N")]
        sr = SelectChoice(self.mf.body, tits, cols, data)
        if sr.selection:
            self.selectNote(sr.selection)
            self.checkNotes()

    def selectNote(self, note):
        self.chgflag = note[5]
        self.chgdate = note[6]
        self.chguser = note[7]
        self.nseq = note[9]
        tit = ("Notes Editing",)
        r1s = (("Normal","N"),("Urgent","U"),("Completed","C"))
        fld = (
            (("T",0,0,0),"O@not_date",0,""),
            (("T",0,1,0),"O@not_user",0,""),
            (("T",0,2,0),"OTV",(50,10),"Details"),
            (("T",0,3,0),("IRB",r1s),0,"Action Flag (C/N/U)","Action Flag",
                "N","N",self.doChgFlag,None,None,None),
            (("T",0,4,0),"I@not_adate",0,"","",
                "","N",self.doChgDate,None,None,("efld",)),
            (("T",0,5,0),"I@not_auser",0,"","",
                "","N",self.doChgUser,None,None,("efld",)))
        but = (
            ("Accept",None,self.doNEnd,1,None,None),
            ("Cancel",None,self.doNExit,1,None, None))
        tnd = ((self.doNEnd, "n"), )
        txt = (self.doNExit, )
        self.nf = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=tnd, txit=txt, focus=False)
        self.nf.loadEntry("T", 0, 0, data=note[4])
        self.nf.loadEntry("T", 0, 1, data=self.user["name"])
        self.nf.loadEntry("T", 0, 2, data=note[8])
        self.nf.loadEntry("T", 0, 3, data=note[5])
        self.nf.loadEntry("T", 0, 4, data=note[6])
        self.nf.loadEntry("T", 0, 5, data=note[7])
        if self.chgflag == "C":
            self.nf.setWidget(self.nf.B0, "normal")
            self.nf.setWidget(self.nf.B1, "normal")
        else:
            self.nf.focusField("T", 0, 4)
        self.mf.startLoop()

    def doChgFlag(self, frt, pag, r, c, p, i, w):
        self.chgflag = w
        if self.chgflag == "C":
            return "nd"

    def doChgDate(self, frt, pag, r, c, p, i, w):
        self.chgdate = w

    def doChgUser(self, frt, pag, r, c, p, i, w):
        usr = self.sql.getRec("ctlpwu", where=[("usr_name", "=", w)],
            limit=1)
        if not usr:
            return "Invalid User Name"
        self.chguser = w
        return "nd"

    def doNEnd(self):
        self.sql.updRec("ctlnot", cols=["not_aflag", "not_adate", "not_auser"],
            data=[self.chgflag, self.chgdate, self.chguser], where=[("not_seq",
            "=", self.nseq)])
        self.dbm.commitDbase()
        self.doNExit()

    def doNExit(self):
        self.nf.closeProcess()
        self.mf.closeLoop()

    def chgUsr(self):
        if not self.dbm.dbopen:
            self.dbm.openDbase()
            dbopend = True
        else:
            dbopend = False
        sql = Sql(self.dbm, "ctlpwu", prog=self.__class__.__name__)
        cnt = sql.getRec("ctlpwu", cols=["count(*)"],
            where=[("usr_name", "<>", self.user["name"])], limit=1)
        if not cnt[0]:
            showError(self.mf.window, "Change", "There are No Other Users")
            if dbopend:
                self.dbm.closeDbase()
            return
        self.userLogout()
        self.userLogin()
        if dbopend:
            self.dbm.closeDbase()
        if not self.user:
            self.doExit()
        self.tarmen.usr = self.user["name"]
        self.tarmen.lvl = self.user["lvl"]
        self.tarmen.men = self.usrmen
        self.tarmen.mod = self.usrmod
        self.tarmen.setVariables()

    def chgPwd(self):
        tit = ("Change Password",)
        fld = (
            (("T",0,0,0),"IHA",30,"Old Password","",
                "","N",self.doOldPwd,None,None,None,None),
            (("T",0,1,0),"IHA",30,"New Password","",
                "","N",self.doNewP1,None,None,None,None),
            (("T",0,2,0),"IHA",30,"New Password","New Password Again",
                "","N",self.doNewP2,None,None,None,None))
        but = (("Cancel", None, self.doPwdExit, 1, None, None),)
        self.np = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=((self.doPwdEnd, "n"),), txit=(self.doPwdExit,))
        if not self.pwd:
            self.np.skip[self.np.pag].append(1)
            self.np.focusField(self.np.frt, self.np.pag, col=2)
        if self.loop:
            self.np.mstFrame.wait_window()
        else:
            self.mf.startLoop()

    def doOldPwd(self, frt, pag, r, c, p, i, w):
        if w == self.pwd or w == b64Convert("decode", self.pwd):
            pass
        else:
            return "Invalid Old Password"

    def doNewP1(self, frt, pag, r, c, p, i, w):
        if w == self.pwd or w == b64Convert("decode", self.pwd):
            return "Same Password"
        pwmust, pwsize = self.getCtlSys(["sys_pwmust", "sys_pwsize"])
        if not w and pwmust == "Y":
            return "You Must Have a Password"
        if pwsize and len(w) < pwsize:
            return "Minimum of %s Characters Required" % pwsize
        self.new = w

    def doNewP2(self, frt, pag, r, c, p, i, w):
        if w != self.new:
            return "Invalid New Password"
        self.pwd = b64Convert("encode", w)

    def doPwdEnd(self):
        pwmust, pwsize = self.getCtlSys(["sys_pwmust", "sys_pwsize"])
        if not self.pwd and pwmust == "Y":
            if not self.pwd:
                self.np.skip[self.np.pag].append(1)
                self.np.focusField(self.np.frt, self.np.pag, col=2)
            else:
                self.np.focusField(self.np.frt, self.np.pag, col=1)
            self.mf.updateStatus("You Must Have a Password",
                bg="white", fg="red")
            return
        t = time.localtime()
        dte = (t[0] * 10000) + (t[1] * 100) + t[2]
        sql = Sql(self.dbm, "ctlpwu", prog="ms0000")
        sql.updRec("ctlpwu", cols=["usr_pwd", "usr_last"], data=[self.pwd,
            dte], where=[("usr_name", "=", self.user["name"])])
        self.dbm.commitDbase()
        self.user["pwd"] = self.pwd
        self.user["last"] = dte
        self.np.closeProcess()
        if not self.loop:
            self.mf.closeLoop()

    def doPwdExit(self):
        self.new = None
        self.np.closeProcess()
        if not self.loop:
            self.mf.closeLoop()

    def tarUsr(self):
        sss = []
        prg = {}
        keys = list(self.sss.keys())
        keys.sort()
        for s in keys:
            sm = []
            sss.append((self.sss[s], s))
            for mod in self.mod:
                if mod[0][0] == "P" and mod[2][:2] == s:
                    if len(mod) == 6:
                        mod[2] = "%s%s" % (mod[2][:5], mod[5])
                    sm.append((mod[3], mod[2][2:], mod[4]))
            prg[s] = sm
        TartanUser(self.mf, self.user["name"], sss, prg)

    def sysUpd(self):
        tit = ("System Upgrade",)
        typ = (("Internet", "I"), ("Local", "L"))
        self.weburl = "https://tartan.co.za"
        fld = (
            (("T",0,0,0),("IRB",typ),0,"Upgrade Type","",
                "I","N",self.doSysLoc,None,None,None,None),
            (("T",0,1,0),"ITX",30,"Server Address","",
                self.weburl,"N",self.doUrl,None,None,("notblank",),None),
            (("T",0,2,0),"ONA",9,"Current Version","",
                "","N",None,None,None,None,None),
            (("T",0,3,0),"ONA",9,"Upgrade Version","",
                "","N",None,None,None,None,None))
        but = (
            ("Upgrade", None, self.doSysUpgrade, 0, ("T",0,0), ("T",0,1)),
            ("Cancel", None, self.doSysUpdXit, 1, None, None))
        self.su = TartanDialog(self.mf, tops=True, title=tit, eflds=fld,
            butt=but, tend=None, txit=(self.doSysUpdXit,))
        self.mf.startLoop()

    def doSysLoc(self, frt, pag, r, c, p, i, w):
        self.updtyp = w
        if self.updtyp == "I":
            return
        self.su.setWidget(self.su.mstFrame, "hide")
        if sys.platform == "win32":
            ftype = [("Upgrade Files", "Tartan_%s.*.exe" % self.cv[0][0])]
        else:
            ftype = [("Upgrade Files", "Tartan_%s.*.tgz" % self.cv[0][0])]
        dialog = FileDialog(**{
            "parent": self.mf.body,
            "title": "Select Upgrade File",
            "initd": self.rcdic["upgdir"],
            "ftype": ftype})
        self.updfle = dialog.askopenfilename()
        self.su.setWidget(self.su.mstFrame, "show")
        if not self.updfle:
            return "Invalid File"
        self.su.loadEntry("T", 0, 1, data=self.cv[1])
        nv = os.path.basename(self.updfle).split("_")[1].split(".")
        self.nv = (int(nv[0]), int(nv[1]))
        self.nt = "%s.%s" % self.nv
        self.su.loadEntry("T", 0, 2, data=self.nt)
        self.su.setWidget(self.su.B0, "focus")
        if int(nv[0]) > self.cv[0][0]:
            return
        if int(nv[0]) == self.cv[0][0] and int(nv[1]) > self.cv[0][1]:
            return
        self.updfle = None
        showError(self.mf.window, "Invalid Version",
            "Not Later Than Current Version.")
        return "Version Error"

    def doUrl(self, frt, pag, r, c, p, i, w):
        self.weburl = w
        try:
            ver = httpDownload("%s/Updates/current" % self.weburl)
            if ver is None:
                raise Exception("Cannot Access Server")
            v = ver.split(".")
            self.nv = (int(v[0]), int(v[1]))
            self.nt = "%s.%s" % self.nv
            if (self.nv[0] > self.cv[0][0]) or (self.nv[0] == self.cv[0][0] \
                    and self.nv[1] > self.cv[0][1]):
                self.su.loadEntry("T", 0, 2, data=self.cv[1])
                self.su.loadEntry("T", 0, 3, data=self.nt)
                return
            self.su.setWidget(self.su.mstFrame, "hide")
            showInfo(self.mf.window, "Upgrade", "Your System is Up to Date")
            return "xt"
        except Exception as err:
            err = "Please Ensure that You Are Connected to the Internet. "\
                "If Not, Please Connect and then Try Again!\n\n%s" % err
            showError(self.mf.window, "Error", err)
            return "ff1"

    def doSysUpgrade(self):
        self.su.closeProcess()
        self.mf.updateStatus("")
        self.mf.closeLoop()
        ScrollText(scrn=self.mf.body, mess="""
                        Performing the Upgrade

  After the update has completed you must perform the following:

  1) If you are running Linux the downloaded file will be in your
     '~/upg' directory. The file's name will be something like
     'Tartan_6.x.tgz'.

                                 or

  1) If you are running Windows the downloaded file will be in your
     'C:\\Tartan\\upg' directory. The file's name will be something like
     'Tartan_6.x-32.exe' or 'Tartan_6.x-64.exe'.
  2) Restart Tartan.
  3) Execute the 'Update File Formats' routine on the 'System' menu.
  4) If Tartan is installed on other workstations, copy the downloaded file
     to those other workstations and either, in the case of linux, extract
     the file and then move the contents of the 'tartan' directory into the
     'prg' directory or, in the case of Windows, execute the file.""")
        try:
            upgdir = self.mf.rcdic["upgdir"]
            if self.updtyp == "I":
                if sys.platform == "win32":
                    if sys.maxsize > 2**32:
                        nam = "Tartan_%s.%s-64.exe" % tuple(self.nv)
                    else:
                        nam = "Tartan_%s.%s-32.exe" % tuple(self.nv)
                else:
                    nam = "Tartan_%s.%s.tgz" % tuple(self.nv)
                fle = os.path.join(upgdir, nam)
                if not httpDownload("%s/Updates/%s" % (self.weburl, nam), fle):
                    raise Exception
            else:
                fle = self.updfle
            if sys.platform == "win32":
                os.spawnv(os.P_NOWAIT, fle, (fle,))
            else:
                os.spawnv(os.P_WAIT, "/bin/tar",
                    ("tar", "-xzf", fle, "-C", upgdir))
                shutil.copytree("%s/tartan" % upgdir, getPrgPath()[1],
                    dirs_exist_ok=True)
                shutil.rmtree("%s/tartan" % upgdir)
            os._exit(0)
        except Exception as err:
            showError(self.mf.window, "Get Error",
                "Upgrade File Could Not be Retrieved.\n\n"\
                "Your System Has Not Been Upgraded.\n\n"\
                "Please Contact Your IT Manager.\n\n%s" % err)
            self.doSysUpdXit()

    def doSysUpdXit(self):
        self.su.closeProcess()
        self.mf.closeLoop()

    def tarUpd(self, dbcreate=False):
        if not dbcreate:
            # Check if database is backed up
            if self.mf.window:
                ok = askQuestion(self.mf.window, "Backup",
                    "Have You Backed Up the Database?", default="no")
            else:
                ok = input("Have You Backed Up the Database? (yes/no) ")
            if ok != "yes":
                return
        elif self.xdisplay:
            self.mf.head.configure(text="Update File Formats (tarUpd)")
            self.mf.updateStatus("")
        dbopen = self.dbm.dbopen
        if not dbopen:
            self.dbm.openDbase()
        popt = {
            "mf": self.mf,
            "bar": True,
            "cln": True,
            "pwd": self.mf.rcdic["dbpwd"],
            "rcf": self.rcfile,
            "upd": False,
            "usr": self.mf.rcdic["dbuser"],
            "ver": self.cv[1]}
        self.doRunModule("tb1020", **popt)
        if not dbopen:
            self.dbm.closeDbase()

    def tarExp(self):
        from TartanClasses import ExportDbase
        ExportDbase(**{"mf": self.mf})

    def tarMrg(self):
        if self.mf.window:
            ok = askQuestion(self.mf.window, "Backup",
                "Have You Backed Up the Database?", default="no")
        else:
            ok = input("Have You Backed Up the Database? (yes/no) ")
        if ok != "yes":
            return
        from TartanClasses import MergeDbase
        MergeDbase(**{"mf": self.mf})

    def tarBck(self):
        from TartanClasses import TarBckRes
        self.dbm.openDbase()
        cf = PwdConfirm(self.mf, conum=0, system="MST", code="TarBck",
            passwd=self.bpwd)
        if cf.flag == "ok":
            try:
                if not self.xdisplay:
                    raise Exception
                sql = Sql(self.dbm, ["ctlmst", "ctlsys"], prog="ms0000")
                if sql.error:
                    raise Exception
                csys = sql.getRec("ctlsys", cols=["sys_budays",
                    "sys_msvr", "sys_mprt", "sys_msec", "sys_maut",
                    "sys_mnam", "sys_mpwd"], limit=1)
                if not csys:
                    raise Exception
            except:
                csys = None
            if self.zerobar:
                TarBckRes(self.mf, mode="B", csys=csys, pbar=False)
            else:
                TarBckRes(self.mf, mode="B", csys=csys)
        elif cf.flag == "no":
            if self.xdisplay:
                scrn = self.mf.window
            else:
                scrn = "text"
            showError(scrn, "Error", "Invalid Backup Password")

    def tarRes(self):
        from TartanClasses import TarBckRes
        cf = PwdConfirm(self.mf, conum=0, system="MST", code="TarRes",
            passwd=self.bpwd)
        if cf.flag == "ok":
            TarBckRes(self.mf, mode="R", ver=self.cv[1])

    def tarCfg(self):
        cfg = TartanConfig(self.mf, rcdic=self.rcdic, level=self.lvl,
            dbskp=True)
        if cfg.rcfile:
            self.rcfile = cfg.rcfile
        self.rcdic = self.mf.rcdic = loadRcFile(self.rcfile)
        if not type(self.rcdic) == dict:
            showError(None, "Error", "Invalid Preferences File (%s)\n\n%s"
                % (self.rcfile, self.rcdic))
            self.doExit(dbm=False)
        self.mf.resizeChildren()

    def sysEnd(self):
        self.userLogout()
        self.doHousekeeping()
        self.doExit()

    def doAbout(self, event=None):
        from TartanClasses import AboutTartan
        AboutTartan(self.mf, self.cv[1])

    def doManual(self, sss, tit):
        try:
            if sss == "REF":
                doc = ["SYS", "CTL", "GEN", "ASS", "BKM", "CRS", "DRS",
                       "LON", "MEM", "RTL", "RCA", "STR", "SLS", "POS",
                       "WAG", "SLN", "BKS", "BWL", "CSH", "SCP", "UTY",
                       "HLP"]
                self.doDisplay(doc)
            else:
                self.doDisplay([sss])
        except Exception as err:
            print(err)

    def doDisplay(self, doc):
        man = ""
        for ddd in doc:
            if ddd != doc[0]:
                man += "\nPageBreak\n"
            rst = os.path.join(getPrgPath()[0], "doc", "%s.rst" % ddd)
            if os.path.exists(rst):
                fle = open(rst, "r")
                if len(doc) == 1 and ddd != "SYS":
                    dat = ""
                    for n, f in enumerate(fle.readlines()):
                        dat += f
                        if n == 1 and f.count("----"):
                            dat += """
.. contents:: **Table of Contents**

"""
                    man += dat
                else:
                    man += fle.read()
                fle.close()
        fle = io.StringIO(str(man))
        if FITZ:
            # Make fitz the default viewer
            vwr = self.mf.rcdic["vwr"]
            self.mf.rcdic["vwr"] = ""
        man = MakeManual(fle, vwr=self.mf.rcdic["vwr"])
        pdf = os.path.join(self.rcdic["wrkdir"], "Manual.pdf")
        try:
            if os.path.exists(pdf):
                os.remove(pdf)
            man.fpdf.output(pdf, "F")
            if os.path.exists(pdf):
                ViewPDF(self.mf, pdf)
        except Exception as err:
            showError(None, "Error", err)
        if FITZ:
            # Restore the viewer
            self.mf.rcdic["vwr"] = vwr

    def doHousekeeping(self):
        fles = []
        for tp in ("csv", "gif", "html", "jpg", "odt", "pdf", "png", \
                                    "ps", "svg", "xls", "xlsx", "xml"):
            fles.extend(glob.glob(os.path.join(self.rcdic["wrkdir"],
                "*.%s" % tp)))
        if fles:
            dft = None
            if "wrka" in self.mf.rcdic and self.mf.rcdic["wrka"] == "Y":
                ask = self.mf.rcdic["wrkf"]
            else:
                if "wrkf" in self.mf.rcdic:
                    if self.mf.rcdic["wrkf"] == "T":
                        dft = "Trash"
                    elif self.mf.rcdic["wrkf"] == "D":
                        dft = "Delete"
                    else:
                        dft = "Keep"
                if TRASH:
                    but = [("Trash", "T", "Send files to Recycle Bin")]
                    if not dft:
                        dft = "Trash"
                else:
                    but = []
                if  not dft:
                        dft = "Delete"
                but.extend([
                    ("Delete", "D", "Permanently Delete the files"),
                    ("Keep", "K", "Keep the files in the Work Directory")])
                ask = askChoice(self.mf.body, "Temporary Files",
                    "What do you wish to do with the Temporary Report Files "\
                    "in the wrk Directory?", butt=but, default=dft)
            if ask == "T":
                for fle in fles:
                    try:
                        send2trash(fle)
                    except:
                        pass
            elif ask == "D":
                for fle in fles:
                    try:
                        os.remove(fle)
                    except:
                        pass

    def doExit(self, dbm=True):
        if dbm and self.dbm.dbopen:
            self.dbm.closeDbase()
        if self.debug:
            sys.settrace(None)
        if self.output:
            # Close and display stdout -- Windows Problem
            try:
                sys.stdout.close()
                sys.stdout = sys.__stdout__
                if os.path.getsize(self.stdout):
                    text = open(self.stdout, "r")
                    lines = text.readlines()
                    text.close()
                    if self.debug and len(lines) > 1000:
                        maxi = 1000
                    else:
                        maxi = len(lines)
                    mess = ""
                    for x in range(maxi):
                        mess = "%s%s" % (mess, lines[x - maxi])
                    if self.help or self.script or self.version:
                        scrn = None
                        font = ("Courier", 12)
                    else:
                        scrn = self.mf.body
                        font = (self.mf.dft, self.mf.dfs)
                    if self.debug:
                        titl = "Trace Output"
                    else:
                        titl = "Standard Output"
                    if self.xdisplay:
                        ScrollText(title=titl, scrn=scrn, mess=mess, font=font)
                    else:
                        print(titl, mess)
                # Housekeeping
                for pid in range(1000):
                    try:
                        if self.debug:
                            name = "tracer_%s.txt" % pid
                        else:
                            name = "stdout_%s.txt" % pid
                        os.remove(os.path.join(getPrgPath()[0], name))
                    except:
                        pass
            except:
                pass
        sys.exit()

    def doCheckSys(self):
        sql = Sql(self.dbm, "ctlsys", prog=self.__class__.__name__)
        if sql.error:
            return "error"
        rec = sql.getRec("ctlsys", limit=1)
        if not rec:
            try:
                self.user = {"name": "admin", "pwd": "", "lvl": 9}
                self.execCommand("PNNY", "msc110", tit="System Record",
                    menu=False, pwd=False)
                rec = sql.getRec("ctlsys", limit=1)
            except:
                rec = [0, "N", 0, 0, 0, "", 0, 0, 0, "", "", "N",
                    "", "", "N", 0]
                sql.insRec("ctlsys", rec)
                self.dbm.commitDbase()
        if not rec:
            return "error"

    def doCheckMst(self):
        chk = self.conoCheck(1, ctl=True)
        if not chk:
            return
        self.user = {"name": "admin", "pwd": "", "lvl": 9}
        self.execCommand("PNNY", "ms1010", tit="Company Record",
            menu=False, pwd=False)
        chk = self.conoCheck(1, ctl=True)
        if chk:
            return "error"

    def conoCheck(self, coy, prg=None, ctl=False):
        gcl = GetCtl(self.mf)
        chk = gcl.getCtl("ctlmst", coy, error=False)
        if not chk:
            self.conum = None
            return "Invalid Company"
        if self.acoy and not self.acoy.count(coy):
            self.conum = None
            return "Unavailable Company Number"
        if self.dcoy and self.dcoy.count(coy):
            self.conum = None
            return "Unavailable Company Number"
        if prg in self.fsys and not self.fcoy[coy]:
            return "xt"
        if ctl:
            return
        self.conum = coy
        self.conum = chk["ctm_cono"]
        self.conam = chk["ctm_name"]
        self.email = chk["ctm_email"]
        self.modul = chk["ctm_modules"]
        if not prg:
            return
        # Check Module
        mod = prg[:2].upper()
        if mod in ("BM", "CP", "MS", "RP"):
            return
        for x in range(0, len(self.modul), 2):
            if self.modul[x:x + 2] == mod:
                return
        return "System (%s) Not Enabled for Company %s" % (mod, self.conum)

    def getCtlSys(self, cols):
        try:
            sql = Sql(self.dbm, "ctlsys", prog="ms0000")
            if sql.error:
                raise Exception
            sss = sql.getRec("ctlsys", cols=cols, limit=1)
            if not sss:
                raise Exception
            if len(cols) == 1:
                return sss[0]
            else:
                return sss
        except:
            sss = []
            for col in cols:
                sss.append(None)
            return sss

    def doSqlCmd(self):
        if type(self.query) is list:
            flenam = self.query
        else:
            name = os.path.abspath(self.query)
            if os.path.isfile(name):
                flenam = open(name, "r")
            else:
                return "Invalid Query File (%s)" % name
        self.dbm.openDbase()
        for line in flenam:
            line = line.rstrip()
            if not line or line[0] == "#":
                continue
            comm = line.split()
            sel = False
            qty = None
            if comm and comm[0].lower() == "select":
                sel = True
                if comm[1][:3].lower() in ("avg", "max", "min", "sum"):
                    qty = 1
                elif comm[1].lower() == "count(*)":
                    qty = 1
                for num, cmd in enumerate(comm):
                    if num < 2:
                        continue
                    if cmd == "limit":
                        qty = int(comm[num + 1])
                        break
            try:
                if comm[0] == "commit":
                    self.dbm.commitDbase()
                else:
                    sq = Sql(self.dbm)
                    if sel:
                        ret = sq.sqlRec(line, limit=qty)
                        self.mess = ""
                        for r in ret:
                            if type(r) is list:
                                r = str(r)[1:-1]
                            else:
                                r = str(r)
                            if not self.mess:
                                self.mess = r
                            else:
                                self.mess = self.mess + "\n" + r
                        if self.xdisplay and self.output:
                            self.mf.head.configure(text="SQL Query")
                            but = ([("Save", self.doSave)])
                            ScrollText(scrn=self.mf.body, mess=self.mess,
                                butt=but)
                        else:
                            print(self.mess)
                    else:
                        sq.sqlRec(line)
            except:
                self.dbm.closeDbase()
                return "Error in SQL Statement\n\n%s" % line
        self.dbm.closeDbase()

    def doSave(self):
        fle = open(os.path.join(self.rcdic["wrkdir"], "query.txt"), "w")
        fle.write(self.mess + "\n")
        fle.close()

if __name__ == "__main__":
    import getopt

    # Ensure that python 3 is being used
    if sys.version_info[:2] < (3, 5):
        print("Invalid Python Version, Must be >= 3.5")
        sys.exit()
    # Add the program path to the PATH variable if possible
    ppath = os.path.realpath(sys.path[0])
    if os.path.isfile(ppath):
        ppath = os.path.normpath(os.path.dirname(ppath))
    if ppath not in os.environ["PATH"].split(os.pathsep):
        epath = "%s%s%s" % (os.environ["PATH"], os.pathsep, ppath)
        os.environ["PATH"] = epath
    # Ubuntu Unity uses the Global Menu which breaks Tartan's Menu
    if sys.platform in ("linux", "linux2"):
        os.environ["UBUNTU_MENUPROXY"] = "0"
    # Load options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "ab:c:de:f:hiklmnoP:p:q:R:r:s:t:u:vxz", [
            "altered", "bpwd=", "conum=", "debug", "exclude=", "finper=",
            "help", "image", "loader", "imods", "output", "pdf=", "program=",
            "query=", "rcfdir=", "rcfile=", "script=", "tcode=",
            "user=", "version", "xdisplay", "zerobar"])
    except:
        opts, args = [("-h", "")], []
    ms0000(opts, args)

# vim:set ts=4 sw=4 sts=4 expandtab:
