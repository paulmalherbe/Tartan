"""
SYNOPSIS
    Salaries and Wages Data Capture Listing.

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
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter, showError

class wg3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagcap", "wagmst", "wagedc"],
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
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        return True

    def doProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Salaries Data Capture Listing (%s)" % self.__class__.__name__)
        fld = (
            (("T",0,0,0),"ID1",10,"Reporting Date","",
                self.sysdtw,"Y",self.doDate,None,None,("efld",)),)
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = self.df.t_disp[0][0][0]

    def doEnd(self):
        self.df.closeProcess()
        recs = self.sql.getRec(tables=["wagcap", "wagmst", "wagedc"],
            cols=["wcp_empno", "wcp_dept", "wcp_job", "wcp_type", "wcp_code",
            "wcp_ind", "wcp_amt", "wgm_sname", "wgm_fname", "ced_desc"],
            where=[("wcp_cono", "=", self.opts["conum"]),
            ("wcp_cono=wgm_cono",), ("wcp_empno=wgm_empno",),
            ("ced_cono=wcp_cono",), ("ced_type=wcp_type",),
            ("ced_code=wcp_code",), ("wcp_paid", "=", "N")],
            order="wcp_empno, wcp_type desc, wcp_code")
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Available")
        else:
            self.doPrintReport(recs)
        self.closeProcess()

    def doPrintReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %10s %49s %10s %10s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm, "", self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        old_empno = 0
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            emp = CCD(dat[0], "UI", 5)
            nam = CCD("%s, %s" % (dat[7].strip(), dat[8].strip()), "NA", 50)
            dep = CCD(dat[1], "UI", 1)
            job = CCD(dat[2], "UI", 5)
            typ = CCD(dat[3], "UA", 1)
            cod = CCD(dat[4], "UI", 3)
            des = CCD(dat[9], "NA", 30)
            ind = CCD(dat[5], "UA", 1)
            amt = CCD(dat[6], "SD", 13.2)
            if old_empno and old_empno != emp.work:
                self.fpdf.drawText()
                self.pglin += 1
            if self.pglin > self.fpdf.lpp:
                self.doPageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s  %s" % (emp.disp,
                nam.disp, dep.disp, job.disp, typ.disp, cod.disp,
                des.disp, ind.disp, amt.disp))
            old_empno = emp.work
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def doPageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-35s %-10s %64s %5s" % (
            "Salaries Data Capture Report as at", self.date,
            "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText(
            "%-5s %-50s %-1s %-5s %-1s %-3s %-30s %-1s %13s" % ("EmpNo",
            "Name", "D", "JobNo", "T", "Cod", "Description", "I", "Amount"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
