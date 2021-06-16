"""
SYNOPSIS
    Rental Tenants Master Listing.

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
from tartanFunctions import copyList, doPrinter, getModName, mthendDate
from tartanFunctions import projectDate, showError

class rc3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcatnm", "rcatnt", "rcacon"],
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
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Rental Tenants Master Listing (%s)" % self.__class__.__name__)
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("All","Y"),("Arrears","A"),("Expiring","E"),("Expired","X"))
        fld = (
            (("T",0,0,0),"ID1",10,"Report Date","",
                self.sysdtw,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r2s),0,"Contracts","Contracts to Print",
                "Y","Y",self.doType,None,None,None),
            (("T",0,2,0),"IUI",2,"Months to Expiry","",
                1,"Y",self.doMonths,None,None,("notzero",)),
            (("T",0,3,0),("IRB",r1s),0,"Consolidate","",
                "N","Y",self.doCons,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.datd = self.df.t_disp[0][0][0]

    def doType(self, frt, pag, r, c, p, i, w):
        self.styp = w
        if self.styp != "E":
            self.months = 0
            return "sk1"

    def doMonths(self, frt, pag, r, c, p, i, w):
        self.months = w
        if self.styp != "A":
            self.cons = "N"
            return "sk1"

    def doCons(self, frt, pag, r, c, p, i, w):
        self.cons = w

    def doEnd(self):
        self.df.closeProcess()
        odr = "rcc_code, rcc_acno, rcc_cnum"
        whr = [
            ("rcc_cono", "=", self.opts["conum"])]
        if self.styp == "E":
            whr.append(("rcc_status", "<>", "X"))
        elif self.styp == "X":
            whr.append(("rcc_status", "=", "X"))
        if self.cons == "Y":
            recs = []
            cols = ["rcc_owner", "rcc_code", "rcc_acno", "max(rcc_cnum)"]
            accs = self.sql.getRec("rcacon", cols=cols, where=whr,
                group="rcc_owner, rcc_code, rcc_acno",
                order="rcc_owner, rcc_code, rcc_acno")
            for acc in accs:
                w = copyList(whr)
                w.append(("rcc_owner", "=", acc[0]))
                w.append(("rcc_code", "=", acc[1]))
                w.append(("rcc_acno", "=", acc[2]))
                w.append(("rcc_cnum", "=", acc[3]))
                rec = self.sql.getRec("rcacon", where=w, limit=1)
                recs.append(rec)
        else:
            recs = self.sql.getRec("rcacon", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-167s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        mst = self.sql.rcatnm_col
        con = self.sql.rcacon_col
        self.tots = [0, 0, 0, 0, 0, 0]
        self.cred = [0, 0, 0, 0, 0, 0]
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            ownr = CCD(dat[con.index("rcc_owner")], "NA", 7)
            code = CCD(dat[con.index("rcc_code")], "NA", 7)
            acno = CCD(dat[con.index("rcc_acno")], "NA", 7)
            cnum = CCD(dat[con.index("rcc_cnum")], "UI", 3)
            freq = CCD(dat[con.index("rcc_payind")], "UA", 1)
            strt = CCD(dat[con.index("rcc_start")], "D1", 10)
            prds = CCD(dat[con.index("rcc_period")], "UI", 3)
            stat = CCD(dat[con.index("rcc_status")], "UA", 1)
            if self.styp != "X":
                curdt = int(self.date / 100)
                if self.months:
                    yy = int(curdt / 100)
                    mm = (curdt % 100) + self.months
                    while mm > 12:
                        yy += 1
                        mm -= 12
                    curdt = (yy * 100) + mm
                if freq.work == "M":
                    mths = 1 * prds.work
                elif freq.work == "3":
                    mths = 3 * prds.work
                elif freq.work == "6":
                    mths = 6 * prds.work
                else:
                    mths = 12 * prds.work
                exdt = projectDate(strt.work, mths - 1, typ="months")
                exdt = CCD(mthendDate(exdt), "D1", 10)
                if self.styp == "E" and int(exdt.work / 100) > curdt:
                    continue
            else:
                exdt = CCD(0, "d1", 10)
            acc = self.sql.getRec("rcatnm", where=[("rtn_cono", "=",
                self.opts["conum"]), ("rtn_owner", "=", ownr.work),
                ("rtn_code", "=", code.work), ("rtn_acno", "=", acno.work)],
                limit=1)
            name = CCD(acc[mst.index("rtn_name")], "NA", 30)
            if self.cons == "Y":
                trn = self.sql.getRec("rcatnt", cols=["rtu_mtyp",
                    "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
                    self.opts["conum"]), ("rtu_owner", "=", ownr.work),
                    ("rtu_code", "=", code.work), ("rtu_acno", "=", acno.work),
                    ("rtu_trdt", "<=", self.date)], group="rtu_mtyp")
            else:
                trn = self.sql.getRec("rcatnt", cols=["rtu_mtyp",
                    "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
                    self.opts["conum"]), ("rtu_owner", "=", ownr.work),
                    ("rtu_code", "=", code.work), ("rtu_acno", "=", acno.work),
                    ("rtu_cnum", "=", cnum.work), ("rtu_trdt", "<=",
                    self.date)], group="rtu_mtyp")
            rtl = CCD(0, "SD", 13.2)
            dep = CCD(0, "SD", 13.2)
            fee = CCD(0, "SD", 13.2)
            sv1 = CCD(0, "SD", 13.2)
            sv2 = CCD(0, "SD", 13.2)
            rep = CCD(0, "SD", 13.2)
            if trn:
                for t in trn:
                    if t[0] == 1:
                        rtl = CCD(t[1], "SD", 13.2)
                    elif t[0] == 2:
                        dep = CCD(t[1], "SD", 13.2)
                    elif t[0] == 3:
                        fee = CCD(t[1], "SD", 13.2)
                    elif t[0] == 4:
                        sv1 = CCD(t[1], "SD", 13.2)
                    elif t[0] == 5:
                        sv2 = CCD(t[1], "SD", 13.2)
                    elif t[0] == 6:
                        rep = CCD(t[1], "SD", 13.2)
            srv = CCD(float(ASD(sv1.work) + ASD(sv2.work)), "SD", 13.2)
            bal = float(ASD(rtl.work) + ASD(fee.work) + ASD(srv.work) + \
                ASD(rep.work))
            bal = CCD(bal, "SD", 13.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s %s %s "\
                "%s %s %s" % (ownr.disp, code.disp, acno.disp, cnum.disp,
                name.disp, freq.disp, strt.disp, prds.disp, exdt.disp,
                stat.disp, dep.disp, rtl.disp, fee.disp, srv.disp, rep.disp,
                bal.disp))
            self.tots[0] = float(ASD(self.tots[0]) + ASD(dep.work))
            if dep.work < 0:
                self.cred[0] = float(ASD(self.cred[0]) + ASD(dep.work))
            self.tots[1] = float(ASD(self.tots[1]) + ASD(rtl.work))
            if rtl.work < 0:
                self.cred[1] = float(ASD(self.cred[1]) + ASD(rtl.work))
            self.tots[2] = float(ASD(self.tots[2]) + ASD(fee.work))
            if fee.work < 0:
                self.cred[2] = float(ASD(self.cred[2]) + ASD(fee.work))
            self.tots[3] = float(ASD(self.tots[3]) + ASD(srv.work))
            if srv.work < 0:
                self.cred[3] = float(ASD(self.cred[3]) + ASD(srv.work))
            self.tots[4] = float(ASD(self.tots[4]) + ASD(rep.work))
            if rep.work < 0:
                self.cred[4] = float(ASD(self.cred[4]) + ASD(rep.work))
            self.tots[5] = float(ASD(self.tots[5]) + ASD(bal.work))
            if bal.work < 0:
                self.cred[5] = float(ASD(self.cred[5]) + ASD(bal.work))
            self.pglin += 1
        t = []
        for x in range(6):
            t.append(CCD(self.tots[x], "SD", 13.2).disp)
        self.fpdf.underLine(txt=self.head)
        self.fpdf.drawText("%27s %-30s %29s %-13s %-13s %-13s %-13s "\
            "%-13s %-13s" % ("", "Grand Totals", "", t[0], t[1], t[2],
            t[3], t[4], t[5]))
        t = []
        for x in range(6):
            t.append(CCD(self.cred[x], "SD", 13.2).disp)
        self.fpdf.underLine(txt=self.head)
        self.fpdf.drawText("%27s %-30s %29s %-13s %-13s %-13s %-13s "\
            "%-13s %-13s" % ("", "Credits", "", t[0], t[1], t[2],
            t[3], t[4], t[5]))
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-10s" % ("Rental Tenants Master "\
            "Report as at", self.datd))
        self.fpdf.drawText()
        opts = "%-14s %-1s" % ("(Options: Type", self.styp)
        if self.styp == "E":
            opts = "%s %-6s %-2s)" % \
            (opts, "Months", self.months)
        elif self.cons == "Y":
            opts = "%s %-12s %-1s)" % \
            (opts, "Consolidated", self.cons)
        else:
            opts = "%s)" % opts
        self.fpdf.drawText(opts)
        self.fpdf.drawText()
        self.fpdf.drawText("%-7s %-7s %-7s %-3s %-30s %-1s %-10s %-3s %-10s "\
            "%-1s %-13s %-13s %-13s %-13s %-13s %-13s" % ("Own-Cod", "Prm-Cod",
            "Acc-Num", "Seq", "Name", "F", "Start-Date", "Per", "Expir-Date",
            "S", "     Deposit ","     Rentals ",  "        Fees ",
            "    Services ", "     Repairs ", "     Balance "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
