"""
SYNOPSIS
    Staff Loans Interrogation.

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
from TartanClasses import ASD, CCD, GetCtl, LoanInterest, MyFpdf, Sql, SRec
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, getModName, getPeriods,  doPrinter
from tartanWork import sltrtp

class sl4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlynd", "wagmst", "waglmf",
            "wagltf"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        # Get the current period starting date
        period = self.sql.getRec("ctlynd", cols=["max(cye_period)"],
            where=[("cye_cono", "=", self.opts["conum"])], limit=1)[0]
        self.opts["period"] = getPeriods(self.opts["mf"], self.opts["conum"],
            period)[0].work
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Staff Loans Interrogation (%s)" % self.__class__.__name__)
        wgm = {
            "stype": "R",
            "tables": ("waglmf", "wagmst"),
            "cols": (
                ("wlm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname", "Y"),
                ("wgm_fname", "", 0, "Names")),
            "where": [
                ("wlm_cono", "=", self.opts["conum"]),
                ("wgm_cono=wlm_cono",),
                ("wgm_empno=wlm_empno",)],
            "group": "wlm_empno"}
        lnm = {
            "stype": "R",
            "tables": ("waglmf",),
            "cols": (
                ("wlm_empno", "", 0, "EmpNo"),
                ("wlm_loan", "", 0, "Ln"),
                ("wlm_desc", "", 0, "Description", "Y")),
            "where": [("wlm_cono", "=", self.opts["conum"])],
            "whera": [["T", "wlm_empno", 0, 0]],
            "order": "wlm_empno, wlm_loan",
            "index": 1}
        r1s = (("Yes", "Y"), ("No", "N"))
        tag = (
            ("General", self.doGeneral, ("T",0,0), ("T",0,1)),
            ("Trans", self.doTrans1, ("T",0,0), ("T",0,1)))
        fld = (
            (("T",0,0,0),"IUI",5,"Emp-Num","Employee Number",
                "","N",self.doEmp,wgm,None,("notzero",)),
            (("T",0,0,0),"ONA",40,"Name"),
            (("T",0,1,0),"IUI",5,"Loan-Num","Loan Number",
                "","N",self.doLoan,lnm,None,("notzero",)),
            (("T",0,1,0),"ONA",40,"Desc"),
            (("T",1,0,0),"OUI",3,"Deduction Code"),
            (("T",1,1,0),"OUD",6.2,"Interest Percentage"),
            (("T",1,2,0),"OD1",10,"Start Date"),
            (("T",1,3,0),"OSD",13.2,"Deduction Amount"),
            (("T",1,4,0),"OSD",13.2,"Total Advances"),
            (("T",1,5,0),"OSD",13.2,"Total Interest"),
            (("T",1,6,0),"OSD",13.2,"Total Repayments"),
            (("T",1,7,0),"OSD",13.2,"Total Adjustments"),
            (("T",1,8,0),"OSD",13.2,"Balance"),
            (("T",1,9,0),"Od1",10,"Last Interest Raised"),
            (("T",1,10,0),"Od1",10,"Last Payment Received"),
            (("T",2,0,0),("IRB",r1s),0,"History","",
                "Y","Y",self.doTrans2,None,None,None))
        tnd = ((self.doEndTop,"N"), None, None)
        txt = (self.doExit, None, None)
        cnd = (None, None, None)
        cxt = (None, None, None)
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tags=tag, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doEmp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagmst", cols=["wgm_sname",
            "wgm_fname"], where=[("wgm_cono", "=", self.opts["conum"]),
            ("wgm_empno", "=", w)], limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.empno = w
        self.name = "%s, %s" % (acc[0], acc[1])
        self.history = "Y"
        self.df.loadEntry("T", pag, p+1, data=self.name)

    def doLoan(self, frt, pag, r, c, p, i, w):
        lmc = self.sql.waglmf_col
        rec = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
            self.opts["conum"]), ("wlm_empno", "=", self.empno),
            ("wlm_loan", "=", w)], limit=1)
        if not rec:
            return "Invalid Loan Number"
        self.loan = w
        self.desc = rec[lmc.index("wlm_desc")]
        self.df.loadEntry("T", pag, p+1, data=self.desc)
        self.df.loadEntry("T", 1, 0, data=rec[lmc.index("wlm_code")])
        self.df.loadEntry("T", 1, 1, data=rec[lmc.index("wlm_rate")])
        self.df.loadEntry("T", 1, 2, data=rec[lmc.index("wlm_start")])
        self.df.loadEntry("T", 1, 3, data=rec[lmc.index("wlm_repay")])
        # Raise Interest
        LoanInterest("S", self.opts["mf"].dbm, rec, update="Y",
            curdt=int(self.sysdtw / 100), tdate=self.sysdtw, refno="Pending")
        # Get Balances
        self.lon = 0.0
        self.imt = 0.0
        self.pay = 0.0
        self.adj = 0.0
        self.bal = 0.0
        self.idt = 0
        self.pdt = 0
        whr = [
            ("wlt_cono", "=", self.opts["conum"]),
            ("wlt_empno", "=", self.empno),
            ("wlt_loan", "=", self.loan)]
        odr = "wlt_trdt, wlt_type"
        self.wlt = self.sql.getRec("wagltf", where=whr, order=odr)
        if self.wlt:
            col = self.sql.wagltf_col
            for rec in self.wlt:
                dat = CCD(rec[col.index("wlt_trdt")], "d1", 10)
                typ = CCD(rec[col.index("wlt_type")], "UI",  2)
                amt = CCD(rec[col.index("wlt_amt")], "SD",13.2)
                self.bal = float(ASD(self.bal) + ASD(amt.work))
                if typ.work == 1:
                    self.idt = dat.work
                    self.imt = float(ASD(self.imt) + ASD(amt.work))
                elif typ.work in (2, 3):
                    self.lon = float(ASD(self.lon) + ASD(amt.work))
                elif typ.work == 4:
                    self.pay = float(ASD(self.pay) + ASD(amt.work))
                    self.pdt = dat.work
                elif typ.work == 5:
                    self.adj = float(ASD(self.adj) + ASD(amt.work))
        # Load Balances
        self.df.loadEntry("T", 1, 4, data=self.lon)
        self.df.loadEntry("T", 1, 5, data=self.imt)
        self.df.loadEntry("T", 1, 6, data=self.pay)
        self.df.loadEntry("T", 1, 7, data=self.adj)
        self.df.loadEntry("T", 1, 8, data=self.bal)
        self.df.loadEntry("T", 1, 9, data=self.idt)
        self.df.loadEntry("T", 1, 10, data=self.pdt)
        self.opts["mf"].updateStatus("")

    def doHist(self, frt, pag, r, c, p, i, w):
        self.history = w

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadBalances(self):
        whr = [
            ("wlt_cono", "=", self.opts["conum"]),
            ("wlt_empno", "=", self.empno),
            ("wlt_loan", "=", self.loan)]
        odr = "wlt_trdt, wlt_type"
        self.wlt = self.sql.getRec("wagltf", where=whr, order=odr)
        if self.wlt:
            for rec in self.wlt:
                dat = CCD(rec[self.sql.wagltf_col.index("wlt_trdt")], "d1", 10)
                typ = CCD(rec[self.sql.wagltf_col.index("wlt_type")], "UI",  2)
                amt = CCD(rec[self.sql.wagltf_col.index("wlt_amt")], "SD",13.2)
                self.bal = float(ASD(self.bal) + ASD(amt.work))
                self.cap = float(ASD(self.cap) + ASD(amt.work))
                if typ.work == 1:
                    if dat.work >= self.opts["period"] and \
                            dat.work >= self.df.t_work[1][0][3]:
                        self.cap = float(ASD(self.cap) - ASD(amt.work))
                        self.due = float(ASD(self.due) + ASD(amt.work))
                    self.imt = float(ASD(self.imt) + ASD(amt.work))
                    self.idt = dat.work
                elif typ.work in (2, 3):
                    self.lon = float(ASD(self.lon) + ASD(amt.work))
                elif typ.work == 4:
                    self.pay = float(ASD(self.pay) + ASD(amt.work))
                    self.pdt = dat.work
                elif typ.work == 5:
                    self.adj = float(ASD(self.adj) + ASD(amt.work))

    def doGeneral(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 2, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        self.history = w
        tit = "Transactions for Loan: %s %s - %s" % \
            (self.empno, self.name, self.desc)
        tab = ["wagltf"]
        col = (("wlt_trdt", "", 0, "   Date"),
                ("wlt_batch", "", 0, "Batch"),
                ("wlt_type", ("XX", sltrtp), 3, "Typ"),
                ("wlt_ref", "", 0, "Reference", "Y"),
                ("wlt_per", "", 0, " Int-%"),
                ("wlt_amt", "", 0, "      Amount"),
                ("wlt_ded", "", 0, "   Deduction"),
                ("wlt_desc", "", 0, "Remarks"))
        whr = [
            ("wlt_cono", "=", self.opts["conum"]),
            ("wlt_empno", "=", self.empno),
            ("wlt_loan", "=", self.loan)]
        if self.history == "N":
            whr.append(("wlt_curdt", ">=", int(self.opts["period"] / 100)))
        odr = "wlt_trdt, wlt_type, wlt_ref"
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.df.nb.Page2, title=tit, tables=tab,
            cols=col, where=whr, order=odr)
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 2, 1)

    def doClear(self):
        self.df.selPage("General")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = (
            ("Information", "I"),
            ("Transactions", "T"),
            ("Both", "B"),
            ("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        print(opt)
        if opt == "N":
            return
        self.head = "%03u %-93s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        if opt != "T":
            self.pageHeading()
            self.printInfo()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if opt == "I":
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit,
                    repprt=["N", "V", "view"])
        elif opt == "B":
            if not self.wlt:
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
            else:
                self.acctot = 0.0
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
        elif opt == "T":
            if self.wlt:
                self.acctot = 0.0
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])

    def printInfo(self):
        self.fpdf.drawText("%-5s %-20s %-25s %s" % ("", "",
                self.df.topf[0][0][3], self.df.t_disp[0][0][0]))
        self.fpdf.drawText("%-5s %-20s %-25s %s" % ("", "",
                self.df.topf[0][1][3], self.df.t_disp[0][0][1]))
        self.fpdf.drawText("%-5s %-20s %-25s %s" % ("", "",
                self.df.topf[0][2][3], self.df.t_disp[0][0][2]))
        self.fpdf.drawText()
        for x in range(0, len(self.df.topf[1])):
            self.fpdf.drawText("%-5s %-20s %-25s %s" % ("", "",
                self.df.topf[1][x][3], self.df.t_disp[1][0][x]))
        self.fpdf.drawText()

    def printTrans(self):
        whr = [
            ("wlt_cono", "=", self.opts["conum"]),
            ("wlt_empno", "=", self.empno),
            ("wlt_loan", "=", self.loan)]
        odr = "wlt_trdt, wlt_type"
        if self.history == "N":
            whr.append(("wlt_curdt", ">=", int(self.opts["period"] / 100)))
        recs = self.sql.getRec("wagltf", where=whr, order=odr)
        for rec in recs:
            trd = CCD(rec[self.sql.wagltf_col.index("wlt_trdt")], "D1", 10)
            typ = CCD(rec[self.sql.wagltf_col.index("wlt_type")], "UI", 1)
            ref = CCD(rec[self.sql.wagltf_col.index("wlt_ref")], "Na", 9)
            bat = CCD(rec[self.sql.wagltf_col.index("wlt_batch")], "Na", 7)
            rte = CCD(rec[self.sql.wagltf_col.index("wlt_per")], "UD", 6.2)
            amt = CCD(rec[self.sql.wagltf_col.index("wlt_amt")], "SD", 13.2)
            ded = CCD(rec[self.sql.wagltf_col.index("wlt_ded")], "SD", 13.2)
            det = CCD(rec[self.sql.wagltf_col.index("wlt_desc")], "NA", 30)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            self.acctot = float(ASD(self.acctot) + ASD(amt.work))
            self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (trd.disp,
                sltrtp[(typ.work - 1)][0], ref.disp, bat.disp,
                rte.disp, amt.disp, ded.disp, det.disp))
            self.pglin += 1
        self.fpdf.underLine(txt=self.head)
        b = CCD(self.acctot, "SD", 13.2)
        self.fpdf.drawText("%-39s %13s %13s %-30s" % \
            ("", b.disp, "", "Closing Balance"))

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("Staff Loans Interrogation as at %s" % self.sysdtd)
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 3

    def pageHeadingTrans(self):
        self.fpdf.setFont(style="B")
        text = "%-8s %5s %-4s %s" % (self.df.topf[0][0][3],
            self.df.t_disp[0][0][0], self.df.topf[0][1][3],
            self.df.t_disp[0][0][1])
        self.fpdf.drawText(text)
        text = "%-8s %5s %-4s %s" % (self.df.topf[0][2][3],
            self.df.t_disp[0][0][2], self.df.topf[0][3][3],
            self.df.t_disp[0][0][3])
        self.fpdf.drawText(text)
        self.fpdf.drawText()
        self.fpdf.drawText("%-10s %-3s %-9s %-7s %6s %12s  %12s  %-30s" % \
            ("   Date", "Typ", "Reference", "Batch", "Int%",
            "    Amount", "  Deduction", "Remarks"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 7
        b = CCD(self.acctot, "SD", 13.2)
        if self.acctot != 0:
            self.fpdf.drawText("%-39s %13s %13s %-30s" % \
                ("", b.disp, "", "Brought Forward"))
            self.pglin += 1

    def doExit(self):
        try:
            self.opts["mf"].dbm.rollbackDbase()
        except:
            pass
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
