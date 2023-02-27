"""
SYNOPSIS
    Rental System Owners Maintenance.

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

class rc1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "rcaowm", "rcaowt",
            "chglog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        return True

    def mainProcess(self):
        own = {
            "stype": "R",
            "tables": ("rcaowm",),
            "cols": (
                ("rom_acno", "", 0, "Acc-Num"),
                ("rom_name", "", 0, "Name", "Y")),
            "where": [("rom_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"INA",7,"Account Number","",
                "","Y",self.doOwner,own,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Name","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"INA",4,"Postal Code","PCod",
                "","N",None,None,None,("notblank",)),
            (("T",0,6,0),"INA",20,"Home Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"INA",20,"Office Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"INA",20,"Mobile Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"INA",20,"Fax Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",0,11,0),"INA",10,"VAT Number","VAT-Number",
                "","N",None,None,None,("efld",)),
            (("T",0,12,0),"IUA",1,"VAT Default","V",
                "","N",None,None,None,("efld",)),
            (("T",0,13,0),"INA",20,"Bank Name","Bank-Name",
                "","N",None,None,None,("efld",)),
            (("T",0,14,0),"IUI",8,"Bank Branch","Bank-IBT",
                "","N",None,None,None,("efld",)),
            (("T",0,15,0),"INA",16,"Bank Account","Bank-Account-Num",
                "","N",None,None,None,("efld",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doOwner(self, frt, pag, r, c, p, i, w):
        self.acno = w
        self.oldm = self.sql.getRec("rcaowm", where=[("rom_cono", "=",
            self.opts["conum"]), ("rom_acno", "=", self.acno)], limit=1)
        if not self.oldm:
            self.new = "y"
            for num in range(2, self.df.topq[0]):
                self.df.clearEntry(frt, pag, num+1)
        else:
            self.new = "n"
            for num, fld in enumerate(self.oldm[1:-1]):
                self.df.loadEntry(frt, pag, p+num, data=fld)
            trn = self.sql.getRec("rcaowt", cols=["count(*)"],
                where=[("rot_cono", "=", self.opts["conum"]), ("rot_acno", "=",
                self.acno)], limit=1)
            if trn[0]:
                self.trn = True
            else:
                self.trn = False

    def doName(self, frt, pag, r, c, p, i, w):
        pass

    def doTelno(self, frt, pag, r, c, p, i, w):
        pass

    def doEmail(self, frt, pag, r, c, p, i, w):
        pass

    def doVatInd(self, frt, pag, r, c, p, i, w):
        pass

    def doVatNum(self, frt, pag, r, c, p, i, w):
        if self.new == "n" and self.trn:
            return "sk1"

    def doStart(self, frt, pag, r, c, p, i, w):
        pass

    def doPeriod(self, frt, pag, r, c, p, i, w):
        pass

    def doPayInd(self, frt, pag, r, c, p, i, w):
        pass

    def doAmount(self, frt, pag, r, c, p, i, w):
        if self.new == "y":
            self.df.loadEntry(frt, pag, p+1, data="C")

    def doStatus(self, frt, pag, r, c, p, i, w):
        pass

    def doDelete(self):
        if self.trn:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("rcaowm", where=[("rom_cono", "=", self.opts["conum"]),
            ("rom_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rcaowm", "D", "%03i%-7s" % \
            (self.opts["conum"], self.acno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        datm = [self.opts["conum"]]
        for num, fld in enumerate(self.df.t_work[0][0]):
            datm.append(fld)
        if self.new == "y":
            self.sql.insRec("rcaowm", data=datm)
        elif datm != self.oldm[:len(datm)]:
            col = self.sql.rcaowm_col
            datm.append(self.oldm[col.index("rom_xflag")])
            self.sql.updRec("rcaowm", data=datm, where=[("rom_cono", "=",
                self.opts["conum"]), ("rom_acno", "=", self.acno)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.oldm):
                if dat != datm[num]:
                    self.sql.insRec("chglog", data=["rcaowm", "U",
                        "%03i%-7s" % (self.opts["conum"], self.acno),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(datm[num]), "", 0])
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
