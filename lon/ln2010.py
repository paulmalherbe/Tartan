"""
SYNOPSIS
    Loans's Ledger Data Capture.

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
from TartanClasses import ASD, Batches, GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, chkGenAcc, getNextCode
from tartanFunctions import showError

class ln2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "lonmf1", "lonmf2",
            "lonrte", "lontrn", "genint", "genmst", "gentrn"],
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
        self.gc = GetCtl(self.opts["mf"])
        lonctl = self.gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.glint = lonctl["cln_glint"]
        self.drte = lonctl["cln_drte"]
        self.crte = lonctl["cln_crte"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["lon_ctl", "int_rec", "int_pay"]
            if self.gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.lonctl = ctlctl["lon_ctl"]
            self.intrec = ctlctl["int_rec"]
            self.intpay = ctlctl["int_pay"]
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
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "LON",
            self.opts["rtn"], glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        if self.opts["rtn"] == 4:
            self.bh.batval = float(ASD(0) - ASD(self.bh.batval))

    def drawDialog(self):
        lm1 = {
            "stype": "R",
            "tables": ("lonmf1",),
            "cols": (
                ("lm1_acno", "", 0, "Acc-Num"),
                ("lm1_name", "", 0, "Name", "Y")),
            "where": [("lm1_cono", "=", self.opts["conum"])]}
        lm2 = {
            "stype": "R",
            "tables": ("lonmf2",),
            "cols": (
                ("lm2_loan", "", 0, "Ln"),
                ("lm2_desc", "", 0, "Description", "Y")),
            "where": [("lm2_cono", "=", self.opts["conum"])],
            "whera": [("C", "lm2_acno", 0)]}
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
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"INA",7,"Acc-Num","Account Code",
                "","Y",self.doLonAcc,lm1,None,("efld",)),
            (("C",1,0,1),"ONA",10,"Name"),
            (("C",1,0,2),"IUI",2,"LN","Loan Number",
                "","N",self.doLonNum,lm2,None,("efld",)),
            (("C",1,0,3),"ITX",(12,30),"Description","",
                "","N",self.doLonDes,None,None,("notblank",)),
            (("C",1,0,4),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,5),"INa",9,"Reference","Reference Number One",
                "i","N",self.doTrnRef,None,None,("notblank",)),
            (("C",1,0,6),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,("notzero",)),
            (("C",1,0,7),"IUD",6.2,"DRte-%","Debit Rate",
                self.drte,"N",self.doLonDrt,None,None,None),
            (("C",1,0,8),"IUD",6.2,"CRte-%","Credit Rate",
                self.crte,"N",self.doLonCrt,None,None,None),
            (("C",1,0,9),"IUI",3,"Mth","Period in Months",
                "","N",self.doLonMth,None,None,("efld",)),
            (("C",1,0,10),"OUD",12.2,"Repay-Amt"),
            (("C",1,0,11),"INA",30,"Details","Loan Details",
                "","N",self.doTrnDet,None,None,None)]
        if self.opts["rtn"] == 3 and self.glint == "Y":
            fld.extend([
                (("T",2,0,0),"OSD",13.2,"Unallocated Balance"),
                [("C",2,0,0),"IUI",3,"Coy","Company Number",
                    self.opts["conum"],"N",self.doCoyNum,coy,None,None],
                (("C",2,0,1),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,2),"ONA",19,"Description"),
                (("C",2,0,4),"ISD",13.2,"All-Amount","Allocation Amount",
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,6),"INA",30,"Allocation Details","",
                    "","N",self.doAllDet,None,None,("notblank",))])
            if not self.incoac:
                fld[15][1] = "OUI"
        but = [("Interrogate",None,self.querySln,0,("C",1,1),("C",1,2))]
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] == 3 and self.glint == "Y":
            but.append(("Cancel",None,self.doCancel,0,("C",2,1),("C",1,1)))
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doLonAcc(self, frt, pag, r, c, p, i, w):
        newacc = False
        if not w and self.opts["rtn"] in (1, 2, 3):
            yn = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Account?", default="no")
            if yn == "no":
                return "Invalid Account Number"
            newacc = True
            w = callModule(self.opts["mf"], self.df, "ln1010",
                coy=(self.opts["conum"], self.opts["conam"]),
                user=self.opts["capnm"], args="auto", ret="acno")
            self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.allcoy),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.lonacc = w
        self.name = acc[0]
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        if newacc:
            self.lonnum = 1
            self.newlon = True
            self.df.loadEntry(frt, pag, p+2, data=self.lonnum)
            return "sk2"

    def doLonNum(self, frt, pag, r, c, p, i, w):
        self.newlon = False
        if not w and self.opts["rtn"] in (1, 2, 3):
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newlon = True
                self.lonnum = getNextCode(self.sql, "lonmf2", "lm2_loan",
                    where=[("lm2_cono", "=", self.allcoy), ("lm2_acno",
                    "=", self.lonacc)], start=1, last=9999999)
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
            self.londes = self.lonmf2[self.sql.lonmf2_col.index("lm2_desc")]
            self.londat = self.lonmf2[self.sql.lonmf2_col.index("lm2_start")]
            self.lonmth = self.lonmf2[self.sql.lonmf2_col.index("lm2_pmths")]
            self.lonpay = self.lonmf2[self.sql.lonmf2_col.index("lm2_repay")]
            if self.opts["rtn"] in (1, 3) and self.lonmth:
                showError(self.opts["mf"].body, "Fixed Loan",
                    """This is a Fixed Period Loan.

Please Create a New Loan for this Account.""")
                return "Invalid Loan Number"
            self.df.loadEntry(frt, pag, p+1, data=self.londes)
            return "sk1"

    def doLonDes(self, frt, pag, r, c, p, i, w):
        self.londes = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        self.refno = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if not self.newlon:
            self.londrt = 0
            self.loncrt = 0
            self.lonmth = 0
            self.lonpay = 0
            if self.opts["rtn"] in (1, 2):
                return "nd"
            else:
                return "sk4"

    def doLonDrt(self, frt, pag, r, c, p, i, w):
        self.londrt = w

    def doLonCrt(self, frt, pag, r, c, p, i, w):
        self.loncrt = w

    def doLonMth(self, frt, pag, r, c, p, i, w):
        self.lonmth = w
        if self.lonmth:
            rte = (self.londrt / 1200.0)
            self.lonpay = round(((self.trnamt * rte) * ((1 + rte) ** w)) /
                (((1 + rte) ** w) - 1), 2)
        else:
            self.lonpay = 0
        self.df.loadEntry(frt, pag, p+1, data=self.lonpay)

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        if self.glint == "Y" and self.opts["rtn"] == 3:
            self.df.colf[2][4][5] = w

    def endPage1(self):
        self.batupd = False
        self.updateTables1()
        self.updateBatch()
        if not self.val:
            self.df.advanceLine(1)
        elif self.opts["rtn"] in (1, 2, 4) or self.glint == "N":
            self.opts["mf"].dbm.commitDbase()
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
        else:
            self.allocated = float(0.0)
            self.df.loadEntry("T", 2, 0, data=self.val)
            self.df.selPage("Allocation")
            self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        if self.opts["rtn"] == 1:
            self.glt = 2
            desc = "Loan Advance"
            self.val = self.trnamt
        elif self.opts["rtn"] == 2:
            self.glt = 6
            desc = "Loan Repayment"
            self.val = float(ASD(0) - ASD(self.trnamt))
        elif self.opts["rtn"] == 3:
            self.glt = 4
            desc = self.trndet
            self.val = self.trnamt
        elif self.opts["rtn"] == 4:
            self.glt = 4
            desc = self.trndet
            self.val = self.trnamt
        if self.newlon:
            # Loans Masterfile
            self.sql.insRec("lonmf2", data=[self.opts["conum"], self.lonacc,
                self.lonnum, self.londes, self.trndat, self.lonmth,
                self.lonpay, 0])
            # Loans Rate File
            self.sql.insRec("lonrte", data=[self.opts["conum"], self.lonacc,
                self.lonnum, self.trndat, self.londrt, self.loncrt])
        # Loans Transaction File
        self.sql.insRec("lontrn", data=[self.opts["conum"], self.lonacc,
            self.lonnum, self.bh.batno, self.opts["rtn"], self.trndat,
            self.refno, self.val, self.curdt, desc, "N", self.opts["capnm"],
            self.sysdtw, 0])
        if self.glint == "N":
            return
        # General Ledger Loans Control Account
        data = (self.opts["conum"], self.lonctl, self.curdt, self.trndat,
            self.glt, self.refno, self.bh.batno, self.val, 0.00, self.name,
            "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if self.opts["rtn"] in (1, 2, 4):
            # General Ledger Bank or Interest
            self.val = float(ASD(0) - ASD(self.val))
            if self.opts["rtn"] in (1, 2):
                ctl = self.bh.acc
            elif self.val < 0:
                ctl = self.intrec
            else:
                ctl = self.intpay
            data = (self.opts["conum"], ctl, self.curdt, self.trndat, self.glt,
                self.refno, self.bh.batno, self.val, 0.00, "Loan - %s" %
                self.name, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
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
            acc = self.sql.getRec("genint", where=[("cti_cono", "=",
                w), ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        self.allcoy = w

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.allcoy, w)
        if type(chk) is str:
            return chk
        self.genacc = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

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
        val = float(ASD(0) - ASD(self.allamt))
        # General Ledger Transaction (Allocation)
        data = (self.allcoy, self.genacc, self.curdt, self.trndat,
            self.glt, self.refno, self.bh.batno, val, 0.00,
            self.alldet, "", "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        # General Ledger Transaction (Intercompany)
        if self.allcoy != self.opts["conum"]:
            # General Ledger Transaction (Intercompany From)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.opts["conum"]),
                ("cti_inco", "=", self.allcoy)], limit=1)[0]
            data = (self.opts["conum"], acc, self.curdt, self.trndat,
                self.glt, self.refno, self.bh.batno, val, 0.00,
                self.alldet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            # General Ledger Transaction (Intercompany To)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.allcoy), ("cti_inco", "=",
                self.opts["conum"])], limit=1)[0]
            val = float(ASD(0) - ASD(val))
            data = (self.allcoy, acc, self.curdt, self.trndat, self.glt,
                self.refno, self.bh.batno, val, 0.00, self.alldet, "N",
                "", 0, self.opts["capnm"], self.sysdtw, 0)
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
        callModule(self.opts["mf"], self.df, "ln4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
