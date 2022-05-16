"""
SYNOPSIS
    Bowls League Results and Assessments.

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

from TartanClasses import TartanDialog, Sql

class bc2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwltab", "bwlflf", "bwlflm",
            "bwlflt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.skip = 0
        return True

    def mainProcess(self):
        fmt = {
            "stype": "R",
            "tables": ("bwlflf",),
            "cols": (
                ("bff_code", "", 0, "Cod"),
                ("bff_desc", "", 0, "Description", "Y")),
            "where": [("bff_cono", "=", self.opts["conum"])]}
        dte = {
            "stype": "R",
            "tables": ("bwlflt",),
            "cols": (("bft_date", "", 0, "Match-Date"),),
            "where": [("bft_cono", "=", self.opts["conum"])],
            "whera": [
                ("T", "bft_fmat", 0, 0),
                ("T", "bft_type", 4, 0)],
            "group": "bft_date",
            "order": "bft_date"}
        skp = {
            "stype": "R",
            "tables": ("bwlflt", "bwlfls", "bwltab"),
            "cols": (
                ("bft_skip", "", 0, "Skp"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names"),
                ("bft_shotsf", "", 0, "For"),
                ("bft_shotsa", "", 0, "Agt")),
            "where": [
                ("bfs_cono", "=", self.opts["conum"]),
                ("bfs_league", "=", "M"),
                ("bfs_code=bft_team",),
                ("btb_tab=bft_skip",)],
            "whera": [
                ("T", "bft_fmat", 0, 0),
                ("T", "bft_type", 4, 0),
                ("T", "bft_date", 5, 0)],
            "group": "bft_skip",
            "order": "btb_surname, btb_names"}
        plr = {
            "stype": "R",
            "tables": ("bwlflt", "bwltab"),
            "cols": (
                ("bft_player", "", 0, "Plr"),
                ("bft_position", "", 0, "P"),
                ("btb_surname", "", 0, "Name", "Y"),
                ("btb_names", "", 0, "Name")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_cono=bft_cono",),
                ("btb_tab=bft_player",)],
            "whera": [
                ["T", "bft_fmat", 0, 0],
                ["T", "bft_type", 4, 0],
                ["T", "bft_date", 5, 0],
                ["C", "bft_skip", 0, 0]],
            "group": "bft_player",
            "order": "bft_position"}
        r1s = (("Fixture", "F"), ("Practice", "P"))
        fld = (
            (("T",0,0,0),"I@bft_fmat",0,"","",
                0,"N",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"OUI",1,"Number of Forms"),
            (("T",0,2,0),"OUA",1,"Assess Self"),
            (("T",0,3,0),("IRB",r1s),0,"Type","",
                "F","N",self.doType,None,None,None),
            (("T",0,4,0),"I@bft_date",0,"","",
                "","N",self.doDate,dte,None,("efld",)),
            (("C",0,0,0),"I@bft_skip",0,"","",
                "r","N",self.doSkip,skp,None,None),
            (("C",0,0,1),"ONA",20,""),
            (("C",0,0,2),"I@bft_player",0,"","",
                "","N",self.doPlayer,plr,None,None),
            (("C",0,0,3),"ONA",20,""),
            (("C",0,0,4),"I@bft_shotsf",0,"","",
                "","N",self.doShotsf,None,None,None),
            (("C",0,0,5),"I@bft_shotsa",0,"","",
                "","N",self.doShotsa,None,None,None),
            (("C",0,0,6),"I@bft_points",0,"","",
                "","N",self.doPoints,None,None,None),
            (("C",0,0,7),"I@bft_rating1",0,"","",
                "","N",self.doRate1,None,None,None),
            (("C",0,0,8),"I@bft_rating2",0,"","",
                "","N",self.doRate2,None,None,None),
            (("C",0,0,9),"I@bft_rating3",0,"","",
                "","N",self.doRate3,None,None,None),
            (("C",0,0,10),"I@bft_rating4",0,"","",
                "","N",self.doRate4,None,None,None),
            (("C",0,0,11),"I@bft_remarks",20,"","",
                "","N",self.doRemarks,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"n"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Format"
        if acc[self.sql.bwlflf_col.index("bff_assess")] == "N":
            return "Assessment Forms Disabled"
        self.fmat = w
        desc = acc[self.sql.bwlflf_col.index("bff_desc")]
        self.forms = acc[self.sql.bwlflf_col.index("bff_forms")]
        self.self = acc[self.sql.bwlflf_col.index("bff_self")]
        self.df.loadEntry(frt, pag, p+1, data=desc)
        self.df.loadEntry(frt, pag, p+2, data=self.forms)
        self.df.loadEntry(frt, pag, p+3, data=self.self)

    def doType(self, frt, pag, r, c, p, i, w):
        self.ftyp = w

    def doDate(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflm", where=[("bfm_cono", "=",
            self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_type",
            "=", self.ftyp), ("bfm_date", "=", w)], limit=1)
        if not acc:
            return "Invalid Date"
        self.date = w

    def doSkip(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["bwlflt", "bwltab"], cols=["btb_surname",
            "btb_names", "bft_shotsf", "bft_shotsa", "bft_rating1",
            "bft_rating2", "bft_rating3", "bft_rating4", "bft_remarks"],
            where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
            self.fmat), ("bft_type", "=", self.ftyp), ("bft_date", "=",
            self.date),
            ("bft_skip", "=", w), ("btb_cono=bft_cono",),
            ("btb_tab=bft_skip",)], limit=1)
        if not acc:
            return "Invalid Skip"
        acc[0] = self.getName(acc[0], acc.pop(1))
        if w == self.skip:
            self.repeat = True
        else:
            self.repeat = False
            self.skip = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if self.forms == 1:
            for x in range(1, 8):
                self.df.loadEntry(frt, pag, p+x+3, data=acc[x])
            return "sk3"

    def doPlayer(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["bwlflt", "bwltab"], cols=["btb_surname",
            "btb_names", "bft_position", "bft_shotsf", "bft_shotsa",
            "bft_points","bft_rating1", "bft_rating2", "bft_rating3",
            "bft_rating4", "bft_remarks"], where=[("bft_cono", "=",
            self.opts["conum"]), ("bft_fmat", "=", self.fmat), ("bft_type",
            "=", self.ftyp), ("bft_date", "=", self.date), ("bft_skip", "=",
            self.skip), ("bft_player", "=", w), ("btb_tab=bft_player",)],
            limit=1)
        if not acc:
            return "This Player Did Not Play for this Skip on this Date"
        acc[0] = self.getName(acc[0], acc.pop(1))
        self.player = w
        self.position = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        if self.repeat:
            self.df.loadEntry(frt, pag, p+2, data=self.shotsf)
            self.df.loadEntry(frt, pag, p+3, data=self.shotsa)
            self.df.loadEntry(frt, pag, p+4, data=self.points)
        else:
            self.df.loadEntry(frt, pag, p+2, data=acc[2])
            self.df.loadEntry(frt, pag, p+3, data=acc[3])
            self.df.loadEntry(frt, pag, p+4, data=acc[4])
        for x in range(5, 10):
            self.df.loadEntry(frt, pag, p+x, data=acc[x])
        if self.repeat:
            if self.forms == 4 and self.self == "N" and self.position == 1:
                self.rate1 = 0
                self.df.loadEntry(frt, pag, p+5, data=self.rate1)
                return "sk5"
            else:
                return "sk4"

    def doShotsf(self, frt, pag, r, c, p, i, w):
        self.shotsf = w

    def doShotsa(self, frt, pag, r, c, p, i, w):
        self.shotsa = w

    def doPoints(self, frt, pag, r, c, p, i, w):
        self.points = w
        if self.forms == 4 and self.self == "N" and self.position == 1:
            self.rate1 = 0
            self.df.loadEntry(frt, pag, p+1, data=self.rate1)
            return "sk1"

    def doRate1(self, frt, pag, r, c, p, i, w):
        self.rate1 = w
        if self.forms == 4 and self.self == "N" and self.position == 2:
            self.rate2 = 0
            self.df.loadEntry(frt, pag, p+1, data=self.rate2)
            return "sk1"

    def doRate2(self, frt, pag, r, c, p, i, w):
        self.rate2 = w
        if self.forms == 4 and self.self == "N" and self.position == 3:
            self.rate3 = 0
            self.df.loadEntry(frt, pag, p+1, data=self.rate3)
            return "sk1"

    def doRate3(self, frt, pag, r, c, p, i, w):
        self.rate3 = w
        if self.forms == 4 and self.self == "N" and self.position == 4:
            self.rate4 = 0
            self.df.loadEntry(frt, pag, p+1, data=self.rate4)
            return "sk1"

    def doRate4(self, frt, pag, r, c, p, i, w):
        self.rate4 = w

    def doRemarks(self, frt, pag, r, c, p, i, w):
        self.remarks = w

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
            return
        col = ["bft_shotsf", "bft_shotsa", "bft_points"]
        dat = [self.shotsf, self.shotsa, self.points]
        self.sql.updRec("bwlflt", cols=col, data=dat, where=[("bft_fmat", "=",
            self.fmat), ("bft_date", "=", self.date), ("bft_skip", "=",
            self.skip)])
        col = ["bft_rating1", "bft_rating2", "bft_rating3", "bft_rating4",
            "bft_remarks"]
        dat = [self.rate1, self.rate2, self.rate3, self.rate4, self.remarks]
        if self.forms == 1:
            for x in range(1, 5):
                self.sql.updRec("bwlflt", cols=col, data=dat,
                    where=[("bft_fmat", "=", self.fmat), ("bft_date", "=",
                    self.date), ("bft_skip", "=", self.skip), ("bft_position",
                    "=", x)])
                dat[4] = ""
        else:
            self.sql.updRec("bwlflt", cols=col, data=dat, where=[("bft_fmat",
                "=", self.fmat), ("bft_date", "=", self.date), ("bft_skip",
                "=", self.skip), ("bft_player", "=", self.player)])
        self.df.advanceLine(0)

    def doExit(self):
        if self.df.frt == "C":
            self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def getName(self, snam, fnam):
        if fnam:
            for i in fnam.split():
                snam = "%s %s" % (snam, i[0])
        return snam.upper()

# vim:set ts=4 sw=4 sts=4 expandtab:
