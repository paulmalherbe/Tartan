"""
SYNOPSIS
    Stores Stock to Order Report.

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

import time
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, showError

class st3120(object):
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
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % (t[0],
            t[1], t[2], t[3], t[4])
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["Grp", "Product-Code", "Description", "U.O.I",
            "Qty-Balance", "Qty-OnOrder", "Qty-BkOrder", "Qty-ToOrder"]
        self.forms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10),
            ("SD", 12,2), ("SD", 12.2), ("SD", 12.2), ("SD", 12.2)]
        self.stot = 0
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
        fld = (
            (("T",0,0,0),"ID1",10,"Reporting Date","",
                self.sysdtw,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),"IUA",1,"Location","",
                "","Y",self.doLoc,loc,None,("efld",)),
            (("T",0,2,0),"IUA",3,"Product Group","",
                "","Y",self.doGrp,grp,None,("efld",)),
            (("T",0,3,0),("IRB",r1s),0,"Include Zeros","",
                "N","Y",self.doZero,None,None,None,None,
                "Include Items Which Have a Zero Order Quantity"))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.repdtw = w
        self.repdtd = self.df.t_disp[pag][0][0]

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

    def doGrp(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
        self.group = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("st1_cono", "=", self.opts["conum"])]
        if self.group:
            whr.append(("st1_group", "=", self.group))
        whr.append(("st1_type", "<>", "X"))
        whr.append(("st1_value_ind", "=", "A"))
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=whr, order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.opts["mf"].closeLoop()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Stock to Order Report as at %s" % self.sysdtd)
        self.expheads.append("(Options: Report Date %s)" % self.repdtd)
        self.expheads.append("Location %s  %s" % (self.loc, self.locd))
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
                vals[2].work, vals[3].work, vals[4].work, vals[5].work,
                vals[6].work, vals[7].work]])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        self.head1 = self.head
        self.head2 = "Stock to Order Report as at %s" % self.sysdtd
        pad = chrs - len(self.head2)
        self.head2 = self.head2 + (" " * pad)
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head2)
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (vals[0].disp,
                vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp,
                vals[5].disp, vals[6].disp, vals[7].disp))
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            if self.pglin > (self.fpdf.lpp - 2):
                self.pageHeading()
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def getValues(self, data):
        grp = CCD(data[0], "UA", 3)
        code = CCD(data[1], "NA", 20)
        desc = CCD(data[2], "UA", 30)
        uoi = CCD(data[3], "NA", 10)
        whr = [
            ("st2_cono", "=", self.opts["conum"]),
            ("st2_group", "=", grp.work),
            ("st2_code", "=", code.work)]
        if self.loc:
            whr.append(("st2_loc", "=", self.loc))
        st2 = self.sql.getRec("strmf2", cols=["st2_reord_ind",
            "st2_reord_level", "st2_reord_qty"], where=whr, limit=1)
        if not st2:
            return
        if self.zero == "N" and not st2[1]:
            return
        req = CCD(st2[1], "SD", 12.2)
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
            int(self.repdtw / 100), keys=(grp.work, code.work, self.loc))
        cbal, obal, bbal = bals.doStrOrds()
        tbal = float(ASD(cbal.work) + ASD(obal.work) - ASD(bbal.work))
        if req.work < tbal:
            if self.zero == "N":
                return
            tbal = CCD(0, "SD", 12.2)
            return (grp, code, desc, uoi, cbal, obal, bbal, tbal)
        tbal = float(ASD(req.work) - ASD(tbal))
        if tbal < st2[2]:
            tbal = st2[2]
        tbal = CCD(tbal, "SD", 12.2)
        if self.zero == "N" and not tbal.work:
            return
        if self.zero == "Y" and not cbal.work and not obal.work and not \
                                            bbal.work and not tbal.work:
            return
        return (grp, code, desc, uoi, cbal, obal, bbal, tbal)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-22s%-10s%-1s" % \
            ("(Options: Report Date-", self.df.t_disp[0][0][0], ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%-8s %s  %s" % \
            ("Location", self.loc, self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-20s %-30s %-10s %11s  %11s  %11s  %11s" % \
            ("Grp", "Product-Code", "Description", "U.O.I", "Qty-Balance",
            "Qty-OnOrder", "Qty-BkOrder", "Qty-ToOrder"))
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head2)))
        self.fpdf.setFont()
        self.pglin = 10

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
