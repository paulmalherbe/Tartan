"""
SYNOPSIS
    Product Sales History Report.

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
from TartanClasses import ASD, Balances, CreateChart, CCD, GetCtl, MyFpdf
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName
from tartanFunctions import getSingleRecords, showError
from tartanWork import mthnam

class si3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strloc", "strmf1"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            self.chnstr = "N"
        else:
            self.chnstr = drsctl["ctd_chain"]
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.fromad = slsctl["ctv_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], "%s"))
        self.forms = [("UA",3),("NA",20),("NA",30),("NA",10)] + [("SI",10)]*12
        self.stots = [0] * 12
        self.gtots = [0] * 12
        self.mchart = []
        self.tipe = None
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Product Sales History (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        chm = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Chn"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": (("chm_cono", "=", self.opts["conum"]),)}
        r1s = (("Quantity","Q"),("Value","V"),("Profit","P"))
        r2s = (("Yes","Y"),("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            self.accs = self.opts["args"]["work"][1]
            view = None
            mail = None
        else:
            var = ["", "V", "", "", 0, "Y"]
            self.accs = []
            view = ("Y","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"Y",self.doCut,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                var[1],"N",self.doType,None,None,None),
            (("T",0,2,0),"IUA",1,"Location","",
                var[2],"N",self.doLoc,loc,None,("efld",)),
            (("T",0,3,0),"IUA",3,"Product Group","",
                var[3],"N",self.doGroup,grp,None,None),
            (("T",0,4,0),"IUI",3,"Chain Store","",
                var[4],"N",self.doDrsChn,chm,None,None),
            (("T",0,5,0),("IRB",r2s),0,"All Accounts","",
                var[5],"N",self.doDrsAcc,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doCut(self, frt, pag, r, c, p, i, w):
        self.coffw = w
        self.coffd = self.df.t_disp[pag][r][p]

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtype = w
        if self.locs == "N":
            self.loc = ""
            self.locd = "ALL"
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        if not w:
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.locd = "%s %s" % (w, acc[0])
        self.loc = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.getGroup(w)
            if not acc:
                return "Invalid Group"
        self.grp = w
        if self.chnstr == "N":
            self.chain = ""
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"

    def doDrsChn(self, frt, pag, r, c, p, i, w):
        self.chain = w

    def doDrsAcc(self, frt, pag, r, c, p, i, w):
        self.acno = []
        if w == "Y":
            return
        whr = [("drm_cono", "=", self.opts["conum"])]
        if self.chain:
            whr.append(("drm_chain", "=", self.chain))
        acc = getSingleRecords(self.opts["mf"], "drsmst", ("drm_acno",
            "drm_name"), where=whr, order="drm_chain, drm_acno",
            items=[0, self.accs])
        for a in acc:
            self.acno.append(a[2])

    def doEnd(self):
        self.df.closeProcess()
        if not self.grp:
            sgrp = ""
            egrp = "zzz"
        else:
            sgrp = egrp = self.grp
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", ">=", sgrp), ("st1_group", "<=",
            egrp)], order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        else:
            self.start = self.coffw - 99
            if self.start % 100 == 13:
                self.start = self.start + 88
            s = self.start % 100
            self.mthhead = ""
            self.colsh = ["Grp", "Stock-Code", "Description", "U.O.I."]
            for _ in range(12):
                if self.mthhead:
                    self.mthhead = "%s%9s " % (self.mthhead, mthnam[s][1])
                else:
                    self.mthhead = "%9s " % mthnam[s][1]
                self.colsh.append(mthnam[s][1])
                s += 1
                if s == 13:
                    s = 1
            if self.df.repprt[2] == "export":
                self.exportReport(recs)
            else:
                self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
            self.t_work.append(self.acno)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Stores Sales History for the 12 Month Period "\
            "to %s" % self.coffd)
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
            cod, dsc, uoi, amt, purchd, purchw = vals
            line = ["BODY", [self.grp.work,cod.work,dsc.work,uoi.work]+purchw]
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %110s %40s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        self.lstgrp = ""
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            cod, dsc, uoi, amt, purchd, purchw = vals
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s" % (self.grp.disp, cod.disp,
                dsc.disp, uoi.disp, purchd))
            self.pglin += 1
            self.lstgrp = self.grp.work
        p.closeProgress()
        if not self.fpdf.page or p.quit:
            return
        self.groupTotal()
        self.grandTotal()
        if "args" in self.opts and "noprint" in self.opts["args"]:
            return
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header=self.tit, repprt=self.df.repprt, fromad=self.fromad,
            repeml=self.df.repeml)
        if self.df.repprt[1] == "X" or not self.tipe:
            return
        CreateChart(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            [self.start, self.coffw], [[self.opts["conam"],
            "Product Sales History"], self.tipe], None, self.mchart,
            ylab=self.tipe)

    def getValues(self, data):
        self.grp = CCD(data[0], "UA", 3)
        if self.df.repprt[2] != "export":
            if self.lstgrp and self.lstgrp != self.grp.work:
                self.groupTotal()
        cod = CCD(data[1], "NA", 20)
        dsc = CCD(data[2], "NA", 30)
        uoi = CCD(data[3], "NA", 10)
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"], self.coffw,
            keys=(self.grp.work, cod.work, self.loc, ("S", self.start)))
        more = []
        if self.chain:
            more.append(("stt_chain", "=", self.chain))
        if self.acno:
            more.append(("stt_acno", "in", tuple(self.acno)))
        this, hist = bals.doStrHist(more=more)
        bals = hist[2]
        purchd = ""
        purchw = []
        tot = 0
        for x in range(11, -1, -1):
            if self.rtype == "Q":
                amt = float(ASD(0) - ASD(bals[x][0]))
            elif self.rtype == "V":
                amt = float(ASD(0) - ASD(bals[x][2]))
            else:
                amt = float(ASD(0) - ASD(bals[x][2]) + ASD(bals[x][1]))
            amt = CCD(round(amt, 0), "SI", 10)
            tot = float(ASD(tot) + ASD(amt.work))
            self.stots[x] = float(ASD(self.stots[x]) + ASD(amt.work))
            self.gtots[x] = float(ASD(self.gtots[x]) + ASD(amt.work))
            purchd = purchd + amt.disp
            purchw.append(amt.work)
        if tot == 0:
            return
        return (cod, dsc, uoi, amt, purchd, purchw)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-47s %-7s %124s %5s" % \
            ("Stores Sales History for the 12 Month Period to", self.coffd,
            "Page", self.pgnum))
        self.fpdf.drawText()
        acc = self.getGroup(self.grp.work)
        if acc:
            grpd = acc[0]
        else:
            grpd = "Missing Group Record"
        if self.rtype == "Q":
            self.tipe = "Quantities"
        elif self.rtype == "V":
            self.tipe = "Values"
        else:
            self.tipe = "Profits"
        self.fpdf.drawText("%s %s %s    %s %s    %s" % \
            ("Group:", self.grp.disp, grpd, "Location:", self.locd, self.tipe))
        self.fpdf.drawText()
        self.fpdf.drawText("%-3s %-20s %-30s %-10s %s" % \
            ("Grp", "Stock-Code", "Description", "U.O.I.", self.mthhead))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def getGroup(self, grp):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            grp)], limit=1)
        return acc

    def groupTotal(self):
        purchd = ""
        mchart = ["T", "Group %s Totals" % self.lstgrp]
        p = None
        for x in range(11,-1,-1):
            a = CCD(self.stots[x], "SI", 10)
            self.stots[x] = 0
            purchd = purchd + a.disp
            mchart.append(a.work)
            if a.work:
                p = "y"
        if p:
            self.mchart.append(mchart)
            self.fpdf.drawText()
            self.fpdf.drawText("%-24s %-41s %s" % (" ", mchart[1], purchd))
            self.pageHeading()

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL",
                ["", "", "Grand Totals", ""] + self.gtots])
            self.expdatas.append(["ULINED"])
            return
        purchd = ""
        mchart = ["T", "Grand Totals"]
        for x in range(11,-1,-1):
            a = CCD(self.gtots[x], "SI", 10)
            purchd = purchd + a.disp
            mchart.append(a.work)
        self.mchart.append(mchart)
        self.fpdf.drawText()
        self.fpdf.drawText("%-24s %-41s %s" % (" ", mchart[1], purchd))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
