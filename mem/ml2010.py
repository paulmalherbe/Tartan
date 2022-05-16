"""
SYNOPSIS
    Members Ledger Data Capture (Invoices, Payments and Journals).

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
from tartanFunctions import askQuestion, chkGenAcc, getVatRate, mthendDate
from tartanFunctions import showError

class ml2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Valid Posting Routine
        if self.opts["rtn"] not in (1, 2, 3, 4):
            showError(self.opts["mf"].body, "Control Error",
                "Invalid Routine %s, Only 1-4 Are Allowed" % \
                str(self.opts["rtn"]))
            return
        tabs = ["ctlvmf", "ctlvrf", "ctlvtf", "memmst", "memtrn"]
        self.gc = GetCtl(self.opts["mf"])
        memctl = self.gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.glint = memctl["mcm_glint"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["mem_ctl", "vat_ctl", "dis_all"]
            if self.gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.memctl = ctlctl["mem_ctl"]
            self.dis_all = ctlctl["dis_all"]
            tabs.extend(["gentrn", "genmst"])
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "MEM", self.opts["rtn"],
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if self.opts["rtn"] == 1:
            self.glt = 1
        elif self.opts["rtn"] == 2:
            self.glt = 2
        elif self.opts["rtn"] == 3:
            self.glt = 4
        elif self.opts["rtn"] == 4:
            self.glt = 1
        self.agevar = tk.BooleanVar()
        self.agevar.set(False)
        return True

    def drawDialog(self):
        mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": (
                ("mlm_memno", "", 0, "Mem-No"),
                ("mlm_oldno", "", 0, "Old-No"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")),
            "where": [("mlm_cono", "=", self.opts["conum"])],
            "order": "mlm_surname, mlm_names",
            "sort": False}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"IUI",6,"Mem-No","Member Number",
                "r","N",self.doMemAcc,mlm,None,("notzero",)),
            [("C",1,0,1),"ONA",10,"Name"],
            (("C",1,0,2),"INa",9,"Reference","Reference Number One",
                "i","N",self.doRefno,None,None,("notblank",)),
            (("C",1,0,3),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,4),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,("efld",))]
        if self.opts["rtn"] == 2:
            fld[3][2] = 20
            fld.extend([
                (("C",1,0,5),"ISD",13.2,"Discount",
                    "Discount Amount","","N",self.doDisAmt,None,None,None,None,
                    "Discount Amount to be Added to the Transaction Amount."),
                (("C",1,0,6),"OSD",13.2,"Total-Amount"),
                (("C",1,0,7),"INA",(20,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None)])
        elif self.glint == "Y":
            fld[3][2] = 24
            fld.extend([
                (("C",1,0,5),"INA",30,"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None),
                (("T",2,0,0),"OSD",13.2,"Unallocated Balance"),
                (("C",2,0,0),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,1),"ONA",19,"Description"),
                (("C",2,0,2),"IUA",1,"V","V.A.T Code",
                    self.taxdf,"N",self.doVatCode2,vtm,None,("notblank",)),
                (("C",2,0,3),"ISD",13.2,"All-Amt","Allocation Amount",
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,4),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doAllVat,None,None,None),
                (("C",2,0,5),"INA",(26,30),"Details","",
                    "","N",self.doAllDet,None,None,("notblank",))])
        else:
            fld[3][2] = 22
            fld.extend([
                (("C",1,0,6),"IUA",1,"V","V.A.T Code",
                    self.taxdf,"N",self.doVatCode1,vtm,None,("notblank",)),
                (("C",1,0,7),"ISD",13.2,"V.A.T","V.A.T Amount",
                    "","N",self.doVatAmt,None,None,None),
                (("C",1,0,8),"INA",(20,30),"Details","Transaction Details",
                    "","N",self.doTrnDet,None,None,None)])
        but = (
            ("Age _Normal",None,self.doAgeNormal,0,None,None,
                "Only Show Unallocated Transactions",1),
            ("Age _History",None,self.doAgeHistory,0,None,None,
                "Show All Transactions Including Already Allocated",1),
            ("Age _Automatic",None,self.doAgeAuto,0,None,None,
                "Automatically Allocate the Amount Starting With the "\
                "Oldest Unallocated One",1),
            ("Age _Current",None,self.doAgeCurrent,0,None,None,
                "Leave the Transaction Unallocated",1),
            ("Cancel",None,self.doCancel,0,("C",2,1),("C",1,1),"",1))
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] != 2 and self.glint == "Y":
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doMemAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("memmst", cols=["mlm_title",
            "mlm_initial", "mlm_surname"], where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not acc:
            return "Invalid Member Number"
        self.memno = w
        self.name = "%s, %s %s" % (acc[2], acc[0], acc[1])
        self.df.loadEntry("C", pag, p+1, data=self.name)

    def doRefno(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("memtrn", cols=["mlt_batch"],
            where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_memno", "=",
            self.memno), ("mlt_type", "=", self.opts["rtn"]), ("mlt_refno",
            "=", w)], limit=1)
        if acc:
            return "Transaction Already Exists"
        self.refno = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if w > mthendDate(self.bh.curdt * 100):
            return "Invalid Date, After Batch Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if self.glint == "Y" or self.opts["rtn"] == 2:
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
        if self.opts["rtn"] != 2 and self.glint == "Y":
            self.df.colf[2][5][5] = w
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
                if self.opts["rtn"] == 2 or self.glint == "N":
                    self.doMemTrn()
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
        elif self.opts["rtn"] == 2:                        # Payment
            if self.trnamt == 0:
                recon = self.curdt
            else:
                recon = 0
            self.vat = 0.00
            self.dis = self.disamt
        elif self.opts["rtn"] == 3:                        # Journal
            recon = 0
            self.dis = 0.00
        elif self.opts["rtn"] == 4:                        # Credit Note
            recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.dis = 0.00
        if self.opts["rtn"] == 1:
            self.ageloop = False
            self.doAgeCurrent()
        else:
            state = self.df.disableButtonsTags()
            self.opts["mf"].updateStatus("Choose an Ageing Option")
            for x in range(0, 4):
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, "normal")
            self.df.setWidget(self.df.B0, "focus")
            self.agevar.set(True)
            self.df.mstFrame.wait_variable(self.agevar)
            self.df.enableButtonsTags(state=state)
            if self.agecan:
                self.doCancel()
                return
        if self.glint == "N":
            return
        # General Ledger Control Transaction (Members)
        val = float(ASD(self.amt) + ASD(self.dis))
        data = (self.opts["conum"], self.memctl, self.curdt, self.trndat,
            self.glt, self.refno, self.bh.batno, val, 0.00, self.trndet,
            "N", "", recon, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Control Transaction (Bank)
        if self.opts["rtn"] == 2:
            val = float(ASD(0) - ASD(self.amt))
            data = (self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.refno, self.bh.batno, val, 0.00,
                self.trndet, "N", "", recon, self.opts["capnm"], self.sysdtw,
                0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Control Transaction (Discount)
            if self.dis:
                val = float(ASD(0) - ASD(self.dis))
                data = (self.opts["conum"], self.dis_all, self.curdt,
                    self.trndat, self.glt, self.refno, self.bh.batno, val,
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
        for x in range(0, 4):
            wid = getattr(self.df, "B%s" % x)
            self.df.setWidget(wid, "disabled")
        self.opts["mf"].updateStatus("Select Transaction to Allocate Against")
        age = AgeAll(self.opts["mf"], system="mem", agetyp=atype,
            agekey=[self.opts["conum"], self.memno, self.opts["rtn"],
            self.refno, self.curdt, self.amt, self.dis])
        self.agecan = age.cancel
        if self.agevar.get():
            self.agevar.set(False)

    def exitPage1(self):
        self.df.closeProcess()
        self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        if not chk[2]:
            self.taxgl = self.taxdf
        else:
            self.taxgl = chk[2]
        self.genacc = w
        self.df.loadEntry("C", pag, p+1, data=chk[0])
        self.df.loadEntry("C", pag, p+2, data=self.taxgl)

    def doVatCode2(self, frt, pag, r, c, p, i, w):
        ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"], error=False)
        if not ctlctl:
            return "Missing ctlctl Record for Company"
        if self.gc.chkRec(self.opts["conum"], ctlctl, ["vat_ctl"]):
            return "Missing or Invalid Control Record"
        self.convat = ctlctl["vat_ctl"]
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if self.vatrte is None:
            return "Invalid V.A.T Code"
        self.vatcode = w

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if w == 0:
            allamt = float(ASD(self.trnamt) - ASD(self.allocated))
            self.allamt = round((allamt * 100 / (100 + self.vatrte)), 2)
            self.df.loadEntry(frt, pag, p, data=self.allamt)
            self.allvat = float(ASD(allamt) - ASD(self.allamt))
        else:
            self.allamt = w
            self.allvat = round((self.allamt * self.vatrte / 100), 2)
        self.df.loadEntry(frt, pag, p+1, data=self.allvat)
        if not self.allvat:
            self.df.loadEntry(frt, pag, p+2, data=self.name)
            return "sk1"

    def doAllVat(self, frt, pag, r, c, p, i, w):
        if self.allamt < 0 and w > 0:
            self.allvat = float(ASD(0) - ASD(w))
        elif self.allamt > 0 and w < 0:
            self.allvat = float(ASD(0) - ASD(w))
        else:
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
            if self.glint == "Y":
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
            self.doMemTrn()
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
        elif self.opts["rtn"] == 3:                        # Journal Entry
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
        data = (self.opts["conum"], self.vatcode, "O", self.curdt, "M",
            self.glt, self.bh.batno, self.refno, self.trndat, self.memno,
            self.alldet, amt, vat, 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        # General Ledger Transaction (Expense)
        data = (self.opts["conum"], self.genacc, self.curdt, self.trndat,
            self.glt, self.refno, self.bh.batno, amt, vat, self.alldet,
            self.vatcode, "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if vat:
            # General Ledger Control Transaction (V.A.T.)
            data = (self.opts["conum"], self.convat, self.curdt, self.trndat,
                self.glt, self.refno, self.bh.batno, vat, 0.00, self.alldet,
                "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        vat = float(ASD(0) - ASD(vat))
        self.vat += vat

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def doMemTrn(self):
        # Members Ledger Transaction
        data = [self.opts["conum"], self.memno, self.opts["rtn"], self.refno,
            self.bh.batno, self.trndat, self.amt, self.vat, self.curdt, "", 0,
            self.trndet, self.vatcode, "N", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("memtrn", data=data)
        if self.dis:
            data = [self.opts["conum"], self.memno, 6, self.refno,
                self.bh.batno, self.trndat, self.dis, self.vat, self.curdt, "",
                0, self.trndet, self.vatcode, "N", self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("memtrn", data=data, unique="mlt_refno")

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty -= 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.trnamt))
        else:
            self.batupd = True
            self.bh.batqty += 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.trnamt))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

# vim:set ts=4 sw=4 sts=4 expandtab:
