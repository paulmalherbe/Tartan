"""
SYNOPSIS
    General Ledger Bank Reconciliation Codes.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import chkGenAcc

class gl1060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        # Create SQL Object
        self.sql = Sql(self.opts["mf"].dbm, ["assgrp", "crsmst", "ctlctl",
            "ctlmst", "ctlvmf", "drsmst", "drschn", "genint", "genmst",
            "genrcc", "rtlprm"], prog=self.__class__.__name__)
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
        #
        self.gc = GetCtl(self.opts["mf"])
        return True

    def mainProcess(self):
        ctl = {
            "stype": "R",
            "tables": ("ctlctl", "genmst"),
            "cols": (
                ("ctl_code", "", 0, "Ctl-Code"),
                ("ctl_conacc", "", 0, "G/L-Num"),
                ("glm_desc", "", 30, "Description")),
            "where": [
                ("ctl_cono", "=", self.opts["conum"]),
                ("ctl_code", "like", "bank_%"),
                ("glm_cono=ctl_cono",),
                ("glm_acno=ctl_conacc",)],
            "index": 1}
        rcc = {
            "stype": "R",
            "tables": ("genrcc",),
            "cols": (
                ("grc_memo", "", 0, "Code"),
                ("grc_desc1", "", 0, "Details"),
                ("grc_rtn", "", 0, "R"),
                ("grc_acoy", "", 0, "Coy"),
                ("grc_aacc", "", 0, "Acc-Num"),
                ("grc_acrs", "", 0, "Crs-Acc"),
                ("grc_achn", "", 0, "Chn"),
                ("grc_adrs", "", 0, "Drs-Acc"),
                ("grc_vat", "", 0, "V")),
            "where": [("grc_cono", "=", self.opts["conum"])],
            "whera": [["T", "grc_acno", 0]]}
        rct = {
            "stype": "R",
            "tables": ("genrct",),
            "cols": (
                ("grt_memo", "", 75, "Details"),
                ("grt_amount", "SD", 13.2, "Value")),
            "where": [
                ("grt_cono", "=", self.opts["conum"]),
                ("grt_flag", "=", "N")],
            "whera": [["T", "grt_acno", 0, 0]],
            "group": "grt_memo",
            "order": "grt_memo",
            "comnd": self.doSameField}
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
            "whera": [["T", "glm_cono", 7]]}
        chn = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "whera": [["T", "chm_cono", 7]]}
        self.crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y"),
                ("crm_add1", "", 0, "Address Line 1")),
            "where": [("crm_stat", "<>", "X")],
            "whera": [["T", "crm_cono", 7]]}
        self.drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1")),
            "where": [("drm_stat", "<>", "X")],
            "whera": [
                ["T", "drm_cono", 7],
                ["T", "drm_chain", 11]]}
        vat = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "Acc-Num"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "whera": [["T", "vtm_cono", 7]]}
        r1s = (("Payment","P"), ("Receipt","R"))
        r2s = (("Oldest","O"), ("Current","C"))
        fld = [
            [("T",0,0,0),"IUI",7,"Bank Account","",
                "","Y",self.doAccNum,ctl,None,None],
            (("T",0,0,0),"ONA",30,""),
            [("T",0,1,0),"IUI",5,"Memo Code","Memo Code (Blank for Next)",
                "","Y",self.doMemo,rcc,None,None],
            [("T",0,2,0),"INA",50,"Memo Desc Contains","",
                "","N",self.doDesc1,rct,self.doDelete,("notblank",)],
            (("T",0,3,0),"INA",50,"      and Contains","Desc Also Contains",
                "","N",self.doDesc2,rct,None,None),
            (("T",0,4,0),"INA",50,"      and Contains","Desc Also Contains",
                "","N",self.doDesc3,rct,None,None),
            (("T",0,5,0),("IRB",r1s),0,"Transaction Type","",
                "P","N",self.doTypCod,None,None,None),
            (("T",0,6,0),"IUI",7,"Allocation Company","",
                self.opts["conum"],"N",self.doAllCoy,coy,None,("notzero",)),
            (("T",0,6,0),"ONA",30,""),
            (("T",0,7,0),"IUI",7,"Allocation Account","",
                "","N",self.doAllAcc,glm,None,("notzero",)),
            (("T",0,7,0),"ONA",30,""),
            [["T",0,8,0],"IUI",3,"Chn","Chain Store Code",
                0,"N",self.doDrsChn,chn,None,("efld",)],
            (("T",0,8,0),"ONA",30,""),
            [("T",0,9,0),"INA",7,"Acc-Num","Account Number",
                "","N",self.doCrsDrsAcc,self.crm,None,("notblank",)],
            (("T",0,9,0),"ONA",30,""),
            (("T",0,10,0),("IRB",r2s),0,"Ageing Code","",
                "O","N",self.doCrsDrsAge,None,None,None,None,
                """
The Ageing Codes are as follows:

Oldest  - Automatically age against the oldest outstanding transactions.

Current - Do not age the transaction.
"""),
            (("T",0,11,0),"INA",1,"Vat Code","",
                "","N",self.doVatCod,vat,None,None)]
        but = [
            ("Cancel",None,self.doCancel,0,("T",0,4),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None)]
        if "args" in self.opts:
            for f in (0, 2, 3):
                if f == 3:
                    fld[f][4] += "(noesc)"
                else:
                    fld[f][7] = None
                fld[f][8] = None
                fld[f][9] = None
            del but[0]
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        if "args" in self.opts:
            foc = False
        else:
            foc = True
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt, focus=foc)
        if "args" in self.opts:
            self.df.loadEntry("T", 0,  0, data=self.opts["args"][0])
            self.doAccNum("T", 0, 0, 1, 0, 0, self.opts["args"][0])
            self.df.loadEntry("T", 0,  2, data=0)
            self.doMemo("T", 0, 0, 3, 2, 2, 0)
            self.df.loadEntry("T", 0,  3, data=self.opts["args"][1][2])
            self.df.focusField("T", 0, 4)

    def doAccNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["ctlctl", "genmst"], cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=", w),
            ("ctl_cono=glm_cono",), ("ctl_conacc=glm_acno",), ("ctl_code",
            "like", "bank_%")], limit=1)
        if not acc:
            return "Invalid Bank Account"
        self.acno = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doSameField(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry("T", 0, self.df.pos, data=w[0])
        self.df.focusField("T", 0, self.df.col)

    def doMemo(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.sql.getRec("genrcc", cols=["max(grc_memo)"],
                where=[("grc_cono", "=", self.opts["conum"]), ("grc_acno", "=",
                self.acno)], limit=1)
            if not w or not w[0]:
                self.memo = 1
            else:
                self.memo = w[0] + 1
            self.df.loadEntry(frt, pag, p, data=self.memo)
        else:
            self.memo = w
        self.old = self.sql.getRec("genrcc", where=[("grc_cono", "=",
            self.opts["conum"]), ("grc_acno", "=", self.acno), ("grc_memo",
            "=", self.memo)], limit=1)
        if not self.old:
            self.new = "y"
        else:
            self.new = "n"
            col = self.sql.genrcc_col
            self.desc1 = self.old[col.index("grc_desc1")]
            self.desc2 = self.old[col.index("grc_desc2")]
            self.desc3 = self.old[col.index("grc_desc3")]
            self.opts["rtn"] = self.old[col.index("grc_rtn")]
            self.acoy = self.old[col.index("grc_acoy")]
            self.aacc = self.old[col.index("grc_aacc")]
            self.acrs = self.old[col.index("grc_acrs")]
            self.achn = self.old[col.index("grc_achn")]
            self.aage = self.old[col.index("grc_aage")]
            self.adrs = self.old[col.index("grc_adrs")]
            self.vat = self.old[col.index("grc_vat")]
            self.df.loadEntry(frt, pag, 3, data=self.desc1)
            self.df.loadEntry(frt, pag, 4, data=self.desc2)
            self.df.loadEntry(frt, pag, 5, data=self.desc3)
            self.df.loadEntry(frt, pag, 6, data=self.opts["rtn"])
            self.df.loadEntry(frt, pag, 7, data=self.acoy)
            self.df.loadEntry(frt, pag, 8, data=self.getCoyName())
            self.df.loadEntry(frt, pag, 9, data=self.aacc)
            self.df.loadEntry(frt, pag, 10, data=self.getAccDesc())
            # Creditor and Debtor Details
            if self.acrs:
                self.crsdrs = "crs"
                self.df.loadEntry(frt, pag, 11, data=0)
                self.df.loadEntry(frt, pag, 12, data="")
                self.df.loadEntry(frt, pag, 13, data=self.acrs)
                self.df.loadEntry(frt, pag, 14, data=self.getCrsName())
                self.df.loadEntry(frt, pag, 15, data=self.aage)
            elif self.adrs:
                self.crsdrs = "drs"
                self.df.loadEntry(frt, pag, 11, data=self.achn)
                if self.achn:
                    self.df.loadEntry(frt, pag, 12, data=self.getChainName())
                else:
                    self.df.loadEntry(frt, pag, 12, data="")
                self.df.loadEntry(frt, pag, 13, data=self.adrs)
                self.df.loadEntry(frt, pag, 14, data=self.getDrsName())
                self.df.loadEntry(frt, pag, 15, data=self.aage)
            else:
                self.crsdrs = None
                self.df.loadEntry(frt, pag, 11, data=0)
                self.df.loadEntry(frt, pag, 12, data="")
                self.df.loadEntry(frt, pag, 13, data="")
                self.df.loadEntry(frt, pag, 14, data="")
                self.df.loadEntry(frt, pag, 15, data="")
            # VAT Code
            self.df.loadEntry(frt, pag, 16, data=self.vat)

    def doDesc1(self, frt, pag, r, c, p, i, w):
        self.desc1 = w

    def doDesc2(self, frt, pag, r, c, p, i, w):
        self.desc2 = w
        if not self.desc2:
            self.desc3 = ""
            self.df.loadEntry(frt, pag, p+1, data=self.desc3)
            if "args" in self.opts:
                if self.opts["args"][1][-1] < 0:
                    self.opts["rtn"] = "P"
                else:
                    self.opts["rtn"] = "R"
                self.df.loadEntry(frt, pag, p+2, data=self.opts["rtn"])
                return "sk2"
            return "sk1"

    def doDesc3(self, frt, pag, r, c, p, i, w):
        self.desc3 = w
        if "args" in self.opts:
            if self.opts["args"][1][-1] < 0:
                self.opts["rtn"] = "P"
            else:
                self.opts["rtn"] = "R"
            self.df.loadEntry(frt, pag, p+1, data=self.opts["rtn"])
            return "sk1"

    def doTypCod(self, frt, pag, r, c, p, i, w):
        self.opts["rtn"] = w
        if not self.incoac:
            self.acoy = self.opts["conum"]
            if self.doChkLoadCtls():
                return "rf"
            else:
                self.df.loadEntry(frt, pag, p+1, data=self.acoy)
                self.df.loadEntry(frt, pag, p+2, data=self.getCoyName())
                return "sk2"

    def doAllCoy(self, frt, pag, r, c, p, i, w):
        self.acoy = w
        name = self.getCoyName()
        if not name:
            return "Invalid Company Number"
        self.df.loadEntry(frt, pag, p+1, data=name)
        return self.doChkLoadCtls()

    def doChkLoadCtls(self):
        # Check for Intercompany Records
        if self.acoy != self.opts["conum"]:
            acc = self.sql.getRec("genint", where=[("cti_cono", "=",
                self.opts["conum"]), ("cti_inco", "=", self.acoy)], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 1"
            acc = self.sql.getRec("genint", where=[("cti_cono", "=",
                self.acoy), ("cti_inco", "=", self.opts["conum"])], limit=1)
            if not acc:
                return "Invalid Company, No Intercompany Record 2"
        # Get Company Details
        ctlmst = self.gc.getCtl("ctlmst", self.acoy)
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
        # Check for Control Records e.g. VAT and Discounts
        self.ctlctl = self.gc.getCtl("ctlctl", self.acoy)
        if not self.ctlctl:
            return "rf"
        ctls = ["vat_ctl"]
        # Load Crs Integration
        if mod.count("CR"):
            ctl = self.gc.getCtl("crsctl", self.acoy)
            if not ctl:
                return "rf"
            self.crs_gl = ctl["ctc_glint"]
            if self.crs_gl == "Y":
                ctls.extend(["crs_ctl", "dis_rec"])
        else:
            self.crs_gl = "N"
        # Load Drs Integration and Chain Store Flag
        if mod.count("DR"):
            ctl = self.gc.getCtl("drsctl", self.acoy)
            if not ctl:
                return "rf"
            self.drs_gl = ctl["ctd_glint"]
            self.drs_ch = ctl["ctd_chain"]
            if self.drs_gl == "Y":
                ctls.extend(["drs_ctl", "dis_all"])
        else:
            self.drs_gl = "N"
        if self.gc.chkRec(self.acoy, self.ctlctl, ctls):
            return "rf"

    def doAllAcc(self, frt, pag, r, c, p, i, w):
        if self.acoy == self.opts["conum"] and w == self.acno:
            return "This is the Bank Account Number"
        ctl = True
        self.crsdrs = False
        if self.crs_gl == "Y" and w == self.ctlctl["crs_ctl"]:
            self.crsdrs = "crs"
            self.df.topf[0][p+4][8] = self.crm
        elif self.drs_gl == "Y" and w == self.ctlctl["drs_ctl"]:
            self.crsdrs = "drs"
            self.df.topf[0][p+4][8] = self.drm
        if self.crsdrs:
            ctl = False
        chk = chkGenAcc(self.opts["mf"], self.acoy, w, ctl=ctl)
        if type(chk) is str:
            return chk
        self.aacc = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        if self.crsdrs:
            if self.crsdrs == "crs" or self.drs_ch == "N":
                self.achn = 0
                self.df.topf[0][p+2][1] = "OUI"
                self.df.loadEntry(frt, pag, p+2, data=self.achn)
                self.df.loadEntry(frt, pag, p+3, data="")
                return "sk3"
            elif self.crsdrs == "drs":
                self.df.topf[0][p+2][1] = "IUI"
                return "sk1"
        else:
            self.acrs = ""
            self.achn = 0
            self.adrs = ""
            self.aage = ""
            self.df.loadEntry(frt, pag, p+2, data=0)
            self.df.loadEntry(frt, pag, p+3, data="")
            self.df.loadEntry(frt, pag, p+4, data="")
            self.df.loadEntry(frt, pag, p+5, data="")
            self.df.loadEntry(frt, pag, p+6, data="")
            if not self.df.t_work[pag][0][p+7]:
                if chk[2]:
                    self.df.loadEntry(frt, pag, p+7, data=chk[2])
                else:
                    self.df.loadEntry(frt, pag, p+7, data=self.taxdf)
            return "sk6"

    def doDrsChn(self, frt, pag, r, c, p, i, w):
        self.achn = w
        name = self.getChainName()
        if not name:
            return "Invalid Account Number"
        self.df.loadEntry(frt, pag, p+1, data=name)

    def doCrsDrsAcc(self, frt, pag, r, c, p, i, w):
        if self.crsdrs == "crs":
            self.acrs = w
            name = self.getCrsName()
        else:
            self.adrs = w
            name = self.getDrsName()
        if not name:
            return "Invalid Account Number %s" % self.crsdrs.capitalize()
        if name[1] == "X":
            return "Invalid Account %s, Redundant" % self.crsdrs.capitalize()
        self.df.loadEntry(frt, pag, p+1, data=name[0])

    def doCrsDrsAge(self, frt, pag, r, c, p, i, w):
        self.aage = w
        self.vat = "N"
        self.df.loadEntry(frt, pag, p+1, data=self.vat)
        return "sk1"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.acoy), ("vtm_code", "=", w)],
            limit=1)
        if not vat:
            return "Invalid VAT Code"
        self.vat = w

    def doDelete(self):
        self.sql.delRec("genrcc", where=[("grc_cono", "=", self.opts["conum"]),
            ("grc_acno", "=", self.acno), ("grc_memo", "=", self.memo)])

    def doEnd(self):
        data = [self.opts["conum"], self.acno, self.memo, self.desc1,
            self.desc2, self.desc3, self.opts["rtn"], self.acoy, self.aacc]
        if self.crsdrs:
            if self.crsdrs == "crs":
                data.extend([self.acrs, 0, "", self.aage, self.vat])
            else:
                data.extend(["", self.achn, self.adrs, self.aage, self.vat])
        else:
            data.extend(["", 0, "", "", self.vat])
        if self.new == "y":
            self.sql.insRec("genrcc", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.genrcc_col
            data.append(self.old[col.index("grc_xflag")])
            self.sql.updRec("genrcc", data=data, where=[("grc_cono",
                "=", self.opts["conum"]), ("grc_acno", "=", self.acno),
                ("grc_memo", "=", self.memo)])
        if "args" in self.opts:
            self.doExit()
        else:
            for x in range(2, self.df.topq[0]):
                self.df.loadEntry("T", 0, x, data="")
            self.df.focusField("T", 0, 3)

    def getCoyName(self):
        coy = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", self.acoy)], limit=1)
        if coy:
            return coy[0]

    def getAccDesc(self):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.acoy), ("glm_acno", "=", self.aacc)],
            limit=1)
        if acc:
            return acc[0]

    def getCrsName(self):
        acc = self.sql.getRec("crsmst", cols=["crm_name", "ctm_stat"],
            where=[("crm_cono", "=", self.acoy), ("crm_acno", "=", self.acrs)],
            limit=1)
        if acc:
            return acc

    def getChainName(self):
        acc = self.sql.getRec("drschn", cols=["chm_name"],
            where=[("chm_cono", "=", self.acoy), ("chm_chain", "=",
            self.achn)], limit=1)
        if acc:
            return acc[0]

    def getDrsName(self):
        acc = self.sql.getRec("drsmst", cols=["drm_name", "drm_stat"],
            where=[("drm_cono", "=", self.acoy), ("drm_chain", "=", self.achn),
            ("drm_acno", "=", self.adrs)], limit=1)
        if acc:
            return acc

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
