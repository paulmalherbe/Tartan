"""
SYNOPSIS
    Stores Ledger Master Code List.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2025 Paul Malherbe.

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
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, showError

class st3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strmf1", "struoi"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.colsh = ["Grp", "Product-Code", "T", "Description",
            "Unit-of-Issue", "Unit-Description"]
        self.forms = [("UA", 3), ("NA", 20), ("UA", 1), ("UA", 30),
            ("NA", 10), ("NA", 30)]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stores Master Code List (%s)" % self.__class__.__name__)
        r1s = (
            ("All", "A"),
            ("Normal", "N"),
            ("Recipe", "R"),
            ("Redundant", "X"))
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"IUA",3,"Product Group","",
                "","Y",self.doGroup,grp,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Product Type","",
                "N","Y",self.doType,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

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

    def doType(self, frt, pag, r, c, p, i, w):
        self.itype = w

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
        if self.itype != "A":
            whr.append(("st1_type", "=", self.itype))
        whr.extend([("unm_cono=st1_cono",), ("unm_unit=st1_uoi",)])
        recs = self.sql.getRec(tables=["strmf1", "struoi"], cols=["st1_group",
            "st1_code", "st1_type", "st1_desc", "st1_uoi", "unm_desc"],
            where=whr, order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        expheads = ["%03u %-30s %s %6s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm, self.__class__.__name__)]
        expheads.append("Stores Master Code List as at %s" % self.sysdtd)
        expcolsh = [self.colsh]
        expforms = self.forms
        expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            expdatas.append(["BODY", [vals[0].work, vals[1].work,
                vals[2].work, vals[3].work, vals[4].work, vals[5].work]])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=expheads, colsh=expcolsh, forms=expforms,
            datas=expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-89s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        old_grp = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            grp, code, itype, desc, uoi, umd = self.getValues(dat)
            self.groupd = grp.disp
            if old_grp and old_grp != grp.work:
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s" % (code.disp, itype.disp,
                desc.disp, uoi.disp, umd.disp))
            self.pglin += 1
            old_grp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        grp = CCD(data[0], "UA", 3)
        code = CCD(data[1], "NA", 20)
        itype = CCD(data[2], "UA", 1)
        desc = CCD(data[3], "UA", 30)
        uoi = CCD(data[4], "NA", 10)
        umd = CCD(data[5], "NA", 30)
        return (grp, code, itype, desc, uoi, umd)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-29s %-10s" % \
            ("Stores Master Code List as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %3s" % ("Group", self.groupd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-1s %-30s %-39s" % \
            ("Product-Code", "T", "Description", "Unit-of-Issue"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
