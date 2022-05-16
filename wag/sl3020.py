"""
SYNOPSIS
    Staff Loans Transaction Audit Trail.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getModName, showError
from tartanWork import sltrtp

class sl3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagltf"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        lir = wagctl["ctw_i_date"]
        self.fromad = wagctl["ctw_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        if lir:
            fy = int(lir / 10000)
            fm = int(lir / 100) - (fy * 100) + 1
            if fm == 13:
                fy = fy + 1
                fm = 1
            self.sdate = (fy * 100) + fm
        else:
            self.sdate = 0
        self.edate = int(self.sysdtw / 100)
        self.totind = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Staff Loans Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in sltrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("wagltf",),
            "cols": (
                ("wlt_batch", "", 0, "Bat-Num"),
                ("wlt_type", ("xx", sltrtp), 20, "Type"),
                ("wlt_curdt", "", 0, "Cur-Dat")),
            "where": [("wlt_cono", "=", self.opts["conum"])],
            "group": "wlt_batch, wlt_type, wlt_curdt",
            "order": "wlt_type, wlt_curdt, wlt_batch"}
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                self.sdate,"Y",self.doStartPer,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"Ending Period","",
                self.edate,"Y",self.doEndPer,None,None,("efld",)),
            (("T",0,2,0),"IUI",1,"Type","Transaction Type",
                "","Y",self.doBatTyp,btt,None,None),
            (("T",0,3,0),"INa",7,"Batch Number","",
                "","Y",self.doBatNum,btm,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Totals Only","",
                "Y","Y",self.doTots,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if w > self.edate:
            return "Invalid Period"
        self.sdatw = w
        self.sdatd = CCD(self.sdatw, "d2", 7).disp

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            self.edatw = self.edate
        elif w < self.sdatw or w > self.edate:
            return "Invalid Period"
        else:
            self.edatw = w
        self.df.loadEntry(frt, pag, p, data=self.edatw)
        self.edatd = CCD(self.edatw, "d2", 7).disp

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(sltrtp):
            return "Invalid Batch Type"
        self.btype = w
        if self.btype:
            self.df.topf[pag][i+1][8]["whera"] = [["T","wlt_type",0]]
        else:
            self.df.topf[pag][i+1][8]["whera"] = []

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.btype:
            self.styp = 0
            self.etyp = 99
        else:
            self.styp = self.etyp = self.btype
        if not self.batch:
            self.sbat = ""
            self.ebat = "zzzzzzz"
        else:
            self.sbat = self.ebat = self.batch
        whr = [("wlt_cono", "=", self.opts["conum"]), ("wlt_curdt", "between",
            self.sdatw, self.edatw), ("wlt_batch", "between", self.sbat,
            self.ebat), ("wlt_type", "between", self.styp, self.etyp)]
        odr = "wlt_type, wlt_batch, wlt_trdt, wlt_ref"
        recs = self.sql.getRec("wagltf", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.totsonly == "Y":
            self.head = "%03u %-76s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-97s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bqty = 0
        self.bamt = 0
        self.bded = 0
        self.tqty = 0
        self.tamt = 0
        self.tded = 0
        self.gqt = [0,0,0,0,0,0,0]
        self.gam = [0,0,0,0,0,0,0]
        self.gdd = [0,0,0,0,0,0,0]
        self.trtp = 0
        self.pglin = 999
        col = self.sql.wagltf_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            empno = CCD(dat[col.index("wlt_empno")], "UI", 5)
            loan = CCD(dat[col.index("wlt_loan")], "UI", 2)
            batch = CCD(dat[col.index("wlt_batch")], "Na", 7)
            trtp = CCD(dat[col.index("wlt_type")], "UI", 2)
            trdt = CCD(dat[col.index("wlt_trdt")], "D1", 10)
            ref = CCD(dat[col.index("wlt_ref")], "Na", 9)
            amt = CCD(dat[col.index("wlt_amt")], "SD", 13.2)
            ded = CCD(dat[col.index("wlt_ded")], "SD", 13.2)
            per = CCD(dat[col.index("wlt_per")], "UD", 13.2)
            desc = CCD(dat[col.index("wlt_desc")], "NA", 30)
            if not self.trtp:
                self.trtp = trtp.work
                self.batch = batch.work
            if trtp.work != self.trtp:
                self.batchTotal()
                self.typeTotal()
                self.trtp = trtp.work
                self.batch = batch.work
                self.pglin = 999
            if batch.work != self.batch:
                self.batchTotal()
                self.batch = batch.work
                if self.totsonly != "Y":
                    self.typeHeading()
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            if self.totsonly != "Y":
                self.fpdf.drawText("%s %s %s %s %s %s %s %s" % \
                    (empno.disp, loan.disp, ref.disp, trdt.disp,
                    desc.disp, per.disp, amt.disp, ded.disp))
                self.pglin += 1
            self.bqty = self.bqty + 1
            self.bamt = float(ASD(self.bamt) + ASD(amt.work))
            self.bded = float(ASD(self.bded) + ASD(ded.work))
            self.tqty = self.tqty + 1
            self.tamt = float(ASD(self.tamt) + ASD(amt.work))
            self.tded = float(ASD(self.tded) + ASD(ded.work))
            self.gqt[trtp.work - 1] = self.gqt[trtp.work - 1] + 1
            self.gam[trtp.work - 1] = float(ASD(self.gam[trtp.work - 1]) + \
                ASD(amt.work))
            self.gdd[trtp.work - 1] = float(ASD(self.gdd[trtp.work - 1]) + \
                ASD(ded.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.batchTotal()
            self.typeTotal()
            self.grandTotal()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-7s %2s %-7s" % \
            ("Staff Loans Audit Trail for Period",
            self.sdatd, "to", self.edatd))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            if self.totsonly == "Y":
                self.fpdf.drawText(
                "%-44s%-8s  %-13s %-13s" % \
                ("Document Type", "Quantity", "      Amount", "   Deduction"))
            else:
                self.fpdf.drawText(
                "%-30s%-8s  %-13s %-13s" % \
                ("Document Type", "Quantity", "      Amount", "   Deduction"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 4

    def typeHeading(self):
        if self.totsonly == "N":
            batch = self.batch
        else:
            batch = "Various"
        if self.fpdf.lpp - self.pglin < 7:
            self.pageHeading()
            return
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-7s %-7s %-10s %3s" % \
            ("Batch", batch, "    Type", sltrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-53s %-13s %-13s" % \
            ("Details", "      Amount", "   Deduction"))
        else:
            self.fpdf.drawText(
            "%-5s %-2s %-9s %-10s %-30s %-13s %-13s %-13s" % \
            ("Empno", "Ln", "Reference", "Trans-Date", "Remarks",
            "       I-Rate", "      Amount", "   Deduction"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        j = CCD(self.bamt, "SD", 13.2)
        k = CCD(self.bded, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-5s %-7s %-39s %13s %13s" % \
                ("Batch", self.batch, "Totals", j.disp, k.disp))
        else:
            self.fpdf.drawText()
            self.pglin += 1
            self.fpdf.drawText("%-29s %-44s %13s %13s" % \
                (" ", "Batch " + self.batch + " Totals", j.disp, k.disp))
        self.pglin += 1
        if self.totsonly == "N":
            self.fpdf.drawText()
            self.pglin += 1
        self.bqty = 0
        self.bamt = 0
        self.bded = 0

    def typeTotal(self):
        j = CCD(self.tamt, "SD", 13.2)
        k = CCD(self.tded, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-53s %13s %13s" % ("Type Totals",
                j.disp, k.disp))
            self.pglin += 2
        else:
            self.fpdf.drawText("%-29s %-44s %13s %13s" % \
            (" ", "Type Totals", j.disp, k.disp))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        self.tqty = 0
        self.tamt = 0
        self.tded = 0

    def grandTotal(self):
        self.totind = "Y"
        self.pageHeading()
        tot = [0,0,0,0]
        for x, t in enumerate(sltrtp):
            qt = CCD(self.gqt[x], "SI", 8)
            am = CCD(self.gam[x], "SD", 13.2)
            dd = CCD(self.gdd[x], "SD", 13.2)
            if self.totsonly == "Y":
                self.fpdf.drawText("%-44s %s %s %s" % \
                (t[1], qt.disp, am.disp, dd.disp))
            else:
                self.fpdf.drawText("%-30s %s %s %s" % \
                (t[1], qt.disp, am.disp, dd.disp))
            tot[0] = tot[0] + qt.work
            tot[1] = float(ASD(tot[1]) + ASD(am.work))
            tot[2] = float(ASD(tot[2]) + ASD(dd.work))
        self.fpdf.drawText()
        qt = CCD(tot[0], "SI", 8)
        am = CCD(tot[1], "SD", 13.2)
        dd = CCD(tot[2], "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-44s %s %s %s" % \
            ("Grand Totals", qt.disp, am.disp, dd.disp))
        else:
            self.fpdf.drawText("%-30s %s %s %s" % \
            ("Grand Totals", qt.disp, am.disp, dd.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
