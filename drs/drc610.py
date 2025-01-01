"""
SYNOPSIS
    Debtors Business Activity File Maintenance.

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

from TartanClasses import Sql, TartanDialog

class drc610(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsact", "drsmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        act = {
            "stype": "R",
            "tables": ("drsact",),
            "cols": (
                ("dac_code", "", 0, "Cod"),
                ("dac_desc", "", 0, "Description", "Y"))}
        self.fld = (
            (("T",0,0,0),"IUA",3,"Code","Business Activity Code",
                "","N",self.doAct,act,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doAct(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.acc = self.sql.getRec("drsact", where=[("dac_code",
            "=", self.code)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            desc = self.acc[self.sql.drsact_col.index("dac_desc")]
            self.df.loadEntry(frt, pag, p+1, data=desc)

    def doDelete(self):
        acc = self.sql.getRec("drsmst", cols=["count(*)"],
            where=[("drm_bus_activity", "=", self.code)], limit=1)
        if acc[0]:
            return "Code in Use, Not Deleted"
        self.sql.delRec("drsact", where=[("dac_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = []
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("drsact", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.drsact_col
            data.append(self.acc[col.index("dac_xflag")])
            self.sql.updRec("drsact", data=data, where=[("dac_code",
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
