"""
SYNOPSIS
    Stores's Ledger Key Change.

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

from TartanClasses import FileImport, GetCtl, ProgressBar, Sql, TartanDialog

class st6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("ctlnot", "not_key"),
            ("slsiv2", "si2_cono", "si2_group", "si2_code"),
            ("slsiv3", "si3_cono", "si3_rgroup", "si3_rcode"),
            ("strmf1", "st1_cono", "st1_group", "st1_code"),
            ("strmf2", "st2_cono", "st2_group", "st2_code"),
            ("strpot", "pot_cono", "pot_group", "pot_code"),
            ("strprc", "stp_cono", "stp_group", "stp_code"),
            ("strrcp", "srr_cono", "srr_group", "srr_code"),
            ("strrcp", "srr_cono", "srr_rgroup", "srr_rcode"),
            ("strtrn", "stt_cono", "stt_group", "stt_code"),
            ("strvar", "stv_cono", "stv_group", "stv_code"))
        tabs = ["strgrp"]
        for tab in self.tables:
            if not tabs.count(tab[0]):
                tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        return True

    def mainProcess(self):
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        stm = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_code", "", 0, "Product-Code"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [("st1_cono", "=", self.opts["conum"])],
            "whera": [["T", "st1_group", 0]]}
        r1s = (("Yes", "Y"), ("No", "N"))
        self.fld = [
            (["T",0,0,0],"IUA",3,"Old Group","Old Group",
                "","Y",self.doGroup,grp,None,("notblank",)),
            (["T",0,0,31],"ONA",30,""),
            (["T",0,1,0],"IUA",3,"New Group","New Group",
                "","Y",self.doGroup,grp,None,("notblank",)),
            (["T",0,1,31],"ONA",30,""),
            (["T",0,2,0],("IRB",r1s),0,"All Codes","All Codes",
                "N","Y",self.doAllCod,None,None,None),
            (["T",0,3,0],"IRW",20,"Old Code","Old Product Code",
                "","Y",self.doOldCod,stm,None,("notblank",)),
            (["T",0,3,0],"ONA",30,""),
            (["T",0,4,0],"INA",20,"New Code","New Product Code",
                "","Y",self.doNewCod,None,None,("notblank",))]
        but = (
            ("Import File",None,self.doImport,0,("T",0,1),("T",0,2),
            "Import a CSV or XLS File with the Correct Format i.e. "\
            "Old Group, New Group, Old Code, New Code. If the New Code "\
            "is left Blank the Old Code will be Retained."),)
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doImport(self):
        self.df.closeProcess()
        impcol = []
        pos = 0
        for num, fld in enumerate(self.fld):
            if num in (1, 3, 4, 6):
                continue
            if type(fld[2]) in (tuple, list):
                size = fld[2][1]
            else:
                size = fld[2]
            impcol.append([fld[4], pos, fld[1][1:], size])
            pos += 1
        fi = FileImport(self.opts["mf"], impcol=impcol)
        if fi.impdat:
            p = ProgressBar(self.opts["mf"].body, typ="Importing Changes",
                mxs=len(fi.impdat))
            for num, line in enumerate(fi.impdat):
                p.displayProgress(num)
                self.oldgrp, self.newgrp, self.oldcod = line[:3]
                if line[3]:
                    self.newcod = line[3]
                else:
                    self.newcod = self.oldcod
                self.oldnot = "%3s%s" % (self.oldgrp, self.oldcod)
                self.newnot = "%3s%s" % (self.newgrp, self.newcod)
                self.doChange()
            p.closeProgress()
            self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doGroup(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Group, Does Not exist"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if c == 1:
            self.oldgrp = w
        else:
            self.newgrp = w
            if self.newgrp == self.oldgrp:
                self.allcod = "N"
                self.df.loadEntry(frt, pag, p+2, data=self.allcod)
                return "sk2"

    def doAllCod(self, frt, pag, r, c, p, i, w):
        self.allcod = w
        if self.allcod == "Y":
            recs = self.sql.getRec("strmf1", where=[("st1_cono", "=",
                self.opts["conum"]), ("st1_group", "=", self.oldgrp)])
            err = None
            for acc in recs:
                cod = acc[self.sql.strmf1_col.index("st1_code")]
                chk = self.sql.getRec("strmf1", where=[("st1_cono", "=",
                    self.opts["conum"]), ("st1_group", "=", self.newgrp),
                    ("st1_code", "=", cod)], limit=1)
                if chk:
                    err = "Group: %s Code: %s - Already Exists" % (self.newgrp,
                        acc[self.sql.strmf1_col.index("st1_code")])
                    break
            if err:
                return "%s, Cannot Do All" % err
            return "sk3"

    def doOldCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.oldgrp),
            ("st1_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Code, Does Not exist"
        self.oldcod = w
        self.oldnot = "%3s%s" % (self.oldgrp, w)
        desc = acc[self.sql.strmf1_col.index("st1_desc")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doNewCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strmf1", where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", "=", self.newgrp),
            ("st1_code", "=", w)], limit=1)
        if acc:
            return "Invalid Code, Already Exists"
        self.newcod = w
        self.newnot = "%3s%s" % (self.newgrp, w)

    def doProcess(self):
        if self.allcod == "Y":
            recs = self.sql.getRec("strmf1", cols=["st1_code"],
                where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
                "=", self.oldgrp)])
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs),
                typ="Changing All Records for Group %s" % self.oldgrp)
            for num, acc in enumerate(recs):
                p.displayProgress(num)
                self.oldcod = acc[0]
                self.newcod = acc[0]
                self.oldnot = "%3s%s" % (self.oldgrp, acc[0])
                self.newnot = "%3s%s" % (self.newgrp, acc[0])
                self.doChange()
            p.closeProgress()
            self.sql.delRec("strgrp", where=[("gpm_cono", "=",
                self.opts["conum"]), ("gpm_group", "=", self.oldgrp)])
        else:
            self.doChange()
        self.df.focusField("T", 0, 1)

    def doChange(self):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                whr = [
                    ("not_cono", "=", self.opts["conum"]),
                    ("not_sys", "=", "STR"),
                    (tab[1], "=", self.oldnot)]
                dat = [self.newnot]
                col = [tab[1]]
            else:
                whr = [(tab[2], "=", self.oldgrp), (tab[3], "=", self.oldcod)]
                dat = [self.newgrp, self.newcod]
                col = [tab[2], tab[3]]
            self.sql.updRec(tab[0], where=whr, data=dat, cols=col)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
