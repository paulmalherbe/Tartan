"""
SYNOPSIS
    Stores Ledger Print Labels. L7159

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
from TartanClasses import ASD, CCD, GetCtl, TartanLabel, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getCost, getModName, doPrinter, getSell
from tartanFunctions import getVatRate, showError
from tartanWork import labels

class st3110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvrf", "strgrp", "strloc",
            "strprc", "strmf1", "strmf2", "strtrn"],
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
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Print Stores Labels (%s)" % self.__class__.__name__)
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
        stm = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_group", "", 0, "Grp"),
                ("st1_code", "", 0, "Product Code"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "<>", "X")],
            "whera": [["T", "st1_group", 2, 0]],
            "index": 1}
        lab = {
            "stype": "C",
            "head": ("Codes",),
            "data": list(labels.keys())}
        r1s = (("Normal", "N"), ("Recipes", "R"))
        r2s = (("Average", "A"), ("Standard", "S"), ("All", "B"))
        r3s = (("No", "N"), ("Yes", "Y"))
        fld = [
            (("T",0,0,0),"ID1",10,"Reporting Date","",
                self.sysdtw,"Y",self.doDate,None,None,("efld",)),
            [("T",0,1,0),"IUA",1,"Location","",
                0,"Y",self.doLoc,loc,None,None],
            (("T",0,2,0),"IUA",3,"Product Group","",
                "","Y",self.doGrp,gpm,None,None),
            (("T",0,3,0),"INA",20,"Product Code","",
                "","Y",self.doCode,stm,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Item Types","",
                "N","Y",self.doTypes,None,None,None),
            (("T",0,5,0),("IRB",r2s),0,"Value Indicator","",
                "A","Y",self.doValInd,None,None,None),
            (("T",0,6,0),("IRB",r3s),0,"Include Out of Stock ","",
                "N","Y",self.doOuts,None,None,None),
            (("T",0,7,0),"IUA",10,"Cost Price Code","",
                "","Y",self.doCCode,None,None,None),
            (("T",0,8,0),"IUA",5,"Avery A4 Code","",
                "L7159","Y",self.doAvery,lab,None,("in",labels)),
            (("T",0,9,0),"IUI",2,"First Label Row","",
                1,"Y",self.doRow,None,None,("notzero",)),
            (("T",0,10,0),"IUI",2,"First Label Column","",
                1,"Y",self.doCol,None,None,("notzero",))]
        if self.locs == "N":
            fld[1][1] = "OUA"
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry(frt, pag, p+1, data=self.loc)
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.loc = w
        if self.loc:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
                self.loc)], limit=1)
            if not acc:
                return "Invalid Location Code"

    def doGrp(self, frt, pag, r, c, p, i, w):
        self.grp = w
        if self.grp:
            acc = self.sql.getRec("strgrp", cols=["gpm_group"],
                where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        if self.code:
            acc = self.sql.getRec("strmf1", cols=["st1_desc"],
                where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                "=", self.grp), ("st1_code", "=", w), ("st1_type", "<>", "X")],
                limit=1)
            if not acc:
                return "Invalid or Redundant Code"

    def doTypes(self, frt, pag, r, c, p, i, w):
        self.types = w

    def doValInd(self, frt, pag, r, c, p, i, w):
        self.valind = w

    def doOuts(self, frt, pag, r, c, p, i, w):
        self.outs = w

    def doCCode(self, frt, pag, r, c, p, i, w):
        self.ccode = w
        if self.ccode:
            spl = w.split()
            if len(spl) != 1 or len(spl[0]) != 10:
                return "Must Have 10 Valid Characters"

    def doAvery(self, frt, pag, r, c, p, i, w):
        self.label = w

    def doRow(self, frt, pag, r, c, p, i, w):
        if w > labels[self.label]["NY"]:
            return "Out of Range"
        self.srow = w

    def doCol(self, frt, pag, r, c, p, i, w):
        if w > labels[self.label]["NX"]:
            return "Out of Range"
        self.scol = w

    def doEnd(self):
        self.df.closeProcess()
        self.prnt = False
        whr = [("st1_cono", "=", self.opts["conum"])]
        if self.grp:
            whr.append(("st1_group", "=", self.grp))
        if self.code:
            whr.append(("st1_code", "=", self.code))
        whr.append(("st1_type", "=", self.types))
        if self.valind in ("A", "S"):
            whr.append(("st1_value_ind", "=", self.valind))
        if self.loc:
            whr.append(("st2_loc", "=", self.loc))
        whr.extend([
            ("st2_cono=st1_cono",),
            ("st2_group=st1_group",),
            ("st2_code=st1_code",)])
        rec = self.sql.getRec(tables=["strmf1", "strmf2"], cols=["st2_loc",
            "st2_group", "st2_code", "st1_desc", "st1_value_ind",
            "st1_vatcode"], where=whr, order="st2_group, st2_code, st2_loc")
        if not rec:
            showError(self.opts["mf"].body, "Error", "No Records Selected")
        else:
            self.fpdf = TartanLabel(self.label, posY=self.srow, posX=self.scol)
            self.fpdf.add_page()
            p = ProgressBar(self.opts["mf"].body, mxs=len(rec), esc=True)
            for num, dat in enumerate(rec):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(dat)
            p.closeProgress()
            if self.fpdf.page and not p.quit:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt)
        self.closeProcess()

    def doProcess(self, dat):
        loc, group, code, desc, valind, vatcod = dat
        icost, bal = getCost(self.sql, self.opts["conum"], group, code,
            loc=loc, qty=1, ind="I", bal=True)
        if self.outs == "N" and not bal[0]:
            return
        if self.ccode:
            # Calculate cost price code
            cost = CCD(int(icost * 100), "UI", 9)
            ncost = " " * (9 - len(str(cost.work)))
            for x in str(cost.work):
                ncost = ncost + self.ccode[int(x)]
            lab = "%-30s %13s" % (self.df.t_disp[0][0][0], ncost)
        else:
            lab = "%-30s" % self.df.t_disp[0][0][0]
        ####################################################################
        lab = "%s\n%s %s %s" % (lab, loc, group, code)
        lab = "%s\n%s\n" % (lab, desc)
        prc = getSell(self.sql, self.opts["conum"], group, code, loc)
        price1 = CCD(prc, "UD", 9.2)
        vrte = getVatRate(self.sql, self.opts["conum"], vatcod, self.date)
        if vrte is None:
            vrte = CCD(0, "UD", 9.2)
        else:
            vrte = CCD(vrte, "UD", 9.2)
        price2 = CCD(round((price1.work * float(ASD(100) + \
            ASD(vrte.work)) / 100.0), 2), "OUD", 9.2)
        lab = "%s\n%s %s %s" % (lab, vatcod, price1.disp, price2.disp)
        self.fpdf.add_label(lab)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
