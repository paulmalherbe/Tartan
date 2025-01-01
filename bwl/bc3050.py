"""
SYNOPSIS
    Bowls League Match Assessment Report.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import dateDiff, showError, textFormat

class bc3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlflf", "bwlflm", "bwlfls",
            "bwlflt", "bwltab"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
        self.pos = ["", "Skip", " 3rd", " 2nd", "Lead"]
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
            "tables": ("bwlflm",),
            "cols": (("bfm_date", "", 0, "Match-Date"),),
            "where": [("bfm_cono", "=", self.opts["conum"])],
            "whera": [
                ("T", "bfm_fmat", 0, 0),
                ("T", "bfm_type", 2, 0)],
            "group": "bfm_date"}
        r1s = (("Fixture", "F"), ("Practice", "P"))
        fld = (
            (("T",0,0,0),"I@bfm_fmat",0,"","",
                "","N",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "F","N",self.doType,fmt,None,None),
            (("T",0,2,0),"I@bfm_date",0,"","",
                "","N",self.doDate,dte,None,("efld",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","Y"))

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Format"
        if acc[self.sql.bwlflf_col.index("bff_assess")] == "N":
            return "Assessment Forms Disabled"
        self.fmat = w
        self.fnam = acc[self.sql.bwlflf_col.index("bff_desc")]
        self.forms = acc[self.sql.bwlflf_col.index("bff_forms")]
        self.df.loadEntry(frt, pag, p+1, data=self.fnam)

    def doType(self, frt, pag, r, c, p, i, w):
        self.ftyp = w

    def doDate(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflm", where=[("bfm_cono", "=",
            self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_type",
            "=", self.ftyp), ("bfm_date", "=", w)], limit=1)
        if not acc:
            return "Invalid Match Date"
        self.date = w
        self.disp = self.df.t_disp[0][0][3]

    def doEnd(self):
        self.df.closeProcess()
        data = []
        recs = self.sql.getRec(tables=["bwlflt", "bwlfls"], cols=["bft_skip",
            "bft_player", "bft_position", "bft_shotsf", "bft_shotsa",
            "bft_points", "bft_rating1", "bft_rating2", "bft_rating3",
            "bft_rating4", "bft_remarks"], where=[("bft_cono", "=",
            self.opts["conum"]), ("bft_fmat", "=", self.fmat), ("bft_type",
            "=", self.ftyp),
            ("bft_date", "=", self.date), ("bfs_cono=bft_cono",),
            ("bfs_fmat=bft_fmat",), ("bfs_league", "=", "M"),
            ("bfs_code=bft_team",)], order="bfs_code, bft_skip, bft_position")
        for player in recs:
            pos = player[2]
            his = player[5 + pos]
            if pos == 1:
                names = self.sql.getRec(tables=["bwlflt", "bwltab"],
                    cols=["btb_surname", "btb_names"], where=[("bft_cono",
                    "=", self.opts["conum"]), ("bft_fmat", "=", self.fmat),
                    ("bft_type", "=", self.ftyp), ("bft_date", "=", self.date),
                    ("bft_skip", "=", player[0]), ("btb_cono=bft_cono",),
                    ("btb_tab=bft_player",)], order="bft_position")
                for nm in names:
                    nm[0] = self.getName(nm[0], nm.pop(1))
            sc = self.sql.getRec("bwlflt", cols=["bft_rating%s" % pos],
                where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
                self.fmat), ("bft_type", "=", self.ftyp), ('bft_date', '=',
                self.date), ("bft_skip", "=", player[0])])
            tot = sc[0][0] + sc[1][0] + sc[2][0] + sc[3][0]
            tav = self.getHistory(player[1])
            if tav == "error":
                break
            if not tav:
                tav = tot
            if self.forms == 1:
                if player[1] == player[0]:
                    desc = textFormat(player[10], width=70)
                if desc:
                    text = desc.pop(0)
                else:
                    text = ""
                data.append([names[player[2]-1][0], self.pos[pos], player[3],
                    player[4], player[5], sc[0][0], tav, text])
            else:
                if his:
                    div = 4.0
                else:
                    div = 3.0
                data.append([names[player[2]-1][0], self.pos[pos], player[3],
                    player[4], player[5], sc[0][0], sc[1][0], sc[2][0],
                    sc[3][0], round(tot / div, 1), his,
                    round((tot - his) / 3.0, 1), tav, player[10]])
            if pos == 4:
                data.append(["BLANK"])
        if tav != "error":
            head = ("Match Assessment for %s Match Played on %s" % \
                (self.fnam, self.disp),)
            cols = [
                ["a", "NA",  20, "Player",  "y"],
                ["b", "NA",   4, "Posn",    "y"],
                ["c", "UI",   3, "For",     "y"],
                ["d", "UI",   3, "Agt",     "y"],
                ["e", "UI",   1, "P",       "y"]]
            if self.forms == 1:
                cols.append(["f", "UD", 4.1, " Ass",    "y"])
            elif self.forms == 4:
                cols.extend([
                    ["f", "UD", 4.1, " Skp",    "y"],
                    ["g", "UD", 4.1, " 3rd",    "y"],
                    ["h", "UD", 4.1, " 2nd",    "y"],
                    ["i", "UD", 4.1, "Lead",    "y"],
                    ["j", "UD", 4.1, " Avg",    "y"],
                    ["k", "UD", 4.1, " Own",    "y"],
                    ["l", "UD", 4.1, " Adj",    "y"]])
            cols.extend([
                ["m", "UD", 4.1, " ATD",    "y"],
                ["n", "NA",  70, "Remarks", "y"]])
            RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
                heads=head, cols=cols, ttype="D", repprt=self.df.repprt,
                repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def getHistory(self, player):
        sdate = 0
        acc = self.sql.getRec("bwlflm", cols=["bfm_date"],
            where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
            self.fmat), ("bfm_type", "=", self.ftyp), ("bfm_round", "=", 1)],
            order="bfm_date")
        for a in acc:
            if dateDiff(a[0], self.date, ptype="months") < 4:
                sdate = a[0]
                break
        if not sdate:
            showError(self.opts["mf"].body, "ERROR",
                "No Start Date of 1st Round")
            return "error"
        rounds = self.sql.getRec("bwlflm", cols=["bfm_round",
            "bfm_date"], where=[("bfm_cono", "=", self.opts["conum"]),
            ("bfm_fmat", "=", self.fmat), ("bfm_type", "=", self.ftyp),
            ("bfm_date", ">=", sdate, "and", "bfm_date", "<=", self.date)],
            group="bfm_round, bfm_date", order="bfm_round")
        cnt = 0
        his = 0
        tot = 0
        for rnd in rounds:
            pl = self.sql.getRec(tables=["bwlfls", "bwlflt"],
                cols=["bft_position", "bft_rating1", "bft_rating2",
                "bft_rating3", "bft_rating4", "bft_skip"],
                where=[("bfs_cono", "=", self.opts["conum"]), ("bfs_fmat", "=",
                self.fmat), ("bft_type", "=", self.ftyp), ("bfs_league",
                "=", "M"), ("bft_date", "=", rnd[1]), ("bft_player", "=",
                player), ("bft_fmat=bfs_fmat",), ("bft_team=bfs_code",)],
                limit=1)
            if not pl:
                # Did not play
                continue
            if not pl[1] and not pl[2] and not pl[3] and not pl[4]:
                # Not yet assessed
                continue
            cnt += 1.0
            his += pl[pl[0]]
            team = self.sql.getRec("bwlflt", cols=["bft_player",
                "bft_rating1","bft_rating2","bft_rating3","bft_rating4"],
                where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
                self.fmat), ("bft_type", "=", self.ftyp), ("bft_date", "=",
                rnd[1]), ("bft_skip", "=", pl[5])])
            for tm in team:
                tot += tm[pl[0]]
        if tot:
            return round((tot - his) / 3.0 / cnt, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def getName(self, snam, fnam):
        if fnam:
            return "%s, %s" % (snam.upper(), fnam.split()[0][0].upper())
        else:
            return snam.upper()

# vim:set ts=4 sw=4 sts=4 expandtab:
