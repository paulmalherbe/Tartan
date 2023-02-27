"""
SYNOPSIS
    Bowls Tab Number Change.

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

from TartanClasses import GetCtl, SplashScreen, Sql, TartanDialog
from tartanFunctions import askChoice

class bc6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.oldtab = self.opts["args"][0]
                self.newtab = self.opts["args"][1]
                self.doProcess()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("bwldrt","bdt_cono","bdt_tab","bdt_team1","bdt_team2","bdt_team3"),
            ("bwlent","bce_cono","bce_scod"),
            ("bwlflm","bfm_cono","bfm_captain"),
            ("bwlflt","bft_cono","bft_skip","bft_player"),
            ("bwlgme","bcg_cono","bcg_scod","bcg_ocod"),
            ("bwltab","btb_cono","btb_tab"))
        tabs = []
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
        self.mlint = bwlctl["ctb_mlint"]
        self.samen = bwlctl["ctb_samen"]
        if self.mlint == "Y" and self.samen == "Y":
            return
        self.mstart = bwlctl["ctb_mstart"]
        self.fstart = bwlctl["ctb_fstart"]
        self.nstart = bwlctl["ctb_nstart"]
        return True

    def mainProcess(self):
        tab = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab-No"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_tab"}
        fld = [
            (["T",0,0,0],"I@btb_tab",0,"Old Tab","Old Tab Number",
                "","Y",self.doOldTab,tab,None,("notzero",)),
            (["T",0,0,18],"ONA",30,""),
            (["T",0,1,0],"I@btb_tab",0,"New Tab","New Tab Number",
                "","Y",self.doNewTab,None,None,("notzero",))]
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        but = [("Generate",None,self.doGenerate,0,("T",0,1),("T",0,2),
            "Auto Generate New Tab Numbers Based on Names and Gender")]
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, butt=but)

    def doOldTab(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", w)], limit=1)
        if not acc:
            return "Invalid Tab Number, Does Not exist"
        self.oldtab = w
        self.gender = acc[self.sql.bwltab_col.index("btb_gender")]
        if acc[4]:
            self.df.loadEntry(frt, pag, p+1, data="%s, %s" % (acc[3],
                acc[4].split()[0]))
        else:
            self.df.loadEntry(frt, pag, p+1, data=acc[3])

    def doNewTab(self, frt, pag, r, c, p, i, w):
        if self.oldtab < self.nstart:
            if self.mstart < self.fstart:
                if self.gender == "M" and w >= self.fstart:
                    return "Invalid Male Tab Number"
                elif self.gender == "F" and w < self.fstart:
                    return "Invalid Female Tab Number"
            elif self.gender == "M" and w >= self.mstart:
                return "Invalid Male Tab Number"
            elif self.gender == "F" and w < self.mstart:
                return "Invalid Female Tab Number"
        elif w < self.nstart:
            return "Invalid Non-Member Tab Number"
        acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", w)], limit=1)
        if acc:
            return "Invalid Tab Number, Already Exists"
        self.newtab = w

    def doGenerate(self):
        self.opts["mf"].updateStatus("")
        but = (
            ("Members", "M"),
            ("Non Members", "N"),
            ("All", "A"),
            ("None", "X"))
        ok = askChoice(self.opts["mf"].body, "ARE YOU SURE???",
            "Are you Certain this is what you want To Do? This will "\
            "Automatically Generate New Tab Numbers For Selected Range "\
            "Based On Member's Names and Gender!", butt=but, default="None")
        if ok == "X":
            self.df.focusField("T", 0, 1)
            return
        self.df.closeProcess()
        splash = SplashScreen(self.opts["mf"].body,
            "Generating New Tab Numbers ... Please Wait")
        # Create temporary tables
        for ot in self.tables:
            tt = "%s_temp" % ot[0]
            self.sql.sqlRec("Create table %s as Select * from %s "\
                "where %s = %s" % (tt, ot[0], ot[1], self.opts["conum"]))
            self.sql.delRec(ot[0], where=[(ot[1], "=", self.opts["conum"])])
        mem = self.sql.sqlRec("Select * from bwltab_temp where btb_cono = %s "\
            "and btb_tab < %s order by btb_surname, btb_names" %
            (self.opts["conum"], self.nstart))
        non = self.sql.sqlRec("Select * from bwltab_temp where btb_cono = %s "\
            "and btb_tab >= %s order by btb_surname, btb_names" %
            (self.opts["conum"], self.nstart))
        mstart = self.mstart
        fstart = self.fstart
        nstart = self.nstart
        key = {}
        for tab in mem:
            otb = tab[self.sql.bwltab_col.index("btb_tab")]
            if ok in ("A", "M"):
                gdr = tab[self.sql.bwltab_col.index("btb_gender")]
                if gdr == "M":
                    new = mstart
                    mstart += 1
                else:
                    new = fstart
                    fstart += 1
                key[otb] = new
            else:
                key[otb] = otb
        for tab in non:
            otb = tab[self.sql.bwltab_col.index("btb_tab")]
            if ok in ("A", "N"):
                key[otb] = nstart
                nstart += 1
            else:
                key[otb] = otb
        for ot in self.tables:
            tt = "%s_temp" % ot[0]
            cc = getattr(self.sql, "%s_col" % ot[0])
            recs = self.sql.sqlRec("Select * from %s" % tt)
            for rec in recs:
                for k in ot[2:]:
                    c = rec[cc.index(k)]
                    if c not in key:
                        continue
                    rec[cc.index(k)] = key[c]
                self.sql.insRec(ot[0], data=rec)
            self.sql.sqlRec("Drop table %s" % tt)
        self.opts["mf"].dbm.commitDbase(ask=True)
        splash.closeSplash()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doProcess(self):
        for tab in self.tables:
            for x in range(len(tab[2:])):
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[x+2], "=", self.oldtab)]
                dat = [self.newtab]
                col = [tab[x+2]]
                self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
        if "args" not in self.opts:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
