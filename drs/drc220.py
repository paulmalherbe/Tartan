"""
SYNOPSIS
    Debtors Chainstores Listing.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import showError

class drc220(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "drschn",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        if drsctl["ctd_chain"] == "N":
            showError(self.opts["mf"].body, "Error",
                "Chain Stores are Not Enabled")
            return
        self.fromad = drsctl["ctd_emadd"]
        return True

    def mainProcess(self):
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=[], tend=tnd,
            txit=txt, view=("Y","V"), mail=("Y","N"))

    def doEnd(self):
        self.df.closeProcess()
        heads = ["Debtor's Chainstores Master Listing"]
        cols = []
        dics = self.sql.drschn_dic
        for col in self.sql.drschn_col:
            if col in ("chm_cono","chm_add1","chm_add2","chm_add3","chm_pcod"):
                continue
            dat = [col, dics[col][2], dics[col][3], dics[col][4]]
            if col == "chm_email":
                dat[2] = 30
            cols.append(dat)
        RepPrt(self.opts["mf"], name=self.__class__.__name__,
            tables=["drschn"], heads=heads, cols=cols,
            where=[("chm_cono", "=", self.opts["conum"])],
            conum=self.opts["conum"], conam=self.opts["conam"],
            repprt=self.df.repprt, repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
