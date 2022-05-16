"""
SYNOPSIS
    General Ledger Chart Of Accounts.

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

from TartanClasses import RepPrt, TartanDialog

class gl3060(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        pass

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Chart of Accounts (%s)" % self.__class__.__name__)
        r1s = (("Numb","N"),("Desc","D"),("Type/Numb","A"),("Type/Desc","B"))
        fld = (
            (("T",0,0,0),("IRB",r1s),1,"Sort Order","",
                "N","Y",self.doSortOrd,None,None,None),)
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSortOrd(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        self.df.closeProcess()
        col = ["glm_acno", "glm_desc", "glm_type", "glm_fstp", "glm_fsgp",
            "glm_ind", "glm_vat"]
        whr = [("glm_cono", "=", self.opts["conum"])]
        if self.sort == "N":
            odr = "glm_acno"
        elif self.sort == "A":
            odr = "glm_type, glm_fstp, glm_acno"
        elif self.sort == "B":
            odr = "glm_type, glm_fstp, glm_desc"
        else:
            odr = "glm_desc"
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=self.__class__.__name__,
            tables=["genmst"], heads=["General Ledger Chart of Accounts"],
            cols=col, where=whr, order=odr, repprt=self.df.repprt,
            repeml=self.df.repeml)
        self.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
