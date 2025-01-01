"""
SYNOPSIS
    Bowls Competition Draw and Score Cards.

    Formulas for Single Elimination Tournaments:

    N = Total number of entries.
    P = The power of 2 to equal or exceed N.
    X = The number of times 2 was raised to get P.

    Number of games             = N - 1
    Number of Byes              = P - N
    Number of Rounds            = X
    Number of First Round Games = N - (P / 2)

    Formulas for Round Robin Tournaments:

    N = Number of entries.

    Number of games             = (N x (N - 1)) / 2

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

import random, time
from operator import itemgetter
from TartanClasses import CCD, GetCtl, MyFpdf, PrintBoards, PrintCards
from TartanClasses import ProgressBar, RepPrt, SplashScreen, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, doPrinter
from tartanFunctions import getModName, getGreens, getSingleRecords
from tartanFunctions import copyList, showError, showWarning

class bc2050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwlgme", "bwltms",
            "bwltab", "bwltyp", "bwlpts", "bwlrnd", "bwlent"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.mstart = bwlctl["ctb_mstart"]
        self.fstart = bwlctl["ctb_fstart"]
        self.nstart = bwlctl["ctb_nstart"]
        self.fromad = bwlctl["ctb_emadd"]
        t = time.localtime()
        self.today = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.sects = False
        self.game = 0
        random.seed()
        return True

    def mainProcess(self):
        cpt = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        gme = {
            "stype": "R",
            "tables": ("bwlgme",),
            "cols": (
                ("bcg_game", "", 0, "Cod"),
                ("bcg_type", "", 0, "T"),
                ("bcg_date", "", 0, "Date")),
            "where": [("bcg_cono", "=", self.opts["conum"])],
            "whera": [("T", "bcg_ccod", 0, 0)],
            "group": "bcg_game, bcg_type, bcg_date",
            "order": "bcg_game"}
        r1s = (("No","N"),("Yes", "Y"))
        r2s = (("First", "F"), ("Last", "L"))
        r3s = (("No", "N"),("Yes","Y"),("Only", "O"))
        r4s = (("Ends","E"),("Totals", "T"))
        fld = [
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","N",self.doCmpCod,cpt,None,None),
            (("T",0,0,0),"ONA",30,""),
            [("T",0,1,0),"I@bcg_game",0,"","",
                self.game,"N",self.doGamNum,gme,None,("efld",)],
            (("T",0,2,0),"I@bcg_date",0,"","",
                self.today,"N",self.doGamDte,None,None,("efld",)),
            (("T",0,3,0),("IRB",r1s),0,"Pair Home with Away Skips","",
                "N","N",self.doHAPair,None,None,None,None,
                "For the First Drawn game Try and Pair Visiting skips "\
                "with Home skips so that Visitors are Not Drawn against "\
                "each other."),
            (("T",0,4,0),"IUI",1,"Number of Groups","",
                0,"N",self.doGrpNum,None,None,("in", (0, 2, 3))),
            (("T",0,5,0),("IRB",r2s),0,"Smallest Groups","",
                "F","N",self.doGrpSml,None,None,None),
            (("T",0,6,0),"IUA",35,"Greens","Greens (A,B,C)",
                "","N",self.doGreens,None,None,("notblank",),None,"Available "\
                "Greens in the format A,B or A,B345 showing Green Code and "\
                "Rinks. If the Rinks are Not Entered they will Default to 6. "\
                "To Default to 7 Rinks enter the Green Code followd by 7 e.g. "\
                "A7 or A1234567"),
            (("T",0,7,0),("IRB",r1s),0,"Group per Green","",
                "N","N",self.doGrpGrn,None,None,None),
            (("T",0,8,0),("IRB",r3s),0,"Print Cards","",
                "N","N",self.doPrtCards,None,None,None),
            (("T",0,9,0),("IRB",r4s),0,"Card Type","",
                "E","N",self.doTypCards,None,None,None),
            (("T",0,10,0),("IRB",r1s),0,"All Cards","",
                "Y","N",self.doAllCards,None,None,None)]
        if "args" in self.opts:
            tnd = ((self.doEnd,"n"),)
        else:
            tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","Y"))
        self.df.setWidget(self.df.topEntry[0][12][2][0], state="hide")
        if self.opts["mf"].window.state() == "withdrawn":
            self.opts["mf"].window.deiconify()
        if "args" in self.opts:
            self.df.topf[0][3][4] = "Game Date(noesc)"
            self.df.doKeyPressed("T", 0, 0, self.opts["args"][0])
            self.df.doKeyPressed("T", 0, 2, self.opts["args"][1])
            self.df.doKeyPressed("T", 0, 3, self.today)
            if self.cfmat == "T":
                self.df.doKeyPressed("T", 0, 4, "N")

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        dogme = False
        self.args = None
        self.fini = False
        self.drawall = False
        self.allgmes = False
        self.reprint = False
        bwlcmp = self.sql.getRec("bwlcmp", where=[("bcm_cono",
            "=", self.opts["conum"]), ("bcm_code", "=", w)], limit=1)
        if not bwlcmp:
            return "Invalid Competition Code"
        self.ccod = w
        self.cdes = bwlcmp[self.sql.bwlcmp_col.index("bcm_name")]
        self.df.loadEntry(frt, pag, p+1, data=self.cdes)
        self.sdat = bwlcmp[self.sql.bwlcmp_col.index("bcm_date")]
        self.ctyp = bwlcmp[self.sql.bwlcmp_col.index("bcm_type")]
        if not self.ctyp:
            showError(self.opts["mf"].body, "Type",
                "There Is No Competition Type.")
            return "xt"
        bwltyp = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", self.ctyp)], limit=1)
        self.cfmat = bwltyp[self.sql.bwltyp_col.index("bct_cfmat")]
        self.tsize = bwltyp[self.sql.bwltyp_col.index("bct_tsize")]
        self.games = bwltyp[self.sql.bwltyp_col.index("bct_games")]
        self.drawn = bwltyp[self.sql.bwltyp_col.index("bct_drawn")]
        ents = self.sql.getRec("bwlent", cols=["bce_scod"],
            where=[("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod)])
        if not ents:
            showError(self.opts["mf"].body, "Entries",
                "There Are No Entries for this Competition.")
            return "rf"
        self.tskps = []
        for ent in ents:
            self.tskps.append(ent[0])
        if self.cfmat == "D":
            if len(self.tskps) % self.tsize:
                showError(self.opts["mf"].body, "Mismatch",
                    "There is an Odd Number of Entries (%s)" % len(self.tskps))
                return "rf"
            self.totskp = int(len(self.tskps) / self.tsize)
        else:
            self.totskp = len(self.tskps)
        if self.totskp % 2 and self.cfmat in ("T", "X"):
            showError(self.opts["mf"].body, "Mismatch",
                "There is an Uneven Number of Teams (%s)" % self.totskp)
            return "rf"
        if self.cfmat in ("D", "K"):
            if self.totskp > 64:
                showError(self.opts["mf"].body, "Maximum Exceeded",
                    "There are Too Many Entries (%s)" % self.totskp)
                return "rf"
            elif self.totskp < 2:
                showError(self.opts["mf"].body, "Minimum Exceeded",
                    "There are Not Enough Entries (%s)" % self.totskp)
                return "rf"
            else:
                self.games = 1
        elif self.cfmat in ("R", "W"):
            chk = self.sql.getRec("bwlgme", cols=["count(*)"],
                where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod)], group="bcg_group")
            if chk and len(chk) > 1:
                self.games = (chk[0][0] // len(chk)) // 2
                self.drawn = self.games
                self.ssiz = chk[0][0] // self.games
                self.sects = True
            elif self.cfmat == "R":
                self.games = self.totskp - 1
                self.drawn = self.games
                self.sects = False
            else:
                self.data = self.sql.getRec("bwlent", cols=["bce_tcod"],
                    where=[("bce_cono", "=", self.opts["conum"]),
                    ("bce_ccod", "=", self.ccod)], group="bce_tcod")
                if not self.games:
                    self.games = len(self.data) - 1
                self.drawn = self.games
                self.ssiz = len(self.data)
                self.sects = True
        self.ends = bwltyp[self.sql.bwltyp_col.index("bct_ends")]
        self.groups = bwltyp[self.sql.bwltyp_col.index("bct_groups")]
        self.grgame = bwltyp[self.sql.bwltyp_col.index("bct_grgame")]
        self.adjust = bwltyp[self.sql.bwltyp_col.index("bct_adjust")]
        expunge = bwltyp[self.sql.bwltyp_col.index("bct_expunge")].split(",")
        self.expunge = []
        for ex in expunge:
            if ex:
                self.expunge.append(int(ex))
        self.strict = bwltyp[self.sql.bwltyp_col.index("bct_strict")]
        self.percent = bwltyp[self.sql.bwltyp_col.index("bct_percent")]
        self.pdiff = bwltyp[self.sql.bwltyp_col.index("bct_pdiff")]
        if self.cfmat in ("T", "X"):
            # Tournament and Teams
            gme = self.sql.getRec("bwlgme", cols=["max(bcg_game)"],
                where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod)], limit=1)
            if gme[0] is None or gme[0] < self.games:
                if gme[0] is None:
                    self.game = 1
                else:
                    self.game = gme[0] + 1
                self.df.loadEntry(frt, pag, p+2, data=self.game)
                return
        if self.cfmat in ("D", "K", "R", "W"):
            # Knock Out and Round Robin
            games = self.sql.getRec("bwlgme", cols=["bcg_game", "bcg_type",
                "bcg_date", "bcg_aflag", "sum(bcg_points)"], where=[("bcg_cono",
                "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod)],
                group="bcg_game, bcg_type, bcg_aflag", order="bcg_game")
            if not games:
                # No Drawn Games
                if self.cfmat in ("R", "W"):
                    # Round Robin
                    lbye = 1
                    if self.cfmat == "R":
                        self.doSections()
                        random.shuffle(self.tskps)
                    if self.sects:
                        if self.ssiz % 2 or self.totskp % self.ssiz:
                            ok = askQuestion(self.opts["mf"].body, "Mismatch",
                                "Uneven Number of Teams or Entries/Section "\
                                "(%s)\nDo You Want Byes?" % self.ssiz)
                            if ok == "no":
                                return "rf"
                        # Create Sections
                        if self.cfmat == "W":
                            teams = []
                            for grp in self.data:
                                skps = self.sql.getRec("bwlent",
                                    cols=["bce_scod"], where=[("bce_cono", "=",
                                    self.opts["conum"]), ("bce_ccod", "=",
                                    self.ccod), ("bce_tcod", "=", grp[0])])
                                random.shuffle(skps)
                                for num, dat in enumerate(skps):
                                    if not teams:
                                        teams.append([])
                                    elif len(teams) == num:
                                        teams.append([])
                                    teams[num].append(dat[0])
                            for num, team in enumerate(teams):
                                while len(team) < self.ssiz:
                                    team.append(900000 + lbye)
                                    self.totskp += 1
                                    lbye += 1
                                if self.ssiz % 2:
                                    team.append(900000 + lbye)
                                    lbye += 1
                                if self.cfmat == "R":
                                    self.games = len(team) - 1
                                self.ssiz = len(team)
                                self.doPopulate(team, sect=int(num + 1))
                        else:
                            for x in range(0, len(self.tskps), self.ssiz):
                                team = self.tskps[x:x+self.ssiz]
                                while len(team) < self.ssiz:
                                    team.append(900000 + lbye)
                                    lbye += 1
                                if self.ssiz % 2:
                                    team.append(900000 + lbye)
                                    lbye += 1
                                self.games = len(team) - 1
                                self.ssiz = len(team)
                                self.doPopulate(team, sect=int((x/self.ssiz)+1))
                    else:
                        if self.totskp % 2:
                            ok = askQuestion(self.opts["mf"].body, "Mismatch",
                                "There is an Uneven Number of Teams (%s), "\
                                "Do You Want Byes?" % self.totskp)
                            if ok == "yes":
                                self.tskps.append(900000 + lbye)
                                self.totskp += 1
                                self.games += 1
                                lbye += 1
                            else:
                                return "rf"
                        self.doPopulate(self.tskps)
                elif self.cfmat == "D":
                    # Drawn Knockout, Create Teams
                    self.doPopulate(self.doDrawTeams(copyList(self.tskps)))
                else:
                    # Normal Knockout, Create Teams
                    self.doPopulate(self.tskps)
                self.game = 1
                self.gtyp = "D"
                self.df.loadEntry(frt, pag, p+2, data=self.game)
                if self.cfmat in ("R", "W"):
                    return "sk1"
                else:
                    self.grpsel = False
                    self.grpgrn = "N"
                    return "sk11"
            elif self.cfmat in ("D", "K"):
                ok = askQuestion(self.opts["mf"].body, "Drawn",
                    "This Knockout Competition has Already Been Drawn."\
                    "\n\nDo You Want to Reprint?")
                if ok == "yes":
                    self.reprint = True
                    return "sk11"
                else:
                    return "rf"
            for game in games:
                if self.cfmat in ("R", "W"):
                    # Round Robin
                    if not game[2]:
                        dogme = True
                        break
                elif not game[3] and not game[4]:
                    dogme = True
                    break
        if dogme:
            self.game = game[0]
            self.gtyp = game[1]
            self.df.loadEntry(frt, pag, p+2, data=self.game)
            return
        ok = askQuestion(self.opts["mf"].body, "All Drawn",
            "All Games are Already Drawn, Do You Want to Reprint?")
        if ok == "yes":
            self.allgmes = True
            self.reprint = True
        else:
            return "rf"

    def doPopulate(self, teams, sect=None):
        cols = self.sql.bwlgme_col
        data = [self.opts["conum"], self.ccod, 0, 0, "D", 0, 0, "",
            0, 0, 0, 0, 0, 0, 0, "", 0, 1]
        if self.cfmat in ("R", "W"):
            sch = self.doMakeSchedule(teams)
            for game in range(self.games):
                for chk in sch[game]:
                    skp = teams[chk[0]]
                    opp = teams[chk[1]]
                    data[cols.index("bcg_scod")] = skp
                    data[cols.index("bcg_game")] = game + 1
                    data[cols.index("bcg_ocod")] = opp
                    if sect:
                        data[cols.index("bcg_group")] = sect
                    self.sql.insRec("bwlgme", data=data)
                    data[cols.index("bcg_scod")] = opp
                    data[cols.index("bcg_ocod")] = skp
                    self.sql.insRec("bwlgme", data=data)
        else:
            for skip in teams:
                data[cols.index("bcg_scod")] = skip
                data[cols.index("bcg_game")] = self.game + 1
                self.sql.insRec("bwlgme", data=data)

    def doMakeSchedule(self, teams):
        grps = [0+i for i in range(len(teams))]
        half = int(len(teams) / 2)
        sch = []
        for _ in range(self.games):
            pairings = []
            for i in range(half):
                pairings.append([grps[i], grps[len(teams)-i-1]])
            grps.insert(1, grps.pop())
            sch.append(pairings)
        return sch

    def doSections(self):
        self.ssiz = 0
        tit = ("Sections (Teams Entered %s" % self.totskp,)
        r1s = (("No","N"),("Yes", "Y"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sections","",
                "N","Y",self.doSecEnt,None,None,None),
            (("T",0,1,0),"IUI",2,"Entries per Section","",
                0,"N",self.doSecSiz,None,None,("notzero",)))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.ss = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doSecEnd,"y"),), txit=(self.doSecExit,))
        self.ss.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doSecEnt(self, frt, pag, r, c, p, i, w):
        if w == "Y":
            self.sects = True
        else:
            self.sects = False
            return "nd"

    def doSecSiz(self, frt, pag, r, c, p, i, w):
        if w >= self.totskp:
            return "Invalid Number"
        self.ssiz = w

    def doSecEnd(self):
        self.ss.closeProcess()

    def doSecExit(self):
        self.sects = False
        self.ss.closeProcess()

    def doDrawTeams(self, teams):
        tabs = []
        col = ["btb_tab", "btb_gender", "btb_pos1", "btb_rate1"]
        men = 0
        wom = 0
        for tab in teams:
            rec = self.sql.getRec("bwltab", cols=col, where=[("btb_cono",
                "=", self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
            tabs.append(rec)
            if rec[1] == "M":
                men += 1
            else:
                wom += 1
        tabs = sorted(tabs, key=itemgetter(2, 3))
        qty = int(len(teams) / self.tsize)
        skips = []
        for _ in range(qty):
            skips.append(tabs.pop())
        if self.tsize == 3:
            seconds = []
            for _ in range(qty):
                seconds.append(tabs.pop())
        leads = []
        for _ in range(qty):
            leads.append(tabs.pop())
        if men and wom:
            qm = int(men / qty)
            if men % qty:
                qm += 1
            qw = int(wom / qty)
            if wom % qty:
                qw += 1
            count = 50000
        else:
            count = 1
        for num in range(count):
            team = []
            redraw = False
            self.teams = {}
            if not num or num % self.tsize == 0:
                random.shuffle(skips)
            sk = copyList(skips)
            if self.tsize == 3:
                if not num or num % self.tsize == 1:
                    random.shuffle(seconds)
                sc = copyList(seconds)
                if not num or num % self.tsize == 2:
                    random.shuffle(leads)
            elif not num or num % self.tsize == 1:
                random.shuffle(leads)
            ld = copyList(leads)
            for _ in range(qty):
                skp = sk.pop()
                team.append(skp[0])
                if self.tsize == 2:
                    self.teams[skp[0]] = [skp, ld.pop()]
                else:
                    self.teams[skp[0]] = [skp, sc.pop(), ld.pop()]
            if men and wom:
                # Mixed Draw
                text = "Draw Number %s" % (num + 1)
                if not num:
                    self.sp = SplashScreen(self.opts["mf"].body, text)
                else:
                    self.sp.label.configure(text=text)
                    self.sp.refreshSplash()
                for tm in self.teams:
                    mm = 0
                    ww = 0
                    for m in self.teams[tm]:
                        if m[1] == "M":
                            mm += 1
                        else:
                            ww += 1
                    if mm > qm or ww > qw:
                        redraw = True
            if not redraw:
                break
        if men and wom:
            self.sp.closeSplash()
        return team

    def doGamNum(self, frt, pag, r, c, p, i, w):
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod)]
        if not self.reprint and self.cfmat in ("T", "X"):
            # Delete bwlgme records
            wer = copyList(whr)
            wer.append(("bcg_game", ">=", self.game))
            self.sql.delRec("bwlgme", where=wer)
            if w == self.game:
                # Populate bwlgme records
                cols = self.sql.bwlgme_col
                if self.game <= self.drawn:
                    self.gtyp = "D"
                else:
                    self.gtyp = "S"
                data = [self.opts["conum"], self.ccod, 0, self.game,
                    self.gtyp, 0, 0, "", 0, 0, 0, 0, 0, 0, 0, "", 0, 1]
                if self.groups == "Y" and self.game > 1:
                    # Get groupings
                    grps = self.sql.getRec("bwlgme", cols=["bcg_scod",
                        "bcg_group"], where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod)],
                        group="bcg_scod, bcg_group", order="bcg_scod")
                    grp = dict(grps)
                for skp in self.tskps:
                    data[cols.index("bcg_scod")] = skp
                    if self.groups == "Y" and self.game > 1:
                        data[cols.index("bcg_group")] = grp[skp]
                    self.sql.insRec("bwlgme", data=data)
        wer = copyList(whr)
        wer.extend([("bcg_game", "=", w), ("bcg_aflag", "in", ("", "D"))])
        col = ["bcg_game", "bcg_type", "bcg_date", "sum(bcg_ocod)"]
        chk = self.sql.getRec("bwlgme", cols=col, where=wer,
            group="bcg_game, bcg_type, bcg_date", limit=1)
        if not chk:
            return "Invalid Game, Missing, Skipped or Abandoned"
        if not self.reprint and w > self.game and chk[1] in ("", "S"):
            return "Invalid Game Number, Previous Games Unfinished"
        if not self.reprint and chk[2] and chk[3]:
            ok = askQuestion(self.opts["mf"].body, "Game Drawn",
                "This Game is Already Drawn, Do You Want to Reprint?",
                default="no")
            if ok == "yes":
                self.reprint = True
            else:
                return "rf"
        if not self.reprint and w > 1 and chk[1] == "S":
            col = ["count(*)"]
            wer = copyList(whr)
            wer.extend([
                ("bcg_game", "=", w - 1),
                ("bcg_scod", "<", 900000),
                ("bcg_ocod", "<", 900000),
                ("bcg_sfor", "=", 0),
                ("bcg_sagt", "=", 0),
                ("bcg_aflag", "in", ("", "D"))])
            res = self.sql.getRec("bwlgme", cols=col, where=wer, limit=1)
            if res[0]:
                mis = int(res[0] / 2)
                return "%s Results of Previous Game Not Entered" % mis
        self.game = chk[0]
        self.gtyp = chk[1]
        if self.reprint:
            self.date = chk[2]
            self.datd = CCD(self.date, "D1", 10).disp
            self.df.loadEntry(frt, pag, p+1, data=self.date)
            self.df.setWidget(self.df.topEntry[0][9][2][0], state="show")
            return "sk6"
        self.df.setWidget(self.df.topEntry[0][9][2][0], state="hide")
        if w == 1 and self.drawn > 1 and (self.cfmat in ("R", "W") or \
                (self.cfmat in ("T", "X") and self.gtyp == "D")):
            ok = askQuestion(self.opts["mf"].body, "Drawn Games",
                "Do You Want to Print All Drawn Games?", default="no")
            if ok == "yes":
                self.drawall = True

    def doGamDte(self, frt, pag, r, c, p, i, w):
        if w < self.today or w < self.sdat:
            return "Invalid Date, in the Past or Before Starting Date"
        self.date = w
        self.datd = self.df.t_disp[pag][0][i]
        self.grpsel = False
        if self.cfmat != "T":
            self.hapair = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk3"
        if self.game > 1:
            if self.groups == "Y" and self.grgame == (self.game - 1):
                self.grpsel = True
            self.hapair = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            if self.grpsel:
                return "sk1"
            else:
                return "sk3"

    def doHAPair(self, frt, pag, r, c, p, i, w):
        self.hapair = w
        if not self.grpsel:
            return "sk2"

    def doGrpNum(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Number, Must Be Two or More"
        self.grpnum = w

    def doGrpSml(self, frt, pag, r, c, p, i, w):
        self.grpsml = w
        col = [
            "bcg_scod",
            "sum(bcg_points) as pts",
            "sum(bcg_sfor - bcg_sagt) as diff",
            "sum(bcg_sagt) as agt"]
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod)]
        grp = "bcg_scod"
        odr = "pts desc, diff desc, agt asc"
        self.gchk = self.sql.getRec("bwlgme", cols=col, where=whr,
            group=grp, order=odr)
        totskp = len(self.gchk)
        grpcnt = self.grpnum
        gqty = int(totskp / grpcnt)
        if gqty % 2:
            gqty -= 1
        self.grps = [gqty] * grpcnt
        ovrs = int((totskp - (gqty * grpcnt)) / 2)
        if ovrs:
            for x in range(ovrs):
                if self.grpsml == "F":
                    self.grps[grpcnt - 1 - x] += 2
                else:
                    self.grps[x] += 2
            mess = ""
            grps = ["A", "B", "C", "D", "E"]
            for num, grp in enumerate(self.grps):
                mess += " Group %s with %s Skips %s Rinks\n" % (grps[num],
                    grp, int(grp/2))
            mess += "\nIs this Correct?"
            ok = askQuestion(self.df.window, head="Group Allocations",
                mess=mess, default="yes")
            if ok == "no":
                return "Invalid Selection"

    def doGreens(self, frt, pag, r, c, p, i, w):
        self.greens, self.first, self.endrks, err = getGreens(w,
            int(self.totskp / 2))
        if err:
            return err
        grns = w.split(",")
        for x in range(1, 5):
            # Up to 4 greens allowed
            if x <= len(grns):
                setattr(self, "gr%s" % x, grns[x-1][0])
            else:
                setattr(self, "gr%s" % x, "")
        if self.groups == "N" or self.game != self.games:
            self.grpgrn = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.grpgrn)
            if self.drawall and self.game > 1:
                return "nd"
            return "sk1"
        grps = self.sql.getRec("bwlgme", cols=["bcg_group"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            self.ccod), ("bcg_game", "=", self.game)], group="bcg_group")
        if len(grps) != len(grns):
            self.grpgrn = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.grpgrn)
            return "sk1"

    def doGrpGrn(self, frt, pag, r, c, p, i, w):
        self.grpgrn = w

    def doPrtCards(self, frt, pag, r, c, p, i, w):
        self.prtcards = w
        if self.prtcards in ("Y", "O"):
            if self.cfmat in ("R", "W") and self.drawall:
                return
            if self.cfmat in ("R", "W") and self.game ==1 and self.allgmes:
                return
            self.ctype = "E"
            self.df.loadEntry(frt, pag, p+1, data=self.ctype)
            if not self.reprint:
                self.allcards = "Y"
                self.df.loadEntry(frt, pag, p+2, data=self.allcards)
                return "sk2"
            return "sk1"
        else:
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            return "sk2"

    def doTypCards(self, frt, pag, r, c, p, i, w):
        self.ctype = w
        if not self.reprint:
            self.allcards = "Y"
            self.df.loadEntry(frt, pag, p+1, data=self.allcards)
            return "sk1"

    def doAllCards(self, frt, pag, r, c, p, i, w):
        self.allcards = w

    def doEnd(self):
        if not self.drawall:
            self.df.closeProcess()
        if self.cfmat in ("D", "K"):
            self.printKnockout()
            if self.cfmat == "D":
                self.printTeams()
            if not self.reprint:
                self.opts["mf"].dbm.commitDbase(ask=True)
            if "wait" not in self.opts:
                self.opts["mf"].closeLoop()
            return
        if not self.reprint:
            if self.cfmat == "T" and self.gtyp == "D":
                repeat = 500
            elif self.cfmat in ("R", "W"):
                repeat = 20
            else:
                repeat = 1
            self.best = [999, {}]
            self.check = int(
                (self.game * len(self.endrks)) / int(self.totskp / 2))
            if (self.game * len(self.endrks)) % int(self.totskp / 2):
                self.check += 1
            text = "Allocating Rinks, Please Wait"
            pb = ProgressBar(self.opts["mf"].body, typ=("P", text), mxs=repeat)
            for x in range(repeat):
                pb.displayProgress(x)
                if not self.pairSkips():
                    self.doExit()
                    return
                if (self.cfmat == "T" and self.gtyp == "D") or self.cfmat == "W":
                    if self.allocateRinks(final=False):
                        break
                    if x == int(repeat - 1):
                        self.allocateRinks(final=True)
                else:
                    self.allocateRinks(final=True)
            pb.closeProgress()
            if self.best[0] >= 10:
                showWarning(self.opts["mf"].body, "Anomalies",
                    "There are Some Draw Anomalies, Please Print a Draw "\
                    "Summary Sheet and, if required, Change the Draw "\
                    "Manually.")
        if self.reprint and self.prtcards == "O":
            pass
        else:
            self.printGame()
        if not self.reprint:
            if self.cfmat in ("R", "W"):
                if self.game == 1:
                    self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_game", ">", self.games)])
            if not self.drawall and not "args" in self.opts:
                ok = askQuestion(self.opts["mf"].body, "Summary",
                    "Do You Want to Print a Draw Summary?", default="no")
                if ok == "yes":
                    callModule(self.opts["mf"], None, "bc3090",
                        coy=[self.opts["conum"], self.opts["conam"]],
                        args=[self.ccod, self.igend, self.df.repprt,
                        self.df.repeml])
        if self.drawall:
            self.sql.updRec("bwlgme", cols=["bcg_aflag"], data=["D"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                "=", self.ccod), ("bcg_game", "=", self.game)])
            self.game += 1
            if self.cfmat == "T":
                nxt = self.sql.getRec("bwlgme", where=[("bcg_cono",
                    "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                    ("bcg_game", "=", self.game), ("bcg_type", "=", "D")],
                    limit=1)
            else:
                nxt = self.sql.getRec("bwlgme", where=[("bcg_cono",
                    "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                    ("bcg_game", "=", self.game)], limit=1)
            if nxt:
                self.df.doInvoke(["T", 0, 3, self.doGamNum], self.game)
            else:
                self.fini = True
        if not self.drawall or self.fini:
            self.df.closeProcess()
            if not self.reprint:
                if "args" in self.opts:
                    ask = False
                else:
                    ask = True
                self.opts["mf"].dbm.commitDbase(ask=ask, rback=False)
            if self.drawall:
                ok = askQuestion(self.opts["mf"].body, "Summary",
                    "Do You Want to Print a Draw Summary?", default="no")
                if ok == "yes":
                    callModule(self.opts["mf"], None, "bc3090",
                        coy=[self.opts["conum"], self.opts["conam"]],
                        args=[self.ccod, self.igend, self.df.repprt,
                            self.df.repeml])
            if self.prtcards in ("Y", "O"):
                if self.ctype == "E":
                    if self.drawall:
                        for self.game in range(1, self.games + 1):
                            self.printCards()
                    else:
                        self.printCards()
                else:
                    self.printBoards()
            if self.opts["conam"] == "TEST" or "args" not in self.opts:
                self.opts["mf"].closeLoop()

    def pairSkips(self):
        if self.cfmat in ("D", "K"):
            return True
        if self.cfmat in ("R", "W"):
            # Round Robin
            self.skips = []
            recs = self.sql.getRec("bwlgme", cols=["bcg_scod", "bcg_ocod"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_game", "=", self.game)], order="bcg_scod")
            for rec in recs:
                if rec[0] not in self.skips:
                    self.skips.extend(rec)
            return True
        if self.gtyp == "D":
            # Drawn Games
            if self.cfmat == "X":
                # Teams
                teams = {"H": {}, "V": {}}
                ents = self.sql.getRec("bwlent", where=[("bce_cono",
                    "=", self.opts["conum"]), ("bce_ccod", "=", self.ccod)])
                for skp in ents:
                    scod = skp[self.sql.bwlent_col.index("bce_scod")]
                    tcod = skp[self.sql.bwlent_col.index("bce_tcod")]
                    teams[tcod][scod] = []
                    opps = self.sql.getRec("bwlgme", cols=["bcg_ocod"],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", scod),
                        ("bcg_ocod", "<>", 0)])
                    for opp in opps:
                        teams[tcod][scod].append(opp[0])
                chk = (len(teams["H"]), len(teams["V"]))
                if chk[0] != chk[1]:
                    showError(self.opts["mf"].body, "Mismatch",
                        """There is an Uneven Number of Skips per Team:

                Home:      %3s
                Visitors:  %3s\n""" % chk)
                    return
                chk = True
                while chk:
                    pair = []
                    home = list(teams["H"].keys())
                    away = list(teams["V"].keys())
                    random.shuffle(home)
                    random.shuffle(away)
                    for skp in home:
                        for opp in away:
                            if opp not in teams["H"][skp] and opp not in pair:
                                pair.extend([skp, opp])
                                break
                    if len(pair) == len(ents):
                        chk = False
                self.skips = pair
                return True
            # Other
            recs = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_game", "=", self.game)], order="bcg_scod")
            if len(recs) % 2:
                showError(self.opts["mf"].body, "Mismatch",
                    "There is an Uneven Number of Teams (%s)" % len(recs))
                return
            self.skips = []
            if self.game == 1 and self.hapair == "Y":
                # Separate home and away skips
                home = []
                away = []
                for rec in recs:
                    if rec[0] < self.nstart:
                        home.append(rec[0])
                    else:
                        away.append(rec[0])
                # pair home and away skips
                random.shuffle(home)
                random.shuffle(away)
                while home:
                    self.skips.append(home.pop())
                    if away:
                        self.skips.append(away.pop())
                    else:
                        self.skips.append(home.pop())
                while away:
                    self.skips.append(away.pop())
                    self.skips.append(away.pop())
                return True
            for rec in recs:
                self.skips.append(rec[0])
            chk = True
            while chk:
                random.shuffle(self.skips)
                # Check for pair clashes in all drawn games
                for x in range(0, len(self.skips), 2):
                    one = self.skips[x]
                    two = self.skips[x + 1]
                    chk = self.sql.getRec("bwlgme", where=[("bcg_cono",
                        "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_scod", "=", one), ("bcg_type", "=", "D"),
                        ("bcg_ocod", "=", two)], limit=1)
                    if chk:
                        break
            return True
        # Strength versus Strength
        if self.grpsel:
            # Allocate Into Groups
            start = 0
            for num, qty in enumerate(self.grps):
                for skp in range(start, start + qty):
                    self.sql.updRec("bwlgme", cols=["bcg_group"],
                        data=[num + 1], where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=",
                        self.ccod), ("bcg_scod", "=", self.gchk[skp][0])])
                start += qty
        groups = self.sql.getRec("bwlgme", cols=["bcg_group"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            self.ccod), ("bcg_game", "<", self.game)], group="bcg_group",
            order="bcg_group")
        self.skips = []
        for grp in groups:
            chk = self.sql.getRec("bwlgme", cols=["bcg_scod",
                "sum(bcg_a_points) as pts", "sum(bcg_a_sagt) as agt",
                "sum(bcg_a_sfor - bcg_a_sagt) as diff"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_group", "in", (0, grp[0]))],
                group="bcg_scod", order="pts desc, diff desc, agt asc")
            if self.strict == "Y" or self.game == self.games:
                # Last game, straight Strength versus Strength
                for x in range(0, len(chk), 2):
                    self.skips.extend([chk[x][0], chk[x + 1][0]])
                continue
            fini = False
            self.lock = []
            for x in range(100):
                if x == 99:
                    self.lock = []
                    fini = True
                err = self.doStrength(chk, fini)
                if not err:
                    break
                self.doClash(chk, err[-1])
        return True

    def doStrength(self, chk, fini):
        dun = copyList(self.lock)
        err = []
        for x, c in enumerate(chk):
            if c[0] in dun or c[0] in err:
                continue
            one = c[0]
            done = False
            count = 0
            for s in chk:
                if s[0] == one or s[0] in dun or s[0] in err:
                    continue
                if not self.checkSkip(one, s[0]):
                    dun.extend([one, s[0]])
                    done = True
                    break
                count += 1
            if not done:
                for s in chk:
                    if s[0] == one or s[0] in dun or s[0] in err:
                        continue
                    if fini:
                        dun.extend([one, s[0]])
                    else:
                        err.extend([one, s[0]])
                    break
        if not err:
            for x in range(0, len(dun), 2):
                self.skips.extend([dun[x], dun[x + 1]])
        return err

    def doClash(self, chk, err):
        for x in range(len(chk), 0, -1):
            s = chk[x - 1]
            if s[0] != err and s[0] not in self.lock and not \
                                    self.checkSkip(err, s[0]):
                self.lock.extend([err, s[0]])
                break

    def checkSkip(self, one, two):
        if self.cfmat in ("R", "W"):
            return
        return self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_scod",
            "=", one), ("bcg_ocod", "=", two), ("bcg_game", "<", self.game)])

    def allocateRinks(self, final=False):
        allrnk = []
        for grn in self.greens:
            for rnk in self.greens[grn]:
                allrnk.append("%s%s" % (grn, rnk))
        skpdic = {}
        if self.cfmat == "T" and self.gtyp == "S" and self.game == self.games:
            # If Final, Allocate First Green to Leaders or Green per Group
            self.igend = "Y"
            groups = self.sql.getRec("bwlgme", cols=["bcg_group"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_group", "<>", 0)], group="bcg_group")
            num = len(groups)                   # Number of groups
            lst = None                          # Last group processed
            cnt = 0                             # Number of rinks allocated
            end = len(self.greens[self.first])  # Last rink of first green
            for x in range(0, len(self.skips), 2):
                one = self.skips[x]
                two = self.skips[x + 1]
                grp = self.sql.getRec("bwlgme", cols=["bcg_group"],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "=", one), ("bcg_game", "=",
                    self.game)], limit=1)[0]
                if lst != grp:
                    lst = grp
                    pos = 0
                rnk = None
                if grp == 0 and pos < len(self.greens[self.first]):
                    rnk = "%s%s" % (self.first, [4, 3, 5, 2, 6, 1, 7][pos])
                elif grp == 1:
                    if self.grpgrn == "Y" and self.gr1:
                        rnk = "%s%s" % (self.gr1, [4, 3, 5, 2, 6, 1, 7][pos])
                    elif pos < len(self.greens[self.first]) - 2:
                        rnk = "%s%s" % (self.first, [4, 3, 5, 2, 6][pos])
                elif grp == 2:
                    if self.grpgrn == "Y" and self.gr2:
                        rnk = "%s%s" % (self.gr2, [4, 3, 5, 2, 6, 1, 7][pos])
                    elif num == 2 and pos < 2:
                        rnk = "%s%s" % (self.first, [1, end][pos])
                    elif num == 3 and pos == 0:
                        rnk = "%s1" % self.first
                elif grp == 3:
                    if self.grpgrn == "Y" and self.gr3:
                        rnk = "%s%s" % (self.gr3, [4, 3, 5, 2, 6, 1, 7][pos])
                    elif num == 3 and pos == 0:
                        rnk = "%s%s" % (self.first, end)
                if rnk and rnk in allrnk:
                    skpdic[one] = (two, rnk)
                    allrnk.remove(rnk)
                    if self.grpgrn == "N":
                        cnt += 1
                        if cnt == end:
                            break
                pos += 1
        else:
            self.igend = "N"
        # Allocate Balance of Rinks to End Rinkers First and then Others
        if self.cfmat == "T" and self.gtyp == "D":
            repeat = 10
        else:
            repeat = 1000
        for _ in range(repeat):
            err = 0
            again = False
            cpydic = copyList(skpdic)
            cpyrnk = copyList(allrnk)
            random.shuffle(cpyrnk)
            for x in range(2):
                # x = 0 - End Rinkers Only
                # x = 1 - All the Rest
                for y in range(0, len(self.skips), 2):
                    one = self.skips[y]
                    if one in cpydic:
                        # Leader already allocated rink
                        continue
                    two = self.skips[y + 1]
                    # Check if bye
                    if one > 900000 or two > 900000:
                        cpydic[one] = (two, "BY")
                        continue
                    # Check if end rinker
                    endr = bool(self.endrks and self.checkEnds(one, two))
                    if not x and not endr:
                        continue
                    done = False
                    for rk in cpyrnk:
                        if endr and rk in self.endrks:
                            # Skip end rinks
                            continue
                        # Check for repeat rinks
                        if not self.checkRink(one, two, rk):
                            cpydic[one] = (two, rk)
                            cpyrnk.remove(rk)
                            done = True
                            break
                    if x and not done:
                        # Check if available rink found
                        err += 1
                        again = True
                        fixed = False
                        for rk in cpyrnk:
                            # Check for repeat rinks
                            if not self.checkRink(one, two, rk, final):
                                cpydic[one] = (two, rk)
                                cpyrnk.remove(rk)
                                fixed = True
                                break
                        if not fixed:
                            err += 9
            if err < self.best[0]:
                self.best = [err, copyList(cpydic)]
            if not again:
                break
        if again and not final:
            return
        if self.best[0] < 999:
            skpdic = copyList(self.best[1])
        else:
            skpdic = copyList(cpydic)
        # Update Tables with Opponents and Rinks
        col = ["bcg_date", "bcg_ocod", "bcg_rink"]
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod)]
        skps = []
        for one in skpdic:
            two, rnk = skpdic[one]
            skps.append([one, two, rnk])
            skps.append([two, one, rnk])
            d = [self.date, two, rnk]
            w = whr[:]
            w.extend([("bcg_scod", "=", one), ("bcg_game", "=", self.game)])
            self.sql.updRec("bwlgme", cols=col, data=d, where=w)
            d = [self.date, one, rnk]
            w = whr[:]
            w.extend([("bcg_scod", "=", two), ("bcg_game", "=", self.game)])
            self.sql.updRec("bwlgme", cols=col, data=d, where=w)
        if not self.sects and self.gtyp == "D" and self.best[0] and self.endrks:
            # Check for drawn game anomalies and attempt to fix them
            low = []
            big = []
            for skp in skps:
                sk, op, rk = skp
                w = whr[:]
                w.append(("bcg_scod", "=", sk))
                w.append(("bcg_rink", "in", self.endrks))
                one = self.sql.getRec("bwlgme", cols=["count(*)"],
                    where=w, limit=1)[0]
                if one < self.check:
                    low.append(skp)
                elif one > self.check:
                    big.append(skp)
            if low and big:
                chg = []
                new = []
                rnk = []
                skp = False
                for n, b in enumerate(big):
                    if skp:
                        skp = False
                        continue
                    if not n == (len(big) - 1) and big[n + 1][2] == b[2] and \
                            len(low) > 1:
                        ok = False
                        for l in low:
                            for m in low:
                                if m == l:
                                    continue
                                if not self.checkSkip(l[0], m[0]):
                                    ok = True
                                    break
                            if ok:
                                break
                        if not ok:
                            continue
                        if not self.checkSkip(b[0], l[1]) and \
                                not self.checkSkip(b[1], m[1]):
                            if not self.checkRink(b[0], l[1], l[2]) and \
                                    not self.checkRink(b[1], m[1], m[2]):
                                chg.append([b[0], l[1], l[2]])
                                chg.append([b[1], m[1], m[2]])
                            elif not self.checkRink(b[0], l[1], m[2]) and \
                                    not self.checkRink(b[1], m[1], l[2]):
                                chg.append([b[0], l[1], m[2]])
                                chg.append([b[1], m[1], l[2]])
                            else:
                                ok = False
                        elif not self.checkSkip(b[0], m[1]) and \
                                not self.checkSkip(b[1], l[1]):
                            if not self.checkRink(b[0], m[1], m[2]) and \
                                    not self.checkRink(b[1], l[1], l[2]):
                                chg.append([b[0], m[1], m[2]])
                                chg.append([b[1], l[1], l[2]])
                            elif not self.checkRink(b[0], m[1], l[2]) and \
                                    not self.checkRink(b[1], l[1], m[2]):
                                chg.append([b[0], m[1], l[2]])
                                chg.append([b[1], l[1], m[2]])
                            else:
                                ok = False
                        else:
                            ok = False
                        if not ok:
                            skp = True
                            continue
                        chg.append([l[0], m[0], b[2]])
                        chg.append([m[0], l[0], b[2]])
                        low.remove(l)
                        low.remove(m)
                        skp = True
                        continue
                    for l in low:
                        if not self.checkSkip(b[0], l[1]) and \
                                not self.checkRink(b[0], l[1], l[2]):
                            chg.append([b[0], l[1], l[2]])
                            new.extend([l[0], b[1]])
                            rnk.append(b[2])
                            low.remove(l)
                            break
                while new:
                    chg.append([new.pop(0), new.pop(0), rnk.pop(0)])
                for c in chg:
                    d = [c[1], c[2]]
                    w = whr[:]
                    w.extend([
                        ("bcg_scod", "=", c[0]),
                        ("bcg_game", "=", self.game)])
                    self.sql.updRec("bwlgme", cols=col[1:], data=d, where=w)
                    d = [c[0], c[2]]
                    w = whr[:]
                    w.extend([
                        ("bcg_scod", "=", c[1]),
                        ("bcg_game", "=", self.game)])
                    self.sql.updRec("bwlgme", cols=col[1:], data=d, where=w)
                if not low and not new:
                    self.best[0] = 0
        if self.adjust == "Y":
            # Adjust scores
            chk = self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_group", ">", 1)], order="bcg_game")
            for gam in chk:
                skp = gam[self.sql.bwlgme_col.index("bcg_scod")]
                gme = gam[self.sql.bwlgme_col.index("bcg_game")]
                shf = gam[self.sql.bwlgme_col.index("bcg_sfor")]
                sha = gam[self.sql.bwlgme_col.index("bcg_sagt")]
                pts = gam[self.sql.bwlgme_col.index("bcg_points")]
                if gme in self.expunge:
                    shf = 0
                    sha = 0
                    pts = 0
                elif gme <= self.grgame:
                    shf = int(round(shf * self.percent / 100.0, 0))
                    sha = int(round(sha * self.percent / 100.0, 0))
                    pts = int(round(pts * self.percent / 100.0, 0))
                self.sql.updRec("bwlgme", cols=["bcg_a_sfor",
                    "bcg_a_sagt", "bcg_a_points"], data=[shf, sha, pts],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "=", skp), ("bcg_game", "=",
                    gme)])
        return True

    def checkEnds(self, one, two):
        # Return whether either skip has played on an end rink more than check
        for sk in (one, two):
            ends = 0
            rnks = self.sql.getRec("bwlgme", cols=["bcg_rink"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_scod", "=", sk), ("bcg_rink", "<>", "")])
            for rk in rnks:
                if rk[0] in self.endrks:
                    ends += 1
            if ends >= self.check:
                return True

    def checkRink(self, one, two, rnk, final=False):
        chk = self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
            ("bcg_scod", "in", (one, two)), ("bcg_game", "<", self.game),
            ("bcg_rink", "=", rnk)])
        if chk and final:
            return
        return chk

    def printTeams(self):
        def getNames(mem):
            rec = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", mem[0])], limit=1)
            if rec[1]:
                return "%s, %s" % (rec[0], rec[1])
            else:
                return rec[0]
        if self.reprint:
            self.teams = {}
            recs = self.sql.getRec("bwltms", where=[("btd_cono",
                "=", self.opts["conum"]), ("btd_ccod", "=", self.ccod)],
                order="btd_scod")
            for rec in recs:
                self.teams[rec[2]] = []
                for mem in rec[2:]:
                    if not mem:
                        continue
                    tab = self.sql.getRec("bwltab", cols=["btb_gender",
                        "btb_pos1", "btb_rate1"], where=[("btb_cono", "=",
                        self.opts["conum"]), ("btb_tab", "=", mem)], limit=1)
                    self.teams[rec[2]].append([mem] + tab)
        if not self.teams:
            return
        head = [
            (self.opts["conam"], 18, "C"),
            ("Teams for %s" % self.cdes, 16, "C")]
        cols = [
            ["a", "NA", 25, "Skip", "y"]]
        if self.tsize == 3:
            cols.append(["b", "NA", 25, "Second", "y"])
        cols.append(["c", "NA", 25, "Lead", "y"])
        data = []
        for skip in self.teams:
            dat = []
            if not self.reprint:
                sql = [self.opts["conum"], self.ccod]
            for mem in self.teams[skip]:
                dat.append(getNames(mem))
                if not self.reprint:
                    sql.append(mem[0])
            data.append(dat)
            if not self.reprint:
                if len(sql) == 4:
                    sql.append(0)
                self.sql.insRec("bwltms", data=sql)
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=head, cols=cols, ttype="D", repprt=self.df.repprt,
            repeml=self.df.repeml, fromad=self.fromad)

    def printKnockout(self):
        pwrs = 2
        self.rnds = 1
        while pwrs < self.totskp:
            self.rnds += 1
            pwrs = pwrs * 2
        self.byes = pwrs - self.totskp
        self.frg = self.totskp - int(pwrs / 2)
        self.prs = int((self.frg + self.byes) / 4)
        self.quit = False
        self.doCompletionDates()
        if self.quit:
            self.doExit()
        head = (self.rnds * 19) + 19
        if head > 120:
            head = 170
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=head)
        self.pageHeading(date=True)
        if not self.reprint:
            if "args" in self.opts and len(self.opts["args"]) == 3:
                self.seeds = []
            else:
                self.doSeeds()
                if self.quit:
                    self.doExit()
            grps = [0, 0]
            # Create shadow players for byes in groups
            num = 900000
            data = [self.opts["conum"], self.ccod, 0, 1, "D", 0, 0, "",
                0, 0, 0, 0, 0, 0, 0, "", 0, 0]
            for bye in range(self.byes):
                num += 1
                data[2] = num
                if bye % 2:
                    grp = 1
                else:
                    grp = 2
                data[8] = grp
                grps[grp-1] += 1
                self.sql.insRec("bwlgme", data=data)
            # Allocate seeded players to groups
            sgrps = [[], []]
            grp = 2
            for num in range(0, len(self.seeds), 2):
                grps[grp-1] += 1
                sgrps[grp-1].append(self.seeds[num])
                self.sql.updRec("bwlgme", cols=["bcg_group"], data=[grp],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "=", self.seeds[num])])
                if num == len(self.seeds) - 1:
                    break
                if grp == 1:
                    grp = 2
                else:
                    grp = 1
                grps[grp-1] += 1
                sgrps[grp-1].append(self.seeds[num + 1])
                self.sql.updRec("bwlgme", cols=["bcg_group"], data=[grp],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "=", self.seeds[num + 1])])
            # Allocate balance of players to groups
            chk = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game),
                ("bcg_group", "=", 0)], order="bcg_scod")
            skips = []
            for c in chk:
                skips.append(c[0])
            random.shuffle(skips)
            for skip in skips:
                if grps[0] < grps[1]:
                    grp = 1
                else:
                    grp = 2
                grps[grp-1] += 1
                self.sql.updRec("bwlgme", cols=["bcg_group"], data=[grp],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "=", skip)])
            # Allocate opponents
            for grp in range(1, 3):
                # Allocate seeded players to byes
                for seed in sgrps[grp-1]:
                    self.doAllocateBye(seed, grp)
                # Allocate balance of byes randomly
                chk = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_scod", "<", 900000), ("bcg_game",
                    "=", self.game), ("bcg_group", "=", grp), ("bcg_ocod",
                    "=", 0)])
                temp = []
                for c in chk:
                    temp.append(c[0])
                random.shuffle(temp)
                for skip in temp:
                    self.doAllocateBye(skip, grp)
                # Allocate opponents to balance of players randomly
                chk = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                    where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                    "=", self.ccod), ("bcg_game", "=", self.game),
                    ("bcg_group", "=", grp), ("bcg_ocod", "=", 0)])
                temp = []
                for c in chk:
                    temp.append(c[0])
                random.shuffle(temp)
                for p1 in self.seeds:
                    # Pair seeded player with unseeded player
                    if p1 not in temp:
                        continue
                    for rec in temp:
                        if rec not in self.seeds:
                            p2 = rec
                            break
                    temp.remove(p1)
                    temp.remove(p2)
                    self.sql.updRec("bwlgme", cols=["bcg_ocod"], data=[p2],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", p1),
                        ("bcg_game", "=", self.game)])
                    self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_scod", "=", p2), ("bcg_game", "=", self.game)])
                while temp:
                    p1 = temp.pop(0)
                    p2 = temp.pop(0)
                    self.sql.updRec("bwlgme", cols=["bcg_ocod"], data=[p2],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_scod", "=", p1),
                        ("bcg_game", "=", self.game)])
                    self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_scod", "=", p2), ("bcg_game", "=", self.game)])
                skips = self.sql.getRec("bwlgme", cols=["bcg_scod",
                    "bcg_ocod"], where=[("bcg_cono", "=", self.opts["conum"]),
                    ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game),
                    ("bcg_group", "=", grp)], order="bcg_ocod")
                if self.prs:
                    # Allocate seeds into pair groups
                    if self.prs == 1:
                        p1 = [1]
                    elif self.prs == 2:
                        p1 = [1, 2]
                    elif self.prs == 4:
                        p1 = [1, 3, 4, 2]
                    elif self.prs == 8:
                        p1 = [1, 5, 7, 3, 4, 8, 6, 2]
                    tot = int(len(skips) / self.prs)
                    p2 = [tot] * self.prs
                    if len(skips) % self.prs:
                        p2[0] += 1
                    for sd, seed in enumerate(self.seeds):
                        for num, skp in enumerate(skips):
                            if skp[0] == seed:
                                pos = p1.pop(0)
                                self.sql.updRec("bwlgme", cols=["bcg_seed",
                                    "bcg_pair"], data=[sd + 1, pos],
                                    where=[("bcg_cono", "=",
                                    self.opts["conum"]), ("bcg_ccod", "=",
                                    self.ccod), ("bcg_scod", "=", skp[0])])
                                p2[pos - 1] -= 1
                                break
                    # Allocate rest into pair groups
                    for num, skp in enumerate(skips):
                        if skp[0] in self.seeds:
                            continue
                        for n, p in enumerate(p2):
                            if p:
                                self.sql.updRec("bwlgme", cols=["bcg_seed",
                                    "bcg_pair"], data=[0, n + 1],
                                    where=[("bcg_cono", "=",
                                    self.opts["conum"]), ("bcg_ccod", "=",
                                    self.ccod), ("bcg_scod", "=", skp[0])])
                                p2[n] -= 1
                                break
        self.two = 0
        for grp in range(1, 3):
            skips = self.sql.getRec("bwlgme", cols=["bcg_scod",
                "bcg_ocod", "bcg_seed", "bcg_pair"], where=[("bcg_cono",
                "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", 1), ("bcg_group", "=", grp)],
                order="bcg_pair, bcg_scod")
            self.printBracket(grp, skips)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        head = "%s Draw" % self.cdes
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                header=head, pdfnam=pdfnam, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doCompletionDates(self):
        tit = ("Completion Dates",)
        r1s = (("Variable", "V"), ("Fixed", "F"))
        fld = [
            [("T",0,0,0),("IRB",r1s),0,"Starting Times","",
                "V","N",self.doComTyp,None,None,None]]
        for x in range(self.rnds):
            if x + 1 == self.rnds:
                dt = "Id1"
                tm = "ItM"
            else:
                dt = "ID1"
                tm = "ITM"
            fld.append((("T",0,x+1,0),dt,10,"Round %s Date" % (x + 1),"",
                0,"N",self.doComDate,None,None,("efld",)))
            fld.append((("T",0,x+1,0),tm,5,"Time","",
                0,"N",None,None,None,("efld",)))
        but = (("Quit",None,self.doCompletionQuit,1,None,None),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.cd = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doCompletionEnd,"y"),),
            focus=False)
        dates = self.sql.getRec("bwlrnd", cols=["bcr_date", "bcr_time"],
            where=[("bcr_cono", "=", self.opts["conum"]), ("bcr_ccod", "=",
            self.ccod)], order="bcr_date, bcr_time")
        if dates:
            self.newdte = False
            if dates[0][1]:
                self.comtyp = "F"
            else:
                self.comtyp = "V"
            self.cd.topf[0][0][5] = self.comtyp
            self.cd.loadEntry("T", 0, 0, data=self.comtyp)
            for num, dte in enumerate(dates):
                p = (num * 2) + 1
                if dte[0] == 99991231:
                    dt = 0
                    tm = 0
                else:
                    dt, tm = dte
                self.cd.loadEntry("T", 0, p, data=dt)
                self.cd.loadEntry("T", 0, p+1, data=tm)
        else:
            self.newdte = True
        self.cd.focusField("T", 0, 1, clr=False)
        self.cd.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doComTyp(self, frt, pag, r, c, p, i, w):
        self.comtyp = w

    def doComDate(self, frt, pag, r, c, p, i, w):
        if not w and self.comtyp == "F" and p == ((self.rnds * 2) - 1):
            pass
        elif w < self.today:
            if self.reprint:
                return "nd"
            else:
                return "Date in the Past"
        elif i > 1 and w < self.cd.t_work[0][0][i - 2]:
            return "Date Before Previous Date"
        if not w or self.comtyp == "V":
            self.cd.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doCompletionEnd(self):
        self.cd.closeProcess()
        self.cdates = []
        self.ctimes = []
        if not self.newdte:
            self.sql.delRec("bwlrnd", where=[("bcr_cono", "=",
                self.opts["conum"]), ("bcr_ccod", "=", self.ccod)])
        dat = copyList(self.cd.t_work[0][0][1:])
        for rnd in range(0, len(dat), 2):
            if not dat[rnd]:
                dte = 99991231
                tim = 0
            else:
                dte = dat[rnd]
                tim = dat[rnd + 1]
            self.cdates.append(CCD(dte, "D1", 10).disp)
            self.ctimes.append(CCD(tim, "TM", 5).disp)
            self.sql.insRec("bwlrnd", data=[self.opts["conum"],
                self.ccod, int(rnd / 2) + 1, dte, tim])
        if self.reprint:
            self.opts["mf"].dbm.commitDbase()

    def doCompletionQuit(self):
        self.quit = True
        self.cd.closeProcess()

    def doSeeds(self):
        if not self.ctyp:
            self.seeds = []
            return
        tit = ("Seeded Players",)
        skp = {
            "stype": "R",
            "tables": ("bwlent", "bwltab"),
            "cols": (
                ("btb_tab", "", 0, "S-Code"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names")),
            "where": [
                ("bce_cono", "=", self.opts["conum"]),
                ("bce_ccod", "=", self.ccod),
                ("btb_cono=bce_cono",),
                ("btb_tab=bce_scod",)],
            "order": "btb_surname, btb_names"}
        fld = (
            (("T",0,0,0),"IUI",2,"Number of Seeds","",
                0,"N",self.doSeedNum,None,None,("efld",)),
            (("T",0,1,0),"IUI",6,"1st Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,1,0),"OUA",20,""),
            (("T",0,2,0),"IUI",6,"2nd Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,2,0),"OUA",20,""),
            (("T",0,3,0),"IUI",6,"3rd Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,3,0),"OUA",20,""),
            (("T",0,4,0),"IUI",6,"4th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,4,0),"OUA",20,""),
            (("T",0,5,0),"IUI",6,"5th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,5,0),"OUA",20,""),
            (("T",0,6,0),"IUI",6,"6th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,6,0),"OUA",20,""),
            (("T",0,7,0),"IUI",6,"7th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,7,0),"OUA",20,""),
            (("T",0,8,0),"IUI",6,"8th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,8,0),"OUA",20,""),
            (("T",0,9,0),"IUI",6,"9th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,9,0),"OUA",20,""),
            (("T",0,10,0),"IUI",6,"10th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,10,0),"OUA",20,""),
            (("T",0,11,0),"IUI",6,"11th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,11,0),"OUA",20,""),
            (("T",0,12,0),"IUI",6,"12th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,12,0),"OUA",20,""),
            (("T",0,13,0),"IUI",6,"13th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,13,0),"OUA",20,""),
            (("T",0,14,0),"IUI",6,"14th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,14,0),"OUA",20,""),
            (("T",0,15,0),"IUI",6,"15th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,15,0),"OUA",20,""),
            (("T",0,16,0),"IUI",6,"16th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,16,0),"OUA",20,""))
        but = (("Quit",None,self.doSeedsQuit,1,None,None),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.sp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doSeedEnd,"y"),))
        self.hideSeeds()
        self.sp.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doSeedNum(self, frt, pag, r, c, p, i, w):
        if w > (self.prs * 2):
            return "Too Many Seeds (>%s)" % (self.prs * 2)
        self.seednum = w
        if not w:
            return "nd"
        self.showSeeds()

    def doSeedTab(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec(tables=["bwlent", "bwltab"], cols=["btb_surname",
            "btb_names"], where=[("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod), ("bce_scod", "=", w),
            ("btb_cono=bce_cono",), ("btb_tab=bce_scod",)], limit=1)
        if not chk:
            return "Not a Valid Entered Tab"
        seeds = []
        for x in range(self.seednum):
            if ((x * 2) + 1) == p:
                continue
            if self.sp.t_work[0][0][x * 2 + 1]:
                seeds.append(self.sp.t_work[0][0][x * 2 + 1])
        if w in seeds:
            return "Invalid Seed, Already Seeded"
        nam = chk[0].strip()
        if chk[1]:
            nam = "%s, %s" % (nam, chk[1][0])
        self.sp.loadEntry(frt, pag, p+1, data=nam)
        if int((p + 1) / 2) == self.seednum:
            return "nd"

    def hideSeeds(self):
        for x in range(1, 32, 2):
            self.sp.setWidget(self.sp.topLabel[0][x], state="hide")
            self.sp.setWidget(self.sp.topEntry[0][x], state="hide")
            self.sp.setWidget(self.sp.topEntry[0][x + 1], state="hide")

    def showSeeds(self):
        self.hideSeeds()
        for x in range(1, (self.seednum * 2), 2):
            self.sp.setWidget(self.sp.topLabel[0][x], state="show")
            self.sp.setWidget(self.sp.topEntry[0][x], state="show")
            self.sp.setWidget(self.sp.topEntry[0][x + 1], state="show")

    def doSeedEnd(self):
        self.sp.closeProcess()
        self.seeds = []
        for x in range(self.seednum):
            self.seeds.append(self.sp.t_work[0][0][x * 2 + 1])

    def doSeedsQuit(self):
        self.quit = True
        self.sp.closeProcess()

    def doAllocateBye(self, one, grp):
        chk = self.sql.getRec("bwlgme", cols=["bcg_scod"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            self.ccod), ("bcg_scod > 900000",), ("bcg_game", "=", self.game),
            ("bcg_group", "=", grp), ("bcg_ocod = 0",)], order="bcg_scod")
        if chk:
            self.sql.updRec("bwlgme", cols=["bcg_ocod"], data=[chk[0][0]],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                "=", self.ccod), ("bcg_scod", "=", one), ("bcg_game",
                "=", self.game)])
            self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_scod", "=", chk[0][0]), ("bcg_game", "=", self.game)])

    def printBracket(self, grp, skips):
        siz, cwth, chgt = self.setBracketFont()
        ohgt = self.fpdf.font[2]
        self.fpdf.font[2] = chgt
        if grp == 2 and self.rnds == 2:
            last = "down"
        else:
            last = ""
        rnds = []
        nm = 18
        l1 = 0
        l2 = 1
        rd = 1
        n1 = nm + l1
        n2 = nm + l1 + l2
        nx = (nm * 2) + l1 + l2

        def drawField(txt, x, y, w):
            nsiz = siz
            chek = w * .95
            nwth = self.fpdf.get_string_width(txt)
            while nwth >= chek:
                nsiz -= 1
                self.fpdf.setFont(style="B", size=nsiz)
                nwth = self.fpdf.get_string_width(txt)
            if txt:
                bdr = "TLRB"
            else:
                bdr = "LRB"
            self.fpdf.drawText(txt, x=x, y=y, w=w, font=("B", nsiz), border=bdr)

        for num, skip in enumerate(skips):
            # Print Round 1 and Round 2 if more than 2 Rounds
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] > 900000:
                self.fpdf.drawText("", w=(cwth * nm))
            else:
                drawField(self.getSkip(skip[0], skip[2]), x, y, w=(cwth * nm))
                self.drawLink(cwth, l1, l2, x + (cwth * nm), y + int(chgt / 2),
                    y + (chgt * 1.5))
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] > 900000:
                drawField(self.getSkip(skip[0], skip[2]),
                    x + (cwth * n2), y, w=(cwth * nm))
            else:
                drawField(self.getWinner(rd, grp, skip), x + (cwth * n2),
                    y, w=(cwth * nm))
            if not last or last == "up":
                self.drawLink(cwth, l1, l2, x + (cwth * nx), y + int(chgt / 2),
                    y + (chgt * 2.5))
                rnds.append([x+(cwth * nx), y + (chgt * 2)])
                last = "down"
            else:
                self.drawLink(cwth, l1, l2, x + (cwth * nx), y + int(chgt / 2),
                    y - (chgt * 1.5))
                if self.rnds == 2:
                    rnds.append([x + (cwth * nx), y + (chgt * 2)])
                last = "up"
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] > 900000:
                self.fpdf.drawText("", w=(cwth * nm))
            else:
                drawField(self.getSkip(skip[1], 0), x, y, w=(cwth * nm))
                self.fpdf.line(x + (cwth * nm), y + int(chgt / 2),
                    x + (cwth * n1), y + int(chgt / 2))
                self.fpdf.line(x + (cwth * n1), y + int(chgt / 2),
                    x + (cwth * n1), y - int(chgt / 2))
            self.fpdf.drawText("")
            lasty = self.fpdf.get_y()
        inc = 4
        for aa in range(self.rnds - 3):
            # Rounds 3 and 4
            rd += 1
            bb = []
            for rnd in range(0, len(rnds), 2):
                x = rnds[rnd][0]
                y = rnds[rnd][1]
                drawField(self.getWinner(rd, grp, 0, rnd + 1),
                    x + (cwth * (l1 + l2)), y, w=(cwth * nm))
                inc1 = inc + .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                    y + (chgt * inc1))
                bb.append([x + (cwth * n2), y + (chgt * (4 * (aa + 1)))])
                x = rnds[rnd + 1][0]
                y = rnds[rnd + 1][1]
                drawField(self.getWinner(rd, grp, 0, rnd + 2),
                    x + (cwth * (l1 + l2)), y, w=(cwth * nm))
                inc1 -= 1
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                    y-(chgt * inc1))
            inc = inc * 2
            rnds = bb
        x = rnds[0][0]
        y = rnds[0][1]
        if self.rnds == 2:
            # Winner
            rd += 1
            if grp == 1:
                drawField(self.getWinner(rd, 2, 0, 1),
                    x + (cwth * (l1 + l2)), y, w=(cwth * nm))
        else:
            # Rest of Rounds and Winner
            rd += 1
            if self.rnds > 5:
                y += (chgt * 4)
            drawField(self.getWinner(rd, grp, 0, 1),
                x + (cwth * (l1 + l2)), y, w=(cwth * nm))
            if grp == 1:
                inc += .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                    y + (chgt * inc))
            else:
                rd += 1
                x1 = x + (cwth * (l1 + l2 + nm))
                y1 = y - (chgt * inc)
                drawField(self.getWinner(rd, grp, 0, 1),
                    x1 + (cwth * (l1 + l2)), y1, w=(cwth * nm))
                inc = 0 - inc + .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                    y + (chgt * inc))
        if grp == 1 and self.totskp > 32:
            self.fpdf.add_page()
            self.fpdf.drawText()
            self.fpdf.drawText()
        else:
            self.fpdf.set_y(lasty)
        self.fpdf.font[2] = ohgt

    def setBracketFont(self):
        if self.rnds == 2:
            siz = 14.1
            chgt = 12
        elif self.rnds == 3:
            siz = 10.6
            chgt = 12
        elif self.rnds == 4:
            siz = 8.4
            chgt = 6
        elif self.rnds == 5:
            siz = 7
            chgt = 3
        else:
            siz = 10
            chgt = 2.6
        self.fpdf.setFont(style="B", size=siz)
        cwth = self.fpdf.get_string_width("X")
        return siz, cwth, chgt

    def getWinner(self, rnd, grp, skip, num=0):
        if skip:
            whr = [
                ("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", rnd),
                ("bcg_group", "=", grp),
                ("bcg_scod", "=", skip[0])]
            wins = self.sql.getRec("bwlgme", cols=["bcg_sfor",
                "bcg_sagt"], where=whr, limit=1)
            if not wins[0] and not wins[1]:
                return ""
            elif wins[0] > wins[1]:
                return self.getSkip(skip[0], skip[2])
            else:
                return self.getSkip(skip[1], skip[2])
        col = [
            "bcg_scod",
            "bcg_ocod",
            "bcg_sfor",
            "bcg_sagt",
            "bcg_seed"]
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod),
            ("bcg_game", "=", rnd),
            ("bcg_group", "=", grp),
            ("bcg_pair", "=", num)]
        skip = self.sql.getRec("bwlgme", cols=col, where=whr, limit=1)
        if not skip:
            return ""
        if not skip or (not skip[2] and not skip[3]):
            return ""
        elif skip[2] > skip[3]:
            return self.getSkip(skip[0], skip[4])
        else:
            return self.getSkip(skip[1], skip[4])

    def getSkip(self, skip, seed):
        if skip > 900000:
            return "Bye"
        skp = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "=", skip)], limit=1)
        name = skp[0].strip()
        if skp[1]:
            name = "%s, %s" % (name, skp[1][0])
        if seed:
            name = "%s (%s)" % (name, seed)
        return name

    def drawLink(self, cwth, l1, l2, x, y, inc):
        self.fpdf.line(x, y, x + (cwth * l1), y)
        self.fpdf.line(x + (cwth * l1), y, x + (cwth * l1), inc)
        self.fpdf.line(x + (cwth * l1), inc, x + (cwth * (l1 + l2)), inc)

    def printGame(self):
        grp = [[0]]
        if self.cfmat in ("R", "W") or self.game > self.grgame:
            grp = self.sql.getRec("bwlgme", cols=["bcg_group"],
                where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod)], group="bcg_group",
                order="bcg_group")
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod),
            ("bcg_game", "=", self.game),
            ("btb_tab=bcg_scod",)]
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=65)
        self.fpdf.lpp = 60
        self.pglin = 999
        lastg = None
        for g in grp:
            where = copyList(whr)
            if self.game <= self.grgame:
                recs = self.sql.getRec(tables=["bwlgme", "bwltab"],
                    cols=["btb_tab", "btb_surname", "btb_names", "bcg_ocod",
                    "bcg_rink"], where=where, order="btb_surname, btb_names")
            else:
                w = copyList(whr[:3])
                w.append(("bcg_group", "=", g[0]))
                recs = self.sql.getRec(tables=["bwlgme"],
                    cols=["bcg_scod", "bcg_ocod", "bcg_rink"],
                    where=w)
                where.append(("bcg_group", "=", g[0]))
                recs = self.sql.getRec(tables=["bwlgme", "bwltab"],
                    cols=["btb_tab", "btb_surname", "btb_names", "bcg_ocod",
                    "bcg_rink"], where=where, order="btb_surname, btb_names")
            if len(recs) > 50:
                h = 4.4
            else:
                h = 4.7
            for skp in recs:
                if self.pglin > self.fpdf.lpp:
                    self.pageHeading()
                if g[0] != lastg:
                    if len(recs) > (self.fpdf.lpp - self.pglin - 3):
                        self.pageHeading()
                    self.groupHeading(g[0])
                    lastg = g[0]
                if self.cfmat in ("R", "W") and skp[3] > 900000:
                    opp = [skp[3], "** Bye **", ""]
                else:
                    opp = self.sql.getRec("bwltab", cols=["btb_tab",
                        "btb_surname", "btb_names"], where=[("btb_cono", "=",
                        self.opts["conum"]), ("btb_tab", "=", skp[3])],
                        limit=1)
                nam = skp[1].strip()
                if skp[2]:
                    nam = "%s, %s" % (nam, skp[2].split()[0])
                a = CCD(nam, "NA", 30)
                b = CCD(skp[4], "UA", 2)
                if opp:
                    nam = opp[1].strip()
                    if opp[2]:
                        nam = "%s, %s" % (nam, opp[2].split()[0])
                else:
                    nam = "Unknown"
                c = CCD(nam, "NA", 30)
                self.printLine(a.disp, " %s " % b.disp, c.disp, h)
                self.pglin += 1
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, "report", ext="pdf")
        if self.game in (1, 21, 31, 41, 51, 61, 71, 81, 91):
            desc = "%sst" % self.game
        elif self.game in (2, 22, 32, 42, 52, 62, 72, 82, 92):
            desc = "2nd"
        elif self.game in (3, 23, 33, 43, 53, 63, 73, 83, 93):
            desc = "3rd"
        else:
            desc = "%sth" % self.game
        head = "%s Draw for the %s game" % (self.cdes, desc)
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self, date=False):
        self.fpdf.add_page()
        head = "%s - %s" % (self.opts["conam"], self.cdes)
        self.fpdf.drawText(head, font=["courier", "B", 18], align="C")
        self.pglin = 1
        if not date:
            return
        siz, cwth, chgt = self.setBracketFont()
        self.fpdf.drawText()
        text = []
        for x in range(self.rnds):
            if self.comtyp == "V":
                text.append("Complete By\n%s" % self.cdates[x])
            elif self.cdates[x] == "9999-12-31":
                text.append("To Be\nAnnounced")
            else:
                if self.ctimes[x] <= "12:00":
                    txt = "%s AM" % self.ctimes[x]
                else:
                    txt = "%s PM" % self.ctimes[x]
                text.append("%s\n%s" % (self.cdates[x], txt))
        text.append("Competition\nWinner")
        x = self.fpdf.get_x()
        y = self.fpdf.get_y()
        for txt in text:
            self.fpdf.drawText(txt, x=x, y=y, w=(cwth * 18), border="TLRB",
                ln=0, fill=1, align="C", ctyp="M")
            x += (cwth * 19)
        self.fpdf.drawText()
        self.fpdf.drawText()

    def groupHeading(self, group):
        self.fpdf.drawText(font=["courier", "B", 18])
        head = "Draw for Game: %s" % self.game
        if group:
            if self.cfmat in ("R", "W"):
                head += "  Section: %s" % chr(64 + group)
            else:
                head += "  Group: %s" % chr(64 + group)
        head += "  Date: %s" % self.datd
        self.fpdf.drawText(head, font=["courier", "B", 18], align="C")
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.printLine("%-30s" % "Name", " RK ", "%-30s" % "Opposition",
            fill=1)
        self.fpdf.setFont()
        self.pglin += 4

    def printLine(self, a, b, c, h=0, fill=0):
        x = 10
        w = self.fpdf.get_string_width("X" * len(a)) + 1
        self.fpdf.drawText(a, x=x, h=h, w=w, border="TLB", fill=fill, ln=0)
        x += w + 1
        w = self.fpdf.get_string_width("X" * len(b)) + 1
        self.fpdf.drawText(b, x=x, h=h, w=w, border="TLB", fill=fill, ln=0)
        x += w + 1
        w = self.fpdf.get_string_width("X" * len(c)) + 1
        self.fpdf.drawText(c, x=x, h=h, w=w, border="TLRB", fill=fill)

    def printCards(self):
        recs = []
        if self.cfmat in ("R", "W"):
            skins = "N"
            sends = 0
        else:
            bwlpts = self.sql.getRec("bwlpts", where=[("bcp_cono",
                "=", self.opts["conum"]), ("bcp_code", "=", self.ctyp),
                ("bcp_ptyp", "=", self.gtyp)], limit=1)
            skins = bwlpts[self.sql.bwlpts_col.index("bcp_skins")]
            sends = bwlpts[self.sql.bwlpts_col.index("bcp_sends")]
        if self.allcards == "N":
            gme = getSingleRecords(self.opts["mf"], "bwlgme", ("bcg_rink",
                "bcg_scod", "bcg_ocod"), where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", self.game)], group="bcg_rink",
                order="bcg_rink")
            if not gme:
                return
            for g in gme:
                recs.append([g[2], g[6], g[7]])
        else:
            recs = self.sql.getRec("bwlgme", cols=["bcg_scod",
                "bcg_ocod", "bcg_rink"], where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", self.game)], order="bcg_rink")
        chk = []
        skips = []
        for rec in recs:
            if rec[0] in chk:
                continue
            if self.cfmat in ("R","W") and (rec[0] > 900000 or rec[1] > 900000):
                continue
            skp = self.sql.getRec("bwltab", cols=["btb_tab",
                "btb_surname", "btb_names"], where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", rec[0])], limit=1)
            opp = self.sql.getRec("bwltab", cols=["btb_tab",
                "btb_surname", "btb_names"], where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", rec[1])], limit=1)
            grn = rec[2]
            skips.append((grn, skp, opp))
            chk.extend([rec[0], rec[1]])
        pc = PrintCards(self.opts["mf"], self.opts["conum"], self.cdes,
            self.game, self.datd, skips, self.ends, skins, sends,
            args=self.args)
        if self.drawall:
            self.args = (pc.tname, pc.repprt)

    def printBoards(self):
        skps = []
        if self.allcards == "N":
            recs = getSingleRecords(self.opts["mf"], ["bwltab", "bwlgme"],
                ("btb_tab", "btb_surname", "btb_names"), where=[("btb_cono",
                "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "=", 1), ("bcg_cono=btb_cono",),
                ("bcg_scod=btb_tab",)], order="btb_tab")
            if not recs:
                return
            for rec in recs:
                skps.append(rec[1])
        else:
            recs = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
                "=", self.ccod), ("bcg_game", "=", 1)], order="bcg_scod")
            for rec in recs:
                skps.append(rec[0])
        PrintBoards(self.opts["mf"], self.opts["conum"], self.ccod,
            self.cdes, skps)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
