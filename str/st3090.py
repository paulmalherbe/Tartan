"""
SYNOPSIS
    Stores Account Statements.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError
from tartanWork import sttrtp

class st3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strloc", "strgrp", "strmf1"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stock Account Statements (%s)" % self.__class__.__name__)
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
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", "", "", "N", "N"]
            view = ("N","V")
            mail = ("Y","N")
        fld = [
            (("T",0,0,0),"ID2",7,"Start Period","",
                int(self.sysdtw / 100),"Y",self.doSdate,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"End Period","",
                int(self.sysdtw / 100),"N",self.doEdate,None,None,("efld",)),
            [("T",0,2,0),"IUA",1,"Location","",
                var[2],"N",self.doLoc,loc,None,("efld",)],
            (("T",0,3,0),"IUA",3,"Product Group","",
                var[3],"N",self.doGroup,grp,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Include Recipes","",
                var[4],"N",self.doRecp,None,None,None),
            (("T",0,5,0),("IRB",r1s),0,"New Account on New Page","",
                var[5],"N",self.doPage,None,None,None)]
        if self.locs == "N":
            fld[2][1] = "OUA"
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doSdate(self, frt, pag, r, c, p, i, w):
        self.sdate = w

    def doEdate(self, frt, pag, r, c, p, i, w):
        self.edate = w
        if self.locs == "N":
            self.df.loadEntry(frt, pag, p+1, data="1")
            no = self.doLoc(frt, pag, r, c+1, p+1, i+1, "1")
            if no:
                return no
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        if not w:
            self.loc = ""
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.loc = w
            self.locd = acc[0]

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

    def doRecp(self, frt, pag, r, c, p, i, w):
        self.recp = w

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
        whr = [
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_group", ">=", self.sgrp),
            ("st1_group", "<=", self.egrp)]
        if self.recp == "N":
            whr.append(("st1_type", "=", "N"))
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc"], where=whr, order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-87s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        lstgrp = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            grp = CCD(dat[0], "UA", 3)
            cod = CCD(dat[1], "NA", 20)
            desc = CCD(dat[2], "UA", 30)
            bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
                self.edate, keys=(grp.work, cod.work, self.loc,
                ("P", self.opts["period"][0])))
            m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls, stt_rslt = \
                bals.doStrBals(self.sdate, trans="Y")
            self.qfwd = y_ob[0]
            self.vfwd = y_ob[1]
            trs = stt_rslt[0]
            dic = stt_rslt[1]
            if self.qfwd or self.vfwd or trs:
                if lstgrp and self.npag == "Y":
                    self.pageHeading(grp.disp, cod.disp, desc.disp)
                elif lstgrp or self.qfwd or self.vfwd:
                    self.accountHeading(grp.disp, cod.disp, desc.disp)
                lstgrp = grp.work
            if trs:
                for z in trs:
                    dt = CCD(z[dic["stt_trdt"][1]], "d1", 10)
                    qt = CCD(z[dic["stt_qty"][1]], "SD", 12.2)
                    cs = CCD(z[dic["stt_cost"][1]], "SD", 12.2)
                    bt = CCD(z[dic["stt_batch"][1]], "Na", 7)
                    r1 = CCD(z[dic["stt_ref1"][1]], "Na", 9)
                    r2 = CCD(z[dic["stt_ref1"][1]], "Na", 7)
                    tp = CCD(z[dic["stt_type"][1]], "UI", 1)
                    if self.pglin > (self.fpdf.lpp - 7):
                        self.pageHeading(grp.disp, cod.disp, desc.disp)
                    self.qfwd = float(ASD(self.qfwd) + ASD(qt.work))
                    self.vfwd = float(ASD(self.vfwd) + ASD(cs.work))
                    qb = CCD(self.qfwd, "SD", 12.2)
                    vb = CCD(self.vfwd, "SD", 12.2)
                    self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % \
                        (bt.disp, r1.disp, r2.disp, sttrtp[tp.work-1][0],
                        dt.disp, qt.disp, cs.disp, qb.disp, vb.disp))
                    self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self, grp, cod, desc):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-30s %-10s" % ("Stock Account "\
            "Statements as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-21s%-7s%-3s%-9s%-7s%-1s" % \
            ("(Options: Start Date-", self.df.t_disp[0][0][0], "",
                "End Date-", self.df.t_disp[0][0][1], ")"))
        self.fpdf.setFont()
        self.pglin = 5
        self.accountHeading(grp, cod, desc)

    def accountHeading(self, grp, cod, desc):
        if self.pglin > (self.fpdf.lpp - 10):
            self.pageHeading(grp, cod, desc)
        else:
            self.fpdf.setFont(style="B")
            self.fpdf.underLine(txt=self.head)
            self.fpdf.drawText("%-5s %3s      %-7s %s      %-8s %s  %s" %
                ("Group", grp, "Product", cod, "Location", self.loc,
                self.locd))
            self.fpdf.drawText()
            self.fpdf.drawText("%-7s %-9s %-7s %-3s %-10s %11s %12s %12s "\
                "%12s" % ("BatchNo", "Reference", "Refno-2", "Typ", "   Date",
                "Quantity", "Cost-Amt", "Qty-Balance", "Cst-Balance"))
            self.fpdf.underLine(txt=self.head)
            self.pglin += 5
            self.fpdf.setFont()
            if not self.qfwd and not self.vfwd:
                return
            qb = CCD(self.qfwd, "SD", 12.2)
            vb = CCD(self.vfwd, "SD", 12.2)
            self.fpdf.drawText("%-25s %-40s %s %s" %
                ("", "Fwd", qb.disp, vb.disp))
            self.pglin += 1

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
