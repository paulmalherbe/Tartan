"""
SYNOPSIS
    Rental System Premises Maintenance.

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

import time
from TartanClasses import Sql, TartanDialog

class rc1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "rcaprm", "rcaowm",
            "rcatnm"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        own = {
            "stype": "R",
            "tables": ("rcaowm",),
            "cols": (
                ("rom_acno", "", 0, "Own-Cod"),
                ("rom_name", "", 0, "Name", "Y")),
            "where": [("rom_cono", "=", self.opts["conum"])]}
        prm = {
            "stype": "R",
            "tables": ("rcaprm",),
            "cols": (
                ("rcp_code", "", 0, "Prm-Code"),
                ("rcp_addr1", "", 0, "Address-Line-1")),
            "where": [("rcp_cono", "=", self.opts["conum"])],
            "whera": [("T", "rcp_owner", 0, 0)]}
        self.fld = [
            (("T",0,0,0),"INA",7,"Owner Code","Owner",
                "","N",self.doOwnCod,own,None,("notblank",)),
            (("T",0,0,0),"ONA",30,"Name"),
            (("T",0,1,0),"INA",7,"Premises Code","Premises",
                "","N",self.doPrmCod,prm,None,("notblank",)),
            (("T",0,2,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",0,4,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"INA",4,"Postal Code","PCod",
                "","N",None,None,None,("notblank",)),
            (("T",0,7,0),"IUD",6.2,"Commission Rate","C-Rate",
                "","N",None,None,None,("efld",))]
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doOwnCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaowm", cols=["rom_name"],
            where=[("rom_cono", "=", self.opts["conum"]), ("rom_acno", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Owner"
        self.owner = w
        self.name = acc[0]
        self.df.loadEntry(frt, pag, p+1, data=self.name)

    def doPrmCod(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.old = self.sql.getRec("rcaprm", where=[("rcp_cono", "=",
            self.opts["conum"]), ("rcp_owner", "=", self.owner), ("rcp_code",
            "=", self.code)], limit=1)
        if not self.old:
            self.new = "y"
        else:
            self.new = "n"
            for num, dat in enumerate(self.old[2:-1]):
                self.df.loadEntry(frt, pag, p+num, data=dat)

    def doDelete(self):
        mst = self.sql.getRec("rcatnm", cols=["count(*)"],
            where=[("rtn_cono", "=", self.opts["conum"]), ("rtn_code", "=",
            self.code)], limit=1)
        if mst[0]:
            return "Accounts Exist, Not Deleted"
        self.sql.delRec("rcaprm", where=[("rcp_cono", "=", self.opts["conum"]),
            ("rcp_code", "=", self.code)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rcaprm", "D", "%03i%-7s" % \
            (self.opts["conum"], self.code), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if x == 1:
                continue
            data.append(self.df.t_work[0][0][x])
        if self.new == "y":
            self.sql.insRec("rcaprm", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.rcaprm_col
            data.append(self.old[col.index("rcp_xflag")])
            self.sql.updRec("rcaprm", data=data, where=[("rcp_cono", "=",
                self.opts["conum"]), ("rcp_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["rcaprm",
                        "U", "%03i%-7s" % (self.opts["conum"], self.code),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
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
