"""
SYNOPSIS
    Bowls Competition Match Results.

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

import time
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, TartanDialog, Sql
from tartanFunctions import askQuestion, callModule, copyList, doPrinter
from tartanFunctions import getModName, getNextCode


class bc3100(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwlgme", "bwltab",
            "bwltyp", "bwlpts", "bwlent"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
        return True

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        gme = {
            "stype": "R",
            "tables": ("bwlgme",),
            "cols": (("bcg_game", "", 0, "GC"),),
            "where": [("bcg_cono", "=", self.opts["conum"])],
            "whera": [("T", "bcg_ccod", 0, 0)],
            "group": "bcg_game"}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                0,"N",self.doCmpCod,com,None,None),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUI",2,"Last Game","",
                0,"N",self.doLstGam,gme,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Game Report","",
                "Y","N",self.doGamRep,None,None,None),
            (("T",0,3,0),("IRB",r1s),0,"Match Report","",
                "Y","N",self.doMatRep,None,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Session Prizes","",
                "N","N",self.doSesPrz,None,None,None),
            (("T",0,5,0),("IRB",r1s),0,"Session Prizes by Group","",
                "N","N",self.doSesGrp,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("B","N"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlcmp", where=[("bcm_cono", "=",
            self.opts["conum"]), ("bcm_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.cdes = chk[self.sql.bwlcmp_col.index("bcm_name")]
        self.ctyp = chk[self.sql.bwlcmp_col.index("bcm_type")]
        self.poff = chk[self.sql.bwlcmp_col.index("bcm_poff")]
        chk = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", self.ctyp)], limit=1)
        self.cfmat = chk[self.sql.bwltyp_col.index("bct_cfmat")]
        self.tsize = chk[self.sql.bwltyp_col.index("bct_tsize")]
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
        elif self.cfmat in ("D", "K"):
            self.df.loadEntry(frt, pag, p+1, data=self.cdes)
            return "sk6"
        else:
            self.games = chk[self.sql.bwltyp_col.index("bct_games")]
        self.groups = chk[self.sql.bwltyp_col.index("bct_groups")]
        self.grgame = chk[self.sql.bwltyp_col.index("bct_grgame")]
        col = ["bcg_game", "bcg_aflag", "sum(bcg_sfor)",
            "sum(bcg_sagt)", "sum(bcg_points)"]
        game = self.sql.getRec("bwlgme", cols=col, where=[("bcg_cono",
            "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod)],
            group="bcg_game, bcg_aflag", order="bcg_game")
        self.lgame = 0
        for g in game:
            if not g[1] and not g[2] and not g[3] and not g[4]:
                break
            self.lgame = g[0]
        if not self.lgame:
            return "No Completed Games"
        self.df.loadEntry(frt, pag, p+1, data=self.cdes)
        self.df.loadEntry(frt, pag, p+2, data=self.lgame)

    def doLstGam(self, frt, pag, r, c, p, i, w):
        if not w:
            chk = self.sql.getRec("bwlgme", cols=["bcg_game",
                "sum(bcg_points)"], where=[("bcg_cono", "=",
                self.opts["conum"]), ("bcg_ccod", "=", self.ccod)],
                group="bcg_game", order="bcg_game")
            game = 0
            for g in chk:
                if g[1]:
                    game = g[0]
                else:
                    break
            if not game:
                return "No Completed Games"
            self.df.loadEntry(frt, pag, p, data=game)
        else:
            game = w
        chk = self.sql.getRec("bwlgme", cols=["count(*)"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod",
            "=", self.ccod), ("bcg_game", "=", game), ("bcg_aflag",
            "=", "A")], group="bcg_aflag", limit=1)
        if chk and chk[0]:
            return "Game Abandoned"
        chk = self.sql.getRec("bwlgme", where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod), ("bcg_game",
            "=", game), ("bcg_aflag", "in", ("", "D"))])
        if not chk:
            return "Invalid Game Number"
        ptyp = chk[0][self.sql.bwlgme_col.index("bcg_type")]
        pts = self.sql.getRec("bwlpts", where=[("bcp_cono",
            "=", self.opts["conum"]), ("bcp_code", "=", self.ctyp),
            ("bcp_ptyp", "=", ptyp)], limit=1)
        self.ponly = pts[self.sql.bwlpts_col.index("bcp_p_only")]
        non = []
        for ck in chk:
            scod = ck[self.sql.bwlgme_col.index("bcg_scod")]
            ocod = ck[self.sql.bwlgme_col.index("bcg_ocod")]
            if scod > 900000 or ocod > 900000:
                continue
            if self.ponly == "Y":
                fors = ck[self.sql.bwlgme_col.index("bcg_points")]
                agts = self.sql.getRec("bwlgme",
                    cols=["bcg_points"], where=[("bcg_cono", "=",
                    self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
                    ("bcg_game", "=", game), ("bcg_scod", "=", ocod)],
                    limit=1)[0]
            else:
                fors = ck[self.sql.bwlgme_col.index("bcg_sfor")]
                agts = ck[self.sql.bwlgme_col.index("bcg_sagt")]
            if not fors and not agts:
                if scod not in non:
                    non.append(scod)
        if non:
            return "%s Result(s) Not Yet Entered" % int(len(non) / 2)
        self.pgame = w
        if self.pgame == 1:
            self.gamrep = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.gamrep)
            if self.pgame < self.games:
                self.matrep = "Y"
                self.sesp = "N"
                self.sesg = "N"
                self.df.loadEntry(frt, pag, p+2, data=self.matrep)
                self.df.loadEntry(frt, pag, p+3, data=self.sesp)
                self.df.loadEntry(frt, pag, p+4, data=self.sesg)
                return "sk4"
            return "sk1"
        if self.cfmat in ("D", "K", "R") or self.pgame < self.lgame:
            self.df.topf[0][3][5] = "N"
        else:
            self.df.topf[0][3][5] = "Y"

    def doGamRep(self, frt, pag, r, c, p, i, w):
        self.gamrep = w

    def doMatRep(self, frt, pag, r, c, p, i, w):
        if w == "N" and self.gamrep == "N":
            return "ff4|No Game or Match Report Selected"
        self.matrep = w
        if self.matrep == "N" or self.cfmat in ("D", "K", "R") or \
                self.pgame < self.games:
            self.sesp = "N"
            self.sesg = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.sesp)
            self.df.loadEntry(frt, pag, p+2, data=self.sesg)
            return "sk2"

    def doSesPrz(self, frt, pag, r, c, p, i, w):
        self.sesp = w
        if self.sesp == "N" or self.groups == "N":
            self.sesg = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.sesg)
            return "sk1"

    def doSesGrp(self, frt, pag, r, c, p, i, w):
        self.sesg = w

    def doEnd(self):
        self.df.closeProcess()
        if self.cfmat in ("D", "K"):
            self.printKnockout()
        else:
            self.printCompetition()

    def printKnockout(self):
        pwrs = 2
        self.rnds = 1
        self.totskp = self.sql.getRec("bwlent", cols=["count(*)"],
            where=[("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod)], limit=1)[0]
        while pwrs < self.totskp:
            self.rnds += 1
            pwrs = pwrs * 2
        head = (self.rnds * 19) + 19
        if head > 120:
            head = 170
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=head)
        self.pageHeading("K")
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
                nsiz -= .1
                self.fpdf.setFont(style="B", size=nsiz)
                nwth = self.fpdf.get_string_width(txt)
            self.fpdf.drawText(txt, x=x, y=y, w=w, font=("B", nsiz),
                border="TLRB")

        for num, skip in enumerate(skips):
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
            rd += 1
            if grp == 1:
                drawField(self.getWinner(rd, 2, 0, 1),
                    x + (cwth * (l1 + l2)), y, w=(cwth * nm))
        else:
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

    def printCompetition(self):
        chk = self.sql.getRec("bwlgme", cols=["bcg_group", "bcg_scod"],
            where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
            self.ccod), ("bcg_game", "=", self.pgame)], order="bcg_group")
        if chk[0][0] and self.cfmat == "R":
            groups = "Y"
        else:
            groups = self.groups
        self.grps = {}
        for rec in chk:
            if self.cfmat in ("T", "X") and self.pgame <= self.grgame:
                rec[0] = 0
            if rec[0] not in self.grps:
                self.grps[rec[0]] = [[rec[1]], [], []]
            else:
                self.grps[rec[0]][0].append(rec[1])
        self.keys = list(self.grps.keys())
        self.keys.sort()
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=65)
        self.lastg = None
        for g in self.keys:
            self.pageHeading()
            if self.gamrep == "Y":
                self.doReport("G", g)
                if g == 0 and len(chk) > 20:
                    self.pageHeading()
            if self.matrep == "Y":
                self.doReport("M", g)
        if self.pgame == self.games:
            # Enter Prizes
            for key in self.keys:
                if self.cfmat == "R" and groups == "Y":
                    self.grps[key][1] = 0
                else:
                    self.doPrizes(key)
            # Match Winners & Summary
            self.gqty = len(self.keys)
            self.wins = {}
            self.allp = []
            self.swin = []
            self.where = [
                ("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod),
                ("bcg_game", "<=", self.pgame),
                ("btb_cono=bcg_cono",),
                ("btb_tab=bcg_scod",)]
            for grp in range(self.gqty):
                if groups == "Y":
                    gcod = grp + 1
                else:
                    gcod = grp
                whr = copyList(self.where)
                whr.append(("bcg_group", "=", gcod))
                col = [
                    "bcg_scod", "btb_surname", "btb_names",
                    "sum(bcg_a_sfor) as sfor",
                    "sum(bcg_a_sagt) as sagt",
                    "sum(bcg_a_sfor - bcg_a_sagt) as agg",
                    "sum(bcg_a_points) as pts"]
                recs = self.sql.getRec(tables=["bwlgme", "bwltab"], cols=col,
                    where=whr, group="bcg_scod, btb_surname, btb_names",
                    order="pts desc, agg desc, sagt asc")
                if not recs:
                    continue
                self.wins[gcod] = []
                for x in range(self.grps[gcod][1]):
                    self.allp.append(recs[x][0])
                    if recs[x][2]:
                        nam = "%s, %s" % (recs[x][1], recs[x][2].split()[0])
                    else:
                        nam = recs[x][1]
                    self.wins[gcod].append([nam] + recs[x][3:])
                if self.cfmat == "R" and groups == "Y":
                    self.swin.append(self.grps[gcod][0][0])
            if self.sesp == "Y":
                self.pageHeading("S")
                self.doSesWin()
            else:
                for grp in self.wins:
                    if self.wins[grp]:
                        self.pageHeading("S")
                        break
            self.doMatchWin()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, "report", ext="pdf")
        if self.df.repeml[1] == "Y":
            if not self.df.repeml[2]:
                col = ["btb_mail"]
                whr = [
                    ("bce_cono", "=", self.opts["conum"]),
                    ("bce_ccod", "=", self.ccod),
                    ("btb_cono=bce_cono",),
                    ("btb_tab=bce_scod",),
                    ("btb_mail", "<>", "")]
                recs = self.sql.getRec(tables=["bwlent", "bwltab"], cols=col,
                    where=whr)
                self.df.repeml[2] = []
                for rec in recs:
                    self.df.repeml[2].append(rec[0])
        head = "%s - Results after game %s" % (self.cdes, self.pgame)
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        if self.pgame == self.lgame and self.cfmat == "R" and \
                groups == "Y" and not self.poff:
            ok = askQuestion(self.opts["mf"].body, "Play-Offs",
                "Must a Play-Off Draw be Created and/or Printed?",
                default="yes")
            if ok == "yes":
                self.doSecEnd()
        self.opts["mf"].closeLoop()

    def doReport(self, rtyp, grp):
        whr = [
            ("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod),
            ("btb_tab=bcg_scod",)]
        col = ["bcg_scod", "btb_surname", "btb_names"]
        if rtyp == "G":
            whr.extend([
                ("bcg_scod", "in", self.grps[grp][0]),
                ("bcg_game", "=", self.pgame)])
            col.extend([
                "sum(bcg_sfor) as sfor",
                "sum(bcg_sagt) as sagt",
                "sum(bcg_sfor - bcg_sagt) as agg",
                "sum(bcg_points) as pts"])
        else:
            whr.extend([
                ("bcg_scod", "in", self.grps[grp][0]),
                ("bcg_game", "<=", self.pgame)])
            if self.pgame <= self.grgame:
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
        recs = self.sql.getRec(tables=["bwlgme", "bwltab"], cols=col,
            where=whr, group="btb_tab, btb_surname, btb_names",
            order="pts desc, agg desc, sagt asc")
        if not recs:
            return
        self.groupHeading(rtyp, grp)
        if self.cfmat == "X":
            tms = {"H": [0, 0, 0, 0], "V": [0, 0, 0, 0]}
        pgno = 1
        for num, (scod,snam,fnam,sfor,sagt,agg,pts) in enumerate(recs):
            if pgno == 1 and num > 41:
                pgno = 2
                self.pageHeading()
                self.groupHeading(rtyp, grp)
            if fnam:
                nam = "%s, %s" % (snam.upper(), fnam.split()[0].upper())
            else:
                nam = snam.upper()
            a = CCD(num+1, "UI", 3)
            b = CCD(nam, "NA", 30)
            c = CCD(sfor, "SD", 7.1)
            d = CCD(sagt, "SD", 7.1)
            e = CCD(agg, "SD", 7.1)
            f = CCD(pts, "SD", 7.1)
            self.printLine(a.disp, b.disp, c.disp, d.disp, e.disp, f.disp)
            if self.cfmat == "X":
                tm = self.sql.getRec("bwlent", cols=["bce_tcod"],
                    where=[("bce_cono", "=", self.opts["conum"]),
                    ("bce_ccod", "=", self.ccod), ("bce_scod", "=", scod)],
                    limit=1)
                tms[tm[0]][0] = float(ASD(tms[tm[0]][0]) + ASD(c.work))
                tms[tm[0]][1] = float(ASD(tms[tm[0]][1]) + ASD(d.work))
                tms[tm[0]][2] = float(ASD(tms[tm[0]][2]) + ASD(e.work))
                tms[tm[0]][3] = float(ASD(tms[tm[0]][3]) + ASD(f.work))
            self.pglin += 1
        if self.cfmat == "X":
            cwth = self.fpdf.cwth
            self.fpdf.drawText()
            self.fpdf.drawText("Match Summary", font=["courier", "B", 18])
            self.fpdf.setFont(style="B")
            self.fpdf.drawText()
            self.fpdf.drawText("Home", w=cwth * 32, border="TLRB",
                align="C", fill=1, ln=0)
            self.fpdf.drawText("Visitors", w=cwth * 32, border="TLRB",
                align="C", fill=1, ln=1)
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            for tm in ("H", "V"):
                self.fpdf.drawText("+For", x=x, y=y, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=1)
                val = CCD(tms[tm][0], "SD", 7.1)
                self.fpdf.drawText(val.disp, x=x, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=0)
                x += (cwth * 8)
                self.fpdf.drawText("-Agt", x=x, y=y, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=1)
                val = CCD(tms[tm][1], "SD", 7.1)
                self.fpdf.drawText(val.disp, x=x, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=0)
                x += (cwth * 8)
                self.fpdf.drawText("=Dif", x=x, y=y, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=1)
                val = CCD(tms[tm][2], "SD", 7.1)
                self.fpdf.drawText(val.disp, x=x, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=0)
                x += (cwth * 8)
                self.fpdf.drawText("Pts", x=x, y=y, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=1)
                val = CCD(tms[tm][3], "SD", 7.1)
                self.fpdf.drawText(val.disp, x=x, w=cwth * 8, h=8,
                    border="TLRB", align="C", fill=0)
                x += (cwth * 8)

    def doSesWin(self):
        # Session Winners
        sess = {}
        for gme in range(1, self.games + 1):
            col = [
                "bcg_scod", "btb_surname", "btb_names",
                "bcg_sfor as sfor",
                "bcg_sagt as sagt",
                "bcg_sfor - bcg_sagt as agg",
                "bcg_points as pts"]
            whr = copyList(self.where)
            whr.append(("bcg_game", "=", gme))
            grp = "bcg_scod, btb_surname, btb_names"
            odr = "pts desc, agg desc, sagt asc"
            if self.sesg == "Y" and gme > self.grgame:
                col.append("bcg_group")
                grp = "bcg_group, %s" % grp
                odr = "bcg_group, %s" % odr
            recs = self.sql.getRec(tables=["bwlgme", "bwltab"],
                cols=col, where=whr, group=grp, order=odr)
            done = None
            for rec in recs:
                if len(rec) == 7:
                    gpc = 0
                else:
                    gpc = rec[7]
                ign = False
                if self.ponly == "Y" and not rec[6]:
                    break
                if self.ponly == "N" and (not rec[3] and not rec[4]):
                    break
                for grp in range(self.gqty):
                    if rec[0] in self.allp:
                        ign = True
                        break
                if not ign:
                    if gpc == done and rec[3:] != sess[gme][gpc][0][1:]:
                        continue
                    self.allp.append(rec[0])
                    if gme not in sess:
                        sess[gme] = {}
                    if gpc not in sess[gme]:
                        sess[gme][gpc] = []
                    if rec[2]:
                        nam = "%s, %s" % (rec[1], rec[2].split()[0])
                    else:
                        nam = rec[1]
                    sess[gme][gpc].append([nam] + rec[3:])
                    done = gpc
        mess = "Session Winners"
        self.fpdf.setFont(style="B", size=14)
        self.fpdf.drawText(mess, align="C", border="TLRB", fill=1)
        if self.sesg == "Y":
            self.printLine("Ses", "Grp", "%-27s" % "Name", "   Pts ",
                "  =Dif ", "  -Agt ", "  +For ", fill=1, last=False)
        else:
            self.printLine("Ses", "%-30s" % "Name", "   Pts ",
                "  =Dif ", "  -Agt ", "  +For ", fill=1, last=False)
        self.fpdf.setFont(size=14)
        for gme in range(1, self.games + 1):
            stxt = str("%3s" % gme)
            if gme not in sess:
                self.fpdf.drawText(stxt, w=12, border="TLRB", ln=0)
                if self.sesg == "Y":
                    self.fpdf.drawText("", w=12, border="TLRB", ln=0)
                self.fpdf.drawText("* No Valid Winner or Abandoned *",
                    border="TLRB")
                continue
            grps = list(sess[gme].keys())
            grps.sort()
            for grp in grps:
                if grp:
                    gtxt = " %s " % chr(64 + grp)
                else:
                    gtxt = "   "
                for per in sess[gme][grp]:
                    if self.sesg == "Y":
                        a = CCD(per[0], "NA", 27).disp
                    else:
                        a = CCD(per[0], "NA", 30).disp
                    b = CCD(per[4], "SD", 7.1).disp
                    c = CCD(per[3], "SD", 7.1).disp
                    d = CCD(per[2], "SD", 7.1).disp
                    e = CCD(per[1], "SD", 7.1).disp
                    if self.sesg == "Y":
                        self.printLine(stxt, gtxt, a, b, c, d, e, last=False)
                    else:
                        self.printLine(stxt, a, b, c, d, e, last=False)
        self.fpdf.drawText()

    def doMatchWin(self):
        for num, gcod in enumerate(self.keys):
            if self.wins[gcod]:
                if gcod:
                    if self.cfmat == "R":
                        mess = "Match Winners - Section %s" % chr(64 + gcod)
                    else:
                        mess = "Match Winners - Group %s" % chr(64 + gcod)
                else:
                    mess = "Match Winners"
                self.fpdf.setFont(style="B", size=14)
                self.fpdf.drawText(mess, align="C", border="TLRB", fill=1)
                self.printLine("Pos", "%-30s" % "Name", "   Pts ", "  =Dif ",
                    "  -Agt ", "  +For ", fill=1, last=False)
                self.fpdf.setFont(size=14)
                for n, s in enumerate(self.wins[gcod]):
                    a = CCD(n+1, "UI", 3).disp
                    b = CCD(s[0], "NA", 30).disp
                    c = CCD(s[4], "SD", 7.1).disp
                    d = CCD(s[3], "SD", 7.1).disp
                    e = CCD(s[2], "SD", 7.1).disp
                    f = CCD(s[1], "SD", 7.1).disp
                    self.printLine(a, b, c, d, e, f, last=False)
            if not num % 2:
                ly = self.fpdf.get_y()
            if num % 2 and self.fpdf.get_y() > ly:
                ly = self.fpdf.get_y()
            self.fpdf.drawText()
        place = ["1st", "2nd", "3rd"]
        for x in range(4, 21):
            place.append("%sth" % x)
        if self.tsize == 2:
            ppos = ("Skip", "Lead")
        elif self.tsize == 3:
            ppos = ("Skip", "Second", "Lead")
        elif self.tsize == 4:
            ppos = ("Skip", "Third", "Second", "Lead")
        for gcod in self.keys:
            if not self.grps[gcod][2]:
                continue
            for num, skp in enumerate(self.wins[gcod]):
                self.fpdf.add_page()
                self.fpdf.setFont(style="B", size=24)
                self.fpdf.drawText(self.cdes, h=10, align="C")
                self.fpdf.drawText()
                self.fpdf.setFont(style="B", size=18)
                if gcod:
                    self.fpdf.drawText("GROUP %s" % chr(64 + gcod),
                        h=10, align="C")
                    self.fpdf.drawText()
                self.fpdf.drawText("%s Prize R%s - %s" % (place[num],
                    self.grps[gcod][2][num], skp[0]), h=10, align="C")
                self.fpdf.setFont(style="B", size=16)
                for pos in ppos:
                    self.fpdf.drawText()
                    self.fpdf.drawText()
                    self.fpdf.drawText("%s's Name" % pos, w=50, h=8,
                        border="TLRB", ln=0, fill=1)
                    self.fpdf.drawText("", h=8, border="TLRB")
                    self.fpdf.drawText("Bank Name", w=50, h=8,
                        border="TLRB", ln=0, fill=1)
                    self.fpdf.drawText("", h=8, border="TLRB")
                    self.fpdf.drawText("Branch Name", w=50, h=8,
                        border="TLRB", ln=0, fill=1)
                    self.fpdf.drawText("", h=8, border="TLRB")
                    self.fpdf.drawText("Branch Code", w=50, h=8,
                        border="TLRB", ln=0, fill=1)
                    self.fpdf.drawText("", h=8, border="TLRB")
                    self.fpdf.drawText("Account Number", w=50, h=8,
                        border="TLRB", ln=0, fill=1)
                    self.fpdf.drawText("", h=8, border="TLRB")
                self.fpdf.drawText()
                self.fpdf.setFont(style="B", size=18)
                self.fpdf.drawText("Congratulations and Well Done!", h=10,
                    align="C")

    def pageHeading(self, htyp=None):
        self.fpdf.add_page()
        head = "%s - %s" % (self.opts["conam"], self.cdes)
        self.fpdf.drawText(head, font=["courier", "B", 18], align="C")
        if htyp == "S":
            self.fpdf.drawText()
            self.fpdf.drawText("Match Summary", font=["courier", "B", 16],
                align="C")
            self.fpdf.drawText()
            self.pglin = 4
        elif htyp == "K":
            dates = self.sql.getRec("bwlrnd", cols=["bcr_date", "bcr_time"],
                where=[("bcr_cono", "=", self.opts["conum"]), ("bcr_ccod",
                "=", self.ccod)], order="bcr_rcod")
            if dates[0][1]:
                self.comtyp = "F"
            else:
                self.comtyp = "V"
            siz, cwth, chgt = self.setBracketFont()
            self.fpdf.drawText()
            text = []
            for x in range(self.rnds):
                date = CCD(dates[x][0], "D1", 10).disp
                time = CCD(dates[x][1], "TM", 5).disp
                if self.comtyp == "V":
                    text.append("Complete By\n%s" % date)
                elif date == "9999-12-31":
                    text.append("To Be\nAnnounced")
                else:
                    if time <= "12:00":
                        txt = "%s AM" % time
                    else:
                        txt = "%s PM" % time
                    text.append("%s\n%s" % (date, txt))
            text.append("Competition\nWinner")
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            for txt in text:
                self.fpdf.drawText(txt, x=x, y=y, w=(cwth * 18), border="TLRB",
                    ln=0, fill=1, align="C", ctyp="M")
                x += (cwth * 19)
            self.fpdf.drawText()
            self.fpdf.drawText()
        else:
            self.pglin = 1

    def groupHeading(self, rtyp, group):
        self.fpdf.drawText(font=["courier", "B", 18], align="C")
        if rtyp == "G":
            head = "Results for Game Number: %s" % self.pgame
        else:
            head = "Match Standings After Game Number: %s" % self.pgame
        if group:
            if self.cfmat == "R":
                head += "  for Section: %s" % chr(64 + group)
            else:
                head += "  for Group: %s" % chr(64 + group)
        self.fpdf.drawText(head, font=["courier", "B", 16], align="C")
        self.fpdf.drawText()
        self.fpdf.setFont(style="B")
        self.printLine("Pos", "%-30s" % "Name", "  +For ", "  -Agt ",
            "  =Dif ", "   Pts ", fill=1)
        self.fpdf.setFont()
        self.pglin += 4

    def printLine(self, a, b, c, d, e, f, g=None, fill=0, last=True):
        x = 10
        w = self.fpdf.get_string_width("X"*len(a)) + 1
        self.fpdf.drawText(a, x=x, w=w, border="TLB", fill=fill, ln=0)
        x += w
        w = self.fpdf.get_string_width("X"*len(b)) + 1
        self.fpdf.drawText(b, x=x, w=w, border="TLB", fill=fill, ln=0)
        x += w
        w = self.fpdf.get_string_width("X"*len(c)) + 1
        self.fpdf.drawText(c, x=x, w=w, border="TLB", fill=fill, ln=0)
        x += w
        w = self.fpdf.get_string_width("X"*len(d)) + 1
        self.fpdf.drawText(d, x=x, w=w, border="TLB", fill=fill, ln=0)
        x += w
        w = self.fpdf.get_string_width("X"*len(e)) + 1
        self.fpdf.drawText(e, x=x, w=w, border="TLB", fill=fill, ln=0)
        x += w
        if g is not None:
            w = self.fpdf.get_string_width("X"*len(f)) + 1
            self.fpdf.drawText(f, x=x, w=w, border="TLB", fill=fill, ln=0)
            x += w
            f = g
        if last:
            w = self.fpdf.get_string_width("X"*len(f)) + 1
            self.fpdf.drawText(f, x=x, w=w, border="TLRB", fill=fill)
        else:
            self.fpdf.drawText(f, x=x, border="TLRB", fill=fill)

    def doPrizes(self, grp):
        self.przgrp = grp
        if grp:
            if self.cfmat == "R":
                tit = "Prizes for Section %s" % chr(64 + grp)
            else:
                tit = "Prizes for Group %s" % chr(64 + grp)
        else:
            tit = "Prizes for Match"
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IUI",2,"Number of Prizes","",
                3,"N",self.doPrzNum,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"EFT Forms","",
                "N","N",self.doPrzEft,None,None,None),
            (("T",0,2,0),"IUI",5,"1st Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,3,0),"IUI",5,"2nd Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,4,0),"IUI",5,"3rd Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,5,0),"IUI",5,"4th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,6,0),"IUI",5,"5th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,7,0),"IUI",5,"6th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,8,0),"IUI",5,"7th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,9,0),"IUI",5,"8th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,10,0),"IUI",5,"9th Prize","",
                0,"N",self.doPrzAmt,None,None,None),
            (("T",0,11,0),"IUI",5,"10th Prize","",
                0,"N",self.doPrzAmt,None,None,None))
        tnd = ((self.doPrzEnd,"n"),)
        self.pz = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=None)
        for x in range(10):
            self.pz.setWidget(self.pz.topLabel[0][2+x], state="hide")
            self.pz.setWidget(self.pz.topEntry[0][2+x], state="hide")
        self.pz.mstFrame.wait_window()

    def doPrzNum(self, frt, pag, r, c, p, i, w):
        if not w and self.cfmat != "R":
            ok = askQuestion(self.opts["mf"].body, "Prizes",
                "Are You Sure that there are No Prizes?", default="no")
            if ok == "no":
                return "Invalid Number od Prizes"
        self.prznum = w
        if not self.prznum:
            self.przeft = []
            self.pz.loadEntry(frt, pag, p+1, data="N")
            return "nd"

    def doPrzEft(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.przeft = []
            return "nd"
        self.przeft = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for x in range(self.prznum):
            self.pz.setWidget(self.pz.topLabel[0][2+x], state="show")
            self.pz.setWidget(self.pz.topEntry[0][2+x], state="show")
        for x in range(self.prznum, 10):
            self.pz.setWidget(self.pz.topLabel[0][2+x], state="hide")
            self.pz.setWidget(self.pz.topEntry[0][2+x], state="hide")

    def doPrzAmt(self, frt, pag, r, c, p, i, w):
        self.przeft[p-2] = w
        if p == self.prznum + 1:
            return "nd"

    def doPrzEnd(self):
        self.grps[self.przgrp][1] = self.prznum
        self.grps[self.przgrp][2] = self.przeft
        self.pz.closeProcess()

    def doSecEnd(self):
        ccod = getNextCode(self.sql, "bwlcmp", "bcm_code",
            where=[("bcm_cono", "=", self.opts["conum"])], last=999)
        tcod = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_cfmat", "=", "K")], limit=1)
        if not tcod:
            tcod = getNextCode(self.sql, "bwltyp", "bct_code",
                where=[("bct_cono", "=", self.opts["conum"])], last=999)
            self.sql.insRec("bwltyp", data=[self.opts["conum"], tcod,
                "Knockout", "K", 1, 0, 21, "N", 0, "N", "", 0, 0, "N", "N"])
        else:
            tcod = tcod[1]
        self.sql.updRec("bwlcmp", cols=["bcm_poff"], data=[ccod],
            where=[("bcm_cono", "=", self.opts["conum"]),
            ("bcm_code", "=", self.ccod)])
        cdes = self.cdes + " Play-Off"
        t = time.localtime()
        cdte = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.sql.insRec("bwlcmp", data=[self.opts["conum"], ccod,
            cdes, cdte, tcod, 0])
        for skp in self.swin:
            self.sql.insRec("bwlent", data=[self.opts["conum"],
                ccod, skp, 0, "Y", ""])
        callModule(self.opts["mf"], self.df, "bc2050", coy=[self.opts["conum"],
            self.opts["conam"]], args=[ccod, 1])

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
