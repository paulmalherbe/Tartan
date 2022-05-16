"""
SYNOPSIS
    Creditors Masterfile Maintenance.

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
from TartanClasses import FileImport, GetCtl, ProgressBar, PwdConfirm, Sql
from TartanClasses import TabPrt, TartanDialog
from tartanFunctions import askQuestion, chkGenAcc, genAccNum, showError

class cr1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "ctlnot", "crsmst",
            "crstrn", "genmst", "strpom"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.glint = crsctl["ctc_glint"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [
                ("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        tag = (
            ("Basic-_A",None,("T",1,1),("T",0,1)),
            ("Basic-_B",None,("T",1,1),("T",0,1)))
        r1s = (("Monthly","M"),("Daily","D"))
        r2s = (("Yes","Y"),("No","N"))
        self.fld = [
            (("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","Y",self.doAcno,crm,None,("efld",),None,
                "To Automatically Generate Account Numbers for "\
                "New Accounts enter a Blank Account Number."),
            (("T",0,0,0),"INA",30,"Name","",
                "","N",self.doName,None,self.doDelete,("notblank",)),
            (("T",1,0,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",1,1,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",1,2,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",1,3,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",1,4,0),"INA",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",1,5,0),"INA",20,"Fax Number","",
                "","N",None,None,None,("efld",)),
            (("T",1,6,0),"INA",30,"Manager's Name","",
                "","N",None,None,None,("efld",)),
            (("T",1,6,0),"ITX",30,"E-Mail","Manager's E-Mail",
                "","N",None,None,None,("email",)),
            (("T",1,7,0),"INA",30,"Account's Contact","Account's Contact Name",
                "","N",None,None,None,("efld",)),
            (("T",1,7,0),"ITX",30,"E-Mail","Account's E-Mail",
                "","N",None,None,None,("email",)),
            (("T",1,8,0),"INA",30,"Order's Contact","Order's Contact Name",
                "","N",None,None,None,("efld",)),
            (("T",1,8,0),"ITX",30,"E-Mail","Order's E-Mail",
                "","N",None,None,None,("email",)),
            (("T",1,9,0),"Id1",10,"Date Account Opened","",
                self.sysdtw,"N",None,None,None,("efld",)),
            (("T",1,10,0),"INA",10,"V.A.T Number","",
                "","N",None,None,None,("efld",)),
            (("T",2,0,0),("IRB",r1s),0,"Terms Base","",
                "M","N",self.doTermsBase,None,None,None),
            (("T",2,1,0),"IUI",2,"Statement Day","",
                "","N",None,None,None,("between",1,30)),
            (("T",2,2,0),"IUI",3,"Terms","",
                "","N",None,None,None,("between",0,90)),
            (("T",2,3,0),"IUI",7,"Credit Limit","",
                "","N",None,None,None,("efld",)),
            (("T",2,4,0),"IUD",5.2,"Trade Discount","",
                "","N",None,None,None,("efld",)),
            (("T",2,5,0),"IUD",5.2,"Settlement Discount",
                "Settlement Discount","","N",None,None,None,("efld",)),
            (("T",2,6,0),("IRB",r2s),0,"Payment Indicator","",
                "Y","N",None,None,None,None),
            (("T",2,7,0),"INA",20,"Bank Name","",
                "","N",None,None,None,("efld",)),
            (("T",2,8,0),"IUI",8,"Bank Branch","",
                "","N",None,None,None,("efld",)),
            (("T",2,9,0),"INA",16,"Bank Account","",
                "","N",None,None,None,("efld",))]
        if self.glint == "Y":
            self.fld.append((("T",2,10,0),"IUI",7,"G/L Account Number",
                "G/L Account Number","","N",self.doGlac,glm,None,("efld",)))
        else:
            self.fld.append((("T",2,10,0),"OUI",7,"G/L Account Number"))
        but = (
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),
                "Import Account Details from a CSV or XLS File."),
            ("Accept",None,self.doAccept,0,("T",1,1),("T",0,1)),
            ("Print",None,self.doPrint,0,("T",0,2),("T",2,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",2,0)),
            ("Quit",None,self.doQuit,1,None,None))
        tnd = ((self.doEnd,"N"), (self.doEnd,"N"), (self.doAccept,"Y"))
        txt = (self.doExit, self.doExit, self.doExit)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tags=tag, butt=but, tend=tnd, txit=txt, clicks=self.doClick)
        if "args" in self.opts:
            self.df.doKeyPressed("T", 0, 0, data=self.opts["args"])

    def doClick(self, *opts):
        if self.df.pag == 0:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doAcno(self, frt, pag, r, c, p, i, w):
        self.acno = w
        if self.acno:
            self.old = self.sql.getRec("crsmst", where=[("crm_cono",
                "=", self.opts["conum"]), ("crm_acno", "=", self.acno)],
                limit=1)
        if not self.acno or not self.old:
            ok = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Account?", default="no")
            if ok == "no":
                return "Invalid Account Number"
            pw = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="CRS", code="NewAcc")
            if pw.flag == "no":
                if "args" in self.opts:
                    return "xt"
                else:
                    return "New Account Creation is Not Allowed"
            self.new = True
        elif self.old[self.sql.crsmst_col.index("crm_stat")] == "X":
            return "Invalid Account, Redundant"
        else:
            self.new = False
            self.df.loadEntry("T", pag, p+1, data=self.old[2])
            d = 3
            for pge in range(1, self.df.pgs+1):
                for x in range(0, self.df.topq[pge]):
                    self.df.loadEntry("T", pge, x, data=self.old[d])
                    d = d + 1

    def doName(self, frt, pag, r, c, p, i, w):
        self.name = w
        if self.new and not self.acno:
            for x in range(1, 100):
                self.acno = genAccNum(self.name, x, 7)
                chk = self.sql.getRec("crsmst", where=[("crm_cono",
                    "=", self.opts["conum"]), ("crm_acno", "=", self.acno)],
                    limit=1)
                if not chk:
                    break
            self.df.loadEntry("T", 0, 0, data=self.acno)

    def doTermsBase(self, frt, pag, r, c, p, i, w):
        if w == "D":
            self.df.loadEntry(frt, pag, p+1, 0)
            return "sk1"

    def doGlac(self, frt, pag, r, c, p, i, w):
        if w:
            chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
            if type(chk) is str:
                return chk

    def doDelete(self):
        trs = self.sql.getRec("crstrn", cols=["count(*)"],
            where=[("crt_cono", "=", self.opts["conum"]), ("crt_acno",
            "=", self.acno)], limit=1)
        if trs[0]:
            return "%s Transactions Exist, Not Deleted" % trs[0]
        pom = self.sql.getRec("strpom", cols=["count(*)"],
            where=[("pom_cono", "=", self.opts["conum"]), ("pom_acno", "=",
            self.acno)], limit=1)
        if pom[0]:
            return "%s Purchase Order Exists, Not Deleted" % pom[0]
        nte = self.sql.getRec("ctlnot", cols=["count(*)"],
            where=[("not_cono", "=", self.opts["conum"]), ("not_sys", "=",
            "CRS"), ("not_key", "=", self.acno)], limit=1)
        if nte[0]:
            return "%s Notes Exist, Not Deleted" % nte[0]
        self.sql.delRec("crsmst", where=[("crm_cono", "=", self.opts["conum"]),
            ("crm_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["crsmst", "D", "%03i%-7s" % \
            (self.opts["conum"], self.acno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        if self.df.pag == 0:
            self.df.focusField("T", 1, 1, clr=self.new)
        elif self.df.pag == 1:
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
                self.df.selPage(self.df.tags[pag-1][0])
            else:
                self.df.focusField(frt, pag, (col+1), err=mes)
            return
        data = [self.opts["conum"]]
        for x in range(0, 3):
            for y in range(0, len(self.df.t_work[x][0])):
                data.append(self.df.t_work[x][0][y])
        if self.new:
            data.extend(["N", ""])
            self.sql.insRec("crsmst", data=data)
        else:
            col = self.sql.crsmst_col
            data.append(self.old[col.index("crm_stat")])
            data.append(self.old[col.index("crm_xflag")])
            if data != self.old[:len(data)]:
                self.sql.updRec("crsmst", data=data, where=[("crm_cono", "=",
                    self.opts["conum"]), ("crm_acno", "=", self.acno)])
                dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
                for num, dat in enumerate(self.old):
                    if dat != data[num]:
                        self.sql.insRec("chglog", data=["crsmst", "U",
                            "%03i%-7s" % (self.opts["conum"], self.acno),
                            col[num], dte, self.opts["capnm"], str(dat),
                            str(data[num]), "", 0])
        if "args" in self.opts:
            self.doQuit()
        else:
            self.opts["mf"].dbm.commitDbase()
            self.df.last[0] = [0, 0]
            self.df.selPage("Basic-A")
            self.df.focusField("T", 0, 1)

    def doPrint(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            name=self.__class__.__name__, tabs="crsmst",
            where=[("crm_cono", "=", self.opts["conum"]),
            ("crm_acno", "=", self.acno)])
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doImport(self):
        self.df.setWidget(self.df.B3, state="disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="crsmst", impskp=["crm_cono"])
        sp = ProgressBar(self.opts["mf"].body,
            typ="Importing Creditor's Accounts", mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            if not line[0]:
                if not line[1]:
                    err = "Blank Account Number and Blank Name"
                    break
                for x in range(1, 100):
                    line[0] = genAccNum(line[1], x, 7)
                    chk = self.sql.getRec("crsmst", where=[("crm_cono",
                        "=", self.opts["conum"]), ("crm_acno", "=", line[0])],
                        limit=1)
                    if not chk:
                        break
            chk = self.sql.getRec("crsmst", where=[("crm_cono",
                "=", self.opts["conum"]), ("crm_acno", "=", line[0])], limit=1)
            if chk:
                err = "%s %s Already Exists" % (fi.impcol[0][0], line[0])
                break
            if not line[1]:
                err = "Blank Name"
                break
            if not line[14]:
                line[14] = self.sysdtw
            if not line[16]:
                line[16] = "M"
            if not line[17]:
                line[17] = 30
            if not line[18]:
                line[18] = 30
            if not line[22]:
                line[22] = "Y"
            if self.glint and line[26]:
                chk = self.sql.getRec("genmst", where=[("glm_cono",
                    "=", self.opts["conum"]), ("glm_acno", "=", line[26])],
                    limit=1)
                if not chk:
                    err = "Invalid General Ledger Account"
                    break
            line.insert(0, self.opts["conum"])
            self.sql.insRec("crsmst", data=line)
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

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.selPage("Basic-A")
        self.df.focusField("T", 0, 1)

    def doExit(self):
        if self.df.pag == 0:
            self.doQuit()
        elif self.df.pag == 1:
            self.df.focusField("T", 0, 1)
        else:
            self.df.selPage("Basic-A")

    def doQuit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
