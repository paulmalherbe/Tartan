"""
SYNOPSIS
    Asset Register Transaction Audit Trail.

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

from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError
from tartanWork import artrtp

class ar3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "asstrn",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.fromad = assctl["cta_emadd"]
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        self.totind = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Asset Register Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in artrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("asstrn",),
            "cols": (
                ("ast_batch", "", 0, "Bat-Num"),
                ("ast_type", ("xx", artrtp), 20, "Type"),
                ("ast_curdt", "", 0, "Cur-Dat")),
            "where": [],
            "group": "ast_batch, ast_type, ast_curdt",
            "order": "ast_type, ast_curdt, ast_batch"}
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                "","Y",self.doStartPer,None,None,("efld",)),
            (("T",0,1,0),"Id2",7,"Ending Period","",
                "","N",self.doEndPer,None,None,("efld",)),
            (("T",0,2,0),"IUI",1,"Type","Transaction Type",
                "","N",self.doBatTyp,btt,None,None),
            (("T",0,3,0),"INa",7,"Batch Number","",
                "","N",self.doBatNum,btm,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Totals Only","",
                "Y","N",self.doTots,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.s_per
        elif w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.sdat = self.df.loadEntry(frt, pag, p, data=w)

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.e_per
        elif w < self.sdat.work or w > self.e_per:
            return "Invalid Period"
        self.edat = self.df.loadEntry(frt, pag, p, data=w)

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(artrtp):
            return "Invalid Batch Type"
        self.btype = w
        whr = [("ast_cono", "=", self.opts["conum"]), ("ast_curdt", "between",
            self.sdat.work, self.edat.work)]
        if self.btype:
            whr.append(("ast_type", "=", self.btype))
        self.df.topf[pag][i+1][8]["where"] = whr

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.btype:
            styp = 0
            etyp = 99
        else:
            styp = etyp = self.btype
        if not self.batch:
            sbat = ""
            ebat = "zzzzzzz"
        else:
            sbat = ebat = self.batch
        recs = self.sql.getRec("asstrn", where=[("ast_cono", "=",
            self.opts["conum"]), ("ast_curdt", "between", self.sdat.work,
            self.edat.work), ("ast_batch", "between", sbat, ebat), ("ast_type",
            "between", styp, etyp)], order="ast_type, ast_batch, ast_refno")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Asset Transactions Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-105s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bcnt = 0
        self.bmt1 = 0
        self.bmt2 = 0
        self.bvat = 0
        self.tcnt = 0
        self.tmt1 = 0
        self.tmt2 = 0
        self.tvat = 0
        self.gcnt = [0,0,0,0,0]
        self.gmt1 = [0,0,0,0,0]
        self.gmt2 = [0,0,0,0,0]
        self.gvat = [0,0,0,0,0]
        self.trtp = 0
        self.pglin = 999
        tc = self.sql.asstrn_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            trtp = CCD(dat[tc.index("ast_type")], "UI", 2)
            batch = CCD(dat[tc.index("ast_batch")], "Na", 7)
            grp = CCD(dat[tc.index("ast_group")], "UA", 3)
            code = CCD(dat[tc.index("ast_code")], "Na", 7)
            refno = CCD(dat[tc.index("ast_refno")], "Na", 9)
            mtyp = CCD(dat[tc.index("ast_mtyp")], "UI", 1)
            trdt = CCD(dat[tc.index("ast_date")], "D1", 10)
            desc = CCD(dat[tc.index("ast_desc")], "NA", 30)
            amt1 = CCD(dat[tc.index("ast_amt1")], "SD", 13.2)
            amt2 = CCD(dat[tc.index("ast_amt2")], "SD", 13.2)
            vat = CCD(dat[tc.index("ast_vat")], "SD", 13.2)
            taxind = CCD(dat[tc.index("ast_taxind")], "NA", 1)
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
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" % \
                    (grp.disp, code.disp, refno.disp, trdt.disp, desc.disp,
                    mtyp.disp, amt1.disp, amt2.disp, vat.disp, taxind.disp))
                self.pglin += 1
            self.bcnt = self.bcnt + 1
            self.bmt1 = float(ASD(self.bmt1) + ASD(amt1.work))
            self.bmt2 = float(ASD(self.bmt2) + ASD(amt2.work))
            self.bvat = float(ASD(self.bvat) + ASD(vat.work))
            self.tcnt = self.tcnt + 1
            self.tmt1 = float(ASD(self.tmt1) + ASD(amt1.work))
            self.tmt2 = float(ASD(self.tmt2) + ASD(amt2.work))
            self.tvat = float(ASD(self.tvat) + ASD(vat.work))
            self.gcnt[trtp.work - 1] = self.gcnt[trtp.work - 1] + 1
            self.gmt1[trtp.work - 1] = float(ASD(self.gmt1[trtp.work - 1]) + \
                ASD(amt1.work))
            self.gmt2[trtp.work - 1] = float(ASD(self.gmt2[trtp.work - 1]) + \
                ASD(amt2.work))
            self.gvat[trtp.work - 1] = float(ASD(self.gvat[trtp.work - 1]) + \
                ASD(vat.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.batchTotal()
            self.typeTotal()
            self.grandTotal()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    repeml=self.df.repeml, fromad=self.fromad)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-36s %-7s %-2s %-61s" %
            ("Asset Register Audit Trail for Period",
            self.sdat.disp, "to", self.edat.disp))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            self.fpdf.drawText("%-30s %-8s %-13s %-13s %-13s" %
                ("Document Type", " Number", "    Amount-1",
                "    Amount-2", "     VAT-Amt"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 4

    def typeHeading(self):
        if self.totsonly != "Y":
            batch = self.batch
        else:
            batch = "Various"
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-7s %7s %-10s %3s" % \
            ("Batch", batch, "    Type", artrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-7s %-9s %-10s %-30s %1s %-13s %-13s %-13s "\
            "%1s" % ("Grp", "Code", "Reference", "   Date", "Remarks", "M",
            "    Amount-1", "    Amount-2", "     VAT-Amt", "I"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        k = CCD(self.bmt1, "SD", 13.2)
        l = CCD(self.bmt2, "SD", 13.2)
        m = CCD(self.bvat, "SD", 13.2)
        if self.totsonly != "Y":
            self.fpdf.drawText()
            self.pglin += 1
        self.fpdf.drawText("%-32s %-32s %13s %13s %13s" % \
            (" ", "Batch " + self.batch + " Totals", k.disp, l.disp, m.disp))
        self.pglin += 1
        if self.totsonly == "N":
            self.fpdf.drawText()
            self.pglin += 1
        self.bcnt = 0
        self.bmt1 = 0
        self.bmt2 = 0
        self.bvat = 0

    def typeTotal(self):
        k = CCD(self.tmt1, "SD", 13.2)
        l = CCD(self.tmt2, "SD", 13.2)
        m = CCD(self.tvat, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.pglin += 1
        self.fpdf.drawText("%-32s %-32s %13s %13s %13s" % \
            (" ", "Type-Totals", k.disp, l.disp, m.disp))
        self.pglin += 1
        self.tcnt = 0
        self.tmt1 = 0
        self.tmt2 = 0
        self.tvat = 0

    def grandTotal(self):
        self.totind = "Y"
        self.pageHeading()
        tot = [0,0,0,0]
        for x, t in enumerate(artrtp):
            cnt = CCD(self.gcnt[x], "SI", 7)
            mt1 = CCD(self.gmt1[x], "SD", 13.2)
            mt2 = CCD(self.gmt2[x], "SD", 13.2)
            vat = CCD(self.gvat[x], "SD", 13.2)
            self.fpdf.drawText("%-31s %s %s %s %s" % \
                (t[1], cnt.disp, mt1.disp, mt2.disp, vat.disp))
            tot[0] = tot[0] + cnt.work
            tot[1] = float(ASD(tot[1]) + ASD(mt1.work))
            tot[2] = float(ASD(tot[2]) + ASD(mt2.work))
            tot[3] = float(ASD(tot[3]) + ASD(vat.work))
        self.fpdf.drawText()
        cnt = CCD(tot[0], "SI", 8)
        mt1 = CCD(tot[1], "SD", 13.2)
        mt2 = CCD(tot[2], "SD", 13.2)
        vat = CCD(tot[3], "SD", 13.2)
        self.fpdf.drawText("%-30s %s %s %s %s" % \
            ("Grand Totals", cnt.disp, mt1.disp, mt2.disp, vat.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
