"""
SYNOPSIS
    Rental Tenants Statements.

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
from TartanClasses import ASD, DrawForm, GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import copyList, doPrinter,  getModName, getSingleRecords
from tartanFunctions import showError
from tartanWork import rttrtp

class rt3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmes", "ctlmst", "rtlmst",
            "rtltrn", "rtlprm", "rtlcon", "tplmst"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        self.stpl = rtlctl["ctr_tplnam"]
        self.fromad = rtlctl["ctr_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.trtypes = []
        for t in rttrtp:
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
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details")),
            "where": [("mss_system", "=", "RTL")]}
        r1s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.stpl,"Y",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Whole File","",
                "Y","Y",self.doWhole,None,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Zero Balances",
                "Include Zero Balances","N","Y",self.doZeros,None,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Minus Balances",
                "Include Minus Balances","N","Y",self.doMinus,None,None,None),
            (("T",0,4,0),"IUI",3,"Message Number","",
                "","Y",self.doMessno,mss,None,("efld",)),
            (("T",0,5,0),"ID1",10,"Statement Date","",
                self.sysdtw,"Y",self.doDat,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "RTL")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doZeros(self, frt, pag, r, c, p, i, w):
        self.zeros = w

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def doMessno(self, frt, pag, r, c, p, i, w):
        if w:
            self.mes = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "RTL"), ("mss_message", "=", w)],
                limit=1)
            if not self.mes:
                return "Invalid Message Number"
        self.mesno = w

    def doDat(self, frt, pag, r, c, p, i, w):
        self.datew = w
        self.dated = self.df.t_disp[pag][0][p]
        self.curdt = int(w / 100)

    def doEnd(self):
        self.df.closeProcess()
        self.emadd = self.df.repeml[2]
        if self.whole == "N":
            recs = getSingleRecords(self.opts["mf"], "rtlmst", ("rtm_code",
                "rtm_acno", "rtm_name"), where=[("rtm_cono", "=",
                self.opts["conum"])])
        else:
            whr = [("rtm_cono", "=", self.opts["conum"])]
            odr = "rtm_code, rtm_acno"
            recs = self.sql.getRec("rtlmst", where=whr, order=odr)
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
                    break
                self.doProcess(rec)
            p.closeProgress()
            if p.quit or not self.form.page:
                pass
            elif self.df.repeml[1] == "N" or not self.emadd:
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

    def doProcess(self, rtm):
        rmc = self.sql.rtlmst_col
        rtc = copyList(self.sql.rtltrn_col)
        tdc = self.form.sql.tpldet_col
        self.code = rtm[rmc.index("rtm_code")]
        self.acno = rtm[rmc.index("rtm_acno")]
        eml = rtm[rmc.index("rtm_email")]
        for col in rmc:
            d = "%s_00" % col
            if d in self.form.newdic:
                dat = rtm[rmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        prm = self.sql.getRec("rtlprm", where=[("rtp_cono", "=",
            self.opts["conum"]), ("rtp_code", "=", self.code)], limit=1)
        if not prm:
            prm = [0, "", "", "", "", "", "", 0, 0]
        prc = self.sql.rtlprm_col
        for col in prc:
            d = "%s_00" % col
            if col in self.form.newdic:
                dat = prm[prc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.opts["conum"]), ("rtc_code", "=", self.code), ("rtc_acno",
            "=", self.acno)], limit=1)
        coc = self.sql.rtlprm_col
        for col in coc:
            d = "%s_00" % col
            if col in self.form.newdic:
                dat = con[coc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        self.tots = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        rtt = self.sql.getRec("rtltrn",
            cols=["round(sum(rtt_tramt), 2)", "round(sum(rtt_taxamt), 2)"],
            where=[("rtt_cono", "=", self.opts["conum"]), ("rtt_code", "=",
            self.code), ("rtt_acno", "=", self.acno), ("rtt_trdt", "<=",
            self.datew), ("rtt_curdt", "=", self.curdt)], limit=1)
        if rtt[0]:
            self.tots[0] = rtt[0]
            self.tots[2] = rtt[0]
            self.tots[5] = rtt[0]
        if rtt[1]:
            self.tots[0] = float(ASD(self.tots[0]) - ASD(rtt[1]))
            self.tots[1] = rtt[1]
        arr = self.sql.getRec("rtltrn",
            cols=["round(sum(rtt_tramt), 2)"], where=[("rtt_cono", "=",
            self.opts["conum"]), ("rtt_code", "=", self.code), ("rtt_acno",
            "=", self.acno), ("rtt_curdt", "<", self.curdt)], limit=1)
        if arr[0]:
            self.tots[3] = arr[0]
            self.tots[5] = float(ASD(self.tots[5]) + ASD(arr[0]))
        if self.zeros == "N" and not self.tots[5]:
            return
        if self.minus == "N" and self.tots[5] < 0:
            return
        rtc = ["rtt_trdt", "rtt_refno", "rtt_type", "rtt_desc", "rtt_cnum",
            "rtt_tramt"]
        rtt = self.sql.getRec("rtltrn", cols=["rtt_trdt", "rtt_refno",
            "rtt_type", "rtt_desc", "rtt_cnum", "round(sum(rtt_tramt), 2)"],
            where=[("rtt_cono", "=", self.opts["conum"]), ("rtt_code", "=",
            self.code), ("rtt_acno", "=", self.acno), ("rtt_type", "<>", 5),
            ("rtt_trdt", "<=", self.datew)],
            group="rtt_trdt, rtt_refno, rtt_type, rtt_desc, rtt_cnum",
            order="rtt_trdt, rtt_cnum, rtt_refno")
        if not rtt:
            rtt = []
        trans = []
        for trn in rtt:
            tramt = trn[rtc.index("rtt_tramt")]
            if tramt < 0:
                trn.extend([0, tramt])
            else:
                trn.extend([tramt, 0])
            trans.append(trn)
        rtc.extend(["line_debit", "line_credit"])
        self.doHeader(rtm, rmc, prm, prc, tdc)
        if len(trans) <= self.form.maxlines:
            self.doBody(rtc, trans, tdc)
        else:
            bal = 0
            lines = len(trans) - self.form.maxlines + 1
            for _ in range(lines):
                trn = trans.pop(0)
                bal = float(ASD(bal) + ASD(trn[5]))
            trn[rtc.index("rtt_refno")] = "B/FWD"
            trn[rtc.index("rtt_type")] = 3
            trn[rtc.index("rtt_desc")] = "Balance Brought Forward"
            trn[rtc.index("rtt_tramt")] = bal
            if bal < 0:
                trn[rtc.index("line_debit")] = 0
                trn[rtc.index("line_credit")] = bal
            else:
                trn[rtc.index("line_debit")] = bal
                trn[rtc.index("line_credit")] = 0
            trans.insert(0, trn)
            self.doBody(rtc, trans, tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        if self.df.repeml[1] == "Y" and not self.emadd:
            self.df.repeml[2] = eml
            self.doPrint()

    def doHeader(self, rtm, rmc, prm, prc, tdc):
        self.form.add_page()
        if "account_details" in self.form.tptp:
            nad = rtm[rmc.index("rtm_name")]
            add1 = rtm[rmc.index("rtm_addr1")]
            if add1:
                nad = "%1s\n%1s" % (nad, add1)
                nad = "%1s\n%1s" % (nad, rtm[rmc.index("rtm_addr2")])
                nad = "%1s\n%1s" % (nad, rtm[rmc.index("rtm_addr3")])
                nad = "%1s\n%1s" % (nad, rtm[rmc.index("rtm_pcode")])
            else:
                nad = prm[prc.index("rtp_addr1")]
                nad = "%1s\n%1s" % (nad, prm[prc.index("rtp_addr2")])
                nad = "%1s\n%1s" % (nad, prm[prc.index("rtp_addr3")])
                nad = "%1s\n%1s" % (nad, prm[prc.index("rtp_pcode")])
            self.form.newdic["account_details_C00"][
                tdc.index("tpd_text")] = nad
        for key in self.form.newkey:
            nl = copyList(self.form.newdic[key])
            if nl[tdc.index("tpd_place")] != "A":
                continue
            if nl[tdc.index("tpd_detseq")] == "rtm_code_C00":
                nl[tdc.index("tpd_text")] = self.code
            elif nl[tdc.index("tpd_detseq")] == "rtm_acno_C00":
                nl[tdc.index("tpd_text")] = self.acno
            self.form.doDrawDetail(nl)

    def doBody(self, rtc, rtt, tdc):
        text = self.form.sql.tpldet_col.index("tpd_text")
        count = 0
        bal = 0
        for trans in rtt:
            for cod in self.form.body:
                if cod == "type_code":
                    c = "rtt_type"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[rtc.index(c)]
                    self.form.newdic[d][text] = rttrtp[ttyp - 1][0]
                elif cod in ("line_debit", "line_credit"):
                    tramt = trans[rtc.index(c)]
                    bal = float(ASD(bal) + ASD(tramt))
                    self.form.newdic[d][text] = trans[rtc.index(c)]
                elif c == "line_balance":
                    self.form.newdic[d][text] = bal
                else:
                    self.form.newdic[d][text] = trans[rtc.index(c)]
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
                if c == "period_rental":
                    line[tdc.index("tpd_text")] = self.tots[0]
                elif c == "period_vat":
                    line[tdc.index("tpd_text")] = self.tots[1]
                elif c == "total_rental":
                    line[tdc.index("tpd_text")] = self.tots[2]
                elif c == "total_arrears":
                    line[tdc.index("tpd_text")] = self.tots[3]
                elif c == "interest":
                    line[tdc.index("tpd_text")] = self.tots[4]
                elif c == "total_balance":
                    line[tdc.index("tpd_text")] = self.tots[5]
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

    def doPrint(self):
        if self.df.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s_%s" % (self.opts["conum"], self.code, self.acno)
        else:
            key = "%s_all_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        self.form.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header="%s Statement at %s" % (self.opts["conam"], self.dated),
            fromad=self.fromad, repprt=self.df.repprt, repeml=self.df.repeml)
        if self.df.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
