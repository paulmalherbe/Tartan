"""
SYNOPSIS
    Debtor's Ledger Calculate Credit Ratings.

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
from TartanClasses import ASD, Balances, GetCtl, ProgressBar, Sql, TartanDialog

class dr6040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.sql = Sql(self.opts["mf"].dbm, "drsmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.curdt = (t[0] * 100) + t[1]
        return True

    def mainProcess(self):
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Current Period","",
                self.curdt,"Y",self.doCurdt,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Ignore Zero Balances","",
                "Y","Y",self.doIgnore,None,None,None))
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt)

    def doCurdt(self, frt, pag, r, c, p, i, w):
        self.curdt = w

    def doIgnore(self, frt, pag, r, c, p, i, w):
        self.ignore = w

    def doProcess(self):
        self.df.closeProcess()
        recs = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_stat", "<>", "X")],
            order="drm_chain, drm_name")
        if recs:
            col = self.sql.drsmst_col
            p = ProgressBar(self.opts["mf"].body, typ="Calculating Ratings",
                mxs=len(recs))
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                chn = rec[col.index("drm_chain")]
                acc = rec[col.index("drm_acno")]
                rft = int(rec[col.index("drm_rfterms")] / 30)
                rjt = int(rec[col.index("drm_rjterms")] / 30)
                lim = rec[col.index("drm_limit")]
                stp = rec[col.index("drm_stop")]
                rte = rec[col.index("drm_rating")]
                if rte == "B" or stp == "Y":
                    rating = "B"
                else:
                    rating = None
                    bal = Balances(self.opts["mf"], "DRS", self.opts["conum"],
                        self.curdt, [chn, acc])
                    obal, cbal, age = bal.doAllBals()
                    if cbal > 0:
                        if lim and cbal > lim:
                            rating = "P"
                        if not rating and rft > 0:
                            bal = 0
                            for y in range(rft-1, 5):
                                bal = float(ASD(bal) + ASD(age[y]))
                            if bal > 0:
                                rating = "F"
                        if not rating and rjt > 0:
                            bal = 0
                            for y in range(rjt-1, 5):
                                bal = float(ASD(bal) + ASD(age[y]))
                            if bal > 0:
                                rating = "B"
                        if not rating and rte in ("", "N"):
                            rating = "G"
                    elif self.ignore == "N" and cbal == 0 and rte in ("", "N"):
                        rating = "G"
                if rating:
                    self.sql.updRec("drsmst", cols=["drm_rating"],
                        data=[rating], where=[("drm_cono", "=",
                        self.opts["conum"]), ("drm_chain", "=", chn),
                        ("drm_acno", "=", acc)])
            p.closeProgress()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
