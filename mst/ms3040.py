"""
SYNOPSIS
    Masterfile Changes Log.

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
from TartanClasses import CCD, RepPrt, TartanDialog
from tartanWork import tabdic

class ms3040(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]

    def mainProcess(self):
        tab = {
            "stype": "R",
            "tables": ("chglog",),
            "cols": (("chg_tab", "", 0, "Table Name", "TabNam"),),
            "group": "chg_tab",
            "order": "chg_tab"}
        usr = {
            "stype": "R",
            "tables": ("chglog",),
            "cols": (("chg_usr", "", 0, "User Login name", "User-Login-Name"),),
            "group": "chg_usr",
            "order": "chg_usr"}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"Id1",10,"Date From","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Date To","",
                self.sysdtw,"N",self.doDate,None,None,("efld",)),
            (("T",0,2,0),"INA",6,"Table Name","",
                "","N",self.doTable,tab,None,("efld",)),
            (("T",0,2,0),"ONA",30,""),
            (("T",0,3,0),("IRB",r1s),0,"Order By Table","",
                "Y","N",self.doOrder,None,None,None),
            (("T",0,4,0),"INA",20,"User Login","",
                "","N",self.doUser,usr,None,("efld",)),
            (("T",0,4,0),"ONA",30,""))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        if p == 0:
            self.frm = CCD(w, "d1", 10)
        elif w < self.frm.work:
            return "Invalid Date, Less than Start Date"
        else:
            self.too = CCD(w, "D1", 10)

    def doTable(self, frt, pag, r, c, p, i, w):
        self.table = w
        if self.table:
            if self.table not in tabdic:
                return "Invalid Table Name"
            self.tname = tabdic[w]["idx"][0][0]
            self.df.loadEntry(frt, pag, p+1, data=self.tname)

    def doUser(self, frt, pag, r, c, p, i, w):
        self.user = w
        if self.user:
            acc = self.sql.getRec("chglog", cols=["usr_fnam"],
                where=[("usr_name", "=", self.user)], limit=1)
            if not acc:
                return "Invalid User Login"
            self.tname = acc[0]
            self.df.loadEntry(frt, pag, p+1, data=self.tname)

    def doOrder(self, frt, pag, r, c, p, i, w):
        self.byusr = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.frm.work:
            frm = "Beginning"
        else:
            frm = self.frm.disp
        hds = "Changes Log Report from %s to %s" % (frm, self.too.disp)
        col = [
            ("chg_tab", "NA", 6.0, "TabNam"),
            ("chg_act", "UA", 1.0, "A"),
            ("chg_key", "NA", 30.0, "Record-Key"),
            ("chg_col", "NA", 20.0, "Column-Name"),
            ("chg_old", "TX", 50.0, "Old-Details"),
            ("chg_new", "TX", 50.0, "New-Details"),
            ("chg_dte", "TS", 19.0, "Date-&-Time-Changed"),
            ("chg_usr", "NA", 20.0, "User-Login")]
        whr = [
            ("chg_dte", ">=", str(self.frm.work * 1000000)),
            ("chg_dte", "<=", str((self.too.work * 1000000) + 999999))]
        if self.byusr == "Y":
            odr = "chg_tab, chg_dte desc"
        else:
            odr = "chg_dte desc"
        if self.table:
            whr.append(("chg_tab", "=", self.table))
        if self.user:
            whr.append(("chg_usr", "=", self.user))
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=["chglog"],
            heads=[hds], cols=col, where=whr, order=odr, repprt=self.df.repprt,
            repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
