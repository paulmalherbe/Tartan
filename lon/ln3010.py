"""
SYNOPSIS
    Loans Batch Error Listing.

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
from tartanFunctions import getModName, doPrinter, showError
from tartanWork import lntrtp

class ln3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlbat", "lontrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.fromad = lonctl["cln_emadd"]
        t = time.localtime()
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % (t[0],
            t[1], t[2], t[3], t[4])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Loans Batch Error Listing (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in lntrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("ctlbat",),
            "cols": (
                ("btm_batno", "", 0, "Bat-Num"),
                ("btm_rtyp", ("xx", lntrtp), 20, "Type"),
                ("btm_curdt", "", 0, "Curr-Dt"),
                ("btm_multi", "", 0, "M")),
            "where": [
                ("btm_cono", "=", self.opts["conum"]),
                ("btm_styp", "=", "LON"),
                ("btm_ind", "=", "N")],
            "whera": []}
        fld = (
            (("T",0,0,0),"IUI",1,"Type","Transaction Type",
                "","Y",self.doBatTyp,btt,None,None),
            (("T",0,1,0),"INa",7,"Batch-Number","Batch Number",
                "","Y",self.doBatNum,btm,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"))

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(lntrtp):
            return "Invalid Batch Type"
        self.rtyp = w
        if self.rtyp:
            self.df.topf[pag][1][8]["whera"] = [("T","btm_rtyp",0)]
        else:
            self.df.topf[pag][1][8]["whera"] = []

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batno = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("btm_cono", "=", self.opts["conum"]), ("btm_styp", "=", "LON")]
        if self.rtyp:
            whr.append(("btm_rtyp", "=", self.rtyp))
        if self.batno:
            whr.append(("btm_batno", "=", self.batno))
        whr.append(("btm_ind", "=", "N"))
        odr = "btm_rtyp, btm_batno"
        recs = self.sql.getRec("ctlbat", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Batch Error",
                "No Batch Transactions Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %39s %6s" %
            (self.opts["conum"], self.opts["conam"], self.sysdttm,
                self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.btot = [0, 0]
        self.pgnum = 0
        self.pglin = 999
        bc = self.sql.ctlbat_col
        tc = self.sql.lontrn_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.rtyp = CCD(dat[bc.index("btm_rtyp")], "UI", 1)
            self.batno = CCD(dat[bc.index("btm_batno")], "Na", 7)
            self.curdt = CCD(dat[bc.index("btm_curdt")], "D2", 7)
            self.multi = CCD(dat[bc.index("btm_multi")], "UA", 1)
            self.trno = CCD(dat[bc.index("btm_trno")], "UI", 7)
            self.trval = CCD(dat[bc.index("btm_trval")], "SD", 13.2)
            whr = [
                ("lnt_cono", "=", self.opts["conum"]),
                ("lnt_type", "=", self.rtyp.work),
                ("lnt_batch", "=", self.batno.work),
                ("lnt_batind", "=", "N")]
            odr = "lnt_seq"
            trndat = self.sql.getRec("lontrn", where=whr, order=odr)
            if not trndat:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            else:
                self.batchHeading()
            for trn in trndat:
                acno = CCD(trn[tc.index("lnt_acno")], "UA", 7)
                loan = CCD(trn[tc.index("lnt_loan")], "UI", 2)
                trdt = CCD(trn[tc.index("lnt_trdt")], "D1", 10)
                ref = CCD(trn[tc.index("lnt_refno")], "Na", 9)
                amt = CCD(trn[tc.index("lnt_tramt")], "SD", 13.2)
                desc = CCD(trn[tc.index("lnt_desc")], "NA", 30)
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                self.fpdf.drawText("%s %s %s %s %s %s" % (acno.disp,
                    loan.disp, trdt.disp, ref.disp, amt.disp, desc.disp))
                self.btot[0] = self.btot[0] + 1
                self.btot[1] = float(ASD(self.btot[1]) + ASD(amt.work))
                self.pglin += 1
            self.batchTotal()
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        else:
            showError(self.opts["mf"].body, "Batch Errors",
                "No Batch Transactions")

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-31s %42s %5s" %
            ("Staff Loans Batch Error Listing", "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.setFont()
        self.pglin = 4
        self.batchHeading()

    def batchHeading(self):
        if self.pglin > self.fpdf.lpp - 4:
            self.pageHeading()
            return
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-s %-s %-s %-17s %-s %-s %-s %s" %
            ("Batch:", self.batno.disp,
            "Type:", lntrtp[self.rtyp.work - 1][1],
            "Current Date:", self.curdt.disp,
            "Multi Allocations:", self.multi.disp))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-2s %-10s %-9s %-13s %-30s" % ("Acc-Num",
            "Ln", "Trans-Date", "Reference", "      Amount", "Description"))
        self.fpdf.underLine(self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        if self.pglin > self.fpdf.lpp - 5:
            self.pageHeading()
        self.fpdf.drawText()
        j = CCD(self.trno.work, "SI", 7)
        k = CCD(self.trval.work, "SD", 13.2)
        self.fpdf.drawText("%-20s %-10s %-10s %-7s %-13s" %
            ("Prelisted", "Quantity", j.disp, "Value", k.disp))
        l = CCD(self.btot[0], "SI", 7)
        m = CCD(self.btot[1], "SD", 13.2)
        self.fpdf.drawText("%-20s %-10s %-10s %-7s %-13s" %
            ("Entered", "Quantity", l.disp, "Value", m.disp))
        n = CCD((j.work - l.work), "SI", 7)
        o = CCD(float(ASD(k.work) - ASD(m.work)), "SD", 13.2)
        self.fpdf.drawText("%-20s %-10s %-10s %-7s %-13s" %
            ("Difference", "Quantity", n.disp, "Value", o.disp))
        self.fpdf.setFont(style="B")
        self.fpdf.underLine(self.head)
        self.fpdf.setFont()
        self.btot[0] = 0
        self.btot[1] = 0
        self.pglin += 5

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
