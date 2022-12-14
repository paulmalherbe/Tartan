"""
SYNOPSIS
    Change Financial Year End.

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

from TartanClasses import SplashScreen, Sql, TartanDialog
from tartanFunctions import callModule, dateDiff, getPeriods, mthendDate
from tartanFunctions import showError

class msy020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawScreen()
            self.opts["mf"].startLoop()

    def setVariables(self):
        if self.opts["period"][0] == 0:
            showError(self.opts["mf"].body, "Year-End Error",
                "Period 0 Cannot be Changed, Change Period 1 Instead!")
            return
        self.sql = Sql(self.opts["mf"].dbm, "ctlynd",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.pers = self.sql.getRec("ctlynd", where=[("cye_cono", "=",
            self.opts["conum"]), ("cye_period", ">=", self.opts["period"][0])],
            order="cye_period")
        if self.pers[0][self.sql.ctlynd_col.index("cye_final")] == "Y":
            showError(self.opts["mf"].body, "Year-End Error",
                "This Period Has Already Been Finalised")
            return
        self.s_per = self.pers[0][self.sql.ctlynd_col.index("cye_start")]
        self.e_per = self.pers[0][self.sql.ctlynd_col.index("cye_end")]
        self.m_per = self.getEndDate(self.s_per)
        self.l_per = self.pers[-1][self.sql.ctlynd_col.index("cye_period")]
        if self.opts["period"][0] == 1 and self.l_per > 1:
            showError(self.opts["mf"].body, "Year-End Error",
                "Period 1 Cannot be Changed as Periods > 1 Exist!")
            return
        return True

    def getEndDate(self, date):
        yr = int(date / 10000) + 1
        mt = (int(date / 100) % 100) - 1
        if not mt:
            yr -= 1
            mt = 12
        return mthendDate(((yr * 10000) + (mt * 100) + 1))

    def getStartDate(self, date):
        yr = int(date / 10000)
        mt = (int(date / 100) % 100) + 1
        if mt > 12:
            yr += 1
            mt = 1
        return ((yr * 10000) + (mt * 100) + 1)

    def drawScreen(self):
        fld = [
            [("T",0,0,0),"I@cye_start",0,"","",
                self.s_per,"N",self.doStartPer,None,None,("efld",)],
            (("T",0,1,0),"I@cye_end",0,"","",
                self.e_per,"N",self.doEndPer,None,None,("efld",))]
        if self.opts["period"][0] != 1:
            fld[0][1] = "O@cye_start"
            fld[0][7] = None
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, focus=True)
        if self.opts["period"][0] != 1:
            self.df.loadEntry("T", 0, 0, data=self.s_per)

    def doStartPer(self, frt, pag, r, c, p, i, w):
        y = int(w / 10000) - 1
        m = int((w % 10000) / 100)
        if m == 2:
            if not y % 4:
                d = 29
            else:
                d = 28
        else:
            d = w % 100
        self.s0 = (y*10000) + (m*100) + d
        self.s_per = w

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if w <= self.s_per:
            return "Invalid Date, Before Start"
        if dateDiff(self.s_per, w, "months") > 14:
            return "Invalid Date, More than 15 Months"
        y = int(w / 10000) - 1
        m = int((w % 10000) / 100)
        if m == 2:
            if not y % 4:
                d = 29
            else:
                d = 28
        else:
            d = w % 100
        self.e0 = (y * 10000) + (m * 100) + d
        self.e_per = w

    def doEnd(self):
        self.df.closeProcess()
        if self.opts["period"][0] == 1:
            self.sql.updRec("ctlynd", cols=["cye_start", "cye_end"],
                data=[self.s0, self.e0], where=[("cye_cono", "=",
                self.opts["conum"]), ("cye_period", "=", 0)])
        for per in self.pers:
            num = per[self.sql.ctlynd_col.index("cye_period")]
            if num == self.opts["period"][0]:
                self.start = self.s_per
                self.end = self.e_per
            else:
                self.start = self.getStartDate(self.end)
                self.end = self.getEndDate(self.start)
            self.sql.updRec("ctlynd", cols=["cye_start", "cye_end"],
                data=[self.start, self.end], where=[("cye_cono", "=",
                self.opts["conum"]), ("cye_period", "=", num)])
        spl = SplashScreen(self.opts["mf"].body,
            text="Running Year End Routine for Period %s" % num)
        per = getPeriods(self.opts["mf"], self.opts["conum"], num - 1)
        per = (num - 1, (per[0].work, per[0].disp), (per[1].work, per[1].disp))
        callModule(self.opts["mf"], None, "msy010", coy=(self.opts["conum"],
            self.opts["conam"]), period=per, user=self.opts["capnm"], args="N")
        spl.closeSplash()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
