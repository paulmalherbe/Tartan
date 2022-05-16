"""
SYNOPSIS
    Bowls Tabs Draw.

    This file is part of Tartan Systems (TARTAN).

    Draw Parameters
    ---------------
    1) Enter type of draw i.e. random or strength v strength.
    2) Apply percentages i.e. increase or decrease player ratings by 10% if
       position is changed in the case of combined draws
    3) Apply history i.e. use historical data to determine draw.
    4) Enter preferred team size i.e. trips or fours.
    5) Select whether in trips to replace 4/4 with 2 x 2/2 (rep42).
    6) If format S (Not Mixed), Group tabs by gender, ratings else
                                Group tabs by ratings only.

    Singles
    -------
    pairs of teams = number of tabs / 2
    if remainder is 1 = remove a tab

    Pairs
    -----
    pairs of teams = number of tabs / 4
    if remainder is 1 = remove a tab
    if remainder is 2 = if rep31:
                            replace 1 pair with a 1/1
                        else:
                            replace 1 pair with a 3/3

    Trips
    -----
    pairs of teams = number of tabs / 6
    if remainder is 1 = replace 1 pair with a 4/3
    if remainder is 2 = if rep42:
                            replace 1 pair with a 2/2 and add a 2/2
                        else:
                            replace 1 pair with a 4/4
    if remainder is 3 = if pairs = 1:
                            replace 1 pair with a 4/3 and add a 1/1
                        elif rep42:
                            replace 2 pairs with a 4/3 and 2/2 and add a 2/2
                        else:
                            replace 2 pairs with a 4/3 and 4/4
    if remainder is 4 = 2/2
    if remainder is 5 = replace 1 pair with a 4/3 and add a 2/2

    Fours
    ------
    pairs of teams = number of tabs / 8
    if remainder is 1:
                        if pairs = 1:
                          replace 1 pair with a 4/3 and add a 1/1
                        elif pairs = 2:
                          replace 2 pairs with a 4/3 and 3/3 and add a 2/2
                        else:
                          replace 3 pairs with a 4/3 and 3 x 3/3
    if remainder is 2:
                        if no pairs:
                          1/1
                        if pairs = 1:
                          replace 1 pair with a 3/3 and add a 2/2
                        else:
                          replace 2 pairs with 2 x 3/3 and add a 3/3
    if remainder is 3:
                        if pairs = 1:
                          replace 1 pair with a 4/3 and add a 2/2
                        else:
                          replace 2 pairs with a 4/3 and a 3/3 and add a 3/3
    if remainder is 4:
                        if no pairs:
                          2/2
                        else:
                          replace 1 pair with 2 x 3/3
    if remainder is 5 = replace 1 pair with a 4/3 and add a 3/3
    if remainder is 6 = 3/3
    if remainder is 7 = 4/3

    Selection Criteria
    ------------------
    1) Determine number of teams and odds i.e. 4/3 or pairs etc.
    2) Determine number of skips, thirds, seconds and leads required.
    3) Select skips for number of teams using all players, by position,
       randomly or by strength.
    4) Select thirds for number of teams using remainder of players, by
       position, randomly or by strength. Skip if 3/3 or 2/2 or ?/3
    5) Select self.seconds for number of teams using remainder of players,
       by position, randomly or by strength. Skip if 2/2 and 1/1.
    6) Select self.leads for number of teams using remainder of all players,
       by position, randomly or by strength. Skip if 1/1.

    Variables:
    ----------
    self.alltabs: {"tab": [surname, names, gender, position, rating, paid]}
    self.adraw1: [[rink, rate, [tab, nam, rte] x 4], []]
    self.dtype: Draw Type S - Strength, R - Randon
    self.hist: Dictionary of all tabs for the past x weeks as follows:
        {tab: [[team members], [opponents]], ...}
    self.tsize = Team Size: Three or Four
    self.dbase: Draw Basis P - Position, R - Rating, C - Combination
    self.broken: list of tabs that have been in a broken rink
                 or in the case of teams True or False
    bdt_flag: A - Arranged, B - Broken Rinks, C - Teams, D - Drawn
    self.dofix: In single gender draws fix broken teams by moving 1 player

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

import random, time
from operator import itemgetter
from TartanClasses import CCD, GetCtl, PrintCards, PrintDraw, PwdConfirm
from TartanClasses import SplashScreen, SelectChoice, Sql, TartanDialog
from tartanFunctions import askChoice, askQuestion, callModule, getGreens
from tartanFunctions import getNextCode, copyList, projectDate, showError

class bc2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwltab", "bwldrm", "bwldrt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.mlint = bwlctl["ctb_mlint"]
        self.samen = bwlctl["ctb_samen"]
        self.dsize = bwlctl["ctb_tsize"]
        self.rep42 = bwlctl["ctb_rep42"]
        self.weeks = bwlctl["ctb_weeks"]
        self.nstart = bwlctl["ctb_nstart"]
        self.dbase = bwlctl["ctb_dbase"]
        self.order = bwlctl["ctb_order"]
        self.mixed = bwlctl["ctb_mixed"]
        self.ratem = CCD(bwlctl["ctb_ratem"], "UD", 6.2)
        self.ratev = CCD(bwlctl["ctb_ratev"], "UD", 6.2)
        self.greens = bwlctl["ctb_greens"]
        t = time.localtime()
        self.sysdt = ((t[0] * 10000) + (t[1] * 100) + t[2])
        if t[3] >= 12:
            self.stime = "A"
        else:
            self.stime = "M"
        self.alltabs = {}
        random.seed()
        return True

    def mainProcess(self):
        r1s = (("Morning", "M"), ("Afternoon", "A"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Position", "P"), ("Rating", "R"), ("Combination", "C"))
        fld = (
            (("T",0,0,0),"ID1",10,"Date","",
                self.sysdt,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Time","",
                self.stime,"N",self.doTime,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Mixed Gender","",
                "Y","N",self.doMixed,None,None,None,None,"Select whether "\
                "the Draw is Gender based or Mixed."),
            (("T",0,3,0),("IRB",r2s),0,"Mixed Rating","",
                self.mixed,"N",self.doMixedRating,None,None,None,None,"If "\
                "available, Select whether or not to use the Alternative "\
                "Gender Ratings."),
            (("T",0,4,0),("IRB",r2s),0,"Fix Odd Numbers","",
                "Y","N",self.doFixOdd,None,None,None,None,"If Both "\
                "Genders have an Odd number of tabs, move a Random "\
                "Tab to Equalize the Numbers."),
            (("T",0,5,0),("IRB",r3s),0,"Draw By","",
                self.dbase,"N",self.doBase,None,None,None,None,"Select "\
                "whether to base the Draw on Positions, Ratings or a "\
                "Combination of Both."),
            (("T",0,6,0),"IUD",5.2,"Fees - Member R","",
                self.ratem.work,"N",self.doRate,None,None,("efld",)),
            (("T",0,6,0),"IUD",5.2," Visitor R","",
                self.ratev.work,"N",self.doRate,None,None,("efld",)))
        tnd = ((self.doMEnd,"y"),)
        txt = (self.doMExit,)
        # Set font as big as possible up to 24pts
        self.dfs = self.opts["mf"].rcdic["dfs"]
        if self.dfs < 24:
            self.doSetFont()
        self.nfs = self.opts["mf"].rcdic["dfs"]
        # Create dialog
        self.mf = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, eframe=True)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.dated = CCD(w, "D1", 10).disp
        self.teams = {}
        self.bounce = {}
        self.alltabs = {}
        self.drawn = False
        self.saved = False
        self.viewer = False
        self.reprint = False
        self.lasttab = self.nstart - 1
        self.position = ["Skip", "Third", "Second", "Lead"]

    def doTime(self, frt, pag, r, c, p, i, w):
        self.time = w
        self.alter = False
        if self.time == "A":
            self.timed = "Afternoon"
        else:
            self.timed = "Morning"
        self.drm = self.sql.getRec("bwldrm", where=[("bdm_cono", "=",
            self.opts["conum"]), ("bdm_date", "=", self.date), ("bdm_time",
            "=", self.time)], limit=1)
        if self.drm:
            state = self.mf.disableButtonsTags()
            self.mf.setWidget(self.mf.mstFrame, state="hide")
            butt = [("None", "N"), ("View", "V"), ("Reprint", "R")]
            dtyp = self.drm[self.sql.bwldrm_col.index("bdm_dtype")]
            dnxt = self.sql.getRec("bwldrm", where=[("bdm_cono", "=",
                self.opts["conum"]), ("bdm_date", ">", self.date)],
                limit=1)
            if dtyp == "N" or not dnxt:
                butt.extend([("Alter", "A"), ("Delete", "X")])
                text = "Would you like to View, Reprint, Alter or "\
                    "Delete the Draw?"
            else:
                text = "Would you like to View or Reprint It?"
            ok = askChoice(self.opts["mf"].body, "Already Exists",
                "A Draw or Entries for this Date and Time Already "\
                "Exists.\n\n%s" % text, butt=butt, default="None")
            self.mf.setWidget(self.mf.mstFrame, state="show")
            self.mf.enableButtonsTags(state=state)
            if ok == "N":
                return "ff1"
            elif ok == "V":
                self.viewer = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
                self.drawn = True
                return "nc"
            elif ok == "R":
                self.reprint = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
                self.drawn = True
                return "nc"
            elif ok == "A":
                self.alter = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
            elif ok == "X":
                self.sql.delRec("bwldrm", where=[("bdm_cono", "=",
                    self.opts["conum"]), ("bdm_date", "=", self.date),
                    ("bdm_time", "=", self.time)])
                self.sql.delRec("bwldrt", where=[("bdt_cono", "=",
                    self.opts["conum"]), ("bdt_date", "=", self.date),
                    ("bdt_time", "=", self.time)])
                self.opts["mf"].dbm.commitDbase()
                return "ff1"

    def doLoadMst(self, drm):
        self.mixgd = drm[self.sql.bwldrm_col.index("bdm_mixed")]
        self.mf.loadEntry("T", 0, 2, data=self.mixgd)
        self.mixrt = drm[self.sql.bwldrm_col.index("bdm_rating")]
        self.mf.loadEntry("T", 0, 3, data=self.mixrt)
        self.nbase = drm[self.sql.bwldrm_col.index("bdm_dbase")]
        self.mf.loadEntry("T", 0, 5, data=self.nbase)
        self.dtype = drm[self.sql.bwldrm_col.index("bdm_dtype")]
        self.dhist = drm[self.sql.bwldrm_col.index("bdm_dhist")]
        self.tsize = drm[self.sql.bwldrm_col.index("bdm_tsize")]
        self.mrate = drm[self.sql.bwldrm_col.index("bdm_mrate")]
        self.mf.loadEntry("T", 0, 6, data=self.mrate)
        self.vrate = drm[self.sql.bwldrm_col.index("bdm_vrate")]
        self.mf.loadEntry("T", 0, 7, data=self.vrate)

    def doLoadTabs(self):
        draws = self.sql.getRec("bwldrt", cols=["bdt_tab",
            "bdt_name", "bdt_rink", "bdt_side", "bdt_pos", "bdt_rate",
            "bdt_pos1", "bdt_team1", "bdt_flag"], where=[("bdt_cono",
            "=", self.opts["conum"]), ("bdt_date", "=", self.date),
            ("bdt_time", "=", self.time)], order="bdt_rink, bdt_side")
        rnk = {}
        self.teams = {}
        self.bounce = {}
        self.adraw1 = []
        if draws[0][8] == "D":
            self.drawn = True
        pos = [0, 3, 2, 1, 0]
        for draw in draws:
            tab = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names", "btb_gender", "btb_pos1", "btb_rate1",
                "btb_pos2", "btb_rate2"], where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", draw[0])],
                limit=1)
            if tab:
                if self.alter:
                    if self.mixrt == "N":
                        p, r = tab[3:5]
                    else:
                        p, r = tab[5:]
                else:
                    p, r = draw[4:6]
                self.alltabs[draw[0]] = [tab[0], tab[1], tab[2], p, r, "Y"]
                if not draw[2]:
                    continue
            else:
                showError(self.opts["mf"].body, "Missing Tab",
                    "Tab Number %s is Not in the Database" % draw[0])
                self.doExit()
            if draw[2] not in rnk:
                rnk[draw[2]] = {}
            if draw[3] not in rnk[draw[2]]:
                rnk[draw[2]][draw[3]] = [0, [0,""], [0,""], [0,""], [0,""]]
            rnk[draw[2]][draw[3]][0] += draw[5]
            rnk[draw[2]][draw[3]][pos[draw[4]] + 1] = [draw[0], draw[1], r]
            if draw[8] == "A":
                # Bounce games
                if draw[2] not in self.bounce:
                    self.bounce[draw[2]] = {"L":[0,0,0,0], "R":[0,0,0,0]}
                if draw[4] == 4:
                    self.bounce[draw[2]][draw[3]][0] = draw[0]
                elif draw[4] == 3:
                    self.bounce[draw[2]][draw[3]][1] = draw[0]
                elif draw[4] == 2:
                    self.bounce[draw[2]][draw[3]][2] = draw[0]
                else:
                    self.bounce[draw[2]][draw[3]][3] = draw[0]
            elif draw[8] == "C":
                # Arranged teams
                if draw[4] == 4:
                    skp = draw[0]
                else:
                    skp = draw[7]
                if skp not in self.teams:
                    self.teams[skp] = [0,0,0,0]
                if draw[4] == 4:
                    self.teams[skp][0] = draw[0]
                elif draw[4] == 3:
                    self.teams[skp][1] = draw[0]
                elif draw[4] == 2:
                    self.teams[skp][2] = draw[0]
                else:
                    self.teams[skp][3] = draw[0]
        for r in rnk:
            for s in rnk[r]:
                self.adraw1.append([r, rnk[r][s][0]] + rnk[r][s][1:])
        self.tot = 0
        self.adraw1.sort()
        for x in range(0, len(self.adraw1), 2):
            self.doAverage(self.adraw1[x], self.adraw1[x + 1])

    def doMixed(self, frt, pag, r, c, p, i, w):
        self.mixgd = w
        if self.mixgd == "N" or self.mixed == "N":
            self.mixrt = "N"
            self.mf.loadEntry(frt, pag, p + 1, data=self.mixrt)
            if self.mixgd == "Y":
                self.dofix = "N"
                self.mf.loadEntry(frt, pag, p + 2, data=self.dofix)
                return "sk2"
            return "sk1"

    def doMixedRating(self, frt, pag, r, c, p, i, w):
        self.mixrt = w
        self.dofix = False
        self.mf.loadEntry(frt, pag, p + 1, data="N")
        if self.dbase == "C":
            return "sk1"
        self.nbase = self.dbase
        self.mf.loadEntry(frt, pag, p + 2, data=self.dbase)
        return "sk2"

    def doFixOdd(self, frt, pag, r, c, p, i, w):
        if w == "Y":
            self.dofix = True
        else:
            self.dofix = False
        if self.dbase != "C":
            self.nbase = self.dbase
            self.mf.loadEntry(frt, pag, p + 1, data=self.dbase)
            return "sk1"

    def doBase(self, frt, pag, r, c, p, i, w):
        if w != self.dbase:
            if self.dbase == "P":
                base = "Position"
            elif self.dbase == "R":
                base = "Rating"
            else:
                base = "Combination"
            ok = askQuestion(self.opts["mf"].body, "Override Default",
                "Are You Sure the  Default Base\n\n%s\n\nMust be Overridden?" %
                base, default="no")
            if ok == "no":
                return "rf"
        self.nbase = w

    def doRate(self, frt, pag, r, c, p, i, w):
        if p == 6:
            self.ratem = CCD(w, "UD", 6.2)
        else:
            self.ratev = CCD(w, "UD", 6.2)

    def doMEnd(self):
        if self.viewer:
            self.doShowDraw("Current Draw", self.adraw1)
            self.mf.focusField("T", 0, 1)
        elif self.reprint:
            self.doPrint(self.mf)
            self.mf.focusField("T", 0, 1)
        else:
            self.mf.closeProcess()
            self.doTabs()

    def doMExit(self):
        self.mf.closeProcess()
        self.opts["mf"].closeLoop()

    def doTabs(self):
        if self.mixgd == "Y":
            tit = "Mixed Draw for the %s of %s" % (self.timed, self.dated)
        else:
            tit = "Gender Draw for the %s of %s" % (self.timed, self.dated)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        v1 = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_tab", "", 0, "Tab")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", ">=", self.nstart)],
            "order": "btb_surname, btb_names"}
        v2 = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_names", "", 0, "Names"),
                ("btb_tab", "", 0, "Tab")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", ">=", self.nstart)],
            "whera": [("T", "btb_surname", 1, 1)],
            "order": "btb_names"}
        r2s = (("Yes", "Y"), ("No", "N"))
        r4s = (("Male", "M"), ("Female", "F"))
        r5s = (("Skip", "4"), ("Third", "3"), ("Second", "2"), ("Lead", "1"))
        tag = (("", None, None, None, False),)
        if self.nbase in ("C", "R"):
            vfy = ("notzero",)
        else:
            vfy = ("efld",)
        fld = (
            (("T",0,0,0),"OUI",3,"Entered: Total"),
            (("T",0,0,0),"OUI",3," Males"),
            (("T",0,0,0),"OUI",3," Females"),
            (("T",1,0,0),"I@btb_tab",0,"","Tab Number(noesc)",
                "","Y",self.doTab,mem,None,("efld",)),
            (("T",1,1,0),"I@btb_surname",0,"","",
                "","N",self.doSurname,v1,None,("notblank",)),
            (("T",1,2,0),"I@btb_names",0,"","",
                "","N",self.doNames,v2,None,("efld",)),
            (("T",1,3,0),("IRB",r4s),0,"Gender","",
                "M","N",self.doGender,None,None,None),
            (("T",1,4,0),("IRB",r5s),0,"Position","",
                "2","N",self.doPosition,None,None,None),
            (("T",1,5,0),"IUI",2,"Rating","",
                0,"N",None,None,None,vfy),
            (("T",1,6,0),("IRB",r2s),0,"Paid","",
                "Y","N",None,None,self.doDelete,None))
        but = (
            ("Bounce",None,self.doBounce,0,("T",1,1),None,
                "Enter Bounce Games",1),
            ("Teams",None,self.doTeams,0,("T",1,1),None,
                "Enter Arranged Teams",1),
            ("Entered",None,self.doEntered,0,("T",1,1),None,
                "Display a list of Entered Tabs",1),
            ("Modify",None,self.doModify,0,("T",1,7),None,
                "Change the Position and/or Rating for this "\
                "Tab for this Draw Only",1),
            ("Do Draw",None,self.doDraw,0,("T",1,1),None,
                "Genetrate a New Draw",2),
            ("View/Edit",None,self.doEdit,0,("T",1,1),None,
                "View and/or Change the Draw",2),
            ("Print",None,self.doPrint,0,("T",1,1),None,
                "Print the Draw",2),
            ("Exit",None,self.doExit,1,None,None,None,2))
        tnd = (None, (self.doEnd,"n"))
        txt = (None, self.doExit)
        # Create dialog
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit,
            tags=tag, eflds=fld, butt=but, tend=tnd, txit=txt, eframe=True)
        if self.alter:
            for b in range(4, 7):
                wid = getattr(self.df, "B%i" % b)
                self.df.setWidget(wid, "normal")
        else:
            self.alltabs = {}
        self.doShowQuantity()
        self.df.focusField("T", 1, 1)

    def doTab(self, frt, pag, r, c, p, i, w):
        self.modify = False
        self.visitor = False
        if w == 999999:
            self.doTestDraw()
            return "rf"
        elif w > 999900:
            self.doTestTabs(w % 100)
            return "rf"
        elif not w:
            yn = askQuestion(self.opts["mf"].body, "Missing Tab",
                "Is This a Visitor?", default="no")
            if yn == "yes":
                self.visitor = True
                self.tab = getNextCode(self.sql, "bwltab", "btb_tab",
                    where=[("btb_cono", "=", self.opts["conum"])],
                    start=self.nstart, last=899999)
                self.df.loadEntry(frt, pag, p, data=self.tab)
            else:
                return "rf"
        elif not self.doLoadTab(w, frt):
            return "Invalid Tab Number"
        elif self.nbase in ("C", "P") and not self.df.t_work[1][0][p + 4]:
            self.df.loadEntry(frt, pag, p + 4, data="1")
            return "sk3"
        elif self.nbase in ("C", "R") and not self.df.t_work[1][0][p + 5]:
            self.df.loadEntry(frt, pag, p + 5, data=1)
            if self.nbase == "C":
                return "sk3"
            else:
                return "sk4"
        else:
            return "sk5"

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwltab", cols=["btb_tab", ],
            where=[("btb_cono", "=", self.opts["conum"]), ("btb_surname",
            "ilike", self.sname, "and", "btb_names", "ilike", w),
            ("btb_tab", ">=", self.nstart)], order="btb_tab", limit=1)
        if chk:
            self.df.loadEntry(frt, pag, 0, data=chk[0])
            self.doLoadTab(chk[0], frt)
            self.visitor = False
            return "sk3"

    def doGender(self, frt, pag, r, c, p, i, w):
        if self.nbase == "R":
            self.df.loadEntry(frt, pag, p + 1, data="")
            return "sk1"

    def doPosition(self, frt, pag, r, c, p, i, w):
        if self.nbase == "P":
            self.df.loadEntry(frt, pag, p + 1, data="")
            return "sk1"

    def doEntered(self):
        data = []
        for tab in self.alltabs:
            data.append([tab] + self.alltabs[tab])
        data.sort()
        titl = "List of All Entered Tabs"
        head = ("Tab", "Surname", "Names", "G", "P", "RT", "P")
        line = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": [("UI", 3), ("NA", 20, "Y"), ("NA", 20),
                ("UA", 1), ("UI", 1), ("UI", 2), ("UA", 1)],
            "data": data,
            "sort": True}
        self.opts["mf"].updateStatus("")
        state = self.df.disableButtonsTags()
        show = self.df.selChoice(line)
        self.df.enableButtonsTags(state=state)
        if self.saved:
            self.df.focusField("T", 1, 1)
            return
        if show.selection:
            self.modify = False
            self.visitor = False
            self.df.loadEntry("T", 1, 0, data=show.selection[0])
            self.doLoadTab(show.selection[0], "T")
            self.df.focusField("T", 1, 7)
        else:
            self.df.focusField("T", 1, 1)

    def doLoadTab(self, tab, form="T", err=True):
        c = self.sql.bwltab_col
        acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
        if not acc and not err:
            return
        elif not acc and tab >= self.nstart:
            showError(self.opts["mf"].body, "Visitor's Tab",
                "This Tab Number is Reserved for Visitors")
            return
        elif not acc and self.mlint == "Y" and self.samen == "Y":
            return
        elif not acc:
            ok = askQuestion(self.opts["mf"].body, "Missing Tab",
                "This Tab Does Not Exist, Is It a New Member?", default="no")
            if ok == "no":
                return
            callModule(self.opts["mf"], self.df, "bc1010",
                coy=[self.opts["conum"], self.opts["conam"]], args=tab)
            acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
            if not acc:
                return
            self.df.loadEntry("T", 1, 0, data=tab)
        if not err and self.nbase != "P" and not acc[c.index("btb_rate1")]:
            return
        snam = acc[c.index("btb_surname")]
        fnam = acc[c.index("btb_names")]
        gend = acc[c.index("btb_gender")]
        if self.mixgd == "Y" and self.mixrt == "Y" and gend == "F":
            pos = str(acc[c.index("btb_pos2")])
            rte = str(acc[c.index("btb_rate2")])
        else:
            pos = str(acc[c.index("btb_pos1")])
            rte = str(acc[c.index("btb_rate1")])
        if form == "T":
            self.tab = int(tab)
            self.df.loadEntry("T", 1, 1, data=snam)
            self.df.loadEntry("T", 1, 2, data=fnam)
            self.df.loadEntry("T", 1, 3, data=gend)
            self.df.loadEntry("T",1,4, data=pos)
            self.df.loadEntry("T",1,5, data=rte)
        else:
            if fnam:
                name = snam.upper() + ", " + fnam[0][0].upper()
            else:
                name = snam.upper()
            if form == "A":
                self.at.loadEntry("C", 0, self.at.pos + 1, data=name)
            elif form == "B":
                self.bg.loadEntry("C", 0, self.bg.pos + 1, data=name)
            elif form == "C":
                return name
            else:
                return [name, pos, rte]
        return True

    def doDelete(self):
        if self.bounce:
            for rink in self.bounce:
                for team in self.bounce[rink]:
                    for tab in self.bounce[rink][team]:
                        if tab and tab == self.tab:
                            showError(self.opts["mf"].body, "Error",
                                """This Tab is in a Bounce Game,

First Change the Bounce Game and then Delete It.""")
                            self.df.clearFrame("T", 1)
                            return ("T", 1, 1)
        if self.tab in self.alltabs:
            del self.alltabs[self.tab]
            self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)
        return ("T", 1, 1)

    def doModify(self):
        state = self.df.disableButtonsTags()
        cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
            system="BWL", code="Modify")
        self.df.enableButtonsTags(state=state)
        if cf.flag == "no":
            self.df.focusField("T", 1, 7)
        else:
            self.modify = True
            if self.nbase in ("C", "P"):
                self.df.focusField("T", 1, 5)
            else:
                self.df.focusField("T", 1, 6)

    def doEnd(self):
        if self.df.pag == 0:
            return
        else:
            if not self.df.t_work[1][0][4]:
                self.df.t_work[1][0][4] = 0
            else:
                self.df.t_work[1][0][4] = int(self.df.t_work[1][0][4])
            if self.tab in self.alltabs:
                del self.alltabs[self.tab]
            self.alltabs[self.tab] = self.df.t_work[1][0][1:]
            if self.visitor:
                data = [self.opts["conum"], self.df.t_work[1][0][0], 0]
                data.extend(self.df.t_work[1][0][1:4])
                data.extend(["", "", "", "", "", "", "", ""])
                data.extend(self.df.t_work[1][0][4:6])
                data.extend(self.df.t_work[1][0][4:6])
                data.append(0)
                self.sql.insRec("bwltab", data=data)
                self.lasttab += 1
            self.drawn = False
            self.doShowQuantity()
            self.df.clearFrame("T", 1)
            self.df.focusField("T", 1, 1)

    def doBounce(self):
        if self.drawn:
            yn = askQuestion(self.opts["mf"].body, "Drawn",
                "This Draw has Already Been Done, Do You Want to Re-Draw?",
                default="no")
            if yn == "no":
                return
        self.drawn = False
        tit = ("Bounce Games",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        fld = (
            (("C",0,0,0),"IUA",2,"RK","Rink",
                "","N",self.doBRnk,None,None,("notblank",)),
            (("C",0,0,1),"OUA",1,"T"),
            (("C",0,0,2),"IUI",3,"Skp","Skip",
                "","N",self.doBTab,mem,None,None),
            (("C",0,1,3),"OUA",15,"Name"),
            (("C",0,1,4),"IUI",3,"3rd","Third",
                "","N",self.doBTab,mem,None,None),
            (("C",0,1,5),"OUA",15,"Name"),
            (("C",0,1,6),"IUI",3,"2nd","Second",
                "","N",self.doBTab,mem,None,None),
            (("C",0,1,7),"OUA",15,"Name"),
            (("C",0,1,8),"IUI",3,"1st","Lead",
                "","N",self.doBTab,mem,None,None),
            (("C",0,1,9),"OUA",15,"Name"))
        but = (
            ("Show",None,self.doBShow,1,None,None,None,1),
            ("Close",None,self.doBExit,1,None,None,None,1))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.bg = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, butt=but, cend=((self.doBEnd,"y"),),
            cxit=(self.doBExit,), rows=[18])
        self.loadBounce()
        self.bg.mstFrame.wait_window()
        self.df.enableButtonsTags(state)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doBRnk(self, frt, pag, r, c, p, i, w):
        if len(w) != 2:
            return "Invalid Green/Rink"
        if w[0] not in self.greens:
            return "Invalid Green"
        try:
            rnk = int(w[1])
        except:
            rnk = 0
        if rnk < 1 or rnk > 7:
            return "Invalid Rink"
        if w in self.bounce:
            but = [
                ("Amend", "A"),
                ("Replace", "R"),
                ("None", "N")]
            txt = "This Rink Has Already Been Used, Amend or Replace?"
            ok = askChoice(self.opts["mf"].body, "Rink Used",
                mess=txt, butt=but, default="None")
            if ok == "A":
                old = copyList(self.bounce)
                self.doBDel(w)
                pos = self.bg.pos
                self.bg.loadEntry(frt, pag, pos, data=w)
                self.bg.loadEntry(frt, pag, pos+1, data="L")
                for num, tab in enumerate(old[w]["L"]):
                    if not tab:
                        continue
                    nam = self.doLoadTab(tab, "C")
                    self.bg.loadEntry(frt, pag, pos+2+(num * 2), data=tab)
                    self.bg.loadEntry(frt, pag, pos+3+(num * 2), data=nam)
                self.bg.loadEntry(frt, pag, pos+11, data="R")
                for num, tab in enumerate(old[w]["R"]):
                    if not tab:
                        continue
                    nam = self.doLoadTab(tab, "C")
                    self.bg.loadEntry(frt, pag, pos+12+(num * 2), data=tab)
                    self.bg.loadEntry(frt, pag, pos+13+(num * 2), data=nam)
                self.bg.colf[0][2][4] += "(noesc)"
            elif ok == "R":
                self.doBDel(w)
                self.bg.loadEntry(frt, pag, self.bg.pos, data=w)
            else:
                return "Duplicate Rink"
        self.rink = w
        self.team = "L"
        self.bg.loadEntry(frt, pag, self.bg.pos + 1, data=self.team)

    def doBDel(self, rnk):
        if rnk in self.bounce:
            del self.bounce[rnk]
        self.loadBounce()

    def doBTab(self, frt, pag, r, c, p, i, w):
        if not w:
            self.bg.loadEntry(frt, pag, p + 1, data="")
            if i == 2:
                return "Missing Skip Number"
        if w and not self.doLoadTab(w, "B"):
            return "Invalid Tab"
        if w:
            err = self.doCheckTab(w)
            if err:
                return err

    def loadBounce(self):
        self.bg.clearFrame("C", 0)
        if self.bounce:
            pos = 0
            for self.rink in self.bounce:
                self.bg.loadEntry("C", 0, pos, data=self.rink)
                pos += 1
                for self.team in ("L", "R"):
                    if self.team == "R":
                        pos += 1
                    self.bg.loadEntry("C", 0, pos, data=self.team)
                    pos += 1
                    for mem in self.bounce[self.rink][self.team]:
                        if mem:
                            self.bg.focusField("C", 0, pos + 1)
                            self.bg.loadEntry("C", 0, pos, data=mem)
                            self.doLoadTab(mem, "B")
                        pos += 2
                    self.bg.advanceLine(0)
                    pos = self.bg.pos
            self.bg.focusField("C", 0, self.bg.col)
        else:
            self.bg.focusField("C", 0, 1)

    def doBEnd(self):
        if self.rink not in self.bounce:
            self.bounce[self.rink] = {}
        self.bounce[self.rink][self.team] = []
        for x in range(2, len(self.bg.c_work[0][self.bg.row]), 2):
            mem = self.bg.c_work[0][self.bg.row][x]
            self.bounce[self.rink][self.team].append(mem)
            if mem and mem not in self.alltabs:
                acc = self.sql.getRec("bwltab", cols=["btb_surname",
                    "btb_names", "btb_gender", "btb_pos1", "btb_rate1"],
                    where=[("btb_cono", "=", self.opts["conum"]), ("btb_tab",
                    "=", mem)], limit=1)
                self.alltabs[mem] = acc + ["Y"]
        self.bg.advanceLine(0)
        if self.team == "L":
            self.team = "R"
            self.bg.colf[0][2][4] += "(noesc)"
            self.bg.loadEntry("C", 0, self.bg.pos + 1, data=self.team)
            self.bg.focusField("C", 0, self.bg.col + 2)
        else:
            self.bg.colf[0][2][4] = self.bg.colf[0][2][4].replace("(noesc)", "")
        self.drawn = False
        self.doShowQuantity()

    def doBShow(self):
        if not self.bounce:
            return
        draw = []
        for rnk in self.bounce:
            for sde in self.bounce[rnk]:
                dat = [rnk, 0]
                for tab in self.bounce[rnk][sde]:
                    if not tab:
                        dat.append([0, ""])
                    else:
                        dat.append([tab, "%s, %s" % (self.alltabs[tab][0],
                            self.alltabs[tab][1][0])])
                draw.append(dat)
        self.doShowDraw("Bounce Games", draw)
        self.df.setWidget(self.df.mstFrame, state="hide")

    def doBExit(self):
        for rink in self.bounce:
            if "R" not in self.bounce[rink]:
                del self.bounce[rink]
                break
        self.bg.closeProcess()
        self.df.focusField("T", 1, 1)

    def doTeams(self):
        if self.drawn:
            yn = askQuestion(self.opts["mf"].body, "Drawn",
                "This Draw has Already Been Done, Do You Want to Re-Draw?",
                default="no")
            if yn == "no":
                return
        self.drawn = False
        tit = ("Arranged Teams",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IUI",1,"Team Size","",
                3,"Y",self.doTSiz,None,None,("between",2,4)),
            (("T",0,0,0),("IRB",r1s),0,"Prefer Pairs","",
                "Y","N",self.doTR42,None,None,None,None,
                "In the case of Trips select whether to Replace "\
                "teams of Four with Pairs."),
            (("C",0,0,2),"IUI",3,"Skp","Skip",
                "","N",self.doTTab,mem,None,("notzero",)),
            (("C",0,1,3),"OUA",15,"Name"),
            (("C",0,1,4),"IUI",3,"3rd","Third",
                "","N",self.doTTab,mem,None,None),
            (("C",0,1,5),"OUA",15,"Name"),
            (("C",0,1,6),"IUI",3,"2nd","Second",
                "","N",self.doTTab,mem,None,None),
            (("C",0,1,7),"OUA",15,"Name"),
            (("C",0,1,8),"IUI",3,"1st","Lead",
                "","N",self.doTTab,mem,None,None),
            (("C",0,1,9),"OUA",15,"Name"))
        but = (
            ("Show",None,self.doTShow,1,None,None,None,1),
            ("Close",None,self.doTExit,1,None,None,None,1))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.at = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, butt=but, tend=((self.doTEnd,"y"),),
            txit=(self.doTExit,), cend=((self.doTEnd,"y"),),
            cxit=(self.doTExit,), rows=[18])
        self.at.mstFrame.wait_window()
        self.df.enableButtonsTags(state)
        self.df.setWidget(self.df.mstFrame, state="show")

    def doTSiz(self, frt, pag, r, c, p, i, w):
        self.tsize = w
        if self.tsize == 4:
            self.rep42 = "N"
            self.at.loadEntry(frt, pag, p + 1, data=self.rep42)
            return "sk1"

    def doTR42(self, frt, pag, r, c, p, i, w):
        self.rep42 = w

    def doTTab(self, frt, pag, r, c, p, i, w):
        if not w:
            self.at.loadEntry(frt, pag, p + 1, data="")
            if i == 0:
                return "Missing Skip Number"
        if w and not self.doLoadTab(w, "A"):
            return "Invalid Tab"
        if i == 0:
            if w in self.teams:
                but = [
                    ("Amend", "A"),
                    ("Replace", "R"),
                    ("None", "N")]
                txt = "This Team Already Exists, Amend or Replace?"
                ok = askChoice(self.opts["mf"].body, "Team Exists",
                    mess=txt, butt=but, default="None")
                if ok == "A":
                    old = copyList(self.teams)
                    self.doTDel(w)
                    pos = self.at.pos
                    for num, tab in enumerate(old[w]):
                        if not tab:
                            continue
                        nam = self.doLoadTab(tab, "C")
                        self.at.loadEntry(frt, pag, pos+(num * 2), data=tab)
                        self.at.loadEntry(frt, pag, pos+1+(num * 2), data=nam)
                    self.at.focusField(frt, pag, pos + 1)
                elif ok == "R":
                    self.doTDel(w)
                    return "rf"
                else:
                    return "Duplicate Team"
            self.tskip = w
        if w:
            err = self.doCheckTab(w)
            if err:
                return err

    def doTDel(self, tab):
        if tab in self.teams:
            del self.teams[tab]
        self.loadTeams()

    def loadTeams(self):
        self.at.clearFrame("C", 0)
        if self.teams:
            pos = 0
            for self.tskip in self.teams:
                for mem in self.teams[self.tskip]:
                    self.at.focusField("C", 0, pos + 1)
                    self.at.loadEntry("C", 0, pos, data=mem)
                    self.doLoadTab(mem, "A", err=False)
                    pos += 2
                self.at.advanceLine(0)
                pos = self.at.pos
            self.at.focusField("C", 0, self.at.col)
        else:
            self.at.focusField("C", 0, 1)

    def doTEnd(self):
        if self.at.frt == "T":
            self.loadTeams()
        else:
            team = []
            for x in range(0, len(self.at.c_work[0][self.at.row]), 2):
                mem = self.at.c_work[0][self.at.row][x]
                team.append(mem)
                if mem and mem not in self.alltabs:
                    acc = self.sql.getRec("bwltab", cols=["btb_surname",
                        "btb_names", "btb_gender", "btb_pos1", "btb_rate1"],
                        where=[("btb_cono", "=", self.opts["conum"]),
                        ("btb_tab", "=", mem)], limit=1)
                    self.alltabs[mem] = acc + ["Y"]
            if team[2] and not team[3]:
                team[3] = team[2]
                team[2] = 0
            if team[1] and not team[2]:
                team[2] = team[1]
                team[1] = 0
            self.teams[self.tskip] = team
            self.loadTeams()
            self.drawn = False
            self.doShowQuantity()

    def doTShow(self):
        if not self.teams:
            return
        draw = []
        for skp in self.teams:
            dat = []
            for tab in self.teams[skp]:
                if not tab:
                    dat.append([0, ""])
                else:
                    dat.append([tab, "%s, %s" % (self.alltabs[tab][0],
                        self.alltabs[tab][1][0])])
            draw.append(dat)
        self.doShowTeams("Arranged Teams", draw)
        self.df.setWidget(self.df.mstFrame, state="hide")

    def doShowTeams(self, title, draw):
        cols = (
            ("skip", "Skip", 24, "UA", "N"),
            ("third", "Third", 24, "UA", "N"),
            ("second", "Second", 24, "UA", "N"),
            ("lead", "Lead", 24, "UA", "N"))
        data = []
        for d in draw:
            dat = []
            for t in d:
                if not t[0]:
                    dat.append("%3s %-20s" % ("", ""))
                else:
                    if len(t) == 2:
                        t.append(0)
                    dat.append("%3s %-16s" % (t[0], t[1][:16]))
            data.append(dat)
        SelectChoice(self.opts["mf"].window, title, cols, data, sort=False,
            live=False)

    def doTExit(self):
        self.at.closeProcess()
        self.df.focusField("T", 1, 1)

    def doCheckTab(self, tab):
        for b in self.bounce:
            for s in self.bounce[b]:
                if tab in self.bounce[b][s]:
                    return "Tab in Bounce Game - %s" % b
        for t in self.teams:
            if tab in self.teams[t]:
                return "Tab in Team - %s" % t

    def doDraw(self):
        if self.drawn:
            yn = askQuestion(self.opts["mf"].body, "Drawn",
                "This Draw has Already Been Done, Do You Want to Re-Draw?",
                default="no")
            if yn == "no":
                self.df.focusField("T", 1, 1)
                return
            else:
                self.sql.delRec("bwldrt", where=[("bdt_cono", "=",
                    self.opts["conum"]), ("bdt_date", "=", self.date),
                    ("bdt_time", "=", self.time)])
                self.drawn = False
        err = False
        invalid = (0, 1, 3, 5)
        if not self.bounce and not self.teams and len(self.alltabs) in invalid:
            showError(self.opts["mf"].body, "Error",
                "Invalid Number of Entries\n(0, 1, 3 or 5)")
            err = True
        if not err and self.teams:
            tabs = []
            for skp in self.teams:
                for mem in self.teams[skp]:
                    if mem:
                        tabs.append(mem)
            if self.bounce:
                for rnk in self.bounce:
                    for sd in self.bounce[rnk]:
                        for mem in self.bounce[rnk][sd]:
                            if mem:
                                tabs.append(mem)
            self.tdata = []
            for t in self.alltabs:
                if t not in tabs:
                    self.tdata.append([t] + self.doLoadTab(t, "D"))
            if self.tdata:
                self.dogen = False
                self.tdata.sort()
                cols = [
                    ("a", "Tab-No", 6, "UI", "N"),
                    ("b", "Name", 20, "NA", "N"),
                    ("c", "Pos", 1, "UI", "N"),
                    ("d", "Rte", 2, "UI", "N")]
                but = [
                    ("Generate", self.doGenTeams),
                    ("Delete", self.doDelTabs)]
                SelectChoice(self.opts["mf"].window,
                    "These Tabs Are Not In Teams",
                    cols, self.tdata, butt=but, sort=False, live=False)
                if self.dogen:
                    self.doDraw()
                    return
                else:
                    err = True
            if not err and len(self.teams) % 2:
                showError(self.opts["mf"].body, "Error",
                    "Unequal Number of Teams (%s)" % len(self.teams))
                err = True
        if err:
            self.df.focusField("T", 1, 1)
            return
        np = ""
        for tab in self.alltabs:
            if self.alltabs[tab][5] == "N":
                # Not paid
                np = "%s\n%3i %s, %s" % (np, tab, self.alltabs[tab][0],
                    self.alltabs[tab][1])
        if np:
            # Not paid
            yn = askQuestion(self.opts["mf"].body, "Non Payments",
                """The following People have Not yet Paid:
%s

Do you still want to continue?""" % np, default="no")
            if yn == "no":
                return
        tit = ("Draw Parameters",)
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Fours","4"), ("Trips","3"), ("Pairs","2"), ("Singles","1"))
        if self.teams:
            r1s = (("Strength", "S"), ("Random", "R"))
            fld = [
                (("T",0,0,0),("IRB",r1s),0,"Draw Type","",
                    "S","N",self.doType,None,None,None,None,
                    """Strength: The Draw will Try and Pair the teams by Strength.
Random: The teams will be Randomly Paired.""")]
            x = 1
            self.dhist = "N"
        elif self.nbase in ("C", "R"):
            r1s = (("Random", "R"), ("Strength", "S"))
            fld = [
                (("T",0,0,0),("IRB",r1s),0,"Draw Type","",
                    "R","N",self.doType,None,None,None,None,
                    """Strength: The Draw will Try and Draw the teams by Strength.
Random: The teams will be Randomly Drawn.""")]
            x = 1
        elif self.nbase == "P":
            fld = []
            self.dtype = "R"
            self.dhist = "Y"
            x = 0
        if not self.teams:
            if self.nbase == "C":
                fld.append((("T",0,x,0),("IRB",r2s),0,"Apply Percentages","",
                    "Y","N",self.doPer,None,None,None,None,
                    "Decrease rating by 10% if position is raised and "\
                    "increase rating by 10% if position is lowered "\
                    "e.g. a Third playing as a Skip would be rated "\
                    "10% lower and a Skip playing as a Third would "\
                    "be rated 10% higher etc."))
                x += 1
            fld.extend([
                (("T",0,x,0),("IRB",r2s),0,"Apply History","",
                    "Y","N",self.doHist,None,None,None,None,
                    """For at Least %s Weeks:
Try Not to Pair the Same Skips
Try to Avoid Broken Rink Repeats
Try to Allocate Different Rinks""" % self.weeks),
                (("T",0,x + 1,0),("IRB",r3s),0,"Team Size","",
                    str(self.dsize),"N",self.doSize,None,None,None),
                (("T",0,x + 2,0),("IRB",r2s),0,"Prefer Pairs","",
                    self.rep42,"N",self.doRep42,None,None,None,None,
                    "In the case of Trips select whether to Replace "\
                    "teams of Fours with Pairs.")])
            x += 3
        fld.append(
            (("T",0,x,0),"IUA",40,"Greens","Greens (A,B,C)",
                "","N",self.doGreens,None,None,("notblank",),None,
                "Available Greens in the format A,B or A,B345 showing "\
                "Green Code and Rinks. If the Rinks are Not Entered they "\
                "will Default to 6. To enter 7 rinks enter A7, B7 etc."))
        self.gpos = x
        but = (("Cancel",None,self.doCancel,1,None,None,None,1),)
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.dw = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doDrawEnd,"y"),), txit=(self.doCancel,),
            butt=but)
        self.dw.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state)
        self.df.focusField("T", 1, 1)

    def doGenTeams(self):
        self.dogen = True
        odds = self.doPositions(self.alltabs, grp=False)
        if self.tsize == 3:
            self.seconds += self.thirds
            self.thirds = 0
            if "4/3" in odds:
                self.thirds += 1
                self.seconds -= 1
        for tm in self.teams:
            for nm, tb in enumerate(self.teams[tm]):
                tmm = []
                if tb:
                    if nm == 0:
                        self.skips -= 1
                    elif nm == 1:
                        self.thirds -= 1
                    elif nm == 2:
                            self.seconds -= 1
                    else:
                        self.leads -= 1
        tmp = sorted(self.tdata, key=itemgetter(2, 3), reverse=True)
        skp = []
        tds = []
        sds = []
        lds = []
        for _ in range(self.skips):
            skp.append(tmp.pop(0)[0])
        for _ in range(self.thirds):
            tds.append(tmp.pop(0)[0])
        for _ in range(self.seconds):
            sds.append(tmp.pop(0)[0])
        for _ in range(self.leads):
            lds.append(tmp.pop(0)[0])
        tmm = {}
        while skp:
            num = skp.pop(0)
            tmm[num] = [num]
            if tds:
                tmm[num].append(tds.pop(0))
            else:
                tmm[num].append(0)
            if sds:
                tmm[num].append(sds.pop(0))
            else:
                tmm[num].append(0)
            tmm[num].append(lds.pop(0))
        if skp or tds or sds or lds:
            showError(self.opts["mf"].body, "Error",
                "Unable To Generate Teams.\n\nPlease Do So Manually.")
            return
        self.teams = self.teams | tmm

    def doDelTabs(self):
        for tab in self.tdata:
            del self.alltabs[tab[0]]
        self.doShowQuantity()
        self.doDraw()

    def doCancel(self):
        self.dw.closeProcess()

    def doType(self, frt, pag, r, c, p, i, w):
        self.dtype = w
        if self.teams:
            self.needed = self.getNeeded(len(self.alltabs))
        elif self.dtype == "S":
            self.dhist = "N"
            self.dw.loadEntry(frt, pag, p+1, data="N")
        if self.teams:
            self.needed = self.getNeeded(len(self.teams))
            self.dw.topf[0][self.gpos][4] = \
                "Greens (%s Rinks Needed)" % self.needed

    def doPer(self, frt, pag, r, c, p, i, w):
        self.dper = w
        if self.dtype == "S":
            self.dw.loadEntry(frt, pag, p+1, data="N")

    def doHist(self, frt, pag, r, c, p, i, w):
        self.dhist = w

    def doSize(self, frt, pag, r, c, p, i, w):
        self.tsize = int(w)
        self.dw.topf[0][-1][4] = ""
        if self.tsize in (1, 2, 4):
            if self.mixgd == "Y":
                self.needed = self.getNeeded(len(self.alltabs))
            else:
                self.needed = self.getNeeded(self.men, self.wom)
            self.dw.topf[0][self.gpos][4] = \
                "Greens (%s Rinks Needed)" % self.needed
            if self.tsize in (1, 2) and len(self.alltabs) % 2:
                return "Odd Number of Tabs"
            elif self.tsize == 4:
                self.rep42 = "N"
                self.dw.loadEntry(frt, pag, p + 1, data=self.rep42)
            return "sk1"

    def doRep42(self, frt, pag, r, c, p, i, w):
        self.rep42 = w
        if self.mixgd == "Y":
            self.needed = self.getNeeded(len(self.alltabs))
        else:
            self.needed = self.getNeeded(self.men, self.wom)
        self.dw.topf[0][self.gpos][4] = \
            "Greens (%s Rinks Needed)" % self.needed

    def getNeeded(self, men, wom=0):
        for rnk in self.bounce:
            for sid in ("L", "R"):
                for tab in self.bounce[rnk][sid]:
                    if tab:
                        if self.dofix:
                            if self.alltabs[tab][2] == "M":
                                men -= 1
                            else:
                                wom -= 1
        if self.teams:
            needed = int(len(self.teams) / 2)
        else:
            needed = 0
            if self.dofix:
                if men % 2 and wom % 2:
                    if men > wom:
                        men -= 1
                        wom += 1
                    else:
                        men += 1
                        wom -= 1
            for qty in (men, wom):
                if not qty:
                    continue
                num = int(qty / (self.tsize * 2))
                rem = qty % (self.tsize * 2)
                if rem:
                    if self.tsize == 3:
                        if rem == 2:
                            if num < 1:
                                num += 1
                            elif self.rep42 == "Y":
                                num += 1
                        elif rem == 3:
                            if num > 1 and self.rep42 == "Y":
                                num += 1
                            else:
                                num += 1
                        elif rem == 4 and (num < 2 or self.rep42 == "Y"):
                            num += 1
                        elif rem == 5 and (num < 3 or self.rep42 == "Y"):
                            num += 1
                    else:
                        num += 1
                needed += num
        needed += len(self.bounce)
        return needed

    def doGreens(self, frt, pag, r, c, p, i, w):
        w = w.strip(",")
        for green in w.split(","):
            if not green or green[0] not in self.greens:
                return "Invalid Green (%s)" % green
        greens, first, endrnk, error = getGreens(w, self.needed,
            list(self.bounce.keys()))
        if error:
            return error
        self.rinks = []
        used = list(self.bounce.keys())
        for green in greens:
            for rink in greens[green]:
                if "%s%s" % (green, rink) in self.bounce:
                    used.remove("%s%s" % (green, rink))
                    continue
                self.rinks.append("%s%s" % (green, rink))
        if used:
            return "Missing Rinks %s" % str(tuple(used)).replace("'", "")
        if len(self.rinks) < (self.needed - len(self.bounce)):
            return "Invalid Number of Rinks"

    def doDrawEnd(self):
        self.dw.closeProcess()
        self.adraw1 = []
        self.rinks1 = copyList(self.rinks)
        self.ndict = copyList(self.alltabs)
        random.shuffle(self.rinks1)
        if self.bounce:
            # Bounce games
            self.adraw2 = []
            for rink in self.bounce:
                if rink in self.rinks1:
                    self.rinks1.remove(rink)
                for team in ("L", "R"):
                    dat = [0, 0]
                    for mem in self.bounce[rink][team]:
                        if mem:
                            dat[0] += 1
                            # Create player and remove from ndict
                            dat.append([mem] + self.ndict.pop(mem))
                    self.loadData(rink, dat)
            self.adraw1.extend(self.adraw2)
        if self.teams:
            # Teams
            # Pair teams and try not to let the same skips play against the
            # same skip they played in their previous game. Also try and
            # put them on a different rink.
            self.adraw2 = []
            temp = []
            for skp in self.teams:
                dat = [0, 0]
                for mem in self.teams[skp]:
                    if mem:
                        dat[0] += 1
                        # Create player and remove from ndict
                        plr = self.ndict.pop(mem)
                        dat.append([mem] + plr)
                        dat[1] += plr[4]
                dat[1] = dat[1] / dat[0]
                temp.append(dat)
            if self.dtype == "S":
                three = []
                four = []
                for num, tmm in enumerate(temp):
                    if tmm[0] == 4:
                        four.append(tmm)
                    elif tmm[0] == 3:
                        three.append(tmm)
                if len(four) % 2:
                    four = random.choice(four)
                    clos = 999
                    for idx, tmm in enumerate(three):
                        rte = tmm[2][5] + tmm[3][5] + tmm[4][5] + tmm[4][5]
                        rte = rte / 4
                        if rte > four[1]:
                            dif = rte - four[1]
                        else:
                            dif = four[1] - rte
                        if dif < clos:
                            clos = dif
                            three = tmm
                    temp.remove(three)
                    temp.remove(four)
                    temp = sorted(temp, key=itemgetter(0, 1))
                    temp.extend([three, four])
                else:
                    temp = sorted(temp, key=itemgetter(0, 1))
            else:
                random.shuffle(temp)
                temp = sorted(temp, key=itemgetter(0))
            while temp:
                ok = False
                rk1 = None
                sk1 = temp.pop(0)       # Next skip
                col = ["bdt_rink", "bdt_date", "bdt_time"]
                whr = [
                    ("bdt_cono", "=", self.opts["conum"]),
                    ("bdt_tab", "=", sk1[2][0]),
                    ("bdt_pos", "=", 4),
                    ("bdt_flag", "=", "C")]
                chk = self.sql.getRec("bwldrt", cols=col, where=whr,
                    order="bdt_date desc, bdt_time asc", limit=1)
                if chk:
                    rk1 = chk[0]        # Rink of last game
                    whr = [
                        ("bdt_cono", "=", self.opts["conum"]),
                        ("bdt_tab", "<>", sk1[2][0]),
                        ("bdt_date", "=", chk[1]),
                        ("bdt_time", "=", chk[2]),
                        ("bdt_rink", "=", rk1),
                        ("bdt_pos", "=", 4),
                        ("bdt_flag", "=", "C")]
                    opp = self.sql.getRec("bwldrt", where=whr, limit=1)
                    if opp:             # Opposition skip of last game
                        for skp in temp:
                            if skp[0] == sk1[0] and skp[2][0] is not opp[1]:
                                ok = True
                                sk2 = skp
                                temp.remove(skp)
                                break
                if not ok:              # Next skip
                    sk2 = temp.pop(0)
                ok = False
                if rk1:
                    for rink in self.rinks1:
                        if rk1 and rink == rk1:
                            continue
                        self.rinks1.remove(rink)
                        ok = True
                        break
                if not ok:
                    rink = self.rinks1.pop(0)
                self.loadData(rink, sk1)
                self.loadData(rink, sk2)
            self.adraw1.extend(self.adraw2)
        if not self.ndict:
            # All games are bounce and/or team games
            self.count = 0
            self.tot = 0
            self.scl = 0
            self.bcl = 0
            self.pcl = 0
        else:
            grps = [[]]
            ntabs = []
            for tab in self.ndict:
                # Create rest of players
                ntabs.append([tab] + self.ndict[tab])
            if self.mixgd.upper() == "N":
                mess = None
                grps.append([])
                for tab in ntabs:
                    if tab[3] == "M":
                        grps[0].append(tab)
                    else:
                        grps[1].append(tab)
                if grps[0] and len(grps[0]) in (1, 3, 5):
                    mess = "Not Enough Men, Do You Want a Mixed Draw?"
                elif grps[1] and len(grps[1]) in (1, 3, 5):
                    mess = "Not Enough Ladies, Do You Want a Mixed Draw?"
                if mess:
                    ok = askQuestion(self.opts["mf"].body,
                        "Insufficient Numbers", mess, default="yes")
                    if ok == "yes":
                        self.mixgd = "Y"
                        self.dofix = False
                        grps = [[]]
                        for tab in ntabs:
                            grps[0].append(tab)
                    else:
                        return None, None
                if self.dofix and len(grps[0]) % 2 and len(grps[1]) % 2:
                    fix = False
                    if self.tsize == 2:
                        if not (len(grps[0]) + 1) % 4:
                            fix = True
                            tt = random.randrange(0, len(grps[1]))
                            grps[0].append(grps[1].pop(tt))
                        elif not (len(grps[1]) + 1) % 4:
                            fix = True
                            tt = random.randrange(0, len(grps[0]))
                            grps[1].append(grps[0].pop(tt))
                    if not fix:
                        if len(grps[0]) > len(grps[1]):
                            tt = random.randrange(0, len(grps[0]))
                            grps[1].append(grps[0].pop(tt))
                        else:
                            tt = random.randrange(0, len(grps[1]))
                            grps[0].append(grps[1].pop(tt))
            else:
                for tab in ntabs:
                    grps[0].append(tab)
            for num, grp in enumerate(grps):
                # Gender or Mixed
                alldraw = []
                self.doPositions(grp)
                if self.dhist == "Y":
                    self.doHistory(self.weeks * -7)
                else:
                    self.hist = {}
                    self.broken = []
                if self.mixgd == "Y":
                    self.count = 0
                    text = "Selecting the Best Mixed Combination"
                elif not num:
                    self.count = 0
                    text = "Selecting the Best Men's Combination"
                else:
                    self.count = 0
                    text = "Selecting the Best Lady's Combination"
                text = text + """

Combination Number %10s"""
                splash = SplashScreen(self.opts["mf"].body, text)
                splash.label.configure(text=text % "")
                if self.dtype == "S" and self.dhist == "N":
                    iters = 1
                else:
                    iters = 5000
                # Do iterations and then look for the best one
                for _ in range(iters):
                    tot = self.doDrawRest(splash, text)
                    scl = 0
                    bcl = 0
                    pcl = []
                    for rink in range(0, len(self.adraw2), 2):
                        sk1 = self.adraw2[rink][2][0]
                        sk2 = self.adraw2[rink + 1][2][0]
                        if sk1 in self.hist and sk2 in self.hist[sk1][1]:
                            scl += 1
                        pls = []
                        tms = []
                        ops = []
                        for team in self.adraw2[rink][2:]:
                            if team[0]:
                                pls.append(team[0])
                                tms.append(team[0])
                        for opp in self.adraw2[rink + 1][2:]:
                            if opp[0]:
                                pls.append(opp[0])
                                ops.append(opp[0])
                        for plr in pls:
                            if len(pls) == 7 and plr in self.broken:
                                bcl += 1
                        for plr in tms:
                            if plr in self.hist:
                                check = copyList(tms)
                                check.remove(plr)
                                for tab in check:
                                    chk = [tab, plr]
                                    if tab in self.hist[plr][0]:
                                        if chk not in pcl:
                                            pcl.append([plr, tab])
                                    if tab in self.hist[plr][1]:
                                        if chk not in pcl:
                                            pcl.append([plr, tab])
                        for plr in ops:
                            if plr in self.hist:
                                check = copyList(ops)
                                check.remove(plr)
                                for tab in check:
                                    chk = [tab, plr]
                                    if tab in self.hist[plr][0]:
                                        if chk not in pcl:
                                            pcl.append([plr, tab])
                                    if tab in self.hist[plr][1]:
                                        if chk not in pcl:
                                            pcl.append([plr, tab])
                    alldraw.append([scl, bcl, len(pcl), tot, self.adraw2, pcl])
                splash.closeSplash()
                # Select the lowest draw where there are least clashes
                # scl = skips clash
                # bcl = broken rinks
                # pcl = players clash
                # tot = total team difference
                self.scl, self.bcl, self.pcl, self.tot, draw, t = \
                    sorted(alldraw, key=itemgetter(0, 1, 2, 3))[0]
                self.adraw1.extend(draw)
                for d in draw:
                    if d[0] in self.rinks1:
                        self.rinks1.remove(d[0])
        if self.adraw1:
            self.adraw1.sort()
            # Move seconds to thirds in broken rinks
            self.tot = 0
            for x in range(0, len(self.adraw1), 2):
                q1 = q2 = 0
                for y in self.adraw1[x][2:]:
                    if y[0]:
                        q1 += 1
                for y in self.adraw1[x + 1][2:]:
                    if y[0]:
                        q2 += 1
                if q1 != q2:
                    if q1 < q2:
                        self.adraw1[x][3] = self.adraw1[x][4]
                        self.adraw1[x][4] = [0, "", 0]
                    else:
                        self.adraw1[x + 1][3] = self.adraw1[x + 1][4]
                        self.adraw1[x + 1][4] = [0, "", 0]
                self.doAverage(self.adraw1[x], self.adraw1[x + 1], True)
            self.drawn = True
            if self.teams:
                txt = "Arranged Teams"
            elif self.dtype == "S" and self.dhist == "N":
                txt = "Best Strength v Strength Draw, "\
                    "Largest Team Difference is %s" % self.tot
            elif self.dtype == "S":
                txt = "Best S v S Draw After Trying %s Different "\
                    "Combinations, Largest Team Difference is %s, "\
                    "Skips Clash %s, Players Clash %s, Broken %s" % \
                    (self.count, self.tot, self.scl, self.pcl, self.bcl)
            elif self.dhist == "N":
                txt = "Best Random Draw After Trying %s Different "\
                    "Combinations, Largest Team Difference is %s" % \
                    (self.count, self.tot)
            else:
                txt = "Best Random Draw After Trying %s Different "\
                    "Combinations, Largest Team Difference is %s, "\
                    "Skips Clash %s, Players Clash %s, Broken %s" % \
                    (self.count, self.tot, self.scl, self.pcl, self.bcl)
            self.doShowDraw(txt, self.adraw1)
            self.doSave()

    def doBalance(self, x):
        d1 = copyList(self.adraw2[x])
        d2 = copyList(self.adraw2[x + 1])
        # Thirds
        if d1[3][0] and d2[3][0]:
            av1, av2 = self.doAverage(d1, d2)
            if av1 < av2 and d1[3][2] < d2[3][2]:
                d1[3] = d2[3]
                d2[3] = copyList(self.adraw2[x][3])
            elif av1 > av2 and d1[3][2] > d2[3][2]:
                d2[3] = d1[3]
                d1[3] = copyList(self.adraw2[x + 1][3])
        # Seconds
        if d1[4][0] and d2[4][0]:
            av1, av2 = self.doAverage(d1, d2)
            if av1 < av2 and d1[4][2] < d2[4][2]:
                d1[4] = d2[4]
                d2[4] = copyList(self.adraw2[x][4])
            elif av1 > av2 and d1[4][2] > d2[4][2]:
                d2[4] = d1[4]
                d1[4] = copyList(self.adraw2[x + 1][4])
        # Leads
        if d1[5][0] and d2[5][0]:
            av1, av2 = self.doAverage(d1, d2)
            df1 = av1 - av2
            if df1 < 0:
                df1 = 0 - df1
            t1 = copyList(d1)
            t2 = copyList(d2)
            if av1 < av2 and d1[5][2] < d2[5][2]:
                d1[5] = d2[5]
                d2[5] = copyList(self.adraw2[x][5])
            elif av1 > av2 and d1[5][2] > d2[5][2]:
                d2[5] = d1[5]
                d1[5] = copyList(self.adraw2[x + 1][5])
            av1, av2 = self.doAverage(d1, d2)
            df2 = av1 - av2
            if df2 < 0:
                df2 = 0 - df2
            if df2 > df1:
                # Revert
                d1 = t1
                d2 = t2
        self.adraw2[x] = d1
        self.adraw2[x + 1] = d2

    def doAverage(self, draw1, draw2, gtot=False):
        draws = {"a": draw1[2:], "b": draw2[2:]}
        ct1 = ct2 = rt1 = rt2 = 0
        for d in ("a", "b"):
            for x in range(4):
                if draws[d][x][0]:
                    if d == "a":
                        ct1 += 1.0
                        rt1 += draws[d][x][2]
                    else:
                        ct2 += 1.0
                        rt2 += draws[d][x][2]
        if ct1 < ct2:
            # Broken rink, double up on lead
            ct1 += 1.0
            rt1 += draws["a"][3][2]
        elif ct1 > ct2:
            # Broken rink, double up on lead
            ct2 += 1.0
            rt2 += draws["b"][3][2]
        av1 = round(rt1 / ct1, 2)
        av2 = round(rt2 / ct2, 2)
        if gtot:
            if av1 > av2:
                dif = av1 - av2
            else:
                dif = av2 - av1
            if dif > self.tot:
                self.tot = dif
        draw1[1] = av1
        draw2[1] = av2
        return av1, av2

    def doPositions(self, tabs, grp=True):
        # Calculate the number of players, by position, required
        # Treating 2nds as 3rds in trips
        teams = int(len(tabs) / (self.tsize * 2))  # full teams
        odds = []                                  # others
        rem = len(tabs) % (self.tsize * 2)         # players short
        if rem:
            if self.tsize == 2 and rem == 2:
                odds = ["1/1"]
            elif self.tsize == 3:
                if rem == 1:
                    teams -= 1
                    odds = ["4/3"]
                elif rem == 2:
                    if teams < 1:
                        odds = ["1/1"]
                    else:
                        teams -= 1
                        if self.rep42 == "Y":
                            odds = ["2/2", "2/2"]
                        else:
                            odds = ["4/4"]
                elif rem == 3:
                    if teams > 1:
                        teams -= 2
                        if self.rep42 == "Y":
                            odds = ["4/3", "2/2", "2/2"]
                        else:
                            odds = ["4/3", "4/4"]
                    else:
                        teams -= 1
                        odds = ["4/3", "1/1"]
                elif rem == 4:
                    if teams < 2 or self.rep42 == "Y":
                        odds = ["2/2"]
                    else:
                        teams -= 2
                        odds = ["4/4", "4/4"]
                elif rem == 5:
                    if teams < 3 or self.rep42 == "Y":
                        teams -= 1
                        odds = ["4/3", "2/2"]
                    else:
                        teams -= 3
                        odds = ["4/4", "4/4", "4/3"]
            elif self.tsize == 4:
                if rem == 1:
                    if teams == 1:
                        teams -= 1
                        odds = ["4/3", "1/1"]
                    elif teams == 2:
                        teams -= 2
                        odds = ["4/3", "3/3", "2/2"]
                    else:
                        teams -= 3
                        odds = ["4/3", "3/3", "3/3", "3/3"]
                elif rem == 2:
                    if teams < 1:
                        odds = ["1/1"]
                    elif teams == 1:
                        teams -= 1
                        odds = ["3/3", "2/2"]
                    else:
                        teams -= 2
                        odds = ["3/3", "3/3", "3/3"]
                elif rem == 3:
                    if teams == 1:
                        teams -= 1
                        odds = ["4/3", "2/2"]
                    else:
                        teams -= 2
                        odds = ["4/3", "3/3", "3/3"]
                elif rem == 4:
                    if teams < 1:
                        odds = ["2/2"]
                    else:
                        teams -= 1
                        odds = ["3/3", "3/3"]
                elif rem == 5:
                    teams -= 1
                    odds = ["4/3", "3/3"]
                elif rem == 6:
                    odds = ["3/3"]
                elif rem == 7:
                    odds = ["4/3"]
        self.skips = (teams + len(odds)) * 2
        if self.tsize == 4:
            self.thirds = teams * 2
            for o in odds:
                if o in ("4/3", "3/3"):
                    self.thirds += 2
            self.seconds = teams * 2
            for o in odds:
                if o == "4/3":
                    self.seconds += 1
            self.leads = teams * 2
            for o in odds:
                if o not in ("1/1",):
                    self.leads += 2
        elif self.tsize == 3:
            self.thirds = teams * 2
            for o in odds:
                if o in ("4/4", "4/3"):
                    self.thirds += 2
            self.seconds = 0
            for o in odds:
                if o == "4/4":
                    self.seconds += 2
                elif o == "4/3":
                    self.seconds += 1
            self.leads = teams * 2
            for o in odds:
                if o not in ("1/1",):
                    self.leads += 2
        elif self.tsize == 2:
            self.thirds = 0
            self.seconds = 0
            self.leads = teams * 2
            for o in odds:
                if o not in ("1/1",):
                    self.leads += 2
        elif self.tsize == 1:
            self.thirds = 0
            self.seconds = 0
            self.leads = 0
        if not grp:
            return odds
        # Group players by position
        self.skip1 = []
        self.third1 = []
        self.second1 = []
        self.lead1 = []
        for tab in tabs:
            if self.nbase in ("R", "N"):
                tab[4] = 0
                self.skip1.append(tab)
            elif tab[4] == 4:
                self.skip1.append(tab)
            elif tab[4] == 3:
                self.third1.append(tab)
            elif tab[4] == 2:
                self.second1.append(tab)
            else:
                self.lead1.append(tab)
        if self.nbase == "P":
            # Rating by position only
            # Shuffle players
            random.shuffle(self.skip1)
            random.shuffle(self.third1)
            random.shuffle(self.second1)
            random.shuffle(self.lead1)
        elif self.nbase in ("R", "C"):
            # Rating by rating only or combination
            # Sort players by rating
            if self.order == "A":
                rev = False
            else:
                rev = True
            self.skip1 = sorted(self.skip1, key=itemgetter(5), reverse=rev)
            self.third1 = sorted(self.third1, key=itemgetter(5), reverse=rev)
            self.second1 = sorted(self.second1, key=itemgetter(5), reverse=rev)
            self.lead1 = sorted(self.lead1, key=itemgetter(5), reverse=rev)
        # Skips
        while self.third1 and len(self.skip1) < self.skips:
            tab = self.third1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .9, 0))
            self.skip1.append(tab)
        while self.second1 and len(self.skip1) < self.skips:
            tab = self.second1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .8, 0))
            self.skip1.append(tab)
        while self.lead1 and len(self.skip1) < self.skips:
            tab = self.lead1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .7, 0))
            self.skip1.append(tab)
        while len(self.skip1) > self.skips:
            tab = self.skip1.pop(0)
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * 1.1, 0))
            self.third1.append(tab)
        # Thirds
        while self.second1 and len(self.third1) < self.thirds:
            tab = self.second1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .9, 0))
            self.third1.append(tab)
        while self.lead1 and len(self.third1) < self.thirds:
            tab = self.lead1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .8, 0))
            self.third1.append(tab)
        while len(self.third1) > self.thirds:
            tab = self.third1.pop(0)
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * 1.1, 0))
            self.second1.append(tab)
        # Seconds
        while len(self.second1) < self.seconds:
            tab = self.lead1.pop()
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * .9, 0))
            self.second1.append(tab)
        while len(self.second1) > self.seconds:
            tab = self.second1.pop(0)
            if self.nbase == "C" and self.dper == "Y":
                tab[5] = int(round(tab[5] * 1.1, 0))
            self.lead1.append(tab)

    def doHistory(self, days):
        self.hist = {}
        self.broken = []
        ldate = projectDate(self.date, days)
        # Get records for past x days excluding bounce, team games and svs
        recs = self.sql.getRec("bwldrt", where=[("bdt_cono", "=",
            self.opts["conum"]), ("bdt_date", ">=", ldate),
            ("bdt_flag", "in", ("B", "D"))])
        for rec in recs:
            dte = rec[self.sql.bwldrt_col.index("bdt_date")]
            tim = rec[self.sql.bwldrt_col.index("bdt_time")]
            rnk = rec[self.sql.bwldrt_col.index("bdt_rink")]
            svs = self.sql.getRec("bwldrm", cols=["bdm_dhist"],
                where=[("bdm_cono", "=", self.opts["conum"]), ("bdm_date",
                "=", dte), ("bdm_time", "=", tim)], limit=1)
            if svs[0] == "N":
                # History not applied on draw
                continue
            if dte == self.date and tim == self.time:
                # Current draw
                continue
            tab = rec[self.sql.bwldrt_col.index("bdt_tab")]
            if rec[self.sql.bwldrt_col.index("bdt_flag")] == "B":
                self.broken.append(tab)
            if tab not in self.hist:
                self.hist[tab] = [[], []]
            team = []
            p1 = self.sql.bwldrt_col.index("bdt_team1")
            p2 = self.sql.bwldrt_col.index("bdt_team2")
            p3 = self.sql.bwldrt_col.index("bdt_team3")
            for r in (p1, p2, p3):
                if rec[r]:
                    team.append(rec[r])
            self.hist[tab][0].extend(team)
            team.append(tab)
            opps = self.sql.getRec("bwldrt", cols=["bdt_tab"],
                where=[("bdt_cono", "=", self.opts["conum"]),
                ("bdt_tab", "not in", team), ("bdt_date", "=", dte),
                ("bdt_time", "=", tim), ("bdt_rink", "=", rnk)])
            for opp in opps:
                self.hist[tab][1].append(opp[0])

    def doDrawRest(self, splash, text):
        # Splash
        self.count += 1
        splash.label.configure(text=text % self.count)
        splash.refreshSplash()
        # Rinks
        rinks2 = copyList(self.rinks1)
        # Shuffle players
        self.skip2 = copyList(self.skip1)
        random.shuffle(self.skip2)
        self.third2 = copyList(self.third1)
        random.shuffle(self.third2)
        self.second2 = copyList(self.second1)
        random.shuffle(self.second2)
        self.lead2 = copyList(self.lead1)
        random.shuffle(self.lead2)
        # Make up teams
        draws = []
        if self.dtype == "S":
            # Sort players for strength v strength
            rev = bool(self.order == "A")
            self.skip2 = sorted(self.skip2, key=itemgetter(5), reverse=rev)
            self.third2 = sorted(self.third2, key=itemgetter(5), reverse=rev)
            self.second2 = sorted(self.second2, key=itemgetter(5), reverse=rev)
            self.lead2 = sorted(self.lead2, key=itemgetter(5), reverse=rev)
            if self.seconds % 2:
                # Broken rink, try and select random teams fairly
                for x in range(2):
                    tm = []
                    mx = len(self.skip2)
                    if not x:
                        tt = random.randrange(0, mx)
                    else:
                        if tt % 2:
                            tt -= 1
                    if tt:
                        av = tt / float(mx)
                    else:
                        av = 0
                    tm.append(self.skip2.pop(tt))
                    tt = int(round(len(self.third2) * av, 0))
                    if tt == len(self.third2):
                        tt -= 1
                    tm.append(self.third2.pop(tt))
                    if x == 1:
                        tt = int(round(len(self.second2) * av, 0))
                        if tt == len(self.second2):
                            tt -= 1
                        tm.append(self.second2.pop(tt))
                    tt = int(round(len(self.lead2) * av, 0))
                    if tt == len(self.lead2):
                        tt -= 1
                    tm.append(self.lead2.pop(tt))
                    draws.append(tm)
        for s in range(len(self.skip2)):
            tm = [self.skip2.pop()]
            if self.third2:
                tm.append(self.third2.pop())
            if self.second2:
                tm.append(self.second2.pop())
            if self.lead2:
                tm.append(self.lead2.pop())
            draws.append(tm)
        # Insert number of players and average rating per team
        temp = copyList(draws)
        for n, d in enumerate(temp):
            siz = len(d)
            draws[n].insert(0, siz)
            tot = 0
            for t in d:
                tot += t[5]
            draws[n].insert(1, round(tot / float(siz), 2))
        if self.dtype == "R":
            # Pair teams by strength and then size for random draw
            if self.order == "A":
                rev = False
            else:
                rev = True
            draws = sorted(draws, key=itemgetter(1), reverse=rev)
            draws = sorted(draws, key=itemgetter(0))
            if self.seconds % 2:
                # Broken rink, try and select random teams fairly
                if self.tsize == 3:
                    nsize = 4
                else:
                    nsize = 3
                while True:
                    x = random.randrange(0, len(draws))
                    if draws[x][0] == nsize:
                        one = draws.pop(x)
                        break
                chk = 99
                seq = 0
                for x, d0 in enumerate(draws):
                    if d0[0] != self.tsize:
                        continue
                    if nsize == 3:
                        d1 = one[4][5]
                        d2 = 0
                        for n in range(2, 5):
                            d1 += one[n][5]
                        for n in range(2, 6):
                            d2 += d0[n][5]
                    else:
                        d1 = 0
                        for n in range(2, 6):
                            d1 += one[n][5]
                        d2 = d0[4][5]
                        for n in range(2, 5):
                            d2 += d0[n][5]
                    df = d1 - d2
                    if df < 0:
                        df = 0 - df
                    if df < chk:
                        chk = df
                        seq = x
                draws.extend([one, draws.pop(seq)])
        # Allocate rinks and calculate maximum rating difference
        total = 0
        self.adraw2 = []
        for x in range(0, len(draws), 2):
            # Allocate rink
            g = rinks2.pop(0)
            # Load team A
            self.loadData(g, draws[x])
            # Load team B
            self.loadData(g, draws[x + 1])
            if self.dtype == "S":
                # Try and balance teams
                self.doBalance(x)
            # Extract average strengths
            av1, av2 = self.doAverage(self.adraw2[x], self.adraw2[x + 1])
            # Calculate difference
            tot = av1 - av2
            if tot < 0:
                tot = 0 - tot
            if tot > total:
                total = tot
        return total

    def loadData(self, g, d):
        # Pad draws with missing players
        if d[2][2]:
            nam = "%s, %s" % (d[2][1].upper(), d[2][2][0].upper())
        else:
            nam = d[2][1].upper()
        drw = [g, d[1], [d[2][0], nam, d[2][5]]]
        if d[0] == 1:
            drw.extend([[0, "",0], [0, "", 0], [0, "", 0]])
        elif d[0] == 2:
            drw.extend([[0, "", 0], [0, "", 0]])
        elif d[0] == 3:
            drw.append([0, "", 0])
        if len(d) > 3:
            for f in d[3:]:
                if f[2]:
                    nam = "%s, %s" % (f[1].upper(), f[2][0].upper())
                else:
                    nam = f[1].upper()
                drw.append([f[0], nam, f[5]])
        self.adraw2.append(drw)

    def doSave(self):
        # Delete all existing records
        self.sql.delRec("bwldrm", where=[("bdm_cono", "=", self.opts["conum"]),
            ("bdm_date", "=", self.date), ("bdm_time", "=", self.time)])
        self.sql.delRec("bwldrt", where=[("bdt_cono", "=", self.opts["conum"]),
            ("bdt_date", "=", self.date), ("bdt_time", "=", self.time)])
        # Insert bwldrm
        self.sql.insRec("bwldrm", data=[self.opts["conum"], self.date,
            self.time, self.mixgd, self.mixrt, self.nbase, self.dtype,
            self.dhist, self.tsize, self.ratem.work, self.ratev.work])
        if not self.drawn:
            return
        # Insert bwldrt
        for x in range(0, len(self.adraw1), 2):
            one = 0
            two = 0
            for r in self.adraw1[x][2:]:
                if r[0]:
                    one += 1
            for r in self.adraw1[x + 1][2:]:
                if r[0]:
                    two += 1
            broken = bool(two != one)
            side = "L"
            for y in range(2):
                dat = self.adraw1[x + y]
                tab = []
                for num, plr in enumerate(dat[2:]):
                    if not plr[0]:
                        continue
                    pos = [4, 3, 2, 1][num]
                    tab.append([plr, pos])
                for t1 in tab:
                    nam = t1[0][1].replace("VAN DER", "V D")
                    nam = nam.replace("JANSE VAN", "J V")
                    rec = [self.opts["conum"], t1[0][0], self.date, self.time,
                        dat[0], side, nam, t1[1], t1[0][2]]
                    for t2 in tab:
                        if t2[0][0] != t1[0][0]:
                            rec.extend([t2[0][0], t2[1]])
                    for _ in range(len(rec), 15):
                        rec.append(0)
                    bounce = False
                    for rk in self.bounce:
                        for sd in self.bounce[rk]:
                            if t1[0][0] in self.bounce[rk][sd]:
                                bounce = True
                    teams = False
                    for sk in self.teams:
                        if t1[0][0] in self.teams[sk]:
                            teams = True
                    if bounce:
                        rec.append("A")
                    elif teams:
                        rec.append("C")
                    elif broken:
                        rec.append("B")
                    else:
                        rec.append("D")
                    self.sql.insRec("bwldrt", data=rec)
                side = "R"
        self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.topEntry[1][0], state="disabled")

    def doPrint(self, dg=None):
        if not dg:
            dg = self.df
        if not self.drawn:
            showError(self.opts["mf"].body, "Error",
                "The Draw Has Not Yet Been Done")
            dg.focusField("T", 1, 1)
            return
        dg.setWidget(dg.mstFrame, state="hide")
        if not self.ratem.work and not self.ratev.work:
            rated = "N"
        else:
            rated = "Y"
        r1s = (("No", "N"), ("Yes", "Y"), ("Only", "O"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Print Cards","",
                "N","Y",self.doCards,None,None,None),
            (("T",0,1,0),"INA",30,"Heading","",
                "","Y",self.doHead,None,None,("notblank",)),
            (("T",0,2,0),"IUI",2,"Number of Ends","",
                0,"Y",self.doEnds,None,None,("notzero",)),
            (("T",0,3,0),("IRB",r2s),0,"Cash Takings Sheet","",
                rated,"Y",self.doTakings,None,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Tabs Draw Listing","",
                "N","Y",self.doListing,None,None,None),
            (("T",0,5,0),("IRB",r2s),0,"Tabs Draw Board","",
                "Y","Y",self.doBoard,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"Include Empty Rinks","",
                "N","Y",self.doEmpty,None,None,None))
        self.pd = TartanDialog(self.opts["mf"], tops=True,
            title="Print Dialog", eflds=fld, tend=((self.doPEnd, "n"),),
            txit=(self.doPExit,), view=("N","V"))
        self.pd.mstFrame.wait_window()
        dg.setWidget(dg.mstFrame, state="show")
        if not self.reprint:
            dg.focusField("T", 1, 1)

    def doCards(self, frt, pag, r, c, p, i, w):
        self.cards = w
        if not self.teams and self.cards == "N":
            self.cdes = None
            return "sk2"

    def doHead(self, frt, pag, r, c, p, i, w):
        self.cdes = w
        if self.teams and self.cards == "N":
            return "sk1"

    def doEnds(self, frt, pag, r, c, p, i, w):
        self.ends = w
        if self.cards == "O":
            return "nd"

    def doTakings(self, frt, pag, r, c, p, i, w):
        self.takings = w

    def doListing(self, frt, pag, r, c, p, i, w):
        self.listing = w

    def doBoard(self, frt, pag, r, c, p, i, w):
        self.board = w
        if self.board == "N":
            if (self.takings, self.listing) == ("N", "N"):
                return "xt"
            else:
                self.empty = "N"
                return "sk1"

    def doEmpty(self, frt, pag, r, c, p, i, w):
        self.empty = w

    def doPEnd(self):
        self.pd.closeProcess()
        if self.cards != "O":
            PrintDraw(self.opts["mf"], self.opts["conum"], self.date,
                self.time, cdes=self.cdes, takings=self.takings,
                listing=self.listing, board=self.board, empty=self.empty,
                repprt=self.pd.repprt, name=self.__class__.__name__)
        if self.cards != "N":
            recs = self.sql.getRec(tables=["bwldrt", "bwltab"],
                cols=["bdt_rink", "bdt_tab"], where=[("bdt_cono", "=",
                self.opts["conum"]), ("bdt_date", "=", self.date),
                ("bdt_time", "=", self.time), ("bdt_pos", "=", 4)],
                group="bdt_rink, bdt_tab", order="bdt_rink")
            skips = []
            for x in range(0, len(recs), 2):
                grn = recs[x][0]
                skp = self.sql.getRec("bwltab", cols=["btb_tab",
                    "btb_surname", "btb_names"], where=[("btb_cono", "=",
                    self.opts["conum"]), ("btb_tab", "=", recs[x][1])],
                    limit=1)
                opp = self.sql.getRec("bwltab", cols=["btb_tab",
                    "btb_surname", "btb_names"], where=[("btb_cono", "=",
                    self.opts["conum"]), ("btb_tab", "=", recs[x+1][1])],
                    limit=1)
                skips.append((grn, skp, opp))
            PrintCards(self.opts["mf"], self.opts["conum"], self.cdes, 1,
                self.dated, skips, self.ends, "N", 0)

    def doPExit(self):
        self.pd.closeProcess()

    def doEdit(self):
        if not self.drawn:
            showError(self.opts["mf"].body, "Error",
                "The Draw Has Not Yet Been Done")
            self.df.focusField("T", 1, 1)
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.adraw3 = copyList(self.adraw1)
        self.reptabs = []
        while True:
            draw = self.doShowDraw("View/Edit the Draw", self.adraw3, True)
            if draw:
                self.doChange(draw)
                if not self.adraw3:
                    break
            else:
                error = False
                chk = []
                for d in self.adraw3:
                    for t in d[2:]:
                        if t[0]:
                            if t[0] in chk:
                                showError(self.opts["mf"].body,
                                    "Duplicate Tab",
                                    "Tab %s - %s Appears More than Once" % \
                                    (t[0], t[1]))
                                error = True
                                break
                            chk.append(t[0])
                if not error:
                    for d in self.alltabs:
                        if d not in chk:
                            showError(self.opts["mf"].body,
                                "Missing Tab",
                                "Tab %s - %s, %s\n\nIs Not in the Draw" % \
                                (d, self.alltabs[d][0], self.alltabs[d][1]))
                            error = True
                            break
                if not error:
                    break
        if self.adraw3 != self.adraw1:
            yn = askQuestion(self.opts["mf"].body, "Keep Changes",
                "Do You Want to Keep the Changes?", default="yes")
            if yn == "yes":
                self.adraw1 = []
                for draw in self.adraw3:
                    if draw[2][0] or draw[3][0] or draw[4][0] or draw[5][0]:
                        self.adraw1.append(draw)
                self.doSave()
            elif self.reptabs:
                # Restore replaced tabs
                for old, dat, new in reversed(self.reptabs):
                    if new in self.alltabs:
                        del self.alltabs[new]
                    if old not in self.alltabs:
                        self.alltabs[old] = dat
        self.df.enableButtonsTags(state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.doShowQuantity()
        self.df.focusField("T", 1, 1)

    def doView(self):
        if not self.drawn:
            showError(self.opts["mf"].body, "Error",
                "The Draw Has Not Yet Been Done")
            self.df.focusField("T", 1, 1)
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.doShowDraw("View of Draw", self.adraw1)
        self.df.enableButtonsTags(state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.doShowQuantity()
        self.df.focusField("T", 1, 1)

    def doShowDraw(self, title, draw, select=False):
        cols = (
            ("rink", "RK", 2, "UA", "N"),
            ("rate", "AVG ", 5.2, "UD", "N"),
            ("skip", "Skip", 24, "UA", "N"),
            ("third", "Third", 24, "UA", "N"),
            ("second", "Second", 24, "UA", "N"),
            ("lead", "Lead", 24, "UA", "N"))
        data = []
        for d in draw:
            dat = [d[0], d[1]]
            for t in d[2:]:
                t[1] = t[1].replace("VAN DER", "V D")
                t[1] = t[1].replace("JANSE VAN", "J V")
                if not t[0]:
                    dat.append("%3s %-20s" % ("", ""))
                else:
                    if len(t) == 2:
                        t.append(0)
                    dat.append("%3s %-16s(%2s)" % (t[0], t[1][:16], t[2]))
            data.append(dat)
        sel = SelectChoice(self.opts["mf"].window, title, cols, data,
            live=select, rowc=2)
        if select:
            return sel.selection

    def doChange(self, draw):
        for self.seq in range(0, len(self.adraw3), 2):
            if self.adraw3[self.seq][0] == draw[1]:
                seq = self.seq + 1
                self.cdraw = self.adraw3[self.seq] + self.adraw3[seq][2:]
                break
        tit = ("Change Draw",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        fld = (
            (("T",0,0,0),"OUA",2,"RK"),
            (("T",0,1,0),"IUI",6,"Skip","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,1,0),"OUA",20,""),
            (("T",0,2,0),"IUI",6,"Third","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,2,0),"OUA",20,""),
            (("T",0,3,0),"IUI",6,"Second","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,3,0),"OUA",20,""),
            (("T",0,4,0),"IUI",6,"Lead","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,4,0),"OUA",20,""),
            (("T",0,5,0),"IUI",6,"Skip","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,5,0),"OUA",20,""),
            (("T",0,6,0),"IUI",6,"Third","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,6,0),"OUA",20,""),
            (("T",0,7,0),"IUI",6,"Second","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,7,0),"OUA",20,""),
            (("T",0,8,0),"IUI",6,"Lead","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,8,0),"OUA",20,""))
        but = (("Replace Tab with New Tab",None,self.doRepTab,1,None,None,
            "This will Remove the Existing Tab and Replace it with a New "\
            "Uncaptured Tab."),)
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doChgEnd,"n"),), txit=(self.doChgExit,),
            butt=but, focus=False)
        self.cg.loadEntry("T", 0, 0, data=self.cdraw[0])
        for n, d in enumerate(self.cdraw[2:]):
            self.cg.loadEntry("T", 0, 1 + (2 * n), data=d[0])
            self.cg.loadEntry("T", 0, 2 + (2 * n), data=d[1])
        self.cg.focusField("T", 0, 1, clr=False)
        self.cg.mstFrame.wait_window()

    def doRepTab(self):
        self.oldtab = self.cg.getEntry("T", 0, self.cg.pos, False)
        oldnam = self.cg.getEntry("T", 0, self.cg.pos + 1, False)
        if not self.oldtab:
            return
        self.oldtab = int(self.oldtab)
        state = self.cg.disableButtonsTags()
        self.cg.setWidget(self.cg.mstFrame, state="hide")
        tit = ("Replace Tab",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        fld = (
            (("T",0,0,0),"OUI",6,"Old Tab"),
            (("T",0,0,0),"OUA",20,""),
            (("T",0,1,0),"IUI",6,"New Tab","",
                0,"N",self.doNewTab,mem,None,("notzero",)),
            (("T",0,1,0),"OUA",20,""))
        self.nt = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRepEnd,"y"),), txit=(self.doRepExit,))
        self.nt.loadEntry("T", 0, 0, data=self.oldtab)
        self.nt.loadEntry("T", 0, 1, data=oldnam)
        self.nt.mstFrame.wait_window()
        self.cg.setWidget(self.cg.mstFrame, state="show")
        self.cg.enableButtonsTags(state=state)
        self.cg.focusField("T", 0, self.cg.col, clr=False)

    def doNewTab(self, frt, pag, r, c, p, i, w):
        if w in self.alltabs:
            return "Invalid Tab, Already Entered"
        self.newtab = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", w)], limit=1)
        if not self.newtab:
            return "Invalid Tab Number"
        a = self.newtab[self.sql.bwltab_col.index("btb_surname")]
        b = self.newtab[self.sql.bwltab_col.index("btb_names")]
        self.nam = a.upper()
        if b:
            self.nam = "%s, %s" % (self.nam, b[0].upper())
        self.nt.loadEntry(frt, pag, p+1, data=self.nam)

    def doRepEnd(self):
        old = self.alltabs[self.oldtab]
        del self.alltabs[self.oldtab]
        tab = self.newtab[self.sql.bwltab_col.index("btb_tab")]
        a = self.newtab[self.sql.bwltab_col.index("btb_surname")]
        b = self.newtab[self.sql.bwltab_col.index("btb_names")]
        c = self.newtab[self.sql.bwltab_col.index("btb_gender")]
        d = self.newtab[self.sql.bwltab_col.index("btb_pos1")]
        e = self.newtab[self.sql.bwltab_col.index("btb_rate1")]
        self.alltabs[tab] = [a, b, c, d, e, "Y"]
        self.reptabs.append((self.oldtab, old, tab))
        self.cg.loadEntry("T", 0, self.cg.pos, data=tab)
        self.cg.loadEntry("T", 0, self.cg.pos + 1, data=self.nam)
        fini = False
        for x, d in enumerate(self.adraw3):
            for y, t in enumerate(d[2:]):
                if t[0] == self.oldtab:
                    self.adraw3[x][2+y][0] = tab
                    self.adraw3[x][2+y][1] = self.nam
                    self.adraw3[x][2+y][2] = e
                    fini = True
                    break
            if fini:
                break
        self.nt.closeProcess()

    def doRepExit(self):
        self.cg.loadEntry("T", 0, self.cg.pos, data=self.oldtab)
        self.nt.closeProcess()

    def doChgTab(self, frt, pag, r, c, p, i, w):
        if w and w not in self.alltabs:
            if p < 9:
                tab = self.adraw3[self.seq][2+(p//2)][0]
            else:
                tab = self.adraw3[self.seq+1][2+((p-8)//2)][0]
            self.cg.loadEntry(frt, pag, p, data=tab)
            return "Invalid Tab (%s), Not Entered" % w
        if not w:
            nam = ""
        else:
            nam = self.alltabs[w][0].upper()
            if self.alltabs[w][1]:
                nam = "%s, %s" % (nam, self.alltabs[w][1][0].upper())
        self.cg.loadEntry(frt, pag, p + 1, data=nam)

    def doChgEnd(self):
        q = 0
        a = 0
        z = 0
        for x in range(1, 17, 2):
            if x == 9:
                z = 1
            if z == 1:
                y = int((x - 8) / 2) + 2
            else:
                y = int(x / 2) + 2
            tab = self.cg.t_work[0][0][x]
            if not tab:
                self.adraw3[self.seq + z][y] = [0, "", 0]
            else:
                fini = False
                for d in self.adraw1:
                    for t in d[2:]:
                        if t[0] == self.cg.t_work[0][0][x]:
                            self.adraw3[self.seq + z][y] = copyList(t)
                            q += 1
                            a += t[2]
                            fini = True
                            break
                    if fini:
                        break
        for x in range(0, len(self.adraw3), 2):
            self.doAverage(self.adraw3[x], self.adraw3[x + 1])
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def doExit(self):
        if self.alltabs and not self.drawn:
            but = [
                ("Exit Without Saving", "E"),
                ("Save and Exit", "S"),
                ("Neither", "N")]
            txt = "This Draw Has Not Been Done"
            ok = askChoice(self.opts["mf"].body, "Exit",
                mess=txt, butt=but, default="None")
            if ok == "N":
                self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                return
            if ok == "S":
                self.dtype = "N"
                self.dhist = "N"
                self.tsize = 0
                self.doSave()
                for tab in self.alltabs:
                    data = [self.opts["conum"], tab, self.date, self.time,
                        "", "", "", 0, 0, 0, 0, 0, 0, 0, 0, "", ""]
                    self.sql.insRec("bwldrt", data=data)
                self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.doSetFont(self.dfs)
        self.opts["mf"].closeLoop()

    def doSetFont(self, size=24):
        self.opts["mf"].rcdic["dfs"] = size
        self.opts["mf"].setThemeFont(butt=False)
        self.opts["mf"].resizeChildren()

    def doTestDraw(self):
        # Reload an existing draw for testing purposes
        titl = "Select Draw to Load"
        cols = (
            ("date", "Date", 10, "D1", "N"),
            ("time", "T", 1, "UA", "N"),
            ("qty", "Qty", 3, "UI", "N"))
        data = self.sql.getRec("bwldrt", cols=["bdt_date", "bdt_time",
            "count(*)"], group="bdt_date, bdt_time", order="bdt_date, bdt_time")
        sel = SelectChoice(self.opts["mf"].window, titl, cols, data)
        if not sel.selection:
            return
        self.teams = {}
        self.bounce = {}
        self.alltabs = {}
        tabs = self.sql.getRec("bwldrt", cols=["bdt_tab"],
            where=[("bdt_cono", "=", self.opts["conum"]), ("bdt_date",
            "=", sel.selection[1]), ("bdt_time", "=", sel.selection[2])])
        for tab in tabs:
            self.doLoadTab(tab[0], "T", err=False)
            self.df.loadEntry("T", 1, 6, data="Y")
            if not self.df.t_work[1][0][4]:
                self.df.t_work[1][0][4] = 0
            else:
                self.df.t_work[1][0][4] = int(self.df.t_work[1][0][4])
            self.alltabs[tab[0]] = self.df.t_work[1][0][1:]
        self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)

    def doTestTabs(self, qty):
        # Load a random selection of tabs for testing purposes
        tabs = []
        self.teams = {}
        self.bounce = {}
        self.alltabs = {}
        recs = self.sql.getRec("bwltab", cols=["btb_tab"],
            where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "<", self.nstart)], group="btb_tab")
        if len(recs) < qty:
            qty = len(recs)
        for rec in recs:
            tabs.append(rec[0])
        random.shuffle(tabs)
        while len(self.alltabs) < qty:
            tab = tabs.pop()
            if self.doLoadTab(tab, "T", err=False):
                self.df.loadEntry("T", 1, 6, data="Y")
                if not self.df.t_work[1][0][4]:
                    self.df.t_work[1][0][4] = 0
                else:
                    self.df.t_work[1][0][4] = int(self.df.t_work[1][0][4])
                self.alltabs[tab] = self.df.t_work[1][0][1:]
        self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)

    def doShowQuantity(self):
        self.men = 0
        self.wom = 0
        for tab in self.alltabs:
            if self.alltabs[tab][2] == "M":
                self.men += 1
            else:
                self.wom += 1
        self.df.loadEntry("T", 0, 0, data=self.men + self.wom)
        self.df.loadEntry("T", 0, 1, data=self.men)
        self.df.loadEntry("T", 0, 2, data=self.wom)

# vim:set ts=4 sw=4 sts=4 expandtab:
