"""
SYNOPSIS
    Bookings Manager Transaction Audit Trail.

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
from tartanFunctions import doWriteExport, getModName, doPrinter, showError
from tartanWork import bktrtp

class bk3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.sper = int(self.opts["period"][1][0] / 100)
            self.eper = int(self.opts["period"][2][0] / 100)
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Bookings Manager Audit Trail (%s)" % self.__class__.__name__)
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "bkmmst", "bkmtrn",
            "bkmcon"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.fromad = bkmctl["cbk_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], "%s"))
        self.colsh = ["TP", "BatchNo", "Book-Num", "Name", "Reference",
            "Date", "Debits", "Credits", "Tax-Amount", "T", "Remarks"]
        self.forms = [("UI", 2, False, False, True), ("Na", 7),
            ("NA", 8, False, False, True), ("NA", 30), ("Na", 9), ("D1", 10),
            ("SD", 13.2), ("SD", 13.2), ("SD", 13.2), ("UA", 1), ("NA", 30)]
        self.gqt = [0] * (len(bktrtp) + 1)
        self.gdr = [0] * (len(bktrtp) + 1)
        self.gcr = [0] * (len(bktrtp) + 1)
        self.gvt = [0] * (len(bktrtp) + 1)
        self.totind = "N"
        return True

    def mainProcess(self):
        data = ["All Types"]
        for typ in bktrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("bkmtrn",),
            "cols": (
                ("bkt_batch", "", 0, "Bat-Num"),
                ("bkt_type", ("xx", bktrtp), 20, "Type"),
                ("bkt_curdt", "", 0, "Cur-Dat")),
            "where": [],
            "group": "bkt_batch, bkt_type, bkt_curdt",
            "order": "bkt_type, bkt_curdt, bkt_batch"}
        r1s = (("Financial","F"),("Capture","C"))
        r2s = (("Yes","Y"),("No","N"))
        fld = [
            (("T",0,0,0),("IRB",r1s),0,"Period Type","",
                "F","Y",self.doPtyp,None,None,None),
            (("T",0,1,0),"Id2",7,"Starting Period","",
                self.sper,"Y",self.doStartPer,None,None,("efld",)),
            (("T",0,2,0),"Id2",7,"Ending Period","",
                self.eper,"Y",self.doEndPer,None,None,("efld",)),
            (("T",0,3,0),"Id1",10,"Starting Date","",
                self.sysdtw,"Y",self.doStartDat,None,None,("efld",)),
            (("T",0,4,0),"Id1",10,"Ending Date","",
                self.sysdtw,"Y",self.doEndDat,None,None,("efld",)),
            (("T",0,5,0),"IUI",1,"Type","Transaction Type",
                "","Y",self.doBatTyp,btt,None,None),
            (("T",0,6,0),"INa",7,"Batch Number","",
                "","Y",self.doBatNum,btm,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Totals Only","",
                "Y","Y",self.doTots,None,None,None)]
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doPtyp(self, frt, pag, r, c, p, i, w):
        self.ptyp = w
        if self.ptyp == "C":
            return "sk2"

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.sper
        elif w < self.sper or w > self.eper:
            return "Invalid Period"
        self.sperw = w
        self.df.loadEntry(frt, pag, p, data=self.sperw)
        self.sperd = self.df.t_disp[pag][0][i]

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.eper
        elif w < self.sperw or w > self.eper:
            return "Invalid Period"
        self.eperw = w
        self.df.loadEntry(frt, pag, p, self.eperw)
        self.eperd = self.df.t_disp[pag][0][i]
        return "sk2"

    def doStartDat(self, frt, pag, r, c, p, i, w):
        self.sdatw = w
        self.df.loadEntry(frt, pag, p, data=self.sdatw)
        self.sperd = self.df.t_disp[pag][0][i]

    def doEndDat(self, frt, pag, r, c, p, i, w):
        if w < self.sdatw:
            return "Invalid Date"
        self.edatw = w
        self.df.loadEntry(frt, pag, p, self.edatw)
        self.eperd = self.df.t_disp[pag][0][i]

    def doBatTyp(self, frt, pag, r, c, p, i, w):
        if w > len(bktrtp):
            return "Invalid Batch Type"
        self.btyp = w
        self.whr = [("bkt_cono", "=", self.opts["conum"])]
        if self.ptyp == "F":
            self.whr.append(("bkt_curdt", "between", self.sperw, self.eperw))
        else:
            self.whr.append(("bkt_capdt", "between", self.sdatw, self.edatw))
        if self.btyp:
            self.whr.append(("bkt_type", "=", self.btyp))
        self.df.topf[pag][i+1][8]["where"] = self.whr

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w
        if self.batch:
            self.whr.append(("bkt_batch", "=", self.batch))

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        mx = len(self.df.topEntry[0][8])
        if self.totsonly == "Y":
            if mx > 3:
                self.df.setWidget(self.df.topEntry[0][8][3][0], state="hide")
            if mx > 4:
                self.df.setWidget(self.df.topEntry[0][8][4][0], state="hide")
        else:
            if mx > 3:
                self.df.setWidget(self.df.topEntry[0][8][3][0], state="show")
            if mx > 4:
                self.df.setWidget(self.df.topEntry[0][8][4][0], state="show")

    def doEnd(self):
        self.df.closeProcess()
        recs = self.getRecords()
        if recs:
            if self.df.repprt[2] == "export":
                self.exportReport(recs)
            else:
                self.printReport(recs)
        self.closeProcess()

    def getRecords(self):
        col = ["bkt_number", "bkt_date", "bkt_type", "bkt_refno", "bkt_batch",
            "bkt_tramt", "bkt_taxamt", "bkt_desc", "bkt_taxind", "bkc_sname",
            "bkc_names"]
        self.whr.extend([("bkm_cono=bkt_cono",), ("bkm_number=bkt_number",),
            ("bkc_cono=bkt_cono",), ("bkc_ccode=bkm_ccode",)])
        odr = "bkt_type, bkt_batch, bkt_date, bkt_refno"
        recs = self.sql.getRec(tables=["bkmtrn", "bkmmst", "bkmcon"], cols=col,
            where=self.whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
                "No Transactions Selected")
        else:
            return recs

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("Bookings Manager Audit Trail for Period "\
            "%s to %s" % (self.sperd, self.eperd))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            bkmno, trdt, trtp, refno, batch, debit, credit, taxamt, \
                detail, taxind, name = self.getValues(dat)
            line = ["BODY", [trtp.work, batch.work, bkmno.work, name.work,
                refno.work, trdt.work, debit.work, credit.work, taxamt.work,
                taxind.work, detail.work]]
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.totsonly == "Y":
            self.head = ("%03u %-30s %49s %6s" % (self.opts["conum"],
                self.opts["conam"], self.sysdttm, self.__class__.__name__))
        else:
            self.head = ("%03u %-30s %91s %10s" % (self.opts["conum"],
                self.opts["conam"], self.sysdttm, self.__class__.__name__))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bqty = 0
        self.bdrs = 0
        self.bcrs = 0
        self.bvat = 0
        self.tqty = 0
        self.tdrs = 0
        self.tcrs = 0
        self.tvat = 0
        self.trtp = 0
        self.pgnum = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            bkmno, trdt, trtp, refno, batch, debit, credit, taxamt, \
                detail, taxind, name = self.getValues(dat)
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
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % (bkmno.disp,
                    name.disp, refno.disp, trdt.disp, debit.disp, credit.disp,
                    taxamt.disp, taxind.disp, detail.disp))
                self.pglin += 1
            # Batch Totals
            self.bqty += 1
            self.bdrs = float(ASD(self.bdrs) + ASD(debit.work))
            self.bcrs = float(ASD(self.bcrs) + ASD(credit.work))
            self.bvat = float(ASD(self.bvat) + ASD(taxamt.work))
            # Type Totals
            self.tqty += 1
            self.tdrs = float(ASD(self.tdrs) + ASD(debit.work))
            self.tcrs = float(ASD(self.tcrs) + ASD(credit.work))
            self.tvat = float(ASD(self.tvat) + ASD(taxamt.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.batchTotal()
            self.typeTotal()
            self.grandTotal()
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        bkmno = CCD(data[0], "UI", 7)
        trdt = CCD(data[1], "D1", 10)
        trtp = CCD(data[2], "UI", 2)
        refno = CCD(data[3], "Na", 9)
        batch = CCD(data[4], "Na", 7)
        if data[5] < 0:
            debit = CCD(0, "SD", 13.2)
            credit = CCD(data[5], "SD", 13.2)
        else:
            debit = CCD(data[5], "SD", 13.2)
            credit = CCD(0, "SD", 13.2)
        taxamt = CCD(data[6], "SD", 13.2)
        detail = CCD(data[7], "NA", 30)
        taxind = CCD(data[8], "NA", 1)
        name = CCD("%s, %s" % (data[9], data[10]), "NA", 30)
        self.gqt[trtp.work - 1] += 1
        self.gdr[trtp.work - 1] = float(ASD(self.gdr[trtp.work - 1]) + \
            ASD(debit.work))
        self.gcr[trtp.work - 1] = float(ASD(self.gcr[trtp.work - 1]) + \
            ASD(credit.work))
        self.gvt[trtp.work - 1] = float(ASD(self.gvt[trtp.work - 1]) + \
            ASD(taxamt.work))
        return (bkmno, trdt, trtp, refno, batch, debit, credit, taxamt,
            detail, taxind, name)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-38s %-10s %-2s %-10s %20s %5s" % \
                ("Bookings Manager Audit Trail for Period",
                self.sperd, "to", self.eperd, "Page", self.pgnum))
        else:
            self.fpdf.drawText("%-38s %-10s %-2s %-10s %66s %5s" % \
                ("Bookings Manager Audit Trail for Period",
                self.sperd, "to", self.eperd, "Page", self.pgnum))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            if self.totsonly == "Y":
                self.fpdf.drawText("%-27s%-8s  %-13s %-13s %-13s %-13s" % \
                    ("Document Type", "Quantity", "      Debits",
                    "     Credits", "  Difference", "      V.A.T."))
            else:
                self.fpdf.drawText("%-33s%-8s  %-13s %-13s %-13s %-13s" % \
                    ("Document Type", "Quantity", "      Debits",
                    "     Credits", "  Difference", "      V.A.T."))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 4

    def typeHeading(self):
        if self.totsonly != "Y":
            batch = self.batch
        else:
            batch = "Various"
        if self.fpdf.lpp - self.pglin < 7:
            self.pageHeading()
            return
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-7s %7s %-10s %3s" % \
            ("Batch", batch, "    Type", bktrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-36s %-13s %-13s %-13s %-13s" % \
                ("Details", "      Debits", "     Credits", "  Difference",
                "      V.A.T."))
        else:
            self.fpdf.drawText("%-7s %-30s %-9s %-10s %-13s %-13s %-13s "\
                "%-1s %-30s" % ("Booking", "Name", "Reference",
                "   Date", "      Debits", "     Credits", "  Tax-Amount",
                "T", "Remarks"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        j = CCD(self.bdrs, "SD", 13.2)
        k = CCD(self.bcrs, "SD", 13.2)
        l = CCD(float(ASD(j.work) + ASD(k.work)), "SD", 13.2)
        m = CCD(self.bvat, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-36s %13s %13s %13s %13s" % \
                ("Batch " + self.batch + " Totals", j.disp,
                k.disp, l.disp, m.disp))
            self.pglin += 1
        else:
            self.fpdf.drawText()
            self.fpdf.drawText("%-7s %-51s %13s %13s %13s" % (" ",
                "Batch " + self.batch + " Totals", j.disp, k.disp, m.disp))
            self.fpdf.drawText()
            self.pglin += 3
        self.bqty = 0
        self.bcrs = 0
        self.bdrs = 0
        self.bvat = 0

    def typeTotal(self):
        j = CCD(self.tdrs, "SD", 13.2)
        k = CCD(self.tcrs, "SD", 13.2)
        l = CCD(float(ASD(j.work) + ASD(k.work)), "SD", 13.2)
        m = CCD(self.tvat, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-36s %13s %13s %13s %13s" % \
                ("Type Totals", j.disp, k.disp, l.disp, m.disp))
            self.pglin += 2
        else:
            self.fpdf.drawText("%-7s %-51s %13s %13s %13s" % \
            (" ", "Type-Totals", j.disp, k.disp, m.disp))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        self.tqty = 0
        self.tcrs = 0
        self.tdrs = 0
        self.tvat = 0

    def grandTotal(self):
        tot = [0, 0, 0, 0, 0]
        if self.df.repprt[2] == "export":
            for x, t in enumerate(bktrtp):
                tot[0] = float(ASD(tot[0]) + ASD(self.gdr[x]))
                tot[1] = float(ASD(tot[1]) + ASD(self.gcr[x]))
                tot[2] = float(ASD(tot[2]) + ASD(self.gvt[x]))
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "", "", "Grand Totals", "",
                "", tot[0], tot[1], tot[2], ""]])
            self.expdatas.append(["ULINED"])
            return
        self.totind = "Y"
        self.pageHeading()
        for x, t in enumerate(bktrtp):
            qt = CCD(self.gqt[x], "SI", 8)
            dr = CCD(self.gdr[x], "SD", 13.2)
            cr = CCD(self.gcr[x], "SD", 13.2)
            df = float(ASD(dr.work) + ASD(cr.work))
            df = CCD(df, "SD", 13.2)
            vt = CCD(self.gvt[x], "SD", 13.2)
            if self.totsonly == "Y":
                self.fpdf.drawText("%-27s %s %s %s %s %s" % \
                (t[1], qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
            else:
                self.fpdf.drawText("%-33s %s %s %s %s %s" % \
                (t[1], qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
            tot[0] = tot[0] + qt.work
            tot[1] = float(ASD(tot[1]) + ASD(dr.work))
            tot[2] = float(ASD(tot[2]) + ASD(cr.work))
            tot[3] = float(ASD(tot[3]) + ASD(df.work))
            tot[4] = float(ASD(tot[4]) + ASD(vt.work))
        self.fpdf.drawText()
        qt = CCD(tot[0], "SI", 8)
        dr = CCD(tot[1], "SD", 13.2)
        cr = CCD(tot[2], "SD", 13.2)
        df = CCD(tot[3], "SD", 13.2)
        vt = CCD(tot[4], "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-27s %s %s %s %s %s" % \
            ("Grand Totals", qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
        else:
            self.fpdf.drawText("%-33s %s %s %s %s %s" % \
            ("Grand Totals", qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
