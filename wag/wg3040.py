"""
SYNOPSIS
    Salaries and Wages Earnings and Deduction Analysis.

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

from TartanClasses import ASD, GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import showError

class wg3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagmst", "wagedc", "wagtf2"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        return True

    def mainProcess(self):
        dte = {
            "stype": "R",
            "tables": ("wagtf1",),
            "cols": (("wt1_date", "", 0, "Date"),),
            "where": [("wt1_cono", "=", self.opts["conum"])],
            "group": "wt1_date",
            "order": "wt1_date"}
        r1s = (("Earnings","E"),("Deductions","D"),("Both","B"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"ID1",10,"Start Date","",
                "","N",self.doSDate,dte,None,("efld",)),
            (("T",0,1,0),"ID1",10,"End   Date","",
                "","N",self.doEDate,dte,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),10,"Type","",
                "B","N",self.doType,None,None,None),
            (("T",0,3,0),("IRB",r2s),10,"Code per Page","New Page per Code",
                "N","N",self.doNewPg,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSDate(self, frt, pag, r, c, p, i, w):
        self.sdatew = w
        self.sdated = self.df.t_disp[0][0][0]
        self.df.topf[0][1][5] = self.sdatew

    def doEDate(self, frt, pag, r, c, p, i, w):
        if w < self.sdatew:
            return "Invalid End Date"
        self.edatew = w
        self.edated = self.df.t_disp[0][0][1]

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtyp = w

    def doNewPg(self, frt, pag, r, c, p, i, w):
        self.newpg = w

    def doEnd(self):
        self.df.closeProcess()
        col = ["wt2_type", "wt2_code", "ced_desc", "wt2_empno", "wgm_sname",
            "wgm_fname", "round(sum(wt2_eamt),2)", "round(sum(wt2_ramt),2)"]
        whr = [("wt2_cono", "=", self.opts["conum"])]
        if self.sdatew == self.edatew:
            whr.append(("wt2_date", "=", self.edatew))
        else:
            whr.append(("wt2_date", "between", self.sdatew, self.edatew))
        if self.rtyp != "B":
            whr.append(("wt2_type", "=", self.rtyp))
        whr.extend([("wgm_cono=wt2_cono",), ("ced_cono=wt2_cono",),
            ("ced_type=wt2_type",), ("ced_code=wt2_code",),
            ("wgm_empno=wt2_empno",)])
        grp = "wt2_type, wt2_code, ced_desc, wt2_empno, wgm_sname, wgm_fname"
        if self.sdatew == self.edatew:
            grp = "%s, wt2_date" % grp
        odr = "wt2_type desc, wt2_code asc, wt2_empno"
        recs = self.sql.getRec(tables=["wagmst", "wagedc", "wagtf2"], cols=col,
            where=whr, group=grp, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Transactions for the Period")
        else:
            self.doPrintReport(recs)
        self.closeProcess()

    def doPrintReport(self, recs):
        name = self.__class__.__name__
        tables = []
        for col in recs:
            if col[0] == "D":
                col[6] = float(ASD(0) - ASD(col[6]))
                col[7] = float(ASD(0) - ASD(col[7]))
            tables.append(col)
        if self.rtyp == "D":
            heads = ["Salaries and Wages Deductions Report"]
        elif self.rtyp == "E":
            heads = ["Salaries and Wages Earnings Report"]
        else:
            heads = ["Salaries and Wages Earnings and Deductions Report"]
        opts = "From %s to %s" % (self.sdated, self.edated)
        cols = [
            ["wt2_type", "UA", 1, "T", "N"],
            ["wt2_code", "UI", 3, "Cod", "N"],
            ["ced_desc", "NA", 30, "Description", "N"],
            ["wt2_empno", "UI", 5, "EmpNo", "Y"],
            ["wgm_sname", "NA", 30, "Surname", "Y"],
            ["wgm_fname", "NA", 30, "First Names", "Y"]]
        cols.extend([
            ["wt2_eamt", "SD", 13.2, "Employee-Amt", "Y"],
            ["wt2_ramt", "SD", 13.2, "Employer-Amt", "Y"]])
        stots = [["ced_desc", "Total", "%s" % self.newpg]]
        gtots = ["wt2_eamt", "wt2_ramt"]
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=name, tables=tables, heads=heads,
            opts=opts, cols=cols, stots=stots, gtots=gtots,
            conum=self.opts["conum"], conam=self.opts["conam"], ttype="D",
            repprt=self.df.repprt, repeml=self.df.repeml, fromad=self.fromad)
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
