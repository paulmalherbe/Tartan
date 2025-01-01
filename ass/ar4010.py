"""
SYNOPSIS
    Asset Register Interrogation.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, NotesCreate
from TartanClasses import Sql, SelectChoice, TabPrt, TartanDialog
from tartanFunctions import askChoice, getModName, doPrinter
from tartanWork import artrtp, armvtp

class ar4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["assctl", "assgrp", "assdep",
            "assmst", "asstrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        assctl = self.gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.glint = assctl["cta_glint"]
        self.rordp = assctl["cta_rordp"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Asset Register Interrogation (%s)" % self.__class__.__name__)
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        cod = {
            "stype": "R",
            "tables": ("assmst",),
            "cols": (
                ("asm_code", "", 0, "Code"),
                ("asm_desc", "", 0, "Description", "Y")),
            "where": [("asm_cono", "=", self.opts["conum"])],
            "whera": (("T", "asm_group", 0, 0),)}
        tag = (
            ("Depreciation", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,0), ("T",0,1)),
            ("Transactions", self.doTrans1, ("T",0,0), ("T",0,1)))
        r1s = (
            ("Straight Line","S"),
            ("Balance","D"),
            ("None","N"))
        r2s = (("Yes","Y"),("No","N"))
        fld = [
            (("T",0,0,0),"IUA",3,"Group","Asset Group",
                "","N",self.doGroup,grp,None,("notblank",)),
            (("T",0,0,0),"INa",7,"Code","Asset Code",
                "","N",self.doCode,cod,None,("notblank",)),
            (("T",0,0,0),"ONA",30,"Description"),
            (("T",1,0,0),"ONa",3,"Dep Code"),
            (("T",1,0,0),"ONA",40,""),
            (("T",1,1,0),("ORB",r1s[:-1]),0,"Company Type"),
            (("T",1,2,0),("ORB",r1s),0,"Receiver Type")]
        if self.rordp == "Y":
            fld.extend([
                (("C",1,0,0),"OUD",15.2,"Company-Rate","",
                    "","N",None,None,None,None,("Period",7)),
                (("C",1,0,1),"OUD",15.2,"Receiver-Rate")])
        else:
            fld.append(
                (("C",1,0,0),"OUD",15.2,"Rate","",
                    "","N",None,None,None,None,("Period",7)))
        fld.extend([
            (("T",2,0,0),"Od1",10,"Date of Purchase"),
            (("T",2,0,0),"OSD",15.2,"Purchase Price")])
        if self.rordp == "Y":
            fld.extend([
                (("C",2,0,0),"OSD",15.2,"Company-Value","","","N",
                    None,None,None,None,("Details",7)),
                (("C",2,0,1),"OSD",15.2,"Receiver-Value")])
        else:
            fld.append(
                (("C",2,0,0),"OSD",15.2,"Value","","","N",
                    None,None,None,None,("Details",7)))
        fld.append(
            (("T",3,0,0),("IRB",r2s),0,"History","",
                "N","N",self.doTrans2,None,None,None))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEndTop, "N"), None, None, None)
        txt = (self.doExit, None, None, self.doExit)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        for x in range(7):
            self.df.colLabel[1][x].configure(text="Year %s" % (x + 1))
        self.df.colLabel[2][0].configure(text="Opening Book Value")
        self.df.colLabel[2][1].configure(text="Purchases         ")
        self.df.colLabel[2][2].configure(text="Improvements      ")
        self.df.colLabel[2][3].configure(text="Write Offs        ")
        self.df.colLabel[2][4].configure(text="Depreciation      ")
        self.df.colLabel[2][5].configure(text="Sales             ")
        self.df.colLabel[2][6].configure(text="Closing Book Value")

    def doGroup(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.opts["conum"]), ("asg_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Asset Group"
        self.group = w

    def doCode(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assmst", cols=["asm_desc", "asm_depcod"],
            where=[("asm_cono", "=", self.opts["conum"]), ("asm_group", "=",
            self.group), ("asm_code", "=", w)], limit=1)
        if not acc:
            return "Asset Does Not Exist"
        self.code = w
        self.desc = acc[0]
        self.df.loadEntry(frt, pag, p+1, data=self.desc)
        dep = self.sql.getRec("assdep", where=[("asd_cono", "=",
            self.opts["conum"]), ("asd_code", "=", acc[1])], limit=1)
        for x in range(self.df.topq[1]):
            self.df.loadEntry("T", 1, x, data=dep[x+1])
        if self.rordp == "Y":
            for y in range(14):
                self.df.loadEntry("C", 1, y, data=dep[x+y+2])
        else:
            p = 5
            for y in range(7):
                self.df.loadEntry("C", 1, y, data=dep[p])
                p += 2
        self.loadBalances()
        self.opts["mf"].updateStatus("")

    def doEndTop(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def loadBalances(self):
        bals = Balances(self.opts["mf"], "ASS", self.opts["conum"], self.sper,
            keys=(self.group, self.code))
        asset = bals.doAssBals(start=self.sper, end=self.eper, trans="C")
        if not asset:
            return
        cap, cdp, rdp, cbl, rbl, mov, trn = asset
        dte = self.sql.getRec("asstrn", cols=["min(ast_date)"],
            where=[("ast_cono", "=", self.opts["conum"]), ("ast_group", "=",
            self.group), ("ast_code", "=", self.code), ("ast_mtyp", "=",
            1)], limit=1)
        if dte[0]:
            val = self.sql.getRec("asstrn", cols=["ast_amt1"],
                where=[("ast_cono", "=", self.opts["conum"]), ("ast_group",
                "=", self.group), ("ast_code", "=", self.code), ("ast_mtyp",
                "=", 1), ("ast_date", "=", dte[0])], limit=1)
            self.df.loadEntry("T", 2, 0, data=dte[0])
            self.df.loadEntry("T", 2, 1, data=val[0])
        self.df.loadEntry("C", 2, 0, data=cbl)
        if self.rordp == "Y":
            self.df.loadEntry("C", 2, 1, data=rbl)
        else:
            self.df.loadEntry("C", 2, 1, data=0)
        if mov:
            for n, c, r in mov:
                if self.rordp == "Y":
                    p = n * 2
                else:
                    p = n
                cbl = float(ASD(cbl) + ASD(c))
                if self.rordp == "Y":
                    rbl = float(ASD(rbl) + ASD(r))
                self.df.loadEntry("C", 2, p, data=c)
                if self.rordp == "Y":
                    self.df.loadEntry("C", 2, p+1, data=r)
        if self.rordp == "Y":
            self.df.loadEntry("C", 2, 12, data=cbl)
            self.df.loadEntry("C", 2, 13, data=rbl)
        else:
            self.df.loadEntry("C", 2, 6, data=cbl)

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 3, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        tit = "Transactions for Item: %s %s - %s" % \
            (self.group, self.code, self.desc)
        dat, atc, col = self.getTrans(hist=w)
        if dat:
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page3, tit, atc, dat)
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    whr = [("ast_seq", "=", rec.selection[len(col)])]
                    TabPrt(self.opts["mf"], tabs="asstrn", where=whr,
                        pdia=False)
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "ASS", "%3s%s" % (self.group, self.code))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("Depreciation")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = (
            ("Balances", "B"),
            ("Transactions", "T"),
            ("Both", "A"),
            ("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if self.rordp == "Y":
            self.head = "%03u %-93s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-77s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        if opt != "T":
            self.pageHeading()
            self.printInfo()
        if opt == "B":
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit,
                    repprt=["N", "V", "view"])
        elif opt == "A":
            dat, atc, col = self.getTrans()
            if not dat:
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
            else:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans(dat, atc)
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])
        elif opt == "T":
            dat, atc, col = self.getTrans()
            if dat:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans(dat, atc)
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit,
                        repprt=["N", "V", "view"])

    def printInfo(self):
        for x in range(0, len(self.df.topf[0])):
            self.fpdf.drawText("%-15s%-30s %s" % ("",
                self.df.topf[0][x][3], self.df.t_disp[0][0][x]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-15s%-30s %s" % ("",
            self.df.topf[1][0][3], self.df.t_disp[1][0][0]))
        self.fpdf.drawText("%-15s%-30s %s" % ("",
            "Dep Description", self.df.t_disp[1][0][1]))
        self.fpdf.drawText()
        self.fpdf.drawText("%-15s%-30s     %s" % ("",
            "Date of Purchase", self.df.t_disp[2][0][0]))
        self.fpdf.drawText("%-15s%-30s %s" % ("",
            "Cost of Purchase", self.df.t_disp[2][0][1]))
        self.fpdf.drawText()
        self.pglin += 3 + len(self.df.topf[1])
        self.fpdf.setFont(style="B")
        if self.rordp == "Y":
            self.fpdf.drawText("%15s%-30s %15s %15s" % \
                ("", "Details", "Company ", "Receiver "))
            self.fpdf.underLine(txt="%15s%s" % ("", self.fpdf.suc * 61))
        else:
            self.fpdf.drawText("%15s%-30s %15s" % \
                ("", "Details", "Balances "))
            self.fpdf.underLine(txt="%15s%s" % ("", self.fpdf.suc * 45))
        self.fpdf.setFont()
        desc = (
            "Opening Book Value",
            "Purchases         ",
            "Improvements      ",
            "Write Offs        ",
            "Depreciation      ",
            "Sales             ",
            "Closing Book Value")
        for n, d in enumerate(self.df.c_disp[2]):
            if n == 6:
                if self.rordp == "Y":
                    self.fpdf.underLine(txt="%15s%s" % ("", self.fpdf.suc * 61))
                else:
                    self.fpdf.underLine(txt="%15s%s" % ("", self.fpdf.suc * 45))
            if self.rordp == "Y":
                self.fpdf.drawText("%15s%-30s %15s %15s" %
                        (" ", desc[n][:30], d[0], d[1]))
            else:
                self.fpdf.drawText("%15s%-30s %15s" %
                        (" ", desc[n][:30], d[0]))

    def printTrans(self, trn, atc):
        for ct in trn:
            trdt = CCD(ct[0], "D1", 10)
            ref1 = CCD(ct[5], "Na", 9)
            trtp = CCD(ct[3], "UI", 1)
            batch = CCD(ct[2], "Na", 7)
            mtyp = CCD(ct[4], "UI", 1)
            amt1 = CCD(ct[6], "SD", 15.2)
            if self.rordp == "Y":
                amt2 = CCD(ct[7], "SD", 15.2)
                detail = CCD(ct[8], "NA", 30)
            else:
                detail = CCD(ct[7], "NA", 30)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            if self.rordp == "Y":
                self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (trdt.disp,
                    ref1.disp, artrtp[(trtp.work - 1)][0], batch.disp,
                    armvtp[(mtyp.work - 1)][0], amt1.disp, amt2.disp,
                    detail.disp))
            else:
                self.fpdf.drawText("%s %s %s %s %s %s %s" % (trdt.disp,
                    ref1.disp, artrtp[(trtp.work - 1)][0], batch.disp,
                    armvtp[(mtyp.work - 1)][0], amt1.disp, detail.disp))
            self.pglin += 1

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.rordp == "Y":
            self.fpdf.drawText("%-35s %-61s" %
                ("Assets Register Interrogation as at", self.sysdtd))
        else:
            self.fpdf.drawText("%-35s %-45s" %
                ("Assets Register Interrogation as at", self.sysdtd))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def pageHeadingTrans(self):
        self.fpdf.setFont(style="B")
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %-10s %s %s %-5s %s %s" % ("", "",
            self.df.topf[0][0][3], self.df.t_disp[0][0][0], "",
            self.df.topf[0][1][3], self.df.t_disp[0][0][1]))
        self.fpdf.drawText()
        if self.rordp == "Y":
            self.fpdf.drawText("%-10s %-9s %-3s %-7s %3s %-15s %-15s %-30s" % \
                ("   Date", "Reference", "Typ", "Batch", "Mov",
                "      Amount-1", "      Amount-2", "Remarks"))
        else:
            self.fpdf.drawText("%-10s %-9s %-3s %-7s %3s %-15s %-30s" % \
                ("   Date", "Reference", "Typ", "Batch", "Mov",
                "      Amount-1", "Remarks"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def getTrans(self, hist="Y"):
        if self.rordp == "Y":
            col = ("ast_date", "ast_curdt", "ast_batch", "ast_type", "ast_mtyp",
                "ast_refno", "ast_amt1", "ast_amt2", "ast_desc", "ast_seq")
        else:
            col = ("ast_date", "ast_curdt", "ast_batch", "ast_type", "ast_mtyp",
                "ast_refno", "ast_amt1", "ast_desc", "ast_seq")
        atc = [
            ("ast_date", "   Date", 10, "D1", "N"),
            ("ast_curdt", "Curr-Dt", 7, "D2", "N"),
            ("ast_batch", "Batch", 7, "Na", "N"),
            ("ast_type", "Typ", 3, ("XX", artrtp), "N"),
            ("ast_mtyp", "Mov", 3, ("XX", armvtp), "N"),
            ("ast_refno", "Reference", 9, "Na", "Y"),
            ("ast_amt1", "  Amount-1", 15.2, "SD", "N")]
        if self.rordp == "Y":
            atc.append(("ast_amt2", "  Amount-2", 15.2, "SD", "N"))
        atc.extend([
            ("ast_desc", "Details", 30, "NA", "N"),
            ("ast_seq", "Sequence", 8, "UI", "N")])
        whr = [
            ("ast_cono", "=", self.opts["conum"]),
            ("ast_group", "=", self.group),
            ("ast_code", "=", self.code),
            ("ast_curdt", "<=", self.eper)]
        if hist == "N":
            whr.append(("ast_curdt", ">=", self.sper))
        odr = "ast_date, ast_refno"
        dat = self.sql.getRec("asstrn", cols=col, where=whr, order=odr)
        return dat, atc, col

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
