"""
SYNOPSIS
    Members Ledger Month End Routine.

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
from TartanClasses import ASD, CCD, GetCtl, ProgressBar, PwdConfirm, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askQuestion, callModule, dateDiff, doChkCatChg
from tartanFunctions import getVatRate, mthendDate, projectDate, showError

class mlm010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        mc = GetCtl(self.opts["mf"])
        ctlmst = mc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        memctl = mc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.glint = memctl["mcm_glint"]
        self.ldays = memctl["mcm_ldays"]
        self.lme = memctl["mcm_lme"]
        self.lmd = int(memctl["mcm_lme"] / 100)
        yr = int(self.lme / 10000)
        mth = (int(self.lme / 100) % 100) + 1
        if mth > 12:
            yr += 1
            mth = 1
        self.tme = mthendDate((yr * 10000) + (mth * 100) + 00)
        tabs = ["chglog", "ctlbat", "ctlmst", "ctlvrf", "ctlvtf", "memage",
            "memcat", "memctc", "memctl", "memctp", "memmst", "memtrn"]
        if self.glint == "Y":
            tabs.append("gentrn")
            ctlctl = mc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["mem_ctl", "mem_pen", "vat_ctl"]
            if mc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.memctl = ctlctl["mem_ctl"]
            self.penctl = ctlctl["mem_pen"]
            self.vatctl = ctlctl["vat_ctl"]
        else:
            self.penctl = 0
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        if self.glint == "Y":
            check = self.sql.getRec("memctc", where=[("mcc_cono", "=",
                self.opts["conum"]), ("mcc_freq", "<>", "N"), ("mcc_glac", "=",
                0)])
            if check:
                mess = "The following Category Record(s) are Missing G/L "\
                    "Accounts:\n"
                for rec in check:
                    mess = "%s\n%s, %2s, %s" % (mess, rec[1], rec[2], rec[3])
                showError(self.opts["mf"].body, "Invalid Category", mess)
                return
        t = time.localtime()
        self.sysdt = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.ynd = False
        return True

    def mainProcess(self):
        r1s = (("No", "N"), ("Yes", "Y"))
        fld = (
            (("T",0,0,0),"OD1",10,"Last Month End Date"),
            (("T",0,1,0),"ID1",10,"This Month End Date","",
                self.tme,"N",self.doTme,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Raise Penalties","",
                "N","N",self.doPenalty,None,None,None),
            (("T",0,3,0),"ID1",10,"Cut-off Date","",
                "","N",self.doCutOff,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, focus=False)
        self.df.loadEntry("T", 0, 0, data=self.lme)
        self.df.focusField("T", 0, 2)

    def doTme(self, frt, pag, r, c, p, i, w):
        if w <= self.lme:
            return "Invalid Month-End Date, Before Last Month End"
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Month-End Date, Out of Financial Period"

        if int(w / 100) == int(self.opts["period"][2][0] / 100):
            ok = askQuestion(self.opts["mf"].body, "Year End",
                "Is this the Financial Year End?", default="yes")
            if ok == "yes":
                self.ynd = True
                w = self.opts["period"][2][0]
                self.df.loadEntry(frt, pag, p, data=w)
            else:
                return "Invalid Month-End Date, Same as Year-End"
        if dateDiff(self.lme, w, "months") != 1:
            return "There Seems to be a Missing Month End"
        self.tme = w
        self.curdt = int(w / 100)
        yy = int(self.curdt / 100)
        mm = (self.curdt % 100) + 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nxtdt = (yy * 10000) + (mm * 100) + 1
        self.nxtcd = int(self.nxtdt / 100)
        self.batch = "M%06s" % self.curdt
        chk = self.sql.getRec("memtrn", cols=["count(*)"],
            where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_type", "=", 1),
            ("mlt_batch", "=", self.batch), ("mlt_trdt", "=", self.nxtdt),
            ("mlt_curdt", "=", self.nxtcd)], limit=1)
        if chk[0]:
            return "Month-End Already Executed"
        num = self.sql.getRec("memtrn", cols=["max(mlt_refno)"],
            where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_type", "=", 1),
            ("mlt_refno", "like", "A________")], limit=1)
        if not num[0]:
            self.refnum = 0
        else:
            self.refnum = int(num[0][4:])

    def doPenalty(self, frt, pag, r, c, p, i, w):
        self.penalty = w
        if self.penalty == "N":
            return "sk1"

    def doCutOff(self, frt, pag, r, c, p, i, w):
        if w >= self.tme:
            return "Invalid Cut-off Date"
        self.cutoff = w
        self.pcodes = {}
        acc = self.sql.getRec("memctp", cols=["mcp_type", "mcp_code",
            "mcp_penalty"], where=[("mcp_cono", "=", self.opts["conum"]),
            ("mcp_date", "<=", self.cutoff), ("mcp_penalty", "<>", 0)],
            order="mcp_date")
        for a in acc:
            self.pcodes["%s%02i" % (a[0], a[1])] = a[2]

    def doEnd(self):
        recs = self.sql.getRec("ctlbat", cols=["count(*)"],
            where=[("btm_cono", "=", self.opts["conum"]), ("btm_styp", "=",
            "MEM"), ("btm_ind", "=", "N"), ("btm_curdt", "=", self.curdt)],
            limit=1)
        if recs[0]:
            ok = askQuestion(self.opts["mf"].body, "Unbalanced Batches Exist",
                "There are Unbalanced Batches for this Month. You "\
                "Should Not Continue, but Print a Batch Error Report, and "\
                "Correct the Errors. Continue, YES or NO ?", default="no")
            if ok == "yes":
                ok = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                    system="MST", code="UnbalBatch")
                if ok.flag == "no":
                    self.closeProcess()
                else:
                    self.doEnder()
            else:
                self.closeProcess()
        else:
            self.doEnder()

    def doEnder(self):
        self.df.closeProcess()
        recs = self.sql.getRec("memmst", cols=["mlm_memno"],
            where=[("mlm_cono", "=", self.opts["conum"]), ("mlm_state", "=",
            "A")])
        if self.ynd:
            p = ProgressBar(self.opts["mf"].body,
                typ="Checking Member Categories", mxs=len(recs))
            for num, acc in enumerate(recs):
                p.displayProgress(num)
                self.memno = acc[0]
                data = doChkCatChg(self.opts["mf"], self.opts["conum"],
                    self.memno, self.nxtdt)
                if data:
                    if not data[3]:
                        self.doRaiseCharge("B", data[0], data[1], data[2],
                            data[3], data[4], data[5], data[6], skip=True)
                    dte = int("%04i%02i%02i%02i%02i%02i" % \
                        time.localtime()[:-3])
                    self.sql.delRec("memcat", where=[("mlc_cono", "=",
                        self.opts["conum"]), ("mlc_memno", "=", self.memno),
                        ("mlc_type", "=", "B"), ("mlc_code", "=", data[0])])
                    self.sql.insRec("chglog", data=["memcat", "D",
                        "%03i%06i%1s%02i" % (self.opts["conum"], self.memno,
                        "B", data[0]), "", dte, self.opts["capnm"],
                        str(data[1]), str(data[2]), "", 0])
                    self.sql.insRec("memcat", data=[self.opts["conum"],
                        self.memno, "B", data[7], "", self.nxtdt, 0, 0])
                    self.sql.insRec("chglog", data=["memcat", "N",
                        "%03i%06i%1s%02i" % (self.opts["conum"], self.memno,
                        "B", data[7]), "", dte, self.opts["capnm"],
                        str(self.nxtdt), str(0), "", 0])
            p.closeProgress()
            ok = askQuestion(self.opts["mf"].body, "Category Changes",
                "Would You Like to Display Category Changes?", default="yes")
            if ok == "yes":
                callModule(self.opts["mf"], None, "ml3060",
                    coy=(self.opts["conum"], self.opts["conam"]),
                    args=(projectDate(self.lme, 1), self.nxtdt))
                ok = askQuestion(self.opts["mf"].body, "Continue",
                    "Would You Like to Continue with the Month End?",
                    default="yes")
                if ok == "no":
                    self.opts["mf"].closeLoop()
                    return
        p = ProgressBar(self.opts["mf"].body, typ="F", mxs=len(recs))
        for num, acc in enumerate(recs):
            p.displayProgress(num)
            self.memno = acc[0]
            if self.penalty == "Y":
                amount = 0
                join = "left outer join memage on mta_cono=mlt_cono and "\
                    "mta_memno=mlt_memno and mta_type=mlt_type and "\
                    "mta_refno=mlt_refno"
                cols = ["mlt_ctyp", "mlt_ccod", "sum(mlt_tramt)"]
                wher = [("mlt_cono", "=", self.opts["conum"]), ("mlt_memno",
                    "=", self.memno), ("mlt_trdt", "<=", self.cutoff)]
                grps = "mlt_ctyp, mlt_ccod"
                ordr = "mlt_trdt"
                recs = self.sql.getRec("memtrn", join=join, cols=cols,
                    where=wher, group=grps, order=ordr)
                for rec in recs:
                    key = "%s%02i" % (rec[0], rec[1])
                    if key in self.pcodes:
                        amt = round(rec[2] * self.pcodes[key] / 100.0, 2)
                        if amt > 0:
                            amount = float(ASD(amount) + ASD(amt))
                if amount:
                    self.doUpdateTables("", "", "Penalty on Overdue Amounts",
                        self.penctl, self.tme, amount)
            cols = ["mlc_type", "mlc_code", "mcc_desc", "mcc_freq",
                "mlc_start", "mlc_end", "mlc_last", "mcc_glac"]
            wher = [
                ("mlc_cono", "=", self.opts["conum"]),
                ("mlc_memno", "=", self.memno),
                ("mlc_start", ">", 0),
                ("mlc_start", "<=", self.nxtdt),
                ("mcc_cono=mlc_cono",),
                ("mcc_type=mlc_type",),
                ("mcc_code=mlc_code",),
                ("mcc_freq", "<>", "N")]
            cats = self.sql.getRec(tables=["memcat", "memctc"], cols=cols,
                where=wher, order="mlc_type, mlc_code")
            for ctyp, code, desc, freq, start, end, last, glac in cats:
                if start > self.nxtdt:
                    # Not yet Started
                    continue
                if last and end and end < self.nxtdt:
                    # Ended
                    continue
                if last and freq == "O":
                    # Once Off
                    continue
                if not self.ynd and last and freq == "A" and \
                        last >= self.opts["period"][1][0] and \
                        last <= self.opts["period"][2][0]:
                    # Out of Period
                    continue
                self.doRaiseCharge(ctyp, code, start, end, last, freq,
                    desc, glac)
        p.closeProgress()
        self.sql.updRec("memctl", cols=["mcm_lme"], data=[self.tme],
            where=[("mcm_cono", "=", self.opts["conum"])])
        ok = askQuestion(self.opts["mf"].body, "Audit Trail",
            "Would You Like to Display an Audit Trail?", default="yes")
        if ok == "yes":
            callModule(self.opts["mf"], None, "ml3020",
                coy=(self.opts["conum"], self.opts["conam"]),
                args=("F", 0, self.nxtcd, 1, self.batch))
        self.opts["mf"].dbm.commitDbase(ask=True,
            mess="Do You Want To Save All Entries?\n\nPlease Note That "\
            "Once The Entries Have Been Saved, There Is No Going Back "\
            "Without Restoring From Backup!")
        if self.ynd and self.opts["mf"].dbm.commit == "yes":
            callModule(self.opts["mf"], None, "msy010", coy=(self.opts["conum"],
                self.opts["conam"]), period=self.opts["period"],
                user=self.opts["capnm"], args="N")
        self.opts["mf"].closeLoop()

    def doRaiseCharge(self, ctyp, code, start, end, last, freq, desc, glac, skip=False):
        if freq == "O":
            dte = True
            nxt = False
        else:
            dte = False
            nxt = bool(self.ynd or freq == "M")
            if not last:
                if dateDiff(start, self.tme, "days") > self.ldays:
                    dte = True
                else:
                    nxt = True
        if dte:
            trdt = start
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(ctyp, code, desc, glac, trdt, amt)
        if not skip and nxt:
            if end and self.nxtdt > end:
                return
            trdt = self.nxtdt
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(ctyp, code, desc, glac, trdt, amt)

    def doGetCharge(self, ctyp, code, date):
        prc = self.sql.getRec("memctp", where=[("mcp_cono", "=",
            self.opts["conum"]), ("mcp_type", "=", ctyp), ("mcp_code", "=",
            code), ("mcp_date", "<=", date)], order="mcp_date desc", limit=1)
        if not prc:
            # No Price
            return
        if prc[5] == "N" or (self.ynd and date == self.nxtdt):
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

    def doUpdateTables(self, ctyp, code, desc, glac, trdt, amt):
        self.refnum += 1
        ref = CCD("A%08i" % self.refnum, "Na", 9).work
        curdt = int(trdt / 100)
        # VAT Rate and Amount
        vrte = getVatRate(self.sql, self.opts["conum"], self.taxdf, trdt)
        if vrte is None:
            vrte = 0.0
        vat = CCD(round(((amt * vrte) / (vrte + 100)), 2), "UD", 12.2).work
        # Members Ledger Transaction (memtrn)
        data = [self.opts["conum"], self.memno, 1, ref, self.batch, trdt, amt,
            vat, curdt, ctyp, code, desc, self.taxdf, "", self.opts["capnm"],
            self.sysdt, 0]
        self.sql.insRec("memtrn", data=data)
        # Members Ledger Category (memcat)
        self.sql.updRec("memcat", cols=["mlc_last"], data=[trdt],
            where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno", "=",
            self.memno), ("mlc_type", "=", ctyp), ("mlc_code", "=", code)])
        if vat:
            # VAT Transaction (ctlvtf)
            val = float(ASD(0) - ASD(amt) + ASD(vat))
            tax = float(ASD(0) - ASD(vat))
            data = [self.opts["conum"], self.taxdf, "O", curdt, "M", 1,
                self.batch, ref, trdt, self.memno, desc, val, tax, 0,
                self.opts["capnm"], self.sysdt, 0]
            self.sql.insRec("ctlvtf", data=data)
        if self.glint == "N":
            return
        ref = "ML/MthEnd"
        # General Ledger Member Control
        whr = [
            ("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.memctl),
            ("glt_batch", "=", self.batch),
            ("glt_curdt", "=", curdt),
            ("glt_trdt", "=", trdt),
            ("glt_type", "=", 1)]
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            tmp = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            tmp = float(ASD(tmp) + ASD(amt))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[tmp], where=whr)
        else:
            data = [self.opts["conum"], self.memctl, curdt, trdt, 1, ref,
                self.batch, amt, 0, "Month End Raising Charges", "", "", 0,
                self.opts["capnm"], self.sysdt, 0]
            self.sql.insRec("gentrn", data=data)
        val = float(ASD(0) - ASD(amt) + ASD(vat))
        tax = float(ASD(0) - ASD(vat))
        # General Ledger Income Account
        whr[1] = ("glt_acno", "=", glac)
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            tmp = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            tmp = float(ASD(tmp) + ASD(val))
            glt[0][self.sql.gentrn_col.index("glt_tramt")] = tmp
            tmp = glt[0][self.sql.gentrn_col.index("glt_taxamt")]
            tmp = float(ASD(tmp) + ASD(tax))
            glt[0][self.sql.gentrn_col.index("glt_taxamt")] = tmp
            self.sql.updRec("gentrn", data=glt[0], where=whr)
        else:
            data = [self.opts["conum"], glac, curdt, trdt, 1, ref, self.batch,
                val, tax, "Month End Raising Charges", self.taxdf, "", 0,
                self.opts["capnm"], self.sysdt, 0]
            self.sql.insRec("gentrn", data=data)
        if not tax:
            return
        # General Ledger VAT Account
        whr = [("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
            self.vatctl), ("glt_batch", "=", self.batch), ("glt_curdt", "=",
            curdt), ("glt_trdt", "=", trdt), ("glt_type", "=", 1)]
        glt = self.sql.getRec("gentrn", where=whr)
        if glt and len(glt) == 1:
            tmp = glt[0][self.sql.gentrn_col.index("glt_tramt")]
            tmp = float(ASD(tmp) + ASD(tax))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[tmp], where=whr)
        else:
            data = [self.opts["conum"], self.vatctl, curdt, trdt, 1, ref,
                self.batch, tax, 0.00, "Month End Raising Charges", "", "", 0,
                self.opts["capnm"], self.sysdt, 0]
            self.sql.insRec("gentrn", data=data)

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
