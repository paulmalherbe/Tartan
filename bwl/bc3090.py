"""
SYNOPSIS
    Bowls Competition Draw Summary Sheet.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2021 Paul Malherbe.

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

class bc3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.getCompDetails(self.opts["args"][0])
                self.excfin = self.opts["args"][1]
                self.doEnd()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwlgme", "bwltab",
            "bwltyp", "bwlent"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
        return True

    def mainProcess(self):
        bcp = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"))}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","N",self.doCmpCod,bcp,None,None),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Exclude Final Clash","",
                "Y","N",self.doExcFin,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","Y"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        ret = self.getCompDetails(w)
        if ret:
            return ret
        self.df.loadEntry(frt, pag, p+1, data=self.cdes)
        if self.cfmat == "R":
            self.excfin = "N"
            self.df.loadEntry(frt, pag, p+2, data=self.excfin)
            return "sk2"

    def getCompDetails(self, w):
        chk = self.sql.getRec("bwlcmp", where=[("bcm_cono", "=",
            self.opts["conum"]), ("bcm_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.cdes = chk[self.sql.bwlcmp_col.index("bcm_name")]
        ctyp = chk[self.sql.bwlcmp_col.index("bcm_type")]
        bwltyp = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", ctyp)], limit=1)
        self.cfmat = bwltyp[self.sql.bwltyp_col.index("bct_cfmat")]
        if self.cfmat in ("D", "K"):
            return "Knockout Competitions has No Summary"
        if self.cfmat == "R":
            games = self.sql.getRec("bwlgme", cols=["count(*)"],
                where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", 1)],
                group="bcg_group")
            self.games = 0
            for gme in games:
                if gme[0] > self.games:
                    self.games = gme[0]
            self.games -= 1
        else:
            self.games = bwltyp[self.sql.bwltyp_col.index("bct_games")]
        self.grgame = bwltyp[self.sql.bwltyp_col.index("bct_grgame")]

    def doExcFin(self, frt, pag, r, c, p, i, w):
        self.excfin = w

    def doEnd(self):
        if "args" not in self.opts:
            self.df.closeProcess()
        lst = self.sql.getRec("bwlgme", cols=["bcg_game",
            "sum(bcg_points)"], where=[("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod)], group="bcg_game", order="bcg_game")
        lgame = 0
        for l in lst:
            if l[1]:
                lgame = l[0]
        col = ["bce_scod", "btb_surname", "btb_names"]
        if lgame <= self.grgame:
            col.extend([
                "sum(bcg_sfor) as sfor",
                "sum(bcg_sagt) as sagt",
                "sum(bcg_sfor - bcg_sagt) as agg",
                "sum(bcg_points) as pts"])
        else:
            col.extend([
                "sum(bcg_a_sfor) as sfor",
                "sum(bcg_a_sagt) as sagt",
                "sum(bcg_a_sfor - bcg_a_sagt) as agg",
                "sum(bcg_a_points) as pts"])
        whr = [
            ("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod),
            ("btb_cono=bce_cono",),
            ("btb_tab=bce_scod",),
            ("bcg_cono=bce_cono",),
            ("bcg_ccod=bce_ccod",),
            ("bcg_scod=bce_scod",)]
        grp = "bce_scod, btb_surname, btb_names, bcg_group"
        odr = "bcg_group, pts desc, agg desc, sagt asc, btb_surname"
        skips = self.sql.getRec(tables=["bwlent", "bwltab", "bwlgme"],
            cols=col, where=whr, group=grp, order=odr)
        rinks = self.sql.getRec("bwlgme", cols=["bcg_rink"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
            "=", self.ccod)], group="bcg_rink", order="bcg_rink")
        endrk = []
        for rnk in rinks:
            if rnk[0] and rnk[0][1] == "7":
                endrk.remove("%s6" % rnk[0][0])
            elif rnk[0] and rnk[0][1] in ("1", "6"):
                endrk.append(rnk[0])
        data = []
        for skip in skips:
            nam = skip[1].strip()
            if skip[2]:
                nam = "%s, %s" % (nam, skip[2].split()[0])
            dat = [skip[0], nam]
            ops = []
            rks = []
            eds = 0
            dup = ["-", "-"]
            games = self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_scod",
                "=", skip[0])], order="bcg_group, bcg_game")
            for game in games:
                grp = game[self.sql.bwlgme_col.index("bcg_group")]
                opp = game[self.sql.bwlgme_col.index("bcg_ocod")]
                if opp > 900000:
                    opp = 0
                    rnk = ""
                else:
                    rnk = game[self.sql.bwlgme_col.index("bcg_rink")]
                    if self.excfin == "Y" and game == games[-1]:
                        pass
                    elif rnk and rnk in endrk:
                        eds += 1
                dat.extend([opp, rnk])
                if opp:
                    if self.excfin == "Y" and game == games[-1]:
                        pass
                    elif opp in ops:
                        dup[0] = "X"
                    ops.append(opp)
                if rnk:
                    if self.excfin == "Y" and game == games[-1]:
                        pass
                    elif rnk in rks:
                        dup[1] = "X"
                    rks.append(rnk)
            dup.append("%s" % eds)
            if grp:
                dat.insert(2, chr(64 + grp))
            else:
                dat.insert(2, "")
            dat.append("%1s%1s%1s" % tuple(dup))
            data.append(dat)
        head = [
            ("%s - %s" % (self.opts["conam"], self.cdes), 18, "C"),
            ("Draw Summary Sheet", 16, "C")]
        cols = [
            ["a", "UI",  6, "Skp",  "y"],
            ["b", "NA", 29, "Name", "y"]]
        if self.cfmat == "R":
            cols.append(["c", "UA",  1, "S",    "y"])
        else:
            cols.append(["c", "UA",  1, "G",    "y"])
        for x in range(self.games):
            cols.extend([
                ["d%s" % x, "UI", 6, "Opp", "y"],
                ["e%s" % x, "UA", 2, "Rk",  "y"]])
        cols.append(["f", "UA",  3, "ORE",  "y"])
        if "args" in self.opts:
            repprt = self.opts["args"][2]
            repeml = self.opts["args"][3]
        else:
            repprt = self.df.repprt
            repeml = self.df.repprt
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=head, cols=cols, ttype="D", pages=False, repprt=repprt,
            repeml=repeml, fromad=self.fromad)
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
