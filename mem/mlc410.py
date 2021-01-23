"""
SYNOPSIS
    Members Ledger Contacts Maintenance.

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

from TartanClasses import Sql, TartanDialog

class mlc410(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "memctk", "memkon"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("memctk")
        if not chk:
            self.sql.insRec("memctk", data=[1,"H","Home Telephone Number"])
            self.sql.insRec("memctk", data=[2,"W","Work Telephone Number"])
            self.sql.insRec("memctk", data=[3,"M","Mobile Telephone Number"])
            self.sql.insRec("memctk", data=[4,"F","Facsimile Number"])
            self.sql.insRec("memctk", data=[5,"E","E-Mail Address"])
            self.opts["mf"].dbm.commitDbase()
        return True

    def mainProcess(self):
        cod = {
            "stype": "R",
            "tables": ("memctk",),
            "cols": (
                ("mck_code", "", 0, "CD"),
                ("mck_desc", "", 0, "Description", "Y"))}
        typ = {
            "stype": "C",
            "title": "Available Types",
            "head": ("C", "Description"),
            "data": (
                ("E", "E-Mail"),
                ("F", "Facsimile"),
                ("H", "Home Phone"),
                ("M", "Mobile"),
                ("W", "Work Phone"))}
        fld = (
            (("T",0,0,0),"I@mck_code",0,"","",
                "","N",self.doCode,cod,None,("notzero",)),
            (("T",0,1,0),"I@mck_type",0,"","",
                "","N",self.doType,typ,None,("in",("E","F","H","M","W"))),
            (("T",0,2,0),"I@mck_desc",0,"","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.old = self.sql.getRec("memctk", where=[("mck_code", "=",
            self.code)], limit=1)
        if self.old:
            self.new = False
            self.ktyp = self.old[self.sql.memctk_col.index("mck_type")]
            self.df.loadEntry(frt, pag, p+1, data=self.ktyp)
            self.desc = self.old[self.sql.memctk_col.index("mck_desc")]
            self.df.loadEntry(frt, pag, p+2, data=self.desc)
        else:
            self.new = True

    def doType(self, frt, pag, r, c, p, i, w):
        self.ktyp = w

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doDelete(self):
        if self.code in (1, 2, 3, 4, 5):
            return "Static Code, Not Deleted"
        chk = self.sql.getRec("memkon", cols=["count(*)"],
            where=[("mlk_code", "=", self.code)], limit=1)
        if chk[0]:
            return "Code in Use (memkon), Not Deleted"
        self.sql.delRec("memctk", where=[("mck_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.code, self.ktyp, self.desc]
        if self.new:
            self.sql.insRec("memctk", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.memctk_col
            data.append(self.old[col.index("mck_xflag")])
            self.sql.updRec("memctk", data=data, where=[("mck_code",
                "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
