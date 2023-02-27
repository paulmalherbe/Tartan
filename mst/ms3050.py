"""
SYNOPSIS
    Appliccation Usage Log.

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
from TartanClasses import CCD, RepPrt, Sql, TartanDialog
from tartanWork import allsys, pkgs, tarmen

class ms3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ctllog",
            prog=self.__class__.__name__)
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        # {"sss": {"mod": {"typ": "desc"}}.....}
        self.allmod = {"tb": {
            "tb1010":
                {0: "Create File Formats"},
            "tb1020":
                {0: "Update File Formats"},
            "tb1030":
                {0: "Table Data Editing"},
            "tb3010":
                {0: "Table Formats Listing"}}}
        for key in tarmen:
            if key[2:] == "men":
                continue
            for itm in tarmen[key]:
                if itm[0][0] != "P":
                    continue
                mod = itm[2]
                sss = mod[:2]
                if sss not in self.allmod:
                    self.allmod[sss] = {}
                if mod not in self.allmod[sss]:
                    self.allmod[sss][mod] = {}
                if len(itm) == 6:
                    typ = itm[5]
                else:
                    typ = 0
                if typ not in self.allmod[sss][mod]:
                    self.allmod[sss][mod][typ] = itm[4]
        return True

    def mainProcess(self):
        usr = {
            "stype": "R",
            "tables": ("ctllog",),
            "cols": (("clg_user", "", 0, "User Name", "F"),),
            "group": "clg_user"}
        self.mod = {
            "stype": "C",
            "titl": "Available Module",
            "head": ("Module", "T", "System", "Description"),
            "typs": (("NA", 6), ("UI", 1), ("NA", 30), ("NA", 30)),
            "data": []}
        r1s = (("Descending","D"), ("Ascending", "A"))
        fld = (
            (("T",0,0,0),"Id1",10,"Date From","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Date To","",
                self.sysdtw,"N",self.doDate,None,None,("efld",)),
            (("T",0,2,0),"INA",20,"User Name","",
                "","N",self.doUsr,usr,None,("efld",)),
            (("T",0,3,0),"INA",20,"Module","",
                "","N",self.doMod,self.mod,None,("efld",)),
            (("T",0,4,0),("IRB",r1s),0,"Date Order","",
                "D","N",self.doOrder,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        if p == 0:
            self.frm = CCD(w, "d1", 10)
        elif w < self.frm.work:
            return "Invalid, Before From"
        else:
            self.too = CCD(w, "D1", 10)

    def doUsr(self, frt, pag, r, c, p, i, w):
        self.usr = w
        self.whr = [
            ("clg_start", ">=", str(self.frm.work * 1000000)),
            ("clg_start", "<=", str((self.too.work * 1000000) + 999999))]
        if self.usr:
            self.whr.append(("clg_user", "=", self.usr))
        usemod = self.sql.getRec("ctllog", cols=["clg_prog", "clg_type"],
            where=self.whr, group="clg_prog, clg_type")
        self.mod["data"] = self.getData(usemod)
        self.mod["data"].sort()

    def doMod(self, frt, pag, r, c, p, i, w):
        self.prog = w

    def doOrder(self, frt, pag, r, c, p, i, w):
        self.order = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.frm.work:
            frm = "Beginning"
        else:
            frm = self.frm.disp
        hds = "Application Usage Report from %s to %s" % (frm, self.too.disp)
        col = [
            ("a", "NA", 20, "User Name",          "y"),
            ("b", "NA",  6, "Module"              "y"),
            ("c", "UA",  1, "T",                  "y"),
            ("d", "NA", 20, "System",             "y"),
            ("e", "NA", 30, "Description",        "y"),
            ("f", "UI",  3, "Coy",                "y"),
            ("g", "UI",  3, "Per",                "y"),
            ("h", "TS", 19, "Starting-Date&Time", "y")]
        whr = self.whr[:]
        if self.usr:
            whr.append(("clg_user", "like", "%s%s%s" % ("%", self.usr, "%")))
        if self.prog:
            whr.append(("clg_prog", "=", self.prog[:5] + "0"))
            whr.append(("clg_type", "=", self.prog[5]))
        if self.order == "A":
            odr = "clg_start asc, clg_prog, clg_type"
        else:
            odr = "clg_start desc, clg_prog, clg_type"
        mods = self.sql.getRec("ctllog", cols=["clg_prog", "clg_type",
            "clg_user", "clg_cono", "clg_period", "clg_start"],
            where=whr, order=odr)
        data = self.getData(mods)
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=[hds], cols=col, ttype="D", repprt=self.df.repprt,
            repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def getData(self, mods):
        data = []
        for mod in mods:
            sss = mod[0][:2]
            if sss not in pkgs:
                continue
            if pkgs[sss].upper() not in allsys:
                if sss == "si":
                    stm = "Sales Invoicing"
                elif sss == "tb":
                    stm = "System"
                elif sss in ("bm", "pw", "td", "tp", "rp"):
                    stm = "Utilities"
            else:
                stm = allsys[pkgs[sss].upper()][0]
            if sss not in self.allmod:
                continue
            if mod[0][2] == "2" and mod[1]:
                ttt = mod[1]
            else:
                ttt = 0
            if mod[0] in self.allmod[sss]:
                if ttt in self.allmod[sss][mod[0]]:
                    dat = [mod[0], ttt, stm,
                        self.allmod[sss][mod[0]][ttt]]
                    if len(mod) == 6:
                        dat.insert(0, mod[2])
                        dat.extend(mod[3:])
                    data.append(dat)
        return data

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
