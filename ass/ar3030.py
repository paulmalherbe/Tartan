"""
SYNOPSIS
    Asset Register Account Statements.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError
from tartanWork import artrtp, armvtp

class ar3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["assgrp", "assmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.rordp = assctl["cta_rordp"]
        self.fromad = assctl["cta_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Asset Account Statements (%s)" % self.__class__.__name__)
        eper = int(self.sysdtw / 100)
        if eper > self.eper:
            eper = self.eper
        asg = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Start Period","",
                self.sper,"Y",self.doSdate,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"End Period","",
                eper,"N",self.doEdate,None,None,("efld",)),
            (("T",0,2,0),"IUA",3,"Product Group","",
                "","N",self.doGroup,asg,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Asset per Page","",
                "N","N",self.doPage,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doSdate(self, frt, pag, r, c, p, i, w):
        if w < self.sper or w > self.eper:
            return "Invalid Period"
        self.sdate = w

    def doEdate(self, frt, pag, r, c, p, i, w):
        if w < self.sdate or w > self.eper:
            return "Invalid Period"
        self.edate = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("assgrp", cols=["asg_desc"],
                where=[("asg_cono", "=", self.opts["conum"]), ("asg_group",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
        self.group = w

    def doPage(self, frt, pag, r, c, p, i, w):
        self.npag = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.group:
            self.sgrp = ""
            self.egrp = "zzz"
        else:
            self.sgrp = self.group
            self.egrp = self.group
        recs = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_group", ">=", self.sgrp), ("asm_group",
            "<=", self.egrp)], order="asm_group, asm_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.rordp == "Y":
            self.head = "%03u %-118s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-91s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        oldgrp = ""
        oldcod = ""
        self.pglin = 999
        mc = self.sql.assmst_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.grp = CCD(dat[mc.index("asm_group")], "UA", 3)
            self.cod = CCD(dat[mc.index("asm_code")], "Na", 7)
            self.desc = CCD(dat[mc.index("asm_desc")], "NA", 30)
            bals = Balances(self.opts["mf"], "ASS", self.opts["conum"],
                self.sper, keys=(self.grp.work, self.cod.work))
            asset = bals.doAssBals(start=self.sdate, end=self.edate, trans="C")
            if not asset:
                continue
            cap, cdp, rdp, cbl, rbl, mov, trn = asset
            self.bal1 = cbl
            self.bal2 = rbl
            if trn[0]:
                for z in trn[0]:
                    dt = CCD(z[trn[1].index("ast_date")], "d1", 10)
                    rf = CCD(z[trn[1].index("ast_refno")], "Na", 9)
                    tp = CCD(z[trn[1].index("ast_type")], "UI", 1)
                    bt = CCD(z[trn[1].index("ast_batch")], "Na", 7)
                    mv = CCD(z[trn[1].index("ast_mtyp")], "UI", 1)
                    m1 = CCD(z[trn[1].index("ast_amt1")], "SD", 13.2)
                    m2 = CCD(z[trn[1].index("ast_amt2")], "SD", 13.2)
                    ds = CCD(z[trn[1].index("ast_desc")], "NA", 30)
                    if self.pglin > (self.fpdf.lpp - 10):
                        self.pageHeading()
                    if (oldgrp and self.grp.work != oldgrp) or \
                            (oldcod and self.cod.work != oldcod):
                        if self.npag == "Y":
                            self.pageHeading()
                        else:
                            self.accountHeading()
                    self.bal1 = float(ASD(self.bal1) + ASD(m1.work))
                    self.bal2 = float(ASD(self.bal2) + ASD(m2.work))
                    b1 = CCD(self.bal1, "SD", 13.2)
                    if self.rordp == "Y":
                        b2 = CCD(self.bal2, "SD", 13.2)
                        self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" % \
                            (dt.disp, rf.disp, artrtp[tp.work-1][0], bt.disp,
                            armvtp[mv.work-1][0], m1.disp, b1.disp, m2.disp,
                            b2.disp, ds.disp))
                    else:
                        self.fpdf.drawText("%s %s %s %s %s %s %s %s" % \
                            (dt.disp, rf.disp, artrtp[tp.work-1][0], bt.disp,
                            armvtp[mv.work-1][0], m1.disp, b1.disp, ds.disp))
                    self.pglin += 1
                    oldgrp = self.grp.work
                    oldcod = self.cod.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    repeml=self.df.repeml, fromad=self.fromad)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.rordp == "Y":
            self.fpdf.drawText("%-22s %-99s" % ("Asset Statements as at",
                self.sysdtd))
        else:
            self.fpdf.drawText("%-22s %-71s" % ("Asset Statements as at",
                self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("(Options: From Period %7s to Period %7s)" % \
            (self.df.t_disp[0][0][0], self.df.t_disp[0][0][1]))
        self.fpdf.setFont()
        self.pglin = 5
        self.accountHeading()

    def accountHeading(self):
        if self.pglin > (self.fpdf.lpp - 10):
            self.pageHeading()
        else:
            acc = self.sql.getRec("assgrp", cols=["asg_desc"],
                where=[("asg_cono", "=", self.opts["conum"]), ("asg_group",
                "=", self.grp.work)], limit=1)
            if not acc:
                acc = [""]
            self.fpdf.setFont(style="B")
            self.fpdf.underLine(txt=self.head)
            self.fpdf.drawText("Group %3s %s    Code %-7s %s" % (self.grp.disp,
                acc[0], self.cod.disp, self.desc.disp))
            self.fpdf.drawText()
            if self.rordp == "Y":
                self.fpdf.drawText("%-10s %-9s %-3s %-7s %-3s %13s %13s %13s "\
                    "%13s %-30s" % ("   Date", "Reference", "Typ", "BatchNo",
                    "Mov", "Amount-C ", "Balance-C ", "Amount-R ", "Balance-R ",
                    "Description"))
            else:
                self.fpdf.drawText("%-10s %-9s %-3s %-7s %-3s %13s %13s "\
                    "%-30s" % ("   Date", "Reference", "Typ", "BatchNo",
                    "Mov", "Amount-C ", "Balance-C ", "Description"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            b1 = CCD(self.bal1, "SD", 13.2)
            if self.rordp == "Y":
                b2 = CCD(self.bal2, "SD", 13.2)
                self.fpdf.drawText("%-50s %-13s %-13s %-13s %-30s" % \
                    ("", b1.disp, "", b2.disp, "Balance Forward"))
            else:
                self.fpdf.drawText("%-50s %-13s %-30s" % \
                    ("", b1.disp, "Balance Forward"))
            self.pglin += 6

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
