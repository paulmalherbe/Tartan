"""
SYNOPSIS
    Debtors Interrogation.

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
from TartanClasses import ASD, Balances, GetCtl, NotesCreate, PrintInvoice
from TartanClasses import RepPrt, Sql, SelectChoice, TabPrt, TartanDialog
from tartanFunctions import askChoice, getTrn
from tartanWork import drtrtp, mthnam

class dr4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        tables = [
            "ctlrep", "ctlmes",
            "drsact", "drschn", "drsmst", "drstrn", "drstyp",
            "slsiv1"]
        self.sql = Sql(self.opts["mf"].dbm, tables,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.chains = drsctl["ctd_chain"]
        self.fromad = drsctl["ctd_emadd"]
        self.paidup = "N"
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Debtors Interrogation (%s)" % self.__class__.__name__)
        drc = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        ratings = {
            "N": "",
            "G": "",
            "F": "Fair",
            "P": "Poor",
            "B": "BAD!"}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1"),
                ("drm_rating", ("RR", ratings), 4, "RATE")),
            "where": [("drm_cono", "=", self.opts["conum"])]}
        if self.chains == "Y":
            drm["whera"] = [["T", "drm_chain", 0]]
        else:
            drm["where"].append(("drm_chain", "=", 0))
        tag = (
            ("Basic-_A", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Basic-_B", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("History", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Trans", self.doTrans1, ("T",0,0), ("T",0,1)),
            ("Other", self.doOthers, ("T",0,0), ("T",0,1)))
        r1s = (("No","N"),("Yes","Y"))
        fld = [
            [("T",0,0,0),"IUI",3,"Chain Store","",
                "","N",self.doChain,drc,None,("efld",)],
            [("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","N",self.doAcno,drm,None,("notblank",)],
            [("T",0,0,0),"ONA",30,"Name"],
            [("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","N",self.doAcno,drm,None,("notblank",)],
            [("T",0,0,0),"ONA",30,"Name"],
            (("T",1,0,0),"ONA",30,"Name"),
            (("T",1,1,0),"ONA",30,"Address Line 1"),
            (("T",1,2,0),"ONA",30,"Address Line 2"),
            (("T",1,3,0),"ONA",30,"Address Line 3"),
            (("T",1,4,0),"ONA",4,"Postal Code"),
            (("T",1,5,0),"ONA",20,"Telephone"),
            (("T",1,6,0),"ONA",20,"Fax"),
            (("T",1,7,0),"ONA",30,"Manager"),
            (("T",1,7,0),"OTX",40,"E-Mail"),
            (("T",1,8,0),"ONA",30,"Accounts Contact"),
            (("T",1,8,0),"OTX",40,"E-Mail"),
            (("T",1,9,0),"ONA",30,"Sales Contact"),
            (("T",1,9,0),"OTX",40,"E-Mail"),
            (("T",1,10,0),"Od1",10,"Date Opened"),
            (("T",1,11,0),"Od1",10,"Date Registered"),
            (("T",1,12,0),"ONA",10,"V.A.T Number"),
            (("T",1,13,0),"ONA",7,"Delivery Code"),
            (("T",1,14,0),"ONa",3,"Rep Code"),
            (("T",1,14,0),"ONA",26,""),
            (("T",1,15,0),"ONA",3,"Business Activity"),
            (("T",1,15,0),"ONA",26,""),
            (("T",1,16,0),"ONA",3,"Business Type"),
            (("T",1,16,0),"ONA",26,""),
            (("T",2,0,0),"OUI",1,"Price Level"),
            (("T",2,1,0),"OUD",5.2,"Discount Percentage"),
            (("T",2,2,0),"OUD",5.2,"Interest Percentage"),
            (("T",2,3,0),"OUI",3,"Referral Terms"),
            (("T",2,4,0),"OUI",3,"Rejected Terms"),
            (("T",2,5,0),"OUI",5,"Credit Limit"),
            (("T",2,6,0),"OUA",1,"Stop Indicator"),
            (("T",2,7,0),"OUI",3,"Invoice Message"),
            (("T",2,7,0),"ONA",40,""),
            (("T",2,8,0),"OUI",3,"Statement Message"),
            (("T",2,8,0),"ONA",40,""),
            (("T",2,9,0),"OUA",1,"Credit Rating"),
            (("T",2,10,0),"OUA",1,"Status"),
            (("T",3,0,0),"Od1",10,"Date Last Sale"),
            (("T",3,1,0),"Od1",10,"Date Last Paid"),
            (("T",3,2,0),"OSD",12.2,"Total Balance"),
            (("T",3,3,0),"OSD",12.2,"Current"),
            (("T",3,4,0),"OSD",12.2,"30 Days"),
            (("T",3,5,0),"OSD",12.2,"60 Days"),
            (("T",3,6,0),"OSD",12.2,"90 Days"),
            (("T",3,7,0),"OSD",12.2,"120 Days"),
            (("C",4,0,0),"OSD",13.2,"Sales","","","N",
                None,None,None,None,("Months",13)),
            (("C",4,0,1),"OSD",13.2,"Receipts"),
            (("T",5,0,0),("IRB",r1s),1,"History","",
                "N","N",self.doTrans2,None,None,None,None)]
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None, None, None)
        txt = (self.doExit, None, None, None, None, self.doExit)
        if self.chains == "Y":
            del fld[3]
            del fld[3]
        else:
            del fld[0]
            del fld[0]
            del fld[0]
            self.chain = 0
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

    def doChain(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
                self.opts["conum"]), ("chm_chain", "=", w)], limit=1)
            if not acc:
                return "Invalid Chain Store"
        self.chain = w

    def doAcno(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_chain", "=", self.chain),
            ("drm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        self.name = acc[self.sql.drsmst_col.index("drm_name")]
        self.df.loadEntry("T",pag,p+1,data=acc[3])
        d = 3
        for pg in range(1, 3):
            for x in range(0, self.df.topq[pg]):
                if pg == 1 and x in (18, 20, 22, 24):
                    continue
                if pg == 2 and x in (8, 10):
                    continue
                if pg == 2 and x == 11 and not acc[d]:
                    data = "N"
                else:
                    data = acc[d]
                self.df.loadEntry("T", pg, x, data=data)
                d = d + 1
        self.loadRep()
        self.loadAct()
        self.loadTyp()
        self.loadMes()
        self.loadBalances()
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadRep(self):
        acc = self.sql.getRec("ctlrep", where=[("rep_cono", "=",
            self.opts["conum"]), ("rep_code", "=", self.df.t_work[1][0][17])],
            cols=["rep_name"], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 18, data=acc[0])

    def loadAct(self):
        acc = self.sql.getRec("drsact", where=[("dac_code", "=",
            self.df.t_work[1][0][19])], cols=["dac_desc"], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 20, data=acc[0])

    def loadTyp(self):
        acc = self.sql.getRec("drstyp", where=[("dtp_code", "=",
            self.df.t_work[1][0][21])], cols=["dtp_desc"], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 22, data=acc[0])

    def loadMes(self):
        acc = self.sql.getRec("ctlmes", where=[("mss_system", "=",
            "INV"), ("mss_message", "=", self.df.t_work[2][0][7])],
            cols=["mss_detail"], limit=1)
        if acc:
            self.df.loadEntry("T", 2, 8, data=acc[0])
        acc = self.sql.getRec("ctlmes", where=[("mss_system", "=",
            "STA"), ("mss_message", "=", self.df.t_work[2][0][9])],
            cols=["mss_detail"], limit=1)
        if acc:
            self.df.loadEntry("T", 2, 10, data=acc[0])

    def loadBalances(self):
        bals = Balances(self.opts["mf"], "DRS", self.opts["conum"],
            int(self.sysdtw / 100), (self.chain, self.acno))
        obal, tbal, ages = bals.doAllBals()
        this, hist = bals.doCrsDrsHist()
        self.sale = hist[0]
        self.pays = hist[1]
        last = self.sql.getRec("drstrn", cols=["max(drt_trdt)"],
            where=[("drt_cono", "=", self.opts["conum"]), ("drt_chain", "=",
            self.chain), ("drt_acno", "=", self.acno), ("drt_type", "=", 1)],
            limit=1)
        if not last or not last[0]:
            lastsald = 0
        else:
            lastsald = last[0]
        last = self.sql.getRec("drstrn", cols=["max(drt_trdt)"],
            where=[("drt_cono", "=", self.opts["conum"]), ("drt_chain", "=",
            self.chain), ("drt_acno", "=", self.acno), ("drt_type", "=", 5)],
            limit=1)
        if not last or not last[0]:
            lastpayd = 0
        else:
            lastpayd = last[0]
        for x in range(0, 8):
            if x == 0:
                data = lastsald
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
            self.df.loadEntry("C", 4, p, data=self.sale[x])
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
            ("drt_cono", "=", self.opts["conum"]),
            ("drt_chain", "=", self.chain),
            ("drt_acno", "=", self.acno)]
        if self.paidup == "Y":
            col, recs = getTrn(self.opts["mf"].dbm, "drs", whr=whr)
        else:
            col, recs = getTrn(self.opts["mf"].dbm, "drs", dte=self.curdt,
                whr=whr)
        if recs:
            data = []
            for dat in recs:
                data.append([
                    dat[col.index("drt_trdt")],
                    dat[col.index("drt_curdt")],
                    dat[col.index("drt_batch")],
                    dat[col.index("drt_type")],
                    dat[col.index("drt_ref1")],
                    self.getRef2(col, dat),
                    dat[col.index("drt_tramt")],
                    dat[col.index("paid")],
                    dat[col.index("balance")],
                    dat[col.index("drt_desc")]])
            if self.chains == "Y":
                tit = "Transactions for Account: %s %s - %s" % \
                    (self.chain, self.acno, self.name)
            else:
                tit = "Transactions for Account: %s - %s" % \
                    (self.acno, self.name)
            col = (
                ("drt_trdt", "   Date", 10, "D1", "N"),
                ("drt_curdt", "Curr-Dt", 7, "D2", "N"),
                ("drt_batch", "Batch", 7, "Na", "N"),
                ("drt_type", "Typ", 3, ("XX", drtrtp), "N"),
                ("drt_ref1", "Reference", 9, "Na", "Y"),
                ("drt_ref2", "Ref-Number-Two", 14, "Na", "Y"),
                ("drt_tramt", "    Amount", 13.2, "SD", "N"),
                ("alloc", " Allocated", 13.2, "SD", "N"),
                ("balan", "   Balance", 13.2, "SD", "N"),
                ("drt_desc", "Details", 30, "NA", "N"))
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page5, tit, col, data)
                # If Invoice or Credit Note, attempt to display the document
                # else display all transaction details
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    if rec.selection[4] in (1, 4):
                        if rec.selection[4] == 1:
                            typ = "I"
                        else:
                            typ = "C"
                        try:
                            doc = int(rec.selection[5])
                            inv = self.sql.getRec("slsiv1",
                                where=[("si1_cono", "=", self.opts["conum"]),
                                ("si1_rtn", "=", typ), ("si1_docno", "=", doc)],
                                limit=1)
                        except:
                            inv = []
                    else:
                        inv = []
                    if inv:
                        PrintInvoice(self.opts["mf"], self.opts["conum"],
                            self.opts["conam"], typ, doc, repprt=["N", "V",
                            "view"], copy="y")
                    else:
                        whr = [
                            ("drt_cono", "=", self.opts["conum"]),
                            ("drt_chain", "=", self.chain),
                            ("drt_acno", "=", self.acno),
                            ("drt_type", "=", rec.selection[4]),
                            ("drt_ref1", "=", rec.selection[5])]
                        TabPrt(self.opts["mf"], tabs="drstrn", where=whr,
                            pdia=False)
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def getRef2(self, col, dat):
        dtyp = dat[col.index("drt_type")]
        ref1 = dat[col.index("drt_ref1")]
        ref2 = dat[col.index("drt_ref2")]
        if dtyp not in (1, 2):
            return ref2
        try:
            doc = int(ref1)
        except:
            return ref2
        if dtyp == 1:
            styp = "I"
        else:
            styp = "C"
        sls = self.sql.getRec("slsiv1", cols=["si1_our_ord",
            "si1_cus_ord"], where=[("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "=", styp), ("si1_docno", "=", doc)], limit=1)
        if sls and sls[1].strip()[:9] == ref2.strip():
            return sls[1]
        return ref2

    def doOthers(self):
        si1 = self.sql.slsiv1_col
        wh1 = [
            ("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "in", ("Q", "O", "W")),
            ("si1_chain", "=", self.chain),
            ("si1_acno", "=", self.acno),
            ("si1_invno", "=", "")]
        recs = self.sql.getRec("slsiv1", where=wh1, order="si1_date")
        if recs:
            data = []
            for dat in recs:
                wh2 = [
                    ("si2_cono", "=", self.opts["conum"]),
                    ("si2_rtn", "=", dat[si1.index("si1_rtn")]),
                    ("si2_docno", "=", dat[si1.index("si1_docno")])]
                si2 = self.sql.getRec("slsiv2", cols=["si2_disc_per",
                    "si2_qty", "si2_price", "si2_vat_rate"], where=wh2)
                incamt = 0
                for dis, qty, pri, vat in si2:
                    incrat = float(ASD(100.0) + ASD(vat))
                    incpri = round((pri * incrat / 100.0), 4)
                    net = float(ASD(100.0) - ASD(dis))
                    inc = round((qty * incpri * net / 100.0), 2)
                    incamt = float(ASD(incamt) + ASD(inc))
                data.append([
                    dat[si1.index("si1_date")],
                    dat[si1.index("si1_rtn")],
                    dat[si1.index("si1_docno")],
                    dat[si1.index("si1_cus_ord")],
                    dat[si1.index("si1_jobno")],
                    dat[si1.index("si1_contact")],
                    incamt])
            tit = "Quotes and Orders for Account: %s - %s" % \
                (self.acno, self.name)
            col = (
                ("si1_date", "   Date", 10, "D1", "N"),
                ("si1_rtn", "T", 1, "UA", "N"),
                ("si1_docno", "Doc-Numbr", 9, "UI", "N"),
                ("si1_cus_ord", "Cust-Ord-Num", 14, "Na"),
                ("si1_jobno", "Job-Num", 7, "Na"),
                ("si1_contact", "Contact", 30, "NA"),
                ("incamt", "Total-Value", 12.2, "SD"))
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page6, tit, col, data)
                # Attempt to display the document
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    typ = rec.selection[2]
                    try:
                        doc = int(rec.selection[3])
                        PrintInvoice(self.opts["mf"], self.opts["conum"],
                            self.opts["conam"], typ, doc, repprt=["N", "V",
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
            self.opts["capnm"], "DRS", "%03i%s" % (self.chain, self.acno))
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
            tab = "drsmst"
            whr = [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_chain", "=", self.chain),
                ("drm_acno", "=", self.acno)]
            rp = TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
                name=self.__class__.__name__, tabs=tab, where=whr,
                keys=[self.chain, self.acno])
            repprt = rp.repprt
            repeml = rp.repeml
            xits = rp.xits
        else:
            repprt = None
            repeml = None
            xits = False
        if opt in ("T", "B") and not xits:
            heads = ["Debtor's Transactions",
                "Chain: %s  Account: %s  Name: %s" % \
                (self.chain, self.acno, self.name)]
            whr = [
                ("drt_cono", "=", self.opts["conum"]),
                ("drt_chain", "=", self.chain),
                ("drt_acno", "=", self.acno)]
            if self.paidup == "Y":
                col, recs = getTrn(self.opts["mf"].dbm, "drs", whr=whr)
            else:
                col, recs = getTrn(self.opts["mf"].dbm, "drs",
                    dte=self.curdt, whr=whr)
            cols = []
            data = []
            dic = self.sql.drstrn_dic
            for num, rec in enumerate(recs):
                dat = []
                for nam in ["drt_ref1", "drt_ref2", "drt_trdt", "drt_type",
                        "drt_tramt", "paid", "balance", "drt_desc"]:
                    if not num:
                        if nam == "drt_ref2":
                            cols.append(["a", "Na", 14, "Ref-Number-Two"])
                        elif nam == "paid":
                            cols.append(["paid", "SD", 13.2, "Paid"])
                        elif nam == "balance":
                            cols.append(["balance", "SD", 13.2, "Balance"])
                        else:
                            cols.append([nam, dic[nam][2], dic[nam][3],
                            dic[nam][5]])
                    if nam == "drt_ref2":
                        dat.append(self.getRef2(col, rec))
                    else:
                        dat.append(rec[col.index(nam)])
                data.append(dat)
            if repprt:
                prtdia = False
            else:
                prtdia = (("Y","V"),("Y","N"))
            rp = RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                ttype="D", tables=data, heads=heads, cols=cols,
                trtp=["drt_type", drtrtp], prtdia=prtdia, repprt=repprt,
                repeml=repeml, fromad=self.fromad)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
