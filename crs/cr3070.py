"""
SYNOPSIS
    Creditors Ledger Reconciliation Statements.

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
from tartanWork import crtrtp
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getTrn, getModName, getSingleRecords
from tartanFunctions import showError

class cr3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
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
            "Reconciliation Statements (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("Singles","S"))
        r2s = (("Number","N"),("Name","M"))
        fld = (
            (("T",0,0,0),"ID2",7,"Period","",
                self.curdt,"Y",self.doPeriod,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doPeriod(self, frt, pag, r, c, p, i, w):
        self.curdt = w
        self.curdd = self.df.t_disp[pag][0][i]

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole == "S":
            return "sk1"

    def doSort(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.sort = "crm_acno"
        else:
            self.sort = "crm_name"

    def doEnd(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.prnt = "N"
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "crsmst", ("crm_acno",
                "crm_name"), where=[("crm_cono", "=", self.opts["conum"])])
        else:
            recs = self.sql.getRec("crsmst", where=[("crm_cono",
                "=", self.opts["conum"])], order=self.sort)
            if not recs:
                showError(self.opts["mf"].body, "Error",
                "No Accounts Available")
        if recs:
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(rec)
            p.closeProgress()
        if self.prnt == "Y" and self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField("T", 0, 1)

    def doProcess(self, crm):
        self.pgnum = 0
        self.totbal = 0
        cmc = self.sql.crsmst_col
        self.acno = CCD(crm[cmc.index("crm_acno")], "NA", 7)
        whr = [
            ("crt_cono", "=", self.opts["conum"]),
            ("crt_acno", "=", self.acno.work)]
        odr = "crt_curdt, crt_trdt, crt_ref1"
        self.ctc, self.crt = getTrn(self.opts["mf"].dbm, "crs", cdt=self.curdt,
            whr=whr, odr=odr)
        if self.crt:
            if self.prnt == "N":
                self.printSetup()
            self.name = CCD(crm[cmc.index("crm_name")], "NA", 30)
            self.add1 = CCD(crm[cmc.index("crm_add1")], "NA", 30)
            self.add2 = CCD(crm[cmc.index("crm_add2")], "NA", 30)
            self.add3 = CCD(crm[cmc.index("crm_add3")], "NA", 30)
            self.pcod = CCD(crm[cmc.index("crm_pcod")], "NA", 4)
            self.terms = CCD(crm[cmc.index("crm_terms")], "UI", 3)
            self.termsb = CCD(crm[cmc.index("crm_termsb")], "NA", 1)
            self.stday = CCD(crm[cmc.index("crm_stday")], "UI", 2)
            self.pydis = CCD(crm[cmc.index("crm_pydis")], "SD", 7.2)
            self.printHeader()
            self.printBody()

    def printSetup(self):
        self.head = "%03u %-102s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.prnt = "Y"

    def printHeader(self):
        self.fpdf.add_page()
        self.pgnum += 1
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-42s %-34s %-18s %-7s" % \
            (self.name.disp, "", "Acc-Num:", self.acno.disp))
        self.fpdf.drawText("%-42s %-34s %-18s %-7s" % \
            (self.add1.disp, "", "Period", self.curdd))
        self.fpdf.drawText("%-42s %-34s %-24s %-5s" % \
            (self.add2.disp, "", "Page:", self.pgnum))
        self.fpdf.drawText("%-42s %-34s %-15s %-10s" % \
            (self.add3.disp, "", "", ""))
        self.fpdf.drawText("%-42s %-34s" % \
            (self.pcod.disp, ""))
        self.fpdf.drawText()
        self.fpdf.drawText("%-11s %-17s %-5s %-17s %-14s %-20s %-6s %-7s" % \
            ("Terms Base:", self.termsb.disp, "Days:", self.terms.disp,
            "Statement Day:", self.stday.disp, "Disc-%:", self.pydis.disp))
        self.fpdf.drawText()
        self.fpdf.drawText("%-10s  %-9s  %-9s  %-16s %-13s %-13s %-13s "\
            "%-13s" % ("   Date", "Reference", "Ref-Num-2", "Type",
            "Orig-Amount", "Paid-Amount", " Bal-Amount", "    Balance"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        if self.pgnum > 1:
            j = CCD(self.totbal, "SD", 13.2)
            self.fpdf.drawText("%-31s %-5s %-67s %s" % \
                ("", "B/Fwd", "", j.disp))
            self.pglin = 11
        else:
            self.pglin = 10
        self.fpdf.setFont()

    def printBody(self):
        for tr in self.crt:
            trtp = CCD(tr[self.ctc.index("crt_type")], "UI", 1)
            ref1 = CCD(tr[self.ctc.index("crt_ref1")], "Na", 9)
            ref2 = CCD(tr[self.ctc.index("crt_ref2")], "Na", 9)
            trdt = CCD(tr[self.ctc.index("crt_trdt")], "d1", 10)
            tramt = CCD(tr[self.ctc.index("crt_tramt")], "SD", 13.2)
            pay = CCD(tr[self.ctc.index("paid")], "SD", 13.2)
            bal = CCD(tr[self.ctc.index("balance")], "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.printHeader()
            self.totbal = float(ASD(self.totbal) + ASD(bal.work))
            totbal = CCD(self.totbal, "SD", 13.2)
            typ = crtrtp[trtp.work-1][1]+(" "*(15-len(crtrtp[trtp.work-1][1])))
            self.fpdf.drawText("%s  %s  %s  %s %s %s %s %s" % (trdt.disp,
                ref1.disp, ref2.disp, typ, tramt.disp, pay.disp, bal.disp,
                totbal.disp))
            self.pglin += 1

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
