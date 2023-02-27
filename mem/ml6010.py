"""
SYNOPSIS
    Members Ledger Change Transaction Allocations.

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
from TartanClasses import AgeTrans, Sql, TartanDialog, tk
from tartanFunctions import copyList, getTrn

class ml6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["memmst", "memtrn", "memage"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        self.agevar = tk.BooleanVar()
        self.agevar.set(False)
        return True

    def dataHeader(self):
        mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": (
                ("mlm_memno", "", 0, "Mem-No"),
                ("mlm_oldno", "", 0, "Old-No"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")),
            "where": [("mlm_cono", "=", self.opts["conum"])],
            "order": "mlm_surname, mlm_names",
            "sort": False}
        fld = (
            (("T",0,0,0),"IUI",6,"Mem-No","Member Number",
                "","Y",self.doMemNo,mlm,None,("notblank",)),
            (("T",0,0,0),"ONA",30,"Member"))
        tnd = ((self.endTop, "n"),)
        txt = (self.exitTop,)
        self.but = (
            ("Normal", None, self.doReAgeNormal, 0, None, None,
                "Only Show Unallocated Transactions"),
            ("History", None, self.doReAgeHistory, 0, None, None,
                "Show All Transactions, Including Already Allocated"))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=self.but)

    def doMemNo(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("memmst", cols=["mlm_title",
            "mlm_initial", "mlm_surname"], where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not acc:
            return "Invalid Member Number"
        self.memno = w
        self.key = None
        name = "%s, %s %s" % (acc[2], acc[0], acc[1])
        self.df.loadEntry(frt, pag, p+1, data=name)
        self.opts["mf"].updateStatus("Select Routine")
        for b in range(2):
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
        for b in range(2):
            wid = getattr(self.df, "B%s" % b)
            self.df.setWidget(wid, "disabled")
        col = ["mlt_refno","mlt_type","mlt_curdt","mlt_tramt","paid","balance"]
        whr = [
            ("mlt_cono", "=", self.opts["conum"]),
            ("mlt_memno", "=", self.memno)]
        if self.key == "normal":
            dtc, recs = getTrn(self.opts["mf"].dbm, "mem", whr=whr, zer="N")
        else:
            dtc, recs = getTrn(self.opts["mf"].dbm, "mem", whr=whr)
        if recs:
            data = []
            for rec in recs:
                dat = []
                for c in col:
                    dat.append(rec[dtc.index(c)])
                data.append(dat)
            age = AgeTrans(self.opts["mf"], "mem", data, 0, xits=False)
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
                        w.extend([("mlt_type", "=", tr[2]),
                            ("mlt_refno", "=", tr[1])])
                        self.sql.insRec("memage", data=[self.opts["conum"],
                            self.memno, tr[1], tr[0], self.curdt, tr[1], tr[0],
                            tr[6], 0])
            else:
                self.key = "cancel"
        self.agevar.set(False)

    def endTop(self):
        self.df.focusField("T", 0, 1)

    def exitTop(self):
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
