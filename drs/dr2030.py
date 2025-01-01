"""
SYNOPSIS
    Debtors Ledger - Raising Recurring Charges.

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

import os, time
from TartanClasses import ASD, Batches, GetCtl, Sql, TartanDialog, PrintCharges
from tartanFunctions import getSingleRecords, getVatRate, mthendDate

class dr2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlvrf", "ctlvtf",
            "drsmst", "drstrn", "drsrcm", "drsrct", "drsrci", "genmst",
            "gentrn", "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.glint = drsctl["ctd_glint"]
        self.ctmpl = drsctl["ctd_chgtpl"]
        self.fromad = drsctl["ctd_emadd"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"],ctlctl,["drs_ctl","vat_ctl"]):
                return
            self.drsctl = ctlctl["drs_ctl"]
            self.vatctl = ctlctl["vat_ctl"]
        ctl = self.sql.getRec("ctlmst",
            where=[("ctm_cono", "=", self.opts["conum"])], limit=1)
        for col in ("ctm_name", "ctm_add1", "ctm_add2", "ctm_add3",
                    "ctm_pcode", "ctm_regno", "ctm_taxno", "ctm_tel",
                    "ctm_fax", "ctm_b_name", "ctm_b_branch", "ctm_b_ibt",
                    "ctm_b_acno", "ctm_logo"):
            setattr(self, "%s" % col, ctl[self.sql.ctlmst_col.index(col)])
        if "LETTERHEAD" in os.environ:
            self.ctm_logo = os.environ["LETTERHEAD"]
        if not self.ctm_logo or not os.path.exists(self.ctm_logo):
            self.ctm_logo = None
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "DRS", self.opts["rtn"],
            multi="N", glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return

    def doProcess(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "I"),
                ("tpm_system", "=", "DRS")],
            "order": "tpm_tname"}
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually","6"),
            ("Annually","Y"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Frequency","",
                "M","N",self.doFreq,None,None,None),
            (("T",0,1,0),("IRB",r2s),1,"All Charges","",
                "N","N",self.doAll,None,None,None),
            (("T",0,2,0),"INa",9,"2nd Reference","",
                "","N",self.doRef2,None,None,None),
            (("T",0,3,0),("IRB",r2s),1,"Print Invoices","",
                "N","N",self.doInv,None,None,None),
            (("T",0,4,0),"INA",20,"Invoice Template","",
                self.ctmpl,"N",self.doTmp,tpm,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","P"), mail=("N","Y"))

    def doFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w
        self.wher = [("dcm_cono", "=", self.opts["conum"]), ("dcm_freq", "=",
            self.freq), ("dcm_last", "<", self.bh.curdt)]
        data = self.sql.getRec("drsrcm", where=self.wher)
        if not data:
            return "No Valid Recurring Charges"
        if self.freq == "M":
            self.mths = 1
        elif self.freq == "3":
            self.mths = 3
        elif self.freq == "6":
            self.mths = 6
        else:
            self.mths = 12

    def doAll(self, frt, pag, r, c, p, i, w):
        self.allc = w

    def doRef2(self, frt, pag, r, c, p, i, w):
        self.ref2 = w

    def doInv(self, frt, pag, r, c, p, i, w):
        self.inv = w
        if self.inv == "N":
            self.df.loadEntry(frt, pag, p+2, data="")
            return "nd"
        self.cwd = None
        self.docs = []

    def doTmp(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "DRS")], limit=1)
        if not chk:
            return "Invalid Template"
        self.tname = w

    def doCons(self, frt, pag, r, c, p, i, w):
        self.cons = w

    def doEml(self, frt, pag, r, c, p, i, w):
        self.eml = w

    def doEnd(self):
        self.df.closeProcess()
        if self.allc == "N":
            recs = getSingleRecords(self.opts["mf"], "drsrcm", ("dcm_num",
                "dcm_desc"), where=self.wher, order="dcm_num")
        else:
            recs = self.sql.getRec("drsrcm", where=self.wher, order="dcm_num")
        for dcm in recs:
            num = dcm[self.sql.drsrcm_col.index("dcm_num")]
            desc = dcm[self.sql.drsrcm_col.index("dcm_desc")]
            day = dcm[self.sql.drsrcm_col.index("dcm_day")]
            if day == 30:
                self.trdt = mthendDate((self.bh.curdt * 100) + 1)
            else:
                self.trdt = (self.bh.curdt * 100) + day
            vat = dcm[self.sql.drsrcm_col.index("dcm_vat")]
            self.vatrte = getVatRate(self.sql, self.opts["conum"],
                vat, self.trdt)
            glac = dcm[self.sql.drsrcm_col.index("dcm_glac")]
            nxt = self.sql.getRec("drstrn", cols=["max(drt_ref1)"],
                where=[("drt_cono", "=", self.opts["conum"]),
                ("drt_ref1", "like", "RCI%")], limit=1)
            if not nxt[0]:
                nxt = 0
            else:
                nxt = int(nxt[0][3:])
            tot_val = 0
            tot_vat = 0
            rec = self.sql.getRec("drsrct", where=[("dct_cono", "=",
                self.opts["conum"]), ("dct_num", "=", num), ("dct_start",
                "<=", self.bh.curdt), ("dct_end", ">=", self.bh.curdt)])
            col = self.sql.drsrct_col
            for dct in rec:
                chain = dct[col.index("dct_chain")]
                acno = dct[col.index("dct_acno")]
                # Check for Redundancy
                chk = self.sql.getRec("drsmst", cols=["drm_stat"],
                    where=[("drm_cono", "=", self.opts["conum"]),
                    ("drm_chain", "=", chain), ("drm_acno", "=",
                    acno)], limit=1)
                if chk[0] == "X":
                    continue
                # Check for Valid Period
                charge = False
                start = dct[col.index("dct_start")]
                year = int(start / 100)
                month = start % 100
                while start <= self.bh.curdt:
                    if start == self.bh.curdt:
                        charge = True
                        break
                    month += self.mths
                    if month > 12:
                        year += 1
                        month -= 12
                    start = (year * 100) + month
                if not charge:
                    continue
                # Create Transactions
                nxt += 1
                refno = "RCI%06i" % nxt
                detail = dct[col.index("dct_detail")]
                amnt = dct[col.index("dct_amnt")]
                vmnt = round(amnt * self.vatrte / 100, 2)
                tmnt = float(ASD(amnt) + ASD(vmnt))
                tot_val = float(ASD(tot_val) + ASD(amnt))
                tot_vat = float(ASD(tot_vat) + ASD(vmnt))
                # Debtors (drstrn)
                self.sql.insRec("drstrn", data=[self.opts["conum"],
                    chain, acno, 1, refno, self.bh.batno,
                    self.trdt, refno, tmnt, vmnt,
                    self.bh.curdt, detail[:30], vat, "Y",
                    self.opts["capnm"], self.sysdtw, 0])
                # Invoice Table
                self.sql.insRec("drsrci", data=[self.opts["conum"],
                    chain, acno, refno, self.trdt,
                    detail, amnt, self.vatrte,
                    self.opts["capnm"], self.sysdtw])
                if self.inv == "Y":
                    self.docs.append(refno)
                # VAT (ctlvtf)
                amnt = float(ASD(0) - ASD(amnt))
                vmnt = float(ASD(0) - ASD(vmnt))
                data = [self.opts["conum"], vat, "O", self.bh.curdt,
                    "D", 1, self.bh.batno, refno, self.trdt, acno,
                    detail[:30], amnt, vmnt, 0, self.opts["capnm"],
                    self.sysdtw, 0]
                self.sql.insRec("ctlvtf", data=data)
            if self.glint == "Y":
                ref = "RC%07i" % num
                # Update Debtors Control
                amnt = float(ASD(tot_val) + ASD(tot_vat))
                data = (self.opts["conum"], self.drsctl, self.bh.curdt,
                    self.trdt, 1, ref, self.bh.batno, amnt, 0, desc,
                    "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                # Update Sales Account
                amnt = float(ASD(0) - ASD(tot_val))
                data = (self.opts["conum"], glac, self.bh.curdt, self.trdt,
                    1, ref, self.bh.batno, amnt, 0, desc, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                amnt = float(ASD(0) - ASD(tot_vat))
                if amnt:
                    # Update VAT Control
                    data = (self.opts["conum"], self.vatctl, self.bh.curdt,
                        self.trdt, 1, ref, self.bh.batno, amnt, 0, desc,
                        "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                    self.sql.insRec("gentrn", data=data)
            # Update Recurring Charge (drsrcm)
            self.sql.updRec("drsrcm", cols=["dcm_last"], data=[self.bh.curdt],
                where=[("dcm_cono", "=", self.opts["conum"]), ("dcm_num", "=",
                num), ("dcm_freq", "=", self.freq)])
        self.opts["mf"].dbm.commitDbase()
        if self.inv == "Y" and self.docs:
            # Create Invoice
            PrintCharges(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], self.docs, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml, copy="n")
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
