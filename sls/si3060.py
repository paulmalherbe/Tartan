"""
SYNOPSIS
    Sales By Salesman Report.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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

class si3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlrep", "strmf1", "strtrn"],
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
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stock Movement Report (%s)" % self.__class__.__name__)
        rpm = {
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
            (("T",0,0,0),"ID2",7,"Start Period","",
                int(self.sysdtw / 100),"Y",self.doSdate,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"End Period","",
                int(self.sysdtw / 100),"N",self.doEdate,None,None,("efld",)),
            (("T",0,2,0),"INa",3,"Salesman","",
                var[2],"N",self.doRep,rpm,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doSdate(self, frt, pag, r, c, p, i, w):
        self.sdate = w

    def doEdate(self, frt, pag, r, c, p, i, w):
        self.edate = w

    def doRep(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlrep", cols=["rep_name"],
                where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Salesman"
        self.rep = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.rep:
            self.srep = ""
            self.erep = "zzz"
        else:
            self.srep = self.rep
            self.erep = self.rep
        col = ["stt_rep", "stt_group", "stt_code", "stt_loc", "stt_type",
            "stt_ref1", "stt_ref2", "stt_trdt", "stt_desc", "stt_acno",
            "stt_qty", "stt_cost", "stt_sell", "st1_desc"]
        whr = [("stt_cono", "=", self.opts["conum"]), ("stt_cono=st1_cono",),
            ("stt_group=st1_group",), ("stt_code=st1_code",), ("stt_curdt",
            ">=", self.sdate), ("stt_curdt", "<=", self.edate), ("stt_rep",
            ">=", self.srep), ("stt_rep", "<=", self.erep), ("stt_type",
            "in", (7, 8))]
        odr = "stt_rep, stt_type, stt_batch, stt_ref1"
        recs = self.sql.getRec(tables=["strmf1", "strtrn"], cols=col,
            where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-138s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.stot = [0] * 3
        self.gtot = [0] * 3
        old_rep = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.rep = CCD(dat[0], "Na", 3)
            grp = CCD(dat[1], "NA", 3)
            cod = CCD(dat[2], "NA", 20)
            rf1 = CCD(dat[5], "Na", 9)
            rf2 = CCD(dat[6], "Na", 9)
            drs = CCD(dat[9], "NA", 7)
            qty = CCD(float(ASD(0) - ASD(dat[10])), "SD", 11.2)
            cst = CCD(float(ASD(0) - ASD(dat[11])), "SD", 11.2)
            sll = CCD(float(ASD(0) - ASD(dat[12])), "SD", 11.2)
            des = CCD(dat[13], "NA", 30)
            prf = float(ASD(sll.work) - ASD(cst.work))
            prf = CCD(prf, "SD", 11.2)
            if sll.work == 0:
                pcn = 0
            else:
                pcn = round((prf.work * 100.0 / sll.work), 2)
            pcn = CCD(pcn, "SD", 7.2)
            if old_rep and old_rep != self.rep.work:
                self.repTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s %s" % \
                (rf1.disp, "Sls", drs.disp, rf2.disp, grp.disp, cod.disp,
                des.disp, qty.disp, sll.disp, cst.disp, prf.disp, pcn.disp))
            self.pglin += 1
            self.stot[0] = float(ASD(self.stot[0]) + ASD(sll.work))
            self.stot[1] = float(ASD(self.stot[1]) + ASD(cst.work))
            self.gtot[0] = float(ASD(self.gtot[0]) + ASD(sll.work))
            self.gtot[1] = float(ASD(self.gtot[1]) + ASD(cst.work))
            old_rep = self.rep.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.repTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
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
        self.fpdf.drawText("%-30s %-10s" % \
            ("Sales By Salesman Report as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-23s%-7s%-3s%-11s%-7s%-1s" % \
            ("(Options: Start Period ", self.df.t_disp[0][0][0], "",
                "End Period ", self.df.t_disp[0][0][1], ")"))
        self.fpdf.drawText()
        rep = self.sql.getRec("ctlrep", cols=["rep_name"],
            where=[("rep_cono", "=", self.opts["conum"]),
            ("rep_code", "=", self.rep.work)], limit=1)
        if rep:
            repn = rep[0]
        else:
            repn = ""
        self.fpdf.drawText("%-5s %3s %s" % ("Rep", self.rep.disp, repn))
        self.fpdf.drawText()
        self.fpdf.drawText("%-9s %-3s %-7s %-9s %-3s %-20s %-30s%11s %11s " \
            "%11s %11s %7s" % ("Reference", "Typ", "Drs-Num", "Ref-Num-2",
            "Grp", "Product-Code", "Description", "Quantity",
            "Sell-Value", "Cost-Value", "Profit", "Prf-%"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 10

    def repTotal(self):
        sll = CCD(self.stot[0], "SD", 12.2)
        cst = CCD(self.stot[1], "SD", 12.2)
        prf = float(ASD(sll.work) - ASD(cst.work))
        prf = CCD(prf, "SD", 11.2)
        if sll.work == 0:
            pcn = 0
        else:
            pcn = round((prf.work * 100.0 / sll.work), 2)
        pcn = CCD(pcn, "SD", 7.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-56s %-41s %s%s %s %s" % \
            (" ", "Rep Totals", sll.disp, cst.disp, prf.disp, pcn.disp))
        self.fpdf.drawText()
        self.stot = [0] * 2

    def grandTotal(self):
        sll = CCD(self.gtot[0], "SD", 12.2)
        cst = CCD(self.gtot[1], "SD", 12.2)
        prf = float(ASD(sll.work) - ASD(cst.work))
        prf = CCD(prf, "SD", 11.2)
        if sll.work == 0:
            pcn = 0
        else:
            pcn = round((prf.work * 100.0 / sll.work), 2)
        pcn = CCD(pcn, "SD", 7.2)
        self.fpdf.drawText("%-56s %-41s %s%s %s %s" % \
            (" ", "Grand Totals", sll.disp, cst.disp, prf.disp, pcn.disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
