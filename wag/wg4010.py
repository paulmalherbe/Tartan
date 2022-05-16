"""
SYNOPSIS
    Salaries Interrogation.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, NotesCreate, Sql, SRec
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, getModName, doPrinter

class wg4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagmst", "wagedc", "wagcod",
            "wagbal", "wagtf1", "wagtf2"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        if t[1] < 3:
            self.taxyr = t[0]
        else:
            self.taxyr = t[0] + 1
        self.startb = self.startt = (((self.taxyr - 1) * 10000) + 301)
        if not self.taxyr % 4:
            self.endb = self.endt = ((self.taxyr * 10000) + 229)
        else:
            self.endb = self.endt = ((self.taxyr * 10000) + 228)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Salaries/Wages Interrogation (%s)" % self.__class__.__name__)
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname"),
                ("wgm_fname", "", 0, "Names")),
            "where": [("wgm_cono", "=", self.opts["conum"])]}
        r1s = (("Weekly","W"),("2xWeekly","F"),("Monthly   ","M"))
        r2s = (("Cash  ","C"),("Cheque  ","Q"),("Electronic","E"))
        r3s = (("Yes","Y"),("No","N"))
        r4s = (("Current","1"),("Transmission","2"),("Savings","3"))
        tag = (
            ("General", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Tax", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Bank", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Earnings", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Deductions", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Balances", self.doTagSelect, ("T",0,2), ("T",0,1)),
            ("Progs", self.doTaxYear, ("T",0,2), ("T",0,1)),
            ("Trans", self.doTaxYear, ("T",0,2), ("T",0,1)))
        fld = (
            (("T",0,0,0),"IUI",5,"Emp-Num","Employee Number",
                "","Y",self.doEmpno,wgm,None,("notzero",)),
            (("T",0,0,0),"OUI",1,"Department"),
            (("T",0,0,0),"OUI",1,"Class"),
            (("T",1,0,0),"ONA",30,"Surname"),
            (("T",1,1,0),"ONA",30,"Names"),
            (("T",1,2,0),"OD1",10,"Date of Birth"),
            (("T",1,3,0),"ONA",13,"ID Number"),
            (("T",1,4,0),"ONA",16,"Spouse Name"),
            (("T",1,5,0),"ONA",13,"Spouse ID Number"),
            (("T",1,6,0),"ONA",30,"Address Line 1"),
            (("T",1,7,0),"ONA",30,"Address Line 2"),
            (("T",1,8,0),"ONA",30,"Address Line 3"),
            (("T",1,9,0),"ONA",4,"Postal Code"),
            (("T",1,10,0),"ONA",16,"Telephone Number"),
            (("T",1,11,0),"OTX",50,"E-Mail Address"),
            (("T",1,12,0),"OD1",10,"Start Date"),
            (("T",1,13,0),"Od1",10,"Term  Date"),
            (("T",1,14,0),"OUD",13.2,"Salary"),
            (("T",1,15,0),("ORB",r1s),1,"Pay Freq"),
            (("T",1,16,0),("ORB",r2s),1,"Pay Type"),
            (("T",2,0,0),("ORB",r3s),1,"P.A.Y.E."),
            (("T",2,1,0),"ONA",16,"Tax Office"),
            (("T",2,2,0),"ONA",10,"Tax Number"),
            (("T",2,3,0),"OUA",1,"Nature of Employee"),
            (("T",2,4,0),"OUI",9,"Reg Number"),
            (("T",2,5,0),"OUA",1,"Voluntary Excess"),
            (("T",2,6,0),"OUD",6.2,"Fixed Rate"),
            (("T",2,7,0),"ONA",13,"Directive"),
            (("T",3,0,0),("ORB",r4s),0,"Account Type"),
            (("T",3,1,0),"ONA",30,"Bank Name"),
            (("T",3,2,0),"OUI",8,"Branch Code"),
            (("T",3,3,0),"ONA",16,"Account Number"),
            (("T",3,4,0),"ONA",30,"Holder's Name"),
            (("T",3,5,0),"OUI",1,"Holder's Relationship"),
            (("C",4,0,0),"OUI",3,"Cod"),
            (("C",4,0,1),"ONA",30,"Description"),
            (("C",4,0,2),"OSD",13.2,"Amnt/Rate"),
            (("C",5,0,0),"OUI",3,"Cod"),
            (("C",5,0,1),"ONA",30,"Description"),
            (("C",5,0,2),"OSD",13.2,"Employee"),
            (("C",5,0,3),"OSD",13.2,"Employer"),
            (("T",6,0,0),"OSD",13.2,"Balance-1"),
            (("T",6,1,0),"OSD",13.2,"Balance-2"),
            (("T",6,2,0),"OSD",13.2,"Balance-3"),
            (("T",7,0,0),"IUI",4,"Tax Year", "Tax Year",
                self.taxyr,"N",self.doBals,None,None,None),
            (("C",7,0,0),"OUA",1,"T"),
            (("C",7,0,1),"OUI",3,"Cod"),
            (("C",7,0,2),"ONA",30,"Description"),
            (("C",7,0,3),"OSD",13.2,"Hours"),
            (("C",7,0,4),"OSD",13.2,"Value"),
            (("T",8,0,0),"IUI",4,"Tax Year", "Tax Year",
                self.taxyr,"N",self.doTrans,None,None,None))
        tnd = (
            None, None, None, None, None, None, None, None,None)
        txt = (
            self.doExit, None, None, None, None, None, None, None, self.doExit)
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        row = [0, 0, 0, 0, 15, 15, 0, 15, 0]
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tags=tag, rows=row, tend=tnd, txit=txt, butt=but)

    def doEmpno(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagmst", where=[("wgm_cono", "=",
            self.opts["conum"]), ("wgm_empno", "=", w)], limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.empno = w
        self.sname = acc[4]
        self.fname = acc[5]
        acc.insert(17, acc.pop())                    # Termination Date
        self.df.loadEntry("T", 0, 1, data=acc[2])    # Department
        self.df.loadEntry("T", 0, 2, data=acc[3])    # Class
        d = 4
        for pg in range(1, 4):
            for x in range(0, self.df.topq[pg]):
                self.df.loadEntry("T", pg, x, data=acc[d])
                d = d + 1
        self.loadDetail()
        self.opts["mf"].updateStatus("")

    def loadDetail(self):
        ear = self.sql.getRec(tables=["wagcod", "wagedc"], cols=["wcd_type",
            "wcd_code", "ced_desc", "wcd_eamt", "wcd_ramt"],
            where=[("wcd_cono", "=", self.opts["conum"]), ("wcd_empno", "=",
            self.empno), ("wcd_type", "=", "E"), ("ced_cono=wcd_cono",),
            ("ced_type=wcd_type",), ("ced_code=wcd_code",)], order="wcd_code")
        p = 0
        for e in ear:
            for y in range(1, 4):
                self.df.loadEntry("C", 4, p, data=e[y])
                p += 1
        ded = self.sql.getRec(tables=["wagcod", "wagedc"], cols=["wcd_type",
            "wcd_code", "ced_desc", "wcd_eamt", "wcd_ramt"],
            where=[("wcd_cono", "=", self.opts["conum"]), ("wcd_empno", "=",
            self.empno), ("wcd_type", "=", "D"), ("ced_cono=wcd_cono",),
            ("ced_type=wcd_type",), ("ced_code=wcd_code",)], order="wcd_code")
        p = 0
        for d in ded:
            for y in range(1, 5):
                self.df.loadEntry("C", 5, p, data=d[y])
                p += 1
        bal = self.sql.getRec("wagbal", where=[("wbl_cono", "=",
            self.opts["conum"]), ("wbl_empno", "=", self.empno)])
        if bal:
            for b in bal:
                self.df.loadEntry("T", 6, (b[2] - 1), data=b[3])

    def doTagSelect(self):
        self.opts["mf"].updateStatus("")

    def doBals(self, frt, pag, r, c, p, i, w):
        self.startb = (((w - 1) * 10000) + 301)
        if not w % 4:
            self.endb = ((w * 10000) + 229)
        else:
            self.endb = ((w * 10000) + 228)
        wt2 = self.sql.getRec("wagtf2", cols=["wt2_type", "wt2_code",
            "round(sum(wt2_hrs),2)", "round(sum(wt2_eamt),2)"],
            where=[("wt2_cono", "=", self.opts["conum"]), ("wt2_empno", "=",
            self.empno), ("wt2_date", "between", self.startb, self.endb)],
            group="wt2_type, wt2_code", order="wt2_type desc, wt2_code")
        if wt2:
            for num, line in enumerate(wt2):
                typ = CCD(line[0], "UA", 1.0)
                cod = CCD(line[1], "UI", 3.0)
                det = self.sql.getRec("wagedc", cols=["ced_desc"],
                    where=[("ced_cono", "=", self.opts["conum"]), ("ced_type",
                    "=", typ.work), ("ced_code", "=", cod.work)], limit=1)
                if not det:
                    des = "Unknown"
                else:
                    des = det[0]
                self.df.loadEntry("C", pag, (num * 5), data=typ.work)
                self.df.loadEntry("C", pag, (num * 5) + 1, data=cod.work)
                self.df.loadEntry("C", pag, (num * 5) + 2, data=des)
                if line[2]:
                    self.df.loadEntry("C", pag, (num * 5) + 3, data=line[2])
                self.df.loadEntry("C", pag, (num * 5) + 4, data=line[3])

    def doTrans(self, frt, pag, r, c, p, i, w):
        self.startt = (((w - 1) * 10000) + 301)
        if not w % 4:
            self.endt = ((w * 10000) + 229)
        else:
            self.endt = ((w * 10000) + 228)
        tit = "Transactions for Employee: %s - %s %s" % \
            (self.empno, self.fname, self.sname)
        tab = ["wagtf1"]
        wcp = (
            ("wt1_date", "", 0, "Date"),
            ("wt1_page", "", 0, "Number"),
            ("wt1_nhrs", "", 13.2, "Norm-Hrs"),
            ("wt1_npay", "", 13.2, "Norm-Pay"),
            ("wt1_taxbl", "", 13.2, "Tx-Pay"),
            ("wt1_notax", "", 13.2, "Non-Tx-Pay"),
            ("wt1_taxdd", "", 13.2, "Tx-Ded"),
            ("wt1_nondd", "", 13.2, "Non-Tx-Ded"))
        whr = [
            ("wt1_cono", "=", self.opts["conum"]),
            ("wt1_empno", "=", self.empno),
            ("wt1_date", "between", self.startt, self.endt)]
        odr = "wt1_date"
        state = self.df.disableButtonsTags()
        SRec(self.opts["mf"], screen=self.df.nb.Page7, title=tit, tables=tab,
            cols=wcp, where=whr, order=odr)
        self.df.enableButtonsTags(state=state)
        self.doTaxYear()

    def doTaxYear(self):
        if self.df.pag == 7:
            self.df.clearFrame("C", 7)
            self.df.focusField("T", 7, 1)
        else:
            self.df.focusField("T", 8, 1)

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "WAG", self.empno)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doClear(self):
        self.df.selPage("General")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = (
            ("Information", "I"),
            ("Transactions", "T"),
            ("Both", "B"),
            ("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        self.head = "%03u %-110s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        if opt != "T":
            self.pageHeading()
            self.printInfo()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if opt == "I":
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
        elif opt == "B":
            self.wagtrn = self.doGetTrans()
            if not self.wagtrn:
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
            else:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])
        elif opt == "T":
            self.wagtrn = self.doGetTrans()
            if self.wagtrn:
                self.pageHeading()
                self.pageHeadingTrans()
                self.printTrans()
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=["N", "V", "view"])

    def printInfo(self):
        self.fpdf.drawText("%15s %-25s %s" % \
            ("", self.df.topf[0][0][3], self.df.t_disp[0][0][0]))
        self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        # General Screen
        for x in range(0, len(self.df.topf[1])):
            self.fpdf.drawText("%15s %-25s %s" % \
                ("", self.df.topf[1][x][3], self.df.t_disp[1][0][x]))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        # Tax Screen
        for x in range(0, len(self.df.topf[2])):
            self.fpdf.drawText("%15s %-25s %s" % \
                ("", self.df.topf[2][x][3], self.df.t_disp[2][0][x]))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        # Bank Details Screen
        if self.df.t_work[1][0][15] == "E":
            for x in range(0, len(self.df.topf[3])):
                self.fpdf.drawText("%15s %-25s %s" % \
                    ("", self.df.topf[3][x][3], self.df.t_disp[3][0][x]))
                self.pglin += 1
            self.fpdf.drawText()
            self.pglin += 1
        # Balances Screen
        self.pglin += 1
        for x in range(0, len(self.df.topf[6])):
            self.fpdf.drawText("%15s %-25s %s" % \
                ("", self.df.topf[6][x][3], self.df.t_disp[6][0][x]))
            self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1
        # Earnings and Deductions Screen
        self.fpdf.drawText("%15s %29s" % ("", "Earnings and Deductions Codes"))
        self.pglin += 1
        self.fpdf.drawText("%15s %29s" % ("", self.fpdf.suc * 29))
        self.pglin += 1
        self.fpdf.drawText("%15s %-3s %-1s %-30s %12s  %12s " % \
            ("", "Cod", "T", "Description", "Employee", "Employer"))
        self.pglin += 1
        self.fpdf.drawText("%15s %s" % ("", self.fpdf.suc * 63))
        self.pglin += 1
        for x in range(0, len(self.df.colf[4])):
            if self.df.c_work[4][x][0] not in ("", 0):
                self.fpdf.drawText("%15s %s %s %s %12s" % \
                    ("", self.df.c_disp[4][x][0], "E",
                    self.df.c_disp[4][x][1], self.df.c_disp[4][x][2]))
                self.pglin += 1
        for x in range(0, len(self.df.colf[5])):
            if self.df.c_work[5][x][0] not in ("", 0):
                self.fpdf.drawText("%15s %s %s %s %12s %12s" % \
                    ("", self.df.c_disp[5][x][0], "D",
                    self.df.c_disp[5][x][1], self.df.c_disp[5][x][2],
                    self.df.c_disp[5][x][3]))
                self.pglin += 1
        # Progressive Balances Screen
        if self.startb is None or self.endb is None:
            pass
        else:
            self.fpdf.drawText()
            self.pglin += 1
            s = CCD(self.startb, "D1", 10.0)
            e = CCD(self.endb, "D1", 10.0)
            self.fpdf.drawText("%15s %-25s %10s %2s %10s" % \
                ("", "Progressive Balances from", s.disp, "to", e.disp))
            self.pglin += 1
            self.fpdf.drawText("%15s %s" % ("", self.fpdf.suc * 50))
            self.pglin += 1
            self.fpdf.drawText("%15s %-3s %-1s %-30s %12s  %12s " % \
                ("", "Cod", "T", "Description", "Hours", "Value"))
            self.pglin += 1
            self.fpdf.drawText("%15s %s" % ("", self.fpdf.suc * 63))
            self.pglin += 1
            for x in range(0, len(self.df.colf[7])):
                if self.df.c_work[7][x][0]:
                    if self.df.c_work[7][x][3]:
                        hr = self.df.c_disp[7][x][3]
                    else:
                        hr = "             "
                    self.fpdf.drawText("%15s %s %s %s %12s %12s" % ("",
                        self.df.c_disp[7][x][0], self.df.c_disp[7][x][1],
                        self.df.c_disp[7][x][2], hr, self.df.c_disp[7][x][4]))
                    self.pglin += 1
        self.fpdf.drawText()
        self.pglin += 1

    def doGetTrans(self):
        if self.startt is None or self.endt is None:
            return
        wagtrn = self.sql.getRec("wagtf1", cols=["wt1_date",
            "wt1_page", "wt1_nhrs", "wt1_npay", "wt1_taxbl", "wt1_notax",
            "wt1_taxdd, wt1_nondd"], where=[("wt1_cono", "=",
            self.opts["conum"]), ("wt1_empno", "=", self.empno), ("wt1_date",
            "between", self.startt, self.endt)], order="wt1_date")
        return wagtrn

    def printTrans(self):
        for x in range(0, len(self.wagtrn)):
            date = CCD(self.wagtrn[x][0], "D1", 10)
            page = CCD(self.wagtrn[x][1], "UI", 5)
            nhrs = CCD(self.wagtrn[x][2], "SD", 13.2)
            npay = CCD(self.wagtrn[x][3], "SD", 13.2)
            taxbl = CCD(self.wagtrn[x][4], "SD", 13.2)
            notax = CCD(self.wagtrn[x][5], "SD", 13.2)
            taxdd = CCD(self.wagtrn[x][6], "SD", 13.2)
            nondd = CCD(self.wagtrn[x][7], "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
                self.pageHeadingTrans()
            net = CCD((float(ASD(taxbl.work) + ASD(notax.work) - \
                ASD(taxdd.work) - ASD(nondd.work))), "OSD", 13.2)
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s" % (date.disp,
                page.disp, nhrs.disp, npay.disp, taxbl.disp, notax.disp,
                taxdd.disp, nondd.disp, net.disp))
            self.pglin += 1

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-38s %-10s" % \
            ("Salaries and Wages Interrogation as at", self.sysdtd))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 6

    def pageHeadingTrans(self):
        self.fpdf.setFont(style="B")
        self.fpdf.drawText()
        self.fpdf.drawText("%8s Emp-Num: %5s Surname: %s Names: %s" % \
            ("", self.empno, self.df.t_disp[1][0][0], self.df.t_disp[1][0][1]))
        self.fpdf.drawText()
        s = CCD(self.startt, "D1", 10.0)
        e = CCD(self.endt, "D1", 10.0)
        self.fpdf.drawText("%8s %-17s %10s %2s %10s" % \
            ("", "Transactions from", s.disp, "to", e.disp))
        self.fpdf.drawText()
        self.fpdf.drawText(
            "%-10s %5s %12s  %12s  %12s  %12s  %12s  %12s  %12s" %
            ("   Date", "Page", "Norm-Hrs", "Norm-Pay", "Taxbl-Pay",
            "Non-Taxbl", "Tax-D-Ded", "Non-D-Ded", "Net-Pay"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 10

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
