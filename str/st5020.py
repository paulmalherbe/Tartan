"""
SYNOPSIS
    Stores Stock Take Returns.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2022 Paul Malherbe.

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
from TartanClasses import FileImport, GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import askChoice, getCost, showError

class st5020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strloc", "strgrp", "strmf1",
            "strmf2", "strgmu", "strcmu", "strprc", "strtrn", "strvar"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.last = 0
        return True

    def dataHeader(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stores Ledger Stock Take Returns (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        gpm = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        stm1 = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_group", "", 0, "Grp"),
                ("st1_code", "", 0, "Product Code"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "not", "in", ("R", "X"))],
            "whera": [["T", "st1_group", 4, 0]],
            "order": "st1_group, st1_code",
            "index": 1}
        r1s = (("Grp/Code","N"),("Bin Number","B"))
        r2s = (("Yes","Y"),("No","N"))
        r3s = (("No","N"),("Last","L"),("Average","A"))
        if self.locs == "N":
            self.loc = "1"
            fld = []
            idx = 0
        else:
            fld = [(("T",0,0,0),"IUA",1,"Location","",
                "","N",self.doLoc,loc,None,("efld",))]
            idx = 1
        fld.extend([
            (("T",0,idx,0),("IRB",r2s),0,"Auto Sequence","",
                "N","N",self.doAuto,None,None,None),
            (("T",0,idx+1,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,idx+2,0),"IUA",8,"First Bin Number","",
                "","N",self.doFbin,None,None,("efld",)),
            (("T",0,idx+3,0),"IUA",3,"First Group","",
                "","N",self.doFgrp,gpm,None,None),
            (("T",0,idx+4,0),"INA",20,"First Code","",
                "","N",self.doFcode,stm1,None,None),
            (("T",0,idx+5,0),("IRB",r3s),0,"Cost Prices","",
                "N","N",self.doCosts,None,None,None)])
        tnd = ((self.endPage1,"y"),)
        txt = (self.exitPage1,)
        self.df1 = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Location Code"
        self.loc = w
        chk = self.sql.getRec("strvar", where=[("stv_cono", "=",
            self.opts["conum"]), ("stv_loc", "=", self.loc)])
        if chk:
            self.df1.setWidget(self.df1.mstFrame, "hide")
            but = (("Continue", "C"), ("Delete", "D"), ("Exit", "E"))
            ok = askChoice(self.opts["mf"].body, "Existing",
                "There Are Still Un-Merged Transactions.", butt=but,
                default="Continue")
            if ok == "E":
                return "xt"
            if ok == "D":
                self.sql.delRec("strvar", where=[("stv_cono", "=",
                    self.opts["conum"]), ("stv_loc", "=", self.loc)])
                self.opts["mf"].dbm.commitDbase(ask=True,
                    mess="Would you like to COMMIT Deletions?")
                if self.opts["mf"].dbm.commit == "no":
                    self.df1.setWidget(self.df1.mstFrame, "show")
                    return "rf"
            self.df1.setWidget(self.df1.mstFrame, "show")

    def doAuto(self, frt, pag, r, c, p, i, w):
        self.auto = w
        if self.auto == "N":
            return "sk4"

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w
        if w == "N":
            return "sk1"

    def doFbin(self, frt, pag, r, c, p, i, w):
        self.fbin = w
        self.fgrp = ""
        self.fcode = ""
        return "sk2"

    def doFgrp(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
        self.fgrp = w
        if not self.fgrp:
            self.fcode = ""
            self.df1.loadEntry(frt, pag, p+1, data=self.fcode)
            return "sk1"

    def doFcode(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("strmf1", cols=["st1_type"],
                where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                "=", self.fgrp), ("st1_code", "=", w)], limit=1)
            if not acc:
                return "Invalid Code"
            if acc[0] == "R":
                return "Invalid Code (Recipe Item)"
            if acc[0] == "X":
                return "Invalid Code (Redundant Item)"
        self.fcode = w

    def doCosts(self, frt, pag, r, c, p, i, w):
        self.costs = w

    def endPage1(self):
        self.df1.closeProcess()
        self.dataBody()
        if self.auto == "Y":
            whr = [("st1_cono", "=", self.opts["conum"])]
            if self.sort == "N":
                if self.fgrp:
                    whr.append(("st1_group", ">=", self.fgrp))
                if self.fcode:
                    whr.append(("st1_code", ">=", self.fcode))
                odr = "st1_group, st1_code"
            else:
                whr.append(("st2_bin", "=", self.fbin))
                odr = "st2_bin, st2_group, st2_code"
            whr.extend([("st1_type", "not", "in", ("R","X")),
                ("st2_cono=st1_cono",), ("st2_group=st1_group",),
                ("st2_code=st1_code",), ("st2_loc", "=", self.loc)])
            self.codes = self.sql.getRec(tables=["strmf1", "strmf2"],
                cols=["st1_group", "st1_code", "st1_desc", "st1_uoi",
                "st2_bin"], where=whr, order=odr)
            if not self.codes:
                showError(self.opts["mf"].body, "No Records",
                    "No Stock Records on File")
                self.exitPage2()
            else:
                self.doNextOne()

    def exitPage1(self):
        self.df1.closeProcess()
        self.opts["mf"].closeLoop()

    def dataBody(self):
        gpm = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        stm2 = {
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
            "index": 1}
        if self.auto == "Y":
            fld = [
                (("C",0,0,0),"ONA",3,"Grp"),
                (("C",0,0,1),"ONA",20,"Product Code")]
        else:
            fld = [
                (("C",0,0,0),"INA",3,"Grp","Product Group",
                    "r","N",self.doGroup2,gpm,None,("notblank",)),
                (("C",0,0,1),"INA",20,"Product Code","",
                    "","N",self.doCode2,stm2,None,("notblank",))]
        fld.extend([
            (("C",0,0,2),"ONA",16,"Description"),
            (("C",0,0,3),"ONA",10,"U.O.I"),
            (("C",0,0,4),"OUA",8,"Bin")])
        if self.costs == "N":
            fld.append((("C",0,0,5),"OUD",9.2,"Unit-Cost"))
        else:
            fld.append((("C",0,0,5),"IUD",9.2,"Unit-Cost","",
                "","N",self.doUcost,None,None,("efld",)))
        fld.append((("C",0,0,6),"ISD",9.2,"Quantity","",
                "","N",self.doQty,None,None,("efld",)))
        if self.auto == "Y":
            but = None
        else:
            txt = "Import a Stock Take Return from a CSV or XLS file "\
                "having the following fields: Grp, Code, "
            if self.costs == "N":
                txt += "Quantity"
            else:
                txt += "Cost Price, Quantity"
            but = [("Import",None,self.doImport,0,("C",0,1),("C",0,2),txt)]
        cnd = ((self.endPage2,"y"),)
        cxt = (self.exitPage2,)
        self.df2 = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            butt=but, cend=cnd, cxit=cxt)

    def doImport(self):
        self.df2.setWidget(self.df2.B0, state="disabled")
        self.df2.setWidget(self.df2.mstFrame, state="hide")
        skp = ["stv_cono", "stv_loc", "stv_bin"]
        if self.costs == "N":
            skp.append("stv_ucost")
        fi = FileImport(self.opts["mf"], imptab="strvar", impskp=skp)
        sp = ProgressBar(self.opts["mf"].body,
            typ="Importing Stock Take", mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            chk = self.sql.getRec("strmf2", where=[("st2_cono",
                "=", self.opts["conum"]), ("st2_group", "=", line[0]),
                ("st2_code", "=", line[1]), ("st2_loc", "=", self.loc)],
                limit=1)
            if not chk:
                err = "%s %s Does Not Exist" % (line[0], line[1])
                break
            data = [self.opts["conum"], line[0], line[1], self.loc]
            data.append(chk[self.sql.strmf2_col.index("st2_bin")])
            if self.costs == "N":
                data.append(line[2])
                data.append(getCost(self.sql, self.opts["conum"], line[0],
                    line[1], loc=self.loc, ind="I"))
            else:
                if line[3]:
                    data.append(line[3])
                else:
                    data.append(getCost(self.sql, self.opts["conum"], line[0],
                        line[1], loc=self.loc, ind=self.costs))
                data.append(line[2])
            whr = [("stv_cono", "=", data[0]), ("stv_group", "=", data[1]),
                ("stv_code", "=", data[2]), ("stv_loc", "=", self.loc)]
            var = self.sql.getRec("strvar", where=whr, limit=1)
            if var:
                self.sql.delRec("strvar", where=whr)
            self.sql.insRec("strvar", data=data)
        sp.closeProgress()
        if err:
            err = "Line %s: %s" % ((num + 1), err)
            showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
            self.opts["mf"].dbm.rollbackDbase()
        elif fi.impdat:
            self.opts["mf"].dbm.commitDbase(True)
        self.df2.setWidget(self.df2.mstFrame, state="show")
        self.df2.focusField(self.df2.frt, self.df2.pag, self.df2.col)

    def doGroup2(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]),
            ("gpm_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Group"
        self.group2 = w

    def doCode2(self, frt, pag, r, c, p, i, w):
        ac1 = self.sql.getRec("strmf1", cols=["st1_type", "st1_desc",
            "st1_uoi"], where=[("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.group2), ("st1_code", "=", w)], limit=1)
        if not ac1:
            return "Invalid Code"
        if ac1[0] == "R":
            return "Invalid Code (Recipe Item)"
        if ac1[0] == "X":
            return "Invalid Code (Redundant Item)"
        ac2 = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group2),
            ("st2_code", "=", w), ("st2_loc", "=", self.loc)], limit=1)
        if not ac2:
            return "Invalid Location For This Product"
        self.code2 = w
        self.df2.loadEntry("C", 0, p+1, data=ac1[1])
        self.df2.loadEntry("C", 0, p+2, data=ac1[2])
        self.bin = ac2[self.sql.strmf2_col.index("st2_bin")]
        self.df2.loadEntry("C", 0, p+3, data=self.bin)
        self.ucost, qty = self.doGetValues()
        self.df2.loadEntry("C", 0, p+4, data=self.ucost)
        self.df2.loadEntry("C", 0, p+5, data=qty)

    def doUcost(self, frt, pag, r, c, p, i, w):
        self.ucost = w

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w

    def endPage2(self):
        self.updateTables()
        self.df2.advanceLine(0)
        if self.auto == "Y":
            self.last += 1
            self.doNextOne()

    def updateTables(self):
        # Stores Variance Transaction
        whr = [
            ("stv_cono", "=", self.opts["conum"]),
            ("stv_group", "=", self.group2),
            ("stv_code", "=", self.code2),
            ("stv_loc", "=", self.loc)]
        if self.sql.getRec("strvar", where=whr, limit=1):
            self.sql.delRec("strvar", where=whr)
        self.sql.insRec("strvar", data=[self.opts["conum"], self.group2,
            self.code2, self.loc, self.bin, self.qty, self.ucost])
        self.opts["mf"].dbm.commitDbase()

    def doNextOne(self):
        if self.last == len(self.codes):
            self.exitPage2()
        else:
            data = self.codes[self.last]
            self.group2 = data[0]
            self.code2 = data[1]
            self.bin = data[4]
            self.ucost, qty = self.doGetValues()
            data.extend([self.ucost, qty])
            p = self.df2.pos
            if self.costs == "N":
                xs = 6
            else:
                xs = 5
            for x in range(0, 7):
                self.df2.loadEntry("C", 0, (p + x - xs), data=data[x])
            self.df2.focusField("C", 0, p)

    def doGetValues(self):
        var = self.sql.getRec("strvar", where=[("stv_cono", "=",
            self.opts["conum"]), ("stv_group", "=", self.group2),
            ("stv_code", "=", self.code2), ("stv_loc", "=", self.loc)],
            limit=1)
        if var:
            qty = var[self.sql.strvar_col.index("stv_qty")]
            cst = var[self.sql.strvar_col.index("stv_ucost")]
            if not cst:
                bal = self.doGetCost(self.group2, self.code2)
                cst = bal[0]
        else:
            cst, qty = self.doGetCost(self.group2, self.code2)
        return (cst, qty)

    def doGetCost(self, grp, code):
        if self.costs == "N":
            ind = "I"
        else:
            ind = self.costs
        cost, bal = getCost(self.sql, self.opts["conum"], grp, code,
            loc=self.loc, ind=ind, bal=True)
        return (cost, bal[0])

    def exitPage2(self):
        self.df2.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
