"""
SYNOPSIS
    Bookings Ledger Balance Listing.

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

class bk3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bkmmst", "bkmcon", "bkmtrn"],
            prog=self.__class__.__name__)
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
        self.head = "%03u %-30s" % (self.opts["conum"], self.opts["conam"])
        self.colsh = ["Number", "S", "Acc-Cod", "Name", "Group", "Tot-Balance",
            "Dr-Balance", "Cr-Balance"]
        self.forms = [("UI", 7), ("UA", 1), ("UA", 7), ("NA", 30),
            ("NA", 30)] + [("SD", 13.2)] * 3
        self.gtots = [0] * 3
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Booking Balances (%s)" % self.__class__.__name__)
        r1s = (
            ("All", "A"),
            ("Query", "Q"),
            ("Confirm", "C"),
            ("Settle", "S"),
            ("Cancel", "X"))
        fld = (
            (("T",0,0,0),"ID2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"Y",self.doCutOff,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Status","",
                "A","Y",self.doStatus,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doCutOff(self, frt, pag, r, c, p, i, w):
        self.cutoff = w
        self.period = self.df.t_disp[pag][r][p]

    def doStatus(self, frt, pag, r, c, p, i, w):
        self.status = w
        if self.status == "A":
            self.statusd = "All"
        elif self.status == "Q":
            self.statusd = "Queries"
        elif self.status == "C":
            self.statusd = "Confirmed"
        elif self.status == "S":
            self.statusd = "Settled"
        elif self.status == "X":
            self.statusd = "Cancelled"

    def doEnd(self):
        self.df.closeProcess()
        whr = [("bkm_cono", "=", self.opts["conum"])]
        if self.status != "A":
            whr.append(("bkm_state", "=", self.status))
        odr = "bkm_number"
        recs = self.sql.getRec("bkmmst", cols=["bkm_number",
            "bkm_state", "bkm_ccode", "bkm_group"], where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head + " %s" % self.sysdttm]
        self.expheads.append("Booking's Balances up to %s" % self.period)
        self.expheads.append("Booking Status: %s" % self.statusd)
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
            line = ["BODY", [vals[0].work, vals[1].work, vals[2].work,
                vals[3].work, vals[4].work]]
            for val in vals[5:]:
                line[1].append(val.work)
            self.expdatas.append(line)
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        chrs = len(self.colsh)
        for f in self.forms:
            chrs += int(f[1])
        if f[0][0].lower() == "s":
            chrs -= 2
        else:
            chrs -= 1
        self.head1 = self.head
        self.head2 = "Booking's Balances up to %s" % self.period
        pad = chrs - len(self.head2)
        self.head2 = self.head2 + (" " * pad)
        self.head3 = "Booking Status: %s" % self.statusd
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head2)
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s" % (vals[0].disp,
                vals[1].disp, vals[2].disp, vals[3].disp, vals[4].disp,
                vals[5].disp, vals[6].disp, vals[7].disp))
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.grandTotal()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        num = CCD(data[0], "UI", 7)
        sta = CCD(data[1], "UA", 1)
        cod = CCD(data[2], "UA", 7)
        if self.df.repprt[2] == "export":
            gpm = CCD(data[3], "NA", len(data[3]))
        else:
            gpm = CCD(data[3], "NA", 30)
        col = ["bkc_sname", "bkc_names", "sum(bkt_tramt)"]
        whr = [
            ("bkc_cono", "=", self.opts["conum"]),
            ("bkc_ccode", "=", cod.work),
            ("bkt_cono=bkc_cono",),
            ("bkt_number", "=", num.work),
            ("bkt_type", "<>", 1),
            ("bkt_curdt", "<=", self.cutoff)]
        grp = "bkc_sname, bkc_names"
        rec = self.sql.getRec(tables=["bkmcon", "bkmtrn"], cols=col,
            where=whr, group=grp, limit=1)
        if not rec or not rec[2]:
            return
        if self.df.repprt[2] == "export":
            nam = "%s %s" % (rec[0].strip(), rec[1].strip())
            nam = CCD(nam, "NA", len(nam))
        else:
            nam = CCD("%s %s" % (rec[0].strip(), rec[1].strip()), "NA", 30)
        bal = CCD(rec[2], "SD", 13.2)
        if bal.work < 0:
            crs = bal
            drs = CCD(0, "SD", 13.2)
        else:
            drs = bal
            crs = CCD(0, "SD", 13.2)
        self.gtots[0] = float(ASD(self.gtots[0]) + ASD(bal.work))
        self.gtots[1] = float(ASD(self.gtots[1]) + ASD(drs.work))
        self.gtots[2] = float(ASD(self.gtots[2]) + ASD(crs.work))
        return (num, sta, cod, nam, gpm, bal, drs, crs)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head1)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head2)
        self.fpdf.drawText()
        self.fpdf.drawText(self.head3)
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %1s %-7s %-30s %-30s %-13s %-13s %-13s" %
            ("Number", "S", "Acc-Cod", "Name", "Group", " Tot-Balance",
            "      Debits", "     Credits"))
        self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.head2)))
        self.fpdf.setFont()
        self.pglin = 8

    def grandTotal(self):
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL",
                ["","","","Grand Totals",""] + self.gtots])
            self.expdatas.append(["ULINED"])
            return
        gt = []
        for x in range(3):
            gt.append(CCD(self.gtots[x], "SD", 13.2))
        self.fpdf.drawText()
        self.fpdf.drawText("%-17s %-30s %30s %13s %13s %13s" % ("",
            "Grand Totals", "", gt[0].disp, gt[1].disp, gt[2].disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
