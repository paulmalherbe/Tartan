"""
SYNOPSIS
    Stores Masterfile Maintenance.

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
from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, getMarkup

class st1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "ctlrep", "drschn",
            "drsmst", "genmst", "slsiv1", "slsiv2", "strcst", "strgrp",
            "strloc", "strmf1", "strmf2", "strgmu", "strcmu", "strprc",
            "strrcp", "struoi", "strtrn", "strpot", "strvar", "slsiv3",
            "chglog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        self.automu = strctl["cts_automu"]
        self.drsctl = gc.getCtl("drsctl", self.opts["conum"], error=False)
        if not self.drsctl:
            self.chains = "N"
        else:
            self.chains = self.drsctl["ctd_chain"]
        return True

    def mainProcess(self):
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
            "whera": [],
            "index": 1}
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        unm = {
            "stype": "R",
            "tables": ("struoi",),
            "cols": (
                ("unm_unit", "", 0, "Unit"),
                ("unm_desc", "", 0, "Description", "Y")),
            "where": [("unm_cono", "=", self.opts["conum"])]}
        drc = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1"))}
        if self.chains == "Y":
            drm["where"] = [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_stat", "<>", "X")]
            drm["whera"] = [["T", "drm_chain", 10]]
        else:
            drm["where"] = [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_chain", "=", 0),
                ("drm_stat", "<>", "X")]
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        tag = (
            ("Basic-_A",None,("T",0,0),("T",0,1)),
            ("Basic-_B",None,("T",0,0),("T",0,1)),
            ("Recipes",self.doReadLoadRecipe,None,("T",0,1)))
        r1s = (("Normal","N"), ("Recipe","R"))
        r2s = (("Average","A"), ("Standard","S"), ("None","N"))
        r3s = (("Manual","M"), ("Automatic","A"), ("Zero","N"))
        self.fld = [
            (("T",0,0,0),"IUA",3,"Group","Product Group",
                "","Y",self.doGroup,gpm,None,("notblank",)),
            (("T",0,0,0),"INA",20,"Code","Product Code",
                "","N",self.doCode,stm,None,("notblank",)),
            (("T",0,0,0),"IUA",1,"Loc","Location",
                "1","N",self.doLoc,loc,None,("notblank",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",1,0,0),("IRB",r1s),0,"Type of Item","",
                "N","N",self.doType,None,None,None),
            (("T",1,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",1,2,0),"INA",10,"Unit of Issue","",
                "","N",self.doUoi,unm,None,("notblank",)),
            (("T",1,2,0),"ONA",30,""),
            (("T",1,3,0),("IRB",r2s),0,"Cost Price Indicator","",
                "A","N",self.doValInd,None,None,None),
            (("T",1,4,0),"IUA",1,"VAT Code","",
                "","N",self.doVat,vtm,None,("notblank",)),
            (("T",1,4,0),"ONA",30,""),
            (("T",1,5,0),"IUI",3,"Exclusive Chainstore","",
                "","N",self.doChnExcl,drc,None,("efld",)),
            (("T",1,5,0),"ONA",30,""),
            (("T",1,6,0),"INA",7,"Exclusive Account","",
                "","N",self.doAccExcl,drm,None,("efld",)),
            (("T",1,6,0),"ONA",30,""),
            (("T",1,7,0),"IUI",7,"Sales Code","",
                "","N",self.doSales,glm,None,("efld",)),
            (("T",1,7,0),"ONA",30,""),
            (("T",1,8,0),"IUI",7,"COS Code","",
                "","N",self.doCos,glm,None,("efld",)),
            (("T",1,8,0),"ONA",30,""),
            (("T",2,0,0),"IUA",8,"Bin Number","",
                "","N",None,None,self.doDelete,("efld",)),
            (("T",2,1,0),("IRB",r3s),0,"Re-Order Indicator","",
                "A","N",self.doReord,None,None,None),
            (("T",2,2,0),"IUI",7,"Re-Order Level","",
                "","N",None,None,None,("efld",)),
            (("T",2,3,0),"IUI",7,"Re-Order Quantity","",
                "","N",None,None,None,("efld",))]
        if self.automu in ("A", "L"):
            self.fld.append((("T",2,4,0),"IUD",6.2,"Percentabge Markup Lv1","",
                "","N",None,None,None,("efld",)))
            for x in range(1, self.plevs):
                self.fld.append((("T",2,4,0),"IUD",6.2,"Lv%s" % (x + 1),"",
                    "","N",None,None,None,("efld",)))
        self.fld.extend([
            (("C",3,0,0),"INA",3,"Grp","Product Group",
                "r","N",self.doRecGrp,gpm,None,None),
            (("C",3,0,1),"INA",20,"Product-Code","Product Code",
                "","N",self.doRecCod,stm,None,None),
            (("C",3,0,2),"ONA",30,"Description"),
            (("C",3,0,3),"IUD",11.2,"Quantity","",
                "","N",self.doRecQty,None,self.doDelRec,("notzero",))])
        but = (
            ("Edit",None,self.doEditor,0,("C",3,1),None),
            ("Accept",None,self.doAccept,0,("T",0,0),("T",0,1)),
            ("Cancel",None,self.doCancel,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doQuit,1,None,None))
        tnd = ((self.doEnd,"N"), (self.doEnd,"N"), (self.doEnd,"Y"), None)
        txt = (self.doExit, self.doExit, self.doExit, self.doExit)
        cnd = (None, None, None, (self.doEnd,"N"))
        cxt = (None, None, None, self.doExit)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tags=tag, butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt,
            clicks=self.doClick)

    def doClick(self, *opts):
        if self.df.pag == 0 or not self.gtype:
            return
        if opts[0] == (1, 0) and not self.newcode:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.grpacc = self.sql.getRec("strgrp", cols=["gpm_vatcode",
            "gpm_sales", "gpm_costs"], where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", w)], limit=1)
        if not self.grpacc:
            return "Invalid Group"
        self.group = w
        self.df.topf[0][1][8]["whera"] = [["T", "st1_group", 0, 0]]

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.mups = [0, 0, 0, 0, 0]
        self.old1 = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.group), ("st1_code",
            "=", w)], limit=1)
        if not self.old1:
            self.newcode = True
            self.gtype = None
        elif self.old1[3] == "X":
            return "Redundant Code"
        else:
            self.newcode = False
            d = 3
            for x in range(0, self.df.topq[1]):
                if x in (3, 6, 8, 10, 12, 14):
                    continue
                if x == 0:
                    self.gtype = self.old1[d]
                self.df.loadEntry("T", 1, x, data=self.old1[d])
                if x == 2:
                    get = self.getUoi(self.old1[d])
                    if get:
                        self.df.loadEntry("T", 1, x+1, data=get[0])
                if x == 5:
                    get = self.getVat(self.old1[d])
                    if get:
                        self.df.loadEntry("T", 1, x+1, data=get[0])
                if x == 7:
                    get = self.getChnExcl(self.old1[d])
                    if get:
                        self.df.loadEntry("T", 1, x+1, data=get[0])
                if x == 9:
                    get = self.getAccExcl(self.old1[d])
                    if get:
                        self.df.loadEntry("T", 1, x+1, data=get[0])
                if self.glint == "Y" and x in (11, 13):
                    get = self.getGenDes(self.old1[d])
                    if get:
                        self.df.loadEntry("T", 1, x+1, data=get[0])
                d += 1
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry("T", 0, 2, data=self.loc)
            err = self.checkLoc()
            if err:
                return err
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        if w == 0:
            return "Invalid Location"
        self.loc = w
        err = self.checkLoc()
        if err:
            return err

    def checkLoc(self):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
            self.loc)], limit=1)
        if not acc:
            return "Invalid Location Code"
        else:
            self.df.loadEntry("T", 0, 3, data=acc[0])
        self.old2 = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.group), ("st2_code",
            "=", self.code), ("st2_loc", "=", self.loc)], limit=1)
        if not self.old2:
            ok = askQuestion(self.opts["mf"].body, "New Location",
                "This location does not exist for this product. " \
                "Are you sure that you want to create it?")
            if ok == "yes":
                self.newloc = "Y"
            else:
                return "Rejected Location"
        if not self.old2:
            self.newloc = "Y"
        else:
            self.newloc = "N"
            d = 3
            for x in range(0, 4):
                d = d + 1
                self.df.loadEntry("T", 2, x, data=self.old2[d])
            if self.automu in ("A", "L"):
                for y in range(self.plevs):
                    mup = getMarkup(self.sql, self.opts["conum"], self.group,
                        self.code, self.loc, y + 1)
                    self.df.loadEntry("T", 2, 4 + y, data=mup)
                    self.mups[y] = mup

    def doType(self, frt, pag, r, c, p, i, w):
        self.gtype = w
        if self.gtype == "R":
            self.df.enableTag(2)
        else:
            self.df.disableTag(2)

    def doUoi(self, frt, pag, r, c, p, i, w):
        acc = self.getUoi(w)
        if not acc:
            return "Invalid UOI Record"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doValInd(self, frt, pag, r, c, p, i, w):
        self.df.topf[1][5][5] = self.grpacc[0]

    def doVat(self, frt, pag, r, c, p, i, w):
        acc = self.getVat(w)
        if not acc:
            return "Invalid VAT Record"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if not self.drsctl:
            self.chain = 0
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+1, data="")
            if self.glint == "N":
                return "sk9"
            else:
                return "sk4"

    def doChnExcl(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.getChnExcl(w)
            if not acc:
                return "Invalid Chainstore"
            self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.chain = w

    def doAccExcl(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.getAccExcl(w)
            if not acc:
                return "Invalid Debtors Account"
            self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if self.glint == "N":
            return "sk5"
        if self.newcode:
            self.df.loadEntry(frt, pag, p+2, data=self.grpacc[1])
            if self.grpacc[1]:
                acc = self.getGenDes(self.grpacc[1])
                if not acc:
                    return "Invalid Sales Code"
                self.df.loadEntry(frt, pag, p+3, data=acc[0])
            self.df.loadEntry(frt, pag, p+4, data=self.grpacc[2])
            if self.grpacc[2]:
                acc = self.getGenDes(self.grpacc[2])
                if not acc:
                    return "Invalid C.O.S. Code"
                self.df.loadEntry(frt, pag, p+5, data=acc[0])

    def doSales(self, frt, pag, r, c, p, i, w):
        acc = self.getGenDes(w)
        if not acc:
            return "Invalid Sales Account"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doCos(self, frt, pag, r, c, p, i, w):
        acc = self.getGenDes(w)
        if not acc:
            return "Invalid COS Account"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doReord(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "sk2"

    def getUoi(self, dat):
        acc = self.sql.getRec("struoi", cols=["unm_desc"],
            where=[("unm_cono", "=", self.opts["conum"]), ("unm_unit", "=",
            dat)], limit=1)
        return acc

    def getVat(self, dat):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            dat)], limit=1)
        return acc

    def getChnExcl(self, dat):
        self.chain = dat
        if dat:
            acc = self.sql.getRec("drschn", cols=["chm_name"],
                where=[("chm_cono", "=", self.opts["conum"]), ("chm_chain",
                "=", dat)], limit=1)
            return acc

    def getAccExcl(self, dat):
        if dat:
            acc = self.sql.getRec("drsmst", cols=["drm_name"],
                where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain",
                "=", self.chain), ("drm_acno", "=", dat), ("drm_stat", "<>",
                "X")], limit=1)
            return acc

    def getGenDes(self, dat):
        if dat:
            acc = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                dat)], limit=1)
            return acc

    def doRecGrp(self, frt, pag, r, c, p, i, w):
        self.rgroup = w
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group"
        self.df.topf[0][1][8]["whera"] = [["C", "st1_group", 0, 3]]

    def doRecCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", cols=["st1_type", "st1_desc"],
            where=[("st1_cono", "=", self.opts["conum"]), ("st1_group", "=",
            self.rgroup), ("st1_code", "=",  w)], limit=1)
        if not acc:
            return "Invalid Code"
        if acc[0] == "R":
            return "Invalid Type (Recipe)"
        self.df.loadEntry(frt, pag, p+1, data=acc[1])
        acc = self.sql.getRec("strmf2", cols=["st2_bin"],
            where=[("st2_cono", "=", self.opts["conum"]), ("st2_group", "=",
            self.rgroup), ("st2_code", "=", w), ("st2_loc", "=", self.loc)],
            limit=1)
        if not acc:
            return "Invalid Code (2)"
        self.rcode = w
        acc = self.sql.getRec("strrcp", cols=["srr_rqty"],
            where=[("srr_cono", "=", self.opts["conum"]), ("srr_group", "=",
            self.group), ("srr_code", "=", self.code), ("srr_loc", "=",
            self.loc), ("srr_rgroup", "=", self.rgroup), ("srr_rcode", "=",
            self.rcode)], limit=1)
        if acc:
            self.newrec = "n"
            self.df.loadEntry(frt, pag, p+2, data=acc[0])
        else:
            self.newrec = "y"

    def doRecQty(self, frt, pag, r, c, p, i, w):
        self.rqty = w

    def doEditor(self):
        if self.df.pag != 3:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        # Display recipe items and allow editing of details
        data = self.sql.getRec(tables=["strrcp", "strmf1"],
            cols=["srr_rgroup", "srr_rcode", "st1_desc", "srr_rqty"],
            where=[("srr_cono", "=", self.opts["conum"]), ("srr_group", "=",
            self.group), ("srr_code", "=", self.code), ("srr_loc", "=",
            self.loc), ("st1_cono=srr_cono",), ("st1_group=srr_rgroup",),
            ("st1_code=srr_rcode",)])
        if data:
            titl = "Recipe Items"
            head = ("Grp", "Product-Code", "Description", "Quantity")
            lin = {
                "stype": "C",
                "titl": titl,
                "head": head,
                "typs": (("NA", 3), ("NA", 20), ("NA", 30), ("SD", 10.2)),
                "data": data}
            state = self.df.disableButtonsTags()
            self.opts["mf"].updateStatus("Select a Product to Edit")
            chg = self.df.selChoice(lin)
            if chg and chg.selection:
                self.change = chg.selection
                self.doChgChanges()
            self.df.enableButtonsTags(state=state)
            self.df.focusField("C", 3, self.df.col)

    def doChgChanges(self):
        tit = ("Change Items",)
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
            "where": [("st1_cono", "=", self.opts["conum"])],
            "whera": [],
            "index": 1}
        fld = (
            (("T",0,0,0),"INA",3,"Group","Product Group",
                "","N",self.doChgGrp,gpm,None,('notblank',)),
            (("T",0,1,0),"INA",20,"Code","Product Code",
                "","N",self.doChgCod,stm,None,('notblank',)),
            (("T",0,2,0),"ONA",30,"Description"),
            (("T",0,3,0),"ISD",10.2,"Quantity","",
                "","N",self.doChgQty,None,None,('notzero',)))
        but = [["Delete",None,self.doChgDel,1,None,None]]
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doChgEnd,"n"),),
            txit=(self.doChgExit,))
        self.cg.loadEntry("T", 0, 0, data=self.change[0])
        self.cg.loadEntry("T", 0, 1, data=self.change[1])
        self.cg.loadEntry("T", 0, 2, data=self.change[2])
        self.cg.loadEntry("T", 0, 3, data=self.change[3])
        self.cg.focusField("T", 0, 1, clr=False)
        self.cg.mstFrame.wait_window()

    def doChgGrp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group"
        self.rgroup = w
        self.cg.topf[0][1][8]["whera"] = [["T", "st1_group", 0, 0]]

    def doChgCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", cols=["st1_type", "st1_desc"],
            where=[("st1_cono", "=", self.opts["conum"]), ("st1_group", "=",
            self.rgroup), ("st1_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        if acc[0] != "N":
            return "Invalid Type"
        cnt = self.sql.getRec("strrcp", cols=["count(*)"],
            where=[("srr_cono", "=", self.opts["conum"]), ("srr_group", "=",
            self.rgroup), ("srr_code", "=", w)], limit=1)
        if cnt[0]:
            return "Product Already In Recipe"
        self.rcode = w
        self.cg.loadEntry("T", 0, 2, data=acc[1])

    def doChgQty(self, frt, pag, r, c, p, i, w):
        self.rqty = w

    def doChgDel(self):
        self.sql.delRec("strrcp", where=[("srr_cono", "=", self.opts["conum"]),
            ("srr_group", "=", self.group), ("srr_code", "=", self.code),
            ("srr_loc", "=", self.loc), ("srr_rgroup", "=", self.change[0]),
            ("srr_rcode", "=", self.change[1])])
        self.doReadLoadRecipe()
        self.doChgExit()

    def doChgEnd(self):
        self.sql.updRec("strrcp", cols=["srr_rgroup", "srr_rcode",
            "srr_rqty"], data=[self.rgroup, self.rcode, self.rqty],
            where=[("srr_cono", "=", self.opts["conum"]), ("srr_group", "=",
            self.group), ("srr_code", "=", self.loc), ("srr_loc", "=",
            self.loc), ("srr_rgroup", "=", self.change[0]), ("srr_rcode", "=",
            self.change[1])])
        self.doReadLoadRecipe()
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def doDelete(self):
        trn = self.sql.getRec("strpot", cols=["count(*)"],
            where=[("pot_cono", "=", self.opts["conum"]), ("pot_group", "=",
            self.group), ("pot_code", "=", self.code)], limit=1)
        if trn[0]:
            return "Purchase Orders Exist, Not Deleted"
        trn = self.sql.getRec("strtrn", cols=["count(*)"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_group", "=",
            self.group), ("stt_code", "=", self.code), ("stt_loc", "=",
            self.loc)], limit=1)
        if trn[0]:
            return "Stores Transactions Exist, Not Deleted"
        trn = self.sql.getRec("slsiv2", cols=["count(*)"],
            where=[("si2_cono", "=", self.opts["conum"]), ("si2_group", "=",
            self.group), ("si2_code", "=", self.code), ("si2_loc", "=",
            self.loc)], limit=1)
        if trn[0]:
            return "Sales-2 Transactions Exist, Not Deleted"
        trn = self.sql.getRec("slsiv3", cols=["count(*)"],
            where=[("si3_cono", "=", self.opts["conum"]), ("si3_rgroup", "=",
            self.group), ("si3_rcode", "=", self.code)], limit=1)
        if trn[0]:
            return "Sales-3 Transactions Exist, Not Deleted"
        self.sql.delRec("strmf2", where=[("st2_cono", "=", self.opts["conum"]),
            ("st2_group", "=", self.group), ("st2_code", "=", self.code),
            ("st2_loc", "=", self.loc)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["strmf2", "D", "%03i%-3s%-20s%-1s" % \
            (self.opts["conum"], self.group, self.code, self.loc), "", dte,
        self.opts["capnm"], "", "", "", 0])
        st2 = self.sql.getRec("strmf2", cols=["count(*)"],
            where=[("st2_cono", "=", self.opts["conum"]), ("st2_group", "=",
            self.group), ("st2_code", "=", self.code)], limit=1)
        if not st2[0]:
            self.sql.delRec("strmf1", where=[("st1_cono", "=",
                self.opts["conum"]), ("st1_group", "=", self.group),
                ("st1_code", "=", self.code)])
            self.sql.insRec("chglog", data=["strmf1", "D", "%03i%-3s%-20s" % \
                (self.opts["conum"], self.group, self.code), "", dte,
                self.opts["capnm"], "", "", "", 0])
        # Other Files
        self.sql.delRec("strcst", where=[("stc_cono", "=", self.opts["conum"]),
            ("stc_group", "=", self.group), ("stc_code", "=", self.code),
            ("stc_loc", "=", self.loc)])
        self.sql.delRec("strprc", where=[("stp_cono", "=", self.opts["conum"]),
            ("stp_group", "=", self.group), ("stp_code", "=", self.code),
            ("stp_loc", "=", self.loc)])
        self.sql.delRec("strrcp", where=[("srr_cono", "=", self.opts["conum"]),
            ("srr_group", "=", self.group), ("srr_code", "=", self.code),
            ("srr_loc", "=", self.loc)])
        self.sql.delRec("strrcp", where=[("srr_cono", "=", self.opts["conum"]),
            ("srr_loc", "=", self.loc), ("srr_rgroup", "=", self.group),
            ("srr_rcode", "=", self.code)])
        self.sql.delRec("strvar", where=[("stv_cono", "=", self.opts["conum"]),
            ("stv_group", "=", self.group), ("stv_code", "=", self.code),
            ("stv_loc", "=", self.loc)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doDelRec(self):
        self.sql.delRec("strrcp", where=[("srr_cono", "=", self.opts["conum"]),
            ("srr_group", "=", self.group), ("srr_code", "=", self.code),
            ("srr_loc", "=", self.loc), ("srr_rgroup", "=", self.rgroup),
            ("srr_rcode", "=", self.rcode)])
        self.df.clearLine(2, focus=True)

    def doEnd(self):
        if self.df.frt == "T" and self.df.pag == 0:
            if self.newcode:
                self.df.focusField("T", 1, 1)
            else:
                if self.gtype == "R":
                    self.df.enableTag(2)
                self.df.skip[1] = [1]
                self.df.focusField("T", 1, 2, clr=False)
        elif self.df.frt == "T" and self.df.pag == 1:
            self.df.selPage("Basic-B")
        elif self.df.frt == "T" and self.df.pag == 2:
            if self.gtype == "R":
                self.df.selPage("Recipes")
            else:
                self.doEnder()
        elif self.df.frt == "C" and self.df.pag == 3:
            data = [self.opts["conum"], self.group, self.code, self.loc,
                self.rgroup, self.rcode, self.rqty]
            if self.newrec == "y":
                self.sql.insRec("strrcp", data=data)
                self.df.advanceLine(3)
            else:
                whr = [
                    ("srr_cono", "=", self.opts["conum"]),
                    ("srr_group", "=", self.group),
                    ("srr_code", "=", self.code),
                    ("srr_loc", "=", self.loc),
                    ("srr_rgroup", "=", self.rgroup),
                    ("srr_rcode", "=", self.rcode)]
                self.sql.updRec("strrcp", data=data, where=whr)
                self.doReadLoadRecipe()

    def doEnder(self):
        data = [self.opts["conum"]]
        for x in range(0, 2):
            data.append(self.df.t_work[0][0][x])
        for x in range(0, len(self.df.t_work[1][0])):
            if x in (3, 6, 8, 10, 12, 14):
                continue
            data.append(self.df.t_work[1][0][x])
        if self.newcode:
            self.sql.insRec("strmf1", data=data)
        elif data != self.old1[:len(data)]:
            col = self.sql.strmf1_col
            data.append(self.old1[col.index("st1_xflag")])
            self.sql.updRec("strmf1", data=data, where=[("st1_cono", "=",
                self.opts["conum"]), ("st1_group", "=", self.group),
                ("st1_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old1):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["strmf1", "U",
                        "%03i%-3s%-20s" % (self.opts["conum"], self.group,
                        self.code), col[num], dte, self.opts["capnm"],
                        str(dat), str(data[num]), "", 0])
        data = [self.opts["conum"], self.group, self.code, self.loc]
        for x in range(0, 4):
            data.append(self.df.t_work[2][0][x])
        if self.newloc == "Y":
            self.sql.insRec("strmf2", data=data)
        elif data != self.old2[:len(data)]:
            col = self.sql.strmf2_col
            data.append(self.old2[col.index("st2_xflag")])
            self.sql.updRec("strmf2", data=data, where=[("st2_cono", "=",
                self.opts["conum"]), ("st2_group", "=", self.group),
                ("st2_code", "=", self.code), ("st2_loc", "=", self.loc)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old2):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["strmf2", "U",
                        "%03i%-3s%-20s%-1s" % (self.opts["conum"], self.group,
                        self.code, self.loc), col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        self.sql.delRec("strcmu", where=[("smc_cono", "=", self.opts["conum"]),
            ("smc_group", "=", self.group), ("smc_code", "=", self.code),
            ("smc_loc", "=", self.loc)])
        for num, mup in enumerate(self.df.t_work[2][0][4:]):
            if mup and mup != self.mups[num]:
                self.sql.insRec("strcmu", data=[self.opts["conum"],
                    self.group, self.code, self.loc, num + 1, mup])
        self.opts["mf"].dbm.commitDbase()
        self.df.selPage("Basic-A")
        self.df.focusField("T", 0, 1)

    def doReadLoadRecipe(self):
        self.df.clearFrame("C", 3)
        self.df.focusField("C", 3, 1)
        rec = self.sql.getRec(tables=["strrcp", "strmf1"],
            cols=["srr_rgroup", "srr_rcode", "st1_desc", "srr_rqty"],
            where=[("srr_cono", "=", self.opts["conum"]), ("srr_group", "=",
            self.group), ("srr_code", "=", self.code), ("srr_loc", "=",
            self.loc), ("st1_cono=srr_cono",), ("st1_group=srr_rgroup",),
            ("st1_code=srr_rcode",)])
        if rec:
            mxs = (self.df.rows[3] - 1) * self.df.colq[3]
            for l, r in enumerate(rec):
                for i, d in enumerate(r):
                    c = l * self.df.colq[3]
                    if c > mxs:
                        c = mxs
                    self.df.loadEntry("C", 3, (c+i), data=d)
                self.df.advanceLine(3)

    def doExit(self):
        if self.df.frt == "T" and self.df.pag == 0:
            self.doQuit()
        elif self.df.frt == "T" and self.df.pag == 1:
            if self.newcode:
                self.df.focusField("T", 1, 1)
            else:
                self.df.skip[1] = [1]
                self.df.focusField("T", 1, 2, clr=False)
        elif self.df.frt == "T" and self.df.pag == 2:
            self.df.focusField("T", 2, 1)
        elif self.df.frt == "C" and self.df.pag == 3:
            if self.df.col == 1:
                self.df.focusField("C", 3, 1)
            else:
                self.doEnder()

    def doAccept(self):
        ok = "yes"
        for page in (1, 2):
            frt, pag, col, err = self.df.doCheckFields(("T", page, None))
            if err:
                ok = "no"
                if pag and pag != self.df.pag:
                    self.df.selPage(self.df.tags[pag - 1][0])
                self.df.focusField(frt, pag, (col+1), err=err)
                break
        if ok == "yes":
            self.doEnder()

    def doQuit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.selPage("Basic-A")
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
