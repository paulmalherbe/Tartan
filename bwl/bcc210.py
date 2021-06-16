"""
SYNOPSIS
    Clubs's Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import getNextCode

class bcc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "bwlclb", "bwlflo"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        acc = self.sql.getRec("bwlclb", where=[("bcc_code", "=",
            self.opts["conum"])], limit=1)
        if not acc:
            self.sql.insRec("bwlclb", data=[self.opts["conum"],
                self.opts["conam"]])
            self.opts["mf"].dbm.commitDbase()
        return True

    def mainProcess(self):
        clb = {
            "stype": "R",
            "tables": ("bwlclb",),
            "cols": (
                ("bcc_code", "", 0, "Cod"),
                ("bcc_name", "", 0, "Name", "Y")),
            "order": "bcc_name"}
        fld = (
            (("T",0,0,0),"I@bcc_code",0,"","",
                "","Y",self.doClbCod,clb,None,("efld",)),
            (("T",0,1,0),"I@bcc_name",0,"","",
                "","N",self.doName,None,self.doDelete,("notblank",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doClbCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.club = getNextCode(self.sql, "bwlclb", "bcc_code", last=999)
            self.df.loadEntry(frt, pag, p, data=self.club)
        else:
            self.club = w
        self.old = self.sql.getRec("bwlclb", where=[("bcc_code", "=",
            self.club)], limit=1)
        if not self.old:
            self.newclb = True
        else:
            self.newclb = False
            for num, fld in enumerate(self.old[:-1]):
                self.df.loadEntry(frt, pag, num, data=fld)

    def doName(self, frt, pag, r, c, p, i, w):
        if self.newclb:
            chk = self.sql.getRec("bwlclb", where=[("bcc_name", "ilike", w)])
            if chk:
                return "A Club with this Name Already Exists"

    def doDelete(self):
        if self.newclb:
            return
        if self.club == self.opts["conum"]:
            return "Cannot Delete Own Club"
        error = False
        for tab in (("bwlflo", "bfo_cono", "bfo_club"),):
            chk = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                self.opts["conum"]), (tab[2], "=", self.club)], limit=1)
            if chk:
                error = True
                break
        if error:
            return "There are Entries for this Club, Not Deleted"
        self.sql.delRec("bwlclb", where=[("bcc_code", "=", self.club)])
        self.opts["mf"].dbm.commitDbase()

    def doEnd(self):
        data = self.df.t_work[0][0][:]
        if self.newclb:
            self.sql.insRec("bwlclb", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bwlclb_col
            data.append(self.old[col.index("bcc_xflag")])
            self.sql.updRec("bwlclb", data=data, where=[("bcc_code", "=",
                self.club)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
