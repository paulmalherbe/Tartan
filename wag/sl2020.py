"""
SYNOPSIS
    Salaries Staff Loans Data Capture.

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
from TartanClasses import ASD, Batches, GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, chkGenAcc

class sl2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "gentrn", "wagmst",
            "waglmf", "wagltf"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.col = self.sql.waglmf_col
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.glint = wagctl["ctw_glint"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["wag_slc", "wag_sli"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.glctls = (ctlctl["wag_slc"], ctlctl["wag_sli"])
        else:
            self.glctls = None
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "SLN", 5,
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return

    def dataHeader(self):
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname", "Y"),
                ("wgm_fname", "", 0, "Names")),
            "where": [("wgm_cono", "=", self.opts["conum"])]}
        lnm = {
            "stype": "R",
            "tables": ("waglmf",),
            "cols": (
                ("wlm_loan", "", 0, "Ln"),
                ("wlm_desc", "", 0, "Description", "Y")),
            "where": [("wlm_cono", "=", self.opts["conum"])],
            "whera": (("C", "wlm_empno", 0),),
            "index": 0}
        typ = {
            "stype": "C",
            "titl": "Transaction Types",
            "head": ("C", "Description"),
            "data": (
                (1, "Interest Adjustment"),
                (3, "Further Advance"),
                (4, "Loan Repayment"),
                (5, "Loan Adjustment")),
            "index": 0}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"IUI",5,"EmpNo","Employee Number",
                "","N",self.doEmp,wgm,None,None),
            (("C",1,0,1),"ONA",10,"Name"),
            (("C",1,0,2),"IUI",2,"Ln","Loan Number",
                "","N",self.doLoan,lnm,None,("notzero",)),
            (("C",1,0,3),"ONA",10,"Descript","Description",
                "","N",None,None,None,None),
            (("C",1,0,4),"ID1",10,"Trans-Date","Transaction Date",
                self.sysdtw,"N",self.doTrdate,None,None,None),
            (("C",1,0,5),"IUI",1,"T","Transaction Type",
                "","N",self.doTyp,typ,None,("in",(1,3,4,5))),
            (("C",1,0,6),"INa",9,"Reference","Reference Number",
                "i","N",self.doRef,None,None,("notblank",)),
            (("C",1,0,7),"IUD",6.2,"Intr-%","New Interest Rate",
                "","N",self.doPer,None,None,None),
            (("C",1,0,8),"ISD",13.2,"Interest",
                "Interest (Adds to interest raised)",
                "","Y",self.doInt,None,None,("notzero",)),
            (("C",1,0,9),"ISD",13.2,"Amount",
                "Amount (Adds to advances or payments)",
                "","Y",self.doPay,None,None,("notzero",)),
            (("C",1,0,10),"IUD",9.2,"Deduct",
                "Deduction Amount (New total deduction)",
                "","Y",self.doDed,None,None,("efld",))]
        if self.glint == "Y":
            fld.extend([
                [("T",2,0,0),"OSD",13.2,"Unallocated Balance"],
                (("C",2,0,0),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,1),"ONA",30,"Description"),
                (("C",2,0,2),"ISD",13.2,"All-Amt","Allocation Amount",
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,3),"INA",30,"Details","",
                    "","N",self.doAllDet,None,None,("notblank",))])
        but = [("Interrogate",None,self.querySln,0,("C",1,1),("C",1,2))]
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.glint == "Y":
            but.append(("Cancel",None,self.doCancel,0,("C",2,1),("C",1,1)))
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag,
            cend=cnd, cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doEmp(self, frt, pag, r, c, p, i, w):
        self.empno = w
        acc = self.sql.getRec("wagmst", cols=["wgm_sname"],
            where=[("wgm_cono", "=", self.opts["conum"]), ("wgm_empno", "=",
            self.empno)], limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.name = acc[0]
        self.df.loadEntry("C", pag, p+1, data=self.name)
        chk = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
            self.opts["conum"]), ("wlm_empno", "=", self.empno)])
        if len(chk) == 1:
            self.acc = chk[0]
            self.loan = self.acc[self.col.index("wlm_loan")]
            desc = self.acc[self.col.index("wlm_desc")]
            self.df.loadEntry("C", pag, p+2, data=self.loan)
            self.df.loadEntry("C", pag, p+3, data=desc)
            return "sk3"

    def doLoan(self, frt, pag, r, c, p, i, w):
        self.loan = w
        self.acc = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
            self.opts["conum"]), ("wlm_empno", "=", self.empno), ("wlm_loan",
            "=", self.loan)], limit=1)
        if not self.acc:
            return "Invalid Loan Number"
        desc = self.acc[self.col.index("wlm_desc")]
        self.df.loadEntry("C", pag, p+1, data=desc)

    def doTrdate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trdate = w

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w

    def doRef(self, frt, pag, r, c, p, i, w):
        self.ref = w
        per = self.acc[self.col.index("wlm_rate")]
        self.df.loadEntry("C", pag, p+1, data=per)

    def doPer(self, frt, pag, r, c, p, i, w):
        self.per = w
        if self.typ in (3, 4, 5):
            self.intp = 0
            return "sk1"

    def doInt(self, frt, pag, r, c, p, i, w):
        self.intp = w
        self.pay = 0
        self.ded = 0
        return "sk2"

    def doPay(self, frt, pag, r, c, p, i, w):
        self.pay = w
        amt = self.acc[self.col.index("wlm_repay")]
        self.df.loadEntry("C", pag, p+1, data=amt)

    def doDed(self, frt, pag, r, c, p, i, w):
        self.ded = w

    def endPage1(self):
        self.batupd = False
        self.updateTables1()
        self.updateBatch()
        if not self.val:
            self.df.advanceLine(1)
        elif self.typ == 1 or self.glint == "N":
            self.opts["mf"].dbm.commitDbase()
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
        else:
            self.allocated = float(0.0)
            self.df.selPage("Allocation")
            self.df.loadEntry("T", 2, 0, data=self.val)
            self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trdate / 100)
        else:
            self.curdt = self.bh.curdt
        if self.typ == 1:
            self.glt = 4
            desc = "Interest Adj"
            self.val = self.intp
            ded = self.acc[self.col.index("wlm_repay")]
            cap = 0.00
        elif self.typ == 3:
            self.glt = 2
            desc = "Advance"
            self.val = self.pay
            ded = self.ded
            cap = self.val
        elif self.typ == 4:
            self.glt = 6
            desc = "Repayment"
            self.val = float(ASD(0) - ASD(self.pay))
            ded = self.ded
            cap = 0.00
        elif self.typ == 5:
            self.glt = 4
            desc = "Adjustment"
            self.val = self.pay
            ded = self.ded
            cap = 0.00
        self.sql.updRec("waglmf", cols=["wlm_rate", "wlm_repay"],
            data=[self.per, ded], where=[("wlm_cono", "=", self.opts["conum"]),
            ("wlm_empno", "=", self.empno), ("wlm_loan", "=", self.loan)])
        self.sql.insRec("wagltf", data=[self.opts["conum"], self.empno,
            self.loan, self.bh.batno, self.typ, self.trdate, self.ref,
            self.val, cap, ded, self.per, self.curdt, desc, "N",
            self.opts["capnm"], self.sysdtw, 0])
        if self.glint == "N":
            return
        # General Ledger Staff Loans Control Account
        data = (self.opts["conum"], self.glctls[0], self.curdt, self.trdate,
            self.glt, self.ref, self.bh.batno, self.val, 0.00, self.name, "N",
            "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        self.val = float(ASD(0) - ASD(self.val))
        if self.typ == 1:
            # General Ledger Interest Received
            data = (self.opts["conum"], self.glctls[1], self.curdt,
                self.trdate, self.glt, self.ref, self.bh.batno, self.val, 0.00,
                "Staff Loan - %s" % self.name, "N", "", 0, self.opts["capnm"],
                self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)

    def exitPage1(self):
        self.df.closeProcess()
        self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        self.genacc = w
        self.df.loadEntry("C", pag, p+1, data=chk[0])

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if w == 0:
            self.allamt = float(ASD(self.val) - ASD(self.allocated))
            self.df.loadEntry(frt, pag, p, data=self.allamt)
        else:
            self.allamt = w

    def doAllDet(self, frt, pag, r, c, p, i, w):
        self.alldet = w

    def doCancel(self):
        ok = askQuestion(self.opts["mf"].body, head="Cancel",
            mess="Are You Certain You Want to Cancel This Entry?")
        if ok == "yes":
            self.opts["mf"].dbm.rollbackDbase()
            if self.batupd:
                self.updateBatch(rev=True)
            self.df.clearFrame("C", 2)
            self.df.selPage("Transaction")
            row = int((self.df.last[1][1] - 1) / self.df.colq[1])
            col = (row * self.df.colq[1]) + 1
            self.df.focusField("C", 1, col)

    def endPage2(self):
        self.updateTables2()
        self.allocated = float(ASD(self.allocated) + ASD(self.allamt))
        if self.allocated == self.val:
            self.opts["mf"].dbm.commitDbase()
            self.df.clearFrame("C", 2)
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
        else:
            bal = float(ASD(self.val) - ASD(self.allocated))
            self.df.loadEntry("T", 2, 0, data=bal)
            self.df.advanceLine(2)

    def updateTables2(self):
        # General Ledger Transaction (Source)
        data = (self.opts["conum"], self.genacc, self.curdt, self.trdate,
            self.glt, self.ref, self.bh.batno, self.allamt, 0.00,
            self.alldet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty = self.bh.batqty - 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.val))
        else:
            self.batupd = True
            self.bh.batqty = self.bh.batqty + 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.val))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def querySln(self):
        callModule(self.opts["mf"], self.df, "sl4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
