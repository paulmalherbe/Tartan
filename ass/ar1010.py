"""
SYNOPSIS
    Asset Register Masterfile Maintenance.

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

import time
from TartanClasses import Sql, TartanDialog

class ar1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "assgrp", "assmst",
            "assdep", "asstrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        cod = {
            "stype": "R",
            "tables": ("assmst",),
            "cols": (
                ("asm_code", "", 0, "Code"),
                ("asm_desc", "", 0, "Description", "Y")),
            "where": [("asm_cono", "=", self.opts["conum"])],
            "whera": (("T", "asm_group", 0, 0),)}
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"IUA",3,"Group","Asset Group",
                "","Y",self.doGroup,grp,None,("notblank",)),
            (("T",0,1,0),"INa",7,"Code","Asset Code",
                "","N",self.doCode,cod,None,("notblank",)),
            (("T",0,2,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"INa",3,"Depreciation Code","",
                "","N",self.doDepCode,dep,None,None),
            (("T",0,3,0),"ONA",34,""))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doGroup(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assgrp", cols=["asg_desc"],
            where=[("asg_cono", "=", self.opts["conum"]),
            ("asg_group", "=",w)], limit=1)
        if not acc:
            return "Invalid Asset Group"
        self.group = w

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.old = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_group", "=", self.group),
            ("asm_code", "=", self.code)], limit=1)
        if not self.old:
            return "Asset Does Not Exist"
        for num, dat in enumerate(self.old[1:-1]):
            self.df.loadEntry(frt, pag, num, data=dat)
        dep = self.sql.getRec("assdep", cols=["asd_desc"],
            where=[("asd_cono", "=", self.opts["conum"]), ("asd_code", "=",
            self.old[self.sql.assmst_col.index("asm_depcod")])], limit=1)
        self.df.loadEntry(frt, pag, 4, data=dep[0])

    def doDepCode(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("assdep", cols=["asd_desc"],
            where=[("asd_cono", "=", self.opts["conum"]), ("asd_code", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Depreciation Code"
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

    def doDelete(self):
        trs = self.sql.getRec("asstrn", cols=["count(*)"],
            where=[("ast_cono", "=", self.opts["conum"]), ("ast_group", "=",
            self.group), ("ast_code", "=", self.code)], limit=1)
        if trs[0]:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("assmst", where=[("asm_cono", "=", self.opts["conum"]),
            ("asm_group", "=", self.group), ("asm_code", "=", self.code)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["assmst", "D", "%03i%-3s%-7s" % \
            (self.opts["conum"], self.group, self.code), "", dte,
            self.opts["capnm"], "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0]) - 1):
            data.append(self.df.t_work[0][0][x])
        col = self.sql.assmst_col
        data.append(self.old[col.index("asm_xflag")])
        if data != self.old:
            self.sql.updRec("assmst", data=data, where=[("asm_cono",
                "=", self.opts["conum"]), ("asm_group", "=", self.group),
                ("asm_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["assmst", "U",
                        "%03i%-3s%-7s" % (self.opts["conum"], self.group,
                        self.code), col[num], dte, self.opts["capnm"],
                        str(dat), str(data[num]), "", 0])
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
