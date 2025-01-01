"""
SYNOPSIS
    Stores Transfers.

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
from TartanClasses import ASD, CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, showError

class st2040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strmf1", "strmf2",
            "strtrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        if self.locs == "N":
            showError(self.opts["mf"].body, "Error",
                "Multiple Locations Are Not Enabled")
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def dataHeader(self):
        gpm = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        stm = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_group", "", 0, "Grp"),
                ("st1_code", "", 0, "Product Code"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "not", "in", ("R", "X"))],
            "whera": [["C", "st1_group", 0, 0]],
            "order": "st1_group, st1_code",
            "index": 1}
        stl = {
            "stype": "R",
            "tables": ("strloc", "strmf2"),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Location", "Y")),
            "where": [
                ("srl_cono", "=", self.opts["conum"]),
                ("srl_loc=st2_loc",),
                ("st2_cono=srl_cono",)],
            "whera": [["C", "st2_group", 0], ["C", "st2_code", 1]],
            "order": "srl_loc",
            "index": 0}
        fld = [
            (("T",0,0,0),"INa",7,"Transfer Number","",
                "","N",self.doTrf,None,None,("notblank",)),
            (("T",0,0,0),"ID1",10,"Date","Transfer Date",
                self.sysdtw,"N",self.doDte,None,None,("efld",)),
            (("C",0,0,0),"IUA",3,"Grp","Product Group",
                "r","N",self.doGroup,gpm,None,("notblank",)),
            (("C",0,0,1),"INA",20,"Product Code","",
                "","N",self.doCode,stm,None,("notblank",)),
            (("C",0,0,2),"ONA",25,"Description"),
            (("C",0,0,3),"ONA",10,"U.O.I"),
            (("C",0,0,4),"ISD",9.2,"Quantity","",
                "","N",self.doQty,None,None,("notzero",)),
            (("C",0,0,5),"IUA",1,"F","From Location",
                "","N",self.doLoc1,stl,None,("notblank",)),
            (("C",0,0,6),"IUA",1,"T","To Location",
                "","N",self.doLoc2,stl,None,("notblank",)),
            (("C",0,0,7),"ISD",9.2,"Unit-Cost","Unit Cost Price",
                "","N",None,None,None,("notzero",)),
            (("C",0,0,8),"INA",(15,30),"Details","Transaction Details",
                "","N",self.doTrnDet,None,None,None)]
        row = (15,)
        tnd = ((self.endPage0,"n"),)
        txt = (self.exitPage0,)
        cnd = ((self.endPage1,"y"),)
        cxt = (self.exitPage1,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, rows=row,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doTrf(self, frt, pag, r, c, p, i, w):
        self.trf = w

    def doDte(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.dte = w
        self.curdt = int(self.dte / 100)
        self.batno = "S%s" % self.curdt

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group"

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        acc = self.sql.getRec("strmf1", cols=["st1_type", "st1_desc",
            "st1_uoi"], where=[("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.group), ("st1_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        if acc[0] == "R":
            return "Invalid Code (Recipe Item)"
        if acc[0] == "X":
            return "Invalid Code (Redundant)"
        self.df.loadEntry("C", pag, p+1, data=acc[1])
        self.df.loadEntry("C", pag, p+2, data=acc[2])

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w

    def doLoc1(self, frt, pag, r, c, p, i, w):
        self.acc = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group), ("st2_code",
            "=", self.code), ("st2_loc", "=", w)], limit=1)
        if not self.acc:
            return "Invalid Location For This Product"
        self.loc1 = w
        self.extractCost()
        self.amt = round((self.qty * self.ucost), 2)
        self.df.loadEntry("C", pag, p+2, data=self.ucost)

    def doLoc2(self, frt, pag, r, c, p, i, w):
        if w == self.loc1:
            return "Invalid Location, Same as From"
        self.newloc = "N"
        acc = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group), ("st2_code",
            "=", self.code), ("st2_loc", "=", w)], limit=1)
        if not acc:
            ok = askQuestion(self.opts["mf"].body, "New Location",
                "This location does not exist for this product. " \
                "Are you sure that you want to create it?")
            if ok == "yes":
                self.newloc = "Y"
            else:
                return "Invalid Location For This Product"
        self.loc2 = w
        return "sk1"

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def endPage0(self):
        self.df.focusField("C", 0, 1)

    def endPage1(self):
        self.updateTables()
        self.opts["mf"].dbm.commitDbase()
        self.df.advanceLine(0)

    def exitPage0(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def exitPage1(self):
        self.df.focusField("T", 0, 1)

    def extractCost(self):
        qbal = 0
        vbal = 0
        self.ucost = 0
        stt_rslt = self.sql.getRec("strtrn",
            cols=["round(sum(stt_qty),2)", "round(sum(stt_cost),2)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_group", "=",
            self.group), ("stt_code", "=", self.code), ("stt_loc", "=",
            self.loc1)])
        if stt_rslt:
            qbal = CCD(stt_rslt[0][0], "SD", 13.2).work
            vbal = CCD(stt_rslt[0][1], "SD", 13.2).work
        if qbal:
            self.ucost = round((vbal / qbal), 2)

    def updateTables(self):
        # Stores Ledger Transaction
        qty = float(ASD(0) - ASD(self.qty))
        val = float(ASD(0) - ASD(self.amt))
        if qty >= 0:
            rtn = 3
        else:
            rtn = 4
        self.sql.insRec("strtrn", data=[self.opts["conum"], self.group,
            self.code, self.loc1, self.dte, rtn, self.trf, self.batno, "",
            qty, val, 0, self.curdt, self.trndet, 0, "", "", "STR", 0, "N",
            self.opts["capnm"], self.sysdtw, 0])
        # Stores Ledger Transaction
        if self.qty >= 0:
            rtn = 3
        else:
            rtn = 4
        if self.newloc == "Y":
            self.acc[self.sql.strmf2_col.index("st2_loc")] = self.loc2
            self.sql.insRec("strmf2", data=self.acc)
        self.sql.insRec("strtrn", data=[self.opts["conum"], self.group,
            self.code, self.loc2, self.dte, rtn, self.trf, self.batno, "",
            self.qty, self.amt, 0, self.curdt, self.trndet, 0, "", "",
            "STR", 0, "", self.opts["capnm"], self.sysdtw, 0])

# vim:set ts=4 sw=4 sts=4 expandtab:
