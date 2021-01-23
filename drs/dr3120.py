"""
SYNOPSIS
    Debtors Ledger Interest Chargeable.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getModName, projectDate, showError

class dr3120(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "drsmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.fromad = drsctl["ctd_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Debtors Interest Chargeable Report (%s)" % self.__class__.__name__)
        fld = (
            (("T",0,0,0),"ID1",10,"Cut-Off Date","",
                self.sysdtw,"Y",self.doCutoff,None,None,("efld",)),
            (("T",0,1,0),"IUI",2,"Days Leeway","",
                "","N",self.doLeeway,None,None,("between",0,31)),
            (("T",0,2,0),"IUD",12.2,"Minimum Balance","",
                "","N",self.doMinBal,None,None,("efld",)),
            (("T",0,3,0),"IUD",5.2,"Default Rate","",
                "","N",self.doDefRte,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doCutoff(self, frt, pag, r, c, p, i, w):
        self.cutoff = w

    def doLeeway(self, frt, pag, r, c, p, i, w):
        self.lway = w
        self.validw = projectDate(self.cutoff, self.lway)
        f = CCD(self.validw, "D1", 10)
        self.repdate = f.disp

    def doMinBal(self, frt, pag, r, c, p, i, w):
        self.minbal = w

    def doDefRte(self, frt, pag, r, c, p, i, w):
        self.defrte = w

    def doEnd(self):
        self.df.closeProcess()
        self.col = ["drm_chain", "drm_acno", "drm_name", "drm_rfterms",
            "drm_int_per"]
        recs = self.sql.getRec("drsmst", cols=self.col,
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_stat",
            "<>", "X")], order="drm_chain, drm_acno")
        if not recs:
            showError(self.opts["mf"].body, "Error", "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %11s %34s %10s %6s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm, "", self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.tots = [0,0]
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            chn = CCD(dat[self.col.index("drm_chain")], "UI", 3)
            acno = CCD(dat[self.col.index("drm_acno")], "NA", 7)
            name = CCD(dat[self.col.index("drm_name")], "NA", 30)
            rft = CCD(dat[self.col.index("drm_rfterms")], "UI", 3)
            per = CCD(dat[self.col.index("drm_int_per")], "UD", 5.2)
            if not per.work:
                if not self.defrte:
                    continue
                per = CCD(self.defrte, "UD", 5.2)
            bals = Balances(self.opts["mf"], "DRS", self.opts["conum"],
                int(self.cutoff / 100), (chn.work, acno.work))
            obal, tbal, ages = bals.doAllBals()
            if tbal <= 0:
                continue
            bal = CCD(tbal, "SD", 13.2)
            tm = int(rft.work / 30)
            if tm > 4:
                tm = 4
            od = 0
            for x in range(tm, 5):
                od = float(ASD(od) + ASD(ages[x]))
            odu = CCD(od, "SD", 13.2)
            if odu.work <= 0 or (self.minbal and odu.work < self.minbal):
                continue
            b = round((odu.work * per.work / 1200), 2)
            amt = CCD(b, "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s       %s %s" % \
                (chn.disp, acno.disp, name.disp, rft.disp, bal.disp,
                odu.disp, per.disp, amt.disp))
            self.pglin += 1
            self.tots[0] = float(ASD(self.tots[0]) + ASD(odu.work))
            self.tots[1] = float(ASD(self.tots[1]) + ASD(amt.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
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
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-36s %-7s %45s %5s" % \
            ("Debtors Interest to be Charged up to",
            self.df.t_disp[0][0][0], "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText("%-18s%-10s%-3s%-7s%-2s%-1s" % \
            ("(Options: Cut-Off-", self.df.t_disp[0][0][0], "",
                "Leeway-", self.df.t_disp[0][0][1], ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%3s %7s %-28s %5s %12s %13s %12s %12s" % \
            ("Chn", "Acc-Num", "Debtor", "Terms", "Tot-Balance",
            "Overdue", "Rate", "Interest"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        a = CCD(self.tots[0], "SD", 13.2)
        b = CCD(self.tots[1], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-11s %-48s %13s %-11s %13s" % \
            (" ", "Grand Totals", a.disp, "", b.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
