"""
SYNOPSIS
    File Maintenance for Staff Loans Record.

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
from TartanClasses import Sql, TartanDialog

class sl1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "wagedc", "wagmst",
            "waglmf"], prog=self.__class__.__name__)
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
                ("wgm_fname", "", 0, "Names")),
            "where": [("wgm_cono", "=", self.opts["conum"])]}
        lnm = {
            "stype": "R",
            "tables": ("waglmf",),
            "cols": (
                ("wlm_empno", "", 0, "EmpNo"),
                ("wlm_loan", "", 0, "Ln"),
                ("wlm_desc", "", 0, "Description", "Y")),
            "where": [("wlm_cono", "=", self.opts["conum"])],
            "whera": [["T", "wlm_empno", 0]],
            "index": 1}
        ced = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (("ced_type", "", 0, "T"),
                ("ced_code", "", 0, "Cde"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [
                ("ced_cono", "=", self.opts["conum"]),
                ("ced_type", "=", "D")],
            "index": 1}
        fld = (
            (("T",0,0,0),"IUI",5,"Emp-Num","Employee Number",
                "","Y",self.doEmp,wgm,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUI",3,"Loan-Num","Loan Number",
                "","N",self.doLoan,lnm,None,("notzero",)),
            (("T",0,2,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"IUI",3,"Deduction Code","",
                "","N",self.doDed,ced,None,("notzero",)),
            (("T",0,4,0),"IUD",6.2,"Interest Percentage","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"ID1",10,"Start Date","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"IUD",10.2,"Deduction Amount","",
                "","N",None,None,None,("efld",)))
        tnd = ((self.doEnd,"n"),(self.doEnd,"y"))
        txt = (self.doExit,self.doExit)
        but = (
            ("Accept",None,self.doAccept,0,("T",0,4),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,4),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=but)

    def doEmp(self, frt, pag, r, c, p, i, w):
        self.empno = w
        acc = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
            where=[("wgm_cono", "=", self.opts["conum"]), ("wgm_empno", "=",
            self.empno)], limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.name = "%s, %s" % (acc[0], acc[1].split()[0])
        self.df.loadEntry("T", pag, p+1, data=self.name)

    def doLoan(self, frt, pag, r, c, p, i, w):
        self.loan = w
        self.rec = self.sql.getRec("waglmf", where=[("wlm_cono",
            "=", self.opts["conum"]), ("wlm_empno", "=", self.empno),
            ("wlm_loan", "=", self.loan)], limit=1)
        if not self.rec:
            return "Invalid Loan Number"
        wlc = self.sql.waglmf_col
        self.df.loadEntry(frt, pag, p+1, data=self.rec[wlc.index("wlm_desc")])
        self.df.loadEntry(frt, pag, p+2, data=self.rec[wlc.index("wlm_code")])
        self.df.loadEntry(frt, pag, p+3, data=self.rec[wlc.index("wlm_rate")])
        self.df.loadEntry(frt, pag, p+4, data=self.rec[wlc.index("wlm_start")])
        self.df.loadEntry(frt, pag, p+5, data=self.rec[wlc.index("wlm_repay")])

    def doDed(self, frt, pag, r, c, p, i, w):
        self.code = w
        desc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type", "=",
            "D"), ("ced_code", "=", w)], limit=1)
        if not desc:
            return "Invalid Code"

    def doEnd(self):
        data = [self.opts["conum"]]
        for p in range(0, len(self.df.t_work[0][0])):
            if p == 1:
                continue
            data.append(self.df.t_work[0][0][p])
        if data != self.rec[:len(data)]:
            col = self.sql.waglmf_col
            data.append(self.rec[col.index("wlm_xflag")])
            self.sql.updRec("waglmf", data=data, where=[("wlm_cono", "=",
                self.opts["conum"]), ("wlm_empno", "=", self.empno),
                ("wlm_loan", "=", self.loan)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.rec):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["waglmf", "U",
                        "%03i%05i%02i" % (self.opts["conum"], self.empno,
                        self.loan), col[num], dte, self.opts["capnm"],
                        str(dat), str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.focusField("T", 0, 1)

    def doExit(self):
        if not self.df.pag:
            self.doCloseProcess()
        elif self.df.pag == 1:
            self.df.focusField("T", 0, 2)

    def doCloseProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
