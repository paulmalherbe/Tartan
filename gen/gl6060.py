"""
SYNOPSIS
    General Ledger - Delete Imported Bank Statements.

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

from TartanClasses import Sql, TartanDialog

class gl6060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "genmst", "genrct"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Delete Imported Bank Statements (%s)" % self.__class__.__name__)
        glm = {
            "stype": "R",
            "tables": ("ctlctl", "genmst"),
            "cols": (
                ("ctl_conacc", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [
                ("ctl_cono", "=", self.opts["conum"]),
                ("ctl_code", "like", "bank_%"),
                ("glm_cono=ctl_cono",),
                ("glm_acno=ctl_conacc",)]}
        r1s = (("Yes","Y"), ("No","N"))
        fld = (
            (("T",0,0,0),"IUI",7,"Bank Account","",
                "","Y",self.doBankAcc,glm,None,("efld",)),
            (("T",0,1,0),"Id1",10,"From Date","From Date (0 for Beginning)",
                0,"Y",self.doFrom,None,None,("efld",)),
            (("T",0,2,0),"Id1",10,"To   Date","To Date (0 for End)",
                0,"Y",self.doTo,None,None,("efld",)),
            (("T",0,3,0),("IRB",r1s),0,"Unallocated Only","",
                "Y","Y",self.doUnall,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doBankAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["ctlctl", "genmst"], cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=", w),
            ("ctl_cono=glm_cono",), ("ctl_conacc=glm_acno",), ("ctl_code",
            "like", "bank_%")], limit=1)
        if not acc:
            return "Invalid Bank Account Number"
        self.acnow = w
        self.acnod = self.df.t_disp[pag][r][p]
        self.name = acc[0]

    def doFrom(self, frt, pag, r, c, p, i, w):
        self.start = w

    def doTo(self, frt, pag, r, c, p, i, w):
        if w and self.start and w < self.start:
            return "Invalid Date, Earlier than From Date"
        self.to = w

    def doUnall(self, frt, pag, r, c, p, i, w):
        self.unall = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [
            ("grt_cono", "=", self.opts["conum"]),
            ("grt_acno", "=", self.acnow)]
        if self.start:
            whr.append(("grt_date", ">=", self.start))
        if self.to:
            whr.append(("grt_date", "<=", self.to))
        if self.unall == "Y":
            whr.append(("grt_flag", "=", "N"))
        cnt = self.sql.getRec("genrct", cols=["count(*)"], where=whr,
            limit=1)
        self.sql.delRec("genrct", where=whr)
        self.opts["mf"].dbm.commitDbase(ask=True,
            mess="A Total of %s Records were Deleted" % cnt[0],
            default="no")
        self.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
