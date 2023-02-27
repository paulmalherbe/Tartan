"""
SYNOPSIS
    Loans's Ledger Account Code Change.

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

from TartanClasses import GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, genAccNum

class ln6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("ctlnot", "not_key"),
            ("lonmf1", "lm1_cono", "lm1_acno"),
            ("lonmf2", "lm2_cono", "lm2_acno"),
            ("lonrte", "lrt_cono", "lrt_acno"),
            ("lontrn", "lnt_cono", "lnt_acno"))
        tabs = []
        for tab in self.tables:
            tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        lonctl = gc.getCtl("lonctl", self.opts["conum"])
        if not lonctl:
            return
        self.autogen = "N"
        return True

    def mainProcess(self):
        lm1 = {
            "stype": "R",
            "tables": ("lonmf1",),
            "cols": [
                ("lm1_acno", "", 0, "Acc-Num"),
                ("lm1_name", "", 0, "Name", "Y"),
                ("lm1_addr1", "", 0, "Address Line 1")],
            "where": [("lm1_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"IRW",7,"Old Account","Old Account Number",
                "","Y",self.doOldAcc,lm1,None,("notblank",)),
            (("T",0,0,0),"O@lm1_name",0,""),
            (("T",0,1,0),"I@lm1_acno",0,"New Account","New Account Number",
                "","Y",self.doNewAcc,None,None,("notblank",)))
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        but = [("Generate",None,self.doGenerate,0,("T",0,1),("T",0,2),
            "Generate New Account Numbers Based on Names of Accounts")]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=but)

    def doOldAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("lonmf1", cols=["lm1_name"],
            where=[("lm1_cono", "=", self.opts["conum"]),
            ("lm1_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.oldacc = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doNewAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("lonmf1", where=[("lm1_cono", "=",
            self.opts["conum"]), ("lm1_acno", "=", w)], limit=1)
        if acc:
            return "Invalid Account Number, Already Exists"
        self.newacc = w

    def doGenerate(self):
        self.opts["mf"].updateStatus("")
        ok = askQuestion(self.opts["mf"].body, "ARE YOU SURE???",
            "Are You Certain This Is What You Want To Do? This "\
            "Will Automatically Generate New Account Numbers For "\
            "All Accounts Based On The Account Names!", default="no")
        if ok == "no":
            self.df.focusField("T", 0, 1)
            return
        self.df.closeProcess()
        self.autogen = "Y"
        recs = self.sql.getRec("lonmf1", where=[("lm1_cono", "=",
            self.opts["conum"])], order="lm1_name")
        col = self.sql.lonmf1_col
        if recs:
            p = ProgressBar(self.opts["mf"].body,
                typ="Generating Account Numbers", mxs=len(recs))
            for num, acc in enumerate(recs):
                p.displayProgress(num)
                self.oldacc = acc[col.index("lm1_acno")]
                name = acc[col.index("lm1_name")]
                for seq in range(1, 100):
                    self.newacc = genAccNum(name, seq)
                    if self.newacc == self.oldacc:
                        break
                    chk = self.sql.getRec("lonmf1",
                        where=[("lm1_cono", "=", self.opts["conum"]),
                        ("lm1_acno", "=", self.newacc)], limit=1)
                    if not chk:
                        break
                self.doProcess(focus=False)
            p.closeProgress()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doProcess(self, focus=True):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                for seq in range(1, 100):
                    oldnot = "%7s%02i" % (self.oldacc, seq)
                    newnot = "%7s%02i" % (self.newacc, seq)
                    whr = [
                        ("not_cono", "=", self.opts["conum"]),
                        ("not_sys", "=", "LON"),
                        (tab[1], "=", oldnot)]
                    col = [tab[1]]
                    dat = [newnot]
                    self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
            else:
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc)]
                col = [tab[2]]
                dat = [self.newacc]
                self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
        if focus:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
