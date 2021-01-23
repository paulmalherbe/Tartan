"""
SYNOPSIS
    Salaries Staff Loans Raise Interest.

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
from TartanClasses import GetCtl, LoanInterest, ProgressBar, Sql
from TartanClasses import TartanDialog

class sl2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagctl", "waglmf"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        glint = wagctl["ctw_glint"]
        if glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["wag_slc", "wag_sli"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.glctl = (
                ctlctl["wag_slc"], ctlctl["wag_sli"], ctlctl["wag_sli"])
        else:
            self.glctl = None
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def dataHeader(self):
        fld = (
            (("T",0,0,0),"ID1",10,"Transaction Date","",
                self.sysdtw,"N",self.doTrdate,None,None,None),)
        tnd = ((self.endPage0, "y"),)
        txt = (self.exitPage0,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doTrdate(self, frt, pag, r, c, p, i, w):
        self.trdate = w
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"

    def endPage0(self):
        self.df.closeProcess()
        recs = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
            self.opts["conum"]), ("wlm_rate", ">", 0), ("wlm_start", "<",
            self.trdate)], order="wlm_empno, wlm_loan")
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs))
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            curdt = int(self.trdate / 100)
            batch = "L%s" % curdt
            LoanInterest("S", self.opts["mf"].dbm, rec, update="Y",
                batch=batch, curdt=curdt, tdate=self.trdate,
                glctl=self.glctl, capnm=self.opts["capnm"])
        p.closeProgress()
        self.sql.updRec("wagctl", cols=["ctw_i_date"], data=[self.trdate],
            where=[("ctw_cono", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase()
        self.opts["mf"].closeLoop()

    def exitPage0(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
