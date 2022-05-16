"""
SYNOPSIS
    Debtors Reps Listing.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog

class drc320(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ctlrep",
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
        r1s = (("Number","N"),("Name","A"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),)
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        self.df.closeProcess()
        tables = ["ctlrep"]
        heads = ["Salemen's Master Listing"]
        cols = []
        dics = self.sql.ctlrep_dic
        for col in self.sql.ctlrep_col:
            if col in ("rep_cono",):
                continue
            dat = [col, dics[col][2], dics[col][3], dics[col][4]]
            cols.append(dat)
        if self.sort == "N":
            odr = "rep_code"
        else:
            odr = "rep_name, rep_code"
        whr = [("rep_cono", "=", self.opts["conum"])]
        opts = "%-5s%-6s" % ("Sort-", self.sort)
        RepPrt(self.opts["mf"], tables=tables, heads=heads, cols=cols,
            order=odr, opts=opts, where=whr, conum=self.opts["conum"],
            conam=self.opts["conam"], repprt=self.df.repprt,
            repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
