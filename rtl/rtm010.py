"""
SYNOPSIS
    Rentals Ledger Month End Routine.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2025 Paul Malherbe.

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
from TartanClasses import ASD, CCD, GetCtl, PwdConfirm, Sql, TartanDialog
from tartanFunctions import askQuestion, getVatRate, mthendDate

class rtm010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlbat", "ctlvrf", "ctlvtf",
            "gentrn", "rtlctl", "rtlprm", "rtlmst", "rtlcon", "rtltrn"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        self.glint = rtlctl["ctr_glint"]
        self.lme = rtlctl["ctr_lme"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if gc.chkRec(self.opts["conum"], ctlctl, ["vat_ctl"]):
                return
            self.convat = ctlctl["vat_ctl"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.tme = mthendDate(self.sysdtw)
        return True

    def mainProcess(self):
        fld = (
            (("T",0,0,0),"Od1",10,"Last Month End Date"),
            (("T",0,1,0),"ID1",10,"This Month End Date","",
                self.tme,"N",self.doTme,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, focus=False)
        self.df.loadEntry("T", 0, 0, data=self.lme)
        self.df.focusField("T", 0, 2)

    def doTme(self, frt, pag, r, c, p, i, w):
        if w <= self.lme:
            return "Invalid Month-End Date"
        self.tme = w
        self.curdt = int(w / 100)
        yy = int(self.curdt / 100)
        mm = (self.curdt % 100) + 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nxtdt = (yy * 10000) + (mm * 100) + 1
        self.nxtcd = int(self.nxtdt / 100)
        self.batch = "R%06s" % self.nxtcd
        chk = self.sql.getRec("rtltrn", cols=["count(*)"],
            where=[("rtt_cono", "=", self.opts["conum"]), ("rtt_type", "=", 1),
            ("rtt_batch", "=", self.batch), ("rtt_trdt", "=", self.nxtdt),
            ("rtt_curdt", "=", self.nxtcd)], limit=1)
        if chk[0]:
            return "Month-End Already Executed"

    def doEnd(self):
        recs = self.sql.getRec("ctlbat", cols=["count(*)"],
            where=[("btm_cono", "=", self.opts["conum"]), ("btm_styp", "=",
            "RTL"), ("btm_ind", "=", "N"), ("btm_curdt", "=", self.curdt)],
            limit=1)
        if recs[0]:
            ok = askQuestion(self.opts["mf"].body, "Unbalanced Batches Exist",
                "There are unbalanced batches for this month. You "\
                "SHOULD not continue, but print a batch error report, and "\
                "correct the errors. Continue, YES or NO ?", default="no")
            if ok == "yes":
                ok = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                    system="RTL", code="UnbalBatch")
                if ok.flag == "no":
                    self.closeProcess()
                else:
                    self.updateTables()
            else:
                self.closeProcess()
        else:
            self.updateTables()

    def updateTables(self):
        self.df.closeProcess()
        whr = [
            ("rtc_cono", "=", self.opts["conum"]),
            ("rtm_cono=rtc_cono",),
            ("rtm_code=rtc_code",),
            ("rtm_acno=rtc_acno",),
            ("rtc_start", "<=", self.nxtdt),
            ("rtc_status", "<>", "X")]
        recs = self.sql.getRec(tables=["rtlcon", "rtlmst"], cols=["rtc_cono",
            "rtc_code", "rtc_acno", "rtc_cnum", "rtc_payind", "rtc_start",
            "rtc_period", "rtc_rtlamt", "rtm_name", "rtm_vatind"], where=whr)
        if recs:
            for num, self.rec in enumerate(recs):
                self.freq = self.rec[4]
                strt = self.rec[5]
                self.pers = self.rec[6]
                self.amnt = self.rec[7]
                if self.freq == "M":
                    mths = 1 * self.pers
                elif self.freq == "3":
                    mths = 3 * self.pers
                elif self.freq == "6":
                    mths = 6 * self.pers
                else:
                    mths = 12 * self.pers
                yy = int(strt / 10000)
                mm = int((strt % 10000) / 100) + mths - 1
                while mm > 12:
                    yy += 1
                    mm -= 12
                dd = strt % 100
                self.exdt = (yy * 10000) + (mm * 100) + dd
                if int(self.exdt / 100) <= self.curdt:
                    self.sql.updRec("rtlcon", cols=["rtc_status"], data=["X"],
                        where=[("rtc_cono", "=", self.rec[0]), ("rtc_code",
                        "=", self.rec[1]), ("rtc_acno", "=", self.rec[2]),
                        ("rtc_cnum", "=", self.rec[3])])
                    ok = askQuestion(self.opts["mf"].body, "Expired Contract",
                        "This contract has Expired, would you like to "\
                        "Renew it?\n\nPremises: %s\nAccount: %s\nName: %s" % \
                        (self.rec[1], self.rec[2], self.rec[8]))
                    if ok == "no":
                        continue
                    self.doRenewContract()
                self.doRaiseRental(num)
        self.sql.updRec("rtlctl", cols=["ctr_lme"], data=[self.tme],
            where=[("ctr_cono", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase(ask=True, mess="Do You Want To Save "\
            "All Changes?\n\nPlease Note That Once The Changes Have Been "\
            "Saved, There Is No Going Back Without Restoring From Backup!")
        self.opts["mf"].closeLoop()

    def doRenewContract(self):
        tit = ("Renew Rental Contract", )
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually", "6"),
            ("Annually","A"))
        self.fld = (
            (("T",0,0,0),"OUA",3,"Premises Code"),
            (("T",0,1,0),"ONA",7,"Account Code"),
            (("T",0,2,0),"ONA",30,"Tenant Name"),
            (("T",0,3,0),("IRB",r1s),0,"Payment Frequency","",
                self.freq,"N",None,None,None,None),
            (("T",0,4,0),"ID1",10,"Start Date","",
                self.exdt,"N",None,None,None,("efld",)),
            (("T",0,5,0),"IUI",3,"Number of Periods","",
                self.pers,"N",None,None,None,("notzero",)),
            (("T",0,6,0),"IUD",12.2,"Rental Amount","",
                self.amnt,"N",None,None,None,("notzero",)))
        tnd = ((self.doRenewEnd,"y"), )
        txt = (self.doLoadFocus, )
        self.na = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=self.fld, tend=tnd, txit=txt, focus=False)
        self.doLoadFocus()
        self.na.mstFrame.wait_window()

    def doRenewEnd(self):
        dat = self.rec[:3]
        dat.append(self.rec[3] + 1)
        for x in range(3, len(self.na.t_work[0][0])):
            dat.append(self.na.t_work[0][0][x])
        dat.append("C")
        self.sql.insRec("rtlcon", data=dat)
        self.rec[:8] = dat[:8]
        self.na.closeProcess()

    def doRaiseRental(self, num):
        ref = CCD((num + 1), "Na", 9).work
        amt = CCD(self.rec[7], "UD", 12.2).work
        vrte = getVatRate(self.sql, self.opts["conum"], self.rec[9], self.nxtdt)
        if vrte is None:
            vrte = 0.0
        vat = CCD(round((amt * vrte / 100), 2), "SD", 11.2).work
        tot = float(ASD(amt) + ASD(vat))
        data = self.rec[:4]
        data.extend([1, ref, self.batch, self.nxtdt, tot, vat, self.nxtcd,
            "Rental Raised", self.rec[9], "", self.opts["capnm"],
            self.sysdtw, 0])
        self.sql.insRec("rtltrn", data=data)
        if self.rec[9]:
            # VAT Transaction (ctlvtf)
            val = float(ASD(0) - ASD(amt))
            tax = float(ASD(0) - ASD(vat))
            data = [self.opts["conum"], self.rec[9], "O", self.nxtcd, "R", 1,
                self.batch, ref, self.nxtdt, self.rec[2], self.rec[8],
                val, tax, 0, self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        acc = self.sql.getRec("rtlprm", cols=["rtp_rtlacc",
            "rtp_incacc"], where=[("rtp_cono", "=", self.opts["conum"]),
            ("rtp_code", "=", self.rec[1])], limit=1)
        if not acc:
            return
        ref = "Month/End"
        # General Ledger Rental Control
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", acc[0]),
            ("glt_batch", "=", self.batch),
            ("glt_curdt", "=", self.nxtcd),
            ("glt_trdt", "=", self.nxtdt),
            ("glt_type", "=", 1)]
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            val = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            val = float(ASD(val) + ASD(tot))
            tax = glt[0][self.sql.gentrn_col.index("glt_taxamt")]
            tax = float(ASD(tax) + ASD(vat))
            self.sql.updRec("gentrn", cols=["glt_tramt", "glt_taxamt"],
                data=[val, tax], where=whr)
        else:
            data = [self.opts["conum"], acc[0], self.nxtcd, self.nxtdt, 1, ref,
                self.batch, tot, vat, self.rec[8], self.rec[9], "", 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        amt = float(ASD(0) - ASD(amt))
        vat = float(ASD(0) - ASD(vat))
        # General Ledger Income Account
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", acc[1]),
            ("glt_batch", "=", self.batch),
            ("glt_curdt", "=", self.nxtcd),
            ("glt_trdt", "=", self.nxtdt),
            ("glt_type", "=", 1)]
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            val = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            val = float(ASD(val) + ASD(amt))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[val], where=whr)
        else:
            data = [self.opts["conum"], acc[1], self.nxtcd, self.nxtdt, 1, ref,
                self.batch, amt, 0.00, self.rec[8], "", "", 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        if not vat:
            return
        # General Ledger VAT Account
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.convat),
            ("glt_batch", "=", self.batch),
            ("glt_curdt", "=", self.nxtcd),
            ("glt_trdt", "=", self.nxtdt),
            ("glt_type", "=", 1)]
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            val = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            val = float(ASD(val) + ASD(vat))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[val], where=whr)
        elif vat:
            data = [self.opts["conum"], self.convat, self.nxtcd, self.nxtdt, 1,
                ref, self.batch, vat, 0.00, self.rec[8], "", "", 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)

    def doLoadFocus(self):
        self.na.loadEntry("T", 0, 0, data=self.rec[1])
        self.na.loadEntry("T", 0, 1, data=self.rec[2])
        self.na.loadEntry("T", 0, 2, data=self.rec[8])
        self.na.focusField("T", 0, 4)

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
