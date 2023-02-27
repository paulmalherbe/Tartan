"""
SYNOPSIS
    Stores Stock Take Report.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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
from TartanClasses import Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError

class st5010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strloc", "strgrp", "strmf1",
            "strmf2"], prog=self.__class__.__name__)
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
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stock Take Report (%s)" % self.__class__.__name__)
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
        r1s = (("Number","N"),("Bin Number","B"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,1,0),"IUA",1,"Location","",
                "","Y",self.doLoc,loc,None,("efld",)),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),"IUA",8,"First Bin Number","",
                "","Y",self.doFbin,None,None,("efld",)),
            (("T",0,3,0),"IUA",8,"Last Bin Number","",
                "","Y",self.doLbin,None,None,("efld",)),
            (("T",0,4,0),"IUA",3,"Product Group","",
                "","Y",self.doGroup,grp,None,None),
            (("T",0,5,0),"IUI",5,"Quantity To Print","",
                "","Y",self.doQty,None,None,("efld",)),
            (("T",0,6,0),("IRB",r2s),0,"Ignore Zero Balances","",
                "N","Y",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry(frt, pag, i+1, data=self.loc)
            self.loadLoc()
            return "sk2"

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.loc = w
        self.loadLoc()
        if not self.locd:
            return "Invalid Location"
        if self.sort == "N":
            self.fbin = ""
            self.lbin = "zzzzzzzz"
            return "sk3"

    def loadLoc(self):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
            self.loc)], limit=1)
        if acc:
            self.locd = acc[0]
            self.df.loadEntry("T", 0, 2, data=self.locd)
        else:
            self.locd = None

    def doFbin(self, frt, pag, r, c, p, i, w):
        self.fbin = w

    def doLbin(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.fbin:
                return "Invalid Last Bin < First Bin"
            self.lbin = w
        else:
            self.lbin = "zzzzzzzz"

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

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.loc:
            self.sloc = ""
            self.eloc = "z"
        else:
            self.sloc = self.loc
            self.eloc = self.loc
        if not self.group:
            self.sgrp = ""
            self.egrp = "zzz"
        else:
            self.sgrp = self.group
            self.egrp = self.group
        if self.sort == "N":
            sortby = "st2_loc, st2_group, st2_code"
        else:
            sortby = "st2_loc, st2_bin, st2_group, st2_code"
        recs = self.sql.getRec(tables=["strmf1", "strmf2"], cols=["st2_group",
            "st2_code", "st2_loc", "st2_bin", "st1_desc", "st1_uoi"],
            where=[("st1_cono=st2_cono",), ("st1_group=st2_group",),
            ("st1_code=st2_code",), ("st1_type", "not", "in", ("R", "X")),
            ("st2_cono", "=", self.opts["conum"]), ("st2_group", ">=",
            self.sgrp), ("st2_group", "<=", self.egrp), ("st2_loc", ">=",
            self.sloc), ("st2_loc", "<=", self.eloc), ("st2_bin", ">=",
            self.fbin), ("st2_bin", "<=", self.lbin)], order=sortby)
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        else:
            self.printReport(recs)
        self.opts["mf"].closeLoop()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-90s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        count = 0
        old_grp = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            grp = CCD(dat[0], "UA", 3)
            self.groupd = grp.disp
            code = CCD(dat[1], "NA", 20)
            loc = CCD(dat[2], "UA", 1)
            sbin = CCD(dat[3], "UA", 8)
            desc = CCD(dat[4], "UA", 30)
            uoi = CCD(dat[5], "NA", 10)
            bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
                int(self.sysdtw / 100), keys=(grp.work, code.work, loc.work,
                ("P", self.opts["period"][0])))
            m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
            if self.zero == "Y" and not y_cb[0]:
                continue
            if old_grp and old_grp != grp.work:
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s   %s   %s   %s   %s" % \
                (grp.disp, code.disp, desc.disp, uoi.disp, sbin.disp))
            self.fpdf.underLine(txt=self.head)
            self.pglin += 2
            old_grp = grp.work
            count = count + 1
            if self.qty and count >= self.qty:
                break
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-23s %-10s" % \
            ("Stock Take Report as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %3s      %-8s %s  %s" % \
            ("Group", self.groupd, "Location", self.loc, self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s   %-20s   %-30s   %-10s   %-8s %-10s" % (
            "Grp", "Product-Code", "Description", "U.O.I", "Bin-Loc",
            "Quantities"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
