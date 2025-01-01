"""
SYNOPSIS
    Asset Register Data Capture Screen and Execution.

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
from tartanFunctions import askQuestion, callModule, chkGenAcc, getVatRate
from tartanFunctions import showError
from tartanWork import armvtp

class ar2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        if self.opts["rtn"] not in (1, 2, 3):
            mes = "Invalid Routine %s" % str(self.opts["rtn"])
            showError(self.opts["mf"].body, "Control Error", mes)
            return
        self.gc = GetCtl(self.opts["mf"])
        assctl = self.gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.glint = assctl["cta_glint"]
        self.rordp = assctl["cta_rordp"]
        tabs = [
            "assgrp", "assmst", "assdep", "asstrn",
            "ctlvmf", "ctlvrf", "ctlvtf",
            "genint", "genmst", "gentrn"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        if self.glint == "Y":
            # Check Sale of Asset Record
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"], ctlctl, "ass_sls"):
                return
            self.slsac = ctlctl["ass_sls"]
            # Check for VAT Control
            if self.gc.chkRec(self.opts["conum"], ctlctl, ["vat_ctl"]):
                return
            self.convat = ctlctl["vat_ctl"]
            # Check All Group Control Records
            errs = (
                "Group %s Has An Invalid",
                "Asset Control Account (%s)",
                "Accumulated Depreciation Account (%s)",
                "Depreciation Expense Account (%s)")
            ass = self.sql.getRec("assgrp", cols=["asg_group",
                "asg_assacc", "asg_depacc", "asg_expacc"],
                where=[("asg_cono", "=", self.opts["conum"])])
            for acc in ass:
                for x in range(1, 4):
                    chk = self.sql.getRec("genmst", where=[("glm_cono",
                        "=", self.opts["conum"]), ("glm_acno", "=", acc[x])],
                        limit=1)
                    if not chk:
                        mess = "%s %s" % (errs[0] % acc[0], errs[x] % acc[x])
                        showError(self.opts["mf"].body, "Control Error", mess)
                        return
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"],
            "ASS", self.opts["rtn"], glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        if self.opts["rtn"] == 2:
            self.bh.batval = float(ASD(0) - ASD(self.bh.batval))

    def drawDialog(self):
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        cod = {
            "stype": "R",
            "tables": ("assmst",),
            "cols": (
                ("asm_code", "", 0, "Cod-Num"),
                ("asm_desc", "", 0, "Description", "Y")),
            "where": [("asm_cono", "=", self.opts["conum"])],
            "whera": [["C", "asm_group", 0, 1]]}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        data = []
        for x in range(1, (len(armvtp) + 1)):
            data.append([x, armvtp[x-1][1]])
        mov = {
            "stype": "C",
            "titl": "Valid Types",
            "head": ("C", "Description"),
            "data": data}
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"IUA",3,"Grp","Asset Group",
                "r","N",self.doAssGrp,grp,None,None),
            (("C",1,0,1),"INa",7,"Cod-Num","Asset Code",
                "r","N",self.doAssCod,cod,None,("notblank",)),
            (("C",1,0,2),"ONA",13,"Description"),
            (("C",1,0,3),"INa",9,"Reference","Reference Number One",
                "i","N",self.doTrnRef,None,None,("notblank",)),
            (("C",1,0,4),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,5),"IUI",1,"M","Movement Type",
                "r","N",self.doTrnMov,mov,None,("in",(1,2,3,4,5))),
            (("C",1,0,6),"ISD",13.2,"Company","Company Amount",
                "","N",self.doCoyAmt,None,None,None),
            (("C",1,0,7),"ISD",13.2,"Receiver","Receiver Amount",
                "","N",self.doRorAmt,None,None,None),
            (("C",1,0,8),"IUA",1,"V","V.A.T Code",
                "C","N",self.doVatCod,vtm,None,("notblank",)),
            (("C",1,0,9),"ISD",13.2,"V.A.T","V.A.T Amount",
                "","N",self.doVatAmt,None,None,None),
            (("C",1,0,10),"INA",(13,30),"Details","Transaction Details",
                "","N",self.doTrnDet,None,None,None)]
        if self.opts["rtn"] not in (1, 2) and self.glint == "Y":
            fld.extend([
                [("T",2,0,0),"OSD",13.2,"Unallocated Balance"],
                (("C",2,0,0),"IUI",7,"Acc-Num","Account Number",
                    "","N",self.doGenAcc,glm,None,None),
                (("C",2,0,1),"ONA",30,"Description"),
                (("C",2,0,2),"ISD",13.2,"All-Amt","Allocation Amount",
                    "","N",self.doAllAmt,None,None,("efld",)),
                (("C",2,0,3),"INA",30,"Details","",
                    "","N",self.doAllDet,None,None,("notblank",))])
        but = (
            ("Interrogate",None,self.queryAss,0,("C",1,1),("C",1,2)),
            ("Cancel",None,self.doCancel,0,("C",2,1),("C",1,1)))
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] not in (1, 2) and self.glint == "Y":
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doAssGrp(self, frt, pag, r, c, p, i, w):
        whr = [("asg_cono", "=", self.opts["conum"]), ("asg_group", "=", w)]
        acc = self.sql.getRec("assgrp", where=whr, limit=1)
        if not acc:
            return "Invalid Asset Group"
        self.group = w
        self.depcod = acc[self.sql.assgrp_col.index("asg_depcod")]
        self.assacc = acc[self.sql.assgrp_col.index("asg_assacc")]
        self.depacc = acc[self.sql.assgrp_col.index("asg_depacc")]
        self.expacc = acc[self.sql.assgrp_col.index("asg_expacc")]

    def doAssCod(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.buydt = 0
        self.seldt = 0
        col = ["asm_desc", "asm_depcod"]
        whr = [
            ("asm_cono", "=", self.opts["conum"]),
            ("asm_group", "=", self.group),
            ("asm_code", "=", self.code)]
        acc = self.sql.getRec("assmst", cols=col, where=whr, limit=1)
        if not acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="New Asset",
                mess="Asset does not exist, Create?")
            if ok == "no":
                return "Invalid Asset"
            self.doNewAsset()
            acc = self.sql.getRec("assmst", cols=col, where=whr, limit=1)
            if not acc:
                return "Asset Not Found"
            self.new = "y"
        else:
            self.new = "n"
        dep = self.sql.getRec("assdep", cols=["asd_rate1r"],
            where=[("asd_cono", "=", self.opts["conum"]),
            ("asd_code", "=", acc[1])], limit=1)
        self.rate1r = dep[0]
        col = ["ast_date"]
        whr = [
            ("ast_cono", "=", self.opts["conum"]),
            ("ast_group", "=", self.group),
            ("ast_code", "=", self.code),
            ("ast_mtyp", "=", 1)]
        pur = self.sql.getRec("asstrn", cols=col, where=whr, limit=1)
        if pur:
            self.buydt = pur[0]
        whr = [
            ("ast_cono", "=", self.opts["conum"]),
            ("ast_group", "=", self.group),
            ("ast_code", "=", self.code),
            ("ast_mtyp", "in", (3, 5))]
        sel = self.sql.getRec("asstrn", cols=col, where=whr, limit=1)
        if sel:
            self.seldt = sel[0]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w
        if self.new == "y":
            self.trnmov = 1
            self.df.loadEntry(frt, pag, p+1, data=self.trnmov)
            return "sk1"

    def doTrnMov(self, frt, pag, r, c, p, i, w):
        if type(w) == list:
            w = w[0] + 1
        # Do some tests to see if not new again or already sold etc.
        if w == 4 and self.opts["rtn"] != 3:
            return "Depreciation Only Allowed with Journal Entries"
        if self.opts["rtn"] == 1 and w not in (1, 2):
            return "Invalid Choice For Payment"
        if self.opts["rtn"] == 2 and w not in (5,):
            return "Invalid Choice For Receipt"
        if w == 1 and self.buydt:
            return "Asset Already Purchased"
        if w in (2, 3, 4, 5) and self.seldt:
            return "Asset Already Sold or Written Off"
        if w in (2, 3, 4, 5) and not self.buydt:
            return "Asset Not Yet Purchased"
        self.df.loadEntry(frt, pag, p, data=w)
        self.trnmov = w
        if self.trnmov == 3:
            bal = self.sql.getRec("asstrn", cols=["sum(ast_amt1)",
                "sum(ast_amt2)"], where=[("ast_cono", "=", self.opts["conum"]),
                ("ast_group", "=", self.group), ("ast_code", "=", self.code)],
                limit=1)
            self.coyamt = float(ASD(0) - ASD(bal[0]))
            self.df.loadEntry(frt, pag, p+1, data=self.coyamt)
            self.roramt = float(ASD(0) - ASD(bal[0]))
            self.df.loadEntry(frt, pag, p+2, data=self.roramt)
            self.vatcode = ""
            self.trnvat = 0
            return "sk4"

    def doCoyAmt(self, frt, pag, r, c, p, i, w):
        if self.opts["rtn"] == 3 and self.trnmov == 5 and w > 0:
            ok = askQuestion(screen=self.opts["mf"].body, head="Debit",
                mess="Should this Amount not be a Credit Entry?")
            if ok == "yes":
                w = float(ASD(0) - ASD(w))
                self.df.loadEntry(frt, pag, p, data=w)
        self.coyamt = w
        if self.rordp == "N" or not self.rate1r or self.trnmov != 4:
            self.roramt = 0
            self.df.loadEntry(frt, pag, p+1, data=self.roramt)
            if self.trnmov == 4:
                self.vatcode = ""
                self.trnvat = 0
                self.df.loadEntry(frt, pag, p+2, data=self.vatcode)
                self.df.loadEntry(frt, pag, p+3, data=self.trnvat)
                return "sk3"
            return "sk1"

    def doRorAmt(self, frt, pag, r, c, p, i, w):
        if self.opts["rtn"] == 3 and self.trnmov == 5 and w > 0:
            ok = askQuestion(screen=self.opts["mf"].body, head="Debit",
                mess="Should this Amount not be a Credit Entry?")
            if ok == "yes":
                w = float(ASD(0) - ASD(w))
                self.df.loadEntry(frt, pag, p, data=w)
        self.roramt = w
        self.vatcode = ""
        self.trnvat = 0
        self.df.loadEntry(frt, pag, p+1, data=self.vatcode)
        self.df.loadEntry(frt, pag, p+2, data=self.trnvat)
        return "sk2"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if vrte is None:
            return "Invalid V.A.T Code"
        self.vatcode = w
        self.trnvat = round((self.coyamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry(frt, pag, p+1, data=self.trnvat)
        if not self.trnvat:
            return "sk1"

    def doVatAmt(self, frt, pag, r, c, p, i, w):
        if self.coyamt < 0 and w > 0:
            self.trnvat = float(ASD(0) - ASD(w))
        elif self.coyamt > 0 and w < 0:
            self.trnvat = float(ASD(0) - ASD(w))
        else:
            self.trnvat = w
        self.df.loadEntry(frt, pag, p, data=self.trnvat)

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        if self.opts["rtn"] not in (1, 2) and self.glint == "Y":
            self.df.colf[2][3][5] = w

    def endPage1(self):
        self.batupd = False
        self.updateTables1()
        self.updateBatch()
        if self.coyamt == 0:
            self.df.advanceLine(1)
        else:
            self.allocated = float(0.0)
            if self.glint == "N" or self.opts["rtn"] in (1, 2) or \
                    self.trnmov == 4:
                self.opts["mf"].dbm.commitDbase()
                self.df.advanceLine(1)
            else:
                self.coyamt = float(ASD(0) - ASD(self.coyamt))
                self.df.loadEntry("T", 2, 0, data=self.coyamt)
                self.df.selPage("Allocation")
                self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        self.amt = self.coyamt
        self.vat = self.trnvat
        if self.trnmov == 4:
            self.net = float(ASD(0) - ASD(self.coyamt))
            self.ror = float(ASD(0) - ASD(self.roramt))
        else:
            self.net = self.ror = float(ASD(self.coyamt) - ASD(self.trnvat))
        if self.opts["rtn"] == 1:                          # Payments
            if self.coyamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            acc = self.assacc
            self.glt = 2
        elif self.opts["rtn"] == 2:                        # Receipts
            if self.coyamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.vat = float(ASD(0) - ASD(self.vat))
            self.net = float(ASD(0) - ASD(self.net))
            acc = self.assacc
            self.glt = 6
        elif self.opts["rtn"] == 3:                        # Journal Entries
            self.recon = 0
            if self.trnmov == 4:
                acc = self.depacc
            else:
                acc = self.assacc
            self.glt = 4
        # Asset Register Transaction
        data = [self.opts["conum"], self.group, self.code, self.opts["rtn"],
            self.trnref, self.bh.batno, self.trndat, self.trnmov, self.net,
            self.ror, self.vat, self.curdt, self.trndet, self.vatcode, "N",
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("asstrn", data=data)
        if self.vatcode:
            # VAT Transaction (ctlvtf)
            data = (self.opts["conum"], self.vatcode, "I", self.curdt, "A",
                self.opts["rtn"], self.bh.batno, self.trnref, self.trndat,
                self.code, self.trndet, self.amt, self.vat, 0,
                self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        # General Ledger Asset or Depreciation Account
        data = (self.opts["conum"], acc, self.curdt, self.trndat, self.glt,
            self.trnref, self.bh.batno, self.net, self.vat, self.trndet,
            self.vatcode, "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if self.vat:
            # General Ledger Control Transaction (V.A.T.)
            data = [self.opts["conum"], self.convat, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.vat, 0.00,
                self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        self.amt = float(ASD(0) - ASD(self.amt))
        if self.opts["rtn"] in (1, 2):
            # General Ledger Control Transaction (Bank)
            data = [self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.amt, 0.00,
                self.trndet, "N", "", self.recon, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        elif self.trnmov == 4:
            # General Ledger Expense Account (Depreciation)
            data = [self.opts["conum"], self.expacc, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.coyamt, self.vat,
                self.trndet, "N", "", self.recon, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        if self.trnmov == 5:
            # Sale of Asset
            # Raise Depreciation
            callModule(self.opts["mf"], None, "ar2030",
                coy=(self.opts["conum"], self.opts["conam"]),
                period=self.opts["period"], user=self.opts["capnm"],
                args=(self.curdt, self.group, self.code))
            # Generate Sale
            amt = self.sql.getRec("asstrn", cols=["sum(ast_amt1)"],
                where=[("ast_cono", "=", self.opts["conum"]), ("ast_group",
                "=", self.group), ("ast_code", "=", self.code)], limit=1)
            if amt[0]:
                data = [self.opts["conum"], self.slsac, self.curdt,
                    self.trndat, self.glt, self.trnref, self.bh.batno,
                    amt[0], 0, self.trndet, "N", "", 0, self.opts["capnm"],
                    self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                data[1] = acc
                data[7] = float(ASD(0) - ASD(amt[0]))
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
            self.allamt = float(ASD(self.coyamt) - ASD(self.allocated))
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
            row = int(int((self.df.last[1][1] - 1) / self.df.colq[1]))
            col = (row * self.df.colq[1]) + 1
            self.df.focusField("C", 1, col)

    def endPage2(self):
        self.updateTables2()
        self.allocated = float(ASD(self.allocated) + ASD(self.allamt))
        if self.allocated == self.coyamt:
            self.opts["mf"].dbm.commitDbase()
            self.df.clearFrame("C", 2)
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
        else:
            bal = float(ASD(self.coyamt) - ASD(self.allocated))
            self.df.loadEntry("T", 2, 0, data=bal)
            self.df.advanceLine(2)

    def updateTables2(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        # General Ledger Transaction (Allocation)
        amt = float(ASD(0) - ASD(self.allamt))
        data = (self.opts["conum"], self.genacc, self.curdt, self.trndat,
            self.glt, self.trnref, self.bh.batno, amt, 0.00, self.alldet, "N",
            "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)

    def exitPage2(self):
        self.df.focusField("C", 2, self.df.col)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty -= 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.coyamt))
        else:
            self.batupd = True
            self.bh.batqty += 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.coyamt))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def doNewAsset(self):
        tit = ("Create New Asset", )
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",0,1,0),"INa",3,"Dep Code","Depreciation Code",
                self.depcod,"N",self.doDepCode,dep,None,("notblank",)),
            (("T",0,1,0),"ONA",34,""))
        tnd = ((self.doNewEnd,"N"), )
        txt = (self.doNewXit, )
        state = self.df.disableButtonsTags()
        self.na = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=self.fld, tend=tnd, txit=txt)
        self.na.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doDepCode(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("assdep", cols=["asd_desc"],
            where=[("asd_cono", "=", self.opts["conum"]), ("asd_code", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Depreciation Code"
        self.na.loadEntry(frt, pag, p+1, data=chk[0])

    def doNewEnd(self):
        dat = [self.opts["conum"], self.group, self.code]
        for x in range(len(self.na.t_work[0][0]) - 1):
            dat.append(self.na.t_work[0][0][x])
        self.sql.insRec("assmst", data=dat)
        self.doNewXit()

    def doNewXit(self):
        self.na.closeProcess()

    def queryAss(self):
        callModule(self.opts["mf"], self.df, "ar4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=self.opts["period"],
            user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
