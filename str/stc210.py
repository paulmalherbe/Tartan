"""
SYNOPSIS
    Units Of Issue File Maintenance.

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

from TartanClasses import Sql, TartanDialog

class stc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "struoi",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        unm = {
            "stype": "R",
            "tables": ("struoi",),
            "cols": (
                ("unm_unit", "", 0, "Unit"),
                ("unm_desc", "", 0, "Description", "Y")),
            "where": [("unm_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"INA",10,"Unit Of Issue","",
                "","N",self.doUnit,unm,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doUnit(self, frt, pag, r, c, p, i, w):
        self.uoi = w
        self.old = self.sql.getRec("struoi", where=[("unm_cono",
            "=", self.opts["conum"]), ("unm_unit", "=", self.uoi)], limit=1)
        if not self.old:
            self.new = "Y"
        else:
            self.new = "N"
            desc = self.old[self.sql.struoi_col.index("unm_desc")]
            self.df.loadEntry(frt, pag, p+1, data=desc)

    def doDelete(self):
        self.sql.delRec("struoi", where=[("unm_cono", "=", self.opts["conum"]),
            ("unm_unit", "=", self.uoi)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("struoi", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.struoi_col
            data.append(self.old[col.index("unm_xflag")])
            self.sql.updRec("struoi", data=data, where=[("unm_cono",
                "=", self.opts["conum"]), ("unm_unit", "=", self.uoi)])
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

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
