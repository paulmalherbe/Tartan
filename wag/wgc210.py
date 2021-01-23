"""
SYNOPSIS
    Wages Receiver of Revenue Codes File Maintenance.

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

class wgc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "wagrcv",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        rcv = {
            "stype": "R",
            "tables": ("wagrcv",),
            "cols": (
                ("rcv_code", "", 0, "Code"),
                ("rcv_desc", "", 0, "Details"))}
        self.fld = (
            (("T",0,0,0),"IUI",4,"Item Code","",
                "","N",self.doCode,rcv,None,("notzero",)),
            (("T",0,1,0),"INA",50,"Description","",
                "","N",None,None,self.doDelete,("notblank",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        acc = self.sql.getRec("wagrcv", where=[("rcv_code", "=",
            self.code)], limit=1)
        if not acc:
            self.new = "Y"
        else:
            self.new = "N"
            for x in range(1, self.df.topq[pag]):
                self.df.loadEntry(frt, pag, p+x, data=acc[x])

    def doDelete(self):
        self.sql.delRec("wagrcv", where=[("rcv_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        dat = []
        for x in range(0, len(self.df.t_work[0][0])):
            dat.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("wagrcv", data=dat)
        else:
            self.sql.updRec("wagrcv", data=dat,
            where=[("rcv_code", "=", self.code)])
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
