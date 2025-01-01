"""
SYNOPSIS
    Stores Ledger - Capturing Selling Prices

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

from TartanClasses import FileImport, GetCtl, Sql, TartanDialog
from tartanFunctions import showError

class st1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strmf1", "strmf2",
            "strloc", "strprc"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        return True

    def drawDialog(self):
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        st1 = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_code", "", 0, "Product-Code"),
                ("st1_type", "", 0, "T"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "<>", "X")],
            "whera": [("C", "st1_group", 0)]}
        loc = {
            "stype": "R",
            "tables": ("strmf2", "strloc"),
            "cols": (
                ("st2_loc", "", 0, "Acc-Num"),
                ("srl_desc", "", 0, "Description")),
            "where": [
                ("st2_cono", "=", self.opts["conum"])],
            "whera": (
                ("C", "st2_group", 0),
                ("C", "st2_code", 1))}
        self.fld = [
            (("C",0,0,0),"IUA",3,"Grp","Product Group",
                "","Y",self.doGrp,grp,None,None),
            (("C",0,0,1),"INA",20,"Code","Product Code",
                "","N",self.doCode,st1,None,None),
            (("C",0,0,2),"ONA",30,"Description"),
            (("C",0,0,3),"IUA",1,"L","Location",
                "","N",self.doLoc,loc,None,None)]
        for x in range(self.plevs):
            lev = x + 1
            txt = "Level-%s" % lev
            if lev == 1:
                ddd = self.doDelete
            else:
                ddd = None
            self.fld.append((("C",0,0,x+4),"IUD",10.2,txt,txt,
                "","N",self.doLevel,None,ddd,("notzero",)))
        but = (
            ("Import File",None,self.doImport,0,("C",0,1),("C",0,2),
                "Import Selling Prices from a CSV or XLS File "\
                "having the following columns: Group, Code, "\
                "Location, Prices by Level"),
            ("Exit", None, self.doExit, 1, ("C", 0, 1), ("C", 0, 2)))
        row = (20,)
        self.df = TartanDialog(self.opts["mf"], rows=row,
            eflds=self.fld, cend=((self.doEnd,"y"),), cxit=(self.doExit,),
            butt=but)

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        impcol = []
        pos = 0
        for num, fld in enumerate(self.fld):
            if num == 2:
                continue
            if type(fld[2]) in (tuple, list):
                size = fld[2][1]
            else:
                size = fld[2]
            impcol.append([fld[4], pos, fld[1][1:], size])
            pos += 1
        fi = FileImport(self.opts["mf"], impcol=impcol)
        err = None
        for num, line in enumerate(fi.impdat):
            if len(line) != pos:
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, pos, len(line))
                break
            self.grp = line[0]
            chk = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
                self.opts["conum"]), ("gpm_group", "=", self.grp)], limit=1)
            if not chk:
                err = "Line %s: Invalid Group %s" % ((num + 1), self.grp)
                break
            self.cod = line[1]
            chk = self.sql.getRec("strmf1", where=[("st1_cono", "=",
                self.opts["conum"]), ("st1_group", "=", self.grp),
                ("st1_code", "=", self.cod)], limit=1)
            if not chk:
                err = "Line %s: Invalid Code %s" % ((num + 1), self.cod)
                break
            self.loc = line[2]
            chk = self.sql.getRec("strmf2", where=[("st2_cono", "=",
                self.opts["conum"]), ("st2_group", "=", self.grp),
                ("st2_code", "=", self.cod), ("st2_loc", "=", self.loc)],
                limit=1)
            if not chk:
                err = "Line %s: Invalid Location %s" % ((num + 1), self.loc)
                break
            self.levs = []
            for x in range(self.plevs):
                self.levs.append(line[x + 3])
            if len(self.levs) != self.plevs:
                err = "Line %s: Invalid Number of Levels (S/B %s is %s)" % \
                    ((num + 1), self.plevs, len(self.levs))
            self.doEnd(det=True)
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        elif fi.impdat:
            self.opts["mf"].dbm.commitDbase()
        self.df.enableButtonsTags(state=state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, 1)

    def doGrp(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", w)], limit=1)
        if not chk:
            return "Invalid Group"
        self.grp = w

    def doCode(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("strmf1", cols=["st1_desc"],
            where=[("st1_cono", "=", self.opts["conum"]), ("st1_group",
            "=", self.grp), ("st1_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Code"
        self.cod = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        if self.locs == "N":
            self.loc = "1"
            self.df.loadEntry(frt, pag, p+2, data=self.loc)
            self.doLoadLevs(p + 3)
            return "sk2"

    def doLoc(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("strmf2", where=[("st2_cono", "=",
            self.opts["conum"]), ("st2_group", "=", self.grp),
            ("st2_code", "=", self.cod), ("st2_loc", "=", w)],
            limit=1)
        if not chk:
            return "Invalid Location"
        self.loc = w
        self.doLoadLevs(p + 1)

    def doDelete(self):
        self.sql.delRec("strprc", where=[("stp_cono", "=", self.opts["conum"]),
            ("stp_group", "=", self.grp), ("stp_code", "=", self.cod),
            ("stp_loc", "=", self.loc)])
        self.opts["mf"].dbm.commitDbase()
        self.df.clearLine(0, focus=True)

    def doLoadLevs(self, p):
        self.levs = []
        for x in range(self.plevs):
            prc = self.sql.getRec("strprc", cols=["stp_price"],
                where=[("stp_cono", "=", self.opts["conum"]), ("stp_group",
                "=", self.grp), ("stp_code", "=", self.cod), ("stp_loc",
                "=", self.loc), ("stp_level", "=", x + 1)], limit=1)
            if not prc:
                prc = [0]
            self.df.loadEntry("C", 0, p, data=prc[0])
            self.levs.append(prc[0])
            p += 1

    def doLevel(self, frt, pag, r, c, p, i, w):
        self.levs[i - 4] = w

    def doEnd(self, det=False):
        self.sql.delRec("strprc", where=[("stp_cono", "=",
            self.opts["conum"]), ("stp_group", "=", self.grp),
            ("stp_code", "=", self.cod), ("stp_loc", "=", self.loc)])
        for num, lev in enumerate(self.levs):
            self.sql.insRec("strprc", data=[self.opts["conum"], self.grp,
                self.cod, self.loc, num + 1, lev])
        self.opts["mf"].dbm.commitDbase()
        self.df.advanceLine(0)
        self.df.loadEntry("C", 0, self.df.pos, data=self.grp)
        self.df.focusField("C", 0, self.df.col + 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
