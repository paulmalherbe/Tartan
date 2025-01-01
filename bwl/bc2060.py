"""
SYNOPSIS
    Bowls Competition Draw Maintenance.

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

import time
from TartanClasses import CCD, MyFpdf, PrintCards, Sql, TartanDialog
from tartanFunctions import askQuestion, copyList, doPrinter, getModName
from tartanFunctions import showError

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
            "bwltyp", "bwlpts", "bwlent"], prog=self.__class__.__name__)
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
                self.today,"N",self.doDate,None,self.doDelete,("efld",)),
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
        but = (
            ("Print",None,self.doPrint,1,None,None),
            ("Quit",None,self.doQuit,1,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"y"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, eflds=fld,
            butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        com = self.sql.getRec("bwlcmp", cols=["bcm_name", "bcm_date",
            "bcm_type"], where=[("bcm_cono", "=", self.opts["conum"]),
            ("bcm_code", "=", w)], limit=1)
        if not com:
            return "Invalid Competition Code"
        self.cdes, self.sdat, self.ctyp = com
        self.df.loadEntry(frt, pag, p+1, data=self.cdes)
        bwltyp = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", self.ctyp)], limit=1)
        self.cfmat = bwltyp[self.sql.bwltyp_col.index("bct_cfmat")]
        self.ends = bwltyp[self.sql.bwltyp_col.index("bct_ends")]
        self.grgame = bwltyp[self.sql.bwltyp_col.index("bct_grgame")]
        gmes = self.sql.getRec("bwlgme", cols=["bcg_game", "bcg_type",
            "bcg_date", "bcg_aflag", "sum(bcg_ocod)", "sum(bcg_sfor)",
            "sum(bcg_sagt)"], where=[("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", w)], group="bcg_game, bcg_date, bcg_aflag")
        self.ccod = w
        self.game = 0
        self.draws = {}
        self.manual = False
        if gmes:
            for gme in gmes:
                if gme[3] == "A" or gme[5] or gme[6]:
                    continue
                if gme[3] in ("", "D", "S") and gme[4]:
                    self.draws[gme[0]] = gme[1:]
        elif self.cfmat in ("D", "K", "R", "W", "X"):
            return "Draw Not Yet Done"
        else:
            ok = askQuestion(self.opts["mf"].body, "Manual Draw",
                "This is the First Game, is it going to be a "\
                "Manual Draw?", default="no")
            if ok == "no":
                return "rf"
            self.manual = True
            self.game = 1
            self.df.loadEntry(frt, pag, p+2, data=self.game)
            skips = self.sql.getRec("bwlent", cols=["bce_scod"],
                where=[("bce_cono", "=", self.opts["conum"]),
                ("bce_ccod", "=", self.ccod)], order="bce_scod")
            self.totskp = len(skips)
            # Populate bwlgme records
            data = [self.opts["conum"], self.ccod, 0, 0, "D", 0, 0, "",
                0, 0, 0, 0, 0, 0, 0, "", 0, 1]
            for skip in skips:
                data[2] = skip[0]
                data[3] = self.game
                self.sql.insRec("bwlgme", data=data)
            return "sk2"

    def doGame(self, frt, pag, r, c, p, i, w):
        if w not in self.draws:
            return "Invalid Game Number"
        self.game = w
        self.gtyp = self.draws[w][0]
        self.date = self.draws[w][1]
        self.df.loadEntry(frt, pag, p+1, data=self.date)
        self.totskp = self.sql.getRec("bwlent", cols=["count(*)"],
            where=[("bce_cono", "=", self.opts["conum"]), ("bce_ccod", "=",
            self.ccod)], limit=1)[0]

    def doDelete(self):
        self.sql.delRec("bwlgme", where=[("bcg_cono", "=", self.opts["conum"]),
            ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game)])
        self.opts["mf"].dbm.commitDbase(ask=True)

    def doDate(self, frt, pag, r, c, p, i, w):
        if w < self.today or w < self.sdat:
            return "Invalid Date, in the Past or Before the Starting Date"
        self.date = w
        self.datd = CCD(self.date, "D1", 10).disp

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
        if skp[1]:
            name = "%s, %s" % tuple(skp[:2])
        else:
            name = skp[0]
        self.df.loadEntry(frt, pag, p+1, data=name)
        if not self.manual and skp[2]:
            self.df.loadEntry(frt, pag, p+2, data=skp[2])
            opp = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", skp[2])], limit=1)
            if opp[1]:
                name = "%s, %s" % tuple(opp[:2])
            else:
                name = opp[0]
            self.df.loadEntry(frt, pag, p+3, data=name)
        if not self.manual and skp[3]:
            self.df.loadEntry(frt, pag, p+4, data=skp[3])
        if self.cfmat in ("D", "K", "R", "W"):
            if skp[2]:
                self.new_opp = skp[2]
            return "sk3"

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
            self.df.advanceLine(0)

    def doExit(self, doprint=False):
        if self.df.frt == "C":
            chk = self.sql.getRec("bwlgme", cols=["bcg_ocod",
                "count(*)"], where=[("bcg_cono", "=", self.opts["conum"]),
                ("bcg_ccod", "=", self.ccod), ("bcg_game", "=", self.game)],
                group="bcg_ocod", order="bcg_ocod")
            for c in chk:
                if not c[0] or c[1] != 1:
                    if c[0]:
                        skp = self.sql.getRec("bwlgme", cols=["bcg_scod"],
                            where=[("bcg_cono", "=", self.opts["conum"]),
                            ("bcg_ccod", "=", self.ccod), ("bcg_game", "=",
                            self.game), ("bcg_ocod", "=", c[0])],
                            order="bcg_scod")
                        err = "Opponent %s is Drawn Against %s Skips\n" % \
                            tuple(c)
                        for s in skp:
                            err = err + "\nSkip %s" % s[0]
                    else:
                        err = ""
                    skp = self.sql.sqlRec("Select bce_scod from bwlent where "\
                        "bce_ccod = %s and bce_scod not in (select bcg_ocod "\
                        "from bwlgme where bcg_ccod = %s and bcg_game = %s)" %
                        (self.ccod, self.ccod, self.game))
                    if err:
                        err += "\n\n"
                    err = err + "Skips Without Opponents\n"
                    for s in skp:
                        err = err + "%s " % s[0]
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
            if doprint:
                if self.opts["mf"].dbm.commit == "yes":
                    return True
                return
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doPrint(self):
        if not self.doExit(doprint=True):
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        self.df.closeProcess()
        r1s = (("No", "N"),("Yes","Y"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Print Cards","",
                "N","N",self.doPrtCards,None,None,None),)
        tnd = ((self.printGame,"n"),)
        txt = (self.printExit,)
        self.pr = TartanDialog(self.opts["mf"], tops=False, eflds=fld,
            tend=tnd, txit=txt, view=("X","V"), mail=("Y","Y"))
        self.pr.mstFrame.wait_window()
        if self.prtcards == "Y":
            self.printCards()
        self.opts["mf"].closeLoop()

    def doPrtCards(self, frt, pag, r, c, p, i, w):
        self.prtcards = w

    def printGame(self):
        grp = [[0]]
        if self.game > self.grgame:
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
                pdfnam=pdfnam, header=head, repprt=self.pr.repprt,
                repeml=self.pr.repeml)
        self.pr.closeProcess()

    def pageHeading(self):
        self.fpdf.add_page()
        head = "%s - %s" % (self.opts["conam"], self.cdes)
        self.fpdf.drawText(head, font=["courier", "B", 18], align="C")
        self.pglin = 1

    def groupHeading(self, group):
        self.fpdf.drawText(font=["courier", "B", 18])
        head = "Draw for Game: %s" % self.game
        if group:
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
        bwlpts = self.sql.getRec("bwlpts", where=[("bcp_cono",
            "=", self.opts["conum"]), ("bcp_code", "=", self.ctyp),
            ("bcp_ptyp", "=", self.gtyp)], limit=1)
        skins = bwlpts[self.sql.bwlpts_col.index("bcp_skins")]
        sends = bwlpts[self.sql.bwlpts_col.index("bcp_sends")]
        recs = self.sql.getRec("bwlgme", cols=["bcg_scod",
            "bcg_ocod", "bcg_rink"], where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
            ("bcg_game", "=", self.game)], order="bcg_rink")
        chk = []
        skips = []
        for rec in recs:
            if rec[0] in chk:
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
        PrintCards(self.opts["mf"], self.opts["conum"], self.cdes,
            self.game, self.datd, skips, self.ends, skins, sends)

    def printExit(self):
        self.pr.closeProcess()
        self.opts["mf"].closeLoop()

    def doQuit(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
