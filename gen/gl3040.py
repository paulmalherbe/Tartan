"""
SYNOPSIS
    General Ledger Trial Balance.

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
from TartanClasses import ASD, CCD, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, showError
from tartanFunctions import showInfo
from tartanWork import mthnam

class gl3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts and "noprint" not in self.opts["args"]:
                self.opebal = "N"
                self.incope = "Y"
                self.end, self.zerbal, self.repprt, self.repeml, self.fpdf = \
                        self.opts["args"]
                self.doEnd()
            elif "wait" in self.opts:
                self.mainProcess()
                self.df.mstFrame.wait_window()
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genbal", "genmst", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head1 = ("%03u %-30s" % (self.opts["conum"], self.opts["conam"]))
        self.colsh = ["Acc-Num", "T", "Description", "Debit", "Credit"]
        self.forms = [("UI", 7), ("UA", 1), ("NA", 40)] + [("SD", 14.2)] * 2
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        self.dtot = 0.00
        self.ctot = 0.00
        self.gp = 0.00
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Trial Balance (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"), ("No","N"))
        r2s = (("Single", "S"), ("Monthly", "M"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["S", "N", "Y", "", "", "Y"]
            view = ("Y","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),("IRB",r2s),0,"Report Columns","",
                var[0],"N",self.doRType,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Opening Balances Only","",
                var[1],"Y",self.doOpeBal1,None,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Include Opening Balances","",
                var[2],"N",self.doOpeBal2,None,None,None,None,
                """Y - Closing Balances will be Printed
N - Period Movements will be Printed"""),
            (("T",0,3,0),"Id2",7,"Starting Period","",
                self.s_per,"N",self.doStartPer,None,None,("efld",)),
            (("T",0,4,0),"Id2",7,"Ending Period","",
                self.e_per,"N",self.doEndPer,None,None,("efld",)),
            (("T",0,5,0),("IRB",r1s),0,"Ignore Zero Balances","",
                var[5],"N",self.doZerBal,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doRType(self, frt, pag, r, c, p, i, w):
        self.rtype = w
        if self.rtype == "M":
            self.opebal = "N"
            self.df.loadEntry(frt, pag, i+1, data=self.opebal)
            return "sk1"

    def doOpeBal1(self, frt, pag, r, c, p, i, w):
        self.opebal = w
        if self.opebal == "Y":
            self.incope = None
            self.end = None
            return "sk3"

    def doOpeBal2(self, frt, pag, r, c, p, i, w):
        self.incope = w
        if self.rtype == "S" and self.incope == "Y":
            self.start = self.s_per
            self.df.loadEntry(frt, pag, p+1, data=self.start)
            return "sk1"

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period, Outside Financial Period"
        self.start = w

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if w < self.start:
            return "Invalid Period, Before Start Period"
        if w > self.e_per:
            return "Invalid Period, Outside Financial Period"
        self.end = w
        if self.rtype == "M":
            yrs = int(self.start / 100)
            mth = self.start % 100
            self.pers = [self.start]
            self.mths = [mthnam[mth][1]]
            per = self.start
            while per != self.end:
                mth += 1
                if mth > 12:
                    mth = 1
                    yrs += 1
                per = (yrs * 100) + mth
                self.pers.append(per)
                self.mths.append(mthnam[mth][1])
            self.gprs = [0.00] * len(self.mths)
            self.dtot = [0.00] * len(self.mths)
            if self.incope == "N":
                self.gprs.append(0.00)
                self.dtot.append(0.00)

    def doZerBal(self, frt, pag, r, c, p, i, w):
        self.zerbal = w

    def doEnd(self):
        if "args" not in self.opts or "noprint" in self.opts["args"]:
            self.repprt = self.df.repprt
            self.repeml = self.df.repeml
            self.t_work = [self.df.t_work[0][0]]
            self.df.closeProcess()
        recs = self.sql.getRec("genmst", cols=["glm_acno", "glm_desc",
            "glm_type"], where=[("glm_cono", "=", self.opts["conum"])],
            order="glm_type desc, glm_acno")
        if not recs:
            showError(self.opts["mf"].body, "Error", "No Accounts Selected")
        elif self.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" not in self.opts or "noprint" in self.opts["args"]:
            self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        expheads = [self.head1 + " %s" % self.sysdttm]
        if self.opebal == "Y":
            date = CCD(self.opts["period"][1][0], "D1", 10)
            expheads.append("General Ledger Opening Balances as at %s" % \
                date.disp)
        else:
            sdate = CCD(self.start, "D2", 7)
            edate = CCD(self.end, "D2", 7)
            expheads.append("General Ledger Trial Balance for Period %s "\
                "to %s" % (sdate.disp, edate.disp))
            if self.incope == "N":
                txt = " Not"
            else:
                txt = ""
            expheads.append("(Options: Opening Balances%s Included)" % txt)
        self.expdatas = []
        if self.rtype == "S":
            expcolsh = [self.colsh]
            expforms = self.forms
        else:
            expcolsh = [self.colsh[:3]]
            expforms = self.forms[:3]
            for mth in self.mths:
                expcolsh[0].append(mth)
                expforms.append(("SD", 14.2))
            if self.incope == "N":
                expcolsh[0].append("Totals")
                expforms.append(("SD", 14.2))
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            val = []
            for v in vals:
                val.append(v.work)
            self.expdatas.append(["BODY", val])
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.repprt[1], name=expnam,
            heads=expheads, colsh=expcolsh, forms=expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        if self.opebal == "Y":
            date = CCD(self.opts["period"][1][0], "D1", 10.0)
            self.head2 = "General Ledger Opening Balances as at %s" % date.disp
        else:
            sdate = CCD(self.start, "D2", 7)
            edate = CCD(self.end, "D2", 7)
            self.head2 = "General Ledger Trial Balance for Period %s to %s" % \
                (sdate.disp, edate.disp)
        if self.rtype == "S":
            head = 80
        else:
            head = 50 + (len(self.mths) * 15)
            if self.incope == "N":
                head += 15
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if "args" not in self.opts or "noprint" in self.opts["args"]:
            self.fpdf = MyFpdf(name=self.__class__.__name__, head=head)
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(rec)
            if not vals:
                continue
            if self.fpdf.newPage():
                self.pageHeading()
            if self.rtype == "S":
                self.fpdf.drawText("%s %1s %-40s %s %s" % (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp))
            else:
                txt = "%s %1s %-40s" % (vals[0].disp, vals[1].disp,
                    vals[2].disp)
                for v in range(len(self.mths)):
                    txt += " %s" % vals[3 + v].disp
                if self.incope == "N":
                    txt += " %s" % vals[4 + v].disp
                self.fpdf.drawText(txt)
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.grandTotal()
            if "args" not in self.opts:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.repprt,
                        repeml=self.repeml)
        elif not p.quit:
            showInfo(self.opts["mf"].body, "Info", "No Balances to Print")

    def getValues(self, data):
        acno = CCD(data[0], "UI", 7)
        desc = CCD(data[1], "NA", 40)
        atyp = CCD(data[2], "UA", 1)
        bal = 0.0
        if self.opebal == "Y" or self.incope == "Y":
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                acno.work), ("glo_trdt", "=", self.opts["period"][1][0])],
                limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            bal = float(ASD(bal) + ASD(b.work))
        if self.rtype == "S":
            vals = self.getTotals(acno, atyp, bal, self.end)
            if vals:
                return (acno, atyp, desc, vals[0], vals[1])
        else:
            val = []
            prt = False
            if self.incope == "N":
                tot = 0.00
            for per in self.pers:
                vals = self.getTotals(acno, atyp, bal, per)
                if vals:
                    prt = True
                    val.append(vals)
                    if self.incope == "N":
                        tot = float(ASD(tot) + ASD(vals.work))
                else:
                    val.append(CCD(0, "SD", 14.2))
            if prt:
                if self.incope == "N":
                    val.append(CCD(tot, "SD", 14.2))
                return [acno, atyp, desc] + val

    def getTotals(self, acno, atyp, bal, per):
        where = [("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", acno.work)]
        if self.opebal == "N":
            whr = where[:]
            if self.incope == "Y":
                whr.append(("glt_curdt", ">=", self.s_per))
                if self.rtype == "S":
                    whr.append(("glt_curdt", "<=", self.end))
                else:
                    whr.append(("glt_curdt", "<=", per))
            elif self.rtype == "S":
                whr.append(("glt_curdt", ">=", self.start))
                whr.append(("glt_curdt", "<=", self.end))
            else:
                whr.append(("glt_curdt", "=", per))
            o = self.sql.getRec("gentrn", cols=["sum(glt_tramt)"],
                where=whr, limit=1)
            if o and o[0]:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            bal = float(ASD(bal) + ASD(b.work))
        if bal == 0 and self.zerbal == "Y":
            return
        if self.rtype == "M":
            mdx = self.pers.index(per)
            self.dtot[mdx] = float(ASD(self.dtot[mdx]) + ASD(bal))
            if self.incope == "N":
                tdx = len(self.gprs) - 1
                self.dtot[tdx] = float(ASD(self.dtot[tdx]) + ASD(bal))
            if atyp.work == "P":
                self.gprs[mdx] = float(ASD(self.gprs[mdx]) + ASD(bal))
                if self.incope == "N":
                    self.gprs[tdx] = float(ASD(self.gprs[tdx]) + ASD(bal))
            return CCD(bal, "SD", 14.2)
        if bal < 0:
            cr = CCD(bal, "SD", 14.2)
            dr = CCD(0.00, "SD", 14.2)
        else:
            dr = CCD(bal, "SD", 14.2)
            cr = CCD(0.00, "SD", 14.2)
        self.dtot = float(ASD(self.dtot) + ASD(dr.work))
        self.ctot = float(ASD(self.ctot) + ASD(cr.work))
        if self.opebal == "N" and atyp.work == "P":
            self.gp = float(ASD(self.gp) + ASD(dr.work) + ASD(cr.work))
        return (dr, cr)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2)
        if self.opebal == "N":
            self.fpdf.drawText()
            if self.incope == "N":
                txt = " Not"
            else:
                txt = ""
            self.fpdf.drawText("(Options: Opening Balances%s Included)" % txt)
        self.fpdf.drawText()
        if self.rtype == "S":
            self.fpdf.drawText("%-7s %-1s %-40s %14s %14s" % \
                ("Acc-Num", "T", "Description", "Debit ", "Credit "))
        else:
            txt = "%-7s %-1s %-40s" % ("Acc-Num", "T", "Description")
            for mth in self.mths:
                txt += " %13s " % mth
            if self.incope == "N":
                txt += " %13s " % "Totals"
            self.fpdf.drawText(txt)
        self.fpdf.underLine()
        self.fpdf.setFont()

    def grandTotal(self):
        if self.repprt[2] == "export":
            if self.rtype == "S":
                self.expdatas.append(["ULINES"])
                self.expdatas.append(["TOTAL", ["", "", "Grand Totals",
                    self.dtot, self.ctot]])
                if self.gp > 0:
                    self.expdatas.append(["TOTAL", ["", "", "Gross-Loss",
                        self.gp, ""]])
                else:
                    self.expdatas.append(["TOTAL", ["", "", "Gross-Profit",
                        "", self.gp]])
                diff = float(ASD(self.dtot) + ASD(self.ctot))
                if diff:
                    self.expdatas.append(["TOTAL", ["", "", "Difference",
                        "", diff]])
            else:
                self.expdatas.append(["ULINES"])
                tmp = ["TOTAL", ["", "", "Gross Profit/Loss"] + self.gprs]
                self.expdatas.append(tmp)
                for d in self.dtot:
                    if d:
                        tmp = ["TOTAL", ["", "", "Difference"] + self.dtot]
                        self.expdatas.append(tmp)
                        break
            return
        self.fpdf.setFont(style="B")
        if self.rtype == "S":
            if self.opebal == "Y":
                extra = 1
            else:
                extra = 3
            diff = CCD(float(ASD(self.dtot) + ASD(self.ctot)), "SD", 14.2)
            if diff:
                extra += 2
        else:
            extra = 2
            diff = False
            for d in self.dtot:
                if d:
                    diff = True
                    extra += 2
                    break
        if self.fpdf.newPage(extra):
            self.pageHeading()
            self.fpdf.setFont(style="B")
        else:
            self.fpdf.underLine()
        if self.rtype == "S":
            d = CCD(self.dtot, "SD", 14.2)
            c = CCD(self.ctot, "SD", 14.2)
            self.fpdf.drawText("%9s %-40s %14s %14s" % \
                ("", "Grand-Totals", d.disp, c.disp))
            if self.opebal == "N":
                self.fpdf.drawText()
                gp = CCD(self.gp, "SD", 14.2)
                if gp.work > 0:
                    self.fpdf.drawText("%9s %-40s %14s %14s" % \
                        ("", "Gross-Loss", gp.disp, ""))
                else:
                    self.fpdf.drawText("%9s %-40s %14s %14s" % \
                        ("", "Gross-Profit", "", gp.disp))
            if diff.work:
                self.fpdf.drawText()
                self.fpdf.drawText("%9s %-40s %14s %14s" % \
                    ("", "Difference", "", diff.disp))
        else:
            txt = "%9s %-40s" % ("", "Gross Profit/Loss")
            for val in self.gprs:
                txt += " %14s" % CCD(val, "SD", 14.2).disp
            self.fpdf.drawText(txt)
            if diff:
                txt = "%9s %-40s" % ("", "Difference")
                for val in self.dtot:
                    txt += " %14s" % CCD(val, "SD", 14.2).disp
                self.fpdf.drawText(txt)
        self.fpdf.setFont()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
