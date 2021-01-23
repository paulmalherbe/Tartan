"""
SYNOPSIS
    Telephone Directory Group Records.

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

class tdc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["telgrp", "telmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def drawDialog(self):
        grp = {
            "stype": "R",
            "tables": ("telgrp",),
            "cols": [
                ("tdg_group", "", 0, "Code"),
                ("tdg_desc", "", 0, "Description")],
            "order": "tdg_desc"}
        self.fld = (
            (("T",0,0,0),"I@tdg_group",0,"","",
                "","N",self.doGroup,grp,None,("notblank",)),
            (("T",0,1,0),"I@tdg_desc",0,"","",
                "","N",None,None,self.doDelete,("notblank",)))
        but = (("Quit",None,self.doExit,1,None,None),)
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w
        self.acc = self.sql.getRec("telgrp", where=[("tdg_group", "=",
            self.group)], limit=1)
        if not self.acc:
            self.new = True
        else:
            self.new = False
            des = self.acc[self.sql.telgrp_col.index("tdg_desc")]
            self.df.loadEntry(frt, pag, p+1, data=des)

    def doDelete(self):
        chk = self.sql.getRec("telmst", cols=["tdm_group"],
            where=[("tdm_group", "<>", "")])
        if chk:
            err = None
            for c in chk:
                d = c[0].split(",")
                if self.group in d:
                    err = "Group In Use, Not Deleted"
            if err:
                return err
        self.sql.delRec("telgrp", where=[("tdg_group", "=", self.group)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = []
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new:
            self.sql.insRec("telgrp", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.telgrp_col
            data.append(self.acc[col.index("tdg_xflag")])
            self.sql.updRec("telgrp", data=data, where=[("tdg_group",
                "=", self.group)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
