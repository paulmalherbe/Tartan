"""
SYNOPSIS
    General Ledger Accounts Maintenance.

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
from TartanClasses import FileImport, GetCtl, ProgressBar
from TartanClasses import SplashScreen, Sql, TartanDialog
from tartanFunctions import showError
from tartanWork import datdic

class gl1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        self.gldep = ctlsys["sys_gl_dep"]
        self.gldig = ctlsys["sys_gl_dig"]
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
        self.mods = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            self.mods.append(ctlmst["ctm_modules"][x:x+2])
        tabs = ["ctlctl", "ctldep", "ctlvmf", "genmst", "genbal", "genbud",
                "genrpt", "gentrn", "chglog"]
        if "CR" in self.mods:
            tabs.append("crsctl")
        if "DR" in self.mods:
            tabs.append("drsctl")
        if "ST" in self.mods:
            tabs.extend(["strctl", "strloc"])
        if "SI" in self.mods:
            tabs.append("slsctl")
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("genmst", cols=["count(*)"],
            where=[("glm_cono", "=", self.opts["conum"])], limit=1)
        if chk[0]:
            self.newgen = False
        else:
            self.newgen = True
        if "args" in self.opts:
            self.acno = None
        return True

    def mainProcess(self):
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        vat = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "Acc-Num"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        r1s = (("Profit & Loss","P"), ("Balance Sheet","B"))
        r2s = (("Yes","Y"), ("No","N"))
        fld = [
            (("T",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "","Y",self.doAccNum,glm,None,("notzero",)),
            (("T",0,1,0),("IRB",r1s),0,"Account Type","",
                "P","N",self.doTypCod,None,self.doDelete,None),
            (("T",0,2,0),"INA",30,"Description","Account Description",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),("IRB",r2s),0,"Allow Postings","",
                "Y","N",None,None,None,None),
            [("T",0,4,0),"IUA",1,"Tax Default","",
                "","N",self.doVatCod,vat,None,("notblank",)]]
        but = [
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),
                "Import a Chart of Accounts from a CSV or XLS file "\
                "having the following fields: Account Number, "\
                "Account Type (P/B), Description, Direct Postings (Y/N), "\
                "VAT Code"),
            ["Populate",None,self.doPopulate,0,("T",0,1),("T",0,2),
                "Generate a Chart of Accounts with Accompanying Control "\
                "Records and Financial Statement Report. This Only Applies "\
                "to Unpopulated (NEW) Ledgers."],
            ("Accept",None,self.doAccept,0,("T",0,2),(("T",0,0),("T",0,1))),
            ("Cancel",None,self.doCancel,0,("T",0,2),(("T",0,0),("T",0,1))),
            ("Quit",None,self.doQuit,1,None,None,"",1,4)]
        tnd = ((self.doEnd,"y"), )
        txt = (self.doQuit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)
        if not self.newgen:
            self.df.butt[1][4] = None
            self.df.butt[1][5] = None
            self.df.setWidget(self.df.B1, state="disabled")

    def doAccNum(self, frt, pag, r, c, p, i, w):
        self.acno = w
        self.old = self.sql.getRec("genmst", where=[("glm_cono", "=",
            self.opts["conum"]), ("glm_acno", "=", self.acno)], limit=1)
        if not self.old:
            self.new = True
            if self.gldep == "Y":
                err = self.doCheckDep(self.acno)
                if err:
                    return err
        elif "args" in self.opts:
            showError(self.opts["mf"].body, "Error",
                "Only a New Account is Allowed")
            return "rf"
        else:
            self.new = False
            for x in range(0, self.df.topq[pag]):
                self.df.loadEntry(frt, pag, p+x, data=self.old[x+1])

    def doTypCod(self, frt, pag, r, c, p, i, w):
        if self.new:
            if w == "P":
                self.df.topf[pag][4][5] = self.taxdf
            else:
                self.df.topf[pag][4][5] = "N"
        elif not self.df.topf[pag][4][5]:
            self.df.topf[pag][4][5] = "N"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[
                ("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=", w)],
            limit=1)
        if not acc:
            return "Invalid VAT Code"

    def doDelete(self):
        t = self.sql.getRec("gentrn", cols=["count(*)"],
            where=[("glt_cono", "=", self.opts["conum"]), (
                "glt_acno", "=", self.acno)],
            limit=1)
        if t[0]:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("genmst", where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", self.acno)])
        self.sql.delRec("genbal", where=[("glo_cono", "=", self.opts["conum"]),
            ("glo_acno", "=", self.acno)])
        self.sql.delRec("genbud", where=[("glb_cono", "=", self.opts["conum"]),
            ("glb_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["genmst", "D", "%03i%07i" %
            (self.opts["conum"], self.acno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        if self.newgen:
            self.df.butt[1][4] = None
            self.df.butt[1][5] = None
        data = [self.opts["conum"], self.acno,
            self.df.t_work[0][0][1], self.df.t_work[0][0][2],
            self.df.t_work[0][0][3], self.df.t_work[0][0][4]]
        if self.new:
            self.sql.insRec("genmst", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.genmst_col
            data.append(self.old[col.index("glm_xflag")])
            self.sql.updRec("genmst", data=data, where=[("glm_cono", "=",
                self.opts["conum"]), ("glm_acno", "=", self.acno)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["genmst", "U",
                        "%03i%07i" % (self.opts["conum"], self.acno),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.B3, state="disabled")
        if "args" in self.opts:
            self.doQuit()
        else:
            self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doImport(self):
        self.df.setWidget(self.df.B3, state="disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="genmst", impskp=["glm_cono"])
        sp = ProgressBar(self.opts["mf"].body,
            typ="Importing Chart of Accounts", mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            chk = self.sql.getRec("genmst", where=[("glm_cono",
                "=", self.opts["conum"]), ("glm_acno", "=", line[0])], limit=1)
            if chk:
                err = "%s %s Already Exists" % (fi.impcol[0][0], line[0])
                break
            if self.gldep == "Y":
                err = self.doCheckDep(line[0])
                if err:
                    break
            if line[1] not in ("B", "P"):
                err = "Invalid %s %s, Only B or P" % (fi.impcol[1][0], line[1])
                break
            if not line[2]:
                err = "Blank Description"
                break
            if line[3] not in ("Y", "N"):
                err = "Invalid %s %s" % (fi.impcol[3][0], line[3])
                break
            chk = self.sql.getRec("ctlvmf", where=[("vtm_cono",
                "=", self.opts["conum"]), ("vtm_code", "=", line[4])], limit=1)
            if not chk:
                err = "%s %s Does Not Exist" % (fi.impcol[4][0], line[4])
                break
            line.insert(0, self.opts["conum"])
            self.sql.insRec("genmst", data=line)
        sp.closeProgress()
        if err:
            err = "Line %s: %s" % ((num + 1), err)
            showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doCheckDep(self, acno):
        dep = int(acno / (10 ** (7 - self.gldig)))
        acc = int(acno % (10 ** (7 - self.gldig)))
        if dep:
            chk = self.sql.getRec("ctldep", where=[("dep_cono",
                "=", self.opts["conum"]), ("dep_code", "=", dep)], limit=1)
            if not chk:
                return "Invalid Department Number (%s)" % dep
            chk = self.sql.getRec("genmst", where=[("glm_cono", "=",
                self.opts["conum"]), ("glm_acno", "=", acc)], limit=1)
            if chk:
                return "This Account Number (%s) is in Use" % acc

    def doPopulate(self):
        if not self.newgen:
            showError(self.opts["mf"].body, "Populate Error",
                "You Cannot Populate with Existing Accounts")
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        if self.gldep == "Y":
            showError(self.opts["mf"].body, "Populate Error",
                "You Cannot Populate with Departments Enabled")
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        self.igcrs = "N"
        self.igdrs = "N"
        self.igstr = "N"
        self.df.setWidget(self.df.B3, state="disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Integrate Subsiduary Ledgers",)
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = []
        col = 0
        if "CR" in self.mods:
            fld.append((("T",0,col,0),("IRB",r1s),0,"Creditor's Ledger",
                "Creditor's Ledger","N","N",self.doIgCrs,None,None,None,None))
            col += 1
        if "DR" in self.mods:
            fld.append((("T",0,col,0),("IRB",r1s),0,"Debtor's Ledger",
                "Debtor's Ledger","N","N",self.doIgDrs,None,None,None,None))
            col += 1
        if "ST" in self.mods:
            fld.append((("T",0,col,0),("IRB",r1s),0,"Stores's Ledger",
                "Stores's Ledger","N","N",self.doIgStr,None,None,None,None))
        if fld:
            self.ig = TartanDialog(self.opts["mf"], title=tit, tops=True,
                eflds=fld, tend=((self.doIgEnd,"y"),), txit=(self.doIgExit,))
            self.ig.mstFrame.wait_window()
            if self.igexit:
                self.doQuit()
                return
        sp = SplashScreen(self.opts["mf"].body,
            "Populating Records\n\nPlease Wait ...")
        # genmst
        genmst = datdic["genmst"]
        for dat in genmst:
            dat.insert(0, self.opts["conum"])
            dat.append("Y")
            if dat[2] == "B":
                dat.append("N")
            else:
                dat.append(self.taxdf)
            self.sql.insRec("genmst", data=dat)
        # genrpt
        genrpt = datdic["genrpt"]
        for dat in genrpt:
            dat.insert(0, self.opts["conum"])
            self.sql.insRec("genrpt", data=dat)
        # ctlctl
        crsctl = 0
        drsctl = 0
        stksoh = 0
        ctlctl = datdic["ctlctl"]
        for dat in ctlctl:
            if dat[0] in ("crs_ctl", "dis_rec"):
                if self.igcrs != "Y":
                    continue
                if dat[0] == "crs_ctl":
                    crsctl = int(dat[2])
            elif dat[0] in ("drs_ctl", "dis_all"):
                if self.igdrs != "Y":
                    continue
                if dat[0] == "drs_ctl":
                    drsctl = int(dat[2])
            elif dat[0] in ("stk_soh", "stk_susp"):
                if self.igstr != "Y":
                    continue
                if dat[0] == "stk_soh":
                    stksoh = int(dat[2])
            elif dat[0] in ("wag_ctl", "wag_slc", "wag_sli"):
                continue
            dat.insert(0, self.opts["conum"])
            self.sql.insRec("ctlctl", data=dat)
        if "CR" in self.mods:
            chk = self.sql.getRec("crsctl",
                where=[("ctc_cono", "=", self.opts["conum"])])
            if not chk:
                self.sql.insRec("crsctl", data=[self.opts["conum"], self.igcrs,
                    "E", "", 0, 0, "remittance_advice", ""])
            else:
                self.sql.updRec("crsctl", cols=["ctc_glint"], data=[self.igcrs],
                    where=[("ctc_cono", "=", self.opts["conum"])])
            if self.igcrs == "Y" and crsctl:
                self.sql.updRec("genmst", cols=["glm_ind"], data=["N"],
                    where=[("glm_cono", "=", self.opts["conum"]),
                    ("glm_acno", "=", crsctl)])
        if "DR" in self.mods:
            chk = self.sql.getRec("drsctl",
                where=[("ctd_cono", "=", self.opts["conum"])])
            if not chk:
                self.sql.insRec("drsctl", data=[self.opts["conum"], self.igdrs,
                    "E", "N", "statement_normal", "Y", ""])
            else:
                self.sql.updRec("drsctl", cols=["ctd_glint"], data=[self.igdrs],
                    where=[("ctd_cono", "=", self.opts["conum"])])
            if self.igdrs == "Y" and drsctl:
                self.sql.updRec("genmst", cols=["glm_ind"], data=["N"],
                    where=[("glm_cono", "=", self.opts["conum"]),
                    ("glm_acno", "=", drsctl)])
        if "ST" in self.mods:
            chk = self.sql.getRec("strctl",
                where=[("cts_cono", "=", self.opts["conum"])])
            if not chk:
                self.sql.insRec("strctl", data=[self.opts["conum"], self.igstr,
                    "N", 1, "N", "purchase_order", ""])
            else:
                self.sql.updRec("strctl", cols=["cts_glint"], data=[self.igstr],
                    where=[("cts_cono", "=", self.opts["conum"])])
            chk = self.sql.getRec("strloc", where=[("srl_cono", "=",
                self.opts["conum"])])
            if not chk:
                self.sql.insRec("strloc", data=[self.opts["conum"], "1",
                    "Location Number One", "", "", "", ""])
            if self.igstr == "Y" and stksoh:
                self.sql.updRec("genmst", cols=["glm_ind"], data=["N"],
                    where=[("glm_cono", "=", self.opts["conum"]),
                    ("glm_acno", "=", stksoh)])
        if "SI" in self.mods:
            chk = self.sql.getRec("slsctl",
                where=[("ctv_cono", "=", self.opts["conum"])])
            if not chk:
                self.sql.insRec("slsctl", data=[self.opts["conum"],
                    "Y", "Y", "sales_document", ""])
        sp.closeSplash()
        self.df.butt[1][4] = None
        self.df.butt[1][5] = None
        self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doIgCrs(self, frt, pag, r, c, p, i, w):
        self.igcrs = w

    def doIgDrs(self, frt, pag, r, c, p, i, w):
        self.igdrs = w

    def doIgStr(self, frt, pag, r, c, p, i, w):
        self.igstr = w

    def doIgEnd(self):
        self.igexit = False
        self.ig.closeProcess()

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.focusField("T", 0, 1)

    def doIgExit(self):
        self.igexit = True
        self.ig.closeProcess()

    def doQuit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
