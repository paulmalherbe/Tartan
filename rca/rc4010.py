"""
SYNOPSIS
    Rentals Owners Interrogation.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2025 Paul Malherbe.

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

class rc4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcaowm", "rcaowt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Rental Ledger Interrogation (%s)" % self.__class__.__name__)
        own = {
            "stype": "R",
            "tables": ("rcaowm",),
            "cols": (
                ("rom_acno", "", 0, "Own-Code"),
                ("rom_name", "", 0, "Name", "Y")),
            "where": [("rom_cono", "=", self.opts["conum"])]}
        tag = (
            ("Owner",self.doTagSelect,("T",0,2),("T",0,1)),
            ("Balances",self.doTagSelect,("T",0,2),("T",0,1)),
            ("Transactions",self.doTrans,("T",0,2),("T",0,1)))
        fld = (
            (("T",0,0,0),"INA",7,"Account","Account Code",
                "","N",self.doAccount,own,None,("notblank",)),
            (("T",0,0,0),"ONA",30,"Name"),
            (("T",1,0,0),"ONA",30,"Address-1"),
            (("T",1,1,0),"ONA",30,"Address-2"),
            (("T",1,2,0),"ONA",30,"Address-3"),
            (("T",1,3,0),"ONA",4,"Postal Code"),
            (("T",1,4,0),"ONA",20,"Home Number"),
            (("T",1,5,0),"ONA",20,"Office Number"),
            (("T",1,6,0),"ONA",20,"Mobile Number"),
            (("T",1,7,0),"ONA",20,"Fax Number"),
            (("T",1,8,0),"OTX",50,"E-Mail Address"),
            (("T",1,9,0),"ONA",10,"VAT Number"),
            (("T",1,10,0),"OUA",1,"VAT Default"),
            (("T",1,11,0),"ONA",20,"Bank Name"),
            (("T",1,12,0),"ONA",8,"Branch IBT"),
            (("T",1,13,0),"ONA",16,"Bank Number"),
            (("C",2,0,0),"OSD",11.2,"Value","",
                "","N",None,None,None,None,("Details",5)))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None)
        txt = (self.doExit, None, None, None)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        self.df.colLabel[2][0].configure(text="Rentals ")
        self.df.colLabel[2][1].configure(text="Receipts")
        self.df.colLabel[2][2].configure(text="Payments")
        self.df.colLabel[2][3].configure(text="Journals")
        self.df.colLabel[2][4].configure(text="Balance ")

    def doAccount(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaowm", where=[("rom_cono", "=",
            self.opts["conum"]), ("rom_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Owner"
        self.acno = w
        self.name = acc[self.sql.rcaowm_col.index("rom_name")]
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        for num, fld in enumerate(acc[3:-1]):
            self.df.loadEntry("T", 1, num, data=fld)
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
        bal = self.sql.getRec("rcaowt", cols=["rot_type",
            "round(sum(rot_tramt), 2)"], where=[("rot_cono", "=",
            self.opts["conum"]), ("rot_acno", "=", self.acno)],
            group="rot_type", order="rot_type")
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
        self.df.loadEntry("C", 2, 0, data=rtl)
        self.df.loadEntry("C", 2, 1, data=rec)
        self.df.loadEntry("C", 2, 2, data=pmt)
        self.df.loadEntry("C", 2, 3, data=jnl)
        self.df.loadEntry("C", 2, 4, data=bal)
        self.trn = self.sql.getRec("rcaowt", where=[("rot_cono", "=",
            self.opts["conum"]), ("rot_acno", "=", self.acno)],
            order="rot_trdt, rot_type")

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doTrans(self):
        tit = "Transactions for Account: %s - %s" % (self.acno, self.name)
        tab = ["rcaowt"]
        col = (
            ("rot_trdt", "", 0, "   Date"),
            ("rot_curdt", "", 0, "Curr-Dt"),
            ("rot_batch", "", 0, "Batch"),
            ("rot_type", ("XX", rttrtp), 3, "Typ"),
            ("rot_refno", "", 0, "Reference", "Y"),
            ("rot_tramt", "", 0, "     Amount"),
            ("rot_taxamt", "", 0, " VAT-Amount"),
            ("rot_desc", "", 0, "Details"))
        whr = [("rot_cono", "=", self.opts["conum"]),
            ("rot_acno", "=", self.acno)]
        odr = "rot_trdt, rot_type"
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.df.nb.Page3, title=tit, tables=tab,
            cols=col, where=whr, order=odr)
        self.df.enableButtonsTags(state=state)
        self.df.selPage("Owner")

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "RCA", self.acno)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Owner")
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
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit,
                    repprt=["N", "V", "view"])
        elif opt == "B":
            if not self.trn:
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
            if self.trn:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])

    def printInfo(self):
        for x in range(0, len(self.df.topf[0])):
            self.fpdf.drawText("%-26s%-25s %s" % ("",
                self.df.topf[0][x][3], self.df.t_disp[0][0][x]))
        self.fpdf.drawText()
        for x in range(0, len(self.df.topf[1])):
            self.fpdf.drawText("%-26s%-25s %s" % ("",
                self.df.topf[1][x][3], self.df.t_disp[1][0][x]))
        self.fpdf.drawText()
        self.pglin += 3 + len(self.df.topf[2])
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
        for n, d in enumerate(self.df.c_disp[2]):
            self.fpdf.drawText("%26s%-34s %13s" % ("", desc[n], d[0]))

    def printTrans(self):
        col = self.sql.rcaowt_col
        bal = 0
        for ct in self.trn:
            trdt = CCD(ct[col.index("rot_trdt")], "D1", 10)
            refno = CCD(ct[col.index("rot_refno")], "Na", 9)
            trtp = CCD(ct[col.index("rot_type")], "UI", 1)
            batch = CCD(ct[col.index("rot_batch")], "Na", 7)
            desc = CCD(ct[col.index("rot_desc")], "NA", 30)
            tramt = ct[col.index("rot_tramt")]
            if tramt < 0:
                debit = CCD(0, "SD", 13.2)
                credit = CCD(tramt, "SD", 13.2)
            else:
                debit = CCD(tramt, "SD", 13.2)
                credit = CCD(0, "SD", 13.2)
            bal = float(ASD(bal) + ASD(tramt))
            tot = CCD(bal, "SD", 13.2)
            taxamt = CCD(ct[col.index("rot_taxamt")], "SD", 13.2)
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
        self.fpdf.drawText("%-16s %s %s %s %s %s" % ("",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1]))
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
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
