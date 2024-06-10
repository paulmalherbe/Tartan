"""
SYNOPSIS
    General Ledger Data Capture for:

        1 Sales
        2 Payments
        3 Petty Cash
        5 Purchases
        6 Receipts
        7 Bank Statements

    Flags used:

        self.incoac - Intercompany accounts posting
        self.dorec  - Bank Statement capture
        self.recon  - Transaction found during Statement Capture
        self.rctimp - RCT (Bank codes) Transactions import
        self.rctupd - Update genrct table

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
from TartanClasses import AgeAll, ASD, BankImport, Batches, CCD, GetCtl
from TartanClasses import ProgressBar, SChoice, Sql, TartanDialog, tk
from tartanFunctions import askQuestion, callModule, chkGenAcc, getNextCode
from tartanFunctions import getSingleRecords, getVatRate, copyList, mthendDate
from tartanFunctions import showError
from tartanWork import gltrtp

class gl2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.checkControls():
            self.batchHeader()
            if self.bh.batno:
                self.setVariables()
                self.drawDialog()
                self.opts["mf"].startLoop()

    def checkControls(self):
        # Check for Valid Posting Routine
        if self.opts["rtn"] not in (1, 2, 3, 5, 6, 7):
            showError(self.opts["mf"].body, "Error",
                "Invalid Routine " + str(self.opts["rtn"]))
            return
        self.glrtn = self.opts["rtn"]
        # Check for Company Record
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.allcoy = self.opts["conum"]
        self.allnam = self.opts["conam"]
        # Get Enabled Modules
        tabs = ["ctlctl", "ctlmst", "ctlpwu", "ctlvmf", "ctlvrf", "ctlvtf",
            "genint", "genmst", "gentrn", "genrcc", "genrct"]
        mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mod.append(ctlmst["ctm_modules"][x:x+2])
        # Load Control Accounts
        self.tags = [
            ("Transaction", None, None, None, False),
            ("Allocation", None, None, None, False)]
        self.tagp = {}
        page = 2
        if mod.count("AR"):
            ctl = self.gc.getCtl("assctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["cta_glint"] == "Y":
                tabs.extend(["assgrp", "assmst", "asstrn"])
                self.tags.append(("ASS", None, None, None, False))
                page += 1
                self.tagp["AR"] = page
        if mod.count("BK"):
            ctl = self.gc.getCtl("bkmctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["cbk_glint"] == "Y":
                tabs.extend(["bkmcon", "bkmmst", "bkmtrn"])
                self.tags.append(("BKM", None, None, None, False))
                page += 1
                self.tagp["BK"] = page
        if mod.count("CR"):
            ctl = self.gc.getCtl("crsctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["ctc_glint"] == "Y":
                if self.glrtn == 5:
                    showError(self.opts["mf"].body, "Invalid Routine",
                        "Because Creditors are Integrated, All %ss Must be "\
                        "Captured via the Creditors System else the Control "\
                        "Account Will Not Balance!" % \
                        gltrtp[self.glrtn - 1][1])
                    return
                tabs.extend(["crsmst", "crstrn"])
                self.tags.append(("CRS", None, None, None, False))
                page += 1
                self.tagp["CR"] = page
        if mod.count("DR"):
            ctl = self.gc.getCtl("drsctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["ctd_glint"] == "Y":
                if self.glrtn == 1:
                    showError(self.opts["mf"].body, "Invalid Routine",
                        "Because Debtors are Integrated, All %ss Must be "\
                        "Captured via the Debtors System else the Control "\
                        "Account Will Not Balance!" % \
                        gltrtp[self.glrtn - 1][1])
                    return
                tabs.extend(["drsmst", "drstrn"])
                self.tags.append(("DRS", None, None, None, False))
                page += 1
                self.tagp["DR"] = page
        if mod.count("LN"):
            ctl = self.gc.getCtl("lonctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["cln_glint"] == "Y":
                tabs.extend(["lonmf1", "lonmf2", "lonrte", "lontrn"])
                self.tags.append(("LON", None, None, None, False))
                page += 1
                self.tagp["LN"] = page
                self.lon_cr = 0
                self.lon_dr = 0
        if mod.count("ML"):
            ctl = self.gc.getCtl("memctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["mcm_glint"] == "Y":
                tabs.extend(["memmst", "memtrn"])
                self.tags.append(("MEM", None, None, None, False))
                page += 1
                self.tagp["ML"] = page
        if mod.count("RC"):
            ctl = self.gc.getCtl("rcactl", self.opts["conum"])
            if not ctl:
                return
            if ctl["cte_glint"] == "Y":
                tabs.extend(["rcaprm", "rcaowm", "rcaowt", "rcatnm",
                    "rcatnt", "rcacon"])
                self.tags.append(("RCA", None, None, None, False))
                page += 1
                self.tagp["RC"] = page
        if mod.count("RT"):
            ctl = self.gc.getCtl("rtlctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["ctr_glint"] == "Y":
                tabs.extend(["rtlprm", "rtlmst", "rtlcon", "rtltrn"])
                self.tags.append(("RTL", None, None, None, False))
                page += 1
                self.tagp["RT"] = page
        if mod.count("SL"):
            ctl = self.gc.getCtl("wagctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["ctw_glint"] == "Y":
                tabs.extend(["wagmst", "waglmf", "wagltf"])
                self.tags.append(("SLN", None, None, None, False))
                page += 1
                self.tagp["SL"] = page
                self.sln_rt = 0
        # Check if Control Accounts Exist
        self.ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
        if not self.ctlctl:
            return
        if self.glrtn == 1:
            if self.gc.chkRec(self.opts["conum"], self.ctlctl, ["drs_ctl"]):
                return
        elif self.glrtn == 3:
            if self.gc.chkRec(self.opts["conum"], self.ctlctl, ["p_cash"]):
                return
        elif self.glrtn == 5:
            if self.gc.chkRec(self.opts["conum"], self.ctlctl, ["crs_ctl"]):
                return
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Check for Intercompany Facility
        if not self.sql.getRec("ctlmst", cols=["count(*)"],
                where=[("ctm_cono", "<>", self.opts["conum"])], limit=1)[0]:
            self.incoac = False
        else:
            itg = self.sql.getRec("genint", cols=["cti_inco"],
                where=[("cti_cono", "=", self.opts["conum"])])
            if itg:
                self.incoac = [self.opts["conum"]]
                [self.incoac.append(coy[0]) for coy in itg]
            else:
                self.incoac = False
        if not self.incoac and self.doChkLoadCtls():
            return
        # Get users security level
        acc = self.sql.getRec("ctlpwu", cols=["usr_lvl"],
            where=[("usr_name", "=", self.opts["capnm"])], limit=1)
        if not acc:
            return
        self.lvl = acc[0]
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "GEN", self.glrtn)
        self.bh.doBatchHeader()
        if self.bh.batno and self.glrtn not in (1, 6):
            self.bh.batval = float(ASD(0) - ASD(self.bh.batval))

    def setVariables(self):
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        # Load Control Account
        if self.glrtn == 1:
            self.conacc = self.ctlctl["drs_ctl"]
        elif self.glrtn == 2:
            self.conacc = self.bh.acc
        elif self.glrtn == 3:
            self.conacc = self.ctlctl["p_cash"]
        elif self.glrtn == 5:
            self.conacc = self.ctlctl["crs_ctl"]
        elif self.glrtn == 6:
            self.conacc = self.bh.acc
        # Bank Import Codes
        self.pcash = False
        self.dorec = False
        self.rctimp = False
        if self.glrtn == 3:
            self.pcash = True
        elif self.glrtn == 7:
            det = self.sql.getRec("ctlctl", where=[("ctl_cono", "=",
                self.opts["conum"]), ("ctl_code", "=", self.bh.ctl)], limit=1)
            self.bankac = det[self.sql.ctlctl_col.index("ctl_bankac")]
            self.impfmt = det[self.sql.ctlctl_col.index("ctl_impfmt")]
            self.dtefmt = det[self.sql.ctlctl_col.index("ctl_dtefmt")]
            self.dorec = True
        self.cancel = False
        self.agecan = False
        self.batupd = False
        # Boolean variables
        self.agevar = tk.BooleanVar()
        self.rctvar = tk.BooleanVar()
        self.othvar = tk.BooleanVar()
        self.agevar.set(False)
        self.rctvar.set(False)
        self.othvar.set(False)

    def drawDialog(self):
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        if self.opts["rtn"] == 7:
            glt = None
        else:
            glt = {
                "stype": "R",
                "title": "Transactions",
                "tables": ("gentrn",),
                "cols": (
                    ("glt_refno", "", 0, ""),
                    ("glt_trdt", "", 0, ""),
                    ("glt_tramt", "", 0, ""),
                    ("glt_desc", "", 0, "")),
                "where": [
                    ("glt_cono", "=", self.opts["conum"]),
                    ("glt_acno", "=", self.conacc),
                    ("glt_type", "=", self.opts["rtn"]),
                    ("glt_batch", "=", self.bh.batno)],
                "order": "glt_seq",
                "comnd": self.doView}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "whera": [("C", "glm_cono", 0, 2)],
            "order": "glm_desc"}
        if "AR" in self.tagp:
            asg = {
                "stype": "R",
                "tables": ("assgrp",),
                "cols": (
                    ("asg_group", "", 0, "Grp"),
                    ("asg_desc", "", 0, "Description", "Y")),
                "whera": [("C", "asg_cono", 0, 2)]}
            asm = {
                "stype": "R",
                "tables": ("assmst",),
                "cols": (
                    ("asm_code", "", 0, "Cod-Num"),
                    ("asm_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "asm_cono", 0, 2),
                    ("C", "asm_group", 0, self.tagp["AR"])]}
            data = []
            from tartanWork import armvtp
            for x in range(1, len(armvtp)+1):
                if x == 4:
                    continue
                data.append([x, armvtp[x-1][1]])
            mov = {
                "stype": "C",
                "titl": "Valid Types",
                "head": ("C", "Description"),
                "data": data}
        if "BK" in self.tagp:
            bkm = {
                "stype": "R",
                "tables": ("bkmmst", "bkmcon"),
                "cols": (
                    ("bkm_number", "", 0, "Bkm-No"),
                    ("bkc_sname", "", 0, "Surname", "Y"),
                    ("bkc_names", "", 0, "Names")),
                "where": [
                    ("bkc_cono=bkm_cono",),
                    ("bkc_ccode=bkm_ccode",)],
                "whera": [("C", "bkm_cono", 0, 2)]}
        if "CR" in self.tagp:
            crm = {
                "stype": "R",
                "tables": ("crsmst",),
                "cols": (
                    ("crm_acno", "", 0, "Acc-Num"),
                    ("crm_name", "", 0, "Name", "Y")),
                "where": [("crm_stat", "<>", "X")],
                "whera": [("C", "crm_cono", 0, 2)]}
        if "DR" in self.tagp:
            chn = {
                "stype": "R",
                "tables": ("drschn",),
                "cols": (
                    ("chm_chain", "", 0, "Num"),
                    ("chm_name", "", 0, "Name", "Y")),
                "whera": [("C", "chm_cono", 0, 2)]}
            drm = {
                "stype": "R",
                "tables": ("drsmst",),
                "cols": (
                    ("drm_acno", "", 0, "Acc-Num"),
                    ("drm_name", "", 0, "Name", "Y"),
                    ("drm_add1", "", 0, "Address Line 1")),
                "where": [("drm_stat", "<>", "X")],
                "whera": [
                    ("C", "drm_cono", 0, 2),
                    ("C", "drm_chain", 0, self.tagp["DR"])]}
        if "LN" in self.tagp:
            lm1 = {
                "stype": "R",
                "tables": ("lonmf1",),
                "cols": (
                    ("lm1_acno", "", 0, "Acc-Num"),
                    ("lm1_name", "", 0, "Name", "Y")),
                "whera": [("C", "lm1_cono", 0, 2)]}
            lm2 = {
                "stype": "R",
                "tables": ("lonmf2",),
                "cols": (
                    ("lm2_loan", "", 0, "Ln"),
                    ("lm2_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "lm2_cono", 0, 2),
                    ("C", "lm2_acno", 0, self.tagp["LN"])]}
        if "ML" in self.tagp:
            mlm = {
                "stype": "R",
                "tables": ("memmst",),
                "cols": (
                    ("mlm_memno", "", 0, "Mem-No"),
                    ("mlm_surname", "", 0, "Surname", "Y"),
                    ("mlm_names", "", 0, "Names")),
                "whera": [("C", "mlm_cono", 0, 2)]}
        if "RC" in self.tagp:
            rcp = {
                "stype": "R",
                "tables": ("rcaprm",),
                "cols": (
                    ("rcp_code", "", 0, "Pr-Code"),
                    ("rcp_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "rcp_cono", 0, 2)]}
            rct = {
                "stype": "R",
                "tables": ("rcatnm",),
                "cols": (
                    ("rtn_acno", "", 0, "Cod-Num"),
                    ("rtn_name", "", 0, "Name", "Y")),
                "whera": [
                    ("C", "rtn_cono", 0, 2),
                    ("C", "rtn_owner", 2, self.tagp["RC"]),
                    ("C", "rtn_code", 0, self.tagp["RC"])]}
            rcc = {
                "stype": "R",
                "tables": ("rcacon",),
                "cols": (
                    ("rcc_cnum", "", 0, "Cod-Num"),
                    ("rcc_payind", "", 0, "F"),
                    ("rcc_start", "", 0, "Start-Date"),
                    ("rcc_period", "", 0, "Per")),
                "whera": [
                    ("C", "rcc_cono", 0, 2),
                    ("C", "rcc_code", 0, self.tagp["RC"]),
                    ("C", "rcc_acno", 4, self.tagp["RC"])]}
            data = []
            from tartanWork import rcmvtp
            for x in range(1, len(rcmvtp)+1):
                if x == 2:
                    continue
                data.append((x, rcmvtp[x-1][1]))
            rcm = {
                "stype": "C",
                "titl": "Select the Required Type",
                "head": ("C", "Type"),
                "data": data}
        if "RT" in self.tagp:
            rtp = {
                "stype": "R",
                "tables": ("rtlprm",),
                "cols": (
                    ("rtp_code", "", 0, "Pr-Code"),
                    ("rtp_desc", "", 0, "Description", "Y")),
                "whera": [("C", "rtp_cono", 0, 2)]}
            rtm = {
                "stype": "R",
                "tables": ("rtlmst",),
                "cols": (
                    ("rtm_acno", "", 0, "Cod-Num"),
                    ("rtm_name", "", 0, "Name", "Y")),
                "whera": [
                    ("C", "rtm_cono", 0, 2),
                    ("C", "rtm_code", 0, self.tagp["RT"])]}
            rtc = {
                "stype": "R",
                "tables": ("rtlcon",),
                "cols": (
                    ("rtc_cnum", "", 0, "Cod-Num"),
                    ("rtc_payind", "", 0, "F"),
                    ("rtc_start", "", 0, "Start-Date"),
                    ("rtc_period", "", 0, "Per")),
                "whera": [
                    ("C", "rtc_cono", 0, 2),
                    ("C", "rtc_code", 0, self.tagp["RT"]),
                    ("C", "rtc_acno", 2, self.tagp["RT"])]}
        if "SL" in self.tagp:
            wgm = {
                "stype": "R",
                "tables": ("wagmst",),
                "cols": (
                    ("wgm_empno", "", 0, "EmpNo"),
                    ("wgm_sname", "", 0, "Surname", "Y"),
                    ("wgm_fname", "", 0, "Names")),
                "whera": [("C", "wgm_cono", 0, 2)]}
            lmf = {
                "stype": "R",
                "tables": ("waglmf",),
                "cols": (
                    ("wlm_loan", "", 0, "Ln"),
                    ("wlm_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "wlm_cono", 0, 2),
                    ("C", "wlm_empno", 0, self.tagp["SL"])]}
            ced = {
                "stype": "R",
                "tables": ("wagedc",),
                "cols": (
                    ("ced_type", "", 0, "T"),
                    ("ced_code", "", 0, "Cde"),
                    ("ced_desc", "", 0, "Description", "Y")),
                "where": [("ced_type", "=", "D")],
                "whera": [("C", "ced_cono", 0, 2)],
                "index": 1}
        vat = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "whera": [("C", "vtm_cono", 0, 2)]}
        fld = [
            [["T",0,0,0],"OUI",9,"Batch %s Quantity" % self.bh.batno],
            [["T",0,0,0],"OSD",13.2,"Value"],
            [["C",1,0,0],"INa",9,"Reference","Reference Number",
                "i","Y",self.doTrnRef,glt,None,("notblank",)],
            [["C",1,0,1],"ID1",10,"Date","Transaction Date",
                "r","N",self.doTrnDte,None,None,("efld",)],
            [["C",1,0,2],"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,("efld",)],
            [["C",1,0,3],"INA",30,"Details","Transaction Details",
                "","N",self.doTrnDet,None,None,("notblank",)],
            [["T",2,0,0],"OSD",13.2,"Unallocated Balance"],
            [["C",2,0,0],"IUI",3,"Coy","Company Number",
                self.opts["conum"],"N",self.doCoyNum,coy,None,("notzero",)],
            [["C",2,0,1],"IUI",7,"Acc-Num","Account Number",
                "","Y",self.doAccNum,glm,None,None],
            [["C",2,0,2],"ONA",30,"Description"],
            [["C",2,0,3],"ISD",13.2,"Alloc-Amt","Allocation Amount",
                "","N",self.doAllAmt,None,None,("efld",)],
            [["C",2,0,4],"IUA",1,"V","V.A.T. Code",
                "","N",self.doVatCod,vat,None,("notblank",)],
            [["C",2,0,5],"ISD",13.2,"VAT-Amt","V.A.T. Amount",
                "","N",self.doVatAmt,None,None,("efld",)],
            [["C",2,0,6],"INA",(28,30),"Details","Allocation Details",
                "","N",self.doAllDet,None,None,("notblank",)]]
        tags = list(self.tagp.keys())
        tags.sort()
        for tag in tags:
            if tag == "AR":
                self.asspag = self.tagp[tag]
                fld.extend([
                    [["T",self.asspag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.asspag,0,0],"IUA",3,"Grp","Asset Group",
                        "r","N",self.doAssGrp,asg,None,("notblank",)],
                    [["C",self.asspag,0,1],"INa",7,"Cod-Num","Asset Code",
                        "r","N",self.doAssCod,asm,None,("notblank",)],
                    [["C",self.asspag,0,2],"ONA",30,"Description"],
                    [["C",self.asspag,0,3],"IUI",1,"M","Movement Type",
                        "r","N",self.doAssMov,mov,None,("in",(1,2,5))],
                    [["C",self.asspag,0,4],"ISD",13.2,"Amount","",
                        "","N",self.doAssAmt,None,None,("efld",)],
                    [["C",self.asspag,0,5],"INA",30,"Details","Details",
                        "","N",self.doAssDet,None,None,("efld",)]])
            elif tag == "BK":
                self.bkmpag = self.tagp[tag]
                fld.extend([
                    [["T",self.bkmpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.bkmpag,0,0],"IUI",6,"Bkm-Num","Booking Number",
                        "","N",self.doBkmNum,bkm,None,("notzero",)],
                    [["C",self.bkmpag,0,1],"ONA",70,"Name"],
                    [["C",self.bkmpag,0,2],"ISD",13.2,"Amount","",
                        "","N",self.doBkmAmt,None,None,("efld",)]])
            elif tag == "CR":
                self.crspag = self.tagp[tag]
                fld.extend([
                    [["T",self.crspag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.crspag,0,0],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doCrsAcc,crm,None,("notblank",)],
                    [["C",self.crspag,0,1],"ONA",30,"Name"],
                    [["C",self.crspag,0,2],"INa",9,"Ref-Num-2","",
                        "i","N",self.doCrsRef,None,None,None],
                    [["C",self.crspag,0,3],"ISD",13.2,"Discount","",
                        "","N",self.doCrsDis,None,None,("efld",),None,
                        "Discount Amount to be Added to the Amount."],
                    [["C",self.crspag,0,4],"ISD",13.2,"Amount","",
                        "","N",self.doCrsAmt,None,None,("efld",)],
                    [["C",self.crspag,0,5],"OSD",13.2,"Total-Amount"]])
            elif tag == "DR":
                self.drspag = self.tagp[tag]
                fld.extend([
                    [["T",self.drspag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.drspag,0,0],"IUI",3,"Chn","Chain Store Code",
                        "","N",self.doDrsChn,chn,None,("efld",)],
                    [["C",self.drspag,0,1],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doDrsAcc,drm,None,("notblank",)],
                    [["C",self.drspag,0,2],"ONA",30,"Name"],
                    [["C",self.drspag,0,3],"INa",9,"Ref-Num-2","",
                        "i","N",self.doDrsRef,None,None,None],
                    [["C",self.drspag,0,4],"ISD",13.2,"Discount","",
                        "","N",self.doDrsDis,None,None,("efld",),None,
                        "Discount Amount to be Added to the Amount."],
                    [["C",self.drspag,0,5],"ISD",13.2,"Amount","",
                        "","N",self.doDrsAmt,None,None,("efld",)],
                    [["C",self.drspag,0,6],"OSD",13.2,"Total-Amount"]])
            elif tag == "LN":
                self.lonpag = self.tagp[tag]
                fld.extend([
                    [["T",self.lonpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.lonpag,0,0],"IUA",7,"Acc-Num","Account Number",
                        "","N",self.doLonAcc,lm1,None,None],
                    [["C",self.lonpag,0,1],"ONA",20,"Name"],
                    [["C",self.lonpag,0,2],"IUI",2,"Ln","Loan Number",
                        "","N",self.doLonNum,lm2,None,("efld",)],
                    [["C",self.lonpag,0,3],"INA",30,"Description","",
                        "","N",self.doLonDes,None,None,("notblank",)],
                    [["C",self.lonpag,0,4],"ISD",13.2,"Amount","",
                        "","N",self.doLonAmt,None,None,("efld",)],
                    [["C",self.lonpag,0,5],"IUD",6.2,"DRte-%","Debit Rate",
                        self.lon_dr,"N",self.doLonDri,None,None,("efld",)],
                    [["C",self.lonpag,0,6],"IUD",6.2,"CRte-%","Credit Rate",
                        self.lon_cr,"N",self.doLonCri,None,None,("efld",)],
                    [["C",self.lonpag,0,7],"IUI",3,"Mth","Period in Months",
                        "","N",self.doLonMth,None,None,("efld",)],
                    [["C",self.lonpag,0,8],"OUD",12.2,"Repayment"]])
            elif tag == "ML":
                self.mempag = self.tagp[tag]
                fld.extend([
                    [["T",self.mempag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.mempag,0,0],"IUI",6,"Mem-Num","Member Number",
                        "","N",self.doMemAcc,mlm,None,("notblank",)],
                    [["C",self.mempag,0,1],"ONA",30,"Name"],
                    [["C",self.mempag,0,2],"ISD",13.2,"Discount","",
                        "","N",self.doMemDis,None,None,("efld",),None,
                        "Discount Amount to be Added to the Amount."],
                    [["C",self.mempag,0,3],"ISD",13.2,"Amount","",
                        "","N",self.doMemAmt,None,None,("efld",)],
                    [["C",self.mempag,0,4],"OSD",13.2,"Total-Amount"]])
            elif tag == "RC":
                self.rcapag = self.tagp[tag]
                fld.extend([
                    [["T",self.rcapag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.rcapag,0,0],"INA",7,"Prm-Cod","Premises Code",
                        "","N",self.doRcaPrm,rcp,None,("efld",)],
                    [["C",self.rcapag,0,1],"ONA",15,"Description"],
                    [["C",self.rcapag,0,0],"ONA",7,"Own-Cod"],
                    [["C",self.rcapag,0,1],"ONA",15,"Owners Name"],
                    [["C",self.rcapag,0,4],"INA",7,"Tnt-Cod","Tenant Code",
                        "","N",self.doRcaTnt,rct,None,("efld",)],
                    [["C",self.rcapag,0,5],"ONA",15,"Tenants Name"],
                    [("C",self.rcapag,0,6),"IUI",3,"Seq","Contract Sequence",
                        "","N",self.doRcaCon,rcc,None,None],
                    [("C",self.rcapag,0,7),"IUI",1,"T","Movement Type",
                        "","N",self.doRcaTyp,rcm,None,("in", (1,3,4,5,6))],
                    [["C",self.rcapag,0,8],"ISD",13.2,"Amount","",
                        "","N",self.doRcaAmt,None,None,("efld",)],
                    [["C",self.rcapag,0,9],"INA",30,"Details","Details",
                        "","N",self.doRcaDet,None,None,("efld",)]])
            elif tag == "RT":
                self.rtlpag = self.tagp[tag]
                fld.extend([
                    [["T",self.rtlpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.rtlpag,0,0],"INA",7,"Prm-Cod","Premises Code",
                        "","N",self.doRtlPrm,rtp,None,("efld",)],
                    [["C",self.rtlpag,0,1],"ONA",20,"Description"],
                    [["C",self.rtlpag,0,2],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doRtlAcc,rtm,None,("notblank",)],
                    [["C",self.rtlpag,0,3],"ONA",20,"Name"],
                    [("C",self.rtlpag,0,4),"IUI",3,"Seq","Contract Sequence",
                        "","N",self.doRtlCon,rtc,None,None],
                    [["C",self.rtlpag,0,5],"ISD",13.2,"Amount","",
                        "","N",self.doRtlAmt,None,None,("efld",)],
                    [["C",self.rtlpag,0,6],"INA",30,"Details","Details",
                        "","N",self.doRtlDet,None,None,("efld",)]])
            elif tag == "SL":
                self.slnpag = self.tagp[tag]
                fld.extend([
                    [["T",self.slnpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.slnpag,0,0],"IUI",5,"EmpNo","Employee Number",
                        "","N",self.doSlnEmp,wgm,None,None],
                    [["C",self.slnpag,0,1],"ONA",20,"Name"],
                    [["C",self.slnpag,0,2],"IUI",2,"Ln","Loan Number",
                        "","N",self.doSlnNum,lmf,None,None],
                    [["C",self.slnpag,0,3],"INA",20,"Description","",
                        "","N",self.doSlnDes,None,None,("notblank",)],
                    [["C",self.slnpag,0,4],"ISD",13.2,"Amount","",
                        "","N",self.doSlnAmt,None,None,("efld",)],
                    [["C",self.slnpag,0,5],"IUI",3,"Cde","Deduction Code",
                        "","N",self.doSlnCod,ced,None,("efld",)],
                    [["C",self.slnpag,0,6],"ONA",20,"Description"],
                    [["C",self.slnpag,0,7],"IUD",6.2,"Rate-%","Interest Rate",
                        self.sln_rt,"N",self.doSlnInt,None,None,("efld",)],
                    [["C",self.slnpag,0,8],"IUD",13.2,"Ded-Amt","Deduction",
                        "","N",self.doSlnDed,None,None,("efld",)]])
        if self.pcash:
            fld[2][10] = None
        if not self.incoac:
            fld[7][1] = "OUI"
        cnd = [
            (None, "n"),
            (self.endPage1, "y"),
            (self.endPage2, "y")]
        cxt = [
            None,
            self.exitPage1,
            None]
        for tag in tags:
            if tag == "AR":
                cnd.append((self.endAss, "y"))
                cxt.append(None)
            elif tag == "BK":
                cnd.append((self.endBkm, "y"))
                cxt.append(None)
            elif tag == "CR":
                cnd.append((self.endCrsDrsMem, "y"))
                cxt.append(None)
            elif tag == "DR":
                cnd.append((self.endCrsDrsMem, "y"))
                cxt.append(None)
            elif tag == "LN":
                cnd.append((self.endLon, "y"))
                cxt.append(None)
            elif tag == "ML":
                cnd.append((self.endCrsDrsMem, "y"))
                cxt.append(None)
            elif tag == "RC":
                cnd.append((self.endRca, "y"))
                cxt.append(None)
            elif tag == "RT":
                cnd.append((self.endRtl, "y"))
                cxt.append(None)
            elif tag == "SL":
                cnd.append((self.endSln, "y"))
                cxt.append(None)
        if self.glrtn in (2, 6) or self.pcash or self.dorec:
            self.but = [
                ["Age _Normal",None,self.doAgeNormal,0,None,None,
                    "Only Show Unallocated Transactions"],
                ["Age _History",None,self.doAgeHistory,0,None,None,
                    "Show All Transactions, Including Already Allocated"],
                ["Age _Automatic",None,self.doAgeAuto,0,None,None,
                    "Automatically Allocate the Amount Starting With the "\
                    "Oldest Unallocated One"],
                ["Age _Current",None,self.doAgeCurrent,0,None,None,
                    "Leave the Transaction Unallocated"]]
        else:
            self.but = []
        if self.pcash or self.dorec:
            if self.pcash:
                sel = None
                self.glt = None
            else:
                sel = {
                    "stype": "M",
                    "func": self.doSelections}
                self.glt = {
                    "stype": "R",
                    "tables": ("gentrn",),
                    "cols": (
                        ("glt_trdt", "", 0, "Date"),
                        ("glt_type", ("XX", gltrtp), 3, "Typ"),
                        ("glt_refno", "", 0, "Reference", "Y"),
                        ("glt_seq", "", 0, "Sequence"),
                        ("glt_tramt", "", 0, "Amount"),
                        ("glt_desc", "", 0, "Details")),
                    "where": [
                        ("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", self.bh.acc),
                        ("glt_recon", "=", 0)],
                    "order": "glt_trdt, glt_type, glt_refno",
                    "index": 2,
                    "zero": "0"}
            fld.insert(2, [("C",1,0,0),"IUA",1,"T","Reference Type (P/R)",
                "P","Y",self.doTrnTyp,sel,None,("in", ("P","R"))])
            fld[3][0][3] = 1
            fld[3][8] = self.glt
            fld[4][0][3] = 2
            fld[5][0][3] = 3
            fld[6][0][3] = 4
        if self.dorec:
            self.but.insert(0, ("Exit",None,self.exitPage1,0,
                ("C",1,1),(("C",1,2),("C",1,5))))
            self.but.insert(1, ("Import Bank File",None,self.doImpBank,0,
                ("C",1,1),(("C",1,2),("C",1,5))))
            self.but.insert(2, ("Process Bank Data",None,self.doImpRct,0,
                ("C",1,1),(("C",1,2),("C",1,5))))
            self.but.insert(3, ("Cance_l",None,self.doCancel,1,
                None,("C",1,1)))
        else:
            self.but.append(("Cance_l",None,self.doCancel,1,
                ("C",1,0),("C",1,1)))
        self.df = TartanDialog(self.opts["mf"], tags=self.tags,
            eflds=fld, butt=self.but, cend=cnd, cxit=cxt)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doImpBank(self):
        if self.impfmt not in ("O", "Q", "S"):
            showError(self.opts["mf"].body, "Recon Error",
                "Invalid Import Format Type for Control %s" % self.bh.ctl)
            self.df.focusField("C", 1, self.df.col)
            return
        if self.impfmt == "S" and not self.bankac:
            showError(self.opts["mf"].body, "Recon Error",
                "Invalid Bank Account for Control %s" % self.bh.ctl)
            self.df.focusField("C", 1, self.df.col)
            return
        if self.impfmt in ("O", "Q") and not self.dtefmt:
            showError(self.opts["mf"].body, "Recon Error",
                "Invalid Date Format for Control %s" % self.bh.ctl)
            self.df.focusField("C", 1, self.df.col)
            return
        self.df.setWidget(self.df.B0, "disabled")
        self.df.setWidget(self.df.B1, "disabled")
        self.df.setWidget(self.df.B2, "disabled")
        self.df.setWidget(self.df.colEntry[1][self.df.pos], "disabled")
        state = self.df.disableButtonsTags()
        tit = ("Bank %s Import" % self.bankac,)
        fld = (
            (("T",0,0,0),"ID1",10,"From Date","Import From Date",
                "","N",self.doFmDate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"To  Date","Import To Date",
                "","N",self.doToDate,None,None,("efld",)))
        tnd = ((self.doImpEnd,"n"), )
        txt = (self.doImpExit, )
        self.ip = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.ip.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField("C", 1, self.df.col)

    def doFmDate(self, frt, pag, r, c, p, i, w):
        self.ifrom = w

    def doToDate(self, frt, pag, r, c, p, i, w):
        self.ito = w

    def doImpEnd(self):
        self.ip.closeProcess()
        bimp = BankImport(self.opts["mf"], self.impfmt, self.bankac,
            self.dtefmt)
        if not bimp.trans:
            return
        for date, memo, refno, payee, amount in bimp.trans:
            date = CCD(date, "D1", 10)
            memo = CCD(memo, "NA", 100)
            refno = CCD(refno, "Na", 9)
            payee = CCD(payee, "NA", 50)
            amount = CCD(amount, "SD", 13.2)
            if date.work < self.ifrom or date.work > self.ito:
                continue
            autoref = False
            if refno.work in ("", "        0", 0):
                autoref = True
            else:
                chk = self.sql.getRec("gentrn", cols=["count(*)"],
                    where=[("glt_cono", "=", self.opts["conum"]),
                    ("glt_acno", "=", self.bh.acc), ("glt_refno", "=",
                    refno.work)], limit=1)
                if chk[0]:
                    autoref = True
            if autoref:
                ref = memo.work.split()
                if amount.work < 0 and ref[0] == "CHEQUE" and \
                             len(ref) > 1 and ref[1] != "CASHED":
                    # Nedbank cheque number
                    refno = ref[1][1:8]
                else:
                    # Next automatic reference
                    acc = self.sql.getRec("genrct",
                        cols=["max(grt_refno)"], where=[("grt_cono", "=",
                        self.opts["conum"]), ("grt_acno", "=",
                        self.bh.acc), ("grt_refno", "like", "BS_______")],
                        limit=1)
                    if acc:
                        try:
                            auto = int(acc[0][2:]) + 1
                        except:
                            auto = 1
                    else:
                        auto = 1
                    refno = "BS%07d" % auto
                refno = CCD(refno, "Na", 9)
            whr = [
                ("grt_cono", "=", self.opts["conum"]),
                ("grt_acno", "=", self.bh.acc),
                ("grt_date", "=", date.work),
                ("grt_memo", "=", memo.work),
                ("grt_payee", "=", payee.work),
                ("grt_amount", "=", amount.work)]
            if not autoref:
                whr.append(("grt_refno", "=", refno.work))
            acc = self.sql.getRec("genrct", where=whr)
            if acc and autoref:
                ok = askQuestion(self.opts["mf"].body, head="Import Error",
                    mess="This record seems to be duplicated,\n"\
                        "  Date:      %s\n"\
                        "  Payee:     %s\n"\
                        "  Amount:    %s\n\n"\
                        "  Import Anyway?" % \
                        (date.disp, payee.disp, amount.disp),
                    default="no")
                if ok == "no":
                    continue
            elif acc:
                continue
            data = [self.opts["conum"], self.bh.acc, date.work, memo.work,
                refno.work, payee.work, amount.work, "N", 0]
            self.sql.insRec("genrct", data=data)
        self.opts["mf"].dbm.commitDbase()

    def doImpExit(self):
        self.ip.closeProcess()

    def doImpRct(self):
        data = self.doReadRct()
        if not data:
            self.df.focusField("C", 1, self.df.col)
            return
        self.rctimp = True
        self.df.setWidget(self.df.B0, "disabled")
        self.df.setWidget(self.df.B1, "disabled")
        self.df.setWidget(self.df.B2, "disabled")
        self.df.setWidget(self.df.colEntry[1][self.df.pos], "disabled")
        self.df.colf[1][4][4] += "(noesc)"
        self.df.setWidget(self.df.mstFrame, state="hide")
        # Try and automatically allocate genrct records
        p = ProgressBar(self.opts["mf"].body, typ="Automatically "\
            "Allocating, Please Wait....", mxs=len(data))
        for num, line in enumerate(data):
            p.displayProgress(num)
            dte = line[self.sql.genrct_col.index("grt_date")]
            mem = line[self.sql.genrct_col.index("grt_memo")][:50]
            ref = line[self.sql.genrct_col.index("grt_refno")]
            amt = line[self.sql.genrct_col.index("grt_amount")]
            seq = line[self.sql.genrct_col.index("grt_seq")]
            self.doAutoRct(dte, mem, ref, amt, seq)
        p.closeProgress()
        self.df.setWidget(self.df.mstFrame, state="show")
        # Show all unallocated genrct and select one to allocate
        while True:
            data = self.doReadRct()
            if not data:
                break
            # Manual Postings and Allocations of unallocated entries
            titl = "Unallocated Statement Entries"
            head = ("   Date", "Memo-Details", "Reference",
                "Payee-Details", "      Amount ")
            types = [["D1", 10],["NA", 50],["Na", 9],["NA", 20],["SD", 13.2]]
            lines = []
            for line in data:
                dte = line[self.sql.genrct_col.index("grt_date")]
                mem = line[self.sql.genrct_col.index("grt_memo")][:50]
                ref = line[self.sql.genrct_col.index("grt_refno")]
                pay = line[self.sql.genrct_col.index("grt_payee")][:20]
                amt = line[self.sql.genrct_col.index("grt_amount")]
                lines.append([dte, mem, ref, pay, amt])
            but = [("Create Import Record", self.doImpRec, True)]
            sc = SChoice(self.opts["mf"], scrn=self.opts["mf"].body,
                titl=titl, head=head, data=lines, typs=types, retn="I",
                mode="S", butt=but)
            if sc.selection is None:
                break
            index = sc.selection                # The record index in data
            self.recon = False
            self.rctupd = False
            self.trndte = data[index][self.sql.genrct_col.index("grt_date")]
            memo = data[index][self.sql.genrct_col.index("grt_memo")]
            self.trnref = data[index][self.sql.genrct_col.index("grt_refno")]
            amount = data[index][self.sql.genrct_col.index("grt_amount")]
            seq = data[index][self.sql.genrct_col.index("grt_seq")]
            if amount < 0:
                self.typ = "P"
                self.glrtn = 2
                self.trnamt = float(ASD(0) - ASD(amount))
            else:
                self.typ = "R"
                self.glrtn = 6
                self.trnamt = amount
            p = self.df.pos
            self.df.loadEntry("C", 1, p, data=self.typ)
            self.df.loadEntry("C", 1, p+1, data=self.trnref)
            self.df.loadEntry("C", 1, p+2, data=self.trndte)
            self.df.loadEntry("C", 1, p+3, data=self.trnamt)
            self.df.loadEntry("C", 1, p+4, data=memo[:30])
            self.df.focusField("C", 1, p+5)
            self.rctvar.set(True)
            self.df.mstFrame.wait_variable(self.rctvar)
            if self.cancel:
                break
            if self.rctupd:
                self.doUpdateRct(seq)
        self.rctimp = False
        self.df.colf[1][4][4] = self.df.colf[1][4][4].replace("(noesc)", "")
        self.df.focusField("C", 1, self.df.col)

    def doImpRec(self, *args):
        coy = (self.opts["conum"], self.opts["conam"])
        args = (self.bh.acc, args[0])
        self.df.setWidget(self.df.mstFrame, state="hide")
        callModule(self.opts["mf"], None, "gl1060", coy=coy, args=args)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doAutoRct(self, date, memo, refno, amount, seq):
        # Automatic Postings and Allocations of unallocated entries
        # Search for rct transactions in gentrn and flag if found
        col = ["glt_seq"]
        sve = [("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
            self.bh.acc), ("glt_recon", "=", 0)]
        # Test with Refno and Amount
        whr = copyList(sve)
        whr.extend([("glt_refno", "=", refno), ("glt_tramt", "=", amount)])
        glt = self.sql.getRec("gentrn", cols=col, where=whr)
        if not glt:
            # Test Date and Amount
            whr = copyList(sve)
            whr.extend([("glt_trdt", "=", date), ("glt_tramt", "=", amount)])
            glt = self.sql.getRec("gentrn", cols=col, where=whr)
            if not glt:
                # Test Amount Only
                whr = copyList(sve)
                whr.append(("glt_tramt", "=", amount))
                glt = self.sql.getRec("gentrn", cols=col, where=whr)
        if glt:
            if len(glt) > 1:
                # More than one transaction found, manually select which one
                get = self.doSelectEntry(date, memo, refno, amount, glt)
                if get is None:
                    return
                glt = [glt[get]]
            # Set recon Flag on gentrn
            self.sql.updRec("gentrn", cols=["glt_recon"],
                data=[int(date / 100)], where=[("glt_seq", "=", glt[0][0])])
            self.doUpdateRct(seq)
            return
        if not amount:
            # Transaction amount is zero
            self.doUpdateRct(seq)
            return
        col = [
            "grc_desc1", "grc_desc2", "grc_desc3", "grc_rtn", "grc_acoy",
            "grc_aacc", "grc_acrs", "grc_achn", "grc_adrs", "grc_aage",
            "grc_vat"]
        whr = [
            ("grc_cono", "=", self.opts["conum"]),
            ("grc_acno", "=", self.bh.acc)]
        if amount < 0:
            whr.append(("grc_rtn", "=", "P"))
        else:
            whr.append(("grc_rtn", "=", "R"))
        codes = self.sql.getRec("genrcc", cols=col, where=whr)
        if codes:
            # There are standard genrcc codes
            if self.bh.multi == "Y":
                self.curdt = int(date / 100)
            else:
                self.curdt = self.bh.curdt
            for desc1, desc2, desc3, trtp, self.allcoy, self.accnum, \
                        acrs, achn, adrs, aage, self.vatcod in codes:
                desc = desc1
                if desc2:
                    desc = "%s %s" % (desc, desc2)
                if desc3:
                    desc = "%s %s" % (desc, desc3)
                self.alldet = CCD(desc, "NA", 30).work
                found = True
                if desc1 not in memo:
                    found = False
                if found and desc2 and desc2 not in memo:
                    found = False
                if found and desc3 and desc3 not in memo:
                    found = False
                if found:
                    # Check Control Details
                    if self.incoac:
                        chk = self.doChkLoadCtls()
                        if chk:
                            found = False
                            break
                    # Code matched, do automatic posting
                    self.trndet = self.alldet
                    if trtp == "P":
                        # Payments
                        othrtn = 5
                        self.glrtn = 2
                        self.vtyp = "I"
                    else:
                        # Receipts
                        othrtn = 2
                        self.glrtn = 6
                        self.vtyp = "O"
                    self.trndte = date
                    self.trnref = refno
                    self.allamt = amount
                    if self.doVatCalc(self.vatcod):
                        self.vatamt = 0
                    data = (self.opts["conum"], self.bh.acc, self.curdt, date,
                        self.glrtn, self.trnref, self.bh.batno, self.allamt,
                        0.00, self.trndet, "", "", int(date / 100),
                        self.opts["capnm"], self.sysdtw, 0)
                    self.sql.insRec("gentrn", data=data)
                    amt = float(ASD(0) - ASD(self.allamt))
                    vat = float(ASD(0) - ASD(self.vatamt))
                    amt = float(ASD(amt) - ASD(vat))
                    self.restDebitCredit(amt, vat)
                    if acrs:
                        amt = float(ASD(0) - ASD(amt))
                        AgeAll(self.opts["mf"], system="crs", agetyp=aage,
                            agekey=[self.allcoy, acrs, othrtn, refno,
                            self.curdt, amt, 0])
                        data = [self.allcoy, acrs, othrtn, refno,
                            self.bh.batno, date, "", amt, 0, 0, self.curdt,
                            0, "", 0, self.trndet, "", "", self.opts["capnm"],
                            self.sysdtw, 0]
                        self.sql.insRec("crstrn", data=data, unique="crt_ref1")
                    elif adrs:
                        AgeAll(self.opts["mf"], system="drs", agetyp=aage,
                            agekey=[self.allcoy, achn, adrs, othrtn, refno,
                            self.curdt, amt, 0])
                        data = [self.allcoy, achn, adrs, othrtn, refno,
                            self.bh.batno, date, "", amt, 0, self.curdt,
                            self.trndet, "", "", self.opts["capnm"],
                            self.sysdtw, 0]
                        self.sql.insRec("drstrn", data=data, unique="drt_ref1")
                    self.doUpdateRct(seq)
                    break

    def doReadRct(self):
        whr = [("grt_cono", "=", self.opts["conum"]), ("grt_acno", "=",
            self.bh.acc), ("grt_flag", "=", "N")]
        start = (self.bh.curdt * 100) + 1
        end = mthendDate(start)
        if self.bh.multi == "N":
            whr.append(("grt_date", "between", start, end))
        else:
            whr.append(("grt_date", "<=", end))
        return self.sql.getRec("genrct", where=whr, order="grt_date")

    def doSelectEntry(self, date, memo, refno, amount, glt):
        # Multiple comparisons found, Select one
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select Transaction")
        date = CCD(date, "D1", 10)
        amount = CCD(amount, "SD", 13.2)
        titl = "Multiple Comparison Entries, Please Select One to Apply"
        head = ("   Date   ", "Reference", "      Amount ", "Details")
        lines = []
        for seq in glt:
            acc = self.sql.getRec("gentrn", cols=["glt_trdt",
                "glt_refno", "glt_tramt", "glt_desc"],
                where=[("glt_seq", "=", seq[0])], limit=1)
            dte = CCD(acc[0], "D1", 10)
            ref = CCD(acc[1], "Na", 9)
            amt = CCD(acc[2], "SD", 13.2)
            des = CCD(acc[3], "NA", 30)
            lines.append([dte.disp, ref.disp, amt.disp, des.disp])
        sc = SChoice(self.opts["mf"], scrn=self.df.mstFrame, titl=titl,
            head=head, data=lines, retn="I", mode="S")
        self.df.enableButtonsTags(state=state)
        return sc.selection

    def doUpdateRct(self, seq):
        # Set genrct grt_flag to Y
        self.sql.updRec("genrct", cols=["grt_flag"], data=["Y"],
            where=[("grt_seq", "=", seq)])
        self.opts["mf"].dbm.commitDbase()

    def doSelections(self):
        recs = getSingleRecords(self.opts["mf"], "gentrn", ("glt_type",
            "glt_trdt", "glt_refno", "glt_tramt", "glt_desc"),
            head=("X", "T", "Trans-Date", "Reference", "Trans-Value",
            "Details"), where=[("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.bh.acc), ("glt_recon", "=", 0)],
            order="glt_trdt, glt_refno")
        if not recs:
            return
        for rec in recs:
            self.seq = rec[self.sql.gentrn_col.index("glt_seq")]
            self.updateRecon()

    def doTrnTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w
        if not self.pcash and not self.dorec:
            return "ok"
        if self.dorec:
            chk = self.doCheckRecords()
            if chk:
                return chk
        if self.typ == "P":
            self.glrtn = 2
        else:
            self.glrtn = 6
        if self.dorec:
            self.df.colf[1][1][8]["where"] = [
                ("glt_cono", "=", self.opts["conum"]),
                ("glt_acno", "=", self.bh.acc),
                ("glt_type", "=", self.glrtn),
                ("glt_recon", "=", 0)]
            try:
                self.df.rs.selection = None
            except:
                pass

    def doCheckRecords(self):
        data = self.doReadRct()
        if data:
            showError(self.opts["mf"].body, "Import Error",
                "Unallocated Records in Previous Bank\n"\
                "           Import File\n\n"\
                "Please Select the 'Process Bank Data'\n"\
                "      Button to Process them")
            return "rf"

    def doView(self, *event):
        self.df.focusField("C", 1, 1)

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        if self.pcash and not w:
            refs = self.sql.getRec("gentrn", cols=["glt_refno"],
                where=[("glt_cono", "=", self.opts["conum"]), ("glt_acno",
                "=", self.conacc),("glt_refno", "like", "PC_______")],
                group="glt_refno", order="glt_refno desc")
            auto = False
            for ref in refs:
                try:
                    w = "PC%07i" % (int(ref[0][2:]) + 1)
                    auto = True
                    break
                except:
                    pass
            if not auto:
                w = "PC0000001"
            self.df.loadEntry(frt, pag, p, data=w)
        self.trnref = w
        if not self.dorec:
            return "ok"
        try:
            rs = self.df.rs.selection
        except:
            rs = None
        if not rs:
            wa = [("glt_type", "=", self.glrtn),
                ("glt_refno", "=", self.trnref)]
            opt = {}
            for k in self.glt:
                if k == "where":
                    opt[k] = copyList(self.glt[k])
                    opt[k].extend(wa)
                elif type(self.glt[k]) == list:
                    opt[k] = copyList(self.glt[k])
                else:
                    opt[k] = self.glt[k]
            rs = self.df.selRecord(1, opt).selection
        if rs:
            self.recon = True
            if self.typ == "P":
                amt = float(ASD(0) - ASD(rs[4]))
            else:
                amt = rs[4]
            self.df.loadEntry(frt, pag, p+1, data=rs[0])
            self.df.loadEntry(frt, pag, p+2, data=amt)
            self.df.loadEntry(frt, pag, p+3, data=rs[5])
            self.seq = rs[3]
            return "nd"
        else:
            self.recon = False

    def doTrnDte(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndte = w

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w
        self.df.colf[2][6][5] = w

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)])
        if not acc:
            return "Invalid Company"
        if self.incoac and w not in self.incoac:
            return "Invalid Company, No Intercompany Record 1"
        self.allcoy = w
        self.allnam = acc[0]
        return self.doChkLoadCtls()

    def doChkLoadCtls(self):
        # Check for Intercompany Records
        if self.allcoy != self.opts["conum"]:
            acc = self.sql.getRec("genint", where=[("cti_cono", "=",
                self.allcoy), ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        # Get Company Details
        ctlmst = self.gc.getCtl("ctlmst", self.allcoy)
        if not ctlmst:
            return "rf"
        # Set Company VAT Default
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
        # Check for Integrated Systems
        mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mod.append(ctlmst["ctm_modules"][x:x+2])
        # Load Ass Integration
        if mod.count("AR"):
            ctl = self.gc.getCtl("assctl", self.allcoy)
            if not ctl:
                return "rf"
            self.ass_gl = ctl["cta_glint"]
        else:
            self.ass_gl = "N"
        # Load Bkm Integration
        if mod.count("BK"):
            ctl = self.gc.getCtl("bkmctl", self.allcoy)
            if not ctl:
                return "rf"
            self.bkm_gl = ctl["cbk_glint"]
        else:
            self.bkm_gl = "N"
        # Load Crs Integration
        if mod.count("CR"):
            ctl = self.gc.getCtl("crsctl", self.allcoy)
            if not ctl:
                return "rf"
            self.crs_gl = ctl["ctc_glint"]
        else:
            self.crs_gl = "N"
        # Load Drs Integration and Chain Store Flag
        if mod.count("DR"):
            ctl = self.gc.getCtl("drsctl", self.allcoy)
            if not ctl:
                return "rf"
            self.drs_gl = ctl["ctd_glint"]
            self.drs_ch = ctl["ctd_chain"]
        else:
            self.drs_gl = "N"
            self.drs_ch = "N"
        # Load Lon Integration
        if mod.count("LN"):
            ctl = self.gc.getCtl("lonctl", self.allcoy)
            if not ctl:
                return "rf"
            self.lon_gl = ctl["cln_glint"]
            self.lon_dr = ctl["cln_drte"]
            self.lon_cr = ctl["cln_crte"]
        else:
            self.lon_gl = "N"
        # Load Mem Integration
        if mod.count("ML"):
            ctl = self.gc.getCtl("memctl", self.allcoy)
            if not ctl:
                return "rf"
            self.mem_gl = ctl["mcm_glint"]
        else:
            self.mem_gl = "N"
        # Load Rca Integration
        if mod.count("RC"):
            ctl = self.gc.getCtl("rcactl", self.allcoy)
            if not ctl:
                return "rf"
            self.rca_gl = ctl["cte_glint"]
        else:
            self.rca_gl = "N"
        # Load Rtl Integration
        if mod.count("RT"):
            ctl = self.gc.getCtl("rtlctl", self.allcoy)
            if not ctl:
                return "rf"
            self.rtl_gl = ctl["ctr_glint"]
        else:
            self.rtl_gl = "N"
        # Load Sln Integration
        if mod.count("SL"):
            ctl = self.gc.getCtl("wagctl", self.allcoy)
            if not ctl:
                return "rf"
            self.sln_gl = ctl["ctw_glint"]
            self.sln_rt = ctl["ctw_i_rate"]
        else:
            self.sln_gl = "N"
        # Check for Control Records e.g. VAT, Crs, Drs and Discounts
        self.ctlctl = self.gc.getCtl("ctlctl", self.allcoy)
        if not self.ctlctl:
            return "rf"
        ctls = ["vat_ctl"]
        if self.glrtn in (2, 3, 6, 7):
            if self.ass_gl == "Y":
                ctls.append("ass_sls")
            if self.bkm_gl == "Y":
                ctls.append("bkm_ctl")
            if self.crs_gl == "Y":
                ctls.extend(["crs_ctl", "dis_rec"])
            if self.drs_gl == "Y":
                ctls.extend(["drs_ctl", "dis_all"])
            if self.lon_gl == "Y":
                ctls.extend(["lon_ctl", "int_pay", "int_rec"])
            if self.mem_gl == "Y":
                ctls.append("mem_ctl")
                if "dis_all" not in ctls:
                    ctls.append("dis_all")
            if self.rca_gl == "Y":
                self.rcactl = []
                for c in ("rca_own", "rca_tnt", "rca_dep"):
                    self.rcactl.append(self.ctlctl[c])
                    ctls.append(c)
            if self.sln_gl == "Y":
                ctls.extend(["wag_slc", "wag_sli"])
        if self.gc.chkRec(self.allcoy, self.ctlctl, ctls):
            return "rf"
        self.convat = self.ctlctl["vat_ctl"]
        # Get for Asset Accounts
        if self.ass_gl == "Y":
            self.assctl = []
            ass = self.sql.getRec("assgrp", cols=["asg_assacc"],
                where=[("asg_cono", "=", self.allcoy)])
            for a in ass:
                self.assctl.append(a[0])
        # Get for Rental Accounts
        if self.rtl_gl == "Y":
            self.rtlctl = []
            rtl = self.sql.getRec("rtlprm", cols=["rtp_rtlacc"],
                where=[("rtp_cono", "=", self.allcoy)])
            for r in rtl:
                self.rtlctl.append(r[0])

    def doAccNum(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Account Number"
        if self.allcoy == self.opts["conum"] and w == self.conacc:
            return "Invalid Number, Same as Control"
        self.others = False
        self.othtot = 0
        self.vattot = 0
        if self.glrtn in (2, 6):
            if self.ass_gl == "Y" and w in self.assctl:
                self.others = "ass"
            elif self.bkm_gl == "Y" and w == self.ctlctl["bkm_ctl"]:
                self.others = "bkm"
            elif self.crs_gl == "Y" and w == self.ctlctl["crs_ctl"]:
                self.others = "crs"
            elif self.drs_gl == "Y" and w == self.ctlctl["drs_ctl"]:
                self.others = "drs"
            elif self.lon_gl == "Y" and w == self.ctlctl["lon_ctl"]:
                self.others = "lon"
            elif self.mem_gl == "Y" and w == self.ctlctl["mem_ctl"]:
                self.others = "mem"
            elif self.rca_gl == "Y" and w in self.rcactl:
                if str(self.rcactl.index(w)) == "0":
                    self.others = "own"
                elif str(self.rcactl.index(w)) == "1":
                    self.others = "tnt"
                else:
                    self.others = "dep"
            elif self.rtl_gl == "Y" and w in self.rtlctl:
                self.others = "rtl"
            elif self.sln_gl == "Y" and w == self.ctlctl["wag_slc"]:
                self.others = "sln"
        if self.others:
            ctl = False
        else:
            ctl = True
        chk = chkGenAcc(self.opts["mf"], self.allcoy, w, ctl=ctl)
        if type(chk) is str:
            return chk
        if self.others:
            # Staff Loans set in endLon, endSln
            if self.glrtn == 2:
                if self.others in ("ass", "lon"):
                    self.othrtn = 1
                elif self.others == "bkm":
                    self.othrtn = 4
                elif self.others == "mem":
                    self.othrtn = 2
                elif self.others in ("own", "tnt", "dep", "rtl"):
                    self.othrtn = 3
                else:
                    self.othrtn = 5
            elif self.others == "bkm":
                self.othrtn = 3
            elif self.others == "mem":
                self.othrtn = 5
            else:
                self.othrtn = 2
        self.accnum = w
        if not chk[2]:
            if chk[3] == "P":
                self.taxgl = self.taxdf
            else:
                self.taxgl = "N"
        else:
            self.taxgl = chk[2]
        self.df.loadEntry(frt, pag, p+1, chk[0])

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if not w:
            w = float(ASD(self.trnamt) - ASD(self.allocated))
            self.df.loadEntry(frt, pag, p, w)
        self.allamt = w
        if self.others:
            self.vatcod = "N"
            self.vatamt = 0
            self.df.loadEntry(frt, pag, p+1, self.vatcod)
            self.df.loadEntry(frt, pag, p+2, self.vatamt)
            return "sk2"
        else:
            self.df.loadEntry(frt, pag, p+1, self.taxgl)

    def doVatCod(self, frt, pag, r, c, p, i, w):
        chk = self.doVatCalc(w)
        if chk:
            return chk
        self.df.loadEntry(frt, pag, p+1, self.vatamt)
        if not self.vatamt:
            return "sk1"

    def doVatCalc(self, code):
        vrte = getVatRate(self.sql, self.opts["conum"], code, self.trndte)
        if vrte is None:
            return "Invalid V.A.T. Code"
        self.vatcod = code
        self.vatamt = round((self.allamt * vrte / (vrte + 100)), 2)

    def doVatAmt(self, frt, pag, r, c, p, i, w):
        if self.allamt < 0 and w > 0:
            self.vatamt = float(ASD(0) - ASD(w))
        elif self.allamt > 0 and w < 0:
            self.vatamt = float(ASD(0) - ASD(w))
        else:
            self.vatamt = w
        self.df.loadEntry(frt, pag, p, data=self.vatamt)

    def doAllDet(self, frt, pag, r, c, p, i, w):
        self.alldet = w

    def endPage1(self):
        self.cancel = False
        self.agecan = False
        self.batupd = False
        if self.dorec and self.recon:
            self.updateRecon()
            self.df.advanceLine(1)
        else:
            self.updateTables(1)
            self.updateBatch()
            if not self.trnamt:
                self.df.advanceLine(1)
            else:
                self.allocated = float(0.0)
                self.df.selPage("Allocation")
                self.df.loadEntry("T", 2, 0, data=self.trnamt)
                self.df.focusField("C", 2, 1)

    def doCancel(self):
        if self.agecan:
            ok = "yes"
        else:
            ok = askQuestion(self.opts["mf"].body, head="Cancel",
                mess="Are You Certain You Want to Cancel This Entry?")
        if ok == "yes":
            self.cancel = True
            self.opts["mf"].dbm.rollbackDbase()
            if self.batupd:
                self.updateBatch(rev=True)
            for pag in range(2, (self.df.pag + 1)):
                self.df.clearFrame("C", pag)
            self.agevar.set(False)
            self.othvar.set(False)
            self.rctvar.set(False)
            row = int((self.df.last[1][1] - 1) / self.df.colq[1])
            col = (row * self.df.colq[1]) + 1
            self.df.selPage("Transaction")
            self.df.focusField("C", 1, col)
        else:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def updateRecon(self):
        if self.bh.multi == "Y":
            acc = self.sql.getRec("gentrn", cols=["glt_curdt"],
                where=[("glt_seq", "=", self.seq)], limit=1)
            curdt = acc[0]
        else:
            curdt = self.bh.curdt
        self.sql.updRec("gentrn", cols=["glt_recon"], data=[curdt],
            where=[("glt_seq", "=", self.seq)])
        self.opts["mf"].dbm.commitDbase()

    def endPage2(self):
        self.updateTables(2)
        if self.others == "ass":
            self.df.selPage("ASS")
            self.allvat = self.vatamt
            bal = float(ASD(self.allamt) - ASD(self.vatamt))
            self.df.loadEntry("T", self.asspag, 0, data=bal)
            self.df.focusField("C", self.asspag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.asspag)
            self.df.selPage("Allocation")
        elif self.others == "bkm":
            self.df.selPage("BKM")
            self.df.loadEntry("T", self.bkmpag, 0, data=self.allamt)
            self.df.focusField("C", self.bkmpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.bkmpag)
            self.df.selPage("Allocation")
        elif self.others == "crs":
            self.df.selPage("CRS")
            self.df.loadEntry("T", self.crspag, 0, data=self.allamt)
            self.df.focusField("C", self.crspag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.crspag)
            self.df.selPage("Allocation")
        elif self.others == "drs":
            if self.drs_ch == "N":
                self.df.colf[self.drspag][0][1] = "OUI"
                self.chain = 0
            else:
                self.df.colf[self.drspag][0][1] = "IUI"
            self.df.selPage("DRS")
            self.df.loadEntry("T", self.drspag, 0, data=self.allamt)
            self.df.focusField("C", self.drspag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.drspag)
            self.df.selPage("Allocation")
        elif self.others == "lon":
            self.df.selPage("LON")
            self.df.loadEntry("T", self.lonpag, 0, data=self.allamt)
            self.df.focusField("C", self.lonpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.lonpag)
            self.df.selPage("Allocation")
        elif self.others == "mem":
            self.df.selPage("MEM")
            self.df.loadEntry("T", self.mempag, 0, data=self.allamt)
            self.df.focusField("C", self.mempag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.mempag)
            self.df.selPage("Allocation")
        elif self.others in ("own", "tnt", "dep"):
            self.df.selPage("RCA")
            self.df.loadEntry("T", self.rcapag, 0, data=self.allamt)
            self.df.focusField("C", self.rcapag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.rcapag)
            self.df.selPage("Allocation")
        elif self.others == "rtl":
            self.df.selPage("RTL")
            self.df.loadEntry("T", self.rtlpag, 0, data=self.allamt)
            self.df.focusField("C", self.rtlpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.rtlpag)
            self.df.selPage("Allocation")
        elif self.others == "sln":
            self.df.selPage("SLN")
            self.df.loadEntry("T", self.slnpag, 0, data=self.allamt)
            self.df.focusField("C", self.slnpag, 1)
            self.othvar.set(True)
            self.df.mstFrame.wait_variable(self.othvar)
            if self.cancel:
                if self.rctimp:
                    self.rctvar.set(False)
                return
            self.df.clearFrame("C", self.slnpag)
            self.df.selPage("Allocation")
        self.allocated = float(ASD(self.allocated) + ASD(self.allamt))
        if self.allocated == self.trnamt:
            self.df.clearFrame("C", 2)
            self.df.selPage("Transaction")
            self.df.advanceLine(1)
            if self.rctimp:
                self.rctupd = True
                self.rctvar.set(False)
            else:
                self.opts["mf"].dbm.commitDbase()
        else:
            bal = float(ASD(self.trnamt) - ASD(self.allocated))
            self.df.loadEntry("T", 2, 0, data=bal)
            self.df.advanceLine(2)

    def updateTables(self, pag):
        if self.bh.multi == "Y":
            self.curdt = int(self.trndte / 100)
        else:
            self.curdt = self.bh.curdt
        if self.glrtn == 1:                          # Sales
            self.rflag = 0
            self.vtyp = "O"
            self.debit(pag)
        elif self.glrtn == 2:                        # Payments
            if self.pcash:
                self.rflag = 0
            else:
                self.conacc = self.bh.acc
                if self.dorec:
                    self.rflag = self.curdt
                elif not self.trnamt:
                    self.rflag = self.curdt
                else:
                    self.rflag = 0
            self.vtyp = "I"
            self.credit(pag)
        elif self.glrtn == 5:                        # Purchases
            self.rflag = 0
            self.vtyp = "I"
            self.credit(pag)
        elif self.glrtn == 6:                        # Receipts
            if self.pcash:
                self.rflag = 0
            else:
                self.conacc = self.bh.acc
                if self.dorec:
                    self.rflag = self.curdt
                elif not self.trnamt:
                    self.rflag = self.curdt
                else:
                    self.rflag = 0
            self.vtyp = "O"
            self.debit(pag)

    def debit(self, pag):
        if pag == 1:
            if self.pcash:
                rtn = 3
            else:
                rtn = self.glrtn
            amt = self.trnamt
            data = (self.opts["conum"], self.conacc, self.curdt, self.trndte,
                rtn, self.trnref, self.bh.batno, amt, 0.00, self.trndet, "",
                "N", self.rflag, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        else:
            amt = float(ASD(0) - (ASD(self.allamt) - ASD(self.vatamt)))
            vat = float(ASD(0) - ASD(self.vatamt))
            self.restDebitCredit(amt, vat)

    def credit(self, pag):
        if pag == 1:
            if self.pcash:
                rtn = 3
            else:
                rtn = self.glrtn
            amt = float(ASD(0) - ASD(self.trnamt))
            data = (self.opts["conum"], self.conacc, self.curdt, self.trndte,
                rtn, self.trnref, self.bh.batno, amt, 0.00, self.trndet, "",
                "N", self.rflag, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        else:
            amt = float(ASD(self.allamt) - ASD(self.vatamt))
            vat = self.vatamt
            self.restDebitCredit(amt, vat)

    def restDebitCredit(self, amt, vat):
        if self.pcash:
            rtn = 3
        else:
            rtn = self.glrtn
        data = (self.allcoy, self.accnum, self.curdt, self.trndte,
            rtn, self.trnref, self.bh.batno, amt, vat, self.alldet,
            self.vatcod, "", 0, self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if self.allcoy != self.opts["conum"]:
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.opts["conum"]), ("cti_inco", "=",
                self.allcoy)], limit=1)[0]
            val = float(ASD(amt) + ASD(vat))
            data = (self.opts["conum"], acc, self.curdt, self.trndte,
                rtn, self.trnref, self.bh.batno, val, 0.00, self.alldet,
                self.vatcod, "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            acc = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.allcoy), ("cti_inco", "=",
                self.opts["conum"])], limit=1)[0]
            val = float(ASD(0) - ASD(amt) - ASD(vat))
            data = (self.allcoy, acc, self.curdt, self.trndte, rtn,
                self.trnref, self.bh.batno, val, 0.00, self.alldet,
                self.vatcod, "", 0, self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
        if self.vatcod:
            if vat:
                data = (self.allcoy, self.convat, self.curdt, self.trndte,
                    rtn, self.trnref, self.bh.batno, vat, 0.00, self.alldet,
                    self.vatcod, "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            data = (self.allcoy, self.vatcod, self.vtyp, self.curdt, "G",
                rtn, self.bh.batno, self.trnref, self.trndte, self.accnum,
                self.alldet, amt, vat, 0,self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("ctlvtf", data=data)

    def doAssGrp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.allcoy), ("asg_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Asset Group (1)"
        self.assgrp = w
        self.depcod = acc[self.sql.assgrp_col.index("asg_depcod")]
        self.assacc = acc[self.sql.assgrp_col.index("asg_assacc")]
        self.depacc = acc[self.sql.assgrp_col.index("asg_depacc")]
        self.expacc = acc[self.sql.assgrp_col.index("asg_expacc")]
        if self.assacc != self.accnum:
            return "Invalid Asset Group (2)"

    def doAssCod(self, frt, pag, r, c, p, i, w):
        self.asscod = w
        self.assbuy = 0
        self.asssel = 0
        cols = ["asm_desc"]
        whr = [("asm_cono", "=", self.allcoy), ("asm_group", "=", self.assgrp),
            ("asm_code", "=", w)]
        acc = self.sql.getRec("assmst", where=whr, cols=cols, limit=1)
        if not acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="New Asset",
                mess="Asset does not exist, Create?")
            if ok == "no":
                return "rf"
            self.doNewAss()
            acc = self.sql.getRec("assmst", where=whr, cols=cols,
                limit=1)
            if not acc:
                return "rf"
            self.newass = True
        else:
            self.newass = False
        pur = self.sql.getRec("asstrn", cols=["ast_date"],
            where=[("ast_cono", "=", self.allcoy), ("ast_group", "=",
            self.assgrp), ("ast_code", "=", w)], limit=1)
        if pur:
            self.assbuy = pur[0]
        sel = self.sql.getRec("asstrn", cols=["ast_date"],
            where=[("ast_cono", "=", self.allcoy), ("ast_group", "=",
            self.assgrp), ("ast_code", "=", w), ("ast_mtyp", "=", 5)],
            limit=1)
        if sel:
            self.asssel = sel[0]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if self.newass:
            self.othmov = 1
            self.df.loadEntry(frt, pag, p+2, data=self.othmov)
            return "sk2"

    def doAssMov(self, frt, pag, r, c, p, i, w):
        if type(w) == list:
            w = w[0] + 1
        # Do some tests to see if not new again or already sold etc.
        if self.glrtn == 2 and w not in (1, 2):
            return "Invalid Choice For Payment"
        if self.glrtn == 6 and w not in (5,):
            return "Invalid Choice For Recipt"
        if w == 1 and self.assbuy:
            return "Asset Already Purchased"
        if w in (2, 5) and self.asssel:
            return "Asset Already Sold"
        if w in (2, 5) and not self.assbuy:
            return "Asset Not Yet Purchased"
        self.df.loadEntry(frt, pag, p, data=w)
        self.othmov = w

    def doAssAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(
                ASD(self.allamt) - ASD(self.vatamt) - ASD(self.othtot))
            self.othvat = float(ASD(self.vatamt) - ASD(self.vattot))
        elif self.vatamt:
            self.othvat = round(((self.othamt / self.allamt) * self.vatamt), 2)
        else:
            self.othvat = 0
        self.df.loadEntry(frt, pag, p, data=self.othamt)
        self.df.loadEntry(frt, pag, p+1, data=self.trndet)

    def doAssDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def endAss(self):
        if self.glrtn == 2:
            self.tramt = self.othamt
            self.vtamt = self.othvat
        else:
            self.tramt = float(ASD(0.0) - ASD(self.othamt))
            self.vtamt = float(ASD(0.0) - ASD(self.othvat))
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        self.vattot = float(ASD(self.vattot) + ASD(self.othvat))
        tot = float(ASD(self.allamt) - ASD(self.vatamt))
        if self.othtot == tot and self.vattot != self.vatamt:
            self.othvat = float(
                ASD(self.othvat) + ASD(self.vatamt) - ASD(self.vattot))
        # Asset Register Transaction
        data = [self.allcoy, self.assgrp, self.asscod, self.othrtn,
            self.trnref, self.bh.batno, self.trndte, self.othmov,
            self.tramt, self.tramt, self.othvat, self.curdt,
            self.alldet, self.vatcod, "", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("asstrn", data=data)
        if self.othmov == 5:
            # Sale of Asset
            # Raise Depreciation
            callModule(self.opts["mf"], None, "ar2030",
                coy=(self.allcoy, self.allnam), period=self.opts["period"],
                user=self.opts["capnm"], args=(self.curdt, self.assgrp,
                self.asscod))
            # Generate Sale
            amt = self.sql.getRec("asstrn", cols=["sum(ast_amt1)"],
                where=[("ast_cono", "=", self.allcoy), ("ast_group", "=",
                self.assgrp), ("ast_code", "=", self.asscod)], limit=1)
            if amt[0]:
                data = [self.opts["conum"], self.ctlctl["ass_sls"],
                    self.curdt, self.trndte, self.glrtn, self.trnref,
                    self.bh.batno, amt[0], 0, self.alldet, "N", "",
                    0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                data[1] = self.accnum
                data[7] = float(ASD(0) - ASD(amt[0]))
                self.sql.insRec("gentrn", data=data)
        if self.othtot != tot:
            bal = float(ASD(self.allamt) - ASD(self.vatamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.asspag, 0, data=bal)
            self.df.advanceLine(self.tagp["AR"])
        else:
            self.othvar.set(False)

    def doNewAss(self):
        tit = ("Create New Asset", )
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.allcoy)]}
        self.fld = (
            (("T",0,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",0,1,0),"INa",3,"Dep Code","Depreciation Code",
                self.depcod,"N",self.doNewADep,dep,None,("notblank",)),
            (("T",0,1,0),"ONA",27,""))
        tnd = ((self.doNewAEnd,"N"), )
        txt = (self.doNewAXit, )
        state = self.df.disableButtonsTags()
        self.na = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=self.fld, tend=tnd, txit=txt)
        self.na.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doNewADep(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("assdep", cols=["asd_desc"],
            where=[("asd_cono", "=", self.allcoy), ("asd_code", "=", w)],
            limit=1)
        if not chk:
            return "Invalid Depreciation Code"
        self.na.loadEntry(frt, pag, p+1, data=chk[0])

    def doNewAEnd(self):
        dat = [self.allcoy, self.assgrp, self.asscod]
        dat.append(self.na.t_work[0][0][0])
        dat.append(self.na.t_work[0][0][1])
        self.sql.insRec("assmst", data=dat)
        self.doNewAXit()

    def doNewAXit(self):
        self.na.closeProcess()

    def doBkmNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["bkmmst", "bkmcon"], cols=["bkm_value",
            "bkc_sname", "bkc_names"], where=[("bkm_cono", "=", self.allcoy),
            ("bkm_number", "=", w), ("bkc_cono=bkm_cono",),
            ("bkc_ccode=bkm_ccode",)], limit=1)
        if not acc:
            return "Invalid Booking Number (1)"
        self.bkmnum = w
        self.bkmval = acc[0]
        if acc[2]:
            name = "%s, %s" % (acc[1], acc[2].split()[0])
        else:
            name = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=name)

    def doBkmAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(
                ASD(self.allamt) - ASD(self.vatamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

    def endBkm(self):
        if self.glrtn == 6:
            tramt = float(ASD(0.0) - ASD(self.othamt))
        else:
            tramt = self.othamt
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        # Bookings Ledger Transaction
        data = [self.allcoy, self.bkmnum, self.othrtn, self.trnref,
            self.bh.batno, self.trndte, tramt, 0, self.curdt, self.alldet,
            "", "", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("bkmtrn", data=data)
        # Check and Update Status
        trn = self.sql.getRec("bkmtrn", cols=["sum(bkt_tramt)"],
            where=[("bkt_cono", "=", self.allcoy), ("bkt_number", "=",
            self.bkmnum), ("bkt_type", "<>", 1)], limit=1)
        if not trn[0]:
            bal = CCD(0, "SD", 13.2).work
        else:
            bal = CCD(trn[0], "SD", 13.2).work
        if not bal or bal == float(ASD(0) - ASD(self.bkmval)):
            state = "S"
        elif bal == self.bkmval:
            state = "Q"
        else:
            state = "C"
        self.sql.updRec("bkmmst", cols=["bkm_state"], data=[state],
            where=[("bkm_cono", "=", self.allcoy), ("bkm_number", "=",
            self.bkmnum)])
        if self.othtot != self.allamt:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.bkmpag, 0, data=bal)
            self.df.advanceLine(self.tagp["BK"])
        else:
            self.othvar.set(False)

    def doCrsAcc(self, frt, pag, r, c, p, i, w):
        self.othacno = w
        acc = self.sql.getRec("crsmst", cols=["crm_name", "crm_stat"],
            where=[("crm_cono", "=", self.allcoy), ("crm_acno", "=",
            self.othacno)], limit=1)
        if not acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="New Creditor",
                mess="Account does not exist, Create?")
            if ok == "no":
                return "rf"
            self.doNewCrs()
            acc = self.sql.getRec("crsmst", cols=["crm_name"],
                where=[("crm_cono", "=", self.allcoy), ("crm_acno", "=",
                self.othacno)], limit=1)
            if not acc:
                return "rf"
        elif acc[1] == "X":
            return "Invalid Account, Redundant"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.allref = self.trnref

    def doCrsRef(self, frt, pag, r, c, p, i, w):
        self.othref = w

    def doCrsDis(self, frt, pag, r, c, p, i, w):
        self.othdis = w

    def doCrsAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        totamt = float(ASD(self.othamt) + ASD(self.othdis))
        self.df.loadEntry(frt, pag, p+1, data=totamt)

    def doNewCrs(self):
        callModule(self.opts["mf"], self.df, "cr1010", coy=(self.allcoy,
            self.allnam), period=None, user=self.opts["capnm"],
            args=self.othacno)

    def doDrsChn(self, frt, pag, r, c, p, i, w):
        self.chain = w

    def doDrsAcc(self, frt, pag, r, c, p, i, w):
        self.othacno = w
        acc = self.sql.getRec("drsmst", cols=["drm_name", "drm_stat"],
            where=[("drm_cono", "=", self.allcoy), ("drm_chain", "=",
            self.chain), ("drm_acno", "=", self.othacno)], limit=1)
        if not acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="New Debtor",
                mess="Account does not exist, Create?")
            if ok == "no":
                return "rf"
            self.doNewDrs()
            acc = self.sql.getRec("drsmst", cols=["drm_name"],
                where=[("drm_cono", "=", self.allcoy), ("drm_chain", "=",
                self.chain), ("drm_acno", "=", self.othacno)], limit=1)
            if not acc:
                return "rf"
        elif acc[1] == "X":
            return "Invalid Account, Redundant"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.allref = self.trnref

    def doDrsRef(self, frt, pag, r, c, p, i, w):
        self.othref = w

    def doDrsDis(self, frt, pag, r, c, p, i, w):
        self.othdis = w

    def doDrsAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        totamt = float(ASD(self.othamt) + ASD(self.othdis))
        self.df.loadEntry(frt, pag, p+1, data=totamt)

    def doNewDrs(self):
        callModule(self.opts["mf"], self.df, "dr1010", coy=(self.allcoy,
            self.allnam), period=None, user=self.opts["capnm"],
            args=(self.chain, self.othacno))

    def doLonAcc(self, frt, pag, r, c, p, i, w):
        newacc = False
        if not w and self.glrtn == 2:
            yn = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Account?", default="no")
            if yn == "no":
                return "Invalid Account Number"
            newacc = True
            w = callModule(self.opts["mf"], self.df, "ln1010",
                coy=(self.allcoy, self.allnam), user=self.opts["capnm"],
                args="auto", ret="acno")
            self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.allcoy),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.lonacc = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if newacc:
            self.lonnum = 1
            self.newlon = True
            self.df.loadEntry(frt, pag, p+2, data=self.lonnum)
            return "sk2"

    def doLonNum(self, frt, pag, r, c, p, i, w):
        self.newlon = False
        if not w and self.glrtn == 2:
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newlon = True
                self.lonnum = getNextCode(self.sql, "lonmf2", "lm2_loan",
                    where=[("lm2_cono", "=", self.allcoy), ("lm2_acno",
                    "=", self.lonacc)], start=1, last=9999999)
                self.df.loadEntry(frt, pag, p, data=self.lonnum)
            else:
                return "Invalid Loan Number"
        else:
            self.lonmf2 = self.sql.getRec("lonmf2", where=[("lm2_cono",
                "=", self.allcoy), ("lm2_acno", "=", self.lonacc),
                ("lm2_loan", "=", w)], limit=1)
            if not self.lonmf2:
                return "Invalid Loan Number"
            self.lonnum = w
            self.londes = self.lonmf2[self.sql.lonmf2_col.index("lm2_desc")]
            self.londat = self.lonmf2[self.sql.lonmf2_col.index("lm2_start")]
            self.lonmth = self.lonmf2[self.sql.lonmf2_col.index("lm2_pmths")]
            self.lonpay = self.lonmf2[self.sql.lonmf2_col.index("lm2_repay")]
            if self.lonmth and self.glrtn == 2:
                return "Invalid Entry, Fixed Loan"
            self.df.loadEntry(frt, pag, p+1, data=self.londes)
            return "sk1"

    def doLonDes(self, frt, pag, r, c, p, i, w):
        self.londes = w

    def doLonAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(
                ASD(self.allamt) - ASD(self.vatamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        if self.glrtn == 6 or not self.newlon:
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "nd"

    def doLonDri(self, frt, pag, r, c, p, i, w):
        self.newdri = w

    def doLonCri(self, frt, pag, r, c, p, i, w):
        self.newcri = w

    def doLonMth(self, frt, pag, r, c, p, i, w):
        self.lonmth = w
        if self.lonmth:
            rte = (self.newdri / 1200.0)
            self.lonpay = round(((self.othamt * rte) * ((1 + rte) ** w)) /
                (((1 + rte) ** w) - 1), 2)
        else:
            self.lonpay = 0
        self.df.loadEntry(frt, pag, p+1, data=self.lonpay)

    def endLon(self):
        if self.glrtn == 6:
            tramt = float(ASD(0.0) - ASD(self.othamt))
        else:
            tramt = self.othamt
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.newlon:
            # Loans Rate
            self.sql.insRec("lonrte", data=[self.allcoy, self.lonacc,
                self.lonnum, self.trndte, self.newdri, self.newcri])
            # Loans Ledger Masterfile
            self.sql.insRec("lonmf2", data=[self.allcoy, self.lonacc,
                self.lonnum, self.londes, self.trndte, self.lonmth,
                self.lonpay, 0])
        # Loans Ledger Transaction
        data = [self.allcoy, self.lonacc, self.lonnum, self.bh.batno,
            self.othrtn, self.trndte, self.trnref, tramt, self.curdt,
            self.alldet, "", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("lontrn", data=data)
        if self.othtot != self.allamt:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.lonpag, 0, data=bal)
            self.df.advanceLine(self.tagp["LN"])
        else:
            self.othvar.set(False)

    def doMemAcc(self, frt, pag, r, c, p, i, w):
        self.othacno = w
        acc = self.sql.getRec("memmst", cols=["mlm_surname",
            "mlm_names"], where=[("mlm_cono", "=", self.allcoy),
            ("mlm_memno", "=", self.othacno)], limit=1)
        if not acc:
            return "Invalid Member Number"
        self.name = "%s, %s" % (acc[0], acc[1])
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        self.allref = self.trnref

    def doMemDis(self, frt, pag, r, c, p, i, w):
        self.othdis = w

    def doMemAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        totamt = float(ASD(self.othamt) + ASD(self.othdis))
        self.df.loadEntry(frt, pag, p+1, data=totamt)

    def doRcaPrm(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["rcaprm", "rcaowm"], cols=["rcp_desc",
            "rcp_owner", "rom_name"], where=[("rcp_cono", "=", self.allcoy),
            ("rcp_code", "=", w), ("rom_cono=rcp_cono",),
            ("rom_acno=rcp_owner",)], limit=1)
        if not acc:
            return "Invalid Premises Code"
        self.rcaprm = w
        self.rcaown = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.df.loadEntry(frt, pag, p+2, data=acc[1])
        self.df.loadEntry(frt, pag, p+3, data=acc[2])
        if self.others == "own":
            self.rcatnt = 0
            return "sk7"

    def doRcaTnt(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcatnm", cols=["rtn_name"],
            where=[("rtn_cono", "=", self.allcoy), ("rtn_owner",
            "=", self.rcaown), ("rtn_code", "=", self.rcaprm),
            ("rtn_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Tenant"
        self.rcatnt = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        con = self.sql.getRec("rcacon", where=[("rcc_cono", "=",
            self.allcoy), ("rcc_owner", "=", self.rcaown), ("rcc_code", "=",
            self.rcaprm), ("rcc_acno", "=", self.rcatnt)], order="rcc_cnum")
        if not con:
            return "No Valid Contracts"
        self.rcacon = con[-1:][0][4]
        self.df.loadEntry(frt, pag, p+2, data=self.rcacon)

    def doRcaCon(self, frt, pag, r, c, p, i, w):
        con = self.sql.getRec("rcacon", where=[("rcc_cono", "=",
            self.allcoy), ("rcc_owner", "=", self.rcaown), ("rcc_code", "=",
            self.rcaprm), ("rcc_acno", "=", self.rcatnt), ("rcc_cnum", "=",
            w)], limit=1)
        if not con:
            return "Invalid Contract Sequence"
        self.rcacon = w
        if self.others == "dep":
            self.rcatyp = 2
            self.df.loadEntry(frt, pag, p+1, data=self.rcatyp)
            return "sk1"

    def doRcaTyp(self, frt, pag, r, c, p, i, w):
        self.rcatyp = w

    def doRcaAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

    def doRcaDet(self, frt, pag, r, c, p, i, w):
        self.alldet = w

    def endRca(self):
        if self.glrtn == 6:
            tramt = float(ASD(0.0) - ASD(self.othamt))
        else:
            tramt = self.othamt
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if not self.rcatnt:
            # Owners Transaction
            data = [self.allcoy, self.rcaown, self.othrtn, self.trnref,
                self.bh.batno, self.trndte, tramt, 0, self.curdt, self.alldet,
                "N", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcaowt", data=data)
        else:
            # Tenants Transaction
            data = [self.allcoy, self.rcaown, self.rcaprm, self.rcatnt,
                self.rcacon, self.othrtn, self.trnref, self.bh.batno,
                self.trndte, self.rcatyp, tramt, 0, self.curdt, self.alldet,
                "N", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcatnt", data=data)
        if self.othtot != self.allamt:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.rcapag, 0, data=bal)
            self.df.advanceLine(self.tagp["RC"])
        else:
            self.othvar.set(False)

    def doRtlPrm(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlprm", cols=["rtp_desc"],
            where=[("rtp_cono", "=", self.allcoy), ("rtp_code", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Premises Code"
        self.rtlprm = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doRtlAcc(self, frt, pag, r, c, p, i, w):
        self.othacno = w
        acc = self.sql.getRec("rtlmst", cols=["rtm_name"],
            where=[("rtm_cono", "=", self.allcoy), ("rtm_code",
            "=", self.rtlprm), ("rtm_acno", "=", self.othacno)],
            limit=1)
        if not acc:
            ok = askQuestion(screen=self.opts["mf"].body, head="New Contract",
                mess="Account does not exist, Create?")
            if ok == "no":
                return "rf"
            self.doNewRtl()
            acc = self.sql.getRec("rtlmst", cols=["rtm_name"],
                where=[("rtm_cono", "=", self.allcoy), ("rtm_code", "=",
                self.rtlprm), ("rtm_acno", "=", self.othacno)], limit=1)
            if not acc:
                return "rf"
        self.othacno = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.allcoy), ("rtc_code", "=", self.rtlprm), ("rtc_acno", "=",
            self.othacno)], order="rtc_cnum")
        if not con:
            return "No Valid Contracts"
        self.rtlcon = con[-1:][0][3]
        self.df.loadEntry(frt, pag, p+2, data=self.rtlcon)

    def doRtlCon(self, frt, pag, r, c, p, i, w):
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.allcoy), ("rtc_code", "=", self.rtlprm), ("rtc_acno", "=",
            self.othacno), ("rtc_cnum", "=", w)], limit=1)
        if not con:
            return "Invalid Contract Sequence"
        self.rtlcon = w

    def doRtlAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

    def doRtlDet(self, frt, pag, r, c, p, i, w):
        self.alldet = w

    def doNewRtl(self):
        callModule(self.opts["mf"], self.df, "rt1010", coy=(self.allcoy,
            self.allnam), period=None, user=self.opts["capnm"],
            args=(self.rtlprm, self.othacno))

    def endRtl(self):
        if self.glrtn == 6:
            tramt = float(ASD(0.0) - ASD(self.othamt))
        else:
            tramt = self.othamt
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        # Rental Ledger Transaction
        data = [self.allcoy, self.rtlprm, self.othacno, self.rtlcon,
            self.othrtn, self.trnref, self.bh.batno, self.trndte, tramt,
            0, self.curdt, self.alldet, "N", "", self.opts["capnm"],
            self.sysdtw, 0]
        self.sql.insRec("rtltrn", data=data)
        if self.othtot != self.allamt:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.rtlpag, 0, data=bal)
            self.df.advanceLine(self.tagp["RT"])
        else:
            self.othvar.set(False)

    def doSlnEmp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
            where=[("wgm_cono", "=", self.allcoy), ("wgm_empno", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.empnum = w
        empnam = "%s, %s" % (acc[0], acc[1].split()[0])
        self.df.loadEntry(frt, pag, p+1, data=empnam)
        chk = self.sql.getRec("waglmf", where=[("wlm_cono", "=",
            self.opts["conum"]), ("wlm_empno", "=", self.empnum)])
        if len(chk) == 1:
            acc = chk[0]
            self.newsln = False
            self.doLoadLoan(acc)
            self.df.loadEntry(frt, pag, p+2, data=self.slnnum)
            self.df.loadEntry(frt, pag, p+3, data=self.slndes)
            return "sk3"

    def doSlnNum(self, frt, pag, r, c, p, i, w):
        if not w:
            if self.glrtn == 6:
                return "Invalid Loan"
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newsln = True
                self.slnnum = getNextCode(self.sql, "waglmf", "wlm_loan",
                    where=[("wlm_cono", "=", self.allcoy), ("wlm_empno",
                    "=", self.empnum)], start=1, last=99999)
                self.df.loadEntry(frt, pag, p, data=self.slnnum)
            else:
                return "Invalid Loan"
        else:
            acc = self.sql.getRec("waglmf", where=[("wlm_cono",
                "=", self.allcoy), ("wlm_empno", "=", self.empnum),
                ("wlm_loan", "=", w)], limit=1)
            if not acc:
                return "Loan Does Not Exist"
            self.newsln = False
            self.doLoadLoan(acc)
            self.df.loadEntry(frt, pag, p+1, data=self.slndes)
            return "sk1"

    def doLoadLoan(self, acc):
        self.slnnum = acc[self.sql.waglmf_col.index("wlm_loan")]
        self.slndes = acc[self.sql.waglmf_col.index("wlm_desc")]
        self.slncod = acc[self.sql.waglmf_col.index("wlm_code")]
        self.slnrte = acc[self.sql.waglmf_col.index("wlm_rate")]
        self.slnded = acc[self.sql.waglmf_col.index("wlm_repay")]

    def doSlnDes(self, frt, pag, r, c, p, i, w):
        self.slndes = w

    def doSlnAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(
                ASD(self.allamt) - ASD(self.vatamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        if self.glrtn == 6:
            return "nd"
        if not self.newsln:
            self.df.loadEntry(frt, pag, p+1, data=self.slncod)

    def doSlnCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagedc", cols=["ced_desc"],
            where=[("ced_cono", "=", self.allcoy), ("ced_type",
            "=", "D"), ("ced_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.slncod = w
        if not self.newsln:
            self.slnrte = 0
            self.slnded = 0
            self.df.loadEntry(frt, pag, p+2, data=0)
            self.df.loadEntry(frt, pag, p+3, data=0)
            return "nd"
        self.df.loadEntry(frt, pag, p+2, data=self.slnrte)

    def doSlnInt(self, frt, pag, r, c, p, i, w):
        self.slnrte = w
        if not self.newsln:
            self.df.loadEntry(frt, pag, p+2, data=self.slnded)

    def doSlnDed(self, frt, pag, r, c, p, i, w):
        self.slnded = w

    def endSln(self):
        if self.glrtn == 6:
            tramt = float(ASD(0.0) - ASD(self.othamt))
        else:
            tramt = self.othamt
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.newsln:
            # Staff Loans Ledger Masterfile
            self.othrtn = 2
            cap = self.othamt
            self.sql.insRec("waglmf", data=[self.allcoy, self.empnum,
                self.slnnum, self.slndes, self.slncod, self.slnrte,
                self.trndte, self.slnded])
        else:
            # Staff Loans Ledger Masterfile
            self.sql.updRec("waglmf", cols=["wlm_rate"], data=[self.slnrte],
                where=[("wlm_cono", "=", self.allcoy), ("wlm_empno", "=",
                self.empnum), ("wlm_loan", "=", self.slnnum)])
            if self.glrtn == 6:
                self.othrtn = 4
                cap = 0.00
            else:
                self.othrtn = 3
                cap = tramt
        # Staff Loans Ledger Transaction
        data = [self.allcoy, self.empnum, self.slnnum, self.bh.batno,
            self.othrtn, self.trndte, self.trnref, tramt, cap, self.slnded,
            self.slnrte, self.curdt, self.alldet, "", self.opts["capnm"],
            self.sysdtw, 0]
        self.sql.insRec("wagltf", data=data)
        if self.othtot != self.allamt:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.slnpag, 0, data=bal)
            self.df.advanceLine(self.tagp["SL"])
        else:
            self.othvar.set(False)

    def endCrsDrsMem(self):
        found = False
        if self.others == "crs" and self.glrtn == 2:
            found = True
        elif self.others in ("drs", "mem") and self.glrtn == 6:
            found = True
        if found:
            self.tramt = float(ASD(0.0) - ASD(self.othamt))
            self.dsamt = float(ASD(0.0) - ASD(self.othdis))
        else:
            self.tramt = self.othamt
            self.dsamt = self.othdis
        # Age Transaction
        state = self.df.disableButtonsTags(tags=False)
        self.opts["mf"].updateStatus("Choose an Ageing Option")
        if len(self.but) == 5:
            self.beg = 0
        elif len(self.but) == 8:
            self.beg = 4
        for b in range(self.beg, (self.beg + 4)):
            wid = getattr(self.df, "B%s" % b)
            self.df.setWidget(wid, "normal")
        wid = getattr(self.df, "B%s" % self.beg)
        self.df.setWidget(wid, "focus")
        self.agevar.set(True)
        self.df.mstFrame.wait_variable(self.agevar)
        self.df.enableButtonsTags(state=state)
        if self.agecan:
            self.doCancel()
            return
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.others == "crs":
            # Creditors Ledger Transaction
            data = [self.allcoy, self.othacno, self.othrtn, self.allref,
                self.bh.batno, self.trndte, self.othref, self.tramt,
                self.vatamt, 0, self.curdt, 0, "Y", 0, self.alldet,
                self.vatcod, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("crstrn", data=data, unique="crt_ref1")
            if self.dsamt:
                # Creditors Ledger Transaction
                data[2] = 6
                data[7] = self.dsamt
                data[8] = 0
                self.sql.insRec("crstrn", data=data, unique="crt_ref1")
                # General Ledger Discount Received
                data = (self.allcoy, self.ctlctl["dis_rec"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, self.dsamt,
                    0, self.alldet, "", "", 0, self.opts["capnm"],
                    self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                # General Ledger Creditors Control
                dis = float(ASD(0.0) - ASD(self.dsamt))
                data = (self.allcoy, self.ctlctl["crs_ctl"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, dis, 0,
                    self.trndet, "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            if self.othtot != self.allamt:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.crspag, 0, data=bal)
                self.df.advanceLine(self.tagp["CR"])
            else:
                self.othvar.set(False)
        elif self.others == "drs":
            # Debtors Ledger Transaction
            data = [self.allcoy, self.chain, self.othacno, self.othrtn,
                self.allref, self.bh.batno, self.trndte, self.othref,
                self.tramt, self.vatamt, self.curdt, self.alldet,
                self.vatcod, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("drstrn", data=data, unique="drt_ref1")
            if self.dsamt:
                # Debtors Ledger Transaction
                data[3] = 6
                data[8] = self.dsamt
                data[9] = 0
                self.sql.insRec("drstrn", data=data, unique="drt_ref1")
                # General Ledger Debtors Control
                data = (self.allcoy, self.ctlctl["drs_ctl"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, self.dsamt,
                    0, self.alldet, "", "", 0, self.opts["capnm"],
                    self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                # General Ledger Discount Allowed
                dis = float(ASD(0.0) - ASD(self.dsamt))
                data = (self.allcoy, self.ctlctl["dis_all"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, dis, 0,
                    self.trndet, "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            if self.othtot != self.allamt:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.drspag, 0, data=bal)
                self.df.advanceLine(self.tagp["DR"])
            else:
                self.othvar.set(False)
        elif self.others == "mem":
            # Members Ledger Transaction
            data = [self.allcoy, self.othacno, self.othrtn, self.allref,
                self.bh.batno, self.trndte, self.tramt, self.vatamt,
                self.curdt, "", 0, self.alldet, self.vatcod, "",
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("memtrn", data=data, unique="mlt_refno")
            if self.dsamt:
                # Members Ledger Transaction
                data[2] = 6
                data[6] = self.dsamt
                data[7] = 0
                self.sql.insRec("memtrn", data=data, unique="mlt_refno")
                # General Ledger Members Control
                data = (self.allcoy, self.ctlctl["mem_ctl"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, self.dsamt,
                    0, self.alldet, "", "", 0, self.opts["capnm"],
                    self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
                # General Ledger Discount Allowed
                dis = float(ASD(0.0) - ASD(self.dsamt))
                data = (self.allcoy, self.ctlctl["dis_all"], self.curdt,
                    self.trndte, 4, self.allref, self.bh.batno, dis, 0,
                    self.trndet, "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            if self.othtot != self.allamt:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.mempag, 0, data=bal)
                self.df.advanceLine(self.tagp["ML"])
            else:
                self.othvar.set(False)

    def doAgeNormal(self):
        self.doAgeing("N")

    def doAgeHistory(self):
        self.doAgeing("H")

    def doAgeAuto(self):
        self.doAgeing("O")

    def doAgeCurrent(self):
        self.doAgeing("C")

    def doAgeing(self, atype):
        # Disable All Ageing Buttons
        for b in range(self.beg, (self.beg + 4)):
            wid = getattr(self.df, "B%s" % b)
            self.df.setWidget(wid, "disabled")
        if self.others == "crs":
            age = AgeAll(self.opts["mf"], system="crs", agetyp=atype,
                agekey=[self.allcoy, self.othacno, self.othrtn, self.allref,
                self.curdt, self.tramt, self.dsamt])
        elif self.others == "drs":
            age = AgeAll(self.opts["mf"], system="drs", agetyp=atype,
                agekey=[self.allcoy, self.chain, self.othacno, self.othrtn,
                self.allref, self.curdt, self.tramt, self.dsamt])
        elif self.others == "mem":
            age = AgeAll(self.opts["mf"], system="mem", agetyp=atype,
                agekey=[self.allcoy, self.othacno, self.othrtn, self.allref,
                self.curdt, self.tramt, self.dsamt])
        self.agecan = age.cancel
        self.agevar.set(False)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty = self.bh.batqty - 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.trnamt))
        else:
            self.batupd = True
            self.bh.batqty = self.bh.batqty + 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.trnamt))
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def exitPage1(self):
        if not self.rctimp:
            self.df.closeProcess()
            if not self.dorec:
                self.bh.doBatchTotal()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
