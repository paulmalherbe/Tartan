"""
SYNOPSIS
    Members Ledger Statements.

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

import copy, time
from TartanClasses import ASD, Balances, CCD, DrawForm, GetCtl, ProgressBar
from TartanClasses import Sql, TartanDialog
from tartanFunctions import askQuestion, doPrinter, getModName, dateDiff
from tartanFunctions import doChkCatChg, getSingleRecords, getVatRate
from tartanFunctions import copyList, mthendDate, showError
from tartanWork import mltrtp

class ml3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.tname = self.stpl
                self.mesno = 0
                self.doEnd()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.ldays = memctl["mcm_ldays"]
        self.lme = memctl["mcm_lme"]
        self.stpl = memctl["mcm_sttpl"]
        self.fromad = memctl["mcm_emadd"]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmes", "ctlmst", "memmst",
            "memtrn", "memadd", "memcat", "memctc", "memctp", "memctk",
            "memkon", "memlnk", "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        yy = int(self.lme / 10000)
        mm = (int(self.lme / 100) % 100) + 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nme = mthendDate((yy*10000) + (mm*100) + 1)
        mm += 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nne = mthendDate((yy*10000) + (mm*100) + 1)
        self.trtypes = []
        for t in mltrtp:
            self.trtypes.append(t[0])
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
                ("tpm_system", "=", "MEM")],
            "order": "tpm_tname"}
        self.mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": (
                ("mlm_memno", "", 0, "Mem-No"),
                ("mlm_oldno", "", 0, "Old-No"),
                ("mlm_idnum", "", 0, "Identity-Numb"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")),
            "where": [],
            "order": "mlm_surname, mlm_names",
            "sort": False}
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details")),
            "where": [("mss_system", "=", "MEM")],
            "order": "mss_message"}
        r1s = (
            ("All", "Z"),
            ("Active", "A"),
            ("Deceased", "D"),
            ("Inactive", "I"),
            ("Resigned", "R"),
            ("Suspended", "S"),
            ("Defaulted", "X"))
        r2s = (
            ("Yes","Y"),
            ("Range","R"),
            ("Singles", "S"),
            ("Print Only","P"),
            ("Email Only","E"))
        r3s = (
            ("Yes","Y"),
            ("No","N"))
        r4s = (
            ("Yes","Y"),
            ("No","N"),
            ("Current","C"))
        r5s = (
            ("Number", "N"),
            ("Surname", "M"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.stpl,"Y",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Status","",
                "A","Y",self.doStatus,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Whole File","",
                "Y","Y",self.doWhole,None,None,None),
            (("T",0,3,0),"IUI",6,"Member Start","Starting Number",
                1,"Y",self.doMember,self.mlm,None,None),
            (("T",0,3,0),"IUI",6,"End","Ending Number",
                999999,"Y",self.doMember,self.mlm,None,None),
            (("T",0,4,0),("IRB",r3s),0,"Current Year Only","",
                "N","Y",self.doCurrent,None,None,None),
            (("T",0,5,0),("IRB",r4s),0,"Zero Balances","",
                "C","Y",self.doZeros,None,None,None),
            (("T",0,6,0),("IRB",r3s),0,"Paid Transactions","",
                "Y","Y",self.doPaid,None,None,None),
            (("T",0,7,0),("IRB",r3s),0,"Minus Balances","",
                "N","Y",self.doMinus,None,None,None),
            (("T",0,8,0),"IUI",3,"Message Number","",
                "","Y",self.doMessno,mss,None,("efld",)),
            (("T",0,9,0),"ID1",10,"Statement Date","",
                self.sysdtw,"Y",self.doDat,None,None,("efld",)),
            (("T",0,10,0),("IRB",r5s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "MEM")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doStatus(self, frt, pag, r, c, p, i, w):
        self.status = w
        self.mlm["where"] = [("mlm_cono", "=", self.opts["conum"])]
        if self.status != "Z":    # Not All
            self.mlm["where"].append(("mlm_state", "=", self.status))

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole != "R":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            return "sk2"

    def doMember(self, frt, pag, r, c, p, i, w):
        if p == 3:
            self.start = w
        elif w < self.start:
            return "Invalid Member, Before From"
        else:
            self.to = w

    def doCurrent(self, frt, pag, r, c, p, i, w):
        self.current = w

    def doZeros(self, frt, pag, r, c, p, i, w):
        self.zeros = w
        if self.zeros == "Y":
            self.paid = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.paid)
            return "sk1"

    def doPaid(self, frt, pag, r, c, p, i, w):
        self.paid = w

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def doMessno(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "MEM"), ("mss_message", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Message Number"
        self.mesno = w

    def doDat(self, frt, pag, r, c, p, i, w):
        self.pro = False
        self.ynd = False
        if w > self.nne:
            showError(self.opts["mf"].body, "Month End Error",
                "More than Two Month Ends are Missing, Aborting ...")
            return "rf"
        if w > self.nme:
            if self.nme == self.opts["period"][2][0]:
                ok = askQuestion(self.opts["mf"].body, "Year End Error",
                    "A Year End as at %s Has Not Been Run\n\n"\
                    "Would You Like to Raise Pro-Forma Charges?" %
                    self.opts["period"][2][1])
                if ok == "yes":
                    self.pro = True
                    self.ynd = True
            else:
                ok = askQuestion(self.opts["mf"].body, "Month End Error",
                    "A Month End as at %s Has Not Been Run\n\n"\
                    "Would You Like to Raise Pro-Forma Charges?" %
                    CCD(self.nme, "D1", 10).disp)
                if ok == "yes":
                    self.pro = True
        self.datew = w
        self.dated = self.df.t_disp[pag][0][p]
        self.curdt = int(w / 100)

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        if "args" in self.opts:
            self.whole = "S"
            self.current = "N"
            self.zeros = "Y"
            self.paid = "Y"
            self.minus = "Y"
            self.mes = None
            self.mes = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "MEM"), ("mss_message", "=", 1)],
                limit=1)
            self.curdt = int(self.opts["args"][1] / 100)
            self.dated = CCD(self.opts["args"][1], "D1", 10).disp
            self.pro = False
            self.repprt = self.opts["args"][2]
            self.repeml = self.opts["args"][3]
            recs = [self.opts["args"][0]]
        else:
            self.df.closeProcess()
            self.repprt = self.df.repprt
            self.repeml = self.df.repeml
            whr = [("mlm_cono", "=", self.opts["conum"])]
            if self.status != "Z":    # Not All
                whr.append(("mlm_state", "=", self.status))
            if self.sort == "N":
                odr = "mlm_memno"
            else:
                odr = "mlm_surname"
            if self.whole == "S":
                recs = getSingleRecords(self.opts["mf"], "memmst",
                    ("mlm_memno", "mlm_surname", "mlm_names"), head=["X",
                    "Number", "Surname", "Names"], where=whr, order=odr,
                    selcol="mlm_surname")
            else:
                if self.whole == "R":
                    whr.append(("mlm_memno", "between", self.start, self.to))
                recs = self.sql.getRec("memmst", where=whr, order=odr)
                if not recs:
                    showError(self.opts["mf"].body, "Error",
                        "No Accounts Selected")
                    if "wait" not in self.opts:
                        self.opts["mf"].closeLoop()
                    return
            # Remove all linked accounts
            col = self.sql.memmst_col
            nos = []
            for acc in recs:
                nos.append(acc[col.index("mlm_memno")])
            chk = copyList(recs)
            for acc in chk:
                whr = [
                    ("mll_cono", "=", self.opts["conum"]),
                    ("mll_lnkno", "=", acc[col.index("mlm_memno")])]
                lnk = self.sql.getRec("memlnk", where=whr, limit=1)
                if lnk and lnk[1] in nos:
                    recs.remove(acc)
        if recs:
            self.emadd = self.repeml[2]
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()
            if self.repeml[1] == "N":
                mess = "Printing Statements"
            else:
                mess = "Printing and Emailing Statements"
            p = ProgressBar(self.opts["mf"].body, typ=mess, mxs=len(recs),
                esc=True)
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                if self.pro:
                    self.doProForma(rec)
                self.doProcess(rec)
            p.closeProgress()
            if self.pro:
                self.opts["mf"].dbm.rollbackDbase()
            if p.quit or not self.form.page:
                pass
            elif self.repeml[1] == "N" or self.emadd:
                self.repeml[2] = self.emadd
                self.doPrint()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

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
        self.form.document_date(self.dated)
        self.form.bank_details(cmc, ctm, 0)

    def doProForma(self, rec):
        self.refno = 0
        dmc = self.sql.memmst_col
        acc = [rec[dmc.index("mlm_memno")]]
        lnk = self.sql.getRec("memlnk", cols=["mll_lnkno"],
            where=[("mll_cono", "=", self.opts["conum"]),
            ("mll_memno", "=", acc[0])])
        for l in lnk:
            chk = self.sql.getRec("memmst", cols=["mlm_state"],
                where=[("mlm_cono", "=", self.opts["conum"]), ("mlm_memno",
                "=", l[0])], limit=1)
            if chk and chk[0] == "A":
                acc.append(l[0])
        for memno in acc:
            if self.ynd:
                data = doChkCatChg(self.opts["mf"], self.opts["conum"],
                    memno, self.datew)
                if data:
                    if not data[3]:
                        self.doRaiseCharge(memno, "B", data[0], data[1],
                            data[2], data[3], data[4], data[5], skip=True)
                    self.sql.delRec("memcat", where=[("mlc_cono", "=",
                        self.opts["conum"]), ("mlc_memno", "=", memno),
                        ("mlc_type", "=", "B"), ("mlc_code", "=", data[0])])
                    self.sql.insRec("memcat", data=[self.opts["conum"], memno,
                        "B", data[7], "", self.datew, 0, 0])
            cols = ["mlc_type", "mlc_code", "mcc_desc", "mcc_freq",
                "mlc_start", "mlc_end", "mlc_last"]
            wher = [
                ("mlc_cono", "=", self.opts["conum"]),
                ("mlc_memno", "=", memno),
                ("mlc_start", ">", 0),
                ("mlc_start", "<=", self.datew),
                ("mcc_cono=mlc_cono",),
                ("mcc_type=mlc_type",),
                ("mcc_code=mlc_code",),
                ("mcc_freq", "<>", "N")]
            cats = self.sql.getRec(tables=["memcat", "memctc"], cols=cols,
                where=wher, order="mlc_type, mlc_code")
            for ctyp, code, desc, freq, start, end, last in cats:
                if start > self.datew:
                    # Not yet Started
                    continue
                if last and end and end < self.datew:
                    # Ended
                    continue
                if last and freq == "O":
                    # Once Off
                    continue
                if last and last > self.opts["period"][2][0]:
                    # Already Raised for Next Period in Advance
                    continue
                if not self.ynd and last and freq == "A" and \
                        last >= self.opts["period"][1][0] and \
                        last <= self.opts["period"][2][0]:
                    # Already Raised in Financial Period
                    continue
                self.doRaiseCharge(memno, ctyp, code, start, end, last, freq,
                    desc)

    def doRaiseCharge(self, memno, ctyp, code, start, end, last, freq, desc, skip=False):
        if freq == "O":
            dte = True
            nxt = False
        else:
            dte = False
            nxt = bool(self.ynd or freq == "M")
            if not last:
                if dateDiff(start, self.nme, "days") > self.ldays:
                    dte = True
                else:
                    nxt = True
        if dte:
            trdt = start
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(memno, ctyp, code, desc, trdt, amt)
        if not skip and nxt:
            if end and self.datew > end:
                return
            trdt = self.datew
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(memno, ctyp, code, desc, trdt, amt)

    def doGetCharge(self, ctyp, code, date):
        prc = self.sql.getRec("memctp", where=[("mcp_cono", "=",
            self.opts["conum"]), ("mcp_type", "=", ctyp), ("mcp_code", "=",
            code), ("mcp_date", "<=", date)], order="mcp_date desc", limit=1)
        if not prc:
            # No Price
            return
        if prc[5] == "N" or (self.ynd and date == self.datew):
            # Not Pro Rata or End of Financial Year
            amt = CCD(prc[6], "UD", 12.2).work
        else:
            # Extract Pro Rata Rate
            mths = 17 - dateDiff(date, self.opts["period"][2][0], "months")
            if mths < 1:
                mths = 12
            amt = CCD(prc[mths], "UD", 12.2).work
        if not amt:
            # No Charge
            return
        else:
            return amt

    def doUpdateTables(self, memno, ctyp, code, desc, trdt, amt):
        batch = "PROFORM"
        self.refno += 1
        refno = "PF%07i" % self.refno
        curdt = int(trdt / 100)
        # VAT Rate and Amount
        vrte = getVatRate(self.sql, self.opts["conum"], self.taxdf, trdt)
        if vrte is None:
            vrte = 0.0
        vat = CCD(round(((amt * vrte) / 114), 2), "UD", 12.2).work
        # Members Ledger Transaction (memtrn)
        self.sql.insRec("memtrn", data=[self.opts["conum"], memno, 1, refno,
            batch, trdt, amt, vat, curdt, ctyp, code, desc, self.taxdf,
            "", self.opts["capnm"], self.sysdtw, 0], unique="mlt_refno")
        # Members Category Record (memcat)
        self.sql.updRec("memcat", cols=["mlc_last"], data=[trdt],
            where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno", "=",
            memno), ("mlc_type", "=", ctyp), ("mlc_code", "=", code)])

    def doProcess(self, mlm):
        dmc = self.sql.memmst_col
        tdc = self.form.sql.tpldet_col
        self.memno = mlm[dmc.index("mlm_memno")]
        self.doGetBalTrn()
        if not self.mlt[1]:
            return
        if self.zeros == "N" and not self.tbal:
            return
        elif self.zeros == "C" and not self.tbal and not self.mlt[2]:
            return
        if self.minus == "N" and self.tbal < 0:
            return
        eml = []
        kon = self.sql.getRec(tables=["memctk", "memkon"], cols=["mlk_detail"],
            where=[("mck_type", "=", "E"), ("mlk_cono", "=",
            self.opts["conum"]), ("mlk_memno", "=", self.memno),
            ("mlk_code=mck_code",)])
        for k in kon:
            eml.append(k[0])
        if self.whole == "E" and not eml:
            return
        elif self.whole == "P" and eml:
            return
        for col in dmc:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = mlm[dmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        self.doHeader(mlm, dmc, tdc)
        mlc, mlt = self.mlt[:2]
        if self.current == "Y":
            amt = 0
            bal = 0
            cdt = int(self.opts["period"][2][0] / 100)
            trn = copy.deepcopy(mlt)
            mlt = []
            while trn:
                rec = trn.pop()
                if rec[mlc.index("mlt_curdt")] < cdt:
                    amt = float(ASD(amt) + ASD(rec[mlc.index("mlt_tramt")]))
                    bal = float(ASD(bal) + ASD(rec[mlc.index("balance")]))
                else:
                    mlt.append(rec)
            if amt or bal:
                rec[mlc.index("mlt_type")] = 3
                rec[mlc.index("mlt_refno")] = "B/FWD"
                rec[mlc.index("mlt_batch")] = ""
                rec[mlc.index("mlt_tramt")] = amt
                rec[mlc.index("balance")] = bal
                rec[mlc.index("mlt_taxamt")] = 0
                rec[mlc.index("mlt_desc")] = "Balance Brought Forward"
                rec[mlc.index("mlt_taxind")] = ""
                rec[mlc.index("mlt_batind")] = ""
                mlt.insert(0, rec)
        if len(mlt) <= self.form.maxlines:
            self.doBody(mlc, mlt, tdc)
        else:
            amt = 0
            bal = 0
            lines = len(mlt) - self.form.maxlines + 1
            for _ in range(lines):
                trn = mlt.pop(0)
                amt = float(ASD(amt) + ASD(trn[mlc.index("mlt_tramt")]))
                bal = float(ASD(bal) + ASD(trn[mlc.index("balance")]))
            trn[mlc.index("mlt_type")] = 3
            trn[mlc.index("mlt_refno")] = "B/FWD"
            trn[mlc.index("mlt_batch")] = ""
            trn[mlc.index("mlt_tramt")] = amt
            trn[mlc.index("balance")] = bal
            trn[mlc.index("mlt_taxamt")] = 0
            trn[mlc.index("mlt_desc")] = "Balance Brought Forward"
            trn[mlc.index("mlt_taxind")] = ""
            trn[mlc.index("mlt_batind")] = ""
            mlt.insert(0, trn)
            self.doBody(mlc, mlt, tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        if self.repeml[1] == "Y" and not self.emadd:
            self.repeml[2] = eml
            self.doPrint()

    def doGetBalTrn(self):
        if self.paid == "Y":
            trans = "A"
        else:
            trans = "Y"
        bals = Balances(self.opts["mf"], "MEM", self.opts["conum"],
            self.curdt, (self.memno,))
        self.obal, self.tbal, self.ages, self.mlt = bals.doAllBals(trans=trans)
        lnk = self.sql.getRec("memlnk", cols=["mll_lnkno"],
            where=[("mll_cono", "=", self.opts["conum"]), ("mll_memno", "=",
            self.memno)])
        if not lnk:
            return
        for l in lnk:
            bals = Balances(self.opts["mf"], "MEM", self.opts["conum"],
                self.curdt, (l[0],))
            obal, tbal, ages, mlt = bals.doAllBals(trans=trans)
            for n, d in enumerate(mlt[1]):
                mlt[1][n][mlt[0].index("mlt_desc")] = "%s (%s)" % \
                    (d[mlt[0].index("mlt_desc")][:30],
                    d[mlt[0].index("mlt_memno")])
            self.obal = float(ASD(self.obal) + ASD(obal))
            self.tbal = float(ASD(self.tbal) + ASD(tbal))
            for x in range(5):
                self.ages[x] = float(ASD(self.ages[x]) + ASD(ages[x]))
            self.mlt[1].extend(mlt[1])
            self.mlt[2] += mlt[2]
        # Sort Transaction by Date
        self.mlt[1].sort(key=lambda x:x[mlt[0].index("mlt_trdt")])

    def doHeader(self, mlm, dmc, tdc):
        self.form.add_page()
        if "account_details" in self.form.tptp:
            tit = mlm[dmc.index("mlm_title")]
            sur = mlm[dmc.index("mlm_surname")]
            nam = mlm[dmc.index("mlm_names")]
            ini = ""
            for n, d in enumerate(nam.split()):
                if n < 3:
                    if not ini:
                        ini = d[0].upper()
                    else:
                        ini = "%s %s" % (ini, d[0].upper())
            nad = "%s %s %s" % (tit.strip(), ini.strip(), sur.strip())
            add = self.sql.getRec("memadd", where=[("mla_cono", "=",
                self.opts["conum"]), ("mla_memno", "=", self.memno),
                ("mla_type", "=", "P")], limit=1)
            adc = self.sql.memadd_col
            if add:
                if add[adc.index("mla_add1")]:
                    nad = "%s\n%s" % (nad, add[adc.index("mla_add1")])
                if add[adc.index("mla_add2")]:
                    nad = "%s\n%s" % (nad, add[adc.index("mla_add2")])
                if add[adc.index("mla_add3")]:
                    nad = "%s\n%s" % (nad, add[adc.index("mla_add3")])
                if add[adc.index("mla_city")]:
                    nad = "%s\n%s" % (nad, add[adc.index("mla_city")])
                if add[adc.index("mla_country")]:
                    nad = "%s\n%-s, %-s" % (nad, add[adc.index("mla_code")],
                        add[adc.index("mla_country")])
                else:
                    nad = "%s\n%s" % (nad, add[adc.index("mla_code")])
            else:
                nad = "\n\n\n\n\n"
            self.form.newdic["account_details_C00"][
                tdc.index("tpd_text")] = nad
        for key in self.form.newkey:
            nl = copyList(self.form.newdic[key])
            if nl[tdc.index("tpd_place")] != "A":
                continue
            if nl[tdc.index("tpd_detseq")] == "mlm_memno_C00":
                nl[tdc.index("tpd_text")] = self.memno
            self.form.doDrawDetail(nl)

    def doBody(self, mlc, mlt, tdc):
        text = self.form.sql.tpldet_col.index("tpd_text")
        self.tots = [0.0, 0.0, 0.0]
        count = 0
        for trans in mlt:
            if trans[mlc.index("mlt_type")] not in (5, 6) and \
                    trans[mlc.index("mlt_curdt")] == self.curdt:
                if self.paid == "Y":
                    self.tots[1] = float(ASD(self.tots[1]) + \
                        ASD(trans[mlc.index("mlt_tramt")]))
                else:
                    self.tots[1] = float(ASD(self.tots[1]) + \
                        ASD(trans[mlc.index("balance")]))
                if trans[mlc.index("mlt_taxamt")]:
                    self.tots[1] = float(ASD(self.tots[1]) - \
                        ASD(trans[mlc.index("mlt_taxamt")]))
                    self.tots[2] = float(ASD(self.tots[2]) + \
                        ASD(trans[mlc.index("mlt_taxamt")]))
            else:
                self.tots[0] = float(ASD(self.tots[0]) + \
                    ASD(trans[mlc.index("balance")]))
            for cod in self.form.body:
                if cod == "type_code":
                    c = "mlt_type"
                elif self.paid == "N" and cod == "mlt_tramt":
                    c = "balance"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[mlc.index(c)]
                    self.form.newdic[d][text] = mltrtp[ttyp - 1][0]
                else:
                    self.form.newdic[d][text] = trans[mlc.index(c)]
                self.form.doDrawDetail(self.form.newdic[d])
            count += 1
        for x in range(count, self.form.maxlines):
            for cod in self.form.body:
                d = "%s_C%02i" % (cod, x)
                self.form.newdic[d][tdc.index("tpd_text")] = "BLANK"
                self.form.doDrawDetail(self.form.newdic[d])

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
                if c == "120_day_balance":
                    line[tdc.index("tpd_text")] = self.ages[4]
                elif c == "90_day_balance":
                    line[tdc.index("tpd_text")] = self.ages[3]
                elif c == "60_day_balance":
                    line[tdc.index("tpd_text")] = self.ages[2]
                elif c == "30_day_balance":
                    line[tdc.index("tpd_text")] = self.ages[1]
                elif c == "current_balance":
                    line[tdc.index("tpd_text")] = self.ages[0]
                elif c == "total_arrears":
                    line[tdc.index("tpd_text")] = self.tots[0]
                elif c == "month_exclusive":
                    line[tdc.index("tpd_text")] = self.tots[1]
                elif c == "month_tax":
                    line[tdc.index("tpd_text")] = self.tots[2]
                elif c == "total_balance":
                    line[tdc.index("tpd_text")] = self.tbal
                self.form.doDrawDetail(line)

    def doTail(self, tdc):
        for c in self.form.tail:
            if c == "message" and not self.mesno:
                continue
            t = "%s_T00" % c
            if c in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[c])
            elif t in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[t])
            d = "%s_C00" % c
            if d in self.form.newdic:
                if d == "message_C00" and self.mesno:
                    mes = self.sql.getRec("ctlmes", cols=["mss_detail"],
                        where=[("mss_system", "=", "MEM"), ("mss_message", "=",
                        self.mesno)], limit=1)
                    self.form.newdic[d][tdc.index("tpd_text")] = mes[0]
                self.form.doDrawDetail(self.form.newdic[d])

    def doPrint(self):
        if self.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s" % (self.opts["conum"], self.memno)
        else:
            key = "%s_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        if self.form.saveFile(pdfnam, self.opts["mf"].window):
            head = "%s Statement at %s" % (self.opts["conam"], self.dated)
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, fromad=self.fromad,
                repprt=self.repprt, repeml=self.repeml)
        if self.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
