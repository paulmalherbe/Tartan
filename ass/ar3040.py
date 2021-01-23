"""
SYNOPSIS
    Asset Register Register.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, doWriteExport, showError

class ar3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["assgrp", "assmst", "asstrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        assctl = self.gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.rordp = assctl["cta_rordp"]
        self.fromad = assctl["cta_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        self.head = ("%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], "%s"))
        self.colsh = ["Code", "Description", "Purch-Date", "Cost-Price",
            "Accum-Dep", "Opening-Bal", "Purchases", "Improvements",
            "Write-Offs", "Depreciation", "Sales", "Profit/Loss",
            "Closing-Bal"]
        self.forms = [("Na", 7), ("NA", 30), ("d1", 10)] + [("SD", 13.2)] * 10
        self.stot = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.gtot = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.oldgrp = ""
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Asset Register Report (%s)" % self.__class__.__name__)
        eper = int(self.sysdtw / 100)
        if eper > self.eper:
            eper = self.eper
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        r1s = (("Company","C"), ("Receiver","R"))
        r2s = (("Yes","Y"), ("No","N"))
        fld = [
            (("T",0,0,0),"ID2",7,"Cut-Off Period","",
                eper,"Y",self.doPeriod,None,None,("efld",))]
        if self.rordp == "Y":
            fld.append((("T",0,1,0),("IRB",r1s),0,"Report Type","",
                "C","N",self.doType,None,None,None))
            seq = 2
        else:
            seq = 1
            self.rtype = "C"
        fld.extend([
            (("T",0,seq,0),"IUA",3,"Asset Group","",
                "","N",self.doGroup,grp,None,None),
            (("T",0,seq+1,0),("IRB",r2s),0,"Ignore Zero Items","",
                "Y","N",self.doZero,None,None,None)])
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doPeriod(self, frt, pag, r, c, p, i, w):
        if w < self.sper or w > self.eper:
            return "Invalid Period"
        self.endper = w

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtype = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("assgrp", cols=["asg_desc"],
                where=[("asg_cono", "=", self.opts["conum"]), ("asg_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
        self.group = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        if self.rtype == "C":
            self.typ = "Company"
        else:
            self.typ = "Receiver"
        if not self.group:
            self.sgrp = ""
            self.egrp = "zzz"
        else:
            self.sgrp = self.group
            self.egrp = self.group
        cols = ["asm_group", "asm_code", "asm_desc"]
        recs = self.sql.getRec("assmst", cols=cols, where=[("asm_cono",
            "=", self.opts["conum"]), ("asm_group", ">=", self.sgrp),
            ("asm_group", "<=", self.egrp)], order="asm_group, asm_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Asset Register Report as at %s" % self.sysdtd)
        self.expheads.append("Options: Report Period: %s Report Type: %s" % \
            (self.df.t_disp[0][0][0], self.typ))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for seq, dat in enumerate(recs):
            p.displayProgress(seq)
            if p.quit:
                p.closeProgress()
                return
            if not seq:
                desc = self.groupDesc(dat[0])
                self.expdatas.append(["HEAD", ["", "Group %s %s" % (dat[0],
                    desc)]])
                self.expdatas.append(["BLANK"])
            vals = self.getValues(dat)
            if not vals:
                continue
            pdte = self.sql.getRec("asstrn", cols=["min(ast_date)"],
                where=[("ast_cono", "=", self.opts["conum"]), ("ast_group",
                "=", dat[0]), ("ast_code", "=", dat[1]), ("ast_mtyp", "=", 1)],
                limit=1)
            pdte = CCD(pdte[0], "d1", 10).work
            if self.oldgrp and self.oldgrp != dat[0]:
                self.groupTotal()
                self.expdatas.append(["BLANK"])
                desc = self.groupDesc(dat[0])
                self.expdatas.append(["HEAD", ["", "Group %s %s" % (dat[0],
                    desc)]])
                self.expdatas.append(["BLANK"])
            line = ["BODY", [dat[1], dat[2], pdte]]
            for num, val in enumerate(vals):
                line[1].append(val)
                self.stot[num] = float(ASD(self.stot[num]) + ASD(val))
                self.gtot[num] = float(ASD(self.gtot[num]) + ASD(val))
            self.expdatas.append(line)
            self.oldgrp = dat[0]
        p.closeProgress()
        self.groupTotal()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        pad = chrs - 35 - len(self.sysdttm)
        self.head1 = self.head % (" " * pad + self.sysdttm)
        self.head2 = "Asset Register Report as at %s%s" % (self.sysdtd, "%s%s")
        pad = chrs - len(self.head2) + 4 - 11  # %s%s and ' Page     1'
        self.head2 = self.head2 % (" " * pad, " Page %5s")
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head1)
        self.pgnum = 0
        self.pglin = 999
        for seq, dat in enumerate(recs):
            p.displayProgress(seq)
            if p.quit:
                break
            grp = CCD(dat[0], "UA", 3)
            code = CCD(dat[1], "Na", 7)
            desc = CCD(dat[2], "NA", 30)
            pdte = self.sql.getRec("asstrn", cols=["min(ast_date)"],
                where=[("ast_cono", "=", self.opts["conum"]), ("ast_group",
                "=", grp.work), ("ast_code", "=", code.work), ("ast_mtyp",
                "=", 1)], limit=1)
            pdte = CCD(pdte[0], "d1", 10)
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.oldgrp and self.oldgrp != grp.work:
                self.groupTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading(grp)
            ldic = {}
            for num, val in enumerate(vals):
                ldic["v%s" % num] = CCD(val, "SD", 13.2)
                self.stot[num] = float(ASD(self.stot[num]) + ASD(val))
                self.gtot[num] = float(ASD(self.gtot[num]) + ASD(val))
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s %s %s" %
                (code.disp, desc.disp, pdte.disp, ldic["v0"].disp,
                ldic["v1"].disp, ldic["v2"].disp, ldic["v3"].disp,
                ldic["v4"].disp, ldic["v5"].disp, ldic["v6"].disp,
                ldic["v7"].disp, ldic["v8"].disp, ldic["v9"].disp))
            self.pglin += 1
            self.oldgrp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.groupTotal()
            if self.pglin > (self.fpdf.lpp - 2):
                self.pageHeading(grp)
            self.grandTotal()
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                repeml=self.df.repeml, fromad=self.fromad)

    def getValues(self, data):
        bals = Balances(self.opts["mf"], "ASS", self.opts["conum"], self.sper,
            keys=(data[0], data[1]))
        asset = bals.doAssBals(start=self.sper, end=self.endper)
        if not asset:
            return
        cap, cdp, rdp, cbl, rbl, mov = asset
        vals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        vals[0] = cap
        if self.rtype == "C":
            vals[1] = cdp
            vals[2] = cbl
            vals[9] = cbl
        else:
            vals[1] = rdp
            vals[2] = rbl
            vals[9] = rbl
        woff = False
        sold = False
        if mov:
            for m in mov:
                if m[0] == 3:
                    woff = True
                if m[0] == 5:
                    sold = True
                if self.rtype == "C":
                    idx = 1
                else:
                    idx = 2
                vals[m[0]+2] = float(ASD(vals[m[0]+2]) + ASD(m[idx]))
                vals[9] = float(ASD(vals[9]) + ASD(m[idx]))
        if woff or sold:
            vals[8] = vals[9]
            vals[9] = 0
        if self.zero == "Y" and all(v == 0 for v in vals[2:10]):
            return
        return vals

    def pageHeading(self, grp):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2 % self.pgnum)
        self.fpdf.drawText()
        self.fpdf.drawText("(%s %s %s %s)" % ("Options: Report Period:",
            self.df.t_disp[0][0][0], "Report Type:", self.typ))
        self.fpdf.drawText()
        grpdesc = self.groupDesc(grp.work)
        self.fpdf.drawText("%-5s %3s %-30s" % ("Group", grp.disp, grpdesc))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %10s %13s %13s %13s %13s %13s %13s "\
            "%13s %13s %13s %13s" % ("Code", "Description", "Purch-Date",
            "Cost-Price ", "Accum-Dep ", "Opening-Bal ", "Purchases ",
            "Improvements ", "  Write-Offs ", "Depreciation ", "Sales ",
            " Profit/Loss ", " Closing-Bal "))
        self.fpdf.underLine(txt=self.head1)
        self.fpdf.setFont()
        self.pglin = 10

    def groupDesc(self, group):
        acc = self.sql.getRec("assgrp", cols=["asg_desc"],
            where=[("asg_cono", "=", self.opts["conum"]), ("asg_group", "=",
            group)], limit=1)
        if not acc:
            return ""
        return acc[0]

    def groupTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL",
                ["", "Group %s Totals" % self.oldgrp, ""] + self.stot])
            self.stot = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            return
        ldic = {}
        for num, val in enumerate(self.stot):
            ldic["v%s" % num] = CCD(val, "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %10s %13s %13s %13s %13s %13s %13s "\
            "%13s %13s %13s %13s" % ("", "Group %s Totals" % self.oldgrp, "",
            ldic["v0"].disp, ldic["v1"].disp, ldic["v2"].disp, ldic["v3"].disp,
            ldic["v4"].disp, ldic["v5"].disp, ldic["v6"].disp, ldic["v7"].disp,
            ldic["v8"].disp, ldic["v9"].disp))
        self.fpdf.drawText()
        self.stot = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL",
                ["", "Grand Totals", ""] + self.gtot])
            self.expdatas.append(["ULINED"])
            return
        ldic = {}
        for num, val in enumerate(self.gtot):
            ldic["v%s" % num] = CCD(val, "SD", 13.2)
        self.fpdf.drawText("%-7s %-30s %10s %13s %13s %13s %13s %13s %13s "\
            "%13s %13s %13s %13s" % (" ", "Grand Totals", "", ldic["v0"].disp,
            ldic["v1"].disp, ldic["v2"].disp, ldic["v3"].disp, ldic["v4"].disp,
            ldic["v5"].disp, ldic["v6"].disp, ldic["v7"].disp, ldic["v8"].disp,
            ldic["v9"].disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
