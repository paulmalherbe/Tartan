"""
SYNOPSIS
    Creditors Ledger Purchase History.

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
from TartanClasses import Balances, CCD, CreateChart, GetCtl, MyFpdf
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import doWriteExport, getModName, doPrinter, showError
from tartanWork import mthnam

class cr3110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "crsmst",
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
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            "%s"))
        self.forms = [("NA", 7), ("NA", 30)] + [("SI", 10)] * 12
        self.gtots = [0] * 12
        self.mchart = []
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditor's Purchase History (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Ending Period","",
                int(self.sysdtw / 100),"Y",self.doDat,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Ignore Zero Purch","",
                "Y","Y",self.doZer,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDat(self, frt, pag, r, c, p, i, w):
        self.coffw = w
        self.coffd = self.df.t_disp[pag][r][p]

    def doZer(self, frt, pag, r, c, p, i, w):
        self.zer = w

    def doEnd(self):
        self.df.closeProcess()
        recs = self.sql.getRec("crsmst", cols=["crm_acno", "crm_name"],
            where=[("crm_cono", "=", self.opts["conum"])], order="crm_acno")
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        else:
            self.start = self.coffw - 99
            if self.start % 100 == 13:
                self.start = self.start + 88
            s = self.start % 100
            self.mthhead = ""
            self.colsh = ["Acc-Num", "Name"]
            for _ in range(12):
                if self.mthhead:
                    self.mthhead = "%s %9s " % (self.mthhead, mthnam[s][1])
                else:
                    self.mthhead = "%9s " % mthnam[s][1]
                self.colsh.append(mthnam[s][1])
                s += 1
                if s == 13:
                    s = 1
            if self.df.repprt[2] == "export":
                self.exportReport(recs)
            else:
                self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Creditor's Purchase History for the 12 Months "\
            "Period to %s" % self.coffd)
        self.expheads.append("Options: Ignore-Zeros %s" % self.zer)
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            line = ["BODY", [vals[0].work, vals[1].work]]
            for val in vals[3]:
                line[1].append(val)
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        pad = chrs - 35 - len(self.sysdttm)
        self.head1 = self.head % (" " * pad + self.sysdttm)
        self.head2 = "Creditor's Purchase History for the 12 Months "\
            "Period to %s%s" % (self.coffd, "%s%s")
        pad = chrs - len(self.head2) + 4 - 11  # %s%s and ' Page     1'
        self.head2 = self.head2 % (" " * pad, " Page %5s")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head2)
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s" % (vals[0].disp, vals[1].disp,
                vals[2]))
            self.pglin += 1
        p.closeProgress()
        if not self.fpdf.page or p.quit:
            return
        self.grandTotal()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header=self.tit, repprt=self.df.repprt, fromad=self.fromad,
            repeml=self.df.repeml)
        if self.df.repprt[1] == "X":
            return
        CreateChart(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            [self.start, self.coffw], [[self.opts["conam"], "Purchase History"],
            "Values"], None, self.mchart)

    def getValues(self, data):
        acc = CCD(data[0], "NA", 7)
        name = CCD(data[1], "NA", 30)
        bals = Balances(self.opts["mf"], "CRS", self.opts["conum"], self.coffw,
            (acc.work,))
        this, hist = bals.doCrsDrsHist()
        if not this:
            return
        purchd = ""
        purchw = []
        purtot = 0
        for x in range(11, -1, -1):
            amt = CCD(round(hist[0][x], 0), "SI", 10)
            self.gtots[x] = self.gtots[x] + amt.work
            purtot = purtot + amt.work
            if purchd:
                purchd = "%s %9s" % (purchd, amt.disp)
            else:
                purchd = "%9s" % amt.disp
            purchw.append(amt.work)
        if self.zer == "Y" and purtot == 0:
            return
        return acc, name, purchd, purchw

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2 % self.pgnum)
        self.fpdf.drawText()
        self.fpdf.drawText("(%-23s%1s)" % ("Options: Ignore Zeros:-",
            self.zer))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %s" % ("Acc-Num", "Name", self.mthhead))
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head1)))
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "Grand Totals"] + self.gtots])
            self.expdatas.append(["ULINED"])
            return
        purchd = ""
        mchart = ["T", "Grand Totals"]
        for x in range(11,-1,-1):
            a = CCD(self.gtots[x], "SI", 10)
            if purchd:
                purchd = "%s %s" % (purchd, a.disp)
            else:
                purchd = "%s" % a.disp
            mchart.append(a.work)
        self.mchart.append(mchart)
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head1)))
        self.fpdf.drawText("%-7s %-30s %s" % (" ", "Grand Totals", purchd))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
