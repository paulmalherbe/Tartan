"""
SYNOPSIS
    Loans Statements.

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
from operator import itemgetter
from TartanClasses import ASD, CCD, DrawForm, GetCtl, LoanInterest, ProgressBar
from TartanClasses import Sql, TartanDialog
from tartanFunctions import copyList, doPrinter, getModName, getSingleRecords
from tartanFunctions import mthendDate, projectDate, showError
from tartanWork import lntrtp

class ln3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.capb = lonctl["cln_capb"]
        self.capf = lonctl["cln_capf"]
        self.lint = lonctl["cln_last"]
        self.stpl = lonctl["cln_tplnam"]
        self.fromad = lonctl["cln_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmes", "ctlmst", "ctlynd",
            "lonmf1", "lonmf2", "lontrn", "tplmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "S"),
                ("tpm_system", "=", "LON")],
            "order": "tpm_tname"}
        r1s = (("No","N"),("Yes","Y"))
        r2s = (("Number","A"),("Name","N"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.stpl,"Y",self.doTplNam,tpm,None,None),
            (("T",0,1,0),"Id2",7,"Start Period","",
                self.sper,"N",self.doSPer,None,None,None),
            (("T",0,2,0),"ID2",7,"End Period","",
                self.eper,"N",self.doEPer,None,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Whole File","",
                "N","N",self.doWhole,None,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Sort Order","",
                "A","N",self.doSort,None,None,None),
            (("T",0,5,0),("IRB",r1s),0,"Include Zero Balances","",
                "N","N",self.doZeros,None,None,None),
            (("T",0,6,0),("IRB",r1s),0,"Include Pending Interest","",
                "N","N",self.doPend,None,None,None),
            (("T",0,7,0),("IRB",r1s),0,"Interest Totals Only","",
                "N","N",self.doITots,None,None,None,None,
                "Show Interest as Period Totals or by Individual Periods"))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "LON")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doSPer(self, frt, pag, r, c, p, i, w):
        self.sperw = w
        self.sperd = self.df.t_disp[pag][0][p]

    def doEPer(self, frt, pag, r, c, p, i, w):
        self.eperw = w
        self.eperd = self.df.t_disp[pag][0][p]
        self.date = CCD(mthendDate((w * 100) + 1), "D1", 10)

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doZeros(self, frt, pag, r, c, p, i, w):
        self.zeros = w

    def doPend(self, frt, pag, r, c, p, i, w):
        self.pend = w

    def doITots(self, frt, pag, r, c, p, i, w):
        self.itot = w

    def doEnd(self):
        self.df.closeProcess()
        self.emadd = self.df.repeml[2]
        if self.whole == "N":
            recs = getSingleRecords(self.opts["mf"], "lonmf1",
                ("lm1_acno", "lm1_name"), where=[("lm1_cono",
                "=", self.opts["conum"])])
        else:
            whr = [("lm1_cono", "=", self.opts["conum"])]
            if self.sort == "A":
                odr = "lm1_acno"
            else:
                odr = "lm1_name"
            recs = self.sql.getRec("lonmf1", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Error",
                "No Accounts Selected")
        else:
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, rec in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(rec)
            p.closeProgress()
            if p.quit or not self.form.page:
                pass
            elif self.df.repeml[1] == "N" or self.emadd:
                self.df.repeml[2] = self.emadd
                self.doPrint()
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
        self.form.document_date(self.date.disp)
        self.form.bank_details(cmc, ctm, 0)

    def doProcess(self, lm1):
        l1c = self.sql.lonmf1_col
        tdc = self.form.sql.tpldet_col
        self.acno = lm1[l1c.index("lm1_acno")]
        self.emlto = lm1[l1c.index("lm1_email")]
        self.form.account_details("lm1", l1c, lm1, 1)
        for col in l1c:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = lm1[l1c.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        lonmf2 = self.sql.getRec("lonmf2", where=[("lm2_cono",
            "=", self.opts["conum"]), ("lm2_acno", "=", self.acno)],
            order="lm2_loan")
        for loan in lonmf2:
            self.doStatement(tdc, loan)

    def doStatement(self, tdc, lm2):
        l2c = self.sql.lonmf2_col
        ltc = copyList(self.sql.lontrn_col)
        self.loan = lm2[l2c.index("lm2_loan")]
        for col in l2c:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = lm2[l2c.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        if self.pend == "Y":
            # Raise Pending Interest
            LoanInterest("L", self.opts["mf"].dbm, lm2, update="Y",
                tdate=self.date.work, batch="Pending", capnm="")
        # Get Transactions
        whr = [
            ("lnt_cono", "=", self.opts["conum"]),
            ("lnt_acno", "=", self.acno),
            ("lnt_loan", "=", self.loan),
            ("lnt_curdt", "<=", self.eperw)]
        odr = "lnt_curdt, lnt_trdt, lnt_type, lnt_refno"
        if self.itot == "Y":
            w = whr[:]
            w.append(("lnt_type", "<>", 4))
            trns = self.sql.getRec("lontrn", where=w, order=odr)
            if self.capb == "A":                        # Anniversary
                fcap = [lm2[l2c.index("lm2_start")], 0]
                fcap[0] = (int(fcap[0] / 100) * 100) + 1
                if self.capf == "A":
                    fcap[1] = projectDate(fcap[0], 11, typ="months")
                else:
                    fcap[1] = projectDate(fcap[0], 5, typ="months")
                fcap[1] = mthendDate(fcap[1])
            else:                                       # Financial
                periods = self.sql.getRec("ctlynd",
                    cols=["cye_period", "cye_start", "cye_end"],
                    where=[("cye_cono", "=", self.opts["conum"])],
                    order="cye_period")
                fcap = [periods[0][1], periods[0][2]]
                if self.capf == "B":                    # Bi-Annual
                    fcap[1] = projectDate(fcap[1], -6, typ="months")
            capdt = [copyList(fcap)]
            while fcap[1] < self.date.work:
                if self.capf == "A":
                    fcap[0] = projectDate(fcap[0], 1, typ="years")
                    fcap[1] = projectDate(fcap[1], 1, typ="years")
                else:
                    fcap[0] = projectDate(fcap[0], 6, typ="months")
                    fcap[1] = projectDate(fcap[1], 6, typ="months")
                if fcap[1] > self.date.work:
                    fcap[1] = self.date.work
                capdt.append(copyList(fcap))
            for capd in capdt:
                w = whr[:]
                w.append(("lnt_type", "=", 4))
                w.append(("lnt_trdt", "between", capd[0], capd[1]))
                ints = self.sql.getRec("lontrn", where=w, order=odr)
                if not ints:
                    continue
                ddes = "Dr Int %s to %s"
                cdes = "Cr Int %s to %s"
                dbal = 0
                cbal = 0
                for trn in ints:
                    amt = trn[ltc.index("lnt_tramt")]
                    if amt < 0:
                        cbal = float(ASD(cbal) + ASD(amt))
                    else:
                        dbal = float(ASD(dbal) + ASD(amt))
                if dbal:
                    trn[ltc.index("lnt_tramt")] = dbal
                    trn[ltc.index("lnt_desc")] = ddes % (
                        CCD(int(capd[0] / 100), "D2", 7).disp,
                        CCD(int(capd[1] / 100), "D2", 7).disp)
                    trns.append(copyList(trn))
                if cbal:
                    trn[ltc.index("lnt_tramt")] = cbal
                    trn[ltc.index("lnt_desc")] = cdes % (
                        CCD(int(capd[0] / 100), "D2", 7).disp,
                        CCD(int(capd[1] / 100), "D2", 7).disp)
                    trns.append(copyList(trn))
            trns = sorted(trns, key=itemgetter(5))
        else:
            trns = self.sql.getRec("lontrn", where=whr, order=odr)
        if not trns:
            return
        self.bal = 0
        self.tots = 0
        if self.sperw:
            obal = 0
            trans = copyList(trns)
            for trn in trans:
                tramt = trn[self.sql.lontrn_col.index("lnt_tramt")]
                if trn[self.sql.lontrn_col.index("lnt_curdt")] < self.sperw:
                    obal = float(ASD(obal) + ASD(tramt))
                    trns.remove(trn)
            trn[ltc.index("lnt_type")] = 3
            trn[ltc.index("lnt_trdt")] = (self.sperw * 100) + 1
            trn[ltc.index("lnt_refno")] = "O/Bal"
            trn[ltc.index("lnt_batch")] = ""
            trn[ltc.index("lnt_tramt")] = obal
            trn[ltc.index("lnt_desc")] = "Opening Balance"
            trn[ltc.index("lnt_batind")] = ""
            trns.insert(0, trn)
        trans = []
        for trn in trns:
            tramt = trn[ltc.index("lnt_tramt")]
            self.tots = float(ASD(self.tots) + ASD(tramt))
            if tramt < 0:
                trn.extend([0, tramt])
            else:
                trn.extend([tramt, 0])
            trans.append(trn)
        ltc.extend(["line_debit", "line_credit"])
        if self.zeros == "N" and not self.tots:
            return
        self.doBody(ltc, trans, tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        if self.pend == "Y":
            self.opts["mf"].dbm.rollbackDbase()
        if self.df.repeml[1] == "Y" and not self.emadd:
            self.df.repeml[2] = self.emlto
            self.doPrint()

    def doPrint(self):
        if self.df.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s_%s" % (self.opts["conum"], self.acno, self.loan)
        else:
            key = "%s_all_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        if self.form.saveFile(pdfnam, self.opts["mf"].window):
            head = "%s Statement at %s" % (self.opts["conam"], self.date.disp)
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        if self.df.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doBody(self, ltc, lnt, tdc):
        page = 0
        count = 0
        text = tdc.index("tpd_text")
        for trans in lnt:
            if not count:
                page += 1
                count = self.doHeader(page)
            if count == self.form.maxlines:
                page = self.doCfwd(page)
                count = self.doHeader(page)
            for cod in self.form.body:
                if cod == "type_code":
                    c = "lnt_type"
                elif cod == "line_paid":
                    c = "paid"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[ltc.index(c)]
                    self.form.newdic[d][text] = lntrtp[ttyp - 1][0]
                elif c in ("line_debit", "line_credit"):
                    tramt = trans[ltc.index(c)]
                    self.bal = float(ASD(self.bal) + ASD(tramt))
                    self.form.newdic[d][text] = trans[ltc.index(c)]
                elif c == "line_balance":
                    self.form.newdic[d][text] = self.bal
                else:
                    self.form.newdic[d][text] = trans[ltc.index(c)]
                self.form.doDrawDetail(self.form.newdic[d])
            count += 1
        for x in range(count, self.form.maxlines):
            for cod in self.form.body:
                d = "%s_C%02i" % (cod, x)
                self.form.newdic[d][tdc.index("tpd_text")] = "BLANK"
                self.form.doDrawDetail(self.form.newdic[d])

    def doHeader(self, page):
        self.form.add_page()
        tdc = self.form.sql.tpldet_col
        for key in self.form.newkey:
            nl = copyList(self.form.newdic[key])
            if nl[tdc.index("tpd_place")] != "A":
                continue
            if nl[tdc.index("tpd_detseq")] == "lm1_acno_C00":
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
                if c == "total_balance":
                    line[tdc.index("tpd_text")] = self.tots
                self.form.doDrawDetail(line)

    def doTail(self, tdc):
        for c in self.form.tail:
            t = "%s_T00" % c
            if c in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[c])
            elif t in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[t])
            d = "%s_C00" % c
            if d in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[d])

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
