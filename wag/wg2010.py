"""
SYNOPSIS
    Salaries - Data Capture.

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
from TartanClasses import GetCtl, Sql, SChoice, TartanDialog
from tartanFunctions import askQuestion, callModule

class wg2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagedc", "wagmst", "wagcap",
            "wagcod"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.m_hrs = wagctl["ctw_m_hrs"]
        self.w_hrs = wagctl["ctw_w_hrs"]
        self.d_hrs = wagctl["ctw_d_hrs"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.edit = None
        return True

    def dataHeader(self):
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "Emp-Num"),
                ("wgm_sname", "", 0, "Surname", "Y"),
                ("wgm_fname", "", 0, "First Names")),
            "where": [
                ("wgm_cono", "=", self.opts["conum"]),
                ("wgm_term", "=", 0)]}
        wed = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (
                ("ced_code", "", 0, "Code"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [("ced_cono", "=", self.opts["conum"])],
            "whera": [["C", "ced_type", 4, 0]]}
        fld = (
            (("C",0,0,0),"IUI",5,"EmpNo","Employee Number",
                "r","N",self.doEmpno,wgm,None,("efld",)),
            (("C",0,0,1),"ONA",40,"Name"),
            (("C",0,0,2),"OUI",3,"Dep"),
            (("C",0,0,3),"IUI",5,"JobNo","Job Number",
                "r","N",None,None,None,("efld",)),
            (("C",0,0,4),"IUA",1,"T","Earnings/Deduction/NoPay",
                "r","N",self.doType,None,None,("in", ("E","D"))),
            (("C",0,0,5),"IUI",3,"Cde","Code Number",
                "","N",self.doCode,wed,None,("efld",)),
            (("C",0,0,6),"ONA",20,"Description"),
            (("C",0,0,7),"IUA",1,"P","Pay (Y or N)",
                "Y","N",self.doPay,None,None,("in", ("Y","N"))),
            [("C",0,0,8),"ISD",13.2,"Amount","",
                "","N",self.doAmt,None,None,None])
        but = (
            ("Edit",None,self.editData,0,("C",0,1),("C",0,2)),
            ("Interrogate",None,self.queryWag,0,("C",0,1),("C",0,2)))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            cend=((self.endData,"y"),), cxit=(self.exitData,))

    def doEmpno(self, frt, pag, r, c, p, i, w):
        rec = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname",
            "wgm_dept", "wgm_freq", "wgm_term"], where=[("wgm_cono", "=",
            self.opts["conum"]), ("wgm_empno", "=", w)], limit=1)
        if not rec:
            return "Invalid Employee Number"
        elif rec[4]:
            return "Employment Terminated"
        self.empno = w
        name = "%s, %s" % (rec[0], rec[1].split()[0])
        self.df.loadEntry(frt, pag, p+1, data=name)
        self.df.loadEntry(frt, pag, p+2, data=rec[2])
        self.freq = rec[3]

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtyp = w

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        rec = self.readWagedc()
        if not rec:
            return "Invalid Code"
        chk = self.sql.getRec("wagcap", where=[("wcp_cono", "=",
            self.opts["conum"]), ("wcp_empno", "=", self.empno),
            ("wcp_type", "=", self.rtyp), ("wcp_code", "=", self.code)])
        if chk:
            if self.rtyp == "E":
                txt = "Earnings"
            else:
                txt = "Deduction"
            ok = askQuestion(self.df.mstFrame, head="Duplicate",
                mess="An Entry for this %s Code Already Exists "\
                "for this Employee.\n\nIs This Correct?" % txt)
            if ok == "no":
                return "rf"
        self.df.loadEntry(frt, pag, p+1, rec[0])
        if self.rtyp == "E" and self.code == 1:
            std = self.sql.getRec("wagcod", cols=["wcd_eamt"],
                where=[("wcd_cono", "=", self.opts["conum"]), ("wcd_empno",
                "=", self.empno), ("wcd_type", "=", "E"), ("wcd_code", "=",
                self.code)], limit=1)
            if std and std[0]:
                hrs = std[0]
            elif self.freq == "M":
                hrs = self.m_hrs
            elif self.freq == "W":
                hrs = self.w_hrs
            elif self.freq == "D":
                hrs = self.d_hrs
            else:
                hrs = self.m_hrs
            self.df.colf[0][8][5] = hrs
        else:
            self.df.colf[0][8][5] = ""

    def doPay(self, frt, pag, r, c, p, i, w):
        pass

    def doAmt(self, frt, pag, r, c, p, i, w):
        self.xrow = r

    def readWagedc(self):
        rec = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type", "=",
            self.rtyp), ("ced_code", "=", self.code)], limit=1)
        if not rec:
            return None
        else:
            return rec

    def endData(self):
        r = self.xrow
        data = [self.opts["conum"], self.empno,
            self.df.c_work[0][r][2], self.df.c_work[0][r][3],
            self.df.c_work[0][r][4], self.df.c_work[0][r][5],
            self.df.c_work[0][r][7], self.df.c_work[0][r][8],
            "N", self.opts["capnm"], self.sysdtw]
        if self.edit:
            data.append(self.edit)
            self.sql.updRec("wagcap", data=data,
                where=[("wcp_seq", "=", self.edit)])
            self.edit = None
        else:
            data.append(0)
            self.sql.insRec("wagcap", data=data)
        self.df.advanceLine(0)

    def exitData(self):
        self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def editData(self):
        # Display captured items and allow editing
        col = ["wcp_empno", "wgm_sname", "wcp_dept", "wcp_job", "wcp_type",
            "wcp_code", "ced_desc", "wcp_ind", "wcp_amt", "wcp_seq"]
        whr = [("wcp_cono", "=", self.opts["conum"]), ("wcp_paid", "=", "N"),
            ("wgm_cono=wcp_cono",), ("wgm_empno=wcp_empno",),
            ("ced_cono=wcp_cono",), ("ced_type=wcp_type",),
            ("ced_code=wcp_code",)]
        data = self.sql.getRec(tables=["wagcap", "wagmst", "wagedc"],
            cols=col, where=whr, order="wcp_empno")
        if not data:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        titl = "Captured Items"
        head = ("EmpNo", "Surname", "Dep", "JobNo", "T", "Cod",
            "Description", "I", "Amount","Sequence")
        lin = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": [
                ("UI", 5), ("NA", 30), ("UI", 3), ("UI", 5), ("UA", 1),
                ("UI", 3), ("NA", 20), ("UA", 1), ("SD", 13.2), ("UI", 10)],
            "data": data,
            "butt": [("Delete", self.doDelete, True)]}
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select an Item to Edit")
        chg = SChoice(self.opts["mf"], deco=True, titl=lin["titl"],
            head=lin["head"], data=lin["data"], typs=lin["typs"], mode="S",
            retn="D", butt=lin["butt"], scrn=self.df.mstFrame)
        self.df.enableButtonsTags(state=state)
        if chg and chg.selection:
            for num, fld in enumerate(chg.selection):
                if num in (0, 3, 4, 5):
                    self.df.doKeyPressed("C", 0, self.df.pos, fld)
                elif num == (len(chg.selection) - 1):
                    self.edit = int(fld)
                else:
                    self.df.loadEntry(self.df.frt, self.df.pag, num, data=fld)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doDelete(self, args):
        self.sql.delRec("wagcap", where=[("wcp_seq", "=", args[-1:][0])])

    def queryWag(self):
        callModule(self.opts["mf"], self.df, "wg4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

# vim:set ts=4 sw=4 sts=4 expandtab:
