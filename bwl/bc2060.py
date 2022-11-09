"""
SYNOPSIS
    Bowls Competition Draw Maintenance.

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
from tartanFunctions import askQuestion, showError

class bc2060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        t = time.localtime()
        self.today = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwltab", "bwlgme",
            "bwltyp", "bwlent"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        skp = {
            "stype": "R",
            "tables": ("bwltab", "bwlgme"),
            "cols": (
                ("btb_tab", "", 0, "Cod"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names"),
                ("bcg_rink", "", 0, "RK"),
                ("bcg_ocod", "", 0, "Opp")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("bcg_cono=btb_cono",),
                ("bcg_scod=btb_tab",)],
            "whera": [
                ("T", "bcg_ccod", 0, 0),
                ("T", "bcg_game", 2, 0)],
            "group": "btb_tab",
            "order": "btb_tab"}
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","Y",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"I@bcg_game",0,"Game Number","",
                1,"N",self.doGame,None,None,("efld",)),
            (("T",0,1,0),"I@bcg_date",0,"Date","",
                self.today,"N",self.doDate,None,None,("efld",)),
            (("T",0,2,0),"IUA",35,"Greens","Greens (A,B,C)",
                "","N",self.doGreens,None,None,("efld",),None,"Available "\
                "Greens in the format A,B or A,B345 showing Green Code and "\
                "Rinks. If the Rinks are Not Entered they will Default to 6."),
            (("C",0,0,0),"I@bcg_scod",0,"","",
                "","N",self.doSkpCod,skp,None,("notzero",)),
            (("C",0,0,0),"ONA",30,"Skp-Name"),
            (("C",0,0,0),"I@bcg_ocod",0,"","",
                "","N",self.doOppCod,skp,None,("notzero",)),
            (("C",0,0,0),"ONA",30,"Opp-Name"),
            (("C",0,0,0),"I@bcg_rink",0,"","",
                "","N",self.doRink,None,None,("notblank",)))
        but = (("Quit",None,self.doQuit,1,None,None),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"y"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        com = self.sql.getRec("bwlcmp", cols=["bcm_name", "bcm_date",
            "bcm_type"], where=[("bcm_cono", "=", self.opts["conum"]),
            ("bcm_code", "=", w)], limit=1)
        if not com:
            return "Invalid Competition Code"
        name, self.sdat, ctyp = com
        self.df.loadEntry(frt, pag, p+1, data=name)
        chk = self.sql.getRec("bwltyp", cols=["bct_cfmat"],
            where=[("bct_cono", "=", self.opts["conum"]), ("bct_code", "=",
            ctyp)], limit=1)
        if chk[0] in ("D", "K", "R"):
            return "Knockout and R/Robin Draws Cannot be Changed"
        chk = self.sql.getRec("bwlgme", cols=["bcg_game", "bcg_date",
            "bcg_aflag", "sum(bcg_ocod)", "sum(bcg_sfor)"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            w)], group="bcg_game, bcg_date, bcg_aflag")
        self.ccod = w
        self.game = 0
        self.draws = {}
        self.manual = False
        for ck in chk:
            if ck[2] == "A" or ck[4]:
                continue
            if ck[4]:
                continue
            if ck[2] in ("", "D", "S") and ck[3]:
                self.draws[ck[0]] = ck[1:]
        if not self.draws:
            ok = askQuestion(self.opts["mf"].body, "Manual Draw",
                "Is this the First Game and is it going to be a "\
                "Manual Draw?", default="no")
            if ok == "no":
                return "rf"
            self.manual = True
            self.game = 1
            self.df.loadEntry(frt, pag, p+2, data=self.game)
            self.totskp = self.sql.getRec("bwlent", cols=["count(*)"],
                where=[("bce_cono", "=", self.opts["conum"]), ("bce_ccod", "=",
                self.ccod)], limit=1)[0]
            return "sk2"

    def doGame(self, frt, pag, r, c, p, i, w):
        if w not in self.draws:
            return "Invalid Game Number"
        self.game = w
        self.date = self.draws[w][0]
        self.df.loadEntry(frt, pag, p+1, data=self.date)
        self.totskp = self.sql.getRec("bwlent", cols=["count(*)"],
            where=[("bce_cono", "=", self.opts["conum"]), ("bce_ccod", "=",
            self.ccod)], limit=1)[0]

    def doDate(self, frt, pag, r, c, p, i, w):
        if w < self.today or w < self.sdat:
            return "Invalid Date, in the Past or Before the Starting Date"
        self.date = w

    def doGreens(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Greens"
        self.rinks = []
        rinks = 0
        grns = w.split(",")
        for gr in grns:
            if len(gr) == 1:
                for x in range(1, 7):
                    self.rinks.append("%s%s" % (gr[0], x))
                rinks += 6
            elif len(gr) == 2 and gr[1] == "7":
                for x in range(1, 8):
                    self.rinks.append("%s%s" % (gr[0], x))
                rinks += 7
            else:
                for rk in gr[1:]:
                    self.rinks.append("%s%s" % (gr[0], rk))
                    rinks += 1
        if int(self.totskp / 2) > rinks:
            return "Not Enough Rinks"

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        skp = self.sql.getRec(tables=["bwlgme", "bwltab"], cols=["btb_surname",
            "btb_names", "bcg_ocod", "bcg_rink"], where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_scod",
            "=", w), ("bcg_game", "=", self.game), ("btb_cono=bcg_cono",),
            ("btb_tab=bcg_scod",)], limit=1)
        if not skp:
            return "Invalid Skip Code"
        self.skip = w
        self.old_opp = skp[2]
        self.old_rink = skp[3]
        if skp[1]:
            name = "%s, %s" % tuple(skp[:2])
        else:
            name = skp[0]
        self.df.loadEntry(frt, pag, p+1, data=name)
        if self.old_opp:
            self.df.loadEntry(frt, pag, p+2, data=self.old_opp)
            opp = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", skp[2])], limit=1)
            if opp[1]:
                name = "%s, %s" % tuple(opp[:2])
            else:
                name = opp[0]
            self.df.loadEntry(frt, pag, p+3, data=name)
        if self.old_rink:
            self.df.loadEntry(frt, pag, p+4, data=self.old_rink)

    def doOppCod(self, frt, pag, r, c, p, i, w):
        opp = self.sql.getRec(tables=["bwlgme", "bwltab"], cols=["btb_surname",
            "btb_names", "bcg_ocod", "bcg_rink"], where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_scod",
            "=", w), ("bcg_game", "=", self.game), ("btb_cono=bcg_cono",),
            ("btb_tab=bcg_scod",)], limit=1)
        if not opp:
            return "Invalid Opponents Code"
        self.new_opp = w
        self.chg_skp = opp[2]
        if opp[1]:
            name = "%s, %s" % tuple(opp[:2])
        else:
            name = opp[0]
        self.df.loadEntry(frt, pag, p+1, data=name)

    def doRink(self, frt, pag, r, c, p, i, w):
        if w not in self.rinks:
            return "Invalid Rink"
        self.new_rink = w

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
        else:
            self.df.advanceLine(0)
            self.sql.updRec("bwlgme", cols=["bcg_date", "bcg_ocod",
                "bcg_rink"], data=[self.date, self.new_opp, self.new_rink],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_scod", "=", self.skip), ("bcg_game", "=",
                self.game)])
            self.sql.updRec("bwlgme", cols=["bcg_date", "bcg_ocod",
                "bcg_rink"], data=[self.date, self.skip, self.new_rink],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_scod", "=", self.new_opp), ("bcg_game",
                "=", self.game)])

    def doExit(self):
        if self.df.frt == "C":
            chk = self.sql.getRec("bwlgme", cols=["bcg_ocod",
                "count(*)"], where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game)],
                group="bcg_ocod", order="bcg_ocod")
            for c in chk:
                if c[0] and c[1] != 1:
                    skp = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                        where=[("bcg_cono", "=", self.opts["conum"]),
                        ("bcg_ccod", "=", self.ccod), ("bcg_game", "=",
                        self.game), ("bcg_ocod", "=", c[0])], order="bcg_scod")
                    err = "Opponent %s is Drawn Against %s Skips\n" % tuple(c)
                    for s in skp:
                        err = err + "\nSkip %s" % s[0]
                    skp = self.sql.sqlRec("Select bce_scod from bwlent where "\
                        "bce_ccod = %s and bce_scod not in (select bcg_ocod "\
                        "from bwlgme where bcg_ccod = %s and bcg_game = %s)" %
                        (self.ccod, self.ccod, self.game))
                    err = err + "\n\nSkips Without Opponents\n"
                    for s in skp:
                        err = err + "\nSkip %s" % s[0]
                    showError(self.opts["mf"].body, "Skip Error", err)
                    self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                    return
            chk = self.sql.getRec("bwlgme", cols=["bcg_rink",
                "count(*)"], where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game)],
                group="bcg_rink", order="bcg_rink")
            for c in chk:
                if c[1] != 2:
                    skp = self.sql.getRec("bwlgme", cols=["bcg_scod",
                        "bcg_ocod"], where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_game", "=", self.game), ("bcg_rink", "=", c[0])],
                        group="bcg_scod, bcg_ocod, bcg_rink", order="bcg_scod")
                    skps = []
                    for s in skp:
                        if [s[1], s[0]] not in skps:
                            skps.append(s)
                    err = "Rink %s Shows %s time(s)\n" % (c[0], int(c[1] / 2))
                    for s in skps:
                        err = err + "\nSkip %2s Opp %2s" % (s[0], s[1])
                    rnk = self.sql.getRec("bwlgme", cols=["bcg_rink",
                        "count(*)"], where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                        ("bcg_game", "=", self.game)], group="bcg_rink",
                        order="bcg_rink")
                    rnks = []
                    for r in rnk:
                        rnks.append(r[0])
                    mis = ""
                    for r in self.rinks:
                        if r not in rnks:
                            if not mis:
                                mis = r
                            else:
                                mis = "%s, %s" % (mis, r)
                    err = err + "\n\nAvailable Rink(s)\n\n%s" % mis
                    showError(self.opts["mf"].body, "Rink Error", err)
                    self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                    return
            self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doQuit(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
