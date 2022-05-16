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
from tartanFunctions import doPrinter, getModName, getSingleRecords, copyList
from tartanFunctions import showError
from tartanWork import rcmvtp, rctrtp

class rc3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.own, self.prm, self.acc, self.datew, self.dated, \
                    self.repprt, self.repeml = self.opts["args"]
                self.emadd = self.repeml[2]
                self.tname = self.stpl
                self.zeros = "Y"
                self.minus = "Y"
                self.mesno = 0
                whr = [
                    ("rtn_cono", "=", self.opts["conum"]),
                    ("rtn_owner", "=", self.own),
                    ("rtn_code", "=", self.prm),
                    ("rtn_acno", "=", self.acc)]
                rtn = self.sql.getRec("rcatnm", where=whr, limit=1)
                self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                    wrkdir=self.opts["mf"].rcdic["wrkdir"])
                self.doLoadStatic()
                self.form.doNewDetail()
                self.doProcess(rtn)
                if self.form.page and (self.repeml[1] == "N" or self.emadd):
                    self.repeml[2] = self.emadd
                    self.doPrint()
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlpwu", "ctlmes", "ctlmst",
            "rcatnm", "rcatnt", "rcaprm", "rcacon", "tplmst"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.stpl = rcactl["cte_tpltnt"]
        usr = self.sql.getRec("ctlpwu", cols=["usr_emadd"], where=[("usr_name",
            "=", self.opts["capnm"])], limit=1)
        if usr[0]:
            self.fromad = usr[0]
        else:
            self.fromad = rcactl["cte_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
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
                ("tpm_system", "=", "RCA"),
                ("tpm_sttp", "=", "T")],
            "order": "tpm_tname"}
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details")),
            "where": [("mss_system", "=", "RCA")]}
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
            ("tpm_type", "=", "S"), ("tpm_system", "=", "RCA"), ("tpm_sttp",
            "=", "T")], limit=1)
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
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "RCA"), ("mss_message", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Message Number"
        self.mesno = w

    def doDat(self, frt, pag, r, c, p, i, w):
        self.datew = w
        self.dated = self.df.t_disp[pag][0][p]

    def doEnd(self):
        self.df.closeProcess()
        self.repprt = self.df.repprt
        self.repeml = self.df.repeml
        self.emadd = self.df.repeml[2]
        if self.whole == "N":
            recs = getSingleRecords(self.opts["mf"], "rcatnm",
                ("rtn_owner", "rtn_code", "rtn_acno", "rtn_name"),
                where=[("rtn_cono", "=", self.opts["conum"])])
        else:
            whr = [("rtn_cono", "=", self.opts["conum"])]
            odr = "rtn_owner, rtn_code, rtn_acno"
            recs = self.sql.getRec("rcatnm", where=whr, order=odr)
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
            elif self.repeml[1] == "N" or self.emadd:
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

    def doProcess(self, rtn):
        tmc = self.sql.rcatnm_col
        tdc = self.form.sql.tpldet_col
        self.own = rtn[tmc.index("rtn_owner")]
        self.prm = rtn[tmc.index("rtn_code")]
        self.acc = rtn[tmc.index("rtn_acno")]
        eml = rtn[tmc.index("rtn_email")]
        acc = self.sql.getRec("rcacon", cols=["rcc_cnum", "rcc_deposit",
            "rcc_status"], where=[("rcc_cono", "=", self.opts["conum"]),
            ("rcc_owner", "=", self.own), ("rcc_code", "=", self.prm),
            ("rcc_acno", "=", self.acc)], order="rcc_cnum")
        if acc:
            dps, dep, sta = acc[-1:][0]
        else:
            dps, dep, sta = 0, 0.0, ""
        if sta != "C":
            dep = 0.0
            dos = 0.0
        else:
            dos = dep
        self.tots = [0.0, dep, 0.0, 0.0, 0.0, dep]
        tots = self.sql.getRec("rcatnt", cols=["rtu_type", "rtu_mtyp",
            "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
            self.opts["conum"]), ("rtu_owner", "=", self.own), ("rtu_code",
            "=", self.prm), ("rtu_acno", "=", self.acc), ("rtu_trdt", "<=",
            self.datew)], group="rtu_type, rtu_mtyp")
        self.dpp = 0.0
        for t in tots:
            if t[1] == 1:
                self.tots[0] = float(ASD(self.tots[0]) + ASD(t[2]))
                self.tots[5] = float(ASD(self.tots[5]) + ASD(t[2]))
            elif t[1] == 2:
                self.dpp = float(ASD(self.dpp) + ASD(t[2]))
                if dep:
                    dos = float(ASD(dos) + ASD(t[2]))
                    self.tots[1] = float(ASD(self.tots[1]) + ASD(t[2]))
                    self.tots[5] = float(ASD(self.tots[5]) + ASD(t[2]))
            elif t[1] == 3:
                self.tots[2] = float(ASD(self.tots[2]) + ASD(t[2]))
                self.tots[5] = float(ASD(self.tots[5]) + ASD(t[2]))
            elif t[1] in (4, 5):
                self.tots[3] = float(ASD(self.tots[3]) + ASD(t[2]))
                self.tots[5] = float(ASD(self.tots[5]) + ASD(t[2]))
            else:
                self.tots[4] = float(ASD(self.tots[4]) + ASD(t[2]))
                self.tots[5] = float(ASD(self.tots[5]) + ASD(t[2]))
        if not dos and not tots:
            return
        if self.zeros == "N" and not dos and not self.tots[5]:
            return
        if self.minus == "N" and not dos and self.tots[5] < 0:
            return
        prc = self.sql.rcaprm_col
        prm = self.sql.getRec("rcaprm", where=[("rcp_cono", "=",
            self.opts["conum"]), ("rcp_owner", "=", self.own), ("rcp_code",
            "=", self.prm)], limit=1)
        ttc = ["rtu_trdt", "rtu_refno", "rtu_type", "rtu_desc", "rtu_cnum",
            "rtu_mtyp", "balance"]
        rtt = self.sql.getRec("rcatnt", cols=["rtu_trdt",
            "rtu_refno", "rtu_type", "rtu_desc", "rtu_cnum", "rtu_mtyp",
            "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
            self.opts["conum"]), ("rtu_owner", "=", self.own), ("rtu_code",
            "=", self.prm), ("rtu_acno", "=", self.acc), ("rtu_type", "<>", 5),
            ("rtu_trdt", "<=", self.datew)], group="rtu_trdt, rtu_refno, "\
            "rtu_type, rtu_desc, rtu_cnum, rtu_mtyp", order="rtu_trdt, "\
            "rtu_cnum, rtu_refno")
        if not rtt:
            rtt = []
        if dos > 0:
            rtt.append([self.datew, "Deposit", 4, "Outstanding Deposit", dps,
                2, dos])
        elif dos < 0:
            rtt.append([self.datew, "Deposit", 4, "Overpaid Deposit", dps,
                2, dos])
        nad = rtn[tmc.index("rtn_name")]
        if rtn[tmc.index("rtn_addr1")]:
            nad = "%s\n%s" % (nad, rtn[tmc.index("rtn_addr1")])
            if rtn[tmc.index("rtn_addr2")]:
                nad = "%s\n%s" % (nad, rtn[tmc.index("rtn_addr2")])
            if rtn[tmc.index("rtn_addr3")]:
                nad = "%s\n%s" % (nad, rtn[tmc.index("rtn_addr3")])
            if rtn[tmc.index("rtn_pcode")]:
                nad = "%s\n%s" % (nad, rtn[tmc.index("rtn_pcode")])
        elif prm[prc.index("rcp_addr1")]:
            nad = "%s\n%s" % (nad, prm[prc.index("rcp_addr1")])
            if prm[prc.index("rcp_addr2")]:
                nad = "%s\n%s" % (nad, prm[prc.index("rcp_addr2")])
            if prm[prc.index("rcp_addr3")]:
                nad = "%s\n%s" % (nad, prm[prc.index("rcp_addr3")])
            if prm[prc.index("rcp_pcode")]:
                nad = "%s\n%s" % (nad, prm[prc.index("rcp_pcode")])
        else:
            nad = "%s\n\n\n\n" % nad
        self.form.newdic["account_details_C00"][tdc.index("tpd_text")] = nad
        for col in tmc:
            d = "%s_C00" % col
            if d in self.form.newkey:
                dat = rtn[tmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        for col in prc:
            d = "%s_C00" % col
            if d in self.form.newkey:
                dat = prm[prc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        if len(rtt) <= self.form.maxlines:
            self.doBody(ttc, rtt, tdc)
        else:
            bal = 0
            lines = len(rtt) - self.form.maxlines + 1
            for _ in range(lines):
                trn = rtt.pop(0)
                if trn[ttc.index("rtu_mtyp")] == 2:
                    continue
                bal = float(ASD(bal) + ASD(trn[ttc.index("balance")]))
            trn[ttc.index("rtu_refno")] = "B/FWD"
            trn[ttc.index("rtu_type")] = 4
            trn[ttc.index("rtu_desc")] = "Balance Brought Forward"
            trn[ttc.index("balance")] = bal
            rtt.insert(0, trn)
            self.doBody(ttc, rtt, tdc)
        self.doTotal(tdc)
        self.doTail(tdc)
        if self.repeml[1] == "Y" and not self.emadd:
            self.repeml[2] = eml
            self.doPrint()

    def doPrint(self):
        if self.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s_%s_%s" % (self.opts["conum"], self.own, self.prm,
                self.acc)
        else:
            key = "%s_all_all_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        self.form.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header="%s Statement at %s" % (self.opts["conam"], self.dated),
            fromad=self.fromad, repprt=self.repprt, repeml=self.repeml)
        if self.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doBody(self, ttc, rtt, tdc):
        page = 0
        count = 0
        rbal = 0
        text = tdc.index("tpd_text")
        for trans in rtt:
            if not count:
                page += 1
                count = self.doHeader(page)
            if count == self.form.maxlines:
                page = self.doCfwd(page)
                count = self.doHeader(page)
            for cod in self.form.body:
                if cod == "type_code":
                    c = "rtu_type"
                elif cod == "mvtype_code":
                    c = "rtu_mtyp"
                elif cod == "line_paid":
                    c = "paid"
                elif cod == "line_balance":
                    c = "balance"
                else:
                    c = cod
                d = "%s_C%02i" % (cod, count)
                if cod == "type_code":
                    ttyp = trans[ttc.index(c)]
                    self.form.newdic[d][text] = rctrtp[ttyp - 1][0]
                elif cod == "mvtype_code":
                    ttyp = trans[ttc.index(c)]
                    self.form.newdic[d][text] = rcmvtp[ttyp - 1][0]
                elif cod == "running_balance":
                    self.form.newdic[d][text] = rbal
                else:
                    self.form.newdic[d][text] = trans[ttc.index(c)]
                    if cod == "line_balance":
                        mtp = trans[ttc.index("rtu_mtyp")]
                        if trans[ttc.index("rtu_desc")]:
                            dsc = trans[ttc.index("rtu_desc")].split()[0]
                        else:
                            dsc = ""
                        if mtp == 2 and dsc not in ("Outstanding", "Overpaid"):
                            pass
                        else:
                            rbal = float(ASD(rbal) + ASD(trans[ttc.index(c)]))
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
            if nl[tdc.index("tpd_detseq")] == "rtn_acno_C00":
                nl[tdc.index("tpd_text")] = self.acc
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
                if c == "total_rental":
                    line[tdc.index("tpd_text")] = self.tots[0]
                elif c == "total_receipts":
                    line[tdc.index("tpd_text")] = self.tots[1]
                elif c == "total_payments":
                    line[tdc.index("tpd_text")] = self.tots[2]
                elif c == "total_journals":
                    line[tdc.index("tpd_text")] = self.tots[3]
                elif c == "total_deposit":
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
                if c == "deposit":
                    dep = float(ASD(0) - ASD(self.dpp))
                    self.form.newdic[d][tdc.index("tpd_text")] = dep
                elif d == "message_C00" and self.mesno:
                    mes = self.sql.getRec("ctlmes", cols=["mss_detail"],
                        where=[("mss_system", "=", "STA"), ("mss_message", "=",
                        self.mesno)], limit=1)
                    self.form.newdic[d][tdc.index("tpd_text")] = mes[0]
                self.form.doDrawDetail(self.form.newdic[d])

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
