"""
SYNOPSIS
    Rentals Ledger Interrogation.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, NotesCreate, Sql, SRec
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, getModName, doPrinter
from tartanWork import rttrtp

class rt4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rtlprm", "rtlmst", "rtlcon",
            "rtltrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Rental Ledger Interrogation (%s)" % self.__class__.__name__)
        prm = {
            "stype": "R",
            "tables": ("rtlprm",),
            "cols": (
                ("rtp_code", "", 0, "Prm-Code"),
                ("rtp_desc", "", 0, "Description", "Y")),
            "where": [("rtp_cono", "=", self.opts["conum"])]}
        acc = {
            "stype": "R",
            "tables": ("rtlmst",),
            "cols": (
                ("rtm_acno", "", 0, "Acc-Num"),
                ("rtm_name", "", 0, "Name", "Y")),
            "where": [("rtm_cono", "=", self.opts["conum"])],
            "whera": (("T", "rtm_code", 0, 0),)}
        seq = {
            "stype": "R",
            "tables": ("rtlcon",),
            "cols": (
                ("rtc_cnum", "", 0, "Acc-Num"),
                ("rtc_payind", "", 0, "F"),
                ("rtc_start", "", 0, "Start-Date"),
                ("rtc_period", "", 0, "Per")),
            "where": [("rtc_cono", "=", self.opts["conum"])],
            "whera": [["T", "rtc_code", 0, 0], ["T", "rtc_acno", 1, 0]]}
        tag = (
            ("Premises",self.doTagSelect,("T",0,0),("T",0,1)),
            ("Tenant",self.doTagSelect,("T",0,0),("T",0,1)),
            ("Balances",self.doTagSelect,("T",0,0),("T",0,1)),
            ("Transactions",self.doTrans1,("T",0,0),("T",0,1)))
        fld = (
            (("T",0,0,0),"INA",7,"Premises","Premises Code",
                "","Y",self.doPremises,prm,None,("notblank",)),
            (("T",0,0,0),"INA",7,"Account","Account Code",
                "","N",self.doAccount,acc,None,("notblank",)),
            (("T",0,0,0),"ONA",30,"Name"),
            (("T",1,0,0),"ONA",30,"Description"),
            (("T",1,1,0),"ONA",30,"Address-1"),
            (("T",1,2,0),"ONA",30,"Address-2"),
            (("T",1,3,0),"ONA",30,"Address-3"),
            (("T",1,4,0),"ONA",4,"Postal Code"),
            (("T",2,0,0),"ONA",30,"Address-1"),
            (("T",2,1,0),"ONA",30,"Address-2"),
            (("T",2,2,0),"ONA",30,"Address-3"),
            (("T",2,3,0),"ONA",4,"Postal Code"),
            (("T",2,4,0),"ONA",20,"Telephone Number"),
            (("T",2,5,0),"OTX",50,"E-Mail Address"),
            (("T",2,6,0),"OUA",1,"VAT Indicator"),
            (("T",2,7,0),"ONA",10,"VAT Number"),
            (("T",2,8,0),"OUA",1,"Payment Frequency"),
            (("T",2,9,0),"OD1",10,"Start Date"),
            (("T",2,10,0),"OUI",3,"Number of Periods"),
            (("T",2,11,0),"OUD",12.2,"Rental Amount"),
            (("T",2,12,0),"OUA",1,"Status"),
            (("C",3,0,0),"OSD",13.2,"Value","",
                "","N",None,None,None,None,("Details",5)),
            (("T",4,0,0),"IUI",3,"Sequence Number","",
                "N","N",self.doTrans2,seq,None,None))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None, None)
        txt = (self.doExit, None, None, None, self.doExit)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        self.df.colLabel[3][0].configure(text="Rentals ")
        self.df.colLabel[3][1].configure(text="Receipts")
        self.df.colLabel[3][2].configure(text="Payments")
        self.df.colLabel[3][3].configure(text="Journals")
        self.df.colLabel[3][4].configure(text="Balance ")

    def doPremises(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlprm", where=[("rtp_cono", "=",
            self.opts["conum"]), ("rtp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises"
        self.code = w
        for num, fld in enumerate(acc):
            if num < 2 or num > 6:
                continue
            self.df.loadEntry("T", 1, (num-2), data=fld)

    def doAccount(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlmst", where=[("rtm_cono", "=",
            self.opts["conum"]), ("rtm_code", "=", self.code), ("rtm_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid Account"
        self.acno = w
        self.name = acc[self.sql.rtlmst_col.index("rtm_name")]
        con = self.sql.getRec("rtlcon", where=[("rtc_cono",
            "=", self.opts["conum"]), ("rtc_code", "=", self.code),
            ("rtc_acno", "=", self.acno)], order="rtc_cnum")
        if not con:
            return "Invalid Contract"
        self.df.loadEntry(frt, pag, p+1, data=acc[3])
        for num, fld in enumerate(acc[4:]):
            self.df.loadEntry("T", 2, num, data=fld)
        self.cnum = con[-1:][0][3]
        self.df.topf[4][0][5] = self.cnum
        for num, fld in enumerate(con[-1:][0][4:-1]):
            self.df.loadEntry("T", 2, num+8, data=fld)
        self.loadBalances()
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadBalances(self):
        rtl = 0
        rec = 0
        pmt = 0
        jnl = 0
        bal = self.sql.getRec("rtltrn", cols=["rtt_type",
            "round(sum(rtt_tramt), 2)"], where=[("rtt_cono", "=",
            self.opts["conum"]), ("rtt_code", "=", self.code), ("rtt_acno",
            "=", self.acno)], group="rtt_type", order="rtt_type")
        if bal:
            for a in bal:
                if a[0] == 1:
                    rtl = a[1]
                if a[0] == 2:
                    rec = a[1]
                if a[0] == 3:
                    pmt = a[1]
                if a[0] == 4:
                    jnl = a[1]
        bal = float(ASD(rtl) + ASD(rec) + ASD(pmt) + ASD(jnl))
        self.df.loadEntry("C", 3, 0, data=rtl)
        self.df.loadEntry("C", 3, 1, data=rec)
        self.df.loadEntry("C", 3, 2, data=pmt)
        self.df.loadEntry("C", 3, 3, data=jnl)
        self.df.loadEntry("C", 3, 4, data=bal)
        self.trn = self.sql.getRec("rtltrn", where=[("rtt_cono", "=",
            self.opts["conum"]), ("rtt_code", "=", self.code), ("rtt_acno",
            "=", self.acno)], order="rtt_trdt, rtt_type")

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 4, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        tit = "Transactions for Account: %s %s - %s" % \
            (self.code, self.acno, self.name)
        tab = ["rtltrn"]
        col = (
            ("rtt_trdt", "", 0, "   Date"),
            ("rtt_curdt", "", 0, "Curr-Dt"),
            ("rtt_batch", "", 0, "Batch"),
            ("rtt_type", ("XX", rttrtp), 3, "Typ"),
            ("rtt_refno", "", 0, "Reference", "Y"),
            ("rtt_tramt", "", 0, "     Amount"),
            ("rtt_taxamt", "", 0, " VAT-Amount"),
            ("rtt_desc", "", 0, "Details"))
        whr = [
            ("rtt_cono", "=", self.opts["conum"]),
            ("rtt_code", "=", self.code),
            ("rtt_acno", "=", self.acno)]
        if w:
            whr.append(("rtt_cnum", "=", w))
        odr = "rtt_trdt, rtt_type"
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.df.nb.Page2, title=tit, tables=tab,
            cols=col, where=whr, order=odr)
        self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "RTL", "%7s%s" % (self.code, self.acno))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Premises")
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
        if self.df.topq[self.df.pag]:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        self.head = "%03u %-101s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        if opt != "T":
            self.pageHeading()
            self.printInfo()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if opt == "I":
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
        elif opt == "B":
            if not self.trn:
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
            else:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
        elif opt == "T":
            if self.trn:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])

    def printInfo(self):
        for x in range(0, len(self.df.topf[0])):
            self.fpdf.drawText("%-26s%-25s %s" % ("",
                self.df.topf[0][x][3], self.df.t_disp[0][0][x]))
        self.fpdf.drawText()
        for x in range(0, len(self.df.topf[1])):
            self.fpdf.drawText("%-26s%-25s %s" % ("",
                self.df.topf[1][x][3], self.df.t_disp[1][0][x]))
        self.fpdf.drawText()
        for x in range(0, len(self.df.topf[2])):
            self.fpdf.drawText("%-26s%-25s %s" % ("",
                self.df.topf[2][x][3], self.df.t_disp[2][0][x]))
        self.fpdf.drawText()
        self.pglin += 3 + len(self.df.topf[3])
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%26s%-34s %13s" % ("", "Details","Amount "))
        self.fpdf.drawText("%26s%s" % ("", self.fpdf.suc * 48))
        self.fpdf.setFont()
        desc = (
            "Rentals ",
            "Receipts",
            "Payments",
            "Journals",
            "Balance ")
        for n, d in enumerate(self.df.c_disp[3]):
            self.fpdf.drawText("%26s%-34s %13s" % ("", desc[n], d[0]))

    def printTrans(self):
        col = self.sql.rtltrn_col
        bal = 0
        for ct in self.trn:
            trdt = CCD(ct[col.index("rtt_trdt")], "D1", 10)
            refno = CCD(ct[col.index("rtt_refno")], "Na", 9)
            trtp = CCD(ct[col.index("rtt_type")], "UI", 1)
            batch = CCD(ct[col.index("rtt_batch")], "Na", 7)
            desc = CCD(ct[col.index("rtt_desc")], "NA", 30)
            tramt = ct[col.index("rtt_tramt")]
            if tramt < 0:
                debit = CCD(0, "SD", 13.2)
                credit = CCD(tramt, "SD", 13.2)
            else:
                debit = CCD(tramt, "SD", 13.2)
                credit = CCD(0, "SD", 13.2)
            bal = float(ASD(bal) + ASD(tramt))
            tot = CCD(bal, "SD", 13.2)
            taxamt = CCD(ct[col.index("rtt_taxamt")], "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % (trdt.disp,
                refno.disp, rttrtp[(trtp.work - 1)][0], batch.disp,
                desc.disp, debit.disp, credit.disp, tot.disp, taxamt.disp))
            self.pglin += 1

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-10s" % \
            ("Rentals Ledger Interrogation as at", self.sysdtd))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def pageHeadingTrans(self):
        self.fpdf.drawText("%-16s %s %s %s %s %s %s %s %s" % ("",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1], "",
            self.df.topf[0][2][3], self.df.t_disp[0][0][2]))
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-10s %-9s %-3s %-7s %-30s %-13s %-13s %-13s" % \
            ("   Date", "Reference", "Typ", "Batch", "Remarks",
            "       Debit", "      Credit",  "     Balance"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
