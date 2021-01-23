"""
SYNOPSIS
    Cash Declaration Report.

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

import socket, time
from TartanClasses import ASD, CCD, MyFpdf, Sql, TartanDialog, ViewPDF
from tartanFunctions import askQuestion, getModName, showError

class ps2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlpwu", "posmst", "poscnt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        try:
            self.host = socket.gethostname()
        except:
            showError(self.opts["mf"].window, "Error",
                "Cannot Determine Terminal Name")
        usr = self.sql.getRec("ctlpwu", cols=["usr_fnam"],
            where=[("usr_name", "=", self.opts["capnm"])], limit=1)
        if usr[0]:
            self.user = usr[0]
        else:
            self.user = self.opts["capnm"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % (t[0],
            t[1], t[2], t[3], t[4])
        self.denoms = (
            ("R200", 200),
            ("R100", 100),
            ("R50", 50),
            ("R20", 20),
            ("R10", 10),
            ("R5", 5),
            ("R2", 2),
            ("R1", 1),
            ("C50", .5),
            ("C20", .2),
            ("C10", .1),
            ("C5", .05),
            ("C2", .02),
            ("C1", .01))
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Cash Declaration Report (%s)" % self.__class__.__name__)
        dte = {
            "stype": "R",
            "tables": ("poscnt",),
            "cols": (
                ("psc_date", "", 0, "Date"),
                ("psc_float", "", 0, "Float")),
            "where": [
                ("psc_cono", "=", self.opts["conum"]),
                ("psc_rec", "=", 0)]}
        fld = (
            (("T",0,0,0),"OTX",15,"Terminal Name"),
            (("T",0,1,0),"ID1",10,"Date","",
                self.sysdtw,"N",self.doDate,dte,None,("efld",)),
            (("T",0,2,0),"ISD",13.2,"Float","Cash Float",
                0,"N",self.doFloat,None,None,("notzero",)),
            (("T",0,3,0),"ISD",13.2,"Vouchers","",
                "","N",self.doVou,None,None,("efld",)),
            (("T",0,4,0),"ISD",13.2,"C/Cards","",
                "","N",self.doChq,None,None,("efld",)),
            (("T",0,5,0),"OSD",13.2,"Cash"),
            (("C",0,0,0),"IUI",5,"Quant","Quantity",
                0,"N",self.doQty,None,None,None,("Denomination",14)),
            (("C",0,1,0),"OSD",13.2,"Value","",
                "","N",None,None,None,("efld",)))
        tnd = ((self.doEnd,"n"), )
        txt = (self.doExit, )
        cnd = ((self.doEnd, "n"),)
        cxt = (self.doExit,)
        but = None
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but, focus=False)
        for x in range(14):
            self.df.colLabel[0][x].configure(text=self.denoms[x][0])
        self.df.loadEntry("T", 0, 0, data=self.host)
        self.df.focusField("T", 0, 2)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.datew = w
        self.dated = self.df.t_disp[pag][r][p]
        mst = self.sql.getRec("posmst", where=[("psm_cono", "=",
            self.opts["conum"]), ("psm_host", "=", self.host), ("psm_date",
            "=", self.datew)])
        if not mst:
            return "Invalid Cash Capture Date"
        csh = self.sql.getRec("poscnt", where=[("psc_cono", "=",
            self.opts["conum"]), ("psc_host", "=", self.host),
            ("psc_user", "=", self.opts["capnm"]),
            ("psc_date", "=", self.datew)], limit=1)
        if csh:
            if csh[self.sql.poscnt_col.index("psc_rec")]:
                showError(self.opts["mf"].window, "Error",
                    "This Declaration Has Already Been Reconciled.")
                return "Already Reconciled"
            self.amend = True
            self.df.loadEntry("T", 0, 2, data=csh[4])
            self.df.loadEntry("T", 0, 3, data=csh[5])
            self.df.loadEntry("T", 0, 4, data=csh[6])
            tot = 0
            p = 0
            for x in range(14):
                p = x * 2
                y = x + 7
                qty = csh[y]
                val = qty * self.denoms[x][1]
                self.df.loadEntry("C", pag, p, qty)
                self.df.loadEntry("C", pag, p+1, val)
                tot = float(ASD(tot) + ASD(val))
                self.df.loadEntry("T", 0, 5, data=tot)
        else:
            self.amend = False

    def doFloat(self, frt, pag, r, c, p, i, w):
        self.float = CCD(w, "SD", 13.2)
        self.ctotal = 0
        self.df.loadEntry("T", 0, 5, data=self.ctotal)

    def doVou(self, frt, pag, r, c, p, i, w):
        self.vou = CCD(w, "SD", 13.2)

    def doChq(self, frt, pag, r, c, p, i, w):
        self.ccc = CCD(w, "SD", 13.2)
        self.ctotal = 0

    def doQty(self, frt, pag, r, c, p, i, w):
        val = w * self.denoms[int(p / 2)][1]
        self.df.loadEntry(frt, pag, p+1, val)
        self.ctotal = float(ASD(self.ctotal) + ASD(val))
        self.df.loadEntry("T", 0, 5, data=self.ctotal)

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
        elif self.df.col == 28:
            ask = askQuestion(self.opts["mf"].body, "Accept",
                "Accept All Entries\n\nYes to Save and View\n\nNo to Re-Enter")
            if ask == "yes":
                data = [self.opts["conum"]]
                data.append(self.df.t_work[0][0][0])
                data.extend([self.opts["capnm"], self.datew])
                data.append(self.df.t_work[0][0][2])
                data.append(self.df.t_work[0][0][3])
                data.append(self.df.t_work[0][0][4])
                for x in range(14):
                    data.append(self.df.c_work[0][x][0])
                data.append(0)
                if self.amend:
                    self.sql.delRec("poscnt", where=[("psc_cono", "=",
                        self.opts["conum"]), ("psc_host", "=", self.host),
                        ("psc_user", "=", self.opts["capnm"]),
                        ("psc_date", "=", self.datew)])
                self.sql.insRec("poscnt", data=data)
                self.opts["mf"].dbm.commitDbase()
                self.doPrint()
            else:
                self.df.focusField("T", 0, 1, clr=False)
        else:
            self.df.advanceLine(self.df.pag)

    def doPrint(self):
        head = ("%03u %-30s" % (self.opts["conum"], self.opts["conam"]))
        txt1 = "Cash Declaration for %s" % self.host
        txt2 = "Declared by %s (%s) on %s" % (
            self.user, self.opts["capnm"], self.dated)
        txt3 = "%-32s %13s %13s" % ("Denomination", "Quantity", "Amount ")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=len(txt3),
            foot=True)
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(head)
        self.fpdf.drawText()
        self.fpdf.drawText(txt1)
        self.fpdf.drawText()
        self.fpdf.drawText(txt2)
        self.fpdf.drawText()
        self.fpdf.drawText(txt3)
        self.fpdf.underLine(txt=txt3)
        self.fpdf.setFont()
        rec = self.sql.getRec("poscnt", where=[("psc_cono", "=",
            self.opts["conum"]), ("psc_host", "=", self.host), ("psc_user",
            "=", self.opts["capnm"]), ("psc_date", "=", self.datew)], limit=1)
        rc = self.sql.poscnt_col
        csh = 0
        for x in range(7, 21):
            if rec[x]:
                qty = CCD(rec[x], "UI", 5)
                val = CCD(qty.work * self.denoms[x-7][1], "SD", 13.2)
                csh = float(ASD(csh) + ASD(val.work))
                self.fpdf.drawText("%-32s %13s %s" % (self.denoms[x-7][0],
                    qty.disp, val.disp))
        self.fpdf.drawText("%46s %-12s" % ("", self.fpdf.suc*12))
        csh = CCD(csh, "SD", 13.2)
        self.fpdf.drawText("%-32s %13s %s" % ("Total cash", "", csh.disp))
        self.fpdf.drawText("%-32s %13s %s" % ("Float", "", self.float.disp))
        self.fpdf.drawText("%46s %-12s" % ("", self.fpdf.suc*12))
        net = CCD(float(ASD(csh.work) - ASD(self.float.work)), "SD", 13.2)
        self.fpdf.drawText("%-32s %13s %s" % ("Net Cash", "", net.disp))
        vou = CCD(rec[rc.index("psc_vou")], "SD", 13.2)
        ccc = CCD(rec[rc.index("psc_ccc")], "SD", 13.2)
        self.fpdf.drawText("%-32s %13s %s" % ("Vouchers", "", vou.disp))
        self.fpdf.drawText("%-32s %13s %s" % ("C/Cards", "", ccc.disp))
        self.fpdf.drawText("%46s %-12s" % ("", self.fpdf.suc*12))
        net = float(ASD(net.work) + ASD(vou.work) + ASD(ccc.work))
        net = CCD(net, "SD", 13.2)
        self.fpdf.drawText("%-32s %13s %s" % ("Total Takings", "", net.disp))
        self.fpdf.drawText("%46s %-12s" % ("", self.fpdf.suc*12))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        ViewPDF(self.opts["mf"], pdfnam)
        self.closeProcess()

    def doExit(self):
        if self.df.frt == "T":
            self.closeProcess()
        elif self.df.pos:
            self.df.loadEntry("C", 0, self.df.pos,
                data=self.df.c_work[0][self.df.row][self.df.idx])
            r = self.df.row - 1
            c = self.df.col - 2
            self.ctotal = float(ASD(self.ctotal)-ASD(self.df.c_work[0][r][1]))
            self.df.focusField("C", 0, c)

    def closeProcess(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
