"""
SYNOPSIS
    Purchase Orders Report.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError

class st3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "strloc", "strpom",
            "strpot"], prog=self.__class__.__name__)
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
        self.maxlines = 20
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Purchase Orders (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        self.orm = {
            "stype": "R",
            "tables": ("strpom",),
            "cols": (
                ("pom_ordno", "", 0, "OrderNo"),
                ("pom_acno", "", 0, "Crs-Num"),
                ("pom_date", "", 0, "Order-Date")),
            "where": []}
        r1s = (("Yes", "Y"), ("No", "N"))
        r2s = (("List", "L"), ("Detail", "D"))
        if self.locs == "N":
            fld = [
            (("T",0,0,0),"OUA",1,"Location","",
                "1","Y",self.doLoc,loc,None,None)]
        else:
            fld = [
            (("T",0,0,0),"IUA",1,"Location","",
                "","Y",self.doLoc,loc,None,None)]
        fld.extend([
            (("T",0,1,0),("IRB",r1s),0,"Oustanding Only","",
                "Y","Y",self.doOut,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Report Type","",
                "L","Y",self.doTyp,None,None,None),
            (("T",0,3,0),"IUI",9,"From Order Number","",
                "","Y",self.doOrd1,self.orm,None,None),
            (("T",0,4,0),"IUI",9,"To   Order Number","",
                "","Y",self.doOrd2,self.orm,None,None)])
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doLoc(self, frt, pag, r, c, p, i, w):
        self.locw = w
        if not w:
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]),
                ("srl_loc", "=", w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.locd = self.locw

    def doOut(self, frt, pag, r, c, p, i, w):
        self.outs = w
        if self.outs == "Y":
            self.orm["where"] = [
                ("pom_cono", "=", self.opts["conum"]),
                ("pom_delno", "=", "")]
        else:
            self.orm["where"] = [
                ("pom_cono", "=", self.opts["conum"])]

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.rtyp = w

    def doOrd1(self, frt, pag, r, c, p, i, w):
        self.ord1 = w

    def doOrd2(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.ord1:
                return "Invalid Last Order < First Order"
            self.ord2 = w
        else:
            self.ord2 = 999999999

    def doEnd(self):
        self.df.closeProcess()
        whr = [("pom_cono", "=", self.opts["conum"])]
        if self.locw:
            whr.append(("pom_loc", "=", self.locw))
        if self.outs == "Y":
            whr.append(("pom_delno", "=", ""))
        else:
            whr.append(("pom_delno", "<>", "cancel"))
        whr.extend([("pom_ordno", ">=", self.ord1),
            ("pom_ordno", "<=", self.ord2)])
        recs = self.sql.getRec("strpom", cols=["pom_ordno", "pom_loc",
            "pom_date", "pom_acno", "pom_deldt"], where=whr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Orders Selected")
        else:
            self.printSetup(recs)
            if self.rtyp == "D":
                self.doDetail(recs)
            else:
                self.doList(recs)
            if self.fpdf.page and not self.p.quit:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def printSetup(self, recs):
        self.p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.rtyp == "D":
            self.head = "%03u %-85s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-107s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999

    def doDetail(self, recs):
        for num, dat in enumerate(recs):
            self.p.displayProgress(num)
            if self.p.quit:
                break
            self.odr = CCD(dat[0], "Na", 9)
            self.pot = self.sql.getRec("strpot", cols=["pot_group",
                "pot_code", "pot_uoi", "pot_desc", "pot_qty", "pot_price",
                "pot_disper"], where=[("pot_cono", "=", self.opts["conum"]),
                ("pot_ordno", "=", self.odr.work)],
                order="pot_group, pot_code")
            self.dto = CCD(dat[2], "d1", 10)
            self.crs = CCD(dat[3], "NA", 7)
            acc = self.sql.getRec("crsmst", cols=["crm_name"],
                where=[("crm_cono", "=", self.opts["conum"]), ("crm_acno", "=",
                self.crs.work)], limit=1)
            if not acc:
                self.nam = ""
            else:
                self.nam = acc[0]
            self.dte = CCD(dat[4], "d1", 10)
            self.printHeader()
            if self.pot:
                self.printBody()
            else:
                self.fpdf.drawText("No Products on Order - Please "\
                    "Amend or Cancel the Order")
        self.p.closeProgress()

    def doList(self, recs):
        for num, dat in enumerate(recs):
            self.p.displayProgress(num)
            if self.p.quit:
                break
            if self.pglin > self.fpdf.lpp:
                self.printHeader()
            odr = CCD(dat[0], "Na", 9)
            dto = CCD(dat[2], "d1", 10)
            crs = CCD(dat[3], "NA", 7)
            if dat[4]:
                dte = CCD(dat[4], "d1", 10)
            else:
                dte = CCD("", "NA", 10)
            acc = self.sql.getRec("crsmst", cols=["crm_name"],
                where=[("crm_cono", "=", self.opts["conum"]), ("crm_acno", "=",
                crs.work)], limit=1)
            if not acc:
                nam = CCD("", "NA", 30)
            else:
                nam = CCD(acc[0], "NA", 30)
            pots = self.sql.getRec("strpot", cols=["pot_qty",
                "pot_price", "pot_disper"], where=[("pot_cono", "=",
                self.opts["conum"]), ("pot_ordno", "=", odr.work)])
            prc = 0
            dis = 0
            val = 0
            for pot in pots:
                a = pot[0] * pot[1]
                b = a * pot[2] / 100.0
                prc = float(ASD(prc) + ASD(a))
                dis = float(ASD(dis) + ASD(b))
                val = float(ASD(val) + ASD(a) - ASD(b))
            prc = CCD(prc, "SD", 13.2)
            dis = CCD(dis, "SD", 13.2)
            val = CCD(val, "SD", 13.2)
            self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (odr.disp, crs.disp,
                nam.disp, dto.disp, dte.disp, prc.disp, dis.disp, val.disp))
            self.pglin += 1
        self.p.closeProgress()

    def printHeader(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.outs == "Y":
            txt = "%-39s %3s %-5s %-10s" % \
                ("Outstanding Orders Report for Location", self.locd, "as at",
                    self.sysdtd)
        else:
            txt = "%-27s %3s %-5s %-10s" % \
                ("Orders Report for Location", self.locd, "as at",
                    self.sysdtd)
        self.fpdf.drawText(txt)
        self.fpdf.drawText()
        if self.rtyp == "D":
            text = "Order Number: %-9s%20sSupplier: %-7s %-30s" % \
                (self.odr.disp, "", self.crs.disp, self.nam)
            self.fpdf.drawText(text)
            self.fpdf.drawText()
            text = "Date Ordered: %s%40sDate Received: %s" % \
                (self.dto.disp, "", self.dte.disp)
            self.fpdf.drawText(text)
            self.fpdf.drawText()
            self.fpdf.drawText("%-3s %-20s %-30s %-10s %11s %10s" % \
                ("Grp", "Product-Code", "Description", "U.O.I", "U-Price",
                "Qty-Ord"))
            self.pglin = 10
        else:
            self.fpdf.drawText("%-9s %-7s %-30s %10s %10s %13s %13s %13s" % \
                ("Order-Num", "Acc-Num", "Name", "Date-Order", "Date-Recvd",
                    "Gross-Value ", "Discount ", "Net-Value "))
            self.pglin = 6
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()

    def printBody(self):
        for dat in self.pot:
            grp = CCD(dat[0], "UA", 3)
            cod = CCD(dat[1], "NA", 20)
            uoi = CCD(dat[2], "NA", 10)
            des = CCD(dat[3], "NA", 30)
            qty = CCD(dat[4], "SD", 11.2)
            prc = CCD(dat[5], "UD", 11.2)
            if self.pglin > self.fpdf.lpp:
                self.printHeader()
            self.fpdf.drawText("%s %s %s %s %s %s" % (grp.disp, cod.disp,
                des.disp, uoi.disp, prc.disp, qty.disp))
            self.pglin += 1

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
