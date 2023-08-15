"""
SYNOPSIS
    Loans Interrogation.

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
from TartanClasses import ASD, CCD, GetCtl, LoanInterest, NotesCreate, MyFpdf
from TartanClasses import SelectChoice, Sql, TartanDialog
from tartanFunctions import askChoice, getModName, doPrinter
from tartanWork import lntrtp

class ln4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlynd", "lonmf1", "lonmf2",
            "lonrte", "lontrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.history = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Staff Loans Interrogation (%s)" % self.__class__.__name__)
        acc = {
            "stype": "R",
            "tables": ("lonmf2", "lonmf1"),
            "cols": (
                ("lm2_acno", "", 0, "Acc-Num"),
                ("lm1_name", "", 0, "Name")),
            "where": [
                ("lm2_cono", "=", self.opts["conum"]),
                ("lm1_cono=lm2_cono",),
                ("lm1_acno=lm2_acno",)],
            "group": "lm2_acno"}
        lnm = {
            "stype": "R",
            "tables": ("lonmf2",),
            "cols": (
                ("lm2_acno", "", 0, "Acc-Num"),
                ("lm2_loan", "", 0, "Ln"),
                ("lm2_desc", "", 0, "Description", "Y")),
            "where": [("lm2_cono", "=", self.opts["conum"])],
            "whera": [("T", "lm2_acno", 0, 0)],
            "order": "lm2_acno, lm2_loan",
            "index": 1}
        r1s = (("Yes", "Y"), ("No", "N"))
        tag = (
            ("General", self.doGeneral, ("T",0,0), ("T",0,1)),
            ("Balances", self.doGeneral, ("T",0,0), ("T",0,1)),
            ("Trans", self.doTrans1, ("T",0,0), ("T",0,1)))
        fld = (
            (("T",0,0,0),"IUA",7,"Acc-Num","Account Number",
                "","N",self.doAcc,acc,None,("notzero",)),
            (("T",0,0,0),"ONA",40,"Name"),
            (("T",0,1,0),"IUI",2,"Loan-Num","Loan Number",
                "","N",self.doLoan,lnm,None,("notzero",)),
            (("T",0,1,15),"ONA",40,"Desc"),
            (("T",1,0,0),"OD1",10,"Start Date"),
            (("T",1,1,0),"OUI",3,"Period in Months"),
            (("T",1,2,0),"OUD",12.2,"Repayment Amount"),
            (("T",1,3,0),"Od1",10,"Last Capitalised"),
            (("T",1,4,0),"OUD",6.2,"Debit Interest Rate"),
            (("T",1,5,0),"OUD",6.2,"Credit Interest Rate"),
            (("T",2,0,0),"OSD",13.2,"Total Advances"),
            (("T",2,1,0),"OSD",13.2,"Total Interest"),
            (("T",2,2,0),"OSD",13.2,"Total Repayments"),
            (("T",2,3,0),"OSD",13.2,"Total Adjustments"),
            (("T",2,4,0),"OSD",13.2,"Balance"),
            (("T",2,5,0),"Od1",10,"Last Interest Raised"),
            (("T",2,6,0),"Od1",10,"Last Payment Received"),
            (("T",3,0,0),("IRB",r1s),0,"History","",
                self.history,"Y",self.doTrans2,None,None,None))
        tnd = ((self.doEndTop,"N"), None, None, None)
        txt = (self.doExit, None, None, None)
        cnd = (None, None, None, None)
        cxt = (None, None, None, None)
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tags=tag, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.opts["conum"]),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        self.name = acc[0]
        self.df.loadEntry("T", pag, p+1, data=self.name)
        chk = self.sql.getRec("lonmf2", cols=["lm2_loan"],
            where=[("lm2_cono", "=", self.opts["conum"]),
            ("lm2_acno", "=", self.acno)])
        if not chk:
            return "No Loans"
        if len(chk) == 1:
            self.df.loadEntry(frt, pag, p+2, data=chk[0][0])
            self.df.doKeyPressed(frt, pag, p+2, chk[0][0])
            return "nd"

    def doLoan(self, frt, pag, r, c, p, i, w):
        lonmf2 = self.sql.getRec("lonmf2", where=[("lm2_cono", "=",
            self.opts["conum"]), ("lm2_acno", "=", self.acno),
            ("lm2_loan", "=", w)], limit=1)
        if not lonmf2:
            return "Invalid Loan Number"
        lonrte = self.sql.getRec("lonrte", where=[("lrt_cono", "=",
            self.opts["conum"]), ("lrt_acno", "=", self.acno),
            ("lrt_loan", "=", w)], order="lrt_start desc", limit=1)
        self.loan = w
        self.desc = lonmf2[self.sql.lonmf2_col.index("lm2_desc")]
        self.df.loadEntry("T", pag, p+1, data=self.desc)
        start = lonmf2[self.sql.lonmf2_col.index("lm2_start")]
        self.df.loadEntry("T", 1, 0, data=start)
        pmths = lonmf2[self.sql.lonmf2_col.index("lm2_pmths")]
        self.df.loadEntry("T", 1, 1, data=pmths)
        repay = lonmf2[self.sql.lonmf2_col.index("lm2_repay")]
        self.df.loadEntry("T", 1, 2, data=repay)
        lcap = lonmf2[self.sql.lonmf2_col.index("lm2_lcap")]
        self.df.loadEntry("T", 1, 3, data=lcap)
        drte = lonrte[self.sql.lonrte_col.index("lrt_drte")]
        self.df.loadEntry("T", 1, 4, data=drte)
        crte = lonrte[self.sql.lonrte_col.index("lrt_crte")]
        self.df.loadEntry("T", 1, 5, data=crte)
        # Raise Interest
        LoanInterest("L", self.opts["mf"].dbm, lonmf2, update="Y",
            tdate=self.sysdtw, batch="Pending")
        # Get Balances
        self.lon = 0.0
        self.imt = 0.0
        self.pay = 0.0
        self.adj = 0.0
        self.bal = 0.0
        self.idt = 0
        self.pdt = 0
        whr = [
            ("lnt_cono", "=", self.opts["conum"]),
            ("lnt_acno", "=", self.acno),
            ("lnt_loan", "=", self.loan)]
        odr = "lnt_trdt, lnt_type"
        self.lnt = self.sql.getRec("lontrn", where=whr, order=odr)
        if self.lnt:
            col = self.sql.lontrn_col
            for rec in self.lnt:
                dat = CCD(rec[col.index("lnt_trdt")], "d1", 10)
                typ = CCD(rec[col.index("lnt_type")], "UI",  2)
                amt = CCD(rec[col.index("lnt_tramt")], "SD",13.2)
                self.bal = float(ASD(self.bal) + ASD(amt.work))
                if typ.work == 1:
                    self.lon = float(ASD(self.lon) + ASD(amt.work))
                elif typ.work == 2:
                    self.pay = float(ASD(self.pay) + ASD(amt.work))
                    self.pdt = dat.work
                elif typ.work == 3:
                    self.adj = float(ASD(self.adj) + ASD(amt.work))
                else:
                    self.idt = dat.work
                    self.imt = float(ASD(self.imt) + ASD(amt.work))
        # Load Balances
        self.df.loadEntry("T", 2, 0, data=self.lon)
        self.df.loadEntry("T", 2, 1, data=self.imt)
        self.df.loadEntry("T", 2, 2, data=self.pay)
        self.df.loadEntry("T", 2, 3, data=self.adj)
        self.df.loadEntry("T", 2, 4, data=self.bal)
        self.df.loadEntry("T", 2, 5, data=self.idt)
        self.df.loadEntry("T", 2, 6, data=self.pdt)
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def doGeneral(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 3, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        self.history = w
        tab = ["lontrn"]
        col = ["lnt_trdt", "lnt_batch", "lnt_type", "lnt_refno",
            "lnt_tramt", "lnt_desc", "lnt_curdt"]
        whr = [
            ("lnt_cono", "=", self.opts["conum"]),
            ("lnt_acno", "=", self.acno),
            ("lnt_loan", "=", self.loan)]
        odr = "lnt_curdt, lnt_trdt, lnt_type, lnt_refno"
        recs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        data = []
        bals = 0
        fini = False
        curdt = int(self.opts["period"][1][0] / 100)
        for rec in recs:
            if self.history == "N":
                if rec[6] < curdt:
                    bals = float(ASD(bals) + ASD(rec[4]))
                    continue
                if not fini:
                    fini = True
                    data.append([self.opts["period"][1][0], "", 3, "", bals,
                        bals, "Opening Balance"])
            bals = float(ASD(bals) + ASD(rec[4]))
            rec.insert(5, bals)
            data.append(rec[:7])
        tit = "Transactions for Loan: %s %s - %s" % \
            (self.acno, self.name, self.desc)
        col = (
            ("lnt_trdt", "   Date", 10, "D1", "N"),
            ("lnt_batch", "Batch", 7, "NA", "N"),
            ("lnt_type", "Typ", 3, ("XX", lntrtp), "N"),
            ("lnt_refno", "Reference", 9, "Na", "Y"),
            ("lnt_tramt", "      Amount", 13.2, "SD", "N"),
            ("balan", "     Balance", 13.2, "SD", "N"),
            ("lnt_desc", "Remarks", 30, "NA", "N"))
        state = self.df.disableButtonsTags()
        SelectChoice(self.df.nb.Page2, tit, col, data)
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 2, 1)

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "LON", "%7s%02i" % (self.acno, self.loan))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.opts["mf"].dbm.rollbackDbase()
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
        if opt == "N":
            return
        self.head = "%03u %-89s" % (self.opts["conum"], self.opts["conam"])
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
            if not self.lnt:
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
            else:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
        elif opt == "T":
            if self.lnt:
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
        for x in range(0, len(self.df.topf[2])):
            self.fpdf.drawText("%-5s %-20s %-25s %s" % ("", "",
                self.df.topf[2][x][3], self.df.t_disp[2][0][x]))
        self.fpdf.drawText()

    def printTrans(self):
        whr = [
            ("lnt_cono", "=", self.opts["conum"]),
            ("lnt_acno", "=", self.acno),
            ("lnt_loan", "=", self.loan)]
        odr = "lnt_curdt, lnt_trdt, lnt_type"
        recs = self.sql.getRec("lontrn", where=whr, order=odr)
        bals = 0
        fini = False
        for rec in recs:
            trd = CCD(rec[self.sql.lontrn_col.index("lnt_trdt")], "D1", 10)
            typ = CCD(rec[self.sql.lontrn_col.index("lnt_type")], "UI", 1)
            ref = CCD(rec[self.sql.lontrn_col.index("lnt_refno")], "Na", 9)
            bat = CCD(rec[self.sql.lontrn_col.index("lnt_batch")], "Na", 7)
            amt = CCD(rec[self.sql.lontrn_col.index("lnt_tramt")], "SD", 13.2)
            det = CCD(rec[self.sql.lontrn_col.index("lnt_desc")], "NA", 30)
            if self.history == "N":
                cdt = rec[self.sql.lontrn_col.index("lnt_curdt")]
                if cdt < int(self.opts["period"][1][0] / 100):
                    bals = float(ASD(bals) + ASD(amt.work))
                    continue
                if not fini:
                    fini = True
                    dte = CCD(self.opts["period"][1][0], "D1", 10)
                    bal = CCD(bals, "SD", 13.2)
                    self.fpdf.drawText("%s %s %9s %7s %s %s %-30s" % (dte.disp,
                        "Jnl", "", "", bal.disp, bal.disp, "Opening Balance"))
                    self.pglin += 1
            bals = float(ASD(bals) + ASD(amt.work))
            bal = CCD(bals, "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            self.fpdf.drawText("%s %s %s %s %s %s %s" % (trd.disp,
                lntrtp[(typ.work - 1)][0], ref.disp, bat.disp,
                amt.disp, bal.disp, det.disp))
            self.pglin += 1

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-31s %-10s" %
            ("Staff Loans Interrogation as at", self.sysdtd))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def pageHeadingTrans(self):
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-1s %-s: %s %-2s %-s: %s" % ("",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-1s %-s: %s %-2s %-s: %s" % ("",
            self.df.topf[0][2][3], self.df.t_disp[0][0][2], "",
            self.df.topf[0][3][3], self.df.t_disp[0][0][3]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-10s %-3s %-9s %-7s %-13s %-13s %-30s" %
            ("   Date", "Typ", "Reference", "Batch", "      Amount",
            "     Balance", "Remarks"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        try:
            self.opts["mf"].dbm.rollbackDbase()
        except:
            pass
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
