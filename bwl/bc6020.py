"""
SYNOPSIS
    Delete Visitor's Tabs without History and Re-number Tabs with History,
    where the last time they visited exceeds the numer of months entered.

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
from TartanClasses import GetCtl, SplashScreen, Sql, TartanDialog
from tartanFunctions import getNextCode, projectDate

class bc6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()

    def setVariables(self):
        self.tables = (
            ("bwldrt","bdt_cono","bdt_tab","bdt_team1","bdt_team2","bdt_team3"),
            ("bwlent","bce_cono","bce_scod"),
            ("bwlgme","bcg_cono","bcg_scod","bcg_ocod"))
        tabs = ["bwltab"]
        for tab in self.tables:
            if tab[0] not in tabs:
                tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.nstart = bwlctl["ctb_nstart"]
        self.keys = (
            ("bwldrt", "bdt_cono", "bdt_tab"),
            ("bwldrt", "bdt_cono", "bdt_team1"),
            ("bwldrt", "bdt_cono", "bdt_team2"),
            ("bwldrt", "bdt_cono", "bdt_team3"),
            ("bwlent", "bce_cono", "bce_scod"),
            ("bwlgme", "bcg_cono", "bcg_scod"),
            ("bwlgme", "bcg_cono", "bcg_ocod"),
            ("bwltab", "btb_cono", "btb_tab"))
        t = time.localtime()
        self.sysdt = ((t[0] * 10000) + (t[1] * 100) + t[2])
        return True

    def mainProcess(self):
        tit = "Delete Visitors' Tabs"
        fld = (
            (("T",0,0,0),"IUI",2,"Months Not Played","",
                12,"N",self.doDelTyp,None,None,("notzero",),None,
                "The Cut-Off Number of Months Since Last Played."),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.opts["mf"].startLoop()

    def doDelTyp(self, frt, pag, r, c, p, i, w):
        self.delent = projectDate(self.sysdt, (0 - w), "months")

    def doEnd(self):
        self.df.closeProcess()
        splash = SplashScreen(self.opts["mf"].body,
            "Deleting Visitors' Tabs ... Please Wait")
        # Removing duplicate names
        col = ["btb_tab", "btb_surname", "btb_names"]
        whr = [
            ("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", ">=", self.nstart)]
        odr = "btb_tab"
        tabs = self.sql.getRec("bwltab", cols=col, where=whr, order=odr)
        for tab in tabs:
            chk = self.sql.getRec("bwltab", cols=col,
                where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", ">", tab[0]), ("btb_surname",
                "=", tab[1]), ("btb_names", "=", tab[2])])
            if chk:
                old = [tab[0]]
                while chk:
                    ttt = chk.pop(0)
                    if not chk:
                        new = ttt[0]
                    else:
                        old.append(ttt[0])
                for ttt in old:
                    self.sql.delRec("bwltab", where=[("btb_cono", "=",
                        self.opts["conum"]), ("btb_tab", "=", ttt)])
                    for key in self.keys:
                        if key == "bwltab":
                            continue
                        self.sql.updRec(key[0], cols=[key[2]], data=[new],
                            where=[(key[1], "=", self.opts["conum"]),
                            (key[2], "=", ttt)])
        # Removing old tabs
        jon = "Left outer join bwldrt on bdt_cono=btb_cono and bdt_tab=btb_tab"
        col = ["btb_tab", "max(bdt_date)", "btb_surname", "btb_names"]
        whr = [
            ("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", ">=", self.nstart)]
        grp = "btb_tab, btb_surname, btb_names"
        odr = "btb_tab"
        tabs = self.sql.getRec("bwltab", join=jon, cols=col, where=whr,
            group=grp, order=odr)
        dels = "Delete These Tabs\n=================\n"
        for tab in tabs:
            if tab[1] and tab[1] >= self.delent:
                continue
            found = False
            for key in self.keys:
                if key[0] in ("bwldrt", "bwltab"):
                    continue
                chk = self.sql.getRec(tables=key[0], where=[(key[1], "=",
                    self.opts["conum"]), (key[2], "=", tab[0])], limit=1)
                if chk:
                    # Got competition history
                    found = True
                    break
            if not found:
                # Delete the tab
                dels += "%s %s, %s\n" % (tab[0], tab[2], tab[3])
                self.sql.delRec("bwltab", where=[("btb_cono", "=",
                    self.opts["conum"]), ("btb_tab", "=", tab[0])])
                # Replace tab in bwldrt with 900001+ number
                nxt = getNextCode(self.sql, "bwldrt", "bdt_tab",
                    [("bdt_cono", "=", self.opts["conum"])], 900001, 999999)
                for key in self.keys:
                    if key[0] == "bwltab":
                        continue
                    self.sql.updRec(key[0], cols=[key[2]], data=[nxt],
                        where=[(key[1], "=", self.opts["conum"]),
                        (key[2], "=", tab[0])])
        # Re-numbering remaining visitor's tabs
        start = self.nstart
        tabs = self.sql.getRec("bwltab", cols=["btb_tab"],
            where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", ">=", self.nstart)], order="btb_tab")
        for tab in tabs:
            for key in self.keys:
                self.sql.updRec(key[0], cols=[key[2]], data=[start],
                    where=[(key[1], "=", self.opts["conum"]),
                    (key[2], "=", tab[0])])
            start += 1
        splash.closeSplash()
        self.opts["mf"].dbm.commitDbase(ask=True, mess=dels)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
