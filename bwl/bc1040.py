"""
SYNOPSIS
    Competition Types Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import askQuestion, callModule, getNextCode

class bc1040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "args" not in self.opts:
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwltyp", "bwlpts", "bwlcmp"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        typ = {
            "stype": "R",
            "tables": ("bwltyp",),
            "cols": (
                ("bct_code", "", 0, "Cod"),
                ("bct_desc", "", 0, "Description", "Y")),
            "where": [("bct_cono", "=", self.opts["conum"])]}
        r1s = (
            ("Tournament", "T"),
            ("K/Out (D)", "D"),
            ("K/Out (N)", "K"),
            ("R/Robin", "R"),
            ("Teams", "X"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"I@bct_code",0,"","",
                0,"Y",self.doTypCod,typ,None,("efld",)),
            (("T",0,1,0),"I@bct_desc",0,"","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)),
            (("T",0,2,0),("IRB",r1s),0,"Competition Format","",
                "T","N",self.doCFmat,None,None,None,None,
                """Select the Competition Format as follows:

Tournament: The default format for tournaments.
K/Out (D): This is for all Drawn Knockout Competitions.
K/Out (N): This is for Normal Knockout Competitions.
R/Robin: This is for Round Robin Competitions.
Teams: This is for Team Competitions e.g. Club V Club.
"""),
            (("T",0,3,0),"I@bct_tsize",0,"","",
                4,"N",self.doTSize,None,None,("notzero",)),
            (("T",0,4,0),"I@bct_games",0,"","",
                0,"N",self.doGames,None,None,("notzero",)),
            (("T",0,5,0),"I@bct_ends",0,"","",
                21,"N",self.doEnds,None,None,("notzero",)),
            (("T",0,6,0),("IRB",r2s),0,"Groups by Position","",
                "N","N",self.doGroups,None,None,None,None,
                "Yes means that teams will be split into Groups after "\
                "a certain number of games based on position. No means "\
                "that teams will not be split into groups"),
            (("T",0,7,0),"I@bct_grgame",0,"","",
                0,"N",self.doGrGame,None,None,("efld",)),
            (("T",0,8,0),("IRB",r2s),0,"Adjust Scores","",
                "N","N",self.doAdjust,None,None,None),
            (("T",0,9,0),"I@bct_expunge",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"I@bct_percent",0,"","",
                100,"N",None,None,None,("efld",)),
            (("T",0,11,0),"I@bct_drawn",0,"","",
                1,"N",self.doDrawn,None,None,("efld",)),
            (("T",0,12,0),("IRB",r2s),0,"Strict S v S",
                "Strict Strength v Strength",
                "N","N",self.doSvS,None,None,None,None,
                "Yes means that teams could play against each other, again, "\
                "in ANY game. No means that teams could only play against "\
                "each other, again, in the FINAL game."),
            (("T",0,13,0),("IRB",r2s),0,"Different Drawn Games Scoring","",
                "N","N",self.doDiff,None,None,None,None,
                "Yes means that Drawn Games have a Different Scoring Format "\
                "from Strength V Strength Games."))
        but = (
            ("Print", None, self.doPrint,0,("T",0,2),None),
            ("Quit", None, self.doExit,1,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        if "args" in self.opts:
            self.df.doKeyPressed("T", 0, 0, data=self.opts["args"])
            self.df.topf[0][0][1] = "OUI"
            self.df.mstFrame.wait_window()

    def doTypCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.ctype = getNextCode(self.sql, "bwltyp", "bct_code",
                where=[("bct_cono", "=", self.opts["conum"])], last=99)
            self.df.loadEntry(frt, pag, p, data=self.ctype)
        else:
            self.ctype = w
        self.old = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", self.ctype)], limit=1)
        if not self.old:
            self.newtyp = True
        else:
            self.newtyp = False
            self.cdesc = self.old[self.sql.bwltyp_col.index("bct_desc")]
            self.cfmat = self.old[self.sql.bwltyp_col.index("bct_cfmat")]
            self.tsize = self.old[self.sql.bwltyp_col.index("bct_tsize")]
            self.ends = self.old[self.sql.bwltyp_col.index("bct_ends")]
            self.groups = self.old[self.sql.bwltyp_col.index("bct_groups")]
            self.adjust = self.old[self.sql.bwltyp_col.index("bct_adjust")]
            for num, fld in enumerate(self.old[1:-1]):
                self.df.loadEntry(frt, pag, num, data=fld)
        chk = self.sql.getRec("bwlcmp", where=[("bcm_cono", "=",
            self.opts["conum"]), ("bcm_type", "=", self.ctype)], limit=1)
        if chk:
            self.exist = True
        else:
            self.exist = False

    def doDelete(self):
        if self.newtyp:
            return
        if self.exist:
            return "There are Competitions Using this Type, Not Deleted"
        self.sql.delRec("bwltyp", where=[("bct_cono", "=", self.opts["conum"]),
            ("bct_code", "=", self.ctype)])
        self.sql.delRec("bwlpts", where=[("bcp_cono", "=", self.opts["conum"]),
            ("bcp_code", "=", self.ctype)])
        self.opts["mf"].dbm.commitDbase()

    def doDesc(self, frt, pag, r, c, p, i, w):
        if self.exist:
            ok = askQuestion(self.opts["mf"].body, "Games exist",
                """There are Competitions Using this Type.

Changes Could Adversely Affect them.

Are you Sure this is what you Want to Do?""", default="no")
            if ok == "no":
                return "ff1"

    def doCFmat(self, frt, pag, r, c, p, i, w):
        self.cfmat = w

    def doTSize(self, frt, pag, r, c, p, i, w):
        if self.cfmat == "D" and w not in (2, 3):
            return "Invalid Team Size"
        self.tsize = w
        if self.cfmat in ("D", "K", "R"):
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doGames(self, frt, pag, r, c, p, i, w):
        self.games = w

    def doEnds(self, frt, pag, r, c, p, i, w):
        self.ends = w
        if self.cfmat in ("D", "K", "R", "X"):
            if self.cfmat in ("D", "K", "R"):
                defaults = ["N", 0, "N", "", 0, 0, "N", "N"]
            else:
                defaults = ["N", 0, "N", "", 0, self.games, "N", "N"]
            for num, dat in enumerate(defaults):
                self.df.loadEntry("T", 0, p+num+1, data=dat)
            self.pdiff = "N"
            return "nd"

    def doGroups(self, frt, pag, r, c, p, i, w):
        self.groups = w
        if self.groups == "N":
            self.adjust = "N"
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data=self.adjust)
            self.df.loadEntry(frt, pag, p+3, data="")
            self.df.loadEntry(frt, pag, p+4, data="")
            return "sk4"

    def doGrGame(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid Game Number"

    def doAdjust(self, frt, pag, r, c, p, i, w):
        self.adjust = w
        if self.adjust == "N":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "sk2"

    def doDrawn(self, frt, pag, r, c, p, i, w):
        self.drawn = w
        if self.drawn == self.games:
            # All drawn games
            self.pdiff = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            self.df.loadEntry(frt, pag, p+2, data="N")
            return "sk2"

    def doSvS(self, frt, pag, r, c, p, i, w):
        if not self.drawn:
            self.pdiff = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doDiff(self, frt, pag, r, c, p, i, w):
        self.pdiff = w

    def doEnd(self):
        data = [self.opts["conum"]] + self.df.t_work[0][0]
        if self.newtyp:
            self.sql.insRec("bwltyp", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bwltyp_col
            data.append(self.old[col.index("bct_xflag")])
            self.sql.updRec("bwltyp", data=data, where=[("bct_cono", "=",
                self.opts["conum"]), ("bct_code", "=", self.ctype)])
        self.perr = False
        if self.cfmat in ("D", "K", "R"):
            if self.newtyp:
                self.sql.insRec("bwlpts", data=[self.opts["conum"],
                    self.ctype, "D", "N", 0, "N", 0, 0, 0, "N", 0, 0])
        else:
            self.df.setWidget(self.df.mstFrame, state="hide")
            if self.pdiff == "Y":
                self.doPtsFmt("D")
            if not self.perr:
                if self.pdiff == "Y":
                    self.doPtsFmt("S")
                else:
                    self.doPtsFmt("B")
            self.df.setWidget(self.df.mstFrame, state="show")
        if self.perr:
            self.opts["mf"].dbm.rollbackDbase()
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        else:
            self.opts["mf"].dbm.commitDbase()
            if "args" in self.opts:
                self.doExit()
            else:
                self.df.focusField("T", 0, 1)

    def doPtsFmt(self, flag=None):
        self.flag = flag
        if flag == "D":
            txt = "Points Format for Drawn Games"
        elif flag == "S":
            txt = "Points Format for SvS Games"
        else:
            txt = "Points Format"
        tit = (txt,)
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Skins","",
                "N","N",self.doSkins,None,None,None),
            (("T",0,1,0),"I@bcp_sends",0,"","",
                0,"N",self.doEndsPerSkin,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Points Only","",
                "N","N",self.doOnly,None,None,None,None,
                "Yes means that No Shots are to be captured and that only "\
                "Points will be used to determine positions. No means that "\
                "Shots and Points are to be captured and used to determine "\
                "positions."),
            (("T",0,3,0),"I@bcp_e_points",0,"","",
                0,"N",self.doPoints,None,None,("efld",)),
            (("T",0,4,0),"I@bcp_s_points",0,"","",
                0,"N",None,None,None,("efld",)),
            (("T",0,5,0),"I@bcp_g_points",0,"","",
                0,"N",None,None,None,("efld",)),
            (("T",0,6,0),("IRB",r1s),0,"Bonus Points","",
                "N","N",self.doBonus,None,None,None),
            (("T",0,7,0),"I@bcp_win_by",0,"","",
                0,"N",None,None,None,("efld",)),
            (("T",0,8,0),"I@bcp_lose_by",0,"","",
                0,"N",None,None,None,("efld",)))
        but = (("Quit", None, self.doPExit,1,None,None),)
        tnd = ((self.doPEnd,"y"),)
        txt = (self.doPExit,)
        self.pf = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        if self.flag in ("D", "S"):
            ptyp = self.flag
        else:
            ptyp = "D"
        acc = self.sql.getRec("bwlpts", where=[("bcp_cono",
            "=", self.opts["conum"]), ("bcp_code", "=", self.ctype),
            ("bcp_ptyp", "=", ptyp)], limit=1)
        if acc:
            self.newpts = False
            for num, dat in enumerate(acc[3:-1]):
                self.pf.loadEntry("T", 0, num, data=dat)
        else:
            self.newpts = True
        self.pf.focusField("T", 0, 1, clr=False)
        self.pf.mstFrame.wait_window()

    def doSkins(self, frt, pag, r, c, p, i, w):
        self.skins = w
        if self.skins == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doEndsPerSkin(self, frt, pag, r, c, p, i, w):
        if self.ends % w:
            return "Invalid Ends per Skin, Not Divisible"

    def doOnly(self, frt, pag, r, c, p, i, w):
        self.ponly = w

    def doPoints(self, frt, pag, r, c, p, i, w):
        if self.skins == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doBonus(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "nd"

    def doPEnd(self):
        self.pf.closeProcess()
        data = [self.opts["conum"], self.ctype, ""]
        data.extend(self.pf.t_work[0][0])
        if self.flag == "B":
            if not self.newpts:
                self.sql.delRec("bwlpts", where=[("bcp_cono", "=",
                    self.opts["conum"]), ("bcp_code", "=", self.ctype)])
            data[2] = "D"
            self.sql.insRec("bwlpts", data=data)
            data[2] = "S"
            self.sql.insRec("bwlpts", data=data)
        else:
            if not self.newpts:
                self.sql.delRec("bwlpts", where=[("bcp_cono", "=",
                    self.opts["conum"]), ("bcp_code", "=", self.ctype),
                    ("bcp_ptyp", "=", self.flag)])
            data[2] = self.flag
            self.sql.insRec("bwlpts", data=data)

    def doPExit(self):
        self.perr = True
        self.pf.closeProcess()

    def doPrint(self):
        if not self.newtyp:
            callModule(self.opts["mf"], None, "bc3080",
                coy=[self.opts["conum"], self.opts["conam"]],
                args=[self.ctype, self.cdesc])
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doExit(self):
        self.df.closeProcess()
        if "args" not in self.opts:
            if "wait" not in self.opts:
                self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
