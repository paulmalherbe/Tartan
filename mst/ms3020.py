"""
SYNOPSIS
    Module Passwords Listing.

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

from TartanClasses import RepPrt, TartanDialog
from tartanWork import allsys, pwctrl

class ms3020(object):
    def __init__(self, **opts):
        self.opts = opts
        self.mainProcess()
        self.opts["mf"].startLoop()

    def mainProcess(self):
        sss = []
        data = [["ALL", "All Systems"]]
        for ctl in pwctrl:
            if ctl[0] not in sss:
                sss.append(ctl[0])
        for s in sss:
            data.append([s, allsys[s][0]])
            data.sort()
        sss.append("ALL")
        stt = {
            "stype": "C",
            "titl": "Select the Required System",
            "head": ("COD", "Description"),
            "data": data}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IUA",3,"System","",
                "ALL","Y",self.doSys,stt,None,("in", sss)),
            (("T",0,1,0),("IRB",r1s),0,"Only Enabled","",
                "Y","N",self.doTyp,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"))

    def doSys(self, frt, pag, r, c, p, i, w):
        self.sys = w

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w

    def doEnd(self):
        self.df.closeProcess()
        self.printReport()
        self.closeProcess()

    def printReport(self):
        state = self.df.disableButtonsTags()
        heads = ["Module Passwords Master Listing"]
        cols = [
            ["pwd_cono","UI",3.0,"Coy"],
            ["pwd_sys","UA",3.0,"Sys"],
            ["pwd_code","NA",20.0,"Access Code"],
            ["pwd_desc","NA",50.0,"Description"],
            ["pwd_pass","HA",30.0,"Password"]]
        if self.typ == "Y":
            tables = ["ctlpwr"]
            if self.sys == "ALL":
                whr = []
            else:
                whr = [("pwd_sys", "=", self.sys)]
            odr = "pwd_cono, pwd_sys, pwd_code"
            RepPrt(self.opts["mf"], name=self.__class__.__name__,
                tables=tables, heads=heads, cols=cols, where=whr,
                order=odr, repprt=self.df.repprt)
        else:
            ccol = cols[:]
            ccol[0][1] = "NA"
            data = []
            for ctl in pwctrl:
                if self.sys == "ALL" or ctl[0] == self.sys:
                    data.append(("", ctl[0], ctl[1], ctl[2], ""))
            RepPrt(self.opts["mf"], name=self.__class__.__name__,
                tables=data, heads=heads, cols=ccol, ttype="D",
                repprt=self.df.repprt)
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
