"""
SYNOPSIS
    Value Added Tax Report.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, getVatRate
from tartanFunctions import showError, mthendDate

class ms3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        if not ctlmst["ctm_taxno"]:
            showError(self.opts["mf"].body, "Unregistered",
                "The Company Record Does Not Have a V.A.T. Number")
            return
        self.genleg = False
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            if ctlmst["ctm_modules"][x:x+2] == "GL":
                self.genleg = True
                break
        if self.genleg:
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            self.convat = ctlctl["vat_ctl"]
        tab = ["ctlvmf", "ctlvtf"]
        if self.genleg:
            tab.extend(["ctlynd", "genbal", "gentrn"])
        self.sql = Sql(self.opts["mf"].dbm, tables=tab,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.head = ("%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            "%s"))
        self.colsh = ["C", "T", "Curr-Dt", "S", "TT", "Acc-Num", "Reference",
            "Date", "Remarks", "Rate-%", "Input-Value", "Input-Tax ",
            "Output-Value", "Output-Tax"]
        self.forms = [("UA", 2), ("UA", 2), ("D2", 7), ("UA", 2),
            ("UI", 2, False, False, True), ("NA", 7), ("Na", 9),
            ("D1", 10), ("NA", 30), ("UD", 6.2), ("SD", 13.2),
            ("SD", 13.2), ("SD", 13.2), ("SD",13.2)]
        self.ctopv = 0
        self.ctopt = 0
        self.ctipv = 0
        self.ctipt = 0
        self.ttopv = {}
        self.ttopt = {}
        self.ttipv = {}
        self.ttipt = {}
        self.gtopv = 0
        self.gtopt = 0
        self.gtipv = 0
        self.gtipt = 0
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "V.A.T. Statement (%s)" % self.__class__.__name__)
        self.cats = [
            ["A", "All"],
            ["B", "All Except (N)one"],
            ["S", "Standard"],
            ["Z", "Zero Rated"],
            ["C", "Capital Item"],
            ["X", "Excluded Item"],
            ["N", "None"]]
        vtc = {
            "stype": "C",
            "titl": "VAT Types",
            "head": ("C", "Description"),
            "data": self.cats}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y"),
                ("vtm_cat",  "", 0, "C")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        sys = {
            "stype": "C",
            "titl": "Systems",
            "head": ("S", "Description"),
            "data": (
                ("", "All Systems"),
                ("A", "Asset's Register"),
                ("B", "Booking's Manager"),
                ("C", "Creditor's Ledger"),
                ("D", "Debtor's Ledger"),
                ("G", "General Ledger"),
                ("M", "Member's Ledger"),
                ("R", "Rental's Ledger"))}
        pdt = {
            "stype": "R",
            "titl": "Payment Date",
            "head": ("Date",),
            "tables": ("ctlvtf",),
            "cols": (("vtt_paid", "", 0, "Date-Paid"),),
            "where": [],
            "group": "vtt_paid",
            "order": "vtt_paid"}
        r1s = (("Yes", "Y"), ("No", "N"))
        r2s = (("Yes", "Y"), ("No", "N"), ("Reprint", "R"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                "","Y",self.doStartPeriod,None,None,("efld",),None,
                "Enter 0 to include All Periods which contain Unpaid Items"),
            (("T",0,1,0),"ID2",7,"Ending Period","",
                "","Y",self.doEndPeriod,None,None,("efld",)),
            (("T",0,2,0),"IUA",1,"Vat Category","",
                "B","Y",self.doCat,vtc,None,("efld",)),
            (("T",0,3,0),"IUA",1,"Vat Code","",
                "","Y",self.doCode,vtm,None,("efld",)),
            (("T",0,4,0),"IUA",1,"System","Originating System",
                "","Y",self.doSystem,sys,None,None),
            (("T",0,5,0),("IRB",r1s),0,"Totals Only","",
                "Y","Y",self.doTotsOnly,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"Flag Items as Paid",
                "Flag Items as Paid","N","Y",self.doFlagPaid,None,None,None),
            (("T",0,7,0),"Id1",10,"Payment Date","",
                "","Y",self.doPayDate,pdt,None,("notzero",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doStartPeriod(self, frt, pag, r, c, p, i, w):
        self.sper = w
        self.sperd = self.df.t_disp[pag][r][p]

    def doEndPeriod(self, frt, pag, r, c, p, i, w):
        self.eper = w
        self.eperd = self.df.t_disp[pag][r][p]
        if not self.genleg:
            return
        chk = self.sql.getRec("ctlynd", cols=["cye_start", "cye_end"],
            where=[("cye_cono", "=", self.opts["conum"])])
        self.start = 0
        for ck in chk:
            if self.eper >= int(ck[0] / 100) and int(self.eper <= ck[1] / 100):
                self.start = ck[0]
        if not self.start:
            return "Invalid Ending Period"

    def doCat(self, frt, pag, r, c, p, i, w):
        if w and w not in ("A", "B", "N","S","Z","C","X"):
            return "Invalid V.A.T Category"
        if not w:
            self.cat = "A"
        else:
            self.cat = w
        if not self.cat:
            self.code = ""
            return "sk1"

    def doCode(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
                where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
                w)], limit=1)
            if not acc:
                return "Invalid V.A.T Code"
        self.code = w

    def doSystem(self, frt, pag, r, c, p, i, w):
        self.system = w

    def doTotsOnly(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if self.totsonly == "Y":
            self.df.setWidget(self.df.topEntry[0][8][3][0], state="hide")
            self.df.setWidget(self.df.topEntry[0][8][4][0], state="hide")
        else:
            self.df.setWidget(self.df.topEntry[0][8][3][0], state="show")
            self.df.setWidget(self.df.topEntry[0][8][4][0], state="show")
        if self.sper or self.cat not in ("A", "B") or self.code or \
                                self.system or self.totsonly == "Y":
            self.flag = "N"
            return "sk2"

    def doFlagPaid(self, frt, pag, r, c, p, i, w):
        self.flag = w
        if self.flag == "N":
            self.paid = 0
            return "sk1"
        self.df.topf[pag][7][8]["where"] = [("vtt_cono", "=",
            self.opts["conum"]), ("vtt_paid", ">=", mthendDate(self.eper*100))]

    def doPayDate(self, frt, pag, r, c, p, i, w):
        self.paid = w
        self.paidd = self.df.t_disp[pag][r][p]

    def doEnd(self):
        self.df.closeProcess()
        vtm = [("vtm_cono", "=", self.opts["conum"])]
        if self.cat == "B":
            vtm.append(("vtm_cat", "<>", "N"))
        elif self.cat != "A":
            vtm.append(("vtm_cat", "=", self.cat))
        if self.code:
            vtm.append(("vtm_code", "=", self.code))
        odr = "vtm_cat, vtm_code"
        recs = self.sql.getRec("ctlvmf", where=vtm, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Records Selected")
        else:
            if self.df.repprt[2] == "export":
                self.exportReport(recs)
            else:
                self.printReport(recs)
            if self.flag == "Y":
                self.sql.updRec("ctlvtf", cols=["vtt_paid"], data=[self.paid],
                    where=[("vtt_cono", "=", self.opts["conum"]), ("vtt_curdt",
                    "<=", self.eper), ("vtt_paid", "=", 0)])
                self.opts["mf"].dbm.commitDbase()
        self.closeProcess()

    def exportReport(self, recs):
        p1 = ProgressBar(self.opts["mf"].body, mxs=len(recs),
            typ="VAT Categories")
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("VAT Statement for Period %s to %s" % \
            (self.sperd, self.eperd))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        self.pcat = None
        self.pcode = None
        for n1, dat1 in enumerate(recs):
            p1.displayProgress(n1)
            vals = self.getValues1(dat1)
            if not vals:
                continue
            code, self.pdesc, cat, vtf = vals
            if not self.pcat:
                self.pcat = cat
                self.expdatas.append(["PAGE", [self.expheads, self.expcolsh,
                    self.expforms, "Category %s" % cat]])
            if not self.pcode:
                self.pcode = code
            if cat != self.pcat:
                self.doPrintCodeTotal(ttype="X")
                self.doPrintCatTotal(ttype="X")
                self.pcat = cat
                self.pcode = code
                self.expdatas.append(["PAGE", [self.expheads, self.expcolsh,
                    self.expforms, "Category %s" % cat]])
            if code != self.pcode:
                self.doPrintCodeTotal(ttype="X")
                self.pcode = code
            p2 = ProgressBar(self.opts["mf"].body, mxs=len(vtf), inn=p1,
                typ="Category Transactions")
            for n2, dat2 in enumerate(vtf):
                p2.displayProgress(n2)
                vtyp, curdt,styp, ttyp, acno, refno, refdt, desc, exc, \
                    vtr, tax, inc = self.getValues2(dat2)
                line = ["BODY", [self.pcode, vtyp.work, curdt.work, styp.work,
                    ttyp.work, acno.work, refno.work, refdt.work, desc.work,
                    vtr.work]]
                if vtyp.work == "I":
                    line[1].extend([inc.work, tax.work, 0, 0])
                    self.ctipv = float(ASD(self.ctipv) + ASD(inc.work))
                    self.ctipt = float(ASD(self.ctipt) + ASD(tax.work))
                    self.ttipv[self.pcat][vtr.disp] = \
                        float(ASD(self.ttipv[self.pcat][vtr.disp]) + \
                        ASD(inc.work))
                    self.ttipt[self.pcat][vtr.disp] = \
                        float(ASD(self.ttipt[self.pcat][vtr.disp]) + \
                        ASD(tax.work))
                    self.gtipv = float(ASD(self.gtipv) + ASD(inc.work))
                    self.gtipt = float(ASD(self.gtipt) + ASD(tax.work))
                else:
                    line[1].extend([0, 0, inc.work, tax.work])
                    self.ctopv = float(ASD(self.ctopv) + ASD(inc.work))
                    self.ctopt = float(ASD(self.ctopt) + ASD(tax.work))
                    self.ttopv[self.pcat][vtr.disp] = \
                        float(ASD(self.ttopv[self.pcat][vtr.disp]) + \
                        ASD(inc.work))
                    self.ttopt[self.pcat][vtr.disp] = \
                        float(ASD(self.ttopt[self.pcat][vtr.disp]) + \
                        ASD(tax.work))
                    self.gtopv = float(ASD(self.gtopv) + ASD(inc.work))
                    self.gtopt = float(ASD(self.gtopt) + ASD(tax.work))
                self.expdatas.append(line)
            p2.closeProgress()
        p1.closeProgress()
        if not self.expdatas:
            return
        self.doPrintCodeTotal(ttype="X")
        self.doPrintCatTotal(ttype="X", page=False)
        if self.cat in ("A", "B"):
            self.doPrintSummary(ttype="X")
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p1 = ProgressBar(self.opts["mf"].body, mxs=len(recs),
            typ="VAT Categories")
        self.head = ("%03u %-30s %30s %18s %27s %6s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm, "", self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        self.pcat = None
        self.pcode = None
        for n1, dat1 in enumerate(recs):
            p1.displayProgress(n1)
            vals = self.getValues1(dat1)
            if not vals:
                continue
            code, self.pdesc, cat, vtf = vals
            if not self.pcat:
                self.pcat = cat
            if not self.pcode:
                self.pcode = code
            if cat != self.pcat:
                if (self.pglin + 5) > self.fpdf.lpp:
                    self.doPrintHeading("A")
                    self.doPrintCodeTotal(ttype="P", line=False)
                else:
                    self.doPrintCodeTotal()
                self.doPrintCatTotal()
                self.pcat = cat
                self.pcode = code
                self.doPrintHeading("A")
            if code != self.pcode:
                if (self.pglin + 2) > self.fpdf.lpp:
                    self.doPrintHeading("A")
                    self.doPrintCodeTotal(ttype="P", line=False)
                else:
                    self.doPrintCodeTotal()
                self.pcode = code
                if self.totsonly == "N":
                    self.doPrintHeading("C")
            p2 = ProgressBar(self.opts["mf"].body, mxs=len(vtf), inn=p1,
                typ="Category Transactions")
            for n2, dat2 in enumerate(vtf):
                p2.displayProgress(n2)
                vtyp, curdt,styp, ttyp, acno, refno, refdt, desc, exc, \
                    vtr, tax, inc = self.getValues2(dat2)
                if self.pglin > self.fpdf.lpp:
                    self.doPrintHeading("A")
                if vtyp.work == "I":
                    if self.totsonly != "Y":
                        self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s "\
                            "%-13s %-13s" % (curdt.disp, styp.disp, ttyp.disp,
                            acno.disp, refno.disp, refdt.disp, desc.disp,
                            vtr.disp, inc.disp, tax.disp, " ", " "))
                        self.pglin += 1
                    self.ctipv = float(ASD(self.ctipv) + ASD(inc.work))
                    self.ctipt = float(ASD(self.ctipt) + ASD(tax.work))
                    self.ttipv[self.pcat][vtr.disp] = \
                        float(ASD(self.ttipv[self.pcat][vtr.disp]) + \
                        ASD(inc.work))
                    self.ttipt[self.pcat][vtr.disp] = \
                        float(ASD(self.ttipt[self.pcat][vtr.disp]) + \
                        ASD(tax.work))
                    self.gtipv = float(ASD(self.gtipv) + ASD(inc.work))
                    self.gtipt = float(ASD(self.gtipt) + ASD(tax.work))
                elif vtyp.work == "O":
                    if self.totsonly != "Y":
                        self.fpdf.drawText("%s %s %s %s %s %s %s %s %-13s "\
                            "%-13s %s %s" % (curdt.disp, styp.disp, ttyp.disp,
                            acno.disp, refno.disp, refdt.disp, desc.disp,
                            vtr.disp, " ", " ", inc.disp, tax.disp))
                        self.pglin += 1
                    self.ctopv = float(ASD(self.ctopv) + ASD(inc.work))
                    self.ctopt = float(ASD(self.ctopt) + ASD(tax.work))
                    self.ttopv[self.pcat][vtr.disp] = \
                        float(ASD(self.ttopv[self.pcat][vtr.disp]) + \
                        ASD(inc.work))
                    self.ttopt[self.pcat][vtr.disp] = \
                        float(ASD(self.ttopt[self.pcat][vtr.disp]) + \
                        ASD(tax.work))
                    self.gtopv = float(ASD(self.gtopv) + ASD(inc.work))
                    self.gtopt = float(ASD(self.gtopt) + ASD(tax.work))
            p2.closeProgress()
        p1.closeProgress()
        if self.fpdf.page:
            if (self.pglin + 5) > self.fpdf.lpp:
                self.doPrintHeading("A")
                self.doPrintCodeTotal(ttype="P", line=False)
            else:
                self.doPrintCodeTotal()
            self.doPrintCatTotal()
            if self.cat in ("A", "B"):
                self.doPrintHeading("S")
                self.doPrintSummary()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                repeml=self.df.repeml)

    def getValues1(self, data):
        code = data[self.sql.ctlvmf_col.index("vtm_code")]
        pdesc = data[self.sql.ctlvmf_col.index("vtm_desc")]
        cat = data[self.sql.ctlvmf_col.index("vtm_cat")]
        vtt = [("vtt_cono", "=", self.opts["conum"]), ("vtt_code", "=", code)]
        if self.sper:
            vtt.append(("vtt_curdt", ">=", self.sper))
        if self.eper:
            vtt.append(("vtt_curdt", "<=", self.eper))
        if self.system:
            vtt.append(("vtt_styp", "=", self.system))
        if self.flag == "R":
            vtt.append(("vtt_paid", "=", self.paid))
        else:
            vtt.append(("vtt_paid", "=", 0))
        vtf = self.sql.getRec("ctlvtf", where=vtt,
            order="vtt_styp, vtt_ttyp, vtt_refdt, vtt_refno")
        if not vtf:
            return
        return (code, pdesc, cat, vtf)

    def getValues2(self, data):
        vtyp = CCD(data[self.sql.ctlvtf_col.index("vtt_vtyp")],"UA",1)
        curdt = CCD(data[self.sql.ctlvtf_col.index("vtt_curdt")],"D2",7)
        styp = CCD(data[self.sql.ctlvtf_col.index("vtt_styp")],"UA",1)
        ttyp = CCD(data[self.sql.ctlvtf_col.index("vtt_ttyp")],"UI",2)
        acno = CCD(data[self.sql.ctlvtf_col.index("vtt_acno")],"NA",7)
        refno = CCD(data[self.sql.ctlvtf_col.index("vtt_refno")],"Na",9)
        refdt = CCD(data[self.sql.ctlvtf_col.index("vtt_refdt")],"D1",10)
        desc = CCD(data[self.sql.ctlvtf_col.index("vtt_desc")],"NA",30)
        exc = CCD(data[self.sql.ctlvtf_col.index("vtt_exc")],"SD",13.2)
        vtr = getVatRate(self.sql, self.opts["conum"], self.pcode, refdt.work)
        vtr = CCD(vtr, "UD", 6.2)
        for cat in ("C", "N", "S", "X", "Z"):
            if cat not in self.ttopv:
                self.ttopv[cat] = {}
                self.ttopt[cat] = {}
                self.ttipv[cat] = {}
                self.ttipt[cat] = {}
            if vtr.disp not in self.ttopv[cat]:
                self.ttopv[cat][vtr.disp] = 0
                self.ttopt[cat][vtr.disp] = 0
                self.ttipv[cat][vtr.disp] = 0
                self.ttipt[cat][vtr.disp] = 0
        tax = CCD(data[self.sql.ctlvtf_col.index("vtt_tax")],"SD",13.2)
        inc = CCD((exc.work + tax.work), "SD", 13.2)
        return (vtyp, curdt,styp, ttyp, acno, refno, refdt, desc, exc, vtr,
                tax, inc)

    def doPrintHeading(self, htype):
        if htype in ("A", "C"):
            for c in self.cats:
                if c[0] == self.pcat:
                    desc = c[1]
                    break
        if htype in ("A", "S"):
            self.fpdf.add_page()
            self.fpdf.setFont(style="B")
            self.pgnum += 1
            self.fpdf.drawText(self.head)
            self.fpdf.drawText()
            if self.flag == "Y":
                flag = "(Transactions Flagged on %s)" % self.paidd
            elif self.flag == "N":
                flag = "(Transactions Not Flagged)"
            elif self.flag == "R":
                flag = "(Transactions Paid on %s)" % self.paidd
            self.fpdf.drawText("%-24s %-7s %-2s %-7s %-79s %4s %5s" % \
                ("VAT Statement for Period",
                self.sperd, "to", self.eperd, flag, "Page", self.pgnum))
            self.fpdf.drawText()
            if htype == "A":
                if self.totsonly != "Y":
                    self.fpdf.drawText("Category: %1s %s Code: %s %s" % \
                        (self.pcat, desc, self.pcode, self.pdesc))
                else:
                    self.fpdf.drawText("Category: %1s %s - Totals Only" % \
                        (self.pcat, desc))
                self.pglin = 6
            else:
                self.fpdf.drawText("V.A.T. Summary")
                self.pglin = 5
        elif htype == "C":
            self.fpdf.setFont(style="B")
            self.fpdf.drawText()
            self.fpdf.drawText("Category: %1s %s - Code: %s %s" % \
                (self.pcat, desc, self.pcode, self.pdesc))
            self.pglin += 2
        self.fpdf.drawText()
        if htype == "S":
            self.fpdf.drawText("%-30s %6s %13s %13s %13s %13s" % ("Category",
                "Rate-%", "Input-Value ", "Input-Tax ", "Output-Value ",
                " Output-Tax "))
        else:
            self.fpdf.drawText("%-7s %-1s %-2s %-7s %-9s %-10s %-30s %6s "\
                "%13s %13s %13s %13s" % ("Curr-Dt", "S", "TT", "Acc-Num",
                "Reference", "   Date", "Remarks", "Rate-%", "Input-Value ",
                "Input-Tax ", "Output-Value ", " Output-Tax "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 3

    def doPrintCodeTotal(self, ttype="P", line=True):
        j = CCD(self.ctipv, "SD", 13.2)
        k = CCD(self.ctipt, "SD", 13.2)
        l = CCD(self.ctopv, "SD", 13.2)
        m = CCD(self.ctopt, "SD", 13.2)
        if ttype == "P":
            if self.totsonly != "Y" and line:
                self.fpdf.drawText("%-125s" % (self.fpdf.suc * len(self.head)))
            self.fpdf.drawText("%-41s %-14s %-22s %-13s %-13s %-13s %-13s" %
                ("", "Code-Total", self.pcode, j.disp, k.disp, l.disp, m.disp))
        else:
            self.expdatas.append(["ULINES"])
            desc = "Code-Total %s" % self.pcode
            line = ["TOTAL", ["", "", "", "", "", "", "", "", desc, "",
                j.work, k.work, l.work, m.work]]
            self.expdatas.append(line)
        self.ctipv = 0
        self.ctipt = 0
        self.ctopv = 0
        self.ctopt = 0

    def doPrintCatTotal(self, ttype="P", page=True):
        rates = list(self.ttipv[self.pcat].keys())
        rates.sort()
        for num, rte in enumerate(rates):
            j = CCD(self.ttipv[self.pcat][rte], "SD", 13.2)
            k = CCD(self.ttipt[self.pcat][rte], "SD", 13.2)
            l = CCD(self.ttopv[self.pcat][rte], "SD", 13.2)
            m = CCD(self.ttopt[self.pcat][rte], "SD", 13.2)
            if not j.work and not k.work and not l.work and not m.work:
                continue
            if ttype == "P":
                if not num:
                    self.fpdf.drawText("%-125s" % (
                        self.fpdf.suc * len(self.head)))
                self.fpdf.drawText("%-41s %-14s %-15s %-6s "\
                    "%-13s %-13s %-13s %-13s" % ("", "Category-Total",
                    self.pcat, rte, j.disp, k.disp, l.disp, m.disp))
            else:
                if not num:
                    self.expdatas.append(["ULINES"])
                desc = "Category-Total %s" % self.pcat
                line = ["TOTAL", ["", "", "", "", "", "", "", "", desc, rte,
                    j.work, k.work, l.work, m.work]]
                self.expdatas.append(line)

    def doPrintSummary(self, ttype="P"):
        if ttype == "X":
            expheads = [self.head % self.sysdttm]
            expheads.append("VAT Summary for Period %s to %s" % \
                (self.sperd, self.eperd))
            expcolsh = [self.colsh[8:]]

            expcolsh[0][0] = "Category"
            expforms = self.expforms[8:]
            self.expdatas.append(["PAGE", [expheads, expcolsh, expforms,
                "Summary"]])
        tots = [0, 0, 0, 0]
        for c in self.cats:
            if c[0] in ("A", "B"):
                continue
            if self.cat == "B" and c[0] == "N":
                continue
            rates = list(self.ttipv[c[0]].keys())
            rates.sort()
            desc = True
            for rte in rates:
                j = CCD(self.ttipv[c[0]][rte], "SD", 13.2)
                tots[0] = float(ASD(tots[0]) + ASD(j.work))
                k = CCD(self.ttipt[c[0]][rte], "SD", 13.2)
                tots[1] = float(ASD(tots[1]) + ASD(k.work))
                l = CCD(self.ttopv[c[0]][rte], "SD", 13.2)
                tots[2] = float(ASD(tots[2]) + ASD(l.work))
                m = CCD(self.ttopt[c[0]][rte], "SD", 13.2)
                tots[3] = float(ASD(tots[3]) + ASD(m.work))
                if not j.work and not k.work and not l.work and not m.work:
                    continue
                if desc:
                    desc = False
                    d = CCD(c[1], "NA", 30)
                else:
                    d = CCD("", "NA", 30)
                if ttype == "P":
                    self.fpdf.drawText("%s %s %s %s %s %s" % (d.disp, rte,
                        j.disp, k.disp, l.disp, m.disp))
                else:
                    line = ["BODY", [d.disp, rte, j.work, k.work, l.work,
                        m.work]]
                    self.expdatas.append(line)
        if ttype == "P":
            self.fpdf.drawText("%-125s" % (self.fpdf.suc * len(self.head)))
        else:
            self.expdatas.append(["ULINES"])
        d = CCD("Grand Total", "NA", 30)
        j = CCD(tots[0], "SD", 13.2)
        k = CCD(tots[1], "SD", 13.2)
        l = CCD(tots[2], "SD", 13.2)
        m = CCD(tots[3], "SD", 13.2)
        tvat = CCD(float(ASD(tots[1]) + ASD(tots[3])), "SD", 13.2)
        if ttype == "P":
            self.fpdf.drawText("%-37s %s %s %s %s" % (d.disp, j.disp, k.disp,
                l.disp, m.disp), font="B")
            self.fpdf.drawText()
            self.fpdf.drawText("%-79s %13s" % ("Total Net Tax Due/Owed",
                tvat.disp), font="B")
        else:
            line = ["TOTAL", [d.disp, "", j.work, k.work, l.work, m.work]]
            self.expdatas.append(line)
            self.expdatas.append(["BLANK"])
            line = ["TOTAL", ["Total Net Tax Due/Owed", "", "", "", "",
                tvat.work]]
            self.expdatas.append(line)
        if not self.genleg:
            return
        bal = 0.0
        o = self.sql.getRec("genbal", cols=["glo_cyr"],
            where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
            self.convat), ("glo_trdt", "=", self.start)], limit=1)
        if o:
            b = CCD(o[0], "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        bal = float(ASD(bal) + ASD(b.work))
        o = self.sql.getRec("gentrn",
            cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
            self.opts["conum"]), ("glt_acno", "=", self.convat), ("glt_curdt",
            ">=", int(self.start / 100)), ("glt_curdt", "<=", self.eper)],
            limit=1)
        if o and o[0]:
            b = CCD(float(o[0]), "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        tbal = CCD(float(ASD(bal) + ASD(b.work)), "SD", 13.2)
        if ttype == "P":
            self.fpdf.drawText()
            self.fpdf.drawText("%-79s %13s" % ("Balance of VAT Control",
                tbal.disp), font="B")
        else:
            self.expdatas.append(["BLANK"])
            line = ["TOTAL", ["Balance of VAT Control", "", "", "", "",
                tbal.work]]
            self.expdatas.append(line)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
