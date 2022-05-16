"""
SYNOPSIS
    Creditors Ledger Age Analysis.

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

class cr3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["Acc-Num", "Name", "Cr-Balance", "Tot-Balance",
            "Current", "30-Days", "60-Days", "90-Days", "Over-90-Days"]
        self.forms = [("NA", 7), ("NA", 30)] + [("SD", 13.2)] * 7
        self.gtots = [0] * 7
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Age Analysis (%s)" % self.__class__.__name__)
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [("crm_cono", "=", self.opts["conum"])],
            "autoc": False}
        r1s = (("Agedt", "A"),("Curdt","C"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Yes", "Y"), ("No", "N"), ("Only", "O"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["A", "", "N", "", "", 0, "Y", "Y"]
            view = ("Y", "V")
            mail = ("Y", "N")
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Base","",
                var[0],"Y",self.doBase,None,None,None),
            (("T",0,1,0),"Id2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"N",self.doCutOff,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Totals Only","",
                var[2],"N",self.doTots,None,None,None),
            (("T",0,3,0),"INA",7,"First Account Number","",
                var[3],"N",self.doAcc1,crm,None,None),
            (("T",0,4,0),"INA",7,"Last Account Number","",
                var[4],"N",self.doAcc2,crm,None,None),
            (("T",0,5,0),"IUI",7,"Lower Balance Limit","",
                var[5],"N",self.doLimit,None,None,None),
            (("T",0,6,0),("IRB",r3s),0,"Include Debit Balances","",
                var[6],"N",self.doDebit,None,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Ignore Zero Balances","",
                var[7],"N",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doBase(self, frt, pag, r, c, p, i, w):
        self.base = w

    def doCutOff(self, frt, pag, r, c, p, i, w):
        self.cutoff = w
        self.opts["period"] = self.df.t_disp[pag][r][p]

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if self.totsonly == "Y":
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                self.df.setWidget(self.df.topEntry[0][8][3][0], state="hide")
                self.df.setWidget(self.df.topEntry[0][8][4][0], state="hide")
            self.acc1 = ""
            self.fm = "First"
            self.acc2 = "zzzzzzz"
            self.to = "Last"
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            self.limit = 0
            self.df.loadEntry(frt, pag, p+3, data=self.limit)
            self.debit = "Y"
            self.df.loadEntry(frt, pag, p+4, data=self.debit)
            self.zero = "Y"
            self.df.loadEntry(frt, pag, p+5, data=self.zero)
            return "sk5"
        elif "args" in self.opts and "noprint" in self.opts["args"]:
            pass
        else:
            self.df.setWidget(self.df.topEntry[0][8][3][0], state="show")
            self.df.setWidget(self.df.topEntry[0][8][4][0], state="show")

    def doAcc1(self, frt, pag, r, c, p, i, w):
        self.acc1 = w
        if not self.acc1:
            self.fm = "First"
        else:
            self.fm = self.acc1

    def doAcc2(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.acc1:
                return "Invalid Last Account < First Account"
            self.acc2 = w
            self.to = self.acc2
        else:
            self.acc2 = "zzzzzzz"
            self.to = "Last"

    def doLimit(self, frt, pag, r, c, p, i, w):
        self.limit = w
        if self.limit:
            self.debit = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.limit)
            self.zero = "Y"
            self.df.loadEntry(frt, pag, p+2, data=self.zero)
            return "sk2"

    def doDebit(self, frt, pag, r, c, p, i, w):
        self.debit = w
        if self.debit == "O":
            self.zero = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.zero)
            return "sk1"

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [
            ("crm_cono", "=", self.opts["conum"]),
            ("crm_acno", ">=", self.acc1),
            ("crm_acno", "<=", self.acc2)]
        recs = self.sql.getRec("crsmst", cols=["crm_acno", "crm_name"],
            where=whr, order="crm_acno")
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Accounts Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Creditor's Age Analaysis up to %s" %
            self.opts["period"])
        self.expheads.append("Options: From %s To %s Low-Bal %s Dr-Bals "\
            "%s Ignore-Zeros %s" % (self.fm, self.to, self.limit, self.debit,
            self.zero))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            line = ["BODY", [vals[0].work, vals[1].work]]
            for val in vals[2:]:
                line[1].append(val.work)
            self.expdatas.append(line)
        p.closeProgress()
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
        self.head1 = self.head
        self.head2 = "Creditor's Age Analysis up to %s" % self.opts["period"]
        pad = chrs - len(self.head2)
        self.head2 = self.head2 + (" " * pad)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head2)
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.totsonly != "Y":
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % \
                    (vals[0].disp, vals[1].disp, vals[2].disp, vals[3].disp,
                    vals[4].disp, vals[5].disp, vals[6].disp, vals[7].disp,
                    vals[8].disp))
                self.pglin += 1
        p.closeProgress()
        if p.quit:
            return
        if self.totsonly == "Y":
            self.pageHeading()
        if self.fpdf.page:
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        acc = CCD(data[0], "NA", 7)
        name = CCD(data[1], "NA", 30)
        if self.base == "A":
            bals = Balances(self.opts["mf"], "CRS", self.opts["conum"],
                self.cutoff, keys=(data[0],))
            obal, cbal, ages = bals.doAllBals()
        else:
            pers = []
            yr = int(self.cutoff / 100)
            mt = int(self.cutoff % 100)
            for x in range(4):
                pers.append((yr * 100) + mt)
                mt -= 1
                if not mt:
                    yr -= 1
                    mt = 12
            cbal = 0
            ages = [0, 0, 0, 0, 0]
            bals = self.sql.getRec("crstrn", cols=["crt_curdt",
                "sum(crt_tramt)"], where=[("crt_cono", "=", self.opts["conum"]),
                ("crt_acno", "=", acc.work), ("crt_curdt", "<=", pers[0])],
                group="crt_curdt", order="crt_curdt")
            for bal in bals:
                try:
                    idx = pers.index(bal[0])
                except:
                    idx = 4
                ages[idx] = float(ASD(ages[idx]) + ASD(bal[1]))
                cbal = float(ASD(cbal) + ASD(bal[1]))
        bal = CCD(cbal, "SD", 13.2)
        if self.limit and bal.work < self.limit:
            return
        if self.zero == "Y" and not bal.work:
            return
        if self.debit == "N" and bal.work < 0:
            return
        if self.debit == "O" and bal.work >= 0:
            return
        cur = CCD(ages[0], "SD", 13.2)
        d30 = CCD(ages[1], "SD", 13.2)
        d60 = CCD(ages[2], "SD", 13.2)
        d90 = CCD(ages[3], "SD", 13.2)
        d120 = CCD(ages[4], "SD", 13.2)
        if bal.work < 0:
            deb = CCD(bal.work, "SD", 13.2)
        else:
            deb = CCD(0, "SD", 13.2)
        self.gtots[0] = float(ASD(self.gtots[0]) + ASD(deb.work))
        self.gtots[1] = float(ASD(self.gtots[1]) + ASD(bal.work))
        self.gtots[2] = float(ASD(self.gtots[2]) + ASD(cur.work))
        self.gtots[3] = float(ASD(self.gtots[3]) + ASD(d30.work))
        self.gtots[4] = float(ASD(self.gtots[4]) + ASD(d60.work))
        self.gtots[5] = float(ASD(self.gtots[5]) + ASD(d90.work))
        self.gtots[6] = float(ASD(self.gtots[6]) + ASD(d120.work))
        return (acc, name, deb, bal, cur, d30, d60, d90, d120)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-16s%-7s%-3s%-4s%-7s%-3s%-9s%-8s%-3s%-13s%-1s"\
            "%-3s%-17s%-1s%-1s" % ("(Options: From: ", self.fm, "", "To: ",
            self.to, "", "Low-Bal: ", self.limit, "", "Dr-Bals: ",
            self.debit, "", "Ignore-Zero-Bal: ", self.zero, ")"))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %-13s %-13s %-13s %-13s %-13s %-13s "\
            "%-13s" % ("Acc-Num", "Name", "  Dr-Balance", " Tot-Balance",
            "     Current", "     30-Days", "     60-Days", "     90-Days",
            "Over-90-Days"))
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head2)))
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "Grand Totals"] + self.gtots])
            self.expdatas.append(["ULINED"])
            return
        t = []
        p = []
        for x in range(0, 7):
            t.append(CCD(self.gtots[x], "SD", 13.2))
            if self.gtots[1] == 0:
                p.append(CCD(0, "SD", 13.2))
            else:
                p.append(CCD(round((self.gtots[x] / self.gtots[1] * 100.0), 2),
                    "SD", 13.2))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %13s %13s %13s %13s %13s %13s %13s" % \
            (" ", "Grand Totals", t[0].disp, t[1].disp, t[2].disp, t[3].disp,
            t[4].disp, t[5].disp, t[6].disp))
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-30s %13s %13s %13s %13s %13s %13s %13s" % \
            (" ", "Percentages", p[0].disp, p[1].disp, p[2].disp, p[3].disp,
            p[4].disp, p[5].disp, p[6].disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
