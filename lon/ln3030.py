"""
SYNOPSIS
    Loans Balances Listing.

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
from TartanClasses import ASD, CCD, GetCtl, LoanInterest, MyFpdf, ProgressBar
from TartanClasses import Sql, TartanDialog
from tartanFunctions import doPrinter, getModName, mthendDate, showError

class ln3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["lonmf1", "lonmf2", "lontrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.fromad = lonctl["cln_emadd"]
        t = time.localtime()
        self.curdt = int(((t[0] * 10000) + (t[1] * 100) + t[2]) / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Loans Balances Listing (%s)" % self.__class__.__name__)
        r1s = (("Number","N"),("Name","M"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Reporting Period","",
                self.curdt,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),1,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,2,0),("IRB",r2s),1,"Include Zero Balances","",
                "N","Y",self.doZero,None,None,None),
            (("T",0,3,0),("IRB",r2s),1,"Include Pending Interest","",
                "N","Y",self.doPend,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.curdt = w
        self.cdte = self.df.t_disp[pag][0][i]
        self.date = mthendDate(w * 100)

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doPend(self, frt, pag, r, c, p, i, w):
        self.pend = w

    def doEnd(self):
        self.df.closeProcess()
        if self.sort == "N":
            odr = "lm1_acno"
        else:
            odr = "lm1_name"
        lm1 = self.sql.getRec("lonmf1", where=[("lm1_cono", "=",
            self.opts["conum"])], order=odr)
        if not lm1:
            showError(self.opts["mf"].body, "Loans Error",
                "No Loans Selected")
        else:
            self.printReport(lm1)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.pend == "Y":
            self.head = "%03u %-118s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-90s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        ltot = 0
        itot = 0
        ntot = 0
        self.pglin = 999
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            acc = CCD(rec[self.sql.lonmf1_col.index("lm1_acno")], "UA", 7)
            nam = CCD(rec[self.sql.lonmf1_col.index("lm1_name")], "NA", 28)
            lm2 = self.sql.getRec("lonmf2", where=[("lm2_cono",
                "=", self.opts["conum"]), ("lm2_acno", "=", acc.work)],
                order="lm2_loan")
            for dat in lm2:
                lon = CCD(dat[self.sql.lonmf2_col.index("lm2_loan")], "UI", 2)
                des = CCD(dat[self.sql.lonmf2_col.index("lm2_desc")], "NA", 30)
                dte = CCD(dat[self.sql.lonmf2_col.index("lm2_start")], "d1", 10)
                col = ["sum(lnt_tramt)"]
                whr = [
                    ("lnt_cono", "=", self.opts["conum"]),
                    ("lnt_acno", "=", acc.work),
                    ("lnt_loan", "=", lon.work),
                    ("lnt_curdt", "<=", self.curdt)]
                lbal = self.sql.getRec("lontrn", cols=col, where=whr,
                    limit=1)
                lbal = CCD(lbal[0], "SD", 13.2)
                if self.zero == "N" and not lbal.work:
                    continue
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                ltot = float(ASD(ltot) + ASD(lbal.work))
                if self.pend == "Y":
                    LoanInterest("L", self.opts["mf"].dbm, dat, update="Y",
                        tdate=self.date, batch="Pending")
                    nbal = self.sql.getRec("lontrn", cols=col, where=whr,
                        limit=1)
                    nbal = CCD(nbal[0], "SD", 13.2)
                    ntot = float(ASD(ntot) + ASD(nbal.work))
                    ibal = CCD(nbal.work - lbal.work, "SD", 13.2)
                    itot = float(ASD(itot) + ASD(ibal.work))
                    self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (acc.disp,
                        nam.disp, lon.disp, des.disp, dte.disp, lbal.disp,
                        ibal.disp, nbal.disp))
                else:
                    self.fpdf.drawText("%s %s %s %s %s %s" % (acc.disp,
                        nam.disp, lon.disp, des.disp, dte.disp, lbal.disp))
                self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.fpdf.underLine(txt=self.head)
            ltot = CCD(ltot, "SD", 13.2)
            if self.pend == "Y":
                itot = CCD(itot, "SD", 13.2)
                ntot = CCD(ntot, "SD", 13.2)
                self.fpdf.drawText("%8s%-74s%13s %13s %13s" % ("", "Totals",
                    ltot.disp, itot.disp, ntot.disp))
            else:
                self.fpdf.drawText("%8s%-74s%13s" % ("", "Totals", ltot.disp))
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
        txt = "%-29s %-7s" % ("Loans Balances Listing as at", self.cdte)
        self.fpdf.drawText(txt=txt)
        self.fpdf.drawText()
        self.fpdf.drawText("%s %s  %s %s)" % \
            ("(Options: Sort:", self.sort, "Include-Zero-Bal:", self.zero))
        self.fpdf.drawText()
        txt = "%-7s %-28s %-2s %-30s %-10s" % \
            ("Acc-Num", "Name", "Ln", "Description", "Start-Date")
        if self.pend == "Y":
            txt = "%s %13s %13s %13s" % \
                (txt, "Ledger-Bal ", "Interest ", "Balance ")
        else:
            txt = "%s %13s" % (txt, "Balance ")
        self.fpdf.drawText(txt=txt)
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
