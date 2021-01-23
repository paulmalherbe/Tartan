"""
SYNOPSIS
    Members Ledger Category Changes.

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

import time
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, SplashScreen, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, doChkCatChg
from tartanFunctions import showError

class ml3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.reptyp = "A"
                if self.opts["args"][0] > self.opts["args"][1]:
                    self.start = CCD(self.opts["args"][1], "D1", 10)
                else:
                    self.start = CCD(self.opts["args"][0], "D1", 10)
                self.dte = int("%08i000000" % self.start.work)
                self.end = CCD(self.opts["args"][1], "D1", 10)
                self.chgtyp = "A"
                self.cat = ""
                self.cod = 0
                self.processRecords()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Members Category Changes (%s)" % self.__class__.__name__)
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "memcat", "memctc",
            "memmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.fromad = memctl["mcm_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.head = ("%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            "%s"))
        self.colsh = ["Mem-No", "Titles", "Inits", "Surname", "Actions",
            "Category", "Action-Dte", "Operator", "Start-Date", " End-Date",
            "Last-Date"]
        self.forms = [("UI", 6), ("NA", 6), ("NA", 5), ("NA", 30), ("UA", 7),
            ("NA", 30), ("D1", 10), ("NA", 20), ("d1", 10), ("d1", 10),
            ("d1", 10)]
        self.ctyp = (
            ("All", "A"),
            ("New", "N"),
            ("Updated", "U"),
            ("Deleted", "D"))
        self.catg = (
            ("All", "X"),
            ("Fees", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        return True

    def mainProcess(self):
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "mcc_type", 3]],
            "order": "mcc_code",
            "size": (400, 600)}
        r1s = (
            ("Actual", "A"),
            ("Pending", "P"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Report Type","",
                "A","Y",self.doRepTyp,None,None,None),
            (("T",0,1,0),"Id1",10,"Starting Date","",
                self.sysdtw,"Y",self.doStartDate,None,None,None),
            (("T",0,2,0),"ID1",10,"Ending   Date","Ending Date",
                self.sysdtw,"Y",self.doEndDate,None,None,None),
            (("T",0,3,0),("IRB",self.ctyp),0,"Change Type","",
                "A","Y",self.doChgTyp,None,None,None),
            (("T",0,4,0),("IRB",self.catg),0,"Category","",
                "X","Y",self.doCat,None,None,None),
            (("T",0,5,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doRepTyp(self, frt, pag, r, c, p, i, w):
        self.reptyp = w

    def doStartDate(self, frt, pag, r, c, p, i, w):
        self.start = CCD(w, "d1", 10)
        self.dte = int("%08i000000" % self.start.work)
        if self.reptyp == "P":
            self.end = self.start
            self.df.loadEntry(frt, pag, p+1, data=self.end.work)
            return "sk1"

    def doEndDate(self, frt, pag, r, c, p, i, w):
        if w < self.start.work:
            return "Invalid End Date, Before Start Date"
        self.end = CCD(w, "d1", 10)
        if self.reptyp == "P":
            self.chgtyp = "A"
            self.cat = None
            self.cod = None
            self.df.loadEntry(frt, pag, p+1, data="A")
            self.df.loadEntry(frt, pag, p+2, data="X")
            self.df.loadEntry(frt, pag, p+3, data=0)
            return "sk3"

    def doChgTyp(self, frt, pag, r, c, p, i, w):
        self.chgtyp = w

    def doCat(self, frt, pag, r, c, p, i, w):
        self.cat = w
        if w == "X":
            self.cat = None
            self.cod = None
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"
        self.cat = w

    def doCod(self, frt, pag, r, c, p, i, w):
        self.cod = w

    def doEnd(self):
        self.df.closeProcess()
        if self.reptyp == "P":
            sp = SplashScreen(self.opts["mf"].body,
                "Preparing Report ... Please Wait")
            recs = self.sql.getRec("memmst", cols=["mlm_memno"],
                where=[("mlm_cono", "=", self.opts["conum"]),
                ("mlm_state", "=", "A")])
            for rec in recs:
                data = doChkCatChg(self.opts["mf"], self.opts["conum"],
                    rec[0], self.start.work)
                if data:
                    self.sql.insRec("chglog", data=["memcat", "D",
                        "%03i%06i%1s%02i" % (self.opts["conum"], rec[0],
                        "B", data[0]), "", self.dte, "", str(data[1]),
                        str(data[2]), "", 0])
                    self.sql.insRec("chglog", data=["memcat", "N",
                        "%03i%06i%1s%02i" % (self.opts["conum"], rec[0],
                        "B", data[7]), "", self.dte, "", str(self.start.work),
                        str(0), "", 0])
            sp.closeSplash()
        self.processRecords()
        self.closeProcess()

    def processRecords(self):
        if "args" in self.opts:
            self.repprt = ["N", "V", "view"]
            self.repeml = None
        else:
            self.repprt = self.df.repprt
            self.repeml = self.df.repeml
        whr = [("chg_tab", "=", "memcat")]
        if self.reptyp == "P":
            whr.append(("chg_dte", "=", self.dte))
        elif self.start.work:
            whr.append(("chg_dte", "between", (self.start.work * 1000000),
                (self.end.work * 1000000) + 999999))
        else:
            whr.append(("chg_dte", "<=", (self.end.work * 1000000) + 999999))
        if self.chgtyp != "A":
            whr.append(("chg_act", "=", self.chgtyp))
        if self.cat:
            key = "%03i______%1s" % (self.opts["conum"], self.cat)
            if self.cod:
                key = "%s%02i" % (key, self.cod)
            else:
                key = "%s__" % key
            whr.append(("chg_key", "like", key))
        odr = "chg_key, chg_seq"
        chg = self.sql.getRec("chglog", where=whr, order=odr)
        if self.reptyp == "P":
            self.opts["mf"].dbm.rollbackDbase()
        if not chg:
            showError(self.opts["mf"].body, "Selection Error",
                "No Available Records")
        elif self.repprt[2] == "export":
            self.exportReport(chg)
        else:
            self.printReport(chg)

    def exportReport(self, chg):
        p = ProgressBar(self.opts["mf"].body, mxs=len(chg), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Members Category Changes between %s and %s" %
            (self.start.disp, self.end.disp))
        self.expheads.append(self.getOptions())
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        lmemno = 0
        for num, dat in enumerate(chg):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            if vals[0].work == lmemno:
                self.expdatas.append(["BODY", ["", "", "", "", vals[4],
                    vals[5].work, vals[6].work, vals[7].work, vals[8].work,
                    vals[9].work, vals[10].work]])
            else:
                self.expdatas.append(["BODY", [vals[0].work, vals[1].work,
                    vals[2].work, vals[3].work, vals[4], vals[5].work,
                    vals[6].work, vals[7].work, vals[8].work, vals[9].work,
                    vals[10].work]])
            lmemno = vals[0].work
        p.closeProgress()
        doWriteExport(xtype=self.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, chg):
        p = ProgressBar(self.opts["mf"].body, mxs=len(chg), esc=True)
        self.head = ("%03u %-30s %27s %33s %46s %10s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm, "", self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(chg):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                lmemno = 0
            if vals[0].work == lmemno:
                self.fpdf.drawText("%6s %6s %5s %30s %s %s %s %s %s %s %s" % \
                    ("", "", "", "", vals[4], vals[5].disp, vals[6].disp,
                    vals[7].disp, vals[8].disp, vals[9].disp, vals[10].disp))
            else:
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s" % \
                    (vals[0].disp, vals[1].disp, vals[2].disp, vals[3].disp,
                    vals[4], vals[5].disp, vals[6].disp, vals[7].disp,
                    vals[8].disp, vals[9].disp, vals[10].disp))
            lmemno = vals[0].work
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.repprt,
                fromad=self.fromad, repeml=self.repeml)

    def getValues(self, data):
        key = data[self.sql.chglog_col.index("chg_key")]
        cono = CCD(key[:3], "UI", 3)
        if cono.work != self.opts["conum"]:
            return
        memno = CCD(key[3:9], "UI", 6)
        ctype = CCD(key[9:10], "UA", 1)
        code = CCD(key[10:12], "UI", 2)
        last = CCD(0, "d1", 10)
        if data[self.sql.chglog_col.index("chg_act")] == "D":
            act = "Removed"
        elif data[self.sql.chglog_col.index("chg_act")] == "N":
            act = "Added  "
            last = self.sql.getRec("memcat", cols=["mlc_last"],
                where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno",
                "=", memno.work), ("mlc_type", "=", ctype.work), ("mlc_code",
                "=", code.work)], limit=1)
            if not last:
                last = CCD("Removed?", "NA", 10)
            else:
                last = CCD(last[0], "d1", 10)
        elif data[self.sql.chglog_col.index("chg_act")] == "U":
            act = "Changed"
        else:
            act = "Unknown"
        dte = data[self.sql.chglog_col.index("chg_dte")]
        dte = CCD(int(dte / 1000000), "D1", 10)
        usr = CCD(data[self.sql.chglog_col.index("chg_usr")], "NA", 20)
        old = CCD(data[self.sql.chglog_col.index("chg_old")], "d1", 10)
        new = CCD(data[self.sql.chglog_col.index("chg_new")], "d1", 10)
        mst = self.sql.getRec("memmst", where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", memno.work)], limit=1)
        if not mst:
            return
        tit = CCD(mst[self.sql.memmst_col.index("mlm_title")], "UA", 6)
        ini = CCD(mst[self.sql.memmst_col.index("mlm_initial")], "UA", 5)
        sur = CCD(mst[self.sql.memmst_col.index("mlm_surname")], "NA", 30)
        cat = self.sql.getRec("memctc", where=[("mcc_cono", "=",
            self.opts["conum"]), ("mcc_type", "=", ctype.work),
            ("mcc_code", "=", code.work)], limit=1)
        if not cat:
            return
        des = CCD(cat[self.sql.memctc_col.index("mcc_desc")], "NA", 30)
        return (memno, tit, ini, sur, act, des, dte, usr, old, new, last)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-32s %10s %3s %10s %89s %5s" % \
            ("Members Category Changes between", self.start.disp, "and",
            self.end.disp, "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText(self.getOptions())
        self.fpdf.drawText()
        self.fpdf.drawText("%6s %-6s %-5s %-30s %1s %-30s %10s %-20s %10s "\
            "%10s %10s" % ("Mem-No", "Titles", "Inits", "Surname", "Actions",
            "Category", "Action-Dte", "Operator", "Start-Date", " End-Date",
            "Last-Date"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def getOptions(self):
        if self.reptyp == "A":
            mess = "Options: Actual"
        else:
            mess = "Options: Pending"
        for x in self.ctyp:
            if self.chgtyp == x[1]:
                mess = mess + ", Type %s" % x[0]
                break
        for x in self.catg:
            if self.cat == x[1]:
                mess = mess + ", Category %s" % x[0]
        if self.cod:
            mess = mess + ", Code %s" % self.cod
        return mess

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
