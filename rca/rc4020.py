"""
SYNOPSIS
    Rentals Tenants Interrogation.

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
from tartanFunctions import askChoice, doPrinter, getDeposit, getModName
from tartanWork import rcmvtp, rctrtp

class rc4020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcaprm", "rcatnm", "rcacon",
            "rcatnt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Rental Tenants Interrogation (%s)" % self.__class__.__name__)
        prm = {
            "stype": "R",
            "tables": ("rcaprm",),
            "cols": (
                ("rcp_owner", "", 0, "Own-Cod"),
                ("rcp_code", "", 0, "Prm-Code"),
                ("rcp_addr1", "", 0, "Address-Line-1")),
            "where": [("rcp_cono", "=", self.opts["conum"])],
            "index": 1}
        acc = {
            "stype": "R",
            "tables": ("rcatnm",),
            "cols": (
                ("rtn_acno", "", 0, "Acc-Num"),
                ("rtn_name", "", 0, "Name", "Y")),
            "where": [("rtn_cono", "=", self.opts["conum"])],
            "whera": (("T", "rtn_code", 0, 0),)}
        seq = {
            "stype": "R",
            "tables": ("rcacon",),
            "cols": (
                ("rcc_cnum", "", 0, "Acc-Num"),
                ("rcc_payind", "", 0, "F"),
                ("rcc_start", "", 0, "Start-Date"),
                ("rcc_period", "", 0, "Per")),
            "where": [("rcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "rcc_code", 0, 0], ["T", "rcc_acno", 1, 0]]}
        tag = (
            ("Premises", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Tenant", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Transactions", self.doTrans1, ("T",0,2), ("T",0,1)),
            ("Deposit", self.doDeposit1, ("T",0,2), ("T",0,1)))
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
            (("T",1,5,0),"OUD",6.2,"Commission Rate"),
            (("T",2,0,0),"ONA",20,"Telephone Number"),
            (("T",2,1,0),"OTX",50,"E-Mail Address"),
            (("T",2,2,0),"OUA",1,"VAT Indicator"),
            (("T",2,3,0),"ONA",10,"VAT Number"),
            (("T",2,4,0),"OUA",1,"Payment Frequency"),
            (("T",2,5,0),"OD1",10,"Start Date"),
            (("T",2,6,0),"OUI",3,"Number of Periods"),
            (("T",2,7,0),"OUD",12.2,"Rental Amount"),
            (("T",2,8,0),"OUD",12.2,"Deposit Amount"),
            (("T",2,9,0),"OUD",12.2,"Basic Water Amount"),
            (("T",2,9,0),"OUI",1,"Type"),
            (("T",2,10,0),"OUD",12.2,"Basic Exlectricity Amount"),
            (("T",2,10,0),"OUI",1,"Type"),
            (("T",2,11,0),"OUA",1,"Status"),
            (("C",3,0,0),"OSD",13.2,"Value","",
                "","N",None,None,None,None,("Details",7)),
            (("T",4,0,0),"IUI",3,"Sequence Number","",
                "N","N",self.doTrans2,seq,None,None),
            (("T",5,0,0),"ID1",10,"Effective Date","",
                self.sysdtw,"N",self.doDeposit2,None,None,("efld",)))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None, None, None)
        txt = (self.doExit, None, None, None, None, None)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        self.df.colLabel[3][0].configure(text="Deposit     ")
        self.df.colLabel[3][1].configure(text="Rentals     ")
        self.df.colLabel[3][2].configure(text="Fees        ")
        self.df.colLabel[3][3].configure(text="Services (O)")
        self.df.colLabel[3][4].configure(text="Services (A)")
        self.df.colLabel[3][5].configure(text="Repairs  (A)")
        self.df.colLabel[3][6].configure(text="Balance     ")

    def doPremises(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaprm", where=[("rcp_cono", "=",
            self.opts["conum"]), ("rcp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises"
        self.code = w
        self.owner = acc[self.sql.rcaprm_col.index("rcp_owner")]
        for num, fld in enumerate(acc[:-1]):
            if num > 2:
                self.df.loadEntry("T", 1, (num-3), data=fld)

    def doAccount(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcatnm", where=[("rtn_cono", "=",
            self.opts["conum"]), ("rtn_owner", "=", self.owner),
            ("rtn_code", "=", self.code), ("rtn_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account"
        self.acno = w
        self.depdtw = self.sysdtw
        self.depdtd = self.sysdtd
        self.name = acc[self.sql.rcatnm_col.index("rtn_name")]
        con = self.sql.getRec("rcacon", where=[("rcc_cono", "=",
            self.opts["conum"]), ("rcc_owner", "=", self.owner),
            ("rcc_code", "=", self.code), ("rcc_acno", "=", self.acno)],
            order="rcc_cnum")
        if not con:
            return "Invalid Contract"
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        for num, fld in enumerate(acc[5:-1]):
            self.df.loadEntry("T", 2, num, data=fld)
        self.cnum = con[-1:][0][4]
        self.df.topf[4][0][5] = self.cnum
        for num, fld in enumerate(con[-1:][0][5:-1]):
            self.df.loadEntry("T", 2, num+4, data=fld)
        self.loadBalances()
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadBalances(self):
        rtl = 0
        dep = 0
        fee = 0
        svo = 0
        sva = 0
        rep = 0
        bal = self.sql.getRec("rcatnt", cols=["rtu_mtyp",
            "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
            self.opts["conum"]), ("rtu_owner", "=", self.owner),
            ("rtu_code", "=", self.code), ("rtu_acno", "=", self.acno)],
            group="rtu_mtyp")
        if bal:
            for a in bal:
                if a[0] == 1:
                    rtl = a[1]
                if a[0] == 2:
                    dep = a[1]
                if a[0] == 3:
                    fee = a[1]
                if a[0] == 4:
                    svo = a[1]
                if a[0] == 5:
                    sva = a[1]
                if a[0] == 6:
                    rep = a[1]
        bal = float(ASD(rtl) + ASD(fee) + ASD(svo) + ASD(sva) + ASD(rep))
        self.df.loadEntry("C", 3, 0, data=dep)
        self.df.loadEntry("C", 3, 1, data=rtl)
        self.df.loadEntry("C", 3, 2, data=fee)
        self.df.loadEntry("C", 3, 3, data=svo)
        self.df.loadEntry("C", 3, 4, data=sva)
        self.df.loadEntry("C", 3, 5, data=rep)
        self.df.loadEntry("C", 3, 6, data=bal)
        self.trn = self.sql.getRec("rcatnt", where=[("rtu_cono", "=",
            self.opts["conum"]), ("rtu_owner", "=", self.owner), ("rtu_code",
            "=", self.code), ("rtu_acno", "=", self.acno)],
            order="rtu_trdt, rtu_type")

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 4, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        tit = "Transactions for Account: %s %s %s - %s" % \
            (self.owner, self.code, self.acno, self.name)
        tab = ["rcatnt"]
        col = (
            ("rtu_trdt", "", 0, "   Date"),
            ("rtu_curdt", "", 0, "Curr-Dt"),
            ("rtu_batch", "", 0, "Batch"),
            ("rtu_type", ("XX", rctrtp), 3, "Typ"),
            ("rtu_mtyp", ("XX", rcmvtp), 3, "Mov"),
            ("rtu_refno", "", 0, "Reference", "Y"),
            ("rtu_tramt", "", 0, "     Amount"),
            ("rtu_taxamt", "", 0, " VAT-Amount"),
            ("rtu_desc", "", 0, "Details"))
        whr = [
            ("rtu_cono", "=", self.opts["conum"]),
            ("rtu_owner", "=", self.owner),
            ("rtu_code", "=", self.code),
            ("rtu_acno", "=", self.acno)]
        if w:
            whr.append(("rtu_cnum", "=", w))
        odr = "rtu_trdt, rtu_type"
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.df.nb.Page3, title=tit, tables=tab,
            cols=col, where=whr, order=odr)
        self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doDeposit1(self):
        self.df.focusField("T", 5, 1)

    def doDeposit2(self, frt, pag, r, c, p, i, w):
        self.depdtw = w
        self.depdtd = self.df.t_disp[pag][0][p]
        dat = getDeposit(self.opts["mf"], self.opts["conum"], self.depdtw,
            self.owner, self.code, self.acno)
        if dat:
            tit = "Deposit for Account: %s %s %s - %s as at %s" % (self.owner,
                self.code, self.acno, self.name, self.depdtd)
            col = (
                ("a", "D1", 10, "    Date"),
                ("b", "SD", 11.2, "  Deposits"),
                ("c", "UI", 5, " Days"),
                ("d", "UD", 5.2, " Rate"),
                ("e", "SD", 11.2, "  Interest"),
                ("f", "SD", 11.2, "   Balance"),
                ("g", "SD", 11.2, "     Admin"))
            state = self.df.disableButtonsTags()
            SRec(self.opts["mf"], screen=self.df.nb.Page4, title=tit, cols=col,
                where=dat, wtype="D")
            self.df.enableButtonsTags(state=state)
        self.doDeposit1()

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "RCA", "%7s%7s%s" % (self.owner, self.code,
            self.acno))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Premises")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = (
            ("Info Only", "I"),
            ("Deposit Only", "D"),
            ("Transactions Only", "T"),
            ("Info and Transactions", "B"),
            ("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        self.df.selPage("Premises")
        self.df.focusField("T", 1, 1)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        self.head = ("%03u %-30s %63s %10s" % \
            (self.opts["conum"], self.opts["conam"], self.sysdttm,
                self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        if opt not in ("D", "T"):
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
        elif opt == "D":
            recs = getDeposit(self.opts["mf"], self.opts["conum"], self.depdtw,
                self.owner, self.code, self.acno)
            if recs:
                self.pageHeading(deposit=True)
                self.pageHeadingDeposit()
                self.printDeposit(recs)
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
            "Deposit     ",
            "Rentals     ",
            "Fees        ",
            "Services (O)",
            "Services (A)",
            "Repairs  (A)",
            "Balance     ")
        for n, d in enumerate(self.df.c_disp[3]):
            self.fpdf.drawText("%26s%-34s %13s" % ("", desc[n], d[0]))

    def printDeposit(self, recs):
        tot1 = 0
        tot2 = 0
        tot3 = 0
        for ct in recs:
            date = CCD(ct[0], "D1", 10)
            move = CCD(ct[1], "SD", 13.2)
            days = CCD(ct[2], "UI", 5)
            rate = CCD(ct[3], "UD", 5.2)
            intr = CCD(ct[4], "SD", 13.2)
            bals = CCD(ct[5], "SD", 13.2)
            admn = CCD(ct[6], "SD", 13.2)
            tot1 = float(ASD(tot1) + ASD(move.work))
            tot2 = float(ASD(tot2) + ASD(intr.work))
            tot3 = float(ASD(tot3) + ASD(admn.work))
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingDeposit()
            self.fpdf.drawText("%s %s %s %s %s %s %s" % (date.disp, move.disp,
                days.disp, rate.disp, intr.disp, bals.disp, admn.disp))
            self.pglin += 1
        self.fpdf.setFont(style="B")
        self.fpdf.underLine(txt=self.head)
        move = CCD(tot1, "SD", 13.2)
        intr = CCD(tot2, "SD", 13.2)
        admn = CCD(tot3, "SD", 13.2)
        self.fpdf.drawText("%-10s %s %11s %s %s %s" % ("Totals", move.disp, "",
            intr.disp, bals.disp, admn.disp))

    def printTrans(self):
        col = self.sql.rcatnt_col
        bal = 0
        for ct in self.trn:
            trdt = CCD(ct[col.index("rtu_trdt")], "D1", 10)
            refno = CCD(ct[col.index("rtu_refno")], "Na", 9)
            trtp = CCD(ct[col.index("rtu_type")], "UI", 1)
            mtyp = CCD(ct[col.index("rtu_mtyp")], "UI", 1)
            batch = CCD(ct[col.index("rtu_batch")], "Na", 7)
            desc = CCD(ct[col.index("rtu_desc")], "NA", 30)
            tramt = ct[col.index("rtu_tramt")]
            if tramt < 0:
                debit = CCD(0, "SD", 13.2)
                credit = CCD(tramt, "SD", 13.2)
            else:
                debit = CCD(tramt, "SD", 13.2)
                credit = CCD(0, "SD", 13.2)
            if mtyp.work != 2:
                bal = float(ASD(bal) + ASD(tramt))
            tot = CCD(bal, "SD", 13.2)
            taxamt = CCD(ct[col.index("rtu_taxamt")], "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" % (trdt.disp,
                refno.disp, rctrtp[(trtp.work - 1)][0],
                rcmvtp[(mtyp.work - 1)][0], batch.disp, desc.disp,
                debit.disp, credit.disp, tot.disp, taxamt.disp))
            self.pglin += 1

    def pageHeading(self, deposit=False):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if deposit:
            self.fpdf.drawText("%-42s %-10s %49s %5s" % \
                ("Rentals Ledger Deposit Interrogation as at", self.depdtd,
                "Page", self.pgnum))
        else:
            self.fpdf.drawText("%-34s %-10s %57s %5s" % \
                ("Rentals Ledger Interrogation as at", self.sysdtd,
                "Page", self.pgnum))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def pageHeadingDeposit(self):
        self.fpdf.drawText("%-16s %s %s %s %s %s %s %s %s" % ("",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1], "",
            self.df.topf[0][2][3], self.df.t_disp[0][0][2]))
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-10s %-13s %-5s %-5s %-13s %-13s %-13s" % \
            ("   Date", "    Deposits", " Days", " Rate", "    Interest",
            "     Balance", "       Admin"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def pageHeadingTrans(self):
        self.fpdf.drawText("%-16s %s %s %s %s %s %s %s %s" % ("",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1], "",
            self.df.topf[0][2][3], self.df.t_disp[0][0][2]))
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-10s %-9s %-3s %-3s %-7s %-30s %-13s %-13s "\
            "%-13s" % ("   Date", "Reference", "Typ", "Mov", "Batch",
            "Remarks", "       Debit", "      Credit",  "     Balance"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
