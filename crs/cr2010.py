"""
SYNOPSIS
    Creditors Data Capture Screen and Execution.

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
from tartanFunctions import askQuestion, callModule, chkGenAcc, getNextCode
from tartanFunctions import getVatRate, paymentDate, showError

class cr2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Valid Posting Routine
        if self.opts["rtn"] not in (1, 2, 3, 4, 5):
            showError(self.opts["mf"].body, "Control Error",
                "Invalid Routine %s, Only 1 - 5 Are Allowed" % \
                str(self.opts["rtn"]))
            return
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlvmf", "ctlvrf",
            "ctlvtf", "crsmst", "crstrn", "genint", "genmst", "gentrn",
            "lonmf1", "lonmf2", "lonrte", "lontrn", "wagedc", "wagmst",
            "waglmf", "wagltf"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Check for Company record
        self.gc = GetCtl(self.opts["mf"])
        self.allcoy = self.opts["conum"]
        self.allnam = self.opts["conam"]
        ctlmst = self.gc.getCtl("ctlmst", self.allcoy)
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        # Check for Intercompany Facility
        if not self.sql.getRec("ctlmst", cols=["count(*)"],
                where=[("ctm_cono", "<>", self.opts["conum"])], limit=1)[0]:
            self.incoac = False
        else:
            rec = self.sql.getRec("genint", cols=["cti_inco"],
                where=[("cti_cono", "=", self.opts["conum"])])
            if rec:
                self.incoac = [self.opts["conum"]]
                [self.incoac.append(coy[0]) for coy in rec]
            else:
                self.incoac = False
        # Get Enabled Modules
        self.lonmod = False
        self.lonpag = None
        self.slnmod = False
        self.slnpag = None
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            if ctlmst["ctm_modules"][x:x+2] == "LN":
                self.lonmod = True
            elif ctlmst["ctm_modules"][x:x+2] == "SL":
                self.slnmod = True
        # Rest of Controls
        crsctl = self.gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.glint = crsctl["ctc_glint"]
        self.glinp = crsctl["ctc_glinp"]
        if self.glint == "Y":
            self.ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not self.ctlctl:
                return
            ctls = ["crs_ctl", "vat_ctl", "dis_rec"]
            if self.gc.chkRec(self.opts["conum"], self.ctlctl, ctls):
                return
            self.crsctl = self.ctlctl["crs_ctl"]
            self.disrec = self.ctlctl["dis_rec"]
        # Batch Header
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        if self.opts["rtn"] == 1:
            self.glt = 5
        elif self.opts["rtn"] == 2:
            self.glt = 6
        elif self.opts["rtn"] == 3:
            self.glt = 4
        elif self.opts["rtn"] == 4:
            self.glt = 5
        elif self.opts["rtn"] == 5:
            self.glt = 2
        self.agevar = tk.BooleanVar()
        self.othvar = tk.BooleanVar()
        self.agevar.set(False)
        self.othvar.set(False)
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "CRS", self.opts["rtn"],
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return

    def drawDialog(self):
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")]}
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
            "whera": [("C", "glm_cono", 0, 2)]}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        if self.opts["rtn"] in (1, 4) and self.lonmod:
            lm1 = {
                "stype": "R",
                "tables": ("lonmf1",),
                "cols": (
                    ("lm1_acno", "", 0, "Acc-Num"),
                    ("lm1_name", "", 0, "Name", "Y")),
                "whera": [("C", "lm1_cono", 0, 2)]}
            lm2 = {
                "stype": "R",
                "tables": ("lonmf2",),
                "cols": (
                    ("lm2_loan", "", 0, "Ln"),
                    ("lm2_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "lm2_cono", 0, 2),
                    ("C", "lm2_acno", 0)]}
        if self.opts["rtn"] in (1, 4) and self.slnmod:
            wgm = {
                "stype": "R",
                "tables": ("wagmst",),
                "cols": (
                    ("wgm_empno", "", 0, "EmpNo"),
                    ("wgm_sname", "", 0, "Surname", "Y"),
                    ("wgm_fname", "", 0, "Names")),
                "whera": [("C", "wgm_cono", 0, 2)]}
            lnm = {
                "stype": "R",
                "tables": ("waglmf",),
                "cols": (
                    ("wlm_loan", "", 0, "Ln"),
                    ("wlm_desc", "", 0, "Description", "Y")),
                "where": [("wlm_cono", "=", self.opts["conum"])],
                "whera": [
                    ("C", "wgm_cono", 0, 2),
                    ("C", "wlm_empno", 0)]}
            ced = {
                "stype": "R",
                "tables": ("wagedc",),
                "cols": (
                    ("ced_type", "", 0, "T"),
                    ("ced_code", "", 0, "Cde"),
                    ("ced_desc", "", 0, "Description", "Y")),
                "where": [("ced_type", "=", "D")],
                "whera": [("C", "wgm_cono", 0, 2)],
                "index": 1}
        viw = {
            "stype": "R",
            "tables": ("crstrn",),
            "cols": (
                ("crt_acno", "", 0, ""),
                ("crt_ref1", "", 0, ""),
                ("crt_trdt", "", 0, ""),
                ("crt_tramt", "", 0, ""),
                ("crt_taxamt", "", 0, "")),
            "where": [
                ("crt_cono", "=", self.opts["conum"]),
                ("crt_type", "=", self.opts["rtn"]),
                ("crt_batch", "=", self.bh.batno)],
            "order": "crt_seq",
            "comnd": self.doView}
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"INA",7,"Acc-Num","Account Number",
                "r","Y",self.doCrsAcc,crm,None,None),
            [("C",1,0,1),"ONA",10,"Name"],
            (("C",1,0,2),"INa",9,"Reference","Reference Number One",
                "i","N",self.doRef1,None,None,("notblank",)),
            (("C",1,0,3),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,4),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,None)]
        if self.opts["rtn"] in (2, 5):
            fld[3][2] = 22
            fld.extend([
                (("C",1,0,5),"ISD",13.2,"Discount","Discount Amount",
                    "","N",self.doDisAmt,None,None,None,None,
                    "Discount Amount to be Added to the Transaction Amount."),
                (("C",1,0,6),"OSD",13.2,"Total-Amount"),
                [("C",1,0,7),"INA",(22,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None]])
        elif self.glint == "Y":
            if self.glinp == "E":
                tx1 = "Exc-Amount"
                tx2 = "Exclusive Amount"
            else:
                tx1 = "Inc-Amount"
                tx2 = "Inclusive Amount"
            fld[3][2] = 30
            fld.extend([
                (("C",1,0,5),"INA",(27,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None),
                [("T",2,0,0),"OSD",13.2,"Unallocated Balance"],
                [("C",2,0,0),"IUI",3,"Coy","Company Number",
                    self.opts["conum"],"N",self.doCoyNum,coy,None,None],
                (("C",2,0,1),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,2),"ONA",19,"Description"),
                (("C",2,0,3),"IUA",1,"V","V.A.T Code",
                    "","N",self.doVatCode2,vtm,None,("notblank",)),
                (("C",2,0,4),"ISD",13.2,tx1,tx2,
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,5),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doAllVat,None,None,None),
                (("C",2,0,6),"INA",(26,30),"Details","",
                    "","N",self.doAllDet,None,None,("notblank",))])
            if not self.incoac:
                fld[9][1] = "OUI"
            nxt = 3
            if self.opts["rtn"] in (1, 4) and self.lonmod:
                fld.extend([
                    (("T",nxt,0,0),"OSD",13.2,"Unallocated Balance"),
                    (("C",nxt,0,0),"IUA",7,"Acc-Num","Account Number",
                        0,"N",self.doLonAcc,lm1,None,None),
                    (("C",nxt,0,1),"ONA",30,"Name"),
                    (("C",nxt,0,2),"IUI",2,"Ln","Loan Number",
                        "","N",self.doLonNum,lm2,None,None),
                    (("C",nxt,0,3),"INA",30,"Description","",
                        "","N",self.doLonDes,None,None,("notblank",)),
                    (("C",nxt,0,4),"ISD",13.2,"Amount","",
                        "","N",self.doLonAmt,None,None,("efld",)),
                    (("C",nxt,0,5),"IUD",6.2,"DRte-%","Debit Rate",
                        "","N",self.doLonDri,None,None,None),
                    (("C",nxt,0,6),"IUD",6.2,"CRte-%","Credit Rate",
                        "","N",self.doLonDri,None,None,None),
                    (("C",nxt,0,7),"IUI",3,"Mth","Period in Months",
                        "","N",self.doLonMth,None,None,("efld",)),
                    (("C",nxt,0,8),"OUD",12.2,"Repayment")])
                self.lonpag = nxt
                nxt += 1
            if self.opts["rtn"] in (1, 4) and self.slnmod:
                fld.extend([
                    (("T",nxt,0,0),"OSD",13.2,"Unallocated Balance"),
                    (("C",nxt,0,0),"IUI",5,"EmpNo","Employee Number",
                        0,"N",self.doEmpNum,wgm,None,None),
                    (("C",nxt,0,1),"ONA",20,"Name"),
                    (("C",nxt,0,2),"IUI",2,"Ln","Loan Number",
                        "","N",self.doSlnNum,lnm,None,None),
                    (("C",nxt,0,3),"INA",20,"Description","",
                        "","N",self.doSlnDes,None,None,("notblank",)),
                    (("C",nxt,0,4),"ISD",13.2,"Amount","",
                        "","N",self.doSlnAmt,None,None,("efld",)),
                    (("C",nxt,0,5),"IUI",3,"Cde","Deduction Code",
                        "","N",self.doSlnCod,ced,None,("efld",)),
                    (("C",nxt,0,6),"ONA",20,"Description"),
                    (("C",nxt,0,7),"IUD",6.2,"Intr-%","Interest Rate",
                        "","N",self.doSlnInt,None,None,None),
                    (("C",nxt,0,8),"IUD",13.2,"Ded-Amt","Deduction Amount",
                        "","N",self.doSlnDed,None,None,("efld",))])
                self.slnpag = nxt
        else:
            fld[3][2] = 20
            fld.extend([
                (("C",1,0,5),"IUA",1,"V","V.A.T Code",
                    self.taxdf,"N",self.doVatCode1,vtm,None,("notblank",)),
                (("C",1,0,6),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doVatAmt,None,None,None),
                [("C",1,0,7),"INA",(18,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None]])
        but = (
            ("Interrogate",None,self.queryCrs,0,("C",1,1),("C",1,2),
                "Interrogate Creditors Records",1),
            ("View Entries",viw,None,0,("C",1,1),("C",1,2),
                "View Batch Transactions",1),
            ("Maintain",None,self.maintainCrs,0,("C",1,1),("C",1,2),
                "Maintain Creditors Records",1),
            ("Canc_el",None,self.doCancel,0,("C",2,1),("C",1,1),
                "Cancel the Entry",1),
            ("Age _Normal",None,self.doAgeNormal,0,None,None,
                "Only Show Unallocated Transactions",2),
            ("Age _History",None,self.doAgeHistory,0,None,None,
                "Show All Transactions Including Already Allocated",2),
            ("Age _Automatic",None,self.doAgeAuto,0,None,None,
                "Automatically Allocate the Amount Starting With the "\
                "Oldest Unallocated Transaction",2),
            ("Age _Current",None,self.doAgeCurrent,0,None,None,
                "Leave the Transaction Unallocated",2))
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] not in (2, 5) and self.glint == "Y":
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
            if self.opts["rtn"] in (1, 4) and self.lonmod:
                tag.append(("LON", None, None, None, False))
                cnd.append((self.endLon,"y"))
                cxt.append(self.exitLon)
            if self.opts["rtn"] in (1, 4) and self.slnmod:
                tag.append(("SLN", None, None, None, False))
                cnd.append((self.endSln,"y"))
                cxt.append(self.exitSln)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doView(self, *event):
        self.df.focusField("C", 1, 1)

    def doCrsAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", cols=["crm_name", "crm_terms",
            "crm_vatno", "crm_termsb", "crm_stday", "crm_pydis",
            "crm_glac", "crm_stat"], where=[("crm_cono", "=",
            self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[7] == "X":
            return "Invalid Account, Redundant"
        self.cracno = w
        self.name = acc[0]
        self.term = acc[1]
        self.vatn = acc[2]
        self.base = acc[3]
        self.stdt = acc[4]
        self.pdis = acc[5]
        self.glac = acc[6]
        self.popv = False
        self.df.loadEntry(frt, pag, p+1, data=self.name)

    def doRef1(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crstrn", cols=["crt_batch"],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_acno", "=",
            self.cracno), ("crt_type", "=", self.opts["rtn"]), ("crt_ref1",
            "=", w)], limit=1)
        if acc:
            return "Transaction Already Exists"
        self.trnref = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if self.glint == "Y" or self.opts["rtn"] in (2, 5):
            self.vatcode = "N"
            self.vatamt = 0
        if self.opts["rtn"] not in (2, 5) and self.glint == "N":
            if not self.vatn:
                self.df.loadEntry(frt, pag, p+1, data="N")
            else:
                self.df.loadEntry(frt, pag, p+1, data=self.taxdf)

    def doVatCode1(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if vrte is None:
            return "Invalid V.A.T Code"
        if vrte and not self.vatn:
            ok = askQuestion(self.opts["mf"].window, "VAT Number",
                "This Account Does Not Have a VAT Number.\n\nMust "\
                "it be Populated?", default="yes")
            if ok == "yes":
                self.vatn = w
                self.popv = True
        self.vatcode = w
        self.vatamt = round((self.trnamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry(frt, pag, p+1, data=self.vatamt)
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
        if self.opts["rtn"] not in (2, 5) and self.glint == "Y":
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
                if self.opts["rtn"] in (2, 5) or self.glint == "N":
                    self.doCrsTrn()
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
            self.recon = 0
            self.dis = 0.00
            self.per = self.pdis
        elif self.opts["rtn"] == 2:                        # Receipts
            if self.trnamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            self.vat = 0.00
            self.dis = self.disamt
            self.per = 0.00
        elif self.opts["rtn"] == 3:                        # Journals
            self.recon = 0
            self.dis = 0.00
            self.per = 0.00
        elif self.opts["rtn"] == 4:                        # Credit Notes
            self.recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.vat = float(ASD(0) - ASD(self.vat))
            self.dis = 0.00
            self.per = self.pdis
        elif self.opts["rtn"] == 5:                        # Payments
            if self.trnamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.vat = 0.00
            self.dis = float(ASD(0) - ASD(self.disamt))
            self.per = 0.00
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
        # General Ledger Control Transaction (Creditors)
        val = float(ASD(0) - ASD(self.amt) - ASD(self.dis))
        data = (self.opts["conum"], self.crsctl, self.curdt, self.trndat,
            self.glt, self.trnref, self.bh.batno, val, 0.00, self.trndet,
            "N", "", self.recon, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Control Transaction (Bank)
        if self.opts["rtn"] in (2, 5):
            data = (self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.amt, 0.00,
                self.trndet, "N", "", self.recon, self.opts["capnm"],
                self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Control Transaction (Discount)
            if self.dis:
                data = (self.opts["conum"], self.disrec, self.curdt,
                    self.trndat, self.glt, self.trnref, self.bh.batno,
                    self.dis, 0.00, self.trndet, "N", "", self.recon,
                    self.opts["capnm"], self.sysdtw, 0)
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
        age = AgeAll(self.opts["mf"],  system="crs", agetyp=atype,
            agekey=[self.opts["conum"], self.cracno, self.opts["rtn"],
            self.trnref, self.curdt, self.amt, self.dis])
        self.agecan = age.cancel
        if self.agevar.get():
            self.agevar.set(False)

    def exitPage1(self):
        self.df.closeProcess()
        self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        nam = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)], limit=1)
        if not nam:
            return "Invalid Company, Missing"
        if self.incoac and w not in self.incoac:
            return "Invalid Company, No Intercompany Record 1"
        if w != self.opts["conum"]:
            acc = self.sql.getRec("genint", where=[("cti_cono", "=", w),
                ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        self.ctlctl = self.gc.getCtl("ctlctl", w)
        if not self.ctlctl:
            return "rf"
        self.allcoy = w
        self.allnam = nam[0]
        self.df.loadEntry(frt, pag, p+1, data=self.glac)

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        ctl = True
        self.loan = False
        if "lon_ctl" in self.ctlctl and w == self.ctlctl["lon_ctl"]:
            self.loan = "other"
        elif "wag_slc" in self.ctlctl and w == self.ctlctl["wag_slc"]:
            self.loan = "staff"
        if self.loan:
            ctl = False
        chk = chkGenAcc(self.opts["mf"], self.allcoy, w, ctl=ctl)
        if type(chk) is str:
            return chk
        if not self.vatn:
            self.taxgl = "N"
        elif not chk[2]:
            self.taxgl = self.taxdf
        else:
            self.taxgl = chk[2]
        self.genacc = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        self.df.loadEntry(frt, pag, p+2, data=self.taxgl)

    def doVatCode2(self, frt, pag, r, c, p, i, w):
        ctlctl = self.gc.getCtl("ctlctl", self.allcoy, error=False)
        if not ctlctl:
            return "Missing ctlctl Record for Company"
        if self.gc.chkRec(self.allcoy, ctlctl, ["vat_ctl"]):
            return "Missing or Invalid Control Record"
        self.convat = ctlctl["vat_ctl"]
        self.vatrte = getVatRate(self.sql, self.allcoy, w, self.trndat)
        if self.vatrte is None:
            return "Invalid V.A.T Code"
        if self.vatrte and not self.vatn:
            ok = askQuestion(self.opts["mf"].window, "VAT Number",
                "This Account Does Not Have a VAT Number.\n\nMust "\
                "it be Populated?", default="yes")
            if ok == "yes":
                self.vatn = w
                self.popv = True
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
            for pg in range(self.df.pgs, 1, -1):
                self.df.clearFrame("C", pg)
            self.df.selPage("Transaction")
            row = int((self.df.last[1][1] - 1) / self.df.colq[1])
            col = (row * self.df.colq[1]) + 1
            self.df.focusField("C", 1, col)
            if self.othvar.get():
                self.othvar.set(False)

    def endPage2(self):
        self.updateTables2()
        if self.loan and self.loan == "other":
            self.othtot = self.allamt
            self.df.selPage("LON")
            self.df.loadEntry("T", self.lonpag, 0, data=self.othtot)
            self.df.focusField("C", self.lonpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                return
        elif self.loan and self.loan == "staff":
            self.othtot = self.allamt
            self.df.selPage("SLN")
            self.df.loadEntry("T", self.slnpag, 0, data=self.othtot)
            self.df.focusField("C", self.slnpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                return
        self.allocated = float(ASD(self.allocated) + ASD(self.allamt) + \
            ASD(self.allvat))
        if self.allocated == self.trnamt:
            self.doCrsTrn()
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
            self.debit()
        elif self.opts["rtn"] == 3:                        # Journals
            self.debit()
        elif self.opts["rtn"] == 4:                        # Credit Notes
            self.credit()

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
        data = (self.allcoy, self.vatcode, "I", self.curdt, "C",
            self.opts["rtn"], self.bh.batno, self.trnref, self.trndat,
            self.cracno, self.alldet, amt, vat, 0, self.opts["capnm"],
            self.sysdtw, 0)
        self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        # General Ledger Transaction (Expense)
        data = (self.allcoy, self.genacc, self.curdt, self.trndat,
            self.glt, self.trnref, self.bh.batno, amt, vat, self.alldet,
            self.vatcode, "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Transaction (Intercompany)
        if self.allcoy != self.opts["conum"]:
            # General Ledger Transaction (Intercompany From)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.opts["conum"]),
                ("cti_inco", "=", self.allcoy)], limit=1)[0]
            val = float(ASD(amt) + ASD(vat))
            data = (self.opts["conum"], acc, self.curdt, self.trndat, self.glt,
                self.trnref, self.bh.batno, val, 0.00, self.alldet, "N", "", 0,
                self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Transaction (Intercompany To)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.allcoy), ("cti_inco", "=",
                self.opts["conum"])], limit=1)[0]
            val = float(ASD(0) - ASD(amt) - ASD(vat))
            data = (self.allcoy, acc, self.curdt, self.trndat, self.glt,
                self.trnref, self.bh.batno, val, 0.00, self.alldet, "N",
                "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        if vat:
            # General Ledger Control Transaction (V.A.T.)
            data = (self.allcoy, self.convat, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, vat, 0.00, self.alldet,
                "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        self.vat = float(ASD(self.vat) + ASD(vat))

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def doCrsTrn(self):
        # Creditors Master File
        if self.popv:
            self.sql.updRec("crsmst", cols=["crm_vatno"], data=["Unknown"],
                where=[("crm_cono", "=", self.opts["conum"]),
                ("crm_acno", "=", self.cracno)])
        # Creditors Ledger Transaction
        paydt = paymentDate(self.base, self.stdt, self.term, self.trndat)
        data = [self.opts["conum"], self.cracno, self.opts["rtn"],
            self.trnref, self.bh.batno, self.trndat, "", self.amt, self.vat,
            self.per, self.curdt, paydt, "Y", self.amt, self.trndet,
            self.vatcode, "N", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("crstrn", data=data)
        if not self.dis:
            return
        data = [self.opts["conum"], self.cracno, 6, self.trnref,
            self.bh.batno, self.trndat, "", self.dis, self.vat,
            0, self.curdt, paydt, "Y", self.dis, self.trndet,
            self.vatcode, "N", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("crstrn", data=data)

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

    def queryCrs(self):
        callModule(self.opts["mf"], self.df, "cr4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def maintainCrs(self):
        callModule(self.opts["mf"], self.df, "cr1010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def doLonAcc(self, frt, pag, r, c, p, i, w):
        newacc = False
        if not w and self.opts["rtn"] == 1:
            yn = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Account?", default="no")
            if yn == "no":
                return "Invalid Account Number"
            newacc = True
            w = callModule(self.opts["mf"], self.df, "ln1010",
                coy=(self.allcoy, self.allnam), user=self.opts["capnm"],
                args="auto", ret="acno")
            self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.allcoy),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.lonacc = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if newacc:
            self.lonnum = 1
            self.newlon = True
            self.df.loadEntry(frt, pag, p+2, data=self.lonnum)
            return "sk2"

    def doLonNum(self, frt, pag, r, c, p, i, w):
        if not w and self.opts["rtn"] == 1:
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newlon = True
                self.lonnum = getNextCode(self.sql, "lonmf2", "lm2_loan",
                    where=[("lm2_cono", "=", self.allcoy),
                    ("lm2_acno", "=", self.lonacc)], start=1, last=9999999)
                self.df.loadEntry(frt, pag, p, data=self.lonnum)
            else:
                return "Invalid Loan Number"
        else:
            self.lonmf2 = self.sql.getRec("lonmf2", where=[("lm2_cono",
                "=", self.allcoy), ("lm2_acno", "=", self.lonacc),
                ("lm2_loan", "=", w)], limit=1)
            if not self.lonmf2:
                return "Invalid Loan Number"
            self.lonnum = w
            self.newlon = False
            self.londes = self.lonmf2[self.sql.lonmf2_col.index("lm2_desc")]
            self.londat = self.lonmf2[self.sql.lonmf2_col.index("lm2_start")]
            self.lonmth = self.lonmf2[self.sql.lonmf2_col.index("lm2_pmths")]
            self.lonpay = self.lonmf2[self.sql.lonmf2_col.index("lm2_repay")]
            if self.lonmth:
                return "Invalid Entry, Fixed Loan"
            self.df.loadEntry(frt, pag, p+1, data=self.londes)
            return "sk1"

    def doLonDes(self, frt, pag, r, c, p, i, w):
        self.londes = w

    def doLonAmt(self, frt, pag, r, c, p, i, w):
        self.lonamt = w
        if not self.lonamt:
            self.lonamt = self.othtot
        self.df.loadEntry(frt, pag, p, data=self.lonamt)
        if not self.newlon:
            self.newdri = 0
            return "nd"

    def doLonDri(self, frt, pag, r, c, p, i, w):
        self.newdri = w

    def doLonCri(self, frt, pag, r, c, p, i, w):
        self.newcri = w

    def doLonMth(self, frt, pag, r, c, p, i, w):
        self.lonmth = w
        if self.lonmth:
            rte = (self.newdri / 1200.0)
            self.lonpay = round(((self.lonamt * rte) * ((1 + rte) ** w)) /
                (((1 + rte) ** w) - 1), 2)
        else:
            self.lonpay = 0
        self.df.loadEntry(frt, pag, p+1, data=self.lonpay)

    def endLon(self):
        if self.opts["rtn"] == 4:
            tramt = float(ASD(0.0) - ASD(self.lonamt))
        else:
            tramt = self.lonamt
        self.othtot = float(ASD(self.othtot) - ASD(self.lonamt))
        if self.newlon:
            # Loans Rate
            self.sql.insRec("lonrte", data=[self.allcoy, self.lonacc,
                self.lonnum, self.trndat, self.newdri, self.newcri])
            # Loans Ledger Masterfile
            self.sql.insRec("lonmf2", data=[self.allcoy, self.lonacc,
                self.lonnum, self.londes, self.trndat, self.lonmth,
                self.lonpay, 0])
            self.othrtn = 2
        else:
            self.othrtn = 3
        # Loans Ledger Transaction
        data = [self.allcoy, self.lonacc, self.lonnum, self.bh.batno,
            self.othrtn, self.trndat, self.trnref, tramt, self.curdt,
            self.alldet, "", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("lontrn", data=data)
        if self.othtot:
            self.df.loadEntry("T", self.lonpag, 0, data=self.othtot)
            self.df.advanceLine(self.lonpag)
        else:
            self.othvar.set(False)

    def exitLon(self):
        self.df.focusField("C", self.lonpag, self.df.col)

    def doEmpNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
            where=[("wgm_cono", "=", self.allcoy), ("wgm_empno", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.empnum = w
        empnam = "%s, %s" % (acc[0], acc[1].split()[0])
        self.df.loadEntry(frt, pag, p+1, data=empnam)

    def doSlnNum(self, frt, pag, r, c, p, i, w):
        if not w and self.opts["rtn"] == 1:
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newsln = True
                self.slnnum = getNextCode(self.sql, "waglmf", "wlm_loan",
                    where=[("wlm_cono", "=", self.allcoy), ("wlm_empno",
                    "=", self.empnum)], start=1, last=9999999)
                self.df.loadEntry(frt, pag, p, data=self.slnnum)
            else:
                return "Invalid Loan Number"
        else:
            acc = self.sql.getRec("waglmf", where=[("wlm_cono",
                "=", self.allcoy), ("wlm_empno", "=", self.empnum),
                ("wlm_loan", "=", w)], limit=1)
            if not acc:
                return "Invalid Loan Number"
            self.slnnum = w
            self.newsln = False
            self.slndes = acc[self.sql.waglmf_col.index("wlm_desc")]
            self.slncod = acc[self.sql.waglmf_col.index("wlm_code")]
            self.slnrte = acc[self.sql.waglmf_col.index("wlm_rate")]
            self.slndat = acc[self.sql.waglmf_col.index("wlm_start")]
            self.slnded = acc[self.sql.waglmf_col.index("wlm_repay")]
            self.df.loadEntry(frt, pag, p+1, data=self.slndes)
            return "sk1"

    def doSlnDes(self, frt, pag, r, c, p, i, w):
        self.slndes = w

    def doSlnAmt(self, frt, pag, r, c, p, i, w):
        self.slnamt = w
        if not self.slnamt:
            self.slnamt = self.othtot
        self.df.loadEntry(frt, pag, p, data=self.slnamt)
        if not self.newsln:
            self.df.loadEntry(frt, pag, p+1, data=self.slncod)

    def doSlnCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.allcoy), ("ced_type",
            "=", "D"), ("ced_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.slncod = w
        if not self.newsln:
            self.newrte = 0
            self.slnded = 0
            return "nd"

    def doSlnInt(self, frt, pag, r, c, p, i, w):
        self.newrte = w
        if not self.newsln:
            self.df.loadEntry(frt, pag, p+2, data=self.slnded)

    def doSlnDed(self, frt, pag, r, c, p, i, w):
        self.slnded = w

    def endSln(self):
        if self.opts["rtn"] == 4:
            tramt = float(ASD(0.0) - ASD(self.slnamt))
        else:
            tramt = self.slnamt
        self.othtot = float(ASD(self.othtot) - ASD(self.slnamt))
        if self.newsln:
            # Staff Loans Ledger Masterfile
            self.sql.insRec("waglmf", data=[self.allcoy, self.empnum,
                self.slnnum, self.slndes, self.slncod, self.newrte,
                self.trndat, self.slnded])
            self.othrtn = 2
        else:
            self.othrtn = 3
        # Staff Loans Ledger Transaction
        data = [self.allcoy, self.empnum, self.slnnum, self.bh.batno,
            self.othrtn, self.trndat, self.trnref, tramt, tramt, self.slnded,
            self.newrte, self.curdt, self.alldet, "", self.opts["capnm"],
            self.sysdtw, 0]
        self.sql.insRec("wagltf", data=data)
        if self.othtot:
            self.df.loadEntry("T", self.slnpag, 0, data=self.othtot)
            self.df.advanceLine(self.slnpag)
        else:
            self.othvar.set(False)

    def exitSln(self):
        self.df.focusField("C", self.slnpag, self.df.col)

# vim:set ts=4 sw=4 sts=4 expandtab:
