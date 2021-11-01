"""
SYNOPSIS
    Stores Goods Received Notes.

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

import time
from TartanClasses import ASD, FileImport, GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, getCost, showError

class st2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.exit = False
            self.setPrinter()
            if not self.exit:
                self.dataHeader()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["gentrn", "strgrp", "strmf1",
            "strmf2", "strgmu", "strcmu", "strtrn", "strpom"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        self.fromad = strctl["cts_emadd"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["stk_soh", "stk_susp"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.stk_soh = ctlctl["stk_soh"]
            self.stk_susp = ctlctl["stk_susp"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        if self.locs == "N":
            self.loc = "1"
        return True

    def setPrinter(self):
        tit = ("Printer Selection",)
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=[], tend=((self.doPrtEnd,"y"),), txit=(self.doPrtExit,),
            view=("N","P"), mail=("N","Y"))
        self.opts["mf"].startLoop()

    def doPrtEnd(self):
        self.doPrtClose()

    def doPrtExit(self):
        self.exit = True
        self.doPrtClose()

    def doPrtClose(self):
        self.pr.closeProcess()
        self.opts["mf"].closeLoop()

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
                ("st1_type", "not", "in", ("R", "X")),
                ("st1_value_ind", "<>", "N")],
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
            "order": "st2_loc",
            "index": 0}
        fld = [
            (("T",0,0,0),"INa",9,"GRN Number","",
                "","Y",self.doGrv,None,None,("notblank",)),
            (("T",0,0,0),"ID1",10,"Date","GRN Date",
                self.sysdtw,"N",self.doDte,None,None,("efld",)),
            (("T",0,0,0),"INa",7,"Order Number","",
                "","N",self.doOrd,None,None,("efld",)),
            (("C",0,0,0),"IUA",3,"Grp","Product Group",
                "r","Y",self.doGroup,gpm,None,("notblank",)),
            (("C",0,0,1),"INA",(15,20),"Product Code","",
                "","N",self.doCode,stm,None,("notblank",)),
            (("C",0,0,2),"ONA",15,"Description"),
            (("C",0,0,3),"ONA",5,"U.O.I"),
            [("C",0,0,4),"IUA",1,"L","Location",
                "r","N",self.doLoc,stl,None,("notblank",)],
            (("C",0,0,5),"ISD",9.2,"Quantity","",
                "","N",self.doQty,None,None,("notzero",)),
            (("C",0,0,6),"IUD",9.2,"Unit-Cost","Unit Cost Price",
                "","N",self.doUcost,None,None,("notzero",)),
            (("C",0,0,7),"IUD",5.2,"Dis-%","Discount Percentage",
                "","N",self.doDisPer,None,None,("efld",)),
            (("C",0,0,8),"OSD",9.2,"Value")]
        tnd = ((self.endPage0,"n"),)
        txt = (self.exitPage0,)
        cnd = ((self.endPage1,"y"),)
        cxt = (self.exitPage1,)
        but = (
            ("Import",None,self.doImport,0,("C",0,1),(("T",0,1),("C",0,2)),
                "Import Stock from a CSV or XLS File"),
            ("StrQuery",None,self.doQuery,0,("C",0,1),(("T",0,1),("C",0,2))),
            ("Reprint",None,self.doReprint,0,("T",0,1),None),
            ("Cancel",None,self.doCancel,0,("C",0,1),(("T",0,1),("C",0,0))))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doGrv(self, frt, pag, r, c, p, i, w):
        self.grv = w
        self.cancel = False

    def doDte(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.dte = w
        self.dtw = self.df.t_disp[0][0][i]
        self.curdt = int(self.dte / 100)
        self.batno = "S%s" % self.curdt

    def doOrd(self, frt, pag, r, c, p, i, w):
        self.odr = w

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if self.locs == "Y":
            impcol = [["Location", 0, "UA", 1]]
            fld = [(("T",0,0,0),("IRB",(("Yes","Y"),("No","N"))),0,
                "Create Items","","N","N",self.doAllLoc,None,None,None,None,
                "Create Item in this location if it is a Valid item, i.e. "\
                "Already exists in another location")]
        else:
            impcol = []
            fld = []
            self.allloc = "N"
        impcol.extend([
            ["Group", 1, "UA", 3],
            ["Code", 2, "NA", 20],
            ["Quantity", 3, "UD", 10.2],
            ["Item Cost", 4, "UD", 10.2]])
        fi = FileImport(self.opts["mf"], impcol=impcol, impfld=fld)
        self.trdis = 0
        err = None
        for num, line in enumerate(fi.impdat):
            if len(line) != len(impcol):
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, len(impcol), len(line))
                break
            if self.locs == "Y":
                loc = line[0]
                idx = 1
            else:
                loc = "1"
                idx = 0
            self.loc = loc.work
            self.group = line[idx]
            self.code = line[idx+1]
            st1 = self.sql.getRec("strmf1", where=[("st1_group", "=",
                self.group), ("st1_code", "=", self.code), ("st1_type", "<>",
                "X")], limit=1)
            err = False
            if not st1:
                err = "Line %s: Invalid Group %s or Code %s" % ((num + 1),
                    self.group, self.code)
            elif st1[self.sql.strmf1_col.index("st1_type")] == "R":
                err = "Line %s: Invalid Code (Recipe Item)" % (num + 1)
            elif st1[self.sql.strmf1_col.index("st1_type")] == "X":
                err = "Line %s: Invalid Code (Redundant" % (num + 1)
            elif st1[self.sql.strmf1_col.index("st1_type")] == "N":
                err = "Line %s: Invalid Code (Value Indicator)" % (num + 1)
            if err:
                break
            self.desc = st1[self.sql.strmf1_col.index("st1_desc")]
            st2 = self.sql.getRec("strmf2", where=[("st2_loc", "=",
                self.loc), ("st2_group", "=", self.group), ("st2_code", "=",
                self.code)], limit=1)
            if not st2 and self.allloc == "Y":
                st2 = self.sql.getRec("strmf2", where=[("st2_loc", "=",
                    "1"), ("st2_group", "=", self.group), ("st2_code", "=",
                    self.code)], limit=1)
                if st2:
                    st2[self.sql.strmf2_col.index("st2_loc")] = self.loc
                    st2[self.sql.strmf2_col.index("st2_bin")] = ""
                    st2[self.sql.strmf2_col.index("st2_reord_ind")] = "A"
                    st2[self.sql.strmf2_col.index("st2_reord_level")] = 0
                    st2[self.sql.strmf2_col.index("st2_reord_qty")] = 0
                    self.sql.insRec("strmf2", data=st2)
            if not st2:
                err = "Line %s: Invalid Location %s" % ((num + 1), self.loc)
                break
            self.qty = line[idx + 2]
            self.tcost = round((self.qty * line[idx + 3]), 2)
            self.usell = 0.00
            self.updateTables()
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        elif fi.impdat:
            self.opts["mf"].dbm.commitDbase()
        self.df.enableButtonsTags(state=state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doAllLoc(self, obj, w):
        self.allloc = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w
        acc = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Group"

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        acc = self.sql.getRec("strmf1", cols=["st1_type", "st1_desc", "st1_uoi",
            "st1_value_ind"], where=[("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.group), ("st1_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        if acc[0] == "R":
            return "Invalid Code (Recipe Item)"
        if acc[0] == "X":
            return "Invalid Code (Redundant"
        if acc[3] == "N":
            return "Invalid Code (Value Indicator)"
        self.desc = acc[1]
        self.uoi = acc[2]
        self.df.loadEntry("C", pag, p+1, data=self.desc)
        self.df.loadEntry("C", pag, p+2, data=self.uoi)
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry("C", pag, p+3, data=self.loc)
            no = self.checkLoc()
            if no:
                return no
            return "sk3"

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.loc = w
        no = self.checkLoc()
        if no:
            return no

    def checkLoc(self):
        acc = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group), ("st2_code",
            "=", self.code), ("st2_loc", "=", self.loc)], limit=1)
        if not acc:
            return "Invalid Location For This Product"

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w
        # Last Cost Price
        lcost = getCost(self.sql, self.opts["conum"], self.group, self.code,
            loc=self.loc, qty=1, ind="L")
        self.df.loadEntry(frt, pag, p+1, data=lcost)

    def doUcost(self, frt, pag, r, c, p, i, w):
        self.ucost = w
        self.tcost = round((self.qty * self.ucost), 2)

    def doDisPer(self, frt, pag, r, c, p, i, w):
        self.trdis = w
        udis = round((self.ucost * self.trdis / 100), 2)
        tdis = round((self.tcost * self.trdis / 100), 2)
        self.ucost = float(ASD(self.ucost) - ASD(udis))
        self.tcost = float(ASD(self.tcost) - ASD(tdis))
        self.df.loadEntry(frt, pag, p+1, data=self.tcost)

    def endPage0(self):
        self.df.focusField("C", 0, 1)

    def endPage1(self):
        self.updateTables()
        self.df.advanceLine(0)

    def exitPage0(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def exitPage1(self):
        if not self.cancel and self.df.col != 1:
            self.opts["mf"].dbm.commitDbase()
            self.doPrintDoc(self.pr.repprt, self.pr.repeml)
        else:
            self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doCancel(self):
        ok = askQuestion(self.opts["mf"].body, "Cancel",
            "Are You Sure that you want to Cancel this Goods Received Note?",
            default="no")
        if ok == "yes":
            self.cancel = True
            self.exitPage1()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def updateTables(self):
        # Stores Ledger Transaction
        data = [self.opts["conum"], self.group, self.code, self.loc,
            self.dte, 1, self.grv, self.batno, self.odr, self.qty,
            self.tcost, 0, self.curdt, self.desc, 0, "", "", "STR",
            self.trdis, "N", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("strtrn", data=data)
        if self.glint == "N":
            return
        # General Ledger Control Transaction (Stock On Hand)
        data = [self.opts["conum"], self.stk_soh, self.curdt, self.dte, 5,
            self.grv, self.batno, self.tcost, 0, self.code, "N", "", 0,
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("gentrn", data=data)
        # General Ledger Control Transaction (Stock Suspense)
        val = float(ASD(0) - ASD(self.tcost))
        data = [self.opts["conum"], self.stk_susp, self.curdt, self.dte, 5,
            self.grv, self.batno, val, 0, self.code, "N", "", 0,
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("gentrn", data=data)

    def doReprint(self):
        tit = ("Reprint Documents",)
        dat = self.sql.getRec("strtrn", cols=["stt_loc", "stt_trdt",
            "stt_ref1", "stt_ref2"], where=[("stt_cono", "=",
            self.opts["conum"]), ("stt_type", "=", 1)],
            group="stt_loc, stt_trdt, stt_ref1, stt_ref2",
            order="stt_trdt, stt_ref1")
        data = []
        for d in dat:
            try:
                # Exclude purchase orders
                doc = int(d[2])
                chk = self.sql.getRec("strpom", where=[("pom_cono", "=",
                    self.opts["conum"]), ("pom_ordno", "=", doc), ("pom_loc",
                    "=", d[0]), ("pom_date", "=", d[1])])
                if chk:
                    continue
            except:
                pass
            data.append([d[2], d[1], d[3]])
        grv = {
            "stype": "R",
            "tables": ("strtrn", "strpom"),
            "cols": (
                ("stt_ref1", "", 0, "Reference", "Y"),
                ("stt_trdt", "", 0, "Date"),
                ("stt_ref2", "", 0, "Order-Num")),
            "wtype": "D",
            "where": data,
            "screen": self.opts["mf"].body,
            "comnd": self.doSelRec}
        grd = {
            "stype": "R",
            "tables": ("strtrn",),
            "cols": (
                ("stt_trdt", "", 0, "Date"),
                ("stt_ref2", "", 0, "Order-Num")),
            "where": [
                ("stt_cono", "=", self.opts["conum"]),
                ("stt_type", "=", 1)],
            "whera": (("T", "stt_ref1", 0, 0),),
            "group": "stt_trdt",
            "order": "stt_trdt"}
        fld = (
            (("T",0,0,0),"INa",9,"GRN Number","",
                "","N",self.doRepGrv,grv,None,("notblank",)),
            (("T",0,1,0),"ID1",10,"Date","GRN Date",
                0,"N",self.doRepDte,grd,None,("notzero",)))
        state = self.df.disableButtonsTags()
        self.tx = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRepEnd, "n"),), txit=(self.doRepExit,),
            view=("Y","V"), mail=("Y","N"))
        self.tx.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doSelRec(self, frt, pag, r, c, p, i, w):
        self.tx.doKeyPressed(frt, pag, p, w[0])
        self.tx.doKeyPressed(frt, pag, p+1, w[1])

    def doRepGrv(self, frt, pag, r, c, p, i, w):
        self.grv = w
        acc = self.sql.getRec("strtrn", where=[("stt_cono", "=",
            self.opts["conum"]), ("stt_type", "=", 1), ("stt_ref1", "=", w)])
        if not acc:
            return "Invalid GRN Number"
        if len(acc) == 1:
            self.dte = acc[0][self.sql.strtrn_col.index("stt_trdt")]
            self.tx.loadEntry(frt, pag, p+1, data=self.dte)
            self.dtw = self.tx.t_disp[0][0][i+1]
            return "sk1"

    def doRepDte(self, frt, pag, r, c, p, i, w):
        self.dte = w
        self.dtw = self.tx.t_disp[0][0][i]
        acc = self.sql.getRec("strtrn", cols=["count(*)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_type", "=", 1),
            ("stt_ref1", "=", self.grv), ("stt_trdt", "=", self.dte)], limit=1)
        if not acc[0]:
            return "No Document Found"

    def doRepEnd(self):
        self.tx.closeProcess()
        self.doPrintDoc(self.tx.repprt, self.tx.repeml)

    def doRepExit(self):
        self.tx.closeProcess()

    def doPrintDoc(self, repprt, repeml):
        hds = ["Goods Received Notes",
            "GRN Number: %s GRN Date: %s" % (self.grv, self.dtw)]
        col = [
            ["stt_group", "UA", 3, "Grp", "y"],
            ["stt_code", "NA", 20, "Product-Code", "y"],
            ["stt_desc", "NA", 40, "Description", "y"],
            ["stt_loc", "UA", 1, "L", "y"],
            ["stt_qty", "SD", 11.2, "Quantity", "y"],
            ["stt_cost", "SD", 11.2, "Price", "y"]]
        gtt = ["stt_cost"]
        whr = [("stt_cono", "=", self.opts["conum"]), ("stt_type", "=", 1),
            ("stt_ref1", "=", self.grv), ("stt_trdt", "=", self.dte)]
        odr = "stt_seq"
        self.df.setWidget(self.df.mstFrame, state="hide")
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=self.__class__.__name__,
                tables=["strtrn"],
            heads=hds, cols=col, gtots=gtt, where=whr, order=odr,
            repprt=repprt, repeml=repeml, fromad=self.fromad)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doQuery(self):
        callModule(self.opts["mf"], self.df, "st4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=self.opts["period"],
            user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
