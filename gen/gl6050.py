"""
SYNOPSIS
    General Ledger Initialise Bank Reconcilition.

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

from TartanClasses import Sql, TartanDialog
from tartanFunctions import copyList
from tartanWork import gltrtp

class gl6050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "genmst", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def doProcess(self):
        glm = {
            "stype": "R",
            "tables": ("ctlctl", "genmst"),
            "cols": (
                ("ctl_conacc", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [
                ("ctl_cono", "=", self.opts["conum"]),
                ("ctl_code", "like", "bank_%"),
                ("glm_cono=ctl_cono",),
                ("glm_acno=ctl_conacc",)]}
        typ = {
            "stype": "C",
            "title": "Select Type",
            "head": ("C", "Type"),
            "data": ((2, "Payment"), (4, "Journal"), (6, "Receipt"))}
        self.glt = {
            "stype": "R",
            "tables": ("gentrn",),
            "cols": (
                ("glt_trdt", "", 0, "Date"),
                ("glt_type", ("XX", gltrtp), 3, "Typ"),
                ("glt_refno", "", 0, "Reference", "Y"),
                ("glt_seq", "", 0, "Sequence"),
                ("glt_tramt", "", 0, "Amount"),
                ("glt_desc", "", 0, "Details")),
            "where": [],
            "index": 2,
            "zero": "0"}
        r1s = (("Yes","Y"), ("No","N"))
        fld = (
            (("T",0,0,0),"IUI",7,"Bank Account","",
                "","N",self.doBankAcc,glm,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"ID2",7,"Last Period","Last Reconciliation Period",
                0,"N",self.doLastPer,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),7,"Clear History","",
                "N","N",self.doClear,None,None,None),
            (("C",0,0,0),"IUA",1,"T","Reference Type",
                2,"N",self.doTrnTyp,typ,None,("in", ("2","4","6"))),
            (("C",0,0,1),"INa",9,"Ref-Num","Reference Number",
                "i","N",self.doTrnRef,self.glt,None,("notblank",)),
            (("C",0,0,2),"OD1",10,"Date"),
            (("C",0,0,3),"OSD",13.2,"Amount"),
            (("C",0,0,4),"ONA",30,"Details"))
        tnd = ((self.endTop,"y"),)
        txt = (self.exitTop,)
        cnd = ((self.endCol,"y"),)
        cxt = (self.exitCol,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, cend=cnd, cxit=cxt)

    def doBankAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["ctlctl", "genmst"], cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=", w),
            ("ctl_cono=glm_cono",), ("ctl_conacc=glm_acno",), ("ctl_code",
            "like", "bank_%")], limit=1)
        if not acc:
            return "Invalid Bank Account Number"
        self.acno = w
        self.df.loadEntry("T", 0, p+1, data=acc[0])

    def doLastPer(self, frt, pag, r, c, p, i, w):
        self.curdt = w

    def doClear(self, frt, pag, r, c, p, i, w):
        self.clear = w

    def endTop(self):
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.acno)]
        if self.clear == "Y":
            self.sql.updRec("gentrn", cols=["glt_recon"], data=[0], where=whr)
        whr.extend([("glt_curdt", "<=", self.curdt), ("glt_recon", "=", 0)])
        self.sql.updRec("gentrn", cols=["glt_recon"], data=[self.curdt],
            where=whr)
        self.df.focusField("C", 0, 1)

    def exitTop(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doTrnTyp(self, frt, pag, r, c, p, i, w):
        self.opts["rtn"] = w
        self.df.colf[0][1][8]["where"] = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.acno),
            ("glt_type", "=", self.opts["rtn"]),
            ("glt_curdt", "<=", self.curdt),
            ("glt_recon", "<>", 0)]
        try:
            self.df.rs.selection = None
        except:
            pass

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w
        try:
            rs = self.df.rs.selection
        except:
            rs = None
        if not rs:
            wa = [
                ("glt_type", "=", self.opts["rtn"]),
                ("glt_refno", "=", self.trnref)]
            opt = {}
            for k in self.glt:
                if k == "where":
                    opt[k] = copyList(self.glt[k])
                    opt[k].extend(wa)
                elif type(self.glt[k]) == list:
                    opt[k] = copyList(self.glt[k])
                else:
                    opt[k] = self.glt[k]
            rs = self.df.selRecord(1, opt).selection
        if rs:
            self.df.loadEntry("C", 0, p+1, data=rs[0])
            self.df.loadEntry("C", 0, p+2, data=rs[4])
            self.df.loadEntry("C", 0, p+3, data=rs[5])
            self.seq = rs[3]
            return "nd"
        else:
            return "Invalid Transaction"

    def endCol(self):
        self.sql.updRec("gentrn", cols=["glt_recon"], data=[0],
            where=[("glt_seq", "=", self.seq)])
        self.df.advanceLine(0)

    def exitCol(self):
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
