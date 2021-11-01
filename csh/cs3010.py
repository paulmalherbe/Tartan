"""
SYNOPSIS
    Cash Reconciliation Report.

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

from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter

class cs3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        cshctl = gc.getCtl("cshctl", self.opts["conum"])
        if not cshctl:
            return
        self.glint = cshctl["ccc_glint"]
        self.fromad = cshctl["ccc_emadd"]
        if self.glint == "Y":
            tabs = ["genmst"]
        else:
            tabs = ["cshmst"]
        tabs.extend(["cshcnt", "cshana"])
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.dte = self.sql.getRec("cshcnt", cols=["max(cct_date)"],
            where=[("cct_cono", "=", self.opts["conum"])], limit=1)[0]
        self.denoms = (
            ("R200", 200),
            ("R100", 100),
            ("R50", 50),
            ("R20", 20),
            ("R10", 10),
            ("R5", 5),
            ("R2", 2),
            ("R1", 1),
            ("C50", .5),
            ("C20", .2),
            ("C10", .1),
            ("C5", .05),
            ("C2", .02),
            ("C1", .01))
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Cash Reconciliation Report (%s)" % self.__class__.__name__)
        dte = {
            "stype": "R",
            "tables": ("cshcnt",),
            "cols": (
                ("cct_date", "", 0, "Date"),),
            "where": [("cct_cono", "=", self.opts["conum"])],
            "group": "cct_date"}
        fld = (
            (("T",0,0,0),"ID1",10,"From Date","",
                self.dte,"Y",self.doFrom,dte,None,("efld",)),
            (("T",0,1,0),"Id1",10,"To   Date","To Date",
                "","Y",self.doTo,dte,None,("efld",)),
            (("T",0,2,0),"ISD",13.2,"Float","Cash Float",
                2000,"Y",self.doFloat,None,None,("notzero",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail = ("Y","N"))

    def doFrom(self, frt, pag, r, c, p, i, w):
        self.fm = w
        self.fmd = self.df.t_disp[pag][r][p]
        self.df.loadEntry(frt, pag, p+1, data=self.fm)

    def doTo(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.fm
        elif w < self.fm:
            return "Invalid To Date"
        self.to = w
        self.tod = CCD(w, "D1", 10).disp
        csh = self.sql.getRec("cshcnt", where=[("cct_cono", "=",
            self.opts["conum"]), ("cct_type", "=", "T"), ("cct_date",
            "between", self.fm, self.to)])
        if not csh:
            return "ff1|Invalid Cash Capture Dates"

    def doFloat(self, frt, pag, r, c, p, i, w):
        self.float = CCD(w, "SD", 13.2)

    def doEnd(self):
        self.df.closeProcess()
        self.tk1 = self.sql.getRec("cshana", where=[("can_cono", "=",
            self.opts["conum"]), ("can_type", "=", "P"), ("can_date",
            "between", self.fm, self.to)], order="can_trdt, can_code")
        self.tk2 = self.sql.getRec("cshana", where=[("can_cono", "=",
            self.opts["conum"]), ("can_type", "=", "T"), ("can_date",
            "between", self.fm, self.to)], order="can_trdt, can_code")
        self.head = "%03u %-78s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        if self.tk1:
            self.pageHeading()
            self.printExpTak(self.tk1, 1)
        if not self.quit:
            if self.tk2:
                self.pageHeading()
                self.printExpTak(self.tk2, 2)
            if not self.quit:
                self.doSummary()
        if not self.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def printExpTak(self, recs, ptyp=None):
        self.fpdf.setFont(style="B")
        if ptyp == 1:
            self.fpdf.drawText("Cash Expenditure")
        else:
            self.fpdf.drawText("Cash Takings")
        self.fpdf.drawText()
        self.fpdf.drawText("%-10s %-36s %7s %13s %13s" % ("  Date",
            "Description", "Code", "Vat-Amount ", "Inc-Amount "))
        self.fpdf.underLine(txt=self.head)
        self.pglin += 4
        self.fpdf.setFont()
        tot = 0
        vat = 0
        c1 = self.sql.cshana_col
        pb = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        for num, dat in enumerate(recs):
            pb.displayProgress(num)
            self.quit = pb.quit
            if self.quit:
                break
            trdt = CCD(dat[c1.index("can_trdt")], "D1", 10)
            code = CCD(dat[c1.index("can_code")], "UI", 7)
            desc = CCD(dat[c1.index("can_desc")], "NA", 36)
            inca = CCD(dat[c1.index("can_incamt")], "SD", 13.2)
            vata = CCD(dat[c1.index("can_vatamt")], "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s" % (trdt.disp, desc.disp,
                code.disp, vata.disp, inca.disp))
            self.pglin += 1
            tot = float(ASD(tot) + ASD(inca.work))
            vat = float(ASD(vat) + ASD(vata.work))
        pb.closeProgress()
        if self.quit:
            return
        tot = CCD(tot, "SD", 13.2)
        vat = CCD(vat, "SD", 13.2)
        self.fpdf.drawText("%55s %-12s  %-12s" % ("", self.fpdf.suc*12,
            self.fpdf.suc*12))
        if ptyp == 1:
            self.fpdf.drawText("%10s %-36s         %13s %13s" % ("",
                "Total Expenses", vat.disp, tot.disp))
        else:
            self.fpdf.drawText("%10s %-36s         %13s %13s" % ("",
                "Total Takings", vat.disp, tot.disp))
        self.fpdf.drawText()

    def doSummary(self):
        self.pageHeading()
        if self.glint == "Y":
            tab = ["cshana", "genmst"]
            col = ["can_code", "glm_desc", "sum(can_incamt)", "sum(can_vatamt)"]
            whr = [
                ("can_cono", "=", self.opts["conum"]),
                ("can_date", "between", self.fm, self.to),
                ("glm_cono=can_cono",),
                ("glm_acno=can_code",)]
            grp = "can_code, glm_desc"
        else:
            tab = ["cshana", "cshmst"]
            col = ["can_code", "ccm_desc", "sum(can_incamt)", "sum(can_vatamt)"]
            whr = [
                ("can_cono", "=", self.opts["conum"]),
                ("can_date", "between", self.fm, self.to),
                ("ccm_cono=can_cono",),
                ("ccm_acno=can_code",)]
            grp = "can_code, ccm_desc"
        w = whr[:]
        w.insert(2, ("can_type", "=", "P"))
        recs = self.sql.getRec(tables=tab, cols=col, where=w, group=grp,
            order="can_code")
        self.printSummary(recs, 1)
        w = whr[:]
        w.insert(2, ("can_type", "=", "T"))
        recs = self.sql.getRec(tables=tab, cols=col, where=w, group=grp,
            order="can_code")
        self.printSummary(recs, 2)

    def printSummary(self, recs, ptyp=None):
        self.fpdf.setFont(style="B")
        if ptyp == 1:
            self.fpdf.drawText("Expenses Summary")
        else:
            self.fpdf.drawText("Takings Summary")
        self.fpdf.drawText()
        self.fpdf.drawText("%7s %-61s %13s" % ("Code", "Description",
            "Amount "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4
        tot = 0
        vat = 0
        for rec in recs:
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            a = CCD(rec[2], "SD", 13.2)
            b = CCD(rec[3], "SD", 13.2)
            c = CCD(float(ASD(a.work) - ASD(b.work)), "SD", 13.2)
            tot = float(ASD(tot) + ASD(a.work))
            vat = float(ASD(vat) + ASD(b.work))
            self.fpdf.drawText("%7s %-61s %s" % (rec[0], rec[1], c.disp))
            self.pglin += 1
        vat = CCD(vat, "SD", 13.2)
        self.fpdf.drawText("%7s %-61s %s" % ("", "Value Added Tax", vat.disp))
        self.fpdf.drawText("%69s %-12s" % ("", self.fpdf.suc*12))
        if ptyp == 1:
            self.exp = CCD(tot, "SD", 13.2)
            self.fpdf.drawText("%7s %-61s %s" % ("", "Total", self.exp.disp))
        else:
            self.tak = CCD(tot, "SD", 13.2)
            self.fpdf.drawText("%7s %-61s %s" % ("", "Total", self.tak.disp))
        self.fpdf.drawText()
        self.fpdf.drawText()
        self.pglin += 5
        if ptyp == 1:
            return
        if (self.pglin + 30) > self.fpdf.lpp:
            self.pageHeading()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Cash Summary")
        self.fpdf.drawText()
        self.fpdf.drawText("%-26s %42s %13s" % ("Denomination", "Quantity",
            "Amount "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4
        col = ["sum(cct_cheq)", "sum(cct_r200)", "sum(cct_r100)",
            "sum(cct_r50)", "sum(cct_r20)", "sum(cct_r10)", "sum(cct_r5)",
            "sum(cct_r2)", "sum(cct_r1)", "sum(cct_c50)", "sum(cct_c20)",
            "sum(cct_c10)", "sum(cct_c5)", "sum(cct_c2)", "sum(cct_c1)"]
        recs = self.sql.getRec("cshcnt", cols=col, where=[("cct_cono",
            "=", self.opts["conum"]), ("cct_type", "=", "T"), ("cct_date",
            "between", self.fm, self.to)], limit=1)
        if recs and recs[0]:
            val = CCD(recs[0], "SD", 13.2)
            csh = val.work
            self.fpdf.drawText("%-26s %42s %s" % ("Cheques", "", val.disp))
            self.pglin += 1
        else:
            csh = 0
        for x in range(1, 15):
            if recs[x]:
                qty = CCD(recs[x], "UI", 5)
                val = CCD(qty.work * self.denoms[x-1][1], "SD", 13.2)
                csh = float(ASD(csh) + ASD(val.work))
                self.fpdf.drawText("%-26s %42s %s" % (self.denoms[x-1][0],
                    qty.disp, val.disp))
                self.pglin += 1
        self.fpdf.drawText("%69s %-12s" % ("", self.fpdf.suc*12))
        csh = CCD(csh, "SD", 13.2)
        self.fpdf.drawText("%-26s %42s %s" % ("Total", "", csh.disp))
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Cash Reconciliation")
        self.fpdf.setFont()
        self.fpdf.drawText()
        self.fpdf.drawText("%-26s %42s %s" % ("Total Takings", "",
            self.tak.disp))
        self.fpdf.drawText("%-26s %42s %s" % ("Total Expended", "",
            self.exp.disp))
        self.fpdf.drawText("%69s %-12s" % ("", self.fpdf.suc*12))
        dif = CCD(float(ASD(self.tak.work) - ASD(self.exp.work)), "SD", 13.2)
        self.fpdf.drawText("%-26s %42s %s" % ("Cash Expected", "", dif.disp))
        self.fpdf.drawText("%-26s %42s %s" % ("Cash Actual", "", csh.disp))
        self.fpdf.drawText("%69s %-12s" % ("", self.fpdf.suc*12))
        dif = CCD(float(ASD(dif.work) - ASD(csh.work)), "SD", 13.2)
        if dif.work:
            if dif.work < 0:
                text = "Cash Over"
                dif = CCD(float(ASD(0) - ASD(dif.work)), "SD", 13.2)
            else:
                text = "Cash Under"
            self.fpdf.drawText("%-26s %42s %s" % (text, "", dif.disp))

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-30s %10s to %-35s" % \
            ("Cash Reconciliation for Period", self.fmd, self.tod))
        self.fpdf.drawText()
        self.pglin = 4
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
