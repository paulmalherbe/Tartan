"""
SYNOPSIS
    Bookings Statements.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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
from TartanClasses import ASD, CCD, DrawForm, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getModName, getSingleRecords, copyList
from tartanFunctions import showError
from tartanWork import bktrtp

class bk3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.doEnd()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.stpl = bkmctl["cbk_statpl"]
        self.fromad = bkmctl["cbk_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = CCD(self.sysdtw, "D1", 10).disp
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "bkmcon", "bkmmst",
            "bkmtrn", "tplmst"], prog=self.__class__.__name__)
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
                ("tpm_system", "=", "BKM")],
            "order": "tpm_tname"}
        bkm = {
            "stype": "R",
            "tables": ("bkmmst", "bkmcon"),
            "cols": (
                ("bkm_number", "", 0, "Booking"),
                ("bkc_sname", "", 0, "Surname", "Y"),
                ("bkc_names", "", 0, "Names", "F")),
            "where": (
                ("bkm_cono", "=", self.opts["conum"]),
                ("bkm_state", "<>", "X"),
                ("bkc_cono=bkm_cono",),
                ("bkc_ccode=bkm_ccode",))}
        r1s = (("Yes","Y"), ("Range","R"), ("Singles","S"))
        r2s = (("Yes","Y"), ("No","N"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.stpl,"Y",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Whole File","",
                "Y","N",self.doWhole,None,None,None),
            (("T",0,2,0),"IUI",7,"From Booking","",
                "","N",self.doAcc,bkm,None,None),
            (("T",0,3,0),"IUI",7,"To Booking","",
                "","N",self.doAcc,bkm,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Include Cancellations","",
                "Y","N",self.doCancel,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "BKM")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole in ("Y", "S"):
            self.snum = 0
            self.enum = 0
            self.df.loadEntry("T", 0, p+1, data="")
            self.df.loadEntry("T", 0, p+2, data="")
            return "sk2"

    def doAcc(self, frt, pag, r, c, p, i, w):
        if p == 2:
            self.snum = w
        else:
            self.enum = w
        chk = self.sql.getRec("bkmmst", where=[("bkm_cono", "=",
            self.opts["conum"]), ("bkm_number", "=", w)], limit=1)
        if not chk:
            return "Invalid Booking Number"
        if p == 2:
            self.df.loadEntry(frt, pag, p+1, data=self.snum)

    def doCancel(self, frt, pag, r, c, p, i, w):
        self.cancel = w

    def doEnd(self):
        if "args" in self.opts:
            self.cancel = "Y"
            self.tname = self.stpl
            self.whole = "A"
            self.snum = 0
            self.enum = 0
            if len(self.opts["args"]) == 1:
                self.repprt = ["N", "V", "view"]
                self.repeml = ["N", "N", "", "", "Y"]
            else:
                self.repprt = self.opts["args"][1]
                self.repeml = self.opts["args"][2]
        else:
            self.df.closeProcess()
            self.repprt = self.df.repprt
            self.repeml = self.df.repeml
            if not self.enum:
                self.enum = 9999999
        self.emadd = self.repeml[2]
        tab = ["bkmmst"]
        whr = [("bkm_cono", "=", self.opts["conum"])]
        if self.cancel == "N":
            whr.append(("bkm_state", "<>", "X"))
        odr = "bkm_number"
        if self.whole == "A":
            if type(self.opts["args"][0]) == int:
                whr.append(("bkm_number", "=", self.opts["args"][0]))
            else:
                whr.append(("bkm_number", "in", self.opts["args"][0]))
            recs = self.sql.getRec("bkmmst", where=whr, order=odr)
        elif self.whole == "S":
            tab.append("bkmcon")
            col = ["bkm_number", "bkc_sname", "bkc_names"]
            whr.extend([
                ("bkc_cono=bkm_cono",),
                ("bkc_ccode=bkm_ccode",)])
            dic = {}
            for c in col:
                for t in tab:
                    d = getattr(self.sql, "%s_dic" % t)
                    if c in d:
                        dic[c] = d[c]
            data = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
            data = getSingleRecords(self.opts["mf"], tab, col, dic=dic,
                where=data, ttype="D")
            recs = []
            for dat in data:
                acc = self.sql.getRec("bkmmst", where=[("bkm_cono", "=",
                    self.opts["conum"]), ("bkm_number", "=", dat[0])])
                recs.append(acc[0])
        else:
            if self.whole == "R":
                whr.extend([
                    ("bkm_number", ">=", self.snum),
                    ("bkm_number", "<=", self.enum)])
            recs = self.sql.getRec("bkmmst", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Error",
                "No Bookings Selected")
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
        self.form.document_date(self.sysdtd)
        self.form.bank_details(cmc, ctm, 0)

    def doProcess(self, bkm):
        bmc = self.sql.bkmmst_col
        ccc = self.sql.bkmcon_col
        btc = self.sql.bkmtrn_col
        tdc = self.form.sql.tpldet_col
        self.num = bkm[bmc.index("bkm_number")]
        self.cod = bkm[bmc.index("bkm_ccode")]
        con = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
            self.opts["conum"]), ("bkc_ccode", "=", self.cod)], limit=1)
        eml = con[self.sql.bkmcon_col.index("bkc_email")]
        if "contact_details" in self.form.tptp:
            dat = "%s %s %s" % (
                con[ccc.index("bkc_title")],
                con[ccc.index("bkc_names")],
                con[ccc.index("bkc_sname")])
            if bkm[bmc.index("bkm_group")]:
                dat = "%s\n%s" % (dat, bkm[bmc.index("bkm_group")][:40])
            for fld in ("addr1", "addr2", "addr3", "pcode"):
                dat = "%1s\n%s" % (dat, con[ccc.index("bkc_%s" % fld)])
            self.form.newdic["contact_details_C00"][tdc.index("tpd_text")] = dat
        for col in bmc:
            d = "%s_C00" % col
            if d in self.form.newdic:
                dat = bkm[bmc.index(col)]
                self.form.newdic[d][tdc.index("tpd_text")] = dat
        bkt = self.sql.getRec("bkmtrn", where=[("bkt_cono", "=",
            self.opts["conum"]), ("bkt_number", "=", self.num)],
            order="bkt_date, bkt_refno")
        if not bkt:
            return
        self.doBody(btc, bkt, tdc)
        self.doTotal(tdc)
        self.doTail()
        if self.repeml[1] == "Y" and not self.emadd:
            self.repeml[2] = eml
            self.doPrint()

    def doPrint(self):
        if self.repeml[1] == "Y" and not self.emadd:
            key = "%s_%s" % (self.opts["conum"], self.num)
        else:
            key = "%s_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        if self.form.saveFile(pdfnam, self.opts["mf"].window):
            head = "%s Statement at %s" % (self.opts["conam"], self.sysdtd)
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.repprt,
                fromad=self.fromad, repeml=self.repeml)
        if self.repeml[1] == "Y":
            self.form = DrawForm(self.opts["mf"].dbm, self.tname,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            self.doLoadStatic()
            self.form.doNewDetail()

    def doBody(self, btc, bkt, tdc):
        page = 0
        count = 0
        self.tbal = 0
        for trans in bkt:
            if not count:
                page += 1
                count = self.doHeader(page)
            if count == self.form.maxlines:
                page = self.doCfwd(page)
                count = self.doHeader(page)
            ldic = {}
            for cod in self.form.body:
                if cod in ("type_code", "line_paid", "line_balance"):
                    continue
                if cod == "bkt_desc":
                    des = self.form.doSplitText("bkt_desc_C00",
                        trans[btc.index(cod)])
                    if len(des) > 1 and not des[-1]:
                        del des[-1]
                else:
                    ldic[cod] = CCD(trans[btc.index(cod)],
                        self.form.tptp[cod][0][1], self.form.tptp[cod][0][2])
            ldic["line_paid"] = 0
            ldic["line_balance"] = ldic["bkt_tramt"].work
            self.tbal = float(ASD(self.tbal) + ASD(ldic["bkt_tramt"].work))
            for n, l in enumerate(des):
                if count == self.form.maxlines:
                    page = self.doCfwd(page)
                    count = self.doHeader(page)
                if n == 0 and len(des) == 1:
                    include = copyList(self.form.body)
                elif n == 0:
                    include = ("bkt_date", "bkt_refno", "type_code")
                elif n + 1 == len(des):
                    include = copyList(self.form.body)
                    include.remove("bkt_date")
                    include.remove("bkt_refno")
                    include.remove("type_code")
                else:
                    include = []
                for code in self.form.body:
                    seq = "%s_C%02i" % (code, count)
                    if code == "bkt_desc":
                        data = l
                    elif code in include:
                        if code == "type_code":
                            data = bktrtp[trans[btc.index("bkt_type")] - 1][0]
                        else:
                            data = ldic[code].work
                    else:
                        data = "BLANK"
                    self.form.newdic[seq][tdc.index("tpd_text")] = data
                    self.form.doDrawDetail(self.form.newdic[seq])
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
            if nl[tdc.index("tpd_detseq")] == "bkm_number_C00":
                nl[tdc.index("tpd_text")] = self.num
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
            if c != "total_balance":
                continue
            t = "%s_T00" % c
            if c in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[c])
            elif t in self.form.newdic:
                self.form.doDrawDetail(self.form.newdic[t])
            d = "%s_C00" % c
            if d in self.form.newdic:
                line = self.form.newdic[d]
                line[tdc.index("tpd_text")] = self.tbal
                self.form.doDrawDetail(line)

    def doTail(self):
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
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
