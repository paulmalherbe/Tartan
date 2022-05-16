"""
SYNOPSIS
    Staff Loans Master Listing.

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
from tartanFunctions import getModName, doPrinter, showError

class sl3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagmst", "waglmf", "wagltf"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Staff Loans Master Listing (%s)" % self.__class__.__name__)
        r1s = (("Number","N"),("Name","M"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),1,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,1,0),("IRB",r2s),1,"Ignore Zero Balances",
                "Ignore Zero Balances","Y","Y",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        col = [
            "wlm_empno",
            "wgm_sname",
            "wgm_fname",
            "wlm_loan",
            "wlm_desc",
            "wlm_code",
            "wlm_start",
            "wlm_rate",
            "wlm_repay",
            "sum(wlt_amt)"]
        whr = [
            ("wlm_cono", "=", self.opts["conum"]),
            ("wlm_cono=wgm_cono",),
            ("wlm_empno=wgm_empno",),
            ("wlt_cono=wgm_cono",),
            ("wlt_empno=wgm_empno",),
            ("wlt_loan=wlm_loan",)]
        if self.sort == "N":
            odr = "wlm_empno, wlm_loan"
        else:
            odr = "wlm_sname, wlm_loan"
        recs = self.sql.getRec(tables=["waglmf", "wagmst", "wagltf"], cols=col,
            where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
                "No Transactions Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-115s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        tot = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            emp = CCD(dat[0], "UI", 5)
            nam = CCD("%s, %s" % (dat[1], dat[2].split()[0]), "NA", 40)
            lon = CCD(dat[3], "UI", 2)
            des = CCD(dat[4], "NA", 20)
            cod = CCD(dat[5], "UI", 2)
            dte = CCD(dat[6], "d1", 10)
            per = CCD(dat[7], "UD", 6.2)
            ded = CCD(dat[8], "SD", 13.2)
            bal = CCD(dat[9], "SD", 13.2)
            if self.zero == "Y" and not bal.work:
                continue
            tot = float(ASD(tot) + ASD(bal.work))
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % (emp.disp,
                nam.disp, lon.disp, des.disp, cod.disp, dte.disp, per.disp,
                ded.disp, bal.disp))
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            tot = CCD(tot, "SD", 13.2)
            self.fpdf.drawText()
            self.fpdf.drawText("%5s %-100s%s" % ("", "Total", tot.disp))
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
        self.fpdf.drawText("%-29s %-10s" % \
            ("Staff Loans Master List as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-15s%-1s%-3s%-16s%-1s%-3s%-4s%-1s%-1s" % \
            ("(Options: Sort-", self.df.t_disp[0][0][0], "",
                "Ignore Zero Bal-", self.df.t_disp[0][0][1], "",
                "Csv-", self.df.t_disp[0][0][2], ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %-40s %-2s %-20s %-2s %-10s %-6s %-13s "\
            "%-13s" % ("EmpNo", "Name", "Ln", "Description", "Cd",
            "Start-Date", "I-Rate", "   Deduction", "     Balance"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
