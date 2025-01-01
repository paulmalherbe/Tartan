"""
SYNOPSIS
    General Ledger Imported Bank Statements..

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

from TartanClasses import RepPrt, Sql, TartanDialog

class gl3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "genmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Imported Bank Statements (%s)" % self.__class__.__name__)
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
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

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
        if self.unall == "Y":
            hds = ["General Ledger Bank Statement Records (Unallocated Only)"]
        else:
            hds = ["General Ledger Bank Statement Records (All)"]
        des = "Bank Account Number %s %s" % (self.acnod, self.name)
        if self.start:
            des = "%s from %s" % (des, self.df.t_disp[0][0][1])
        if self.to:
            des = "%s to %s" % (des, self.df.t_disp[0][0][2])
        hds.append(des)
        col = ["grt_date", "grt_memo", "grt_refno", "grt_payee",
            "grt_flag", "grt_amount"]
        whr = [
            ("grt_cono", "=", self.opts["conum"]),
            ("grt_acno", "=", self.acnow)]
        if self.start:
            whr.append(("grt_date", ">=", self.start))
        if self.to:
            whr.append(("grt_date", "<=", self.to))
        if self.unall == "Y":
            whr.append(("grt_flag", "=", "N"))
        tab = ["genrct"]
        tot = ["grt_amount"]
        odr = "grt_date, grt_refno"
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=self.__class__.__name__, tables=tab,
            heads=hds, cols=col, where=whr, order=odr, gtots=tot,
            repprt=self.df.repprt, repeml=self.df.repeml)
        self.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
