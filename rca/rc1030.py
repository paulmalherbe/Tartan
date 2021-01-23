"""
SYNOPSIS
    Rental System Tenants Maintenance.

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
from TartanClasses import Sql, TartanDialog

class rc1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "rcaprm", "rcaowm",
            "rcatnm", "rcacon", "rcatnt", "chglog"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        own = {
            "stype": "R",
            "tables": ("rcaowm",),
            "cols": (
                ("rom_acno", "", 0, "Acc-Num"),
                ("rom_name", "", 0, "Name", "Y")),
            "where": [("rom_cono", "=", self.opts["conum"])]}
        prm = {
            "stype": "R",
            "tables": ("rcaprm",),
            "cols": (
                ("rcp_code", "", 0, "Prm-Code"),
                ("rcp_addr1", "", 0, "Address-Line-1")),
            "where": [("rcp_cono", "=", self.opts["conum"])],
            "whera": (("T", "rcp_owner", 0, 0),)}
        acc = {
            "stype": "R",
            "tables": ("rcatnm",),
            "cols": (
                ("rtn_acno", "", 0, "Acc-Num"),
                ("rtn_name", "", 0, "Name", "Y")),
            "where": [("rtn_cono", "=", self.opts["conum"])],
            "whera": (("T", "rtn_owner", 0, 0), ("T", "rtn_code", 1, 0))}
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": ((4, "Services (Owner)"), (5, "Services (Agency)"))}
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually", "6"),
            ("Annually","A"))
        self.fld = (
            (("T",0,0,0),"INA",7,"Owners Code","",
                "","Y",self.doOwner,own,None,("notblank",)),
            (("T",0,1,0),"INA",7,"Premises Code","",
                "","Y",self.doPremises,prm,None,("notblank",)),
            (("T",0,2,0),"INA",7,"Account Code","",
                "","N",self.doAccount,acc,None,("notblank",)),
            (("T",0,3,0),"INA",30,"Tenant Name","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,4,0),"INA",30,"Address Line 1","",
                "","N",self.doAddr,None,None,("efld",)),
            (("T",0,5,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"INA",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",0,10,0),"INA",10,"VAT Number","",
                "","N",self.doVatNum,None,None,("efld",)),
            (("T",0,11,0),("IRB",r1s),0,"Payment Frequency","",
                "M","N",None,None,None,None),
            (("T",0,12,0),"ID1",10,"Start Date","",
                "","N",None,None,None,("notzero",)),
            (("T",0,13,0),"IUI",3,"Number of Periods","Periods",
                "","N",None,None,None,("notzero",)),
            (("T",0,14,0),"IUD",12.2,"Rental Amount","",
                "","N",None,None,None,("notzero",)),
            (("T",0,15,0),"IUD",12.2,"Deposit Amount","",
                "","N",None,None,None,("efld",)),
            (("T",0,16,0),"IUD",12.2,"Basic Water Amount","",
                "","N",self.doBWater,None,None,("efld",)),
            (("T",0,16,0),"IUI",1,"Type","",
                "","N",None,typ,None,("efld",)),
            (("T",0,17,0),"IUD",12.2,"Basic Exlectricity Amount","",
                "","N",self.doBElec,None,None,("efld",)),
            (("T",0,17,0),"IUI",1,"Type","",
                "","N",self.doEType,typ,None,("efld",)),
            (("T",0,18,0),"IUA",1,"Status","",
                "","N",None,None,None,("in",("C","X"))))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doOwner(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaowm", cols=["rom_name"],
            where=[("rom_cono", "=", self.opts["conum"]), ("rom_acno", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Owner"
        self.owner = w

    def doPremises(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaprm", cols=["rcp_desc"],
            where=[("rcp_cono", "=", self.opts["conum"]), ("rcp_owner", "=",
            self.owner), ("rcp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises"
        self.code = w

    def doAccount(self, frt, pag, r, c, p, i, w):
        self.acno = w
        self.oldm = self.sql.getRec("rcatnm", where=[("rtn_cono", "=",
            self.opts["conum"]), ("rtn_owner", "=", self.owner), ("rtn_code",
            "=", self.code), ("rtn_acno", "=", self.acno)], limit=1)
        if not self.oldm:
            self.new = "y"
            for num in range(4, self.df.topq[0]):
                self.df.clearEntry(frt, pag, num+1)
            con = self.sql.getRec("rcacon", cols=["count(*)"],
                where=[("rcc_cono", "=", self.opts["conum"]), ("rcc_owner",
                "=", self.owner), ("rcc_code", "=", self.code), ("rcc_acno",
                "=", self.acno)], limit=1)
            if not con[0]:
                self.cnum = 1
            else:
                self.cnum = con[0] + 1
        else:
            self.new = "n"
            for num, fld in enumerate(self.oldm[3:]):
                self.df.loadEntry(frt, pag, p+num, data=fld)
            oldc = self.sql.getRec("rcacon", where=[("rcc_cono",
                "=", self.opts["conum"]), ("rcc_owner", "=", self.owner),
                ("rcc_code", "=", self.code), ("rcc_acno", "=", self.acno)],
                order="rcc_cnum")
            self.oldc = oldc[-1:][0]
            self.cnum = self.oldc[4]
            for num, fld in enumerate(self.oldc[5:-1]):
                self.df.loadEntry(frt, pag, num+11, data=fld)
            trn = self.sql.getRec("rcatnt", cols=["count(*)"],
                where=[("rtu_cono", "=", self.opts["conum"]), ("rtu_owner",
                "=", self.owner), ("rtu_code", "=", self.code), ("rtu_acno",
                "=", self.acno)], limit=1)
            if trn[0]:
                self.trn = True
            else:
                self.trn = False

    def doAddr(self, frt, pag, r, c, p, i, w):
        if not w:
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            self.df.loadEntry(frt, pag, p+3, data="")
            return "sk3"

    def doVatNum(self, frt, pag, r, c, p, i, w):
        if self.new == "n" and self.trn:
            return "sk1"

    def doBWater(self, frt, pag, r, c, p, i, w):
        if not w:
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doBElec(self, frt, pag, r, c, p, i, w):
        if not w:
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doEType(self, frt, pag, r, c, p, i, w):
        if self.new == "y":
            self.df.loadEntry(frt, pag, p+1, data="C")

    def doDelete(self):
        if self.trn:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("rcatnm", where=[("rtn_cono", "=", self.opts["conum"]),
            ("rtn_owner", "=", self.owner), ("rtn_code", "=", self.code),
            ("rtn_acno", "=", self.acno)])
        self.sql.delRec("rcacon", where=[("rcc_cono", "=", self.opts["conum"]),
            ("rcc_owner", "=", self.owner), ("rcc_code", "=", self.code),
            ("rcc_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rcatnm", "D", "%03i%-7s" % \
            (self.opts["conum"], self.code), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        datm = [self.opts["conum"]]
        datc = [self.opts["conum"], self.owner, self.code, self.acno, self.cnum]
        for num, fld in enumerate(self.df.t_work[0][0]):
            if num < 11:
                datm.append(fld)
            if num > 10:
                datc.append(fld)
        if self.new == "y":
            self.sql.insRec("rcatnm", data=datm)
            self.sql.insRec("rcacon", data=datc)
        else:
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            if datm != self.oldm[:len(datm)]:
                col = self.sql.rcatnm_col
                datm.append(self.oldm[col.index("rtn_xflag")])
                self.sql.updRec("rcatnm", data=datm, where=[("rtn_cono", "=",
                    self.opts["conum"]), ("rtn_owner", "=", self.owner),
                    ("rtn_code", "=", self.code), ("rtn_acno", "=",
                    self.acno)])
                for num, dat in enumerate(self.oldm):
                    if dat != datm[num]:
                        self.sql.insRec("chglog", data=["rcatnm", "U",
                            "%03i%-7s%-7s" % (self.opts["conum"], self.owner,
                            self.code), col[num], dte, self.opts["capnm"],
                            str(dat), str(datm[num]), "", 0])
            if datc != self.oldc[:len(datc)]:
                col = self.sql.rcacon_col
                datc.append(self.oldc[col.index("rcc_xflag")])
                self.sql.updRec("rcacon", data=datc, where=[("rcc_cono", "=",
                    self.opts["conum"]), ("rcc_owner", "=", self.owner),
                    ("rcc_code", "=", self.code), ("rcc_acno", "=", self.acno),
                    ("rcc_cnum", "=", self.cnum)])
                for num, dat in enumerate(self.oldc):
                    if dat != datc[num]:
                        self.sql.insRec("chglog", data=["rcacon", "U",
                            "%03i%-7s%-7s%-7s%03i" % (self.opts["conum"],
                            self.owner, self.code, self.acno, self.cnum),
                            col[num], dte, self.opts["capnm"], str(dat),
                            str(datc[num]), "", 0])
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
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
