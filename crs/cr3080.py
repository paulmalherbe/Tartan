"""
SYNOPSIS
    Creditors Ledger Remittance Advices.

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
from TartanClasses import ASD, DrawForm, GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName, getSingleRecords, getTrn
from tartanFunctions import copyList, showError
from tartanWork import crtrtp

class cr3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "ctlmst", "crsctl",
            "crsmst", "crstrn", "crsage", "gentrn", "tplmst"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.glint = crsctl["ctc_glint"]
        self.bestac = crsctl["ctc_bestac"]
        self.besttp = crsctl["ctc_besttp"]
        self.bankac = crsctl["ctc_bankac"]
        self.tplnam = crsctl["ctc_tplnam"]
        self.fromad = crsctl["ctc_emadd"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if gc.chkRec(self.opts["conum"], ctlctl, ["crs_ctl"]):
                return
            self.crsctl = ctlctl["crs_ctl"]
        acc = self.sql.getRec("crstrn", cols=["max(crt_ref1)"],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_type", "=", 5),
            ("crt_ref1", "like", "EFT______")], limit=1)
        try:
            self.cats = int(acc[0][3:])
            self.refs = int(acc[0][3:]) + 1
        except:
            self.cats = 0
            self.refs = 1
        self.etotal = 0
        return True

    def mainProcess(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "R"),
                ("tpm_system", "=", "CRS")],
            "order": "tpm_tname"}
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")]}
        r1s = (("Yes","Y"),("Range","R"),("Singles", "S"))
        r2s = (("Yes","Y"),("No","N"))
        r3s = (("Number","N"),("Name","M"),("Postal Code","P"))
        r4s = (("Monthly","M"),("Daily","D"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.tplnam,"Y",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            [["T",0,2,0],"INA",7,"From Account","",
                "","Y",self.doAcc,crm,None,None],
            [["T",0,3,0],"INA",7,"To   Account","",
                "","Y",self.doAcc,crm,None,None],
            (("T",0,4,0),("IRB",r3s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,5,0),("IRB",r4s),0,"Terms Base","",
                "M","Y",self.doFrequency,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"Exceptions","",
                "N","Y",self.doExcepts,None,None,None),
            (("T",0,7,0),"ID1",10,"Due Date","",
                self.sysdtw,"Y",self.doDuedat,None,None,("efld",)),
            (("T",0,8,0),"ID1",10,"Payment Date","",
                self.sysdtw,"Y",self.doPaydat,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "R"), ("tpm_system", "=", "CRS")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole in ("Y", "S"):
            self.sacc = ""
            self.eacc = ""
            self.df.loadEntry("T", 0, p+1, data=self.sacc)
            self.df.loadEntry("T", 0, p+2, data=self.eacc)
            return "sk2"

    def doAcc(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("crsmst", cols=["crm_name", "crm_stat"],
            where=[("crm_cono", "=", self.opts["conum"]), ("crm_acno", "=",
                w)], limit=1)
        if not chk:
            return "Invalid Creditors Account"
        if not chk[1] == "X":
            return "Invalid Account, Redundant"
        if c == 3:
            self.sacc = w
        else:
            self.eacc = w

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doFrequency(self, frt, pag, r, c, p, i, w):
        self.freq = w

    def doExcepts(self, frt, pag, r, c, p, i, w):
        self.excepts = w

    def doDuedat(self, frt, pag, r, c, p, i, w):
        self.duedtw = w
        self.duedtd = self.df.t_disp[pag][0][p]

    def doPaydat(self, frt, pag, r, c, p, i, w):
        self.paydtw = w
        self.paydtd = self.df.t_disp[pag][0][p]
        self.curdt = int(self.paydtw / 100)
        self.batno = "E%s" % self.curdt

    def doEnd(self):
        self.df.closeProcess()
        if self.excepts == "Y":
            self.doExceptions()
        self.emadd = self.df.repeml[2]
        if self.bestac:
            self.export = open(os.path.join(self.opts["mf"].rcdic["wrkdir"],
                "best%03d_%s.txt" % (self.opts["conum"], self.paydtw)), "w")
            # Header for BEST
            self.export.write("%1s%4s%-40s%8s%1s%8s%-15s%1s%2s%1s%9s%2s%4s"\
                "\r\n" % ("*", self.bestac, self.opts["conam"], self.paydtw,
                "Y", "", "CREDITORS EFT", "+", self.besttp, 0, "", "01",
                "LIVE"))
        else:
            self.export = None
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "crsmst",
                ("crm_acno", "crm_name"), where=[("crm_cono", "=",
                self.opts["conum"]), ("crm_termsb", "=", self.freq),
                ("crm_pyind", "<>", "N"), ("crm_stat", "<>", "X")])
        else:
            if not self.eacc:
                self.eacc = "zzzzzzz"
            whr = [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_acno", "between", self.sacc, self.eacc),
                ("crm_termsb", "=", self.freq),
                ("crm_pyind", "<>", "N"),
                ("crm_stat", "<>", "X")]
            if self.sort == "N":
                odr = "crm_acno"
            elif self.sort == "M":
                odr = "crm_name"
            else:
                odr = "crm_pcod"
            recs = self.sql.getRec("crsmst", where=whr, order=odr)
            if not recs:
                showError(self.opts["mf"].body, "Error",
                    "No Accounts Selected")
        if recs:
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    self.opts["mf"].dbm.rollbackDbase()
                    break
                self.doProcess(rec)
            p.closeProgress()
            if p.quit or not self.form.page:
                pass
            elif self.df.repeml[1] == "N" or self.emadd:
                self.df.repeml[2] = self.emadd
                self.doPrint()
            if self.bestac:
                # Trailer for BEST
                value = int(round((self.etotal * 100), 0))
                self.export.write("%1s%4s%1s%30s%013u%47s\r\n" % \
                    (2, self.bestac, "T", "", value, ""))
                self.export.close()
                if self.glint == "Y" and self.etotal:
                    # Create total transactions in GL
                    data = [self.opts["conum"], self.crsctl, self.curdt,
                        self.paydtw, 2, self.refno, self.batno, self.etotal,
                        0.0, "Payment EFT%06i to EFT%06i" % (self.refs,
                        self.cats),
                        "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                    data[1] = self.bankac
                    data[7] = float(ASD(0) - ASD(self.etotal))
                    self.sql.insRec("gentrn", data=data)
                self.opts["mf"].dbm.commitDbase(ask=True,
                    mess="""Would you like to commit all elecronic payments?

If you decide to do this, you must remember to upload the BEST file to the Bank otherwise you are NOT going to Reconcile!""", default="no")
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doExceptions(self):
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_termsb", "=", self.freq),
                ("crm_stat", "<>", "X")]}
        crt = {
            "stype": "R",
            "tables": ("crstrn",),
            "cols": (
                ("crt_ref1", "", 0, "Reference", "Y"),
                ("crt_type", ("XX", crtrtp), 3, "Typ"),
                ("crt_trdt", "", 0, "Date"),
                ("crt_tramt", "", 0, "    Amount"),
                ("paid", "SD", 13.2, "      Paid"),
                ("balance", "SD", 13.2, "   Balance"),
                ("crt_paydt", "", 0, "Pay-Date"),
                ("crt_payind", "", 0, "I"),
                ("crt_payamt", "", 0, "  Pay-Amnt")),
            "wtype": "D",
            "where": [],
            "order": "crt_ref1"}
        types = []
        for x in range(1, len(crtrtp) + 1):
            types.append((x, crtrtp[x - 1][1]))
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": types}
        fld = (
            (("T",0,0,0),"I@crm_acno",0,"","",
                "","N",self.doExAcNo,crm,None,("notblank",)),
            (("T",0,0,0),"O@crm_name",0,""),
            (("C",0,0,1),"I@crt_type",0,"", "",
                "","N",self.doExTrnTyp,typ,None,("in",(1,2,3,4,5))),
            (("C",0,0,0),"I@crt_ref1",0,"","",
                "","N",self.doExTrnRef,crt,None,("notblank",)),
            (("C",0,0,2),"O@crt_trdt",0,""),
            (("C",0,0,3),"OSD",13.2,"Balance"),
            (("C",0,0,4),"I@crt_payind",0,"","",
                "","N",self.doExInd,None,None,("in", ("Y", "N"))),
            (("C",0,0,5),"I@crt_paydt",0,"","",
                "","N",self.doExDte,None,None,("efld",)),
            (("C",0,0,6),"I@crt_payamt",0,"","",
                "","N",self.doExAmt,None,None,("efld",)))
        tnd = ((self.doExEndTop,"n"),)
        txt = (self.doExExitTop,)
        cnd = ((self.doExEndCol,"y"),)
        cxt = (self.doExExitCol,)
        self.ex = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, cend=cnd, cxit=cxt)
        self.ex.mstFrame.wait_window()

    def doExAcNo(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", cols=["crm_name",
            "crm_termsb", "crm_pyind", "crm_stat"], where=[("crm_cono",
            "=", self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[1] != self.freq:
            return "Invalid Terms Base"
        if acc[2] == "N":
            return "Invalid Payment Indicator"
        if acc[3] == "X":
            return "Invalid Account, Redundant"
        self.exacc = w
        self.ex.loadEntry(frt, pag, p+1, data=acc[0])

    def doExEndTop(self):
        self.ex.focusField("C", 0, 1)

    def doExExitTop(self):
        self.opts["mf"].dbm.commitDbase(ask=True,
            mess="Would you like to commit these exceptions?")
        self.ex.closeProcess()

    def doExTrnTyp(self, frt, pag, r, c, p, i, w):
        self.extyp = w
        data = []
        # Build the data for the F1 choice selection
        col, dat = getTrn(self.opts["mf"].dbm, "crs", whr=[("crt_cono", "=",
            self.opts["conum"]), ("crt_acno", "=", self.exacc), ("crt_type",
            "=", w)], zer="N")
        if dat:
            cols = ("crt_ref1", "crt_type", "crt_trdt", "crt_tramt", "paid",
                "balance", "crt_paydt", "crt_payind", "crt_payamt")
            for d in dat:
                rec = []
                for cc in cols:
                    rec.append(d[col.index(cc)])
                data.append(rec)
        self.ex.colf[0][1][8]["where"] = data

    def doExTrnRef(self, frt, pag, r, c, p, i, w):
        col = ["crt_trdt", "balance", "crt_payind", "crt_paydt", "crt_payamt"]
        whr = [
            ("crt_cono", "=", self.opts["conum"]),
            ("crt_acno", "=", self.exacc),
            ("crt_type", "=", self.extyp),
            ("crt_ref1", "=", w)]
        c, d = getTrn(self.opts["mf"].dbm, "crs", whr=whr, lim=1)
        if not d:
            return "Invalid Transaction Number"
        if not d[0][c.index("balance")]:
            return "Transaction Has No Balance"
        self.exref = w
        self.exdte = d[0][c.index("crt_paydt")]
        self.examt = d[0][c.index("crt_payamt")]
        for pos, fld in enumerate(col):
            self.ex.loadEntry(frt, pag, p+1+pos, data=d[0][c.index(fld)])

    def doExInd(self, frt, pag, r, c, p, i, w):
        self.exind = w
        if self.exind == "N":
            return "nd"

    def doExDte(self, frt, pag, r, c, p, i, w):
        self.exdte = w

    def doExAmt(self, frt, pag, r, c, p, i, w):
        self.examt = w

    def doExEndCol(self):
        # Update Transaction"
        self.sql.updRec("crstrn", cols=["crt_payind", "crt_paydt",
            "crt_payamt"], data=[self.exind, self.exdte, self.examt],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_acno", "=",
            self.exacc), ("crt_type", "=", self.extyp), ("crt_ref1", "=",
            self.exref)])
        self.ex.advanceLine(0)

    def doExExitCol(self):
        self.ex.focusField("T", 0, 1)

    def doLoadStatic(self):
        cmc = self.sql.ctlmst_col
        ctm = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        for fld in cmc:
            dat = ctm[cmc.index(fld)]
            if fld in self.form.tptp:
                if fld == "ctm_logo":
                    self.form.letterhead(cmc, ctm, fld, dat)
                    continue
                self.form.tptp[fld][1] = dat
        if "letterhead" in self.form.tptp:
            self.form.letterhead(cmc, ctm, "letterhead", None)
        self.form.document_date(self.duedtd)

    def doProcess(self, crm):
        cmc = self.sql.crsmst_col
        tdc = self.form.sql.tpldet_col
        self.acno = crm[cmc.index("crm_acno")]
        eml = crm[cmc.index("crm_acc_email")]
        self.form.account_details("crm", cmc, crm, 1)
        for col in cmc:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = crm[cmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        whr = [
            ("crt_cono", "=", self.opts["conum"]),
            ("crt_acno", "=", self.acno),
            ("crt_payind", "=", "Y"),
            ("crt_paydt", "<=", self.duedtw)]
        ctc, crt = getTrn(self.opts["mf"].dbm, "crs", cdt=self.curdt,
            whr=whr, zer="N")
        if not crt:
            return
        bal = 0
        self.pay = 0
        for d in crt:
            if d[ctc.index("balance")] < 0:
                d[ctc.index("crt_payamt")] = d[ctc.index("balance")]
            bal = float(ASD(bal) + ASD(d[ctc.index("balance")]))
            self.pay = float(ASD(self.pay) + ASD(d[ctc.index("crt_payamt")]))
        if self.pay > bal:
            self.pay = bal
        if self.pay > 0:
            self.bname = crm[cmc.index("crm_bname")]
            self.bibt = crm[cmc.index("crm_bibt")]
            self.bacc = crm[cmc.index("crm_bacc")]
            if self.bname and self.bibt and self.bacc:
                self.ptype = "E"                        # Electronic
                test = False
                while not test:
                    self.cats += 1
                    self.refno = "EFT%06i" % self.cats
                    # Check if Reference Number Already Exists
                    chk = self.sql.getRec("crstrn", where=[("crt_cono",
                        "=", self.opts["conum"]), ("crt_acno", "=", self.acno),
                        ("crt_type", "=", 5), ("crt_ref1", "=", self.refno)])
                    if not chk:
                        test = True
            else:
                self.ptype = "C"                        # Cheque
            self.doBody(ctc, crt, tdc)
            self.doTotal(tdc)
            self.doTail(tdc)
            if self.df.repeml[1] == "Y" and not self.emadd:
                self.df.repeml[2] = eml
                self.doPrint()

    def doPrint(self):
        if self.df.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s" % (self.opts["conum"], self.acno)
        else:
            key = "%s_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        self.form.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header="%s Remittance Advice" % self.opts["conam"],
            repprt=self.df.repprt, fromad=self.fromad, repeml=self.df.repeml)
        if self.df.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doBody(self, ctc, crt, tdc):
        page = 0
        count = 0
        text = self.form.sql.tpldet_col.index("tpd_text")
        for trans in crt:
            trbal = trans[ctc.index("balance")]
            payamt = trans[ctc.index("crt_payamt")]
            if payamt > trbal:
                payamt = trbal
            trans[ctc.index("balance")] = payamt
            if not count:
                page += 1
                count = self.doHeader(page)
            if count == self.form.maxlines:
                page = self.doCfwd(page)
                count = self.doHeader(page)
            for cod in self.form.body:
                if cod == "type_code":
                    c = "crt_type"
                elif cod == "line_paid":
                    c = "paid"
                elif cod == "line_balance":
                    c = "balance"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[ctc.index(c)]
                    self.form.newdic[d][text] = crtrtp[ttyp - 1][0]
                else:
                    self.form.newdic[d][text] = trans[ctc.index(c)]
                self.form.doDrawDetail(self.form.newdic[d])
            if self.ptype == "E" and self.bestac:
                trtp = trans[ctc.index("crt_type")]
                ref1 = trans[ctc.index("crt_ref1")]
                # Create Ageing Transaction
                self.sql.insRec("crsage", data=[self.opts["conum"], self.acno,
                    trtp, ref1, self.curdt, 5, self.refno, payamt, 0])
            count += 1
        for x in range(count, self.form.maxlines):
            for cod in self.form.body:
                d = "%s_C%02i" % (cod, x)
                self.form.newdic[d][tdc.index("tpd_text")] = "BLANK"
                self.form.doDrawDetail(self.form.newdic[d])

    def doHeader(self, page):
        tdc = self.form.sql.tpldet_col
        self.form.add_page()
        for key in self.form.newkey:
            nl = copyList(self.form.newdic[key])
            if nl[tdc.index("tpd_place")] != "A":
                continue
            if nl[tdc.index("tpd_detseq")] == "crm_acno_C00":
                nl[tdc.index("tpd_text")] = self.acno
            elif nl[tdc.index("tpd_detseq")] == "page_number_C00":
                nl[tdc.index("tpd_text")] = str(page)
            self.form.doDrawDetail(nl)
        return 0

    def doCfwd(self, page):
        if "carried_forward" in self.form.tptp:
            tdc = self.form.sql.tpldet_col
            line = copyList(self.form.cfwd)
            line[tdc.index("tpd_text")] = "Continued on Page %i" % (page + 1)
            self.form.doDrawDetail(line)
        return page + 1

    def doTotal(self, tdc):
        for c in self.form.total:
            t = "%s_T00" % c
            if c in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[c])
            elif t in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[t])
            d = "%s_C00" % c
            if d in self.form.newdic:
                line = self.form.newdic[d]
                if c == "total_payment":
                    line[tdc.index("tpd_text")] = self.pay
                self.form.doDrawDetail(line)
        if self.ptype == "E" and self.bestac:
            value = int(round((self.pay * 100), 0))
            self.export.write("%1s%4s%06u%-7s%019u%1s%1s%011u%-20s%10s"\
                "%-15s%1s\r\n" % (2, self.bestac, self.bibt, self.acno,
                int(self.bacc), "", "1", value, self.bname, "",
                self.opts["conam"][:15], ""))
            self.etotal = float(ASD(self.etotal) + ASD(self.pay))
            # Create Payment and Ageing Transaction
            p = float(ASD(0) - ASD(self.pay))
            self.sql.insRec("crstrn", data=[self.opts["conum"], self.acno, 5,
                self.refno, self.batno, self.paydtw, "", p, 0.0, 0.0,
                self.curdt, 0, "", 0.0, "Electronic Payment", "", "",
                self.opts["capnm"], self.sysdtw, 0])
            self.sql.insRec("crsage", data=[self.opts["conum"], self.acno, 5,
                self.refno, self.curdt, 5, self.refno, p, 0])

    def doTail(self, tdc):
        for c in self.form.tail:
            t = "%s_T00" % c
            if c in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[c])
            elif t in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[t])
            d = "%s_C00" % c
            if d in self.form.newdic:
                line = self.form.newdic[d]
                if c == "eft_message" and self.ptype == "E" and self.bestac:
                    line[tdc.index("tpd_text")] = "ELECTRONIC TRANSFER AT %s "\
                        "REFERENCE %s" % (self.paydtd, self.refno)
                self.form.doDrawDetail(line)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
