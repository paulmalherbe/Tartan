"""
SYNOPSIS
    Debtors Ledger Statements.

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
from TartanClasses import ASD, Balances, DrawForm, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getModName, getSingleRecords, copyList
from tartanFunctions import showError
from tartanWork import drtrtp

class dr3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmes", "ctlmst", "drschn",
            "drsmst", "drstrn", "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.chains = drsctl["ctd_chain"]
        self.stpl = drsctl["ctd_tplnam"]
        self.ageing = drsctl["ctd_ageing"]
        self.fromad = drsctl["ctd_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        if self.chains == "N":
            self.schn = 0
            self.echn = 0
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
                ("tpm_system", "=", "DRS")],
            "order": "tpm_tname"}
        drc = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1"))}
        if self.chains == "Y":
            drm["where"] = [("drm_cono", "=", self.opts["conum"])]
            drm["whera"] = [["C", "drm_chain", 0, 1]]
        else:
            drm["where"] = [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_chain", "=", 0)]
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details")),
            "where": [("mss_system", "=", "STA")]}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Yes","Y"),("Range","R"),("Singles", "S"))
        r3s = (("Number","N"),("Name","M"),("Postal Code","P"))
        fld = [
            [["T",0,0,0],"INA",20,"Template Name","",
                self.stpl,"Y",self.doTplNam,tpm,None,None],
            [["T",0,1,0],("IRB",r1s),0,"Open Item","",
                "Y","Y",self.doOItem,None,None,None],
            [["T",0,2,0],"IUI",2,"Maximum Pages","",
                1,"Y",self.doPages,None,None,None],
            [["T",0,3,0],("IRB",r2s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None],
            [["T",0,4,0],"IUI",3,"From Chain","",
                "","Y",self.doChn,drc,None,None],
            [["T",0,5,0],"INA",7,"From Account","",
                "","Y",self.doAcc,drm,None,None],
            [["T",0,6,0],"INA",3,"To Chain","",
                "","Y",self.doChn,drc,None,None],
            [["T",0,7,0],"INA",7,"To Account","",
                "","Y",self.doAcc,drm,None,None],
            [["T",0,8,0],("IRB",r3s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None],
            [["T",0,9,0],("IRB",r1s),0,"Include Zero Balances","",
                "N","Y",self.doZeros,None,None,None],
            [["T",0,10,0],("IRB",r1s),0,"Include Negative Balances","",
                "N","Y",self.doMinus,None,None,None],
            [["T",0,11,0],("IRB",r1s),0,"Include Stopped Accounts","",
                "N","Y",self.doStops,None,None, None],
            [["T",0,12,0],("IRB",r1s),0,"Include Redundant Accounts","",
                "N","Y",self.doRedu,None,None, None],
            [["T",0,13,0],("IRB",r1s),0,"Include Allocated Transactions","",
                "N","Y",self.doAlloc,None,None,None],
            [["T",0,14,0],"ID1",10,"Statement Date","",
                self.sysdtw,"Y",self.doDat,None,None,("efld",)],
            [["T",0,15,0],"IUI",3,"Message Number","",
                "","Y",self.doMessno,mss,None,("efld",)]]
        if self.chains != "Y":
            del fld[6]
            del fld[4]
            for n, f in enumerate(fld):
                fld[n][0][2] = n
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "DRS")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w
        self.sttyp = acc[self.sql.tplmst_col.index("tpm_sttp")]
        if self.sttyp == "N":
            self.oitem = "Y"
            self.pages = 0
            self.df.loadEntry(frt, pag, p+1, data=self.oitem)
            self.df.loadEntry(frt, pag, p+2, data=self.pages)
            return "sk2"

    def doOItem(self, frt, pag, r, c, p, i, w):
        self.oitem = w
        if self.oitem == "N":
            self.pages = 0
            self.df.loadEntry(frt, pag, p+1, data=self.pages)
            return "sk1"

    def doPages(self, frt, pag, r, c, p, i, w):
        self.pages = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole in ("Y", "S"):
            self.schn = 0
            self.echn = 0
            self.sacc = ""
            self.eacc = ""
            if self.chains == "Y":
                self.df.loadEntry("T", 0, p+1, data=self.schn)
                self.df.loadEntry("T", 0, p+2, data=self.sacc)
                self.df.loadEntry("T", 0, p+3, data=self.echn)
                self.df.loadEntry("T", 0, p+4, data=self.eacc)
                return "sk4"
            else:
                self.df.loadEntry("T", 0, p+1, data=self.sacc)
                self.df.loadEntry("T", 0, p+2, data=self.eacc)
                return "sk2"

    def doChn(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("drschn", cols=["chm_name"],
            where=[("chm_chain", "=", w)], limit=1)
        if not chk:
            return "Invalid Chain Store"
        if c == 5:
            self.schn = w
        else:
            self.echn = w

    def doAcc(self, frt, pag, r, c, p, i, w):
        if self.chains == "Y" and c == 6:
            chk = self.schn
            self.sacc = w
        elif self.chains == "Y" and c == 8:
            chk = self.echn
            self.eacc = w
        elif c == 5:
            chk = self.schn
            self.sacc = w
        else:
            chk = self.echn
            self.eacc = w
        chk = self.sql.getRec("drsmst", cols=["drm_name"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            chk), ("drm_acno", "=", w)], limit=1)
        if not chk:
            return "Invalid Debtors Account"

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doZeros(self, frt, pag, r, c, p, i, w):
        self.zeros = w

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def doStops(self, frt, pag, r, c, p, i, w):
        self.stops = w

    def doRedu(self, frt, pag, r, c, p, i, w):
        self.redu = w
        if self.sttyp == "O":
            self.alloc = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.alloc)
            return "sk1"

    def doAlloc(self, frt, pag, r, c, p, i, w):
        self.alloc = w

    def doMessno(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "STA"), ("mss_message", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Message Number"
        self.mess = w

    def doDat(self, frt, pag, r, c, p, i, w):
        self.datew = w
        self.dated = self.df.t_disp[pag][0][p]
        self.curdt = int(w / 100)

    def doEnd(self):
        self.df.closeProcess()
        self.emadd = self.df.repeml[2]
        if not self.echn:
            self.echn = 999
        if not self.eacc:
            self.eacc = "zzzzzzz"
        whr = [("drm_cono", "=", self.opts["conum"]), ("drm_chain", ">=",
            self.schn), ("drm_acno", ">=", self.sacc), ("drm_chain", "<=",
            self.echn), ("drm_acno", "<=", self.eacc)]
        if self.stops == "N":
            whr.append(("drm_stop", "<>", "Y"))
        if self.redu == "N":
            whr.append(("drm_stat", "<>", "X"))
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "drsmst",
                ("drm_chain", "drm_acno", "drm_name"), where=whr)
        else:
            if self.sort == "N":
                odr = "drm_chain, drm_acno"
            elif self.sort == "M":
                odr = "drm_name"
            else:
                odr = "drm_pcod"
            recs = self.sql.getRec("drsmst", where=whr, order=odr)
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
        self.form.document_date(self.dated)
        self.form.bank_details(cmc, ctm, 0)

    def doProcess(self, drm):
        dmc = self.sql.drsmst_col
        dtc = self.sql.drstrn_col
        tdc = self.form.sql.tpldet_col
        self.chn = drm[dmc.index("drm_chain")]
        self.acc = drm[dmc.index("drm_acno")]
        eml = drm[dmc.index("drm_acc_email")]
        self.form.account_details("drm", dmc, drm, 1)
        if drm[dmc.index("drm_stames")]:
            self.mesno = drm[dmc.index("drm_stames")]
        else:
            self.mesno = self.mess
        for col in dmc:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = drm[dmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        bals = Balances(self.opts["mf"], "DRS", self.opts["conum"], self.curdt,
            (self.chn, self.acc))
        if self.alloc == "Y":
            tt = "A"
        else:
            tt = "Y"
        obal, self.tbal, self.ages, trns = bals.doAllBals(trans=tt)
        if not trns[1]:
            return
        if self.sttyp == "O":
            self.tots = [0.0, 0.0, 0.0]
            cmth = False
            tran = copyList(trns[1])
            for t in tran:
                if t[dtc.index("drt_type")] not in (2, 6) and \
                        t[dtc.index("drt_curdt")] == self.curdt:
                    self.tots[1] = float(ASD(self.tots[1]) + \
                        ASD(t[dtc.index("drt_tramt")]))
                    if t[dtc.index("drt_taxamt")]:
                        self.tots[1] = float(ASD(self.tots[1]) - \
                            ASD(t[dtc.index("drt_taxamt")]))
                        self.tots[2] = float(ASD(self.tots[2]) + \
                            ASD(t[dtc.index("drt_taxamt")]))
                else:
                    self.tots[0] = float(ASD(self.tots[0]) + \
                        ASD(t[dtc.index("drt_tramt")]))
                if t[dtc.index("drt_curdt")] == self.curdt:
                    cmth = True
                elif self.oitem == "N":
                    trns[1].remove(t)
            if self.zeros == "N" and not self.tbal and not cmth:
                return
            if self.minus == "N" and self.tbal < 0:
                return
            if self.oitem == "N" and obal:
                t[trns[0].index("drt_type")] = 3
                t[trns[0].index("drt_ref1")] = "O/Bal"
                t[trns[0].index("drt_batch")] = ""
                t[trns[0].index("drt_trdt")] = (self.curdt * 100) + 1
                t[trns[0].index("drt_ref2")] = ""
                t[trns[0].index("drt_tramt")] = obal
                t[trns[0].index("drt_taxamt")] = 0
                t[trns[0].index("drt_desc")] = "Opening Balance"
                t[trns[0].index("drt_taxind")] = ""
                t[trns[0].index("drt_batind")] = ""
                trns[1].insert(0, t)
            if len(trns[1]) <= self.form.maxlines:
                self.doBody(trns[0], trns[1], tdc)
            else:
                pages = int(len(trns[1]) / self.form.maxlines)
                if len(trns[1]) % self.form.maxlines:
                    pages += 1
                if pages <= self.pages:
                    self.doBody(trns[0], trns[1], tdc)
                else:
                    bal = 0
                    lines = len(trns[1]) - (self.pages * self.form.maxlines)+1
                    for _ in range(lines):
                        trn = trns[1].pop(0)
                        bal = float(ASD(bal) + ASD(trn[dtc.index("drt_tramt")]))
                    trn[trns[0].index("drt_type")] = 3
                    trn[trns[0].index("drt_ref1")] = "B/FWD"
                    trn[trns[0].index("drt_batch")] = ""
                    trn[trns[0].index("drt_ref2")] = ""
                    trn[trns[0].index("drt_tramt")] = bal
                    trn[trns[0].index("drt_taxamt")] = 0
                    trn[trns[0].index("drt_desc")] = "Balance Brought Forward"
                    trn[trns[0].index("drt_taxind")] = ""
                    trn[trns[0].index("drt_batind")] = ""
                    trns[1].insert(0, trn)
                    self.doBody(trns[0], trns[1], tdc)
        else:
            if self.zeros == "N" and not self.tbal:
                return
            if self.minus == "N" and self.tbal < 0:
                return
            self.doBody(trns[0], trns[1], tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        if self.df.repeml[1] == "Y" and not self.emadd:
            self.df.repeml[2] = eml
            self.doPrint()

    def doPrint(self):
        if self.df.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s_%s" % (self.opts["conum"], self.chn, self.acc)
        else:
            key = "%s_all_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        self.form.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header="%s Statement for %s as at %s" % (self.opts["conam"],
            self.acc, self.dated), repprt=self.df.repprt, fromad=self.fromad,
            repeml=self.df.repeml)
        if self.df.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doBody(self, dtc, drt, tdc):
        page = 0
        count = 0
        rbal = 0
        text = tdc.index("tpd_text")
        for trans in drt:
            if not count:
                page += 1
                count = self.doHeader(page)
            if count == self.form.maxlines:
                page = self.doCfwd(page)
                count = self.doHeader(page)
            for cod in self.form.body:
                if cod == "type_code":
                    c = "drt_type"
                elif cod == "line_paid":
                    c = "paid"
                elif cod == "line_balance":
                    c = "balance"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[dtc.index(c)]
                    self.form.newdic[d][text] = drtrtp[ttyp - 1][0]
                elif self.sttyp == "O" and cod == "running_balance":
                    self.form.newdic[d][text] = rbal
                else:
                    self.form.newdic[d][text] = trans[dtc.index(c)]
                    if self.sttyp == "O" and cod == "drt_tramt":
                        rbal = float(ASD(rbal) + ASD(trans[dtc.index(c)]))
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
            if nl[tdc.index("tpd_detseq")] == "drm_acno_C00":
                nl[tdc.index("tpd_text")] = self.acc
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
            if self.ageing == "N" and c != "total_balance":
                continue
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
                        where=[("mss_system", "=", "STA"), ("mss_message", "=",
                        self.mesno)], limit=1)
                    self.form.newdic[d][tdc.index("tpd_text")] = mes[0]
                self.form.doDrawDetail(self.form.newdic[d])

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
