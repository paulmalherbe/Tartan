"""
SYNOPSIS
    Debtor's Ledger Data Capture.

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
from TartanClasses import AgeAll, ASD, Batches, GetCtl, Sql, TartanDialog, tk
from tartanFunctions import askQuestion, callModule, chkGenAcc, getVatRate
from tartanFunctions import showError

class dr2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Valid Posting Routine
        if self.opts["rtn"] not in (1, 3, 4, 5):
            showError(self.opts["mf"].body, "Control Error",
                "Invalid Routine %s, Only 1, 3, 4 and 5 Are Allowed" % \
                str(self.opts["rtn"]))
            return
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlvmf", "ctlvrf",
            "ctlvtf", "drschn", "drsmst", "drstrn", "genint", "genmst",
            "gentrn"], prog=self.__class__.__name__)
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
        self.gc = GetCtl(self.opts["mf"])
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.glint = drsctl["ctd_glint"]
        self.glinp = drsctl["ctd_glinp"]
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
        if self.opts["rtn"] == 1:
            self.glt = 1
        elif self.opts["rtn"] == 3:
            self.glt = 4
        elif self.opts["rtn"] == 4:
            self.glt = 1
        elif self.opts["rtn"] == 5:
            self.glt = 2
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
        if self.opts["rtn"] == 4:
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
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "whera": [["C", "glm_cono", 0, 2]]}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
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
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            [("C",1,0,0),"IUI",3,"Chn","Chain Store",
                "r","Y",self.doChain,drc,None,("efld",)],
            [("C",1,0,1),"INA",7,"Acc-Num","Account Number",
                "r","N",self.doDrsAcc,drm,None,("notblank",)],
            [("C",1,0,2),"ONA",10,"Name"],
            (("C",1,0,3),"INa",9,"Reference","Reference Number One",
                "i","N",self.doRef1,None,None,("notblank",)),
            (("C",1,0,4),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,5),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,("efld",))]
        if self.opts["rtn"] == 5:
            fld[4][2] = 20
            fld.extend([
                [["C",1,0,6],"ISD",13.2,"Discount",
                    "Discount Amount","","N",self.doDisAmt,None,None,None,None,
                    "Discout Amount to be Added to the Transaction Amount"],
                [["C",1,0,7],"OSD",13.2,"Total-Amount"],
                [["C",1,0,8],"INA",(20,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None]])
        elif self.glint == "Y":
            if self.glinp == "E":
                tx1 = "Exc-Amount"
                tx2 = "Exclusive Amount"
            else:
                tx1 = "Inc-Amount"
                tx2 = "Inclusive Amount"
            fld[4][2] = 24
            fld.extend([
                [["C",1,0,6],"INA",30,"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None],
                [("T",2,0,0),"OSD",13.2,"Unallocated Balance"],
                [("C",2,0,0),"IUI",3,"Coy","Company Number",
                    self.opts["conum"],"N",self.doCoyNum,coy,None,None],
                (("C",2,0,1),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,2),"ONA",19,"Description"),
                (("C",2,0,3),"IUA",1,"V","V.A.T Code",
                    self.taxdf,"N",self.doVatCode2,vtm,None,("notblank",)),
                (("C",2,0,4),"ISD",13.2,tx1,tx2,
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,5),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doAllVat,None,None,None),
                [("C",2,0,6),"INA",(26,30),"Details","",
                    "","N",self.doAllDet,None,None,("notblank",)]])
            if not self.incoac:
                fld[10][1] = "OUI"
        else:
            fld[4][2] = 22
            fld.extend([
                (("C",1,0,6),"IUA",1,"V","V.A.T Code",
                    self.taxdf,"N",self.doVatCode1,vtm,None,("notblank",)),
                (("C",1,0,7),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doVatAmt,None,None,None),
                [["C",1,0,8],"INA",(20,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None]])
        if self.chains == "N":
            fld[2][1] = "OUI"
            idx = 2
        else:
            idx = 1
        but = (
            ("Interrogate",None,self.queryDrs,0,("C",1,idx),("C",1,idx+1),
                "Interrogate Debtors Records",1),
            ("View Entries",viw,None,0,("C",1,idx),("C",1,idx+1),
                "View Batch Transactions",1),
            ("Maintain",None,self.maintainDrs,0,("C",1,idx),("C",1,idx+1),
                "Maintain Debtors Records",1),
            ("Canc_el",None,self.doCancel,0,("C",2,1),("C",1,1),
                "Cancel the Entry",1),
            ("Age _Normal",None,self.doAgeNormal,0,None,None,
                "Only Show Unallocated Transactions",2),
            ("Age _History",None,self.doAgeHistory,0,None,None,
                "Show All Transactions Including Already Allocated",2),
            ("Age _Automatic",None,self.doAgeAuto,0,None,None,
                "Automatically Allocate the Amount Starting With the "\
                "Oldest Unallocated One",2),
            ("Age _Current",None,self.doAgeCurrent,0,None,None,
                "Leave the Transaction Unallocated",2))
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] != 5 and self.glint == "Y":
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doChain(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", cols=["chm_chain"],
                where=[("chm_cono", "=", self.opts["conum"]), ("chm_chain",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Chain Store"
        self.chain = w

    def doDrsAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", cols=["drm_name", "drm_stat"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            self.chain), ("drm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[1] == "X":
            return "Invalid Account, Redundant"
        self.dracno = w
        self.name = acc[0]
        self.df.loadEntry("C", pag, p+1, data=self.name)

    def doRef1(self, frt, pag, r, c, p, i, w):
        self.ref1 = w
        acc = self.sql.getRec("drstrn", cols=["drt_batch"],
            where=[("drt_cono", "=", self.opts["conum"]), ("drt_chain", "=",
            self.chain), ("drt_acno", "=", self.dracno), ("drt_type", "=",
            self.opts["rtn"]), ("drt_ref1", "=", self.ref1)], limit=1)
        if acc:
            return "Transaction Already Exists"

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if self.glint == "Y" or self.opts["rtn"] == 5:
            self.vatcode = "N"
            self.vatamt = 0

    def doVatCode1(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if vrte is None:
            return "Invalid V.A.T Code"
        self.vatcode = w
        self.vatamt = round((self.trnamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry(frt, pag, p+1, self.vatamt)
        if not self.vatamt:
            return "sk1"

    def doVatAmt(self, frt, pag, r, c, p, i, w):
        if self.trnamt < 0 and w > 0:
            self.vatamt = float(ASD(0) - ASD(w))
        elif self.trnamt > 0 and w < 0:
            self.vatamt = float(ASD(0) - ASD(w))
        else:
            self.vatamt = w
        self.df.loadEntry(frt, pag, p, data=self.vatamt)

    def doDisAmt(self, frt, pag, r, c, p, i, w):
        if self.trnamt < 0 and w > 0:
            self.disamt = float(ASD(0) - ASD(w))
        elif self.trnamt > 0 and w < 0:
            self.disamt = float(ASD(0) - ASD(w))
        else:
            self.disamt = w
        self.df.loadEntry(frt, pag, p, data=self.disamt)
        totamt = float(ASD(self.trnamt) + ASD(self.disamt))
        self.df.loadEntry(frt, pag, p+1, data=totamt)

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        if self.opts["rtn"] != 5 and self.glint == "Y":
            self.df.colf[2][6][5] = w
        self.allocated = float(0.00)

    def endPage1(self):
        self.cancel = False
        self.agecan = False
        self.batupd = False
        self.updateTables1()
        if self.cancel:
            return
        else:
            self.updateBatch()
            if self.trnamt == 0:
                self.df.advanceLine(1)
            else:
                self.allocated = float(0.0)
                if self.opts["rtn"] == 5 or self.glint == "N":
                    self.doDrsTrn()
                    self.opts["mf"].dbm.commitDbase()
                    self.df.selPage("Transaction")
                    self.df.advanceLine(1)
                else:
                    self.df.selPage("Allocation")
                    self.df.loadEntry("T", 2, 0, data=self.trnamt)
                    self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        self.amt = self.trnamt
        self.vat = self.vatamt
        if self.opts["rtn"] == 1:                          # Invoices
            recon = 0
            self.dis = 0.00
        elif self.opts["rtn"] == 3:                        # Journals
            recon = 0
            self.dis = 0.00
        elif self.opts["rtn"] == 4:                        # Credit Notes
            recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.vat = float(ASD(0) - ASD(self.vat))
            self.dis = 0.00
        elif self.opts["rtn"] == 5:                        # Payments
            if self.trnamt == 0:
                recon = self.curdt
            else:
                recon = 0
            self.vat = 0.00
            self.dis = self.disamt
        if self.opts["rtn"] == 1:
            self.doAgeCurrent()
        else:
            state = self.df.disableButtonsTags()
            self.opts["mf"].updateStatus("Choose an Ageing Option")
            for x in range(4, 8):
                if self.opts["rtn"] == 3 and x == 6:
                    continue
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, "normal")
            self.df.setWidget(self.df.B4, "focus")
            self.agevar.set(True)
            self.df.mstFrame.wait_variable(self.agevar)
            self.df.enableButtonsTags(state=state)
            if self.agecan:
                self.doCancel()
                return
        if self.glint == "N":
            return
        # General Ledger Control Transaction (Debtors)
        val = float(ASD(self.amt) + ASD(self.dis))
        data = (self.opts["conum"], self.drsctl, self.curdt, self.trndat,
            self.glt, self.ref1, self.bh.batno, val, 0.00, self.trndet,
            "N", "", recon, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Control Transaction (Bank)
        if self.opts["rtn"] == 5:
            val = float(ASD(0) - ASD(self.amt))
            data = (self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.ref1, self.bh.batno, val, 0.00, self.trndet,
                "N", "", recon, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Control Transaction (Discount)
            if self.dis:
                val = float(ASD(0) - ASD(self.dis))
                data = (self.opts["conum"], self.dis_all, self.curdt,
                    self.trndat, self.glt, self.ref1, self.bh.batno, val,
                    0.00, self.trndet, "N", "", recon, self.opts["capnm"],
                    self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)

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
            agekey=[self.opts["conum"], self.chain, self.dracno,
            self.opts["rtn"], self.ref1, self.curdt, self.amt,
            self.dis])
        self.agecan = age.cancel
        if self.agevar.get():
            self.agevar.set(False)

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
            acc = self.sql.getRec("genint", where=[("cti_cono", "=",
                w), ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        self.allcoy = w

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.allcoy, w)
        if type(chk) is str:
            return chk
        if not chk[2]:
            self.taxgl = self.taxdf
        else:
            self.taxgl = chk[2]
        self.genacc = w
        self.df.loadEntry("C", pag, p+1, chk[0])
        self.df.loadEntry("C", pag, p+2, data=self.taxgl)

    def doVatCode2(self, frt, pag, r, c, p, i, w):
        ctlctl = self.gc.getCtl("ctlctl", self.allcoy, error=False)
        if not ctlctl:
            return "Missing ctlctl Record for Company"
        if self.gc.chkRec(self.opts["conum"], ctlctl, ["vat_ctl"]):
            return "Missing or Invalid Control Record"
        self.convat = ctlctl["vat_ctl"]
        self.vatrte = getVatRate(self.sql, self.allcoy, w, self.trndat)
        if self.vatrte is None:
            return "Invalid V.A.T Code"
        self.vatcode = w

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if not w:
            incamt = float(ASD(self.trnamt) - ASD(self.allocated))
        elif self.glinp == "E":
            incamt = round((w * (100 + self.vatrte) / 100), 2)
        else:
            incamt = w
        self.allamt = round((incamt * 100 / (100 + self.vatrte)), 2)
        self.allvat = float(ASD(incamt) - ASD(self.allamt))
        if self.glinp == "E":
            self.df.loadEntry(frt, pag, p, data=self.allamt)
        else:
            self.df.loadEntry(frt, pag, p, data=incamt)
        self.df.loadEntry(frt, pag, p+1, data=self.allvat)
        if not self.allvat:
            self.df.loadEntry(frt, pag, p+2, data=self.name)
            return "sk1"

    def doAllVat(self, frt, pag, r, c, p, i, w):
        if (self.allamt < 0 and w > 0) or (self.allamt > 0 and w < 0):
            w = float(ASD(0) - ASD(w))
        if self.glinp == "I" and w != self.allvat:
            self.allamt = float(ASD(self.allamt) + ASD(self.allvat) - ASD(w))
        self.allvat = w
        self.df.loadEntry(frt, pag, p, data=self.allvat)
        self.df.loadEntry(frt, pag, p+1, data=self.name)

    def doAllDet(self, frt, pag, r, c, p, i, w):
        self.alldet = w

    def doCancel(self):
        if self.agecan:
            ok = "yes"
        else:
            ok = askQuestion(self.opts["mf"].body, head="Cancel",
                mess="Are You Certain You Want to Cancel This Entry?")
        if ok == "yes":
            self.cancel = True
            self.opts["mf"].dbm.rollbackDbase()
            if self.batupd:
                self.updateBatch(rev=True)
            if self.glint == "Y" and self.opts["rtn"] != 5:
                self.df.clearFrame("C", 2)
            row = int((self.df.last[1][1] - 1) / self.df.colq[1])
            col = (row * self.df.colq[1]) + 1
            self.df.selPage("Transaction")
            self.df.focusField("C", 1, col)

    def endPage2(self):
        self.updateTables2()
        self.allocated = float(ASD(self.allocated) + \
            ASD(self.allamt) + ASD(self.allvat))
        if self.allocated == self.trnamt:
            self.doDrsTrn()
            self.opts["mf"].dbm.commitDbase()
            self.df.clearFrame("C", 2)
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
        else:
            bal = float(ASD(self.trnamt) - ASD(self.allocated))
            self.df.loadEntry("T", 2, 0, data=bal)
            self.df.advanceLine(2)

    def updateTables2(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        if self.opts["rtn"] == 1:                          # Invoices
            self.credit()
        elif self.opts["rtn"] == 3:                        # Journals
            self.credit()
        elif self.opts["rtn"] == 4:                        # Credit Notes
            self.debit()

    def debit(self):
        amt = self.allamt
        vat = self.allvat
        self.restDebitCredit(amt, vat)

    def credit(self):
        amt = float(ASD(0) - ASD(self.allamt))
        vat = float(ASD(0) - ASD(self.allvat))
        self.restDebitCredit(amt, vat)

    def restDebitCredit(self, amt, vat):
        # VAT Transaction (ctlvtf)
        data = (self.allcoy, self.vatcode, "O", self.curdt, "D",
            self.opts["rtn"], self.bh.batno, self.ref1, self.trndat,
            self.dracno, self.alldet, amt, vat, 0, self.opts["capnm"],
            self.sysdtw, 0)
        self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        # General Ledger Transaction (Allocation)
        data = (self.allcoy, self.genacc, self.curdt, self.trndat,
            self.glt, self.ref1, self.bh.batno, amt, vat, self.alldet,
            self.vatcode, "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Transaction (Intercompany)
        if self.allcoy != self.opts["conum"]:
            # General Ledger Transaction (Intercompany From)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.opts["conum"]), ("cti_inco", "=",
                self.allcoy)], limit=1)[0]
            val = float(ASD(amt) + ASD(vat))
            data = (self.opts["conum"], acc, self.curdt, self.trndat, self.glt,
                self.ref1, self.bh.batno, val, 0.00, self.alldet, "N",
                "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Transaction (Intercompany To)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.allcoy), ("cti_inco", "=",
                self.opts["conum"])], limit=1)[0]
            val = float(ASD(0) - ASD(amt) - ASD(vat))
            data = (self.allcoy, acc, self.curdt, self.trndat, self.glt,
                self.ref1, self.bh.batno, val, 0.00, self.alldet, "N",
                "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        if vat:
            # General Ledger Control Transaction (V.A.T.)
            data = (self.allcoy, self.convat, self.curdt, self.trndat,
                self.glt, self.ref1, self.bh.batno, vat, 0.00, self.alldet,
                "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        self.vat = float(ASD(self.vat) + ASD(vat))

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def doDrsTrn(self):
        # Debtors Ledger Transaction
        data = [self.opts["conum"], self.chain, self.dracno, self.opts["rtn"],
            self.ref1, self.bh.batno, self.trndat, "", self.amt, self.vat,
            self.curdt, self.trndet, self.vatcode, "N", self.opts["capnm"],
            self.sysdtw, 0]
        self.sql.insRec("drstrn", data=data)
        if not self.dis:
            return
        data = [self.opts["conum"], self.chain, self.dracno, 6, self.ref1,
            self.bh.batno, self.trndat, "", self.dis, self.vat, self.curdt,
            self.trndet, self.vatcode, "N", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("drstrn", data=data)

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
