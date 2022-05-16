"""
SYNOPSIS
    Rental System Masterfile Maintenance.

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
from TartanClasses import CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import projectDate

class rt1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "rtlprm", "rtlmst",
            "rtlcon", "rtltrn", "chglog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        return True

    def mainProcess(self):
        prm = {
            "stype": "R",
            "tables": ("rtlprm",),
            "cols": (
                ("rtp_code", "", 0, "Prm-Code"),
                ("rtp_desc", "", 0, "Description", "Y")),
            "where": [("rtp_cono", "=", self.opts["conum"])]}
        acc = {
            "stype": "R",
            "tables": ("rtlmst",),
            "cols": (
                ("rtm_acno", "", 0, "Acc-Num"),
                ("rtm_name", "", 0, "Name", "Y")),
            "where": [("rtm_cono", "=", self.opts["conum"])],
            "whera": (("T", "rtm_code", 0, 0),)}
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually", "6"),
            ("Annually","A"))
        r2s = (("Current","C"), ("Expired","X"))
        self.fld = (
            (("T",0,0,0),"INA",7,"Premises Code","",
                "","Y",self.doPremises,prm,None,("notblank",)),
            (("T",0,1,0),"INA",7,"Account Code","",
                "","N",self.doAccount,acc,None,("notblank",)),
            (("T",0,2,0),"INA",30,"Tenant Name","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"INA",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",0,9,0),"IUA",1,"VAT Indicator","",
                self.taxdf,"N",None,None,None,("notblank",)),
            (("T",0,10,0),"INA",10,"VAT Number","",
                "","N",self.doVatNum,None,None,("efld",)),
            (("T",0,11,0),("IRB",r1s),0,"Payment Frequency","",
                "M","N",None,None,None,None),
            (("T",0,12,0),"ID1",10,"Start Date","",
                "","N",self.doStart,None,None,("notzero",)),
            (("T",0,13,0),"IUI",3,"Number of Periods","",
                "","N",None,None,None,("notzero",)),
            (("T",0,14,0),"IUD",12.2,"Rental Amount","",
                "","N",self.doAmount,None,None,("notzero",)),
            (("T",0,15,0),("IRB",r2s),0,"Status","",
                "","N",None,None,None,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)
        if "args" in self.opts:
            self.df.doKeyPressed("T", 0, 0, data=self.opts["args"][0])
            self.df.doKeyPressed("T", 0, 1, data=self.opts["args"][1])

    def doPremises(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlprm", cols=["rtp_desc"],
            where=[("rtp_cono", "=", self.opts["conum"]), ("rtp_code", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Premises"
        self.code = w
        col = ["rtc_payind", "rtc_start", "rtc_period"]
        whr = [
            ("rtc_cono", "=", self.opts["conum"]),
            ("rtc_code", "=", self.code),
            ("rtc_status", "=", "C")]
        chk = self.sql.getRec("rtlcon", cols=col, where=whr,
            order="rtc_start desc")
        if not chk:
            self.end = 0
            return
        freq, start, period = chk[0]
        if freq == "M":
            self.end = CCD(projectDate(start, period, "months"), "D1", 10)
        elif freq == "3":
            self.end = CCD(projectDate(start, period * 3, "months"), "D1", 10)
        elif freq == "6":
            self.end = CCD(projectDate(start, period * 6, "months"), "D1", 10)
        else:
            self.end = CCD(projectDate(start, period, "years"), "D1", 10)

    def doAccount(self, frt, pag, r, c, p, i, w):
        self.acno = w
        self.oldm = self.sql.getRec("rtlmst", where=[("rtm_cono", "=",
            self.opts["conum"]), ("rtm_code", "=", self.code), ("rtm_acno",
            "=", self.acno)], limit=1)
        if not self.oldm:
            self.new = "y"
            for num in range(2, self.df.topq[0]):
                self.df.clearEntry(frt, pag, num+1)
            con = self.sql.getRec("rtlcon", cols=["count(*)"],
                where=[("rtc_cono", "=", self.opts["conum"]), ("rtc_code", "=",
                self.code), ("rtc_acno", "=", self.acno)], limit=1)
            if not con[0]:
                self.cnum = 1
            else:
                self.cnum = con[0] + 1
        else:
            self.new = "n"
            for num, fld in enumerate(self.oldm[2:]):
                self.df.loadEntry(frt, pag, p+num, data=fld)
            self.oldc = self.sql.getRec("rtlcon", where=[("rtc_cono",
                "=", self.opts["conum"]), ("rtc_code", "=", self.code),
                ("rtc_acno", "=", self.acno)], order="rtc_cnum")
            self.cnum = self.oldc[-1:][0][3]
            for num, fld in enumerate(self.oldc[-1:][0][4:-1]):
                self.df.loadEntry(frt, pag, num+11, data=fld)
            trn = self.sql.getRec("rtltrn", cols=["count(*)"],
                where=[("rtt_cono", "=", self.opts["conum"]), ("rtt_code", "=",
                self.code), ("rtt_acno", "=", self.acno)], limit=1)
            if trn[0]:
                self.trn = True
            else:
                self.trn = False

    def doVatNum(self, frt, pag, r, c, p, i, w):
        if self.new == "n" and self.trn:
            return "sk1"

    def doStart(self, frt, pag, r, c, p, i, w):
        if self.new == "y" and self.end and w < self.end.work:
            return "Premises Already Let till %s" % self.end.disp

    def doAmount(self, frt, pag, r, c, p, i, w):
        if self.new == "y":
            self.df.loadEntry(frt, pag, p+1, data="C")

    def doDelete(self):
        if self.trn:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("rtlmst", where=[("rtm_cono", "=", self.opts["conum"]),
            ("rtm_code", "=", self.code), ("rtm_acno", "=", self.acno)])
        self.sql.delRec("rtlcon", where=[("rtc_cono", "=", self.opts["conum"]),
            ("rtc_code", "=", self.code), ("rtc_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rtlmst", "D", "%03i%-7s" %
            (self.opts["conum"], self.code), "", dte, self.opts["capnm"],
            "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        datm = [self.opts["conum"]]
        datc = [self.opts["conum"], self.code, self.acno, self.cnum]
        for num, fld in enumerate(self.df.t_work[0][0]):
            if num < 11:
                datm.append(fld)
            if num > 10:
                datc.append(fld)
        if self.new == "y":
            self.sql.insRec("rtlmst", data=datm)
            self.sql.insRec("rtlcon", data=datc)
        else:
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            if datm != self.oldm[:len(datm)]:
                col = self.sql.rtlmst_col
                datm.append(self.oldm[col.index("rtm_xflag")])
                self.sql.updRec("rtlmst", data=datm, where=[("rtm_cono", "=",
                    self.opts["conum"]), ("rtm_code", "=", self.code),
                    ("rtm_acno", "=", self.acno)])
                for num, dat in enumerate(self.oldm):
                    if dat != datm[num]:
                        self.sql.insRec("chglog", data=["rtlmst", "U",
                            "%03i%-7s" % (self.opts["conum"], self.code),
                            col[num], dte, self.opts["capnm"], str(dat),
                            str(datm[num]), "", 0])
            if datc != self.oldc[-1:][0][:len(datc)]:
                col = self.sql.rtlcon_col
                datc.append(self.oldc[col.index("rtc_xflag")])
                self.sql.updRec("rtlcon", data=datc, where=[("rtc_cono", "=",
                    self.opts["conum"]), ("rtc_code", "=", self.code),
                    ("rtc_acno", "=", self.acno), ("rtc_cnum", "=",
                    self.cnum)])
                for num, dat in enumerate(self.oldc[-1:][0]):
                    if dat != datc[num]:
                        self.sql.insRec("chglog", data=["rtlcon", "U",
                        "%03i%-7s%-7s%03i" % (self.opts["conum"], self.code,
                        self.acno, self.cnum), col[num], dte,
                        self.opts["capnm"], str(dat), str(datc[num]),
                        "", 0])
        if "args" in self.opts:
            self.doExit()
        else:
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
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
