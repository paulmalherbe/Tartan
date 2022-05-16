"""
SYNOPSIS
    Book Club Author's Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import getNextCode, showError

class bsc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bksaut", "bksmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        clb = {
            "stype": "R",
            "tables": ("bksaut",),
            "cols": (
                ("baf_code", "", 0, "Cod"),
                ("baf_snam", "", 0, "Surname", "Y"),
                ("baf_fnam", "", 0, "Names")),
            "order": "baf_snam"}
        fld = (
            (("T",0,0,0),"I@baf_code",0,"","",
                "","Y",self.doCode,clb,None,("efld",)),
            (("T",0,1,0),"I@baf_snam",0,"","",
                "","N",self.doSnam,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"I@baf_fnam",0,"","",
                "","N",self.doFnam,None,None,("efld",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        if not w:
            self.author = getNextCode(self.sql, "bksaut", "baf_code", last=999)
            self.df.loadEntry(frt, pag, p, data=self.author)
        else:
            self.author = w
        self.old = self.sql.getRec("bksaut", where=[("baf_code", "=",
            self.author)], limit=1)
        if not self.old:
            self.newaut = True
        else:
            self.newaut = False
            for num, fld in enumerate(self.old[:-1]):
                self.df.loadEntry(frt, pag, num, data=fld)

    def doDelete(self):
        chk = self.sql.getRec("bksmst", where=[("bmf_auth",
            "=", self.author)], limit=1)
        if chk:
            showError(self.opts["mf"].body, "Error", "Author in Use")
            return
        self.sql.delRec("bksaut", where=[("baf_code", "=", self.author)])
        self.opts["mf"].dbm.commitDbase()

    def doSnam(self, frt, pag, r, c, p, i, w):
        self.snam = w

    def doFnam(self, frt, pag, r, c, p, i, w):
        if self.newaut:
            chk = self.sql.getRec("bksaut", where=[("baf_snam",
                "=", self.snam), ("baf_fnam", "=", w)], limit=1)
            if chk:
                return "An Author with this Name Already Exists"

    def doEnd(self):
        data = self.df.t_work[0][0][:]
        if self.newaut:
            self.sql.insRec("bksaut", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bksaut_col
            data.append(self.old[col.index("baf_xflag")])
            self.sql.updRec("bksaut", data=data, where=[("baf_code", "=",
                self.author)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
