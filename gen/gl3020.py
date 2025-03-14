"""
SYNOPSIS
    General Ledger Transaction Audit Trail.

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
from tartanFunctions import doWriteExport, getModName, doPrinter, showError
from tartanWork import gltrtp

class gl3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genmst", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Check for Multiple Companies
        coy = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if coy[0]:
            self.multi = "Y"
        else:
            self.multi = "N"
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["TP", "BatchNo", "Coy", "Acc-Num", "Description",
            "Reference", "Date", "Debits", "Credits", "Tax-Amount", "T",
            "Remarks"]
        self.forms = [("UI", 2, False, False, True), ("Na", 7),
            ("UI", 3, False, False, True), ("UI", 7, False, False, True),
            ("NA", 30), ("Na", 9), ("D1", 10), ("SD", 15.2), ("SD", 15.2),
            ("SD", 15.2), ("UA", 1), ("NA", 30)]
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        self.gqt = [0] * (len(gltrtp) + 1)
        self.gdr = [0] * (len(gltrtp) + 1)
        self.gcr = [0] * (len(gltrtp) + 1)
        self.gvt = [0] * (len(gltrtp) + 1)
        self.totind = "N"
        self.other = "N"
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Audit Trail (%s)" % self.__class__.__name__)
        data = ["All Types"]
        for typ in gltrtp:
            data.append(typ[1])
        btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": data,
            "retn": "I"}
        btm = {
            "stype": "R",
            "tables": ("gentrn",),
            "cols": (
                ("glt_batch", "", 0, "Bat-Num"),
                ("glt_type", ("xx", gltrtp), 20, "Type"),
                ("glt_curdt", "", 0, "Cur-Dat")),
            "where": [],
            "group": "glt_batch, glt_type, glt_curdt",
            "order": "glt_type, glt_curdt, glt_batch"}
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
        fld = [
            (("T",0,0,0),("IRB",r1s),0,"Period Type","",
                var[0],"Y",self.doPtyp,None,None,None),
            (("T",0,1,0),"Id2",7,"Starting Period","",
                self.s_per,"N",self.doStartPer,None,None,("efld",)),
            (("T",0,2,0),"Id2",7,"Ending Period","",
                self.e_per,"N",self.doEndPer,None,None,("efld",)),
            (("T",0,3,0),"Id1",10,"Starting Date","",
                self.sysdtw,"N",self.doStartDat,None,None,("efld",)),
            (("T",0,4,0),"Id1",10,"Ending Date","",
                self.sysdtw,"N",self.doEndDat,None,None,("efld",)),
            (("T",0,5,0),"IUI",1,"Type","Transaction Type",
                var[5],"N",self.doBatTyp,btt,None,None),
            (("T",0,6,0),"INa",7,"Batch Number","",
                var[6],"N",self.doBatNum,btm,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Totals Only","",
                var[7],"N",self.doTots,None,None,None)]
        if self.multi == "Y":
            fld.append(
                (("T",0,8,0),("IRB",r2s),10,"Other Companies","",
                    "N","N",self.doCoy,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doPtyp(self, frt, pag, r, c, p, i, w):
        self.ptyp = w
        if self.ptyp == "C":
            return "sk2"

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.s_per
        elif w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.sperw = w
        self.df.loadEntry(frt, pag, p, data=self.sperw)
        self.sperd = self.df.t_disp[pag][0][i]

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.e_per
        elif w < self.sperw or w > self.e_per:
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
        if w > len(gltrtp):
            return "Invalid Batch Type"
        self.btyp = w
        whr = [("glt_cono", "=", self.opts["conum"])]
        if self.ptyp == "F":
            whr.append(("glt_curdt", "between", self.sperw, self.eperw))
        else:
            whr.append(("glt_capdt", "between", self.sdatw, self.edatw))
        if self.btyp:
            whr.append(("glt_type", "=", self.btyp))
        self.df.topf[pag][i+1][8]["where"] = whr

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batch = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.totsonly = w
        if "args" in self.opts and "noprint" in self.opts["args"]:
            return
        if self.multi == "Y":
            x = 9
        else:
            x = 8
        if self.totsonly == "Y":
            state = "hide"
        else:
            state = "show"
        for y in range(3, len(self.df.rvs)):
            self.df.setWidget(self.df.topEntry[0][x][y][0], state=state)

    def doCoy(self, frt, pag, r, c, p, i, w):
        self.other = w

    def doEnd(self):
        self.df.closeProcess()
        jon = "left outer join genmst on glt_cono=glm_cono and "\
            "glt_acno=glm_acno"
        col = ["glt_cono", "glt_acno", "glt_trdt", "glt_type", "glt_refno",
            "glt_batch", "glt_tramt", "glt_taxamt", "glt_desc", "glt_taxind",
            "glm_desc"]
        if self.other == "Y":
            self.doSelCoy()
            if self.con == "X":
                self.closeProcess()
                return
            whr = [("glt_cono", "in", tuple(self.con))]
        else:
            whr = [("glt_cono", "=", self.opts["conum"])]
        if self.ptyp == "F":
            whr.append(("glt_curdt", "between", self.sperw,
            self.eperw))
        else:
            whr.append(("glt_capdt", "between", self.sdatw, self.edatw))
        if self.btyp:
            whr.append(("glt_type", "=", self.btyp))
        if self.batch:
            whr.append(("glt_batch", "=", self.batch))
        odr = "glt_type, glt_batch, glt_trdt, glt_refno"
        recs = self.sql.getRec("gentrn", join=jon, cols=col,
            where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Transaction Error",
            "No Transactions Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def doSelCoy(self):
        tit = ("Company Selection",)
        self.coys = self.sql.getRec("ctlmst", cols=["ctm_cono",
            "ctm_name"], order="ctm_cono")
        coy = {
            "stype": "C",
            "head": ("Num", "Name"),
            "typs": (("UI", 3), ("NA", 30)),
            "data": self.coys,
            "mode": "M",
            "comnd": self.doCoyCmd}
        r1s = (("Yes","Y"),("Include","I"),("Exclude","E"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Companies","",
                "Y","N",self.doAllCoy,None,None,None,None),
            (("T",0,1,0),"INA",30,"Companies","",
                "","N",self.doCoySel,coy,None,None,None))
        self.cf = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doCoyEnd, "y"),), txit=(self.doCoyExit,))
        self.cf.mstFrame.wait_window()

    def doAllCoy(self, frt, pag, r, c, p, i, w):
        self.con = w
        if self.con == "Y":
            self.con = []
            for coy in self.coys:
                self.con.append(coy[0])
            return "nd"
        elif self.con == "I":
            self.cf.topf[pag][i+1][8]["titl"] = "Select Companies to Include"
        else:
            self.cf.topf[pag][i+1][8]["titl"] = "Select Companies to Exclude"

    def doCoyCmd(self, frt, pag, r, c, p, i, w):
        c = ""
        for co in w:
            if int(co):
                c = c + str(int(co)) + ","
        if len(c) > 1:
            c = c[:-1]
        self.cf.loadEntry(frt, pag, p, data=c)

    def doCoySel(self, frt, pag, r, c, p, i, w):
        if w[-1:] == ",":
            w = w[:-1]
        self.coy = w.split(",")

    def doCoyEnd(self):
        if self.con == "I":
            self.con = self.coy
        elif self.con == "E":
            self.con = []
            for co in self.coys:
                self.con.append(int(co[0]))
            for co in self.coy:
                del self.con[self.con.index(int(co))]
            self.con.sort()
        self.doCoyClose()

    def doCoyExit(self):
        self.con = "X"
        self.doCoyClose()

    def doCoyClose(self):
        self.cf.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("General Ledger Audit Trail for Period "\
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
            cono, acno, trdt, trtp, refno, batch, debit, credit, taxamt, \
                detail, taxind, desc = vals
            line = ["BODY", [trtp.work, batch.work, cono.work, acno.work,
                desc.work, refno.work, trdt.work, debit.work, credit.work,
                taxamt.work, taxind.work, detail.work]]
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.totsonly == "Y":
            self.head = "%03i %-95s" % (self.opts["conum"],
                self.opts["conam"])
        else:
            self.head = "%03i %-138s" % (self.opts["conum"],
                self.opts["conam"])
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
        self.newpage = True
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            cono, acno, trdt, trtp, refno, batch, debit, credit, taxamt, \
                detail, taxind, desc = vals
            if not self.trtp:
                self.trtp = trtp.work
                self.batch = batch.work
            if trtp.work != self.trtp:
                self.batchTotal()
                self.typeTotal()
                self.trtp = trtp.work
                self.batch = batch.work
                self.newpage = True
            if batch.work != self.batch:
                self.batchTotal()
                self.batch = batch.work
                if self.totsonly != "Y":
                    self.typeHeading()
            if self.newpage or self.fpdf.newPage():
                self.newpage = False
                self.pageHeading()
            if self.totsonly != "Y":
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" %
                    (cono.disp, acno.disp, desc.disp, refno.disp, trdt.disp,
                    debit.disp, credit.disp, taxamt.disp, taxind.disp,
                    detail.disp))
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
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        repeml=self.df.repeml)

    def getValues(self, data):
        cono = CCD(data[0], "UI", 3)
        acno = CCD(data[1], "UI", 7)
        trdt = CCD(data[2], "D1", 10)
        trtp = CCD(data[3], "UI", 2)
        refno = CCD(data[4], "Na", 9)
        batch = CCD(data[5], "Na", 7)
        if data[6] < 0:
            debit = CCD(0, "SD", 15.2)
            credit = CCD(data[6], "SD", 15.2)
        else:
            debit = CCD(data[6], "SD", 15.2)
            credit = CCD(0, "SD", 15.2)
        taxamt = CCD(data[7], "SD", 15.2)
        detail = CCD(data[8], "NA", 30)
        taxind = CCD(data[9], "NA", 1)
        desc = CCD(data[10], "NA", 30)
        self.gqt[trtp.work - 1] = self.gqt[trtp.work - 1] + 1
        self.gdr[trtp.work - 1] = float(ASD(self.gdr[trtp.work - 1]) + \
            ASD(debit.work))
        self.gcr[trtp.work - 1] = float(ASD(self.gcr[trtp.work - 1]) + \
            ASD(credit.work))
        self.gvt[trtp.work - 1] = float(ASD(self.gvt[trtp.work - 1]) + \
            ASD(taxamt.work))
        return (cono, acno, trdt, trtp, refno, batch, debit, credit, taxamt,
            detail, taxind, desc)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.drawText(self.head, font=["B"])
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-37s %-7s %-2s %-50s" %
                ("General Ledger Audit Trail for Period", self.sperd,
                "to", self.eperd))
        else:
            self.fpdf.drawText("%-37s %-7s %-2s %-94s" %
                ("General Ledger Audit Trail for Period", self.sperd,
                "to", self.eperd))
        self.fpdf.drawText()
        if self.totind == "N":
            self.typeHeading()
        else:
            self.fpdf.drawText("%-14s" % "Totals Summary")
            self.fpdf.drawText()
            if self.totsonly == "Y":
                self.fpdf.drawText("%-27s%-8s  %-15s %-15s %-15s %-15s" %
                    ("Document Type", "Quantity", "        Debits",
                    "       Credits", "    Difference", "        V.A.T."))
            else:
                self.fpdf.drawText("%-34s%-8s  %-15s %-15s %-15s %-15s" %
                    ("Document Type", "Quantity", "        Debits",
                    "       Credits", "    Difference", "        V.A.T."))
            self.fpdf.underLine(self.head)
            self.fpdf.setFont()

    def typeHeading(self):
        if self.fpdf.newPage(4):
            self.pageHeading()
            return
        if self.totsonly != "Y":
            batch = self.batch
        else:
            batch = "Various"
        self.fpdf.drawText("%-7s %7s %-10s %3s" % ("Batch", batch, "    Type",
            gltrtp[self.trtp - 1][1]), font=["B"])
        self.fpdf.drawText()
        if self.totsonly == "Y":
            self.fpdf.drawText("%-36s %-15s %-15s %-15s %-15s" % ("Details",
                "        Debits", "       Credits", "    Difference",
                "        V.A.T."))
        else:
            self.fpdf.drawText("%-3s %-7s %-30s %-9s %-10s %-15s %-15s "\
                "%-15s %-1s %-30s" % ("Coy", "Acc-Num", "Description",
                "Reference", "   Date", "        Debits", "       Credits",
                "    Tax-Amount", "T", "Remarks"))
        self.fpdf.underLine(self.head)
        self.fpdf.setFont()

    def batchTotal(self):
        if self.fpdf.newPage(3):
            self.pageHeading()
        j = CCD(self.bdrs, "SD", 15.2)
        k = CCD(self.bcrs, "SD", 15.2)
        l = CCD(float(ASD(j.work) + ASD(k.work)), "SD", 15.2)
        m = CCD(self.bvat, "SD", 15.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-36s %15s %15s %15s %15s" %
                ("Batch " + self.batch + " Totals", j.disp, k.disp,
                l.disp, m.disp))
        else:
            self.fpdf.drawText()
            self.fpdf.drawText("%-11s %-51s %15s %15s %15s" % (" ",
                "Batch " + self.batch + " Totals", j.disp, k.disp, m.disp))
            self.fpdf.drawText()
        self.bqty = 0
        self.bcrs = 0
        self.bdrs = 0
        self.bvat = 0

    def typeTotal(self):
        if self.fpdf.newPage(2):
            self.pageHeading()
        j = CCD(self.tdrs, "SD", 15.2)
        k = CCD(self.tcrs, "SD", 15.2)
        l = CCD(float(ASD(j.work) + ASD(k.work)), "SD", 15.2)
        m = CCD(self.tvat, "SD", 15.2)
        if self.totsonly == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText("%-36s %15s %15s %15s %15s" % ("Type Totals",
                j.disp, k.disp, l.disp, m.disp))
        else:
            self.fpdf.drawText("%-11s %-51s %15s %15s %15s" % (" ",
                "Type-Totals", j.disp, k.disp, m.disp))
        self.fpdf.drawText()
        self.tqty = 0
        self.tcrs = 0
        self.tdrs = 0
        self.tvat = 0

    def grandTotal(self):
        tot = [0, 0, 0, 0, 0]
        if self.df.repprt[2] == "export":
            for x in range(0, len(gltrtp)):
                tot[0] = float(ASD(tot[0]) + ASD(self.gdr[x]))
                tot[1] = float(ASD(tot[1]) + ASD(self.gcr[x]))
                tot[2] = float(ASD(tot[2]) + ASD(self.gvt[x]))
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "", "", "Grand Totals",
                "", "", tot[0], tot[1], tot[2], ""]])
            self.expdatas.append(["ULINED"])
            return
        self.totind = "Y"
        self.pageHeading()
        for x, t in enumerate(gltrtp):
            qt = CCD(self.gqt[x], "SI", 8)
            dr = CCD(self.gdr[x], "SD", 15.2)
            cr = CCD(self.gcr[x], "SD", 15.2)
            df = float(ASD(dr.work) + ASD(cr.work))
            df = CCD(df, "SD", 15.2)
            vt = CCD(self.gvt[x], "SD", 15.2)
            if self.totsonly == "Y":
                self.fpdf.drawText("%-27s %s %s %s %s %s" % (t[1],
                    qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
            else:
                self.fpdf.drawText("%-34s %s %s %s %s %s" % (t[1],
                    qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
            tot[0] = tot[0] + qt.work
            tot[1] = float(ASD(tot[1]) + ASD(dr.work))
            tot[2] = float(ASD(tot[2]) + ASD(cr.work))
            tot[3] = float(ASD(tot[3]) + ASD(df.work))
            tot[4] = float(ASD(tot[4]) + ASD(vt.work))
        self.fpdf.drawText()
        qt = CCD(tot[0], "SI", 8)
        dr = CCD(tot[1], "SD", 15.2)
        cr = CCD(tot[2], "SD", 15.2)
        df = CCD(tot[3], "SD", 15.2)
        vt = CCD(tot[4], "SD", 15.2)
        if self.totsonly == "Y":
            self.fpdf.drawText("%-27s %s %s %s %s %s" % ("Grand Totals",
                qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
        else:
            self.fpdf.drawText("%-34s %s %s %s %s %s" % ("Grand Totals",
                qt.disp, dr.disp, cr.disp, df.disp, vt.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
