"""
SYNOPSIS
    Debtor's Ledger Key Change.

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

class dr6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("ctlnot", "not_key"),
            ("drsdel", "del_code"),
            ("ctlvtf", "vtt_cono", "vtt_acno", "vtt_styp"),
            ("drsmst", "drm_cono", "drm_chain", "drm_acno", "drm_delivery"),
            ("drsrct", "dct_cono", "dct_chain", "dct_acno"),
            ("drstrn", "drt_cono", "drt_chain", "drt_acno"),
            ("drsage", "dra_cono", "dra_chain", "dra_acno"),
            ("genrcc", "grc_cono", "grc_achn", "grc_adrs"),
            ("slsiv1", "si1_cono", "si1_chain", "si1_acno"),
            ("strmf1", "st1_cono", "st1_chn_excl", "st1_acc_excl"),
            ("strtrn", "stt_cono", "stt_chain", "stt_acno", "stt_styp"))
        tabs = ["drschn"]
        for tab in self.tables:
            tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.chains = drsctl["ctd_chain"]
        self.autogen = "N"
        return True

    def mainProcess(self):
        chn = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": [
                ("drm_chain", "", 0, "Chn"),
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y"),
                ("drm_add1", "", 0, "Address Line 1")],
            "where": [("drm_cono", "=", self.opts["conum"])]}
        if self.chains == "Y":
            drm["whera"] = [["T", "drm_chain", 0]]
            drm["index"] = 1
        else:
            del drm["cols"][0]
        fld = [
            [["T",0,0,0],"I@drm_chain",0,"Old Chain","Old Chain Number",
                "","Y",self.doOldChn,chn,None,("efld",)],
            [["T",0,0,12],"IRW",7,"Old Account","Old Account Number",
                "","Y",self.doOldAcc,drm,None,("notblank",)],
            [["T",0,0,30],"O@drm_name",0,""],
            [["T",0,1,0],"I@drm_chain",0,"New Chain","New Chain Number",
                "","Y",self.doNewChn,chn,None,("efld",)],
            [["T",0,1,12],"I@drm_acno",0,"New Account","New Account Number",
                "","Y",self.doNewAcc,None,None,("notblank",)]]
        if self.chains == "N":
            self.oldchn = self.newchn = 0
            del fld[0]
            del fld[2]
            fld[0][0][3] = 0
            fld[1][0][3] = 18
            fld[2][0][3] = 0
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        but = [("Generate",None,self.doGenerate,0,("T",0,1),("T",0,2),
            "Generate New Account Numbers Based on Names of Accounts")]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=but)

    def doOldChn(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
                self.opts["conum"]), ("chm_chain", "=", w)], limit=1)
            if not acc:
                return "Invalid Chain Number, Does Not exist"
        self.oldchn = w

    def doOldAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_chain", "=", self.oldchn), ("drm_acno",
            "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.oldacc = w
        self.oldnot = "%03i%s" % (self.oldchn, w)
        self.olddel = acc[self.sql.drsmst_col.index("drm_delivery")]
        self.df.loadEntry(frt, pag, p+1, data=acc[3])

    def doNewChn(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
                self.opts["conum"]), ("chm_chain", "=", w)], limit=1)
        if not acc:
            return "Invalid Chain Number, Does Not exist"
        self.newchn = w

    def doNewAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_chain", "=", self.newchn), ("drm_acno",
            "=", w)], limit=1)
        if acc:
            return "Invalid Account Number, Already Exists"
        self.newacc = w
        self.newnot = "%03i%s" % (self.newchn, w)
        if self.olddel == self.oldacc:
            self.newdel = self.newacc
        else:
            self.newdel = self.olddel

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
        recs = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"])], order="drm_chain, drm_name")
        col = self.sql.drsmst_col
        if recs:
            p = ProgressBar(self.opts["mf"].body,
                typ="Generating Account Numbers", mxs=len(recs))
            for num, acc in enumerate(recs):
                p.displayProgress(num)
                self.oldchn = self.newchn = acc[col.index("drm_chain")]
                self.oldacc = acc[col.index("drm_acno")]
                if self.oldacc[:4] == "CASH":
                    continue
                # Remove invalid characters
                name = acc[col.index("drm_name")].replace(" ", "")
                name = name.replace(".", "")
                name = name.replace(",", "")
                name = name.replace(";", "")
                name = name.replace(":", "")
                name = name.replace("'", "")
                name = name.replace('"', "")
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
                    chk = self.sql.getRec("drsmst",
                        where=[("drm_cono", "=", self.opts["conum"]),
                        ("drm_chain", "=", self.newchn), ("drm_acno", "=",
                        self.newacc)])
                    if not chk:
                        break
                self.oldnot = "%03i%s" % (self.oldchn, self.oldacc)
                self.newnot = "%03i%s" % (self.newchn, self.newacc)
                self.olddel = acc[col.index("drm_delivery")]
                if self.olddel == self.oldacc:
                    self.newdel = self.newacc
                else:
                    self.newdel = self.olddel
                self.doProcess(focus=False)
            p.closeProgress()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doProcess(self, focus=True):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                whr = [
                    ("not_cono", "=", self.opts["conum"]),
                    ("not_sys", "=", "DRS"),
                    (tab[1], "=", self.oldnot)]
                dat = [self.newnot]
                col = [tab[1]]
            elif tab[0] == "drsdel":
                if self.newdel == self.olddel:
                    continue
                whr = [(tab[1], "=", self.olddel)]
                dat = [self.newdel]
                col = [tab[1]]
            elif tab[0] == "ctlvtf":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc),
                    (tab[3], "=", "D")]
                dat = [self.newacc]
                col = [tab[2]]
            elif tab[0] == "drsmst":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldchn),
                    (tab[3], "=", self.oldacc)]
                dat = [self.newchn, self.newacc, self.newdel]
                col = [tab[2], tab[3], tab[4]]
            elif tab[0] == "strtrn":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldchn),
                    (tab[3], "=", self.oldacc),
                    (tab[4], "=", "INV")]
                dat = [self.newchn, self.newacc]
                col = [tab[2], tab[3]]
            else:
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldchn),
                    (tab[3], "=", self.oldacc)]
                dat = [self.newchn, self.newacc]
                col = [tab[2], tab[3]]
            self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
        if focus:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
