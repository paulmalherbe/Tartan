"""
SYNOPSIS
    Stores Revalue at Average or Last Cost and Optionally Calculate Selling
    Prices and Eradicate All Minus Balances.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import showError

class st6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["gentrn", "strmf1", "strmf2",
            "strgmu", "strcmu", "strprc", "strtrn"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["stk_soh", "stk_susp"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.stk_soh = ctlctl["stk_soh"]
            self.stk_susp = ctlctl["stk_susp"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def dataHeader(self):
        r1s = (("Average", "A"), ("Last", "L"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = [
            (("T",0,0,0),"ID1",10,"Effective Date","",
                self.sysdtw,"N",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Cost Method","",
                "L","N",self.doMethod,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Clear Minuses","",
                "Y","N",self.doMinus,None,None,None)]
        tnd = ((self.endPage,"y"),)
        txt = (self.exitPage,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.curdt = int(w / 100)

    def doMethod(self, frt, pag, r, c, p, i, w):
        self.method = w

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def endPage(self):
        self.df.closeProcess()
        whr = [
            ("st2_cono", "=", self.opts["conum"]),
            ("st1_cono=st2_cono",),
            ("st1_group=st2_group",),
            ("st1_code=st2_code",),
            ("st1_type", "<>", "X"),
            ("st1_value_ind", "<>", "N")]
        recs = self.sql.getRec(tables=["strmf1", "strmf2"], cols=["st2_group",
            "st2_code", "st2_loc"], where=whr, order="st2_group, st2_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Stock Records")
        else:
            self.cnt = 0
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs),
                typ="Valuation of Stock at Last Cost")
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                self.updateTables(rec)
            p.closeProgress()
            self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def exitPage(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def updateTables(self, rec):
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
            int(self.sysdtw / 100), keys=(rec[0], rec[1], rec[2], ("P",
            self.opts["period"][0])))
        m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
        if self.minus == "N" and not ac and not lc:
            return
        fqty = CCD(y_cb[0], "SD", 12.2)
        fval = CCD(y_cb[1], "SD", 12.2)
        if self.minus == "Y" and fqty.work < 0:
            nqty = 0
        else:
            nqty = fqty.work
        if self.method == "L" and lc:
            nval = nqty * lc
        elif self.method == "A" and ac:
            nval = nqty * ac
        elif lc:
            nval = nqty * lc
        else:
            nval = nqty * ac
        dqty = float(ASD(nqty) - ASD(fqty.work))
        dval = float(ASD(nval) - ASD(fval.work))
        if not dqty and not dval:
            return
        # Stores Ledger Transaction
        if dqty >= 0:
            rtn = 5
        else:
            rtn = 6
        txt = "Revaluation"
        self.sql.insRec("strtrn", data=[self.opts["conum"], rec[0], rec[1],
            rec[2], self.date, rtn, self.cnt, "ST-RVAL", "", dqty, dval, 0,
            self.curdt, txt, 0, "", "", "STR", 0, "", self.opts["capnm"],
            self.sysdtw, 0])
        if self.glint == "N":
            self.cnt = self.cnt + 1
            return
        # General Ledger Control Transaction (Stock On Hand)
        self.sql.insRec("gentrn", data=[self.opts["conum"], self.stk_soh,
            self.curdt, self.date, 4, self.cnt, "ST-RVAL", dval, 0, txt, "N",
            "", 0, self.opts["capnm"], self.sysdtw, 0])
        # General Ledger Control Transaction (Stock Reconciliation)
        val = float(ASD(0) - ASD(dval))
        self.sql.insRec("gentrn", data=[self.opts["conum"], self.stk_susp,
            self.curdt, self.date, 4, self.cnt, "ST-RVAL", val, 0, txt, "N",
            "", 0, self.opts["capnm"], self.sysdtw, 0])

# vim:set ts=4 sw=4 sts=4 expandtab:
