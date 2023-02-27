"""
SYNOPSIS
    Loan Accounts Maintenance.

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
from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, genAccNum

class ln1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "lonmf1", "lonmf2"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        con = {
            "stype": "R",
            "tables": ("lonmf1",),
            "cols": (
                ("lm1_acno", "", 0, "Code"),
                ("lm1_name", "", 0, "Surname", "Y"),
                ("lm1_email", "", 0, "Email Address"))}
        if "args" in self.opts:
            fld = [
                (("T",0,0,0),"OUA",7,"Account Code"),
                (("T",0,1,0),"ITX",30,"Name","",
                    "","N",self.doName,None,None,("notblank",))]
            self.newacc = True
            self.acno = None
        else:
            fld = [
                (("T",0,0,0),"IUA",7,"Account Code","",
                    "","Y",self.doAcno,con,None,None),
                (("T",0,1,0),"ITX",30,"Name","",
                    "","N",self.doName,None,self.doDelete,("notblank",))]
        fld.extend([
            (("T",0,2,0),"ITX",30,"Address Line 1","",
                "","N",None,None,None,("efld",)),
            (("T",0,3,0),"ITX",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"ITX",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"ITX",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"ITX",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"ITX",20,"Fax Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"ITX",20,"Mobile Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"ITX",30,"E-Mail Address","",
                "","N",None,None,None,("email",))])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,1)),
            ("Quit", None, self.doExit,1,None,None))
        tnd = ((self.doAccept,"N"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt, clicks=self.doClick)

    def doClick(self, *opts):
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doAcno(self, frt, pag, r, c, p, i, w):
        if w:
            self.oldacc = self.sql.getRec("lonmf1", where=[("lm1_cono",
                "=", self.opts["conum"]), ("lm1_acno", "=", w)], limit=1)
            if not self.oldacc:
                return "Invalid Account Number"
            self.acno = w
            self.name = self.oldacc[self.sql.lonmf1_col.index("lm1_name")]
            self.email = self.oldacc[self.sql.lonmf1_col.index("lm1_email")]
            for num, dat in enumerate(self.oldacc[1:-1]):
                self.df.loadEntry("T", 0, num, data=dat)
            self.newacc = False
        else:
            yn = askQuestion(self.opts["mf"].body, "New Account",
                "Is This a New Loan Account?", default="no")
            if yn == "no":
                return "Invalid Account Number"
            self.newacc = True

    def doName(self, frt, pag, r, c, p, i, w):
        if self.newacc:
            chk = self.sql.getRec("lonmf1", where=[("lm1_cono", "=",
                self.opts["conum"]), ("lm1_name", "=", w)], limit=1)
            if chk:
                return "An Account With This Name Already Exists"
            for seq in range(1, 100):
                self.acno = genAccNum(w, seq)
                chk = self.sql.getRec("lonmf1", where=[("lm1_cono",
                    "=", self.opts["conum"]), ("lm1_acno", "=", self.acno)],
                    limit=1)
                if not chk:
                    break
            self.df.loadEntry(frt, pag, p-1, data=self.acno)

    def doDelete(self):
        chk = self.sql.getRec("lonmf2", cols=["count(*)"],
            where=[("lm2_cono", "=", self.opts["conum"]), ("lm2_acno",
            "=", self.acno)], limit=1)
        if chk[0]:
            return "Loans Exist, Not Deleted"
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.delRec("lonmf1", where=[("lm1_cono", "=", self.opts["conum"]),
            ("lm1_acno", "=", self.acno)])
        self.sql.insRec("chglog", data=["lonmf1", "D", "%03i%-7s" %
            (self.opts["conum"], self.acno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
            return
        # Create/Update Record
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        data = [self.opts["conum"]]
        for x in range(len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.newacc:
            self.sql.insRec("lonmf1", data=data)
        elif data != self.oldacc[:len(data)]:
            col = self.sql.lonmf1_col
            data.append(self.oldacc[col.index("lm1_xflag")])
            self.sql.updRec("lonmf1", data=data, where=[("lm1_cono", "=",
                self.opts["conum"]), ("lm1_acno", "=", self.acno)])
            for num, dat in enumerate(self.oldacc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["lonmf1", "U",
                        "%03i%-7s" % (self.opts["conum"], self.acno),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        if "args" in self.opts:
            self.doExit()
        else:
            self.opts["mf"].dbm.commitDbase()
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
