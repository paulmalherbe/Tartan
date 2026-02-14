"""
SYNOPSIS
    Asset's Register Key Change.

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

import time
from TartanClasses import GetCtl, Sql, TartanDialog

class ar6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.tables = (
            ("ctlnot", "not_key"),
            ("ctlvtf", "vtt_cono", "vtt_acno", "vtt_styp"),
            ("assmst", "asm_cono", "asm_group", "asm_code"),
            ("asstrn", "ast_cono", "ast_group", "ast_code"))
        tabs = ["chglog", "assgrp"]
        for tab in self.tables:
            if tab[0] not in tabs:
                tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        grp = {
            "stype": "R",
            "tables": ("assgrp",),
            "cols": (
                ("asg_group", "", 0, "Grp"),
                ("asg_desc", "", 0, "Description", "Y")),
            "where": [("asg_cono", "=", self.opts["conum"])]}
        asm = {
            "stype": "R",
            "tables": ("assmst",),
            "cols": (
                ("asm_code", "", 0, "Code"),
                ("asm_desc", "", 0, "Description", "Y")),
            "where": [("asm_cono", "=", self.opts["conum"])],
            "whera": [["T", "asm_group", 0]]}
        fld = [
            (["T",0,0,0],"I@asm_group",0,"Old Group","Old Group",
                "","Y",self.doOldGrp,grp,None,("notblank",)),
            (["T",0,0,12],"INA",7,"Code","Old Asset Code",
                "","Y",self.doOldCod,asm,None,("notblank",)),
            (["T",0,0,27],"ONA",30,""),
            (["T",0,1,0],"I@asm_group",0,"New Group","New Group",
                "","Y",self.doNewGrp,grp,None,("notblank",)),
            (["T",0,1,12],"I@asm_code",0,"Code","New Asset Code",
                "","Y",self.doNewCod,None,None,("notblank",))]
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doOldGrp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.opts["conum"]), ("asg_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Group, Does Not exist"
        self.oldgrp = w

    def doOldCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_group", "=", self.oldgrp), ("asm_code",
            "=", w)], limit=1)
        if not acc:
            return "Invalid Code, Does Not exist"
        self.oldcod = w
        self.oldnot = "%3s%s" % (self.oldgrp, w)
        self.df.loadEntry(frt, pag, p+1, data=acc[3])

    def doNewGrp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.opts["conum"]), ("asg_group", "=", w)], limit=1)
        if not acc:
            return "Invalid Group, Does Not exist"
        self.newgrp = w

    def doNewCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_group", "=", self.newgrp), ("asm_code",
            "=", w)], limit=1)
        if acc:
            return "Invalid Code, Already Exists"
        self.newcod = w
        self.newnot = "%3s%s" % (self.newgrp, w)

    def doProcess(self):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                col = [tab[1]]
                dat = [self.newnot]
                whr = [
                    ("not_cono", "=", self.opts["conum"]),
                    ("not_sys", "=", "ASS"),
                    (tab[1], "=", self.oldnot)]
            elif tab[0] == "ctlvtf":
                col = [tab[2]]
                dat = [self.newcod]
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldcod),
                    (tab[3], "=", "A")]
            else:
                col = [tab[2], tab[3]]
                dat = [self.newgrp, self.newcod]
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldgrp),
                    (tab[3], "=", self.oldcod)]
            self.sql.updRec(tab[0], cols=col, data=dat, where=whr)
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        if self.newgrp != self.oldgrp:
            self.sql.insRec("chglog", data=["assmst", "U", "%03i%-3s%-7s" % \
                (self.opts["conum"], self.oldgrp, self.oldcod), "asm_group",
                dte, self.opts["capnm"], self.oldgrp, self.newgrp])
        if self.newcod != self.oldcod:
            self.sql.insRec("chglog", data=["assmst", "U", "%03i%-3s%-7s" % \
                (self.opts["conum"], self.oldgrp, self.oldcod), "asm_code",
                dte, self.opts["capnm"], self.oldcod, self.newcod])
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
