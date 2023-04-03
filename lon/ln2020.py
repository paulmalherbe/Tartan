"""
SYNOPSIS
    Loans Raise Interest.

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
from TartanClasses import GetCtl, LoanInterest, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import mthendDate

class ln2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        glint = lonctl["cln_glint"]
        tab = ["lonctl", "lonmf2", "lontrn"]
        if glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["lon_ctl", "int_rec", "int_pay"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.glctl = (
                ctlctl["lon_ctl"], ctlctl["int_rec"], ctlctl["int_pay"])
            tab.append("gentrn")
        else:
            self.glctl = None
        self.sql = Sql(self.opts["mf"].dbm, tables=tab,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        yr = int(self.sysdtw / 10000)
        mt = (int(self.sysdtw / 100) % 100) - 1
        self.lme = mthendDate((yr * 10000) + (mt * 100) + 1)
        if self.lme < self.opts["period"][1][0]:
            self.lme = self.opts["period"][1][0]
        elif self.lme > self.opts["period"][2][0]:
            self.lme = self.opts["period"][2][0]
        return True

    def dataHeader(self):
        fld = (
            (("T",0,0,0),"ID1",10,"Transaction Date","",
                self.lme,"N",self.doTrdate,None,None,None),)
        tnd = ((self.endPage0, "y"),)
        txt = (self.exitPage0,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doTrdate(self, frt, pag, r, c, p, i, w):
        self.trdate = w
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if w != mthendDate(w):
            return "Invalid Date, Not a Month End"

    def endPage0(self):
        self.df.closeProcess()
        recs = self.sql.getRec("lonmf2", where=[("lm2_cono", "=",
            self.opts["conum"]), ("lm2_start", "<", self.trdate)],
            order="lm2_acno, lm2_loan")
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs))
        for num, lonmf2 in enumerate(recs):
            p.displayProgress(num)
            batch = "L%s" % int(self.trdate / 100)
            LoanInterest("L", self.opts["mf"].dbm, lonmf2, update="Y",
                tdate=self.trdate, batch=batch, curdt=int(self.trdate / 100),
                refno=True, glctl=self.glctl, capnm=self.opts["capnm"])
        p.closeProgress()
        self.sql.updRec("lonctl", cols=["cln_last"], data=[self.trdate],
            where=[("cln_cono", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase()
        self.opts["mf"].closeLoop()

    def exitPage0(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
