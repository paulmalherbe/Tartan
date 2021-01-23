"""
SYNOPSIS
    Sales Invoicing Point of Sale Terminal

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2021 Paul Malherbe.

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

import copy, functools, os, socket, sys, textwrap, time
try:
    from escpos import printer
    ESCPOS = True
except:
    ESCPOS = False
from TartanClasses import tk, tkfont, ttk
from TartanClasses import AgeAll, ASD, CCD, DrawForm, GetCtl, MyButton
from TartanClasses import MyButtonBox, MyFrame, MyLabel, PwdConfirm
from TartanClasses import SelectChoice, SimpleDialog, SplashScreen, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askQuestion, callModule, doPrinter, copyList
from tartanFunctions import getCost, getImage, getModName, getSell, getVatRate
from tartanFunctions import showError, showInfo

class SmallGrid(object):
    """
    Create a scrollable grid using the following options:

    mf     = Mainframe
    parent = The parent window
    arrow  = The size of the scrollbar arrow
    cols = [
        [(text, ('SD',10.2)), or (text, 10), ..... ]]
    data = [
        ((text, tag, span), (text, tag), (text, tag), (text, tag)),)]
    line   = Number of lines
    butt   = A list of additional buttons e.g. [("hello", cmd)]
    cmds   = A list of bind commands
    font   = (family, size)
    minc   = Minimum columns to show
    """
    def __init__(self, **opts):
        if "line" not in opts:
            opts["line"] = 100
        if "loop" not in opts:
            opts["loop"] = False
        if "arrow" not in opts:
            opts["arrow"] = 20
        self.opts = opts
        self.drawGrid()

    def drawGrid(self):
        # Name main window
        self.window = self.opts["parent"]
        # Style and colours
        style = ttk.Style()
        style.configure("TScrollbar", arrowsize=self.opts["arrow"])
        if "mf" in self.opts:
            self.nbg = self.opts["mf"].rcdic["nbg"]
            self.nfg = self.opts["mf"].rcdic["nfg"]
        else:
            self.nbg = "blue"
            self.nfg = "white"
        # Draw widgets
        # Container frame
        self.cframe = MyFrame(self.window, bg="blue")
        self.rframec = MyFrame(self.cframe, bg="green")
        self.rframec.pack(fill="both", expand="yes")
        self.vsb = ttk.Scrollbar(self.rframec, orient="vertical",
            command=self._yview)
        self.vsb.pack(fill="y", side="right", expand=False)
        rframeh = MyFrame(self.rframec, bg="yellow")
        rframeh.pack(anchor="nw", fill="x")
        self.rframed = MyFrame(self.rframec, bg="pink")
        self.rframed.pack(anchor="nw", fill="both", expand="yes")
        for x in range(len(self.opts["cols"])):
            rframeh.grid_columnconfigure(x, weight=1)
            self.rframed.grid_columnconfigure(x, weight=1)
        # Column headings canvas and font resizing
        self.cv1 = tk.Canvas(rframeh, bd=0, highlightthickness=0)
        if "font" in self.opts:
            ft = self.opts["font"][0]
        elif "mf" in self.opts:
            ft = self.opts["mf"].rcdic["dft"]
        else:
            ft = "Courier"
        fs = 1
        ext = False
        chrs = len(self.opts["cols"])
        for col in self.opts["cols"]:
            chrs += int(col[1][1])
        self.window.update_idletasks()
        ww = self.window.winfo_width() - self.opts["arrow"]
        while True:
            self.norm = tkfont.Font(font=(ft, fs))
            self.bold = tkfont.Font(font=(ft, fs, "bold"))
            self.cw, self.ch = (self.bold.measure("X"),
                self.bold.metrics("linespace"))
            if ext:
                break
            if self.cw * chrs < ww:
                fs += 1
            else:
                fs -= 1
                ext = True
        dif = ww - (self.cw * chrs) - len(self.opts["cols"])
        if self.ch < 40:
            self.ch = 40
        self.cv1.configure(height=self.ch)
        #    height=(self.ch * 1))
        self.cv1.pack(fill="x", anchor="nw")
        # Column headings
        x1 = 0
        y1 = 0
        dd = dif
        for col in self.opts["cols"]:
            w = (col[1][1] + 1) * self.cw
            if dd:
                w += dd
                dd = 0
            x2 = x1 + w
            y2 = y1 + self.ch
            self.cv1.create_rectangle(x1, y1, x2, y2, width=2, fill=self.nbg)
            if col[1][0][1] in ("D", "I"):
                if col[1][0][0] == "S":
                    txt = "%" + str(int(col[1][1]) - 1) + "s"
                else:
                    txt = "%" + str(int(col[1][1])) + "s"
                txt = txt % col[0]
            else:
                txt = col[0]
            self.cv1.create_text(x1 + (self.cw / 2), y1 + int(self.ch / 2),
                text=txt, anchor="w", font=self.bold, fill=self.nfg)
            x1 = x2
        self.cv1.configure(width=ww)
        # Column details canvas
        self.cv2 = tk.Canvas(self.rframed, bd=0, highlightthickness=0,
            yscrollcommand=self.vsb.set, bg="white")
        self.cv2.configure(yscrollincrement=self.ch)
        self.cv2.pack(fill="both", expand="yes", anchor="nw")
        self.window.bind("<Configure>", self.set_scrollregion)
        # Populate cells
        self.cv2.configure(width=ww, height=(self.ch * chrs))
        # Columns and Rows of lines
        y1 = 0
        self.rowcol = []
        rfill, tfill = "white", "black"
        for row in range(self.opts["line"]):
            x1 = 0
            dd = dif
            dat = []
            for col in range(len(self.opts["cols"])):
                # Column data
                if col == len(self.opts["cols"]) - 1:
                    w = (self.opts["cols"][col][1][1] + 1) * self.cw
                else:
                    w = (self.opts["cols"][col][1][1] + 1) * self.cw
                if dd:
                    w += dd
                    dd = 0
                x2 = x1 + w
                y2 = y1 + self.ch
                rect = self.cv2.create_rectangle(x1, y1, x2, y2, width=2,
                    fill=rfill)
                txt = " " * int(self.opts["cols"][col][1][1])
                text = self._load_cell(col, x1, y1, None, self.norm, tfill, txt)
                if "cmds" in self.opts:
                    for cmd in self.opts["cmds"]:
                        self.cv2.tag_bind(rect, cmd[0], functools.partial(
                            self._get_cell, cmd[1], (row, col), text))
                        self.cv2.tag_bind(text, cmd[0], functools.partial(
                            self._get_cell, cmd[1], (row, col), text))
                dat.append(text)
                x1 = x2
            self.rowcol.append(dat)
            y1 = y2
        # Arrow and page keys
        for key in ("Left", "Right", "Up", "Down", "Prior", "Next"):
            self.window.bind("<%s>" % key, self._scroll)
        # Buttons
        if "butt" in self.opts:
            bbox = MyButtonBox(self.window)
            for but in self.opts["butt"]:
                bbox.addButton(but[0], but[1])
                if but[0] in ("Exit", "Quit"):
                    self.window.bind("<Escape>", but[1])
        # Pack frame
        self.cframe.pack(fill="both")
        self.window.update_idletasks()

    def set_scrollregion(self, *args):
        self.cv2.configure(scrollregion=(self.cv2.bbox("all")))

    def _scroll(self, event):
        if event == "Up":
            self._yview("scroll", -1, "units")
        elif event == "Down":
            self._yview("scroll", 1, "units")
        elif event == "Top":
            self._yview("scroll", -10, "page")
            self._yview("scroll", 1, "units")

    def _yview(self, *args):
        self.cv2.yview(*args)

    def _load_cell(self, *args):
        # execute command with following arguments:
        # (col, x, y, delete, font, fill, txt)
        if type(args[0]) == list:
            col, x, y, rem, font, fill, txt = args[0]
        else:
            col, x, y, rem, font, fill, txt = args
        if rem:
            self.cv2.delete(rem)
        # Column data
        fmt = self.opts["cols"][col][1]
        if txt.strip():
            txt = CCD(txt, fmt[0], fmt[1]).disp
        text = self.cv2.create_text(x + (self.cw / 2), y + int(self.ch / 2),
            text=txt, anchor="w", font=self.bold, fill=fill)
        return text

    def _chg_cell(self, *args):
        # (id, txt)
        self.cv2.itemconfig(args[0], text=args[1])

    def _get_cell(self, *args):
        # execute command with following arguments:
        #   (row, col, (rframed, (x, y)), cell)
        plc = (args[3].x, args[3].y)
        args[0](args[1], args[2], (self.rframed, plc), self.window)

class ps2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doDrawScreens()
            self.opts["mf"].startLoop()
            self.opts["mf"].setThemeFont()
            self.opts["mf"].packChildren()
            self.opts["mf"].window.resizable(False, False)
            self.opts["mf"].window.update_idletasks()
            if self.declare:
                callModule(self.opts["mf"], None, "ps2020",
                    coy=(self.opts["conum"], self.opts["conam"]),
                    period=self.opts["period"], user=self.opts["capnm"])

    def setVariables(self):
        # Set Table Fields
        tables = [
            "ctlmst", "ctlvrf", "ctlvtf", "drschn", "drsmst", "drstrn",
            "gentrn", "strgrp", "strmf1", "strmf2", "strgmu", "strcmu",
            "strprc", "strtrn", "strrcp", "posdev","posmst","postrn",
            "posrcp", "tplmst", "tpldet"]
        self.sql = Sql(self.opts["mf"].dbm, tables,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Set, Check Controls
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        if ctlsys and ctlsys["sys_msvr"]:
            self.email = "Y"
        else:
            self.email = "N"
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        ####################################################################
        # Check for Point of Sale Record
        ####################################################################
        try:
            self.host = socket.gethostname()
        except:
            showError(self.opts["mf"].window, "Error",
                "Cannot Determine Terminal Name")
            return
        self.posdev = self.sql.getRec("posdev", where=[("psd_cono",
            "=", self.opts["conum"]), ("psd_host", "=", self.host)], limit=1)
        if not self.posdev:
            showError(self.opts["mf"].window, "Missing Record", "The Point "\
                "of Sale Record for this Workstation (%s) Does Not Exist" %
                self.host)
            return
        self.loc = self.posdev[self.sql.posdev_col.index("psd_lcod")]
        self.fsc = self.posdev[self.sql.posdev_col.index("psd_fscn")]
        self.prt = self.posdev[self.sql.posdev_col.index("psd_pdoc")]
        self.dtp = self.posdev[self.sql.posdev_col.index("psd_dtyp")]
        self.prn = self.posdev[self.sql.posdev_col.index("psd_prnt")]
        self.wid = self.posdev[self.sql.posdev_col.index("psd_pwid")]
        self.pcd = None
        for x in range(1, 6):
            cd = self.posdev[self.sql.posdev_col.index("psd_pc%s" % x)]
            if cd:
                if self.pcd is None:
                    self.pcd = chr(int(cd))
                else:
                    self.pcd += chr(int(cd))
        self.ocd = None
        for x in range(1, 6):
            cd = self.posdev[self.sql.posdev_col.index("psd_od%s" % x)]
            if cd:
                if self.ocd is None:
                    self.ocd = chr(int(cd))
                else:
                    self.ocd += chr(int(cd))
        self.tpl = self.posdev[self.sql.posdev_col.index("psd_tplnam")]
        ####################################################################
        # Create slip printer
        ####################################################################
        try:
            if self.dtp == "I" or not self.prn or self.prn == "view":
                raise Exception
            if ESCPOS:
                self.prtr = printer.Network(host=self.prn, port=9100)
            else:
                raise Exception
        except:
            self.prtr = None
        ####################################################################
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.drgl = drsctl["ctd_glint"]
        self.chns = drsctl["ctd_chain"]
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.stgl = strctl["cts_glint"]
        self.levels = strctl["cts_plevs"]
        self.automu = strctl["cts_automu"]
        if self.drgl == "Y" or self.stgl == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["pos_cash", "pos_card", "pos_vchr"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.cash = ctlctl["pos_cash"]
            self.card = ctlctl["pos_card"]
            self.vchr = ctlctl["pos_vchr"]
            if self.drgl == "Y":
                ctls = ["drs_ctl", "vat_ctl"]
                if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                    return
                self.dctl = ctlctl["drs_ctl"]
                self.vctl = ctlctl["vat_ctl"]
            if self.stgl == "Y":
                ctls = ["stk_soh", "stk_susp"]
                if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                    return
                self.soh = ctlctl["stk_soh"]
                self.ssp = ctlctl["stk_susp"]
        # Load Groups
        sp = SplashScreen(self.opts["mf"].window,
            "Loading Groups, Please Wait ....")
        tab = ["strgrp", "strmf1"]
        col = ["gpm_group", "gpm_desc"]
        whr = [
            ("gpm_cono", "=", self.opts["conum"]),
            ("gpm_desc", "<>", ""),
            ("st1_cono=gpm_cono",),
            ("st1_group=gpm_group",),
            ("st1_type", "<>", "X")]
        if self.automu == "N":
            tab.append("strprc")
            whr.extend([
                ("stp_cono=gpm_cono",),
                ("stp_group=gpm_group",)])
        grp = "gpm_group, gpm_desc"
        odr = "gpm_group"
        self.grps = self.sql.getRec(tables=tab, cols=col, where=whr,
            group=grp, order=odr)
        # Load Items
        self.glist = []
        self.itms = {}
        count = 0
        lst = []
        grps = copyList(self.grps)
        for grp in grps:
            items = self.sql.getRec(
                tables=["strmf1"],
                cols=["st1_code", "st1_desc", "st1_type"],
                where=[
                    ("st1_cono", "=", self.opts["conum"]),
                    ("st1_group", "=", grp[0]),
                    ("st1_type", "<>", "X")],
                order="st1_desc")
            if items:
                for itm in items:
                    qty = self.sql.getRec(
                        tables="strtrn",
                        cols=["sum(stt_qty)"],
                        where=[
                            ("stt_cono", "=", self.opts["conum"]),
                            ("stt_group", "=", grp[0]),
                            ("stt_code", "=", itm[0]),
                            ("stt_loc", "=", self.loc)],
                        limit=1)
                    if itm[2] == "R" or (qty[0] and qty[0] > 0):
                        if grp[0] not in self.itms:
                            self.itms[grp[0]] = []
                        self.itms[grp[0]].append(itm[:2])
                    if grp[0] not in self.itms:
                        continue
                if grp[0] not in self.itms:
                    self.grps.remove(grp)
                    continue
                if not count:
                    lst = []
                lst.append(grp)
                count += 1
                if count == 20:
                    # 20 Items per screen page
                    self.glist.append(copy.deepcopy(lst))
                    count = 0
            else:
                self.grps.remove(grp)
        if lst:
            self.glist.append(copy.deepcopy(lst))
        sp.closeSplash()
        if not self.grps:
            showError(self.opts["mf"].window, "Error",
                "No Valid Group Records.")
            return
        if not self.itms:
            showError(self.opts["mf"].window, "Error",
                "No Valid Product Records.")
            return
        t = time.localtime()
        self.trdt = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.trdt / 100)
        self.batch = "S%s" % self.curdt
        self.declare = False
        self.repno = 1
        self.level = 1
        self.row = 0
        return True

    def doDrawScreens(self):
        # Set Screen sizes
        self.state = "normal"
        self.opts["mf"].window.withdraw()
        self.opts["mf"].packChildren("unpack")
        self.opts["mf"].window.resizable(True, True)
        self.opts["mf"].window.maxsize(-1, -1)
        self.opts["mf"].window.configure(background="white")
        if self.fsc == "Y":
            if sys.platform == "win32":
                self.opts["mf"].window.overrideredirect(1)
                self.opts["mf"].window.state("zoomed")
            else:
                self.opts["mf"].window.attributes("-fullscreen", True)
            ww = self.opts["mf"].window.winfo_screenwidth()
            wh = self.opts["mf"].window.winfo_screenheight()
        else:
            ww = self.opts["mf"].geo[0]
            wh = self.opts["mf"].geo[1]
        self.opts["mf"].window.minsize(ww, wh)
        self.opts["mf"].window.maxsize(ww, wh)
        self.opts["mf"].window.update_idletasks()
        # Rounded Frame Image
        imgpth = os.path.join(self.opts["mf"].rcdic["wrkdir"], "white.png")
        if not os.path.exists(imgpth):
            getImage("white", fle=imgpth)
        if not os.path.exists(imgpth):
            self.img = None
        self.img = tk.PhotoImage("frameborder", file=imgpth)
        # Themes and Styles
        self.style = ttk.Style()
        if "RoundedFrame" not in self.style.element_names():
            self.style.element_create("RoundedFrame", "image", self.img,
                border=16, sticky="nsew")
            self.style.layout("RoundedFrame",
                [("RoundedFrame", {"sticky": "nsew"})])
        self.style.configure("D.TFrame",
            align="center",
            background="white",
            borderwidth=10)
        self.style.configure("D.TButton",
            align="center",
            border=5,
            borderwidth=5,
            relief="flat")
        self.style.configure("L.TButton",
            align="center",
            border=5,
            borderwidth=5,
            font=("Helvetica", 4, "bold"),
            relief="flat")
        self.style.configure("R.TButton",
            align="center",
            border=5,
            borderwidth=5,
            font=("Helvetica", 4, "bold"),
            relief="flat")
        self.style.configure("G.TButton",
            align="center",
            background="pink",
            border=5,
            borderwidth=5,
            font=("Helvetica", 4, "bold"),
            foreground="black",
            relief="flat")
        self.style.map("G.TButton",
            background=[("active", "red"), ("focus", "red")],
            foreground=[("active", "white"), ("focus", "white")])
        self.style.configure("I.TButton",
            align="center",
            background="lightblue",
            border=5,
            borderwidth=5,
            font=("Helvetica", 4, "bold"),
            foreground="black",
            relief="flat")
        self.style.map("I.TButton",
            background=[("active", "blue"), ("focus", "blue")],
            foreground=[("active", "white"), ("focus", "white")])
        self.style.configure("P.TButton",
            align="center",
            foreground="yellow",
            background="red",
            borderwidth=0,
            relief="raised",
            font=("Helvetica", 32, "bold"))
        self.style.map("P.TButton",
            foreground=[("active", "white"), ("focus", "white")],
            background=[("active", "red"), ("focus", "red")])
        # Widgets
        self.window = MyFrame(self.opts["mf"].window, width=ww, height=wh,
            style="D.TFrame")
        self.window.winfo_toplevel().wm_geometry("%sx%s" % (ww, wh))
        self.window.pack(fill="both", expand="yes")
        for row in range(6):
            self.window.grid_rowconfigure(row, weight=1)
        for col in range(7):
            self.window.grid_columnconfigure(col, weight=1)
        # Initial Frame
        self.butts = {}
        self.f0 = MyFrame(self.window)
        self.doButton(self.f0, "Cash\nSale", self.doCash,
            stl="D", rc=(0, 0))
        self.doButton(self.f0, "Account\nSale", self.doAccount,
            stl="D", rc=(0, 1))
        self.butts["D"][-1][0].update_idletasks()
        bw = self.butts["D"][-1][0].winfo_width()
        bh = self.butts["D"][-1][0].winfo_height()
        self.doButton(self.f0, "Cash Up", self.doDeclare,
            stl="D", rc=(0, 2))
        self.doButton(self.f0, "Exit", self.doLogout,
            stl="D", rc=(0, 3))
        for col in range(4):
            self.f0.grid_columnconfigure(col, minsize=bw, weight=1)
        self.f0.grid_rowconfigure(0, minsize=bh, weight=1)
        # Left and Right Frames
        self.lf = MyFrame(self.window)
        self.rf = MyFrame(self.window)
        self.lf.grid(row=0, column=0, rowspan=6, columnspan=3)
        self.rf.grid(row=0, column=3, rowspan=6, columnspan=4)
        # Details Frame
        self.f1 = MyFrame(self.lf, style="RoundedFrame", padding=10)
        self.f1.grid(row=0, column=0, rowspan=5, columnspan=3, sticky="nsew")
        # Groups Frame
        self.grpf = MyFrame(self.rf, bg="blue")
        self.grpf.grid(row=0, column=3, rowspan=5, columnspan=4, sticky="nsew")
        # Items Frame
        self.itmf = MyFrame(self.rf, bg="blue")
        self.itmf.grid(row=0, column=3, rowspan=5, columnspan=4, sticky="nsew")
        # Buttons
        txt = "XXXXXXXXXX"
        for _ in range(2):
            txt = "%s\n%s" % (txt, "XXXXXXXXXX")
        for x in range(0, 3):
            self.doButton(self.lf, txt, None, False, "L", (6, x))
        for x in range(3, 7):
            self.doButton(self.rf, txt, None, False, "R", (6, x))
        self.window.update_idletasks()
        wdt = self.window.winfo_width()
        hgt = self.window.winfo_height()
        self.fsz = 4
        while True:
            chk = self.window.winfo_reqheight() * 6
            if self.window.winfo_reqwidth() >= wdt or chk >= hgt:
                self.fsz -= 1
                self.style.configure("L.TButton",
                    font=("Helvetica", self.fsz, "bold"))
                self.style.configure("R.TButton",
                    font=("Helvetica", self.fsz, "bold"))
                self.window.update_idletasks()
                break
            self.fsz += 1
            self.style.configure("L.TButton", font=("Helvetica", self.fsz,
                "bold"))
            self.style.configure("R.TButton", font=("Helvetica", self.fsz,
                "bold"))
            self.window.update_idletasks()
        self.style.configure("R.TButton", font=("Helvetica", self.fsz, "bold"))
        self.style.configure("G.TButton", font=("Helvetica", self.fsz, "bold"))
        self.style.configure("I.TButton", font=("Helvetica", self.fsz, "bold"))
        for x in range(5):
            for y in range(3, 7):
                self.doButton(self.grpf, txt, None, False, "G", (x, y))
        for x in range(5):
            for y in range(3, 7):
                self.doButton(self.itmf, txt, None, False, "I", (x, y))
        # Fix Settings
        self.window.update_idletasks()
        self.f1.configure(height=self.grpf.winfo_height())
        self.window.update_idletasks()
        self.f1.propagate(0)
        for page in self.butts:
            for but in self.butts[page]:
                but[0].propagate(0)
        if self.fsc == "N":
            ww = self.window.winfo_reqwidth()
            wh = self.window.winfo_reqheight()
        self.opts["mf"].window.minsize(ww, wh)
        self.opts["mf"].window.maxsize(ww, wh)
        self.opts["mf"].window.update_idletasks()
        # Calculate Default Font size
        tsz = 49
        lim = self.f1.winfo_width()
        dft = self.opts["mf"].rcdic["dft"]
        dfs = 5
        while True:
            wth = tkfont.Font(font=(dft, dfs)).measure("X" * tsz)
            if wth > lim:
                break
            dfs += 1
        self.font = (dft, dfs)
        # Left and Right Screens
        # Details Frames
        self.style.configure("f1.TFrame",
            foreground="black",
            background="white")
        self.fh = MyFrame(self.f1, style="f1.TFrame")
        self.fh.pack(anchor="nw", fill="x", expand="yes")
        self.fh.grid_columnconfigure(0, weight=1)
        self.fh.grid_columnconfigure(1, weight=1)
        # Total Lines
        ft1 = self.font[1]
        ft2 = int(ft1 * 1.333)
        self.style.configure("ft1.TLabel", font=("Helvetica", ft1, "bold"))
        self.style.configure("ft2.TLabel", font=("Helvetica", ft2, "bold"))
        l = MyLabel(self.fh, anchor="w", text="Items", color=("black", "white"),
            style="ft1.TLabel")
        l.grid(row=0, column=0, sticky="w")
        self.items = MyLabel(self.fh, anchor="e", text="", color=("black",
            "white"), style="ft1.TLabel", width=11)
        self.items.grid(row=0, column=1, sticky="e")
        self.values = MyLabel(self.fh, anchor="center", text="", color=("black",
            "white"), style="ft2.TLabel", width=11)
        self.values.grid(row=1, column=0, columnspan=2, sticky="nsew")
        # Body Frame
        self.bd = ["row", "grp", "cod", "gtp", "des", "qty", "prc", "exc",
            "inc", "rte", "vcd"]
        self.body = []
        self.fb = MyFrame(self.f1, style="f1.TFrame")
        self.fb.pack(anchor="nw", fill="both", expand="yes")
        self.fb.grid_columnconfigure(0, weight=1)
        self.fb.grid_columnconfigure(1, weight=1)
        self.window.update_idletasks()
        # Draw grid
        self.cols = [
            ("Description", ("NA", 30)),
            ("Qty", ("SD", 11.2)),
            ("Price ", ("SD", 11.2)),
            ("Value ", ("SD", 11.2))]
        self.grid = SmallGrid(**{"parent": self.fb, "font": ("courier", 10),
            "cols": self.cols, "cmds": [("<Button-1>", self.doCallBack)]})
        if self.fsc == "N":
            ww = int(self.lf.winfo_reqwidth() + self.rf.winfo_reqwidth() + 5)
            wh = int(self.lf.winfo_reqheight())
            self.opts["mf"].window.minsize(ww, wh)
            self.opts["mf"].window.maxsize(ww, wh)
        self.butts["L"][0][1].setLabel("Refund", cmd=self.doRefund)
        self.butts["L"][1][1].setLabel("Void", cmd=self.doVoid)
        self.butts["L"][2][1].setLabel("Payment", cmd=self.doPayment)
        self.butts["R"][0][1].setLabel("Undo", cmd=self.doUndo)
        self.butts["R"][1][1].setLabel("Left", cmd=self.doLeft)
        self.butts["R"][2][1].setLabel("Right", cmd=self.doRight)
        self.butts["R"][3][1].setLabel("Exit", cmd=self.doGrpExit)
        self.opts["mf"].window.update()
        self.window.pack_forget()
        self.window.place(anchor="center", relx=0.5, rely=0.5)
        self.lf.grid_forget()
        self.rf.grid_forget()
        self.f0.place(anchor="center", relx=0.5, rely=0.5)
        self.opts["mf"].window.deiconify()

    def doCallBack(self, *args):
        if args[0][1] == 0:
            if self.grid.cv2.itemcget(args[1], "text"):
                return
            else:
                item = self.doSearch()
                if item is None:
                    return
                if self.grp is None:
                    self.grp = item[1]
                    self.code = item[2]
                else:
                    self.code = item[1]
                self.doCode("Manual")
                return
        if args[0][0] != self.row - 1 or args[0][1] not in (1, 2):
            return
        if self.state == "disable":
            return
        if args[0][1] == 1:
            txt = "Quantity"
        else:
            txt = "Price"
        ent = SimpleDialog(style="RoundedFrame", trans=self.window,
            pad=10, cols=[("a", txt, 11.2, "SD", txt)])
        ent.window.grab_set_global()
        ent.sframe.wait_window()
        if not ent.data:
            return
        if args[0][1] == 1 and not ent.data[0]:
            return
        oqty = self.body[-1][self.bd.index("qty")]
        oprc = self.body[-1][self.bd.index("prc")]
        oinc = self.body[-1][self.bd.index("inc")]
        if args[0][1] == 1:
            nqty = CCD(ent.data[0], "SD", 11.2)
            nprc = CCD(oprc, "SD", 11.2)
        else:
            nqty = CCD(oqty, "SD", 11.2)
            nprc = CCD(ent.data[0], "SD", 11.2)
        ninc = CCD(nqty.work * nprc.work, "SD", 11.2)
        vat = round(
            ninc.work * self.vrte / float(ASD(self.vrte) + ASD(100)), 2)
        nexc = CCD(float(ASD(ninc.work) - ASD(vat)), "SD", 11.2)
        # Remove Old
        totqty = float(ASD(self.totqty) - ASD(oqty))
        totval = float(ASD(self.totval.work) - ASD(oinc))
        # Add New
        self.totqty = float(ASD(totqty) + ASD(nqty.work))
        self.totval = CCD(float(ASD(totval) + ASD(ninc.work)), "SD", 11.2)
        # Update Body
        self.body[-1][self.bd.index("qty")] = nqty.work
        self.body[-1][self.bd.index("prc")] = nprc.work
        self.body[-1][self.bd.index("exc")] = nexc.work
        self.body[-1][self.bd.index("inc")] = ninc.work
        if args[0][1] == 1:
            self.grid._chg_cell(args[1], nqty.disp)
            self.grid._chg_cell(args[1] + 2, nprc.disp)
            self.grid._chg_cell(args[1] + 4, ninc.disp)
        else:
            self.grid._chg_cell(args[1] - 2, nqty.disp)
            self.grid._chg_cell(args[1], nprc.disp)
            self.grid._chg_cell(args[1] + 2, ninc.disp)
        self.items.configure(text="%s" % self.totqty)
        self.values.configure(text="%s" % self.totval.disp)

    def doSearch(self):
        if self.grp is None:
            cols = [("group", "Grp", 3, "NA", "F")]
            col = ["st2_group", "st2_code", "st1_desc"]
            whr = [
                ("st2_cono", "=", self.opts["conum"]),
                ("st2_loc", "=", self.loc)]
            odr = "st2_group, st2_code"
        else:
            cols = []
            col = ["st2_code", "st1_desc"]
            whr = [
                ("st2_cono", "=", self.opts["conum"]),
                ("st2_group", "=", self.grp),
                ("st2_loc", "=", self.loc)]
            odr = "st2_code"
        whr.extend([
            ("st1_cono=st2_cono",),
            ("st1_group=st2_group",),
            ("st1_code=st2_code",)])
        data = self.sql.getRec(tables=["strmf1", "strmf2"], cols=col,
            where=whr, order=odr)
        cols.extend([
            ("code", "Product-Code", 20, "NA", "F"),
            ("desc", "Product-Description", 30, "NA", "Y")])
        sc = SelectChoice(self.window, "Select Item", cols, data,
            fltr=(None, self.window, True, "D.TFrame"))
        return sc.selection

    def doChgState(self, frm, state):
        for chld in frm.winfo_children():
            if "state" in chld.configure():
                chld.configure(state=state)
            self.doChgState(chld, state)
        self.state = state

    def doCash(self):
        try:
            self.f0.place_forget()
        except:
            pass
        if not self.getUserPwd():
            self.f0.place(anchor="center", relx=0.5, rely=0.5)
            return
        self.ttype = "cash"
        self.ptype = None
        self.plev = self.level
        self.doLoadGrps(clear=True)

    def doAccount(self):
        try:
            self.f0.place_forget()
        except:
            pass
        if not self.getUserPwd():
            self.f0.place(anchor="center", relx=0.5, rely=0.5)
            return
        self.chain = 0
        self.acno = ""
        titl = "Debtors Account"
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1")),
            "where": [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_stat", "<>", "X")]}
        fld = (
            (("T",0,0,0),"INA",7,"Account Number","",
                "","Y",self.doAcno,drm,None,None),
            (("T",0,1,0),"ONA",30,"Account Name"),
            (("T",0,2,0),"ONA",30,"Address Line"),
            (("T",0,3,0),"IUI",1,"Price level","",
                0,"N",self.doPdev,None,None,("between", 1, self.levels)))
        but = (("Cancel",None,self.doAccXit,1,None,None),)
        tnd = ((self.doAccEnd, "n"),)
        txt = (self.doAccXit,)
        self.ac = TartanDialog(self.opts["mf"], screen=self.window,
            tops=True, title=titl, eflds=fld, tend=tnd, txit=txt,
            butt=but)
        self.ac.mstFrame.wait_window()
        if self.flag == "E":
            self.ttype = "account"
            self.ptype = None
            self.doLoadGrps(clear=True)
        else:
            self.f0.place(anchor="center", relx=0.5, rely=0.5)

    def doAcno(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", where=[("drm_cono",
            "=", self.opts["conum"]), ("drm_chain", "=", self.chain),
            ("drm_acno", "=", w), ("drm_stat", "<>", "X")], limit=1)
        if not acc:
            return "Invalid Account"
        self.acno = w
        self.name = acc[self.sql.drsmst_col.index("drm_name")]
        self.add1 = acc[self.sql.drsmst_col.index("drm_add1")]
        self.plev = acc[self.sql.drsmst_col.index("drm_plev")]
        if not self.plev:
            self.plev = self.level
        self.ac.loadEntry("T", pag, p+1, data=self.name)
        self.ac.loadEntry("T", pag, p+2, data=self.add1)
        self.ac.loadEntry("T", pag, p+3, data=self.plev)

    def doPdev(self, frt, pag, r, c, p, i, w):
        self.pdev = w

    def doAccRej(self):
        self.ac.focusField("T", 0, 1)

    def doAccEnd(self):
        if not self.acno:
            return
        self.flag = "E"
        self.ac.closeProcess()

    def doAccXit(self):
        self.flag = "X"
        self.ac.closeProcess()

    def getUserPwd(self):
        cf = PwdConfirm(self.opts["mf"], screen=self.window,
            conum=self.opts["conum"], system="INV", code="UserPwd",
            desc="User's Password", user=self.opts["capnm"])
        if cf.flag == "ok":
            return True

    def doDeclare(self):
        self.declare = True
        self.doLogout()

    def doLogout(self):
        self.window.destroy()
        if sys.platform == "win32":
            self.opts["mf"].window.state("normal")
            self.opts["mf"].window.overrideredirect(0)
        else:
            self.opts["mf"].window.attributes("-fullscreen", False)
        self.opts["mf"].closeLoop()

    def doLoadGrps(self, page=0, clear=False):
        try:
            self.itmf.grid_forget()
        except:
            pass
        self.grp = None
        self.page = page
        self.scanner = False
        if self.page == 0:
            self.lf.pack(anchor="nw", side="left")
            self.rf.pack(anchor="nw", side="left")
            self.rf.bind("<Key>", self.doScanner)
            self.rf.focus_set()
            if clear:
                self.doClearDetail()
        groups = self.glist[self.page]
        for num, grp in enumerate(groups):
            self.butts["G"][num][1].configure(state="normal")
            txt = self.doWrap(grp[1])
            self.butts["G"][num][1].setLabel(txt, img=False,
                cmd=(self.doGroup, num))
        for x in range(num + 1, 20):
            self.butts["G"][x][1].configure(state="normal")
            self.butts["G"][x][1].setLabel("")
            self.butts["G"][x][1].configure(state="disabled")
        self.butts["R"][3][1].setLabel("Exit", cmd=self.doGrpExit)
        self.grpf.grid(row=0, column=3, rowspan=5, columnspan=4, sticky="nsew")
        self.opts["mf"].window.update_idletasks()
        self.grppag = True
        self.itmpag = False

    def doClearDetail(self, event=None):
        self.items.configure(text="")
        self.values.configure(text="")
        for x in range(100):
            self.grid._chg_cell(self.grid.rowcol[x][0], "")
            self.grid._chg_cell(self.grid.rowcol[x][1], "")
            self.grid._chg_cell(self.grid.rowcol[x][2], "")
            self.grid._chg_cell(self.grid.rowcol[x][3], "")
        self.body = []
        self.totqty = 0
        self.totval = CCD(0, "SD", 11.2)
        self.totdis = CCD(0, "SD", 11.2)
        self.grid._scroll("Top")
        self.row = 0

    def doGroup(self, args):
        if not self.butts["G"][args][1].cget("text"):
            return
        self.grp = self.grps[args][0]
        self.ilist = []
        count = 0
        for item in self.itms[self.grp]:
            if not count:
                lst = []
            lst.append(item)
            count += 1
            if count == 20:
                self.ilist.append(copy.deepcopy(lst))
                count = 0
        self.ilist.append(copy.deepcopy(lst))
        self.page = 0
        self.doLoadItms()

    def doGrpExit(self):
        if self.body:
            return
        self.lf.pack_forget()
        self.rf.pack_forget()
        self.f0.place(anchor="center", relx=0.5, rely=0.5)

    def doLoadItms(self):
        self.grpf.grid_forget()
        items = self.ilist[self.page]
        for num, itm in enumerate(items):
            self.butts["I"][num][1].configure(state="normal")
            txt = self.doWrap(itm[1])
            self.butts["I"][num][1].setLabel(txt, img=False,
                cmd=(self.doCode, num))
        for x in range(num + 1, 20):
            self.butts["I"][x][1].configure(state="normal")
            self.butts["I"][x][1].setLabel("")
            self.butts["I"][x][1].configure(state="disabled")
        self.butts["R"][3][1].setLabel("Groups", cmd=self.doLoadGrps)
        self.itmf.grid(row=0, column=3, rowspan=5, columnspan=4, sticky="nsew")
        self.grppag = False
        self.itmpag = True

    def doWrap(self, text, chrs=10):
        chrs += text.count(" ")
        if chrs > 12:
            chrs = 12
        text = textwrap.wrap(text, chrs)
        newt = text[0]
        for d in text[1:]:
            newt = "%s\n%s" % (newt, d)
        return newt

    def doScanner(self, event):
        try:
            if event.keysym in ("Return", "KP_Enter"):
                if self.scanner:
                    self.grp = self.scandat[:3]
                    self.code = self.scandat[3:].rstrip()
                    self.scanner = False
                    self.doCode("Manual")
                else:
                    return
            elif not self.scanner:
                self.scanner = True
                self.scandat = event.char
            else:
                self.scandat += event.char
        except:
            return

    def doCode(self, args):
        if args != "Manual":
            if not self.butts["I"][args][1].cget("text"):
                return
            self.code = self.ilist[self.page][args][0]
        strmf1 = self.sql.getRec("strmf1", where=[("st1_cono",
            "=", self.opts["conum"]), ("st1_group", "=", self.grp),
            ("st1_code", "=", self.code)], limit=1)
        if not strmf1:
            self.window.bell()
            return
        desc = strmf1[self.sql.strmf1_col.index("st1_desc")]
        qty = CCD(1, "SD", 11.2)
        self.vatcod = strmf1[self.sql.strmf1_col.index("st1_vatcode")]
        # Get VAT Rate
        self.vrte = getVatRate(self.sql, self.opts["conum"], self.vatcod,
            self.trdt)
        self.totqty = float(ASD(self.totqty) + ASD(qty.work))
        self.gtype = strmf1[self.sql.strmf1_col.index("st1_type")]
        if self.gtype == "R":
            # Recipe
            recs = self.sql.getRec("strrcp", where=[("srr_cono",
                "=", self.opts["conum"]), ("srr_group", "=", self.grp),
                ("srr_code", "=", self.code), ("srr_loc", "=", self.loc)])
            if not recs:
                self.window.bell()
                return
            incl = 0
            for rec in recs:
                st1 = self.sql.getRec("strmf1", cols=["st1_type"],
                    where=[("st1_cono", "=", rec[0]), ("st1_group",
                    "=", rec[4]), ("st1_code", "=", rec[5])], limit=1)
                if st1[0] == "X":
                    self.window.bell()
                    return
                pr, ec, ic = self.doCalSell(rec[4], rec[5], rec[6])
                incl = float(ASD(incl) + ASD(ic.work))
            prc = CCD(incl, "UD", 10.2)
            incl = CCD(qty.work * prc.work, "SD", 11.2)
            vat = round(
                incl.work * self.vrte / float(ASD(self.vrte) + ASD(100)), 2)
            excl = CCD(float(ASD(incl.work) - ASD(vat)), "SD", 11.2)
        else:
            prc, excl, incl = self.doCalSell(self.grp, self.code, qty.work)
        if not prc.work:
            cf = PwdConfirm(self.opts["mf"], screen=self.opts["mf"].window,
                conum=self.opts["conum"], system="INV", code="NoCharge")
            if cf.flag == "no":
                return
        self.totval = CCD(float(ASD(self.totval.work) +
            ASD(incl.work)), "SD", 11.2)
        self.grid._chg_cell(self.grid.rowcol[self.row][0], desc)
        self.grid._chg_cell(self.grid.rowcol[self.row][1], qty.disp)
        self.grid._chg_cell(self.grid.rowcol[self.row][2], prc.disp)
        self.grid._chg_cell(self.grid.rowcol[self.row][3], incl.disp)
        y2 = self.grid.cv2.bbox(self.grid.rowcol[self.row][0])[3]
        if y2 + self.grid.ch > self.fb.winfo_height():
            self.grid._scroll("Down")
        self.items.configure(text="%s" % self.totqty)
        self.values.configure(text="%s" % self.totval.disp)
        self.body.append([self.row, self.grp, self.code, self.gtype, desc,
            qty.work, prc.work, excl.work, incl.work, 0, self.vatcod])
        self.row += 1
        self.window.bell()

    def doCalSell(self, grp, cod, qty):
        sprc = getSell(self.sql, self.opts["conum"], grp, cod, self.loc,
            self.plev)
        sprc = round(sprc * (float(ASD(100.0) + ASD(self.vrte))) / 100.0, 2)
        sprc = CCD(sprc, "UD", 10.2)
        incl = CCD(qty * sprc.work, "SD", 11.2)
        vat = round(incl.work * self.vrte / float(ASD(self.vrte) + ASD(100)), 2)
        excl = CCD(float(ASD(incl.work) - ASD(vat)), "SD", 11.2)
        return sprc, excl, incl

    def doRefund(self):
        if not self.totval.work:
            return
        cf = PwdConfirm(self.opts["mf"], screen=self.opts["mf"].window,
            conum=self.opts["conum"], system="INV", code="Refund")
        if cf.flag == "no":
            return
        self.refund = True
        self.clearPayments()
        self.doPayScreen()

    def doVoid(self):
        self.doClearDetail()
        self.doGrpExit()

    def doPayment(self, event=None):
        if not self.totval.work:
            return
        self.clearPayments()
        self.ptype = None
        self.refund = False
        self.vpay = CCD(0, "SD", 11.2)
        self.tpay = CCD(0, "SD", 11.2)
        self.doPayScreen()

    def doPayScreen(self):
        # Clear Screen
        self.cxit = True
        self.lf.pack_forget()
        self.rf.pack_forget()
        # Draw Payment Screen
        self.payf = MyFrame(self.window, style="RoundedFrame", padding=10)
        topF = MyFrame(self.payf, relief="ridge", style="D.TFrame")
        for x in range(5):
            topF.grid_rowconfigure(x, weight=1)
        topF.grid_columnconfigure(0, weight=1)
        topF.grid_columnconfigure(1, weight=1)
        topF.pack(side="left", expand="yes", fill="both")
        self.style.configure("lab.TLabel", font=("Helvetica", self.fsz, "bold"),
            padding=10, relief="ridge")
        efont = ("Courier", self.fsz, "bold")
        lab = MyLabel(topF, text="Due Amount", color=False,
            style="lab.TLabel")
        lab.grid(column=0, row=0, sticky="nsew")
        self.due = ttk.Entry(topF, width=12, justify="right", font=efont)
        self.due.insert(0, self.totval.disp)
        self.due.configure(state="disabled")
        self.due.grid(column=1, row=0, sticky="nsew")
        lab = MyLabel(topF, text="Discount Percent", color=False,
            style="lab.TLabel")
        lab.grid(column=0, row=1, sticky="nsew")
        self.dis = ttk.Entry(topF, width=12, justify="right", font=efont)
        self.dis.configure(state="disabled")
        self.dis.grid(column=1, row=1, sticky="nsew")
        lab = MyLabel(topF, text="Voucher Amount", color=False,
            style="lab.TLabel")
        lab.grid(column=0, row=2, sticky="nsew")
        self.vou = ttk.Entry(topF, width=12, justify="right", font=efont)
        self.vou.configure(state="disabled")
        self.vou.grid(column=1, row=2, sticky="nsew")
        lab = MyLabel(topF, text="Paid Amount", color=False,
            style="lab.TLabel")
        lab.grid(column=0, row=3, sticky="nsew")
        self.pay = ttk.Entry(topF, width=12, justify="right", font=efont)
        self.pay.configure(state="disabled")
        self.pay.grid(column=1, row=3, sticky="nsew")
        lab = MyLabel(topF, text="Change", color=False,
            style="lab.TLabel")
        lab.grid(column=0, row=4, sticky="nsew")
        self.chg = ttk.Entry(topF, width=12, justify="right", font=efont)
        self.chg.configure(state="disabled")
        self.chg.grid(column=1, row=4, sticky="nsew")
        keyF = MyFrame(self.payf, style="D.TFrame", bg="white")
        self.window.update_idletasks()
        bh = int(self.window.winfo_reqheight() / 6)
        for x in range(4):
            keyF.grid_columnconfigure(x, minsize=bh, weight=1)
        for x in range(5):
            keyF.grid_rowconfigure(x, minsize=bh, weight=1)
        keyF.pack(side="left", expand="yes", fill="both")
        self.doButton(keyF, "Cash", (self.doPtype, "cash"), rc=(0, 0))
        self.doButton(keyF, "C/Card", self.doGetCard, rc=(1, 0))
        self.doButton(keyF, "Voucher", (self.doPtype, "voucher"), rc=(2, 0))
        self.doButton(keyF, "Discount", (self.doPtype, "discount"), rc=(3, 0))
        self.doButton(keyF, "Exit", self.doPayExit, rc=(4, 0))
        # Draw Numeric Keypad
        for row, key in enumerate(("123", "456", "789", "d0.")):
            for col, char in enumerate(key):
                if char == "d":
                    char = "00"
                self.doButton(keyF, char, (self.doEntry, char), False,
                    "P", (row, col + 1))
        self.doButton(keyF, "Clear", self.doClear, rc=(4, 1))
        self.doButton(keyF, "Enter", self.doCalc, rc=(4, 2, 2))
        self.payf.pack(fill="both", expand="yes")
        self.window.update_idletasks()
        self.payf.wait_window()
        self.payf.destroy()
        if self.cxit:
            # Update Tables
            self.doUpdateTables()
            ok = "yes"
            if self.prt == "N":
                ok = "no"
            elif self.prt == "A":
                ok = askQuestion(self.window, "Print",
                    "Print Slip?", default="no")
            if ok == "yes":
                self.doPrintDoc()
            if self.ttype == "cash":
                if self.ocd and self.prtr:
                    # Open the Cash Drawer
                    self.prtr._raw(self.ocd)
                if self.refund:
                    pay = CCD(0, "SD", 11.2)
                    chg = self.tpay
                else:
                    pay = self.tpay
                    chg = self.cchg
                if chg.work:
                    showInfo(self.window, "Till",
                        """Cash          %s
Change        %s""" % (pay.disp, chg.disp))
            self.doClearDetail()
            self.doGrpExit()
        else:
            self.doLoadGrps()

    def doButton(self, frm, txt, cmd, img=True, stl="L", rc=(0, 0), var=None):
        if type(cmd) == tuple:
            cmd = functools.partial(self.doCommand, cmd)
        f = MyFrame(frm, padding=10, relief="raised", style="RoundedFrame")
        b = MyButton(f, text=txt, cmd=cmd, img=img, padding=10,
            style="%s.TButton" % stl, takefocus=False)
        if var:
            b.configure(textvariable=var)
        b.pack(fill="both", expand="yes")
        if len(rc) == 3:
            span = rc[2]
        else:
            span = 1
        f.grid(row=rc[0], column=rc[1], columnspan=span, sticky="nsew")
        if stl not in self.butts:
            self.butts[stl] = []
        self.butts[stl].append((f, b))

    def doCommand(self, cmd):
        if type(cmd) in (list, tuple):
            cmd[0](cmd[1])
        else:
            cmd()

    def doPtype(self, ptype):
        if self.ttype == "account" and ptype == "cash":
            return
        if ptype == "voucher" and self.vpay.work:
            return
        if ptype == "discount" and self.drate.work:
            return
        self.ptype = ptype
        if self.ptype == "cash" and self.refund:
            self.due.configure(state="normal")
            self.tpay = CCD(self.due.get(), "SD", 11.2)
            self.due.configure(state="disabled")
            self.doEndPayment()

    def doGetCard(self):
        # Swipe credit card
        if self.ttype == "account":
            return
        self.cpay = CCD(float(ASD(self.totval.work) -
            ASD(self.vpay.work)), "SD", 11.2)
        self.doEndPayment()

    def doEntry(self, char, event=None):
        if self.ptype not in ("cash", "discount", "voucher"):
            return
        self.doPayWidgets("normal")
        if self.ptype == "discount":
            amt = self.dis.get() + char
            self.dis.delete(0, "end")
            self.dis.insert(0, amt)
        elif self.ptype == "voucher":
            amt = self.vou.get() + char
            self.vou.delete(0, "end")
            self.vou.insert(0, amt)
        else:
            amt = self.pay.get() + char
            self.pay.delete(0, "end")
            self.pay.insert(0, amt)
        self.doPayWidgets("disabled")

    def doPayExit(self, event=None):
        try:
            self.payf.destroy()
        except:
            pass
        self.cxit = False

    def doClear(self, event=None):
        self.doPayWidgets("normal")
        due = CCD(self.due.get(), "SD", 11.2).work
        dis = self.totdis.work
        if dis:
            self.body = copyList(self.oldbody)
        vou = CCD(self.vou.get(), "SD", 11.2).work
        self.totval = CCD(float(ASD(due) + ASD(dis) + ASD(vou)), "SD", 11.2)
        self.totdis = CCD(0, "SD", 11.2)
        self.due.delete(0, "end")
        self.due.insert(0, self.totval.disp)
        self.dis.delete(0, "end")
        self.vou.delete(0, "end")
        self.pay.delete(0, "end")
        self.chg.delete(0, "end")
        self.doPayWidgets("disabled")
        self.clearPayments()

    def clearPayments(self):
        self.apay = CCD(0, "SD", 11.2)
        self.cpay = CCD(0, "SD", 11.2)
        self.vpay = CCD(0, "SD", 11.2)
        self.tpay = CCD(0, "SD", 11.2)
        self.cchg = CCD(0, "SD", 11.2)
        self.drate = CCD(0, "UD", 6.2)

    def doCalc(self, event=None):
        if self.ttype == "account" and self.ptype is None:
            self.apay = CCD(self.due.get(), "SD", 11.2)
            self.doEndPayment()
        elif self.ptype not in ("cash", "discount", "voucher"):
            return
        elif self.ptype == "discount":
            self.dis.configure(state="normal")
            self.drate = CCD(self.dis.get(), "UD", 6.2)
            self.dis.delete(0, "end")
            self.dis.insert(0, "%s%s" % (self.drate.disp, "%"))
            self.dis.configure(state="disabled")
        elif self.ptype == "voucher":
            self.vou.configure(state="normal")
            self.vpay = CCD(self.vou.get(), "SD", 11.2)
            self.dis.configure(state="disabled")
        else:
            # Check Change
            self.pay.configure(state="normal")
            self.tpay = CCD(self.pay.get(), "SD", 11.2)
            paid = float(ASD(self.vpay.work) + ASD(self.tpay.work))
            cchg = float(ASD(paid) - ASD(self.totval.work))
            self.cchg = CCD(cchg, "SD", 11.2)
            if self.cchg.work < 0:
                self.pay.delete(0, "end")
                self.pay.insert(0, "ERROR")
                self.pay.configure(state="disabled")
                return
            self.pay.configure(state="disabled")
        self.doEndPayment()

    def doEndPayment(self):
        self.doPayWidgets("normal")
        if self.ptype == "discount":
            self.oldbody = copyList(self.body)
            self.body = []
            totval = 0
            totdis = 0
            for lin in self.oldbody:
                newl = copyList(lin)
                # Apply Discount
                exd = round(newl[self.bd.index("exc")] *
                    self.drate.work / 100.0, 2)
                ind = round(newl[self.bd.index("inc")] *
                    self.drate.work / 100.0, 2)
                newl[self.bd.index("exc")] = float(
                    ASD(newl[self.bd.index("exc")]) - ASD(exd))
                newl[self.bd.index("inc")] = float(
                    ASD(newl[self.bd.index("inc")]) - ASD(ind))
                newl[self.bd.index("rte")] = self.drate.work
                totval = float(ASD(totval) + ASD(newl[self.bd.index("inc")]))
                totdis = float(ASD(totdis) + ASD(ind))
                self.body.append(newl)
            self.totval = CCD(totval, "SD", 11.2)
            self.totdis = CCD(totdis, "SD", 11.2)
            self.due.delete(0, "end")
            self.due.insert(0, self.totval.disp)
            due = CCD(float(ASD(self.totval.work) - ASD(self.vpay.work)),
                "SD", 11.2)
            self.due.delete(0, "end")
            self.due.insert(0, due.disp)
            self.payf.update_idletasks()
            self.ptype = None
            self.doPayWidgets("disabled")
            return
        elif self.ptype == "voucher":
            self.vou.delete(0, "end")
            self.vou.insert(0, self.vpay.disp)
            due = CCD(float(ASD(self.totval.work) -
                ASD(self.vpay.work)), "SD", 11.2)
            self.due.delete(0, "end")
            self.due.insert(0, due.disp)
            self.payf.update_idletasks()
            if due.work:
                self.ptype = None
                self.doPayWidgets("disabled")
                return
        elif self.ptype == "cash":
            self.pay.delete(0, "end")
            self.pay.insert(0, self.tpay.disp)
            self.chg.insert(0, self.cchg.disp)
            self.payf.update_idletasks()
        self.payf.destroy()

    def doPayWidgets(self, state):
        self.due.configure(state=state)
        self.dis.configure(state=state)
        self.vou.configure(state=state)
        self.pay.configure(state=state)
        self.chg.configure(state=state)

    def doUpdateTables(self):
        # Get Next Reference Number
        acc = self.sql.getRec("postrn", cols=["max(pst_docno)"],
            where=[("pst_cono", "=", self.opts["conum"]), ("pst_host",
            "=", self.host)], limit=1)
        if acc:
            try:
                auto = int(acc[0][1:]) + 1
            except:
                auto = 1
        else:
            auto = 1
        self.ref1 = "P%08d" % auto
        ref2 = ""
        # Check Sales Accounts
        if self.ttype == "cash":
            self.chain = 0
            self.acno = "CASHSLS"
            self.name = "POS Sale"
            drm = self.sql.getRec("drsmst", where=[("drm_cono",
                "=", self.opts["conum"]), ("drm_chain", "=", self.chain),
                ("drm_acno", "=", self.acno)], limit=1)
            if not drm:
                self.sql.insRec("drsmst", data=[self.opts["conum"], self.chain,
                    self.acno, self.name, "", "", "", "", "", "", "", "", "",
                    "", "", "", 0, 0, "", "", "", "", "", 0, 0, 0, 0, 0, 0, "",
                    0, 0, ""])
        # Create POS Master Record
        data = [self.opts["conum"], self.host, self.ref1, self.trdt,
            self.chain, self.acno]
        self.sql.insRec("posmst", data=data)
        # Create POS Detail Records and update tables
        totvat = 0
        for row, grp, cod, gtp, des, qty, prc, exc, inc, rte, vcd in self.body:
            # Accumulate total vat
            vat = float(ASD(inc) - ASD(exc))
            totvat = float(ASD(totvat) + ASD(vat))
            # Create POS Transaction Record
            if self.refund:
                ttyp = "R"
                tqty = float(ASD(0) - ASD(qty))
                texc = float(ASD(0) - ASD(exc))
                tinc = float(ASD(0) - ASD(inc))
                tvat = float(ASD(0) - ASD(vat))
            else:
                ttyp = "I"
                tqty = qty
                texc = exc
                tinc = inc
                tvat = vat
            data = [self.opts["conum"], self.host, ttyp, self.ref1, row,
                grp, cod, self.loc, des, tqty, prc, texc, tinc, rte, vcd,
                self.vrte, self.opts["capnm"], self.trdt, 0]
            self.sql.insRec("postrn", data=data)
            # Get Cost Price
            if gtp == "R":
                # Recipe - Create posrcp records
                cst = 0
                recs = self.sql.getRec("strrcp", where=[("srr_cono",
                    "=", self.opts["conum"]), ("srr_group", "=", grp),
                    ("srr_code", "=", cod), ("srr_loc", "=", self.loc)])
                for rec in recs:
                    icst = getCost(self.sql, self.opts["conum"], rec[4],
                        rec[5], loc=self.loc, qty=1, ind="I")
                    data = [self.opts["conum"], self.host, self.ref1, row,
                        rec[4], rec[5], rec[6], icst, 0]
                    self.sql.insRec("posrcp", data=data)
                    rqty = round(qty * rec[6], 2)
                    rcst = round(rqty * icst, 2)
                    cst = float(ASD(cst) + ASD(rcst))
                    if self.refund:
                        rtyp = 5
                    else:
                        rtyp = 6
                        rqty = float(ASD(0) - ASD(rqty))
                        rcst = float(ASD(0) - ASD(rcst))
                    data = [rec[0], rec[4], rec[5], rec[3], self.trdt,
                        rtyp, self.ref1, self.batch, ref2, rqty, rcst,
                        0, self.curdt, self.name, 0, self.acno, self.repno,
                        "INV", 0, "", self.opts["capnm"], self.trdt, 0]
                    self.sql.insRec("strtrn", data=data)
                if self.refund:
                    rtyp = 6
                else:
                    rtyp = 5
                data = [self.opts["conum"], grp, cod, self.loc, self.trdt,
                    rtyp, self.ref1, self.batch, ref2, qty, cst, 0,
                    self.curdt, self.name, 0, self.acno, self.repno, "INV",
                    0, "", self.opts["capnm"], self.trdt, 0]
                self.sql.insRec("strtrn", data=data)
            else:
                icost, cst = getCost(self.sql, self.opts["conum"],
                    grp, cod, loc=self.loc, qty=qty, tot=True)
            # Create/Update Stores Transaction Record
            if self.refund:
                tqty = qty
                tcst = cst
                texc = exc
                tvat = vat
            else:
                tqty = float(ASD(0) - ASD(qty))
                tcst = float(ASD(0) - ASD(cst))
                texc = float(ASD(0) - ASD(exc))
                tvat = float(ASD(0) - ASD(vat))
            data = [self.opts["conum"], grp, cod, self.loc, self.trdt, 8,
                self.ref1, self.batch, ref2, tqty, tcst, texc, self.curdt,
                self.name, 0, self.acno, self.repno, "INV", 0, "",
                self.opts["capnm"], self.trdt, 0]
            self.sql.insRec("strtrn", data=data)
            # If Integrated Create GL Transaction (Sales & Cost of Sales)
            if self.stgl == "Y":
                col = ["glt_tramt", "glt_taxamt", "glt_seq"]
                # Stock on Hand Control
                if tcst:
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", self.soh), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt),
                        ("glt_type", "=", 1), ("glt_refno", "=", self.ref1),
                        ("glt_batch", "=", self.batch), ("glt_desc", "=",
                        self.name)], limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(tcst))
                        self.sql.updRec("gentrn", cols=["glt_tramt"],
                            data=[at1], where=[("glt_seq", "=", rec[2])])
                    else:
                        data = (self.opts["conum"], self.soh, self.curdt,
                            self.trdt, 1, self.ref1, self.batch, tcst, 0,
                            self.name, "", "", 0, self.opts["capnm"],
                            self.trdt, 0)
                        self.sql.insRec("gentrn", data=data)
                # Sales and COS Accounts
                ac1 = self.sql.getRec("strgrp", cols=["gpm_sales",
                    "gpm_costs"], where=[("gpm_cono", "=", self.opts["conum"]),
                    ("gpm_group", "=", grp)], limit=1)
                ac2 = self.sql.getRec("strmf1", cols=["st1_sls",
                    "st1_cos"], where=[("st1_cono", "=", self.opts["conum"]),
                    ("st1_group", "=", grp), ("st1_code", "=", cod)], limit=1)
                if ac2[0]:
                    ac1[0] = ac2[0]
                if ac2[1]:
                    ac1[1] = ac2[1]
                # Sales Account
                if texc or tvat:
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", ac1[0]), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt),
                        ("glt_type", "=", 1), ("glt_refno", "=", self.ref1),
                        ("glt_batch", "=", self.batch), ("glt_desc", "=",
                        self.name)], limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(texc))
                        at2 = float(ASD(rec[1]) + ASD(tvat))
                        self.sql.updRec("gentrn", cols=["glt_tramt",
                            "glt_taxamt"], data=[at1, at2], where=[("glt_seq",
                            "=", rec[2])])
                    else:
                        data = (self.opts["conum"], ac1[0], self.curdt,
                            self.trdt, 1, self.ref1, self.batch, texc, tvat,
                            self.name, vcd, "", 0, self.opts["capnm"],
                            self.trdt, 0)
                        self.sql.insRec("gentrn", data=data)
                # Cost of Sales Account
                if cst:
                    if self.refund:
                        cst = float(ASD(0) - ASD(cst))
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", ac1[1]), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt),
                        ("glt_type", "=", 1), ("glt_refno", "=", self.ref1),
                        ("glt_batch", "=", self.batch), ("glt_desc", "=",
                        self.name)], limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(cst))
                        self.sql.updRec("gentrn", cols=["glt_tramt"],
                            data=[at1], where=[("glt_seq", "=", rec[2])])
                    else:
                        data = (self.opts["conum"], ac1[1], self.curdt,
                            self.trdt, 1, self.ref1, self.batch, cst, 0,
                            self.name, "", "", 0, self.opts["capnm"],
                            self.trdt, 0)
                        self.sql.insRec("gentrn", data=data)
            # Create VAT Transaction (ctlvtf)
            if self.refund:
                rtn = 4
            else:
                rtn = 1
            whr = [("vtt_cono", "=", self.opts["conum"]), ("vtt_code", "=",
                vcd), ("vtt_vtyp", "=", "O"), ("vtt_curdt", "=", self.curdt),
                ("vtt_styp", "=", "D"), ("vtt_ttyp", "=", rtn), ("vtt_batch",
                "=", self.batch), ("vtt_refno", "=", self.ref1), ("vtt_refdt",
                "=", self.trdt), ("vtt_acno", "=", self.acno), ("vtt_desc", "=",
                self.name)]
            rec = self.sql.getRec("ctlvtf", cols=["vtt_exc", "vtt_tax"],
                where=whr, limit=1)
            if rec:
                at1 = float(ASD(rec[0]) + ASD(texc))
                at2 = float(ASD(rec[1]) + ASD(tvat))
                self.sql.updRec("ctlvtf", cols=["vtt_exc", "vtt_tax"],
                    data=[at1, at2], where=whr)
            else:
                self.sql.insRec("ctlvtf", data=[self.opts["conum"], vcd, "O",
                    self.curdt, "D", rtn, self.batch, self.ref1, self.trdt,
                    self.acno, self.name, texc, tvat, 0, self.opts["capnm"],
                    self.trdt, 0])
        self.totvat = CCD(totvat, "SD", 11.2)
        # Create POS Transactions and if Integrated Create GL Transactions
        cash = float(ASD(self.tpay.work) - ASD(self.cchg.work))
        if self.refund:
            desc = "POS Refund"
            apay = float(ASD(0) - ASD(self.apay.work))
            cpay = float(ASD(0) - ASD(self.cpay.work))
            vpay = float(ASD(0) - ASD(self.vpay.work))
            tvat = float(ASD(0) - ASD(self.totvat.work))
            tpay = float(ASD(0) - ASD(cash))
        else:
            desc = "POS Sale"
            apay = self.apay.work
            cpay = self.cpay.work
            vpay = self.vpay.work
            tvat = self.totvat.work
            tpay = cash
        if apay:
            data = [self.opts["conum"], self.host, "A", self.ref1, 0,
                "", "", "", self.name, 0, 0, 0, apay, 0, "", 0,
                self.opts["capnm"], self.trdt, 0]
            self.sql.insRec("postrn", data=data)
            # Create Debtors Transaction
            if self.refund:
                rtn = 4
                AgeAll(self.opts["mf"], system="drs", agetyp="O",
                    agekey=[self.opts["conum"], self.chain, self.acno,
                    rtn, self.ref1, self.curdt, apay, 0.0])
            else:
                rtn = 1
                AgeAll(self.opts["mf"], system="drs", agetyp="C",
                    agekey=[self.opts["conum"], self.chain, self.acno,
                    rtn, self.ref1, self.curdt, apay, 0.0])
            ref2 = ""
            data = [self.opts["conum"], 0, self.acno, rtn, self.ref1,
                self.batch, self.trdt, ref2, apay, tvat, self.curdt, desc,
                vcd, "", self.opts["capnm"], self.trdt, 0]
            self.sql.insRec("drstrn", data=data)
            if self.drgl == "Y":
                # Debtors Control
                data = (self.opts["conum"], self.dctl, self.curdt, self.trdt,
                    1, self.ref1, self.batch, apay, 0, desc, "", "", 0,
                    self.opts["capnm"], self.trdt, 0)
                self.sql.insRec("gentrn", data=data)
        if vat and (self.stgl == "Y" or self.drgl == "Y"):
            # VAT Control
            vat = float(ASD(0) - ASD(tvat))
            data = (self.opts["conum"], self.vctl, self.curdt, self.trdt, 1,
                self.ref1, self.batch, vat, 0, desc, "", "", 0,
                self.opts["capnm"], self.trdt, 0)
            self.sql.insRec("gentrn", data=data)
        if cpay:
            des = "Credit Card"
            data = [self.opts["conum"], self.host, "C", self.ref1, 0,
                "", "", "", des, 0, 0, 0, cpay, 0, "", 0, self.opts["capnm"],
                self.trdt, 0]
            self.sql.insRec("postrn", data=data)
            if cpay and (self.stgl == "Y" or self.drgl == "Y"):
                data = (self.opts["conum"], self.card, self.curdt, self.trdt,
                    1, self.ref1, self.batch, cpay, 0, desc, "", "", 0,
                    self.opts["capnm"], self.trdt, 0)
                self.sql.insRec("gentrn", data=data)
        if tpay:
            des = "Cash"
            data = [self.opts["conum"], self.host, "T", self.ref1, 0,
                "", "", "", des, 0, 0, 0, tpay, 0, "", 0, self.opts["capnm"],
                self.trdt, 0]
            self.sql.insRec("postrn", data=data)
            if self.stgl == "Y" or self.drgl == "Y":
                data = (self.opts["conum"], self.cash, self.curdt, self.trdt,
                    1, self.ref1, self.batch, tpay, 0, desc, "", "", 0,
                    self.opts["capnm"], self.trdt, 0)
                self.sql.insRec("gentrn", data=data)
        if vpay:
            des = "Voucher"
            data = [self.opts["conum"], self.host, "V", self.ref1, 0,
                "", "", "", des, 0, 0, 0, vpay, 0, "", 0, self.opts["capnm"],
                self.trdt, 0]
            self.sql.insRec("postrn", data=data)
            if self.stgl == "Y" or self.drgl == "Y":
                data = (self.opts["conum"], self.vchr, self.curdt, self.trdt,
                    1, self.ref1, self.batch, vpay, 0, desc, "", "", 0,
                    self.opts["capnm"], self.trdt, 0)
                self.sql.insRec("gentrn", data=data)
        self.opts["mf"].dbm.commitDbase()

    def doLeft(self):
        if not self.page:
            return
        if self.grppag:
            self.page -= 1
            self.doLoadGrps(self.page)
        else:
            self.page -= 1
            self.doLoadItms()

    def doRight(self):
        if self.grppag:
            if self.page == len(self.glist) - 1:
                return
            self.page += 1
            self.doLoadGrps(self.page)
        else:
            if self.page == len(self.ilist) - 1:
                return
            self.page += 1
            self.doLoadItms()

    def doUndo(self):
        if not self.body:
            return
        item = self.body.pop()
        self.totqty = float(ASD(self.totqty) - ASD(item[5]))
        val = float(ASD(self.totval.work) - ASD(item[8]))
        self.totval = CCD(val, "SD", 11.2)
        self.items.configure(text="%s" % self.totqty)
        self.values.configure(text="%s" % self.totval.disp)
        self.grid._chg_cell(self.grid.rowcol[item[0]][0], "")
        self.grid._chg_cell(self.grid.rowcol[item[0]][1], "")
        self.grid._chg_cell(self.grid.rowcol[item[0]][2], "")
        self.grid._chg_cell(self.grid.rowcol[item[0]][3], "")
        y2 = self.grid.cv2.bbox(self.grid.rowcol[self.row][0])[3]
        if y2 + self.grid.ch > self.fb.winfo_height():
            self.grid._scroll("Up")
        self.row = len(self.body)

    def doPrintDoc(self):
        pmc = self.sql.posmst_col
        ptc = self.sql.postrn_col
        dmc = self.sql.drsmst_col
        self.docno = CCD(self.ref1, "Na", 9.0)
        # posmst
        psm = self.sql.getRec("posmst", where=[("psm_cono", "=",
            self.opts["conum"]), ("psm_host", "=", self.host),
            ("psm_docno", "=", self.docno.work)], limit=1)
        pst = self.sql.getRec("postrn", where=[("pst_cono", "=",
            self.opts["conum"]), ("pst_host", "=", self.host),
            ("pst_docno", "=", self.docno.work), ("pst_dtype", "in",
            ("I", "R"))], order="pst_rowno")
        if not psm or not pst:
            print("NO RECS", self.host, self.docno.work)
            return
        # Template variables
        tplmst = self.sql.getRec("tplmst", where=[("tpm_tname",
            "=", self.tpl)], limit=1)
        if not tplmst:
            showError(None, "Template Error", "Invalid Template Name")
            return
        tpldet = self.sql.getRec("tpldet", where=[("tpd_tname",
            "=", self.tpl)], order="tpd_detseq")
        seq = 0
        lines = 0
        chk = copyList(tpldet)
        col = self.sql.tpldet_col
        for det in chk:
            if det[col.index("tpd_mrgcod")] == "account_details":
                if self.dtp == "S" and self.acno == "CASHSLS":
                    y1 = det[col.index("tpd_y1")]
                    n1 = chk[seq + 1][col.index("tpd_y1")]
                    lines = n1 - y1
                    del tpldet[seq]
                    continue
            if self.dtp == "S":
                if det[col.index("tpd_place")] == "B":
                    tpldet[seq][col.index("tpd_repeat")] = len(pst)
                if lines:
                    if det[col.index("tpd_y1")]:
                        tpldet[seq][col.index("tpd_y1")] -= lines
                        tpldet[seq][col.index("tpd_y2")] -= lines
                    if det[col.index("tpd_mrg_y1")]:
                        tpldet[seq][col.index("tpd_mrg_y1")] -= lines
                        tpldet[seq][col.index("tpd_mrg_y2")] -= lines
            seq += 1
        self.form = DrawForm(self.opts["mf"].dbm, [tplmst, tpldet])
        txt = self.form.sql.tpldet_col.index("tpd_text")
        tdc = self.form.sql.tpldet_col
        self.doLoadStatic()
        self.form.doNewDetail()
        for fld in pmc:
            if fld in self.form.tptp:
                self.form.tptp[fld][1] = psm[pmc.index(fld)]
        # drsmst
        chn = psm[pmc.index("psm_chain")]
        acc = psm[pmc.index("psm_acno")]
        drm = self.sql.getRec("drsmst", where=[("drm_cono",
            "=", self.opts["conum"]), ("drm_chain", "=", chn),
            ("drm_acno", "=", acc)], limit=1)
        for fld in dmc:
            if fld in self.form.tptp:
                d = "%s_C00" % fld
                self.form.newdic[d][txt] = drm[dmc.index(fld)]
        self.form.account_details("drm", dmc, drm, 0)
        self.form.document_date(psm[pmc.index("psm_date")])
        self.doHeader(tdc)
        self.doBody(ptc, pst, tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        pfx = "POSInv%s" % self.docno.work
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, pfx, ext="pdf")
        self.form.output(pdfnam, "F")
        if self.dtp == "S":
            self.form.changeSize(pdfnam)
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            repprt=("N", "P", self.prn))
        if self.dtp == "S" and self.pcd and self.prtr:
            # Cut Paper
            self.prtr._raw(self.pcd)

    def doHeader(self, tdc):
        self.form.add_page()
        for key in self.form.newkey:
            line = self.form.newdic[key]
            if line[tdc.index("tpd_place")] != "A":
                continue
            nl = copyList(line)
            if nl[tdc.index("tpd_type")] == "T" and \
                        nl[tdc.index("tpd_ttyp")] == "H":
                mrgcod = nl[tdc.index("tpd_mrgcod")]
                if mrgcod and mrgcod == "deliver_to" and not self.deliver:
                    continue
                if mrgcod and self.form.tptp[mrgcod][0][1][0] == "S":
                    txt = nl[tdc.index("tpd_text")]
                    nl[tdc.index("tpd_text")] = "%s " % txt
            elif nl[tdc.index("tpd_type")] == "C":
                mrgcod = nl[tdc.index("tpd_mrgcod")]
                nl[tdc.index("tpd_text")] = self.doGetData(mrgcod)
            if key == "document_type_C00":
                if self.ttype == "account":
                    if self.refund:
                        nl[tdc.index("tpd_text")] = "Credit Note"
                    else:
                        nl[tdc.index("tpd_text")] = "Invoice"
                elif self.refund:
                    nl[tdc.index("tpd_text")] = "Cash Refund"
                else:
                    nl[tdc.index("tpd_text")] = "Cash Sale"
                self.form.doDrawDetail(nl, fmat=False)
            else:
                self.form.doDrawDetail(nl)
        return 0

    def doBody(self, ptc, pst, tdc):
        for count, item in enumerate(pst):
            ldic = {}
            for cod in self.form.body:
                ldic[cod] = CCD(item[ptc.index(cod)],
                    self.form.tptp[cod][0][1],
                    self.form.tptp[cod][0][2])
            for code in self.form.body:
                seq = "%s_C%02i" % (code, count)
                data = ldic[code].work
                self.form.newdic[seq][tdc.index("tpd_text")] = data
                self.form.doDrawDetail(self.form.newdic[seq])
        if self.dtp == "I":
            for x in range(count, self.form.maxlines):
                for cod in self.form.body:
                    seq = "%s_C%02i" % (cod, x)
                    self.form.newdic[seq][tdc.index("tpd_text")] = "BLANK"
                    self.form.doDrawDetail(self.form.newdic[seq])
        cash = float(ASD(self.tpay.work) - ASD(self.cchg.work))
        if self.refund:
            self.total_tax = float(ASD(0) - ASD(self.totvat.work))
            self.total_value = float(ASD(0) - ASD(self.totval.work))
            self.total_vouchers = float(ASD(0) - ASD(self.vpay.work))
            self.total_discount = float(ASD(0) - ASD(self.totdis.work))
            self.total_card = float(ASD(0) - ASD(self.cpay.work))
            self.total_cred = float(ASD(0) - ASD(self.apay.work))
            self.total_cash = float(ASD(0) - ASD(cash))
        else:
            self.total_tax = self.totvat.work
            self.total_value = self.totval.work
            self.total_vouchers = self.vpay.work
            self.total_discount = self.totdis.work
            self.total_card = self.cpay.work
            self.total_cred = self.apay.work
            self.total_cash = cash

    def doTotal(self, tdc):
        lasty = 0
        for c in self.form.total:
            tline = None
            if c in self.form.newdic:
                tline = self.form.newdic[c]
            else:
                t = "%s_T00" % c
                if t in self.form.newdic:
                    tline = self.form.newdic[t]
            if self.dtp == "I":
                if tline:
                    self.form.doDrawDetail(tline)
                d = "%s_C00" % c
                if d in self.form.newkey:
                    tline = self.form.newdic[d]
                    mrgcod = tline[tdc.index("tpd_mrgcod")]
                    tline[tdc.index("tpd_text")] = getattr(self, "%s" % mrgcod)
                    self.form.doDrawDetail(tline)
            else:
                d = "%s_C00" % c
                if d in self.form.newkey:
                    vline = self.form.newdic[d]
                    mrgcod = vline[tdc.index("tpd_mrgcod")]
                    value = getattr(self, "%s" % mrgcod)
                    if not lasty:
                        lasty = vline[tdc.index("tpd_mrg_y1")]
                    if value:
                        lh = tline[tdc.index("tpd_lh")]
                        tline[tdc.index("tpd_y1")] = lasty
                        tline[tdc.index("tpd_y2")] = lasty + lh
                        vline[tdc.index("tpd_mrg_y1")] = lasty
                        vline[tdc.index("tpd_mrg_y2")] = lasty + lh
                        if tline:
                            self.form.doDrawDetail(tline)
                        vline[tdc.index("tpd_text")] = value
                        self.form.doDrawDetail(vline)
                        lasty = lasty + lh

    def doTail(self, tdc):
        for c in self.form.tail:
            line = None
            if c in self.form.newdic:
                line = self.form.newdic[c]
            else:
                t = "%s_T00" % c
                if t in self.form.newdic:
                    line = self.form.newdic[t]
            if line:
                if line[tdc.index("tpd_mrgcod")] == "message":
                    if not self.message:
                        continue
                self.form.doDrawDetail(line)
            d = "%s_C00" % c
            if d in self.form.newdic:
                line = self.form.newdic[d]
                mrgcod = line[tdc.index("tpd_mrgcod")]
                line[tdc.index("tpd_text")] = self.doGetData(mrgcod)
                self.form.doDrawDetail(line, fmat=False)

    def doLoadStatic(self):
        # ctlmst
        cmc = self.sql.ctlmst_col
        ctm = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        for fld in cmc:
            dat = ctm[cmc.index(fld)]
            if fld in self.form.tptp:
                if fld == "ctm_logo":
                    self.form.letterhead(cmc, ctm, fld, dat)
                    continue
                self.form.tptp[fld][1] = dat
        if "letterhead" in self.form.tptp:
            self.form.letterhead(cmc, ctm, "letterhead", None)
        if "document_type" in self.form.tptp:
            if ctm[cmc.index("ctm_taxno")]:
                self.form.tptp["document_type"][1] = "TAX INVOICE"
            else:
                self.form.tptp["document_type"][1] = "INVOICE"
        self.form.bank_details(cmc, ctm, 0)
        if "terms" in self.form.tptp:
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "CON"), ("mss_message", "=", 1)],
                limit=1)
            if acc:
                self.form.tptp["terms"][1] = acc[0]
            else:
                del self.form.tptp["terms"]

    def doGetData(self, mrgcod):
        if mrgcod and mrgcod in self.form.tptp and self.form.tptp[mrgcod][1]:
            return self.form.tptp[mrgcod][1]
        return ""

# vim:set ts=4 sw=4 sts=4 expandtab:
