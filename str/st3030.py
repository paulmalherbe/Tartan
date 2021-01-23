"""
SYNOPSIS
    Stores Ledger Selling And Cost Price List.

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
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import doWriteExport, getCost, getSell, getModName
from tartanFunctions import getVatRate, doPrinter, showError

class st3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvrf", "strloc", "strgrp",
            "strgmu", "strcmu", "strprc", "strmf1", "strmf2", "strtrn"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.stot = [0] * 6
        self.gtot = [0] * 6
        self.pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stores Selling Price List (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Selling Price","S"),("Cost Price","C"))
        if self.locs == "N":
            self.loc = "1"
            fld = []
        else:
            fld = [(("T",0,0,0),"IUA",1,"Location","",
                "1","Y",self.doLoc,loc,None,("efld",))]
        fld.extend([
            (("T",0,1,0),"IUA",3,"Product Group","",
                "","Y",self.doGroup,grp,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Ignore Out of Stock","",
                "Y","N",self.doNoStock,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Report Type","",
                "S","N",self.doType,None,None,None),
            (("T",0,4,0),"IUI",1,"Price Level","",
                0,"N",self.doLvl,None,None,("between",0,self.plevs)),
            (("T",0,5,0),("IRB",r1s),0,"Ignore Un-priced","",
                "Y","N",self.doNoPrice,None,None,None),
            (("T",0,6,0),("IRB",r1s),0,"V.A.T Inclusive","",
                "Y","N",self.doVat,None,None,None),
            (("T",0,7,0),("IRB",r1s),0,"Show Cost Price","",
                "N","N",self.doCost,None,None,None)])
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.getLoc(w)
        if not acc:
            return "Invalid Location"
        self.loc = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        if not w:
            self.group = ""
        else:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
            self.group = w

    def doNoStock(self, frt, pag, r, c, p, i, w):
        self.nostock = w

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtype = w
        if self.rtype == "C":
            return "sk4"
        if self.plevs == 1:
            self.levs = [1]
            self.df.loadEntry(frt, pag, p+1, data=1)
            return "sk1"

    def doLvl(self, frt, pag, r, c, p, i, w):
        if not w:
            self.levs = []
            for x in range(1, self.plevs + 1):
                self.levs.append(x)
        else:
            self.levs = [w]

    def doNoPrice(self, frt, pag, r, c, p, i, w):
        self.noprice = w

    def doLastSP(self, frt, pag, r, c, p, i, w):
        self.lasts = w

    def doVat(self, frt, pag, r, c, p, i, w):
        self.vatinc = w

    def doCost(self, frt, pag, r, c, p, i, w):
        self.costs = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("st2_cono", "=", self.opts["conum"])]
        if self.group:
            whr.append(("st2_group", "=", self.group))
        whr.append(("st1_type", "=", "N"))
        whr.append(("st2_loc", "=", self.loc))
        whr.extend([("st1_cono=st2_cono",), ("st1_group=st2_group",),
            ("st1_code=st2_code",)])
        odr = "st2_loc, st2_group, st2_code"
        recs = self.sql.getRec(tables=["strmf1", "strmf2"], cols=["st2_group",
            "st2_code", "st1_desc", "st1_uoi", "st1_vatcode"], where=whr,
            order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        elif self.rtype == "S":
            self.printSell(recs)
        else:
            self.printCost(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        expheads = ["%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            self.sysdttm)]
        if self.rtype == "S":
            expheads.append("Selling Price List as at %s" % self.sysdtd)
            mess = "Options:- Ignore Out of Stock: %s  VAT Inclusive: %s  "\
                "Ignore Un-priced: %s" % (self.nostock, self.vatinc,
                self.noprice)
            expheads.append(mess)
            expcolsh = [["Grp", "Product-Code", "Description", "U.O.I",
                "V", "Quantity"]]
            expforms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10),
                ("UA", 1), ("SD", 10.2)]
            for lev in self.levs:
                expcolsh[0].append("Level-%s" % lev)
                expforms.append(("UD", 9.2))
            if self.costs == "Y":
                expcolsh[0].extend(["Avg-Cost", "Last-Cost"])
                expforms.extend([("SD", 10.2), ("SD", 10.2)])
        else:
            expheads.append("Cost Price List as at %s" % self.sysdtd)
            mess = "Options:- Ignore Out of Stock: %s" % self.nostock
            expheads.append(mess)
            expcolsh = [["Grp", "Product-Code", "Description", "U.O.I",
                    "Quantity", "Avg-Cost", "Last-Cost"]]
            expforms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10),
                ("SD", 10.2), ("SD", 10.2), ("SD", 10.2)]
        expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.rtype == "S":
                grp, code, desc, uoi, vat, qty, acst, lcst, prcs = vals
                vvv = [grp.work, code.work, desc.work, uoi.work, vat.work,
                    qty.work]
                for lev in prcs:
                    vvv.append(lev.work)
                if self.costs == "Y":
                    vvv.extend([acst.work, lcst.work])
                expdatas.append(["BODY", vvv])
            else:
                grp, code, desc, uoi, qty, acst, lcst = vals
                expdatas.append(["BODY", [grp.work, code.work, desc.work,
                    uoi.work, qty.work, acst.work, lcst.work]])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=expheads, colsh=expcolsh, forms=expforms, datas=expdatas,
            rcdic=self.opts["mf"].rcdic)

    def printSell(self, recs):
        hdr = 77 + (len(self.levs) * 10)
        if self.costs == "Y":
            hdr += 22
        self.head = ("%03u %-30s" % (self.opts["conum"], self.opts["conam"]))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=hdr, foot=True)
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        old_grp = ""
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            grp, code, desc, uoi, vat, qty, acst, lcst, prcs = vals
            if old_grp and old_grp != grp.work:
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            txt = "%s %s %s %s %s" % (code.disp, desc.disp,
                uoi.disp, vat.disp, qty.disp)
            for prc in prcs:
                txt += " %s" % prc.disp
            if self.costs == "Y":
                txt += " %s" % acst.disp
                txt += " %s" % lcst.disp
            self.fpdf.drawText(txt)
            self.pglin += 1
            old_grp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.fpdf.output(self.pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=self.pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def printCost(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s" % (self.opts["conum"], self.opts["conam"]))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=100, foot=True)
        old_grp = ""
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            grp, code, desc, uoi, qty, acst, lcst = vals
            if old_grp and old_grp != grp.work:
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s" % (code.disp, desc.disp,
                uoi.disp, qty.disp, acst.disp, lcst.disp))
            self.pglin += 1
            old_grp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.fpdf.output(self.pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=self.pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        grp = CCD(data[0], "UA", 3)
        self.groupd = grp.disp
        code = CCD(data[1], "NA", 20)
        desc = CCD(data[2], "UA", 30)
        uoi = CCD(data[3], "NA", 10)
        # Cost Prices and Balances
        cst, bal = getCost(self.sql, self.opts["conum"], grp.work, code.work,
            loc=self.loc, qty=1, ind="AL", bal=True)
        qty = CCD(bal[0], "SD", 12.2)
        if self.nostock == "Y" and qty.work <= 0:
            return
        acst = CCD(cst[0], "SD", 10.2)
        lcst = CCD(cst[1], "SD", 10.2)
        if self.rtype == "C":
            return (grp, code, desc, uoi, qty, acst, lcst)
        # Selling Prices
        vat = CCD(data[4], "NA", 1)
        rte = 0
        if self.vatinc == "Y":
            vatrte = getVatRate(self.sql, self.opts["conum"],
                vat.work, self.sysdtw)
            if vatrte is not None:
                rte = vatrte
        prcs = []
        for lev in self.levs:
            prc = getSell(self.sql, self.opts["conum"], grp.work, code.work,
                self.loc, lev)
            prcs.append(CCD(round((prc*((100 + rte)/100.0)),2), "UD", 9.2))
        if self.noprice == "Y":
            cont = False
            for prc in prcs:
                if prc.work:
                    cont = True
                    break
            if not cont:
                return
        return (grp, code, desc, uoi, vat, qty, acst, lcst, prcs)

    def pageHeading(self):
        locd = self.getLoc(self.loc)[0]
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.rtype == "S":
            self.fpdf.drawText("%-24s %-10s" % ("Selling Price List as at",
                self.sysdtd))
            self.fpdf.drawText()
            mess = "%-31s %1s %-14s %1s %-16s %s" % (
                "(Options:- Ignore Out of Stock:", self.nostock,
                "VAT Inclusive:", self.vatinc,
                "Ignore Un-priced:", self.noprice)
            self.fpdf.drawText("%s%s" % (mess, ")"))
        else:
            self.fpdf.drawText("%-21s %-10s" % ("Cost Price List as at",
                self.sysdtd))
            self.fpdf.drawText()
            self.fpdf.drawText("%-31s %1s%1s" % (
                "(Options:- Ignore Out of Stock:", self.nostock, ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %3s  %-8s %s %s" % \
            ("Group", self.groupd, "Location", self.loc, locd))
        self.fpdf.drawText()
        cost = "Avg-Cost"
        last = "Last-Cost"
        if self.rtype == "S":
            self.txt = "%-20s %-30s %-10s %1s %11s " % ("Product-Code",
                "Description", "U.O.I", "V", "Quantity")
            for lev in self.levs:
                self.txt += "   Level-%s" % lev
            if self.costs == "Y":
                self.txt += " %9s  %9s" % (cost, last)
        else:
            self.txt = "%-20s %-30s %-10s %11s  %9s  %9s" % ("Product-Code",
                "Description", "U.O.I", "Quantity", cost, last)
        self.fpdf.drawText(self.txt)
        self.fpdf.underLine(txt=self.txt)
        self.fpdf.setFont()
        self.pglin = 10

    def getLoc(self, loc):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
            loc)], limit=1)
        return acc

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
