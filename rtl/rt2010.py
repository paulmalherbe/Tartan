"""
SYNOPSIS
    Rentals Data Capture Screen and Execution.

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
from TartanClasses import ASD, Batches, GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, chkGenAcc, getVatRate
from tartanFunctions import showError

class rt2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        tabs = [
            "ctlmst", "ctlvmf", "ctlvrf", "ctlvtf",
            "genint", "genmst", "gentrn",
            "rtlprm", "rtlmst","rtlcon",  "rtltrn"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        if self.opts["rtn"] not in (2, 3, 4):
            mes = "Invalid Routine %s" % str(self.opts["rtn"])
            showError(self.opts["mf"].body, "Control Error", mes)
            return
        self.gc = GetCtl(self.opts["mf"])
        rtlctl = self.gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        self.glint = rtlctl["ctr_glint"]
        if self.glint == "Y":
            # Check All Premises Control Records
            errs = (
                "Premises %s Has An Invalid",
                "Rental Control Account (%s)",
                "Rental Income Account (%s)")
            ass = self.sql.getRec("rtlprm", cols=["rtp_code",
                "rtp_rtlacc", "rtp_incacc"], where=[("rtp_cono", "=",
                self.opts["conum"])])
            for acc in ass:
                for x in range(1, 3):
                    chk = self.sql.getRec("genmst", where=[("glm_cono",
                        "=", self.opts["conum"]), ("glm_acno", "=", acc[x])],
                        limit=1)
                    if not chk:
                        mess = "%s %s" % (errs[0] % acc[0], errs[x] % acc[x])
                        showError(self.opts["mf"].body, "Control Error", mess)
                        return
            # Check for VAT Control
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"], ctlctl, ["vat_ctl"]):
                return
            self.convat = ctlctl["vat_ctl"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "RTL", self.opts["rtn"],
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        if self.opts["rtn"] == 2:
            self.bh.batval = float(ASD(0) - ASD(self.bh.batval))
        return True

    def drawDialog(self):
        prm = {
            "stype": "R",
            "tables": ("rtlprm",),
            "cols": (
                ("rtp_code", "", 0, "Prm-Cod"),
                ("rtp_desc", "", 0, "Description", "Y")),
            "where": [("rtp_cono", "=", self.opts["conum"])]}
        mst = {
            "stype": "R",
            "tables": ("rtlmst",),
            "cols": (
                ("rtm_acno", "", 0, "Acc-Num"),
                ("rtm_name", "", 0, "Name", "Y")),
            "where": [("rtm_cono", "=", self.opts["conum"])],
            "whera": [["C", "rtm_code", 0, 1]]}
        con = {
            "stype": "R",
            "tables": ("rtlcon",),
            "cols": (
                ("rtc_cnum", "", 0, "Acc-Num"),
                ("rtc_payind", "", 0, "F"),
                ("rtc_start", "", 0, "Start-Date"),
                ("rtc_period", "", 0, "Per")),
            "where": [("rtc_cono", "=", self.opts["conum"])],
            "whera": [["C", "rtc_code", 0, 1], ["C", "rtc_acno", 1, 1]]}
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
        fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"INA",7,"Prm-Cod","Premises Code",
                "r","N",self.doPrmCod,prm,None,None),
            (("C",1,0,1),"INA",7,"Acc-Num","Account Number",
                "r","N",self.doAccNum,mst,None,None),
            (("C",1,0,2),"IUI",3,"Seq","Contract Sequence",
                "","N",self.doConSeq,con,None,None),
            (("C",1,0,3),"INa",9,"Reference","Reference Number",
                "i","N",self.doTrnRef,None,None,("notblank",)),
            (("C",1,0,4),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            (("C",1,0,5),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,None),
            (("C",1,0,6),"IUA",1,"V","V.A.T Code",
                "","N",self.doVatCod,vtm,None,("notblank",)),
            (("C",1,0,7),"ISD",11.2,"V.A.T","V.A.T Amount",
                "","N",self.doVatAmt,None,None,None),
            [("C",1,0,8),"INA",30,"Details","Transaction Details",
                "","N",self.doTrnDet,None,None,None]]
        if self.opts["rtn"] not in (2, 3) and self.glint == "Y":
            fld[10][2] = (22,30)
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
            ("Interrogate",None,self.queryRtl,0,("C",1,1),("C",1,2)),
            ("Cancel",None,self.doCancel,0,("C",2,1),("C",1,1)))
        tag = [("Transaction", None, None, None, False)]
        cnd = [(None,"n"), (self.endPage1,"y")]
        cxt = [None, self.exitPage1]
        if self.opts["rtn"] not in (2, 3) and self.glint == "Y":
            tag.append(("Allocation", None, None, None, False))
            cnd.append((self.endPage2,"y"))
            cxt.append(self.exitPage2)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag, cend=cnd,
            cxit=cxt, butt=but)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doPrmCod(self, frt, pag, r, c, p, i, w):
        whr = [("rtp_cono", "=", self.opts["conum"]), ("rtp_code", "=", w)]
        acc = self.sql.getRec("rtlprm", where=whr, limit=1)
        if not acc:
            return "Invalid Premises Code"
        self.code = w
        self.rtlacc = acc[self.sql.rtlprm_col.index("rtp_rtlacc")]

    def doAccNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlmst", cols=["rtm_name",
            "rtm_vatind"], where=[("rtm_cono", "=", self.opts["conum"]),
            ("rtm_code", "=", self.code), ("rtm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.opts["conum"]), ("rtc_code", "=", self.code), ("rtc_acno",
            "=", self.acno)], order="rtc_cnum")
        if not con:
            return "No Valid Contracts"
        self.cnum = con[-1:][0][3]
        self.df.colf[1][2][5] = self.cnum
        if self.opts["rtn"] == 4:
            self.df.colf[1][6][5] = acc[1]
        else:
            self.df.colf[1][6][5] = "N"

    def doConSeq(self, frt, pag, r, c, p, i, w):
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.opts["conum"]), ("rtc_code", "=", self.code), ("rtc_acno",
            "=", self.acno), ("rtc_cnum", "=", w)], order="rtc_cnum")
        if not con:
            return "Invalid Contract Sequence"
        self.cnum = w

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndat = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if self.opts["rtn"] in (2, 3):
            self.vatcode = ""
            self.trnvat = 0
            return "sk2"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if vrte is None:
            return "Invalid V.A.T Code"
        self.vatcode = w
        self.trnvat = round((self.trnamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry(frt, pag, p+1, data=self.trnvat)
        if not self.trnvat:
            return "sk1"

    def doVatAmt(self, frt, pag, r, c, p, i, w):
        if self.trnamt < 0 and w > 0:
            self.trnvat = float(ASD(0) - ASD(w))
        elif self.trnamt > 0 and w < 0:
            self.trnvat = float(ASD(0) - ASD(w))
        else:
            self.trnvat = w
        self.df.loadEntry(frt, pag, p, data=self.trnvat)

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        if self.opts["rtn"] not in (2, 3) and self.glint == "Y":
            self.df.colf[2][3][5] = w

    def endPage1(self):
        self.batupd = False
        self.updateTables1()
        self.updateBatch()
        if self.trnamt == 0:
            self.df.advanceLine(1)
        else:
            self.allocated = float(0.0)
            if self.opts["rtn"] in (2, 3) or self.glint == "N":
                self.opts["mf"].dbm.commitDbase()
                self.df.selPage("Transaction")
                self.df.advanceLine(1)
            else:
                self.trnamt = float(ASD(self.trnamt) - ASD(self.trnvat))
                self.df.loadEntry("T", 2, 0, data=self.trnamt)
                self.df.selPage("Allocation")
                self.df.focusField("C", 2, 1)

    def updateTables1(self):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndat / 100)
        else:
            self.curdt = self.bh.curdt
        self.amt = self.trnamt
        self.vat = self.trnvat
        if self.opts["rtn"] == 2:                           # Receipts
            if self.trnamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            self.amt = float(ASD(0) - ASD(self.amt))
            self.vat = float(ASD(0) - ASD(self.vat))
            self.glt = 6
        elif self.opts["rtn"] == 3:                        # Payments
            if self.trnamt == 0:
                self.recon = self.curdt
            else:
                self.recon = 0
            self.glt = 2
        elif self.opts["rtn"] == 4:                        # Journal Entries
            self.recon = 0
            self.glt = 4
        # Rental Ledger Transaction
        data = [self.opts["conum"], self.code, self.acno, self.cnum,
            self.opts["rtn"], self.trnref, self.bh.batno, self.trndat,
            self.amt, self.vat, self.curdt, self.trndet, self.vatcode, "N",
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("rtltrn", data=data)
        if self.vatcode:
            # VAT Transaction (ctlvtf)
            exc = float(ASD(0) - ASD(self.amt) + ASD(self.vat))
            vat = float(ASD(0) - ASD(self.vat))
            data = (self.opts["conum"], self.vatcode, "O", self.curdt, "R",
                self.opts["rtn"], self.bh.batno, self.trnref, self.trndat,
                self.code, self.trndet, exc, vat, 0, self.opts["capnm"],
                self.sysdtw, 0)
            self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        # General Ledger Rental Account
        data = (self.opts["conum"], self.rtlacc, self.curdt, self.trndat,
            self.glt, self.trnref, self.bh.batno, self.amt, self.vat,
            self.trndet, self.vatcode, "", 0, self.opts["capnm"],
            self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        self.trnamt = float(ASD(0) - ASD(self.amt))
        self.trnvat = float(ASD(0) - ASD(self.vat))
        if self.vatcode and self.trnvat:
            # General Ledger Control Transaction (V.A.T.)
            data = (self.opts["conum"], self.convat, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.trnvat, 0.00,
                self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        if self.opts["rtn"] in (2, 3):
            # General Ledger Control Transaction (Bank)
            data = (self.opts["conum"], self.bh.acc, self.curdt, self.trndat,
                self.glt, self.trnref, self.bh.batno, self.trnamt, 0.00,
                self.trndet, "N", "", self.recon, self.opts["capnm"],
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
            self.allamt = float(ASD(self.trnamt) - ASD(self.allocated))
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
        if self.allocated == self.trnamt:
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
        # General Ledger Transaction (Source)
        data = (self.opts["conum"], self.genacc, self.curdt, self.trndat,
            self.glt, self.trnref, self.bh.batno, self.allamt, 0.00,
            self.alldet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)

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

    def queryRtl(self):
        callModule(self.opts["mf"], self.df, "rt4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
