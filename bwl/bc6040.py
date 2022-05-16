"""
SYNOPSIS
    Bowls Clear History Dialog.

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
from TartanClasses import TartanDialog, Sql

class bc6040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwldrm", "bwldrt",
            "bwlent", "bwlgme", "bwlrnd", "bwltyp", "bwlpts", "bwlfls",
            "bwlflm", "bwlflt", "bwlflo"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.today = ((t[0] * 10000) + (t[1] * 100) + t[2])
        return True

    def mainProcess(self):
        r1s = (("Yes", "Y"), ("No", "N"))
        r2s = (("No", "N"), ("All", "A"), ("Unplayed", "U"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Tabs-Inn","",
                "N","Y",self.doTabs,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"League","",
                "N","N",self.doLeague,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Competition Entries","",
                "N","N",self.doComps,None,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Competition Types","",
                "N","N",self.doTypes,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doTabs(self, frt, pag, r, c, p, i, w):
        self.tabs = w

    def doLeague(self, frt, pag, r, c, p, i, w):
        self.league = w

    def doComps(self, frt, pag, r, c, p, i, w):
        self.comps = w

    def doTypes(self, frt, pag, r, c, p, i, w):
        self.types = w

    def doEnd(self):
        self.df.closeProcess()
        if self.tabs == "Y":
            self.sql.delRec("bwldrm", where=[("bdm_cono", "=",
                self.opts["conum"])])
            self.sql.delRec("bwldrt", where=[("bdt_cono", "=",
                self.opts["conum"])])
        if self.league == "Y":
            self.sql.delRec("bwlfls", where=[("bfs_cono", "=",
                self.opts["conum"])])
            self.sql.delRec("bwlflm", where=[("bfm_cono", "=",
                self.opts["conum"])])
            self.sql.delRec("bwlflt", where=[("bft_cono", "=",
                self.opts["conum"])])
            self.sql.delRec("bwlflo", where=[("bfo_cono", "=",
                self.opts["conum"])])
        delc = []
        delt = []
        if self.comps in ("A", "U"):
            tabs = [
                ("bwlcmp", "bcm_cono", "bcm_code"),
                ("bwlcmp", "bcm_cono", "bcm_poff"),
                ("bwlent", "bce_cono", "bce_ccod"),
                ("bwlgme", "bcg_cono", "bcg_ccod"),
                ("bwlrnd", "bcr_cono", "bcr_ccod")]
            whr = [("bcm_cono", "=", self.opts["conum"])]
            if self.comps == "U":
                whr.append(("bcm_date", "<=", self.today))
            comps = self.sql.getRec("bwlcmp", cols=["bcm_code"],
                where=whr, order="bcm_code")
            if self.comps == "A":
                for comp in comps:
                    delc.append(comp[0])
            elif self.comps == "U":
                col = ["sum(bcg_sfor)", "sum(bcg_sagt)",
                    "sum(bcg_points)"]
                for comp in comps:
                    chk = self.sql.getRec("bwlgme", cols=col,
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", comp[0])], limit=1)
                    if not chk:
                        delc.append(comp[0])
                        continue
                    if not chk[0] and not chk[1] and not chk[2]:
                        delc.append(comp[0])
            if delc:
                for tab in tabs:
                    whr = [(tab[1], "=", self.opts["conum"])]
                    if self.comps == "U":
                        whr.append((tab[2], "in", delc))
                    self.sql.delRec(tab[0], where=whr)
            if self.comps == "U":
                # Renumber competitions
                comps = self.sql.getRec("bwlcmp", where=[("bcm_cono",
                    "=", self.opts["conum"])], order="bcm_code")
                self.sql.delRec("bwlcmp", where=[("bcm_cono", "=",
                    self.opts["conum"])])
                for num, dat in enumerate(comps):
                    ccod = num + 1
                    nrec = dat[:]
                    nrec[1] = ccod
                    self.sql.insRec("bwlcmp", data=nrec)
                    for tab in tabs[1:]:
                        self.sql.updRec(tab[0], cols=[tab[2]], data=[ccod],
                            where=[(tab[1], "=", self.opts["conum"]),
                            (tab[2], "=", dat[1])])
        if self.types == "Y":
            typs = self.sql.getRec("bwltyp", cols=["bct_code"],
                where=[("bct_cono", "=", self.opts["conum"])])
            for typ in typs:
                cnt = self.sql.getRec("bwlcmp", cols=["count(*)"],
                    where=[("bcm_cono", "=", self.opts["conum"]),
                    ("bcm_type", "=", typ[0])], limit=1)
                if not cnt[0]:
                    delt.append(typ[0])
                    self.sql.delRec("bwltyp", where=[("bct_cono",
                        "=", self.opts["conum"]), ("bct_code",
                        "=", typ[0])])
                    self.sql.delRec("bwlpts", where=[("bcp_cono",
                        "=", self.opts["conum"]), ("bcp_code",
                        "=", typ[0])])
            # Renumber types
            types = self.sql.getRec("bwltyp", where=[("bct_cono",
                "=", self.opts["conum"])], order="bct_code")
            self.sql.delRec("bwltyp", where=[("bct_cono", "=",
                self.opts["conum"])])
            for num, dat in enumerate(types):
                ctyp = num + 1
                nrec = dat[:]
                nrec[1] = ctyp
                self.sql.insRec("bwltyp", data=nrec)
                self.sql.updRec("bwlpts", cols=["bcp_code"],
                    data=[ctyp], where=[("bcp_cono", "=",
                    self.opts["conum"]), ("bcp_code", "=", dat[1])])
                self.sql.updRec("bwlcmp", cols=["bcm_type"],
                    data=[ctyp], where=[("bcm_cono", "=",
                    self.opts["conum"]), ("bcm_type", "=", dat[1])])
        if self.types == "Y" and delt:
            mess = "Delete (%s) Types" % len(delt)
        else:
            mess = ""
        if self.comps in ("A", "U") and delc:
            mess = "%s\nDelete (%s) Competitions" % (mess, len(delc))
        if delt or delc:
            self.opts["mf"].dbm.commitDbase(ask=True, mess=mess)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
