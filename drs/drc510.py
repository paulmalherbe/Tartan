"""
SYNOPSIS
    Debtors Messages File Maintenance.

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

class drc510(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ctlmes",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_system", "", 0, "Sys"),
                ("mss_message", "", 0, "Mss"),
                ("mss_detail", "NA", 50, "Details")),
            "where": [],
            "index": 1}
        r1s = (("Invoice","I"), ("Statement","S"), ("Conditions","C"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Message Type","",
                "I","Y",self.doType,None,None,None),
            (("T",0,1,0),"IUI",3,"Message Number","",
                "","N",self.doMes,mss,None,("notzero",)),
            (("T",0,2,0),"ITv",(30,6),"Details","",
                "","N",self.doDetail,None,self.doDelete,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,3),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,3),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doType(self, frt, pag, r, c, p, i, w):
        if w == "I":
            self.system = "INV"
        elif w == "S":
            self.system = "STA"
        else:
            self.system = "CON"
            self.df.loadEntry(frt, pag, p+1, data=1)
            self.doMes(frt, pag, r, c+1, p+1, i+1, 1)
            return "sk1"
        self.df.topf[pag][1][8]["where"] = [("mss_system", "=", self.system)]

    def doMes(self, frt, pag, r, c, p, i, w):
        self.message = w
        self.acc = self.sql.getRec("ctlmes", where=[("mss_system",
            "=", self.system), ("mss_message", "=", self.message)],
            order="mss_message", limit=1)
        if not self.acc:
            self.new = "Y"
            self.df.loadEntry(frt, pag, p+1, data="")
        else:
            self.new = "N"
            self.detail = self.acc[2]
            self.df.loadEntry(frt, pag, p+1, data=self.detail)

    def doDetail(self, frt, pag, r, c, p, i, w):
        if len(w) > 150:
            return "Invalid Message Length, Maximum 150 Characters"

    def doDelete(self):
        self.sql.delRec("ctlmes", where=[("mss_system", "=", self.system),
            ("mss_message", "=", self.message)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        wid, self.detail = self.df.getEntry("T", 0, 2)
        if len(self.detail) > 150:
            self.df.focusField("T", 0, 3,
                err="Invalid Message Length, Maximum 150 Characters")
        else:
            data = [self.system, self.message, self.detail]
            if self.new == "Y":
                self.sql.insRec("ctlmes", data=data)
            elif data != self.acc[:len(data)]:
                col = self.sql.ctlmes_col
                data.append(self.acc[col.index("mss_xflag")])
                self.sql.updRec("ctlmes", data=data, where=[("mss_system",
                    "=", self.system), ("mss_message", "=", self.message)])
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
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
