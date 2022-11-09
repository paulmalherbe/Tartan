"""
SYNOPSIS
    Salesmen Sales History Report.

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
from TartanClasses import ASD, Balances, CCD, CreateChart, GetCtl, MyFpdf
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter, showError
from tartanWork import mthnam

class si3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ctlrep",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.fromad = slsctl["ctv_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.mchart = []
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Salesman's Sales History (%s)" % self.__class__.__name__)
        rep = {
            "stype": "R",
            "tables": ("ctlrep",),
            "cols": (
                ("rep_code", "", 0, "Rep"),
                ("rep_name", "", 0, "Name", "Y")),
            "where": [("rep_cono", "=", self.opts["conum"])]}
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", ""]
            view = ("N","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID2",7,"Ending Period","",
                int(self.sysdtw / 100),"Y",self.doDat,None,None,("efld",)),
            (("T",0,1,0),"INa",3,"First Rep Code","",
                var[1],"N",self.doRep1,rep,None,None),
            (("T",0,2,0),"INa",3,"Last Rep Code","",
                var[2],"N",self.doRep2,rep,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doDat(self, frt, pag, r, c, p, i, w):
        self.end = w
        yr = int(w / 100) - 1
        mth = (w % 100) + 1
        if mth > 12:
            yr = yr + 1
            mth = mth - 12
        self.start = (yr * 100) + mth

    def doRep1(self, frt, pag, r, c, p, i, w):
        self.rep1 = w

    def doRep2(self, frt, pag, r, c, p, i, w):
        self.rep2 = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("rep_cono", "=", self.opts["conum"])]
        if self.rep1:
            whr.append(("rep_code", ">=", self.rep1))
        if self.rep2:
            whr.append(("rep_code", "<=", self.rep2))
        recs = self.sql.getRec("ctlrep", cols=["rep_code", "rep_name"],
            where=whr, order="rep_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        else:
            self.mthhead = ""
            space = " " * 11
            y = self.end % 100
            for _ in range(0, 12):
                y = y + 1
                if y == 13:
                    y = 1
                self.mthhead = self.mthhead + \
                    space[:(11 - len(mthnam[y][1]))] + mthnam[y][1]
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-169s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.stots = [0] * 13
        self.ctots = [0] * 13
        self.pglin = 999
        for x1, r1 in enumerate(recs):
            p.displayProgress(x1)
            if p.quit:
                break
            rep = CCD(r1[0], "Na", 3)
            name = CCD(r1[1], "NA", 30)
            bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
                self.end, (rep.work,))
            this, hist = bals.doStrHist(self.start)
            if this == 0:
                continue
            costsd = ""
            salesd = ""
            proftd = ""
            prperd = ""
            prt = False
            mchart = ["T", name.work]
            for x2 in range(11,-1,-1):
                c = float(ASD(0) - ASD(hist[2][x2][1]))
                c = CCD(round(c, 0), "SL", 11)
                s = float(ASD(0) - ASD(hist[2][x2][2]))
                s = CCD(round(s, 0), "SL", 11)
                if c.work or s.work:
                    prt = True
                prf = float(ASD(s.work) - ASD(c.work))
                prf = CCD(round(prf, 0), "SL", 11)
                if s.work == 0:
                    pcn = 0
                else:
                    pcn = round((prf.work * 100.0 / s.work), 2)
                pcn = CCD(pcn, "SD", 11.2)
                self.ctots[x2] = self.ctots[x2] + c.work
                self.stots[x2] = self.stots[x2] + s.work
                costsd = costsd + c.disp
                salesd = salesd + s.disp
                proftd = proftd + prf.disp
                prperd = prperd + pcn.disp
                mchart.append(s.work)
            if not prt:
                continue
            self.mchart.append(mchart)
            if self.pglin > (self.fpdf.lpp - 5):
                self.pageHeading()
            self.fpdf.drawText("%s %s %-6s %s" % (rep.disp, name.disp,
                "Sales", salesd))
            self.fpdf.drawText("%-34s %-6s %s" % ("", "Costs ", costsd))
            self.fpdf.drawText("%-34s %-6s %s" % ("", "Profit", proftd))
            self.fpdf.drawText("%-34s %-6s %s" % ("", "Prf-% ", prperd))
            self.fpdf.underLine(txt=self.head)
            self.pglin += 5
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)
                CreateChart(self.opts["mf"], self.opts["conum"],
                    self.opts["conam"], [self.start, self.end],
                    [[self.opts["conam"], "Saleman's Sales History"],
                    "Values"], None, self.mchart)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        per = CCD(self.end, "D2", 7)
        self.fpdf.drawText("%-29s %-7s" % \
            ("Salesman's Sales History up to", per.disp))
        self.fpdf.drawText()
        if self.rep1:
            opt = "(Options: From Rep %s" % self.rep1
        else:
            opt = "(Options: From First Rep"
        if self.rep2:
            opt = "%s To Rep %s)" % (opt, self.rep2)
        else:
            opt = "%s To Last Rep)" % opt
        self.fpdf.drawText(opt)
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-37s%-13s" % ("Rep", "Name", self.mthhead))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        costsd = ""
        salesd = ""
        proftd = ""
        prperd = ""
        mchart = ["T", "Grand Totals"]
        for x in range(11,-1,-1):
            c = CCD(self.ctots[x], "SL", 11)
            s = CCD(self.stots[x], "SL", 11)
            prf = float(ASD(s.work) - ASD(c.work))
            prf = CCD(prf, "SL", 11)
            if s.work == 0:
                pcn = 0
            else:
                pcn = round((prf.work * 100.0 / s.work), 2)
            pcn = CCD(pcn, "SD", 11.2)
            self.ctots[x] = self.ctots[x] + c.work
            self.stots[x] = self.stots[x] + s.work
            costsd = costsd + c.disp
            salesd = salesd + s.disp
            proftd = proftd + prf.disp
            prperd = prperd + pcn.disp
            mchart.append(s.work)
        self.mchart.append(mchart)
        self.fpdf.drawText("%-3s %-6s %30s %s" % ("", "Totals", "Sales ",
            salesd))
        self.fpdf.drawText("%-34s %s %s" % ("", "Costs ", costsd))
        self.fpdf.drawText("%-34s %s %s" % ("", "Profit", proftd))
        self.fpdf.drawText("%-34s %s %s" % ("", "Prf-% ", prperd))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
