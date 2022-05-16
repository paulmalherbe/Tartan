"""
SYNOPSIS
    Bulk Mailing Utility.

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

from TartanClasses import Sql, TartanDialog

class bkc410(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, tables="bkmlet",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        r1s = (("Query","Q"),("Confirm","C"),("Settle","S"),("Cancel","X"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Letter Type","",
                "Q","Y",self.doType,None,None,None),
            (("T",0,1,0),"ITV",(80,10),"Body","",
                "","N",None,None,None,("notblank",)))
        but = (
            ("Save", None, self.doSave, 0, ("T",0,2), ("T",0,1)),
            ("Quit", None, self.doQuit, 1, None, ("T",0,1)))
        tnd = ((self.doEnd, "y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt)

    def doType(self, frt, pag, r, c, p, i, w):
        self.ltyp = w
        self.let = self.sql.getRec("bkmlet", where=[("bkl_cono", "=",
            self.opts["conum"]), ("bkl_code", "=", self.ltyp)], limit=1)
        if not self.let:
            self.lnew = True
        else:
            self.lnew = False
            self.df.loadEntry(frt, pag, p+1,
                data=self.let[self.sql.bkmlet_col.index("bkl_body")])

    def doSave(self):
        self.df.loadEntry("T", 0, 1, data=self.df.getEntry("T", 0, 1)[1])
        self.doEnd()

    def doEnd(self):
        data = [self.opts["conum"], self.ltyp, self.df.t_work[0][0][1]]
        if self.lnew:
            self.sql.insRec("bkmlet", data=data)
        elif data != self.let[:len(data)]:
            col = self.sql.bkmlet_col
            data.append(self.let[col.index("bkl_xflag")])
            self.sql.updRec("bkmlet", data=data, where=[("bkl_cono", "=",
                self.opts["conum"]), ("bkl_code", "=", self.ltyp)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doQuit(self):
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
