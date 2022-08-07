"""
SYNOPSIS
    Salaries and Wages Payslips.

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

import os, time
from TartanClasses import ASD, CCD, GetCtl, LoanInterest, PrintPayslip
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, dateDiff, getSingleRecords
from tartanFunctions import mthendDate, payeTables, showError, showInfo

class wg2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.hrsmt = float(wagctl["ctw_m_hrs"])
        self.hrswk = float(wagctl["ctw_w_hrs"])
        self.hrsdy = float(wagctl["ctw_d_hrs"])
        self.glint = wagctl["ctw_glint"]
        self.bestac = wagctl["ctw_bestac"]
        self.besttp = wagctl["ctw_besttp"]
        self.tplnam = wagctl["ctw_tplnam"]
        tabs = ["tplmst", "wagcod", "wagedc", "wagmst", "wagcap", "wagbal",
            "wagtf1", "wagtf2", "waglmf", "wagltf", "wagtxa", "wagtxr"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if gc.chkRec(self.opts["conum"], ctlctl, ["wag_ctl"]):
                return
            self.wagctl = ctlctl["wag_ctl"]
            self.slnctl = ctlctl["wag_slc"]
            tabs.extend(["ctldep", "ctlmst", "genmst", "genint", "gentrn"])
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        accs = self.sql.getRec("waglmf", cols=["wlm_code"],
            where=[("wlm_cono", "=", self.opts["conum"])],
            group="wlm_code")
        self.lonacc = []
        for acc in accs:
            self.lonacc.append(acc[0])
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = CCD(self.sysdtw, "d1", 10).disp
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        self.etotal = 0
        self.pgnum = 0
        self.empnos = []
        return True

    def mainProcess(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "P"),
                ("tpm_system", "=", "WAG")],
            "order": "tpm_tname"}
        mes = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": [
                ("mss_message", "",  0, "Cod"),
                ("mss_detail",  "", 60, "Details")],
            "where": [("mss_system", "=", "WAG")],
            "screen": self.opts["mf"].body}
        r1s = (("Weekly","W"),("Fortnightly","F"),("Monthly","M"))
        r2s = (("Yes","Y"),("Singles","S"))
        r3s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),"ID1",10,"Pay-Run Date","",
                "","N",self.doRunDate,None,None,("efld",)),
            (("T",0,2,0),"ID1",10,"Payment Date","",
                self.sysdtw,"N",self.doPayDate,None,None,("efld",)),
            (("T",0,3,0),"IUI",3,"Message Code","",
                "","N",self.doMess,mes,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Frequency","Payment Frequency",
                "M","N",self.doFreq,None,None,None),
            (("T",0,5,0),("IRB",r2s),0,"Whole File","",
                "S","N",self.doWhole,None,None,None),
            (("T",0,6,0),"IUI",1,"Department","",
                "","N",self.doDept,None,None,None),
            (("T",0,7,0),("IRB",r3s),0,"Ignore Standards","",
                "N","N",self.doIgnore,None,None,None),
            (("T",0,8,0),("IRB",r3s),0,"Include Monthly","",
                "Y","N",self.doMthly,None,None,None),
            (("T",0,9,0),("IRB",r3s),0,"Exclude Minus Balances","",
                "N","N",self.doMinus,None,None,None),
            (("T",0,10,0),("IRB",r3s),0,"Preview Only","",
                "Y","N",self.doPreview,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("N","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "P"), ("tpm_system", "=", "WAG")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doRunDate(self, frt, pag, r, c, p, i, w):
        self.rundt = w
        self.curdt = int(w / 100)
        self.taxyr = int(w / 10000)
        mth = self.curdt % 100
        if mth > 2:
            self.taxyr = self.taxyr + 1
        if self.glint == "Y":
            if self.curdt < self.s_per or self.curdt > self.e_per:
                return "Invalid Date, Not In Financial Period"
        self.allow, self.rates = payeTables(self.sql, self.taxyr)
        if not self.allow or not self.rates:
            showError(self.opts["mf"].body, "Missing Rates",
                "There are No Tax Rates for Year %s" % self.taxyr)
            return "rf"
        y = int(w / 10000)
        m = int((w % 10000) / 100)
        if m < 3:
            self.sdate = ((y - 1) * 10000) + 301
        else:
            self.sdate = (y * 10000) + 301

    def doPayDate(self, frt, pag, r, c, p, i, w):
        self.paydt = w

    def doMess(self, frt, pag, r, c, p, i, w):
        if not w:
            self.mess = None
        else:
            self.mess = self.sql.getRec("ctlmes", cols=["mss_detail"],
            where=[("mss_system", "=", "WAG"), ("mss_message", "=", w)],
            limit=1)

    def doFreq(self, frt, pag, r, c, p, i, w):
        old = self.sql.getRec("wagtf1", cols=["count(*)"],
            where=[("wt1_cono", "=", self.opts["conum"]), ("wt1_date", "=",
            self.rundt), ("wt1_freq", "=", w)], limit=1)
        if old[0]:
            ok = askQuestion(screen=self.opts["mf"].body,
                head="Duplicate Payrun",
                mess="A Payrun for this date has already been run!\n\n"\
                "Do you want to continue?", default="no")
            if ok == "no":
                return "Duplicate Payrun"
        self.freq = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole == "Y":
            self.dept = ""
            return "sk1"

    def doDept(self, frt, pag, r, c, p, i, w):
        self.dept = w

    def doIgnore(self, frt, pag, r, c, p, i, w):
        self.ignore = w
        if self.freq != "M":
            self.df.loadEntry(frt, pag, p+1, data="N")

    def doMthly(self, frt, pag, r, c, p, i, w):
        self.mthly = w

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def doPreview(self, frt, pag, r, c, p, i, w):
        self.preview = w

    def doEnd(self):
        self.df.closeProcess()
        if self.bestac:
            self.export = open(os.path.join(self.opts["mf"].rcdic["wrkdir"],
                "best%03d_%s.txt" % (self.opts["conum"], self.paydt)), "w")
            # Header for BEST
            self.export.write("%1s%4s%-40s%8s%1s%8s%-15s%1s%2s%1s%9s%2s%4s"\
                "\r\n" % ("*", self.bestac, self.opts["conam"], self.paydt,
                "Y", "", "SALARIES EFT", "+", self.besttp, 0, "", "01","LIVE"))
        else:
            self.export = None
        whr = [
            ("wgm_cono", "=", self.opts["conum"]),
            ("wgm_freq", "=", self.freq)]
        if self.dept:
            whr.append(("wgm_dept", "=", self.dept))
        if self.whole == "S":
            whr.extend(
                [("wcp_cono", "=", self.opts["conum"]),
                ("wcp_empno=wgm_empno",),
                ("wcp_paid", "=", "N")])
            col = ["wgm_empno", "wgm_sname", "wgm_fname"]
            recs = getSingleRecords(self.opts["mf"], ["wagmst", "wagcap"], col,
                where=whr, group=True)
        else:
            recs = self.sql.getRec("wagmst", where=whr,
                order="wgm_empno")
            if not recs:
                showError(self.opts["mf"].body, "Error",
                    "No Records Available")
        if recs:
            if self.preview == "Y":
                pb = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            else:
                pb = ProgressBar(self.opts["mf"].body, mxs=len(recs))
            for num, emp in enumerate(recs):
                pb.displayProgress(num)
                if self.preview == "Y" and pb.quit:
                    break
                self.doProcess(emp)
            pb.closeProgress()
            if self.preview == "Y" and pb.quit:
                self.opts["mf"].closeLoop()
                return
            if self.glint == "Y":
                chk = self.doIntegration()
            else:
                chk = True
            if chk:
                self.doPrint()
                if self.preview == "Y":
                    self.opts["mf"].dbm.rollbackDbase()
                    showInfo(self.opts["mf"].window, "Preview",
                        """Please Note That this was a Preview Only.

No Records Have Been Updated.""")
                else:
                    self.opts["mf"].dbm.commitDbase()
                    if self.export:
                        # Trailer for BEST
                        value = int(round((self.etotal * 100), 0))
                        self.export.write("%1s%4s%1s%30s%013u%47s\r\n" % \
                            (2, self.bestac, "T", "", value, ""))
                        self.export.close()
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doProcess(self, emp):
        self.empno = int(emp[self.sql.wagmst_col.index("wgm_empno")])
        self.dob = emp[self.sql.wagmst_col.index("wgm_dob")]
        self.begin = emp[self.sql.wagmst_col.index("wgm_start")]
        if self.begin > self.rundt:
            return
        self.edept = emp[self.sql.wagmst_col.index("wgm_dept")]
        self.efreq = emp[self.sql.wagmst_col.index("wgm_freq")]
        self.etype = emp[self.sql.wagmst_col.index("wgm_ptype")]
        self.erate = float(emp[self.sql.wagmst_col.index("wgm_payamt")])
        self.paye = emp[self.sql.wagmst_col.index("wgm_paye")]
        self.fix_rate = emp[self.sql.wagmst_col.index("wgm_fix_rate")]
        self.direct = emp[self.sql.wagmst_col.index("wgm_direct")]
        self.doRates(self.erate)
        self.taxamt = 0
        self.doCodes()
        if self.doCapture():
            self.empnos.append(self.empno)
            self.nhrs = 0
            self.npay = 0
            self.taxbl = 0
            self.notax = 0
            self.rtpay = 0
            self.anpay = 0
            self.pspay = 0
            self.uifpay = 0
            self.sdlpay = 0
            self.taxdd = 0
            self.nondd = 0
            self.psded = 0
            self.shift = 0
            self.drbal = 0
            self.totern = 0
            self.totded = 0
            self.pgnum += 1
            self.loan = True
            self.doEarnings()
            self.doDeductions()
            wagtf1 = (self.opts["conum"], self.empno, self.pgnum, self.rundt,
                self.freq, self.etype, self.edept, self.erate, self.nhrs,
                self.npay, self.taxbl, self.notax, self.rtpay, self.anpay,
                self.pspay, self.taxdd, self.nondd, self.psded,
                int(self.uifpay), int(self.sdlpay), self.shift,
                self.drbal, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("wagtf1", data=wagtf1)
            self.doPAYE()
            if self.loan:
                self.doStaffLoans()

    def doRates(self, rate):
        if self.freq == "M":
            self.mrate = rate
            self.wrate = round((self.mrate * self.hrswk / self.hrsmt), 2)
            self.drate = round((self.mrate * self.hrsdy / self.hrsmt), 2)
            self.hrate = round((self.mrate / self.hrsmt), 2)
        else:
            self.hrate = rate
            self.drate = round(self.hrate * self.hrsdy, 2)
            self.wrate = round(self.hrate * self.hrswk, 2)
            self.mrate = round(self.hrate * self.hrsmt, 2)
        self.frate = round((self.wrate * 2), 2)

    def doCodes(self):
        self.ern = {}
        self.ded = {}
        codes = self.sql.getRec("wagcod", where=[("wcd_cono", "=",
            self.opts["conum"]), ("wcd_empno", "=", self.empno)])
        if not codes:
            return
        for c in codes:
            ctype = c[self.sql.wagcod_col.index("wcd_type")]
            code = int(c[self.sql.wagcod_col.index("wcd_code")])
            eamt = float(c[self.sql.wagcod_col.index("wcd_eamt")])
            ramt = float(c[self.sql.wagcod_col.index("wcd_ramt")])
            det = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"]), ("ced_type", "=", ctype), ("ced_code",
                "=", code)], limit=1)
            if not det:
                continue
            if ctype == "D" and det[
                    self.sql.wagedc_col.index("ced_ror")] == 4102:
                self.taxamt = float(ASD(self.taxamt) + ASD(eamt))
            elif self.ignore == "Y":
                continue
            elif ctype == "E" and code > 5:
                if code in self.ern:
                    self.ern[code][0] = float(ASD(self.ern[code][0])+ASD(eamt))
                    self.ern[code][1] = float(ASD(self.ern[code][0])+ASD(ramt))
                else:
                    self.ern[code] = [eamt, ramt]
            elif ctype == "D":
                if code in self.ded:
                    self.ded[code][0] = float(ASD(self.ded[code][0])+ASD(eamt))
                    self.ded[code][1] = float(ASD(self.ded[code][0])+ASD(ramt))
                else:
                    self.ded[code] = [eamt, ramt]

    def doCapture(self):
        yes = self.sql.getRec("wagcap", cols=["wcp_type", "wcp_code",
            "round(sum(wcp_amt),2)"], where=[("wcp_cono", "=",
            self.opts["conum"]), ("wcp_empno", "=", self.empno), ("wcp_ind",
            "=", "Y"), ("wcp_paid", "=", "N")], group="wcp_type, wcp_code")
        no = self.sql.getRec("wagcap", cols=["wcp_type", "wcp_code"],
            where=[("wcp_cono", "=", self.opts["conum"]), ("wcp_empno", "=",
            self.empno), ("wcp_ind", "=", "N"), ("wcp_paid", "=", "N")])
        if not yes:
            return
        if not no:
            no = []
        for y in yes:
            typ = y[0]
            cod = int(y[1])
            amt = float(y[2])
            ind = self.sql.getRec("wagedc", cols=["ced_eind",
                "ced_ror"], where=[("ced_cono", "=", self.opts["conum"]),
                ("ced_type", "=", typ), ("ced_code", "=", cod)], limit=1)
            if not ind:
                continue
            if typ == "E":
                if cod in self.ern:
                    if ind[0] == "R":
                        self.ern[cod][0] = amt
                    else:
                        self.ern[cod][0] = float(ASD(self.ern[cod][0]) + \
                            ASD(amt))
                else:
                    self.ern[cod] = [amt, 0]
            else:
                if ind[1] == 4102:
                    self.taxamt = float(ASD(self.taxamt) + ASD(amt))
                elif cod in self.ded:
                    if ind[0] == "R":
                        self.ded[cod] = amt
                    else:
                        self.ded[cod][0] = float(ASD(self.ded[cod][0]) + \
                            ASD(amt))
                else:
                    self.ded[cod] = [amt, 0]
        for n in no:
            typ = n[0]
            cod = int(n[1])
            if typ == "E":
                if cod in self.ern:
                    del self.ern[cod]
            else:
                if cod in self.ded:
                    del self.ded[cod]
        if self.preview == "N":
            self.sql.updRec("wagcap", cols=["wcp_paid"], data=["Y"],
                where=[("wcp_cono", "=", self.opts["conum"]), ("wcp_empno",
                "=", self.empno)])
        return True

    def doEarnings(self):
        if self.freq == "W":
            rate = self.wrate
        elif self.freq == "F":
            rate = self.frate
        elif self.freq == "M":
            rate = self.mrate
        idx = list(self.ern.keys())
        idx.sort()
        for cod in idx:
            ced = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"]), ("ced_type", "=", "E"), ("ced_code", "=",
                cod)], limit=1)
            if not ced:
                continue
            eind = ced[self.sql.wagedc_col.index("ced_eind")]
            ebase = ced[self.sql.wagedc_col.index("ced_ebase")]
            eamt = ced[self.sql.wagedc_col.index("ced_eamt")]
            if cod == 1 and eamt == 0:
                # Invalid wgexp0 conversion/imported from old system
                eamt = 1
            tax = ced[self.sql.wagedc_col.index("ced_taxcode")]
            taxp = ced[self.sql.wagedc_col.index("ced_taxportion")]
            earnt = ced[self.sql.wagedc_col.index("ced_earntype")]
            eglco = int(ced[self.sql.wagedc_col.index("ced_eglco")])
            eglno = int(ced[self.sql.wagedc_col.index("ced_eglno")])
            if eglno and not eglco:
                eglco = self.opts["conum"]
            uifportion = ced[self.sql.wagedc_col.index("ced_uifportion")]
            sdlportion = ced[self.sql.wagedc_col.index("ced_sdlportion")]
            if eind == "F" and not self.ern[cod][0]:
                self.ern[cod][0] = eamt
            if cod != 1 and not self.ern[cod][0]:
                continue
            if cod < 6:
                if cod == 5:
                    hrs = self.ern[cod][0] * self.hrsdy
                else:
                    hrs = self.ern[cod][0]
                if cod == 1 and hrs == 0:
                    if self.freq == "W":
                        hrs = self.hrswk
                    elif self.freq == "F":
                        hrs = self.hrswk * 2
                    elif self.freq == "M":
                        hrs = self.hrsmt
                if hrs == self.hrsmt:
                    emt = self.mrate
                elif hrs == self.hrswk:
                    emt = self.wrate
                elif hrs == self.hrsdy:
                    emt = self.drate
                else:
                    emt = round((hrs * self.hrate * eamt), 2)
                self.nhrs = float(ASD(self.nhrs) + ASD(hrs))
                self.npay = float(ASD(self.npay) + ASD(emt))
                if not uifportion:
                    uifportion = 100.00
                if not sdlportion:
                    sdlportion = 100.00
            elif eind == "R":
                hrs = 0
                ct1 = self.ern[cod][0]
                if ebase == 1:
                    emt = round((ct1 * eamt * self.erate), 2)
                elif ebase == 2:
                    emt = round((eamt * rate), 2)
                elif ebase == 3:
                    emt = round((eamt * rate / 100), 2)
                elif ebase == 4:
                    emt = round((eamt * self.drate * ct1), 2)
                elif ebase == 5:
                    emt = round((eamt * self.hrate * ct1), 2)
                else:
                    emt = 0
            else:
                hrs = 0
                if self.ern[cod][0]:
                    emt = self.ern[cod][0]
                else:
                    emt = eamt
            if tax == "N":
                self.notax = float(ASD(self.notax) + ASD(emt))
            elif taxp:
                amt = round((emt * taxp / 100), 2)
                self.notax = float(ASD(self.notax) + ASD(emt) - ASD(amt))
                self.taxbl = float(ASD(self.taxbl) + ASD(amt))
            if tax == "R":
                self.rtpay = float(ASD(self.rtpay) + ASD(emt))
            if tax == "O":
                self.anpay = float(ASD(self.anpay) + ASD(emt))
            if tax == "T":
                self.pspay = float(ASD(self.pspay) + ASD(emt))
            else:
                self.totern = float(ASD(self.totern) + ASD(emt))
            if uifportion:
                amt = round((emt * uifportion / 100.0), 2)
                self.uifpay = float(ASD(self.uifpay) + ASD(amt))
            if sdlportion:
                amt = round((emt * sdlportion / 100.0), 2)
                self.sdlpay = float(ASD(self.sdlpay) + ASD(amt))
            # Write Transaction Detail
            wagtf2 = [self.opts["conum"], self.empno, self.pgnum, self.rundt,
                "E", cod, hrs, emt, 0, tax, taxp, earnt, eglco, eglno, 0, 0]
            self.doWriteWagtf2(wagtf2)

    def doDeductions(self):
        if self.freq == "W":
            rate = self.wrate
        elif self.freq == "F":
            rate = self.frate
        elif self.freq == "M":
            rate = self.mrate
        idx = list(self.ded.keys())
        idx.sort()
        for cod in idx:
            ced = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"]), ("ced_type", "=", "D"), ("ced_code", "=",
                cod)], limit=1)
            if not ced:
                continue
            eind = ced[self.sql.wagedc_col.index("ced_eind")]
            ebase = ced[self.sql.wagedc_col.index("ced_ebase")]
            eamt = ced[self.sql.wagedc_col.index("ced_eamt")]
            elim = ced[self.sql.wagedc_col.index("ced_elimit")]
            rind = ced[self.sql.wagedc_col.index("ced_rind")]
            rbase = ced[self.sql.wagedc_col.index("ced_rbase")]
            ramt = ced[self.sql.wagedc_col.index("ced_ramt")]
            rlim = ced[self.sql.wagedc_col.index("ced_rlimit")]
            must = ced[self.sql.wagedc_col.index("ced_must")]
            tax = ced[self.sql.wagedc_col.index("ced_taxcode")]
            taxp = ced[self.sql.wagedc_col.index("ced_taxportion")]
            hlim = ced[self.sql.wagedc_col.index("ced_hr_limit")]
            mthly = ced[self.sql.wagedc_col.index("ced_monthly")]
            balno = ced[self.sql.wagedc_col.index("ced_balno")]
            earnt = ced[self.sql.wagedc_col.index("ced_earntype")]
            eglco = int(ced[self.sql.wagedc_col.index("ced_eglco")])
            eglno = int(ced[self.sql.wagedc_col.index("ced_eglno")])
            if eglno and not eglco:
                eglco = self.opts["conum"]
            rglco = int(ced[self.sql.wagedc_col.index("ced_rglco")])
            rglno = int(ced[self.sql.wagedc_col.index("ced_rglno")])
            if not rglco and rglno:
                rglco = self.opts["conum"]
            if mthly == "Y" and self.mthly == "N":
                continue
            if hlim and self.nhrs < hlim:
                continue
            if eind == "R":
                ct1 = self.ded[cod][0]
                if ebase == 1:
                    emt = round((ct1 * eamt * self.erate), 2)
                elif ebase == 2:
                    emt = round((eamt * rate), 2)
                elif ebase == 3:
                    emt = round((eamt * rate / 100), 2)
                elif ebase == 4:
                    emt = round((eamt * self.drate * ct1), 2)
                elif ebase == 5:
                    emt = round((eamt * self.hrate * ct1), 2)
                elif ebase == 6:
                    emt = round((self.allow[5] * int(self.uifpay) / 100), 2)
                elif ebase == 7:
                    emt = round((self.allow[7] * int(self.sdlpay) / 100), 2)
                else:
                    emt = 0
            elif self.ded[cod][0]:
                emt = self.ded[cod][0]
            else:
                emt = eamt
            # Check Balance Records
            if balno:
                bwh = [
                    ("wbl_cono", "=", self.opts["conum"]),
                    ("wbl_empno", "=", self.empno),
                    ("wbl_balno", "=", balno)]
                old = self.sql.getRec("wagbal", where=bwh, limit=1)
                if old:
                    tmp = old[:-1]
                    if tmp[3] < emt:
                        emt = tmp[3]
                    tmp[3] = float(ASD(tmp[3]) - ASD(emt))
            else:
                old = None
            if elim and emt > elim:
                emt = elim
            if tax == "N":
                self.nondd = float(ASD(self.nondd) + ASD(emt))
            else:
                self.taxdd = float(ASD(self.taxdd) + ASD(emt))
            if must == "N" and self.taxdd > self.totern:
                emt = 0
            if not emt:
                continue
            if tax == "T":
                self.psded = float(ASD(self.psded) + ASD(emt))
            else:
                self.totded = float(ASD(self.totded) + ASD(emt))
            if tax != "N" and taxp:
                amt = round((emt * taxp / 100), 2)
                self.taxbl = float(ASD(self.taxbl) - ASD(amt))
            # Update Balance Records
            if old and tmp != old[:len(tmp)]:
                col = self.sql.wagbal_col
                tmp.append(old[col.index("wbl_xflag")])
                self.sql.updRec("wagbal", data=tmp, where=bwh)
            if rind == "N":
                rmt = 0
            elif eind == "R":
                ct1 = self.ded[cod][1]
                if rbase == 1:
                    rmt = round((ct1 * ramt * self.erate), 2)
                elif rbase == 2:
                    rmt = round((ramt * rate), 2)
                elif rbase == 3:
                    rmt = round((ramt * rate / 100), 2)
                elif rbase == 4:
                    rmt = round((ramt * self.drate * ct1), 2)
                elif rbase == 5:
                    rmt = round((ramt * self.hrate * ct1), 2)
                elif ebase == 6:
                    rmt = round((self.allow[6] * self.uifpay / 100), 2)
                elif ebase == 7:
                    rmt = round((self.allow[8] * self.sdlpay / 100), 2)
                else:
                    rmt = 0
            elif self.ded[cod][1]:
                rmt = self.ded[cod][1]
            else:
                rmt = ramt
            if rlim and rmt > rlim:
                rmt = rlim
            # Write Transaction Detail
            wagtf2 = [self.opts["conum"], self.empno, self.pgnum, self.rundt,
                "D", cod, 0, emt, rmt, tax, taxp, earnt, eglco, eglno, rglco,
                rglno]
            self.doWriteWagtf2(wagtf2)
            if cod in self.lonacc:
                # Get Latest Loan
                lon = self.sql.getRec("waglmf", cols=["max(wlm_loan)"],
                    where=[("wlm_cono", "=", self.opts["conum"]),
                    ("wlm_empno", "=", self.empno)], limit=1)[0]
                # Write Loan Transaction
                emt = float(ASD(0) - ASD(emt))
                dat = [self.opts["conum"], self.empno, lon, "Payslip", 4,
                    self.rundt, self.pgnum, emt, 0, 0, 0, self.curdt,
                    "Salary Deduction", "N", self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("wagltf", data=dat)
                self.loan = False

    def doPAYE(self):
        if self.paye == "N":
            return
        if not self.taxamt:
            # Not manually captured PAYE
            if self.fix_rate and self.direct:
                self.doFlatRate()
            else:
                self.doFormulae()
            if self.taxamt < 0:
                self.taxamt = 0
            else:
                tx = self.sql.getRec("wagtf2",
                    cols=["round(sum(wt2_eamt),2)"], where=[("wt2_cono", "=",
                    self.opts["conum"]), ("wt2_empno", "=", self.empno),
                    ("wt2_date", "between", self.sdate, self.rundt),
                    ("wt2_type", "=", "D"), ("wt2_code", "=", 1)])
                if tx == [[None]]:
                    tx = 0
                else:
                    tx = tx[0][0]
                self.taxamt = float(ASD(self.taxamt) - ASD(tx))
        if self.taxamt <= 0:
            return
        ced = self.sql.getRec("wagedc", where=[("ced_cono", "=",
            self.opts["conum"]), ("ced_type", "=", "D"), ("ced_code", "=", 1)],
            limit=1)
        if not ced:
            return
        eglco = int(ced[self.sql.wagedc_col.index("ced_eglco")])
        eglno = int(ced[self.sql.wagedc_col.index("ced_eglno")])
        if eglno and not eglco:
            eglco = self.opts["conum"]
        self.totded = float(ASD(self.totded) + ASD(self.taxamt))
        # Write PAYE Transaction Detail
        wagtf2 = [self.opts["conum"], self.empno, self.pgnum, self.rundt, "D",
            1, 0, self.taxamt, 0, "N", 0, "", eglco, eglno, 0, 0]
        self.doWriteWagtf2(wagtf2)

    def doFlatRate(self):
        inc, ret, tot = self.doTaxableIncome()
        if inc <= 0:
            self.taxamt = 0
            return
        self.taxamt = round((inc * self.fix_rate / 100), 2)
        if self.taxamt <= 0:
            self.taxamt = 0
            return
        self.taxamt = round((self.taxamt * self.pers / self.base), 2)

    def doFormulae(self):
        taxinc, retinc, totinc = self.doTaxableIncome()
        #if taxinc <= 0:
        #    self.taxamt = 0
        #    return
        ann = 0
        ret = 0
        self.taxamt, prb, arb, nrb, rmx = self.doCompute(taxinc)
        if taxinc != totinc:
            ann, _, _, _, _ = self.doCompute(totinc)
            ann = float(ASD(ann) - ASD(self.taxamt))
        yrend = mthendDate((self.taxyr * 10000) + 228)
        age = dateDiff(self.dob, yrend, "years")
        if age > 64:
            prb = float(ASD(prb) + ASD(arb))
        if age > 74:
            prb = float(ASD(prb) + ASD(nrb))
        self.taxamt = float(ASD(self.taxamt) - ASD(prb))
        if retinc > 0 and retinc > rmx:
            avg = round(((self.taxamt / taxinc) * 100), 2)
            ret = round(((float(ASD(retinc) - ASD(rmx))) * avg / 100), 2)
        self.taxamt = round((self.taxamt * self.pers / self.base), 2)
        self.taxamt = float(ASD(self.taxamt) + ASD(ann) + ASD(ret))

    def doTaxableIncome(self):
        ed = self.sql.getRec("wagtf1", cols=["round(sum(wt1_taxbl), 2)",
            "round(sum(wt1_rtpay), 2)", "round(sum(wt1_anpay), 2)"],
            where=[("wt1_cono", "=", self.opts["conum"]), ("wt1_empno", "=",
            self.empno), ("wt1_date", "between", self.sdate, self.rundt)])
        inc = 0
        anp = 0
        if ed:
            anp = ed[0][2]
            inc = float(ASD(ed[0][0]) - ASD(anp))
        if self.begin < self.sdate:
            begin = self.sdate
        else:
            begin = self.begin
        if self.efreq == "M":
            self.base = 12
            y1 = int(self.rundt / 10000)
            y2 = int(begin / 10000)
            m1 = int((self.rundt - (y1 * 10000)) / 100)
            m2 = int((begin - (y2 * 10000)) / 100)
            self.pers = 1 + ((y1 - y2) * self.base) + (m1 - m2)
            while self.pers > self.base:
                self.pers = self.pers - self.base
        else:
            days = dateDiff(begin, self.rundt, "days")
            if self.efreq == "W":
                per = 7
                self.base = 52
            else:
                per = 14
                self.base = 26
            self.pers = int(days / per)
            if days % per > 0:
                self.pers = self.pers + 1
            if self.pers > self.base:
                self.pers = self.base
        inc = round((inc * self.base / self.pers), 2)
        tot = float(ASD(inc) + ASD(anp))
        return inc, float(ed[0][1]), tot

    def doCompute(self, inc):
        tax = 0
        for lvl in self.rates:
            if inc > lvl[0]:
                tax = round(lvl[1] + (((inc - lvl[0] + 1) * lvl[2]) / 100.0), 2)
            if tax:
                break
        prb = self.allow[0]                # Primary Rebate
        arb = self.allow[1]                # Over 65 Rebate Extra
        nrb = self.allow[2]                # Over 75 Rebate Extra
        rmx = self.allow[3]                # Retrenchment Allowance
        return tax, prb, arb, nrb, rmx

    def doStaffLoans(self):
        if self.ignore == "Y":
            return
        loan = 0
        self.lonbl1 = 0
        self.lonbl2 = 0
        while loan != 99:
            totpay = float(ASD(self.totern) - ASD(self.totded))
            if totpay <= 0:
                return
            loan = loan + 1
            lmf = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
                self.opts["conum"]), ("wlm_empno", "=", self.empno),
                ("wlm_loan", "=", loan)], limit=1)
            if not lmf:
                continue
            dcode = lmf[self.sql.waglmf_col.index("wlm_code")]
            damnt = lmf[self.sql.waglmf_col.index("wlm_repay")]
            if not damnt:
                return  # No deduction amount
            ced = self.sql.getRec("wagedc", where=[("ced_cono", "=",
                self.opts["conum"]), ("ced_type", "=", "D"), ("ced_code", "=",
                dcode)], limit=1)
            if not ced:
                return  # Missing Loan wagedc record
            mthly = ced[self.sql.wagedc_col.index("ced_monthly")]
            earnt = ced[self.sql.wagedc_col.index("ced_earntype")]
            eglco = int(ced[self.sql.wagedc_col.index("ced_eglco")])
            eglno = int(ced[self.sql.wagedc_col.index("ced_eglno")])
            if eglno and not eglco:
                eglco = self.opts["conum"]
            if mthly == "Y" and self.mthly == "N":
                return
            lint = LoanInterest("S", self.opts["mf"].dbm, lmf, update="N",
                tdate=self.rundt)
            bal = float(ASD(lint.cap) + ASD(lint.rin))
            if bal <= 0:
                continue
            if damnt > bal:
                ded = bal
            else:
                ded = damnt
            if totpay <= ded:
                ded = totpay
            # Write Salary Transaction
            wagtf2 = [self.opts["conum"], self.empno, self.pgnum, self.rundt,
                "D", dcode, 0, ded, 0, "N", 0, earnt, eglco, eglno, 0, 0]
            self.doWriteWagtf2(wagtf2)
            # Write Loan Transaction
            ded = float(ASD(0) - ASD(ded))
            dat = [self.opts["conum"], self.empno, loan, "Payslip", 4,
                self.rundt, self.pgnum, ded, 0, 0, 0, self.curdt,
                "Salary Deduction", "N", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("wagltf", data=dat)

    def doWriteWagtf2(self, dat):
        old = self.sql.getRec("wagtf2", cols=["wt2_hrs", "wt2_eamt",
            "wt2_ramt"], where=[("wt2_cono", "=", dat[0]), ("wt2_empno", "=",
            dat[1]), ("wt2_page", "=", dat[2]), ("wt2_date", "=", dat[3]),
            ("wt2_type", "=", dat[4]), ("wt2_code", "=", dat[5])], limit=1)
        if old:
            old[0] = float(ASD(old[0]) + ASD(dat[6]))
            old[1] = float(ASD(old[1]) + ASD(dat[7]))
            old[2] = float(ASD(old[2]) + ASD(dat[8]))
            self.sql.updRec("wagtf2",
                cols=["wt2_hrs", "wt2_eamt", "wt2_ramt"],
                data=[old[0], old[1], old[2]],
                where=[
                    ("wt2_cono", "=", dat[0]),
                    ("wt2_empno", "=", dat[1]),
                    ("wt2_date", "=", dat[3]),
                    ("wt2_type", "=", dat[4]),
                    ("wt2_code", "=", dat[5])])
        else:
            self.sql.insRec("wagtf2", data=dat)

    def doPrint(self):
        if self.preview == "Y":
            runtp = "p"
        else:
            runtp = "o"
        psl = PrintPayslip(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.empnos, self.rundt, progs="y",
            runtp=runtp, repprt=self.df.repprt, tname=self.tname,
            repeml=self.df.repeml, message=self.mess, export=self.export,
            bestac=self.bestac)
        self.etotal = float(ASD(self.etotal) + ASD(psl.etotal))

    def doIntegration(self):
        tr1 = self.sql.getRec("wagtf1", where=[("wt1_cono", "=",
            self.opts["conum"]), ("wt1_date", "=", self.rundt), ("wt1_freq",
            "=", self.freq)], order="wt1_empno")
        if not tr1:
            return
        for t1 in tr1:
            empno = int(t1[self.sql.wagtf1_col.index("wt1_empno")])
            self.dept = int(t1[self.sql.wagtf1_col.index("wt1_dept")])
            # Check that Department Accounts are Loaded
            cols = ["dep_dr_coy", "dep_dr_sal", "dep_dr_com", "dep_cr_coy",
                "dep_cr_sal", "dep_cr_com"]
            self.glacno = self.sql.getRec("ctldep", cols=cols,
                where=[("dep_cono", "=", self.opts["conum"]),
                ("dep_code", "=", self.dept)], limit=1)
            if not self.glacno:
                showError(self.opts["mf"].body, "Department Error",
                    "Department %s %s Has No valid GL Account Numbers. "\
                    "Please Correct it and Re-Run Payslips." %
                    (self.opts["conum"], self.dept))
                return
            tr2 = self.sql.getRec("wagtf2", where=[("wt2_cono", "=",
                self.opts["conum"]), ("wt2_empno", "=", empno), ("wt2_date",
                "=", self.rundt)])
            if not tr2:
                continue
            for num, t2 in enumerate(tr2):
                # Check if Notional
                if t2[self.sql.wagtf2_col.index("wt2_taxcode")] == "T":
                    continue
                code = t2[self.sql.wagtf2_col.index("wt2_code")]
                wgtp = t2[self.sql.wagtf2_col.index("wt2_type")]
                gltp = t2[self.sql.wagtf2_col.index("wt2_gl_type")]
                coy1 = t2[self.sql.wagtf2_col.index("wt2_gl_econo")]
                acc1 = int(t2[self.sql.wagtf2_col.index("wt2_gl_eacno")])
                coy2 = self.glacno[3]
                acc2 = self.glacno[4]
                edc = self.sql.getRec("wagedc", cols=["ced_desc",
                    "ced_eglco", "ced_eglno"], where=[("ced_cono", "=",
                    self.opts["conum"]), ("ced_type", "=", wgtp), ("ced_code",
                    "=", code)], limit=1)
                edes = edc[0]
                if edc and not coy1:
                    coy1 = edc[1]
                if edc and not acc1:
                    acc1 = edc[2]
                if wgtp == "E":
                    if not coy1:
                        coy1 = self.glacno[0]
                    if gltp == "S" and not acc1:
                        acc1 = self.glacno[1]  # Salary
                    if gltp == "C" and not acc1:
                        acc1 = self.glacno[2]  # Commission
                elif not coy1:
                    coy1 = self.opts["conum"]
                # Expense Record
                eamt = float(t2[self.sql.wagtf2_col.index("wt2_eamt")])
                if not eamt:
                    continue
                if wgtp == "D":
                    eamt = float(ASD(0) - ASD(eamt))
                edes = "Sal/Wag - %s" % edes
                self.doGenTrn(coy1, acc1, eamt, edes)
                if coy1 != self.opts["conum"]:
                    err = self.doGenInt(coy1, eamt)
                    if err:
                        return
                if wgtp == "E":
                    if not coy2:
                        coy2 = self.glacno[3]
                    if gltp == "S" and not acc2:
                        acc2 = self.glacno[4]  # Salary
                    if gltp == "C" and not acc2:
                        acc2 = self.glacno[5]  # Commission
                else:
                    if not coy2:
                        coy2 = self.opts["conum"]
                    if not acc2:
                        acc2 = self.wagctl
                # Control Record
                eamt = float(ASD(0) - ASD(eamt))
                self.doGenTrn(coy2, acc2, eamt)
                if coy2 != self.opts["conum"]:
                    err = self.doGenInt(coy2, eamt)
                    if err:
                        return
        return True

    def doGenTrn(self, cono, acno, amnt, edes=None):
        if not edes:
            edes = "Salaries and Wages"
        batno = CCD("%03i%04i" % (self.opts["conum"], (self.curdt % 10000)),
            "Na", 7)
        refno = CCD(1, "Na", 9)
        whr = [("glt_cono", "=", cono), ("glt_acno", "=", acno),
            ("glt_curdt", "=", self.curdt), ("glt_trdt", "=", self.rundt),
            ("glt_type", "=", 4), ("glt_refno", "=", refno.work),
            ("glt_batch", "=", batno.work),
            ("glt_desc", "=", edes)]
        trn = self.sql.getRec("gentrn", cols=["glt_seq", "glt_tramt"],
            where=whr, limit=1)
        if not trn:
            data = [cono, acno, self.curdt, self.rundt, 4, refno.work,
                batno.work, amnt, 0.00, edes, "", "", 0, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
        else:
            newamt = float(ASD(trn[1]) + ASD(amnt))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[newamt],
                where=[("glt_seq", "=", int(trn[0]))])

    def doGenInt(self, cono, amnt):
        # General Ledger Transaction (Intercompany From)
        acc = self.sql.getRec("genint", cols=["cti_acno"],
            where=[("cti_cono", "=", self.opts["conum"]), ("cti_inco", "=",
            cono)], limit=1)
        if not acc:
            showError(self.opts["mf"].body, "Inter Company Error",
                "Invalid Account %s for Company %s in %s" % (acc, cono,
                self.opts["conum"]))
            return "err"
        self.doGenTrn(self.opts["conum"], acc[0], amnt)
        # General Ledger Transaction (Intercompany To)
        acc = self.sql.getRec("genint", cols=["cti_acno"],
            where=[("cti_cono", "=", cono), ("cti_inco", "=",
            self.opts["conum"])], limit=1)
        if not acc:
            showError(self.opts["mf"].body, "Inter Company Error",
                "Invalid Account %s for Company %s in %s" % (acc,
                self.opts["conum"], cono))
            return "err"
        amnt = float(ASD(0) - ASD(amnt))
        self.doGenTrn(cono, acc[0], amnt)

# vim:set ts=4 sw=4 sts=4 expandtab:
