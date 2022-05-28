"""
SYNOPSIS
    General Ledger Check Intercompany Balances.

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

from TartanClasses import ASD, CCD, MyFpdf, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter

class gl6040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genint", "genbal",
            "gentrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        recs = self.sql.getRec("genint", cols=["cti_inco", "cti_acno"],
            where=[("cti_cono", "=", self.opts["conum"])], order="cti_inco")
        if not recs:
            return
        self.accs = []
        for acc in recs:
            acn = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", acc[0]), ("cti_inco", "=",
                self.opts["conum"])], limit=1)
            if acn:
                self.accs.append([acc[0], acc[1], acn[0]])
        self.s_per = int(self.opts["period"][1][0] / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Check Intercompany Accounts (%s)" % self.__class__.__name__)
        fld = (
            (("T",0,0,0),"ID1",10,"Reporting Date","",
                self.opts["period"][2][0],"N",self.doRepDte,None,None,None),)
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doRepDte(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.e_per = int(w / 100)

    def doEnd(self):
        self.printReport()
        self.doExit()

    def printReport(self):
        self.head = "%03u %-80s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        for acc in self.accs:
            if self.fpdf.newPage():
                self.pageHeading()
            n = self.sql.getRec("ctlmst", cols=["ctm_name"],
                where=[("ctm_cono", "=", acc[0])], limit=1)
            if not n:
                continue
            n = CCD(n[0], "NA", 30)
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                acc[1]), ("glo_trdt", "=", self.opts["period"][1][0])],
                limit=1)
            if o:
                b = CCD(o[0], "SD", 13.2)
            else:
                b = CCD(0, "SD", 13.2)
            bal1 = b.work
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", acc[1]), ("glt_curdt",
                ">=", self.s_per), ("glt_curdt", "<=", self.e_per)], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 13.2)
            else:
                b = CCD(0, "SD", 13.2)
            bal1 = float(ASD(bal1) + ASD(b.work))
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", acc[0]), ("glo_acno", "=", acc[2]),
                ("glo_trdt", "=", self.opts["period"][1][0])], limit=1)
            if o:
                b = CCD(o[0], "SD", 13.2)
            else:
                b = CCD(0, "SD", 13.2)
            bal2 = b.work
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                acc[0]), ("glt_acno", "=", acc[2]), ("glt_curdt", ">=",
                self.s_per), ("glt_curdt", "<=", self.e_per)], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 13.2)
            else:
                b = CCD(0, "SD", 13.2)
            bal2 = float(ASD(bal2) + ASD(b.work))
            a0 = CCD(acc[0], "UI", 3)
            a1 = CCD(bal1, "SD", 13.2)
            a2 = CCD(bal2, "SD", 13.2)
            a = float(ASD(a1.work) + ASD(a2.work))
            a3 = CCD(a, "SD", 13.2)
            self.fpdf.drawText("%-3s %-32s %15s %15s %15s" % (a0.disp,
                n.disp, a1.disp, a2.disp, a3.disp))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header=self.tit, repprt=self.df.repprt, repeml=self.df.repeml)
        self.doExit()

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-40s %-10s" %
            ("General Ledger Intercompany Balances as at",
            self.df.t_disp[0][0][0]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-32s%15s %15s %15s" %
            ("Coy", "Company-Name", "Balance-1", "Balance-2", "Difference"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
