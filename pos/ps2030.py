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

import time
from TartanClasses import ASD, CCD, MyFpdf, Sql, TartanDialog
from tartanFunctions import askQuestion, getModName, doPrinter

class ps2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlpwu", "postrn", "poscnt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % (t[0],
            t[1], t[2], t[3], t[4])
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
            "Cash Declaration Report (%s)" % self.__class__.__name__)
        hst = {
            "stype": "R",
            "tables": ("postrn",),
            "cols": (
                ("pst_host", "", 0, "Terminal-Name"),),
            "where": [
                ("pst_cono", "=", self.opts["conum"])],
            "group": "pst_host"}
        usr = {
            "stype": "R",
            "tables": ("postrn", "ctlpwu"),
            "cols": (
                ("pst_capnm", "", 0, "Cashier"),
                ("usr_fnam", "", 0, "Full-Name")),
            "where": [
                ("pst_cono", "=", self.opts["conum"]),
                ("usr_name=pst_capnm",)],
            "whera": [
                ("T", "pst_host", 0, 0)],
            "group": "pst_capnm"}
        dte = {
            "stype": "R",
            "tables": ("poscnt",),
            "cols": (
                ("psc_date", "", 0, "Decln-Date"),
                ("psc_rec", "d1", 0, "Recon-Date")),
            "where": [
                ("psc_cono", "=", self.opts["conum"])],
            "whera": [
                ("T", "psc_host", 0, 0),
                ("T", "psc_user", 1, 0)],
            "group": "psc_date"}
        fld = (
            (("T",0,0,0),"ITX",15,"Terminal Name","",
                "","N",self.doHost,hst,None,("efld",)),
            (("T",0,1,0),"ITX",15,"Cashier Name","",
                "","N",self.doUser,usr,None,("efld",)),
            (("T",0,2,0),"Id1",10,"Declaration Date","",
                self.sysdtw,"N",self.doDate,dte,None,("efld",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        but = None
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, butt=but, view=("N","V"), mail=("Y","N"))

    def doHost(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("postrn", where=[("pst_cono",
            "=", self.opts["conum"]), ("pst_host", "=", w)], limit=1)
        if not acc:
            return "Invalid Terminal Name"
        self.host = w

    def doUser(self, frt, pag, r, c, p, i, w):
        usr = self.sql.getRec("postrn", where=[("pst_cono",
            "=", self.opts["conum"]), ("pst_host", "=", self.host),
            ("pst_capnm", "=", w)], limit=1)
        if not usr:
            return "Invalid Terminal Name"
        self.user = w
        usr = self.sql.getRec("ctlpwu", cols=["usr_fnam"],
            where=[("usr_name", "=", self.user)], limit=1)
        if usr[0]:
            self.name = usr[0]
        else:
            self.name = self.user

    def doDate(self, frt, pag, r, c, p, i, w):
        self.cnt = self.sql.getRec("poscnt", where=[("psc_cono",
            "=", self.opts["conum"]), ("psc_host", "=", self.host),
            ("psc_user", "=", self.user), ("psc_date", "=", w)])
        if not self.cnt:
            ok = askQuestion(self.opts["mf"].window, "Declaration",
                "This Has Not Yet Been Declared, Continue Anyway?",
                default="yes")
            if ok == "no":
                return "Invalid Declaration"
            self.decl = False
        else:
            self.decl = True
        self.datew = w
        self.dated = self.df.t_disp[pag][r][p]

    def doEnd(self):
        # Actual
        trn = self.sql.getRec("postrn", cols=["pst_dtype",
            "sum(pst_incl)"], where=[("pst_cono", "=", self.opts["conum"]),
            ("pst_host", "=", self.host), ("pst_dtype", "<>", "I"),
            ("pst_capnm", "=", self.user), ("pst_capdt", "=", self.datew)],
            group="pst_dtype")
        ccc0 = 0
        csh0 = 0
        vou0 = 0
        for t in trn:
            if t[0] == "C":
                ccc0 = t[1]
            elif t[0] == "T":
                csh0 = t[1]
            elif t[0] == "V":
                vou0 = t[1]
        # Declared
        if not self.decl:
            flo1 = 0
            vou1 = 0
            ccc1 = 0
            recon = 0
            csh1 = 0
        else:
            rec = self.sql.getRec("poscnt", where=[("psc_cono", "=",
                self.opts["conum"]), ("psc_host", "=", self.host), ("psc_user",
                "=", self.user), ("psc_date", "=", self.datew)], limit=1)
            rc = self.sql.poscnt_col
            flo1 = rec[rc.index("psc_float")]
            vou1 = rec[rc.index("psc_vou")]
            ccc1 = rec[rc.index("psc_ccc")]
            recon = rec[rc.index("psc_rec")]
            csh1 = float(ASD(0) - ASD(flo1))
            for x in range(7, 21):
                if rec[x]:
                    qty = rec[x]
                    val = qty * self.denoms[x-7][1]
                    csh1 = float(ASD(csh1) + ASD(val))
        # Differences
        vou0 = CCD(vou0, "SD", 13.2)
        vou1 = CCD(vou1, "SD", 13.2)
        ccc0 = CCD(ccc0, "SD", 13.2)
        ccc1 = CCD(ccc1, "SD", 13.2)
        csh0 = CCD(csh0, "SD", 13.2)
        csh1 = CCD(csh1, "SD", 13.2)
        voud = CCD(float(ASD(vou1.work) - ASD(vou0.work)), "SD", 13.2)
        cccd = CCD(float(ASD(ccc1.work) - ASD(ccc0.work)), "SD", 13.2)
        cshd = CCD(float(ASD(csh1.work) - ASD(csh0.work)), "SD", 13.2)
        tot1 = CCD(float(ASD(vou1.work) + ASD(ccc1.work) +
            ASD(csh1.work)), "SD", 13.2)
        tot2 = CCD(float(ASD(vou0.work) + ASD(ccc0.work) +
            ASD(csh0.work)), "SD", 13.2)
        tot3 = CCD(float(ASD(voud.work) + ASD(cccd.work) +
            ASD(cshd.work)), "SD", 13.2)
        # Draw Report
        head = ("%03u %-30s" % (self.opts["conum"], self.opts["conam"]))
        txt1 = "Cash Reconciliation for %s" % self.host
        txt2 = "Declared by %s (%s) on %s" % (self.name, self.user, self.dated)
        txt3 = "%34s %13s %13s" % ("Declared", "Actual ", "Difference ")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=len(txt3),
            foot=True)
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(head)
        self.fpdf.drawText()
        self.fpdf.drawText(txt1)
        self.fpdf.drawText()
        self.fpdf.drawText(txt2)
        self.fpdf.drawText()
        self.fpdf.drawText(txt3)
        self.fpdf.underLine(txt=txt3)
        self.fpdf.setFont()
        self.fpdf.drawText("%-20s %13s %13s %13s" % ("Voucher", vou1.disp,
            vou0.disp, voud.disp))
        self.fpdf.drawText("%-20s %13s %13s %13s" % ("C/Cards", ccc1.disp,
            ccc0.disp, cccd.disp))
        self.fpdf.drawText("%-20s %13s %13s %13s" % ("Cash", csh1.disp,
            csh0.disp, cshd.disp))
        self.fpdf.drawText("%20s %-13s %13s %13s" % ("", self.fpdf.suc*12,
            self.fpdf.suc*12, self.fpdf.suc*12))
        self.fpdf.drawText("%-20s %13s %13s %13s" % ("Totals", tot1.disp,
            tot2.disp, tot3.disp))
        self.fpdf.drawText("%20s %-13s %13s %13s" % ("", self.fpdf.suc*12,
            self.fpdf.suc*12, self.fpdf.suc*12))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
            pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
            repeml=self.df.repeml)
        if not recon and self.decl:
            ok = askQuestion(self.opts["mf"].window, "Verify",
                "Flag Cash Decalaration as Verified?", default="yes")
            if ok == "yes":
                self.sql.updRec("poscnt", cols=["psc_rec"], data=[self.sysdtw],
                    where=[("psc_cono", "=", self.opts["conum"]), ("psc_host",
                    "=", self.host), ("psc_user", "=", self.user), ("psc_date",
                    "=", self.datew)])
                self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
