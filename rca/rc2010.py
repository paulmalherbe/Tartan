"""
SYNOPSIS
    Rentals Data Capture Screen and Execution.

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
from TartanClasses import ASD, GetCtl, NotesCreate, PwdConfirm, Sql
from TartanClasses import SelectChoice, TartanDialog
from tartanFunctions import getVatRate, mthendDate, projectDate, runModule
from tartanWork import rcmvtp, rctrtp

class rc2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        tabs = ["ctlmst", "ctlvmf", "ctlvrf", "ctlvtf", "genmst", "gentrn",
            "rcaowm", "rcaowt", "rcaprm", "rcatnm","rcacon", "rcatnt"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.glint = rcactl["cte_glint"]
        self.ch1 = ((rcactl["cte_lme"] // 100) * 100) + 1
        self.ch2 = projectDate(self.ch1, 2, typ="months")
        if self.glint == "Y":
            self.glbnk = rcactl["cte_glbnk"]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["rca_com", "rca_dep", "rca_fee", "rca_orx", "rca_own",
                "rca_tnt", "rca_trx", "vat_ctl"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.rcacom = ctlctl["rca_com"]
            self.rcadep = ctlctl["rca_dep"]
            self.rcafee = ctlctl["rca_fee"]
            self.rcaorx = ctlctl["rca_orx"]
            self.rcaown = ctlctl["rca_own"]
            self.rcatnt = ctlctl["rca_tnt"]
            self.rcatrx = ctlctl["rca_trx"]
            self.convat = ctlctl["vat_ctl"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.batno = "R%04i%02i" % (t[0], t[1])
        return True

    def drawDialog(self):
        # Transaction Types
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": []}
        # Movement Types
        data = []
        for x in range(1, len(rcmvtp) + 1):
            data.append((x, rcmvtp[x - 1][1]))
        mov = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": data}
        # Premises
        prm = {
            "stype": "R",
            "tables": ("rcaprm", "rcaowm"),
            "cols": (
                ("rcp_owner", "", 0, "Owner"),
                ("rom_name", "", 0, "Owner"),
                ("rcp_code", "", 0, "Prm-Cod"),
                ("rcp_addr1", "", 0, "Address-Line-1")),
            "where": [
                ("rcp_cono", "=", self.opts["conum"]),
                ("rom_cono=rcp_cono",),
                ("rom_acno=rcp_owner",)],
            "index": 2}
        # Tenant
        tnm = {
            "stype": "R",
            "tables": ("rcatnm",),
            "cols": (
                ("rtn_acno", "", 0, "Acc-Num"),
                ("rtn_name", "", 0, "Description", "Y")),
            "where": [("rtn_cono", "=", self.opts["conum"])],
            "whera": [("T", "rtn_owner", 0, 1)]}
        # Contract
        con = {
            "stype": "R",
            "tables": ("rcacon",),
            "cols": (
                ("rcc_cnum", "", 0, "Seq"),
                ("rcc_payind", "", 0, "F"),
                ("rcc_start", "", 0, "Start-Date"),
                ("rcc_period", "", 0, "Per"),
                ("rcc_status", "", 0, "S")),
            "where": [("rcc_cono", "=", self.opts["conum"])],
            "whera": [
                ("T", "rcc_owner", 0, 1),
                ("T", "rcc_code", 0, 0),
                ("T", "rcc_acno", 0, 2)]}
        # VAT Records
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        tag = (
            ("Owner",None,
                (("T",2,1),("C",2,1)),                      # On
                (("C",1,1),("T",2,2),("C",2,2))),           # Off
            ("Tenant",None,
                ("C",1,1),                                  # On
                (("C",1,2),("T",2,1),("C",2,1))),           # Off
            ("Allocation",self.doAllocation,None,None))
        fld = [
            (("T",0,0,0),"INA",7,"Prm-Cod","Premises Code",
                "","Y",self.doPrmCod,prm,None,None),
            (("T",0,0,0),"ONA",30,"Description"),
            (("T",1,0,0),"ONA",7,"Acc-Num"),
            (("T",1,0,0),"ONA",30,"Name"),
            (("T",1,0,0),"OSD",11.2,"Payable"),
            (("C",1,0,0),"INa",9,"Reference","Reference Number",
                "i","Y",self.doOwnRef,None,None,("notblank",)),
            (("C",1,0,1),"ID1",10,"Date","Transaction Date",
                "r","N",self.doOwnDat,None,None,("efld",)),
            (("C",1,0,2),"IUI",1,"T","Transaction Type",
                "r","N",self.doOwnTyp,typ,None,("notzero",)),
            (("C",1,0,3),"ISD",11.2,"Amount","Transaction Amount",
                "","N",self.doOwnAmt,None,None,None),
            (("C",1,0,4),"IUA",1,"V","V.A.T Code",
                "N","N",self.doOwnCod,vtm,None,("efld",)),
            (("C",1,0,5),"ISD",11.2,"V.A.T","V.A.T Amount",
                "","N",self.doOwnVat,None,None,None),
            (("C",1,0,6),"INA",43,"Details","Transaction Details",
                "","N",self.doOwnDet,None,None,None),
            (("T",2,0,0),"INA",7,"Acc-Num","Account Number",
                "","Y",self.doAccNum,tnm,None,None),
            (("T",2,0,0),"ONA",30,"Name"),
            (("T",2,0,0),"IUI",3,"Seq", "Contract Number",
                "","N",self.doConSeq,con,None,None),
            (("T",2,0,0),"OSD",11.2,"Balance"),
            (("C",2,0,0),"INa",9,"Reference","Reference Number",
                "i","Y",self.doTntRef,None,None,("notblank",)),
            (("C",2,0,1),"ID1",10,"Date","Transaction Date",
                "r","N",self.doTntDat,None,None,("efld",)),
            (("C",2,0,2),"IUI",1,"T","Transaction Type",
                "r","N",self.doTntTyp,typ,None,("notzero",)),
            (("C",2,0,3),"ISD",11.2,"Amount","Transaction Amount",
                "","N",self.doTntAmt,None,None,None),
            (("C",2,0,4),"INA",(60,30),"Details","Transaction Details",
                "","N",self.doTntDet,None,None,None),
            (("T",3,0,0),"OSD",11.2,"Rentals     "),
            (("T",3,0,0),"OSD",11.2,"Deposit     "),
            (("T",3,0,0),"OSD",11.2,"Fees        "),
            (("T",3,1,0),"OSD",11.2,"Services (O)"),
            (("T",3,1,0),"OSD",11.2,"Services (A)"),
            (("T",3,1,0),"OSD",11.2,"Repairs     "),
            (("T",3,2,0),"OSD",11.2,"Allocation"),
            (("C",3,0,0),"IUI",1,"M","Movement Type",
                "","Y",self.doAllMov,mov,None,("notzero",)),
            (("C",3,0,1),"ISD",11.2,"Amount","Allocation Amount",
                "","N",self.doAllAmt,None,None,None),
            (("C",3,0,2),"IUA",1,"V","V.A.T Code",
                "N","N",self.doAllCod,vtm,None,("efld",)),
            (("C",3,0,3),"ISD",11.2,"V.A.T","V.A.T Amount",
                "","N",self.doAllVat,None,None,None),
            (("C",3,0,4),"INA",(50,30),"Details","Transaction Details",
                "","N",self.doAllDet,None,None,None)]
        row = [0, 4, 4, 10]
        tnd = [
            (self.endPage,"y"),
            (self.endPage,"y"),
            (self.endPage,"y"),
            (self.endPage,"y")]
        txt = [
            self.exitPage,
            self.exitPage,
            self.exitPage,
            self.exitPage]
        cnd = [
            (None,"n"),
            (self.endPage,"y"),
            (self.endPage,"y"),
            (self.endPage,"y")]
        cxt = [
            None,
            self.exitPage,
            self.exitPage,
            self.exitPage]
        but = (
            ("Notes",None,self.allNotes,0,("T",0,0),("T",0,1)),
            ("Statement",None,self.allStmnt,0, (("C",1,1),("C",2,1)),
                (("T",0,1),("T",2,1))),
            ("Cancel",None,self.doAllCancel,0,("C",3,1),("C",2,1)))
        self.df = TartanDialog(self.opts["mf"], tags=tag, eflds=fld,
            rows=row, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doPrmCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcaprm", cols=["rcp_desc", "rcp_owner",
            "rcp_crate", "rcp_addr1"], where=[("rcp_cono", "=",
            self.opts["conum"]), ("rcp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises Code"
        self.code = w
        desc, self.owner, self.crate, addr1 = acc
        if desc:
            self.df.loadEntry(frt, pag, p+1, data=desc)
        else:
            self.df.loadEntry(frt, pag, p+1, data=addr1)
        acc = self.sql.getRec("rcaowm", cols=["rom_name",
            "rom_vatdf"], where=[("rom_cono", "=", self.opts["conum"]),
            ("rom_acno", "=", self.owner)], limit=1)
        if not acc:
            return "Missing Owner Record (%s)" % self.owner
        self.df.loadEntry("T", 1, 0, data=self.owner)
        self.df.loadEntry("T", 1, 1, data=acc[0])
        self.vatdf = acc[1]
        self.acno = None

    def doAccNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rcatnm", cols=["rtn_name"],
            where=[("rtn_cono", "=", self.opts["conum"]), ("rtn_owner", "=",
            self.owner), ("rtn_code", "=", self.code), ("rtn_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        self.acno = w
        self.name = acc[0]
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        con = self.sql.getRec("rcacon", where=[("rcc_cono", "=",
            self.opts["conum"]), ("rcc_owner", "=", self.owner),
            ("rcc_code", "=", self.code), ("rcc_acno", "=", self.acno)],
            order="rcc_cnum")
        if not con:
            return "No Valid Contracts"
        self.cnum = con[-1:][0][self.sql.rcacon_col.index("rcc_cnum")]
        self.df.topf[2][2][5] = self.cnum

    def doConSeq(self, frt, pag, r, c, p, i, w):
        con = self.sql.getRec("rcacon", where=[("rcc_cono", "=",
            self.opts["conum"]), ("rcc_code", "=", self.code), ("rcc_acno",
            "=", self.acno), ("rcc_cnum", "=", w)], order="rcc_cnum")
        if not con:
            return "Invalid Contract Sequence"
        self.cnum = w
        self.showTenantBalance()

    def doOwnRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w

    def doOwnDat(self, frt, pag, r, c, p, i, w):
        if w < self.ch1 or w > self.ch2:
            ov = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="RCA", code="DateOver")
            if ov.flag == "no":
                return "Invalid Date (< %s or > %s)" % (self.ch1, self.ch2)
        self.trndat = w
        data = []
        for x in range(2, len(rctrtp)+1):
            data.append((x, rctrtp[x-1][1]))
        self.df.colf[1][2][8]["data"] = data

    def doOwnTyp(self, frt, pag, r, c, p, i, w):
        if w not in (2, 3, 4):
            return "Invalid Transaction Type"
        self.trntyp = w

    def doOwnAmt(self, frt, pag, r, c, p, i, w):
        if self.trntyp == 3 and w > self.due:
            op = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="RCA", code="Overpaid")
            if op.flag == "no":
                return "Overpaid"
        self.trnamt = w
        # Ignore VAT at this stage
        self.vatcode = ""
        self.trnvat = 0
        self.df.loadEntry(frt, pag, p+1, data=self.vatcode)
        self.df.loadEntry(frt, pag, p+2, data=self.trnvat)
        return "sk2"

    def doOwnCod(self, frt, pag, r, c, p, i, w):
        pass
    #    vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
    #    if vrte is None:
    #        return "Invalid V.A.T Code"
    #    self.vatcode = w
    #    self.trnvat = round((self.trnamt * vrte / (vrte + 100)), 2)
    #    self.df.loadEntry(frt, pag, p+1, data=self.trnvat)
    #    if not self.trnvat:
    #        return "sk1"

    def doOwnVat(self, frt, pag, r, c, p, i, w):
        pass
    #    if self.trnamt < 0 and w > 0:
    #        self.trnvat = float(ASD(0) - ASD(w))
    #    elif self.trnamt > 0 and w < 0:
    #        self.trnvat = float(ASD(0) - ASD(w))
    #    else:
    #        self.trnvat = w
    #    self.df.loadEntry(frt, pag, p, data=self.trnvat)

    def doOwnDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def doTntRef(self, frt, pag, r, c, p, i, w):
        self.trnref = w

    def doTntDat(self, frt, pag, r, c, p, i, w):
        if w < self.ch1 or w > self.ch2:
            ov = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="RCA", code="DateOver")
            if ov.flag == "no":
                return "Invalid Date (< %s or > %s)" % (self.ch1, self.ch2)
        self.trndat = w
        data = []
        for x in range(1, len(rctrtp)+1):
            data.append((x, rctrtp[x-1][1]))
        self.df.colf[2][2][8]["data"] = data

    def doTntTyp(self, frt, pag, r, c, p, i, w):
        if w not in (1, 2, 3, 4):
            return "Invalid Transaction Type"
        self.trntyp = w

    def doTntAmt(self, frt, pag, r, c, p, i, w):
        self.trnamt = w
        if self.trntyp == 1:
            # Rental Raised
            self.vatcode = self.vatdf
            vrte = getVatRate(self.sql, self.opts["conum"], self.vatcode,
                self.trndat)
            if vrte is None:
                vrte = 0.0
            self.trnvat = round((w * vrte / (vrte + 100)), 2)
            self.df.loadEntry(frt, pag, p+1, data="Rental Raised")
        else:
            # Ignore VAT at this stage
            self.vatcode = ""
            self.trnvat = 0

    def doTntDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def doAllocation(self):
        self.df.setWidget(self.df.B1, state="normal")

    def doAllMov(self, frt, pag, r, c, p, i, w):
        if w == 2 and self.trntyp not in (2, 3):
            return "Deposits Only Allowed for Receipts and Payments"
        self.allmov = w

    def doAllAmt(self, frt, pag, r, c, p, i, w):
        if not w:
            self.allamt = float(ASD(self.trnamt) - ASD(self.alltot))
            self.df.loadEntry(frt, pag, p, data=self.allamt)
        else:
            self.allamt = w
        if self.allmov == 2:
            # Deposit
            self.allcod = ""
            self.df.loadEntry(frt, pag, p+1, data=self.allcod)
            self.allvat = 0
            self.df.loadEntry(frt, pag, p+2, data=self.allvat)
            return "sk2"
        if self.trntyp in (2, 3):
            # Receipt or Payment
            self.df.loadEntry(frt, pag, p+1, self.vatdf)
        if self.trntyp == 4 and self.allmov == 3:
            # Journal Fee
            self.df.loadEntry(frt, pag, p+1, self.taxdf)
        else:
            self.allcod = ""
            self.allvat = 0

    def doAllCod(self, frt, pag, r, c, p, i, w):
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if vrte is None:
            return "Invalid V.A.T Code"
        self.allcod = w
        self.allvat = round((self.allamt * vrte / (vrte + 100)), 2)
        self.df.loadEntry(frt, pag, p+1, data=self.allvat)
        if not self.allvat:
            self.df.loadEntry(frt, pag, p+2, data=self.trndet)
            return "sk1"

    def doAllVat(self, frt, pag, r, c, p, i, w):
        if self.allamt < 0 and w > 0:
            self.allvat = float(ASD(0) - ASD(w))
        elif self.allamt > 0 and w < 0:
            self.allvat = float(ASD(0) - ASD(w))
        else:
            self.allvat = w
        self.df.loadEntry(frt, pag, p, data=self.allvat)
        self.df.loadEntry(frt, pag, p+1, data=self.trndet)

    def doAllDet(self, frt, pag, r, c, p, i, w):
        self.trndet = w

    def doAllCancel(self):
        self.allocs = []
        self.df.clearFrame("C", 3)
        self.df.setWidget(self.df.B1, state="disabled")
        self.df.selPage("Tenant")
        self.df.clearLine(2, int((self.df.last[2][1]-1) / self.df.colq[2]),
            "Y")

    def endPage(self):
        if self.df.frt == "T" and self.df.pag == 0:
            self.df.focusField("C", 1, 1)
        elif self.df.frt == "C" and self.df.pag == 1:
            # Owners
            self.updateTables()
            self.df.advanceLine(self.df.pag)
        elif self.df.frt == "T" and self.df.pag == 2:
            self.df.focusField("C", 2, 1)
        elif self.df.frt == "C" and self.df.pag == 2:
            # Tenants
            self.allocs = []
            self.alltot = 0.0
            if self.trntyp == 1:
                self.movtyp = 1
                self.updateTables()
                self.df.advanceLine(self.df.pag)
            else:
                self.df.selPage("Allocation")
                dpp = 0.0
                acc = self.sql.getRec("rcacon", cols=["rcc_deposit"],
                    where=[("rcc_cono", "=", self.opts["conum"]), ("rcc_owner",
                    "=", self.owner), ("rcc_code", "=", self.code),
                    ("rcc_acno", "=", self.acno)], order="rcc_cnum")
                if acc:
                    dpo = acc[-1:][0][0]
                else:
                    dpo = 0.0
                dat = self.sql.getRec("rcatnt", cols=["rtu_mtyp",
                    "round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
                    self.opts["conum"]), ("rtu_owner", "=", self.owner),
                    ("rtu_code", "=", self.code), ("rtu_acno", "=",
                    self.acno)], group="rtu_mtyp", order="rtu_mtyp")
                if dat:
                    for d in dat:
                        if d[0] == 2:
                            dpp = d[1]
                        else:
                            self.df.loadEntry("T", 3, d[0]-1, data=d[1])
                dpo = float(ASD(dpo) + ASD(dpp))
                if dpo:
                    self.df.loadEntry("T", 3, 1, data=dpo)
                self.df.loadEntry("T", 3, 6, data=self.trnamt)
                self.df.focusField("C", 3, 1)
        else:
            # Allocations
            self.allocs.append([self.allmov, self.allamt, self.allcod,
                self.allvat])
            self.alltot = float(ASD(self.alltot) + ASD(self.allamt))
            bal = float(ASD(self.trnamt) - ASD(self.alltot))
            if bal:
                pos = self.allmov - 1
                if self.trntyp == 2:
                    a = float(ASD(self.df.t_work[3][0][pos])-ASD(self.allamt))
                else:
                    a = float(ASD(self.df.t_work[3][0][pos])+ASD(self.allamt))
                self.df.loadEntry("T", 3, pos, data=a)
                self.df.loadEntry("T", 3, 6, data=bal)
                self.df.advanceLine(3)
            else:
                for line in self.allocs:
                    self.movtyp, self.trnamt, self.vatcode, self.trnvat = line
                    self.updateTables()
                self.df.clearFrame("C", 3)
                self.df.selPage("Tenant")
                self.df.advanceLine(2)
        self.showOwnerTrans()
        if self.acno:
            self.showTenantTrans()

    def showOwnerTrans(self):
        whr = [("rot_cono", "=", self.opts["conum"]), ("rot_acno", "=",
            self.owner)]
        tot = self.sql.getRec("rcaowt",
            cols=["round(sum(rot_tramt),2)"], where=[("rot_cono", "=",
            self.opts["conum"]), ("rot_acno", "=", self.owner)], limit=1)
        if not tot or not tot[0]:
            self.due = 0
        else:
            self.due = float(ASD(0) - ASD(tot[0]))
        arr = self.sql.getRec("rcatnt", cols=["round(sum(rtu_tramt),2)"],
            where=[("rtu_cono", "=", self.opts["conum"]), ("rtu_owner", "=",
            self.owner), ("rtu_mtyp", "in", (1, 4))], limit=1)
        if arr and arr[0]:
            self.due = float(ASD(self.due) - ASD(arr[0]))
        self.df.loadEntry("T", 1, 2, data=self.due)
        try:
            self.otrn.closeProcess()
        except:
            pass
        tab = ["rcaowt"]
        col = ["rot_trdt", "rot_type", "rot_refno", "rot_desc", "rot_tramt",
            "rot_taxamt"]
        whr = [("rot_cono", "=", self.opts["conum"]), ("rot_acno", "=",
            self.owner)]
        odr = "rot_trdt, rot_type, rot_refno"
        dat = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        data = []
        bals = 0
        for d in dat:
            bals = float(ASD(bals) + ASD(d[4]))
            data.append(d + [bals])
        col = (
            ("rot_trdt", "Trans-Date", 10, "D1", "N"),
            ("rot_type", "Typ", 3, ("XX", rctrtp), "N"),
            ("rot_refno", "Reference", 9, "Na", "N"),
            ("rot_desc", "Details", 30, "NA", "N"),
            ("rot_tramt", "Amount", 11.2, "SD", "N"),
            ("rot_taxamt", "VAT-Amount", 11.2, "SD", "N"),
            ("balance", "Balance", 15.2, "SD", "N"))
        self.otrn = SelectChoice(self.df.topPage1, None, col, data, wait=False,
            neww=False, live=False, lines=9)

    def showTenantTrans(self):
        try:
            self.ttrn.closeProcess()
        except:
            pass
        tab = ["rcatnt"]
        col = ["rtu_trdt", "rtu_type", "rtu_refno", "rtu_desc", "rtu_mtyp",
            "rtu_tramt", "rtu_taxamt"]
        whr = [("rtu_cono", "=", self.opts["conum"]), ("rtu_owner", "=",
            self.owner), ("rtu_code", "=", self.code), ("rtu_acno", "=",
            self.acno)]
        odr = "rtu_trdt, rtu_type, rtu_refno, rtu_mtyp"
        dat = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        data = []
        bals = 0
        for d in dat:
            bals = float(ASD(bals) + ASD(d[5]))
            data.append(d + [bals])
        col = (
            ("rtu_trdt", "Trans-Date", 10, "D1", "N"),
            ("rtu_type", "Typ", 3, ("XX", rctrtp), "N"),
            ("rtu_refno", "Reference", 9, "Na", "N"),
            ("rtu_desc", "Details", 35, "NA", "N"),
            ("rtu_mtyp", "Mov", 3, ("XX", rcmvtp), "N"),
            ("rtu_tramt", "Amount", 11.2, "SD", "N"),
            ("rtu_taxamt", "VAT-Amount", 11.2, "SD", "N"),
            ("balance", "Balance", 15.2, "SD", "N"))
        self.ttrn = SelectChoice(self.df.topPage2, None, col, data, wait=False,
            neww=False, live=False, lines=9)

    def showTenantBalance(self):
        bal = self.sql.getRec("rcatnt",
            cols=["round(sum(rtu_tramt),2)"], where=[("rtu_cono", "=",
            self.opts["conum"]), ("rtu_owner", "=", self.owner), ("rtu_code",
            "=", self.code), ("rtu_acno", "=", self.acno), ("rtu_cnum", "=",
            self.cnum), ("rtu_mtyp", "<>", 2)], limit=1)
        self.df.loadEntry("T", 2, 3, data=bal[0])

    def updateTables(self):
        curdt = int(self.trndat / 100)
        amt = self.trnamt
        vat = self.trnvat
        if self.trntyp in (1, 4):
            # Rental and Journal
            gltyp = 4
        elif self.trntyp == 2:
            # Receipt
            gltyp = 6
            bnk = amt
            amt = float(ASD(0) - ASD(amt))
            vat = float(ASD(0) - ASD(vat))
        elif self.trntyp == 3:
            # Payment
            gltyp = 2
            bnk = float(ASD(0) - ASD(amt))
        if self.df.pag == 1:
            # Owners Transaction
            accod = self.owner
            data = [self.opts["conum"], self.owner, self.trntyp, self.trnref,
                self.batno, self.trndat, amt, vat, curdt, self.trndet,
                self.vatcode, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcaowt", data=data)
            if self.glint == "Y":
                # General Ledger Transaction for Owner Control
                gld = "%7s %s" % (self.owner, self.trndet[:22])
                data = [self.opts["conum"], self.rcaown, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, amt, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
        else:
            # Tenants Transaction
            accod = self.code
            data = [self.opts["conum"], self.owner, self.code, self.acno,
                self.cnum, self.trntyp, self.trnref, self.batno, self.trndat,
                self.movtyp, amt, vat, curdt, self.trndet, self.vatcode, "",
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcatnt", data=data)
            if self.glint == "Y":
                gld = "%7s %7s %7s" % (self.owner, self.code, self.acno)
                if self.df.pag == 3 and self.movtyp == 2:
                    # General Ledger Transaction for Deposit Control
                    acc = self.rcadep
                else:
                    # General Ledger Transaction for Tenant Control
                    acc = self.rcatnt
                data = [self.opts["conum"], acc, curdt, self.trndat, gltyp,
                    self.trnref, self.batno, amt, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            self.showTenantBalance()
        if self.trntyp in (2, 3):
            if self.glint == "Y":
                # General Ledger Transaction for Bank Account
                data = [self.opts["conum"], self.glbnk, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, bnk, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            return
        if self.df.pag == 1 and self.df.pag == 1:
            # Owners Journal Entries (Unallocated)
            if self.glint == "Y":
                amt = float(ASD(0) - ASD(amt))
                data = [self.opts["conum"], self.rcaorx, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, amt, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            return
        if self.df.pag == 2 and self.movtyp == 1:
            # Rental and Commission Raised
            rta = float(ASD(0) - ASD(amt))
            rtv = float(ASD(0) - ASD(vat))
            des = "Rental on %s Premises" % self.code
            data = [self.opts["conum"], self.owner, self.trntyp, self.trnref,
                self.batno, self.trndat, rta, rtv, curdt, des, self.vatcode,
                "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcaowt", data=data)
            if self.glint == "Y":
                # General Ledger Transaction for Owner Control
                gld = "%7s Rental on %7s" % (self.owner, self.code)
                data = [self.opts["conum"], self.rcaown, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, rta, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            if self.crate:
                # If there is a Commission Rate on the Premises Record
                cma = float(ASD(0) - ASD(round((rta * self.crate / 100.0), 2)))
                vrte = getVatRate(self.sql, self.opts["conum"], self.taxdf,
                    self.trndat)
                if vrte is None:
                    vrte = 0.0
                cmv = round((cma * vrte / 100.0), 2)
                cmt = float(ASD(cma) + ASD(cmv))
                cma = float(ASD(0) - ASD(cma))
                tax = float(ASD(0) - ASD(cmv))
                des = "Commission @ %3.5s%s Inclusive" % (self.crate, "%")
                data = [self.opts["conum"], self.owner, 4, self.trnref,
                    self.batno, self.trndat, cmt, cmv, curdt, des, self.vatdf,
                    "", self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("rcaowt", data=data)
                if self.glint == "Y":
                    # Update Owner Control
                    gld = "%7s Commission Raised" % self.owner
                    data = [self.opts["conum"], self.rcaown, curdt,
                        self.trndat, gltyp, self.trnref, self.batno, cmt, 0,
                        gld, "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                    # Update Commission Account
                    data = [self.opts["conum"], self.rcacom, curdt,
                        self.trndat, gltyp, self.trnref, self.batno, cma, tax,
                        gld, "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                if self.taxdf:
                    # VAT Transaction (ctlvtf)
                    data = [self.opts["conum"], self.taxdf, "O", curdt, "R",
                        self.trntyp, self.batno, self.trnref, self.trndat,
                        self.acno, self.name, cma, tax, 0, self.opts["capnm"],
                        self.sysdtw, 0]
                    self.sql.insRec("ctlvtf", data=data)
                    if self.glint == "Y" and tax:
                        # Update VAT Control
                        data = [self.opts["conum"], self.convat, curdt,
                            self.trndat, gltyp, self.trnref, self.batno,
                            tax, 0, gld, "", "", 0, self.opts["capnm"],
                            self.sysdtw, 0]
                        self.sql.insRec("gentrn", data=data)
            return
        if self.df.pag == 3 and self.movtyp == 3:
            # Contract Fees
            amt = float(ASD(0) - ASD(amt) + ASD(vat))
            vat = float(ASD(0) - ASD(vat))
            if self.glint == "Y":
                # Update Contract Fee Account
                data = [self.opts["conum"], self.rcafee, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, amt, vat, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            if self.taxdf:
                # VAT Transaction (ctlvtf)
                data = (self.opts["conum"], self.vatcode, "O", curdt, "R",
                    self.trntyp, self.batno, self.trnref, self.trndat,
                    accod, self.trndet, amt, vat, 0, self.opts["capnm"],
                    self.sysdtw, 0)
                self.sql.insRec("ctlvtf", data=data)
                if self.glint == "Y":
                    # Update VAT Control
                    data = [self.opts["conum"], self.convat, curdt,
                        self.trndat, gltyp, self.trnref, self.batno, vat, 0,
                        gld, "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
            return
        if self.df.pag == 3 and self.movtyp == 4:
            # Services - Owner Recovery
            rta = float(ASD(0) - ASD(amt))
            rtv = float(ASD(0) - ASD(vat))
            des = "Services Recovery on %s" % self.code
            data = [self.opts["conum"], self.owner, self.trntyp, self.trnref,
                self.batno, self.trndat, rta, rtv, curdt, des, self.vatcode,
                "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("rcaowt", data=data)
            if self.glint == "Y":
                # General Ledger Transaction for Owner Control
                gld = "%7s Services Recovery" % self.owner
                data = [self.opts["conum"], self.rcaown, curdt, self.trndat,
                    gltyp, self.trnref, self.batno, rta, 0, gld, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
            return
        # Tenants Journal Entries (Unallocated)
        if self.glint == "Y":
            amt = float(ASD(0) - ASD(amt))
            data = [self.opts["conum"], self.rcatrx, curdt, self.trndat,
                gltyp, self.trnref, self.batno, amt, 0, gld, "", "", 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)

    def exitPage(self):
        if self.df.frt == "T" and self.df.pag == 0:
            self.df.closeProcess()
            self.opts["mf"].closeLoop()
        elif self.df.frt == "C" and self.df.pag == 3:
            self.df.focusField("C", 3, self.df.col)
        else:
            self.opts["mf"].dbm.commitDbase(ask=True)
            try:
                self.otrn.closeProcess()
            except:
                pass
            try:
                self.ttrn.closeProcess()
            except:
                pass
            self.df.selPage("Owner")
            self.df.focusField("T", 0, 1)

    def allNotes(self):
        if self.df.frt == "C":
            state = self.df.disableButtonsTags()
            self.df.setWidget(self.df.mstFrame, state="hide")
            if self.df.pag == 1:
                key = "%s" % self.owner
            else:
                key = "%7s%7s%s" % (self.owner, self.code, self.acno)
            NotesCreate(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], self.opts["capnm"], "RCA",
                key, commit=False)
            self.df.setWidget(self.df.mstFrame, state="show")
            self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def allStmnt(self):
        if self.df.frt == "C" and self.df.pag == 1:
            self.sargs = [self.owner]
            self.repModule("rc3050")
        elif self.df.frt == "C" and self.df.pag == 2:
            self.sargs = [self.owner, self.code, self.acno]
            self.repModule("rc3060")
        else:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def repModule(self, mod):
        self.exit = False
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Date and Printer Selection",)
        fld = (
            (("T",0,0,0),"ID1",10,"Statement Date","",
                self.sysdtw,"N",self.doPrtDate,None,None,("efld",)),)
        self.st = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doPrtEnd,"y"),), txit=(self.doPrtExit,),
            view=("N","V"), mail=("B","Y"))
        self.st.mstFrame.wait_window()
        if not self.exit:
            self.sargs.extend([self.stdtw, self.stdtd, self.st.repprt,
                self.st.repeml])
            popt = {"mf": self.opts["mf"], "conum": self.opts["conum"],
                "conam": self.opts["conam"], "capnm": self.opts["capnm"],
                "args": self.sargs}
            runModule(mod, **popt)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrtDate(self, frt, pag, r, c, p, i, w):
        self.stdtw = w
        self.stdtd = self.st.t_disp[0][0][0]

    def doPrtEnd(self):
        self.doPrtClose()

    def doPrtExit(self):
        self.exit = True
        self.doPrtClose()

    def doPrtClose(self):
        self.st.closeProcess()

# vim:set ts=4 sw=4 sts=4 expandtab:
