"""
SYNOPSIS
    Stores Interrogation.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, NotesCreate, PrintInvoice 
from TartanClasses import PrintOrder, RepPrt, Sql, SRec, TabPrt, TartanDialog
from tartanFunctions import askChoice, getMarkup
from tartanWork import mthnam, sttrtp

class st4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "drschn", "drsmst",
            "genmst", "strgrp", "strloc", "strmf1", "strmf2", "strgmu",
            "strcmu", "strrcp", "strtrn", "struoi"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.plevs = strctl["cts_plevs"]
        self.automu = strctl["cts_automu"]
        if strctl["cts_locs"] == "Y":
            self.locs = self.sql.getRec("strloc", cols=["count(*)"],
                where=[("srl_cono", "=", self.opts["conum"])], limit=1)[0]
        else:
            self.locs = 1
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.per_from = 0
        self.per_to = 0
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Stores Interrogation (%s)" % self.__class__.__name__)
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
            "whera": [["T", "st1_group", 0, 0]],
            "index": 1}
        stl = {
            "stype": "R",
            "tables": ("strloc", "strmf2"),
            "cols": (
                ("srl_loc", "UA", 1, "L"),
                ("srl_desc", "", 0, "Location", "Y")),
            "where": [
                ("srl_cono", "=", self.opts["conum"]),
                ("srl_loc=st2_loc",),
                ("st2_cono=srl_cono",)],
            "whera": [["T", "st2_group", 0], ["T", "st2_code", 1]],
            "sort": "srl_loc",
            "index": 0}
        r1s = (("Normal", "N"), ("Recipe", "R"))
        r2s = (("Average", "A"), ("Standard", "S"), ("None", "N"))
        r3s = (("Manual", "M"), ("Automatic", "A"), ("Zero", "Z"))
        tag = (
            ("Basic", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("History", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Trans", self.doTrans1, ("T",0,0), ("T",0,1)),
            ("Orders", self.doOrders, ("T",0,0), ("T",0,1)))
        fld = [
            (("T",0,0,0),"IUA",3,"Grp","Product Group",
                "","N",self.doGroup,gpm,None,("notblank",)),
            (("T",0,0,0),"INA",20,"Code","Product Code",
                "","N",self.doCode,stm,None,("notblank",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,0,0),"IUA",1,"Loc","Location",
                "","N",self.doLoc,stl,None,("efld",)),
            (("T",0,0,0),"ONA",20,""),
            (("T",1,0,0),("ORB",r1s),0,"Type of Item"),
            (("T",1,1,0),"ONA",10,"Unit of Issue"),
            (("T",1,1,0),"ONA",20,""),
            (("T",1,2,0),("ORB",r2s),0,"Value Indicator"),
            (("T",1,3,0),"OUA",1,"VAT Code"),
            (("T",1,3,0),"ONA",29,""),
            (("T",1,4,0),"OUI",3,"Exclusive Chainstore"),
            (("T",1,4,0),"ONA",27,""),
            (("T",1,5,0),"ONA",7,"Exclusive Account"),
            (("T",1,5,0),"ONA",23,""),
            (("T",1,6,0),"OUI",7,"Sales Code"),
            (("T",1,6,0),"ONA",23,""),
            (("T",1,7,0),"OUI",7,"COS Code"),
            (("T",1,7,0),"ONA",23,""),
            (("T",1,8,0),"OUA",8,"Bin Number"),
            (("T",1,9,0),("ORB",r3s),0,"Re-Order Indicator"),
            (("T",1,10,0),"OUI",7,"Re-Order Level"),
            (("T",1,11,0),"OUI",7,"Re-Order Quantity"),
            (("T",1,12,0),"OUD",6.2,"Price Markup    Lv1")]
        for x in range(self.plevs - 1):
            fld.append((("T",1,12,0),"OUD",6.2," Lv%s" % (x + 2)))
        fld.extend([
            (("T",2,0,0),"Od1",10,"Date Last Receipt"),
            (("T",2,1,0),"Od1",10,"Date Last Issue"),
            (("T",2,2,0),"OSD",12.2,"Quantity Balance"),
            (("T",2,3,0),"OSD",12.2,"Value Balance"),
            [("T",2,4,0),"OSD",12.2,"Average Cost"],
            (("T",2,5,0),"OSD",12.2,"Quantity on P/O"),
            (("T",2,6,0),"OSD",12.2,"Quantity on S/O"),
            (("C",3,0,0),"OSD",13.2,"Qty-Receipts","",
                "","N",None,None,None,None,("Months",13)),
            (("C",3,0,1),"OSD",13.2,"Val-Receipts"),
            (("C",3,0,2),"OSD",13.2,"Qty-Issues"),
            (("C",3,0,3),"OSD",13.2,"Val-Issues"),
            (("T",4,0,0),"Id2",7,"Start Period", "Start Period (0=All)",
                "","N",self.doTrans2a,None,None,("efld",)),
            (("T",4,0,0),"Id2",7,"End Period", "End Period",
                "","N",self.doTrans2b,None,None,("efld",))])
        but = (
            ("Clear",None,self.doClear,1,("T",0,0),("T",0,1)),
            ("Recipe",None,self.doRecipe,None,None,None),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,1,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop,"N"),None,None,None,(self.doTrans2c,"N"))
        txt = (self.doExit,None,None,None,self.doExit)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        yer = int(self.sysdtw / 10000)
        mon = int((self.sysdtw % 10000) / 100)
        self.hist_tit = []
        for x in range(1, 14):
            if x == 13:
                txt = "Last 12 Month Total"
                self.df.colLabel[3][x - 1].configure(text=txt)
                self.hist_tit.append(txt)
            else:
                nam = mthnam[mon][1]
                nam = nam + (" " * (15 - len(nam))) + str(yer)
                self.df.colLabel[3][x - 1].configure(text=nam)
                self.hist_tit.append(nam)
            if x != 13:
                mon -= 1
                if not mon:
                    mon = mon + 12
                    yer -= 1

    def doGroup(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", cols=["gpm_group"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group"
        self.group = w

    def doCode(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.group),
            ("st1_code", "=", w), ("st1_type", "<>", "X")], limit=1)
        if not acc:
            return "Invalid or Redundant Code"
        self.code = w
        self.desc = acc[self.sql.strmf1_col.index("st1_desc")]
        valind = acc[self.sql.strmf1_col.index("st1_value_ind")]
        self.df.loadEntry("T", 0, 2, data=self.desc)
        pag = 1
        d = 3
        for x in range(0, 15):
            if x == 2:
                self.loadUoi(x, acc[d-1])
            elif x == 5:
                self.loadVat(x, acc[d-1])
            elif x == 7:
                self.loadChnExcl(x, acc[d-1])
            elif x == 9:
                self.loadAccExcl(x, acc[d-1])
            elif x in (11, 13):
                self.loadGen(x, acc[d-1])
            else:
                self.df.loadEntry("T", pag, x, data=acc[d])
                if d == 3:
                    self.itype = acc[d]
                    d += 2
                else:
                    d += 1
        if valind == "S":
            self.df.topLabel[2][4].configure(text="%-18s" % "Standard Cost")
        else:
            self.df.topLabel[2][4].configure(text="%-18s" % "Average Cost")
        if self.locs == 1:
            self.df.loadEntry("T", 0, 3, data="1")
            no = self.doLoc(frt, pag, r, c+1, p+1, i+1, "1")
            if no:
                return no
            return "sk2"

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Location Code"
        self.df.loadEntry("T", 0, 4, data=acc[0])
        acc = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group),
            ("st2_code", "=", self.code), ("st2_loc", "=", w)], limit=1)
        if not acc:
            return "This location does not exist for this product"
        self.loc = w
        d = 4
        for x in range(14, 18):
            self.df.loadEntry("T", 1, x, data=acc[d])
            d += 1
        if self.automu in ("A", "L"):
            for lev in range(1, self.plevs + 1):
                mup = getMarkup(self.sql, self.opts["conum"], self.group,
                    self.code, self.loc, lev)
                self.df.loadEntry("T", 1, x + lev, data=mup)
        self.loadBalances()
        if self.itype == "R":
            self.df.setWidget(self.df.B1, "normal")
        else:
            self.df.setWidget(self.df.B1, "disabled")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadUoi(self, pos, uoi):
        acc = self.sql.getRec("struoi", cols=["unm_desc"],
            where=[("unm_cono", "=", self.opts["conum"]), ("unm_unit", "=",
            uoi)], limit=1)
        if acc:
            self.df.loadEntry("T", 1, pos, data=acc[0])

    def loadChnExcl(self, pos, chn):
        self.chn = chn
        if self.chn:
            acc = self.sql.getRec("drschn", cols=["chm_name"],
                where=[("chm_cono", "=", self.opts["conum"]), ("chm_chain",
                "=", self.chn)], limit=1)
            if acc:
                self.df.loadEntry("T", 1, pos, data=acc[0])

    def loadAccExcl(self, pos, drm):
        acc = self.sql.getRec("drsmst", cols=["drm_name"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            self.chn), ("drm_acno", "=", drm)], limit=1)
        if acc:
            self.df.loadEntry("T", 1, pos, data=acc[0])

    def loadVat(self, pos, vat):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            vat)], limit=1)
        if not vat:
            self.df.loadEntry("T", 1, pos, data="Invalid VAT Record")
        else:
            self.df.loadEntry("T", 1, pos, data=acc[0])

    def loadGen(self, pos, gen):
        if self.glint == "N":
            return
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            gen)], limit=1)
        if acc:
            self.df.loadEntry("T", 1, pos, data=acc[0])

    def loadBalances(self):
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
            int(self.sysdtw / 100), keys=(self.group, self.code,
            self.loc, ("P", self.opts["period"][0])))
        m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
        cb, oo, bo = bals.doStrOrds()
        this, hist = bals.doStrHist()
        rec = hist[0]
        rec.append(this[0])
        iss = hist[1]
        iss.append(this[1])
        lrec = self.sql.getRec("strtrn", cols=["max(stt_trdt)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_group", "=",
            self.group), ("stt_code", "=", self.code), ("stt_loc", "=",
            self.loc), ("stt_type", "in", (1, 3))])
        if not lrec[0][0]:
            lastrec = 0
        else:
            lastrec = lrec[0][0]
        liss = self.sql.getRec("strtrn", cols=["max(stt_trdt)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_group", "=",
            self.group), ("stt_code", "=", self.code), ("stt_loc", "=",
            self.loc), ("stt_type", "in", (2, 4, 7, 8))])
        if not liss or not liss[0][0]:
            lastiss = 0
        else:
            lastiss = liss[0][0]
        qbal = float(y_cb[0])
        vbal = float(y_cb[1])
        if qbal:
            cost = round((vbal / qbal), 2)
        else:
            cost = 0.0
        cst = CCD(cost, "SD", 10.2)
        self.df.loadEntry("T", 2, 0, data=lastrec)
        self.df.loadEntry("T", 2, 1, data=lastiss)
        self.df.loadEntry("T", 2, 2, data=qbal)
        self.df.loadEntry("T", 2, 3, data=vbal)
        self.df.loadEntry("T", 2, 4, data=cst.disp)
        self.df.loadEntry("T", 2, 5, data=oo.disp)
        self.df.loadEntry("T", 2, 6, data=bo.disp)
        p = 0
        for x in range(0, 13):
            i = 0
            self.df.loadEntry("C", 3, p, data=rec[x][0])
            p = p + 1
            i = i + 1
            self.df.loadEntry("C", 3, p, data=rec[x][1])
            p = p + 1
            i = i + 1
            amt = float(ASD(0) - ASD(iss[x][0]))
            self.df.loadEntry("C", 3, p, data=amt)
            p = p + 1
            i = i + 1
            amt = float(ASD(0) - ASD(iss[x][1]))
            self.df.loadEntry("C", 3, p, data=amt)
            p = p + 1
            i = i + 1

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doRecipe(self):
        tit = "Recipe"
        self.rcp = self.getRecipeItems()
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.opts["mf"].body, title=tit,
            cols=self.rcp[0], where=self.rcp[1], wtype="D", butt=[("Print",
            self.printRecipe)])
        self.df.enableButtonsTags(state=state)

    def printRecipe(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        hds = ["Stores's Recipe",
            "Location: %s  Code: %s  Description: %s" %
            (self.loc, self.code, self.desc)]
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=self.__class__.__name__,
            heads=hds, cols=self.rcp[0], tables=self.rcp[1], ttype="D",
            prtdia=(("Y", "V"), ("Y", "N")))
        self.df.setWidget(self.df.mstFrame, state="show")
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def getRecipeItems(self):
        tab = ["strrcp", "strmf1"]
        col = ["srr_rgroup", "srr_rcode", "st1_desc", "srr_rqty"]
        whr = [
            ("srr_cono", "=", self.opts["conum"]),
            ("srr_group", "=", self.group),
            ("srr_code", "=", self.code),
            ("srr_loc", "=", self.loc),
            ("st1_cono=srr_cono",),
            ("st1_group=srr_rgroup",),
            ("st1_code=srr_rcode",)]
        odr = "srr_rgroup, srr_rcode"
        items = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        for seq, item in enumerate(items):
            bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
                int(self.sysdtw / 100), keys=(item[0], item[1], self.loc,
                ("P", self.opts["period"][0])))
            m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
            items[seq].extend([y_cb[0], lc])
        return ((
            ("srr_rgroup","UA",3.0,"Grp"),
            ("srr_rcode","NA",20.0,"Product-Code"),
            ("st1_desc","NA",30.0,"Description"),
            ("srr_rqty","UD",11.2,"   Quantity"),
            ("balance","SD",13.2,"    In-Stock"),
            ("cost","UD",11.2,"  Last-Cost")), items)

    def doTrans1(self):
        self.df.focusField("T", 4, 1)

    def doTrans2a(self, frt, pag, r, c, p, i, w):
        self.per_from = w
        self.df.loadEntry("T", 4, 1, data=w)
        if not self.per_from:
            return "nc"

    def doTrans2b(self, frt, pag, r, c, p, i, w):
        self.per_to = w
        if not self.per_to or self.per_to < self.per_from:
            return "Invalid Period"

    def doTrans2c(self):
        tit = "Transactions for Item: %s %s - %s" % \
            (self.group, self.code, self.desc)
        tab = ["strtrn"]
        crt = (
            ("stt_trdt", "", 0, "   Date"),
            ("stt_batch", "", 0, "Batch"),
            ("stt_type", "NA", 3, "Typ"),
            ("stt_ref1", "", 0, "Reference","Y"),
            ("stt_ref2", "", 0, "Ref-Num-2"),
            ("stt_qty", "", 0, "  Quantity"),
            ("stt_cost", "", 0, "      Cost"),
            ("stt_sell", "", 0, "   Selling"),
            ("qbal", "SD", 13.2, "   Qty-Bal"),
            ("cbal", "SD", 13.2, "  Cost-Bal"),
            ("stt_desc", "", 0, "Details"))
        whr = [
            ("stt_cono", "=", self.opts["conum"]),
            ("stt_group", "=", self.group),
            ("stt_code", "=", self.code),
            ("stt_loc", "=", self.loc)]
        if self.per_from:
            whr.extend([("stt_curdt", ">=", self.per_from),
                ("stt_curdt", "<=", self.per_to)])
        odr = "stt_trdt, stt_qty desc"
        recs = self.sql.getRec("strtrn", cols=["stt_trdt", "stt_batch",
            "stt_type", "stt_ref1", "stt_ref2", "stt_qty", "stt_cost",
            "stt_sell", "stt_desc"], where=whr, order=odr)
        data = []
        tqty = 0
        tcst = 0
        for rec in recs:
            rec[2] = sttrtp[rec[2] - 1][0]
            tqty = float(ASD(tqty) + ASD(rec[5]))
            tcst = float(ASD(tcst) + ASD(rec[6]))
            rec.insert(8, tqty)
            rec.insert(9, tcst)
            data.append(rec)
        state = self.df.disableButtonsTags()
        while True:
            rec = SRec(self.opts["mf"], screen=self.df.nb.Page4, title=tit,
                tables=tab, cols=crt, where=data, wtype="D")
            if rec.selection:
                for n, t in enumerate(sttrtp):
                    if t[0] == rec.selection[2]:
                        typ = n + 1
                        break
                dte = rec.selection[0]
                doc = rec.selection[3]
                if self.itype == "R" and typ in (7, 8):
                    bt = (("Transaction", "T"), ("Recipe", "R"))
                    ask = askChoice(self.df.window, head="Details",
                        mess="Transaction Details or the Recipe Details",
                        butt=bt, default="Transaction")
                else:
                    ask = "T"
                if ask == "T":
                    wher = [
                        ("stt_cono", "=", self.opts["conum"]),
                        ("stt_group", "=", self.group),
                        ("stt_code", "=", self.code),
                        ("stt_loc", "=", self.loc),
                        ("stt_type", "=", typ),
                        ("stt_trdt", "=", dte),
                        ("stt_ref1", "=", doc)]
                    TabPrt(self.opts["mf"], tabs="strtrn", where=wher,
                        pdia=False)
                elif typ == 7:
                    rct = "Recipe Details"
                    rcc = (
                        ("si3_line", "", 0, ""),
                        ("si3_rgroup", "", 0, ""),
                        ("si3_rcode", "", 0, ""),
                        ("st1_desc", "", 0, ""),
                        ("si3_rqty", "", 0, ""),
                        ("si3_cost", "", 0, ""))
                    rcw = (
                        ("si3_cono", "=", self.opts["conum"]),
                        ("si3_rtn", "=", "I"),
                        ("si3_docno", "=", doc),
                        ("st1_cono=si3_cono",),
                        ("st1_group=si3_rgroup",),
                        ("st1_code=si3_rcode",))
                    rco = "si3_line"
                    SRec(self.opts["mf"], title=rct, tables=["slsiv3",
                        "strmf1"], cols=rcc, where=rcw, order=rco)
                else:
                    rct = "Recipe Details"
                    rcc = (
                        ("prp_rowno", "", 0, ""),
                        ("prp_rgroup", "", 0, ""),
                        ("prp_rcode", "", 0, ""),
                        ("st1_desc", "", 0, ""),
                        ("prp_rqty", "", 0, ""),
                        ("prp_cost", "", 0, ""))
                    rcw = (
                        ("prp_cono", "=", self.opts["conum"]),
                        ("prp_docno", "=", doc),
                        ("st1_cono=prp_cono",),
                        ("st1_group=prp_rgroup",),
                        ("st1_code=prp_rcode",))
                    rco = "prp_rowno"
                    SRec(self.opts["mf"], title=rct, tables=["posrcp",
                        "strmf1"], cols=rcc, where=rcw, order=rco)
            else:
                break
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 4, 1)

    def doOrders(self):
        tit = "Outstanding Orders for Item: %s %s - %s" % \
            (self.group, self.code, self.desc)
        data = []
        tb1 = ["drsmst", "slsiv1", "slsiv2"]
        wh1 = [
            ("si2_cono", "=", self.opts["conum"]),
            ("si2_group", "=", self.group),
            ("si2_code", "=", self.code),
            ("si2_loc", "=", self.loc),
            ("si2_rtn", "in", ("O", "W")),
            ("si1_invno", "=", ""),
            ("drm_cono=si2_cono",),
            ("drm_acno=si1_acno",),
            ("si1_cono=si2_cono",),
            ("si1_rtn=si2_rtn",),
            ("si1_docno=si2_docno",)]
        recs = self.sql.getRec(tb1, cols=["si2_rtn", "si2_docno",
            "si1_acno", "drm_name", "si2_qty"],
            where=wh1, order="si2_docno")
        for rec in recs:
            if rec[0] == "O":
                data.append(["SO"] + rec[1:])
            else:
                data.append(["WO"] + rec[1:])
        tb2 = ["crsmst", "strpom", "strpot"]
        wh2 = [
            ("pot_cono", "=", self.opts["conum"]),
            ("pot_group", "=", self.group),
            ("pot_code", "=", self.code),
            ("pom_loc", "=", self.loc),
            ("pom_delno", "=", ""),
            ("crm_cono=pot_cono",),
            ("crm_acno=pom_acno",),
            ("pom_cono=pot_cono",),
            ("pom_ordno=pot_ordno",)]
        recs = self.sql.getRec(tb2, cols=["pot_ordno",
            "pom_acno", "crm_name", "pot_qty"],
            where=wh2, order="pot_ordno")
        for rec in recs:
            data.append(["PO"] + rec)
        if data:
            state = self.df.disableButtonsTags()
            col = (
                ("rtn", "UA", 2, "DT"),
                ("docno", "Na", 9, "Reference"),
                ("acno", "NA", 7, "Acc-Num"),
                ("name", "NA", 30, "Name"),
                ("qty", "SD", 13.2, "  Quantity"))
            while True:
                rec = SRec(self.opts["mf"], screen=self.df.nb.Page5, title=tit,
                    cols=col, where=data, wtype="D")
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    typ = rec.selection[0]
                    if rec.selection[0] == "SO":
                        typ = "O"
                    elif rec.selection[0] == "WO":
                        typ = "W"
                    else:
                        typ = "P"
                    doc = int(rec.selection[1])
                    if typ in ("O", "W"):
                        doc = int(rec.selection[1])
                        PrintInvoice(self.opts["mf"], self.opts["conum"],
                            self.opts["conam"], typ, doc, repprt=["N", "V",
                            "view"], copy="y")
                    else:
                        PrintOrder(self.opts["mf"], self.opts["conum"],
                            self.opts["conam"], doc, repprt=["N", "V",
                            "view"], copy="y")
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)
        self.df.selPage(index=self.df.lastnbpage)

    def doNotes(self, wiget=None):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "STR", "%3s%s" % (self.group, self.code))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Basic")
        self.df.setWidget(self.df.B1, "disabled")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = [
            ("Information", "I"),
            ("Transactions", "T")]
        if self.itype == "R":
            butt.append(("Recipe", "R"))
        butt.append(("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if opt == "I":
            head = "Stores Masterfile Record"
            tab = ["strmf1", "strmf2"]
            col = [
                "st1_group", "st1_code", "st2_loc", "st1_desc", "st1_type",
                "st1_uoi", "st1_value_ind", "st1_vatcode", "st1_chn_excl",
                "st1_acc_excl", "st1_sls", "st1_cos", "st2_bin",
                "st2_reord_ind", "st2_reord_level", "st2_reord_qty"]
            whr = [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_group", "=", self.group),
                ("st1_code", "=", self.code),
                ("st2_cono=st1_cono",),
                ("st2_group=st1_group",),
                ("st2_code=st1_code",),
                ("st2_loc", "=", self.loc)]
            TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
                name=self.__class__.__name__, head=head, tabs=tab, cols=col,
                where=whr, keys=[self.group, self.code, self.loc])
        elif opt == "T":
            tab = ["strtrn"]
            hds = ["Stores's Transactions",
                    "Location: %s  Group: %s  Code: %s  Description: %s" %
                    (self.loc, self.group, self.code, self.desc)]
            col = []
            dic = self.sql.strtrn_dic
            for c in ["stt_ref1", "stt_trdt", "stt_type", "stt_qty",
                                "stt_cost", "stt_sell", "stt_desc"]:
                col.append([c, dic[c][2], dic[c][3], dic[c][5]])
            whr = [
                ("stt_cono", "=", self.opts["conum"]),
                ("stt_group", "=", self.group),
                ("stt_code", "=", self.code),
                ("stt_loc", "=", self.loc)]
            if self.per_from:
                whr.extend([("stt_curdt", ">=", self.per_from),
                    ("stt_curdt", "<=", self.per_to)])
            odr = "stt_trdt, stt_ref1"
            gtots = ["stt_qty", "stt_cost", "stt_sell"]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                tables=tab, heads=hds, cols=col, where=whr, order=odr,
                gtots=gtots, prtdia=(("Y","V"),("Y","N")))
        else:
            self.rcp = self.getRecipeItems()
            hds = ["Stores's Recipe",
                "Location: %s  Code: %s  Description: %s" %
                (self.loc, self.code, self.desc)]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                heads=hds, cols=self.rcp[0], tables=self.rcp[1], ttype="D",
                prtdia=(("Y", "V"), ("Y", "N")))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
