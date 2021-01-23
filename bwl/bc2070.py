"""
SYNOPSIS
    Bowls Competition Capture Match Results.

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

from TartanClasses import ASD, TartanDialog, Sql
from tartanFunctions import askChoice, askQuestion, copyList, showError

class bc2070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwltab", "bwlent",
            "bwltyp", "bwlpts", "bwlgme"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        bcp = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        gme = {
            "stype": "R",
            "tables": ("bwlgme",),
            "cols": (
                ("bcg_game", "", 0, "GC"),
                ("bcg_type", "", 0, "T"),
                ("bcg_date", "", 0, "Date")),
            "where": [("bcg_cono", "=", self.opts["conum"])],
            "whera": [("T", "bcg_ccod", 0, 0)],
            "group": "bcg_game"}
        skp = {
            "stype": "R",
            "tables": ("bwlent", "bwltab", "bwlgme"),
            "cols": (
                ("btb_tab", "", 0, "Cod"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names"),
                ("bcg_rink", "", 0, "RK")),
            "where": [
                ("bce_cono", "=", self.opts["conum"]),
                ("btb_cono=bce_cono",),
                ("btb_tab=bce_scod",),
                ("bcg_cono=bce_cono",),
                ("bcg_scod=bce_scod",),
                ("bcg_sfor=0 and bcg_sagt=0",)],
            "whera": [
                ("T", "bce_ccod", 0, 0),
                ("T", "bcg_ccod", 0, 0),
                ("T", "bcg_game", 2, 0)],
            "order": "bcg_rink"}
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","Y",self.doCmpCod,bcp,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,0,0),"I@bcg_game",0,"Game Number","",
                "","N",self.doGamCod,gme,None,("efld",)),
            (("T",0,0,0),"IUI",2,"Ends Completed","",
                0,"N",self.doEndsFin,None,None,("efld",)),
            (("C",0,0,0),"I@bcg_scod",0,"","",
                "","N",self.doSkpCod,skp,None,("efld",)),
            (("C",0,0,0),"ONA",30,"Skp-Name"),
            (("C",0,0,0),"I@bcg_sfor",0,"","",
                "","N",self.doShots,None,None,("efld",)),
            (("C",0,0,0),"I@bcg_points",0,"","",
                "","N",self.doPoints,None,None,("efld",)),
            (("C",0,0,0),"O@bcg_ocod",0,""),
            (("C",0,0,0),"ONA",30,"Opp-Name"),
            (("C",0,0,0),"I@bcg_sagt",0,"","",
                "","N",self.doShots,None,None,("efld",)),
            (("C",0,0,0),"I@bcg_points",0,"","",
                "","N",self.doPoints,None,None,("efld",)))
        but = (("Quit",None,self.doQuit,1,None,None),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"y"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            rows=(19,), eflds=fld, butt=but, tend=tnd, txit=txt,
            cend=cnd, cxit=cxt)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        com = self.sql.getRec("bwlcmp", cols=["bcm_name", "bcm_type"],
            where=[("bcm_cono", "=", self.opts["conum"]), ("bcm_code", "=",
            w)], limit=1)
        if not com:
            return "Invalid Competition Code"
        self.ccod = w
        self.code = com[1]
        self.df.loadEntry(frt, pag, p + 1, data=com[0])
        bwltyp = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", com[1])], limit=1)
        self.cfmat = bwltyp[self.sql.bwltyp_col.index("bct_cfmat")]
        self.groups = bwltyp[self.sql.bwltyp_col.index("bct_groups")]
        self.grgame = bwltyp[self.sql.bwltyp_col.index("bct_grgame")]
        if self.cfmat == "R":
            self.games = self.sql.getRec("bwlent", cols=["count(*)"],
                where=[("bce_cono", "=", self.opts["conum"]), ("bce_ccod", "=",
                self.ccod)], limit=1)[0] - 1
        elif self.cfmat in ("D", "K"):
            totskp = self.sql.getRec("bwlent", cols=["count(*)"],
                where=[("bce_cono", "=", self.opts["conum"]),
                ("bce_ccod", "=", self.ccod)], limit=1)[0]
            pwrs = 2
            self.games = 1
            while pwrs < totskp:
                self.games += 1
                pwrs = pwrs * 2
        else:
            self.games = bwltyp[self.sql.bwltyp_col.index("bct_games")]
        self.ends = bwltyp[self.sql.bwltyp_col.index("bct_ends")]
        chk = self.sql.getRec("bwlgme", cols=["bcg_game",
            "sum(bcg_sfor)", "sum(bcg_sagt)", "sum(bcg_points)"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            self.ccod), ("bcg_aflag", "in", ("", "D"))],
            group="bcg_game", order="bcg_game")
        for game in chk:
            self.gcod = game[0]
            if not game[1] and not game[2] and not game[3]:
                self.df.loadEntry(frt, pag, p + 2, data=self.gcod)
                break
        self.df.loadEntry(frt, pag, p + 3, data=self.ends)

    def doGamCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlgme", cols=["bcg_aflag",
            "sum(bcg_ocod)"], where=[("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", w)],
            group="bcg_aflag")
        if not chk:
            return "Invalid Game Number"
        for ck in chk:
            if not ck[0] and not ck[1]:
                return "Invalid Game Number, Not Yet Drawn"
        if w != self.games:
            col = [
                "bcg_game",
                "bcg_type",
                "sum(bcg_ocod)",
                "sum(bcg_sfor)",
                "sum(bcg_points)"]
            whr = [
                ("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod),
                ("bcg_game", ">", w)]
            drwn = self.sql.getRec("bwlgme", cols=col, where=whr,
                group="bcg_game, bcg_type", order="bcg_game")
            drawn = []
            for n, d in enumerate(drwn):
                if d[1] == "S" and d[2]:
                    if d[3] or d[4]:
                        drawn = "X"
                        break
                    drawn.append(d[0])
            if drawn == "X":
                showError(self.opts["mf"].body, "Error",
                    "Results Have Already Been Captured for Game %s" % d[0])
                return "Completed SvS Game %s" % d[0]
            elif drawn:
                if len(drawn) == 1:
                    text = "Game %s" % drawn[0]
                    plural = "Draw"
                    word = "Has"
                else:
                    text = "Games"
                    for d in drawn:
                        text += " %s" % d
                    plural = "Draws"
                    word = "Have"
                ok = askQuestion(self.opts["mf"].body, head="Draw Done",
                    mess="""Strength v Strength %s %s Been Drawn.

Do You Want to Delete the %s and Alter This Game's Results?

You Will Then Have to Re-Print Reports and Re-Draw %s.

If You Continue and Have Not Made a Backup You Will Not be Able to Restore.

Do You Still Want to Continue?""" % (text, word, plural, text), default="no")
                if ok == "no":
                    return "rf"
                col = ["bcg_date", "bcg_ocod", "bcg_rink"]
                dat = [0, 0, ""]
                if self.groups == "Y" and w == self.grgame:
                    col.append("bcg_group")
                    dat.append(0)
                col.extend(["bcg_sfor", "bcg_sagt", "bcg_points",
                    "bcg_a_sfor", "bcg_a_sagt", "bcg_a_points",
                    "bcg_aflag"])
                dat.extend([0, 0, 0, 0, 0, 0, ""])
                whr = [
                    ("bcg_cono", "=", self.opts["conum"]),
                    ("bcg_ccod", "=", self.ccod),
                    ("bcg_game", "in", tuple(drawn))]
                self.sql.updRec("bwlgme", cols=col, data=dat, where=whr)
                self.opts["mf"].dbm.commitDbase()
        elif chk[0] in ("A", "S"):
            return "Invalid Game Number, Abandoned or Skipped"
        self.gcod = w
        gtyp = self.sql.getRec("bwlgme", cols=["bcg_type"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
            "=", self.ccod), ("bcg_game", "=", w)], limit=1)[0]
        bwlpts = self.sql.getRec("bwlpts", where=[("bcp_cono",
            "=", self.opts["conum"]), ("bcp_code", "=", self.code),
            ("bcp_ptyp", "=", gtyp)], limit=1)
        self.skins = bwlpts[self.sql.bwlpts_col.index("bcp_skins")]
        self.sends = bwlpts[self.sql.bwlpts_col.index("bcp_sends")]
        self.ponly = bwlpts[self.sql.bwlpts_col.index("bcp_p_only")]
        self.epts = bwlpts[self.sql.bwlpts_col.index("bcp_e_points")]
        self.spts = bwlpts[self.sql.bwlpts_col.index("bcp_s_points")]
        self.gpts = bwlpts[self.sql.bwlpts_col.index("bcp_g_points")]
        self.bpts = bwlpts[self.sql.bwlpts_col.index("bcp_bonus")]
        dif = bwlpts[self.sql.bwlpts_col.index("bcp_win_by")]
        self.win_by = [dif, dif * -1]
        dif = bwlpts[self.sql.bwlpts_col.index("bcp_lose_by")]
        self.lose_by = [dif, dif * -1]

    def doEndsFin(self, frt, pag, r, c, p, i, w):
        self.bonus = self.bpts
        if w != self.ends:
            if not w:
                but = (("Exit",1),("Skipped",2),("Abandoned",3))
                ok = askChoice(self.opts["mf"].body, head="Zero Ends",
                    mess="No Ends Completed, Choose Option", butt=but)
                if ok == 1:
                    return "rf"
                elif ok == 2:
                    self.sql.updRec("bwlgme", cols=["bcg_aflag"], data=["S"],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_game", "=",
                        self.gcod)])
                elif ok == 3:
                    self.sql.updRec("bwlgme", cols=["bcg_ocod", "bcg_rink",
                        "bcg_sfor", "bcg_sagt", "bcg_points",
                        "bcg_a_sfor", "bcg_a_sagt", "bcg_a_points",
                        "bcg_aflag"], data=[0, "", 0, 0, 0, 0, 0, 0, "A"],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_game", "=",
                        self.gcod)])
                self.opts["mf"].dbm.commitDbase()
                return "xt"
            ok = askQuestion(self.opts["mf"].body, head="Shortened",
                mess="Was This Game Shortened?", default="no")
            if ok == "no":
                return "rf"
            if self.bonus == "Y":
                ok = askQuestion(self.opts["mf"].body, head="Bonus Points",
                    mess="Must Bonus Points Still be Awarded?", default="no")
                if ok == "no":
                    self.bonus = "N"
        self.totpts = (w * self.epts) + self.gpts
        if self.skins == "Y":
            self.totpts = self.totpts + (int(w / self.sends) * self.spts)
        if self.bonus == "Y":
            self.maxpts = float(ASD(self.totpts) + ASD(1))
        else:
            self.maxpts = self.totpts

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec(tables=["bwlgme", "bwltab"], cols=["btb_surname",
            "btb_names", "bcg_ocod", "bcg_sfor", "bcg_sagt",
            "bcg_points"], where=[("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", w), ("bcg_game",
            "=", self.gcod), ("btb_tab=bcg_scod",)], limit=1)
        if not chk:
            return "Invalid Skip Code"
        if chk[3] or chk[4] or chk[5]:
            ok = askQuestion(self.opts["mf"].body, head="Already Entered",
                mess="""This Card Has Already Been Entered, Re-Enter?

            Shots For:        %s
            Shots Against:    %s
            Points:            %s""" % (chk[3], chk[4], chk[5]),
                default="no")
            if ok == "no":
                return "rf"
            self.reenter = True
        else:
            self.reenter = False
        self.skp = w
        self.opp = chk[2]
        if self.opp > 900000:
            return "This Skip Had a Bye"
        if chk[1]:
            name = "%s, %s" % tuple(chk[:2])
        else:
            name = chk[0]
        self.df.loadEntry(frt, pag, p + 1, data=name)
        if self.ponly == "N":
            self.df.loadEntry(frt, pag, p + 2, data=chk[3])
        self.df.loadEntry(frt, pag, p + 3, data=chk[5])
        self.df.loadEntry(frt, pag, p + 4, data=self.opp)
        if self.cfmat in ("D", "K"):
            opp = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", self.opp)], limit=1)
            chk = opp + [chk[4], chk[3], 0]
        else:
            chk = self.sql.getRec(tables=["bwlgme", "bwltab"],
                cols=["btb_surname", "btb_names", "bcg_sfor",
                "bcg_sagt", "bcg_points"], where=[("bcg_cono",
                "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_scod", "=", self.opp), ("bcg_game", "=", self.gcod),
                ("btb_tab=bcg_scod",)], limit=1)
        if chk[1]:
            name = "%s, %s" % tuple(chk[:2])
        else:
            name = chk[0]
        self.df.loadEntry(frt, pag, p + 5, data=name)
        if self.ponly == "N":
            self.df.loadEntry(frt, pag, p + 6, data=chk[2])
        self.df.loadEntry(frt, pag, p + 7, data=chk[4])
        if self.ponly == "Y":
            self.mpts = self.totpts
            return "sk2"

    def doShots(self, frt, pag, r, c, p, i, w):
        if i == 2:
            self.s_for = w
            if self.cfmat in ("D", "K"):
                self.p_for = 0
                self.df.loadEntry(frt, pag, p + 1, data=0)
                return "sk1"
            if not self.s_for or (not self.totpts and self.bonus != "Y"):
                self.p_for = w
                self.df.loadEntry(frt, pag, p + 1, data=0)
                return "sk1"
        else:
            self.s_agt = w
            if self.cfmat in ("D", "K"):
                self.p_agt = 0
                self.df.loadEntry(frt, pag, p + 1, data=0)
                return "sk1"
            if not self.s_agt or (not self.totpts and self.bonus != "Y"):
                self.p_agt = w
                self.df.loadEntry(frt, pag, p + 1, data=0)
                return "sk1"
            self.mpts = self.totpts
            if self.bonus == "N":
                return
            diff = float(ASD(self.s_for) - ASD(self.s_agt))
            if not diff:
                return
            if diff > self.win_by[0] or diff < self.win_by[1]:
                self.mpts = float(ASD(self.mpts) + ASD(1))
            elif diff < self.lose_by[0] and diff > self.lose_by[1]:
                self.mpts = float(ASD(self.mpts) + ASD(1))

    def doPoints(self, frt, pag, r, c, p, i, w):
        if w and w % 1 not in (0.0, 0.5):
            return "Invalid Decimal in Points"
        if w > self.maxpts:
            return "Invalid Points, Exceed Maximum"
        if i == 3:
            self.p_for = w
            self.df.loadEntry(frt, pag, p + 1, data=self.opp)
            chk = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", self.opp)], limit=1)
            if chk[1]:
                name = "%s, %s" % tuple(chk[:2])
            else:
                name = chk[0]
            self.df.loadEntry(frt, pag, p + 2, data=name)
            if self.ponly == "Y":
                self.s_for = w
                return "sk3"
            else:
                return "sk2"
        if not w:
            self.p_agt = float(ASD(self.mpts) - ASD(self.p_for))
            self.df.loadEntry(frt, pag, p, data=self.p_agt)
        else:
            self.p_agt = w
        if self.ponly == "Y":
            self.s_agt = self.p_agt
        tot = float(ASD(self.p_for) + ASD(self.p_agt))
        if tot != self.mpts:
            return "Invalid Total Points (%s s/b %s)" % (tot, self.mpts)

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
            self.doLoadCards()
        else:
            if self.ponly == "Y" and not self.p_for and not self.p_agt:
                aflag = "S"
            elif self.ponly == "N" and not self.s_for and not self.s_agt:
                aflag = "S"
            else:
                aflag = ""
            col = [
                "bcg_sfor", "bcg_sagt", "bcg_points",
                "bcg_a_sfor", "bcg_a_sagt", "bcg_a_points",
                "bcg_aflag"]
            whr = [
                ("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", self.gcod)]
            w = whr[:]
            w.append(("bcg_scod", "=", self.skp))
            self.sql.updRec("bwlgme", cols=col, data=[self.s_for, self.s_agt,
                self.p_for, self.s_for, self.s_agt, self.p_for, aflag],
                where=w)
            if self.cfmat not in ("D", "K"):
                w = whr[:]
                w.append(("bcg_scod", "=", self.opp))
                self.sql.updRec("bwlgme", cols=col, data=[self.s_agt,
                    self.s_for, self.p_agt, self.s_agt, self.s_for,
                    self.p_agt, aflag], where=w)
            self.opts["mf"].dbm.commitDbase()
            if self.reenter:
                self.doLoadCards()
            else:
                self.df.advanceLine(0)

    def doLoadCards(self):
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod),
            ("bcg_game", "=", self.gcod)]
        if self.ponly == "Y":
            whr.append(("bcg_points", ">", 0))
        else:
            whr.append(("(", "bcg_sfor", ">", 0, "or",
                "bcg_sagt", ">", 0, ")"))
        recs = self.sql.getRec("bwlgme", cols=["bcg_scod", "bcg_ocod"],
            where=whr, order="bcg_scod")
        if not recs:
            return
        self.df.clearFrame("C", 0)
        self.df.focusField("C", 0, 1)
        skips = []
        seq = 0
        for rec in recs:
            if rec[0] in skips:
                continue
            skips.extend(rec)
            col = [
                "btb_surname", "btb_names",
                "bcg_sfor", "bcg_sagt", "bcg_points"]
            skp = self.sql.getRec(tables=["bwlgme", "bwltab"],
                cols=col, where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", rec[0]),
                ("bcg_game", "=", self.gcod), ("btb_tab=bcg_scod",)], limit=1)
            idx = seq * 8
            self.df.loadEntry("C", 0, idx, data=rec[0])
            if skp[1]:
                name = "%s, %s" % tuple(skp[:2])
            else:
                name = skp[0]
            self.df.loadEntry("C", 0, idx + 1, data=name)
            self.df.loadEntry("C", 0, idx + 2, data=skp[2])
            self.df.loadEntry("C", 0, idx + 3, data=skp[4])
            if self.cfmat in ("D", "K"):
                tab = self.sql.getRec("bwltab", cols=col[:2],
                    where=[("btb_cono", "=", self.opts["conum"]),
                    ("btb_tab", "=", rec[1])], limit=1)
                opp = tab + [skp[3], skp[4], 0]
            else:
                opp = self.sql.getRec(tables=["bwlgme", "bwltab"],
                    cols=col, where=[("bcg_cono", "=", self.opts["conum"]),
                    ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", rec[1]),
                    ("bcg_game", "=", self.gcod), ("btb_tab=bcg_scod",)],
                    limit=1)
            self.df.loadEntry("C", 0, idx + 4, data=rec[1])
            if opp[1]:
                name = "%s, %s" % tuple(opp[:2])
            else:
                name = opp[0]
            self.df.loadEntry("C", 0, idx + 5, data=name)
            self.df.loadEntry("C", 0, idx + 6, data=opp[2])
            self.df.loadEntry("C", 0, idx + 7, data=opp[4])
            self.df.advanceLine(0)
            if seq < 17:
                seq += 1

    def doExit(self):
        if self.df.frt == "C" and self.df.col != 1:
            chk = self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_game",
                "=", self.gcod), ("bcg_aflag", "in", ("", "D"))])
            for c in chk:
                scod = c[self.sql.bwlgme_col.index("bcg_scod")]
                ocod = c[self.sql.bwlgme_col.index("bcg_ocod")]
                if scod > 900000 or ocod > 900000:
                    continue
                if self.ponly == "Y":
                    fors = c[self.sql.bwlgme_col.index("bcg_points")]
                    agts = self.sql.getRec("bwlgme",
                        cols=["bcg_points"], where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_game", "=", self.gcod), ("bcg_scod",
                        "=", ocod)], limit=1)[0]
                else:
                    fors = c[self.sql.bwlgme_col.index("bcg_sfor")]
                    agts = c[self.sql.bwlgme_col.index("bcg_sagt")]
                if not fors and not agts:
                    self.df.focusField(self.df.frt, self.df.pag, self.df.col,
                        err="Missing Score Card for Skips %s and %s" % (scod,
                        ocod))
                    return
            if self.cfmat in ("D", "K") and self.gcod != self.games:
                # Delete Next Round's Records
                whr = [
                    ("bcg_cono", "=", self.opts["conum"]),
                    ("bcg_ccod", "=", self.ccod)]
                w = whr[:]
                w.append(("bcg_game", ">", self.gcod))
                self.sql.delRec("bwlgme", where=w)
                # Create Next Round's Records
                whr.append(("bcg_game", "=", self.gcod))
                odr = "bcg_group, bcg_pair, bcg_scod"
                g = self.sql.bwlgme_col
                for grp in range(1, 3):
                    w = whr[:]
                    w.append(("bcg_group", "=", grp))
                    recs = self.sql.getRec("bwlgme", where=w, order=odr)
                    for num in range(0, len(recs), 2):
                        pair = int(num / 2) + 1
                        rec1 = copyList(recs[num])
                        if len(recs) == 1:
                            w = whr[:]
                            w.append(("bcg_group", "=", 2))
                            rec2 = self.sql.getRec("bwlgme", where=w,
                                order=odr, limit=1)
                            grp = 2
                        else:
                            rec2 = copyList(recs[num + 1])
                        skp1 = rec1[g.index("bcg_scod")]
                        opp1 = rec1[g.index("bcg_ocod")]
                        for1 = rec1[g.index("bcg_sfor")]
                        agt1 = rec1[g.index("bcg_sagt")]
                        skp2 = rec2[g.index("bcg_scod")]
                        opp2 = rec2[g.index("bcg_ocod")]
                        for2 = rec2[g.index("bcg_sfor")]
                        agt2 = rec2[g.index("bcg_sagt")]
                        if opp1 > 900000:
                            pl1 = skp1
                        elif for1 > agt1:
                            pl1 = skp1
                        else:
                            pl1 = opp1
                        if opp2 > 900000:
                            pl2 = skp2
                        elif for2 > agt2:
                            pl2 = skp2
                        else:
                            pl2 = opp2
                        dat = [self.opts["conum"], self.ccod, pl1,
                            self.gcod + 1, "D", 0, pl2, "", grp, 0,
                            0, 0.0, 0, 0, 0.0, "", 0, pair]
                        self.sql.insRec("bwlgme", data=dat)
                    if len(recs) == 1:
                        break
                self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doQuit(self, event=None):
        col = ["count(*)"]
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod),
            ("bcg_game", "=", self.gcod),
            ("bcg_scod", "<", 900000),
            ("bcg_ocod", "<", 900000),
            ("bcg_sfor=0 and bcg_sagt=0",)]
        chk = self.sql.getRec("bwlgme", cols=col, where=whr, limit=1)
        if chk[0]:
            ok = askQuestion(self.opts["mf"].body, "Quit Capture",
                "Are You Sure that you would like to Quit before "\
                "capturing All Results?", default="no")
            if ok == "no":
                self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                return
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
