"""
SYNOPSIS
    Debtors Ledger Sales History.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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
from TartanClasses import Balances, CCD, CreateChart, GetCtl, MyFpdf
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import doWriteExport, getModName, doPrinter, showError
from tartanWork import mthnam

class dr3110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "drsmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.fromad = drsctl["ctd_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.forms = [("UI",3), ("NA",7), ("NA",30), ("Na",3), ("UA",3),
            ("UA",3)] + [("SI",10)] * 12
        self.stots = [0] * 12
        self.gtots = [0] * 12
        self.mchart = []
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Debtor's Sales History (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"ID2",7,"Ending Period","",
                int(self.sysdtw / 100),"Y",self.doDat,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Ignore Zero Sales","",
                "Y","Y",self.doZer,None,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Report By Salesman","",
                "N","Y",self.doRep,None,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Report By Activity","",
                "N","Y",self.doAct,None,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Report By Type","",
                "N","Y",self.doTyp,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDat(self, frt, pag, r, c, p, i, w):
        self.coffw = w
        self.coffd = self.df.t_disp[pag][r][p]

    def doZer(self, frt, pag, r, c, p, i, w):
        self.zer = w

    def doRep(self, frt, pag, r, c, p, i, w):
        self.rep = w
        if self.rep == "Y":
            self.act = "N"
            self.typ = "N"
            return "sk2"

    def doAct(self, frt, pag, r, c, p, i, w):
        self.act = w
        if self.act == "Y":
            self.typ = "N"
            return "sk1"

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("drm_cono", "=", self.opts["conum"])]
        if self.rep == "Y":
            odr = "drm_rep, drm_chain, drm_acno"
        elif self.act == "Y":
            odr = "drm_bus_activity, drm_chain, drm_acno"
        elif self.typ == "Y":
            odr = "drm_bus_type, drm_chain, drm_acno"
        else:
            odr = "drm_chain, drm_acno"
        acs = self.sql.getRec("drsmst", cols=["drm_chain", "drm_acno",
            "drm_name", "drm_rep", "drm_bus_activity", "drm_bus_type"],
            where=whr, order=odr)
        if not acs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Accounts Selected")
        else:
            self.start = self.coffw - 99
            if self.start % 100 == 13:
                self.start = self.start + 88
            s = self.start % 100
            self.mthhead = ""
            self.colsh = ["Chn", "Acc-Num", "Name", "Rep", "Act", "Typ"]
            for _ in range(12):
                if self.mthhead:
                    self.mthhead = "%s %9s " % (self.mthhead, mthnam[s][1])
                else:
                    self.mthhead = "%9s " % mthnam[s][1]
                self.colsh.append(mthnam[s][1])
                s += 1
                if s == 13:
                    s = 1
            if self.df.repprt[2] == "export":
                self.exportReport(acs)
            else:
                self.printReport(acs)
        self.closeProcess()

    def exportReport(self, acs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(acs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Debtor's Sales History for the 12 Months "\
            "Period to %s" % self.coffd)
        self.expheads.append("Options:- Ignore-Zeros: %s" % self.zer)
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(acs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            line = ["BODY", [vals[0].work, vals[1].work, vals[2].work,
                vals[3].work, vals[4].work, vals[5].work]]
            for val in vals[7]:
                line[1].append(val)
            self.expdatas.append(line)
        p.closeProgress()
        self.doTotals()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, acs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(acs), esc=True)
        chrs = len(self.colsh)
        if self.rep == "Y" or self.act == "Y" or self.typ == "Y":
            chrs -= 1
        for n, f in enumerate(self.forms):
            if self.rep == "Y" and n == 3:
                continue
            if self.act == "Y" and n == 4:
                continue
            if self.typ == "Y" and n == 5:
                continue
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        self.head1 = self.head
        self.head2 = "Debtor's Sales History for the 12 Months "\
            "Period to %s" % self.coffd
        pad = chrs - len(self.head2)
        self.head2 = self.head2 + (" " * pad)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head2)
        self.pglin = 999
        self.repno = None
        self.actno = None
        self.typno = None
        for num, dat in enumerate(acs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            if self.rep == "Y":
                self.fpdf.drawText("%s %s %s %s %s %s" % (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[4].disp, vals[5].disp,
                    vals[6]))
            elif self.act == "Y":
                self.fpdf.drawText("%s %s %s %s %s %s" % (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[3].disp, vals[5].disp,
                    vals[6]))
            elif self.typ == "Y":
                self.fpdf.drawText("%s %s %s %s %s %s" % (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp,
                    vals[6]))
            else:
                self.fpdf.drawText("%s %s %s %s %s %s %s" % (vals[0].disp,
                    vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp,
                    vals[5].disp, vals[6]))
            self.pglin += 1
        p.closeProgress()
        if not self.fpdf.page or p.quit:
            return
        if self.rep == "Y" or self.act == "Y" or self.typ == "Y":
            self.doTotals(ttype="S")
        self.doTotals(ttype="G")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header=self.tit, repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)
        if self.df.repprt[1] == "X":
            return
        CreateChart(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            [self.start, self.coffw], [[self.opts["conam"], "Sales History"],
            "Values"], None, self.mchart)

    def getValues(self, data):
        chn = CCD(data[0], "UI", 3)
        acc = CCD(data[1], "NA", 7)
        name = CCD(data[2], "NA", 30)
        rep = CCD(data[3], "Na", 3)
        act = CCD(data[4], "UA", 3)
        typ = CCD(data[5], "UA", 3)
        if self.df.repprt[2] != "export":
            if self.rep == "Y":
                if rep.work != self.repno:
                    if self.repno is not None:
                        self.doTotals(ttype="S")
                    self.repno = rep.work
                    self.pageHeading()
            elif self.act == "Y":
                if act.work != self.actno:
                    if self.actno is not None:
                        self.doTotals(ttype="S")
                    self.actno = act.work
                    self.pageHeading()
            elif self.typ == "Y":
                if typ.work != self.typno:
                    if self.typno is not None:
                        self.doTotals(ttype="S")
                    self.typno = typ.work
                    self.pageHeading()
        bals = Balances(self.opts["mf"], "DRS", self.opts["conum"], self.coffw,
            (chn.work, acc.work))
        this, hist = bals.doCrsDrsHist()
        if not this:
            return
        salesd = ""
        salesw = []
        purtot = 0
        for x in range(11, -1, -1):
            amt = CCD(round(hist[0][x], 0), "SI", 10)
            self.stots[x] = self.stots[x] + amt.work
            self.gtots[x] = self.gtots[x] + amt.work
            purtot = purtot + amt.work
            if salesd:
                salesd = "%s %9s" % (salesd, amt.disp)
            else:
                salesd = "%9s" % amt.disp
            salesw.append(amt.work)
        if self.zer == "Y" and purtot == 0:
            return
        return chn, acc, name, rep, act, typ, salesd, salesw

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2)
        self.fpdf.drawText()
        self.fpdf.drawText("(%-23s %1s %-12s %1s)" % \
            ("Options:- Ignore Zeros:", self.zer, "By Salesman:", self.rep))
        self.fpdf.drawText()
        if self.rep == "Y":
            acc = self.sql.getRec("ctlrep", cols=["rep_name"],
                where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=",
                self.repno)], limit=1)
            if acc:
                self.repnam = acc[0]
            else:
                self.repnam = "Unallocated Accounts"
            self.fpdf.drawText("Saleman %-3s %-30s" % (self.repno,
                self.repnam))
            self.fpdf.drawText()
            self.fpdf.drawText("%-3s %-7s %-30s %3s %3s %s" % ("Chn",
                "Acc-Num", "Name", "Act", "Typ", self.mthhead))
        elif self.act == "Y":
            acc = self.sql.getRec("drsact", cols=["dac_desc"],
                where=[("dac_code", "=", self.actno)], limit=1)
            if acc:
                self.actnam = acc[0]
            else:
                self.actnam = "Unallocated Accounts"
            self.fpdf.drawText("Activity %-3s %-30s" % (self.actno,
                self.actnam))
            self.fpdf.drawText()
            self.fpdf.drawText("%-3s %-7s %-30s %3s %3s %s" % ("Chn",
                "Acc-Num", "Name", "Rep", "Typ", self.mthhead))
        elif self.typ == "Y":
            acc = self.sql.getRec("drstyp", cols=["dtp_desc"],
                where=[("dtp_code", "=", self.typno)], limit=1)
            if acc:
                self.typnam = acc[0]
            else:
                self.typnam = "Unallocated Accounts"
            self.fpdf.drawText("Type %-3s %-30s" % (self.typno, self.typnam))
            self.fpdf.drawText()
            self.fpdf.drawText("%-3s %-7s %-30s %3s %3s %s" % ("Chn",
                "Acc-Num", "Name", "Rep", "Act", self.mthhead))
        else:
            self.fpdf.drawText("%-3s %-7s %-30s %-3s %3s %3s %s" % ("Chn",
                "Acc-Num", "Name", "Rep", "Act", "Typ", self.mthhead))
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head2)))
        self.fpdf.setFont()
        self.pglin = 10

    def doTotals(self, ttype="G"):
        self.gtots.reverse()
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "",
                "Grand Totals", "", "", ""] + self.gtots])
            self.expdatas.append(["ULINED"])
            return
        if ttype == "G":
            desc = "Grand Total"
        elif self.rep == "Y":
            desc = "%s Total" % self.repnam
        elif self.act == "Y":
            desc = "%s Total" % self.actnam
        else:
            desc = "%s Total" % self.typnam
        mchart = ["T", desc]
        salesd = ""
        for x in range(12):
            if ttype == "G":
                a = CCD(self.gtots[x], "SI", 10)
            else:
                a = CCD(self.stots[x], "SI", 10)
                self.stots[x] = 0
            if salesd:
                salesd = "%s %s" % (salesd, a.disp)
            else:
                salesd = "%s" % a.disp
            mchart.append(a.work)
        self.mchart.append(mchart)
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head2)))
        if self.rep == "Y":
            self.fpdf.drawText("%7s %3s %-30s %-3s %-3s %s" % ("", "",
                desc, "", "", salesd))
        elif self.act == "Y":
            self.fpdf.drawText("%7s %3s %-30s %-3s %-3s %s" % ("", "",
                desc, "", "", salesd))
        elif self.typ == "Y":
            self.fpdf.drawText("%7s %3s %-30s %-3s %-3s %s" % ("", "",
                desc, "", "", salesd))
        else:
            self.fpdf.drawText("%7s %3s %-30s %-3s %-3s %-3s %s" % ("", "",
                desc, "", "", "", salesd))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
