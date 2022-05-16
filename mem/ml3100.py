"""
SYNOPSIS
    Members Ledger Birthday Report.

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

import time
from TartanClasses import GetCtl, RepPrt, Sql, SplashScreen, TartanDialog

class ml3100(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "memmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        mc = GetCtl(self.opts["mf"])
        memctl = mc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.fromad = memctl["mcm_emadd"]
        t = time.localtime()
        self.frdt = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.todt = self.frdt
        return True

    def mainProcess(self):
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "mcc_type", 0]],
            "order": "mcc_code",
            "size": (400, 600)}
        r1s = (
            ("All", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        r2s = (("Number", "N"), ("Surname", "M"), ("Mth/Day", "D"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Category","",
                "A","Y",self.doCat,None,None,None),
            (("T",0,1,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),("IRB",r2s),0,"Sort Order","",
                "M","Y",self.doSort,None,None,None),
            (("T",0,3,0),"ID1",10,"From Date","",
                self.frdt,"Y",self.doDate,None,None,("efld",)),
            (("T",0,4,0),"ID1",10,"To   Date","",
                self.todt,"Y",self.doDate,None,None,("efld",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.cat = ""
            self.cod = ""
            self.df.loadEntry(frt, pag, p+2, data="All Categories and Codes")
            return "sk2"
        self.cat = w

    def doCod(self, frt, pag, r, c, p, i, w):
        self.cod = w
        if self.cod:
            self.chk = self.sql.getRec("memctc", cols=["mcc_desc"],
                where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
                self.cat), ("mcc_code", "=", self.cod)], limit=1)
            if not self.chk:
                return "Invalid Category Code"
            self.df.loadEntry(frt, pag, p+1, data=self.chk[0])
        else:
            self.df.loadEntry(frt, pag, p+1, "All Codes")

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doDate(self, frt, pag, r, c, p, i, w):
        if i == 4:
            self.frdt = w
        elif w < self.frdt:
            return "Invalid To Date, Before From Date"
        else:
            self.todt = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["memmst"]
        col = [
            "mlm_memno",
            "mlm_surname",
            "mlm_names",
            "mlm_dob%10000 as date"]
        whr = [
            ("mlm_cono", "=", self.opts["conum"]),
            ("mlm_state", "=", "A"),
            ("date", "between", self.frdt % 10000, self.todt % 10000)]
        if self.cat:
            tab.append("memcat")
            whr.append(("mlc_cono=mlm_cono",))
            whr.append(("mlc_memno=mlm_memno",))
            whr.append(("mlc_type", "=", self.cat))
            if self.cod:
                whr.append(("mlc_code", "=", self.cod))
        if self.sort == "N":
            odr = "mlm_memno"
        elif self.sort == "M":
            odr = "mlm_surname"
        else:
            odr = "date"
        sp = SplashScreen(self.opts["mf"].body,
            "Preparing Report ... Please Wait")
        recs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        sp.closeSplash()
        if not recs:
            self.opts["mf"].closeLoop()
            return
        name = self.__class__.__name__
        head = ["Members Birthday Report"]
        cols = [
            ["a", "NA",  7, "Mem-No", "y"],
            ["b", "NA", 50, "Surname", "y"],
            ["c", "NA", 50, "Names",  "y"],
            ["d", "DM", 5, "Birthday", "y"]]
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=name, tables=recs, heads=head,
            cols=cols, ttype="D", repprt=self.df.repprt,
            repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
