"""
SYNOPSIS
    Sales By Customer By Product Report.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getModName, doPrinter, showError

class si3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsact", "drstyp", "drsmst",
            "strmf1", "strtrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.fromad = slsctl["ctv_emadd"]
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.chains = drsctl["ctd_chain"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Cust/Product Sales Report (%s)" % self.__class__.__name__)
        chm = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Chn"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": (("chm_cono", "=", self.opts["conum"]),)}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y")),
            "order": "drm_acno"}
        if self.chains == "Y":
            drm["where"] = [("drm_cono", "=", self.opts["conum"])]
            drm["whera"] = [["T", "drm_chain", 2]]
        else:
            drm["where"] = [("drm_cono", "=", self.opts["conum"])]
        dra = {
            "stype": "R",
            "tables": ("drsact",),
            "cols": (
                ("dac_code", "", 0, "Cod"),
                ("dac_desc", "", 0, "Description", "Y"))}
        drt = {
            "stype": "R",
            "tables": ("drstyp",),
            "cols": (
                ("dtp_code", "", 0, "Cod"),
                ("dtp_desc", "", 0, "Description", "Y"))}
        r1s = (("Yes","Y"),("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", "", "", "", "", "Y"]
            view = ("N","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID2",7,"Start Period","",
                int(self.sysdtw / 100),"Y",self.doSdate,None,None,("efld",)),
            (("T",0,1,0),"ID2",7,"End Period","",
                int(self.sysdtw / 100),"N",self.doEdate,None,None,("efld",)),
            (("T",0,2,0),"IUI",3,"Chain Store","",
                var[2],"N",self.doDrsChn,chm,None,None),
            (("T",0,3,0),"INA",7,"Account Number","",
                var[3],"N",self.doDrsAcc,drm,None,None),
            (("T",0,4,0),"IUA",3,"Business Activity","",
                var[4],"N",self.doDrsAct,dra,None,None),
            (("T",0,5,0),"IUA",3,"Business Type","",
                var[5],"N",self.doDrsTyp,drt,None,None),
            (("T",0,6,0),("IRB",r1s),0,"Sales Value Only","",
                var[6],"N",self.doVals,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doSdate(self, frt, pag, r, c, p, i, w):
        self.sdate = w

    def doEdate(self, frt, pag, r, c, p, i, w):
        self.edate = w
        if self.chains == "N":
            self.chain = 0
            return "sk1"

    def doDrsChn(self, frt, pag, r, c, p, i, w):
        self.chain = w

    def doDrsAcc(self, frt, pag, r, c, p, i, w):
        self.acno = w
        if self.chain or self.acno:
            self.drsact = ""
            self.drstyp = ""
            return "sk2"

    def doDrsAct(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drsact", where=[("dac_code", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Account Activity"
        self.drsact = w

    def doDrsTyp(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drstyp", where=[("dtp_code", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Account Activity"
        self.drstyp = w

    def doVals(self, frt, pag, r, c, p, i, w):
        self.vals = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["strmf1", "strtrn"]
        col = ["stt_group", "stt_code", "stt_loc", "stt_type", "stt_ref1",
            "stt_ref2", "stt_trdt", "stt_desc", "stt_chain", "stt_acno",
            "round(sum(stt_qty),2)", "round(sum(stt_cost),2)",
            "round(sum(stt_sell),2)", "st1_desc"]
        whr = [
            ("stt_cono", "=", self.opts["conum"]),
            ("stt_type", "in", (7, 8)),
            ("stt_cono=st1_cono",),
            ("stt_group=st1_group",),
            ("stt_code=st1_code",),
            ("stt_curdt", ">=", self.sdate),
            ("stt_curdt", "<=", self.edate)]
        if self.chain:
            whr.append(("stt_chain", "=", self.chain))
        if self.acno:
            whr.append(("stt_acno", "=", self.acno))
        if self.drsact or self.drstyp:
            tab.append("drsmst")
            whr.extend([
                ("stt_chain=drm_chain",),
                ("stt_acno=drm_acno",)])
            if self.drsact:
                whr.append(("drm_bus_activity", "=", self.drsact))
            if self.drstyp:
                whr.append(("drm_bus_type", "=", self.drstyp))
        grp = "stt_group, stt_code, stt_loc, stt_type, stt_ref1, stt_ref2, "\
            "stt_trdt, stt_desc, stt_chain, stt_acno, st1_desc"
        odr = "stt_chain, stt_acno, stt_type, stt_ref1, stt_group, stt_code"
        recs = self.sql.getRec(tables=tab, cols=col, where=whr, group=grp,
            order=odr)
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
        if self.vals == "Y":
            spc = " " * 67
        else:
            spc = " " * 99
        self.head = "%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], spc)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.dtot = [0] * 3
        self.gtot = [0] * 3
        old_chn = recs[0][8]
        old_drs = recs[0][9]
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.chn = CCD(dat[8], "UI", 3)
            self.drs = CCD(dat[9], "UA", 7)
            self.grp = CCD(dat[0], "NA", 3)
            self.cod = CCD(dat[1], "NA", 20)
            rf1 = CCD(dat[4], "Na", 9)
            rf2 = CCD(dat[5], "Na", 9)
            qty = CCD(float(ASD(0) - ASD(dat[10])), "SD", 11.2)
            cst = CCD(float(ASD(0) - ASD(dat[11])), "SD", 11.2)
            sll = CCD(float(ASD(0) - ASD(dat[12])), "SD", 11.2)
            des = CCD(dat[13], "NA", 30)
            prf = float(ASD(sll.work) - ASD(cst.work))
            prf = CCD(prf, "SD", 11.2)
            if sll.work == 0:
                pcn = 0
            else:
                pcn = round((prf.work * 100.0 / sll.work), 2)
            pcn = CCD(pcn, "SD", 7.2)
            if old_chn != self.chn.work or old_drs != self.drs.work:
                self.drsTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            if self.vals == "Y":
                self.fpdf.drawText("%s %s %s %s %s %s %s %s" % \
                    (rf1.disp, "Sls", rf2.disp, self.grp.disp,
                    self.cod.disp, des.disp, qty.disp, sll.disp))
            else:
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s" % \
                    (rf1.disp, "Sls", rf2.disp, self.grp.disp,
                    self.cod.disp, des.disp, qty.disp, sll.disp,
                    cst.disp, prf.disp, pcn.disp))
            self.pglin += 1
            self.dtot[0] = float(ASD(self.dtot[0]) + ASD(cst.work))
            self.dtot[1] = float(ASD(self.dtot[1]) + ASD(sll.work))
            self.gtot[0] = float(ASD(self.gtot[0]) + ASD(cst.work))
            self.gtot[1] = float(ASD(self.gtot[1]) + ASD(sll.work))
            old_chn = self.chn.work
            old_drs = self.drs.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.drsTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-30s %-10s" % \
            ("Sales By Customer Report as at", self.sysdtd))
        self.fpdf.drawText()
        if not self.drsact:
            act = "All"
        else:
            act = self.drsact
        if not self.drstyp:
            typ = "All"
        else:
            typ = self.drstyp
        self.fpdf.drawText(
            "%24s%7s%3s%12s%7s%3s%10s%3s%3s%6s%3s%3s%13s%1s%1s" %
            ("(Options: Start Period: ", self.df.t_disp[0][0][0], "",
            "End Period: ", self.df.t_disp[0][0][1], "",
            "Activity: ", act, "",
            "Type: ", typ, "",
            "Values Only: ", self.vals, ")"))
        self.fpdf.drawText()
        drn = self.sql.getRec("drsmst", cols=["drm_name"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            self.chn.work), ("drm_acno", "=", self.drs.work)], limit=1)
        if drn:
            drsn = drn[0]
        else:
            drsn = ""
        self.fpdf.drawText("%s %s    %s %s    %s %s" % ("Chain:",
            self.chn.disp, "Acc-Num:", self.drs.disp, "Name:", drsn))
        self.fpdf.drawText()
        if self.vals == "Y":
            self.fpdf.drawText("%-9s %-3s %-9s %-3s %-20s %-30s%11s %11s" % \
                ("Reference", "Typ", "Ref-Num-2", "Grp", "Product-Code",
                "Description", "Quantity", "Sell-Value"))
        else:
            self.fpdf.drawText("%-9s %-3s %-9s %-3s %-20s %-30s%11s %11s "\
                "%11s %11s %7s" % ("Reference", "Typ", "Ref-Num-2", "Grp",
                "Product-Code", "Description", "Quantity", "Sell-Value",
                "Cost-Value", "Profit", "Prf-%"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 10

    def drsTotal(self):
        cst = CCD(self.dtot[0], "SD", 12.2)
        sll = CCD(self.dtot[1], "SD", 12.2)
        prf = float(ASD(sll.work) - ASD(cst.work))
        prf = CCD(prf, "SD", 11.2)
        if sll.work == 0:
            pcn = 0
        else:
            pcn = round((prf.work * 100.0 / sll.work), 2)
        pcn = CCD(pcn, "SD", 7.2)
        self.fpdf.underLine(txt=self.head)
        if self.vals == "Y":
            self.fpdf.drawText("%-48s %-41s %s" % (" ",
                "Customer Totals", sll.disp))
        else:
            self.fpdf.drawText("%-48s %-41s %s%s %s %s" % (" ",
                "Customer Totals", sll.disp, cst.disp, prf.disp, pcn.disp))
        self.fpdf.drawText()
        self.dtot = [0] * 2

    def grandTotal(self):
        cst = CCD(self.gtot[0], "SD", 12.2)
        sll = CCD(self.gtot[1], "SD", 12.2)
        prf = float(ASD(sll.work) - ASD(cst.work))
        prf = CCD(prf, "SD", 11.2)
        if sll.work == 0:
            pcn = 0
        else:
            pcn = round((prf.work * 100.0 / sll.work), 2)
        pcn = CCD(pcn, "SD", 7.2)
        if self.vals == "Y":
            self.fpdf.drawText("%-48s %-41s %s" % \
            (" ", "Grand Totals", sll.disp))
        else:
            self.fpdf.drawText("%-48s %-41s %s%s %s %s" % \
            (" ", "Grand Totals", sll.disp, cst.disp, prf.disp, pcn.disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
