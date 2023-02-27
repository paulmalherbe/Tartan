"""
SYNOPSIS
    New Loan Rate Capture.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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
from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion

class ln2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "gentrn", "lonctl",
            "lonmf1", "lonmf2", "lonrte", "lontrn"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        lonctl = self.gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.glint = lonctl["cln_glint"]
        self.drate = lonctl["cln_drte"]
        self.crate = lonctl["cln_crte"]
        self.lastd = lonctl["cln_last"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"], ctlctl, ["lon_ctl"]):
                return
            self.glctl = (
                ctlctl["lon_ctl"], ctlctl["int_rec"], ctlctl["int_pay"])
        else:
            self.glctl = None
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def dataHeader(self):
        lm1 = {
            "stype": "R",
            "tables": ("lonmf1",),
            "cols": (
                ("lm1_acno", "", 0, "Acc-Num"),
                ("lm1_name", "", 0, "Name", "Y")),
            "where": [("lm1_cono", "=", self.opts["conum"])]}
        lm2 = {
            "stype": "R",
            "tables": ("lonmf2",),
            "cols": (
                ("lm2_loan", "", 0, "Ln"),
                ("lm2_desc", "", 0, "Description", "Y")),
            "where": [("lm2_cono", "=", self.opts["conum"])],
            "whera": [("C", "lm2_acno", 0, 0)]}
        dte = {
            "stype": "R",
            "tables": ("lonrte",),
            "cols": (
                ("lrt_start", "", 0, "Start-Date"),
                ("lrt_drte", "", 0, "DRte-%"),
                ("lrt_crte", "", 0, "CRte-%")),
            "where": [("lrt_cono", "=", self.opts["conum"])],
            "whera": [
                ("C", "lrt_acno", 0, 0),
                ("C", "lrt_loan", 2, 0)],
            "order": "lrt_start"}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Current Rates","",
                "N","N",self.doAll,None,None,None),
            (("T",0,1,0),"ID1",10,"Effective Date","",
                "","N",self.doSdate,None,None,("efld",)),
            (("T",0,2,0),"IUD",6.2,"Debit  Rate - Old","",
                self.drate,"N",self.doDRte,None,None,None),
            (("T",0,2,0),"IUD",6.2,"New","New Debit Rate",
                "","N",self.doDRte,None,None,None),
            (("T",0,3,0),"IUD",6.2,"Credit Rate - Old","",
                self.crate,"N",self.doCRte,None,None,None),
            (("T",0,3,0),"IUD",6.2,"New","New Credit Rate",
                "","N",self.doCRte,None,None,None),
            (("C",0,0,0),"IUA",7,"Acc-Num","Account Number",
                "","N",self.doAcc,lm1,None,None),
            (("C",0,0,1),"ONA",30,"Name"),
            (("C",0,0,2),"IUI",2,"Ln","Loan Number",
                "","N",self.doLon,lm2,None,None),
            (("C",0,0,3),"ONA",30,"Description"),
            (("C",0,0,4),"ID1",10,"Date","",
                "","N",self.doSdate,dte,None,("efld",)),
            (("C",0,0,5),"IUD",6.2,"DRte-%","Debit Rate",
                "","N",self.doDRte,None,None,None),
            (("C",0,0,6),"IUD",6.2,"CRte-%","Credit Rate",
                "","N",self.doCRte,None,None,None))
        tnd = ((self.endPage,"y"), )
        txt = (self.exitPage, )
        cnd = ((self.endPage,"y"), )
        cxt = (self.exitPage, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doAll(self, frt, pag, r, c, p, i, w):
        self.allrte = w
        if self.allrte == "N":
            return "nd"

    def doSdate(self, frt, pag, r, c, p, i, w):
        if w <= self.lastd:
            return "Invalid Date, Before Last Interest Raise Date"
        self.sdate = w
        self.curdt = int(w / 100)
        self.chgrte = False
        if self.allrte == "N":
            chk = self.sql.getRec("lonrte", where=[("lrt_cono", "=",
                self.opts["conum"]), ("lrt_acno", "=", self.acno), ("lrt_loan",
                "=", self.loan), ("lrt_start", "=", w)], limit=1)
            if chk:
                self.df.loadEntry(frt, pag, p+1, data=chk[4])
                self.df.loadEntry(frt, pag, p+2, data=chk[5])
                ok = askQuestion(self.opts["mf"].body, "Exists",
                """This Date "Already Exists.

Debit Rate: %s  Credit Rate: %s

Changing It Could Cause Problems.

Would You Like to Continue?""" % (chk[4], chk[5]), default="no")
                if ok == "no":
                    return "rf"
                self.chgrte = True

    def doDRte(self, frt, pag, r, c, p, i, w):
        if self.df.frt == "T" and p == 2:
            self.oldd = w
        else:
            self.newd = w

    def doCRte(self, frt, pag, r, c, p, i, w):
        if self.df.frt == "T" and p == 4:
            self.oldc = w
        else:
            self.newc = w

    def doAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.opts["conum"]),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        self.name = acc[0]
        self.df.loadEntry("C", pag, p+1, data=self.name)

    def doLon(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("lonmf2", where=[("lm2_cono", "=",
            self.opts["conum"]), ("lm2_acno", "=", self.acno),
            ("lm2_loan", "=", w)], limit=1)
        if not acc:
            return "Invalid Loan Number"
        self.loan = w
        desc = acc[self.sql.lonmf2_col.index("lm2_desc")]
        self.start = acc[self.sql.lonmf2_col.index("lm2_start")]
        self.pmths = acc[self.sql.lonmf2_col.index("lm2_pmths")]
        if self.pmths:
            return "Fixed Loan, Rate Change Not Allowed"
        self.df.loadEntry("C", pag, p+1, data=desc)

    def endPage(self):
        if self.df.frt == "T":
            if self.allrte == "N":
                self.df.focusField("C", 0, 1)
            else:
                self.updateTables()
                self.opts["mf"].dbm.commitDbase(True)
                self.exitPage()
        else:
            self.updateTables()
            self.df.advanceLine(0)

    def exitPage(self):
        if self.df.frt == "C":
            self.opts["mf"].dbm.commitDbase(True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def updateTables(self):
        if self.allrte == "Y":
            if self.oldd == self.drate and self.oldc == self.crate:
                self.sql.updRec("lonctl", cols=["cln_drte", "cln_crte"],
                    data=[self.newd, self.newc], where=[("cln_cono", "=",
                    self.opts["conum"])])
            whr = [
                ("lm2_cono", "=", self.opts["conum"]),
                ("lrt_cono=lm2_cono",),
                ("lrt_acno=lm2_acno",),
                ("lrt_loan=lm2_loan",),
                ("lrt_drte", "=", self.oldd),
                ("lrt_crte", "=", self.oldc)]
            recs = self.sql.getRec(tables=["lonmf2", "lonrte"],
                cols=["lm2_acno", "lm2_loan", "lm2_pmths"], where=whr,
                group="lm2_acno, lm2_loan, lm2_pmths", order="lm2_acno")
        else:
            recs = [[self.acno, self.loan, 0]]
        for rec in recs:
            if rec[2]:
                # Fixed Period Loan, No Rate Changes Allowed
                continue
            # Loans Rate Record
            if self.chgrte:
                self.sql.updRec("lonrte", cols=["lrt_drte", "lrt_crte"],
                    data=[self.newd, self.newc], where=[("lrt_cono", "=",
                    self.opts["conum"]), ("lrt_acno", "=", rec[0]),
                    ("lrt_loan", "=", rec[1]), ("lrt_start", "=", self.sdate)])
            else:
                self.sql.insRec("lonrte", data=[self.opts["conum"], rec[0],
                    rec[1], self.sdate, self.newd, self.newc])

# vim:set ts=4 sw=4 sts=4 expandtab:
