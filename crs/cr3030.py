"""
SYNOPSIS
    Creditors Ledger Transactions Due For Payment.

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
from tartanFunctions import doPrinter, getTrn, getModName, paymentDate
from tartanFunctions import projectDate, showError
from tartanWork import crtrtp

class cr3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Transactions Due For Payment (%s)" %
                self.__class__.__name__)
        r1s = (("Monthly","M"),("Daily","D"),("Both","B"))
        r2s = (("No","N"),("Yes","Y"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["M", "N", "", 0]
            view = ("N","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Terms Base","",
                var[0],"Y",self.doPerTyp,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Re-Apply Terms","",
                var[1],"N",self.doReTerm,None,None,None,None,
                "Use this to re-calculate the due date on all "\
                "outstanding transactions. This is normally used "\
                "if the terms have been altered."),
            (("T",0,2,0),"ID1",10,"Payment Date","",
                self.sysdtw,"N",self.doPayDate,None,None,("efld",)),
            (("T",0,3,0),"IUI",2,"Days Leeway","",
                var[3],"N",self.doLeeway,None,None, ("between",0,30)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doPerTyp(self, frt, pag, r, c, p, i, w):
        self.ptyp = w

    def doReTerm(self, frt, pag, r, c, p, i, w):
        self.term = w

    def doPayDate(self, frt, pag, r, c, p, i, w):
        if w == 0:
            w = self.sysdtw
        self.pdatw = w
        self.pdatd = self.df.t_disp[pag][r][p]
        self.df.loadEntry(frt, pag, p, data=self.pdatw)

    def doLeeway(self, frt, pag, r, c, p, i, w):
        self.leeway = w
        if self.leeway:
            self.pdatw = projectDate(self.pdatw, self.leeway)

    def doEnd(self):
        self.df.closeProcess()
        whr = [("crm_cono", "=", self.opts["conum"]), ("crm_pyind", "<>", "N")]
        if self.ptyp != "B":
            whr.append(("crm_termsb", "=", self.ptyp))
        mst = self.sql.getRec("crsmst", where=whr, order="crm_acno")
        if not mst:
            showError(self.opts["mf"].body, "Selection Error",
            "No Accounts Selected")
        else:
            if self.term == "Y":
                self.dueDate(mst)
            self.printReport(mst)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def dueDate(self, mst):
        txt = "Re-Calculating Due Dates"
        p = ProgressBar(self.opts["mf"].body, typ=txt, mxs=len(mst))
        for num, rec in enumerate(mst):
            p.displayProgress(num)
            acno = rec[self.sql.crsmst_col.index("crm_acno")]
            base = rec[self.sql.crsmst_col.index("crm_termsb")]
            stdt = rec[self.sql.crsmst_col.index("crm_stday")]
            term = rec[self.sql.crsmst_col.index("crm_terms")]
            col, recs = getTrn(self.opts["mf"].dbm, "crs",
                whr=[("crt_cono", "=", self.opts["conum"]),
                ("crt_acno", "=", acno)], neg=False, zer="N")
            if not recs:
                continue
            for trn in recs:
                trdt = trn[col.index("crt_trdt")]
                seq = trn[col.index("crt_seq")]
                due = paymentDate(base, stdt, term, trdt)
                self.sql.updRec("crstrn", cols=["crt_paydt"], data=[due],
                    where=[("crt_cono", "=", self.opts["conum"]),
                    ("crt_acno", "=", acno), ("crt_seq", "=", seq)])
        p.closeProgress()
        self.opts["mf"].dbm.commitDbase()

    def printReport(self, mst):
        p = ProgressBar(self.opts["mf"].body, mxs=len(mst), esc=True)
        self.head = "%03u %-107s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.ctots = [0,0,0,0,0]
        self.gtots = [0,0,0,0,0]
        self.pglin = 999
        for num, rec in enumerate(mst):
            p.displayProgress(num)
            if p.quit:
                break
            acno = CCD(rec[self.sql.crsmst_col.index("crm_acno")], "NA", 7)
            name = CCD(rec[self.sql.crsmst_col.index("crm_name")], "NA", 30)
            bnam = rec[self.sql.crsmst_col.index("crm_bname")]
            bibt = rec[self.sql.crsmst_col.index("crm_bibt")]
            bacc = rec[self.sql.crsmst_col.index("crm_bacc")]
            if bnam and bibt and bacc:
                ptyp = "E"
            else:
                ptyp = "C"
            col, trns = getTrn(self.opts["mf"].dbm, "crs", whr=[("crt_cono",
                "=", self.opts["conum"]), ("crt_acno", "=", acno.work),
                ("crt_paydt", "<=", self.pdatw), ("crt_payind", "=", "Y")],
                neg=False, zer="N")
            if not trns:
                continue
            if self.pglin == 999:
                self.pageHeading(acno.disp, name.disp, ptyp)
            else:
                self.newAccount(acno.disp, name.disp, ptyp)
            for trn in trns:
                ref1 = CCD(trn[col.index("crt_ref1")], "Na", 9)
                ref2 = CCD(trn[col.index("crt_ref2")], "Na", 9)
                trtp = CCD(trn[col.index("crt_type")], "UI", 1)
                trdt = CCD(trn[col.index("crt_trdt")], "d1", 10)
                disper = CCD(trn[col.index("crt_disper")], "SD", 7.2)
                tramt = CCD(trn[col.index("crt_tramt")], "SD", 13.2)
                paid = CCD(trn[col.index("paid")], "SD", 13.2)
                trbal = CCD(trn[col.index("balance")], "SD", 13.2)
                sett = round((trbal.work * disper.work / 100), 2)
                sett = CCD(sett, "SD", 13.2)
                nett = float(ASD(trbal.work) - ASD(sett.work))
                nett = CCD(nett, "SD", 13.2)
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading(acno.disp, name.disp, ptyp)
                self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s" % \
                    (ref1.disp, ref2.disp, crtrtp[trtp.work-1][0], trdt.disp,
                    disper.disp, tramt.disp, paid.disp, trbal.disp, sett.disp,
                    nett.disp))
                self.pglin += 1
                self.ctots[0] = float(ASD(self.ctots[0]) + ASD(tramt.work))
                self.ctots[1] = float(ASD(self.ctots[1]) + ASD(paid.work))
                self.ctots[2] = float(ASD(self.ctots[2]) + ASD(trbal.work))
                self.ctots[3] = float(ASD(self.ctots[3]) + ASD(sett.work))
                self.ctots[4] = float(ASD(self.ctots[4]) + ASD(nett.work))
                self.gtots[0] = float(ASD(self.gtots[0]) + ASD(tramt.work))
                self.gtots[1] = float(ASD(self.gtots[1]) + ASD(paid.work))
                self.gtots[2] = float(ASD(self.gtots[2]) + ASD(trbal.work))
                self.gtots[3] = float(ASD(self.gtots[3]) + ASD(sett.work))
                self.gtots[4] = float(ASD(self.gtots[4]) + ASD(nett.work))
            if self.fpdf.page:
                self.accountTotal()
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self, acno, name, ptyp):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-44s %-66s" % \
            ("Creditors Transactions Due For Payment as at", self.pdatd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-21s%-1s%-3s%-9s%-10s%-3s%-12s%-2s%-1s" % \
            ("(Options: Terms-Base", self.ptyp, "", "Pay-Date", self.pdatd,
            "", "Days-Leeway", self.leeway, ")"))
        self.fpdf.setFont()
        self.pglin = 5
        self.newAccount(acno, name, ptyp)

    def newAccount(self, acno, name, ptyp):
        if self.pglin > (self.fpdf.lpp - 5):
            self.pageHeading(acno, name, ptyp)
        else:
            self.fpdf.setFont(style="B")
            self.fpdf.underLine(txt=self.head)
            self.fpdf.drawText("%-7s %-7s %-30s (%s)" % ("Account", acno,
                name, ptyp))
            self.fpdf.drawText()
            self.fpdf.drawText("%-9s %-9s %-3s %-10s %-6s %-13s %-13s %-13s "\
                "%-13s %-13s" % ("Reference", "Ref-Num-2", "Typ", "   Date",
                " Dis-%", "   Trn-Amount", "   Set-Amount", "   Due-Amount",
                "   Dis-Amount", "   Net-Amount"))
            self.fpdf.underLine(txt=self.head)
            self.fpdf.setFont()
            self.pglin += 5

    def accountTotal(self):
        j = CCD(self.ctots[0], "SD", 13.2)
        k = CCD(self.ctots[1], "SD", 13.2)
        l = CCD(self.ctots[2], "SD", 13.2)
        m = CCD(self.ctots[3], "SD", 13.2)
        n = CCD(self.ctots[4], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-42s %13s %13s %13s %13s %13s" % \
            ("Account Totals", j.disp, k.disp, l.disp, m.disp, n.disp))
        self.pglin += 3
        self.ctots = [0,0,0,0,0,0]

    def grandTotal(self):
        j = CCD(self.gtots[0], "SD", 13.2)
        k = CCD(self.gtots[1], "SD", 13.2)
        l = CCD(self.gtots[2], "SD", 13.2)
        m = CCD(self.gtots[3], "SD", 13.2)
        n = CCD(self.gtots[4], "SD", 13.2)
        self.fpdf.drawText()
        self.fpdf.drawText("%-42s %13s %13s %13s %13s %13s" % \
            ("Grand Totals", j.disp, k.disp, l.disp, m.disp, n.disp))
        self.fpdf.drawText()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
