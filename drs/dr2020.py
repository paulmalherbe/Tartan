"""
SYNOPSIS
    Debtors Ledger Receipts Data Capture.

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
from TartanClasses import AgeAll, ASD, Batches, GetCtl, Sql, TartanDialog, tk
from tartanFunctions import askQuestion, callModule, showError

class dr2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Valid Posting Routine
        if self.opts["rtn"] != 2:
            mes = "Invalid Routine %s" % str(self.opts["rtn"])
            showError(self.opts["mf"].body, "Control Error", mes)
            return
        # Setup SQL Object
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlvmf", "drschn",
            "drsmst", "drstrn", "genint", "genmst", "gentrn"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Check for Intercompany Facility
        if not self.sql.getRec("ctlmst", cols=["count(*)"],
                where=[("ctm_cono", "<>", self.opts["conum"])], limit=1)[0]:
            self.incoac = False
        else:
            itg = self.sql.getRec("genint", cols=["cti_inco"],
                where=[("cti_cono", "=", self.opts["conum"])])
            if itg:
                self.incoac = [self.opts["conum"]]
                [self.incoac.append(coy[0]) for coy in itg]
            else:
                self.incoac = False
        #
        self.gc = GetCtl(self.opts["mf"])
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.glint = drsctl["ctd_glint"]
        self.chains = drsctl["ctd_chain"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["drs_ctl", "vat_ctl", "dis_all"]
            if self.gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.drsctl = ctlctl["drs_ctl"]
            self.dis_all = ctlctl["dis_all"]
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.allcoy = self.opts["conum"]
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if self.chains == "N":
            self.chain = 0
        self.glt = 6
        self.agevar = tk.BooleanVar()
        self.agevar.set(False)
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "DRS", self.opts["rtn"],
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        self.bh.batval = float(ASD(0) - ASD(self.bh.batval))

    def drawDialog(self):
        drc = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1"))}
        if self.chains == "Y":
            drm["where"] = [("drm_cono", "=", self.opts["conum"])]
            drm["whera"] = [["C", "drm_chain", 0, 1]]
        else:
            drm["where"] = [
            ("drm_cono", "=", self.opts["conum"]),
            ("drm_chain", "=", 0)]
        drm["where"].append(("drm_stat", "<>", "X"))
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        viw = {
            "stype": "R",
            "tables": ("drstrn",),
            "cols": (
                ("drt_chain", "", 0, ""),
                ("drt_acno", "", 0, ""),
                ("drt_ref1", "", 0, ""),
                ("drt_trdt", "", 0, ""),
                ("drt_tramt", "", 0, ""),
                ("drt_taxamt", "", 0, "")),
            "where": [
                ("drt_cono", "=", self.opts["conum"]),
                ("drt_type", "=", self.opts["rtn"]),
                ("drt_batch", "=", self.bh.batno)],
            "order": "drt_seq"}
        tag = (
            ("Deposit", None, None, None, False),
            ("Allocation", None, None, None, False))
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"INa",9,"Reference","Reference Number One",
                "i","Y",self.doRef1,None,None,("efld",)),
            (("C",1,0,1),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,2),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,("notzero",)),
            (("C",1,0,3),"INA",(30),"Details","Deposit Details",
                "","N",self.doTrnDet,None,None,None),
            (("T",2,0,0),"OSD",13.2,"Unallocated Balance"),
            [("C",2,0,0),"OUI",3,"Coy","Company Number",
                self.opts["conum"],"N",self.doCoyNum,coy,None,("notzero",)],
            [("C",2,0,1),"IUI",3,"Chn","Chain Store",
                "r","N",self.doChain,drc,None,("efld",)],
            (("C",2,0,2),"INA",7,"Acc-Num","Account Number",
                "r","N",self.doDrsAcc,drm,None,("notblank",)),
            (("C",2,0,3),"ONA",30,"Name"),
            (("C",2,0,4),"ISD",13.2,"Receipt","Receipt Amount",
                "","N",self.doAllAmt,None,None,("efld",)),
            (("C",2,0,5),"ISD",13.2,"Discount","Discount Amount",
                "","N",self.doDisAmt,None,None,("efld",),None,
                "Discount Amount to be Added to the Receipt Amount"),
            (("C",2,0,6),"OSD",13.2,"Total-Amount")]
        if self.glint == "Y" and self.incoac:
            fld[7][1] = "IUI"
        if self.chains == "N":
            fld[8][1] = "OUI"
            but = [
                ("View Entries",viw,None,1,("C",2,3),("C",2,4),
                    "View Batch Transactions",1),
                ("Interrogate",None,self.queryDrs,0,("C",2,3),("C",2,0),
                    "Interrogate Debtors Accounts",1),
                ("Maintain",None,self.maintainDrs,0,("C",2,3),("C",2,4),
                    "Maintain Debtors Accounts",1),
                ("Canc_el",None,self.doCancel,0,("C",2,1),("C",1,1),"",1)]
        else:
            but = [
                ("View Entries",viw,None,0,("C",2,3),("C",2,4),
                    "View Batch Transactions",1),
                ("Interrogate",None,self.queryDrs,0,("C",2,2),("C",2,0),
                    "Interrogate Debtors Accounts",1),
                ("Maintain",None,self.maintainDrs,0,("C",2,2),("C",2,3),
                    "Maintain Debtors Accounts",1),
                ("Canc_el",None,self.doCancel,0,("C",2,1),("C",1,1),"",1)]
        but.extend((
                ("Age _Normal",None,self.doAgeNormal,0,None,None,
                    "Only Show Unallocated Transactions",2),
                ("Age _History",None,self.doAgeHistory,0,None,None,
                    "Show All Transactions, Including Already Allocated",2),
                ("Age _Automatic",None,self.doAgeAuto,0,None,None,
                    "Automatically Allocate the Amount Starting With the "\
                    "Oldest Unallocated One",2),
                ("Age _Current",None,self.doAgeCurrent,0,None,None,
                    "Leave the Transaction Unallocated",2)))
        txt = (None, None, None)
        cnd = [None, (self.endPage1,"y"), (self.endPage2,"y")]
        cxt = [None, self.exitPage1, self.exitPage2]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, txit=txt,
            cend=cnd, cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doRef1(self, frt, pag, r, c, p, i, w):
        if not w:
            trns = self.sql.getRec("drstrn", cols=["drt_ref1"],
                where=[("drt_cono", "=", self.opts["conum"]), ("drt_ref1",
                "like", "R________")], order="drt_ref1 desc")
            auto = False
            for trn in trns:
                try:
                    w = "R%08i" % (int(trn[0][1:]) + 1)
                    auto = True
                    break
                except:
                    pass
            if not auto:
                w = "R00000001"
            self.df.loadEntry(frt, pag, p, data=w)
        chk = self.sql.getRec("drstrn", cols=["drt_acno"],
            where=[("drt_cono", "=", self.opts["conum"]), ("drt_type", "=",
            self.opts["rtn"]), ("drt_ref1", "=", w)])
        if chk:
            return "A Transaction with this Reference Already Exists"
        self.ref1 = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        self.allocated = float(0.00)

    def endPage1(self):
        self.agecan = False
        self.batupd = False
        self.updateTables1()
        self.updateBatch()
        self.allocated = float(0.0)
        self.df.selPage("Allocation")
        self.df.loadEntry("T", 2, 0, data=self.trnamt)
        self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        if self.glint == "Y":
            # General Ledger Control Transaction (Bank)
            data = (self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.ref1, self.bh.batno, self.trnamt, 0.00,
                self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)

    def exitPage1(self):
        self.df.closeProcess()
        self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)], limit=1)
        if not acc:
            return "Invalid Company, Missing"
        if self.incoac and w not in self.incoac:
            return "Invalid Company, No Intercompany Record 1"
        if w != self.opts["conum"]:
            acc = self.sql.getRec("genint", where=[("cti_cono", "=", w),
                ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        self.allcoy = w

    def doChain(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", cols=["chm_chain"],
                where=[("chm_cono", "=", self.allcoy), ("chm_chain", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Chain Store"
        self.chain = w

    def doDrsAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", cols=["drm_name", "drm_stat"],
            where=[("drm_cono", "=", self.allcoy), ("drm_chain", "=",
            self.chain), ("drm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[1] == "X":
            return "Invalid Account, Redundant"
        self.dracno = w
        self.name = acc[0]
        self.df.loadEntry("C", pag, p+1, data=self.name)
        self.allref = self.ref1
        while self.sql.getRec("drstrn", cols=["drt_batch"],
                where=[("drt_cono", "=", self.allcoy), ("drt_chain", "=",
                self.chain), ("drt_acno", "=", self.dracno), ("drt_type",
                "=", self.opts["rtn"]), ("drt_ref1", "=", self.allref)]):
            self.doGetAnotherRef()

    def doGetAnotherRef(self):
        tit = ("Duplicate Reference Number",)
        fld = (
            (("T",0,0,0),"ONa",9,"Old Reference","",
                self.allref,"N",None,None,None,None),
            (("T",0,1,0),"INa",9,"New Reference","",
                "","N",self.doRefNew,None,None,("notblank",)))
        tnd = ((self.doRefEnd,"n"), )
        txt = (self.doRefExit, )
        state = self.df.disableButtonsTags()
        self.tf = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=tnd, txit=txt)
        self.tf.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doRefExit(self):
        self.tf.focusField("T", 0, 2)

    def doRefNew(self, frt, pag, r, c, p, i, w):
        self.allref = w

    def doRefEnd(self):
        self.tf.closeProcess()

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if w == 0:
            self.allamt = float(ASD(self.trnamt) - ASD(self.allocated))
            self.df.loadEntry(frt, pag, p, data=self.allamt)
        else:
            self.allamt = w

    def doDisAmt(self, frt, pag, r, c, p, i, w):
        if self.allamt < 0 and w > 0:
            ok = self.checkSign()
        elif self.allamt > 0 and w < 0:
            ok = self.checkSign()
        else:
            ok = "yes"
        if ok != "yes":
            return "Invalid Discount Amount (Sign Error)"
        self.disamt = w
        totamt = float(ASD(self.allamt) + ASD(self.disamt))
        self.df.loadEntry(frt, pag, p+1, data=totamt)

    def checkSign(self):
        return askQuestion(self.opts["mf"].body, "Check Sign",
            "The Sign of the Discount Amount is not the same "\
            "as the Sign of the Receipt Amount, Is This Correct?")

    def endPage2(self):
        self.amt = float(ASD(0) - ASD(self.allamt))
        self.dis = float(ASD(0) - ASD(self.disamt))
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Choose an Ageing Option")
        for x in range(4, 8):
            wid = getattr(self.df, "B%s" % x)
            self.df.setWidget(wid, "normal")
        self.agevar.set(True)
        self.df.mstFrame.wait_variable(self.agevar)
        self.df.enableButtonsTags(state=state)
        if self.agecan:
            self.doCancel()
            return
        # Debtors Ledger Transaction
        data = [self.allcoy, self.chain, self.dracno, self.opts["rtn"],
            self.allref, self.bh.batno, self.trndat, "", self.amt, 0.00,
            self.curdt, self.trndet, "", "N", self.opts["capnm"], self.sysdtw,
            0]
        self.sql.insRec("drstrn", data=data)
        if self.dis:
            data = [self.allcoy, self.chain, self.dracno, 6, self.allref,
                self.bh.batno, self.trndat, "", self.dis, 0.00, self.curdt,
                self.trndet, "", "N", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("drstrn", data=data)
        self.allocated = float(ASD(self.allocated) + ASD(self.allamt))
        if self.glint == "Y":
            # General Ledger Control Transaction (Debtors)
            amt = float(ASD(self.amt) + ASD(self.dis))
            data = (self.allcoy, self.drsctl, self.curdt, self.trndat,
                self.glt, self.allref, self.bh.batno, amt, 0.00, self.trndet,
                "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Control Transaction (Discount)
            if self.disamt:
                data = (self.allcoy, self.dis_all, self.curdt, self.trndat,
                    self.glt, self.allref, self.bh.batno, self.disamt, 0.00,
                    self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw,
                    0)
                self.sql.insRec("gentrn", data=data)
            # General Ledger Transaction (Intercompany)
            if self.allcoy != self.opts["conum"]:
                # General Ledger Transaction (Intercompany From)
                acc = self.sql.getRec("genint", cols=["cti_acno"],
                    where=[("cti_cono", "=", self.opts["conum"]), ("cti_inco",
                    "=", self.allcoy)], limit=1)[0]
                data = (self.opts["conum"], acc, self.curdt, self.trndat,
                    self.glt, self.allref, self.bh.batno, self.amt, 0.00,
                    self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw,
                    0)
                self.sql.insRec("gentrn", data=data)
                # General Ledger Transaction (Intercompany To)
                acc = self.sql.getRec("genint", cols=["cti_acno"],
                    where=[("cti_cono", "=", self.allcoy), ("cti_inco", "=",
                    self.opts["conum"])], limit=1)[0]
                amt = float(ASD(0) - ASD(self.amt))
                data = (self.allcoy, acc, self.curdt, self.trndat, self.glt,
                    self.allref, self.bh.batno, amt, 0.00, self.trndet, "N",
                    "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
        if self.allocated == self.trnamt:
            self.opts["mf"].dbm.commitDbase()
            self.df.clearFrame("C", 2)
            self.df.selPage("Deposit")
            self.df.advanceLine(1)
        else:
            bal = float(ASD(self.trnamt) - ASD(self.allocated))
            self.df.loadEntry("T", 2, 0, data=bal)
            self.df.advanceLine(2)

    def doAgeNormal(self):
        self.doAgeing("N")

    def doAgeHistory(self):
        self.doAgeing("H")

    def doAgeAuto(self):
        self.doAgeing("O")

    def doAgeCurrent(self):
        self.doAgeing("C")

    def doAgeing(self, atype):
        # Disable All Ageing Buttons
        for x in range(4, 8):
            wid = getattr(self.df, "B%s" % x)
            self.df.setWidget(wid, "disabled")
        self.opts["mf"].updateStatus("Select Transaction to Allocate Against")
        age = AgeAll(self.opts["mf"], system="drs", agetyp=atype,
            agekey=[self.allcoy, self.chain, self.dracno, self.opts["rtn"],
            self.allref, self.curdt, self.amt, self.dis])
        self.agecan = age.cancel
        self.agevar.set(False)

    def doCancel(self):
        if self.agecan:
            ok = "yes"
        else:
            ok = askQuestion(self.opts["mf"].body, head="Cancel",
                mess="Are You Certain You Want to Cancel This Entry?")
        if ok == "yes":
            self.opts["mf"].dbm.rollbackDbase()
            if self.batupd:
                self.updateBatch(rev=True)
            self.df.clearFrame("C", 2)
            self.df.selPage("Deposit")
            row = int((self.df.last[1][1] - 1) / self.df.colq[1])
            col = (row * self.df.colq[1]) + 1
            self.df.focusField("C", 1, col)

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty = self.bh.batqty - 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.trnamt))
        else:
            self.batupd = True
            self.bh.batqty = self.bh.batqty + 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.trnamt))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def queryDrs(self):
        callModule(self.opts["mf"], self.df, "dr4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def maintainDrs(self):
        callModule(self.opts["mf"], self.df, "dr1010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
