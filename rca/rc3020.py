"""
SYNOPSIS
    Rental Tenants Transaction Audit Trail.

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
from tartanFunctions import doPrinter, getModName, showError
from tartanWork import rttrtp, rcmvtp

class rc3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcatnt", "rcatnm"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.fromad = rcactl["cte_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        self.totind = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Rental Tenants Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in rttrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("rcatnt",),
            "cols": (
                ("rtu_batch", "", 0, "Bat-Num"),
                ("rtu_type", ("xx", rttrtp), 20, "Type"),
                ("rtu_curdt", "", 0, "Cur-Dat")),
            "where": [],
            "group": "rtu_batch, rtu_type, rtu_curdt",
            "order": "rtu_type, rtu_curdt, rtu_batch"}
        r1s = (("Financial","F"),("Capture","C"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Period Type","",
                "F","Y",self.doPtyp,None,None,None),
            (("T",0,1,0),"Id2",7,"Starting Period","",
                self.curdt,"Y",self.doStartPer,None,None,("efld",)),
            (("T",0,2,0),"Id2",7,"Ending Period","",
                self.curdt,"Y",self.doEndPer,None,None,("efld",)),
            (("T",0,3,0),"Id1",10,"Starting Date","",
                self.sysdtw,"Y",self.doStartDat,None,None,("efld",)),
            (("T",0,4,0),"Id1",10,"Ending Date","",
                self.sysdtw,"Y",self.doEndDat,None,None,("efld",)),
            (("T",0,5,0),"IUI",1,"Type","Transaction Type",
                "","Y",self.doBatTyp,btt,None,None),
            (("T",0,6,0),"INa",7,"Batch Number","",
                "","Y",self.doBatNum,btm,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Totals Only","",
                "Y","Y",self.doTots,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doPtyp(self, frt, pag, r, c, p, i, w):
        self.ptyp = w
        if self.ptyp == "C":
            return "sk2"

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if w > self.curdt:
            return "Invalid Period, After To-Day"
        else:
            self.sperw = w
        self.df.loadEntry(frt, pag, p, data=self.sperw)
        self.sperd = self.df.t_disp[pag][0][i]
        self.df.topf[pag][i+1][5] = self.sperw

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            self.eperw = self.sperw
        elif w < self.sperw:
            return "Invalid Period, Before Start"
        else:
            self.eperw = w
        self.df.loadEntry(frt, pag, p, self.eperw)
        self.eperd = self.df.t_disp[pag][0][i]
        return "sk2"

    def doStartDat(self, frt, pag, r, c, p, i, w):
        if w > self.sysdtw:
            return "Invalid Date, After To-Day"
        else:
            self.sdatw = w
        self.df.topf[pag][i+1][5] = self.sdatw
        self.sperd = self.df.t_disp[pag][0][i]

    def doEndDat(self, frt, pag, r, c, p, i, w):
        if w == 0:
            self.edatw = self.sdatw
        elif w < self.sdatw:
            return "Invalid Date, Before Start"
        else:
            self.edatw = w
        self.df.loadEntry(frt, pag, p, self.edatw)
        self.eperd = self.df.t_disp[pag][0][i]

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(rttrtp):
            return "Invalid Batch Type"
        self.btyp = w
        self.whr = [("rtu_cono", "=", self.opts["conum"])]
        if self.ptyp == "F":
            self.whr.append(("rtu_curdt", "between", self.sperw, self.eperw))
        else:
            self.whr.append(("rtu_capdt", "between", self.sdatw, self.edatw))
        if self.btyp:
            self.whr.append(("rtu_type", "=", w))
        self.df.topf[pag][i+1][8]["where"] = self.whr

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w

    def doEnd(self):
        self.df.closeProcess()
        jon = "left outer join rcatnm on rtu_cono=rtn_cono and "\
            "rtu_owner=rtn_owner and rtu_code=rtn_code and rtu_acno=rtn_acno"
        self.col = ["rtu_owner", "rtu_code", "rtu_acno", "rtu_type",
            "rtu_batch", "rtu_refno", "rtu_trdt", "rtu_desc", "rtu_mtyp",
            "rtu_tramt", "rtu_taxamt", "rtu_taxind", "rtn_name"]
        odr = "rtu_type, rtu_batch, rtu_trdt, rtu_refno"
        recs = self.sql.getRec("rcatnt", join=jon, cols=self.col,
            where=self.whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.totsonly == "Y":
            self.head = "%03u %-71s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-136s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bqty = 0
        self.bamt = 0
        self.bdis = 0
        self.bvat = 0
        self.tqty = 0
        self.tamt = 0
        self.tdis = 0
        self.tvat = 0
        self.gqt = [0] * (len(rttrtp) + 1)
        self.gam = [0] * (len(rttrtp) + 1)
        self.gvt = [0] * (len(rttrtp) + 1)
        self.trtp = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            owner = CCD(dat[self.col.index("rtu_owner")], "NA", 7)
            code = CCD(dat[self.col.index("rtu_code")], "NA", 7)
            acno = CCD(dat[self.col.index("rtu_acno")], "NA", 7)
            name = CCD(dat[self.col.index("rtn_name")], "NA", 30)
            trtp = CCD(dat[self.col.index("rtu_type")], "UI", 2)
            batch = CCD(dat[self.col.index("rtu_batch")], "Na", 7)
            refno = CCD(dat[self.col.index("rtu_refno")], "Na", 9)
            trdt = CCD(dat[self.col.index("rtu_trdt")], "D1", 10)
            desc = CCD(dat[self.col.index("rtu_desc")], "NA", 30)
            mtyp = CCD(dat[self.col.index("rtu_mtyp")], "UI", 1)
            tramt = CCD(dat[self.col.index("rtu_tramt")], "SD", 13.2)
            taxamt = CCD(dat[self.col.index("rtu_taxamt")], "SD", 13.2)
            taxind = CCD(dat[self.col.index("rtu_taxind")], "NA", 1)
            if not self.trtp:
                self.trtp = trtp.work
                self.batch = batch.work
            if trtp.work != self.trtp:
                self.batchTotal()
                self.typeTotal()
                self.trtp = trtp.work
                self.batch = batch.work
                self.pglin = 999
            if batch.work != self.batch:
                self.batchTotal()
                self.batch = batch.work
                if self.totsonly != "Y":
                    self.typeHeading()
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            if self.totsonly != "Y":
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s" % \
                    (owner.disp, code.disp, acno.disp, refno.disp, trdt.disp,
                    desc.disp, rcmvtp[mtyp.work-1][0], tramt.disp, taxamt.disp,
                    taxind.disp, name.disp))
                self.pglin += 1
            self.bqty = self.bqty + 1
            self.bamt = float(ASD(self.bamt) + ASD(tramt.work))
            self.bvat = float(ASD(self.bvat) + ASD(taxamt.work))
            self.tqty = self.tqty + 1
            self.tamt = float(ASD(self.tamt) + ASD(tramt.work))
            self.tvat = float(ASD(self.tvat) + ASD(taxamt.work))
            self.gqt[trtp.work - 1] = self.gqt[trtp.work - 1] + 1
            self.gam[trtp.work - 1] = float(ASD(self.gam[trtp.work - 1]) + \
                ASD(tramt.work))
            self.gvt[trtp.work - 1] = float(ASD(self.gvt[trtp.work - 1]) + \
                ASD(taxamt.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.batchTotal()
            self.typeTotal()
            self.grandTotal()
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
        self.fpdf.drawText("Rental Tenants Audit Trail for Period "\
            "%s to %s" % (self.sperd, self.eperd))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            if self.totsonly == "Y":
                self.fpdf.drawText(
                "%-39s%-8s  %-13s %-13s" % ("Document Type", "Quantity",
                "      Amount", "      V.A.T."))
            else:
                self.fpdf.drawText(
                "%-26s%-8s  %-13s %-13s" % ("Document Type", "Quantity ",
                "      Amount", "      V.A.T."))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 4

    def typeHeading(self):
        if self.totsonly == "N":
            batch = self.batch
        else:
            batch = "Various"
        if self.fpdf.lpp - self.pglin < 7:
            self.pageHeading()
            return
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-7s %7s %-10s %3s" % \
            ("Batch", batch, "    Type", rttrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText(
                "%-48s %-13s %-13s" % \
                ("Details", "      Amount", "  Tax-Amount"))
        else:
            self.fpdf.drawText(
                "%-7s %-7s %-7s %-9s %-10s %-30s %-3s %-13s %-13s %-1s "\
                "%-30s" % ("Own-Cod", "Prm-Cod", "Acc-Num", "Reference",
                "   Date", "Remarks", "Mtp", "      Amount", "  Tax-Amount",
                "I", "Tenant"))
        self.fpdf.underLine(txt=self.head)
        self.pglin += 4
        self.fpdf.setFont()

    def batchTotal(self):
        j = CCD(self.bamt, "SD", 13.2)
        k = CCD(self.bvat, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-48s %13s %13s" % \
                ("Batch " + self.batch + " Totals", j.disp, k.disp))
        else:
            self.fpdf.drawText()
            self.pglin += 1
            self.fpdf.drawText("%-44s %-34s %13s %13s" % (" ",
                "Batch " + self.batch + " Totals", j.disp, k.disp))
        self.pglin += 1
        if self.totsonly != "Y":
            self.fpdf.drawText()
            self.pglin += 1
        self.bqty = 0
        self.bamt = 0
        self.bdis = 0
        self.bvat = 0

    def typeTotal(self):
        j = CCD(self.tamt, "SD", 13.2)
        k = CCD(self.tvat, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-48s %13s %13s" % \
                ("Type Totals", j.disp, k.disp))
            self.pglin += 2
        else:
            self.fpdf.drawText("%-44s %-34s %13s %13s" % \
            (" ", "Type-Totals", j.disp, k.disp))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        self.tqty = 0
        self.tamt = 0
        self.tdis = 0
        self.tvat = 0

    def grandTotal(self):
        self.totind = "Y"
        self.pageHeading()
        tot = [0,0,0,0]
        for x, t in enumerate(rttrtp):
            qt = CCD(self.gqt[x], "SI", 8)
            am = CCD(self.gam[x], "SD", 13.2)
            vt = CCD(self.gvt[x], "SD", 13.2)
            if self.totsonly == "Y":
                self.fpdf.drawText("%-39s %s %s %s" % \
                (t[1], qt.disp, am.disp, vt.disp))
            else:
                self.fpdf.drawText("%-26s %s %s %s" % \
                (t[1], qt.disp, am.disp, vt.disp))
            tot[0] = tot[0] + qt.work
            tot[1] = float(ASD(tot[1]) + ASD(am.work))
            tot[3] = float(ASD(tot[3]) + ASD(vt.work))
        self.fpdf.drawText()
        qt = CCD(tot[0], "SI", 8)
        am = CCD(tot[1], "SD", 13.2)
        vt = CCD(tot[3], "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-39s %s %s %s" % \
            ("Grand Totals", qt.disp, am.disp, vt.disp))
        else:
            self.fpdf.drawText("%-26s %s %s %s" % \
            ("Grand Totals", qt.disp, am.disp, vt.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
