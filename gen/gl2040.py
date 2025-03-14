"""
SYNOPSIS
    General Ledger Journal Entries.

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
from TartanClasses import ASD, Batches, CCD, FileImport, GetCtl
from TartanClasses import ProgressBar, PwdConfirm, SplashScreen, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askQuestion, callModule, chkGenAcc, getNextCode
from tartanFunctions import getVatRate, showError

class gl2040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Company Record
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.allcoy = self.opts["conum"]
        self.allnam = self.opts["conam"]
        # Get Enabled Modules
        tabs = ["ctlctl", "ctlmst", "ctlpwu", "ctlvmf", "ctlvrf", "ctlvtf",
            "genint", "genmst", "gentrn"]
        mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mod.append(ctlmst["ctm_modules"][x:x+2])
        # Load Control Accounts
        self.tags = [("Transaction", None, None, None, False)]
        self.tagp = {}
        page = 1
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
                tabs.extend(["crsmst", "crstrn"])
                self.tags.append(("CRS", None, None, None, False))
                page += 1
                self.tagp["CR"] = page
        if mod.count("DR"):
            ctl = self.gc.getCtl("drsctl", self.opts["conum"])
            if not ctl:
                return
            if ctl["ctd_glint"] == "Y":
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
        # Batch Header
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "GEN",
            self.opts["rtn"], multi=None)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        # Other
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][1][0] / 100)
        self.importing = False
        return True

    def doProcess(self):
        lst = {
            "stype": "R",
            "tables": ("gentrn",),
            "cols": (
                ("glt_acno", "", 0, "Acc-Num"),
                ("glt_refno", "", 0, "Ref-Num"),
                ("glt_trdt", "", 0, "   Date"),
                ("glt_tramt", "", 0, "      Amount")),
            "where": [
                ("glt_cono", "=", self.opts["conum"]),
                ("glt_type", "=", self.opts["rtn"]),
                ("glt_batch", "=", self.bh.batno),
                ("glt_batind", "<>", "")],
            "order": "glt_refno"}
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "whera": [["C", "glm_cono", 2, 1]]}
        if "AR" in self.tagp:
            asg = {
                "stype": "R",
                "tables": ("assgrp",),
                "cols": (
                    ("asg_group", "", 0, "Grp"),
                    ("asg_desc", "", 0, "Description", "Y")),
                "whera": [("C", "asg_cono", 2, 1)]}
            asm = {
                "stype": "R",
                "tables": ("assmst",),
                "cols": (
                    ("asm_code", "", 0, "Cod-Num"),
                    ("asm_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "asm_cono", 2, 1),
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
                "whera": [("C", "bkm_cono", 2, 1)]}
        if "CR" in self.tagp:
            crm = {
                "stype": "R",
                "tables": ("crsmst",),
                "cols": (
                    ("crm_acno", "", 0, "Acc-Num"),
                    ("crm_name", "", 0, "Name", "Y")),
                "where": [("crm_stat", "<>", "X")],
                "whera": [("C", "crm_cono", 2, 1)]}
        if "DR" in self.tagp:
            chn = {
                "stype": "R",
                "tables": ("drschn",),
                "cols": (
                    ("chm_chain", "", 0, "Num"),
                    ("chm_name", "", 0, "Name", "Y")),
                "whera": [("C", "chm_cono", 2, 1)]}
            drm = {
                "stype": "R",
                "tables": ("drsmst",),
                "cols": (
                    ("drm_acno", "", 0, "Acc-Num"),
                    ("drm_name", "", 0, "Name", "Y"),
                    ("drm_add1", "", 0, "Address Line 1")),
                "where": [("drm_stat", "<>", "X")],
                "whera": [
                    ("C", "drm_cono", 2, 1),
                    ("C", "drm_chain", 0, self.tagp["DR"])]}
        if "LN" in self.tagp:
            lm1 = {
                "stype": "R",
                "tables": ("lonmf1",),
                "cols": (
                    ("lm1_acno", "", 0, "Acc-Num"),
                    ("lm1_name", "", 0, "Name", "Y")),
                "whera": [("C", "lm1_cono", 2, 1)]}
            lm2 = {
                "stype": "R",
                "tables": ("lonmf2",),
                "cols": (
                    ("lm2_loan", "", 0, "Ln"),
                    ("lm2_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "lm2_cono", 2, 1),
                    ("C", "lm2_acno", 0, self.tagp["LN"])]}
        if "ML" in self.tagp:
            mlm = {
                "stype": "R",
                "tables": ("memmst",),
                "cols": (
                    ("mlm_memno", "", 0, "Mem-No"),
                    ("mlm_surname", "", 0, "Surname", "Y"),
                    ("mlm_names", "", 0, "Names")),
                "whera": [("C", "mlm_cono", 2, 1)]}
        if "RC" in self.tagp:
            rcp = {
                "stype": "R",
                "tables": ("rcaprm",),
                "cols": (
                    ("rcp_code", "", 0, "Pr-Code"),
                    ("rcp_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "rcp_cono", 2, 1)]}
            rct = {
                "stype": "R",
                "tables": ("rcatnm",),
                "cols": (
                    ("rtn_acno", "", 0, "Cod-Num"),
                    ("rtn_name", "", 0, "Name", "Y")),
                "whera": [
                    ("C", "rtn_cono", 2, 1),
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
                    ("C", "rcc_cono", 2, 1),
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
            prm = {
                "stype": "R",
                "tables": ("rtlprm",),
                "cols": (
                    ("rtp_code", "", 0, "Pr-Code"),
                    ("rtp_desc", "", 0, "Description", "Y")),
                "whera": [("C", "rtp_cono", 2, 1)]}
            rtm = {
                "stype": "R",
                "tables": ("rtlmst",),
                "cols": (
                    ("rtm_acno", "", 0, "Cod-Num"),
                    ("rtm_name", "", 0, "Name", "Y")),
                "whera": [
                    ("C", "rtm_cono", 2, 1),
                    ("C", "rtm_code", 0, self.tagp["RT"])]}
            con = {
                "stype": "R",
                "tables": ("rtlcon",),
                "cols": (
                    ("rtc_cnum", "", 0, "Cod-Num"),
                    ("rtc_payind", "", 0, "F"),
                    ("rtc_start", "", 0, "Start-Date"),
                    ("rtc_period", "", 0, "Per")),
                "whera": [
                    ("C", "rtc_cono", 2, 1),
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
                "whera": [("C", "wgm_cono", 2, 1)]}
            lmf = {
                "stype": "R",
                "tables": ("waglmf",),
                "cols": (
                    ("wlm_loan", "", 0, "Ln"),
                    ("wlm_desc", "", 0, "Description", "Y")),
                "whera": [
                    ("C", "wlm_cono", 2, 1),
                    ("C", "wlm_empno", 0, self.tagp["SL"])]}
            ced = {
                "stype": "R",
                "tables": ("wagedc",),
                "cols": (
                    ("ced_type", "", 0, "T"),
                    ("ced_code", "", 0, "Cde"),
                    ("ced_desc", "", 0, "Description", "Y")),
                "where": [("ced_type", "=", "D")],
                "whera": [("C", "ced_cono", 2, 1)],
                "index": 1}
        vat = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "whera": [["C", "vtm_cono", 2, 1]]}
        self.fld = [
            (("T",0,0,0),"OUI",9,"Batch %s Quantity" % self.bh.batno),
            (("T",0,0,0),"OSD",13.2,"Value"),
            (("C",1,0,0),"INa",9,"Ref-Num","Reference Number",
                "i","Y",self.doTrnRef,None,None,("notblank",)),
            (("C",1,0,1),"Id1",10,"Date","Transaction Date",
                "r","N",self.doTrnDat,None,None,("efld",)),
            [("C",1,0,2),"IUI",3,"Coy","Company Number",
                self.opts["conum"],"N",self.doCoyNum,coy,None,("notzero",)],
            (("C",1,0,3),"IUI",7,"Acc-Num","Account Number",
                "","Y",self.doAccNum,glm,None,None),
            (("C",1,0,4),"ONA",20,"Description"),
            (("C",1,0,5),"ISD",13.2,"Amount","Transaction Amount",
                "","N",self.doTrnAmt,None,None,None),
            (("C",1,0,6),"IUA",1,"V","V.A.T. Code",
                "N","N",self.doVatCod,vat,None,("notblank",)),
            (("C",1,0,7),"ISD",13.2,"VAT-Amt","V.A.T. Amount",
                "","N",self.doVatAmt,None,None,("efld",)),
            (("C",1,0,8),"INA",30,"Details","Details",
                "r","N",self.doTrnDet,None,None,("notblank",))]
        tags = list(self.tagp.keys())
        tags.sort()
        for tag in tags:
            if tag == "AR":
                self.asspag = self.tagp[tag]
                self.fld.extend([
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
                self.fld.extend([
                    [["T",self.bkmpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.bkmpag,0,0],"IUI",6,"Bkm-Num","Booking Number",
                        "","N",self.doBkmNum,bkm,None,("notzero",)],
                    [["C",self.bkmpag,0,1],"ONA",70,"Name"],
                    [["C",self.bkmpag,0,2],"ISD",13.2,"Amount","",
                        "","N",self.doBkmAmt,None,None,("efld",)]])
            elif tag == "CR":
                self.crspag = self.tagp[tag]
                self.fld.extend([
                    [["T",self.crspag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.crspag,0,0],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doCrsAcc,crm,None,("notblank",)],
                    [["C",self.crspag,0,1],"ONA",30,"Name"],
                    [["C",self.crspag,0,2],"INa",9,"Ref-Num-2","",
                        "i","N",self.doCrsRef,None,None,None],
                    [["C",self.crspag,0,3],"ISD",13.2,"Amount","",
                        "","N",self.doCrsAmt,None,None,("efld",)]])
            elif tag == "DR":
                self.drspag = self.tagp[tag]
                self.fld.extend([
                    [["T",self.drspag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.drspag,0,0],"IUI",3,"Chn","Chain Store Code",
                        "","N",self.doDrsChn,chn,None,("efld",)],
                    [["C",self.drspag,0,1],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doDrsAcc,drm,None,("notblank",)],
                    [["C",self.drspag,0,2],"ONA",30,"Name"],
                    [["C",self.drspag,0,3],"INa",9,"Ref-Num-2","",
                        "i","N",self.doDrsRef,None,None,None],
                    [["C",self.drspag,0,4],"ISD",13.2,"Amount","",
                        "","N",self.doDrsAmt,None,None,("efld",)]])
            elif tag == "LN":
                self.lonpag = self.tagp[tag]
                self.fld.extend([
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
                self.fld.extend([
                    [["T",self.mempag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.mempag,0,0],"IUI",6,"Mem-No","Member Number",
                        "","N",self.doMemAcc,mlm,None,("notblank",)],
                    [["C",self.mempag,0,1],"ONA",30,"Name"],
                    [["C",self.mempag,0,2],"ISD",13.2,"Amount","",
                        "","N",self.doMemAmt,None,None,("efld",)]])
            elif tag == "RC":
                self.rcapag = self.tagp[tag]
                self.fld.extend([
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
                self.fld.extend([
                    [["T",self.rtlpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.rtlpag,0,0],"INA",7,"Prm-Cod","Premises Code",
                        "","N",self.doRtlPrm,prm,None,("efld",)],
                    [["C",self.rtlpag,0,1],"ONA",30,"Description"],
                    [["C",self.rtlpag,0,2],"INA",7,"Acc-Num","Account Number",
                        "","N",self.doRtlAcc,rtm,None,("notblank",)],
                    [["C",self.rtlpag,0,3],"ONA",30,"Name"],
                    [("C",self.rtlpag,0,4),"IUI",3,"Seq","Contract Sequence",
                        "","N",self.doRtlCon,con,None,None],
                    [["C",self.rtlpag,0,5],"ISD",13.2,"Amount","",
                        "","N",self.doRtlAmt,None,None,("efld",)],
                    [["C",self.rtlpag,0,6],"INA",30,"Details","Details",
                        "","N",self.doRtlDet,None,None,("efld",)]])
            elif tag == "SL":
                self.slnpag = self.tagp[tag]
                self.fld.extend([
                    [["T",self.slnpag,0,0],"OSD",13.2,"Unallocated Balance"],
                    [["C",self.slnpag,0,0],"IUI",5,"EmpNo","Employee Number",
                        "","N",self.doSlnEmp,wgm,None,None],
                    [["C",self.slnpag,0,1],"ONA",20,"Name"],
                    [["C",self.slnpag,0,2],"IUI",2,"Ln","Loan Number",
                        "","N",self.doSlnNum,lmf,None,("notzero",)],
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
        if not self.incoac:
            self.fld[4][1] = "OUI"
            self.allcoy = self.opts["conum"]
        but = [
            ("_Import File",None,self.doImport,0,("C",1,1),("C",1,2),
                "Import a CSV or XLS File with the Correct Format i.e. "\
                "Reference Number, Transaction Date, Company Number, "\
                "Account Number, Transaction Amount, V.A.T. Code, "\
                "V.A.T. Amount, Details. If there is a VAT Code with "\
                "Zero VAT Amount, it will be Calculated."),
            ("View Entries",lst,None,0,("C",1,1),("C",1,2)),
            ("End Batch",None,self.exitPage,0,("C",1,1),("C",1,2)),
            ("Abort Batch",None,self.doAbort,1,None,None)]
        cnd = [None, (self.endPage,"y")]
        cxt = [None, self.exitPage]
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
        self.df = TartanDialog(self.opts["mf"], tags=self.tags, eflds=self.fld,
            butt=but, cend=cnd, cxit=cxt)
        self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
        self.df.loadEntry("T", 0, 1, data=self.bh.batval)
        self.df.focusField("C", 1, 1)

    def doImport(self):
        self.df.closeProcess()
        self.importing = True
        impcol = []
        pos = 0
        for num, fld in enumerate(self.fld[2:11]):
            if num == 4:
                continue
            if type(fld[2]) in (tuple, list):
                size = fld[2][1]
            else:
                size = fld[2]
            impcol.append([fld[4], pos, fld[1][1:], size])
            pos += 1
        if self.incoac:
            fld = [(("T",0,0,0),("IRB",(("Yes","Y"),("No","N"))),0,
                "Allow Intercompany","","N","N",self.doAllowIC,None,None,None)]
        else:
            fld = []
            self.impint = "N"
        fi = FileImport(self.opts["mf"], impcol=impcol, impfld=fld)
        p = ProgressBar(self.opts["mf"].body, typ="Importing Journals",
            mxs=len(fi.impdat))
        trans = []
        tot = 0
        err = False
        for num, line in enumerate(fi.impdat):
            p.displayProgress(num)
            lin = num + 1
            if len(line) != 8:
                err = "Line %s: Invalid Number of Fields (S/B 8 is %s)" % \
                    (lin, len(line))
                break
            ref = line[0]
            if not ref:
                err = "Line %s: Invalid Reference Number" % (lin)
                break
            dte = line[1]
            # Check if date in period
            if dte < self.opts["period"][1][0] or \
                    dte > self.opts["period"][2][0]:
                txt = "Invalid Date, Not in Financial Period"
                err = "Line %s: %s" % (lin, txt)
                break
            coy = line[2]
            # Check if valid company number
            if self.impint == "N" and coy != self.opts["conum"]:
                err = "Invalid Company (S/B %s is %s)" % \
                    (self.opts["conum"], coy)
            elif self.incoac and coy not in self.incoac:
                err = "Invalid Company, No Intercompany Record 1"
            else:
                self.allcoy = coy
                err = self.doChkLoadCtls()
                if err == "rf":
                    err = "Invalid Company, Control Record Error"
            if err:
                err = "Line %s: %s" % (lin, err)
                break
            acc = line[3]
            # Check if valid account number
            chk = chkGenAcc(self.opts["mf"], coy, acc, pwd=False)
            if type(chk) is str:
                err = "Line %s: %s" % (lin, chk)
                break
            if not line[4]:
                continue
            val = line[4]
            tot = float(ASD(tot) + ASD(val))
            cod = line[5]
            # Check if valid vat code
            chk = self.sql.getRec("ctlvmf", where=[("vtm_cono",
                "=", coy), ("vtm_code", "=", cod)], limit=1)
            if not chk:
                err = "Line %s: %s" % (lin, "Invalid VAT Code")
                break
            vat = line[6]
            des = line[7]
            trans.append([ref, dte, coy, acc, val, cod, vat, des])
        p.closeProgress()
        if not err and tot:
            err = "Debits Do Not Equal Credits"
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        else:
            sp = SplashScreen(self.opts["mf"].body,
                "Updating Records ... Please Wait")
            for self.trnref, self.trndte, self.allcoy, self.acno, \
                    self.trnamt, self.vatcod, vat, self.trndet in trans:
                if self.bh.multi == "N":
                    self.curdt = self.bh.curdt
                else:
                    self.curdt = int(self.trndte / 100)
                self.doChkLoadCtls()
                if self.vatcod and not vat:
                    vrte = getVatRate(self.sql, self.opts["conum"],
                        self.vatcod, self.trndte)
                    if vrte is None:
                        vrte = 0.0
                    self.vatamt = round((self.trnamt * vrte / (vrte + 100)), 2)
                else:
                    self.vatamt = vat
                self.allamt = float(ASD(self.trnamt) - ASD(self.vatamt))
                self.updateTables()
                self.updateBatch()
            if trans:
                self.bh.doBatchTotal(det=True)
            else:
                self.bh.doBatchTotal()
            sp.closeSplash()
        self.opts["mf"].closeLoop()

    def doAllowIC(self, obj, w):
        self.impint = w
        if self.impint == "N":
            self.batind = "N"

    def doTrnRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w

    def doTrnDat(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        if self.bh.multi == "N" and int(w / 100) > self.bh.curdt:
            return "Invalid Date, After Batch Period"
        self.trndte = w
        if self.bh.multi == "Y":
            self.curdt = int(self.trndte / 100)
        else:
            self.curdt = self.bh.curdt

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlmst", where=[("ctm_cono", "=", w)])
        if not acc:
            return "Invalid Company Number"
        if self.incoac and w not in self.incoac:
            return "Invalid Company, No Intercompany Record 1"
        self.allcoy = w
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
        # Check for Control Records e.g. VAT, Crs and Drs
        self.ctlctl = self.gc.getCtl("ctlctl", self.allcoy)
        if not self.ctlctl:
            return "rf"
        ctls = ["vat_ctl"]
        if self.ass_gl == "Y":
            ctls.append("ass_sls")
        if self.bkm_gl == "Y":
            ctls.append("bkm_ctl")
        if self.crs_gl == "Y":
            ctls.append("crs_ctl")
        if self.drs_gl == "Y":
            ctls.append("drs_ctl")
        if self.lon_gl == "Y":
            ctls.extend(["lon_ctl", "int_pay", "int_rec"])
        if self.mem_gl == "Y":
            ctls.append("mem_ctl")
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
        # Batch Indicator
        if self.allcoy == self.opts["conum"]:
            self.batind = "N"
        else:
            self.batind = ""

    def doAccNum(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Account Number"
        self.others = False
        self.othtot = 0
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
        self.acno = w
        self.df.loadEntry(frt, pag, p+1, chk[0])
        if self.others:
            if self.others in ("bkm", "sln"):
                self.othrtn = 5
            elif self.others in ("own", "tnt", "dep", "rtl"):
                self.othrtn = 4
            else:
                self.othrtn = 3
            self.vatcod = "N"
        elif not chk[2]:
            if chk[3] == "P":
                self.vatcod = self.taxdf
            else:
                self.vatcod = "N"
        else:
            self.vatcod = chk[2]

    def doTrnAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        self.df.loadEntry("C", 1, p+1, self.vatcod)
        if self.others:
            self.vatamt = 0
            self.allamt = self.trnamt
            self.df.loadEntry("C", 1, p+2, self.vatamt)
            return "sk2"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndte)
        if vrte is None:
            return "Invalid V.A.T. Code"
        self.vatcod = w
        self.vatamt = round((self.trnamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry("C", 1, p+1, data=self.vatamt)
        if not self.vatamt:
            self.allamt = self.trnamt
            return "sk1"

    def doVatAmt(self, frt, pag, r, c, p, i, w):
        if self.trnamt < 0 and w > 0:
            self.vatamt = float(ASD(0) - ASD(w))
        elif self.trnamt > 0 and w < 0:
            self.vatamt = float(ASD(0) - ASD(w))
        else:
            self.vatamt = w
        self.allamt = float(ASD(self.trnamt) - ASD(self.vatamt))
        self.df.loadEntry(frt, pag, p, data=self.vatamt)

    def doTrnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def endPage(self):
        self.updateTables()
        self.updateBatch()
        if self.others == "ass":
            self.df.selPage("ASS")
            self.allvat = self.vatamt
            self.df.loadEntry("T", self.asspag, 0, data=self.allamt)
            self.df.focusField("C", self.asspag, 1)
        elif self.others == "bkm":
            self.df.selPage("BKM")
            self.df.loadEntry("T", self.bkmpag, 0, data=self.allamt)
            self.df.focusField("C", self.bkmpag, 1)
        elif self.others == "crs":
            self.df.selPage("CRS")
            self.df.loadEntry("T", self.crspag, 0, data=self.allamt)
            self.df.focusField("C", self.crspag, 1)
        elif self.others == "drs":
            if self.drs_ch == "N":
                self.df.colf[self.drspag][0][1] = "OUI"
                self.chain = 0
            else:
                self.df.colf[self.drspag][0][1] = "IUI"
            self.df.selPage("DRS")
            self.df.loadEntry("T", self.drspag, 0, data=self.allamt)
            self.df.focusField("C", self.drspag, 1)
        elif self.others == "lon":
            self.df.selPage("LON")
            self.df.loadEntry("T", self.lonpag, 0, data=self.allamt)
            self.df.focusField("C", self.lonpag, 1)
        elif self.others == "mem":
            self.df.selPage("MEM")
            self.df.loadEntry("T", self.mempag, 0, data=self.allamt)
            self.df.focusField("C", self.mempag, 1)
        elif self.others in ("own", "tnt", "dep"):
            self.df.selPage("RCA")
            self.df.loadEntry("T", self.rcapag, 0, data=self.allamt)
            self.df.focusField("C", self.rcapag, 1)
        elif self.others == "rtl":
            self.df.selPage("RTL")
            self.df.loadEntry("T", self.rtlpag, 0, data=self.allamt)
            self.df.focusField("C", self.rtlpag, 1)
        elif self.others == "sln":
            self.df.selPage("SLN")
            self.df.loadEntry("T", self.slnpag, 0, data=self.allamt)
            self.df.focusField("C", self.slnpag, 1)
        else:
            self.df.advanceLine(1)

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
        if self.assacc != self.acno:
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
        if w == 1 and self.assbuy:
            return "Asset Already Purchased"
        if w in (2, 5) and self.asssel:
            return "Asset Already Sold"
        if w in (2, 3, 5) and not self.assbuy:
            return "Asset Not Yet Purchased"
        self.df.loadEntry(frt, pag, p, data=w)
        self.othmov = w

    def doAssAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
        self.df.loadEntry(frt, pag, p, data=self.othamt)
        self.df.loadEntry(frt, pag, p+1, data=self.trndet)

    def doAssDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def endAss(self):
        # Asset Register Transaction
        data = [self.allcoy, self.assgrp, self.asscod, self.othrtn,
            self.trnref, self.bh.batno, self.trndte, self.othmov,
            self.othamt, self.othamt, 0, self.curdt, self.trndet,
            "", "", self.opts["capnm"], self.sysdtw, 0]
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
                data = [self.opts["conum"], self.ctlctl["ass_sls"], self.curdt,
                    self.trndte, self.opts["rtn"], self.trnref, self.bh.batno,
                    amt[0], 0, self.trndet, "N", "", 0, self.opts["capnm"],
                    self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                data[1] = self.acno
                data[7] = float(ASD(0) - ASD(amt[0]))
                self.sql.insRec("gentrn", data=data)
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.asspag, 0, data=bal)
            self.df.advanceLine(self.tagp["AR"])

    def doNewAss(self):
        tit = ("Create New Asset", )
        dep = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.allcoy)]}
        fld = (
            (("T",0,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",0,1,0),"INa",3,"Dep Code","Depreciation Code",
                self.depcod,"N",self.doNewADep,dep,None,("notblank",)),
            (("T",0,1,0),"ONA",27,""))
        tnd = ((self.doNewAEnd,"N"), )
        txt = (self.doNewAXit, )
        state = self.df.disableButtonsTags()
        self.na = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
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
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

    def endBkm(self):
        # Bookings Ledger Transaction
        data = [self.allcoy, self.bkmnum, self.othrtn, self.trnref,
            self.bh.batno, self.trndte, self.othamt, 0, self.curdt,
            self.trndet, "", "", self.opts["capnm"], self.sysdtw, 0]
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
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.bkmpag, 0, data=bal)
            self.df.advanceLine(self.tagp["BK"])

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

    def doCrsAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

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

    def doDrsAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

    def doNewDrs(self):
        callModule(self.opts["mf"], self.df, "dr1010", coy=(self.allcoy,
            self.allnam), period=None, user=self.opts["capnm"],
            args=(self.chain, self.othacno))

    def doLonAcc(self, frt, pag, r, c, p, i, w):
        newacc = False
        if not w:
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
        if not w:
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
            if self.lonmth:
                return "Invalid Entry, Fixed Loan"
            self.df.loadEntry(frt, pag, p+1, data=self.londes)
            return "sk1"

    def doLonDes(self, frt, pag, r, c, p, i, w):
        self.londes = w

    def doLonAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
        if not self.newlon:
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
            self.othrtn, self.trndte, self.trnref, self.othamt, self.curdt,
            self.trndet, "", self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("lontrn", data=data)
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.lonpag, 0, data=bal)
            self.df.advanceLine(self.tagp["LN"])

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

    def doMemAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)

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
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if not self.rcatnt:
            # Owners Transaction
            data = [self.allcoy, self.rcaown, self.othrtn, self.trnref,
                self.bh.batno, self.trndte, self.othamt, 0, self.curdt,
                self.alldet, "N", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcaowt", data=data)
        else:
            # Tenants Transaction
            data = [self.allcoy, self.rcaown, self.rcaprm, self.rcatnt,
                self.rcacon, self.othrtn, self.trnref, self.bh.batno,
                self.trndte, self.rcatyp, self.othamt, 0, self.curdt,
                self.alldet, "N", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcatnt", data=data)
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.rcapag, 0, data=bal)
            self.df.advanceLine(self.tagp["RC"])

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
            self.allcoy), ("rtc_code", "=", self.rtlprm), ("rtc_acno",
            "=", self.othacno)], order="rtc_cnum")
        if not con:
            return "No Valid Contracts"
        self.rtlcon = con[-1:][0][3]
        self.df.loadEntry(frt, pag, p+2, data=self.rtlcon)

    def doRtlCon(self, frt, pag, r, c, p, i, w):
        con = self.sql.getRec("rtlcon", where=[("rtc_cono", "=",
            self.allcoy), ("rtc_code", "=", self.rtlprm), ("rtc_acno",
            "=", self.othacno), ("rtc_cnum", "=", w)], order="rtc_cnum")
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
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        # Rental Ledger Transaction
        data = [self.allcoy, self.rtlprm, self.othacno, self.rtlcon,
            self.othrtn, self.trnref, self.bh.batno, self.trndte,
            self.othamt, 0, self.curdt, self.alldet, "N", "",
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("rtltrn", data=data)
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.rtlpag, 0, data=bal)
            self.df.advanceLine(self.tagp["RT"])

    def doSlnEmp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
            where=[("wgm_cono", "=", self.allcoy), ("wgm_empno", "=", w)],
            limit=1)
        if not acc:
            return "Invalid Employee Number"
        self.empnum = w
        empnam = "%s, %s" % (acc[0], acc[1].split()[0])
        self.df.loadEntry(frt, pag, p+1, data=empnam)

    def doSlnNum(self, frt, pag, r, c, p, i, w):
        if not w:
            ok = askQuestion(self.opts["mf"].body, head="New Loan",
                mess="Is This a New Loan?", default="no")
            if ok == "yes":
                self.newsln = True
                self.slnnum = getNextCode(self.sql, "waglmf", "wlm_loan",
                    where=[("wlm_cono", "=", self.allcoy), ("wlm_empno",
                    "=", self.empnum)], start=1, last=99999)
                self.df.loadEntry(frt, pag, p, data=self.slnnum)
        else:
            acc = self.sql.getRec("waglmf", where=[("wlm_cono",
                "=", self.allcoy), ("wlm_empno", "=", self.empnum),
                ("wlm_loan", "=", w)], limit=1)
            if not acc:
                return "Loan Does Not Exist"
            self.slnnum = w
            self.newsln = False
            self.slndes = acc[self.sql.waglmf_col.index("wlm_desc")]
            self.slncod = acc[self.sql.waglmf_col.index("wlm_code")]
            self.slnrte = acc[self.sql.waglmf_col.index("wlm_rate")]
            self.slndat = acc[self.sql.waglmf_col.index("wlm_start")]
            self.slnded = acc[self.sql.waglmf_col.index("wlm_repay")]
            self.df.loadEntry(frt, pag, p+1, data=self.slndes)
            return "sk1"

    def doSlnDes(self, frt, pag, r, c, p, i, w):
        self.slndes = w

    def doSlnAmt(self, frt, pag, r, c, p, i, w):
        self.othamt = w
        if not self.othamt:
            self.othamt = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry(frt, pag, p, data=self.othamt)
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
            self.newrte = 0
            self.slnded = 0
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "nd"
        self.df.loadEntry(frt, pag, p+2, data=self.slnrte)

    def doSlnInt(self, frt, pag, r, c, p, i, w):
        self.newrte = w
        if not self.newsln:
            self.df.loadEntry(frt, pag, p+2, data=self.slnded)

    def doSlnDed(self, frt, pag, r, c, p, i, w):
        self.slnded = w

    def endSln(self):
        if self.newsln:
            # Staff Loans Ledger Masterfile
            cap = self.othamt
            self.sql.insRec("waglmf", data=[self.allcoy, self.empnum,
                self.slnnum, self.slndes, self.slncod, self.newrte,
                self.trndte, self.slnded])
        else:
            # Staff Loans Ledger Masterfile
            cap = self.othamt
            self.sql.updRec("waglmf", cols=["wlm_int_per"], data=[self.newrte],
                where=[("wlm_cono", "=", self.allcoy), ("wlm_empno", "=",
                self.empnum), ("wlm_loan", "=", self.slnnum)])
        # Staff Loans Ledger Transaction
        data = [self.allcoy, self.empnum, self.slnnum, self.bh.batno,
            self.othrtn, self.trndte, self.trnref, self.othamt, cap,
            self.slnded, self.newrte, self.curdt, self.trndet, "",
            self.opts["capnm"], self.sysdtw, 0]
        self.sql.insRec("wagltf", data=data)
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.othtot == self.allamt:
            self.endOther()
        else:
            bal = float(ASD(self.allamt) - ASD(self.othtot))
            self.df.loadEntry("T", self.slnpag, 0, data=bal)
            self.df.advanceLine(self.tagp["SL"])

    def endCrsDrsMem(self):
        self.othtot = float(ASD(self.othtot) + ASD(self.othamt))
        if self.others == "crs":
            # Creditors Ledger Transaction
            amt = float(ASD(0) - ASD(self.othamt))
            data = [self.allcoy, self.othacno, self.othrtn, self.allref,
                self.bh.batno, self.trndte, self.othref, amt, 0, 0,
                self.curdt, 0, "Y", 0, self.trndet, "", "",
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("crstrn", data=data, unique="crt_ref1")
            if self.othtot == self.allamt:
                self.endOther()
            else:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.crspag, 0, data=bal)
                self.df.advanceLine(self.tagp["CR"])
        elif self.others == "drs":
            # Debtors Ledger Transaction
            data = [self.allcoy, self.chain, self.othacno, self.othrtn,
                self.allref, self.bh.batno, self.trndte, self.othref,
                self.othamt, 0, self.curdt, self.trndet, "", "",
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("drstrn", data=data, unique="drt_ref1")
            if self.othtot == self.allamt:
                self.endOther()
            else:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.drspag, 0, data=bal)
                self.df.advanceLine(self.tagp["DR"])
        elif self.others == "mem":
            # Members Ledger Transaction
            data = [self.allcoy, self.othacno, self.othrtn, self.allref,
                self.bh.batno, self.trndte, self.othamt, 0, self.curdt,
                "", 0, self.trndet, "", "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("memtrn", data=data, unique="mlt_refno")
            if self.othtot == self.allamt:
                self.endOther()
            else:
                bal = float(ASD(self.allamt) - ASD(self.othtot))
                self.df.loadEntry("T", self.mempag, 0, data=bal)
                self.df.advanceLine(self.tagp["ML"])

    def endOther(self):
        if self.others == "crs":
            self.df.clearFrame("C", self.crspag)
        elif self.others == "drs":
            self.df.clearFrame("C", self.drspag)
        elif self.others == "lon":
            self.df.clearFrame("C", self.lonpag)
        elif self.others == "mem":
            self.df.clearFrame("C", self.mempag)
        elif self.others in ("own", "tnt", "dep"):
            self.df.clearFrame("C", self.rcapag)
        elif self.others == "rtl":
            self.df.clearFrame("C", self.rtlpag)
        elif self.others == "sln":
            self.df.clearFrame("C", self.slnpag)
        self.df.selPage("Transaction")
        self.df.advanceLine(1)

    def updateTables(self):
        if self.allcoy != self.opts["conum"]:
            inter = True
            ac1 = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.opts["conum"]),
                ("cti_inco", "=", self.allcoy)], limit=1)[0]
            ac2 = self.sql.getRec("genint", cols=["cti_acno"],
                where=[("cti_cono", "=", self.allcoy),
                ("cti_inco", "=", self.opts["conum"])], limit=1)[0]
        else:
            inter = False
        data = (self.allcoy, self.acno, self.curdt, self.trndte,
            self.opts["rtn"], self.trnref, self.bh.batno, self.allamt,
            self.vatamt, self.trndet, self.vatcod, self.batind, 0,
            self.opts["capnm"], self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if self.vatcod:
            if self.vatamt:
                data = (self.allcoy, self.convat, self.curdt, self.trndte,
                    self.opts["rtn"], self.trnref, self.bh.batno, self.vatamt,
                    0.00, self.trndet, self.vatcod, self.batind, 0,
                    self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            if self.allamt < 0:
                vtyp = "O"
            else:
                vtyp = "I"
            data = (self.allcoy, self.vatcod, vtyp, self.curdt, "G",
                self.opts["rtn"], self.bh.batno, self.trnref, self.trndte,
                self.acno, self.trndet, self.allamt, self.vatamt, 0,
                self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("ctlvtf", data=data)
        if inter:
            data = (self.opts["conum"], ac1, self.curdt, self.trndte,
                self.opts["rtn"], self.trnref, self.bh.batno, self.trnamt,
                0.00, self.trndet, self.vatcod, "N", 0, self.opts["capnm"],
                self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)
            val = float(ASD(0) - ASD(self.trnamt))
            data = (self.allcoy, ac2, self.curdt, self.trndte,
                self.opts["rtn"], self.trnref, self.bh.batno, val, 0.00,
                self.trndet, self.vatcod, "", 0, self.opts["capnm"],
                self.sysdtw, 0)
            self.sql.insRec("gentrn", data=data)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty = self.bh.batqty - 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.trnamt))
        else:
            self.bh.batqty = self.bh.batqty + 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.trnamt))
        if not self.importing:
            self.df.loadEntry("T", 0, 0, data=self.bh.batqty)
            self.df.loadEntry("T", 0, 1, data=self.bh.batval)

    def exitPage(self):
        err = False
        if self.bh.batval:
            cf = PwdConfirm(self.opts["mf"], conum=self.allcoy,
                system="GEN", code="JnlBal")
            if not cf.pwd or cf.flag == "no":
                err = "Debits Do Not Equal Credits"
        if err:
            self.opts["mf"].updateStatus(err)
            showError(self.opts["mf"].body, "Total Error", err)
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        else:
            self.df.closeProcess()
            self.bh.doBatchTotal()
            self.opts["mf"].closeLoop()

    def doAbort(self):
        ok = askQuestion(self.opts["mf"].body, head="Abort",
            mess="Are You Certain You Want to Cancel These Batch Postings?")
        if ok == "yes":
            self.abort = True
            self.opts["mf"].dbm.rollbackDbase()
            self.df.closeProcess()
            self.opts["mf"].closeLoop()
        else:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

# vim:set ts=4 sw=4 sts=4 expandtab:
