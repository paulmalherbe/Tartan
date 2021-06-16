"""
SYNOPSIS
    Creditors Ledger Change Age Allocations.

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
from TartanClasses import AgeTrans, GetCtl, ProgressBar, Sql, TartanDialog, tk
from tartanFunctions import copyList, doAutoAge, getTrn

class cr6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in opts:
                self.curdt = opts["args"][0]
                for self.acno in opts["args"][1]:
                    self.doReAgeAuto()
                self.opts["mf"].dbm.commitDbase()
            else:
                self.dataHeader()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn", "crsage"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        if "args" not in self.opts:
            self.agevar = tk.BooleanVar()
            self.agevar.set(False)
        return True

    def dataHeader(self):
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")]}
        fld = [
            [["T",0,0,0],"ID2",7,"Period","Current Financial Period",
                self.curdt,"N",self.doCurdt,None,None,("efld",)],
            [["T",0,1,0],"INA",7,"Acc-Num","Account Number",
                "","N",self.doAccno,crm,None,("notblank",)],
            [["T",0,1,0],"ONA",30,"Name"]]
        tnd = ((self.endTop, "n"),)
        txt = (self.exitTop,)
        self.but = (
            ("Normal", None, self.doReAgeNormal, 0, None, None,
                "Only Show Unallocated Transactions"),
            ("History", None, self.doReAgeHistory, 0, None, None,
                "Show All Transactions, Including Already Allocated"),
            ("Automatic", None, self.doReAgeAuto, 0, None, None,
                "Automatically Re-Age the Account Based on Date"))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=self.but)

    def doCurdt(self, frt, pag, r, c, p, i, w):
        self.curdt = w

    def doAccno(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", cols=["crm_name", "crm_stat"],
            where=[("crm_cono", "=", self.opts["conum"]), ("crm_acno", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[1] == "X":
            return "Invalid Account, Redundant"
        self.acno = w
        self.key = None
        self.df.loadEntry("T", pag, p+1, data=acc[0])
        self.opts["mf"].updateStatus("Select Routine")
        for b in range(3):
            wid = getattr(self.df, "B%s" % b)
            self.df.setWidget(wid, "normal")
        self.df.setWidget(self.df.B0, "focus")
        self.agevar.set(True)
        self.df.mstFrame.wait_variable(self.agevar)
        if self.key in ("normal", "history"):
            return "nd"
        elif self.key == "cancel":
            return "nc"

    def doReAgeNormal(self):
        self.key = "normal"
        self.doReAge()

    def doReAgeHistory(self):
        self.key = "history"
        self.doReAge()

    def doReAge(self):
        self.opts["mf"].updateStatus("")
        for b in range(3):
            wid = getattr(self.df, "B%s" % b)
            self.df.setWidget(wid, "disabled")
        col = ["crt_trdt","crt_ref1","crt_type","crt_tramt","paid","balance"]
        whr = [
            ("crt_cono", "=", self.opts["conum"]),
            ("crt_acno", "=", self.acno)]
        if self.key == "normal":
            dtc, recs = getTrn(self.opts["mf"].dbm, "crs", whr=whr, zer="N")
        else:
            dtc, recs = getTrn(self.opts["mf"].dbm, "crs", whr=whr)
        if recs:
            data = []
            for rec in recs:
                dat = []
                for c in col:
                    dat.append(rec[dtc.index(c)])
                data.append(dat)
            age = AgeTrans(self.opts["mf"], "crs", data, 0, xits=False)
            if not age.ccl and age.data:
                if age.total.work:
                    while not age.ccl:
                        age.doAllocate()
                        if age.ccl or not age.total.work:
                            break
                if age.ccl:
                    self.key = "cancel"
                    age.data = []
                for tr in age.data:
                    if tr[6]:
                        w = copyList(whr)
                        w.extend([("crt_type", "=", tr[2]),
                            ("crt_ref1", "=", tr[1])])
                        self.sql.insRec("crsage", data=[self.opts["conum"],
                            self.acno, tr[2], tr[1], self.curdt, tr[2], tr[1],
                            tr[6], 0])
            else:
                self.key = "cancel"
        self.agevar.set(False)

    def doReAgeAuto(self):
        self.key = "normal"
        if "args" not in self.opts:
            for b in range(3):
                wid = getattr(self.df, "B%s" % b)
                self.df.setWidget(wid, "disabled")
            self.opts["mf"].updateStatus("Re-Ageing .... Please Wait!")
            self.df.setWidget(self.df.mstFrame, state="hide")
            txt = "Re-Allocating ... Please Wait"
            pb = ProgressBar(self.opts["mf"].body, typ=("G", txt))
            doAutoAge(self.opts["mf"].dbm, "crs", self.opts["conum"],
                acno=self.acno, pbar=pb)
            pb.closeProgress()
            self.df.setWidget(self.df.mstFrame, state="show")
            self.agevar.set(False)
        else:
            doAutoAge(self.opts["mf"].dbm, "crs", self.opts["conum"],
                acno=self.acno, pbar=None)

    def endTop(self):
        self.df.clearEntry("T", 0, 2)
        self.df.clearEntry("T", 0, 3)
        self.df.focusField("T", 0, 2)

    def exitTop(self):
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
