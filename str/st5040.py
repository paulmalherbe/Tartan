"""
SYNOPSIS
    Stores Stock Take Merge.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import showError

class st5040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["gentrn", "strmf1", "strtrn",
            "strvar", "strprc"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
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
        fld = [
            (("T",0,0,0),"ID1",10,"Merging Date","",
                self.sysdtw,"N",self.doDate,None,None,("efld",))]
        tnd = ((self.endPage,"y"),)
        txt = (self.exitPage,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doDate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.date = w
        self.curdt = int(w / 100)

    def endPage(self):
        self.df.closeProcess()
        col = ["stv_group", "stv_code", "stv_loc", "stv_bin", "stv_qty",
            "stv_ucost"]
        recs = self.sql.getRec(tables=["strmf1", "strvar"], cols=col,
            where=[("stv_cono", "=", self.opts["conum"]),
            ("stv_cono=st1_cono",), ("stv_group=st1_group",),
            ("stv_code=st1_code",)], order="stv_group, stv_code, stv_loc")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        else:
            p = ProgressBar(self.opts["mf"].body, typ="F", mxs=len(recs))
            for num, dat in enumerate(recs):
                p.displayProgress(num)
                self.updateTables(num+1, col, dat)
                self.sql.delRec("strvar", where=[("stv_cono", "=",
                    self.opts["conum"]), ("stv_group", "=",
                    dat[col.index("stv_group")]),
                    ("stv_code", "=", dat[col.index("stv_code")]),
                    ("stv_loc", "=", dat[col.index("stv_loc")])])
            self.opts["mf"].dbm.commitDbase()
            p.closeProgress()
        self.opts["mf"].closeLoop()

    def exitPage(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def updateTables(self, cnt, col, rec):
        grp = rec[col.index("stv_group")]
        code = rec[col.index("stv_code")]
        loc = rec[col.index("stv_loc")]
        vqty = CCD(rec[col.index("stv_qty")], "SD", 12.2)
        vprc = CCD(rec[col.index("stv_ucost")], "SD", 12.2)
        # Test for Variances
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"], self.curdt,
            keys=(grp, code, loc, ("P", self.opts["period"][0])))
        m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
        fqty = CCD(y_cb[0], "SD", 12.2)
        fval = CCD(y_cb[1], "SD", 12.2)
        if fval.work and fqty.work:
            c = round((fval.work / fqty.work), 2)
        else:
            c = 0
        fprc = CCD(c, "SD", 12.2)
        if fprc.work != vprc.work and vprc.work:
            prc = vprc.work
        else:
            prc = fprc.work
        prc = CCD(prc, "SD", 12.2)
        val = round((prc.work * vqty.work),2)
        vval = CCD(val, "SD", 12.2)
        qdif = CCD(float(ASD(vqty.work) - ASD(fqty.work)), "SD", 12.2)
        vdif = CCD(float(ASD(vval.work) - ASD(fval.work)), "SD", 12.2)
        if not qdif.work and not vdif.work:
            return
        # Stores Ledger Transaction
        if qdif.work >= 0:
            rtn = 5
        else:
            rtn = 6
        ref = CCD(cnt, "Na", 9).work
        self.sql.insRec("strtrn", data=[self.opts["conum"],
            rec[col.index("stv_group")], rec[col.index("stv_code")],
            rec[col.index("stv_loc")], self.date, rtn, ref, "ST-MERG", "",
            qdif.work, vdif.work, 0, self.curdt, "Stock Take Adjustment", 0,
            "", "", "STR", 0, "", self.opts["capnm"], self.sysdtw, 0])
        if self.glint == "N":
            return
        # General Ledger Control Transaction (Stock On Hand)
        col = self.sql.gentrn_col
        acc = self.sql.getRec("gentrn", where=[("glt_cono", "=",
            self.opts["conum"]), ("glt_acno", "=", self.stk_soh), ("glt_curdt",
            "=", self.curdt), ("glt_trdt", "=", self.date), ("glt_type", "=",
            4), ("glt_refno", "=", "STOCK-ADJ"), ("glt_batch", "=",
            "ST-MERG")], limit=1)
        if acc:
            amnt = float(ASD(acc[col.index("glt_tramt")]) + ASD(vdif.work))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[amnt],
                where=[("glt_seq", "=", acc[col.index("glt_seq")])])
        else:
            self.sql.insRec("gentrn", data=[self.opts["conum"], self.stk_soh,
                self.curdt, self.date, 4, "STOCK-ADJ", "ST-MERG", vdif.work, 0,
                "Stock Take Adjustment", "N", "", 0, self.opts["capnm"],
                self.sysdtw, 0])
        # General Ledger Control Transaction (Stock Suspense)
        val = float(ASD(0) - ASD(vdif.work))
        acc = self.sql.getRec("gentrn", where=[("glt_cono", "=",
            self.opts["conum"]), ("glt_acno", "=", self.stk_susp),
            ("glt_curdt", "=", self.curdt), ("glt_trdt", "=", self.date),
            ("glt_type", "=", 4), ("glt_refno", "=", "STOCK-ADJ"),
            ("glt_batch", "=", "ST-MERG")], limit=1)
        if acc:
            amnt = float(ASD(acc[col.index("glt_tramt")]) + ASD(val))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[amnt],
                where=[("glt_seq", "=", acc[col.index("glt_seq")])])
        else:
            self.sql.insRec("gentrn", data=[self.opts["conum"], self.stk_susp,
                self.curdt, self.date, 4, "STOCK-ADJ", "ST-MERG", val, 0,
                "Stock Take Adjustment", "N", "", 0, self.opts["capnm"],
                self.sysdtw, 0])

# vim:set ts=4 sw=4 sts=4 expandtab:
