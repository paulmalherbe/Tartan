"""
SYNOPSIS
    Asset Groups File Maintenance.

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

from TartanClasses import GetCtl, Sql, TartanDialog

class arc310(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["assdep", "assgrp", "assmst",
            "genmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.glint = assctl["cta_glint"]
        return True

    def mainProcess(self):
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.opts["conum"])]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])],
            "order": "glm_acno"}
        fld = [
            (("T",0,0,0),"IUA",3,"Asset Group","",
                "","N",self.doGroup,grp,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"INa",3,"Depreciation Code","",
                "","N",self.doDepCode,dep,None,None),
            (("T",0,2,0),"ONA",34,"")]
        if self.glint == "Y":
            fld.extend([
                (("T",0,3,0),"IUI",7,"Asset Account","",
                    "","N",self.doAsset,glm,None,("notzero",)),
                (("T",0,3,0),"ONA",30,""),
                (("T",0,4,0),"IUI",7,"Accum Account","",
                    "","N",self.doAccum,glm,None,("notzero",)),
                (("T",0,4,0),"ONA",30,""),
                (("T",0,5,0),"IUI",7,"Expense Account","",
                    "","N",self.doExpense,glm,None,("notzero",)),
                (("T",0,5,0),"ONA",30,"")])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt)

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w
        self.acc = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.opts["conum"]), ("asg_group", "=", self.group)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.acc[2])
            self.df.loadEntry(frt, pag, p+2, data=self.acc[3])
            dep = self.sql.getRec("assdep", cols=["asd_desc"],
                where=[("asd_cono", "=", self.opts["conum"]),
                ("asd_code", "=", self.acc[3])], limit=1)
            if dep:
                self.df.loadEntry(frt, pag, p+3, data=dep[0])
            if self.glint == "N":
                return
            self.df.loadEntry(frt, pag, p+4, data=self.acc[4])
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                self.acc[4])], limit=1)
            if des:
                self.df.loadEntry("T", pag, p+5, data=des[0])
            self.df.loadEntry(frt, pag, p+6, data=self.acc[5])
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                self.acc[5])], limit=1)
            if des:
                self.df.loadEntry("T", pag, p+7, data=des[0])
            self.df.loadEntry(frt, pag, p+8, data=self.acc[6])
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                self.acc[6])], limit=1)
            if des:
                self.df.loadEntry("T", pag, p+9, data=des[0])

    def doDepCode(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("assdep", cols=["asd_desc"],
            where=[("asd_cono", "=", self.opts["conum"]), ("asd_code",
            "=", w)], limit=1)
        if not chk:
            return "Invalid Depreciation Code"
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

    def doAsset(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry("T", pag, p+1, data=acc[0])

    def doAccum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry("T", pag, p+1, data=acc[0])

    def doExpense(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry("T", pag, p+1, data=acc[0])

    def doDelete(self):
        chk = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_group", "=", self.group)])
        if chk:
            return "Group in Use, Not Deleted"
        self.sql.delRec("assgrp", where=[("asg_cono", "=", self.opts["conum"]),
            ("asg_group", "=", self.group)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if x == 3 or (self.glint == "Y" and x in (5, 7, 9)):
                continue
            data.append(self.df.t_work[0][0][x])
        if self.glint == "N":
            data.extend([0, 0, 0])
        if self.new == "Y":
            self.sql.insRec("assgrp", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.assgrp_col
            data.append(self.acc[col.index("asg_xflag")])
            self.sql.updRec("assgrp", data=data, where=[("asg_cono", "=",
                self.opts["conum"]), ("asg_group", "=", self.group)])
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
