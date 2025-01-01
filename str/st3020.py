"""
SYNOPSIS
    Stores Ledger Transaction Audit Trail.

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
from tartanFunctions import doWriteExport, doPrinter, getModName, showError
from tartanWork import sttrtp

class st3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "strtrn",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.colsh = ["TP", "BatchNo", "Grp", "Product-Code", "L",
            "Reference", "Date", "Remarks", "Acc-Num", "Quantity",
            "Cost-Value", "Sale-Value"]
        self.forms = [("UI", 2, False, False, True), ("Na", 7), ("UA", 3),
            ("NA", 20), ("UA", 1), ("Na", 9), ("D1", 10), ("NA", 30),
            ("NA", 7), ("SD", 13.2), ("SD", 13.2), ("SD", 13.2)]
        self.curdt = int(self.sysdtw / 100)
        self.gcnt = [0] * (len(sttrtp) + 1)
        self.gqty = [0] * (len(sttrtp) + 1)
        self.gcst = [0] * (len(sttrtp) + 1)
        self.gsel = [0] * (len(sttrtp) + 1)
        self.totind = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Stores Ledger Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in sttrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("strtrn",),
            "cols": (
                ("stt_batch", "", 0, "Bat-Num"),
                ("stt_type", ("xx", sttrtp), 20, "Type"),
                ("stt_curdt", "", 0, "Cur-Dat")),
            "where": [],
            "group": "stt_batch, stt_type, stt_curdt",
            "order": "stt_type, stt_curdt, stt_batch"}
        r1s = (("Financial","F"),("Capture","C"))
        r2s = (("Yes","Y"),("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["F", "", "", "", "", "", "", "Y"]
            view = ("Y","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Period Type","",
                var[0],"Y",self.doPtyp,None,None,None),
            (("T",0,1,0),"Id2",7,"Starting Period","",
                self.curdt,"N",self.doStartPer,None,None,("efld",)),
            (("T",0,2,0),"Id2",7,"Ending Period","",
                self.curdt,"N",self.doEndPer,None,None,("efld",)),
            (("T",0,3,0),"Id1",10,"Starting Date","",
                self.sysdtw,"N",self.doStartDat,None,None,("efld",)),
            (("T",0,4,0),"Id1",10,"Ending Date","",
                self.sysdtw,"N",self.doEndDat,None,None,("efld",)),
            (("T",0,5,0),"IUI",1,"Type","Transaction Type",
                var[5],"N",self.doBatTyp,btt,None,None),
            (("T",0,6,0),"INa",7,"Batch Number","",
                var[6],"N",self.doBatNum,btm,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Totals Only","",
                var[7],"N",self.doTots,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

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
        self.sperd = self.df.t_disp[pag][0][i]
        self.df.topf[pag][i+1][5] = self.sdatw

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
        if w > len(sttrtp):
            return "Invalid Batch Type"
        self.whr = [("stt_cono", "=", self.opts["conum"])]
        if self.ptyp == "F":
            self.whr.append(("stt_curdt", "between", self.sperw, self.eperw))
        else:
            self.whr.append(("stt_capdt", "between", self.sdatw, self.edatw))
        if w:
            self.whr.append(("stt_type", "=", w))
        self.df.topf[pag][i+1][8]["where"] = self.whr

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w
        if self.batch:
            self.whr.append(("stt_batch", "=", self.batch))

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if "args" in self.opts and "noprint" in self.opts["args"]:
            return
        if self.totsonly == "Y":
            state = "hide"
        else:
            state = "show"
        for x in range(3, len(self.df.rvs)): 
            self.df.setWidget(self.df.topEntry[0][8][x][0], state=state)

    def doEnd(self):
        self.df.closeProcess()
        tab = "strtrn"
        odr = "stt_type, stt_batch, stt_trdt, stt_ref1"
        recs = self.sql.getRec(tables=tab, where=self.whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Stores Transactions Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = ["%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm)]
        self.expheads.append("Store's Ledger Audit Trail for Period "\
            "%s to %s" % (self.sperd, self.eperd))
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
            trtp, batch, grp, code, loc, ref1, trdt, desc, debtor, \
                qty, cost, sell = vals
            line = ["BODY", [trtp.work, batch.work, grp.work, code.work,
                loc.work, ref1.work, trdt.work, desc.work, debtor.work,
                qty.work, cost.work, sell.work]]
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.totsonly == "Y":
            self.head = "%03u %-75s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-123s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.bcnt = 0
        self.bqty = 0
        self.bcst = 0
        self.bsel = 0
        self.tcnt = 0
        self.tqty = 0
        self.tcst = 0
        self.tsel = 0
        self.trtp = 0
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            trtp, batch, grp, code, loc, ref1, trdt, desc, debtor, \
                qty, cost, sell = vals
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
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" % \
                    (grp.disp, code.disp, loc.disp, ref1.disp, trdt.disp,
                    desc.disp, debtor.disp, qty.disp, cost.disp, sell.disp))
                self.pglin += 1
            self.bcnt = self.bcnt + 1
            self.bqty = float(ASD(self.bqty) + ASD(qty.work))
            self.bcst = float(ASD(self.bcst) + ASD(cost.work))
            self.bsel = float(ASD(self.bsel) + ASD(sell.work))
            self.tcnt = self.tcnt + 1
            self.tqty = float(ASD(self.tqty) + ASD(qty.work))
            self.tcst = float(ASD(self.tcst) + ASD(cost.work))
            self.tsel = float(ASD(self.tsel) + ASD(sell.work))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.batchTotal()
            self.typeTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        col = self.sql.strtrn_col
        trtp = CCD(data[col.index("stt_type")], "UI", 2)
        batch = CCD(data[col.index("stt_batch")], "Na", 7)
        grp = CCD(data[col.index("stt_group")], "UA", 3)
        code = CCD(data[col.index("stt_code")], "NA", 20)
        loc = CCD(data[col.index("stt_loc")], "UA", 1)
        ref1 = CCD(data[col.index("stt_ref1")], "Na", 9)
        trdt = CCD(data[col.index("stt_trdt")], "D1", 10)
        desc = CCD(data[col.index("stt_desc")], "NA", 30)
        debtor = CCD(data[col.index("stt_acno")], "NA", 7)
        qty = CCD(data[col.index("stt_qty")], "SD", 13.2)
        cost = CCD(data[col.index("stt_cost")], "SD", 13.2)
        sell = CCD(data[col.index("stt_sell")], "SD", 13.2)
        self.gcnt[trtp.work - 1] = self.gcnt[trtp.work - 1] + 1
        self.gqty[trtp.work - 1] = float(ASD(self.gqty[trtp.work - 1]) + \
            ASD(qty.work))
        self.gcst[trtp.work - 1] = float(ASD(self.gcst[trtp.work - 1]) + \
            ASD(cost.work))
        self.gsel[trtp.work - 1] = float(ASD(self.gsel[trtp.work - 1]) + \
            ASD(sell.work))
        return (trtp, batch, grp, code, loc, ref1, trdt, desc, debtor,
            qty, cost, sell)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-36s %-7s %-2s %-7s" % \
            ("Stores Ledger Audit Trail for Period",
            self.sperd, "to", self.eperd))
        self.fpdf.drawText()
        self.pglin = 4
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            self.fpdf.drawText("%-29s %-8s %-13s %-13s %-13s" %
                ("Document Type", " Number", "    Quantity", "    Cost-Amt",
                "    Sell-Amt"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 4

    def typeHeading(self):
        if self.totsonly != "Y":
            batch = self.batch
        else:
            batch = "Various"
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%-7s %7s %-10s %3s" % \
            ("Batch", batch, "    Type", sttrtp[self.trtp - 1][1]))
        self.fpdf.drawText()
        if self.trtp == 1:
            drscrs = "Crs-Acc"
        elif self.trtp == 7:
            drscrs = "Drs-Acc"
        else:
            drscrs = ""
        if self.totsonly == "Y":
            self.fpdf.drawText("%-30s %-7s %-13s %-13s %-13s" % ("Remarks",
                "", "    Quantity", "    Cost-Amt", "    Sell-Amt"))
        else:
            self.fpdf.drawText("%-3s %-20s %1s %-9s %-10s %-30s %-7s %-13s "\
                "%-13s %-13s" % ("Grp", "Product-Code", "L", "Reference",
                "   Date", "Remarks", drscrs, "    Quantity", "    Cost-Amt",
                "    Sell-Amt"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin += 4

    def batchTotal(self):
        k = CCD(self.bqty, "SD", 13.2)
        l = CCD(self.bcst, "SD", 13.2)
        m = CCD(self.bsel, "SD", 13.2)
        if self.totsonly == "N":
            self.fpdf.drawText()
            self.pglin += 1
        if self.totsonly == "Y":
            self.fpdf.drawText("%-38s %13s %13s %13s" % \
            ("Batch " + self.batch + " Totals", k.disp, l.disp, m.disp))
        else:
            self.fpdf.drawText("%-47s %-38s %13s %13s %13s" % \
            (" ", "Batch " + self.batch + " Totals", k.disp, l.disp, m.disp))
        self.pglin += 1
        if self.totsonly != "Y":
            self.fpdf.drawText()
            self.pglin += 1
        self.bcnt = 0
        self.bqty = 0
        self.bcst = 0
        self.bsel = 0

    def typeTotal(self):
        k = CCD(self.tqty, "SD", 13.2)
        l = CCD(self.tcst, "SD", 13.2)
        m = CCD(self.tsel, "SD", 13.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-38s %13s %13s %13s" % \
                ("Type-Totals", k.disp, l.disp, m.disp))
            self.pglin += 2
        else:
            self.fpdf.drawText("%-47s %-38s %13s %13s %13s" % \
            (" ", "Type-Totals", k.disp, l.disp, m.disp))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        self.tcnt = 0
        self.tqty = 0
        self.tcst = 0
        self.tsel = 0

    def grandTotal(self):
        tot = [0, 0, 0, 0]
        if self.df.repprt[2] == "export":
            for x in range(0, len(sttrtp)):
                tot[0] = float(ASD(tot[0]) + ASD(self.gcnt[x]))
                tot[1] = float(ASD(tot[1]) + ASD(self.gqty[x]))
                tot[2] = float(ASD(tot[2]) + ASD(self.gcst[x]))
                tot[3] = float(ASD(tot[3]) + ASD(self.gsel[x]))
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "", "", "", "", "",
                "Grand Totals", "", tot[1], tot[2], tot[3]]])
            self.expdatas.append(["ULINED"])
            return
        self.totind = "Y"
        self.pageHeading()
        for x, t in enumerate(sttrtp):
            cnt = CCD(self.gcnt[x], "SI", 7)
            qty = CCD(self.gqty[x], "SD", 13.2)
            cst = CCD(self.gcst[x], "SD", 13.2)
            sel = CCD(self.gsel[x], "SD", 13.2)
            self.fpdf.drawText("%-30s %s %s %s %s" % \
                (t[1], cnt.disp, qty.disp, cst.disp, sel.disp))
            tot[0] = tot[0] + cnt.work
            tot[1] = float(ASD(tot[1]) + ASD(qty.work))
            tot[2] = float(ASD(tot[2]) + ASD(cst.work))
            tot[3] = float(ASD(tot[3]) + ASD(sel.work))
        self.fpdf.drawText()
        cnt = CCD(tot[0], "SI", 8)
        qty = CCD(tot[1], "SD", 13.2)
        cst = CCD(tot[2], "SD", 13.2)
        sel = CCD(tot[3], "SD", 13.2)
        self.fpdf.drawText("%-29s %s %s %s %s" % \
            ("Grand Totals", cnt.disp, qty.disp, cst.disp, sel.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
