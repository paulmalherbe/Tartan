"""
SYNOPSIS
    Stores Issues.

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
from TartanClasses import ASD, GetCtl, PwdConfirm, RepPrt, Sql, TartanDialog
from tartanFunctions import chkGenAcc, getCost, showError

class st2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.exit = False
            self.setPrinter()
            if not self.exit:
                self.dataHeader()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "gentrn", "strgrp",
            "strmf1", "strmf2", "strtrn", "strrcp"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
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
        self.glnum = 0
        return True

    def setPrinter(self):
        tit = ("Printer Selection",)
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=[], tend=((self.doPrtEnd,"y"),), txit=(self.doPrtExit,),
            view=("N","P"))
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
                ("st1_type", "", 0, "T"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "<>", "X")],
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
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        fld = [
            (("T",0,0,0),"INa",9,"Issue Number","",
                "","N",self.doIss,None,None,("notblank",)),
            (("T",0,0,0),"ID1",10,"Date","Issue Date",
                self.sysdtw,"N",self.doDte,None,None,("efld",)),
            (("C",0,0,0),"IUA",3,"Grp","Product Group",
                "","N",self.doGroup,gpm,None,("notblank",)),
            [("C",0,0,1),"INA",20,"Product Code","",
                "","N",self.doCode,stm,None,("notblank",)],
            (("C",0,0,2),"ONA",5,"U.O.I"),
            (("C",0,0,3),"IUA",1,"L","Location",
                "r","N",self.doLoc,stl,None,("notblank",)),
            (("C",0,0,4),"ISD",9.2,"Quantity","",
                "","N",self.doQty,None,None,("notzero",)),
            (("C",0,0,5),"OUD",9.2,"Unit-Cost"),
            (("C",0,0,6),"OSD",9.2,"Value")]
        if self.glint == "Y":
            fld.append((("C",0,0,7),"IUI",7,"G/L-Acc","G/L Account Number",
                self.stk_susp,"N",self.doGenAcc,glm,None,None))
            fld.append((("C",0,0,8),"ONA",10,"Desc"))
            fld.append((("C",0,0,9),"INA",(20,30),"Details","Transaction "\
                "Details","","N",self.doTrnDet,None,None,None))
        row = (15,)
        tnd = ((self.endPage0,"n"),)
        txt = (self.exitPage0,)
        cnd = ((self.endPage1,"y"),)
        cxt = (self.exitPage1,)
        but = (("Reprint",None,self.doReprint,0,("T",0,1),None),)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, rows=row,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doIss(self, frt, pag, r, c, p, i, w):
        self.iss = w

    def doDte(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.dte = w
        self.ddt = self.df.t_disp[pag][0][p]
        self.curdt = int(self.dte / 100)
        self.batno = "S%s" % self.curdt

    def doGroup(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group"
        self.group = w

    def doCode(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", cols=["st1_desc", "st1_type",
            "st1_uoi"], where=[("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.group), ("st1_code", "=", w),
            ("st1_type", "<>", "X")], limit=1)
        if not acc:
            return "Invalid or Redundant Code"
        self.code = w
        self.desc = acc[0]
        self.gtype = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=acc[2])
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry("C", pag, p+2, data=self.loc)
            no = self.checkLoc()
            if no:
                return no
            else:
                return "sk2"

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.loc = w
        no = self.checkLoc()
        if no:
            return no

    def checkLoc(self):
        acc = self.sql.getRec("strmf2", cols=["st2_bin"],
            where=[("st2_cono", "=", self.opts["conum"]), ("st2_group", "=",
            self.group), ("st2_code", "=", self.code), ("st2_loc", "=",
            self.loc)], limit=1)
        if not acc:
            return "Invalid Location For This Product"

    def doQty(self, frt, pag, r, c, p, i, w):
        self.quant = w
        if self.gtype == "R" and self.doRecipe():
            return "ff2"
        if self.extractCost():
            return "rf"
        self.df.loadEntry("C", pag, p+1, data=self.ucost)
        self.df.loadEntry("C", pag, p+2, data=self.tcost)

    def doRecipe(self):
        self.recipe = self.sql.getRec("strrcp", where=[("srr_cono",
            "=", self.opts["conum"]), ("srr_group", "=", self.group),
            ("srr_code", "=", self.code), ("srr_loc", "=", self.loc)],
            order="srr_rgroup, srr_rcode")
        if not self.recipe:
            err = "Invalid Recipe, No Items"
            showError(self.opts["mf"].body, "Recipe Error", err)
            return err
        else:
            return self.doRecChg()

    def doRecChg(self):
        # Display recipe items and allow editing of quantities etc.
        data = []
        for num, item in enumerate(self.recipe):
            st1 = self.sql.getRec("strmf1", cols=["st1_type",
                "st1_desc"], where=[("st1_cono", "=", self.opts["conum"]),
                ("st1_group", "=", item[4]), ("st1_code", "=", item[5])],
                limit=1)
            err = False
            if not st1:
                err = "Invalid Stock Record in Recipe"
            elif st1[0] == "X":
                err = "Redundant Stock Record in Recipe"
            if err:
                showError(self.opts["mf"].body, "Recipe Error",
                    """%s!

Group: %s
Code:  %s""" % (err, item[4], item[5]))
                return err
            data.append([num, item[4], item[5], st1[1], item[6]])
        titl = "Recipe Items"
        head = ("Seq","Grp","Product-Code", "Description", "Quantity")
        lin = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": [
                ("UI", 2),
                ("NA", 3),
                ("NA", 20),
                ("NA", 30),
                ("SD", 11.2)],
            "data": data}
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus(
            "Select a Product to Edit or Exit to Continue")
        chg = self.df.selChoice(lin)
        if chg and chg.selection:
            self.recchg = chg.selection
            self.doRecChanges()
            self.doRecChg()
        else:
            self.df.enableButtonsTags(state=state)

    def doRecChanges(self):
        tit = ("Change Items",)
        fld = (
            (("T",0,0,0),"ONA",3,"Group"),
            (("T",0,1,0),"ONA",20,"Code"),
            (("T",0,2,0),"ONA",30,"Description"),
            (("T",0,3,0),"ISD",10.2,"Quantity","",
                "","N",self.doRecQty,None,None,('notzero',)))
        but = (("Delete",None,self.doRecDel,1,None,None),)
        self.rp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doRecEnd,"n"),),
            txit=(self.doRecExit,))
        self.rp.loadEntry("T", 0, 0, data=self.recchg[1])
        self.rp.loadEntry("T", 0, 1, data=self.recchg[2])
        self.rp.loadEntry("T", 0, 2, data=self.recchg[3])
        self.rp.loadEntry("T", 0, 3, data=self.recchg[4])
        self.rp.focusField("T", 0, 4, clr=False)
        self.rp.mstFrame.wait_window()

    def doRecQty(self, frt, pag, r, c, p, i, w):
        self.recqty = w

    def doRecDel(self):
        del self.recipe[int(self.recchg[0])]
        self.doRecExit()

    def doRecEnd(self):
        self.recipe[int(self.recchg[0])][6] = self.recqty
        self.doRecExit()

    def doRecExit(self):
        self.rp.closeProcess()

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        self.glnum = w
        self.df.loadEntry("C", pag, p+1, data=chk[0])

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        if not w:
            self.trndet = self.desc
        else:
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
        if self.df.col != 1:
            self.doPrintDoc(self.pr.repprt)
        self.df.focusField("T", 0, 1)

    def extractCost(self):
        self.ucost = 0
        self.tcost = 0
        if self.gtype == "R":
            for item in self.recipe:
                quant = item[6] * self.quant
                tcost = self.doCalCost(item[4], item[5], quant)
                if tcost is None:
                    return "error"
                self.tcost = float(ASD(self.tcost) + ASD(tcost))
        else:
            tcost = self.doCalCost(self.group, self.code, self.quant)
            if tcost is None:
                return "error"
            self.tcost = tcost
        self.ucost = round(self.tcost / self.quant, 2)

    def updateTables(self):
        if self.gtype == "R":
            # Issue individual items
            for item in self.recipe:
                acc = self.sql.getRec("strmf1", cols=["st1_desc"],
                    where=[("st1_cono", "=", item[0]), ("st1_group", "=",
                    item[4]), ("st1_code", "=", item[5])], limit=1)
                if acc:
                    des = acc[0]
                else:
                    des = "Unknown Description"
                qty = item[6] * self.quant
                tcost = self.doCalCost(item[4], item[5], qty, chk=False)
                qty = float(ASD(0) - ASD(qty))
                val = float(ASD(0) - ASD(tcost))
                data = [self.opts["conum"], item[4], item[5], self.loc,
                    self.dte, 6, self.iss, self.batno, self.glnum, qty, val,
                    0, self.curdt, des, 0, "", "", "STR", 0, "",
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("strtrn", data=data)
            # Receive recipe item
            data = [self.opts["conum"], self.group, self.code, self.loc,
                self.dte, 5, self.iss, self.batno, self.glnum, self.quant,
                self.tcost, 0, self.curdt, self.desc, 0, "", "", "STR", 0,
                "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("strtrn", data=data)
        # Stores Ledger Transaction
        qty = float(ASD(0) - ASD(self.quant))
        val = float(ASD(0) - ASD(self.tcost))
        data = [self.opts["conum"], self.group, self.code, self.loc, self.dte,
            2, self.iss, self.batno, self.glnum, qty, val, 0, self.curdt,
            self.desc, 0, "", "", "STR", 0, "N", self.opts["capnm"],
            self.sysdtw, 0]
        self.sql.insRec("strtrn", data=data)
        if self.glint == "N":
            return
        col = self.sql.gentrn_col
        # General Ledger Control Transaction (Stock On Hand)
        acc = self.sql.getRec("gentrn", where=[("glt_cono", "=",
            self.opts["conum"]), ("glt_acno", "=", self.stk_soh), ("glt_curdt",
            "=", self.curdt), ("glt_trdt", "=", self.dte), ("glt_type", "=",
            4), ("glt_refno", "=", self.iss), ("glt_batch", "=", self.batno)],
            limit=1)
        if acc:
            amnt = float(ASD(acc[col.index("glt_tramt")]) + ASD(val))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[amnt],
                where=[("glt_seq", "=", acc[col.index("glt_seq")])])
        else:
            self.sql.insRec("gentrn", data=[self.opts["conum"], self.stk_soh,
            self.curdt, self.dte, 4, self.iss, self.batno, val, 0,
            self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0])
        # General Ledger Transaction (Expense)
        acc = self.sql.getRec("gentrn", where=[("glt_cono", "=",
            self.opts["conum"]), ("glt_acno", "=", self.glnum), ("glt_curdt",
            "=", self.curdt), ("glt_trdt", "=", self.dte), ("glt_type", "=",
            4), ("glt_refno", "=", self.iss), ("glt_batch", "=", self.batno)],
            limit=1)
        if acc:
            amnt = float(ASD(acc[col.index("glt_tramt")]) + ASD(self.tcost))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[amnt],
                where=[("glt_seq", "=", acc[col.index("glt_seq")])])
        else:
            self.sql.insRec("gentrn", data=[self.opts["conum"], self.glnum,
            self.curdt, self.dte, 4, self.iss, self.batno, self.tcost,
            0, self.trndet, "N", "", 0, self.opts["capnm"], self.sysdtw, 0])

    def doCalCost(self, grp, code, qty, chk=True):
        # Calculate cost price
        icost, tcost, bal = getCost(self.sql, self.opts["conum"], grp, code,
            loc=self.loc, qty=qty, tot=True, bal=True)
        if chk and qty > bal[0]:
            acc = self.sql.getRec("strmf1", cols=["st1_desc"],
                where=[("st1_cono", "=", self.opts["conum"]),
                ("st1_group", "=", grp), ("st1_code", "=", code)],
                limit=1)
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="STR", code="ExQty", product=(grp, code, acc[0]))
            if cf.flag == "no":
                return
        return tcost

    def doReprint(self):
        tit = ("Reprint Documents",)
        data = self.sql.getRec("strtrn", cols=["stt_ref1", "stt_trdt"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_type", "=",
            2)], group="stt_ref1, stt_trdt", order="stt_trdt, stt_ref1")
        iss = {
            "stype": "R",
            "tables": ("strtrn",),
            "cols": (
                ("stt_ref1", "", 0, "Reference"),
                ("stt_trdt", "", 0, "Date", "Y")),
            "wtype": "D",
            "where": data,
            "screen": self.opts["mf"].body,
            "comnd": self.doSelRec}
        isd = {
            "stype": "R",
            "tables": ("strtrn",),
            "cols": (
                ("stt_trdt", "", 0, "Date"),),
            "where": [
                ("stt_cono", "=", self.opts["conum"]),
                ("stt_type", "=", 2)],
            "whera": (("T", "stt_ref1", 0, 0),),
            "group": "stt_trdt",
            "order": "stt_trdt",
            "screen": self.opts["mf"].body}
        fld = (
            (("T",0,0,0),"INa",9,"Issue Number","",
                "","N",self.doRepIss,iss,None,("notblank",)),
            (("T",0,1,0),"ID1",10,"Date","GRN Date",
                0,"N",self.doRepDte,isd,None,("notzero",)))
        state = self.df.disableButtonsTags()
        self.tx = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRepEnd, "n"),), txit=(self.doRepExit,),
            view=("N","V"), mail=("Y","N"))
        self.tx.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doSelRec(self, frt, pag, r, c, p, i, w):
        self.tx.doKeyPressed(frt, pag, p, w[0])
        self.tx.doKeyPressed(frt, pag, p+1, w[1])

    def doRepIss(self, frt, pag, r, c, p, i, w):
        self.iss = w

    def doRepDte(self, frt, pag, r, c, p, i, w):
        self.dte = w
        self.ddt = self.df.t_disp[pag][0][p]
        acc = self.sql.getRec("strtrn", cols=["count(*)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_type", "=", 2),
            ("stt_ref1", "=", self.iss), ("stt_trdt", "=", self.dte)], limit=1)
        if not acc[0]:
            return "No Document Found"

    def doRepEnd(self):
        self.tx.closeProcess()
        self.doPrintDoc(self.tx.repprt)

    def doRepExit(self):
        self.tx.closeProcess()

    def doPrintDoc(self, repprt):
        hds = ["Goods Issued Notes",
            "GIN Number: %s GIN Date: %s" % (self.iss, self.ddt)]
        tab = ["strmf1", "strtrn"]
        col = [
            ["stt_group", "UA", 3, "Grp", "y"],
            ["stt_code", "NA", 20, "Product-Code", "y"],
            ["stt_desc", "NA", 40, "Description", "y"],
            ["stt_loc", "UA", 1, "L", "y"],
            ["stt_qty", "SD", 11.2, "Quantity", "y", "y"],
            ["stt_cost", "SD", 11.2, "Price", "y", "y"]]
        gtt = ["stt_cost"]
        whr = [
            ("stt_cono", "=", self.opts["conum"]),
            ("stt_type", "in", (2, 6)),
            ("stt_ref1", "=", self.iss),
            ("stt_trdt", "=", self.dte),
            ("st1_cono=stt_cono",),
            ("st1_group=stt_group",),
            ("st1_code=stt_code",),
            ("st1_type", "<>", "R")]
        odr = "stt_seq"
        self.df.setWidget(self.df.mstFrame, state="hide")
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=self.__class__.__name__, tables=tab,
            heads=hds, cols=col, gtots=gtt, where=whr, order=odr, repprt=repprt)
        self.df.setWidget(self.df.mstFrame, state="show")

# vim:set ts=4 sw=4 sts=4 expandtab:
