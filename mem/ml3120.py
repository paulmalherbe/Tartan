"""
SYNOPSIS
    Member's Status Summary.

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

from TartanClasses import CreateChart, TartanDialog, Sql
from tartanFunctions import dateDiff, mthendDate

class ml3120(object):
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
            "A": ["Active",0,0,0,0,0,0,0,0,0,0,0,0],
            "D": ["Deceased",0,0,0,0,0,0,0,0,0,0,0,0],
            "I": ["Inactive",0,0,0,0,0,0,0,0,0,0,0,0],
            "R": ["Resigned",0,0,0,0,0,0,0,0,0,0,0,0],
            "S": ["Suspended",0,0,0,0,0,0,0,0,0,0,0,0],
            "X": ["Defaulted",0,0,0,0,0,0,0,0,0,0,0,0]}
        return True

    def mainProcess(self):
        fld = (
            (("T",0,0,0),"ID2",7,"Starting Period","",
                "","N",self.doStartPer,None,None,None),
            (("T",0,1,0),"ID2",7,"Ending   Period","",
                "","N",self.doEndPer,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doStartPer(self, frt, pag, r, c, p, i, w):
        self.sdate = (w * 100) + 1
        y = int(w / 100)
        m = (w % 100) + 11
        if m > 12:
            y += 1
            m -= 12
        self.df.loadEntry(frt, pag, p+1, ((y * 100) + m))

    def doEndPer(self, frt, pag, r, c, p, i, w):
        self.edate = mthendDate((w * 100) + 1)
        if dateDiff(self.sdate, self.edate, "months") > 11:
            return "More than 12 month period"

    def doEnd(self):
        self.df.closeProcess()
        rec = self.sql.getRec("memsta", cols=["mls_status",
            "mls_date/100 as date", "count(*)"], where=[("mls_date",
            "between", self.sdate, self.edate)], group="mls_status, date")
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
            mth = r[1] % 100
            self.desc[r[0]][lookup[mth]] = r[2]
        achart = []
        for s in self.desc:
            achart.append([s] + self.desc[s])
        CreateChart(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            [int(self.sdate / 100), int(self.edate / 100)],
            [[self.opts["conam"], "Status Summary"], "Count"], achart, achart)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
