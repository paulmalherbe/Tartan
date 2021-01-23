"""
SYNOPSIS
    Stores Stock On Hand Report.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doWriteExport, getModName, doPrinter
from tartanFunctions import mthendDate, showError

class st3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strloc", "strgrp", "strmf1",
            "strtrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], "%s"))
        self.colsh = ["Grp", "Product-Code", "Description", "U.O.I",
            "Qty-Balance", "Val-Balance"]
        self.forms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10),
            ("SD", 12.2), ("SD", 12.2)]
        self.gtot = 0
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stock On Hand Report (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        r1s = (("Yes","Y"), ("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", "", "Y", "Y"]
            view = ("Y","V")
            mail = ("Y","N")
        fld = [
            (("T",0,0,0),"ID2",7,"Reporting Period","",
                int(self.sysdtw / 100),"Y",self.doPeriod,None,None,("efld",)),
            [("T",0,1,0),"IUA",1,"Location","",
                var[1],"N",self.doLoc,loc,None,("efld",)],
            (("T",0,2,0),"IUA",3,"Product Group","",
                var[2],"N",self.doGroup,grp,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Ignore Zero Balances","",
                var[3],"N",self.doZero,None,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Ignore Redundant Stock","",
                var[4],"N",self.doRedt,None,None,None)]
        if self.locs == "N":
            fld[1][1] = "OUA"
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doPeriod(self, frt, pag, r, c, p, i, w):
        if w > int(self.sysdtw / 100):
            return "Invalid Period"
        self.curdt = w
        self.date = CCD(mthendDate(w*100), "D1", 10)
        if self.locs == "N":
            self.df.loadEntry(frt, pag, p+1, data="1")
            no = self.doLoc(frt, pag, r, c+1, p+1, i+1, "1")
            if no:
                return no
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        if not w:
            self.loc = ""
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.loc = w
            self.locd = acc[0]

    def doGroup(self, frt, pag, r, c, p, i, w):
        if not w:
            self.group = ""
        else:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
            self.group = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w
        if self.zero == "Y":
            self.redt = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.redt)
            return "sk1"

    def doRedt(self, frt, pag, r, c, p, i, w):
        self.redt = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.group:
            self.sgrp = ""
            self.egrp = "zzz"
        else:
            self.sgrp = self.group
            self.egrp = self.group
        whr = [
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_group", ">=", self.sgrp),
            ("st1_group", "<=", self.egrp)]
        if self.redt == "Y":
            whr.append(("st1_type", "not", "in", ("R", "X")))
        else:
            whr.append(("st1_type", "<>", "R"))
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=whr, order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Stock On Hand Report as at %s" % self.date.disp)
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            self.expdatas.append(["BODY", [vals[0].work, vals[1].work,
                vals[2].work, vals[3].work, vals[4].work, vals[5].work]])
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %5s %46s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.stot = 0
        old_grp = ""
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            grp, code, desc, uoi, qbal, vbal = vals
            if old_grp and old_grp != grp.work:
                self.groupTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s" % \
                (code.disp, desc.disp, uoi.disp, qbal.disp, vbal.disp))
            self.pglin += 1
            self.stot = float(ASD(self.stot) + ASD(vbal.work))
            old_grp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.groupTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        grp = CCD(data[0], "UA", 3)
        self.groupd = grp.disp
        code = CCD(data[1], "NA", 20)
        desc = CCD(data[2], "NA", 30)
        uoi = CCD(data[3], "NA", 10)
        whr = [
            ("stt_cono", "=", self.opts["conum"]),
            ("stt_group", "=", grp.work),
            ("stt_code", "=", code.work)]
        if self.loc:
            whr.append(("stt_loc", "=", self.loc))
        whr.append(("stt_curdt", "<=", self.curdt))
        bal = self.sql.getRec("strtrn", cols=["round(sum(stt_qty), 2)",
            "round(sum(stt_cost), 2)"], where=whr, limit=1)
        if not bal[0]:
            bal[0] = 0
        if not bal[1]:
            bal[1] = 0
        qbal = CCD(bal[0], "SD", 12.2)
        vbal = CCD(bal[1], "SD", 12.2)
        if self.zero == "Y" and qbal.work == 0 and vbal.work == 0:
            return
        self.gtot = float(ASD(self.gtot) + ASD(vbal.work))
        return (grp, code, desc, uoi, qbal, vbal)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-26s %-10s %43s %5s" % \
            ("Stock On Hand Report as at", self.date.disp, "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %3s      %-8s %s  %s" % ("Group", self.groupd,
            "Location", self.loc, self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-30s %-10s %11s %12s" % ("Product-Code",
            "Description", "U.O.I", "Qty-Balance", "Val-Balance"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def groupTotal(self):
        val = CCD(self.stot, "SD", 12.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-41s %12s %12s" % \
            ("", "Group Totals", "", val.disp))
        self.fpdf.drawText()
        self.stot = 0

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "Grand Totals", "", "",
                self.gtot]])
            self.expdatas.append(["ULINED"])
            return
        val = CCD(self.gtot, "SD", 12.2)
        self.fpdf.drawText("%-20s %-41s %12s %12s" % \
            (" ", "Grand Totals", "", val.disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
