"""
SYNOPSIS
    Sales Invoicing Data Capture.

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
from TartanClasses import AgeAll, ASD, Balances, CCD, GetCtl, PrintInvoice
from TartanClasses import PwdConfirm, Sql, TartanDialog
from tartanFunctions import callModule, copyList, getCost, getSell, getVatRate

class si2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.exit = False
            self.selectPrinter()
            if not self.exit:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        # Set Table Fields
        tables = [
            "ctlsys", "ctlmst", "ctlmes", "ctlrep", "ctlvrf", "ctlvtf",
            "drschn", "drsmst", "drstrn", "drsdel", "genmst", "gentrn",
            "strgrp", "strmf1", "strmf2", "strgmu", "strcmu", "strrcp",
            "strtrn", "struoi", "slsctl", "slsiv1", "slsiv2", "slsiv3",
            "tplmst"]
        self.sql = Sql(self.opts["mf"].dbm, tables,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        # Set, Check Controls
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.drgl = drsctl["ctd_glint"]
        self.chns = drsctl["ctd_chain"]
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.stgl = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        if self.drgl == "Y" or self.stgl == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.drgl == "Y":
                ctls = ["drs_ctl", "vat_ctl"]
                if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                    return
                self.dctl = ctlctl["drs_ctl"]
                self.vctl = ctlctl["vat_ctl"]
            if self.stgl == "Y":
                ctls = ["stk_soh", "stk_susp"]
                if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                    return
                self.soh = ctlctl["stk_soh"]
                self.ssp = ctlctl["stk_susp"]
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.delnos = slsctl["ctv_delnos"]
        self.delval = slsctl["ctv_delval"]
        self.dtpl = slsctl["ctv_tplnam"]
        ####################################################################
        # Check for Password Requirement to Invoice and Credit Note Creation
        ####################################################################
        cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
            system="INV", code="Invoices")
        if cf.flag == "no":
            self.allow = "N"
        else:
            self.allow = "Y"
        ####################################################################
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def selectPrinter(self):
        tit = ("Date and Printer Selection",)
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "I"),
                ("tpm_system", "=", "INV")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        fld = [
            (("T",0,0,0),"INA",20,"Template Name","",
                self.dtpl,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),"ID1",10,"Document Date","",
                self.sysdtw,"N",self.doDocDate,None,None,("efld",))]
        if self.delnos == "Y":
            fld.append(
                (("T",0,2,0),("IRB",r1s),0,"Delivery Notes","Delivery Notes",
                    "Y","N",self.doDelNote,None,None,None))
        else:
            self.dnote = "N"
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doPrtClose,"y"),), txit=(self.doPrtExit,),
            view=("N","P"), mail=("N","Y","Y"))
        self.opts["mf"].startLoop()

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "INV")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doDocDate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not In Financial Period"
        self.trdt = w
        self.trdd = self.pr.t_disp[0][0][1]
        self.curdt = int(self.trdt / 100)
        self.batch = "S%s" % self.curdt

    def doDelNote(self, frt, pag, r, c, p, i, w):
        self.dnote = w

    def doPrtExit(self):
        self.exit = True
        self.doPrtClose()

    def doPrtClose(self):
        self.pr.closeProcess()
        self.opts["mf"].closeLoop()

    def mainProcess(self):
        rep = {
            "stype": "R",
            "tables": ("ctlrep",),
            "cols": (
                ("rep_code", "", 0, "Rep"),
                ("rep_name", "", 0, "Name", "Y")),
            "where": [("rep_cono", "=", self.opts["conum"])]}
        chn = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": [
                ("chm_chain", "", 0, "Chn"),
                ("chm_name", "", 0, "Name", "Y")],
            "where": [("chm_cono", "=", self.opts["conum"])],
            "screen": self.opts["mf"].body}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": [
                ("drm_chain", "", 0, "Chn"),
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name","Y"),
                ("drm_add1", "", 0, "Address Line 1")],
            "where": [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_stat", "<>", "X")],
            "screen": self.opts["mf"].body,
            "index": 1}
        self.grps = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])],
            "screen": self.opts["mf"].body}
        self.cods = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_group", "", 0, "Grp"),
                ("st1_code", "", 0, "Product-Code"),
                ("st1_type", "", 0, "T"),
                ("st1_desc", "", 0, "Description","Y")),
            "where": [],
            "screen": self.opts["mf"].body,
            "index": 1}
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "Grp"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])],
            "order": "srl_loc",
            "autoc": False}
        r1s = (
            ("Invoice","I"),
            ("Credit-Note","C"),
            ("Sales-Order","O"),
            ("Works-Order","W"),
            ("Quote","Q"))
        r2s = (("Account","A"),("Cash","C"))
        fld = [
            [["T",0,0,0],("IRB",r1s),0,"Type","Transaction Type",
                "I","Y",self.doTyp,None,None,None],
            [["T",0,1,0],("IRB",r2s),0,"Mode ","Mode of Payment",
                "A","Y",self.doMod,None,None,None],
            [["T",0,2,0],"IUI",3,"Chain","Chain Store",
                "","N",self.doChn,chn,None,None],
            [["T",0,2,0],"ONA",30,""],
            [["T",0,3,0],"INA",7,"Acc-Num","Account Number",
                "","N",self.doAcc,drm,None,None],
            [["T",0,3,0],"ONA",30,""],
            [["T",0,4,0],"INa",3,"Rep","Rep Number",
                "","N",self.doRep,rep,None,None],
            [["T",0,4,0],"ONA",30,""]]
        if self.chns == "N":
            self.chain = 0
            del drm["cols"][0]
            drm["index"] = 0
            del fld[2]
            del fld[2]
            fld[2][0][2] = 2
            fld[3][0][2] = 2
            fld[4][0][2] = 3
            fld[5][0][2] = 3
        else:
            drm["whera"] = [["T", "drm_chain", 2]]
        if self.plevs == 1:
            self.opts["level"] = 1
        else:
            r3s = [("One","1"),("Two","2")]
            if self.plevs > 2:
                r3s.append(("Three","3"))
            if self.plevs > 3:
                r3s.append(("Four","4"))
            if self.plevs > 4:
                r3s.append(("Five","5"))
            if self.chns == "Y":
                fld.append([("T",0,5,0),("IRB",r3s),0,"Level",
                "Price Level","","Y",self.doLev,None,None,None])
            else:
                fld.append([("T",0,4,0),("IRB",r3s),0,"Level",
                "Price Level","","Y",self.doLev,None,None,None])
        fld.extend((
            (("C",0,0,0),"INA",3,"Grp","Product Group(noesc)",
                "r","Y",self.doGrp,self.grps.copy(),None,None),
            (("C",0,0,1),"INA",(20,20),"Product-Code","Product Code",
                "","N",self.doCod,self.cods.copy(),None,None),
            (("C",0,0,2),"ITv",30,"Description","",
                "","N",self.doDes,None,None,None),
            (("C",0,0,3),"IUA",1,"L","Location",
                "","N",self.doLoc,loc,None,None),
            (("C",0,0,4),"ISD",11.2,"Quantity","",
                1,"N",self.doQty,None,None,("notzero",)),
            (("C",0,0,5),"IUA",1,"V","V.A.T. Code",
                "I","N",self.doVat,None,None,("notblank",)),
            (("C",0,0,6),"IUD",10.2,"Price","Price",
                "","N",self.doPri,None,None,None),
            (("C",0,0,7),"IUD",6.2,"Dis-%","Discount Percentage",
                "","N",self.doDis,None,None,None),
            (("C",0,0,8),"OSD",11.2,"Value")))
        self.row = (15,)
        self.but = (
            ("Cancel",None,self.doCancel,1,("C",0,1),("T",0,1),
                "Cancel the Document"),
            ("DelAdd",None,self.doDelAdd,1,("C",0,1),("T",0,1),
                "Enter a Delivery Address"),
            ("Ribbon",None,self.doRibbon,1,("C",0,1),("T",0,1),
                "Enter Ribbon Line Details"),
            ("Message",None,self.doMessage,1,("C",0,1),("T",0,1),
                "Enter a Message"),
            ("Edit",None,self.doEdit,0,("C",0,1),(("T",0,1),("C",0,2)),
                "Display All Lines and Allow Editing"),
            ("Reprint",None,self.doReprnt,0,("T",0,1),(("T",0,2),("T",0,0)),
                "Reprint Documents"),
            ("DrsMaint",None,self.doDrsMaint,0,("T",0,3),("T",0,5),
                "Maintain Debtors Accounts"),
            ("DrsQuery",None,self.doDrsQuery,1,None,None,
                "Interrogate Debtors Accounts"),
            ("StrMaint",None,self.doStrMaint,0,("C",0,1),(("T",0,1),("C",0,2)),
                "Maintain Stores Records"),
            ("StrQuery",None,self.doStrQuery,1,None,None,
                "Interrogate Stores Records"),
            ("Exit",None,self.doTopExit,0,("T",0,1),(("T",0,2),("T",0,0)),
                "Exit the Sales Invoicing Routine"),
            ("Accept",None,self.doAccept,0,("C",0,1),(("T",0,1),("C",0,2)),
                "Accept and Process the Document"))
        tnd = ((self.doTopEnd,"n"), )
        txt = (self.doTopExit, )
        cnd = ((self.doColEnd,"n"), )
        cxt = (None, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, rows=self.row,
            butt=self.but, tend=tnd, txit=txt, cend=cnd, cxit=cxt, vport=True)
        self.df.setViewPort("I", 0)

    def doTyp(self, frt, pag, r, c, p, i, w):
        if w in ("C", "I") and self.allow == "N":
            return "Unauthorised Type"
        self.typs = w
        # Initialise Variables
        self.accept = None
        self.crlimit = None
        self.dnum = ""
        self.onum = ""
        self.jnum = ""
        self.dadd = ""
        self.cnam = ""
        self.vatn = ""
        self.ribbon = None
        self.drsdel = None
        self.message = ""
        # Initialise Action Variables
        self.actxit = False
        self.acttyp = None
        # Action
        if self.typs in ("O", "W", "Q"):
            # Sales Order, Works Order or Query
            self.doAction()
            if self.actxit:
                # Refocus on type field
                return "rf"
            if self.acttyp in ("A", "D", "X"):
                # Amend, Despatch or Convert
                err = self.doReadLoadDrs()
                if err:
                    return err
                self.df.loadEntry("T", 0, 1, data=self.mode)
                if self.chns == "Y":
                    chn = self.sql.getRec("drschn", cols=["chm_name"],
                        where=[("chm_cono", "=", self.opts["conum"]),
                        ("chm_chain", "=", self.chain)], limit=1)
                    if chn:
                        nam = chn[0]
                    else:
                        nam = ""
                    self.df.loadEntry("T", 0, 2, data=self.chain)
                    self.df.loadEntry("T", 0, 3, data=nam)
                    num = 4
                else:
                    num = 2
                self.df.loadEntry("T", 0, num, data=self.acno)
                self.df.loadEntry("T", 0, num+1, data=self.name)
                self.df.loadEntry("T", 0, num+2, data=self.repno)
                self.df.loadEntry("T", 0, num+3, data=self.repnm)
                if self.plevs == 1:
                    return "nd"
                self.df.loadEntry("T", 0, num+4, data=str(self.opts["level"]))
                return "nd"
            elif self.acttyp == "C":
                # Cancellation, Force focus to field 1
                return "ff1"

    def doAction(self):
        tit = ("Select Action",)
        doc = {
            "stype": "R",
            "tables": ("slsiv1", "drsmst"),
            "cols": [
                ("si1_docno", "", 0, "Doc-Num"),
                ("si1_chain", "", 0, "Chn"),
                ("si1_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y")],
            "where": [
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_rtn", "=", self.typs),
                ("si1_invno", "=", ""),
                ("drm_cono=si1_cono",),
                ("drm_chain=si1_chain",),
                ("drm_acno=si1_acno",)],
            "screen": self.df.mstFrame}
        r1s = [
            ("New", "N"),
            ("Amend", "A")]
        if self.typs == "Q":
            r1s.append(("Convert to Order", "X"))
        r1s.extend([
            ("Despatch", "D"),
            ("Cancel", "C")])
        fld = [
            [["T",0,0,0],("IRB",r1s),0,"Action","Action Type",
                "N","N",self.doActTyp,None,None,None],
            [["T",0,1,0],"IUI",9,"Document","Document Number",
                "","N",self.doActDoc,doc,None,("notzero",)]]
        state = self.df.disableButtonsTags()
        self.at = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doActEnd,"n"),), txit=(self.doActExit,))
        self.at.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doActTyp(self, frt, pag, r, c, p, i, w):
        if w == "D" and self.allow == "N":
            return "Unauthorised Selection"
        self.acttyp = w
        if self.acttyp == "N":
            return "sk1"

    def doActDoc(self, frt, pag, r, c, p, i, w):
        s1c = self.sql.slsiv1_col
        slsiv1 = self.sql.getRec("slsiv1", where=[("si1_cono", "=",
            self.opts["conum"]), ("si1_rtn", "=", self.typs), ("si1_docno",
            "=", w), ("si1_invno", "=", "")], limit=1)
        if not slsiv1:
            return "Invalid Document"
        self.docno = CCD(w, "UI", 9.0).work
        self.othno = CCD(w, "Na", 9.0).work
        self.repno = slsiv1[s1c.index("si1_rep")]
        self.chain = slsiv1[s1c.index("si1_chain")]
        self.acno = slsiv1[s1c.index("si1_acno")]
        self.mode = slsiv1[s1c.index("si1_mode")]
        self.opts["level"] = slsiv1[s1c.index("si1_level")]
        if not self.opts["level"]:
            self.opts["level"] = 1
        self.trndat = slsiv1[s1c.index("si1_date")]
        self.dnum = slsiv1[s1c.index("si1_our_ord")]
        self.onum = slsiv1[s1c.index("si1_cus_ord")]
        self.jnum = slsiv1[s1c.index("si1_jobno")]
        self.cnam = slsiv1[s1c.index("si1_contact")]
        self.vatn = slsiv1[s1c.index("si1_vatno")]
        self.ribbon = [self.dnum, self.onum, self.jnum, self.cnam, self.vatn]
        if not slsiv1[s1c.index("si1_add1")]:
            self.drsdel = None
        else:
            self.drsdel = ["",
                slsiv1[s1c.index("si1_add1")],
                slsiv1[s1c.index("si1_add2")],
                slsiv1[s1c.index("si1_add3")],
                slsiv1[s1c.index("si1_add4")]]
        self.message = slsiv1[s1c.index("si1_mess")]

    def doActEnd(self):
        if self.acttyp == "C":
            self.sql.updRec("slsiv1", cols=["si1_invno"], data=["cancel"],
                where=[("si1_cono", "=", self.opts["conum"]), ("si1_rtn",
                "=", self.typs), ("si1_docno", "=", self.docno)])
            self.opts["mf"].dbm.commitDbase()
        self.doActClose()

    def doActExit(self):
        self.actxit = True
        self.doActClose()

    def doActClose(self):
        self.at.closeProcess()

    def doMod(self, frt, pag, r, c, p, i, w):
        self.mode = w
        if self.mode == "C":
            self.bal = 0
            self.chain = 0
            self.acno = "CASHSLS"
            self.repno = ""
            self.drsmst = None
            err = self.doReadLoadDrs()
            if not self.drsmst:
                data = [self.opts["conum"], self.chain, self.acno,
                    "Cash Sales Account", "", "", "", "", "", "", "",
                    "", "", "", "", "", 0, 0, "", "", "", "", "", 0,
                    0, 0, 0, 0, 0, "N", 0, 0, "", "", ""]
                self.sql.insRec("drsmst", data=data)
            elif err:
                return err
            self.name = self.drsmst[self.sql.drsmst_col.index("drm_name")]
            if self.chns == "Y":
                idx = p + 3
            else:
                idx = p + 1
            self.df.loadEntry("T", 0, idx, data=self.acno)
            self.df.loadEntry("T", 0, idx+1, data=self.name)
            self.df.loadEntry("T", 0, idx+2, data=self.repno)
            if self.chns == "Y":
                return "sk4"
            else:
                return "sk2"

    def doChn(self, frt, pag, r, c, p, i, w):
        self.chain = w
        if self.chain:
            chn = self.sql.getRec("drschn", cols=["chm_name"],
                where=[("chm_cono", "=", self.opts["conum"]), ("chm_chain",
                "=", w)], limit=1)
            if not chn:
                return "Invalid Chain"
            self.df.loadEntry(frt, pag, p+1, data=chn[0])

    def doAcc(self, frt, pag, r, c, p, i, w):
        self.acno = w
        err = self.doReadLoadDrs()
        if err:
            return err
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        self.df.loadEntry(frt, pag, p+2, data=self.repno)

    def doReadLoadDrs(self):
        self.drsmst = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_chain", "=", self.chain), ("drm_acno",
            "=", self.acno)], limit=1)
        if not self.drsmst:
            return "Invalid Account"
        if self.drsmst[self.sql.drsmst_col.index("drm_stop")] == "Y":
            return "Account Stopped"
        if self.drsmst[self.sql.drsmst_col.index("drm_stat")] == "X":
            return "Account Redundant"
        ref = int(self.drsmst[self.sql.drsmst_col.index("drm_rfterms")] / 30)
        rej = int(self.drsmst[self.sql.drsmst_col.index("drm_rjterms")] / 30)
        bal = Balances(self.opts["mf"], "DRS", self.opts["conum"], self.curdt,
            [self.chain, self.acno])
        obal, self.bal, age = bal.doAllBals()
        if self.bal > 0:
            if not self.crlimit and ref > 0:
                bal = 0
                for y in range(ref-1, 5):
                    bal = float(ASD(bal) + ASD(age[y]))
                if bal > 0:
                    state = self.df.disableButtonsTags()
                    cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                        system="DRS", code="RefLimit")
                    self.df.enableButtonsTags(state=state)
                    if cf.flag == "no":
                        return "Referral Terms Exceeded"
                    self.crlimit = "ok"
            if not self.crlimit and rej > 0:
                bal = 0
                for y in range(rej-1, 5):
                    bal = float(ASD(bal) + ASD(age[y]))
                if bal > 0:
                    state = self.df.disableButtonsTags()
                    cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                        system="DRS", code="RejLimit")
                    self.df.enableButtonsTags(state=state)
                    if cf.flag == "no":
                        return "Rejected Terms Exceeded"
                    self.crlimit = "ok"
        if self.acttyp and self.acttyp in ("A", "D", "X"):
            pass
        else:
            self.repno = self.drsmst[self.sql.drsmst_col.index("drm_rep")]
        if self.repno:
            nam = self.sql.getRec("ctlrep", cols=["rep_name"],
                where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=",
                self.repno)], limit=1)
            if nam:
                self.repnm = nam[0]
            else:
                self.repnm = ""
        else:
            self.repnm = ""
        self.name = self.drsmst[self.sql.drsmst_col.index("drm_name")]
        self.dadd = self.drsmst[self.sql.drsmst_col.index("drm_delivery")]
        self.dmes = self.drsmst[self.sql.drsmst_col.index("drm_invmes")]
        if self.typs in ("O", "W", "Q") and self.acttyp in ("A", "D", "X"):
            return
        self.drsdel = self.sql.getRec("drsdel",
            where=[("del_code", "=", self.dadd)], limit=1)
        mess = self.sql.getRec("ctlmes", cols=["mss_detail"],
            where=[("mss_system", "=", "INV"), ("mss_message", "=",
            self.dmes)], limit=1)
        if mess:
            self.message = mess[0]
        else:
            self.message = ""
        self.cnam = self.drsmst[self.sql.drsmst_col.index("drm_sls")]
        self.vatn = self.drsmst[self.sql.drsmst_col.index("drm_vatno")]
        self.ribbon = [self.dnum, self.onum, self.jnum, self.cnam, self.vatn]

    def doRep(self, frt, pag, r, c, p, i, w):
        nam = self.sql.getRec("ctlrep", cols=["rep_name"],
            where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=", w)],
            limit=1)
        if not nam:
            return "Invalid Rep Code"
        if self.repno and w != self.repno:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="INV", code="ChangeRep")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "rf"
        self.repno = w
        self.repnm = nam[0]
        self.df.loadEntry(frt, pag, p+1, data=self.repnm)
        if self.plevs == 1:
            pass
        else:
            lev = str(self.drsmst[self.sql.drsmst_col.index("drm_plev")])
            if lev in ("", "0"):
                lev = "1"
            if self.chns == "Y":
                self.df.topf[0][8][5] = lev
            else:
                self.df.topf[0][6][5] = lev

    def doLev(self, frt, pag, r, c, p, i, w):
        self.opts["level"] = int(w)

    def doTopEnd(self):
        if not self.drsmst:
            if self.chns == "Y":
                self.df.focusField("T", 0, 5)
            else:
                self.df.focusField("T", 0, 3)
        elif self.acttyp in ("A", "D", "X"):
            self.doReadLoadStr()
            self.amend = False
        else:
            # Get Next Document Number
            self.doGetDocno(self.typs)
            # Create Document Transaction (Head)
            self.dad1, self.dad2, self.dad3, self.dad4 = "", "", "", ""
            if self.typs in ("I", "C"):
                self.trndat = self.trdt
            else:
                self.trndat = self.sysdtw
            data = [self.opts["conum"], self.typs, self.docno, self.mode,
                self.opts["level"], self.chain, self.acno, self.dad1,
                self.dad2, self.dad3, self.dad4, self.trndat, "", "", "", "",
                "", self.repno, "I", "", "", self.opts["capnm"], self.sysdtw]
            # Write and Commit the new document header
            self.sql.insRec("slsiv1", data=data)
            self.opts["mf"].dbm.commitDbase()
            # Clear Totals for document
            self.doClearTots()

    def doReadLoadStr(self):
        self.doClearTots()
        slsiv2 = self.sql.getRec("slsiv2", where=[("si2_cono", "=",
            self.opts["conum"]), ("si2_rtn", "=", self.typs), ("si2_docno",
            "=", self.docno)], order="si2_line")
        if not slsiv2:
            return
        for seq, line in enumerate(slsiv2):
            self.doExtractData(line)
            self.sql.updRec("slsiv2", cols=["si2_line"], data=[seq],
                where=[("si2_cono", "=", self.opts["conum"]), ("si2_rtn", "=",
                self.typs), ("si2_docno", "=", self.docno), ("si2_line", "=",
                self.oldline)])
            self.sql.updRec("slsiv3", cols=["si3_line"], data=[seq],
                where=[("si3_cono", "=", self.opts["conum"]), ("si3_rtn", "=",
                self.typs), ("si3_docno", "=", self.docno), ("si3_line", "=",
                self.oldline)])
            if seq >= self.row[0]:
                self.df.scrollScreen(0)
                pos = (self.row[0] - 1) * 9
            else:
                pos = seq * 9
            # Load Values
            self.df.loadEntry("C", 0, pos, self.grp)
            self.df.loadEntry("C", 0, pos + 1, self.code)
            self.df.loadEntry("C", 0, pos + 2, self.desc)
            self.df.loadEntry("C", 0, pos + 3, self.loc)
            self.df.loadEntry("C", 0, pos + 4, self.qty)
            self.df.loadEntry("C", 0, pos + 5, self.vatcod)
            self.df.loadEntry("C", 0, pos + 6, self.price)
            self.df.loadEntry("C", 0, pos + 7, self.disrat)
            self.df.loadEntry("C", 0, pos + 8, self.incamt)
            self.totvat = float(ASD(self.totvat) + ASD(self.vatamt))
            self.totinv = float(ASD(self.totinv) + ASD(self.incamt))
        if seq >= (self.row[0] - 1):
            self.df.scrollScreen(0)
        else:
            self.df.focusField("C", 0, pos + 10)
        self.df.setViewPort(self.typs, self.totinv)

    def doTopExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doClearTots(self):
        self.totvat = 0
        self.totinv = 0
        self.df.setViewPort(self.typs, self.totinv)
        self.df.clearFrame("C", 0)
        self.df.focusField("C", 0, 1)

    def doGrp(self, frt, pag, r, c, p, i, w):
        self.grp = w
        self.strgrp = self.doReadGroup(self.grp)
        if not self.strgrp:
            return "Invalid Group Code"
        self.df.colf[pag][1][8]["where"] = [
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.grp),
            ("st1_type", "<>", "X")]
        #######################################################################
        # Get Next Line Number
        #######################################################################
        seq = self.sql.getRec("slsiv2", cols=["count(*)"],
            where=[("si2_cono", "=", self.opts["conum"]), ("si2_rtn", "=",
            self.typs), ("si2_docno", "=", self.docno)], limit=1)
        self.newline = int(seq[0])
        #######################################################################

    def doCod(self, frt, pag, r, c, p, i, w):
        strmf1 = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.grp), ("st1_code",
            "=", w), ("st1_type", "<>", "X")], limit=1)
        if not strmf1:
            return "Invalid or Redundant Code"
        if self.stgl == "Y":
            gl = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                strmf1[self.sql.strmf1_col.index("st1_sls")])], limit=1)
            if not gl:
                return "Invalid GL Sales Code"
            gl = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                strmf1[self.sql.strmf1_col.index("st1_cos")])], limit=1)
            if not gl:
                return "Invalid GL Cost of Sales Code"
        self.code = w
        self.gtype = strmf1[self.sql.strmf1_col.index("st1_type")]
        desc = strmf1[self.sql.strmf1_col.index("st1_desc")]
        self.uoi = strmf1[self.sql.strmf1_col.index("st1_uoi")]
        self.vind = strmf1[self.sql.strmf1_col.index("st1_value_ind")]
        self.vatc = strmf1[self.sql.strmf1_col.index("st1_vatcode")]
        if not self.vatc:
            self.vatc = self.strgrp[self.sql.strgrp_col.index("gpm_vatcode")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doReadGroup(self, group):
        strgrp = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", group)], limit=1)
        return strgrp

    def doDes(self, frt, pag, r, c, p, i, w):
        self.desc = w
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry(frt, pag, p+1, data=self.loc)
            return "sk1"
        self.loc = self.sql.getRec("strloc", cols=["srl_loc"],
            where=[("srl_cono", "=", self.opts["conum"])], order="srl_loc",
            limit=1)[0]
        self.df.loadEntry(frt, pag, p+1, data=self.loc)

    def doLoc(self, frt, pag, r, c, p, i, w):
        strmf2 = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.grp), ("st2_code",
            "=", self.code), ("st2_loc", "=", w)], limit=1)
        if not strmf2:
            return "Invalid Location, Item Not In Stock"
        self.loc = w

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w
        if self.gtype == "R":
            ok = self.doRecipe(atype="I", lineno=self.newline)
            if ok == "NoItems":
                return "Invalid Recipe, No Items"
            elif ok == "Redundant":
                return "Invalid Recipe, Has Redundant Items"
            elif ok == "NoQty":
                return "cl"
            elif ok == "Quit":
                return "cl"
            self.doRecipe(atype="S", lineno=self.newline)
        else:
            self.doCalSell()
            if self.typs in ("C", "O", "W", "Q"):
                pass
            else:
                # Check for quantity on hand
                bal = self.sql.getRec("strtrn", cols=["sum(stt_qty)"],
                    where=[("stt_cono", "=", self.opts["conum"]),
                    ("stt_group", "=", self.grp), ("stt_code", "=", self.code),
                    ("stt_loc", "=", self.loc)], limit=1)
                if bal:
                    qty = CCD(bal[0], "SD", 11.2).work
                else:
                    qty = CCD(0, "SD", 11.2).work
                if self.vind != "N" and self.typs != "C" and self.qty > qty:
                    state = self.df.disableButtonsTags()
                    cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                        system="INV", code="ExQty")
                    self.df.enableButtonsTags(state=state)
                    if cf.flag == "no":
                        return "cl"
        self.df.loadEntry(frt, pag, p+1, data=self.vatc)

    def doRecipe(self, atype="I", lineno=0):
        """
        I = Load Recipe and Allow Changes
        C = Change Quantity
        U = Get Cost Prices
        S = Get Selling Price
        """
        self.lineno = lineno
        if atype == "I":
            try:
                self.sql.delRec("slsiv3", where=[("si3_cono", "=",
                    self.opts["conum"]), ("si3_rtn", "=", self.typs),
                    ("si3_docno", "=", self.docno), ("si3_line", "=",
                    self.lineno)])
            except:
                pass
            recipe = self.sql.getRec("strrcp", where=[("srr_cono", "=",
                self.opts["conum"]), ("srr_group", "=", self.grp),
                ("srr_code", "=", self.code), ("srr_loc", "=", self.loc)])
            if not recipe:
                return "NoItems"
            self.recipe = []
            needpwd = False
            for item in recipe:
                st1 = self.sql.getRec("strmf1", cols=["st1_type",
                    "st1_value_ind"], where=[("st1_cono", "=", item[0]),
                    ("st1_group", "=", item[4]), ("st1_code", "=", item[5])],
                    limit=1)
                if st1[0] == "X":
                    return "Redundant"
                quant = item[6] * self.qty
                icost, bal = getCost(self.sql, self.opts["conum"], item[4],
                    item[5], loc=self.loc, qty=1, ind="I", bal=True)
                if st1[1] == "A" and quant > bal[0]:
                    needpwd = True
                self.recipe.append([self.opts["conum"], self.typs, self.docno,
                    self.lineno, item[4], item[5], item[6], icost, 0])
            if needpwd:
                state = self.df.disableButtonsTags()
                cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                    system="INV", code="ExQty")
                self.df.enableButtonsTags(state=state)
                if cf.flag == "no":
                    return "NoQty"
            self.doRecChg()
            if self.rectyp == "quit":
                return "Quit"
            for item in self.recipe:
                self.sql.insRec("slsiv3", data=item)
        elif atype == "C":
            self.recipe = self.sql.getRec("slsiv3", where=[("si3_cono",
                "=", self.opts["conum"]), ("si3_rtn", "=", self.typs),
                ("si3_docno", "=", self.docno), ("si3_line", "=", self.lineno)])
            self.sql.delRec("slsiv3", where=[("si3_cono", "=",
                self.opts["conum"]), ("si3_rtn", "=", self.typs), ("si3_docno",
                "=", self.docno), ("si3_line", "=", self.lineno)])
            self.doRecChg()
            if self.rectyp == "quit":
                return "Quit"
            for item in self.recipe:
                self.sql.insRec("slsiv3", data=item)
        elif atype == "U":
            self.icost = 0
            self.tcost = 0
            recipe = self.sql.getRec("slsiv3", where=[("si3_cono", "=",
                self.opts["conum"]), ("si3_rtn", "=", self.typs), ("si3_docno",
                "=", self.docno), ("si3_line", "=", self.lineno)])
            for item in recipe:
                quant = item[6] * self.qty
                icost, tcost = getCost(self.sql, self.opts["conum"], item[4],
                    item[5], loc=self.loc, qty=quant, ind="I", tot=True)
                self.tcost = float(ASD(self.tcost) + ASD(tcost))
            self.icost = round(self.tcost / self.qty, 2)
        elif atype == "S":
            self.doCalSell()

    def doRecChg(self):
        # Display recipe items and allow editing of quantities etc.
        data = []
        for num, item in enumerate(self.recipe):
            desc = self.sql.getRec("strmf1", cols=["st1_desc"],
                where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                "=", item[4]), ("st1_code", "=", item[5])], limit=1)
            icost, tcost = getCost(self.sql, self.opts["conum"], item[4],
                item[5], loc=self.loc, qty=item[6], ind="I", tot=True)
            data.append([num, item[4], item[5], desc[0], item[6], tcost])
        titl = "Recipe Items"
        head = ("Seq","Grp","Product-Code", "Description", "  Quantity",
            "      Cost")
        lin = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": [
                ("UI", 2),
                ("NA", 3),
                ("NA", 20),
                ("NA", 30),
                ("SD", 11.2),
                ("SD", 11.2)],
            "data": data,
            "butt": [
                ("Add", self.doRecAdd),
                ("Accept", self.doRecAccept),
                ("Quit", self.doRecQuit)]}
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select a Product to Edit or an Action")
        self.rectyp = None
        chg = self.df.selChoice(lin)
        self.df.enableButtonsTags(state=state)
        if chg and chg.selection:
            self.rectyp = "chg"
            self.recchg = chg.selection
        if self.rectyp in ("add", "chg"):
            self.doRecChanges()
            self.doRecChg()

    def doRecAdd(self):
        self.rectyp = "add"

    def doRecAccept(self):
        self.rectyp = "continue"

    def doRecQuit(self):
        self.rectyp = "quit"

    def doRecChanges(self):
        fld = []
        if self.rectyp == "chg":
            tit = ("Change Item",)
            fld = (
                (("T",0,0,0),"ONA",3,"Group"),
                (("T",0,1,0),"ONA",20,"Code"),
                (("T",0,2,0),"ONA",30,"Description"),
                (("T",0,3,0),"ISD",11.2,"Quantity","",
                    "","N",self.doRecQty,None,None,("notzero",)))
            but = (("Delete",None,self.doRecDel,1,None,None),)
        else:
            tit = ("Add Item",)
            fld = (
                (("T",0,0,0),"INA",3,"Group","Product Group",
                    "","N",self.doRecGrp,self.grps.copy(),None,None),
                (("T",0,1,0),"INA",20,"Code", "Product Code",
                    "","N",self.doRecCod,self.cods.copy(),None,None),
                (("T",0,2,0),"ONA",30,"Description"),
                (("T",0,3,0),"ISD",11.2,"Quantity","",
                    "","N",self.doRecQty,None,None,("notzero",)))
            but = None
        state = self.df.disableButtonsTags()
        self.rc = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doRecEnd,"n"),),
            txit=(self.doRecExit,))
        if self.rectyp == "chg":
            self.rc.loadEntry("T", 0, 0, data=self.recchg[1])
            self.rc.loadEntry("T", 0, 1, data=self.recchg[2])
            self.rc.loadEntry("T", 0, 2, data=self.recchg[3])
            self.rc.loadEntry("T", 0, 3, data=self.recchg[4])
            self.rc.focusField("T", 0, 4, clr=False)
        else:
            self.rc.focusField("T", 0, 1)
        self.rc.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doRecGrp(self, frt, pag, r, c, p, i, w):
        strgrp = self.doReadGroup(w)
        if not strgrp:
            return "Invalid Group Code"
        self.recgrp = w
        self.rc.topf[pag][1][8]["where"] = [
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.recgrp),
            ("st1_type", "not", "in", ("R", "X"))]

    def doRecCod(self, frt, pag, r, c, p, i, w):
        strmf1 = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.recgrp), ("st1_code",
            "=", w), ("st1_type", "not", "in", ("R", "X"))], limit=1)
        if not strmf1:
            return "Invalid Code"
        self.reccod = w
        desc = strmf1[self.sql.strmf1_col.index("st1_desc")]
        self.rc.loadEntry(frt, pag, p+1, data=desc)

    def doRecQty(self, frt, pag, r, c, p, i, w):
        self.recqty = w

    def doRecDel(self):
        del self.recipe[int(self.recchg[0])]
        self.doRecExit()

    def doRecEnd(self):
        if self.rectyp == "chg":
            self.recipe[int(self.recchg[0])][6] = self.recqty
        else:
            icost = getCost(self.sql, self.opts["conum"], self.recgrp,
                self.reccod, loc=self.loc, qty=1, ind="I")
            self.recipe.append([self.opts["conum"], self.typs, self.docno,
                self.lineno, self.recgrp, self.reccod, self.recqty, icost, 0])
        self.doRecExit()

    def doRecExit(self):
        self.rc.closeProcess()

    def doVat(self, frt, pag, r, c, p, i, w):
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.trndat)
        if self.vatrte is None:
            return "Invalid V.A.T Code"
        self.vatcod = w
        self.df.loadEntry(frt, pag, p+1, data=self.rrp)

    def doPri(self, frt, pag, r, c, p, i, w):
        if not w:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="INV", code="NoCharge")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "rf"
        if self.gtype == "R":
            self.doRecipe(atype="U", lineno=self.newline)
            icost = self.icost
        else:
            icost = getCost(self.sql, self.opts["conum"], self.grp, self.code,
                loc=self.loc, qty=self.qty, ind="I")
        if w < icost:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="INV", code="BelowCost")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "rf"
        self.price = w
        rat = float(ASD(100.0) + ASD(self.vatrte))
        self.inc = round((self.price * rat / 100.0), 4)
        self.exc = round((self.price * 1), 2)
        dis = self.drsmst[self.sql.drsmst_col.index("drm_dis_per")]
        self.df.loadEntry(frt, pag, p+1, data=dis)

    def doDis(self, frt, pag, r, c, p, i, w):
        self.disrat = w
        dis = float(ASD(100.0) - ASD(self.disrat))
        self.excamt = round((self.qty * self.exc * dis / 100.0), 2)
        self.incamt = round((self.qty * self.inc * dis / 100.0), 2)
        self.vatamt = float(ASD(self.incamt) - ASD(self.excamt))
        self.df.loadEntry(frt, pag, p+1, data=self.incamt)
        self.totvat = float(ASD(self.totvat) + ASD(self.vatamt))
        self.totinv = float(ASD(self.totinv) + ASD(self.incamt))
        lim = self.drsmst[self.sql.drsmst_col.index("drm_limit")]
        bal = float(ASD(self.bal) + ASD(self.totinv))
        if not self.crlimit and lim > 0 and bal > lim:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="DRS", code="CrLimit")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                self.totvat = float(ASD(self.totvat) - ASD(self.vatamt))
                self.totinv = float(ASD(self.totinv) - ASD(self.incamt))
                return "cl"
            self.crlimit = "ok"

    def doColEnd(self):
        # Create Sales Invoice Transaction (Body)
        data = [self.opts["conum"], self.typs, self.docno, self.newline,
            self.grp, self.code, self.loc, self.uoi, self.desc, self.disrat,
            self.qty, self.price, self.vatcod, self.vatrte, self.opts["capnm"],
            self.sysdtw]
        self.sql.insRec("slsiv2", data=data)
        if self.acttyp == "A":
            self.amend = True
        self.df.advanceLine(0)
        self.df.setViewPort(self.typs, self.totinv)

    def doDrsQuery(self):
        callModule(self.opts["mf"], self.df, "dr4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def doStrQuery(self):
        callModule(self.opts["mf"], self.df, "st4010", coy=(self.opts["conum"],
            self.opts["conam"]), period=self.opts["period"],
            user=self.opts["capnm"])

    def doDelAdd(self):
        tit = ("Delivery Address",)
        cod = {
            "stype": "R",
            "tables": ("drsdel",),
            "cols": [
                ("del_code", "", 0, "Del-Cod"),
                ("del_add1", "", 0, "Address Line 1"),
                ("del_add2", "", 0, "Address Line 2")],
            "screen": self.opts["mf"].body}
        fld = (
            (("T",0,0,0),"INa",7,"Del-Cod","Delivery Code",
                self.dadd,"N",self.doDelCod,cod,None,None),
            (("T",0,1,0),"INA",30,"Address-1","Address Line 1",
                "","N",None,None,None,None),
            (("T",0,2,0),"INA",30,"Address-2","Address Line 2",
                "","N",None,None,None,None),
            (("T",0,3,0),"INA",30,"Address-3","Address Line 3",
                "","N",None,None,None,None),
            (("T",0,4,0),"INA",30,"Address-4","Address Line 4",
                "","N",None,cod,None,None))
        state = self.df.disableButtonsTags()
        self.da = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doDelEnd,"y"),), txit=(self.doDelExit,),
            focus=False)
        if self.drsdel:
            self.doLoadDel(True)
        else:
            self.da.focusField("T", 0, 1)
        self.da.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doDelCod(self, frt, pag, r, c, p, i, w):
        if not w:
            return
        self.drsdel = self.sql.getRec("drsdel", where=[("del_code",
            "=", w)], limit=1)
        if self.drsdel:
            self.doLoadDel()
            return "nd"

    def doLoadDel(self, focus=False):
        for n, m in enumerate(self.drsdel[:-1]):
            self.da.loadEntry("T", 0, n, data=m)
        if focus:
            self.da.focusField("T", 0, 2, clr=False)

    def doDelEnd(self):
        self.drsdel = []
        for x in range(0, self.da.topq[0]):
            self.drsdel.append(self.da.t_work[0][0][x])
        self.doDelExit()

    def doDelExit(self):
        self.da.closeProcess()

    def doMessage(self):
        tit = ("Invoice Message",)
        cod = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": [
                ("mss_message", "",  0, "Cod"),
                ("mss_detail",  "", 60, "Details")],
            "where": [("mss_system", "=", "INV")],
            "screen": self.opts["mf"].body}
        fld = (
            (("T",0,0,0),"IUI",3,"Message Code","",
                "","N",self.doMesCod,cod,None,None),
            (("T",0,1,0),"ITv",(30,6),"Message","",
                self.message,"N",None,None,None,None))
        but = (("Accept",None,self.doMesEnd,0,("T",0,1),("T",0,0)),)
        state = self.df.disableButtonsTags()
        self.mg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doMesEnd,"y"),), txit=(self.doMesExit,),
            butt=but)
        self.mg.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doMesCod(self, frt, pag, r, c, p, i, w):
        if w:
            mess = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "INV"), ("mss_message", "=", w)],
                limit=1)
            if not mess:
                return "Invalid Message Code"
            self.message = mess[0]
            self.mg.loadEntry(frt, pag, p+1, data=self.message)

    def doMesEnd(self):
        wid, self.message = self.mg.getEntry("T", 0, 1)
        self.doMesExit()

    def doMesExit(self):
        self.mg.closeProcess()

    def doEdit(self):
        # Display document items and allow editing of desc, qty and price
        data = self.sql.getRec("slsiv2", cols=["si2_line", "si2_group",
            "si2_code", "si2_desc", "si2_loc", "si2_qty", "si2_vat_code",
            "si2_price", "si2_disc_per"], where=[("si2_cono", "=",
            self.opts["conum"]), ("si2_rtn", "=", self.typs), ("si2_docno",
            "=", self.docno)], order="si2_line")
        if data:
            titl = "Document Product Lines"
            head = ("Seq","Grp","Product-Code", "Description","L", "Quantity",
                "V","Price","Disc-%")
            lin = {
                "stype": "C",
                "titl": titl,
                "head": head,
                "data": data}
            state = self.df.disableButtonsTags()
            self.opts["mf"].updateStatus("Select a Product to Edit")
            chg = self.df.selChoice(lin)
            if chg and chg.selection:
                self.change = chg.selection
                self.doChgChanges()
            self.df.enableButtonsTags(state=state)
        self.df.focusField("C", 0, self.df.col)

    def doChgChanges(self):
        tit = ("Change Item",)
        fld = (
            (("T",0,0,0),"ONA",3,"Group"),
            (("T",0,1,0),"ONA",20,"Code"),
            (("T",0,2,0),"ITv",30,"Description","",
                "","N",self.doChgDes,None,None,None),
            (("T",0,3,0),"ISD",11.2,"Quantity","",
                "","N",self.doChgQty,None,None,("notzero",)),
            (("T",0,4,0),"IUD",10.2,"Selling Price","",
                "","N",self.doChgPrc,None,None,("notzero",)),
            (("T",0,5,0),"IUD",6.2,"Discount Percent","",
                "","N",self.doChgDis,None,None,("efld",)))
        but = [["Delete",None,self.doChgDel,1,None,None]]
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doChgEnd,"n"),),
            txit=(self.doChgExit,))
        acc = self.sql.getRec("strmf1", cols=["st1_type"],
            where=[("st1_cono", "=", self.opts["conum"]), ("st1_group", "=",
            self.change[1]), ("st1_code", "=", self.change[2])], limit=1)
        if acc:
            self.gtype = acc[0]
        else:
            self.gtype = "N"
        self.cg.loadEntry("T", 0, 0, data=self.change[1])
        self.cg.loadEntry("T", 0, 1, data=self.change[2])
        self.cg.loadEntry("T", 0, 2, data=self.change[3])
        self.cg.loadEntry("T", 0, 3, data=self.change[5])
        self.cg.loadEntry("T", 0, 4, data=self.change[7])
        self.cg.loadEntry("T", 0, 5, data=self.change[8])
        self.cg.focusField("T", 0, 3, clr=False)
        self.cg.mstFrame.wait_window()

    def doChgDes(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doChgQty(self, frt, pag, r, c, p, i, w):
        self.qty = w
        if self.gtype == "R":
            self.cg.setWidget(self.cg.window, state="hide")
            self.doRecipe(atype="C", lineno=self.change[0])
            self.doRecipe(atype="S", lineno=self.change[0])
            self.cg.setWidget(self.cg.window, state="show")
            self.cg.loadEntry(frt, pag, p+1, data=self.rrp)
            self.cg.focusField(frt, pag, c)

    def doChgPrc(self, frt, pag, r, c, p, i, w):
        self.price = w
        if self.gtype == "R":
            self.doRecipe(atype="U", lineno=self.change[0])
            icost = self.icost
        else:
            icost = getCost(self.sql, self.opts["conum"], self.change[1],
                self.change[2], loc=self.change[4], qty=self.qty, ind="I")
        if w < icost:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="INV", code="BelowCost")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "rf"

    def doChgDis(self, frt, pag, r, c, p, i, w):
        self.disrat = w

    def doChgDel(self):
        seq = self.change[0]
        self.sql.delRec("slsiv2", where=[("si2_cono", "=", self.opts["conum"]),
            ("si2_rtn", "=", self.typs), ("si2_docno", "=", self.docno),
            ("si2_line", "=", seq)])
        self.sql.delRec("slsiv3", where=[("si3_cono", "=", self.opts["conum"]),
            ("si3_rtn", "=", self.typs), ("si3_docno", "=", self.docno),
            ("si3_line", "=", seq)])
        if self.acttyp == "A":
            self.amend = True
        self.doReadLoadStr()
        self.doChgExit()

    def doChgEnd(self):
        seq = self.change[0]
        self.sql.updRec("slsiv2", cols=["si2_desc", "si2_qty", "si2_price",
            "si2_disc_per"], data=[self.desc, self.qty, self.price,
            self.disrat], where=[("si2_cono", "=", self.opts["conum"]),
            ("si2_rtn", "=", self.typs), ("si2_docno", "=", self.docno),
            ("si2_line", "=", seq)])
        if self.acttyp == "A":
            self.amend = True
        self.doReadLoadStr()
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def doReprnt(self):
        tit = ("Reprint Documents",)
        iv1 = {
            "stype": "R",
            "tables": ("slsiv1", "drsmst"),
            "cols": [
                ("si1_docno", "",  0, "Doc-Num"),
                ("si1_date", "",  0, "Date"),
                ("si1_chain", "",  0, "Chn"),
                ("si1_acno",  "", 0, "Acc-Num"),
                ("drm_name",  "", 0, "Name", "Y"),
                ("si1_invno",  "", 0, "Dis-Num")],
            "where": [
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_cono=drm_cono",),
                ("si1_chain=drm_chain",),
                ("si1_acno=drm_acno",),
                ("si1_invno", "<>", "cancel")],
            "whera": [["T", "si1_rtn", 1, 0]],
            "screen": self.opts["mf"].body}
        r1s = (("Copies", "C"), ("Originals", "O"))
        r2s = (
            ("Inv","I"),
            ("C-N","C"),
            ("S-O","O"),
            ("W-O","W"),
            ("Qte","Q"))
        r3s = (("Yes", "Y"), ("No", "N"))
        fld = [
            (("T",0,0,0),("IRB",r1s),0,"Document Mode","",
                "C","N",self.doMode,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Document Type","",
                "I","N",self.doReprntType,None,None,None)]
        if self.delnos == "Y":
            fld.append(
                (("T",0,2,0),("IRB",r3s),0,"Delivery Note","Delivery Note",
                    self.dnote,"N",None,None,None,None))
            idx = 3
        else:
            idx = 2
        fld.extend([
            (("T",0,idx,0),"IUI",9,"From Number","From Document Number",
                "","N",self.doIv1,iv1,None,("notblank",)),
            (("T",0,idx+1,0),"IUI",9,"To   Number","To Document Number",
                "","N",self.doIv1,iv1,None,("notblank",))])
        state = self.df.disableButtonsTags()
        self.rp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doReprntEnd, "n"),),
            txit=(self.doReprntExit,), view=("N","V"), mail=("B","Y"))
        self.rp.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doMode(self, frt, pag, r, c, p, i, w):
        if w == "C":
            self.copy = "y"
        else:
            self.copy = "n"

    def doReprntType(self, frt, pag, r, c, p, i, w):
        self.dtyp = w
        if self.delnos == "Y" and self.dtyp != "I":
            self.rp.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doIv1(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("slsiv1", where=[("si1_cono",
            "=", self.opts["conum"]), ("si1_rtn", "=", self.dtyp),
            ("si1_docno", "=", w)], limit=1)
        if not chk:
            return "Invalid Document Number"
        if chk[self.sql.slsiv1_col.index("si1_invno")] == "cancel":
            return "This Document Was Cancelled"
        if p == self.rp.topq[0] - 8:
            self.rp.loadEntry(frt, pag, p+1, data=w)

    def doReprntEnd(self):
        self.rp.closeProcess()
        self.df.setWidget(self.df.mstFrame, state="hide")
        typ = self.rp.t_work[0][0][1]
        if self.delnos == "Y":
            dn = self.rp.t_work[0][0][2]
            idx = 3
        else:
            dn = "N"
            idx = 2
        frm = self.rp.t_work[0][0][idx]
        to = self.rp.t_work[0][0][idx+1]
        iv1 = self.sql.getRec("slsiv1", cols=["si1_docno"],
            where=[("si1_cono", "=", self.opts["conum"]), ("si1_rtn", "=",
            typ), ("si1_docno", ">=", frm), ("si1_docno", "<=", to)],
            order="si1_docno")
        if iv1:
            PrintInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], typ, iv1, tname=self.tname,
                repprt=self.rp.repprt, repeml=self.rp.repeml,
                copy=self.copy, dnote=dn, dvals=self.delval)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doReprntExit(self):
        self.rp.closeProcess()

    def doDrsMaint(self):
        callModule(self.opts["mf"], self.df, "dr1010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def doStrMaint(self):
        callModule(self.opts["mf"], self.df, "st1010", coy=(self.opts["conum"],
            self.opts["conam"]), period=None, user=self.opts["capnm"])

    def doAccept(self):
        self.df.setWidget(self.df.B11, "disabled")
        if self.df.col == 1:
            self.doCancel()
            return
        if self.typs in ("O", "W", "Q") and self.acttyp == "D" and \
                                            self.doChkItems():
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        if self.totinv >= 1000.00 and not self.ribbon[4]:
            self.accept = "y"
            self.doRibbon()
            return
        # Update Tables
        self.doUpdateTables()
        # Commit Transaction
        self.opts["mf"].dbm.commitDbase()
        # Print Document
        if self.acttyp == "A" and not self.amend:
            pass
        else:
            if self.typs in ("O", "W"):
                repeml = ["N", "N", "", "", "Y"]
            else:
                repeml = copyList(self.pr.repeml)
            if self.typs == "I":
                dnote = self.dnote
            else:
                dnote = "N"
            self.df.setWidget(self.df.mstFrame, state="hide")
            if self.acttyp == "A":
                copy = "a"
            else:
                copy = "n"
            PrintInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], self.typs, self.docno,
                copy=copy, tname=self.tname, repprt=self.pr.repprt,
                repeml=repeml, dnote=dnote, dvals=self.delval)
            self.df.setWidget(self.df.mstFrame, state="show")
        # Clear total and focus
        self.df.setViewPort(self.typs, 0)
        self.df.focusField("T", 0, 1)

    def doChkItems(self):
        trn = self.sql.getRec("slsiv2", where=[("si2_cono", "=",
            self.opts["conum"]), ("si2_rtn", "=", self.typs), ("si2_docno",
            "=", self.docno)])
        needpwd = False
        for line in trn:
            # Check for quantity on hand
            grp = line[self.sql.slsiv2_col.index("si2_group")]
            cod = line[self.sql.slsiv2_col.index("si2_code")]
            loc = line[self.sql.slsiv2_col.index("si2_loc")]
            qty = line[self.sql.slsiv2_col.index("si2_qty")]
            mf1 = self.sql.getRec("strmf1", where=[("st1_cono", "=",
                self.opts["conum"]), ("st1_group", "=", grp), ("st1_code", "=",
                cod)], limit=1)
            ind = mf1[self.sql.strmf1_col.index("st1_value_ind")]
            if ind == "A":
                bal = self.sql.getRec("strtrn", cols=["sum(stt_qty)"],
                    where=[("stt_cono", "=", self.opts["conum"]),
                    ("stt_group", "=", grp), ("stt_code", "=", cod),
                    ("stt_loc", "=", loc)], limit=1)
                if bal[0] is None or qty > bal[0]:
                    needpwd = True
        if needpwd:
            state = self.df.disableButtonsTags()
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="INV", code="ExQty")
            self.df.enableButtonsTags(state=state)
            if cf.flag == "no":
                return "NoQty"

    def doExtractData(self, line):
        self.oldline = line[self.sql.slsiv2_col.index("si2_line")]
        self.grp = line[self.sql.slsiv2_col.index("si2_group")]
        self.code = line[self.sql.slsiv2_col.index("si2_code")]
        self.desc = line[self.sql.slsiv2_col.index("si2_desc")]
        self.loc = line[self.sql.slsiv2_col.index("si2_loc")]
        self.qty = line[self.sql.slsiv2_col.index("si2_qty")]
        self.uoi = line[self.sql.slsiv2_col.index("si2_uoi")]
        self.vatcod = line[self.sql.slsiv2_col.index("si2_vat_code")]
        self.vatrte = line[self.sql.slsiv2_col.index("si2_vat_rate")]
        self.price = line[self.sql.slsiv2_col.index("si2_price")]
        self.disrat = line[self.sql.slsiv2_col.index("si2_disc_per")]
        # Calculate Values
        rat = float(ASD(100) + ASD(self.vatrte))
        self.inc = round((self.price * rat / 100), 4)
        self.exc = round((self.price * 1), 2)
        dis = float(ASD(100) - ASD(self.disrat))
        self.excamt = round((self.qty * self.exc * dis / 100), 2)
        self.incamt = round((self.qty * self.inc * dis / 100), 2)
        self.vatamt = float(ASD(self.incamt) - ASD(self.excamt))

    def doAgeNormal(self):
        self.doAgeing("N")

    def doAgeCurrent(self):
        self.doAgeing("C")

    def doAgeing(self, atype):
        if atype == "N":
            state = self.df.disableButtonsTags()
        self.age = AgeAll(self.opts["mf"], system="drs", agetyp=atype,
            agekey=[self.opts["conum"], self.chain, self.acno,
            self.opts["rtn"], self.othno, self.curdt, self.agetot, 0.0])
        if self.age.cancel:
            self.age.agetot = self.agetot
        if atype == "N":
            self.df.enableButtonsTags(state=state)

    def doRibbon(self):
        tit = ("Ribbon Line",)
        fld = (
            (("T",0,0,0),"INa",9,"Delivery Note Number",
                "Delivery Note Number",self.dnum,"N",None,None,None,None),
            (("T",0,1,0),"INA",14,"Customer Order Number",
                "Customer Order Number",self.onum,"N",None,None,None,None),
            (("T",0,2,0),"INa",7,"Job Number","",
                self.jnum,"N",None,None,None,None),
            (("T",0,3,0),"INA",30,"Contact Person","",
                self.cnam,"N",None,None,None,None),
            (("T",0,4,0),"INA",10,"VAT Number","",
                self.vatn,"N",self.doVatNum,None,None,None))
        state = self.df.disableButtonsTags()
        self.rl = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRibEnd,"n"),), txit=(self.doRibExit,),
            focus=False)
        if self.ribbon:
            for x in range(5):
                self.rl.loadEntry("T", 0, x, data=self.ribbon[x])
        pos = 1
        if self.typs in ("O", "W", "Q"):
            if self.typs in ("O", "W") or self.acttyp in ("D", "X"):
                self.rl.loadEntry("T", 0, 0, data="")
                self.rl.skip[0] = [1]
                pos = 2
            else:
                self.rl.loadEntry("T", 0, 1, data="")
                self.rl.loadEntry("T", 0, 2, data="")
                self.rl.skip[0] = [1, 2, 3]
                pos = 4
        self.rl.focusField("T", 0, pos, clr=False)
        self.rl.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        if self.accept:
            self.doAccept()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doVatNum(self, frt, pag, r, c, p, i, w):
        if self.totinv >= 1000.00 and not w:
            return "Invalid VAT Number"

    def doRibEnd(self):
        self.rl.closeProcess()
        self.ribbon = []
        for x in range(0, self.rl.topq[0]):
            self.ribbon.append(self.rl.t_work[0][0][x])

    def doRibExit(self):
        self.rl.closeProcess()
        self.accept = None

    def doUpdateTables(self):
        # Update slsiv1 with ribbon, delivery and message details and
        # Update drsmst with VAT number if available
        whr = [
            ("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "=", self.typs),
            ("si1_docno", "=", self.docno),
            ("si1_chain", "=", self.chain),
            ("si1_acno", "=", self.acno)]
        if self.ribbon:
            self.sql.updRec("slsiv1", cols=["si1_our_ord", "si1_cus_ord",
                "si1_jobno", "si1_contact", "si1_vatno"],
                data=[self.ribbon[0], self.ribbon[1], self.ribbon[2],
                self.ribbon[3], self.ribbon[4]], where=whr)
            if self.mode == "A" and self.typs in ("I", "O", "W") and not \
                                        self.vatn and self.ribbon[4]:
                self.sql.updRec("drsmst", cols=["drm_vatno"],
                    data=[self.ribbon[4]], where=[("drm_cono", "=",
                    self.opts["conum"]), ("drm_chain", "=", self.chain),
                    ("drm_acno", "=", self.acno)])
        if self.drsdel:
            self.sql.updRec("slsiv1", cols=["si1_add1", "si1_add2",
                "si1_add3", "si1_add4"], data=[self.drsdel[1],
                self.drsdel[2], self.drsdel[3], self.drsdel[4]],
                where=whr)
        if self.message:
            self.sql.updRec("slsiv1", cols=["si1_mess"], data=[self.message],
                where=whr)
        if self.typs in ("O", "W", "Q") and self.acttyp in ("A", "N"):
            return
        if self.typs == "Q" and self.acttyp == "X":
            # Convert quote to order
            actdoc = self.docno
            self.doGetDocno("O")
            self.sql.updRec("slsiv1", cols=["si1_rtn","si1_docno","si1_date",
                "si1_capnm", "si1_capdt"], data=["O", self.docno, self.trdt,
                self.opts["capnm"], self.sysdtw], where=[("si1_cono", "=",
                self.opts["conum"]), ("si1_rtn", "=", self.typs),
                ("si1_docno", "=", actdoc)])
            self.sql.updRec("slsiv2", cols=["si2_rtn","si2_docno","si2_capnm",
                "si2_capdt"], data=["O", self.docno, self.opts["capnm"],
                self.sysdtw], where=[("si2_cono", "=", self.opts["conum"]),
                ("si2_rtn", "=", self.typs), ("si2_docno", "=", actdoc)])
            self.sql.updRec("slsiv3", cols=["si3_rtn", "si3_docno"], data=["O",
                self.docno], where=[("si3_cono", "=", self.opts["conum"]),
                ("si3_rtn", "=", self.typs), ("si3_docno", "=", actdoc)])
            self.typs = "O"
            return
        # Dispatch of order or quotation - change slsiv1, slsiv2 and slsiv3
        if self.typs in ("O", "W", "Q") and self.acttyp == "D":
            actdoc = self.docno
            self.doGetDocno("I")
            data = self.sql.getRec("slsiv1", where=[("si1_cono", "=",
                self.opts["conum"]), ("si1_rtn", "=", self.typs), ("si1_docno",
                "=", actdoc)], limit=1)
            data[self.sql.slsiv1_col.index("si1_rtn")] = "I"
            data[self.sql.slsiv1_col.index("si1_docno")] = self.docno
            data[self.sql.slsiv1_col.index("si1_date")] = self.trdt
            ordno = CCD(actdoc, "Na", 9).work
            data[self.sql.slsiv1_col.index("si1_our_ord")] = ordno
            data[self.sql.slsiv1_col.index("si1_capnm")] = self.opts["capnm"]
            data[self.sql.slsiv1_col.index("si1_capdt")] = self.sysdtw
            # Write and Commit the new invoice header
            self.sql.insRec("slsiv1", data=data)
            self.opts["mf"].dbm.commitDbase()
            # Update order/quote header by inserting the invoice number
            self.sql.updRec("slsiv1", cols=["si1_invno"], data=[self.docno],
                where=[("si1_cono", "=", self.opts["conum"]), ("si1_rtn", "=",
                self.typs), ("si1_docno", "=", actdoc)])
            # Move the order/quote body lines to the new invoice
            self.sql.updRec("slsiv2", cols=["si2_rtn", "si2_docno",
                "si2_capnm", "si2_capdt"], data=["I", self.docno,
                self.opts["capnm"], self.sysdtw], where=[("si2_cono",
                "=", self.opts["conum"]), ("si2_rtn", "=", self.typs),
                ("si2_docno", "=", actdoc)])
            # Update slsiv3
            self.sql.updRec("slsiv3", cols=["si3_rtn", "si3_docno"],
                data=["I", self.docno], where=[("si3_cono", "=",
                self.opts["conum"]), ("si3_rtn", "=", self.typs),
                ("si3_docno", "=", actdoc)])
            self.typs = "I"
            # Check and change V.A.T. rates if applicable and reload screen
            chg = False
            recs = self.sql.getRec("slsiv2", where=[("si2_cono", "=",
                self.opts["conum"]), ("si2_rtn", "=", "I"), ("si2_docno",
                "=", self.docno)])
            for rec in recs:
                cod = rec[self.sql.slsiv2_col.index("si2_vat_code")]
                rat = rec[self.sql.slsiv2_col.index("si2_vat_rate")]
                chk = getVatRate(self.sql, rec[0], cod, self.trdt)
                if rat != chk:
                    chg = True
                    self.sql.updRec("slsiv2", cols=["si2_vat_rate"],
                        data=[chk], where=[("si2_cono", "=", rec[0]),
                        ("si2_rtn", "=", rec[1]), ("si2_docno", "=",
                        rec[2]), ("si2_line", "=", rec[3])])
            if chg:
                self.doReadLoadStr()
        else:
            actdoc = None
        # Create Stores Transactions
        trn = self.sql.getRec("slsiv2", where=[("si2_cono", "=",
            self.opts["conum"]), ("si2_rtn", "=", self.typs),
            ("si2_docno", "=", self.docno)])
        if not trn:
            return
        for line in trn:
            self.doExtractData(line)
            gtype = self.sql.getRec("strmf1", cols=["st1_type"],
                where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                "=", self.grp), ("st1_code", "=", self.code)], limit=1)
            if gtype[0] == "R":
                self.doRecipe(atype="U", lineno=self.oldline)
                icost = self.icost
                tcost = self.tcost
            else:
                icost, tcost = getCost(self.sql, self.opts["conum"], self.grp,
                    self.code, loc=self.loc, qty=self.qty, ind="I", tot=True)
            if self.typs == "I":
                rtn = 7
                qty = float(ASD(0) - ASD(self.qty))
                cst = float(ASD(0) - ASD(tcost))
                sel = float(ASD(0) - ASD(self.excamt))
                vat = float(ASD(0) - ASD(self.vatamt))
            elif self.typs == "C":
                rtn = 7
                qty = self.qty
                cst = tcost
                sel = self.excamt
                vat = self.vatamt
            if self.ribbon:
                ref2 = self.ribbon[0]
            else:
                ref2 = ""
            # Write strtrn record
            data = [self.opts["conum"], self.grp, self.code, self.loc,
                self.trdt, rtn, self.othno, self.batch, ref2, qty, cst, sel,
                self.curdt, self.name, self.chain, self.acno, self.repno,
                "INV", self.disrat, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("strtrn", data=data)
            if gtype[0] == "R":
                # Recipe issue and receive items
                items = self.sql.getRec("slsiv3", where=[("si3_cono",
                    "=", self.opts["conum"]), ("si3_rtn", "=", self.typs),
                    ("si3_docno", "=", self.othno), ("si3_line", "=",
                    self.oldline)])
                for item in items:
                    quan = item[6] * qty
                    icost = getCost(self.sql, self.opts["conum"], item[4],
                        item[5], loc=self.loc, qty=1, ind="I")
                    cost = icost * quan
                    data = [self.opts["conum"], item[4], item[5], self.loc,
                        self.trdt, 6, self.othno, self.batch, ref2, quan, cost,
                        0, self.curdt, self.name, self.chain, self.acno,
                        self.repno, "INV", 0, "", self.opts["capnm"],
                        self.sysdtw, 0]
                    self.sql.insRec("strtrn", data=data)
                quan = float(ASD(0) - ASD(qty))
                cost = float(ASD(0) - ASD(cst))
                data = [self.opts["conum"], self.grp, self.code, self.loc,
                    self.trdt, 5, self.othno, self.batch, ref2, quan, cost, 0,
                    self.curdt, self.name, self.chain, self.acno, "", "INV", 0,
                    "", self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("strtrn", data=data)
            # If Integrated Create GL Transaction (Sales & Cost of Sales)
            if self.stgl == "Y":
                col = ["glt_tramt", "glt_taxamt", "glt_seq"]
                # Stock on Hand Control
                if cst:
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", self.soh), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt), ("glt_type",
                        "=", 1), ("glt_refno", "=", self.othno), ("glt_batch",
                        "=", self.batch), ("glt_desc", "=", self.name)],
                        limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(cst))
                        self.sql.updRec("gentrn", cols=["glt_tramt"],
                            data=[at1], where=[("glt_seq", "=", rec[2])])
                    else:
                        data = (self.opts["conum"], self.soh, self.curdt,
                            self.trdt, 1, self.othno, self.batch, cst, 0,
                            self.name, "", "", 0, self.opts["capnm"],
                            self.sysdtw, 0)
                        self.sql.insRec("gentrn", data=data)
                # Sales and COS Accounts
                acc = self.sql.getRec("strmf1", cols=["st1_sls",
                    "st1_cos"], where=[("st1_cono", "=", self.opts["conum"]),
                    ("st1_group", "=", self.grp), ("st1_code", "=",
                    self.code)], limit=1)
                # Sales Account
                if sel or vat:
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", acc[0]), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt), ("glt_type",
                        "=", 1), ("glt_refno", "=", self.othno), ("glt_batch",
                        "=", self.batch), ("glt_desc", "=", self.name)],
                        limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(sel))
                        at2 = float(ASD(rec[1]) + ASD(vat))
                        self.sql.updRec("gentrn", cols=["glt_tramt",
                            "glt_taxamt"], data=[at1, at2], where=[("glt_seq",
                            "=", rec[2])])
                    else:
                        data = (self.opts["conum"], acc[0], self.curdt,
                            self.trdt, 1, self.othno, self.batch, sel, vat,
                            self.name, self.vatcod, "", 0, self.opts["capnm"],
                            self.sysdtw, 0)
                        self.sql.insRec("gentrn", data=data)
                # Cost of Sales Account
                if cst:
                    cst = float(ASD(0) - ASD(cst))
                    rec = self.sql.getRec("gentrn", cols=col,
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", acc[1]), ("glt_curdt", "=",
                        self.curdt), ("glt_trdt", "=", self.trdt), ("glt_type",
                        "=", 1), ("glt_refno", "=", self.othno), ("glt_batch",
                        "=", self.batch), ("glt_desc", "=", self.name)],
                        limit=1)
                    if rec:
                        at1 = float(ASD(rec[0]) + ASD(cst))
                        self.sql.updRec("gentrn", cols=["glt_tramt"],
                            data=[at1], where=[("glt_seq", "=", rec[2])])
                    else:
                        data = (self.opts["conum"], acc[1], self.curdt,
                            self.trdt, 1, self.othno, self.batch, cst, 0,
                        self.name, "", "", 0, self.opts["capnm"], self.sysdtw,
                        0)
                        self.sql.insRec("gentrn", data=data)
            # Create VAT Transaction (ctlvtf)
            if self.typs in ("I", "C"):
                if self.typs == "I":
                    rtn = 1
                elif self.typs == "C":
                    rtn = 4
                whr = [("vtt_cono", "=", self.opts["conum"]), ("vtt_code", "=",
                    self.vatcod), ("vtt_vtyp", "=", "O"), ("vtt_curdt", "=",
                    self.curdt), ("vtt_styp", "=", "D"), ("vtt_ttyp", "=",
                    rtn), ("vtt_batch", "=", self.batch), ("vtt_refno", "=",
                    self.othno), ("vtt_refdt", "=", self.trdt), ("vtt_acno",
                    "=", self.acno), ("vtt_desc", "=", self.name)]
                rec = self.sql.getRec("ctlvtf", cols=["vtt_exc",
                    "vtt_tax"], where=whr, limit=1)
                if rec:
                    at1 = float(ASD(rec[0]) + ASD(sel))
                    at2 = float(ASD(rec[1]) + ASD(vat))
                    self.sql.updRec("ctlvtf", cols=["vtt_exc", "vtt_tax"],
                        data=[at1, at2], where=whr)
                else:
                    self.sql.insRec("ctlvtf", data=[self.opts["conum"],
                        self.vatcod, "O", self.curdt, "D", rtn, self.batch,
                        self.othno, self.trdt, self.acno, self.name, sel, vat,
                        0, self.opts["capnm"], self.sysdtw, 0])
        # Create Debtors Transaction
        if self.typs == "I":
            self.opts["rtn"] = 1
            self.agetot = self.totinv
            vat = self.totvat
            self.doAgeCurrent()
        elif self.typs == "C":
            self.opts["rtn"] = 4
            self.agetot = float(ASD(0) - ASD(self.totinv))
            vat = float(ASD(0) - ASD(self.totvat))
            self.doAgeNormal()
        ref2 = ""
        if self.ribbon:
            if self.ribbon[0]:
                ref2 = self.ribbon[0].strip()
            elif self.ribbon[1]:
                ref2 = self.ribbon[1].strip()[:9]
        if not ref2 and actdoc:
            ref2 = actdoc
        if self.drsdel:
            desc = self.drsdel[1]
        else:
            desc = self.name
        data = [self.opts["conum"], self.chain, self.acno, self.opts["rtn"],
            self.othno, self.batch, self.trdt, ref2, self.agetot, vat,
            self.curdt, desc, self.vatcod, "", self.opts["capnm"], self.sysdtw,
            0]
        self.sql.insRec("drstrn", data=data)
        # If Integrated Create GL Transaction (Drs Control & VAT)
        if self.drgl == "Y":
            # Debtors Control
            if self.totinv:
                if self.typs == "C":
                    amt = float(ASD(0) - ASD(self.totinv))
                else:
                    amt = self.totinv
                data = (self.opts["conum"], self.dctl, self.curdt, self.trdt,
                    1, self.othno, self.batch, amt, 0, self.name, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            # VAT Control
            if self.totvat:
                if self.typs == "C":
                    vat = self.totvat
                else:
                    vat = float(ASD(0) - ASD(self.totvat))
                data = (self.opts["conum"], self.vctl, self.curdt, self.trdt,
                    1, self.othno, self.batch, vat, 0, self.name, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)

    def doGetDocno(self, atype):
        # Get Next Document Number
        docno = self.sql.getRec("slsiv1", cols=["max(si1_docno)"],
            where=[("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "=", atype)], limit=1)[0]
        if not docno:
            docno = 0
        if atype not in ("C", "I"):
            docno += 1
        else:
            if atype == "I":
                dtyp = 1
            else:
                dtyp = 4
            check = True
            while check:
                docno += 1
                nxt = CCD(docno, "Na", 9).work
                check = self.sql.getRec("drstrn", where=[("drt_cono",
                    "=", self.opts["conum"]), ("drt_chain", "=", self.chain),
                    ("drt_acno", "=", self.acno), ("drt_type", "=", dtyp),
                    ("drt_ref1", "=", nxt)])
        self.docno = CCD(docno, "UI", 9).work
        self.othno = CCD(docno, "Na", 9).work

    def doCalSell(self):
        if self.gtype == "R":
            gtyp = [self.typs, self.docno, self.lineno]
        else:
            gtyp = False
        self.rrp = getSell(self.sql, self.opts["conum"], self.grp,
            self.code, self.loc, self.opts["level"], recp=gtyp)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        if self.acttyp not in ("A", "D", "X"):
            self.sql.updRec("slsiv1", cols=["si1_invno"], data=["cancel"],
                where=[("si1_cono", "=", self.opts["conum"]), ("si1_rtn", "=",
                self.typs), ("si1_docno", "=", self.docno)])
            self.opts["mf"].dbm.commitDbase()
        self.df.setViewPort(self.typs, 0)
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
