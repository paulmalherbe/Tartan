"""
SYNOPSIS
    Stores Stock Movement Report.

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
from tartanFunctions import doWriteExport, getModName, doPrinter, showError

class st3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strloc", "strmf1"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.stot = [0] * 8
        self.gtot = [0] * 8
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stock Movement Report (%s)" % self.__class__.__name__)
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
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Start Period","",
                int(self.sysdtw / 100),"Y",self.doSdate,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"End Period","",
                int(self.sysdtw / 100),"Y",self.doEdate,None,None,("efld",)),
            (("T",0,2,0),"IUA",1,"Location","",
                "","Y",self.doLoc,loc,None,("efld",)),
            (("T",0,3,0),"IUA",3,"Product Group","",
                "","Y",self.doGroup,grp,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Exclude Zeros","",
                "Y","Y",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSdate(self, frt, pag, r, c, p, i, w):
        self.sdate = w
        self.sdatd = self.df.t_disp[0][0][i]

    def doEdate(self, frt, pag, r, c, p, i, w):
        self.edate = w
        self.edatd = self.df.t_disp[0][0][i]

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.loc = w
        if not w:
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]),
                ("srl_loc", "=", w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.locd = acc[0]

    def doGroup(self, frt, pag, r, c, p, i, w):
        if not w:
            self.group = ""
        else:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]),
                ("gpm_group", "=", w)], limit=1)
            if not acc:
                return "Invalid Group"
            self.group = w

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.group:
            self.sgrp = ""
            self.egrp = "zzz"
        else:
            self.sgrp = self.group
            self.egrp = self.group
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", ">=", self.sgrp),
            ("st1_group", "<=", self.egrp), ("st1_type", "=", "N")],
            order="st1_group, st1_code")
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
        self.expheads = ["%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm), "Stock Movement Report "\
            "as at %s for Period %s to %s" % (self.sysdtd, self.sdatd,
            self.edatd)]
        self.expcolsh = [["", "", "", "", ["*** Opening Balances ***", 4, 5],
            ["******* Receipts *******", 6, 7], ["******** Issues ********",
            8, 9], ["*** Closing Balances ***", 10, 11]], ["Grp",
            "Product-Code", "Description", "U.O.I", "Quantity", "Value",
            "Quantity", "Value", "Quantity", "Value", "Quantity", "Value"]]
        self.expforms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10),
            ("SD", 12,2), ("SD", 12.2), ("SD", 12.2), ("SD", 12.2),
            ("SD", 12,2), ("SD", 12.2), ("SD", 12.2), ("SD", 12.2)]
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            self.expdatas.append(["BODY", [vals[0].work, vals[1].work,
                vals[2].work, vals[3].work, vals[4].work, vals[5].work,
                vals[6].work, vals[7].work, vals[8].work, vals[9].work,
                vals[10].work, vals[11].work]])
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-161s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        old_grp = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            grp, code, desc, uoi, t0, t1, t2, t3, t4, t5, t6, t7 = vals
            if old_grp and old_grp != grp.work:
                self.groupTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s" % \
                (code.disp, desc.disp, uoi.disp, t0.disp, t1.disp,
                t2.disp, t3.disp, t4.disp, t5.disp, t6.disp, t7.disp))
            self.pglin += 1
            old_grp = grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.groupTotal()
            self.grandTotal()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def getValues(self, data):
        grp = CCD(data[0], "UA", 3)
        self.groupd = grp.disp
        code = CCD(data[1], "NA", 20)
        desc = CCD(data[2], "NA", 30)
        uoi = CCD(data[3], "NA", 10)
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"], self.edate,
            keys=(grp.work, code.work, self.loc))
        figs = [0] * 8
        m_ob,m_mv,m_cb,y_ob,y_mv,y_cb,ac,lc, ls = bals.doStrBals(self.sdate)
        figs[0] = y_ob[0]
        figs[1] = y_ob[1]
        for bal in y_mv:
            if bal[0] in (1, 3, 5):
                figs[2] = float(ASD(figs[2]) + ASD(bal[1]))
                figs[3] = float(ASD(figs[3]) + ASD(bal[2]))
            else:
                figs[4] = float(ASD(figs[4]) - ASD(bal[1]))
                figs[5] = float(ASD(figs[5]) - ASD(bal[2]))
        figs[6] = y_cb[0]
        figs[7] = y_cb[1]
        t = [grp, code, desc, uoi]
        for y in range(8):
            t.append(CCD(figs[y], "SD", 12.2))
            self.stot[y] = float(ASD(self.stot[y]) + ASD(t[y+4].work))
            self.gtot[y] = float(ASD(self.gtot[y]) + ASD(t[y+4].work))
        if self.zero == "Y" and not t[4].work and not t[5].work and \
                not t[6].work and not t[7].work and not t[8].work and \
                not t[9].work and not t[10].work and not t[11].work:
            return
        return t

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("Stock Movement Report as at %s for Period "\
            "%s to %s" % (self.sysdtd, self.sdatd, self.edatd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-5s %3s      %-8s %s  %s" % \
            ("Group", self.groupd, "Location", self.loc, self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-62s %24s  %24s  %24s  %24s" % ("",
            "*** Opening Balances ***", "******* Receipts *******",
            "******** Issues ********", "*** Closing Balances ***"))
        self.fpdf.drawText("%-20s %-30s %-10s %11s  %11s  %11s  %11s  %11s  " \
            "%11s  %11s  %11s " % ("Product-Code", "Description", "U.O.I",
            "Quantity", "Value", "Quantity", "Value",
            "Quantity", "Value", "Quantity", "Value"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 11

    def groupTotal(self):
        t = []
        for x in range(8):
            t.append(CCD(self.stot[x], "SD", 12.2))
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-41s %12s %12s %12s %12s %12s %12s %12s " \
            "%12s" % (" ", "Group Totals", t[0].disp, t[1].disp, t[2].disp,
            t[3].disp, t[4].disp, t[5].disp, t[6].disp, t[7].disp))
        self.stot = [0] * 8

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            gtot = ["TOTAL", ["", "", "Grand Totals", ""]]
            gtot[1].extend(self.gtot)
            self.expdatas.append(gtot)
            self.expdatas.append(["ULINED"])
            return
        t = []
        for x in range(8):
            t.append(CCD(self.gtot[x], "SD", 12.2))
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-41s %12s %12s %12s %12s %12s %12s %12s " \
            "%12s" % (" ", "Grand Totals", t[0].disp, t[1].disp, t[2].disp,
            t[3].disp, t[4].disp, t[5].disp, t[6].disp, t[7].disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
