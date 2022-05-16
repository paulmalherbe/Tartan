"""
SYNOPSIS
    Rentals Ledger Deposit Listing.

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
from TartanClasses import ASD, GetCtl, ProgressBar, RepPrt, Sql, TartanDialog
from tartanFunctions import getDeposit, showError

class rc3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcatnm", "rcatnt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.fromad = rcactl["cte_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Outstanding Deposits (%s)" % self.__class__.__name__)
        fld = (
            (("T",0,0,0),"ID1",10,"Report Date","",
                self.sysdtw,"N",self.doDate,None,None,("efld",)),)
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.datep = self.df.t_disp[pag][0][p]

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        self.df.closeProcess()
        grp = "rtu_owner, rtu_code, rtu_acno"
        recs = self.sql.getRec("rcatnt", cols=["rtu_owner", "rtu_code",
            "rtu_acno"], where=[("rtu_cono", "=", self.opts["conum"]),
            ("rtu_mtyp", "=", 2), ("rtu_trdt", "<=", self.date)],
            group=grp, order=grp)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        data = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            owner, code, acno = dat
            dep = getDeposit(self.opts["mf"], self.opts["conum"], self.date,
                owner, code, acno)
            if not dep:
                continue
            dept = 0
            intr = 0
            admn = 0
            for d in dep:
                dept = float(ASD(dept) + ASD(d[1]))
                intr = float(ASD(intr) + ASD(d[4]))
                admn = float(ASD(admn) + ASD(d[6]))
            balance = float(ASD(dept) + ASD(intr))
            name = self.sql.getRec("rcatnm", cols=["rtn_name"],
                where=[("rtn_cono", "=", self.opts["conum"]), ("rtn_owner",
                "=", owner), ("rtn_code", "=", code), ("rtn_acno", "=", acno)],
                limit=1)
            if name:
                name = name[0]
            else:
                name = "Unknown"
            if dept:
                data.append([code, acno, name, dept, intr, balance, admn])
        p.closeProgress()
        if not p.quit:
            head = ["Tenants Outstanding Deposits as at %s" % self.datep]
            cols = [
                ["aa", "NA",  7,   "Pr-Code",  "y"],
                ["bb", "NA",  7,   "Acc-Num",  "y"],
                ["cc", "NA", 40,   "Name",     "y"],
                ["dd", "SD", 13.2, "Deposit",  "y"],
                ["ee", "SD", 13.2, "Interest", "y"],
                ["ff", "SD", 13.2, "Balance",  "y"],
                ["gg", "SD", 13.2, "Admin",  "y"]]
            RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
                heads=head, cols=cols, gtots=["dd", "ee", "ff", "gg"],
                ttype="D", repprt=self.df.repprt, repeml=self.df.repeml,
                fromad=self.fromad)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
