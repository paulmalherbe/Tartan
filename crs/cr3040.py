"""
SYNOPSIS
    Creditors Ledger Outstanding Transactions.

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
from tartanFunctions import doPrinter, getTrn, getModName, showError
from tartanWork import crtrtp

class cr3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Outstanding Transactions (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["Y", "N"]
            view = ("N","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID2",7,"Report Period","",
                self.curdt,"Y",self.doRepPer,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Account per Page","",
                var[1],"N",self.doNewPage,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doRepPer(self, frt, pag, r, c, p, i, w):
        if w:
            self.curdt = w
        self.curdd = self.df.t_disp[0][0][0]

    def doNewPage(self, frt, pag, r, c, p, i, w):
        self.npag = w

    def doEnd(self):
        self.df.closeProcess()
        mst = self.sql.getRec("crsmst", cols=["crm_acno", "crm_name"],
            where=[("crm_cono", "=", self.opts["conum"])], order="crm_acno")
        if not mst:
            showError(self.opts["mf"].body, "Selection Error",
            "No Accounts Selected")
        else:
            self.printReport(mst)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def printReport(self, mst):
        p = ProgressBar(self.opts["mf"].body, mxs=len(mst), esc=True)
        self.head = "%03u %-102s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.ctots = [0,0,0,0]
        self.gtots = [0,0,0,0]
        self.pglin = 999
        for num, rec in enumerate(mst):
            p.displayProgress(num)
            if p.quit:
                break
            acno = CCD(rec[0], "NA", 7)
            name = CCD(rec[1], "NA", 30)
            col, recs = getTrn(self.opts["mf"].dbm, "crs", dte=self.curdt,
                whr=[("crt_cono", "=", self.opts["conum"]), ("crt_acno", "=",
                acno.work)], zer="N")
            if not recs:
                continue
            if self.pglin == 999:
                self.pageHeading(acno.disp, name.disp)
            else:
                self.newAccount(acno.disp, name.disp)
            for dat in recs:
                ref1 = CCD(dat[col.index("crt_ref1")], "Na", 9)
                ref2 = CCD(dat[col.index("crt_ref2")], "Na", 9)
                trtp = CCD(dat[col.index("crt_type")], "UI", 2)
                trdt = CCD(dat[col.index("crt_trdt")], "d1", 10)
                if dat[col.index("crt_desc")] == name.work:
                    desc = CCD("", "NA", 30)
                else:
                    desc = CCD(dat[col.index("crt_desc")], "NA", 30)
                tramt = CCD(dat[col.index("crt_tramt")], "SD", 13.2)
                paid = CCD(dat[col.index("paid")], "SD", 13.2)
                trbal = CCD(dat[col.index("balance")], "SD", 13.2)
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading(acno.disp, name.disp)
                self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (ref1.disp,
                    ref2.disp, crtrtp[trtp.work-1][0], trdt.disp,
                    desc.disp, tramt.disp, paid.disp, trbal.disp))
                self.pglin += 1
                self.ctots[0] = self.ctots[0] + 1
                self.ctots[1] = float(ASD(self.ctots[1]) + ASD(tramt.work))
                self.ctots[2] = float(ASD(self.ctots[2]) + ASD(paid.work))
                self.ctots[3] = float(ASD(self.ctots[3]) + ASD(trbal.work))
                self.gtots[0] = self.gtots[0] + 1
                self.gtots[1] = float(ASD(self.gtots[1]) + ASD(tramt.work))
                self.gtots[2] = float(ASD(self.gtots[2]) + ASD(paid.work))
                self.gtots[3] = float(ASD(self.gtots[3]) + ASD(trbal.work))
            if self.fpdf.page:
                self.accountTotal()
            if self.npag == "Y":
                self.pglin = 999
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self, acno, name):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-42s %-64s" % \
            ("Creditors Outstanding Transactions as at", self.curdd))
        self.fpdf.setFont()
        self.pglin = 3
        self.newAccount(acno, name)

    def newAccount(self, acno, name):
        if self.pglin > (self.fpdf.lpp - 10):
            self.pageHeading(acno, name)
        else:
            self.fpdf.setFont(style="B")
            self.fpdf.underLine(txt=self.head)
            self.fpdf.drawText("%-7s %-7s %-30s" % ("Account", acno, name))
            self.fpdf.drawText()
            self.fpdf.drawText("%-9s %-9s %-3s %-10s %-30s %-13s %-13s "\
                "%-13s" % ("Reference", "Ref-Num-2", "Typ", "   Date",
                "Details", "      Amount", "        Paid", "     Balance"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 5

    def accountTotal(self):
        j = CCD(self.ctots[0], "SI", 7)
        k = CCD(self.ctots[1], "SD", 13.2)
        l = CCD(self.ctots[2], "SD", 13.2)
        m = CCD(self.ctots[3], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-57s %7s %13s %13s %13s" % \
            ("Account Totals", j.disp, k.disp, l.disp, m.disp))
        self.ctots = [0,0,0,0]
        self.pglin += 2

    def grandTotal(self):
        j = CCD(self.gtots[0], "SI", 7)
        k = CCD(self.gtots[1], "SD", 13.2)
        l = CCD(self.gtots[2], "SD", 13.2)
        m = CCD(self.gtots[3], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-57s %7s %13s %13s %13s" % \
            ("Grand Totals", j.disp, k.disp, l.disp, m.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
