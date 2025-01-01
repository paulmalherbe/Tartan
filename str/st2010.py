"""
SYNOPSIS
    Stores Purchase Orders Placing and Receiving.

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
from TartanClasses import ASD, CCD, GetCtl, PrintOrder, PwdConfirm, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askQuestion, callModule, getCost, getVatRate
from tartanFunctions import showError

class st2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.exit = False
            self.selectPrinter()
            if not self.exit:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlmes", "ctlvrf",
            "ctlrep", "crsmst", "gentrn", "strgrp", "strloc", "strmf1",
            "strmf2", "strpom", "strpot", "strtrn", "strgmu", "strcmu",
            "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        mods = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mods.append(ctlmst["ctm_modules"][x:x+2])
        if "CR" not in mods:
            showError(self.opts["mf"].body, "System Error",
                "This module requires you to have a Creditor's Activated")
            return
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.stgl = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        self.dtpl = strctl["cts_tplnam"]
        if self.stgl == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["stk_soh", "stk_susp"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.soh = ctlctl["stk_soh"]
            self.ssp = ctlctl["stk_susp"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def selectPrinter(self):
        tit = ("Printer Selection",)
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "O"),
                ("tpm_system", "=", "STR")],
            "order": "tpm_tname"}
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.dtpl,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),"ID1",10,"Order Date","",
                self.sysdtw,"N",self.doOrdDate,None,None,("efld",)))
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doPrtEnd,"y"),), txit=(self.doPrtExit,),
            view=("N","P"), mail=("N","Y","Y"))
        self.opts["mf"].startLoop()

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "O"), ("tpm_system", "=", "STR")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doOrdDate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not In Financial Period"
        self.trdt = w
        self.trdd = self.pr.t_disp[0][0][1]
        self.curdt = int(self.trdt / 100)
        self.batch = "S%s" % self.curdt

    def doPrtEnd(self):
        self.doPrtClose()

    def doPrtExit(self):
        self.exit = True
        self.doPrtClose()

    def doPrtClose(self):
        self.pr.closeProcess()
        self.opts["mf"].closeLoop()

    def mainProcess(self):
        doc = {
            "stype": "R",
            "tables": ("strpom", "crsmst"),
            "cols": (
                ("pom_ordno", "", 0, "Ord-Num"),
                ("pom_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("pom_cono", "=", self.opts["conum"]),
                ("crm_cono=pom_cono",),
                ("crm_acno=pom_acno",),
                ("pom_delno", "=", "")]}
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": [
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name","Y")],
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")],
            "index": 0}
        odr = {
            "stype": "R",
            "tables": ("ctlrep",),
            "cols": [
                ("rep_code", "", 0, "Ord"),
                ("rep_name", "", 0, "Name","Y")],
            "where": [("rep_cono", "=", self.opts["conum"])],
            "index": 0}
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        cod = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_code", "", 0, "Product-Code"),
                ("st1_desc", "", 0, "Description","Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "not", "in", ("R", "X")),
                ("st1_value_ind", "<>", "N")],
            "whera": [("C", "st1_group", 0)],
            "order": "st1_group, st1_code"}
        r1s = (
            ("New", "N"),
            ("Amend", "A"),
            ("Receive", "R"),
            ("Cancel", "C"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Action","",
                "N","Y",self.doActTyp,None,None,None),
            (("T",0,1,0),"IUI",9,"Ord-No","Order Number",
                "","N",self.doOrdNum,doc,None,("notblank",)),
            (("T",0,2,0),"IUA",1,"Loc","Location Code",
                "1","N",self.doLoc,loc,None,None),
            (("T",0,2,0),"ONA",30,""),
            (("T",0,3,0),"INA",7,"Acc-No","Account Number",
                "","N",self.doCrsAcc,crm,None,None),
            (("T",0,3,0),"ONA",30,""),
            (("T",0,4,0),"INa",3,"Ord-By","Ordered By",
                "","N",self.doOrdBy,odr,None,None),
            (("T",0,4,0),"ONA",30,""),
            (("T",0,5,0),"INa",7,"Del-No","Delivery Note Number",
                "","N",self.doDelNum,None,None,("notblank",)),
            (("T",0,5,0),"ID1",10,"Date","Delivery Date",
                self.trdt,"N",self.doDelDate,None,None,("efld",)),
            (("C",0,0,0),"INA",3,"Grp","Product Group",
                "","Y",self.doGrp,grp,None,None),
            (("C",0,0,1),"INA",20,"Product-Code","",
                "","N",self.doCod,cod,None,None),
            (("C",0,0,2),"INA",(20,30),"Description","",
                "","N",self.doDes,None,None,None),
            (("C",0,0,3),"ISD",11.2,"Quantity","",
                1,"N",self.doQty,None,None,("notzero",)),
            (("C",0,0,4),"IUA",1,"V","V.A.T. Code",
                "I","N",self.doVat,None,None,("notblank",)),
            (("C",0,0,5),"IUD",10.2,"Price","Exclusive Price",
                "","N",self.doPri,None,None,None),
            (("C",0,0,6),"IUD",6.2,"Dis-%","Trade Discount",
                "","N",self.doDis,None,None,None),
            (("C",0,0,7),"OSD",10.2,"Value"))
        self.row = (15,)
        self.but = (
            ("Cancel",None,self.doCancel,1,("C",0,1),("T",0,1)),
            ("DelAdd",None,self.doDelAdd,1,("C",0,1),("T",0,1)),
            ("Ribbon",None,self.doRibbon,1,("C",0,1),("T",0,1)),
            ("Message",None,self.doMessag,1,("C",0,1),("T",0,1)),
            ("Edit",None,self.doEdit,0,("C",0,1),("C",0,2)),
            ("Reprint",None,self.doReprnt,0,("T",0,1),("T",0,2)),
            ("CrsMaint",None,self.doCrsMaint,0,("T",0,5),("T",0,6)),
            ("CrsQuery",None,self.doCrsQuery,1,None,None),
            ("StrMaint",None,self.doStrMaint,0,("C",0,1),(("T",0,1),("C",0,2))),
            ("StrQuery",None,self.doStkQuery,1,None,None),
            ("Exit",None,self.doTopExit,0,("T",0,1),
                (("T",0,2),("T",0,3),("T",0,5)),"Exit Purchase Orders"),
            ("Accept",None,self.doAccept,0,("C",0,1),(("T",0,1),("C",0,2))))
        tnd = ((self.doTopEnd,"n"), )
        txt = (self.doTopExit, )
        cnd = ((self.doColEnd,"n"), )
        cxt = (None, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            rows=self.row, butt=self.but, tend=tnd, txit=txt, cend=cnd,
            cxit=cxt, vport=True)

    def doActTyp(self, frt, pag, r, c, p, i, w):
        # Initialise Action Variables
        self.acttyp = w
        # Initialise Variables
        self.dnum = ""
        self.onum = ""
        self.jnum = ""
        self.dadd = ""
        self.cnam = ""
        self.vatn = ""
        self.ribbon = None
        ctl = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        self.deladd = [
            ctl[self.sql.ctlmst_col.index("ctm_sadd1")],
            ctl[self.sql.ctlmst_col.index("ctm_sadd2")],
            ctl[self.sql.ctlmst_col.index("ctm_sadd3")],
            ctl[self.sql.ctlmst_col.index("ctm_spcode")]]
        self.message = ""
        for x in (1,2,3):
            if self.acttyp == "R":
                self.df.butt[x][1] = 0
                self.df.butt[x][2] = None
            else:
                self.df.butt[x][1] = 1
                self.df.butt[x][2] = ["C", 0, 1]
        if self.acttyp == "N":
            # Location default
            if self.locs == "N":
                self.loc = "1"
                self.df.loadEntry(frt, pag, p+2, data=self.loc)
                self.df.loadEntry(frt, pag, p+3, data="Location One")
                return "sk3"
            return "sk1"

    def doOrdNum(self, frt, pag, r, c, p, i, w):
        strpom = self.sql.getRec("strpom", where=[("pom_cono", "=",
            self.opts["conum"]), ("pom_ordno", "=", w)], limit=1)
        if not strpom:
            return "Invalid Document"
        if strpom[self.sql.strpom_col.index("pom_delno")] == "cancel":
            if self.acttyp == "C":
                return "Already Cancelled"
            ok = askQuestion(self.opts["mf"].body, "Cancelled",
                "This order was Cancelled.\n\nDo you want to Reinstate It?",
                default="no")
            if ok == "no":
                return "Order Cancelled"
            self.sql.updRec("strpom", cols=["pom_delno"], data=[""],
                where=[("pom_cono", "=", self.opts["conum"]),
                ("pom_ordno", "=", w)])
            strpom[self.sql.strpom_col.index("pom_delno")] = ""
        elif strpom[self.sql.strpom_col.index("pom_delno")]:
            return "Order Already Received"
        self.ordno = CCD(w, "UI", 9.0).work
        self.othno = CCD(w, "Na", 9.0).work
        self.loc = strpom[self.sql.strpom_col.index("pom_loc")]
        self.acno = strpom[self.sql.strpom_col.index("pom_acno")]
        self.cnam = strpom[self.sql.strpom_col.index("pom_contact")]
        self.vatn = strpom[self.sql.strpom_col.index("pom_vatno")]
        self.ordby = strpom[self.sql.strpom_col.index("pom_ordby")]
        self.ribbon = ["", "", self.cnam, self.vatn]
        self.df.loadEntry(frt, pag, p+1, data=self.loc)
        self.doLoc(frt, pag, r, c+1, p+1, i+1, self.loc)
        self.df.loadEntry(frt, pag, p+3, data=self.acno)
        self.doCrsAcc(frt, pag, r, c+3, p+3, i+3, self.acno)
        self.df.loadEntry(frt, pag, p+5, data=self.ordby)
        self.doOrdBy(frt, pag, r, c+5, p+5, i+5, self.ordby)
        if self.acttyp == "R":
            return "sk6"
        else:
            return "nd"

    def doLoc(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=", w)],
            limit=1)
        if not desc:
            return "Invalid Location"
        self.loc = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])

    def doCrsAcc(self, frt, pag, r, c, p, i, w):
        self.crsmst = self.sql.getRec("crsmst", where=[("crm_cono",
            "=", self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if not self.crsmst:
            return "Invalid Account"
        if self.crsmst[self.sql.crsmst_col.index("crm_stat")] == "X":
            return "Invalid Account, Redundant"
        self.acno = w
        self.name = self.crsmst[self.sql.crsmst_col.index("crm_name")]
        self.vatn = self.crsmst[self.sql.crsmst_col.index("crm_vatno")]
        self.df.loadEntry(frt, pag, p+1, data=self.name)

    def doOrdBy(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlrep", cols=["rep_name"],
            where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Code"
        self.ordby = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        return "sk3"

    def doDelNum(self, frt, pag, r, c, p, i, w):
        self.delno = w

    def doDelDate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not In Financial Period"
        if w > self.sysdtw:
            return "Invalid Date, In the Future"
        self.deldt = w

    def doTopEnd(self):
        if self.acttyp == "N":
            # Get and Display Next Document Number
            ordno = self.sql.getRec("strpom", cols=["max(pom_ordno)"],
                where=[("pom_cono", "=", self.opts["conum"])], limit=1)
            if not ordno[0]:
                self.ordno = CCD(1, "UI", 9).work
                self.othno = CCD(1, "Na", 9).work
            else:
                self.ordno = CCD((int(ordno[0]) + 1), "UI", 9).work
                self.othno = CCD((int(ordno[0]) + 1), "Na", 9).work
            self.df.loadEntry(self.df.frt, self.df.pag, 1, data=self.ordno)
            # Create Document Transaction (Header)
            self.dad1, self.dad2, self.dad3, self.dad4 = "", "", "", ""
            data = [self.opts["conum"], self.ordno, self.loc, self.trdt,
                self.acno, self.dad1, self.dad2, self.dad3, self.dad4, "",
                "", "", self.vatn, self.ordby, "", "", 0, self.opts["capnm"],
                self.sysdtw]
            # Write and Commit Header
            self.sql.insRec("strpom", data=data)
            self.opts["mf"].dbm.commitDbase()
            # Clear Totals
            self.doClearTots()
        elif self.acttyp == "C":
            self.doReadLoadStr()
            ok = askQuestion(self.opts["mf"].body, "Cancel",
                "Are You Sure This Order Must be Cancelled?", default="no")
            if ok == "yes":
                # Print Cancellation
                self.df.setWidget(self.df.mstFrame, state="hide")
                PrintOrder(self.opts["mf"], self.opts["conum"],
                    self.opts["conam"], self.ordno, tname=self.tname,
                    repprt=self.pr.repprt, repeml=self.pr.repeml,
                    copy=self.acttyp.lower())
                self.df.setWidget(self.df.mstFrame, state="show")
                # Update Deletion
                self.sql.updRec("strpom", cols=["pom_delno"], data=["cancel"],
                    where=[("pom_cono", "=", self.opts["conum"]), ("pom_ordno",
                    "=", self.ordno)])
                self.opts["mf"].dbm.commitDbase()
            # Clear totals and focus
            self.doClearTots()
            self.df.focusField("T", 0, 1)
        else:
            self.doReadLoadStr()
            self.amend = False

    def doReadLoadStr(self):
        self.doClearTots()
        data = self.sql.getRec("strpot", where=[("pot_cono", "=",
            self.opts["conum"]), ("pot_ordno", "=", self.ordno)],
            order="pot_group, pot_code")
        if not data:
            return
        for seq, line in enumerate(data):
            self.doExtData(line)
            if seq >= self.row[0]:
                self.df.scrollScreen(0)
                pos = (self.row[0] - 1) * 8
            else:
                pos = seq * 8
            # Load Values
            self.df.loadEntry("C", 0, pos, data=self.grp)
            self.df.loadEntry("C", 0, pos + 1, data=self.code)
            self.df.loadEntry("C", 0, pos + 2, data=self.desc)
            self.df.loadEntry("C", 0, pos + 3, data=self.qty)
            self.df.loadEntry("C", 0, pos + 4, data=self.vatcod)
            self.df.loadEntry("C", 0, pos + 5, data=self.price)
            self.df.loadEntry("C", 0, pos + 6, data=self.disrat)
            self.df.loadEntry("C", 0, pos + 7, data=self.excamt)
            self.vattot = float(ASD(self.vattot) + ASD(self.vatamt))
            self.ordtot = float(ASD(self.ordtot) + ASD(self.excamt))
            self.inctot = float(ASD(self.inctot) + ASD(self.incamt))
        if seq >= (self.row[0] - 1):
            self.df.scrollScreen(0)
        else:
            self.df.focusField("C", 0, pos + 9)
        self.df.setViewPort("O", self.inctot)

    def doTopExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doClearTots(self):
        self.vattot = 0
        self.ordtot = 0
        self.inctot = 0
        self.df.clearFrame("C", 0)
        self.df.focusField("C", 0, 1)
        self.df.setViewPort(None, 0)

    def doGrp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Group Code"
        self.grp = w

    def doCod(self, frt, pag, r, c, p, i, w):
        strmf1 = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.grp), ("st1_code",
            "=", w)], limit=1)
        if not strmf1:
            return "Invalid Code"
        if strmf1[self.sql.strmf1_col.index("st1_type")] == "R":
            return "Invalid Code (Recipe)"
        if strmf1[self.sql.strmf1_col.index("st1_type")] == "X":
            return "Invalid Code (Redundant)"
        if strmf1[self.sql.strmf1_col.index("st1_value_ind")] == "N":
            return "Invalid Code (Value Indicator)"
        self.vatcod = strmf1[self.sql.strmf1_col.index("st1_vatcode")]
        strmf2 = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.grp), ("st2_code",
            "=", w), ("st2_loc", "=", self.loc)], limit=1)
        if not strmf2:
            return "Invalid Location"
        odt = self.sql.getRec("strpot", cols=["count(*)"],
            where=[("pot_cono", "=", self.opts["conum"]), ("pot_ordno",
            "=", self.ordno), ("pot_group", "=", self.grp), ("pot_code",
            "=", w)], limit=1)
        if odt[0]:
            return "This Item is Already On This Order"
        odq = self.sql.getRec(tables=["strpom", "strpot"],
            cols=["sum(pot_qty)"], where=[("pom_cono", "=",
            self.opts["conum"]), ("pom_loc", "=", self.loc),
            ("pom_delno", "=", ""), ("pot_cono", "=", self.opts["conum"]),
            ("pot_ordno=pom_ordno",), ("pot_group", "=", self.grp),
            ("pot_code", "=", w)], limit=1)
        if odq[0]:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="STR", code="DupOrd",
                desc="%s of this Item is Already On Order" % odq[0])
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "rf"
        self.code = w
        desc = strmf1[self.sql.strmf1_col.index("st1_desc")]
        self.uoi = strmf1[self.sql.strmf1_col.index("st1_uoi")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doDes(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w
        self.df.loadEntry(frt, pag, p+1, data=self.vatcod)

    def doVat(self, frt, pag, r, c, p, i, w):
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.trdt)
        if self.vatrte is None:
            return "Invalid V.A.T Code"
        self.vatcod = w
        # Last Cost Price
        lcost = getCost(self.sql, self.opts["conum"], self.grp, self.code,
            loc=self.loc, qty=1, ind="L")
        self.df.loadEntry(frt, pag, p+1, data=lcost)

    def doPri(self, frt, pag, r, c, p, i, w):
        self.price = w
        self.inc = round((self.price * (self.vatrte + 100.0) / 100.0), 4)
        self.exc = round((self.price * 1), 2)
        dis = self.crsmst[self.sql.crsmst_col.index("crm_trdis")]
        self.df.loadEntry(frt, pag, p+1, data=dis)

    def doDis(self, frt, pag, r, c, p, i, w):
        self.disrat = w
        dis = float(ASD(100) - ASD(self.disrat))
        self.excamt = round((self.qty * self.exc * dis / 100.0), 2)
        self.incamt = round((self.qty * self.inc * dis / 100.0), 2)
        self.vatamt = float(ASD(self.incamt) - ASD(self.excamt))
        self.df.loadEntry(frt, pag, p+1, data=self.excamt)
        self.vattot = float(ASD(self.vattot) + ASD(self.vatamt))
        self.ordtot = float(ASD(self.ordtot) + ASD(self.excamt))
        self.inctot = float(ASD(self.inctot) + ASD(self.incamt))
        self.df.setViewPort("O", self.inctot)

    def doColEnd(self):
        # Create Purchase Order Transaction (Body)
        data = [self.opts["conum"], self.ordno, self.grp, self.code,
            self.uoi, self.desc, self.qty, self.price, self.disrat,
            self.vatcod, self.vatrte, self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("strpot", data=data)
        if self.acttyp == "A":
            self.amend = True
        self.df.advanceLine(0)

    def doCrsQuery(self):
        callModule(self.opts["mf"], self.df, "cr4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def doStkQuery(self):
        callModule(self.opts["mf"], self.df, "st4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=self.opts["period"],
            user=self.opts["capnm"])

    def doDelAdd(self):
        tit = ("Delivery Address",)
        fld = (
            (("T",0,0,0),"INA",30,"Address-1","Address Line 1",
                "","N",None,None,None,None),
            (("T",0,1,0),"INA",30,"Address-2","Address Line 2",
                "","N",None,None,None,None),
            (("T",0,2,0),"INA",30,"Address-3","Address Line 3",
                "","N",None,None,None,None),
            (("T",0,3,0),"INA",30,"Address-4","Address Line 4",
                "","N",None,None,None,None))
        state = self.df.disableButtonsTags()
        self.da = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doDelEnd,"n"),), txit=(self.doDelExit,),
            focus=False)
        for x in range(0, len(self.deladd)):
            self.da.loadEntry("T", 0, 0+x, data=self.deladd[x])
        self.da.focusField("T", 0, 1, clr=False)
        self.da.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doDelEnd(self):
        self.deladd = []
        for x in range(0, self.da.topq[0]):
            self.deladd.append(self.da.t_work[0][0][x])
        self.doDelExit()

    def doDelExit(self):
        self.da.closeProcess()

    def doMessag(self):
        tit = ("Order Message",)
        cod = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": [
                ("mss_message", "",  0, "Cod"),
                ("mss_detail",  "", 60, "Details")],
            "where": [("mss_system", "=", "STR")],
            "screen": self.df.mstFrame}
        fld = (
            (("T",0,0,0),"IUI",3,"Message Code","",
                "","N",self.doMesCod,cod,None,None),
            (("T",0,1,0),"ITv",(30,6),"Message","",
                self.message,"N",None,None,None,None))
        but = (("Accept",None,self.doMesEnd,0,("T",0,1),("T",0,0)),)
        state = self.df.disableButtonsTags()
        self.mg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doMesEnd,"n"),), txit=(self.doMesExit,),
            butt=but)
        self.mg.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doMesCod(self, frt, pag, r, c, p, i, w):
        if w:
            mess = self.sql.getRec("ctlmes",
                where=[("mss_system", "=", "STR"), ("mss_message", "=", w)],
                limit=1)
            if not mess:
                return "Invalid Message Code"
            self.message = mess[self.sql.ctlmse_col.index("mss_detail")]
            self.mg.loadEntry(frt, pag, p+1, data=self.message)

    def doMesEnd(self):
        wid, self.message = self.mg.getEntry("T", 0, 1)
        self.doMesExit()

    def doMesExit(self):
        self.mg.closeProcess()

    def doEdit(self):
        # Display document items and allow editing of desc, qty and price
        recs = self.sql.getRec("strpot", where=[("pot_cono", "=",
            self.opts["conum"]), ("pot_ordno", "=", self.ordno)],
            order="pot_group, pot_code")
        if recs:
            data = []
            for l in recs:
                qty = CCD(l[self.sql.strpot_col.index("pot_qty")],"SD",11.2)
                prc = CCD(l[self.sql.strpot_col.index("pot_price")],"UD",10.2)
                dis = CCD(l[self.sql.strpot_col.index("pot_disper")],"UD",6.2)
                data.append([
                    l[self.sql.strpot_col.index("pot_group")],
                    l[self.sql.strpot_col.index("pot_code")],
                    l[self.sql.strpot_col.index("pot_desc")],
                    qty.disp,
                    l[self.sql.strpot_col.index("pot_vatcod")],
                    prc.disp, dis.disp])
            head = ("Grp", "Product-Code", "Description", "Quantity",
                "V", "Price", "Disc-%")
            lin = {
                "stype": "C",
                "head": head,
                "typs": (("NA", 3), ("NA", 20), ("NA", 30), ("SD", 11.2),
                    ("UA", 1), ("UD", 10.2), ("UD", 6.2)),
                "data": data}
            state = self.df.disableButtonsTags()
            chg = self.df.selChoice(lin)
            if chg and chg.selection:
                self.change = chg.selection
                self.doChanges()
            self.df.enableButtonsTags(state=state)
        self.df.focusField("C", 0, self.df.col)

    def doChanges(self):
        tit = ("Change Items",)
        fld = (
            (("T",0,1,0),"ONA",3,"Group"),
            (("T",0,2,0),"ONA",20,"Code"),
            (("T",0,3,0),"INA",30,"Description","",
                "","N",self.doChgDes,None,None,("notblank",)),
            (("T",0,4,0),"ISD",11.2,"Quantity","",
                "","N",self.doChgQty,None,None,("notzero",)),
            (("T",0,5,0),"IUD",10.2,"Selling Price","",
                "","N",self.doChgPrc,None,None,("notzero",)),
            (("T",0,6,0),"IUD",6.2,"Discount Percent","",
                "","N",self.doChgDis,None,None,("efld",)))
        but = (("Delete",None,self.doChgDel,1,None,None),)
        tnd = ((self.doChgEnd,"n"),)
        txt = (self.doChgExit,)
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        self.cg.loadEntry("T", 0, 0, data=self.change[0])
        self.cg.loadEntry("T", 0, 1, data=self.change[1])
        self.cg.loadEntry("T", 0, 2, data=self.change[2])
        self.cg.loadEntry("T", 0, 3, data=self.change[3])
        self.cg.loadEntry("T", 0, 4, data=self.change[5])
        self.cg.loadEntry("T", 0, 5, data=self.change[6])
        self.cg.focusField("T", 0, 3, clr=False)
        self.cg.mstFrame.wait_window()

    def doChgDes(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doChgQty(self, frt, pag, r, c, p, i, w):
        self.qty = w

    def doChgPrc(self, frt, pag, r, c, p, i, w):
        self.price = w

    def doChgDis(self, frt, pag, r, c, p, i, w):
        self.disrat = w

    def doChgDel(self):
        grp = self.change[0]
        cod = self.change[1]
        self.sql.delRec("strpot", where=[("pot_cono", "=", self.opts["conum"]),
            ("pot_ordno", "=", self.ordno), ("pot_group", "=", grp),
            ("pot_code", "=", cod)])
        if self.acttyp == "A":
            self.amend = True
        self.doChgExit(loader=True)

    def doChgEnd(self):
        grp = self.change[0]
        cod = self.change[1]
        col = ["pot_desc", "pot_qty", "pot_price", "pot_disper"]
        dat = [self.desc, self.qty, self.price, self.disrat]
        whr = [
            ("pot_cono", "=", self.opts["conum"]),
            ("pot_ordno", "=", self.ordno),
            ("pot_group", "=", grp),
            ("pot_code", "=", cod)]
        self.sql.updRec("strpot", cols=col, data=dat, where=whr)
        if self.acttyp == "A":
            self.amend = True
        self.doChgExit(loader=True)

    def doChgExit(self, loader=False):
        self.cg.closeProcess()
        if loader:
            self.doReadLoadStr()

    def doReprnt(self):
        tit = ("Reprint Orders",)
        odr = {
            "stype": "R",
            "tables": ("strpom","crsmst"),
            "cols": [
                ("pom_ordno", "",  0, "Doc-Num"),
                ("pom_date", "",  0, "Date"),
                ("pom_acno",  "", 0, "Acc-Num"),
                ("crm_name",  "", 0, "Name", "Y")],
            "where": [
                ("pom_cono", "=", self.opts["conum"]),
                ("pom_cono=crm_cono",),
                ("pom_acno=crm_acno",)],
            "screen": self.opts["mf"].body}
        r1s = (("Copies", "C"), ("Originals", "O"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Document Mode","",
                "C","N",self.doMode,None,None,None),
            (("T",0,1,0),"IUI",9,"From Number","From Document Number",
                "","N",self.doOrd,odr,None,("notzero",)),
            [("T",0,2,0),"IUI",9,"To   Number","To Document Number",
                "","N",None,odr,None,("notzero",)])
        state = self.df.disableButtonsTags()
        self.rp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doReprntEnd,"n"),),
            txit=(self.doReprntExit,), view=("N","V"), mail=("B","Y"))
        self.rp.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doMode(self, frt, pag, r, c, p, i, w):
        if w == "C":
            self.copy = "y"
        else:
            self.copy = "n"

    def doOrd(self, frt, pag, r, c, p, i, w):
        self.rp.topf[pag][2][5] = w

    def doReprntEnd(self):
        self.rp.closeProcess()
        self.df.setWidget(self.df.mstFrame, state="hide")
        frm = self.rp.t_work[0][0][1]
        if not self.rp.t_work[0][0][2]:
            to = frm
        else:
            to = self.rp.t_work[0][0][2]
        odr = self.sql.getRec("strpom", cols=["pom_ordno"],
            where=[("pom_cono", "=", self.opts["conum"]),
            ("pom_ordno", ">=", frm), ("pom_ordno", "<=", to)])
        if odr:
            PrintOrder(self.opts["mf"], self.opts["conum"], self.opts["conam"],
                odr, tname=self.tname, repprt=self.rp.repprt,
                repeml=self.rp.repeml, copy=self.copy)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doReprntExit(self):
        self.rp.closeProcess()

    def doCrsMaint(self):
        state = self.df.disableButtonsTags()
        cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
            system="STR", code="NewAcc")
        if cf.flag == "ok":
            callModule(self.opts["mf"], self.df, "cr1010",
                coy=(self.opts["conum"], self.opts["conam"]), period=None,
                user=self.opts["capnm"])
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doStrMaint(self):
        state = self.df.disableButtonsTags()
        cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
            system="STR", code="NewAcc")
        if cf.flag == "ok":
            callModule(self.opts["mf"], self.df, "st1010",
                coy=(self.opts["conum"], self.opts["conam"]), period=None,
                user=self.opts["capnm"])
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doAccept(self):
        self.df.setWidget(self.df.B11, "disabled")
        if self.df.col == 1:
            self.doCancel()
        else:
            # Update Tables
            self.doUpdateTables()
            # Commit Transaction
            self.opts["mf"].dbm.commitDbase()
            # Print Document
            if self.acttyp == "N" or (self.acttyp == "A" and self.amend):
                self.df.setWidget(self.df.mstFrame, state="hide")
                PrintOrder(self.opts["mf"], self.opts["conum"],
                    self.opts["conam"], self.ordno, tname=self.tname,
                    repprt=self.pr.repprt, repeml=self.pr.repeml,
                    copy=self.acttyp.lower())
                self.df.setWidget(self.df.mstFrame, state="show")
            self.df.focusField("T", 0, 1)

    def doRibbon(self):
        tit = ("Ribbon Line",)
        fld = (
            (("T",0,0,0),"INA",30,"Customer Order","",
                self.onum,"N",None,None,None,None),
            (("T",0,1,0),"INA",30,"Job Number","",
                self.jnum,"N",None,None,None,None),
            (("T",0,2,0),"INA",30,"Contact Person","",
                self.cnam,"N",None,None,None,None),
            (("T",0,3,0),"INA",10,"VAT Number","",
                self.vatn,"N",self.doVatNum,None,None,None))
        state = self.df.disableButtonsTags()
        self.rb = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRibEnd,"n"),), txit=(self.doRibExit,),
            focus=False)
        if self.ribbon:
            self.rb.loadEntry("T", 0, 0, data=self.ribbon[0])
            self.rb.loadEntry("T", 0, 1, data=self.ribbon[1])
            self.rb.loadEntry("T", 0, 2, data=self.ribbon[2])
            self.rb.loadEntry("T", 0, 3, data=self.ribbon[3])
        self.rb.focusField("T", 0, 1)
        self.rb.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doVatNum(self, frt, pag, r, c, p, i, w):
        if self.ordtot >= 1000.00 and not w:
            return "Invalid VAT Number"

    def doRibEnd(self):
        self.ribbon = []
        for x in range(0, self.rb.topq[0]):
            self.ribbon.append(self.rb.t_work[0][0][x])
        self.doRibExit()

    def doRibExit(self):
        self.rb.closeProcess()

    def doUpdateTables(self):
        # Update strpom with ribbon, delivery and message details
        whr = [
            ("pom_cono", "=", self.opts["conum"]),
            ("pom_ordno", "=", self.ordno),
            ("pom_acno", "=", self.acno)]
        if self.ribbon:
            self.sql.updRec("strpom", cols=["pom_cusord", "pom_jobnum",
                "pom_contact", "pom_vatno"], data=[self.ribbon[0],
                self.ribbon[1], self.ribbon[2], self.ribbon[3]], where=whr)
            if not self.vatn:
                self.sql.updRec("crsmst", cols=["crm_vatno"],
                    data=[self.ribbon[3]], where=[("crm_cono", "=",
                    self.opts["conum"]), ("crm_acno", "=", self.acno)])
        if self.deladd:
            self.sql.updRec("strpom", cols=["pom_add1", "pom_add2", "pom_add3",
                "pom_add4"], data=[self.deladd[0], self.deladd[1],
                self.deladd[2], self.deladd[3]], where=whr)
        if self.message:
            self.sql.updRec("strpom", cols=["pom_mess"], data=[self.message],
                where=whr)
        if self.acttyp != "R":
            return
        # Receipt of Order
        # Create Stores Transactions and update strpot lines
        trn = self.sql.getRec("strpot", where=[("pot_cono", "=",
            self.opts["conum"]), ("pot_ordno", "=", self.ordno)],
            order="pot_group, pot_code")
        if not trn:
            return
        for line in trn:
            self.doExtData(line)
            curdt = int(self.deldt / 100)
            # Update strpom record
            self.sql.updRec("strpom", cols=["pom_delno", "pom_deldt"],
                data=[self.delno, self.deldt], where=[("pom_cono", "=",
                self.opts["conum"]), ("pom_ordno", "=", self.ordno)])
            # Write strtrn record
            data = [self.opts["conum"], self.grp, self.code, self.loc,
                self.deldt, 1, self.othno, self.batch, self.delno, self.qty,
                self.excamt, 0, curdt, self.name, 0, self.acno, "", "STR",
                self.disrat, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("strtrn", data=data)
            # If Integrated Create GL Transaction (SOH and Recon Accounts)
            if self.stgl == "Y" and self.excamt:
                # Stock on Hand Control
                data = (self.opts["conum"], self.soh, curdt, self.deldt, 5,
                    self.othno, self.batch, self.excamt, 0, self.name, "",
                    "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                cst = float(ASD(0) - ASD(self.excamt))
                # Stock Reconciliation Control
                data = (self.opts["conum"], self.ssp, curdt, self.deldt, 5,
                    self.othno, self.batch, cst, 0, self.name, "",
                    "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)

    def doExtData(self, line):
        self.grp = line[self.sql.strpot_col.index("pot_group")]
        self.code = line[self.sql.strpot_col.index("pot_code")]
        self.uoi = line[self.sql.strpot_col.index("pot_uoi")]
        self.desc = line[self.sql.strpot_col.index("pot_desc")]
        self.qty = line[self.sql.strpot_col.index("pot_qty")]
        self.price = line[self.sql.strpot_col.index("pot_price")]
        self.disrat = line[self.sql.strpot_col.index("pot_disper")]
        self.vatcod = line[self.sql.strpot_col.index("pot_vatcod")]
        self.vatrte = line[self.sql.strpot_col.index("pot_vatrat")]
        # Calculate Values
        rat = float(ASD(100) + ASD(self.vatrte))
        inc = round((self.price * rat / 100.0), 4)
        exc = round((self.price * 1), 2)
        dis = float(ASD(100) - ASD(self.disrat))
        self.excamt = round((self.qty * exc * dis / 100.0), 2)
        self.incamt = round((self.qty * inc * dis / 100.0), 2)
        self.vatamt = float(ASD(self.incamt) - ASD(self.excamt))

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        if self.acttyp == "N":
            self.sql.updRec("strpom", cols=["pom_delno"], data=["cancel"],
                where=[("pom_cono", "=", self.opts["conum"]), ("pom_ordno",
                "=", self.ordno), ("pom_acno", "=", self.acno)])
            self.opts["mf"].dbm.commitDbase()
        self.doClearTots()
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
