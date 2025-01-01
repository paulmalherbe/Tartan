"""
SYNOPSIS
    Asset Register Take on.

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
from TartanClasses import ASD, GetCtl, FileImport, Sql, TartanDialog
from tartanFunctions import askQuestion, projectDate, showError

class ar2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.gc = GetCtl(self.opts["mf"])
        assctl = self.gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.rordp = assctl["cta_rordp"]
        tabs = ["assgrp", "assmst", "assdep", "asstrn"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.dend = projectDate(self.opts["period"][1][0], -1)
        self.todat = 0
        self.imports = False
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def drawDialog(self):
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
                ("asm_code", "", 0, "Cod-Num"),
                ("asm_desc", "", 0, "Description", "Y")),
            "where": [("asm_cono", "=", self.opts["conum"])],
            "whera": [["C", "asm_group", 0, 0]]}
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.opts["conum"])]}
        self.fld = [
            (("T",0,0,0),"ID1",10,"Take-on Date","",
                self.dend,"N",self.doTakeOnDate,None,None,("efld",)),
            (("C",0,0,0),"IUA",3,"Grp","Asset Group",
                "r","N",self.doAssGrp,grp,None,None),
            (("C",0,0,1),"INa",7,"Cod-Num","Asset Code",
                "","N",self.doAssCod,cod,None,("notblank",)),
            (("C",0,0,2),"INA",30,"Description","Description",
                "","N",self.doDesc,None,None,("notblank",)),
            (("C",0,0,3),"INa",3,"Dep","Depreciation Code",
                "","N",self.doDepCode,dep,None,("notblank",)),
            (("C",0,0,4),"ONA",10,"Dp-Details"),
            (("C",0,0,5),"ID1",10,"Purch-Date","Purchase Date",
                0,"N",self.doPurDat,None,None,("efld",)),
            (("C",0,0,6),"IUD",10.2,"Cost","Original Cost",
                0,"N",self.doCost,None,None,("notzero",)),
            (("C",0,0,7),"IUD",10.2,"Coy-Dep","Company Depreciation",
                0,"N",self.doCDep,None,None,("efld",))]
        if self.rordp == "Y":
            self.fld.append((("C",0,0,8),"IUD",10.2,"Rec-Dep",
                "Receiver Depreciation",0,"N",self.doRDep,None,None,("efld",)))
        tnd = [[self.endPage,"y"]]
        txt = (self.exitPage,)
        cnd = [[self.endPage,"y"]]
        cxt = (self.exitPage,)
        but = ((("Import File",None,self.doImport,0,("T",0,0),("C",0,2),
            "Import a CSV or XLS File having the following fields: "\
            "Asset Group, Code, Description, Depreciation Code, "\
            "Purchase Date, Original Cost, Company Depeciation and "\
            "Receiver Depreciation if applicable"),))
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            rows=(15,), tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doTakeOnDate(self, frt, pag, r, c, p, i, w):
        if w < self.dend:
            return "Invalid Date, Too Far in the Past"
        self.todat = w

    def doAssGrp(self, frt, pag, r, c, p, i, w):
        self.group = w
        col = ["asg_depcod"]
        whr = [
            ("asg_cono", "=", self.opts["conum"]),
            ("asg_group", "=", self.group)]
        acc = self.sql.getRec("assgrp", cols=col, where=whr, limit=1)
        if not acc:
            return "Invalid Asset Group"
        self.depcod = acc[0]

    def doImport(self):
        self.df.closeProcess()
        self.imports = True
        impcol = []
        for num, fld in enumerate(self.fld[1:]):
            if fld[0][3] == 4:
                continue
            if num > 4:
                num -= 1
            impcol.append([fld[4], num, fld[1][1:], fld[2]])
        fi = FileImport(self.opts["mf"], impcol=impcol)
        err = False
        for row, data in enumerate(fi.impdat):
            funcs = ["doAssGrp", "doAssCod", "doDesc", "doDepCode",
                "doPurDat", "doCost", "doCDep"]
            if self.rordp == "Y":
                funcs.append("doRDep")
            for col, func in enumerate(funcs):
                err = getattr(self, "%s" % func)("", 0, 0, 0, 0, 0, data[col])
                if err:
                    showError(self.opts["mf"].body, "Import Error",
                        """Row %s Column %s - %s - %s

Please Correct the Import File and Try Again.""" % (row, col, data[col], err))
                    break
            if err:
                break
            self.endPage()
        if err:
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.opts["mf"].dbm.commitDbase()
        self.opts["mf"].closeLoop()

    def doAssCod(self, frt, pag, r, c, p, i, w):
        self.code = w
        acc = self.sql.getRec("assmst", cols=["asm_desc"],
            where=[("asm_cono", "=", self.opts["conum"]), ("asm_group", "=",
            self.group), ("asm_code", "=", w)], limit=1)
        if acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="Asset Exists",
                mess="""Asset already exists, Replace?

Please Note that if you decide to Replace the Asset, the Original Asset will be Deleted along with any History which may exist.""", default="no")
            if ok == "no":
                return "Invalid Asset"
            self.sql.delRec("assmst", where=[("asm_cono", "=",
                self.opts["conum"]), ("asm_group", "=", self.group),
                ("asm_code", "=", self.code)])
            self.sql.delRec("asstrn", where=[("ast_cono", "=",
                self.opts["conum"]), ("ast_group", "=", self.group),
                ("ast_code", "=", self.code)])
            if not self.imports:
                self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w
        if not self.imports:
            self.df.loadEntry(frt, pag, p+1, data=self.depcod)

    def doDepCode(self, frt, pag, r, c, p, i, w):
        col = ["asd_rate1r", "asd_desc"]
        chk = self.sql.getRec("assdep", cols=col, where=[("asd_cono",
            "=", self.opts["conum"]), ("asd_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Depreciation Code"
        self.rate1r = chk[0]
        if not self.imports:
            self.df.loadEntry(frt, pag, p+1, data=chk[1])

    def doPurDat(self, frt, pag, r, c, p, i, w):
        if w > self.todat:
            return "Invalid Date, After Financial Period"
        self.purdat = w

    def doCost(self, frt, pag, r, c, p, i, w):
        self.ccst = w
        if self.rordp == "Y":
            self.rcst = w
        else:
            self.rcst = 0

    def doCDep(self, frt, pag, r, c, p, i, w):
        self.cdep = float(ASD(0) - ASD(w))
        if self.rordp == "N":
            self.rdep = 0
            return
        if not self.rate1r:
            self.rdep = 0
            if not self.imports:
                self.df.loadEntry(frt, pag, p+1, data=self.rdep)
            return "sk1"

    def doRDep(self, frt, pag, r, c, p, i, w):
        self.rdep = float(ASD(0) - ASD(w))

    def endPage(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
            return
        data = [self.opts["conum"], self.group, self.code, self.desc,
            self.depcod]
        self.sql.insRec("assmst", data=data)
        data = [self.opts["conum"], self.group, self.code, 3, "Take-On",
            "Take-On", self.purdat, 1, self.ccst, self.rcst, 0,
            int(self.purdat / 100), "Original Cost", "", "",
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("asstrn", data=data)
        if self.cdep or self.rdep:
            data = [self.opts["conum"], self.group, self.code, 3, "Take-On",
                "Take-On", self.todat, 4, self.cdep, self.rdep, 0,
                int(self.todat / 100), "Accumulated Depreciation",
                "", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("asstrn", data=data)
        if not self.imports:
            self.df.advanceLine(0)

    def exitPage(self):
        self.df.closeProcess()
        if self.df.frt == "C":
            self.opts["mf"].dbm.commitDbase()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
