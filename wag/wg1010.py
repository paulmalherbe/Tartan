"""
SYNOPSIS
    File Maintenance for Salaries & Wages Masterfile Record.

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
from TartanClasses import TartanDialog, RepPrt, Sql

class wg1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctldep", "chglog", "wagbal",
            "wagcap", "wagcod", "wagedc", "wagmst", "wagtf1", "wagtf2",
            "waglmf", "wagltf"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname", "Y"),
                ("wgm_fname", "", 0, "Names"),
                ("wgm_freq", "", 0, "F"),
                ("wgm_start", "", 0, "Start-Date"),
                ("wgm_term", "", 0, "Term-Date")),
            "where": [("wgm_cono", "=", self.opts["conum"])]}
        dep = {
            "stype": "R",
            "tables": ("ctldep",),
            "cols": (
                ("dep_code", "", 0, "Dep"),
                ("dep_name", "", 0, "Name", "Y")),
            "where": [("dep_cono", "=", self.opts["conum"])]}
        wec = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (
                ("ced_code", "", 0, "Code"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [
                ("ced_cono", "=", self.opts["conum"]),
                ("ced_type", "=", "E")]}
        wdc = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (
                ("ced_code", "", 0, "Code"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [
                ("ced_cono", "=", self.opts["conum"]),
                ("ced_type", "=", "D")]}
        r1s = (("Weekly","W"),("2xWeekly","F"),("Monthly   ","M"))
        r2s = (("Cash  ","C"),("Cheque  ","Q"),("Electronic","E"))
        r3s = (("Yes","Y"),("No","N"))
        r4s = (("Current","1"),("Transmission","2"),("Savings","3"))
        fld = (
            (("T",0,0,0),"IUI",5,"Emp-Num","Employee Number",
                "","Y",self.doEmpNum,wgm,None,("notzero",)),
            (("T",0,0,0),"IUI",3,"Department","",
                "","N",self.doDept,dep,None,None),
            (("T",0,0,0),"IUI",1,"Class","",
                "","N",None,None,None,None),
            (("T",1,0,0),"INA",30,"Surname","",
                "","N",None,None,None,("notblank",)),
            (("T",1,1,0),"INA",30,"Names","",
                "","N",None,None,None,("notblank",)),
            (("T",1,2,0),"ID1",10,"Date of Birth","",
                "","N",self.doDOB,None,None,("efld",)),
            (("T",1,3,0),"INA",13,"ID Number","",
                "","N",self.doIdNo,None,None,("idno",)),
            (("T",1,4,0),"INA",16,"Spouse Name","",
                "","N",None,None,None,None),
            (("T",1,5,0),"INA",13,"Spouse ID Number","",
                "","N",self.doIdNo,None,None,("idno",)),
            (("T",1,6,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",1,7,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,None),
            (("T",1,8,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,None),
            (("T",1,9,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("notblank",)),
            (("T",1,10,0),"INA",16,"Telephone Number","",
                "","N",None,None,None,None),
            (("T",1,11,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",1,12,0),"ID1",10,"Start Date","",
                "","N",None,None,None,("efld",)),
            (("T",1,13,0),"IUD",10.2,"Salary/Rate","",
                "","N",None,None,None,("efld",)),
            (("T",1,14,0),("IRB",r1s),0,"Pay Freq","Pay Frequency",
                "M","N",None,None,None,None),
            (("T",1,15,0),("IRB",r2s),0,"Pay Type","",
                "E","N",self.doPayTyp,None,None,None),
            (("T",2,0,0),("IRB",r3s),0,"P.A.Y.E.","",
                "Y","N",None,None,None,None),
            (("T",2,1,0),"INA",16,"Tax Office","",
                "","N",None,None,None,None),
            (("T",2,2,0),"INA",10,"Tax Number","",
                "","N",None,None,None,None),
            (("T",2,3,0),"IUA",1,"Nature of Employee","",
                "A","N",None,None,None,("notblank",)),
            (("T",2,4,0),"IUI",9,"Reg Number","Registration Number",
                "","N",None,None,None,None),
            (("T",2,5,0),"IUA",1,"Voluntary Excess","",
                "N","N",None,None,None,None),
            (("T",2,6,0),"IUD",6.2,"Fixed Rate","",
                "","N",None,None,None,None),
            (("T",2,7,0),"INA",13,"Directive","",
                "","N",None,None,None,None),
            (("T",3,0,0),("IRB",r4s),0,"Account Type","Bank Account Type",
                "1","N",None,None,None,None),
            (("T",3,1,0),"INA",30,"Bank Name","",
                "","N",self.doBankNam,None,None,None),
            (("T",3,2,0),"IUI",8,"Branch Code","Bank Branch Code",
                "","N",self.doBankBch,None,None,None),
            (("T",3,3,0),"INA",16,"Account Number","Bank Account Number",
                "","N",self.doBankAcc,None,None,None),
            (("T",3,4,0),"INA",30,"Account Holder's Name","",
                "","N",self.doHolderNam,None,None,None),
            (("T",3,5,0),"IUI",1,"Holder's Relationship","",
                "","N",self.doHolderRel,None,None,None),
            (("C",4,0,0),"IUI",3,"Cod","Earnings Code",
                "","N",self.doEarnCod,wec,None,("efld",)),
            (("C",4,0,1),"ONA",30,"Description"),
            (("C",4,0,2),"ISD",13.2,"Amnt/Rate","Amount or Rate",
                "","N",self.doEarnAmt,None,self.doCodeDelete,("efld",)),
            (("C",5,0,0),"IUI",3,"Cod","Deduction Code",
                "","N",self.doDedCod,wdc,None,("efld",)),
            (("C",5,0,1),"ONA",30,"Description"),
            (("C",5,0,2),"ISD",13.2,"Amnt/Rate","Employees Amount or Rate",
                "","N",self.doDedEAmt,None,self.doCodeDelete,("efld",)),
            (("C",5,0,3),"ISD",13.2,"Amnt/Rate","Employers Amount or Rate",
                "","N",self.doDedRAmt,None,None,("efld",)),
            (("T",6,0,0),"ISD",13.2,"Balance-1","",
                "","N",None,None,None,("efld",)),
            (("T",6,1,0),"ISD",13.2,"Balance-2","",
                "","N",None,None,None,("efld",)),
            (("T",6,2,0),"ISD",13.2,"Balance-3","",
                "","N",None,None,None,("efld",)))
        tag = (
            ("General",None,("T",0,0),("T",0,1)),
            ("Tax",None,("T",0,0),("T",0,1)),
            ("Bank",None,("T",0,0),("T",0,1)),
            ("Earnings",None,("T",0,0),("T",0,1)),
            ("Deductions",None,("T",0,0),("T",0,1)),
            ("Balances",None,("T",0,0),("T",0,1)))
        tnd = (
            (self.doEnd, "n"),
            (self.doEnd, "n"),
            (self.doEnd, "n"),
            (self.doEnd, "n"),
            None,
            None,
            (self.doEnd, "y"))
        txt = (
            self.doExit,
            self.doExit,
            self.doExit,
            self.doExit,
            None,
            None,
            self.doExit)
        cnd = (
            None,
            None,
            None,
            None,
            (self.doEndEarn, "y"),
            (self.doEndDed, "y"),
            None)
        cxt = (
            None,
            None,
            None,
            None,
            self.doExit,
            self.doExit,
            None)
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doCloseProcess,1,None,None))
        row = [0,0,0,0,15,15,0]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag,
            rows=row, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but,
            clicks=self.doClick)

    def doClick(self, *opts):
        if self.df.pag == 0:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doEmpNum(self, frt, pag, r, c, p, i, w):
        self.empno = w
        self.oldm = self.sql.getRec("wagmst", where=[("wgm_cono", "=",
            self.opts["conum"]), ("wgm_empno", "=", self.empno)], limit=1)
        self.oldb = self.sql.getRec("wagbal", where=[("wbl_cono", "=",
            self.opts["conum"]), ("wbl_empno", "=", self.empno)],
            order="wbl_balno")
        if not self.oldm:
            self.new = True
            self.term = 0
            self.ptyp = ""
        else:
            self.new = False
            self.term = self.oldm[len(self.oldm)-1]
            d = 1
            for pg in range(0, self.df.pgs):
                for x in range(0, self.df.topq[pg]):
                    self.df.loadEntry("T", pg, x, data=self.oldm[d])
                    d = d + 1
            self.ptyp = self.df.t_work[1][0][15]
            self.doLoadEarnDed("E")
            self.doLoadEarnDed("D")
            if self.oldb:
                for b in self.oldb:
                    self.df.loadEntry("T", 6, b[2]-1, data=b[3])

    def doDept(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctldep", cols=["dep_name"],
            where=[("dep_cono", "=", self.opts["conum"]),
            ("dep_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Department"
        self.dept = w

    def doDOB(self, frt, pag, r, c, p, i, w):
        self.dob = w

    def doIdNo(self, frt, pag, r, c, p, i, w):
        if p == 6:
            a = int(int(w) / 10000000)
            b = int(self.dob % 1000000)
            if a != b:
                return "ID Number Does Not Agree with Birth Date"

    def doPayTyp(self, frt, pag, r, c, p, i, w):
        self.ptyp = w

    def doBankNam(self, frt, pag, r, c, p, i, w):
        if self.ptyp == "E" and not w:
            return "Invalid Bank Name"

    def doBankBch(self, frt, pag, r, c, p, i, w):
        if self.ptyp == "E" and not w:
            return "Invalid Branch"

    def doBankAcc(self, frt, pag, r, c, p, i, w):
        if self.ptyp == "E" and not w:
            return "Invalid Account"

    def doHolderNam(self, frt, pag, r, c, p, i, w):
        self.holnam = w

    def doHolderRel(self, frt, pag, r, c, p, i, w):
        self.holrel = w

    def doEnd(self):
        if self.df.pag == 0:
            self.df.focusField("T", 1, 1)
        elif self.df.pag == 1:
            self.df.selPage("Tax")
            self.df.focusField("T", 2, 1)
        elif self.df.pag == 2:
            self.df.selPage("Bank")
            self.df.focusField("T", 3, 1)
        elif self.df.pag == 3:
            self.df.selPage("Earnings")
        elif self.df.pag == 6:
            self.doAccept()

    def doEarnCod(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type", "=",
            "E"), ("ced_code", "=", w)], limit=1)
        if not desc:
            return "Invalid Code"
        self.code = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])
        code = self.sql.getRec("wagcod", cols=["wcd_eamt", "wcd_ramt"],
            where=[("wcd_cono", "=", self.opts["conum"]), ("wcd_empno", "=",
            self.empno), ("wcd_type", "=", "E"), ("wcd_code", "=", w)],
            limit=1)
        if not code:
            self.ncod = "y"
        else:
            self.ncod = "n"
            self.df.loadEntry(frt, pag, p+2, data=code[0])

    def doEarnAmt(self, frt, pag, r, c, p, i, w):
        self.eamt = w
        self.ramt = 0

    def doEndEarn(self):
        self.doEndCode("E")

    def doDedCod(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type", "=",
            "D"), ("ced_code", "=", w)], limit=1)
        if not desc:
            return "Invalid Code"
        self.code = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])
        code = self.sql.getRec("wagcod", cols=["wcd_eamt", "wcd_ramt"],
            where=[("wcd_cono", "=", self.opts["conum"]), ("wcd_empno", "=",
            self.empno), ("wcd_type", "=", "D"), ("wcd_code", "=", w)],
            limit=1)
        if not code:
            self.ncod = "y"
        else:
            self.ncod = "n"
            self.df.loadEntry(frt, pag, p+2, data=code[0])
            self.df.loadEntry(frt, pag, p+3, data=code[1])

    def doDedEAmt(self, frt, pag, r, c, p, i, w):
        self.eamt = w

    def doDedRAmt(self, frt, pag, r, c, p, i, w):
        self.ramt = w

    def doEndDed(self):
        self.doEndCode("D")

    def doEndCode(self, rtype):
        if self.ncod == "y":
            self.sql.insRec("wagcod", data=[self.opts["conum"],
            self.empno, rtype, self.code, self.eamt, self.ramt])
        else:
            self.sql.updRec("wagcod", cols=["wcd_eamt", "wcd_ramt"],
                data=[self.eamt, self.ramt], where=[("wcd_cono", "=",
                self.opts["conum"]), ("wcd_empno", "=", self.empno),
                ("wcd_type", "=", rtype), ("wcd_code", "=", self.code)])
        self.doLoadEarnDed(rtype, focus=True)

    def doLoadEarnDed(self, rtype, focus=False):
        if rtype == "E":
            pag = 4
        else:
            pag = 5
        self.df.clearFrame("C", pag)
        codes = self.sql.getRec(tables=["wagcod", "wagedc"], cols=["wcd_code",
            "ced_desc", "wcd_eamt", "wcd_ramt"], where=[("wcd_cono", "=",
            self.opts["conum"]), ("wcd_empno", "=", self.empno), ("wcd_type",
            "=", rtype), ("ced_cono = wcd_cono",), ("ced_type = wcd_type",),
            ("ced_code = wcd_code",)])
        if not codes:
            return
        p = 0
        for cod in codes:
            for i, c in enumerate(cod):
                if rtype == "E" and i == 3:
                    continue
                self.df.loadEntry("C", pag, p, data=c)
                p = p + 1
        if focus:
            self.df.focusField("C", pag, p+1)
        else:
            self.df.last[pag][1] = p + 1

    def doCodeDelete(self):
        if self.df.pag == 4:
            rtype = "E"
        else:
            rtype = "D"
        code = self.df.c_work[self.df.pag][self.df.row][self.df.idx-2]
        self.sql.delRec("wagcod", where=[("wcd_cono", "=", self.opts["conum"]),
            ("wcd_empno", "=", self.empno), ("wcd_type", "=", rtype),
            ("wcd_code", "=", code)])
        self.doLoadEarnDed(rtype, focus=True)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields(("T",0,None))
        if not mes:
            frt, pag, col, mes = self.df.doCheckFields(("T",1,None))
        if not mes:
            frt, pag, col, mes = self.df.doCheckFields(("T",2,None))
        if not mes and self.df.t_work[1][0][15] == "E":
            frt, pag, col, mes = self.df.doCheckFields(("T",3,None))
        if mes:
            if pag > 0 and pag != self.df.pag:
                if frt == "T":
                    self.df.last[pag][0] = col+1
                else:
                    self.df.last[pag][1] = col+1
                self.df.selPage(self.df.tags[pag - 1][0])
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            data = [self.opts["conum"]]
            for p in range(0, self.df.pgs):
                for x in range(0, self.df.topq[p]):
                    data.append(self.df.t_work[p][0][x])
            data.append(self.term)
            if self.new:
                self.sql.insRec("wagmst", data=data)
                for b in range(3):
                    data = [self.opts["conum"], self.empno, b+1,
                        self.df.t_work[6][0][b], ""]
                    self.sql.insRec("wagbal", data=data)
            else:
                dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
                if data != self.oldm[:len(data)]:
                    col = self.sql.wagmst_col
                    data.append(self.oldm[col.index("wgm_xflag")])
                    self.sql.updRec("wagmst", data=data, where=[("wgm_cono",
                        "=", self.opts["conum"]), ("wgm_empno", "=",
                        self.empno)])
                    for num, dat in enumerate(self.oldm):
                        if dat != data[num]:
                            self.sql.insRec("chglog", data=["wagmst", "U",
                                "%03i%05i" % (self.opts["conum"], self.empno),
                                col[num], dte, self.opts["capnm"], str(dat),
                                str(data[num]), "", 0])
                for n, b in enumerate(self.df.t_work[6][0]):
                    lvl = n + 1
                    data = [self.opts["conum"], self.empno, lvl, b]
                    whr = [
                        ("wbl_cono", "=", self.opts["conum"]),
                        ("wbl_empno", "=", self.empno),
                        ("wbl_balno", "=", lvl)]
                    chk = self.sql.getRec("wagbal", where=whr, limit=1)
                    if not chk:
                        self.sql.insRec("wagbal", data=data)
                        continue
                    if data != self.oldb[n][:len(data)]:
                        col = self.sql.wagbal_col
                        data.append(self.oldb[n][col.index("wbl_xflag")])
                        self.sql.updRec("wagbal", data=data, where=whr)
                        for num, dat in enumerate(self.oldb[n]):
                            if dat != data[num]:
                                self.sql.insRec("chglog", data=["wagbal", "U",
                                    "%03i%05i%i" % (self.opts["conum"],
                                    self.empno, lvl), col[num], dte,
                                    self.opts["capnm"], str(dat),
                                    str(data[num]), "", 0])
            self.opts["mf"].dbm.commitDbase()
            self.df.last[0] = [0, 0]
            self.df.selPage("General")
            self.df.focusField("T", 0, 1)

    def doMainDelete(self):
        t = self.sql.getRec("wagtf1", cols=["count(*)"],
            where=[("wt1_cono", "=", self.opts["conum"]), ("wt1_empno", "=",
            self.empno)], limit=1)
        if t[0]:
            return "Transactions 1 Exist, Not Deleted"
        t = self.sql.getRec("wagtf2", cols=["count(*)"],
            where=[("wt2_cono", "=", self.opts["conum"]), ("wt2_empno=%s", "=",
            self.empno)], limit=1)
        if t[0]:
            return "Transactions 2 Exist, Not Deleted"
        t = self.sql.getRec("wagltf", cols=["count(*)"],
            where=[("wlt_cono", "=", self.opts["conum"]), ("wlt_empno", "=",
            self.empno)], limit=1)
        if t[0]:
            return "Loan Transactions Exist, Not Deleted"
        self.sql.delRec("wagbal", where=[("wbl_cono", "=", self.opts["conum"]),
            ("wbl_empno", "=", self.empno)])
        self.sql.delRec("wagcap", where=[("wcp_cono", "=", self.opts["conum"]),
            ("wcp_empno", "=", self.empno)])
        self.sql.delRec("wagcod", where=[("wcd_cono", "=", self.opts["conum"]),
            ("wcd_empno", "=", self.empno)])
        self.sql.delRec("waglmf", where=[("wlm_cono", "=", self.opts["conum"]),
            ("wlm_empno", "=", self.empno)])
        self.sql.delRec("wagmst", where=[("wgm_cono", "=", self.opts["conum"]),
            ("wgm_empno", "=", self.empno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["wagmst", "D", "%03i%05i" %
            (self.opts["conum"], self.empno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        tables = []
        for pag in range(0, (self.df.pgs+1)):
            for x in range(0, self.df.topq[pag]):
                lin = []
                lin.append(self.df.topf[pag][x][3])
                lin.append(self.df.t_disp[pag][0][x])
                tables.append(lin)
        heads = ["Salaries and Wages File Maintenance"]
        cols = [["a","NA",30.0,"Field Name"],
                ["b","NA",30.0,"Values"]]
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=cols, conum=self.opts["conum"],
            conam=self.opts["conam"], ttype="D")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.selPage("General")
        self.df.focusField("T", 0, 1)

    def doExit(self):
        if self.df.pag == 0:
            self.doCloseProcess()
        elif self.df.pag == 1:
            self.df.focusField("T", 0, 3)
        elif self.df.pag == 2:
            self.df.selPage("General")
        elif self.df.pag == 3:
            self.df.selPage("Tax")
        elif self.df.pag == 4:
            self.df.selPage("Deductions")
        elif self.df.pag == 5:
            self.df.selPage("Balances")

    def doCloseProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
