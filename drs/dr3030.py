"""
SYNOPSIS
    Debtors Ledger Transactions Due For Payment.

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
from tartanWork import drtrtp
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getTrn, getModName, showError

class dr3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsmst", "drstrn"],
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
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Debtors Transactions Due For Payment (%s)" %
                self.__class__.__name__)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            view = None
            mail = None
        else:
            view = ("N","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID1",10,"Payment Date","",
                self.sysdtw,"Y",self.doPayDate,None,None,("efld",)),)
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doPayDate(self, frt, pag, r, c, p, i, w):
        if w == 0:
            w = self.sysdtw
        self.pdatw = w
        self.pdatd = self.df.t_disp[0][0][0]
        self.df.loadEntry(frt, pag, p, data=self.pdatw)

    def doEnd(self):
        self.df.closeProcess()
        mst = self.sql.getRec("drsmst", cols=["drm_chain", "drm_acno",
            "drm_name"], where=[("drm_cono", "=", self.opts["conum"])],
            order="drm_chain, drm_acno")
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
        self.head = "%03u %-71s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.ctots = [0,0,0]
        self.gtots = [0,0,0]
        self.pglin = 999
        for seq, rec in enumerate(mst):
            p.displayProgress(seq)
            if p.quit:
                break
            chn = CCD(rec[0], "UI", 3)
            acno = CCD(rec[1], "NA", 7)
            name = CCD(rec[2], "NA", 30)
            col, trns = getTrn(self.opts["mf"].dbm, "drs", whr=[("drt_cono",
                "=", self.opts["conum"]), ("drt_chain", "=", chn.work),
                ("drt_acno", "=", acno.work), ("drt_trdt", "<=", self.pdatw)],
                neg=False, zer="N")
            if not trns:
                continue
            if self.pglin == 999:
                self.pageHeading(chn.disp, acno.disp, name.disp)
            else:
                self.newAccount(chn.disp, acno.disp, name.disp)
            for trn in trns:
                ref1 = CCD(trn[col.index("drt_ref1")], "Na", 9)
                ref2 = CCD(trn[col.index("drt_ref2")], "Na", 9)
                trtp = CCD(trn[col.index("drt_type")], "UI", 1)
                trdt = CCD(trn[col.index("drt_trdt")], "d1", 10)
                tramt = CCD(trn[col.index("drt_tramt")], "SD", 13.2)
                paid = CCD(trn[col.index("paid")], "SD", 13.2)
                trbal = CCD(trn[col.index("balance")], "SD", 13.2)
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading(chn.disp, acno.disp, name.disp)
                self.fpdf.drawText("%s %s %s %s %s %s %s" % (ref1.disp,
                    ref2.disp, drtrtp[trtp.work-1][0], trdt.disp,
                    tramt.disp, paid.disp, trbal.disp))
                self.pglin += 1
                self.ctots[0] = float(ASD(self.ctots[0]) + ASD(tramt.work))
                self.ctots[1] = float(ASD(self.ctots[1]) + ASD(paid.work))
                self.ctots[2] = float(ASD(self.ctots[2]) + ASD(trbal.work))
                self.gtots[0] = float(ASD(self.gtots[0]) + ASD(tramt.work))
                self.gtots[1] = float(ASD(self.gtots[1]) + ASD(paid.work))
                self.gtots[2] = float(ASD(self.gtots[2]) + ASD(trbal.work))
            if self.fpdf.page:
                self.accountTotal()
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

    def pageHeading(self, chn, acno, name):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-42s %-32s" % \
            ("Debtors Transactions Due For Payment as at", self.pdatd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-19s%-10s%-1s" % \
            ("(Options: Pay Date-", self.df.t_disp[0][0][0], ")"))
        self.fpdf.setFont()
        self.pglin = 5
        self.newAccount(chn, acno, name)

    def newAccount(self, chn, acno, name):
        if self.pglin > (self.fpdf.lpp - 10):
            self.pageHeading(chn, acno, name)
        else:
            self.fpdf.setFont(style="B")
            self.fpdf.underLine(txt=self.head)
            self.fpdf.drawText("%-7s %-3s %-7s %-30s" % \
                ("Account", chn, acno, name))
            self.fpdf.drawText()
            self.fpdf.drawText("%-9s %-9s %-3s %-10s %-13s %-13s %-13s" % \
                ("Reference", "Ref-Num-2", "Typ", "   Date",
                "      Amount", "        Paid", "     Balance"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 5

    def accountTotal(self):
        j = CCD(self.ctots[0], "SD", 13.2)
        k = CCD(self.ctots[1], "SD", 13.2)
        l = CCD(self.ctots[2], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-13s %13s %13s" % \
            ("Account Totals", j.disp, k.disp, l.disp))
        self.ctots = [0,0,0]
        self.pglin += 2

    def grandTotal(self):
        j = CCD(self.gtots[0], "SD", 13.2)
        k = CCD(self.gtots[1], "SD", 13.2)
        l = CCD(self.gtots[2], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %13s %-13s %13s" % \
            ("Grand Totals", j.disp, k.disp, l.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
