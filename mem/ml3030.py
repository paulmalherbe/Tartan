"""
SYNOPSIS
    Members Ledger Age Analysis.

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

class ml3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["memmst", "memtrn", "memctc"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.fromad = memctl["mcm_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["Mem-No", "Member", "Cr-Balance", "Tot-Balance",
            "Current", "30-Days", "60-Days", "90-Days", "Over-90-Days"]
        self.forms = [("UI", 6), ("NA", 30)] + [("SD", 13.2)] * 7
        self.gtots = [0] * 7
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Members Ledger Age Analysis (%s)" % self.__class__.__name__)
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "mcc_type", 2]],
            "order": "mcc_code",
            "size": (400, 600)}
        mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": (
                ("mlm_memno", "", 0, "Mem-No"),
                ("mlm_oldno", "", 0, "Old-No"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")),
            "where": [("mlm_cono", "=", self.opts["conum"])],
            "order": "mlm_surname, mlm_names",
            "sort": False}
        r1s = (
            ("All", "B"),
            ("Active", "A"),
            ("Not Active", "N"))
        r2s = (
            ("All", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        r3s = (("Yes","Y"),("No","N"))
        r4s = (("Number","N"),("Surname","M"))
        fld = (
            (("T",0,0,0),"Id2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"Y",self.doCutOff,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Status","",
                "B","Y",self.doStat,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Category","",
                "A","Y",self.doCat,None,None,None),
            (("T",0,3,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None),
            (("T",0,3,0),"ONA",30,""),
            (("T",0,4,0),("IRB",r3s),0,"Totals Only","",
                "N","Y",self.doTots,None,None,None),
            (("T",0,5,0),("IRB",r4s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,6,0),"IUI",6,"First Member Number","",
                "","Y",self.doAcc1,mlm,None,None),
            (("T",0,7,0),"IUI",6,"Last Member Number","",
                "","Y",self.doAcc2,mlm,None,None),
            (("T",0,8,0),"IUI",7,"Lower Balance Limit","",
                0,"Y",self.doLimit,None,None,None),
            (("T",0,9,0),("IRB",r3s),0,"Include Credit Balances","",
                "Y","Y",self.doCredit,None,None,None),
            (("T",0,10,0),("IRB",r3s),0,"Credit Balances Only","",
                "N","Y",self.doOnlyCr,None,None,None),
            (("T",0,11,0),("IRB",r3s),0,"Ignore Zero Balances","",
                "Y","Y",self.doZero,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doCutOff(self, frt, pag, r, c, p, i, w):
        self.cutoff = w
        self.opts["period"] = self.df.t_disp[pag][r][p]

    def doStat(self, frt, pag, r, c, p, i, w):
        self.stat = w

    def doCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.cat = ""
            self.cod = ""
            self.df.loadEntry(frt, pag, p+2, data="All Categories and Codes")
            return "sk2"
        self.cat = w

    def doCod(self, frt, pag, r, c, p, i, w):
        self.cod = w
        if self.cod:
            self.chk = self.sql.getRec("memctc", cols=["mcc_desc"],
                where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
                self.cat), ("mcc_code", "=", self.cod)], limit=1)
            if not self.chk:
                return "Invalid Category Code"
            self.df.loadEntry(frt, pag, p+1, data=self.chk[0])
        else:
            self.df.loadEntry(frt, pag, p+1, "All Codes")

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if self.totsonly == "Y":
            self.df.setWidget(self.df.topEntry[0][13][3][0], state="hide")
            self.df.setWidget(self.df.topEntry[0][13][4][0], state="hide")
            self.sort = "N"
            self.acc1 = 0
            self.fm = "First"
            self.acc2 = 999999
            self.to = "Last"
            self.limit = 0
            self.credit = "Y"
            self.onlycr = "N"
            self.zero = "Y"
            return "sk7"
        else:
            self.df.setWidget(self.df.topEntry[0][13][3][0], state="show")
            self.df.setWidget(self.df.topEntry[0][13][4][0], state="show")

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doAcc1(self, frt, pag, r, c, p, i, w):
        self.acc1 = w
        if not self.acc1:
            self.fm = "First"
        else:
            self.fm = self.acc1

    def doAcc2(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.acc1:
                return "Invalid Last Member < First Member"
            self.acc2 = w
            self.to = self.acc2
        else:
            self.acc2 = 999999
            self.to = "Last"

    def doLimit(self, frt, pag, r, c, p, i, w):
        self.limit = w
        if self.limit:
            self.credit = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.limit)
            self.onlycr = "N"
            self.df.loadEntry(frt, pag, p+2, data=self.onlycr)
            self.zero = "Y"
            self.df.loadEntry(frt, pag, p+3, data=self.zero)
            return "sk3"

    def doCredit(self, frt, pag, r, c, p, i, w):
        self.credit = w
        if self.credit == "N":
            self.onlycr = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.limit)
            return "sk1"

    def doOnlyCr(self, frt, pag, r, c, p, i, w):
        self.onlycr = w
        if self.onlycr == "Y":
            self.zero = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.zero)
            return "sk1"

    def doZero(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["memmst"]
        whr = [
            ("mlm_cono", "=", self.opts["conum"]),
            ("mlm_memno", ">=", self.acc1),
            ("mlm_memno", "<=", self.acc2)]
        if self.stat == "A":
            whr.append(("mlm_state", "=", "A"))
        elif self.stat == "N":
            whr.append(("mlm_state", "<>", "A"))
        if self.cat:
            tab.append("memcat")
            whr.append(("mlc_cono=mlm_cono",))
            whr.append(("mlc_memno=mlm_memno",))
            whr.append(("mlc_type", "=", self.cat))
            if self.cod:
                whr.append(("mlc_code", "=", self.cod))
        if self.totsonly == "N" and self.sort == "N":
            odr = "mlm_memno"
        else:
            odr = "mlm_surname"
        recs = self.sql.getRec(tables=tab, cols=["mlm_memno", "mlm_title",
            "mlm_initial", "mlm_surname"], where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Members Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Members Age Analysis up to %s" %
            self.opts["period"])
        self.expheads.append(self.getOptions())
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
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        self.head1 = self.head
        self.head2 = "Members Age Analysis up to %s" % self.opts["period"]
        pad = chrs - len(self.head2)
        self.head2 = self.head2 + (" " * pad)
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
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
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" %
                    (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp,
                    vals[5].disp, vals[6].disp, vals[7].disp, vals[8].disp))
                self.pglin += 1
        p.closeProgress()
        if p.quit:
            return
        if self.totsonly == "Y":
            self.pageHeading()
        if self.fpdf.page:
            self.grandTotal()
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        acc = CCD(data[0], "UI", 6)
        name = CCD("%s, %s %s" % (data[3], data[1], data[2]), "NA", 30)
        bals = Balances(self.opts["mf"], "MEM", self.opts["conum"],
            self.cutoff, keys=(acc.work,))
        obal, cbal, ages = bals.doAllBals()
        bal = CCD(cbal, "SD", 13.2)
        if self.limit and bal.work < self.limit:
            return
        if self.zero == "Y" and not bal.work:
            return
        if self.credit == "N" and bal.work < 0:
            return
        if self.onlycr == "Y" and bal.work >= 0:
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
        self.fpdf.drawText(self.getOptions())
        self.fpdf.drawText()
        self.fpdf.drawText("%-6s %-30s %-13s %-13s %-13s %-13s %-13s %-13s "\
            "%-13s" % ("Mem-No", "Member", "  Cr-Balance", " Tot-Balance",
            "     Current", "     30-Days", "     60-Days", "     90-Days",
            "Over-90-Days"))
        self.fpdf.underLine(txt=self.head2)
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
        for x in range(7):
            t.append(CCD(self.gtots[x], "SD", 13.2))
            if self.gtots[1] == 0:
                p.append(CCD(0, "SD", 13.2))
            else:
                p.append(CCD(round((self.gtots[x] / self.gtots[1] * 100.0), 2),
                    "SD", 13.2))
        self.fpdf.drawText()
        self.fpdf.drawText("%-6s %-30s %13s %13s %13s %13s %13s %13s %13s" % \
            (" ", "Grand Totals", t[0].disp, t[1].disp, t[2].disp, t[3].disp,
            t[4].disp, t[5].disp, t[6].disp))
        self.fpdf.drawText()
        self.fpdf.drawText("%-6s %-30s %13s %13s %13s %13s %13s %13s %13s" % \
            (" ", "Percentages", p[0].disp, p[1].disp, p[2].disp, p[3].disp,
            p[4].disp, p[5].disp, p[6].disp))

    def getOptions(self):
        if self.stat == "B":
            mess = "Options: All Members"
        elif self.stat == "A":
            mess = "Options: Active Members"
        else:
            mess = "Options: Non Active Members"
        if self.cat == "A":
            mess = mess + ", All Categories"
        elif self.cat == "B":
            mess = mess + ", Main Category:"
        elif self.cat == "C":
            mess = mess + ", Sports Category:"
        elif self.cat == "D":
            mess = mess + ", Debentures:"
        if self.cod:
            mess = mess + " %s" % self.chk[0]
        else:
            mess = mess + " All Codes"
        mess = "%s, From %s To %s, Low-Bal %s, Cr-Bal %s, Cr-Bal-Only %s, "\
            "Ignore-Zeros %s" % (mess, self.fm, self.to, self.limit,
            self.df.t_disp[0][0][10], self.df.t_disp[0][0][11],
            self.df.t_disp[0][0][12])
        return mess

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
