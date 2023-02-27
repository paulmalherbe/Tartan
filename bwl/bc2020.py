"""
SYNOPSIS
    Bowls League Selections.

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

from TartanClasses import GetCtl, MyFpdf, TartanDialog, Sql
from tartanFunctions import askQuestion, dateDiff, doDrawTable, doPrinter
from tartanFunctions import getModName, getNextCode, showError
from tartanWork import mthnam

class bc2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.nstart = bwlctl["ctb_nstart"]
        self.fromad = bwlctl["ctb_emadd"]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "bwlclb", "bwlflf",
            "bwlflm", "bwlflo", "bwltab", "bwlfls", "bwlflt"],
                prog=self.__class__.__name__)
        if self.sql.error:
            return
        acc = self.sql.getRec("bwlclb", where=[("bcc_code", "=",
            self.opts["conum"])])
        if not acc:
            self.sql.insRec("bwlclb", data=[self.opts["conum"],
                self.opts["conam"]])
            self.opts["mf"].dbm.commitDbase()
        self.reprint = False
        self.fmat = 0
        self.date = 0
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
        sid = {
            "stype": "R",
            "tables": ("bwlfls",),
            "cols": (
                ("bfs_code", "", 0, "Cod"),
                ("bfs_desc", "", 0, "Description", "Y"),
                ("bfs_division", "", 0, "DV")),
            "where": [
                ("bfs_cono", "=", self.opts["conum"]),
                ("bfs_active", "=", "Y")],
            "whera": [("T", "bfs_fmat", 0, 0)],
            "order": "bfs_desc"}
        opp = {
            "stype": "R",
            "tables": ("bwlflo",),
            "cols": (
                ("bfo_code", "", 0, "Cod"),
                ("bfo_desc", "", 0, "Description", "Y")),
            "where": [("bfo_cono", "=", self.opts["conum"])],
            "whera": [("T", "bfo_fmat", 0, 0)],
            "order": "bfo_desc"}
        self.plr = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Cod"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names")),
            "where": [],
            "order": "btb_surname, btb_names"}
        r1s = (("Fixture", "F"), ("Practice", "P"))
        fld = (
            (("T",0,0,0),"I@bfm_fmat",0,"","",
                "","Y",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "F","N",self.doType,None,None,None),
            (("T",0,2,0),"I@bfm_date",0,"","",
                "","N",self.doDate,None,None,("efld",)),
            (("T",0,3,0),"I@bfm_round",0,"","",
                "","N",self.doRound,None,None,("notzero",)),
            (("T",0,4,0),"I@bfm_team",0,"","",
                "","N",self.doSide,sid,None,None),
            (("T",0,4,0),"ONA",20,""),
            (("T",0,5,0),"I@bfm_opps",0,"","",
                "","N",self.doOpp,opp,None,None),
            (("T",0,5,0),"ONA",30,""),
            (("T",0,6,0),"I@bfm_venue",0,"Venue (H/A/Name)","",
                "","N",self.doVenue,None,None,("efld",)),
            (("T",0,7,0),"IUD",5.2,"Meeting Time","",
                "","N",self.doMTime,None,None,("efld",)),
            (("T",0,7,0),"INA",20," At (H/A/Name)","",
                "H","N",self.doMPlace,None,None,("efld",)),
            (("T",0,8,0),"I@bfm_captain",0,"","",
                "","N",self.doCaptain,self.plr,None,("notzero",)),
            (("T",0,8,0),"ONA",30,""),
            (("C",0,0,1),"I@bft_skip",0,"Skp","",
                "","N",self.doSkip,self.plr,None,("notzero",)),
            (("C",0,0,2),"ONA",20,""),
            (("C",0,0,3),"I@bft_player",0,"3rd","",
                "","N",self.doPlayer,self.plr,None,("notzero",)),
            (("C",0,0,4),"ONA",20,""),
            (("C",0,0,5),"I@bft_player",0,"2nd","",
                "","N",self.doPlayer,self.plr,None,("notzero",)),
            (("C",0,0,6),"ONA",20,""),
            (("C",0,0,7),"I@bft_player",0,"1st","",
                "","N",self.doPlayer,self.plr,None,("notzero",)),
            (("C",0,0,8),"ONA",20,""))
        but = (("Quit",None,self.doQuit,1,None,None),)
        tnd = ((self.doEnd,"n"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"n"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, rows=[3], butt=but, tend=tnd, txit=txt, cend=cnd,
            cxit=cxt)

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Format"
        self.fmat = w
        self.fdes = acc[self.sql.bwlflf_col.index("bff_desc")].upper()
        self.plr["where"] = [
            ("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "<", self.nstart)]
        gndr = acc[self.sql.bwlflf_col.index("bff_gender")]
        if gndr in ("F", "M"):
            self.plr["where"].append(("btb_gender", "=", gndr))
        self.assess = acc[self.sql.bwlflf_col.index("bff_assess")]
        self.df.loadEntry(frt, pag, p+1, data=self.fdes)

    def doType(self, frt, pag, r, c, p, i, w):
        self.ftyp = w

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.disp = "%i %s %i" % (w % 100, mthnam[int(w / 100) % 100][1],
            int(w / 10000))
        acc = self.sql.getRec("bwlflt", cols=["sum(bft_shotsf)"],
            where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
            self.fmat), ("bft_type", "=", self.ftyp), ("bft_date", "=",
            self.date)], limit=1)
        self.reprint = False
        if acc[0]:
            self.reprint = True
            return "xt"
        if acc[0] == 0:
            # Edit
            acc = self.sql.getRec("bwlflm", cols=["bfm_round"],
                where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
                self.fmat), ("bfm_type", "=", self.ftyp), ("bfm_date", "=",
                self.date)], limit=1)
            self.rnd = acc[0]
        else:
            # New
            acc = self.sql.getRec("bwlflm", cols=["max(bfm_date)",
                "max(bfm_round)"], where=[("bfm_cono", "=",
                self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_type",
                "=", self.ftyp)], limit=1)
            if not acc[0] or dateDiff(acc[0], self.date, ptype="months") > 6:
                self.rnd = 1
            else:
                self.rnd = acc[1] + 1
        self.df.loadEntry(frt, pag, p+1, data=self.rnd)

    def doRound(self, frt, pag, r, c, p, i, w):
        if w != self.rnd:
            ok = askQuestion(self.opts["mf"].body, "Round Change",
                "The Round Has Been Changed, Please Confirm", default="no")
            if ok == "no":
                return "Invalid Round Number"
            self.sql.updRec("bwlflm", cols=["bfm_round"], data=[w],
                where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat",
                "=", self.fmat), ("bfm_type", "=", self.ftyp), ("bfm_date",
                "=", self.date)])
        self.rnd = w

    def doSide(self, frt, pag, r, c, p, i, w):
        if not w:
            if askQuestion(self.opts["mf"].body, "New Side",
                    "Do You Want to Enter a New Side") == "yes":
                w = self.enterNewSide()
                self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("bwlfls", cols=["bfs_desc", "bfs_number"],
            where=[("bfs_cono", "=", self.opts["conum"]), ("bfs_fmat", "=",
            self.fmat), ("bfs_code", "=", w), ("bfs_active", "=", "Y")],
            limit=1)
        if not acc:
            return "Invalid Side"
        self.team = w
        self.qty = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        acc = self.sql.getRec(tables=["bwlflm", "bwlfls", "bwlflo", "bwltab"],
            cols=["bfo_code", "bfo_desc", "bfm_venue", "bfm_mtime",
            "bfm_mplace", "bfm_captain", "btb_surname", "btb_names"],
            where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
            self.fmat), ("bfm_date", "=", self.date), ("bfm_team", "=",
            self.team), ("bfs_cono=bfm_cono",), ("bfs_fmat=bfm_fmat",),
            ("bfs_code=bfm_team",), ("bfo_cono=bfm_cono",),
            ("bfo_fmat=bfm_fmat",), ("bfo_code=bfm_opps",),
            ("btb_cono=bfm_cono",), ("btb_tab=bfm_captain",)], limit=1)
        if acc:
            self.opp = acc[0]
            self.venue = acc[2]
            self.mtime = acc[3]
            self.mplace = acc[4]
            self.captain = acc[5]
            for x in range(6):
                self.df.loadEntry(frt, pag, p+x+2, data=acc[x])
            self.df.loadEntry(frt, pag, p+8, data=self.getName(acc[6], acc[7]))
            self.loadPlayers()
        else:
            for x in range(c+2, c+9):
                self.df.clearEntry("T", 0, x)
            self.df.clearFrame("C", 0)
            # Get previous captain
            acc = self.sql.getRec(tables=["bwlflm", "bwltab"],
                cols=["bfm_captain", "btb_surname", "btb_names"],
                where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
                self.fmat), ("bfm_team", "=", self.team),
                ("btb_cono=bfm_cono",), ("btb_tab=bfm_captain",)],
                order="bfm_date desc", limit=1)
            if acc:
                self.df.loadEntry("T", 0, 12, data=acc[0])
                self.df.loadEntry("T", 0, 13, data=self.getName(acc[1],
                    acc[2]))
            # Get previous team members
            col = ["bft_date", "bft_player", "btb_surname", "btb_names"]
            odr = "bft_date desc, bft_skip, bft_position"
            acc = self.sql.getRec(tables=["bwlflt", "bwltab"], cols=col,
                where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
                self.fmat), ("bft_type", "=", self.ftyp), ("bft_team", "=",
                self.team), ("btb_cono=bft_cono",), ("btb_tab=bft_player",)],
                order=odr)
            if acc:
                date = acc[0][0]
                for num, data in enumerate(acc):
                    if data[0] != date:
                        break
                    pos = num * 2
                    self.df.loadEntry("C", 0, pos, data=data[1])
                    self.df.loadEntry("C", 0, pos+1, data=self.getName(data[2],
                        data[3]))

    def doOpp(self, frt, pag, r, c, p, i, w):
        if not w:
            if askQuestion(self.opts["mf"].body, "New Opponent",
                    "Do You Want to Enter a New Opponent") == "yes":
                w = self.enterNewOpp()
                self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("bwlflm", where=[("bfm_cono", "=",
            self.opts["conum"]), ("bfm_fmat", "=", self.fmat), ("bfm_date",
            "=", self.date), ("bfm_opps", "=", w), ("bfm_team", "<>",
            self.team)], limit=1)
        if acc:
            return "Invalid Opposition, Already Selected"
        acc = self.sql.getRec("bwlflo", cols=["bfo_desc"],
            where=[("bfo_cono", "=", self.opts["conum"]), ("bfo_fmat", "=",
            self.fmat), ("bfo_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Opposition"
        self.opp = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def loadPlayers(self):
        acc = self.sql.getRec(tables=["bwlflt", "bwltab"], cols=["bft_player",
            "btb_surname", "btb_names"], where=[("bft_cono", "=",
            self.opts["conum"]), ("bft_fmat", "=", self.fmat), ("bft_type",
            "=", self.ftyp), ("bft_date", "=", self.date), ("bft_team", "=",
            self.team), ("btb_cono=bft_cono",), ("btb_tab=bft_player",)],
            order="bft_skip, bft_position")
        if acc:
            for num, name in enumerate(acc):
                pos = num * 2
                self.df.loadEntry("C", 0, pos, data=name[0])
                self.df.loadEntry("C", 0, pos+1, data=self.getName(name[1],
                    name[2]))

    def doVenue(self, frt, pag, r, c, p, i, w):
        w = w.strip()
        if len(w.strip()) == 1:
            w = w.upper()
            if w not in ("A", "H"):
                return "Invalid Venue"
        self.venue = w
        self.df.loadEntry(frt, pag, p, data=self.venue)
        if not self.df.t_work[0][0][p+1]:
            if self.venue == "H":
                self.df.loadEntry(frt, pag, p+1, data=1.30)
            else:
                self.df.loadEntry(frt, pag, p+1, data=1.15)

    def doMTime(self, frt, pag, r, c, p, i, w):
        self.mtime = w

    def doMPlace(self, frt, pag, r, c, p, i, w):
        w = w.strip()
        if len(w.strip()) == 1:
            w = w.upper()
            if w not in ("A", "H"):
                return "Invalid Place"
        self.mplace = w
        self.df.loadEntry(frt, pag, p, data=self.mplace)

    def doCaptain(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "=", w)], limit=1)
        if not acc:
            return "Invalid Tab"
        self.captain = w
        self.df.loadEntry(frt, pag, p+1, data=self.getName(acc[0], acc[1]))

    def doSkip(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "=", w)], limit=1)
        if not acc:
            return "Invalid Tab"
        self.skip = w
        self.df.loadEntry(frt, pag, p+1, data=self.getName(acc[0], acc[1]))

    def doPlayer(self, frt, pag, r, c, p, i, w):
        if w == self.skip:
            return "Invalid Player, This is the Skip"
        acc = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "=", w)], limit=1)
        if not acc:
            return "Invalid Tab"
        self.df.loadEntry(frt, pag, p+1, data=self.getName(acc[0], acc[1]))

    def enterNewSide(self):
        tit = ("New Side",)
        lge = (("Main", "M"), ("Friendly", "F"))
        fld = (
            (("T",0,0,0),"I@bfs_desc",0,"","",
                "","N",None,None,None,("notblank",)),
            (("T",0,1,0),("IRB",lge),0,"League","",
                "M","N",None,None,None,None),
            (("T",0,2,0),"I@bfs_division",0,"","",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"I@bfs_number",0,"","",
                "","N",None,None,None,("notzero",)))
        state = self.df.disableButtonsTags()
        self.new = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doSideEnd,"y"),), txit=(self.doSideExit,))
        self.new.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        return self.team

    def doSideEnd(self):
        team = self.sql.getRec("bwlfls", cols=["max(bfs_code)"],
            where=[("bfs_cono", "=", self.opts["conum"]), ("bfs_fmat", "=",
            self.fmat)], limit=1)
        if not team[0]:
            self.team = 1
        else:
            self.team = team[0] + 1
        self.sql.insRec("bwlfls", data=[self.opts["conum"], self.fmat,
            self.team] + self.new.t_work[0][0] + ["Y"])
        self.opts["mf"].dbm.commitDbase()
        self.new.closeProcess()

    def doSideExit(self):
        self.team = 0
        self.new.closeProcess()

    def enterNewOpp(self):
        tit = ("New Opponent",)
        clb = {
            "stype": "R",
            "tables": ("bwlclb",),
            "cols": (
                ("bcc_code", "", 0, "Cod"),
                ("bcc_name", "", 0, "Name", "Y"))}
        fld = (
            (("T",0,0,0),"I@bcc_code",0,"","",
                "","N",self.doClubCode,clb,None,("efld",)),
            (("T",0,0,0),"I@bcc_name",0,"","",
                "","N",self.doClubDesc,None,None,("notblank",)),
            (("T",0,1,0),"I@bfo_desc",0,"","",
                "","N",None,None,None,("notblank",)))
        state = self.df.disableButtonsTags()
        self.nop = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doOppEnd,"y"),), txit=(self.doOppExit,))
        self.nop.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        return self.opp

    def doClubCode(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlclb", where=[("bcc_code", "=", w)],
            limit=1)
        if acc:
            self.nop.loadEntry(frt, pag, p+1, data=acc[1])
            return "sk1"

    def doClubDesc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlclb", where=[("bcc_name", "=", w)],
            limit=1)
        if acc:
            self.nop.loadEntry(frt, pag, p-1, data=acc[0])
        else:
            self.club = getNextCode(self.sql, "bwlclb", "bcc_code", last=999)
            self.nop.loadEntry(frt, pag, p-1, data=self.club)
            self.sql.insRec("bwlclb", data=[self.club, w])
            self.opts["mf"].dbm.commitDbase()

    def doOppEnd(self):
        opp = self.sql.getRec("bwlflo", where=[("bfo_cono", "=",
            self.opts["conum"]), ("bfo_fmat", "=", self.fmat), ("bfo_desc",
            "=", self.nop.t_work[0][0][2])], limit=1)
        if opp:
            self.opp = opp[1]
        else:
            opp = self.sql.getRec("bwlflo", cols=["max(bfo_code)"],
                where=[("bfo_cono", "=", self.opts["conum"]), ("bfo_fmat", "=",
                self.fmat)], limit=1)
            if not opp[0]:
                self.opp = 1
            else:
                self.opp = opp[0] + 1
            self.sql.insRec("bwlflo", data=[self.opts["conum"], self.fmat,
                self.opp, self.nop.t_work[0][0][0], self.nop.t_work[0][0][2]])
            self.opts["mf"].dbm.commitDbase()
        self.nop.closeProcess()

    def doOppExit(self):
        self.opp = 0
        self.nop.closeProcess()

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
        elif self.df.row == (self.qty - 1):
            self.doUpdate()
        else:
            self.df.advanceLine(0)

    def doUpdate(self):
        self.sql.delRec("bwlflm", where=[("bfm_cono", "=", self.opts["conum"]),
            ("bfm_fmat", "=", self.fmat), ("bfm_type", "=", self.ftyp),
            ("bfm_date", "=", self.date), ("bfm_team", "=", self.team)])
        self.sql.insRec("bwlflm", data=[self.opts["conum"], self.fmat,
            self.ftyp, self.date, self.rnd, self.team, self.opp, self.venue,
            self.mtime, self.mplace, self.captain])
        self.sql.delRec("bwlflt", where=[("bft_cono", "=", self.opts["conum"]),
            ("bft_fmat", "=", self.fmat), ("bft_type", "=", self.ftyp),
            ("bft_date", "=", self.date), ("bft_team", "=", self.team)])
        for x in range(self.qty):
            for y in range(4):
                data = [self.opts["conum"], self.fmat, self.ftyp, self.date,
                    self.team, self.df.c_work[0][x][0],
                    self.df.c_work[0][x][y*2], y+1, 0, 0, 0, 0, 0, 0, 0, ""]
                acc = self.sql.getRec("bwlflt", where=[("bft_cono", "=",
                    data[0]), ("bft_fmat", "=", data[1]), ("bft_type", "=",
                    data[2]), ("bft_date", "=", data[3]), ("bft_team", "=",
                    data[4]), ("bft_player", "=", data[6])], limit=1)
                if acc:
                    showError(self.opts["mf"].body, "Duplicate",
                        "Player Code %s is Entered More than Once" % data[6])
                    self.df.focusField("C", 0, 1)
                    self.opts["mf"].dbm.rollbackDbase()
                    return
                self.sql.insRec("bwlflt", data=data)
        for x in range(6, 15):
            self.df.clearEntry("T", 0, x)
        self.df.clearFrame("C", 0)
        self.df.skip = [[1, 2, 3, 4, 5]]
        self.df.focusField("T", 0, 6)

    def doExit(self):
        if self.df.frt == "C":
            self.df.focusField("C", 0, self.df.col)
            return
        if not self.fmat or not self.date:
            self.df.closeProcess()
            self.opts["mf"].closeLoop()
            return
        plrs = {}
        acc = self.sql.getRec("bwlflt", cols=["bft_player", "bft_team",
            "bft_skip", "bft_position"], where=[("bft_cono", "=",
            self.opts["conum"]), ("bft_fmat", "=", self.fmat), ("bft_type",
            "=", self.ftyp), ("bft_date", "=", self.date)], order="bft_player")
        for a in acc:
            if a[0] in plrs:
                showError(self.opts["mf"].body, "Duplicate",
                    "Player Code %s is in Team Codes %s and %s" % (a[0],
                    plrs[a[0]][0], a[1]))
                self.df.focusField("T", 0, 6)
                return
            else:
                plrs[a[0]] = [a[1], a[2], a[3]]
        self.df.closeProcess()
        if not self.reprint:
            self.opts["mf"].dbm.commitDbase()
        ok = askQuestion(self.opts["mf"].body, "Print",
            "Do You Want to View/Print the Selections")
        if ok == "yes":
            self.doPrintSelection()
        self.opts["mf"].closeLoop()

    def doPrintSelection(self):
        fld = (
            (("T",0,0,0),"INA",70,"Note-Line-1","",
                "","N",None,None,None,("efld",)),
            (("T",0,1,0),"INA",70,"Note-Line-2","",
                "","N",None,None,None,("efld",)))
        self.pr = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=((self.doPrint,"y"),), txit=None, view=("N","V"),
            mail=("Y","N"))
        self.pr.mstFrame.wait_window()

    def doPrint(self):
        self.pr.closeProcess()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, "select_%s" % self.date, ext="pdf")
        fpdf = MyFpdf(name=self.__class__.__name__, head=90)
        cw = fpdf.get_string_width("X")           # character width
        ld = 4.5                                  # line depth
        fm = {
            "margins": ((10, 80), (5, 12.5)),     # left, right, top, bottom
            "repeat": (1, 5),                     # repeat across and below
            "rows": (                             # x, y, w, h, fill, text, qty
                (10, 5, 80, 1.5, .8),
                (10, 6.5, (
                    (10, 1.5, .9, ("Skip", "Third", "Second", "Lead")),
                    (23, 1.5), (23, 1.5), (24, 1.5)), 4),
                (10, 12.5, 80, 1.5))}
        ff = {
            "margins": ((10, 80), ((5, 15))),     # left, right, top, bottom
            "repeat": (1, 3),                     # repeat across and below
            "rows": (                             # x, y, w, h, fill, text, qty
                (10, 5, 80, 2, .8),
                (10, 7, (
                    (10, 2, .9, ("Skip", "Third", "Second", "Lead")),
                    (70, 2)), 4),
                (10, 15, 80, 2))}
        for div in ("Main", "Friendly"):
            whr = [
                ("bfm_cono", "=", self.opts["conum"]),
                ("bfm_fmat", "=", self.fmat),
                ("bfm_type", "=", self.ftyp),
                ("bfm_date", "=", self.date)]
            if div == "Main":
                ppad = 1
                rr = fm
                if self.ftyp == "P":
                    ftyp = "PRACTICE"
                else:
                    ftyp = "FIXTURE"
                h1 = "TEAMS FOR %s %s - %s %s %s" % (self.fdes, ftyp,
                    self.date % 100, mthnam[int(self.date / 100) % 100][1],
                    int(self.date / 10000))
                whr.append(("bfs_league", "=", "M"))
            else:
                ppad = 1.5
                rr = ff
                h1 = "TEAMS FOR %s FRIENDLY - %s %s %s" % (self.fdes,
                    self.date % 100, mthnam[int(self.date / 100) % 100][1],
                    int(self.date / 10000))
                whr.append(("bfs_league", "=", "F"))
            whr.extend([
                ("bfs_cono=bfm_cono",),
                ("bfs_fmat=bfm_fmat",),
                ("bfs_code=bfm_team",),
                ("bfo_cono=bfm_cono",),
                ("bfo_fmat=bfm_fmat",),
                ("bfo_code=bfm_opps",),
                ("bcc_code=bfo_club",)])
            games = self.sql.getRec(tables=["bwlflm", "bwlfls", "bwlflo",
                "bwlclb"], cols=["bfm_round", "bfm_team", "bfs_desc",
                "bfo_desc", "bfm_venue", "bfm_mtime", "bfm_mplace",
                "bfm_captain", "bcc_name", "bfs_number"], where=whr,
                order="bfm_team")
            if not games:
                continue
            fpdf.add_page()
            if games[0][0] == 0:
                h1 = h1.replace("FIXTURE", "PRACTICE")
            totp = 0
            for game in games:
                if totp < game[9]:
                    totp = game[9] * 4
            # Draw headings
            fpdf.drawText(x=0, y=1*ld, w=90*cw, align="C", txt=h1,
                font=("helvetica", "B", 18))
            fpdf.setFont("helvetica", "B", 12)
            # Draw table
            last, table = doDrawTable(fpdf, rr, ppad, spad=2, cw=cw, ld=ld)
            # Fill Form
            tc = []
            pl = []
            fpdf.setFont("helvetica", "B", 12)
            for x, game in enumerate(games):
                tc.append(game[7])
                if game[4].strip().upper() == "H":
                    text = "%s vs %s at %s" % (game[2], game[3],
                        self.opts["conam"])
                elif game[4].strip().upper() == "A":
                    text = "%s vs %s at %s" % (game[2], game[3], game[8])
                else:
                    text = "%s vs %s at %s" % (game[2], game[3], game[4])
                pos = table[0][1][x] + .5
                fpdf.drawText(x=0, y=pos*ld, w=90*cw, align="C", txt=text)
                pos = table[-1][1][x] + .5
                if game[6].strip().upper() in ("H", "A"):
                    text = "Meet at the Club at %5.2f" % game[5]
                else:
                    text = "Meet at %s at %5.2f" % (game[6], game[5])
                fpdf.drawText(x=0, y=pos*ld, w=90*cw, align="C", txt=text)
                plrs = self.sql.getRec(tables=["bwlflt", "bwltab"],
                    cols=["btb_tab", "btb_surname", "btb_names"],
                    where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat",
                    "=", self.fmat), ("bft_type", "=", self.ftyp), ("bft_date",
                    "=", self.date), ("bft_team", "=", game[1]),
                    ("btb_cono=bft_cono",), ("btb_tab=bft_player",)],
                    order="bft_team, bft_skip, bft_position")
                while len(plrs) < totp:
                    plrs.append(["", "", ""])
                pl.extend(plrs)
            fpdf.setFont("helvetica", "", 12)
            col = len(rr["rows"][1][2])
            cnt = 0
            for p in pl:
                if p == ["", "", ""]:
                    continue
                pn = self.getName(p[1], p[2])
                if p[0] in tc:
                    pn = "%s (C)" % pn
                x = table[(int((cnt % totp) / 4) + 2)][0][0] + 1
                y = table[((cnt - (int(cnt / 4) * 4)) * col) + 2][1][
                    int(cnt / totp)] + .5
                fpdf.drawText(x=x*cw, y=y*ld, txt=pn)
                cnt += 1
            # Draw trailer
            fpdf.setFont("helvetica", "B", 14)
            txt = """Please tick your names on the right hand side to indicate availability. If unavailable please inform skips and skips to inform selectors."""
            if self.assess == "Y":
                txt = """%s

Captains (C) are responsible to distribute and return assessment forms, completed and initialled, to a selector.""" % txt
            txt = """%s

%s

%s""" % (txt, self.pr.t_work[0][0][0], self.pr.t_work[0][0][1])
            fpdf.drawText(x=10.0*cw, y=(last+3)*ld, txt=txt, ctyp="M")
        head = "Match Selections for %s" % self.disp
        if fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], header=head, pdfnam=pdfnam,
                repprt=self.pr.repprt, fromad=self.fromad,
                repeml=self.pr.repeml)

    def getName(self, snam, fnam):
        if fnam:
            return "%s, %s" % (snam.upper(), fnam.split()[0][0].upper())
        else:
            return snam.upper()

    def doQuit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.rollbackDbase()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
