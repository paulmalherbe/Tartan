"""
SYNOPSIS
    Creditors Interrogation.

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
from TartanClasses import ASD, Balances, GetCtl, NotesCreate, PrintOrder, RepPrt
from TartanClasses import SelectChoice, Sql, TabPrt, TartanDialog
from tartanFunctions import askChoice, getTrn
from tartanWork import crtrtp, mthnam

class cr4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn", "strpom"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.curdt = int(self.sysdtw / 100)
        self.paidup = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Interrogation (%s)" % self.__class__.__name__)
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [("crm_cono", "=", self.opts["conum"])]}
        tag = (
            ("Basic-_A", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Basic-_B", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("History", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Trans", self.doTrans1, ("T",0,2), ("T",0,1)),
            ("Orders", self.doOrders, ("T",0,2), ("T",0,1)))
        r1s = (("No","N"),("Yes","Y"))
        fld = (
            (("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","N",self.doAccNum,crm,None,None),
            (("T",0,0,0),"ONA",30,"Name"),
            (("T",1,0,0),"ONA",30,"Address Line 1"),
            (("T",1,1,0),"ONA",30,"Address Line 2"),
            (("T",1,2,0),"ONA",30,"Address Line 3"),
            (("T",1,3,0),"ONA",4,"Postal Code"),
            (("T",1,4,0),"ONA",20,"Telephone"),
            (("T",1,5,0),"ONA",20,"Fax"),
            (("T",1,6,0),"ONA",30,"Manager"),
            (("T",1,6,0),"OTX",30,"E-Mail"),
            (("T",1,7,0),"ONA",30,"Accounts"),
            (("T",1,7,0),"OTX",30,"E-Mail"),
            (("T",1,8,0),"ONA",30,"Orders"),
            (("T",1,8,0),"OTX",30,"E-Mail"),
            (("T",1,9,0),"Od1",10,"Date Opened"),
            (("T",1,10,0),"ONA",10,"V.A.T. Number"),
            (("T",2,0,0),"OUA",1,"Terms Base"),
            (("T",2,1,0),"OUI",2,"Statement Day"),
            (("T",2,2,0),"OUI",3,"Terms"),
            (("T",2,3,0),"OUI",5,"Credit Limit"),
            (("T",2,4,0),"OUD",5.2,"Trade Discount"),
            (("T",2,5,0),"OUD",5.2,"Settlement Discount"),
            (("T",2,6,0),"OUA",1,"Payment Indicator"),
            (("T",2,7,0),"OUA",20,"Bank Name"),
            (("T",2,8,0),"OUI",8,"Bank Branch"),
            (("T",2,9,0),"OUA",16,"Bank Account"),
            (("T",2,10,0),"OUI",7,"G/L Account"),
            (("T",2,11,0),"OUA",1,"Status"),
            (("T",3,0,0),"Od1",10,"Date Last Purchased"),
            (("T",3,1,0),"Od1",10,"Date Last Paid"),
            (("T",3,2,0),"OSD",13.2,"Total Balance"),
            (("T",3,3,0),"OSD",13.2,"Current"),
            (("T",3,4,0),"OSD",13.2,"30 Days"),
            (("T",3,5,0),"OSD",13.2,"60 Days"),
            (("T",3,6,0),"OSD",13.2,"90 Days"),
            (("T",3,7,0),"OSD",13.2,"120 Days"),
            (("C",4,0,0),"OSD",13.2,"Purchases","","","N",
                None,None,None,None,("Months",13)),
            (("C",4,0,1),"OSD",13.2,"Payments"),
            (("T",5,0,0),("IRB",r1s),0,"History", "",
                "N","N",self.doTrans2,None,None,None))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None, None, None)
        txt = (self.doExit, None, None, None, None, self.doExit)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        yer = int(self.sysdtw / 10000)
        mon = int((self.sysdtw % 10000) / 100)
        self.hist_tit = []
        for x in range(1, 14):
            if x == 13:
                txt = "Last 12 Month Total"
                self.df.colLabel[4][x-1].configure(text=txt)
                self.hist_tit.append(txt)
            else:
                nam = mthnam[mon][1]
                nam = nam + (" " * (15-len(nam))) + str(yer)
                self.df.colLabel[4][x-1].configure(text=nam)
                self.hist_tit.append(nam)
            if x != 13:
                mon = mon - 1
                if mon == 0:
                    mon = mon + 12
                    yer = yer - 1

    def doAccNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", where=[("crm_cono", "=",
            self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        self.name = acc[self.sql.crsmst_col.index("crm_name")]
        self.df.loadEntry("T",0, 1, data=self.name)
        seq = 3
        for x in range(0, self.df.topq[1]):
            self.df.loadEntry("T", 1, x, data=acc[seq])
            seq += 1
        for x in range(0, self.df.topq[2]):
            self.df.loadEntry("T", 2, x, data=acc[seq])
            seq += 1
        self.loadBalances()
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadBalances(self):
        bals = Balances(self.opts["mf"], "CRS", self.opts["conum"],
            int(self.sysdtw / 100), (self.acno,))
        obal, tbal, ages = bals.doAllBals()
        this, hist = bals.doCrsDrsHist()
        self.purch = hist[0]
        self.pays = hist[1]
        last = self.sql.getRec("crstrn", cols=["max(crt_trdt)"],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_acno", "=",
            self.acno), ("crt_type", "=", 1)], limit=1)
        if not last or not last[0]:
            lastpurd = 0
        else:
            lastpurd = last[0]
        last = self.sql.getRec("crstrn", cols=["max(crt_trdt)"],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_acno", "=",
            self.acno), ("crt_type", "=", 5)], limit=1)
        if not last or not last[0]:
            lastpayd = 0
        else:
            lastpayd = last[0]
        for x in range(0, 8):
            if x == 0:
                data = lastpurd
            elif x == 1:
                data = lastpayd
            elif x == 2:
                data = tbal
            else:
                data = ages[x-3]
            self.df.loadEntry("T", 3, x, data=data)
        p = 0
        for x in range(0, 13):
            i = 0
            self.df.loadEntry("C", 4, p, data=self.purch[x])
            p = p + 1
            i = i + 1
            pay = float(ASD(0) - ASD(self.pays[x]))
            self.df.loadEntry("C", 4, p, data=pay)
            p = p + 1
            i = i + 1

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 5, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        self.paidup = w
        whr = [
            ("crt_cono", "=", self.opts["conum"]),
            ("crt_acno", "=", self.acno)]
        if self.paidup == "Y":
            col, recs = getTrn(self.opts["mf"].dbm, "crs", whr=whr)
        else:
            col, recs = getTrn(self.opts["mf"].dbm, "crs", dte=self.curdt,
                whr=whr)
        if recs:
            data = []
            for dat in recs:
                data.append([
                    dat[col.index("crt_trdt")],
                    dat[col.index("crt_curdt")],
                    dat[col.index("crt_batch")],
                    dat[col.index("crt_type")],
                    dat[col.index("crt_ref1")],
                    dat[col.index("crt_tramt")],
                    dat[col.index("paid")],
                    dat[col.index("balance")],
                    dat[col.index("crt_desc")]])
            tit = "Transactions for Account: %s - %s" % (self.acno, self.name)
            col = (
                ("crt_trdt", "Date", 10, "D1", "N"),
                ("crt_curdt", "Curr-Dt", 7, "D2", "N"),
                ("crt_batch", "Batch", 7, "Na", "N"),
                ("crt_type", "Typ", 3, ("XX", crtrtp), "N"),
                ("crt_ref1", "Reference", 9, "Na", "Y"),
                ("crt_tramt", "Amount", 13.2, "SD", "N"),
                ("alloc", "Allocated", 13.2, "SD", "N"),
                ("balan", "Balance", 13.2, "SD", "N"),
                ("crt_desc", "Details", 30, "NA", "N"))
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page4, tit, col, data)
                # Display all transaction details
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    whr = [
                        ("crt_cono", "=", self.opts["conum"]),
                        ("crt_acno", "=", self.acno),
                        ("crt_type", "=", rec.selection[4]),
                        ("crt_ref1", "=", rec.selection[5])]
                    TabPrt(self.opts["mf"], tabs="crstrn", where=whr,
                        pdia=False)
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doOrders(self):
        col = self.sql.strpom_col
        whr = [
            ("pom_cono", "=", self.opts["conum"]),
            ("pom_acno", "=", self.acno),
            ("pom_delno", "<>", "cancel"),
            ("pom_deldt", "=", 0)]
        recs = self.sql.getRec("strpom", where=whr, order="pom_date")
        if recs:
            data = []
            for dat in recs:
                data.append([
                    dat[col.index("pom_date")],
                    dat[col.index("pom_ordno")],
                    dat[col.index("pom_cusord")],
                    dat[col.index("pom_jobnum")],
                    dat[col.index("pom_contact")]])
            tit = "Orders for Account: %s - %s" % (self.acno, self.name)
            col = (
                ("pom_date", "   Date", 10, "D1", "N"),
                ("pom_ordno", "Doc-Numbr", 9, "UI", "N"),
                ("pom_cusord", "Cust-Ord-Num", 15, "Na"),
                ("pom_jobnum", "Job-Num", 7, "Na"),
                ("pom_contact", "Contact", 30, "NA"))
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page6, tit, col, data)
                # Attempt to display the document
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    try:
                        doc = int(rec.selection[2])
                        PrintOrder(self.opts["mf"], self.opts["conum"],
                            self.opts["conam"], doc, repprt=["N", "V",
                            "view"], copy="y")
                    except:
                        pass
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "CRS", self.acno)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Basic-_A")
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
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if opt in ("I", "B"):
            table = "crsmst"
            whr = [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_acno", "=", self.acno)]
            rp = TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
                name=self.__class__.__name__, tabs=table, where=whr,
                keys=[self.acno])
            repprt = rp.repprt
            repeml = rp.repeml
            xits = rp.xits
        else:
            repprt = None
            repeml = None
            xits = False
        if opt in ("T", "B") and not xits:
            heads = ["Creditor's Transactions",
                "Account: %s  Name: %s" % (self.acno, self.name)]
            whr = [
                ("crt_cono", "=", self.opts["conum"]),
                ("crt_acno", "=", self.acno)]
            if self.paidup == "Y":
                col, recs = getTrn(self.opts["mf"].dbm, "crs", whr=whr)
            else:
                col, recs = getTrn(self.opts["mf"].dbm, "crs",
                    dte=self.curdt, whr=whr)
            cols = []
            data = []
            dic = self.sql.crstrn_dic
            for num, rec in enumerate(recs):
                dat = []
                for nam in ["crt_ref1", "crt_trdt", "crt_type",
                        "crt_tramt", "paid", "balance", "crt_desc"]:
                    if not num:
                        if nam == "paid":
                            cols.append(["paid", "SD", 13.2, "Paid"])
                        elif nam == "balance":
                            cols.append(["balance", "SD", 13.2, "Balance"])
                        else:
                            cols.append([nam, dic[nam][2], dic[nam][3],
                                dic[nam][5]])
                    dat.append(rec[col.index(nam)])
                data.append(dat)
            gtots = ["crt_tramt", "paid", "balance"]
            if repprt:
                prtdia = False
            else:
                prtdia = (("Y","V"),("Y","N"))
            rp = RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                ttype="D", tables=data, heads=heads, cols=cols,
                trtp=["crt_type", crtrtp], gtots=gtots, prtdia=prtdia,
                repprt=repprt, repeml=repeml, fromad=self.fromad)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
