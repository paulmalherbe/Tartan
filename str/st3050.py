"""
SYNOPSIS
    Stores Recipe Listing.

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
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, getSingleRecords, doPrinter, showError

class st3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strmf1", "strloc",
            "strrcp"], prog=self.__class__.__name__)
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
            "Stores Recipe Listing (%s)" % self.__class__.__name__)
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
        r1s = (("Yes","Y"), ("Singles", "S"))
        r2s = (("Yes","Y"), ("No","N"))
        if self.locs == "N":
            self.loc = "1"
            self.locd = "Location One"
            fld = []
        else:
            fld = [[("T",0,0,0),"IUA",1,"Location","",
                "1","Y",self.doLoc,loc,None,("notblank",)]]
        fld.extend([
            (("T",0,1,0),"IUA",3,"Product Group","",
                "","Y",self.doGroup,grp,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Recipe per Page","Recipe per Page",
                "N","Y",self.doPage,None,None,None)])
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=", w)],
            limit=1)
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

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doPage(self, frt, pag, r, c, p, i, w):
        self.page = w

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
            ("st1_group", "<=", self.egrp),
            ("st1_type", "=", "R")]
        odr = "st1_group, st1_code"
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "strmf1",
                ("st1_group", "st1_code", "st1_desc"), where=whr, order=odr)
        else:
            recs = self.sql.getRec("strmf1", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-71s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        oldrec = ""
        self.pglin = 999
        st1 = self.sql.strmf1_col
        srr = self.sql.strrcp_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            grp = CCD(dat[st1.index("st1_group")], "UA", 3)
            cod = CCD(dat[st1.index("st1_code")], "NA", 20)
            whr = [
                ("srr_cono", "=", self.opts["conum"]),
                ("srr_group", "=", grp.work),
                ("srr_code", "=", cod.work),
                ("srr_loc", "=", self.loc)]
            odr = "srr_rgroup, srr_rcode"
            rec = self.sql.getRec("strrcp", where=whr, order=odr)
            if not rec:
                continue
            newrec = "%s%s" % (grp.work, cod.work)
            if oldrec and newrec != oldrec:
                self.pageHeading(grp.disp, cod.disp, chg=True)
            for z in rec:
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading(grp.disp, cod.disp)
                gp = CCD(z[srr.index("srr_rgroup")], "UA", 3)
                cd = CCD(z[srr.index("srr_rcode")],  "NA", 20)
                qt = CCD(z[srr.index("srr_rqty")], "UD", 11.2)
                dd = self.sql.getRec("strmf1", cols=["st1_desc"],
                    where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                    "=", gp.work), ("st1_code", "=", cd.work)], limit=1)
                if dd:
                    dc = dd[0]
                else:
                    dc = ""
                self.fpdf.drawText("%s %s %-38s %s" % (gp.disp, cd.disp, dc,
                    qt.disp))
                self.pglin += 1
                oldrec = newrec
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self, grp, cod, chg=False):
        if self.page == "N" and chg and self.pglin < (self.fpdf.lpp - 10):
            self.fpdf.drawText()
            self.fpdf.drawText()
            self.fpdf.setFont(style="B")
            self.pglin += 2
        else:
            self.fpdf.add_page()
            self.fpdf.setFont(style="B")
            self.fpdf.drawText(self.head)
            self.fpdf.drawText()
            self.fpdf.drawText("%-19s %-10s" % ("Stock Recipes as at",
                self.sysdtd))
            self.fpdf.drawText()
            self.pglin = 4
        self.fpdf.drawText("%-5s %3s  %-4s %s  %-8s %s %s" % ("Group", grp,
            "Code", cod, "Location", self.loc, self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-20s %-38s %11s" % ("Grp", "Product-Code",
            "Description", "Quantity"))
        self.fpdf.underLine(txt=self.head)
        self.pglin += 4
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
