"""
SYNOPSIS
    General Ledger Control Accounts Maintenance.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog

class glc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "genmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        # -------------------------------
        # General Ledger Control Records
        # -------------------------------
        # Get Company Details
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        # Standard Controls
        self.glctrl = [
            ("bank_1", "Bank Control 1"),
            ("bank_2", "Bank Control 2"),
            ("bank_3", "Bank Control 3"),
            ("bank_4", "Bank Control 4"),
            ("bank_5", "Bank Control 5"),
            ("bank_6", "Bank Control 6"),
            ("bank_7", "Bank Control 7"),
            ("bank_8", "Bank Control 8"),
            ("bank_9", "Bank Control 9"),
            ("bank_10", "Bank Control 10"),
            ("p_cash", "Petty Cash Control"),
            ("crs_ctl", "Creditors Control"),
            ("drs_ctl", "Debtors Control"),
            ("ret_inc", "Retained Income"),
            ("vat_ctl", "VAT Control")]
        # Check for Integrated Systems
        mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mod.append(ctlmst["ctm_modules"][x:x+2])
        # Load Systems Integration
        if mod.count("AR"):
            assctl = gc.getCtl("assctl", self.opts["conum"], error=False)
            if assctl and assctl["cta_glint"] == "Y":
                self.glctrl.extend([
                    ("ass_sls", "Sale of Assets")])
        if mod.count("BK"):
            bkmctl = gc.getCtl("bkmctl", self.opts["conum"], error=False)
            if bkmctl and bkmctl["cbk_glint"] == "Y":
                self.glctrl.extend([
                    ("bkm_ctl", "Bookings Control"),
                    ("bkm_chq", "Cheques Received"),
                    ("bkm_csh", "Cash Received"),
                    ("bkm_ccg", "Cancellation Fee")])
                if not mod.count("DR"):
                    self.glctrl.extend([
                        ("dis_all", "Discount Allowed")])
        if mod.count("CR"):
            crsctl = gc.getCtl("crsctl", self.opts["conum"], error=False)
            if crsctl and crsctl["ctc_glint"] == "Y":
                self.glctrl.extend([
                    ("dis_rec", "Discount Received")])
        if mod.count("CS"):
            cshctl = gc.getCtl("cshctl", self.opts["conum"], error=False)
            if cshctl and cshctl["ccc_glint"] == "Y":
                self.glctrl.extend([
                    ("csh_ctl", "Cash Control")])
        if mod.count("DR"):
            drsctl = gc.getCtl("drsctl", self.opts["conum"], error=False)
            if drsctl and drsctl["ctd_glint"] == "Y":
                self.glctrl.extend([
                    ("dis_all", "Discount Allowed")])
        if mod.count("LN"):
            lonctl = gc.getCtl("lonctl", self.opts["conum"], error=False)
            if lonctl and lonctl["cln_glint"] == "Y":
                self.glctrl.extend([
                    ("lon_ctl", "Loans Control"),
                    ("int_pay", "Interest Paid"),
                    ("int_rec", "Interest Received")])
        if mod.count("ML"):
            memctl = gc.getCtl("memctl", self.opts["conum"], error=False)
            if memctl and memctl["mcm_glint"] == "Y":
                self.glctrl.extend([
                    ("mem_ctl", "Members Control"),
                    ("mem_pen", "Members Penalties")])
        if mod.count("RC"):
            rcactl = gc.getCtl("rcactl", self.opts["conum"], error=False)
            if rcactl and rcactl["cte_glint"] == "Y":
                self.glctrl.extend([
                    ("rca_com", "Commission Raised"),
                    ("rca_dep", "Deposits Control"),
                    ("rca_fee", "Contract Fees"),
                    ("rca_own", "Owners Control"),
                    ("rca_orx", "Owners Charges"),
                    ("rca_tnt", "Tenants Control"),
                    ("rca_trx", "Tenants Charges")])
        if mod.count("ST"):
            strctl = gc.getCtl("strctl", self.opts["conum"], error=False)
            if strctl and strctl["cts_glint"] == "Y":
                self.glctrl.extend([
                    ("stk_soh", "Stock on Hand"),
                    ("stk_susp", "Stock Reconciliation")])
        if mod.count("WG") or mod.count("SL"):
            wagctl = gc.getCtl("wagctl", self.opts["conum"], error=False)
            if wagctl and wagctl["ctw_glint"] == "Y":
                self.glctrl.extend([
                    ("wag_ctl", "Salaries Control"),
                    ("wag_slc", "Staff Loans Control"),
                    ("wag_sli", "Staff Loans Interest")])
        return True

    def drawDialog(self):
        ctl = {
            "stype": "C",
            "titl": "Select Control",
            "head": ("Code", "Description"),
            "typs": (("NA", 10), ("NA", 30)),
            "data": self.glctrl}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        r1s = (
            ("None", "N"),
            ("OFX", "O"),
            ("QIF", "Q"),
            ("S/Bank Online", "S"))
        r2s = (
            ("None", "N"),
            ("CCYYMMDD", "A"),
            ("DDMMCCYY", "B"),
            ("MMDD(CC)YY", "C"))
        fld = (
            (("T",0,0,0),"INA",10,"Code","Control Code",
                "","Y",self.doCode,ctl,None,None),
            (("T",0,0,25),"ONA",30,"Description"),
            (("T",0,1,0),"IUI",7,"G/L Acc-Num","G/L Account Number",
                "","N",self.doAccNum,glm,self.doDelete,("notzero",)),
            (("T",0,1,25),"ONA",30,"Description"),
            (("T",0,2,0),"INA",16,"Bank Account","Bank Account Number",
                "","N",self.doImpBnk,None,None,("efld",)),
            (("T",0,3,0),("IRB",r1s),0,"Import Format","",
                "N","N",self.doImpFmt,None,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Date Format","",
                "A","N",self.doDteFmt,None,None,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,3),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,3),("T",0,0)),
            ("Print",None,self.doPrint,0,("T",0,1),("T",0,2)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        d1 = ""
        for ctl in self.glctrl:
            if self.code in ctl:
                d1 = ctl[1]
                break
        if not d1:
            return "Invalid Control Code"
        self.df.loadEntry(frt, pag, p+1, data=d1)
        self.acc = self.sql.getRec("ctlctl", where=[("ctl_cono", "=",
            self.opts["conum"]), ("ctl_code", "=", self.code)], limit=1)
        if not self.acc:
            self.new = "y"
        else:
            self.new = "n"
            col = self.sql.ctlctl_col
            desc = self.readAcno(self.acc[col.index("ctl_conacc")])
            if not desc:
                desc = [""]
            self.df.loadEntry(frt, pag, p+2,
                    data=self.acc[col.index("ctl_conacc")])
            self.df.loadEntry(frt, pag, p+3,
                    data=desc[0])
            self.df.loadEntry(frt, pag, p+4,
                    data=self.acc[col.index("ctl_bankac")])
            self.df.loadEntry(frt, pag, p+5,
                    data=self.acc[col.index("ctl_impfmt")])
            self.df.loadEntry(frt, pag, p+6,
                    data=self.acc[col.index("ctl_dtefmt")])

    def doDelete(self):
        self.sql.delRec("ctlctl", where=[("ctl_cono", "=", self.opts["conum"]),
            ("ctl_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccNum(self, frt, pag, r, c, p, i, w):
        desc = self.readAcno(w)
        if not desc:
            return "Invalid Account Number"
        self.df.loadEntry(frt, pag, p+1, data=desc[0])
        if self.code[:4] != "bank":
            self.impfmt = "N"
            self.bankac = ""
            self.dtefmt = "N"
            return "nd"

    def readAcno(self, acno):
        self.acno = acno
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            self.acno)], limit=1)
        return acc

    def doImpBnk(self, frt, pag, r, c, p, i, w):
        self.bankac = w
        if not self.bankac:
            self.impfmt = "N"
            self.dtefmt = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.impfmt)
            self.df.loadEntry(frt, pag, p+2, data=self.dtefmt)
            return "sk2"

    def doImpFmt(self, frt, pag, r, c, p, i, w):
        self.impfmt = w
        if self.impfmt == "N":
            self.dtefmt = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.dtefmt)
            return "nd"
        self.df.loadEntry(frt, pag, p+1, data="A")

    def doDteFmt(self, frt, pag, r, c, p, i, w):
        if w not in ("A", "B", "C"):
            return "Invalid Date Format"
        self.dtefmt = w

    def doEnd(self):
        data = [self.opts["conum"], self.code, self.df.t_work[0][0][1],
            self.acno, self.bankac, self.impfmt, self.dtefmt]
        if self.new == "y":
            self.sql.insRec("ctlctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.ctlctl_col
            data.append(self.acc[col.index("ctl_xflag")])
            self.sql.updRec("ctlctl", data=data, where=[("ctl_cono",
                "=", self.opts["conum"]), ("ctl_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        table = ["ctlctl"]
        heads = ["General Ledger Control Accounts"]
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, "hide")
        RepPrt(self.opts["mf"], name="glc110", tables=table, heads=heads,
            where=[("ctl_cono", "=", self.opts["conum"])], order="ctl_code",
            prtdia=(("Y","V"),("Y","N")))
        self.df.setWidget(self.df.mstFrame, "show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
