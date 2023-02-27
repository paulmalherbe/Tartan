"""
SYNOPSIS
    Earnings and Deduction Codes Listing.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import showError

class wgc320(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "wagedc",
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
        r1s = (("Earnings","E"),("Deductions","D"),("Both","B"))
        r2s = (("Code Number","N"),("Description","D"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Report Type     ","Report Type",
                "E","Y",self.doType,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Sort Order      ","Sort Order",
                "N","Y",self.doSort,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("N","V"), mail=("Y","N"))

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtyp = w

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        self.df.closeProcess()
        if self.sort == "N":
            odr = "ced_type desc, ced_code"
        else:
            odr = "ced_type desc, ced_desc"
        if self.rtyp in ("E", "D"):
            recs = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"]), ("ced_type", "=", self.rtyp)], order=odr)
        else:
            recs = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"])], order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        else:
            self.printReport(recs)
        self.opts["mf"].closeLoop()

    def printReport(self, recs):
        descs = ["", "Type", "Code Number", "Description", "Fixed or Variable",
                "EMPLOYEE Rate or Amount", "         Based On",
                "         Amount",   "         Limit",
                "         G/L Cono", "         G/L Number",
                "         Earnings Type",
                "EMPLOYER Rate or Amount", "         Based On",
                "         Amount", "         Limit", "         G/L Cono",
                "         G/L Number", "Tax Code", "Taxable Portion",
                "Receiver of Revenue Code", "Include in Union Report",
                "Must Pay", "Balance Number", "Hourly Limit",
                "Monthly Deduction", "UIF Portion", "SDL Portion"]
        tables = []
        for rec in recs:
            for y in range(1, len(recs[0]) - 1):
                lin = []
                lin.append("")
                lin.append(descs[y])
                lin.append(rec[y])
                tables.append(lin)
        if self.rtyp == "E":
            typ = "Earnings"
        elif self.rtyp == "D":
            typ = "Deductions"
        else:
            typ = "Earnings and Deductions"
        heads = ["%s Codes Listing" % typ]
        cols = [["a","NA",15.0," "],
                ["b","RW",30.0,"Field Name"],
                ["c","NA",30.0,"Details"]]
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=cols, conum=self.opts["conum"], ttype="D",
            conam=self.opts["conam"], lines=(len(descs) - 1),
            repprt=self.df.repprt, repeml=self.df.repeml,
            fromad=self.fromad)
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
