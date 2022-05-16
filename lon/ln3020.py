"""
SYNOPSIS
    Loans Transaction Audit Trail.

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
from tartanFunctions import copyList, doPrinter, doWriteExport, getModName
from tartanFunctions import showError
from tartanWork import lntrtp

class ln3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["lontrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.fromad = lonctl["cln_emadd"]
        t = time.localtime()
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["TP", "BatchNo", "Acc-Num", "Ln", "Reference",
            "Trans-Date", "Remarks", "Debits", "Credits"]
        self.forms = [("UI", 2), ("NA", 7), ("UA", 7), ("UI", 2),
            ("Na", 9), ("D1", 10), ("NA", 30), ("SD", 13.2), ("SD", 13.2)]
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        self.gqt = [0,0,0,0,0]
        self.gam = [0,0,0,0,0]
        self.prtrtp = copyList(lntrtp)
        self.prtrtp[3] = ("DRI", "Debit Interest")
        self.prtrtp.append(("CRI", "Credit Interest"))
        self.totind = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Loans Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in self.prtrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("lontrn",),
            "cols": (
                ("lnt_batch", "", 0, "Bat-Num"),
                ("lnt_type", ("xx", self.prtrtp), 20, "Type"),
                ("lnt_curdt", "", 0, "Cur-Dat")),
            "where": [("lnt_cono", "=", self.opts["conum"])],
            "group": "lnt_batch, lnt_type, lnt_curdt",
            "order": "lnt_type, lnt_curdt, lnt_batch"}
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                self.sper,"Y",self.doStartPer,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"Ending Period","",
                self.eper,"Y",self.doEndPer,None,None,("efld",)),
            (("T",0,2,0),"IUI",1,"Type","Transaction Type",
                "","Y",self.doBatTyp,btt,None,None),
            (("T",0,3,0),"INa",7,"Batch Number","",
                "","Y",self.doBatNum,btm,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Totals Only","",
                "Y","Y",self.doTots,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if w > self.eper:
            return "Invalid Period"
        self.sdatw = w
        self.sdatd = CCD(self.sdatw, "d2", 7).disp

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            self.edatw = self.eper
        elif w < self.sper or w > self.eper:
            return "Invalid Period"
        else:
            self.edatw = w
        self.df.loadEntry(frt, pag, p, data=self.edatw)
        self.edatd = CCD(self.edatw, "d2", 7).disp

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(self.prtrtp):
            return "Invalid Batch Type"
        self.btype = w
        if self.btype:
            self.df.topf[pag][i+1][8]["whera"] = [("T","lnt_type",0)]
        else:
            self.df.topf[pag][i+1][8]["whera"] = []

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if self.totsonly == "Y":
            self.df.setWidget(self.df.topEntry[0][5][3][0], state="hide")
            self.df.setWidget(self.df.topEntry[0][5][4][0], state="hide")
        else:
            self.df.setWidget(self.df.topEntry[0][5][3][0], state="show")
            self.df.setWidget(self.df.topEntry[0][5][4][0], state="show")

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
        whr = [("lnt_cono", "=", self.opts["conum"]), ("lnt_curdt", "between",
            self.sdatw, self.edatw), ("lnt_batch", "between", self.sbat,
            self.ebat), ("lnt_type", "between", self.styp, self.etyp)]
        odr = "lnt_type, lnt_batch, lnt_trdt, lnt_refno"
        recs = self.sql.getRec("lontrn", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Loans's Ledger Audit Trail for Period "\
            "%s to %s" % (self.sdatd, self.edatd))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        self.gdrs = 0
        self.gcrs = 0
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            acno, loan, batch, trtp, trdt, ref, drs, crs, desc = vals
            line = ["BODY", [trtp.work, batch.work, acno.work, loan.work,
                ref.work, trdt.work, desc.work, drs.work, crs.work]]
            self.expdatas.append(line)
            self.gdrs = float(ASD(self.gdrs) + ASD(drs.work))
            self.gcrs = float(ASD(self.gcrs) + ASD(crs.work))
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-86s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bqty = 0
        self.bdrs = 0
        self.bcrs = 0
        self.tqty = 0
        self.tdrs = 0
        self.tcrs = 0
        self.trtp = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            acno, loan, batch, trtp, trdt, ref, drs, crs, desc = vals
            if not self.trtp:
                self.trtp = trtp.work
                self.batch = batch.work
            if trtp.work != self.trtp and self.trtp < 4:
                self.batchTotal()
                self.typeTotal()
                self.trtp = trtp.work
                self.batch = batch.work
                self.pglin = 999
            if batch.work != self.batch:
                self.batchTotal()
                self.batch = batch.work
                if self.totsonly == "N":
                    self.typeHeading()
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            if self.totsonly == "N":
                self.fpdf.drawText("%s %s %s %s %s %s %s" % (acno.disp,
                    loan.disp, ref.disp, trdt.disp, desc.disp, drs.disp,
                    crs.disp))
                self.pglin += 1
            self.bqty = self.bqty + 1
            self.bdrs = float(ASD(self.bdrs) + ASD(drs.work))
            self.bcrs = float(ASD(self.bcrs) + ASD(crs.work))
            self.tqty = self.tqty + 1
            self.tdrs = float(ASD(self.tdrs) + ASD(drs.work))
            self.tcrs = float(ASD(self.tcrs) + ASD(crs.work))
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

    def getValues(self, data):
        col = self.sql.lontrn_col
        acno = CCD(data[col.index("lnt_acno")], "UA", 7)
        loan = CCD(data[col.index("lnt_loan")], "UI", 2)
        batch = CCD(data[col.index("lnt_batch")], "Na", 7)
        trtp = CCD(data[col.index("lnt_type")], "UI", 2)
        trdt = CCD(data[col.index("lnt_trdt")], "D1", 10)
        ref = CCD(data[col.index("lnt_refno")], "Na", 9)
        amt = data[col.index("lnt_tramt")]
        if amt < 0:
            crs = CCD(amt, "SD", 13.2)
            drs = CCD(0, "SD", 13.2)
            if trtp.work == 4:
                trtp = CCD(trtp.work + 1, "UI", 2)
        else:
            drs = CCD(amt, "SD", 13.2)
            crs = CCD(0, "SD", 13.2)
        desc = CCD(data[col.index("lnt_desc")], "NA", 30)
        self.gqt[trtp.work - 1] = self.gqt[trtp.work - 1] + 1
        self.gam[trtp.work - 1] = float(
            ASD(self.gam[trtp.work - 1]) + ASD(drs.work))
        self.gam[trtp.work - 1] = float(
            ASD(self.gam[trtp.work - 1]) + ASD(crs.work))
        return (acno, loan, batch, trtp, trdt, ref, drs, crs, desc)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-28s %-7s %2s %-7s" % \
            ("Loans Audit Trail for Period", self.sdatd, "to", self.edatd))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            self.fpdf.drawText("%-67s%-8s  %13s" % \
                ("Document Type", "Quantity", "Amount "))
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
        self.fpdf.drawText("%-7s %-7s %-10s %3s" % ("Batch:", batch,
            "   Type:", self.prtrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-62s %13s %13s" % ("Details",
                "Debits ", "Credits "))
        else:
            self.fpdf.drawText(
                "%-7s %-2s %-9s %-10s %-30s %13s %13s" % ("Acc-Num", "Ln",
                "Reference", "Trans-Date", "Remarks", "Debits ", "Credits "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        j = CCD(self.bdrs, "SD", 13.2)
        k = CCD(self.bcrs, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-5s %-7s %-48s %13s %13s" %
                ("Batch", self.batch, "Totals", j.disp, k.disp))
        else:
            self.fpdf.drawText()
            self.pglin += 1
            self.fpdf.drawText("%-31s %-30s %13s %13s" %
                (" ", "Batch " + self.batch + " Totals", j.disp, k.disp))
        self.pglin += 1
        if self.totsonly == "N":
            self.fpdf.drawText()
            self.pglin += 1
        self.bqty = 0
        self.bdrs = 0
        self.bcrs = 0

    def typeTotal(self):
        j = CCD(self.tdrs, "SD", 13.2)
        k = CCD(self.tcrs, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-62s %13s %13s" %
                ("Type Totals", j.disp, k.disp))
            self.pglin += 2
        else:
            self.fpdf.drawText("%-31s %-30s %13s %13s" %
                (" ", "Type Totals", j.disp, k.disp))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        self.tqty = 0
        self.tdrs = 0
        self.tcrs = 0

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "", "", "", "",
                "Grand Totals", self.gdrs, self.gcrs]])
            self.expdatas.append(["ULINED"])
            return
        tot = [0, 0]
        self.totind = "Y"
        self.pageHeading()
        for x in range(0, len(self.prtrtp)):
            qt = CCD(self.gqt[x], "SI", 8)
            am = CCD(self.gam[x], "SD", 13.2)
            self.fpdf.drawText("%-67s %s %s" % (self.prtrtp[x][1],
                qt.disp, am.disp))
            tot[0] = tot[0] + qt.work
            tot[1] = float(ASD(tot[1]) + ASD(am.work))
        self.fpdf.underLine(txt=self.head)
        qt = CCD(tot[0], "SI", 8)
        am = CCD(tot[1], "SD", 13.2)
        self.fpdf.drawText("%-67s %s %s" % ("Grand Totals", qt.disp, am.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
