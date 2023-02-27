"""
SYNOPSIS
    Debtors Materfile Maintenance.

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
from TartanClasses import FileImport, GetCtl, ProgressBar, PwdConfirm, Sql
from TartanClasses import TabPrt, TartanDialog
from tartanFunctions import askQuestion, callModule, genAccNum, showError

class dr1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmes", "ctlrep", "chglog",
            "ctlnot", "slsiv1", "drsact", "drschn", "drsdel", "drsmst",
            "drstrn", "drstyp"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.chains = drsctl["ctd_chain"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        drc = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1"))}
        if self.chains == "Y":
            drm["where"] = [("drm_cono", "=", self.opts["conum"])]
            drm["whera"] = [["T", "drm_chain", 0]]
        else:
            drm["where"] = [
            ("drm_cono", "=", self.opts["conum"]),
            ("drm_chain", "=", 0)]
        drm["where"].append(("drm_stat", "<>", "X"))
        dlm = {
            "stype": "R",
            "tables": ("drsdel",),
            "cols": (
                ("del_code", "", 0, "Del-Cod"),
                ("del_add1", "", 0, "Address", "Y"))}
        rpm = {
            "stype": "R",
            "tables": ("ctlrep",),
            "cols": (
                ("rep_code", "", 0, "Rep"),
                ("rep_name", "", 0, "Name", "Y")),
            "where": [("rep_cono", "=", self.opts["conum"])]}
        act = {
            "stype": "R",
            "tables": ("drsact",),
            "cols": (
                ("dac_code", "", 0, "Cod"),
                ("dac_desc", "", 0, "Description", "Y"))}
        typ = {
            "stype": "R",
            "tables": ("drstyp",),
            "cols": (
                ("dtp_code", "", 0, "Cod"),
                ("dtp_desc", "", 0, "Description", "Y"))}
        msi = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details", "Y")),
            "where": [("mss_system", "=", "INV")]}
        mss = {
            "stype": "R",
            "tables": ("ctlmes",),
            "cols": (
                ("mss_message", "", 0, "Num"),
                ("mss_detail", "NA", 50, "Details", "Y")),
            "where": [("mss_system", "=", "STA")]}
        tag = (
            ("Basic-_A",None,("T",1,1),("T",0,1)),
            ("Basic-_B",None,("T",1,1),("T",0,1)))
        r1s = (("Yes","Y"),("No","N"))
        r2s = (
            ("New","N"),
            ("Good","G"),
            ("Fair","F"),
            ("Poor","P"),
            ("Bad","B"))
        self.fld = [
            [("T",0,0,0),"IUI",3,"Chain Store","",
                "","Y",self.doChain,drc,None,("efld",)],
            [("T",0,0,14),"INA",7,"Acc-Num","Account Number",
                "","N",self.doAcno,drm,None,("efld",),None,
                "To Automatically Generate Account Numbers for "\
                "New Accounts enter a Blank Account Number."],
            (("T",0,0,30),"INA",30,"Name","",
                "","N",self.doName,None,self.doDelete,("notblank",)),
            [("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","Y",self.doAcno,drm,None,("efld",),None,
                "To Automatically Generate Account Numbers for "\
                "New Accounts enter a Blank Account Number."],
            (("T",0,0,14),"INA",30,"Name","",
                "","N",self.doName,None,self.doDelete,("notblank",)),
            (("T",1,0,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",1,1,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",1,2,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",1,3,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",1,4,0),"INA",20,"Telephone","",
                "","N",None,None,None,("efld",)),
            (("T",1,5,0),"INA",20,"Fax","",
                "","N",None,None,None,("efld",)),
            (("T",1,6,0),"INA",30,"Manager","Manager's Name",
                "","N",None,None,None,("efld",)),
            (("T",1,6,47),"ITX",30,"E-Mail","Manager's E-Mail Address",
                "","N",None,None,None,("email",)),
            (("T",1,7,0),"INA",30,"Accounts","Accounts Contact",
                "","N",None,None,None,("efld",)),
            (("T",1,7,47),"ITX",30,"E-Mail","Accounts E-Mail Address",
                "","N",None,None,None,("email",)),
            (("T",1,8,0),"INA",30,"Sales","Sales Contact",
                "","N",None,None,None,("efld",)),
            (("T",1,8,47),"ITX",30,"E-Mail","Sales E-Mail Address",
                "","N",None,None,None,("email",)),
            (("T",1,9,0),"Id1",10,"Date Opened","Date Account Opened",
                self.sysdtw,"N",None,None,None,("efld",)),
            (("T",1,10,0),"Id1",10,"Date Registered","",
                "","N",None,None,None,("efld",)),
            (("T",1,11,0),"INA",10,"V.A.T Number","",
                "","N",None,None,None,("efld",)),
            (("T",1,12,0),"INa",7,"Delivery Code","",
                "","N",self.doDelivery,dlm,None,("efld",)),
            (("T",1,13,0),"INa",3,"Rep Code","",
                "","N",self.doRep,rpm,None,("efld",)),
            (("T",1,13,20),"ONA",26,""),
            (("T",1,14,0),"IUA",3,"Business Activity","",
                "","N",self.doBusAct,act,None,("efld",)),
            (("T",1,14,20),"ONA",26,""),
            (("T",1,15,0),"IUA",3,"Business Type","",
                "","N",self.doBusTyp,typ,None,("efld",)),
            (("T",1,15,20),"ONA",26,""),
            (("T",2,0,0),"IUI",1,"Price Level","",
                "","N",None,None,None,("efld",)),
            (("T",2,1,0),"IUD",5.2,"Discount Percentage","",
                "","N",None,None,None,("efld",)),
            (("T",2,2,0),"IUD",5.2,"Interest Percentage","",
                "","N",None,None,None,("efld",)),
            (("T",2,3,0),"IUI",3,"Referral Terms","",
                "","N",None,None,None,("efld",)),
            (("T",2,4,0),"IUI",3,"Rejected Terms","",
                "","N",None,None,None,("efld",)),
            (("T",2,5,0),"IUI",5,"Credit Limit","",
                "","N",None,None,None,("efld",)),
            (("T",2,6,0),("IRB",r1s),0,"Stop Indicator","",
                "N","N",None,None,None,None),
            (("T",2,7,0),"IUI",3,"Invoice Message","",
                "","N",self.doImes,msi,None,("efld",)),
            (("T",2,7,22),"ONA",50,""),
            (("T",2,8,0),"IUI",3,"Statement Message","",
                "","N",self.doSmes,mss,None,("efld",)),
            (("T",2,8,22),"ONA",50,""),
            (("T",2,9,0),("IRB",r2s),0,"Credit Rating","",
                "N","N",None,None,None,None)]
        but = (
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),
                "Import Account Details from a CSV or XLS File."),
            ("Accept",None,self.doAccept,0,("T",1,1),("T",0,1)),
            ("Print", None, self.doPrint,0,("T",1,1),("T",0,1)),
            ("Cancel", None, self.doCancel,0,("T",1,1),("T",0,1)),
            ("Quit", None, self.doExit1,1,None,None))
        tnd = ((self.doEnd1,"N"), (self.doEnd2,"N"), (self.doAccept,"Y"))
        txt = (self.doExit1, self.doExit2, self.doExit3)
        if self.chains == "Y":
            del self.fld[3]
            del self.fld[3]
        else:
            del self.fld[0]
            del self.fld[0]
            del self.fld[0]
            self.chain = 0
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tags=tag, butt=but, tend=tnd, txit=txt, clicks=self.doClick)
        if "args" in self.opts:
            if self.chains == "Y":
                self.df.doKeyPressed("T", 0, 0, data=self.opts["args"][0])
                self.df.doKeyPressed("T", 0, 1, data=self.opts["args"][1])
            else:
                self.chain = self.opts["args"][0]
                self.df.doKeyPressed("T", 0, 0, data=self.opts["args"][1])

    def doClick(self, *opts):
        if self.df.pag == 0:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doChain(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
                self.opts["conum"]), ("chm_chain", "=", self.chain)], limit=1)
            if not acc:
                return "Invalid Chain Store"
        self.chain = w

    def doAcno(self, frt, pag, r, c, p, i, w):
        self.acno = w
        if self.acno:
            self.old = self.sql.getRec("drsmst", where=[("drm_cono",
                "=", self.opts["conum"]), ("drm_chain", "=", self.chain),
                ("drm_acno", "=", self.acno)], limit=1)
        if not self.acno or not self.old:
            ok = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Account?", default="no")
            if ok == "no":
                return "Invalid Account Number"
            pw = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="DRS", code="NewAcc")
            if pw.flag == "no":
                if "args" in self.opts:
                    return "xt"
                else:
                    return "New Account Creation is Not Allowed"
            self.new = True
        elif self.old[self.sql.drsmst_col.index("drm_stat")] == "X":
            return "Invalid Account, Redundant"
        else:
            self.new = False
            self.df.loadEntry("T", pag, p+1, data=self.old[3])
            d = 4
            for pg in range(1, self.df.pgs+1):
                for x in range(0, self.df.topq[pg]):
                    if pg == 1 and x in (17, 19, 21):
                        continue
                    if pg == 2 and x in (8, 10):
                        continue
                    if pg == 2 and x == 11 and not self.old[d]:
                        data = "N"
                    else:
                        data = self.old[d]
                    self.df.loadEntry("T", pg, x, data=data)
                    d += 1
            self.loadRep()
            self.loadAct()
            self.loadTyp()
            self.loadInvMess()
            self.loadStaMess()

    def loadRep(self):
        acc = self.sql.getRec("ctlrep", cols=["rep_name"],
            where=[("rep_cono", "=", self.opts["conum"]), ("rep_code", "=",
            self.df.t_work[1][0][16])], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 17, data=acc[0])

    def loadAct(self):
        acc = self.sql.getRec("drsact", cols=["dac_desc"],
            where=[("dac_code", "=", self.df.t_work[1][0][18])], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 19, data=acc[0])

    def loadTyp(self):
        acc = self.sql.getRec("drstyp", cols=["dtp_desc"],
            where=[("dtp_code", "=", self.df.t_work[1][0][20])], limit=1)
        if acc:
            self.df.loadEntry("T", 1, 21, data=acc[0])

    def loadInvMess(self):
        acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
            where=[("mss_system", "=", "INV"), ("mss_message", "=",
            self.df.t_work[2][0][7])], limit=1)
        if acc:
            self.df.loadEntry("T", 2, 8, data=acc[0])

    def loadStaMess(self):
        acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
            where=[("mss_system", "=", "STA"), ("mss_message", "=",
            self.df.t_work[2][0][9])], limit=1)
        if acc:
            self.df.loadEntry("T", 2, 10, data=acc[0])

    def doName(self, frt, pag, r, c, p, i, w):
        self.name = w
        if self.new and not self.acno:
            for x in range(1, 100):
                self.acno = genAccNum(self.name, x, 7)
                chk = self.sql.getRec("drsmst", where=[("drm_cono",
                    "=", self.opts["conum"]), ("drm_chain", "=", self.chain),
                    ("drm_acno", "=", self.acno)], limit=1)
                if not chk:
                    break
            self.df.loadEntry("T", 0, 0, data=self.acno)

    def doDelivery(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drsdel", where=[("del_code",
                "=", w)], limit=1)
            if not acc:
                ok = askQuestion(self.opts["mf"].body, head="Delivery Address",
                    mess="This Delivery Address Does Not Exist, Would "\
                    "You Like to Create It Now?", default="no")
                if ok == "no":
                    return "rf"
                callModule(self.opts["mf"], self.df, "drc410",
                    coy=(self.opts["conum"], self.opts["conam"]),
                    period=None, user=None, args=w)
                acc = self.sql.getRec("drsdel", where=[("del_code",
                    "=", w)], limit=1)
                if not acc:
                    return "rf"

    def doRep(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlrep", cols=["rep_name"],
                where=[("rep_cono", "=", self.opts["conum"]), ("rep_code",
                "=", w)], limit=1)
            if not acc:
                return "Invalid Rep"
            self.df.loadEntry("T", 1, p+1, data=acc[0])

    def doBusAct(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drsact", cols=["dac_desc"],
                where=[("dac_code", "=", w)], limit=1)
            if not acc:
                return "Invalid Business Activity"
            self.df.loadEntry("T", 1, p+1, data=acc[0])

    def doBusTyp(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drstyp", cols=["dtp_desc"],
                where=[("dtp_code", "=", w)], limit=1)
            if not acc:
                return "Invalid Business Type"
            self.df.loadEntry("T", 1, p+1, data=acc[0])

    def doImes(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "INV"), ("mss_message", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Invoice Message"
            self.df.loadEntry("T", 2, p+1, data=acc[0])

    def doSmes(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("ctlmes", cols=["mss_detail"],
                where=[("mss_system", "=", "STA"), ("mss_message", "=", w)],
                limit=1)
            if not acc:
                return "Invalid Statement Message"
            self.df.loadEntry("T", 2, p+1, data=acc[0])

    def doDelete(self):
        trs = self.sql.getRec("drstrn", cols=["count(*)"],
            where=[("drt_cono", "=", self.opts["conum"]), ("drt_chain", "=",
            self.chain), ("drt_acno", "=", self.acno)], limit=1)
        if trs[0]:
            return "%s Transactions Exist, Not Deleted" % trs[0]
        iv1 = self.sql.getRec("slsiv1", cols=["count(*)"],
            where=[("si1_cono", "=", self.opts["conum"]), ("si1_chain", "=",
            self.chain), ("si1_acno", "=", self.acno)], limit=1)
        if iv1[0]:
            return "%s Sales Document Exists, Not Deleted" % iv1[0]
        key = "%03i%s" % (self.chain, self.acno)
        nte = self.sql.getRec("ctlnot", cols=["count(*)"],
            where=[("not_cono", "=", self.opts["conum"]), ("not_sys", "=",
            "DRS"), ("not_key", "=", key)], limit=1)
        if nte[0]:
            return "%s Notes Exist, Not Deleted" % nte[0]
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.delRec("drsmst", where=[("drm_cono", "=", self.opts["conum"]),
            ("drm_chain", "=", self.chain), ("drm_acno", "=", self.acno)])
        self.sql.insRec("chglog", data=["drsmst", "D", "%03i%03i%-7s" % \
            (self.opts["conum"], self.chain, self.acno), "", dte,
            self.opts["capnm"], "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd1(self):
        self.df.focusField("T", 1, 1, clr=self.new)

    def doEnd2(self):
        self.df.selPage("Basic-B")
        self.df.focusField("T", 2, 1, clr=self.new)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            if pag > 0 and pag != self.df.pag:
                if frt == "T":
                    self.df.last[pag][0] = col+1
                else:
                    self.df.last[pag][1] = col+1
                self.df.selPage(self.df.tags[pag - 1][0])
            else:
                self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            data = [self.opts["conum"], self.chain]
            if self.chains == "Y":
                f = 1
            else:
                f = 0
            for x in range(f, f+2):
                data.append(self.df.t_work[0][0][x])
            for x in range(0, len(self.df.t_work[1][0])):
                if x in (17, 19, 21):
                    continue
                data.append(self.df.t_work[1][0][x])
            for x in range(0, len(self.df.t_work[2][0])):
                if x in (8, 10):
                    continue
                data.append(self.df.t_work[2][0][x])
            if self.new:
                data.extend(["N", ""])
                self.sql.insRec("drsmst", data=data)
            else:
                col = self.sql.drsmst_col
                data.append(self.old[col.index("drm_stat")])
                data.append(self.old[col.index("drm_xflag")])
                if data != self.old:
                    self.sql.updRec("drsmst", data=data, where=[("drm_cono",
                        "=", self.opts["conum"]), ("drm_chain", "=",
                        self.chain), ("drm_acno", "=", self.acno)])
                    dte = int("%04i%02i%02i%02i%02i%02i" %
                            time.localtime()[:-3])
                    for num, dat in enumerate(self.old):
                        if dat != data[num]:
                            self.sql.insRec("chglog", data=["drsmst", "U",
                                "%03i%03i%-7s" % (self.opts["conum"],
                                self.chain, self.acno), col[num], dte,
                                self.opts["capnm"], str(dat),
                                str(data[num]), "", 0])
            if "args" in self.opts:
                self.doExit1()
            else:
                self.opts["mf"].dbm.commitDbase()
                self.df.last[0] = [0, 0]
                self.df.selPage("Basic-A")
                self.df.focusField("T", 0, 1)

    def doImport(self):
        self.df.setWidget(self.df.B3, state="disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="drsmst", impskp=["drm_cono"])
        sp = ProgressBar(self.opts["mf"].body,
            typ="Importing Debtor's Accounts", mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            if not line[1]:
                if not line[2]:
                    err = "Blank Account Number and Blank Name"
                    break
                for x in range(1, 100):
                    line[1] = genAccNum(line[2], x, 7)
                    chk = self.sql.getRec("drsmst", where=[("drm_cono",
                        "=", self.opts["conum"]), ("drm_chain", "=", line[0]),
                        ("drm_acno", "=", line[1])], limit=1)
                    if not chk:
                        break
            chk = self.sql.getRec("drsmst", where=[("drm_cono",
                "=", self.opts["conum"]), ("drm_chain", "=", line[0]),
                ("drm_acno", "=", line[1])], limit=1)
            if chk:
                err = "%s %s %s %s Already Exists" % (fi.impcol[0][0], line[0],
                    fi.impcol[1][0], line[1])
                break
            if not line[2]:
                err = "Blank Name"
                break
            if not line[15]:
                line[15] = self.sysdtw
            if not line[28]:
                line[28] = "N"
            if not line[31]:
                line[31] = "N"
            line.insert(0, self.opts["conum"])
            self.sql.insRec("drsmst", data=line)
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

    def doPrint(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            name=self.__class__.__name__, tabs="drsmst", where=[("drm_cono",
            "=", self.opts["conum"]), ("drm_chain", "=", self.chain),
            ("drm_acno", "=", self.acno)])
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.selPage("Basic-A")
        self.df.focusField("T", 0, 1)

    def doExit1(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doExit2(self):
        self.df.focusField("T", 0, 1)

    def doExit3(self):
        self.df.selPage("Basic-A")

# vim:set ts=4 sw=4 sts=4 expandtab:
