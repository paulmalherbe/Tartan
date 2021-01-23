"""
SYNOPSIS
    Email Log.

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

import time
from TartanClasses import CCD, RepPrt, TartanDialog

class ms3030(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]

    def mainProcess(self):
        eml = {
            "stype": "R",
            "tables": ("emllog",),
            "cols": (("eml_too", "", 0, "E-Mail Address", "F"),),
            "group": "eml_too"}
        r1s = (("Ascending", "A"), ("Descending","D"))
        fld = (
            (("T",0,0,0),"Id1",10,"Date From","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Date To","",
                self.sysdtw,"N",self.doDate,None,None,("efld",)),
            (("T",0,2,0),"INA",50,"Recipient","",
                "","N",self.doRecpt,eml,None,("efld",)),
            (("T",0,3,0),("IRB",r1s),0,"Date Order","",
                "A","N",self.doOrder,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        if p == 0:
            self.frm = w
        elif w < self.frm:
            return "Invalid Date, Less than Start Date"
        else:
            self.too = w

    def doRecpt(self, frt, pag, r, c, p, i, w):
        self.recpt = w

    def doOrder(self, frt, pag, r, c, p, i, w):
        self.order = w

    def doEnd(self):
        self.df.closeProcess()
        frm = CCD(self.frm, "d1", 10).disp
        too = CCD(self.too, "D1", 10).disp
        hds = "Email Log Report from %s to %s" % (frm, too)
        col = ["eml_too", "eml_sub", "eml_dtt", "eml_sta"]
        whr = [
            ("eml_dtt", ">=", "%10s 00:00" % frm),
            ("eml_dtt", "<=", "%10s 99:99" % too)]
        if self.recpt:
            whr.append(("eml_too", "like", "%s%s%s" % ("%", self.recpt, "%")))
        if self.order == "A":
            odr = "eml_dtt asc"
        else:
            odr = "eml_dtt desc"
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=["emllog"],
            heads=[hds], cols=col, where=whr, order=odr, repprt=self.df.repprt,
            repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
