"""
SYNOPSIS
    Bowls League Assessment Forms.

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

from TartanClasses import GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import askQuestion, getModName, doDrawTable, doPrinter
from tartanWork import mthnam

class bc3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "bwlclb", "bwlflf",
            "bwlflm", "bwlflo", "bwltab", "bwlfls", "bwlflt"],
            prog=self.__class__.__name__)
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
            "where": [("bfm_cono", "=", self.opts["conum"])],
            "whera": [("T", "bfm_fmat", 0, 0)],
            "group": "bfm_date",
            "order": "bfm_date"}
        r1s = (("Fixture", "F"), ("Practice", "P"))
        fld = (
            (("T",0,0,0),"I@bfm_fmat",0,"","",
                "","N",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "F","N",self.doType,dte,None,None),
            (("T",0,2,0),"I@bfm_date",0,"","",
                "","N",self.doDate,dte,None,("efld",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("Y","Y"))

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Format"
        if acc[self.sql.bwlflf_col.index("bff_assess")] == "N":
            return "Assessment Forms Disabled"
        self.fmat = w
        desc = acc[self.sql.bwlflf_col.index("bff_desc")]
        self.forms = acc[self.sql.bwlflf_col.index("bff_forms")]
        self.self = acc[self.sql.bwlflf_col.index("bff_self")]
        self.rate = acc[self.sql.bwlflf_col.index("bff_rate")]
        self.sets = acc[self.sql.bwlflf_col.index("bff_sets")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doType(self, frt, pag, r, c, p, i, w):
        self.ftyp = w

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.disp = "%i %s %i" % (w % 100, mthnam[int(w / 100) % 100][1],
            int(w / 10000))
        acc = self.sql.getRec("bwlflt", cols=["sum(bft_shotsf)"],
            where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
            self.fmat), ("bft_type", "=", self.ftyp), ("bft_date", "=", w)],
            limit=1)
        if acc[0]:
            ok = askQuestion(self.opts["mf"].body, "Completed",
                "Match Already Completed, Do You Want to Re-Print?")
            if ok == "no":
                return "rf"
            self.reprint = True
        else:
            self.reprint = False

    def doEnd(self):
        self.df.closeProcess()
        # Get data
        cards = []
        whr = [
            ("bft_cono", "=", self.opts["conum"]),
            ("bft_fmat", "=", self.fmat),
            ("bft_type", "=", self.ftyp),
            ("bft_date", "=", self.date)]
        if self.forms == 4:
            maxf = 8
        else:
            maxf = 3
            whr.append(("bft_position", "=", 1))
        col = ["bft_team", "bft_skip", "bft_player"]
        whr.extend([
            ("bfs_cono=bft_cono",),
            ("bfs_fmat=bft_fmat",),
            ("bfs_code=bft_team",),
            ("bfs_league", "=", "M")])
        recs = self.sql.getRec(tables=["bwlflt", "bwlfls"], cols=col,
            where=whr, order="bft_team, bft_skip, bft_position asc")
        for rec in recs:
            match = self.sql.getRec("bwlflm", cols=["bfm_opps",
                "bfm_venue"], where=[("bfm_cono", "=", self.opts["conum"]),
                ("bfm_fmat", "=", self.fmat), ("bfm_type", "=", self.ftyp),
                ("bfm_date", "=", self.date), ("bfm_team", "=", rec[0])],
                limit=1)
            team = self.sql.getRec("bwlfls", cols=["bfs_desc"],
                where=[("bfs_cono", "=", self.opts["conum"]), ("bfs_fmat", "=",
                self.fmat), ("bfs_code", "=", rec[0])], limit=1)
            opp = self.sql.getRec(tables=["bwlflo", "bwlclb"],
                cols=["bfo_desc", "bcc_name"], where=[("bfo_cono", "=",
                self.opts["conum"]), ("bfo_fmat", "=", self.fmat), ("bfo_code",
                "=", match[0]), ("bcc_code=bfo_club",)], limit=1)
            skp = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", "=", rec[1])], limit=1)
            if self.forms == 4:
                plr = self.sql.getRec(tables=["bwltab", "bwlflt"],
                    cols=["btb_surname", "btb_names", "bft_position"],
                    where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat",
                    "=", self.fmat), ("bft_date", "=", self.date),
                    ("bft_skip", "=", rec[1]), ("bft_player", "=", rec[2]),
                    ("btb_cono=bft_cono",), ("btb_tab=bft_player",)], limit=1)
            else:
                plr = self.sql.getRec(tables=["bwltab", "bwlflt"],
                    cols=["btb_surname", "btb_names"], where=[("bft_cono",
                    "=", self.opts["conum"]), ("bft_fmat", "=", self.fmat),
                    ("bft_date", "=", self.date), ("bft_skip", "=", rec[1]),
                    ("btb_cono=bft_cono",), ("btb_tab=bft_player",)],
                    order="bft_position")
            if match[1] == "H":
                ven = self.opts["conam"]
            else:
                ven = "%s" % opp[1]
            if self.forms == 4:
                cards.append([team[0], opp[0], ven, self.getName(skp[0],
                    skp[1]), self.getName(plr[0], plr[1]), plr[2]])
            else:
                card = [team[0], opp[0], ven, "%s, %s" % (skp[0], skp[1])]
                for p in plr:
                    card.append(self.getName(p[0], p[1]))
                cards.append(card)
        while len(cards) % maxf:
            if self.forms == 4:
                cards.append(["", "", "", "", "", 0])
            else:
                cards.append(["", "", "", "", "", "", "", ""])
        # Print
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, "assess_%s" % self.date, ext="pdf")
        fpdf = MyFpdf(name=self.__class__.__name__, head=90)
        cw = fpdf.get_string_width("X")
        ld = 4.5
        if self.forms == 4:
            rr = {
                "margins": ((2.5, 47.5), (1.5, 15.5)),
                "repeat": (2, 4),
                "rows": (
                    (2.5, 1.5, 47.5, 14.5),
                    (2.5, 8.5, (
                        (8, 1.5, .8, "Title", True),
                        (12, 1.5, .8, "Out of %s" % self.rate, True),
                        (27.5, 1.5, .8, "Remarks", True))),
                    (2.5, 10, (
                        (8, 1.5, .9, ("Skip", "Third", "Second", "Lead")),
                        (12, 1.5)), 4))}
        else:
            rr = {
                "margins": ((2.5, 47.5), (1.5, 20.5)),
                "repeat": (1, 3),
                "rows": (
                    (2.5, 1.5, 95.1, 19.5),
                    (2.5, 11, (
                        (10, 2, .8, "Position"),
                        (20, 2, .8, "Name"),
                        (12, 2, .8, "Rating 1-%s" % self.rate),
                        (7, 2, .8, "Initial"),
                        (46.1, 2, .8, "Remarks"))),
                    (2.5, 13, (
                        (10, 2, .9, ("Skip", "Third", "Second", "Lead")),
                        (20, 2), (12, 2), (7, 2)), 4))}
        if self.forms == 4:
            ppad = 1
            h1 = "Assessment Form"
            yy = [2, 18, 34, 50]
        else:
            ppad = 1.5
            h1 = "Assessment Form for %s" % self.disp
            yy = [2.5, 23.5, 44.5]
        for x in range(0, len(cards), maxf):
            fpdf.add_page()
            last, table = doDrawTable(fpdf, rr, ppad, spad=2, cw=cw, ld=ld)
            for y in range(maxf):
                card = cards[x + y]
                if self.forms == 4:
                    if y % 2:
                        xx = 53 * cw
                    else:
                        xx = 5 * cw
                    sx = xx
                    fpdf.setFont("helvetica", "B", 12)
                    fpdf.set_y((yy[int(y / 2)]) * ld)
                    fpdf.drawText(x=xx, w=45 * cw, align="C", txt=h1)
                    fpdf.setFont("helvetica", "B", 8)
                    h2 = "%s vs %s at %s on %s" % (card[0], card[1], card[2],
                        self.disp)
                    fpdf.drawText(x=xx, w=45 * cw, align="C", txt=h2)
                    fpdf.setFont("helvetica", "B", 10)
                    h3 = "Skip: %s    Player: %s" % (card[3], card[4])
                    fpdf.drawText(x=xx, w=45 * cw, align="C", txt=h3)
                    fpdf.drawText(h=2)
                    fpdf.setFont("helvetica", "B", 10)
                else:
                    xx = 3 * cw
                    sx = 25 * cw
                    fpdf.setFont("helvetica", "B", 18)
                    fpdf.set_y((yy[y]) * ld)
                    fpdf.drawText(x=xx, w=90 * cw, h=10, align="C", txt=h1)
                    fpdf.setFont("helvetica", "B", 16)
                    h2 = "%s vs %s at %s on %s" % (card[0], card[1], card[2],
                        self.disp)
                    fpdf.drawText(x=xx, w=90 * cw, h=8, align="C", txt=h2)
                    fpdf.drawText()
                    fpdf.setFont("helvetica", "B", 12)
                w1 = fpdf.get_string_width("XXXXXXXXX")
                w2 = fpdf.get_string_width("XXXXX")
                fpdf.drawText(x=sx + (7 * cw), w=w1, txt="Shots-For", border=1,
                    fill=1, ln=0)
                fpdf.drawText(w=w1, txt="Shots-Agt", border=1, fill=1, ln=0)
                fpdf.drawText(w=w1, txt="   Points", border=1, fill=1, ln=0)
                fpdf.drawText(w=w2, txt="Total", border=1, fill=1)
                if self.sets == "Y":
                    for s in range(1, 3):
                        fpdf.drawText(x=sx, h=5, txt="Set %s" % s, ln=0)
                        fpdf.drawText(x=sx + (7 * cw), w=w1, h=5, txt="",
                            border=1, ln=0)
                        fpdf.drawText(w=w1, h=5, txt="", border=1, ln=0)
                        fpdf.drawText(w=w1, h=5, txt="", border=1, ln=0)
                        if s == 1:
                            fpdf.drawText(w=w2, h=5, txt="", border="LR")
                        else:
                            fpdf.drawText(w=w2, h=5, txt="", border="LRB")
                else:
                    fpdf.drawText(x=sx + (7 * cw), w=w1, h=5, txt="",
                        border=1, ln=0)
                    fpdf.drawText(w=w1, h=5, txt="", border=1, ln=0)
                    fpdf.drawText(w=w1, h=5, txt="", border=1, ln=0)
                    fpdf.drawText(w=w2, h=5, txt="", border=1)
                if self.forms == 1:
                    fpdf.setFont("helvetica", "", 12)
                    r = (y * 21) + 4.5
                    for z in range(4):
                        fpdf.set_xy(13.5 * cw, (9 + (z * 2) + r) * ld)
                        fpdf.drawText(txt=card[4 + z])
                elif self.self == "N" and card[5] in (1,2,3,4):
                    if y % 2:
                        posx = 127
                    else:
                        posx = 25
                    if card[5] == 1:
                        posy = fpdf.get_y() + 10
                    elif card[5] == 2:
                        posy = fpdf.get_y() + 16.75
                    elif card[5] == 3:
                        posy = fpdf.get_y() + 23.5
                    else:
                        posy = fpdf.get_y() + 30.25
                    fpdf.drawText(x=posx, y=posy, txt="XXXXXXX")
        head = "Match Assessment Forms for %s" % self.disp
        if fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], header=head, pdfnam=pdfnam,
                repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def getName(self, snam, fnam):
        snam = snam.replace("VAN DER", "V D")
        snam = snam.replace("JANSE VAN", "J V")
        if fnam:
            return "%s, %s" % (snam.upper(), fnam.split()[0][0].upper())
        else:
            return snam.upper()

# vim:set ts=4 sw=4 sts=4 expandtab:
