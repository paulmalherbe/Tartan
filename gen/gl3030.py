"""
SYNOPSIS
    General Ledger Account Statements.

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
from TartanClasses import ASD, CCD, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName
from tartanFunctions import getSingleRecords, showError
from tartanWork import gltrtp

class gl3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genbal", "genmst", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            "%s"))
        self.colsh = ["Coy", "Acc-Num", "Description", "Date", "Reference",
            "Typ", "Batch", "Remarks", "Debit", "Credit", "Balance"]
        self.forms = [("UI", 3), ("UI", 7), ("NA", 30), ("D1", 10),
            ("Na", 9), ("NA", 3), ("Na", 7), ("NA", 30), ("SD", 13.2),
            ("SD", 13.2), ("SD", 13.2)]
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        self.recs = None
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Account Statements (%s)" % self.__class__.__name__)
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])],
            "order": "glm_acno"}
        r1s = (("Yes","Y"),("Range","R"),("Singles", "S"))
        r2s = (("Yes","Y"), ("No","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            self.accs = self.opts["args"]["work"][1]
            view = None
            mail = None
        else:
            var = ["S", "", 0, "", "", "N"]
            self.accs = []
            view = ("Y","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Whole File","",
                var[0],"Y",self.doWhole,None,None,None),
            (("T",0,1,0),"IUI",7,"From Account","",
                var[1],"N",self.doStartAcc,glm,None,("efld",)),
            (("T",0,2,0),"IUI",7,"To Account","",
                var[2],"N",self.doEndAcc,glm,None,("efld",)),
            (("T",0,3,0),"Id2",7,"Starting Period","",
                self.s_per,"N",self.doStartPer,None,None,("efld",)),
            (("T",0,4,0),"Id2",7,"Ending Period","",
                self.e_per,"N",self.doEndPer,None,None,("efld",)),
            (("T",0,5,0),("IRB",r2s),7,"Separate Pages","",
                var[5],"N",self.doPages,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole in ("Y", "S"):
            self.sacno = 0
            self.eacno = 0
            self.df.loadEntry("T", 0, 1, data=self.sacno)
            self.df.loadEntry("T", 0, 2, data=self.eacno)
            return "sk2"

    def doStartAcc(self, frt, pag, r, c, p, i, w):
        if w == 0:
            ok = "yes"
        else:
            ok = self.readAcno(w)
        if ok != "yes":
            return "Invalid Account Number"
        self.sacno = w

    def doEndAcc(self, frt, pag, r, c, p, i, w):
        if w == 0:
            self.eacno = 9999999
            ok = "yes"
        else:
            self.eacno = w
            ok = self.readAcno(w)
        if ok != "yes":
            return "Invalid Account Number"

    def readAcno(self, acno):
        nam = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", acno)], limit=1)
        if not nam:
            return "no"
        else:
            return "yes"

    def doStartPer(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period, Outside Financial Period"
        self.sdate = CCD(w, "D2", 7)

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if w < self.sdate.work:
            return "Invalid Period, Before Start Period"
        if w > self.e_per:
            return "Invalid Period, Outside Financial Period"
        self.edate = CCD(w, "D2", 7)

    def doPages(self, frt, pag, r, c, p, i, w):
        self.pages = w

    def doEnd(self):
        self.df.closeProcess()
        if self.whole == "S":
            self.recs = getSingleRecords(self.opts["mf"], "genmst",
                ("glm_acno", "glm_desc"), where=[("glm_cono", "=",
                self.opts["conum"])], items=[0, self.accs])
        elif self.whole == "R":
            self.recs = self.sql.getRec("genmst", where=[("glm_cono",
                "=", self.opts["conum"]), ("glm_acno", "between", self.sacno,
                self.eacno)], order="glm_acno")
        else:
            self.recs = self.sql.getRec("genmst", where=[("glm_cono",
                "=", self.opts["conum"])], order="glm_acno")
        if not self.recs:
            showError(self.opts["mf"].body, "Error", "No Accounts Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(self.recs)
        else:
            self.printReport(self.recs)
        self.doExit()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = [self.head % self.sysdttm]
        self.expheads.append("General Ledger Account Statements for Period "\
            "%s to %s" % (self.sdate.disp, self.edate.disp))
        self.expcolsh = [self.colsh]
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            self.acno, self.desc, acctot = self.getAccValues(dat)
            trn = self.sql.getRec("gentrn", where=[("glt_cono", "=",
                dat[0]), ("glt_acno", "=", dat[1]), ("glt_curdt", ">=",
                self.sdate.work), ("glt_curdt", "<=", self.edate.work)],
                order="glt_acno, glt_curdt, glt_trdt, glt_type, glt_refno, "\
                "glt_batch")
            prt = False
            if acctot:
                prt = True
                self.expdatas.append(["BODY", [self.opts["conum"],
                    self.acno.work, self.desc.work,
                    ((self.sdate.work * 100) + 1), "", "",
                    "", "Opening Balance", "", "", acctot]])
            for acc in trn:
                prt = True
                trdt, refno, trtp, batch, amt, dbt, crt, detail, curdt, \
                    curmth = self.getTrnValues(acc)
                acctot = float(ASD(acctot) + ASD(amt.work))
                self.expdatas.append(["BODY", [self.opts["conum"],
                    self.acno.work, self.desc.work, trdt.work, refno.work,
                    gltrtp[(trtp.work - 1)][0], batch.work, detail.work,
                    dbt.work, crt.work, acctot]])
            if prt:
                self.expdatas.append(["BLANK"])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        self.pgnum = 0
        self.pglin = 999
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %59s %10s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm, self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        for seq, dat in enumerate(recs):
            p.displayProgress(seq)
            if p.quit:
                break
            self.acno, self.desc, acctot = self.getAccValues(dat)
            trn = self.sql.getRec("gentrn", where=[("glt_cono", "=",
                dat[0]), ("glt_acno", "=", dat[1]), ("glt_curdt", ">=",
                self.sdate.work), ("glt_curdt", "<=", self.edate.work)],
                order="glt_acno, glt_curdt, glt_trdt, glt_type, glt_refno, "\
                "glt_batch")
            if acctot or trn:
                if not self.pgnum or self.pages == "Y":
                    self.pageHeading()
                else:
                    self.newAccount()
            if acctot:
                w1 = CCD(acctot, "SD", 13.2)
                self.fpdf.drawText("%-10s %-9s %-3s %-7s %-30s %-13s %-13s "\
                    "%-13s" % (self.sdate.disp + "-01", "", "", "",
                    "Opening Balance", "", "", w1.disp))
                self.pglin += 1
            for acc in trn:
                trdt, refno, trtp, batch, amt, dbt, crt, detail, curdt, \
                    curmth = self.getTrnValues(acc)
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                    bf = CCD(acctot, "SD", 13.2)
                    if bf.work:
                        self.fpdf.drawText("%32s %-30s %27s %13s" % ("",
                            "Brought Forward", "", bf.disp))
                        self.pglin += 1
                acctot = float(ASD(acctot) + ASD(amt.work))
                w1 = CCD(acctot, "SD", 13.2)
                self.fpdf.drawText("%-10s %-9s %-3s %-7s %-30s %13s %13s %13s"\
                    % (trdt.disp, refno.disp, gltrtp[(trtp.work - 1)][0],
                    batch.disp, detail.disp, dbt.disp, crt.disp, w1.disp))
                self.pglin += 1
            if self.pages == "Y" and (acctot or trn):
                self.pglin = 999
        p.closeProgress()
        if p.quit or not self.fpdf.page:
            return
        if "args" not in self.opts or "noprint" not in self.opts["args"]:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                repeml=self.df.repeml)

    def getAccValues(self, data):
        dic = self.sql.genmst_dic
        acno = CCD(data[dic["glm_acno"][1]], "UI", 7)
        desc = CCD(str(data[dic["glm_desc"][1]]), "NA", 30)
        o = self.sql.getRec("genbal", cols=["glo_cyr"],
            where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
            acno.work), ("glo_trdt", "=", self.opts["period"][1][0])], limit=1)
        if o:
            b = CCD(o[0], "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        ob = b.work
        o = self.sql.getRec("gentrn", cols=["round(sum(glt_tramt), 2)"],
            where=[("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
            acno.work), ("glt_curdt", ">=", self.s_per), ("glt_curdt",
            "<", self.sdate.work)], limit=1)
        if o and o[0]:
            b = CCD(o[0], "SD", 13.2)
        else:
            b = CCD(0, "SD", 13.2)
        acctot = float(ASD(ob) + ASD(b.work))
        return (acno, desc, acctot)

    def getTrnValues(self, data):
        tic = self.sql.gentrn_dic
        trdt = CCD(data[tic["glt_trdt"][1]], "D1", 10)
        refno = CCD(data[tic["glt_refno"][1]], "Na", 9)
        trtp = CCD(data[tic["glt_type"][1]], "UI", 1)
        batch = CCD(data[tic["glt_batch"][1]], "Na", 7)
        amt = CCD(data[tic["glt_tramt"][1]], "SD", 13.2)
        if amt.work < 0:
            dbt = CCD(0, "SD", 13.2)
            crt = CCD(amt.work, "SD", 13.2)
        else:
            dbt = CCD(amt.work, "SD", 13.2)
            crt = CCD(0, "SD", 13.2)
        detail = CCD(data[tic["glt_desc"][1]], "NA", 30)
        curdt = CCD(data[tic["glt_curdt"][1]], "UI", 6)
        curmth = int(curdt.disp[4:6])
        return (trdt, refno, trtp, batch, amt, dbt, crt, detail, curdt, curmth)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        if self.sacno == 0:
            sacc = "  First"
        else:
            sacc = self.df.t_disp[0][0][1]
        if self.eacno == 0:
            eacc = "Last"
        else:
            eacc = self.df.t_disp[0][0][2]
        self.fpdf.drawText("%-38s %-7s %2s %-7s %-10s %7s %2s %7s %11s %5s" % \
            ("General Ledger Statements for Accounts", sacc, "to", eacc,
            "for Period", self.sdate.disp, "to", self.edate.disp, "Page",
            self.pgnum))
        self.fpdf.setFont()
        self.pglin = 3
        self.newAccount()

    def newAccount(self):
        if self.fpdf.lpp - self.pglin < 5:
            self.pageHeading()
        else:
            self.fpdf.setFont(style="B")
            self.fpdf.drawText()
            self.fpdf.drawText("%-7s %-7s %-30s" % ("Account", self.acno.disp,
                self.desc.disp))
            self.fpdf.drawText()
            self.fpdf.drawText("%-10s %-9s %-3s %-7s %-30s %-13s %-13s %-13s" \
                % ("   Date", "Reference", "Typ", "Batch", "Remarks",
                "       Debit", "      Credit", "     Balance"))
            self.fpdf.underLine(self.head)
            self.fpdf.setFont()
            self.pglin += 5

    def doExit(self):
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
            accs = []
            if self.recs:
                for rec in self.recs:
                    accs.append(rec[1])
            self.t_work.append(accs)
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
