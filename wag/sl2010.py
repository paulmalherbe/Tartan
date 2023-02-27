"""
SYNOPSIS
    Salaries New Staff Loans Capture.

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
from tartanFunctions import callModule, getNextCode

class sl2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "gentrn", "wagedc",
            "wagmst", "waglmf", "wagltf"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        wagctl = self.gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.glint = wagctl["ctw_glint"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"], ctlctl, ["wag_slc"]):
                return
            self.slnctl = ctlctl["wag_slc"]
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "SLN", 2,
            glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def dataHeader(self):
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname", "Y")),
            "where": [("wgm_cono", "=", self.opts["conum"])]}
        ced = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (("ced_type", "", 0, "T"),
                ("ced_code", "", 0, "Cde"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [
                ("ced_cono", "=", self.opts["conum"]),
                ("ced_type", "=", "D")],
            "index": 1}
        fld = (
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",0,0,0),"IUI",5,"EmpNo","Employee Number",
                "","N",self.doEmpno,wgm,None,None),
            (("C",0,0,1),"ONA",20,"Name"),
            (("C",0,0,2),"OUI",2,"Ln"),
            (("C",0,0,3),"INA",15,"Description","",
                "","N",self.doDesc,None,None,None),
            (("C",0,0,4),"ID1",10,"Date","",
                "","N",self.doSdate,None,None,None),
            (("C",0,0,5),"INa",9,"Ref-No","Reference Number",
                "","N",self.doRef,None,None,("notblank",)),
            (("C",0,0,6),"IUI",3,"Cde","Deduction Code",
                "","N",self.doCode,ced,None,("notzero",)),
            (("C",0,0,7),"IUD",6.2,"Intr-%","Interest Rate",
                "","N",self.doInt,None,None,None),
            (("C",0,0,8),"IUD",12.2,"Loan-Amt","Loan Amount",
                "","N",self.doAmt,None,None,("notzero",)),
            (("C",0,0,9),"IUD",12.2,"Ded-Amt","Deduction Amount",
                "","N",self.doDed,None,None,("efld",)))
        but = (("Interrogate",None,self.querySln,0,("C",0,1),("C",0,2)),)
        cnd = ((self.endPage,"y"), )
        cxt = (self.exitPage, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            cend=cnd, cxit=cxt)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 0, 1)

    def doEmpno(self, frt, pag, r, c, p, i, w):
        self.empno = w
        acc = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
            where=[("wgm_cono", "=", self.opts["conum"]), ("wgm_empno", "=",
            self.empno)], limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.name = "%s, %s" % (acc[0], acc[1].split()[0])
        self.df.loadEntry("C", pag, p+1, data=self.name)
        self.loan = getNextCode(self.sql, "waglmf", "wlm_loan",
            where=[("wlm_cono", "=", self.opts["conum"]),
            ("wlm_empno", "=", self.empno)], start=1, last=9999999)
        self.df.loadEntry("C", pag, p+2, data=self.loan)

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doSdate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.sdate = w

    def doRef(self, frt, pag, r, c, p, i, w):
        self.ref = w

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        desc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type", "=",
            "D"), ("ced_code", "=", w)], limit=1)
        if not desc:
            return "Invalid Code"

    def doInt(self, frt, pag, r, c, p, i, w):
        self.rte = w

    def doAmt(self, frt, pag, r, c, p, i, w):
        self.amt = w

    def doDed(self, frt, pag, r, c, p, i, w):
        self.ded = w

    def endPage(self):
        self.updateTables()
        self.updateBatch()
        self.opts["mf"].dbm.commitDbase()
        self.df.advanceLine(0)

    def exitPage(self):
        self.df.closeProcess()
        self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

    def updateTables(self):
        if self.bh.multi == "Y":
            curdt = int(self.sdate / 100)
        else:
            curdt = self.bh.curdt
        self.sql.insRec("waglmf", data=[self.opts["conum"], self.empno,
            self.loan, self.desc, self.code, self.rte, self.sdate, self.ded])
        self.sql.insRec("wagltf", data=[self.opts["conum"], self.empno,
            self.loan, self.bh.batno, 2, self.sdate, self.ref, self.amt,
            self.amt, self.ded, self.rte, curdt, self.desc, "N",
            self.opts["capnm"], self.sysdtw, 0])
        if self.glint == "N":
            return
        # General Ledger Staff Loans Control Account
        data = (self.opts["conum"], self.slnctl, curdt, self.sdate, 2,
            self.ref, self.bh.batno, self.amt, 0.00, self.name, "N",
            "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        amt = float(ASD(0) - ASD(self.amt))
        # General Ledger Bank Account
        data = (self.opts["conum"], self.bh.acc, curdt, self.sdate, 2,
            self.ref, self.bh.batno, amt, 0.00, "Staff Loan - %s" % self.name,
            "N", "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)

    def updateBatch(self):
        self.bh.batqty = self.bh.batqty + 1
        self.bh.batval = float(ASD(self.bh.batval) + ASD(self.amt))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def querySln(self):
        callModule(self.opts["mf"], self.df, "sl4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
