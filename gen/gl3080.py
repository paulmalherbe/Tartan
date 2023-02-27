"""
SYNOPSIS
    General Ledger Bank Reconciliation.

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
from TartanClasses import ASD, CCD, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter, mthendDate

class gl3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "genbal", "genmst",
            "gentrn", "genrct"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        t = time.localtime()
        self.c_per = (t[0] * 100) + t[1]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Bank Reconciliation (%s)" % self.__class__.__name__)
        glm = {
            "stype": "R",
            "tables": ("ctlctl", "genmst"),
            "cols": (
                ("ctl_conacc", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [
                ("ctl_cono", "=", self.opts["conum"]),
                ("ctl_code", "like", "bank_%"),
                ("glm_cono=ctl_cono",),
                ("glm_acno=ctl_conacc",)]}
        fld = (
            (("T",0,0,0),"IUI",7,"Bank Account","",
                "","Y",self.doBankAcc,glm,None,("efld",)),
            (("T",0,1,0),"Id2",7,"Accounting Period","",
                self.c_per,"Y",self.doPer,None,None,("efld",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doBankAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["ctlctl", "genmst"], cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=", w),
            ("ctl_cono=glm_cono",), ("ctl_conacc=glm_acno",), ("ctl_code",
            "like", "bank_%")], limit=1)
        if not acc:
            return "Invalid Bank Account Number"
        self.acno = w
        self.name = acc[0]

    def doPer(self, frt, pag, r, c, p, i, w):
        self.perw = w
        self.perd = self.df.t_disp[pag][r][p]

    def doEnd(self):
        self.df.closeProcess()
        self.extractBalance()
        self.sortPayments()
        self.sortReceipts()
        self.sortImports()
        self.printReport()
        self.closeProcess()

    def sortPayments(self):
        col = ["glt_trdt", "glt_refno", "glt_desc", "glt_tramt"]
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.acno),
            ("glt_curdt", "<=", self.perw),
            ("(", "glt_recon", "=", 0, "or", "glt_recon", ">", self.perw, ")"),
            ("glt_type", "in", (2, 4))]
        odr = "glt_curdt, glt_trdt, glt_type, glt_refno, glt_batch"
        self.pays = self.sql.getRec("gentrn", cols=col, where=whr,
            order=odr)
        if not self.pays:
            self.pays = []

    def sortReceipts(self):
        col = ["glt_trdt", "glt_refno", "glt_desc", "glt_tramt"]
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.acno),
            ("glt_curdt", "<=", self.perw),
            ("(", "glt_recon", "=", 0, "or", "glt_recon", ">", self.perw, ")"),
            ("glt_type", "=", 6)]
        odr = "glt_curdt, glt_trdt, glt_type, glt_refno, glt_batch"
        self.recs = self.sql.getRec("gentrn", cols=col, where=whr,
            order=odr)
        if not self.recs:
            self.recs = []

    def sortImports(self):
        dte = mthendDate((self.perw * 100) + 1)
        col = ["grt_date", "grt_refno", "grt_memo", "grt_amount"]
        whr = [
            ("grt_cono", "=", self.opts["conum"]),
            ("grt_acno", "=", self.acno),
            ("grt_date", "<=", dte),
            ("grt_flag", "=", "N")]
        odr = "grt_date, grt_refno"
        self.imps = self.sql.getRec("genrct", cols=col, where=whr,
            order=odr)
        if not self.imps:
            self.imps = []

    def printReport(self):
        p = ProgressBar(self.opts["mf"].body,
            mxs=(len(self.pays) + len(self.recs) + len(self.imps)))
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=90)
        self.tot_chq = 0
        self.tot_dep = 0
        self.tot_imp = 0
        self.pageHeading()
        bal = CCD(self.bal, "SD", 13.2)
        self.fpdf.drawText("%-71s %-13s" % ("Balance as per Cash Book",
            bal.disp))
        if self.pays:
            self.fpdf.drawText()
            self.fpdf.drawText("%-70s" % ("Add: Cheques Not Presented",))
            self.fpdf.drawText()
            mxs = len(self.pays) - 1
            for num, pay in enumerate(self.pays):
                p.displayProgress(num)
                self.printLine(num, mxs, pay, "C")
        if self.recs:
            self.fpdf.drawText()
            self.fpdf.drawText("%-70s" % ("Less: Deposits Not Presented",))
            self.fpdf.drawText()
            mxs = len(self.recs) - 1
            for num, rec in enumerate(self.recs):
                p.displayProgress(len(self.pays) + num)
                self.printLine(num, mxs, rec, "D")
        # Bank Imports
        if self.imps:
            self.fpdf.drawText()
            self.fpdf.drawText("%-70s" % ("+-: Imports Not Captured",))
            self.fpdf.drawText()
            mxs = len(self.imps) - 1
            for num, rec in enumerate(self.imps):
                p.displayProgress(len(self.pays) + len(self.imps) + num)
                self.printLine(num, mxs, rec, "I")
        p.closeProgress()
        self.fpdf.underLine(txt="%72s%12s" % ("", 12 * self.fpdf.suc))
        b = float(ASD(self.bal) + ASD(self.tot_chq) - ASD(self.tot_dep) + \
            ASD(self.tot_imp))
        bal = CCD(b, "SD", 13.2)
        self.fpdf.drawText("%-71s %-13s" % ("Balance as per Bank Statement",
            bal.disp))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                repeml=self.df.repeml)

    def printLine(self, num, mxs, dat, typ):
        trdt = CCD(dat[0], "D1", 10)
        refno = CCD(dat[1], "Na", 9)
        desc = CCD(dat[2], "NA", 30)
        if typ in ("D", "I"):
            amt = dat[3]
        else:
            amt = float(ASD(0) - ASD(dat[3]))
        tramt = CCD(amt, "SD", 13.2)
        if self.fpdf.newPage():
            self.pageHeading()
        if typ == "C":
            self.tot_chq = float(ASD(self.tot_chq) + ASD(tramt.work))
            if num == mxs:
                bal = CCD(self.tot_chq, "SD", 13.2)
        elif typ == "D":
            self.tot_dep = float(ASD(self.tot_dep) + ASD(tramt.work))
            if num == mxs:
                bal = CCD(self.tot_dep, "SD", 13.2)
        else:
            self.tot_imp = float(ASD(self.tot_imp) + ASD(tramt.work))
            if num == mxs:
                bal = CCD(self.tot_imp, "SD", 13.2)
        if num == mxs:
            self.fpdf.drawText("%-5s %-9s %-10s %-30s %-13s %-13s" % \
                ("", refno.disp, trdt.disp, desc.disp, tramt.disp, bal.disp))
        else:
            self.fpdf.drawText("%-5s %-9s %-10s %-30s %-13s" % \
                ("", refno.disp, trdt.disp, desc.disp, tramt.disp))

    def extractBalance(self):
        o = self.sql.getRec("genbal", cols=["glo_cyr"],
            where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno",
            "=", self.acno), ("glo_trdt", "=", self.opts["period"][1][0])],
            limit=1)
        if o:
            b = CCD(o[0], "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        self.bal = b.work
        o = self.sql.getRec("gentrn", cols=["round(sum(glt_tramt), 2)"],
            where=[("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
            self.acno), ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
            self.perw)], limit=1)
        if o[0]:
            b = CCD(o[0], "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        self.bal = float(ASD(self.bal) + ASD(b.work))

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("Bank Reconciliation for %s (%s) up to Period %s" %
            (self.name, self.acno, self.perd))
        self.fpdf.underLine()
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
