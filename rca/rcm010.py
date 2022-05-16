"""
SYNOPSIS
    Rentals Ledger Month End Routine.

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
from TartanClasses import ASD, CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, getVatRate, mthendDate, projectDate
from tartanFunctions import showError

class rcm010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvrf", "ctlvtf", "gentrn",
            "rcactl", "rcaprm", "rcaowm", "rcaowt", "rcatnm", "rcacon",
            "rcatnt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.lme = rcactl["cte_lme"]
        self.glint = rcactl["cte_glint"]
        if self.glint == "Y":
            self.glbnk = rcactl["cte_glbnk"]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["rca_com", "rca_own", "rca_tnt", "vat_ctl"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.rcacom = ctlctl["rca_com"]
            self.rcaown = ctlctl["rca_own"]
            self.rcatnt = ctlctl["rca_tnt"]
            self.rcatrx = ctlctl["rca_trx"]
            self.convat = ctlctl["vat_ctl"]
        # Check for Company Record
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        # Set Company VAT Default
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
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
        chk = self.sql.getRec("rcatnt", cols=["count(*)"],
            where=[("rtu_cono", "=", self.opts["conum"]), ("rtu_type", "=", 1),
            ("rtu_batch", "=", self.batch), ("rtu_trdt", "=", self.nxtdt),
            ("rtu_curdt", "=", self.nxtcd)], limit=1)
        if chk[0]:
            return "Month-End Already Executed"

    def doEnd(self):
        self.df.closeProcess()
        whr = [
            ("rcc_cono", "=", self.opts["conum"]),
            ("rtn_cono=rcc_cono",), ("rtn_owner=rcc_owner",),
            ("rtn_code=rcc_code",), ("rtn_acno=rcc_acno",),
            ("rcc_status", "<>", "X")]
        recs = self.sql.getRec(tables=["rcacon", "rcatnm"], cols=["rcc_cono",
            "rcc_owner", "rcc_code", "rcc_acno", "rcc_cnum", "rcc_payind",
            "rcc_start", "rcc_period", "rcc_rtlamt", "rcc_deposit", "rcc_wamt",
            "rcc_wtyp", "rcc_eamt", "rcc_etyp", "rtn_name"], where=whr,)
        if recs:
            for num, self.con in enumerate(recs):
                own = self.sql.getRec("rcaowm", cols=["rom_vatdf"],
                    where=[("rom_cono", "=", self.opts["conum"]), ("rom_acno",
                    "=", self.con[1])], limit=1)
                if not own:
                    showError(self.opts["mf"].body, "Missing Owner",
                        "This Owner's Record (%s) Could Not Be Found!" %
                        self.con[1])
                    continue
                self.vatdf = own[0]
                self.prm = self.sql.getRec("rcaprm", cols=["rcp_crate"],
                    where=[("rcp_cono", "=", self.opts["conum"]), ("rcp_owner",
                    "=", self.con[1]), ("rcp_code", "=", self.con[2])], limit=1)
                if not self.prm:
                    showError(self.opts["mf"].body, "Missing Premises",
                        "This Premises's Record (%s %s) Could Not Be Found!" %
                        (self.con[1], self.con[2]))
                    continue
                self.freq = self.con[5]
                self.strt = CCD(self.con[6], "D1", 10)
                self.pers = self.con[7]
                self.amnt = self.con[8]
                self.depo = self.con[9]
                self.wamt = self.con[10]
                self.wtyp = self.con[11]
                self.eamt = self.con[12]
                self.etyp = self.con[13]
                if self.freq == "M":
                    self.mths = 1 * self.pers
                elif self.freq == "3":
                    self.mths = 3 * self.pers
                elif self.freq == "6":
                    self.mths = 6 * self.pers
                else:
                    self.mths = 12 * self.pers
                exdt = projectDate(self.strt.work, self.mths - 1, typ="months")
                exdt = CCD(mthendDate(exdt), "D1", 10)
                if int(exdt.work / 100) <= self.curdt:
                    self.sql.updRec("rcacon", cols=["rcc_status"], data=["X"],
                        where=[("rcc_cono", "=", self.con[0]), ("rcc_owner",
                        "=", self.con[1]), ("rcc_code", "=", self.con[2]),
                        ("rcc_acno", "=", self.con[3]), ("rcc_cnum", "=",
                        self.con[4])])
                    ok = askQuestion(self.opts["mf"].body, "Expired Contract",
                        "This contract has Expired, would you like to "\
                        "Renew it?\n\nOwner: %s\nPremises: %s\nAccount: %s\n"\
                        "Name: %s\nStart: %s\nEnd:   %s" % (self.con[1],
                        self.con[2], self.con[3], self.con[14], self.strt.disp,
                        exdt.disp))
                    if ok == "no":
                        continue
                    self.doExpiredContract()
                self.doRaiseRental(num)
                self.doRaiseExtra(num)
        self.sql.updRec("rcactl", cols=["cte_lme"], data=[self.tme],
            where=[("cte_cono", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase(ask=True, mess="Do You Want To Save "\
            "All Changes?\n\nPlease Note That Once The Changes Have Been "\
            "Saved, There Is No Going Back Without Restoring From Backup!")
        self.opts["mf"].closeLoop()

    def doExpiredContract(self):
        tit = ("Renew Rental Contract", )
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually", "6"),
            ("Annually","A"))
        chdt = self.strt.work
        while True:
            chdt = projectDate(chdt, self.mths, typ="months")
            exdt = mthendDate(projectDate(chdt, self.mths - 1, typ="months"))
            if int(exdt / 100) > self.curdt:
                break
        self.fld = (
            (("T",0,0,0),"OUA",7,"Owner Code"),
            (("T",0,1,0),"OUA",7,"Premises Code"),
            (("T",0,2,0),"ONA",7,"Account Code"),
            (("T",0,3,0),"ONA",30,"Tenant Name"),
            (("T",0,4,0),("IRB",r1s),0,"Payment Frequency","",
                self.freq,"N",None,None,None,None),
            (("T",0,5,0),"ID1",10,"Start Date","",
                chdt,"N",None,None,None,("efld",)),
            (("T",0,6,0),"IUI",3,"Number of Periods","",
                self.pers,"N",None,None,None,("notzero",)),
            (("T",0,7,0),"IUD",12.2,"Rental Amount","",
                self.amnt,"N",None,None,None,("notzero",)),
            (("T",0,8,0),"IUD",12.2,"Deposit Amount","",
                self.depo,"N",None,None,None,("efld",)),
            (("T",0,9,0),"IUD",12.2,"Basic Water Amount","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"IUI",1,"Type","",
                "","N",None,None,None,("efld",)),
            (("T",0,11,0),"IUD",12.2,"Basic Exlectricity Amount","",
                "","N",None,None,None,("efld",)),
            (("T",0,12,0),"IUI",1,"Type","",
                "","N",None,None,None,("efld",)))
        tnd = ((self.doExpireEnd,"y"), )
        txt = (None, )
        self.na = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=self.fld, tend=tnd, txit=txt, focus=False)
        self.doLoadFocus(chdt)
        self.na.mstFrame.wait_window()

    def doExpireEnd(self):
        dat = self.con[:4]
        dat.append(self.con[4] + 1)
        for x in range(4, len(self.na.t_work[0][0])):
            dat.append(self.na.t_work[0][0][x])
        dat.append("C")
        self.sql.insRec("rcacon", data=dat)
        self.con[:9] = dat[:9]
        self.na.closeProcess()

    def doRaiseRental(self, num):
        ref = CCD((num + 1), "Na", 9).work
        amt = CCD(self.con[8], "UD", 12.2).work
        vrte = getVatRate(self.sql, self.opts["conum"], self.vatdf, self.nxtdt)
        if vrte is None:
            vrte = 0.0
        vat = CCD(round((amt * vrte / 100), 2), "SD", 11.2).work
        tot = float(ASD(amt) + ASD(vat))
        # Tenant Transaction
        data = self.con[:5]
        data.extend([1, ref, self.batch, self.nxtdt, 1, tot, vat, self.nxtcd,
            "Rental Raised", self.vatdf, "", self.opts["capnm"], self.sysdtw,
            0])
        self.sql.insRec("rcatnt", data=data)
        if self.glint == "Y":
            # Update Tenant Control
            gld = "%7s Rental Raised" % self.con[3]
            data = [self.opts["conum"], self.rcatnt, self.nxtcd, self.nxtdt, 4,
                ref, self.batch, tot, 0, gld, "", "", 0, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        rta = float(ASD(0) - ASD(tot))
        rtv = float(ASD(0) - ASD(vat))
        # Owner Transaction
        data = self.con[:2]
        data.extend([1, ref, self.batch, self.nxtdt, rta, rtv, self.nxtcd,
            "Rental on %s Premises" % self.con[2], self.vatdf, "",
            self.opts["capnm"], self.sysdtw, 0])
        self.sql.insRec("rcaowt", data=data)
        if self.glint == "Y":
            # Update Owner Control
            gld = "%7s Rental Raised" % self.con[1]
            data = [self.opts["conum"], self.rcaown, self.nxtcd, self.nxtdt, 4,
                ref, self.batch, rta, 0, gld, "", "", 0, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        if self.prm[0]:
            cma = round((tot * self.prm[0] / 100.0), 2)
            vrte = getVatRate(self.sql, self.opts["conum"], self.taxdf,
                self.nxtdt)
            if vrte is None:
                vrte = 0.0
            cmv = round((cma * vrte / 100.0), 2)
            cmt = float(ASD(cma) + ASD(cmv))
            cma = float(ASD(0) - ASD(cma))
            tax = float(ASD(0) - ASD(cmv))
            des = "Commission @ %3.5s%s Inclusive" % (self.prm[0], "%")
            # Raise Commission
            data = self.con[:2]
            data.extend([4, ref, self.batch, self.nxtdt, cmt, cmv, self.nxtcd,
                des, self.taxdf, "", self.opts["capnm"], self.sysdtw, 0])
            self.sql.insRec("rcaowt", data=data)
            if self.glint == "Y":
                # Update Owner Control
                gld = "%7s Commission Raised" % self.con[1]
                data = [self.opts["conum"], self.rcaown, self.nxtcd,
                    self.nxtdt, 4, ref, self.batch, cmt, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                # Update Commission Account
                data = [self.opts["conum"], self.rcacom, self.nxtcd,
                    self.nxtdt, 4, ref, self.batch, cma, tax, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            if self.taxdf:
                # VAT Transaction (ctlvtf)
                data = [self.opts["conum"], self.taxdf, "O", self.nxtcd, "R",
                    1, self.batch, ref, self.nxtdt, self.con[3], self.con[14],
                    cma, tax, 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("ctlvtf", data=data)
                if self.glint == "Y" and tax:
                    # Update VAT Control
                    data = [self.opts["conum"], self.convat, self.nxtcd,
                        self.nxtdt, 4, ref, self.batch, tax, 0, gld, "", "", 0,
                        self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)

    def doRaiseExtra(self, num):
        for x in ("W", "E"):
            ref = CCD((num + 1), "Na", 9).work
            num += 1
            if x == "W":
                if not self.con[10]:
                    continue
                amt = self.con[10]
                typ = self.con[11]
                des = "Basic Water Charge"
            elif x == "E":
                if not self.con[12]:
                    continue
                amt = self.con[12]
                typ = self.con[13]
                des = "Basic Electricity Charge"
            # Tenant Transaction
            data = self.con[:5]
            data.extend([1, ref, self.batch, self.nxtdt, 4, amt, 0, self.nxtcd,
                des, "", "", self.opts["capnm"], self.sysdtw, 0])
            self.sql.insRec("rcatnt", data=data)
            if self.glint == "Y":
                gld = "%7s %7s %7s" % tuple(self.con[1:4])
                data = [self.opts["conum"], self.rcatnt, self.nxtcd,
                    self.nxtdt, 4, num, self.batch, amt, 0, gld, "",
                    "", 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            amt = float(ASD(0) - ASD(amt))
            if typ == 4:
                # Services - Owner Recovery
                des = "Services Recovery on %s" % self.con[2]
                data = [self.opts["conum"], self.con[1], 4, num, self.batch,
                    self.nxtdt, amt, 0, self.nxtcd, des, "", "",
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("rcaowt", data=data)
                if self.glint == "Y":
                    # General Ledger Transaction for Owner Control
                    gld = "%7s Services Recovery" % self.con[2]
                    data = [self.opts["conum"], self.rcaown, self.nxtcd,
                        self.nxtdt, 4, num, self.batch, amt, 0, gld, "",
                        "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
            elif self.glint == "Y":
                # Non Recovery - Update Rental Control
                data = [self.opts["conum"], self.rcatrx, self.nxtcd,
                    self.nxtdt, 4, num, self.batch, amt, 0, gld, "",
                    "", 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)

    def doLoadFocus(self, chdt=None):
        for num, fld in enumerate(self.con[1:14]):
            if chdt and num == 5:
                self.na.loadEntry("T", 0, num, data=chdt)
            else:
                self.na.loadEntry("T", 0, num, data=fld)
        self.na.focusField("T", 0, 4)

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
