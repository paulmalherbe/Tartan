"""
SYNOPSIS
    Wages Earnings and Deductions File Maintenance.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import chkGenAcc, showInfo

class wgc310(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genmst", "wagrcv",
            "wagedc", "wagtf2"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        wagctl = self.gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.glint = wagctl["ctw_glint"]
        return True

    def mainProcess(self):
        ced = {
            "stype": "R",
            "tables": ("wagedc",),
            "cols": (
                ("ced_code", "", 0, "Cde"),
                ("ced_desc", "", 0, "Description", "Y")),
            "where": [("ced_cono", "=", self.opts["conum"])],
            "whera": [["T", "ced_type", 0]],
            "order": "ced_code"}
        bas = {
            "stype": "C",
            "titl": "Available Base Rates",
            "head": ("C", "Description"),
            "data": (
                (1, "X * Normal Rate of Pay * Factor"),
                (2, "Normal Pay * Factor"),
                (3, "Normal Pay * Factor / 100"),
                (4, "X * Daily Rate of Pay * Factor"),
                (5, "X * Hourly Rate of Pay * Factor"),
                (6, "U.I.F. Pay * Factor"),
                (7, "S.D.L. Pay * Factor"))}
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        rcv = {
            "stype": "R",
            "tables": ("wagrcv",),
            "cols": (
                ("rcv_code", "", 0, "Code"),
                ("rcv_desc", "", 0, "Details", "Y"))}
        r1s = (("Variable","V"),("Fixed","F"))
        r2s = (("Amount","A"),("Rate","R"))
        r3s = (("Salary","S"),("Commission","C"))
        r4s = (("Amount","A"),("Rate","R"),("None","N"))
        r5s = (("Yes","Y"),("No","N"),("Notional","T"),
                ("One Time","O"),("Retrench","R"))
        r6s = (("Yes","Y"),("No","N"))
        tag = (
            ("Detail-_A",None,("T",0,0),("T",0,1)),
            ("Detail-_B",None,("T",0,0),("T",0,1)))
        self.fld = (
            (("T",0,0,0),"IUA",1,"Type","Earning/Deduction Type",
                "E","N",self.doType,None,None,("in", ("E", "D"))),
            (("T",0,0,0),"IUI",3,"Code","",
                "","N",self.doCode,ced,None,("notzero",)),
            (("T",0,0,0),"ONA",30,"Description"),
            (("T",1,0,0),"INA",30,"Description","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)),
            (("T",1,1,0),("IRB",r1s),0,"Type","",
                "V","N",None,None,None,None),
            (("T",1,2,0),("IRB",r2s),0,"Employee Portion","",
                "A","N",self.doEmployeePortion,None,None,None),
            (("T",1,3,0),"IUI",3,"         Base","",
                "","N",self.doEmployeeBase,bas,None,("between",0,7)),
            (("T",1,4,0),"IUD",8.2,"         Value","",
                "","N",self.doValue,None,None,("efld",)),
            (("T",1,5,0),"IUD",8.2,"         Limit","",
                "","N",self.doElim,None,None,("efld",)),
            (("T",1,6,0),"IUI",3,"         GL/Cono","",
                "","N",self.doEglco,coy,None,("efld",)),
            (("T",1,6,0),"IUI",7,"         GL/Acno","",
                "","N",self.doEglno,glm,None,("efld",)),
            (("T",1,7,0),("IRB",r3s),0,"Earnings Type","",
                "S","N",self.doEarnType,None,None,None),
            (("T",1,8,0),("IRB",r4s),0,"Employer Portion","",
                "N","N",self.doEmployerPortion,None,None,None),
            (("T",1,9,0),"IUI",3,"         Base","Base",
                "","N",self.doEmployerBase,bas,None,("between",0,7)),
            (("T",1,10,0),"IUD",8.2,"         Value","",
                "","N",None,None,None,("efld",)),
            (("T",1,11,0),"IUD",8.2,"         Limit","",
                "","N",self.doRlim,None,None,("efld",)),
            (("T",1,12,0),"IUI",3,"         GL/Cono","",
                "","N",self.doRglco,coy,None,("efld",)),
            (("T",1,12,0),"IUI",7,"         GL/Acno","",
                "","N",self.doRglno,glm,None,("efld",)),
            (("T",1,13,0),("IRB",r5s),0,"Tax Code","",
                "N","N",self.doTaxcode,None,None,None),
            (("T",1,14,0),"IUD",6.2,"Tax Portion","",
                "","N",self.doTaxportion,None,None,("efld",)),
            (("T",2,0,0),"IUI",4,"Rec Of Rev Code","",
                "","N",self.doRcv,rcv,None,("notzero",)),
            (("T",2,0,0),"ONA",30,""),
            (("T",2,1,0),("IRB",r6s),0,"Union Report","",
                "N","N",self.doUniRep,None,None,None),
            (("T",2,2,0),("IRB",r6s),0,"Must Pay","",
                "N","N",None,None,None,None),
            (("T",2,3,0),"IUI",2,"Balance Number","",
                "","N",self.doBalNo,None,None,("between",0,3)),
            (("T",2,4,0),"IUD",5.2,"Hourly Limit","",
                "","N",self.doLimit,None,None,("efld",)),
            (("T",2,5,0),("IRB",r6s),0,"Monthly Deduction","",
                "N","N",self.doMthly,None,None,None),
            (("T",2,6,0),"IUD",6.2,"UIF Percentage","",
                "","N",None,None,None,("efld",)),
            (("T",2,7,0),"IUD",6.2,"SDL Percentage","",
                "","N",None,None,None,("efld",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",1,1),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",1,1),("T",0,0)),
            ("Quit",None,self.doExit0,1,None,None))
        tnd = ((self.doEnd0,"N"), (self.doEnd1,"N"), (self.doEnd2,"Y"))
        txt = (self.doExit0, self.doExit1, self.doExit2)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tags=tag, butt=but, tend=tnd, txit=txt)

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtype = w
        if self.rtype == "E":
            self.df.topf[1][15][5] = "Y"
        else:
            self.df.topf[1][15][5] = "Y"

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.acc = self.sql.getRec("wagedc", where=[("ced_cono", "=",
            self.opts["conum"]), ("ced_type", "=", self.rtype), ("ced_code",
            "=", self.code)], limit=1)
        if not self.acc:
            self.new = True
            if self.rtype == "D" and self.code == 1:
                showInfo(self.opts["mf"].body, "PAYE",
                    "This code is Reserved for PAYE Deductions")
            elif self.rtype == "D" and self.code == 2:
                showInfo(self.opts["mf"].body, "UIF",
                    "This code is Reserved for UIF Deductions")
        else:
            self.new = False
            d = 3
            self.df.loadEntry(frt, pag, p+1, data=self.acc[d])
            for pg in range(1, self.df.pgs+1):
                for x in range(0, self.df.topq[pg]):
                    if pg == 2 and x == 1:
                        continue
                    self.df.loadEntry("T", pg, x, data=self.acc[d])
                    if pg == 2 and not x:
                        ror = self.sql.getRec("wagrcv", limit=1,
                            cols=["rcv_desc"], where=[("rcv_code", "=",
                            self.acc[d])])
                        if not ror:
                            desc = ""
                        else:
                            desc = ror[0]
                        self.df.loadEntry("T", 2, 1, data=desc)
                    d = d + 1

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry("T", 0, 2, data=self.df.t_disp[1][0][0])
        if self.rtype == "E" and self.code < 6:
            self.df.loadEntry("T", 1, p+1, data="V")
            self.df.loadEntry("T", 1, p+2, data="R")
            if self.code == 5:
                self.df.loadEntry("T", 1, p+3, data=4)
            else:
                self.df.loadEntry("T", 1, p+3, data=1)
            if self.code in (1, 5):
                self.df.loadEntry("T", 1, p+4, data=1)
                self.df.loadEntry("T", 1, p+5, data=0)
                if self.glint != "Y":
                    self.df.loadEntry("T", 1, p+6, data=0)
                    self.df.loadEntry("T", 1, p+7, data=0)
                    self.df.loadEntry("T", 1, p+8, data="S")
                    return "sk8"
                else:
                    return "sk5"
            else:
                return "sk3"
        elif self.rtype == "D" and self.code in (1, 2):
            if self.code == 1:
                self.df.loadEntry("T", 1, 1, data="V")
                self.df.loadEntry("T", 1, 2, data="R")
                if self.glint != "Y":
                    self.df.loadEntry("T", 1, p+6, data=0)
                    self.df.loadEntry("T", 1, p+7, data=0)
                    self.df.loadEntry("T", 1, p+9, data="N")
                    self.df.loadEntry("T", 1, p+15, data="N")
                    return "nd"
                return "sk5"
            elif self.code == 2:
                self.df.loadEntry("T", 1, 1, data="V")
                self.df.loadEntry("T", 1, 2, data="R")
                self.df.loadEntry("T", 1, 3, data=6)
                return "sk3"

    def doDelete(self):
        t = self.sql.getRec("wagtf2", cols=["count(*)"],
            where=[("wt2_cono", "=", self.opts["conum"]), ("wt2_type", "=",
            self.rtype), ("wt2_code", "=", self.code)], limit=1)
        if t[0]:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("wagedc", where=[("ced_cono", "=", self.opts["conum"]),
            ("ced_type", "=", self.rtype), ("ced_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEmployeePortion(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doEmployeeBase(self, frt, pag, r, c, p, i, w):
        if w > 7:
            return "Invalid Employee Base"

    def doValue(self, frt, pag, r, c, p, i, w):
        self.value = w
        if self.rtype == "E" and self.code < 6:
            self.df.loadEntry("T", 1, p+1, data=0)
            if self.glint != "Y":
                self.df.loadEntry("T", 1, p+2, data=0)
                self.df.loadEntry("T", 1, p+3, data=0)
                self.df.loadEntry("T", 1, p+4, data="S")
                return "sk3"
            else:
                return "sk1"

    def doElim(self, frt, pag, r, c, p, i, w):
        self.elim = w
        if self.glint != "Y":
            self.df.loadEntry("T", 1, p+1, data=0)
            self.df.loadEntry("T", 1, p+2, data=0)
            if self.rtype == "E":
                return "sk2"
            else:
                self.df.loadEntry("T", 1, p+3, data="")
                return "sk3"

    def doEglco(self, frt, pag, r, c, p, i, w):
        if self.rtype == "E" and self.code < 6 and not w:
            # Use department code for integration
            self.eglco = w
            self.df.loadEntry("T", 1, p+1, data=0)
            self.df.loadEntry("T", 1, p+2, data="S")
            self.df.loadEntry("T", 1, p+9, data="Y")
            self.df.loadEntry("T", 1, p+10, data=100.00)
            return "sk10"
        if w:
            self.eglco = w
        else:
            self.eglco = self.opts["conum"]
        name = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", self.eglco)], limit=1)
        if not name:
            return "Invalid Company"

    def doEglno(self, frt, pag, r, c, p, i, w):
        if self.rtype == "D":
            ctl = self.gc.getCtl("ctlctl", self.eglco)
            if ctl and not self.gc.chkRec(self.eglco, ctl, ["wag_slc"]):
                sln = ctl["wag_slc"]
            else:
                sln = None
        else:
            sln = None
        if w and w != sln:
            chk = chkGenAcc(self.opts["mf"], self.eglco, w)
            if type(chk) is str:
                return chk
        self.eglno = w
        if self.rtype == "D":
            if self.code == 2:
                self.df.loadEntry(frt, pag, 9, data="R")
                self.df.loadEntry(frt, pag, 10, data=6)
                self.df.loadEntry(frt, pag, 11, data=self.value)
                self.df.loadEntry(frt, pag, 12, data=self.elim)
                self.df.loadEntry(frt, pag, 13, data=self.eglco)
                self.df.loadEntry(frt, pag, 14, data=self.eglno)
                return "sk7"
            else:
                return "sk1"
        if self.code < 6:
            self.df.loadEntry("T", 1, p+1, data="S")
            self.df.loadEntry("T", 1, p+8, data="Y")
            self.df.loadEntry("T", 1, p+9, data=100.00)
            return "sk9"

    def doEarnType(self, frt, pag, r, c, p, i, w):
        if self.rtype == "E":
            return "sk6"

    def doEmployerPortion(self, frt, pag, r, c, p, i, w):
        if w == "N":
            for x in range(1, 6):
                self.df.loadEntry(frt, pag, p+x, data=0)
            return "sk5"
        if w == "A":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doEmployerBase(self, frt, pag, r, c, p, i, w):
        if w > 7:
            return "Invalid Employer Base"

    def doRlim(self, frt, pag, r, c, p, i, w):
        if self.glint != "Y":
            return "sk2"

    def doRglco(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.opts["conum"]
        name = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)], limit=1)
        if not name:
            return "Invalid Company"
        self.rglco = w

    def doRglno(self, frt, pag, r, c, p, i, w):
        if w:
            chk = chkGenAcc(self.opts["mf"], self.rglco, w)
            if type(chk) is str:
                return chk

    def doTaxcode(self, frt, pag, r, c, p, i, w):
        if self.rtype == "D" and w not in ("Y", "T", "N"):
            return "Invalid Selection"
        if w == "N":
            self.df.loadEntry("T", pag, p+1, data=0)
            return "sk1"
        if self.glint == "Y" and not self.eglno and w != "T":
            return "ff8|Invalid G/L Account Number"

    def doTaxportion(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Tax Portion"

    def doRcv(self, frt, pag, r, c, p, i, w):
        if w == 4101:
            return "SITE Code Not Allowed"
        acc = self.sql.getRec("wagrcv", cols=["rcv_desc"],
            where=[("rcv_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Rec of Rev Code"
        else:
            self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doUniRep(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry(frt, pag, p+1, data="N")
        if self.rtype == "E":
            if self.code in (1, 2, 3, 4, 5):
                self.df.loadEntry(frt, pag, p+2, data=0)
                self.df.loadEntry(frt, pag, p+3, data=0)
                self.df.loadEntry(frt, pag, p+4, data="N")
                self.df.loadEntry(frt, pag, p+5, data=100.00)
                return "sk5"
            return "sk4"
        return "sk1"

    def doBalNo(self, frt, pag, r, c, p, i, w):
        if self.rtype == "E":
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data="N")
            self.df.loadEntry(frt, pag, p+3, data="N")
            return "sk3"

    def doLimit(self, frt, pag, r, c, p, i, w):
        pass

    def doMthly(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry(frt, pag, p+1, data=0)
        return "sk1"

    def doEnd0(self):
        self.df.focusField("T", 1, 1, clr=self.new)

    def doEnd1(self):
        self.df.selPage("Detail-_B")
        self.df.focusField("T", 2, 1, clr=self.new)

    def doEnd2(self):
        dat = [self.opts["conum"]]
        for x in range(0, 2):
            dat.append(self.df.t_work[0][0][x])
        for x in range(0, len(self.df.t_work[1][0])):
            dat.append(self.df.t_work[1][0][x])
        for x in range(0, len(self.df.t_work[2][0])):
            if x in (0,2,3,4,5,6,7,8):
                dat.append(self.df.t_work[2][0][x])
        if self.new:
            self.sql.insRec("wagedc", data=dat)
        elif dat != self.acc[:len(dat)]:
            col = self.sql.wagedc_col
            dat.append(self.acc[col.index("ced_xflag")])
            self.sql.updRec("wagedc", data=dat, where=[("ced_cono",
                "=", self.opts["conum"]), ("ced_type", "=", self.rtype),
                ("ced_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.last[0] = [0, 0]
        self.df.selPage("Detail-_A")
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        if self.rtype == "D":
            frt, pag, col, mes = self.df.doCheckFields(("T",0,None))
            if not mes:
                frt, pag, col, mes = self.df.doCheckFields(
                    ("T",1,(0,1,2,3,4,5,6,7,9,10,11,12,13,14)))
                if not mes:
                    if self.df.t_work[1][0][15] not in ("Y","N","T","O","R"):
                        frt = "T"
                        pag = 1
                        col = 15
                        mes = "Invalid Tax Code Selection"
                    if not mes:
                        frt, pag, col, mes = self.df.doCheckFields(
                            ("T",1,(16,)))
                        if not mes:
                            frt, pag, col, mes = self.df.doCheckFields(
                                ("T",2,(0,2,3,4,5,6)))
        else:
            frt, pag, col, mes = self.df.doCheckFields(("T",0,None))
            if not mes:
                frt, pag, col, mes = self.df.doCheckFields(
                    ("T",1,(0,1,2,3,4,5,6,7,8,15,16)))
                if not mes:
                    frt, pag, col, mes = self.df.doCheckFields(
                        ("T",2,(0,2,3)))
        if mes:
            if pag > 0 and pag != self.df.pag:
                if frt == "T":
                    self.df.last[pag][0] = col+1
                else:
                    self.df.last[pag][1] = col+1
                self.df.selPage(self.df.tags[pag - 1][0])
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.doEnd2()

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit0(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doExit1(self):
        self.df.focusField("T", 0, 1)

    def doExit2(self):
        self.df.selPage("Detail-_A")

# vim:set ts=4 sw=4 sts=4 expandtab:
