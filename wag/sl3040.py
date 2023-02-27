"""
SYNOPSIS
    Staff Loans Statements.

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
from tartanFunctions import doPrinter, getModName, getSingleRecords
from tartanFunctions import showError
from tartanWork import sltrtp

class sl3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagmst", "waglmf", "wagltf"],
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
        self.head = "%03u %-118s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        return True

    def mainProcess(self):
        r1s = (("Yes","Y"),("Singles","S"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"Id1",10,"Start Date","",
                "","Y",self.doFdate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Last Date","",
                self.sysdtw,"Y",self.doLdate,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Ignore Paid Ups","",
                "Y","Y",self.doPaidup,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doFdate(self, frt, pag, r, c, p, i, w):
        self.fdate = w

    def doLdate(self, frt, pag, r, c, p, i, w):
        self.ldate = w
        self.dated = self.df.t_disp[pag][0][p]

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doPaidup(self, frt, pag, r, c, p, i, w):
        self.paidup = w

    def doEnd(self):
        self.df.closeProcess()
        if self.whole == "S":
            col = [
                "wlm_empno", "wgm_sname", "wgm_fname", "wlm_loan", "wlm_desc"]
            whr = [
                ("wlm_cono", "=", self.opts["conum"]),
                ("wgm_cono=wlm_cono",), ("wgm_empno=wlm_empno",)]
            dic = {}
            dic["wlm_empno"] = self.sql.waglmf_dic["wlm_empno"]
            dic["wlm_loan"] = self.sql.waglmf_dic["wlm_loan"]
            dic["wlm_desc"] = self.sql.waglmf_dic["wlm_desc"]
            dic["wgm_sname"] = self.sql.wagmst_dic["wgm_sname"]
            dic["wgm_fname"] = self.sql.wagmst_dic["wgm_fname"]
            dat = self.sql.getRec(tables=["waglmf", "wagmst"], cols=col,
                where=whr, order="wlm_empno, wlm_loan")
            get = getSingleRecords(self.opts["mf"], "waglmf", col,
                where=dat, ttype="D", dic=dic)
            if get:
                acc = []
                for g in get:
                    acc.append(g[0])
                whr = [
                    ("wlm_cono", "=", self.opts["conum"]),
                    ("wlm_empno", "in", acc)]
                odr = "wlm_empno, wlm_loan"
                recs = self.sql.getRec("waglmf", where=whr, order=odr)
            else:
                recs = None
        else:
            whr = [("wlm_cono", "=", self.opts["conum"])]
            odr = "wlm_empno, wlm_loan"
            recs = self.sql.getRec("waglmf", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Error",
                "No Accounts Selected")
        else:
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, emp in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(emp)
            p.closeProgress()
            if self.fpdf.page and not p.quit and self.df.repeml[1] == "N":
                self.doPrint()
        self.opts["mf"].closeLoop()

    def doProcess(self, emp):
        self.totbal = 0
        wlc = self.sql.waglmf_col
        self.emp = CCD(emp[wlc.index("wlm_empno")], "UI", 5)
        whr = [
            ("wgm_cono", "=", self.opts["conum"]),
            ("wgm_empno", "=", self.emp.work)]
        col = ("wgm_sname", "wgm_fname", "wgm_emadd")
        mst = self.sql.getRec("wagmst", where=whr, cols=col, limit=1)
        self.nam = CCD(mst[0] + ", " + mst[1], "NA", 60)
        self.lon = CCD(emp[wlc.index("wlm_loan")], "UI", 2)
        self.des = CCD(emp[wlc.index("wlm_desc")], "NA", 30)
        whr = [
            ("wlt_cono", "=", self.opts["conum"]),
            ("wlt_empno", "=", self.emp.work),
            ("wlt_loan", "=", self.lon.work)]
        col = ("wlt_trdt", "wlt_type", "wlt_ref", "wlt_batch", "wlt_per",
            "wlt_amt", "wlt_ded", "wlt_desc")
        odr = "wlt_trdt, wlt_type, wlt_ref"
        wlt = self.sql.getRec("wagltf", where=whr, cols=col, order=odr)
        if wlt:
            self.loadBalances(wlt)
            if self.paidup == "Y" and not self.cbal:
                pass
            else:
                self.printHeader()
                self.printBody(wlt)
                if self.df.repeml[1] == "Y":
                    self.df.repeml[2] = mst[2]
                    self.doPrint()

    def loadBalances(self, wlt):
        self.obal = 0.0
        self.cbal = 0.0
        for x, w in enumerate(wlt):
            dat = CCD(w[0], "d1", 10)
            amt = CCD(w[5], "SD", 13.2)
            if self.fdate and dat.work < self.fdate:
                self.obal = float(ASD(self.obal) + ASD(float(amt.work)))
            if dat.work <= self.ldate:
                self.cbal = float(ASD(self.cbal) + ASD(float(amt.work)))

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-27s %-15s %2s %15s" % \
            ("Staff Loans Statements from", self.df.t_disp[0][0][0],
            "to", self.df.t_disp[0][0][1]))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 4

    def printHeader(self):
        self.pageHeading()
        self.pglin += 1
        self.fpdf.setFont(style="B")
        mess = "%-8s %-5s %-60s %-4s %-2s %-30s" % ("Employee",
            self.emp.disp, self.nam.disp, "Loan", self.lon.disp, self.des.disp)
        self.fpdf.drawText(mess)
        self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        mess = "%-10s %-3s %-9s %-7s %-6s %-13s %-13s %-13s %-30s" % \
            ("   Date", "Typ", "Reference", "Batch", "  Int-%",
            "      Amount", "   Deduction", "     Balance", "Remarks")
        self.fpdf.drawText(mess)
        self.pglin += 1
        self.fpdf.underLine(txt=self.head)
        self.pglin += 1
        self.fpdf.setFont()

    def printBody(self, wlt):
        for trn in wlt:
            dat = CCD(trn[0], "d1", 10)
            bat = CCD(trn[3], "Na", 7)
            typ = CCD(trn[1], "UI", 2)
            ref = CCD(trn[2], "Na", 9)
            per = CCD(trn[4], "UD", 7.2)
            amt = CCD(trn[5], "SD", 13.2)
            ded = CCD(trn[6], "SD", 13.2)
            des = CCD(trn[7], "NA", 30)
            if self.fdate and dat.work < self.fdate:
                continue
            if dat.work > self.ldate:
                continue
            if self.pglin > self.fpdf.lpp:
                self.printHeader()
                bal = CCD(self.obal, "SD", 13.2)
                if bal.work:
                    mess = "%-69s%s%-30s" % ("", bal.disp, " Brought Forward")
                    self.fpdf.drawText(mess)
                    self.pglin += 1
            self.obal = float(ASD(self.obal) + ASD(float(amt.work)))
            bal = CCD(self.obal, "SD", 13.2)
            mess = "%s %s %s %s %s %s %s %s %s" % \
                (dat.disp, sltrtp[typ.work - 1][0], ref.disp, bat.disp,
                per.disp, amt.disp, ded.disp, bal.disp, des.disp)
            self.fpdf.drawText(mess)
            self.pglin += 1

    def doPrint(self):
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header="%s Loan Statement at %s" % (self.opts["conam"], self.dated),
                fromad=self.fromad, repprt=self.df.repprt, repeml=self.df.repeml)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
