"""
SYNOPSIS
    Rental Owners Master Listing.

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

class rc3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcaowm", "rcaowt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.fromad = rcactl["cte_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Rental Owners Master Report (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"Id2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"Y",self.doCutOff,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Totals Only","",
                "Y","Y",self.doTots,None,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Zero Balances",
                "Include Zero Balances","N","Y",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doCutOff(self, frt, pag, r, c, p, i, w):
        self.cutoff = w
        self.opts["period"] = self.df.t_disp[pag][r][p]

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if self.totsonly == "Y":
            self.zero = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.zero)
            return "sk1"

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        recs = self.sql.getRec("rcaowm", cols=["rom_acno", "rom_name"],
            where=[("rom_cono", "=", self.opts["conum"])], order="rom_acno")
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Accounts Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-71s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.tots = 0
        self.pglin = 999
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            acc = CCD(rec[0], "NA", 7)
            name = CCD(rec[1], "NA", 30)
            bals = self.sql.getRec("rcaowt", cols=["sum(rot_tramt)"],
                where=[("rot_cono", "=", self.opts["conum"]), ("rot_acno", "=",
                acc.work), ("rot_curdt", "<=", self.cutoff)], limit=1)
            if self.zero == "N" and not bals[0]:
                continue
            bal = CCD(bals[0], "SD", 13.2)
            if self.totsonly != "Y":
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                self.fpdf.drawText("%s %-53s %s" % (acc.disp, name.disp,
                    bal.disp))
                self.pglin += 1
            self.tots = float(ASD(self.tots) + ASD(bal.work))
        p.closeProgress()
        if p.quit:
            return
        if self.totsonly == "Y":
            self.pageHeading()
        if self.fpdf.page:
            self.grandTotal()
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
        self.fpdf.drawText("%-33s %-7s" % ("Rental Owners Master "\
            "Report up to", self.opts["period"]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-27s%-1s%-1s" % ("(Options: "\
            "Include-Zero-Bal: ", self.df.t_disp[0][0][2], ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-53s %13s" % ("Acc-Num", "Name", "Balance "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        self.fpdf.drawText()
        t = CCD(self.tots, "SD", 13.2)
        self.fpdf.drawText("%-7s %-53s %13s" % (" ", "Grand Totals", t.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
