"""
SYNOPSIS
    Module Passwords Maintenance.

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
from tartanFunctions import b64Convert
from tartanWork import allsys, pwctrl

class ms1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlpwr"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.pwd = ""
        return True

    def mainProcess(self):
        sss = []
        self.sys_data = []
        for ctl in pwctrl:
            if ctl[0] not in sss:
                sss.append(ctl[0])
        for s in sss:
            self.sys_data.append([s, allsys[s][0]])
        self.sys_data.sort()
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Num"),
                ("ctm_name", "", 0, "Name", "Y")),
            "extra": ((0, "All Companies"),)}
        sys = {
            "stype": "C",
            "titl": "Select the System",
            "head": ("SYS", "Description"),
            "data": self.sys_data}
        self.ctl = {
            "stype": "C",
            "titl": "Available Control Codes",
            "head": ("Sys","Code","Description"),
            "data": pwctrl,
            "index": 1,
            "retn": "D"}
        pwd = {
            "stype": "R",
            "tables": ("ctlpwr",),
            "cols": (
                ("pwd_code", "", 0, "Code"),
                ("pwd_desc", "", 0, "Description", "Y")),
            "whera": [["T", "pwd_cono", 0], ["T", "pwd_sys", 1]]}
        fld = (
            (("T",0,0,0),"IUI",3,"Company","",
                "","Y",self.doCompany,coy,None,None),
            (("T",0,1,0),"IUA",3,"System","",
                "","N",self.doSystem,sys,None,("notblank",)),
            (("T",0,2,0),"INA",20,"Code","",
                "","N",self.doCode,pwd,None,("notblank",)),
            (("T",0,3,0),"ONA",50,"Description"),
            (("T",0,4,0),"IHA",30,"Password","",
                "","N",self.doPwd,None,self.doDelete,None))
        but = (
            ("Show All",self.ctl,None,0,("T",0,1),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCompany(self, frt, pag, r, c, p, i, w):
        if w:
            nam = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
                w)], limit=1)
            if not nam:
                return "Invalid Company Number"
        self.coy = w
        self.sys = None

    def doSystem(self, frt, pag, r, c, p, i, w):
        d1 = ""
        for sys in self.sys_data:
            if w in sys:
                d1 = sys[1]
                break
        if not d1:
            return "Invalid System Code"
        if w == "MST" and self.coy:
            return "Company Invalid with MST Code"
        self.sys = w
        self.mod_data = []
        for mod in pwctrl:
            if self.sys == mod[0]:
                self.mod_data.append(mod)
        self.ctl["data"] = self.mod_data

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.desc = ""
        for cod in self.mod_data:
            if self.code in cod:
                self.desc = cod[2]
                break
        if not self.desc:
            return "Invalid Password Code"
        self.df.loadEntry(frt, pag, p+1, data=self.desc)
        acc = self.sql.getRec("ctlpwr", cols=["pwd_desc", "pwd_pass"],
            where=[("pwd_cono", "=", self.coy), ("pwd_sys", "=", self.sys),
            ("pwd_code", "=", self.code)], limit=1)
        if not acc:
            self.new = "y"
        else:
            self.new = "n"
            self.df.loadEntry(frt, pag, p+2, data=b64Convert("decode", acc[1]))

    def doPwd(self, frt, pag, r, c, p, i, w):
        self.pwd = w

    def doEnd(self):
        if self.pwd:
            pwd = b64Convert("encode", self.pwd)
            if self.new == "y":
                self.sql.insRec("ctlpwr", data=[self.coy, self.sys, self.code,
                    self.desc, pwd])
            else:
                self.sql.updRec("ctlpwr", cols=["pwd_desc", "pwd_pass"],
                    data=[self.desc, pwd], where=[("pwd_cono", "=", self.coy),
                    ("pwd_sys", "=", self.sys), ("pwd_code", "=", self.code)])
            self.opts["mf"].dbm.commitDbase()
            self.df.focusField("T", 0, 1)
        elif self.new == "n":
            self.doDelete()

    def doDelete(self):
        self.sql.delRec("ctlpwr", where=[("pwd_cono", "=", self.coy),
            ("pwd_sys", "=", self.sys), ("pwd_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
