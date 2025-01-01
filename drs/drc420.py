"""
SYNOPSIS
    Debtors Delivery Addresses Listing.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import showError

class drc420(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "drsdel",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.fromad = drsctl["ctd_emadd"]
        return True

    def mainProcess(self):
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=[], tend=tnd,
            txit=txt, view=("Y","V"), mail=("Y","N"))

    def doEnd(self):
        recs = self.sql.getRec("drsdel", order="del_code")
        if not recs:
            showError(self.opts["mf"].body, "Error", "No Available Records")
            self.closeProcess()
        else:
            self.printReport(recs)

    def printReport(self, recs):
        self.df.closeProcess()
        tables = []
        for rec in recs:
            lin = []
            lin.append(rec[0])
            lin.append(rec[1])
            lin.append(rec[2])
            tables.append(lin)
            lin = []
            if rec[3] or rec[4]:
                lin.append("")
                lin.append(rec[3])
                lin.append(rec[4])
                tables.append(lin)
            lin = []
            for _ in range(0, 3):
                lin.append("")
            tables.append(lin)
        heads = ["Debtors Delivery Address Listing"]
        cols = [["a","NA",7.0,"Add-Cod"],
                ["b","NA",30.0,"Address-Line"],
                ["c","NA",30.0,"Address-Line"]]
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=cols, conum=self.opts["conum"], ttype="D",
            conam=self.opts["conam"], repprt=self.df.repprt,
            repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
