"""
SYNOPSIS
    Bowls League Side's Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import getNextCode

class bc1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlflf", "bwlflm", "bwlfls",
            "bwlflt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        fmt = {
            "stype": "R",
            "tables": ("bwlflf",),
            "cols": (
                ("bff_code", "", 0, "Cod"),
                ("bff_desc", "", 0, "Description", "Y")),
            "where": [("bff_cono", "=", self.opts["conum"])]}
        sid = {
            "stype": "R",
            "tables": ("bwlfls",),
            "cols": (
                ("bfs_code", "", 0, "Cod"),
                ("bfs_desc", "", 0, "Description", "Y"),
                ("bfs_league", "", 0, "L"),
                ("bfs_division", "", 0, "DV"),
                ("bfs_number", "", 0, "N")),
            "where": [("bfs_cono", "=", self.opts["conum"])],
            "whera": [("T", "bfs_fmat", 0, 0)],
            "order": "bfs_code"}
        r1s = (("Main", "M"), ("Friendly", "F"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"I@bff_code",0,"","",
                0,"Y",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"I@bfs_code",0,"","",
                0,"Y",self.doSide,sid,None,("efld",)),
            (("T",0,2,0),"I@bfs_desc",0,"","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)),
            (("T",0,3,0),("IRB",r1s),0,"League","",
                "M","N",None,None,None,None),
            (("T",0,4,0),"I@bfs_division",0,"","",
                "","N",None,None,None,("notblank",)),
            (("T",0,5,0),"I@bfs_number",0,"","",
                "","N",None,None,None,("in",(1,2,3))),
            (("T",0,6,0),("IRB",r2s),0,"Active Flag","",
                "Y","N",None,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Format"
        self.fmat = w
        self.df.loadEntry(frt, pag, p+1, data=acc[2])

    def doSide(self, frt, pag, r, c, p, i, w):
        if not w:
            self.side = getNextCode(self.sql, "bwlfls", "bfs_code",
                where=[("bfs_cono", "=", self.opts["conum"]),
                ("bfs_fmat", "=", self.fmat)], last=999)
            self.df.loadEntry(frt, pag, p, data=self.side)
        else:
            self.side = w
        self.old = self.sql.getRec("bwlfls", where=[("bfs_cono", "=",
            self.opts["conum"]), ("bfs_fmat", "=", self.fmat), ("bfs_code",
            "=", self.side)], limit=1)
        if not self.old:
            self.newfls = True
        else:
            self.newfls = False
            for num, fld in enumerate(self.old[3:-1]):
                self.df.loadEntry(frt, pag, num+3, data=fld)

    def doDesc(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlflm", where=[("bfm_cono", "=",
            self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_team",
            "=", self.side)])
        if chk:
            return "sk3"

    def doDelete(self):
        if self.newfls:
            return
        error = False
        for tab in (("bwlflm", "bfm_cono", "bfm_team"),
                    ("bwlflt", "bft_cono", "bft_team")):
            chk = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                self.opts["conum"]), (tab[2], "=", self.side)], limit=1)
            if chk:
                error = True
                break
        if error:
            return "There are Movements for this Side, Not Deleted"
        self.sql.delRec("bwlfls", where=[("bfs_cono", "=", self.opts["conum"]),
            ("bfs_fmat", "=", self.fmat), ("bfs_code", "=", self.side)])
        self.opts["mf"].dbm.commitDbase()

    def doEnd(self):
        data = [self.opts["conum"], self.fmat] + self.df.t_work[0][0][2:]
        if self.newfls:
            self.sql.insRec("bwlfls", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bwlfls_col
            data.append(self.old[col.index("bfs_xflag")])
            self.sql.updRec("bwlfls", data=data, where=[("bfs_cono", "=",
                self.opts["conum"]), ("bfs_fmat", "=", self.fmat),
                ("bfs_code", "=", self.side)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
