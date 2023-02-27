"""
SYNOPSIS
    Bookings's Occupancy by Status Summary.

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

from TartanClasses import CreateChart, TartanDialog, Sql
from tartanFunctions import dateDiff, mthendDate

class bk3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "memsta",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.desc = {
            "Q": ["Query",0,0,0,0,0,0,0,0,0,0,0,0],
            "S": ["Settled",0,0,0,0,0,0,0,0,0,0,0,0],
            "C": ["Confirmed",0,0,0,0,0,0,0,0,0,0,0,0],
            "X": ["Cancelled",0,0,0,0,0,0,0,0,0,0,0,0],
            "T": ["QSC Total",0,0,0,0,0,0,0,0,0,0,0,0]}
        return True

    def mainProcess(self):
        r1s = (("Beds","B"), ("Value","V"))
        fld = (
            (("T",0,0,0),"ID2",7,"Starting Period","",
                "","N",self.doStartPer,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"Ending   Period","",
                "","N",self.doEndPer,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Report by","",
                "B","N",self.doRepTyp,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doStartPer(self, frt, pag, r, c, p, i, w):
        self.sper = w
        self.sdate = (w * 100) + 1
        y = int(w / 100)
        m = (w % 100) + 11
        if m > 12:
            y += 1
            m -= 12
        self.df.loadEntry(frt, pag, p+1, ((y * 100) + m))

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if w < self.sper:
            return "Invalid Period, before Start"
        self.edate = mthendDate((w * 100) + 1)
        if dateDiff(self.sdate, self.edate, "months") > 11:
            return "More than 12 month period"

    def doRepTyp(self, frt, pag, r, c, p, i, w):
        self.reptyp = w

    def doEnd(self):
        self.df.closeProcess()
        if self.reptyp == "B":
            col = ["bkm_state", "bkm_guests", "bkm_arrive", "bkm_depart"]
            whr = [("bkm_btype", "=", "A"), ("bkm_arrive", ">=", self.sdate,
                "and", "bkm_depart", "<=", self.edate)]
        else:
            col = ["bkm_state", "bkm_value", "bkm_arrive", "bkm_depart"]
            whr = [("bkm_btype", "=", "A"), ("bkm_arrive", "between",
                self.sdate, self.edate, "or", "bkm_depart", "between",
                self.sdate, self.edate)]
        rec = self.sql.getRec("bkmmst", cols=col, where=whr)
        num = 1
        lookup = {}
        mth = int(self.sdate / 100) % 100
        end = int(self.edate / 100) % 100
        lookup[mth] = num
        while mth != end:
            mth += 1
            if mth > 12:
                mth = 1
            num += 1
            lookup[mth] = num
        for r in rec:
            if self.reptyp == "B":
                if int(r[2] / 100) == int(r[3] / 100):
                    days = dateDiff(r[2], r[3], "days")
                    mth = int(r[2] / 100) % 100
                    self.desc[r[0]][lookup[mth]] += (days * r[1])
                    if r[0] == "X":
                        continue
                    self.desc["T"][lookup[mth]] += (days * r[1])
                else:
                    mnd = mthendDate(r[2])
                    days = dateDiff(r[2], mnd, "days")
                    mth = int(r[2] / 100) % 100
                    self.desc[r[0]][lookup[mth]] += (days * r[1])
                    self.desc["T"][lookup[mth]] += (days * r[1])
                    mth = int(r[3] / 100) % 100
                    days = dateDiff(((int(r[3] / 100) * 100) + 1), r[3], "days")
                    self.desc[r[0]][lookup[mth]] += (days * r[1])
                    if r[0] == "X":
                        continue
                    self.desc["T"][lookup[mth]] += (days * r[1])
            else:
                mth = int(r[2] / 100) % 100
                self.desc[r[0]][lookup[mth]] += r[1]
                if r[0] == "X":
                    continue
                self.desc["T"][lookup[mth]] += r[1]
        achart = []
        mchart = []
        for s in self.desc:
            mchart.append([s] + self.desc[s])
            if s in ("T", "X"):
                continue
            achart.append([s] + self.desc[s])
        if self.reptyp == "B":
            typ = "Beds"
        else:
            typ = "Value"
        CreateChart(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            [int(self.sdate / 100), int(self.edate / 100)],
            [[self.opts["conam"], "Status Summary"], typ], achart, mchart)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
