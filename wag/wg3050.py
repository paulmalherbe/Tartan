"""
SYNOPSIS
    Salaries and Wages IRP5 Statements Printing.

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

import csv, os, time
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import dateDiff, doPrinter, getModName, getSingleRecords
from tartanFunctions import payeTables, showError

class wg3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlsys", "ctlmst", "wagctl",
            "wagedc", "wagmst", "wagirp", "wagtf2", "wagrcv", "wagtxa",
            "wagtxr", "wagtf1"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        ctc = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        ctw = self.sql.getRec("wagctl", where=[("ctw_cono", "=",
            self.opts["conum"])], limit=1)
        if not ctc or not ctw:
            return
        self.coad1 = ctc[self.sql.ctlmst_col.index("ctm_add1")]
        self.coad2 = ctc[self.sql.ctlmst_col.index("ctm_add2")]
        self.coad3 = ctc[self.sql.ctlmst_col.index("ctm_add3")]
        try:
            self.cocod = int(ctc[self.sql.ctlmst_col.index("ctm_pcode")])
        except:
            self.cocod = 0
        self.cname = ctc[self.sql.ctlmst_col.index("ctm_contact")]
        self.cotel = ctc[self.sql.ctlmst_col.index("ctm_tel")]
        self.coeml = ctc[self.sql.ctlmst_col.index("ctm_email")].strip()
        try:
            self.regno = int(ctw[self.sql.wagctl_col.index("ctw_regno")])
        except:
            return
        self.sdlno = ctw[self.sql.wagctl_col.index("ctw_sdlno")]
        self.uifno = ctw[self.sql.wagctl_col.index("ctw_uifno")]
        self.trade = ctw[self.sql.wagctl_col.index("ctw_trade")]
        self.codip = ctw[self.sql.wagctl_col.index("ctw_irp_dip")]
        self.totrecs = 0
        self.totcode = 0
        self.totamnt = 0
        self.pdfnam = None
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Salaries IRP5 Statements (%s)" % self.__class__.__name__)
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname"),
                ("wgm_fname", "", 0, "Names"),
                ("wgm_start", "", 0, "Start-Date"),
                ("wgm_term", "", 0, "Term-Date"))}
        r1s = (("Live", "L"), ("Test", "T"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Yes","Y"),("Range","R"),("Singles", "S"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Submission Type","",
                "T","Y",self.doType,None,None,None),
            (("T",0,1,0),"IUI",4,"Tax Year","",
                0,"Y",self.doYear,None,None,("notzero",)),
            (("T",0,2,0),"ID1",10,"Cut Off Date","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",0,3,0),("IRB",r2s),0,"Reprint","Reprint Statements",
                "Y","Y",self.doReprint,None,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Preview","Preview Only",
                "Y","Y",self.doPreview,None,None,None),
            (("T",0,5,0),("IRB",r3s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            (("T",0,6,0),("IRB",r2s),10,"Include Other Companies","",
                "N","N",self.doCoy,None,None,None),
            (("T",0,7,0),"IUI",5,"From Employee","",
                "","Y",self.doEmp,wgm,None,None),
            (("T",0,8,0),"IUI",5,"To   Employee","To Employee",
                "","Y",self.doEmp,wgm,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","P"), mail=("B","Y"))

    def doType(self, frt, pag, r, c, p, i, w):
        if w == "L":
            self.rtype = "LIVE"
        else:
            self.rtype = "TEST"

    def doYear(self, frt, pag, r, c, p, i, w):
        self.taxyr = w
        self.allow, self.rates = payeTables(self.sql, self.taxyr)
        if not self.allow or not self.rates:
            showError(self.opts["mf"].body, "Missing Rates",
                "There are No Tax Rates for Year %s" % self.taxyr)
            self.doExit()
        self.sdate = CCD(((self.taxyr - 1) * 10000) + 301, "D1", 10)
        if self.taxyr % 4:
            self.edate = (self.taxyr * 10000) + 200 + 28
        else:
            self.edate = (self.taxyr * 10000) + 200 + 29
        if self.sysdtw < self.edate:
            self.edate = self.sysdtw
        self.edate = CCD(self.edate, "D1", 10)
        self.uifr = float(ASD(self.allow[5]) + ASD(self.allow[6]))
        self.sdlr = float(ASD(self.allow[7]) + ASD(self.allow[8]))
        self.df.loadEntry(frt, pag, p+1, data=self.edate.work)

    def doDate(self, frt, pag, r, c, p, i, w):
        yr = int(w / 10000)
        if yr < (self.taxyr - 1) or yr > self.taxyr:
            return "Invalid Date"
        self.taxmth = int(w / 100) % 100
        if self.taxmth < 3 and yr < self.taxyr:
            return "Invalid Date"
        if self.taxmth > 2 and yr == self.taxyr:
            return "Invalid Date"
        self.edate = CCD(w, "D1", 10)
        whr = [("wgm_cono", "=", self.opts["conum"]), ("wgm_start", "<",
            self.edate.work), ("(", "wgm_term", "=", 0, "or",
            "wgm_term", ">=", self.sdate.work, ")")]
        self.df.topf[0][7][8]["where"] = whr
        self.df.topf[0][8][8]["where"] = whr

    def doReprint(self, frt, pag, r, c, p, i, w):
        self.reprint = w
        seq = self.sql.getRec("wagirp", cols=["max(wip_irpno)"],
            where=[("wip_cono", "=", self.opts["conum"])], limit=1)
        if not seq[0]:
            self.lastreg = 0
            self.lastirp = 0
        else:
            self.lastirp = seq[0]
            reg = self.sql.getRec("wagirp", cols=["wip_genno"],
                where=[("wip_cono", "=", self.opts["conum"]), ("wip_irpno",
                "=", self.lastirp)], limit=1)
            self.lastreg = reg[0]
        if self.reprint == "Y":
            self.preview = "Y"
            self.df.loadEntry("T", 0, p+1, data=self.preview)
            return "sk1"

    def doPreview(self, frt, pag, r, c, p, i, w):
        self.preview = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole in ("Y", "S"):
            self.semp = 0
            self.eemp = 0
            self.df.loadEntry("T", 0, p+2, data=self.semp)
            self.df.loadEntry("T", 0, p+3, data=self.eemp)
            if self.whole == "S":
                self.other = "N"
                self.df.loadEntry("T", 0, p+1, data=self.other)
                return "sk3"
        else:
            self.other = "N"
            self.df.loadEntry("T", 0, p+1, data=self.other)
            return "sk1"

    def doCoy(self, frt, pag, r, c, p, i, w):
        self.other = w
        return "sk2"

    def doEmp(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("wagmst", cols=["wgm_sname"],
            where=[("wgm_cono", "=", self.opts["conum"]), ("wgm_empno", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Employee Number"
        if p == 7:
            self.semp = w
        else:
            self.eemp = w

    def doEnd(self):
        self.df.closeProcess()
        self.emldf = self.df.repeml[2]
        self.error = False
        self.doWriteHeader()
        if self.error:
            self.opts["mf"].dbm.rollbackDbase()
            self.closeProcess()
            return
        if self.df.repeml[1] == "N":
            self.printSetup()
        if not self.eemp:
            self.eemp = 99999
        if self.other == "Y":
            self.doSelCoy()
            if self.con == "X":
                return
            whr = [("wgm_cono", "in", tuple(self.con))]
        else:
            whr = [("wgm_cono", "=", self.opts["conum"])]
        whr.extend([("wgm_empno", "between", self.semp, self.eemp),
            ("wgm_paye", "=", "Y"), ("wgm_start", "<=", self.edate.work),
            ("(", "wgm_term", "=", 0, "or", "wgm_term", ">", self.sdate.work,
            ")")])
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "wagmst",
                ("wgm_empno", "wgm_sname"), where=whr)
        else:
            recs = self.sql.getRec("wagmst", where=whr,
                order="wgm_cono, wgm_empno")
        if not recs:
            showError(self.opts["mf"].body, "Error",
                "No Employees Selected")
        else:
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(rec)
                if self.error:
                    break
            p.closeProgress()
            if p.quit or self.error:
                self.opts["mf"].dbm.rollbackDbase()
            else:
                # Employer Total
                total = CCD(self.totamnt, "UD", 15.2)
                self.irp5fl.write('6010,%015i,6020,%015i,6030,%015.2f,9999\n' \
                    % (self.totrecs, self.totcode, total.work))
                self.irp5fl.close()
                self.doCheckTotals()
                if self.error:
                    self.opts["mf"].dbm.rollbackDbase()
                else:
                    if self.preview == "Y":
                        self.opts["mf"].dbm.rollbackDbase()
                    else:
                        self.opts["mf"].dbm.commitDbase()
                    if self.df.repeml[1] == "N" or self.emldf:
                        self.df.repeml[2] = self.emldf
                        self.doPrint()
        self.closeProcess()

    def doWriteHeader(self):
        # Header Record
        if self.reprint == "N" or not self.lastreg:
            self.lastreg += 1
        self.irp5nm = os.path.join(self.opts["mf"].rcdic["wrkdir"],
            "irp5fl_%03i_%04i.txt" % (self.opts["conum"], self.taxyr))
        self.irp5fl = open(self.irp5nm, "w")
        # Employer Details
        try:
            recon = int("%4i%02i" % (self.taxyr, self.taxmth))
            self.irp5fl.write('2010,"%s",2015,"%4s",2020,%010i,2022,"%-10s",'\
                '2024,"%-10s",2025,"%s",2026,"%s",2027,"%s",2028,"tartan",'\
                '2030,%04i,2031,%06i,2035,%04i,2064,"%s",2065,"%s",2066,"%s",'\
                '2080,%04i,9999\n' % (self.opts["conam"].strip(), self.rtype,
                self.regno, self.sdlno, self.uifno, self.cname.strip(),
                self.cotel[:11].strip(), self.coeml, self.taxyr, recon,
                self.trade, self.coad1[:24].strip(), self.coad2.strip(),
                self.coad3[:21].strip(), self.cocod))
            self.totrecs += 1
            for code in (2010,2015,2020,2022,2024,2025,2026,2027,2028,2030,
                    2031, 2035,2064,2065,2066,2080,9999):
                self.totcode += code
        except Exception as err:
            showError(None, "Header Record Error", "There is a Problem "\
                "with your Company or Control Records, Please Fix the "\
                "Problem and then Reprint\n\n%s" % err)
            self.error = True

    def doSelCoy(self):
        tit = ("Company Selection",)
        self.coys = self.sql.getRec("ctlmst", cols=["ctm_cono",
            "ctm_name"], order="ctm_cono")
        coy = {
            "stype": "C",
            "titl": "",
            "head": ("Num", "Name"),
            "data": self.coys,
            "mode": "M",
            "comnd": self.doCoyCmd}
        r1s = (("Yes","Y"),("Include","I"),("Exclude","E"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Companies","",
                "Y","N",self.doAllCoy,None,None,None,None),
            (("T",0,1,0),"INA",30,"Companies","",
                "","N",self.doCoySel,coy,None,None,None))
        self.cf = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doCoyEnd, "y"),), txit=(self.doCoyExit,))
        self.cf.mstFrame.wait_window()

    def doAllCoy(self, frt, pag, r, c, p, i, w):
        self.con = w
        if self.con == "Y":
            self.con = []
            for coy in self.coys:
                self.con.append(coy[0])
            return "nd"
        elif self.con == "I":
            self.cf.topf[pag][2][8]["titl"] = "Select Companies to Include"
        else:
            self.cf.topf[pag][2][8]["titl"] = "Select Companies to Exclude"

    def doCoyCmd(self, frt, pag, r, c, p, i, w):
        c = ""
        for co in w:
            if int(co[0]):
                c = c + str(int(co[0])) + ","
        if len(c) > 1:
            c = c[:-1]
        self.cf.loadEntry(frt, pag, p, data=c)

    def doCoySel(self, frt, pag, r, c, p, i, w):
        if w[-1:] == ",":
            w = w[:-1]
        self.coy = w.split(",")

    def doCoyEnd(self):
        if self.con == "I":
            self.con = self.coy
        elif self.con == "E":
            self.con = []
            for co in self.coys:
                self.con.append(int(co[0]))
            for co in self.coy:
                del self.con[self.con.index(int(co))]
            self.con.sort()
        self.doCoyClose()

    def doCoyExit(self):
        self.con = "X"
        self.doCoyClose()

    def doCoyClose(self):
        self.cf.closeProcess()

    def doProcess(self, wgm):
        col = self.sql.wagmst_col
        self.com = wgm[col.index("wgm_cono")]
        self.emp = wgm[col.index("wgm_empno")]
        if self.reprint == "N":
            chk = self.sql.getRec("wagirp", cols=["wip_irpno"],
                where=[("wip_cono", "=", self.com), ("wip_empno", "=",
                self.emp), ("wip_year", "=", self.taxyr)], limit=1)
            if chk:
                return
        self.sname = wgm[col.index("wgm_sname")]
        fname = wgm[col.index("wgm_fname")].split()
        if len(fname) == 1:
            self.fname = fname[0]
        else:
            self.fname = "%s %s" % (fname[0], fname[1])
        self.inits = ""
        for i in fname:
            self.inits = self.inits + i[0]
        self.nature = wgm[col.index("wgm_nature")]
        try:
            self.idno = int(wgm[col.index("wgm_idno")])
        except:
            self.idno = 0
        self.dob = CCD(wgm[col.index("wgm_dob")], "D1", 10)
        self.emadd = wgm[col.index("wgm_emadd")].strip()
        self.addr1 = wgm[col.index("wgm_addr1")]
        self.addr2 = wgm[col.index("wgm_addr2")]
        self.addr3 = wgm[col.index("wgm_addr3")]
        try:
            self.pcode = int(wgm[col.index("wgm_pcode")])
        except:
            self.pcode = 0
        self.taxno = CCD(wgm[col.index("wgm_taxno")], "NA", 10)
        self.start = CCD(wgm[col.index("wgm_start")], "D1", 10)
        if self.start.work < self.sdate.work:
            self.start = self.sdate
        self.term = CCD(wgm[col.index("wgm_term")], "D1", 10)
        if not self.term.work:
            self.term = self.edate
        self.freq = wgm[col.index("wgm_freq")]
        # Test number with modulus 10
        if self.taxno.work and len(self.taxno.work) == 10:
            paye10 = 0
            for x in range(0, 9, 2):
                paye10b = int(self.taxno.work[x]) * 2
                paye10 = paye10 + int(paye10b / 10) + (paye10b % 10)
                if x < 8:
                    paye10 = paye10 + int(self.taxno.work[(x + 1)])
            paye10 = paye10 % 10
            paye10 = 10 - paye10
            if paye10 != int(self.taxno.work[9]):
                self.taxno = CCD("0000000000", "NA", 10)
        else:
            self.taxno = CCD("0000000000", "NA", 10)
        #
        self.vol = wgm[col.index("wgm_vol_over")]
        rate = CCD(wgm[col.index("wgm_fix_rate")], "UD", 6.2)
        if rate.work:
            self.fixed = "Y"
        else:
            self.fixed = "N"
        self.direct = wgm[col.index("wgm_direct")]
        self.btype = wgm[col.index("wgm_btype")]
        self.bname = wgm[col.index("wgm_bname")]
        self.branch = wgm[col.index("wgm_bbranch")]
        self.bacno = wgm[col.index("wgm_bacno")]
        self.payee = wgm[col.index("wgm_bpayee")]
        self.relate = wgm[col.index("wgm_relate")]
        # Extract all transactions
        wt1 = self.sql.getRec("wagtf1", cols=["sum(wt1_uifpay)",
            "sum(wt1_sdlpay)"], where=[("wt1_cono", "=", self.com),
            ("wt1_empno", "=", self.emp), ("wt1_date", "between",
            self.sdate.work, self.edate.work)], limit=1)
        self.uifpay, self.sdlpay = wt1
        wt2 = self.sql.getRec(tables=["wagtf2", "wagedc"],
            cols=["wt2_type", "ced_ror", "ced_taxcode",
            "round(sum(wt2_eamt), 2)"], where=[("wt2_cono", "=",
            self.com), ("wt2_empno", "=", self.emp),
            ("wt2_date", "between", self.sdate.work, self.edate.work),
            ("ced_cono=wt2_cono",), ("ced_type=wt2_type",),
            ("ced_code=wt2_code",), ("ced_ror", "between", 3601, 4103)],
            group="wt2_type, ced_ror, ced_taxcode",
            order="wt2_type desc, ced_ror")
        if wt2:
            if self.df.repeml[1] == "Y":
                self.printSetup()
            self.printHeader()
            if self.error:
                return
            # Retirement Funding
            self.rfund = "N"
            for trn in wt2:
                if trn[1] in (4001, 4002, 4003, 4004):
                    self.rfund = "Y"
            #
            trtp = None
            for trn in wt2:
                chk = self.sql.getRec("wagrcv", cols=["rcv_desc"],
                    where=[("rcv_code", "=", trn[1])], limit=1)
                if not chk:
                    showError(self.opts["mf"].body, "Invalid Code",
                        """This Receiver of Revenue Code (%s) Does Not Exist.

Please Amend the Earnings or Deduction Codes containing It and then Try Again.""" % trn[1])
                    break
                trn.insert(3, chk[0])
                if trn[0] == "E":
                    trtp = self.doEarningCode(trtp, trn)
                else:
                    if trtp == "E":
                        self.printGross()
                    if trn[1] < 4101:
                        trtp = self.doDeductionCode(trtp, trn)
                    elif trn[1] == 4102:
                        trtp = "T"
                        site = self.doSite()
                        self.printTax(site, trn)
            if trtp == "E":
                self.printGross()
            if trtp != "T" and self.ttyp == "IT3(a)":
                self.printTax()
            if self.preview == "N":
                self.sql.insRec("wagirp", data=[self.opts["conum"], self.taxyr,
                    self.lastreg, self.emp, self.lastirp])
            if self.df.repeml[1] == "Y" and not self.emldf:
                self.df.repeml[2] = self.emadd
                self.doPrint()

    def doEarningCode(self, trtp, trn):
        if not trtp:
            self.fpdf.setFont(style="B")
            self.fpdf.drawText("Income Sources")
            self.fpdf.drawText("Code    Description              "\
                "                        R/F-Ind         Amount")
            self.fpdf.setFont()
        # Earning Codes 3601-3617, 3651-3667, 3701-3718, 3751-3768
        # 3801-3816, 3851-3866, 3901-3922, 3951-3957
        trtp = "E"
        if trn[1] == 3601:
            rfund = self.rfund
        else:
            rfund = "N"
        if trn[1] == 3810:
            trn[4] = round((trn[4] / 3), 2)
        self.fpdf.drawText("%-4s    %-50s  %1s         %9s" % \
            (trn[1], trn[3], rfund, int(trn[4])))
        self.emprec = '%s,%04i,%015i' % (self.emprec, trn[1], int(trn[4]))
        self.totcode += trn[1]
        if trn[1] in (3602, 3604, 3609, 3612, 3703, 3705, 3709, 3714):
            # Non Taxable Income
            self.totntax = self.totntax + int(trn[4])
        else:
            if trn[2] == "O":
                # Annual Payment
                self.totannp = self.totannp + int(trn[4])
            if rfund == "Y":
                # Retirement Funding
                self.totyrfi = self.totyrfi + int(trn[4])
            else:
                self.totnrfi = self.totnrfi + int(trn[4])
            self.totincm = self.totincm + int(trn[4])
        self.totamnt = float(ASD(self.totamnt) + ASD(int(trn[4])))
        return trtp

    def doDeductionCode(self, trtp, trn):
        if trtp in (None, "E"):
            self.fpdf.setFont(style="B")
            self.fpdf.drawText("Deductions")
            self.fpdf.drawText("Code    Description              "\
                "                        Clearance       Amount")
            self.fpdf.setFont()
        # Deduction Codes 4001-4007, 4018, 4024, 4026, 4030, 4474, 4493, 4497
        trtp = "D"
        self.fpdf.drawText("%-4s    %-50s  %1s         %9s" % \
            (trn[1], trn[3], "N", int(trn[4])))
        self.emprec = '%s,%04i,%015i' % (self.emprec, trn[1], int(trn[4]))
        self.totcode += trn[1]
        self.totamnt = float(ASD(self.totamnt) + ASD(int(trn[4])))
        return trtp

    def doSite(self):
        inc = round((self.allow[4] * self.base / self.pers), 4)
        tax = 0
        for lvl in self.rates:
            if inc > lvl[0]:
                tax = round(lvl[1] + (((inc - lvl[0] + 1) * lvl[2]) / 100.0),2)
            if tax:
                break
        tax = float(ASD(tax) - ASD(self.allow[0]))
        age = dateDiff(self.dob.work, self.edate.work, "years")
        if age > 64:
            tax = float(ASD(tax) - ASD(self.allow[1]))
        if age > 74:
            tax = float(ASD(tax) - ASD(self.allow[2]))
        tax = round((tax * self.pers / self.base), 2)
        if tax < 0:
            return 0
        else:
            return tax

    def doCheckTotals(self):
        csvrdr = csv.reader(open(self.irp5nm, "r"), delimiter=",",
            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        empls = 0
        count = 0
        total = 0
        empcd = (2010, 3010)
        totcd = (4472, 4473, 4474, 4485, 4486, 4487, 4493, 4497)
        fincd = (6010, 6020, 6030)
        check = {}
        for line in csvrdr:
            for num in range(0, len(line), 2):
                if int(line[0]) in fincd:
                    if int(line[num]) != 9999:
                        if int(line[num]) in (6010, 6020):
                            check["C%s" % line[num]] = int(line[num + 1])
                        else:
                            check["C%s" % line[num]] = float(line[num + 1])
                elif int(line[num]) == 9999:
                    count += int(line[num])
                else:
                    if int(line[num]) in empcd:
                        empls += 1
                    count += int(line[num])
                    if int(line[num]) > 3600 and int(line[num]) < 4150:
                        total += float(line[num+1])
                    elif int(line[num]) in totcd:
                        total += float(line[num+1])
        check["C6010"] -= empls
        check["C6020"] -= count
        check["C6030"] = float(ASD(check["C6030"]) - ASD(total))
        if check["C6010"] or check["C6020"] or check["C6030"]:
            showError(None, "Total Error", "There is a Problem "\
                "with Totals Record. Please Contact Your IT Manager.")
            self.error = True

    def printSetup(self):
        pth = self.opts["mf"].rcdic["wrkdir"]
        if self.df.repeml[1] == "Y":
            key = "%s_%s" % (self.com, self.emp)
            self.pdfnam = getModName(pth, self.__class__.__name__, key,
                ext="pdf")
        elif not self.pdfnam:
            self.pdfnam = getModName(pth, self.__class__.__name__,
                self.opts["conum"], ext="pdf")
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=90)

    def printHeader(self):
        self.fpdf.add_page()
        # Employee Totals
        self.totannp = 0
        self.totntax = 0
        self.totntax = 0
        self.totyrfi = 0
        self.totnrfi = 0
        self.totincm = 0
        # Calculate Pay Periods
        if self.freq == "M":
            self.base = 12
            y1 = int(self.term.work / 10000)
            y2 = int(self.start.work / 10000)
            m1 = int((self.term.work - (y1 * 10000)) / 100)
            m2 = int((self.start.work - (y2 * 10000)) / 100)
            self.pers = 1 + ((y1 - y2) * self.base) + (m1 - m2)
            while self.pers > self.base:
                self.pers = self.pers - self.base
        else:
            days = dateDiff(self.start.work, self.term.work, "days")
            if self.freq == "W":
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
        # Extract PAYE Paid
        tax = self.sql.getRec(tables=["wagtf2", "wagedc"],
            cols=["round(sum(wt2_eamt), 2)"], where=[("wt2_cono", "=",
            self.com), ("wt2_empno", "=", self.emp), ("wt2_date",
            "between", self.sdate.work, self.edate.work),
            ("ced_cono=wt2_cono",), ("ced_type=wt2_type",),
            ("ced_code=wt2_code",), ("ced_ror", "=", 4102)])
        if tax[0][0]:
            self.tax = CCD(tax[0][0], "UD", 12.2)
        else:
            self.tax = CCD(0, "UD", 12.2)
        if self.tax.work:
            self.ttyp = "IRP 5"
        else:
            self.ttyp = "IT3(a)"
        #
        if self.reprint == "Y":
            acc = self.sql.getRec("wagirp", cols=["wip_irpno"],
                where=[("wip_cono", "=", self.opts["conum"]), ("wip_year", "=",
                self.taxyr), ("wip_empno", "=", self.emp)], limit=1)
            if not acc:
                self.lastirp += 1
            else:
                self.lastirp = acc[0]
        else:
            self.lastirp += 1
        irp5 = CCD(self.lastirp, "UI", 10)
        self.irp5 = "%010i%4i%2i%014i" % (self.regno, self.taxyr,
            self.taxmth, self.lastirp)
        # Print Fields
        self.fpdf.drawText()
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("%6s                    EMPLOYEES TAX "\
            "CERTIFICATE                      %6s" % (self.ttyp, self.ttyp))
        self.fpdf.drawText()
        self.fpdf.drawText("Employer Information")
        self.fpdf.setFont(size=8)
        self.fpdf.drawText("Trading Name      %-30s" % self.opts["conam"])
        self.fpdf.drawText("IRP 5 Number      %s                   "\
            "   Business Address  %30s" % (irp5.disp, self.coad1))
        self.fpdf.drawText("Reference No.     %10s                 "\
            "                       %30s" % (self.regno, self.coad2))
        self.fpdf.drawText("Tax Year          %s                       "\
            "                       %30s" % (self.taxyr, self.coad3))
        self.fpdf.drawText("Dipl. Immunity    %1s                          "\
            "                       %30s" % (self.codip, self.cocod))
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Employee Information")
        self.fpdf.setFont(size=8)
        self.fpdf.drawText("Nature of Person  %1s                          "\
            "     Employee Surname  %30s" % (self.nature, self.sname))
        self.fpdf.drawText("First Two Names   %-30s  "\
            "Employee Initials %s" % (self.fname, self.inits))
        self.fpdf.drawText("Identity Number   %13s              "\
            "     Residential Addr  %30s" % (self.idno, self.addr1))
        self.fpdf.drawText("Passport Number                              "\
            "                       %30s" % self.addr2)
        self.fpdf.drawText("Date of Birth     %s                 "\
            "                       %30s" % (self.dob.disp, self.addr3))
        self.fpdf.drawText("Company/CC/Trust                             "\
            "                       %30s" % self.pcode)
        self.fpdf.drawText("Income Tax Number %s" % self.taxno.disp)
        self.fpdf.drawText("                                             "\
            "     Employee Number   %5s" % self.emp)
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Tax Calculation Information")
        self.fpdf.setFont(size=8)
        self.fpdf.drawText("Employed From  %s        Employed To    %s"\
            "        Voluntary Over-Deduction  %1s" % (self.start.disp,
            self.term.disp, self.vol))
        self.fpdf.drawText("Periods in Year  %08.4f        Periods Worked"\
            "   %08.4f        Fixed Rate %s Directive %13s" % (self.base,
            self.pers, self.fixed, self.direct))
        self.fpdf.drawText()
        # Employee Details
        # Removing 3070, pasport number and 3075, country of issue
        try:
            if self.dob.work % 1000000 != int(int(self.idno) / 10000000):
                raise Exception
            try:
                btype = int(self.btype)
            except:
                btype = 0
            try:
                bacno = int(self.bacno)
            except:
                bacno = 0
            try:
                taxno = int(self.taxno.work)
            except:
                taxno = 0
            self.emprec = '3010,"%s",3015,"%s",3020,"%1s",3025,%04i,'\
                '3030,"%s",3040,"%s",3050,"%s",3060,%013i,3080,%08i,'\
                '3100,%010i,3125,"%s",3136,"%s",3147,"%s",3148,"%s",'\
                '3149,"%s",3150,"%s",3160,"%s",3170,%08i,3180,%08i,'\
                '3200,%08.4f,3210,%08.4f,3214,"%s",3215,"%s",3216,"%s",'\
                '3217,"%s",3218,"X",3230,"%s",3240,%01i,3241,%s,3242,%s,'\
                '3245,"%s",3246,%01i' % (self.irp5, self.ttyp, self.nature,
                self.taxyr, self.sname, self.fname, self.inits, self.idno,
                self.dob.work, taxno, self.emadd, self.cotel[:11].strip(),
                self.coad1[:24].strip(), self.coad2.strip(),
                self.coad3[:21].strip(), self.cocod, self.emp,
                self.start.work, self.term.work, self.base, self.pers,
                self.addr1, self.addr2, self.addr3, self.pcode,
                self.direct, btype, bacno, self.branch, self.payee,
                self.relate)
            for code in (3010,3015,3020,3025,3030,3040,3050,3060,3080,
                    3100,3125,3136,3147,3148,3149,3150,3160,3170,3180,
                    3200,3210,3214,3215,3216,3217,3218,3230,3240,3241,
                    3242,3245,3246):
                self.totcode += code
            self.totrecs += 1
        except Exception as err:
            showError(None, "Header Record Error", "There is a Problem "\
                "with Employee %s's Record. Please Fix the Problem and "\
                "then Reprint\n\n%s" % (self.emp, err))
            self.error = True

    def printGross(self):
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Gross Remuneration")
        self.fpdf.drawText("Code    Description                            "\
            "                          Amount")
        self.fpdf.setFont()
        amount = CCD(self.totannp, "UI", 15)
        if amount.work:
            self.fpdf.drawText("3695    Annual Payments                   "\
                "                      %s" % amount.disp)
        amount = CCD(self.totntax, "UI", 15)
        if amount.work:
            self.fpdf.drawText("3696    Non-Taxable Income                "\
                "                      %s" % amount.disp)
        amount = CCD(self.totyrfi, "UI", 15)
        if amount.work:
            self.fpdf.drawText("3697    Retirement Funding Income         "\
                "                      %s" % amount.disp)
        amount = CCD(self.totnrfi, "UI", 15)
        if amount.work:
            self.fpdf.drawText("3698    Non-Retirement Funding Income     "\
                "                      %s" % amount.disp)
        amount = CCD(self.totincm, "UI", 15)
        if amount.work:
            self.fpdf.drawText("3699    Gross Remuneration                "\
                "                      %s" % amount.disp)
        self.fpdf.drawText()
        # Gross Earnings
        self.emprec = '%s,3696,%015i,3697,%015i,3698,%015i' % (self.emprec,
            self.totntax, self.totyrfi, self.totnrfi)
        for code in (3696,3697,3698):
            self.totcode += code
        self.totamnt = float(ASD(self.totamnt) + ASD(self.totntax))
        self.totamnt = float(ASD(self.totamnt) + ASD(self.totyrfi))
        self.totamnt = float(ASD(self.totamnt) + ASD(self.totnrfi))

    def printTax(self, site=None, trn=None):
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText("Employees Tax Deductions")
        self.fpdf.drawText("Code    Description                       "\
            "                               Amount")
        self.fpdf.setFont()
        if not site and not trn:
            # Tax Codes IT3(a) 4150
            self.fpdf.drawText("4150    Reason Code                       "\
                "                         %s" % "          02")
            self.emprec = '%s,4150,%02i' % (self.emprec, 2)
            for code in (4150,):
                self.totcode += code
            total = CCD(0, "UD", 15.2)
        else:
            # Tax Codes 4101, 4102, 4115
            site = CCD(site, "UD", 15.2)
            if site.work >= trn[4]:
                site = CCD(trn[4], "UD", 15.2)
                paye = 0
            else:
                paye = float(ASD(trn[4]) - ASD(site.work))
            paye = CCD(paye, "UD", 15.2)
            total = CCD(trn[4], "UD", 15.2)
            if site.work:
                self.fpdf.drawText("4101    Standard Income Tax - SITE   "\
                    "                           %s" % site.disp)
            if paye.work:
                self.fpdf.drawText("4102    Pay As You Earn              "\
                    "                           %s" % paye.disp)
            if total.work:
                self.fpdf.drawText("4103    Total Employees Tax          "\
                    "                           %s" % total.disp)
            self.emprec = '%s,4101,%014.2f,4102,%014.2f' % (self.emprec,
                site.work, paye.work)
            for code in (4101,4102):
                self.totcode += code
            self.totamnt = float(ASD(self.totamnt) + ASD(site.work))
            self.totamnt = float(ASD(self.totamnt) + ASD(paye.work))
        # Tax Codes 4141, 4142, 4149, 4116, 4150
        uif = CCD((self.uifpay * self.uifr) / 100.0, "UD", 15.2)
        sdl = CCD((self.sdlpay * self.sdlr) / 100.0, "UD", 15.2)
        total = CCD(total.work, "UD", 15.2)
        self.emprec = '%s,4141,%014.2f,4142,%014.2f,4149,%014.2f,9999\n' % \
            (self.emprec, uif.work, sdl.work, total.work)
        for code in (4141,4142,4149,9999):
            self.totcode += code
        self.totamnt = float(ASD(self.totamnt) + ASD(uif.work))
        self.totamnt = float(ASD(self.totamnt) + ASD(sdl.work))
        self.totamnt = float(ASD(self.totamnt) + ASD(total.work))
        self.irp5fl.write(self.emprec)

    def doPrint(self):
        if self.fpdf.saveFile(self.pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=self.pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
