"""
SYNOPSIS
    Creditor's Ledger Account Code Change.

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

from TartanClasses import GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion

class cr6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("ctlnot", "not_key"),
            ("ctlvtf", "vtt_cono", "vtt_acno", "vtt_styp"),
            ("crsmst", "crm_cono", "crm_acno"),
            ("crstrn", "crt_cono", "crt_acno"),
            ("crsage", "cra_cono", "cra_acno"),
            ("genrcc", "grc_cono", "grc_acrs"),
            ("strpom", "pom_cono", "pom_acno"),
            ("strtrn", "stt_cono", "stt_acno", "stt_styp"))
        tabs = []
        for tab in self.tables:
            tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.autogen = "N"
        return True

    def mainProcess(self):
        crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": (
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")),
            "where": [("crm_cono", "=", self.opts["conum"])]}
        fld = [
            (["T",0,0,0],"IRW",7,"Old Account","Old Account Number",
                "","Y",self.doOldAcc,crm,None,("notblank",)),
            (["T",0,0,18],"O@crm_name",0,""),
            (["T",0,1,0],"I@crm_acno",0,"New Account","New Account Number",
                "","Y",self.doNewAcc,None,None,("notblank",))]
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        but = [("Generate",None,self.doGenerate,0,("T",0,1),("T",0,2),
            "Auto Generate New Account Numbers Based on Names of Accounts")]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=but)

    def doOldAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", where=[("crm_cono", "=",
            self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.oldacc = w
        self.oldnot = w
        self.df.loadEntry(frt, pag, p+1, data=acc[2])

    def doNewAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("crsmst", where=[("crm_cono", "=",
            self.opts["conum"]), ("crm_acno", "=", w)], limit=1)
        if acc:
            return "Invalid Account Number, Already Exists"
        self.newacc = w
        self.newnot = w

    def doGenerate(self):
        self.opts["mf"].updateStatus("")
        ok = askQuestion(self.opts["mf"].body, "ARE YOU SURE???",
            "Are You Certain This Is What You Want To Do? This Will "\
            "Automatically Generate New Account Numbers For All Accounts "\
            "Based On The Account Names!", default="no")
        if ok == "no":
            self.df.focusField("T", 0, 1)
            return
        self.df.closeProcess()
        self.autogen = "Y"
        recs = self.sql.getRec("crsmst", where=[("crm_cono", "=",
            self.opts["conum"])], order="crm_name")
        if recs:
            p = ProgressBar(self.opts["mf"].body,
                typ="Generating Account Numbers", mxs=len(recs))
            for num, acc in enumerate(recs):
                p.displayProgress(num)
                self.oldacc = acc[1]
                name = acc[2].replace(" ", "")
                name = name.replace(".", "")
                name = name.replace(",", "")
                name = name.replace(";", "")
                name = name.replace(":", "")
                name = name.replace("'", "")
                name = name.replace('"', "")
                # Remove other invalid characters
                if len(name) < 5:
                    name = name + ("0" * (5 - len(name)))
                acno = ""
                for c in range(0, 5):
                    acno = (acno + name[c]).upper()
                acno = acno.strip()
                text = "%s%0" + str((7 - len(acno))) + "d"
                for x in range(1, 100):
                    self.newacc = text % (acno, x)
                    if self.newacc == self.oldacc:
                        break
                    chk = self.sql.getRec("crsmst", where=[("crm_cono",
                        "=", self.opts["conum"]), ("crm_acno", "=",
                        self.newacc)])
                    if not chk:
                        break
                self.oldnot = self.oldacc
                self.newnot = self.newacc
                self.doProcess(focus=False)
            p.closeProgress()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doProcess(self, focus=True):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                whr = [
                    ("not_cono", "=", self.opts["conum"]),
                    ("not_sys", "=", "CRS"),
                    (tab[1], "=", self.oldnot)]
                dat = [self.newnot]
                col = [tab[1]]
            elif tab[0] == "ctlvtf":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc),
                    (tab[3], "=", "D")]
                dat = [self.newacc]
                col = [tab[2]]
            elif tab[0] == "strtrn":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc),
                    (tab[3], "=", "STR")]
                dat = [self.newacc]
                col = [tab[2]]
            else:
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc)]
                dat = [self.newacc]
                col = [tab[2]]
            self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
        if focus:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
