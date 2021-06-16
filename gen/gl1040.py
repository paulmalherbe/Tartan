"""
SYNOPSIS
    General Ledger Detail Records Creation, Deletion and Amendments.

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

class gl1040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.buildScreen()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["gendtm", "gendtt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        return True

    def buildScreen(self):
        cod_sel = {
            "stype": "R",
            "tables": ("gendtm",),
            "cols": (
                ("gdm_code", "", 0, "Cod"),
                ("gdm_desc", "", 0, "Description", "Y")),
            "where": [("gdm_cono", "=", self.opts["conum"])]}
        per_sel = {
            "stype": "R",
            "tables": ("gendtt",),
            "cols": (
                ("gdt_curdt", "", 0, "Period"),
                ("gdt_value", "", 0, "Value")),
            "where": [
                ("gdt_cono", "=", self.opts["conum"]),
                ("gdt_curdt", "between", self.sper, self.eper)],
            "whera": (("T","gdt_code", 0),)}
        fld = (
            (("T",0,0,0,4),"INa",2,"Code","",
                "","Y",self.doCode,cod_sel,None,("notblank",)),
            (("T",0,0,0),"INA",30,"Description","",
                "","N",self.doDesc,None,self.doDelCode,("notblank",)),
            (("C",0,0,0),"ID2",7,"Period","Financial Period",
                "p","N",self.doPeriod,per_sel,None,None),
            (("C",0,0,1),"ISD",13.2,"Value","Period Value",
                "","N",self.doValue,None,self.doDelPeriod,None))
        row = (17,)
        but = (
            ("Cancel",None,self.doCancel,0,("C",0,1),("T",0,1)),
            ("Quit",None,self.exitTops,1,None,None))
        txt = (self.exitTops,)
        tnd = ((self.endTops,"y"),)
        cnd = ((self.endData,"y"),)
        cxt = (self.exitData,)
        self.df = TartanDialog(self.opts["mf"], sc=None, eflds=fld, rows=row,
            butt=but, tend=tnd, cend=cnd, txit=txt, cxit=cxt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.oldm = self.sql.getRec("gendtm", where=[("gdm_cono",
            "=", self.opts["conum"]), ("gdm_code", "=", self.code)], limit=1)
        if not self.oldm:
            self.newcod = True
        else:
            self.newcod = False
            desc = self.oldm[self.sql.gendtm_col.index("gdm_desc")]
            self.df.loadEntry(frt, pag, p+1, data=desc)
            self.loadPeriods(focus=False)

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doDelCode(self):
        self.sql.delRec("gendtm", where=[("gdm_cono", "=", self.opts["conum"]),
            ("gdm_code", "=", self.code)])
        self.sql.delRec("gendtt", where=[("gdt_cono", "=", self.opts["conum"]),
            ("gdt_code", "=", self.code)])
        self.exitData()

    def endTops(self):
        data = [self.opts["conum"], self.code, self.desc]
        if self.newcod:
            self.sql.insRec("gendtm", data=data)
            self.df.focusField("C", 0, 1)
        else:
            if data != self.oldm[:len(data)]:
                col = self.sql.gendtm_col
                data.append(self.oldm[col.index("gdm_xflag")])
                self.sql.updRec("gendtm", data=data, where=[("gdm_cono",
                    "=", self.opts["conum"]), ("gdm_code", "=", self.code)])
            self.df.focusField("C", 0, self.col)

    def doPeriod(self, frt, pag, r, c, p, i, w):
        if w < self.sper or w > self.eper:
            return "Invalid Period"
        self.per = w
        self.oldt = self.sql.getRec("gendtt", where=[("gdt_cono",
            "=", self.opts["conum"]), ("gdt_code", "=", self.code),
            ("gdt_curdt", "=", self.per)], limit=1)
        if not self.oldt:
            self.newper = "y"
        else:
            self.newper = "n"
            val = self.oldt[self.sql.gendtt_col.index("gdt_value")]
            self.df.loadEntry(frt, pag, p+1, data=val)

    def doDelPeriod(self):
        if self.newper == "y":
            return
        self.sql.delRec("gendtt", where=[("gdt_cono", "=", self.opts["conum"]),
            ("gdt_code", "=", self.code), ("gdt_curdt", "=", self.per)])
        self.loadPeriods()

    def doValue(self, frt, pag, r, c, p, i, w):
        self.val = w

    def endData(self):
        data = [self.opts["conum"], self.code, self.per, self.val]
        if self.newper == "y":
            self.sql.insRec("gendtt", data=data)
        elif data != self.oldt[:len(data)]:
            col = self.sql.gendtt_col
            data.append(self.oldt[col.index("gdt_xflag")])
            self.sql.updRec("gendtt", data=data, where=[("gdt_cono",
                "=", self.opts["conum"]), ("gdt_code", "=", self.code),
                ("gdt_curdt", "=", self.per)])
        self.loadPeriods()

    def loadPeriods(self, focus=True):
        self.df.clearFrame("C", 0)
        pers = self.sql.getRec("gendtt", cols=["gdt_curdt", "gdt_value"],
            where=[("gdt_cono", "=", self.opts["conum"]), ("gdt_code", "=",
            self.code), ("gdt_curdt", "between", self.sper, self.eper)])
        if pers:
            for num, per in enumerate(pers):
                p = (num * 2)
                self.df.loadEntry("C", 0, p, data=per[0])
                self.df.loadEntry("C", 0, p + 1, data=per[1])
            self.col = p + 3
        else:
            self.col = 1
        if focus:
            self.df.focusField("C", 0, self.col)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def exitTops(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def exitData(self):
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
