"""
SYNOPSIS
    Purchase Order Cancellations.

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

import time
from TartanClasses import GetCtl, Sql, TartanDialog

class st6040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "strloc", "strpom",
            "strpot"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Purchase Order Cancellations (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        orm = {
            "stype": "R",
            "tables": ("strpom",),
            "cols": (
                ("pom_ordno", "", 0, "OrderNo"),
                ("pom_acno", "", 0, "Crs-Num"),
                ("pom_date", "", 0, "Order-Date")),
            "where": [
                ("pom_cono", "=", self.opts["conum"]),
                ("pom_delno", "=", "")],
            "whera": [("T", "pom_loc", 0)],
            "order": "pom_ordno"}
        if self.locs == "N":
            self.locw = "1"
            fld = [
                (("T",0,0,0),"OUA",1,"Location")]
        else:
            fld = [
                (("T",0,0,0),"IUA",1,"Location","",
                    "1","Y",self.doLoc,loc,None,None)]
        fld.extend([
            (("T",0,1,0),"Id1",10,"Orders Older Than","",
                "","Y",self.doOld,orm,None,None),
            (("T",0,2,0),"IUI",9,"From Order Number","",
                "","Y",self.doOrd,orm,None,None),
            (("T",0,3,0),"IUI",9,"To   Order Number","",
                "","Y",self.doOrd,orm,None,None)])
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)
        if self.locs == "N":
            self.df.loadEntry("T", 0, 0, data=self.locw)

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]),
            ("srl_loc", "=", w)], limit=1)
        if not acc:
            return "Invalid Location"
        self.locw = w

    def doOld(self, frt, pag, r, c, p, i, w):
        self.oldr = w
        if self.oldr:
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            return "nd"

    def doOrd(self, frt, pag, r, c, p, i, w):
        if p == 3 and w < self.ord1:
            return "Invalid, Last Order less than First Order"
        acc = self.sql.getRec("strpom", where=[("pom_cono", "=",
            self.opts["conum"]), ("pom_ordno", "=", w), ("pom_loc", "=",
            self.locw), ("pom_delno", "=", "")], limit=1)
        if not acc:
            return "Invalid Order Number"
        if p == 2:
            self.ord1 = w
        else:
            self.ord2 = w

    def doEnd(self):
        self.df.closeProcess()
        if self.oldr:
            whr = [
                ("pom_cono", "=", self.opts["conum"]),
                ("pom_loc", "=", self.locw),
                ("pom_date", "<", self.oldr),
                ("pom_delno", "<>", "cancel"),
                ("pom_deldt", "=", 0)]
        else:
            whr = [
                ("pom_cono", "=", self.opts["conum"]),
                ("pom_loc", "=", self.locw),
                ("pom_ordno", ">=", self.ord1),
                ("pom_ordno", "<=", self.ord2),
                ("pom_delno", "<>", "cancel"),
                ("pom_deldt", "=", 0)]
        self.sql.updRec("strpom", cols=["pom_delno"], data=["cancel"],
            where=whr)
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
