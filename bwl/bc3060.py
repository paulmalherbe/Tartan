"""
SYNOPSIS
    Bowls League Assessment Summary.

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

class bc3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlflf", "bwlflm", "bwlflt",
            "bwlfls", "bwltab"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
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
            "where": [
                ("bfm_cono", "=", self.opts["conum"]),
                ("bfm_round", "=", 1)],
            "whera": [("T", "bfm_fmat", 0, 0)],
            "group": "bfm_date"}
        r1s = (("Fixture", "F"), ("Practice", "P"))
        fld = (
            (("T",0,0,0),"I@bfm_fmat",0,"","",
                "","N",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "F","N",self.doType,dte,None,None),
            (("T",0,2,0),"I@bfm_date",0,"First Round Date","",
                "","N",self.doDate,dte,None,("efld",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

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
        acc = self.sql.getRec("bwlflm", cols=["bfm_date"],
            where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
            self.fmat), ("bfm_type", "=", self.ftyp), ("bfm_round", "=",
            1)], order="bfm_date")
        if acc:
            self.df.loadEntry(frt, pag, p+2, data=acc[-1][0])

    def doDate(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflm", where=[("bfm_cono", "=",
            self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_type",
            "=", self.ftyp), ("bfm_date", "=", w), ("bfm_round", "=", 1)],
            limit=1)
        if not acc:
            return "Invalid 1st Round Date"
        self.sdate = w
        self.ddisp = self.df.t_disp[0][0][3]
        acc = self.sql.getRec("bwlflm", cols=["bfm_date"],
            where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
            self.fmat), ("bfm_type", "=", self.ftyp), ("bfm_date", ">",
            self.sdate), ("bfm_round", "=", 1)], limit=1)
        if not acc:
            self.edate = 99999999
        else:
            self.edate = acc[0]
        self.rounds = self.sql.getRec("bwlflm", cols=["bfm_round",
            "bfm_date"], where=[("bfm_cono", "=", self.opts["conum"]),
            ("bfm_fmat", "=", self.fmat), ("bfm_type", "=", self.ftyp),
            ("bfm_date", ">=", self.sdate, "and", "bfm_date", "<",
            self.edate)], group="bfm_round, bfm_date", order="bfm_round")

    def doEnd(self):
        self.df.closeProcess()
        data = []
        dat = self.sql.getRec(tables=["bwlflt", "bwltab"], cols=["bft_player",
            "btb_surname", "btb_names"], where=[("bft_cono", "=",
            self.opts["conum"]), ("bft_fmat", "=", self.fmat), ("bft_type",
            "=", self.ftyp), ("bft_date", ">=", self.sdate, "and", "bft_date",
            "<", self.edate), ("btb_cono=bft_cono",), ("btb_tab=bft_player",)],
            group="bft_player, btb_surname, btb_names",
            order="btb_surname, btb_names")
        for plr in dat:
            values = [self.getName(plr[1], plr[2])]
            if self.forms == 1:
                values = values + [0] * 10
            else:
                values = values + [0] * 12
            his = 0
            tot = 0
            cnt = 0
            for rnd in self.rounds:
                pl = self.sql.getRec(tables=["bwlfls", "bwlflt"],
                    cols=["bft_position", "bft_rating1", "bft_rating2",
                    "bft_rating3", "bft_rating4", "bft_skip"],
                    where=[("bfs_cono", "=", self.opts["conum"]), ("bfs_fmat",
                    "=", self.fmat), ("bfs_league", "=", "M"), ("bft_type",
                    "=", self.ftyp), ("bft_date", "=", rnd[1]), ("bft_player",
                    "=", plr[0]), ("bft_cono=bfs_cono",),
                    ("bft_fmat=bfs_fmat",), ("bft_team=bfs_code",)], limit=1)
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
                    where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat",
                    "=", self.fmat), ("bft_date", "=", rnd[1]), ("bft_skip",
                    "=", pl[5])])
                tmp = 0
                for tm in team:
                    tmp += tm[pl[0]]
                    tot += tm[pl[0]]
                if rnd[0]:
                    if his:
                        div = 4.0
                    else:
                        div = 3.0
                    avg = round(tmp / div, 1)
                    values[rnd[0]] = avg
            if not tot:
                # No assessments
                continue
            if his:
                div = 4.0
            else:
                div = 3.0
            values[10] = round(tot / div / cnt, 1)
            if self.forms == 4:
                values[11] = round(his / cnt)
                values[12] = round((tot - his) / 3.0 / cnt, 1)
            data.append(values)
        head = ("Assessments Summary for %s Season Commencing on the %s" % \
            (self.fnam, self.ddisp),)
        if self.forms == 1:
            cols = [["a", "NA",  40, "Player", "y"]]
        else:
            cols = [["a", "NA",  30, "Player", "y"]]
        cols.extend([
            ["b", "UD", 4.1, "R1",     "y"],
            ["c", "UD", 4.1, "R2",     "y"],
            ["d", "UD", 4.1, "R3",     "y"],
            ["e", "UD", 4.1, "R4",     "y"],
            ["f", "UD", 4.1, "R5",     "y"],
            ["g", "UD", 4.1, "R6",     "y"],
            ["h", "UD", 4.1, "R7",     "y"],
            ["i", "UD", 4.1, "R8",     "y"],
            ["j", "UD", 4.1, "R9",     "y"],
            ["k", "UD", 4.1, "AV",     "y"]])
        if self.forms == 4:
            cols.extend([
                ["l", "UD", 4.1, "HA",     "y"],
                ["m", "UD", 4.1, "NA",     "y"]])
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=head, cols=cols, ttype="D", blank=True,
            repprt=self.df.repprt, repeml=self.df.repeml, fromad=self.fromad)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def getName(self, snam, fnam):
        if fnam:
            return "%s, %s" % (snam.upper(), fnam.split()[0][0].upper())
        else:
            return snam.upper()

# vim:set ts=4 sw=4 sts=4 expandtab:
