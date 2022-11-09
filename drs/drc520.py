"""
SYNOPSIS
    Debtors Messages Listing.

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
from TartanClasses import CCD, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, textFormat, doPrinter, showError

class drc520(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ctlmes",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.mtyp = "S"
        return True

    def mainProcess(self):
        self.tit = "Messages Master Listing (%s)" % self.__class__.__name__
        r1s = (("All Types","A"),("Invoice","I"),("Statement","S"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Message Type","",
                "I","Y",self.doType,None,None,None),)
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"))

    def doType(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.mtyp = "ALL"
        elif w == "I":
            self.mtyp = "INV"
        else:
            self.mtyp = "STA"

    def doEnd(self):
        if self.mtyp != "ALL":
            recs = self.sql.getRec("ctlmes", where=[("mss_system",
                "=", self.mtyp)], order="mss_system, mss_message")
        else:
            recs = self.sql.getRec("ctlmes", where=[("mss_system",
                "in", ("INV", "STA"))], order="mss_system, mss_message")
        if not recs:
            showError(self.opts["mf"].body, "Error",
                "No Records Available")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%-75s" % "Tartan Systems"
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        old_sys = recs[0][0]
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.sys = CCD(dat[0], "NA", 3)
            mes = CCD(dat[1], "UI", 3)
            det = CCD(dat[2], "NA", 150)
            fmt = textFormat(det.work, width=30)
            if len(fmt) > 5:
                l = 5
            else:
                l = len(fmt)
            if old_sys != self.sys.work:
                old_sys = self.sys.work
                self.pglin = self.fpdf.lpp
            if self.pglin > (self.fpdf.lpp - 5):
                self.pageHeading()
            self.fpdf.drawText("%-14s %s %-10s %s" % ("", mes.disp, "",
                fmt[0]))
            self.pglin += 1
            for q in range(1, len(fmt)):
                self.fpdf.drawText("%-29s %s" % ("", fmt[q]))
                self.pglin += 1
            self.fpdf.drawText()
            for r in range(l, 5):
                fmt.append("")
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, 0, ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], pdfnam=pdfnam, header=self.tit,
                    repprt=self.df.repprt)
        self.closeProcess()

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.sys.work == "INV":
            desc = "Debtors  Invoice  Messages as at"
        else:
            desc = "Debtors Statement Messages as at"
        self.fpdf.drawText("%-32s %-42s" % (desc, self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-14s %-3s %-10s %-30s" % ("", "Num",
            "", "Message"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
