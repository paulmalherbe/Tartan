"""
SYNOPSIS
    Outstanding Sales Documents Report.

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
from tartanFunctions import doWriteExport, getModName, doPrinter, showError

class si3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlrep", "drsmst", "slsiv1",
            "slsiv2"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.fromad = slsctl["ctv_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.slstot = [0, 0, 0, 0]
        self.tot2 = 0
        self.tot3 = 0
        self.tot4 = 0
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Sales Orders Outstanding (%s)" % self.__class__.__name__)
        si1 = {
            "stype": "R",
            "tables": ("slsiv1",),
            "cols": (
                ("si1_docno", "", 0, "Order-Num"),
                ("si1_chain", "", 0, "Chn"),
                ("si1_acno", "", 0, "Drs-Acc"),
                ("si1_date", "", 0, "Order-Date")),
            "where": [
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_invno", "=", "")],
            "whera": [("T", "si1_rtn", 0)]}
        r1s = (("Sales", "O"), ("Works", "W"), ("Quotes", "Q"))
        r2s = (("List", "L"), ("Detail", "D"))
        r3s = (("Rep's Name", "R"), ("Delivery Address", "D"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Order Type","",
                "O","Y",self.doOrdTyp,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Report Type","",
                "L","Y",self.doRepTyp,None,None,None),
            (("T",0,2,0),("IRB",r3s),0,"Content","",
                "R","Y",self.doContent,None,None,None),
            (("T",0,3,0),"IUI",9,"From Order Number","",
                "","Y",self.doOrd1,si1,None,None),
            (("T",0,4,0),"IUI",9,"To   Order Number","",
                "","Y",self.doOrd2,si1,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doOrdTyp(self, frt, pag, r, c, p, i, w):
        self.otype = w

    def doRepTyp(self, frt, pag, r, c, p, i, w):
        self.rtype = w
        if self.rtype == "L":
            self.ord1 = 0
            self.ord2 = 999999999
            self.df.setWidget(self.df.topEntry[0][5][3][0], state="show")
            self.df.setWidget(self.df.topEntry[0][5][4][0], state="show")
        else:
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.setWidget(self.df.topEntry[0][5][3][0], state="hide")
            self.df.setWidget(self.df.topEntry[0][5][4][0], state="hide")
            return "sk1"

    def doContent(self, frt, pag, r, c, p, i, w):
        self.content = w
        return "sk2"

    def doOrd1(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("slsiv1", where=[("si1_cono", "=",
                self.opts["conum"]), ("si1_rtn", "=", self.otype),
                ("si1_docno", "=", w), ("si1_invno", "=", "")], limit=1)
            if not acc:
                return "This is Not an Outstanding Order"
        self.ord1 = w

    def doOrd2(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.ord1:
                return "Invalid Last Order < First Order"
            acc = self.sql.getRec("slsiv1", where=[("si1_cono", "=",
                self.opts["conum"]), ("si1_rtn", "=", self.otype),
                ("si1_docno", "=", w), ("si1_invno", "=", "")], limit=1)
            if not acc:
                return "This is Not an Outstanding Order"
            self.ord2 = w
        else:
            self.ord2 = 999999999

    def doEnd(self):
        self.df.closeProcess()
        whr = (
            ("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "=", self.otype),
            ("si1_docno", "between", self.ord1, self.ord2),
            ("si1_invno", "=", ""))
        odr = "si1_docno"
        recs = self.sql.getRec("slsiv1", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Orders Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = ["%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm)]
        self.expheads.append("Outstanding Sales Orders Report as at %s" % \
            self.sysdtd)
        self.expcolsh = [["Order-Num", "Order-Date", "Chn", "Acc-Num", "Name",
            "Rep", "Rep-Name", "Job-Num", "Taxable", "Non-Taxable",
            "Total-Tax", "Total-Value"]]
        if self.rtype == "L" and self.content == "D":
            self.expcolsh[0][6] = "Delivery-Address"
        self.expforms = [("Na", 9), ("D1", 10), ("UI", 3), ("NA", 7),
            ("NA", 30), ("Na", 3), ("NA", 30), ("Na", 7), ("SD", 13.2),
            ("SD", 13.2), ("SD", 13.2), ("SD", 13.2)]
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            if not self.getValues(dat):
                continue
            self.getOrdTot()
            self.expdatas.append(["BODY", [self.odr.work, self.dte.work,
                self.chn.work, self.drs.work, self.drsnam, self.rep.work,
                self.context, self.job.work, self.total_taxable,
                self.total_nontaxable, self.total_tax, self.total_value]])
        self.expdatas.append(["BLANK"])
        self.expdatas.append(["TOTAL", [""] * 8 + self.slstot])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        if self.rtype == "L":
            self.head = "%03u %-157s" % (self.opts["conum"], self.opts["conam"])
        else:
            self.head = "%03u %-86s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            if not self.getValues(dat):
                continue
            if self.rtype == "D":
                self.printHeader()
            self.printBody()
        if self.rtype == "L":
            t1 = CCD(self.slstot[0], "SD", 13.2)
            t2 = CCD(self.slstot[1], "SD", 13.2)
            t3 = CCD(self.slstot[2], "SD", 13.2)
            t4 = CCD(self.slstot[3], "SD", 13.2)
            self.fpdf.drawText()
            self.fpdf.drawText("%106s %s %s %s %s" % ("", t1.disp, t2.disp,
                t3.disp, t4.disp))
        p.closeProgress()
        if not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        col = self.sql.slsiv1_col
        self.odr = CCD(data[col.index("si1_docno")], "Na", 9)
        self.si2 = self.sql.getRec("slsiv2", where=[("si2_cono",
            "=", self.opts["conum"]), ("si2_rtn", "=", self.otype),
            ("si2_docno", "=", self.odr.work)], order="si2_line")
        if not self.si2:
            return
        self.mod = CCD(data[col.index("si1_mode")], "UA", 1)
        self.chn = CCD(data[col.index("si1_chain")], "UI", 3)
        self.drs = CCD(data[col.index("si1_acno")], "NA", 7)
        acc = self.sql.getRec("drsmst", cols=["drm_name"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            self.chn.work), ("drm_acno", "=", self.drs.work)], limit=1)
        if not acc:
            self.drsnam = ""
        else:
            self.drsnam = acc[0]
        self.dte = CCD(data[col.index("si1_date")], "D1", 10)
        self.job = CCD(data[col.index("si1_jobno")], "Na", 7)
        self.rep = CCD(data[col.index("si1_rep")], "Na", 3)
        if self.rtype == "L" and self.content == "R":
            acc = self.sql.getRec("ctlrep", cols=["rep_name"],
                where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=",
                self.rep.work)], limit=1)
            if not acc:
                self.context = ""
            else:
                self.context = acc[0]
        else:
            self.context = data[col.index("si1_add1")]
        return True

    def printHeader(self):
        self.pageHeading()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText()
        if self.rtype == "L":
            if self.content == "R":
                text = "Rep-Name"
            else:
                text = "Delivery-Address"
            self.fpdf.drawText("%-9s %-10s %-3s %-7s %-30s %-3s %-30s %-7s"\
                "%13s %13s %13s %13s" % ("Order-Num", "Order-Date", "Chn",
                "Acc-Num", "Name", "Rep", text, "Job-Num", "Taxable",
                "Non-Taxable", "Total-Tax", "Total-Value"))
            self.pglin += 3
        else:
            text = "Order Number: %-9s Date: %-10s Salesman: %-3s %-30s" % \
                (self.odr.disp, self.dte.disp, self.rep.disp, self.context)
            self.fpdf.drawText(text)
            self.fpdf.drawText()
            text = "Chain: %-3s  Acc-Num: %-7s  Name: %-30s" % (self.chn.disp,
                self.drs.disp, self.drsnam)
            self.fpdf.drawText(text)
            self.fpdf.drawText()
            self.fpdf.drawText("%-3s %-20s %-30s %-1s %10s  %-1s %11s %-6s" % \
                ("Grp", "Product-Code", "Description", "L", "Qty-Ord", "V",
                "U-Price", "Disc-%"))
            self.pglin += 7
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.otype == "O":
            txt = "Sales"
        elif self.otype == "W":
            txt = "Works"
        else:
            txt = "Quote"
        self.fpdf.drawText("%-37s %-10s" % \
            ("Outstanding %s Documents Report as at" % txt, self.sysdtd))
        self.fpdf.setFont()
        self.pglin = 3

    def printBody(self):
        if self.rtype == "L":
            if self.pglin > self.fpdf.lpp:
                self.printHeader()
            self.getOrdTot()
            v1 = CCD(self.total_taxable, "SD", 13.2)
            v2 = CCD(self.total_nontaxable, "SD", 13.2)
            v3 = CCD(self.total_tax, "SD", 13.2)
            v4 = CCD(self.total_value, "SD", 13.2)
            text = "%s %s %s %s %-30s %s %-30s %s %s %s %s %s" % \
                (self.odr.disp, self.dte.disp, self.chn.disp, self.drs.disp,
                self.drsnam, self.rep.disp, self.context, self.job.disp,
                v1.disp, v2.disp, v3.disp, v4.disp)
            self.fpdf.drawText(text)
            self.pglin += 1
        else:
            col = self.sql.slsiv2_col
            for dat in self.si2:
                grp = CCD(dat[col.index("si2_group")], "UA", 3)
                cod = CCD(dat[col.index("si2_code")], "NA", 20)
                des = CCD(dat[col.index("si2_desc")], "NA", 30)
                loc = CCD(dat[col.index("si2_loc")], "UA", 1)
                qty = CCD(dat[col.index("si2_qty")], "SD", 11.2)
                vat = CCD(dat[col.index("si2_vat_code")], "UA", 1)
                prc = CCD(dat[col.index("si2_price")], "UD", 11.2)
                dis = CCD(dat[col.index("si2_disc_per")], "UD", 6.2)
                if self.pglin > self.fpdf.lpp:
                    self.printHeader()
                self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (grp.disp,
                    cod.disp, des.disp, loc.disp, qty.disp, vat.disp,
                    prc.disp, dis.disp))
                self.pglin += 1

    def getOrdTot(self):
        self.total_taxable = 0
        self.total_nontaxable = 0
        self.total_tax = 0
        self.total_value = 0
        col = self.sql.slsiv2_col
        for dat in self.si2:
            dis = CCD(dat[col.index("si2_disc_per")], "UD", 6.2)
            qty = CCD(dat[col.index("si2_qty")], "SD", 13.2)
            pri = CCD(dat[col.index("si2_price")], "UD", 12.2)
            vat = CCD(dat[col.index("si2_vat_rate")], "UD", 6.2)
            excpri = round((pri.work * 1), 2)
            incrat = float(ASD(100.0) + ASD(vat.work))
            incpri = round((pri.work * incrat / 100.0), 4)
            net = float(ASD(100.0) - ASD(dis.work))
            excamt = round((qty.work * excpri * net / 100.0), 2)
            incamt = round((qty.work * incpri * net / 100.0), 2)
            vatamt = float(ASD(incamt) - ASD(excamt))
            if excamt == incamt:
                self.total_nontaxable = float(ASD(self.total_nontaxable) + \
                    ASD(excamt))
            else:
                self.total_taxable = float(ASD(self.total_taxable) + \
                    ASD(excamt))
            self.total_tax = float(ASD(self.total_tax) + ASD(vatamt))
            self.total_value = float(ASD(self.total_value) + ASD(incamt))
        self.slstot[0] = float(ASD(self.slstot[0])+ASD(self.total_taxable))
        self.slstot[1] = float(ASD(self.slstot[1])+ASD(self.total_nontaxable))
        self.slstot[2] = float(ASD(self.slstot[2])+ASD(self.total_tax))
        self.slstot[3] = float(ASD(self.slstot[3])+ASD(self.total_value))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
