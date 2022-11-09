"""
SYNOPSIS
    This utility creates pdf files for all tables in the database.

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
from tartanFunctions import doPrinter, getModName, getSingleRecords
from tartanWork import allsys

class tb3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ftable", "ffield"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.head = "Tartan Systems"
        return True

    def mainProcess(self):
        dats = [["ALL", "All Systems"]]
        syss = list(allsys.keys())
        syss.sort()
        for s in syss:
            dats.append((s, allsys[s][0]))
        syss.append("ALL")
        sts = {
            "stype": "C",
            "titl": "Select the Required System",
            "head": ("COD", "System"),
            "data": dats}
        r1s = (("All", "A"), ("System", "S"), ("Singles", "X"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Tables","",
                "X","Y",self.doTab,None,None,None),
            (("T",0,1,0),"IUA",3,"System","",
                "ALL","Y",self.doSys,sts,None,("in", syss)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("N","V"), mail=("Y","N"))

    def doTab(self, frt, pag, r, c, p, i, w):
        self.seltab = w
        if self.seltab != "S":
            self.sys = None
            return "sk1"

    def doSys(self, frt, pag, r, c, p, i, w):
        if w == "MST":
            self.sys = "ctl"
        else:
            self.sys = w

    def doEnd(self):
        self.df.closeProcess()
        self.printReport()
        self.opts["mf"].closeLoop()

    def printReport(self):
        if self.seltab == "X":
            tabs = getSingleRecords(self.opts["mf"], "ftable",
            ("ft_tabl", "ft_desc"), where=[("ft_seq", "=", 1)])
        else:
            whr = [("ft_seq", "=", 1)]
            if self.seltab == "S":
                whr.append(("ft_tabl", "like", self.sys.lower() + "%"))
            tabs = self.sql.getRec("ftable", cols=["ft_tabl",
                "ft_desc"], where=whr, order="ft_tabl")
        if not tabs:
            return
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=80)
        self.pgnum = 0
        p = ProgressBar(self.opts["mf"].body, mxs=len(tabs), esc=True)
        for num, tab in enumerate(tabs):
            p.displayProgress(num)
            if p.quit:
                break
            recs = self.sql.getRec("ffield", where=[("ff_tabl", "=",
                tab[0])], order="ff_seq")
            if not recs:
                continue
            self.doHeading("F", tab[0])
            for rec in recs:
                a = CCD(rec[1], "UI", 3).disp
                b = CCD(rec[2], "NA", 20).disp
                c = CCD(rec[3], "NA", 2).disp
                d = CCD(rec[4], "UD", 6.1).disp
                e = CCD(rec[5], "NA", 30).disp
                f = CCD(rec[6], "NA", 30).disp
                self.fpdf.drawText("%3s %-20s %2s %6s %-30s %-30s" % \
                    (a, b, c, d, e, f))
            recs = self.sql.getRec("ftable", where=[("ft_tabl", "=",
                tab[0])], order="ft_seq")
            if not recs:
                continue
            self.doHeading("I", tab[0])
            for rec in recs:
                a = CCD(rec[1], "NA", 20).disp
                b = CCD(rec[2], "UI", 1).disp
                c = CCD(rec[3], "NA", 1).disp
                d = CCD(rec[4], "NA", 10).disp
                e = CCD(rec[5], "NA", 10).disp
                f = CCD(rec[6], "NA", 10).disp
                g = CCD(rec[7], "NA", 10).disp
                h = CCD(rec[8], "NA", 10).disp
                i = CCD(rec[9], "NA", 10).disp
                j = CCD(rec[10], "NA", 10).disp
                self.fpdf.drawText("%-20s %2s %1s %-10s %-10s %-10s %-10s "\
                    "%-10s %-10s %-10s" % (a, b, c, d, e, f, g, h, i, j))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, 0, ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=1, pdfnam=pdfnam,
                    header="Table Fields and Indexes", repprt=self.df.repprt,
                    repeml=self.df.repeml)

    def doHeading(self, htyp, table):
        self.fpdf.setFont(style="B")
        if htyp == "F":
            self.fpdf.add_page()
            self.pgnum += 1
            self.fpdf.drawText(self.head)
            self.fpdf.drawText()
            self.fpdf.drawText("%-90s %-5s %5s" % ("Table Fields for "\
                "Table %s" % table, "Page", self.pgnum))
            head = "%3s %-20s %2s %6s %-30s %-30s" % ("Seq", "Field Name",
                "Tp", "Size", "Description", "Heading")
        else:
            self.fpdf.drawText()
            self.fpdf.drawText("Table Indexes for Table %s" % table)
            head = "%-20s %2s %1s %-10s %-10s %-10s %-10s %-10s %-10s "\
                "%-10s" % ("Table Description", "Sq", "T", "1st-Col",
                "2nd-Col", "3rd-Col", "4th-Col", "5th-Col", "6th-Col",
                "7th-Col")
        self.fpdf.drawText()
        self.fpdf.drawText(head)
        self.fpdf.underLine(head)
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
