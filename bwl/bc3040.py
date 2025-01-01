"""
SYNOPSIS
    Bowls League Match Declaration Forms.

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

import os
from TartanClasses import GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import doDrawTable, doPrinter, getModName

class bc3040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, tables=["ctlmst", "bwlclb",
            "bwlflf", "bwlflm", "bwlflo", "bwltab", "bwlfls", "bwlflt"],
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
        mch = {
            "stype": "R",
            "tables": ("bwlflm",),
            "cols": (
                ("bfm_date", "", 0, "Match-Date"),
                ("bfm_round", "", 0, "RN")),
            "where": [("bfm_cono", "=", self.opts["conum"])],
            "whera": [("T", "bfm_fmat", 0, 0)],
            "group": "bfm_date, bfm_round"}
        fld = (
            (("T",0,0,0),"I@bff_code",0,"","",
                0,"Y",self.doFmat,fmt,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"I@bfm_date",0,"","",
                0,"Y",self.doDate,mch,None,("efld",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("N","V"), mail=("Y","Y"))

    def doFmat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bwlflf", cols=["bff_desc", "bff_logo"],
            where=[("bff_cono", "=", self.opts["conum"]), ("bff_code", "=",
            w)], limit=1)
        if not acc:
            return "Invalid Format"
        self.fmat = w
        self.fdes = acc[0].upper()
        self.logo = acc[1]
        if not os.path.isfile(self.logo):
            self.logo = None
        self.df.loadEntry(frt, pag, p+1, data=self.fdes)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.recs = self.sql.getRec("bwlflm", cols=["bfm_round",
            "bfm_team", "bfm_opps", "bfm_venue", "bfm_captain"],
            where=[("bfm_cono", "=", self.opts["conum"]), ("bfm_fmat", "=",
            self.fmat), ("bfm_type", "=", "F"), ("bfm_date", "=", w)],
            order="bfm_team")
        if not self.recs:
            return "No Fixtures for this Date"
        self.date = w
        self.disp = self.df.t_disp[0][0][2]

    def doEnd(self):
        self.df.closeProcess()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, "declare_%s" % self.date, ext="pdf")
        fpdf = MyFpdf(name=self.__class__.__name__, head=90)
        cw = fpdf.get_string_width("X")             # character width
        ld = 4.3                                    # line depth
        r1 = {
            "margins": ((25, 85), (10, 16)),
            "repeat": (1, 1),
            "rows": (
                (25, 10, 50, 1.5, .8),
                (25, 13, 50, 1.5, .8),
                (25, 15, (
                    (11, 1.5, .8, "Division"), (4, 1.5),
                    (11, 1.5, .8, "Round"), (4, 1.5),
                    (6, 1.5, .8, "Date"), (14, 1.5))),
                (25, 17, ((10, 1.5, .8, "Played at"), (40, 1.5))))}
        r2 = {
            "margins": ((10, 85), (19.5, 27)),
            "repeat": (1, 3),
            "rows": (
                (10, 19.5, (
                    (10, 1.5, .8, "Position"),
                    (10, 1.5, .8, "Initials"),
                    (50, 1.5, .8, "Surname"),
                    (10, 1.5, .8, "BSA No."))),
                (10, 21, (
                    (10, 1.5, .9, ("Skip", "Third", "Second", "Lead")),
                    (10, 1.5), (50, 1.5), (10, 1.5)), 4))}
        r3 = {
            "margins": ((10, 85), (46, 50.5)),
            "repeat": (1, 1),
            "rows": (
                (10, 46, (
                    (10, 1.5, .8, "Position"),
                    (10, 1.5, .8, "Initials"),
                    (50, 1.5, .8, "Surname"),
                    (10, 1.5, .8, "BSA No."))),
                (10, 47.5, (
                    (10, 1.5, .9, "Reserve"), (10,1.5), (50,1.5), (10,1.5))),
                (10, 49, (
                    (10, 1.5, .9, "Captain"), (10,1.5), (50,1.5))))}
        for cnt, match in enumerate(self.recs):
            fpdf.add_page()
            side = self.sql.getRec("bwlfls", cols=["bfs_league",
                "bfs_division"], where=[("bfs_cono", "=", self.opts["conum"]),
                ("bfs_fmat", "=", self.fmat), ("bfs_code", "=", match[1])],
                limit=1)
            if side[0] == "F":
                continue
            if self.logo:
                fpdf.image(self.logo, 5*cw, 1*ld, 35, 40)
                fpdf.image(self.logo, 77*cw, 1*ld, 35, 40)
            fpdf.setFont("helvetica", "B", 16)
            fpdf.drawText(y=2*ld, w=90*cw, align="C",
                txt="WESTERN PROVINCE BOWLS")
            fpdf.drawText(y=4*ld, w=90*cw, align="C",
                txt="%s CHAMPIONSHIP" % self.fdes)
            fpdf.drawText(y=6*ld, w=90*cw, align="C",
                txt="MATCH DECLARATION FORM")
            fpdf.setFont("helvetica", "B", 14)
            fpdf.drawText(y=8*ld, w=90*cw, align="C",
                txt="The following players will "\
                "represent")
            fpdf.drawText(y=11.7*ld, w=90*cw, align="C", txt="vs")
            fpdf.setFont("helvetica", "B", 12)
            last, tab1 = doDrawTable(fpdf, r1, ppad=1, cw=cw, ld=ld,
                font=False)
            last, tab2 = doDrawTable(fpdf, r2, ppad=1, cw=cw, ld=ld,
                font=False)
            last, tab3 = doDrawTable(fpdf, r3, ppad=1, cw=cw, ld=ld,
                font=False)
            if "Bowl" in self.opts["conam"]:
                home = self.opts["conam"]
            else:
                home = "%s Bowling Club" % self.opts["conam"]
            fpdf.drawText(y=(10*ld)+1.2, w=90*cw, align="C", txt=home)
            opp = self.sql.getRec(tables=["bwlflo", "bwlclb"],
                cols=["bcc_name", "bfo_desc"], where=[("bfo_cono", "=",
                self.opts["conum"]), ("bfo_fmat", "=", self.fmat), ("bfo_code",
                "=", match[2]), ("bcc_code=bfo_club",)], limit=1)
            if "Bowl" in opp[0]:
                away = opp[0]
            else:
                away = "%s Bowling Club" % opp[0]
            fpdf.drawText(y=(13*ld)+1.2, w=90*cw, align="C", txt=away)
            fpdf.drawText(x=36*cw, y=(15*ld)+1.2, txt=side[1])
            fpdf.drawText(x=52*cw, y=(15*ld)+1.2, txt=str(match[0]))
            fpdf.drawText(x=63*cw, y=(15*ld)+1.2, txt=self.disp)
            if match[3] == "H":
                venue = home
            else:
                venue = away
            fpdf.drawText(x=36*cw, y=17.3*ld, txt=venue)
            teams = self.sql.getRec(tables=["bwlflt", "bwltab"],
                cols=["btb_names", "btb_surname", "btb_bsano"],
                where=[("bft_cono", "=", self.opts["conum"]), ("bft_fmat", "=",
                self.fmat), ("bft_date", "=", self.date), ("bft_team", "=",
                match[1]), ("btb_tab=bft_player",)],
                order="bft_skip, bft_position")
            for num, player in enumerate(teams):
                init = ""
                if player[0]:
                    for i in player[0].split():
                        init = init + i[0].upper() + " "
                pos = tab2[((num % 4) + 1) * 4][1][int(num / 4)] + .4
                fpdf.drawText(x=20*cw, y=pos*ld, txt=init.strip())
                fpdf.drawText(x=30*cw, y=pos*ld, txt=player[1])
                fpdf.drawText(x=82*cw, y=pos*ld, txt=str(player[2]))
            captain = self.sql.getRec("bwltab", cols=["btb_names",
                "btb_surname", "btb_bsano"], where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", match[4])], limit=1)
            init = ""
            if captain[0]:
                for i in captain[0].split():
                    init = init + i[0].upper() + " "
            fpdf.drawText(x=20*cw, y=(tab3[8][1][0]+.4)*ld, txt=init.strip())
            fpdf.drawText(x=30*cw, y=(tab3[8][1][0]+.4)*ld, txt=captain[1])
            fpdf.drawText(x=10*cw, y=54*ld, txt="Declaration")
            fpdf.drawText(x=10*cw, y=57*ld, txt="I certify that the above "\
                "players are registered with WP Bowls as playing members")
            fpdf.drawText(x=10*cw, y=58*ld, txt="of the Club and that the "\
                "names are without exception the same as those entered")
            fpdf.drawText(x=10*cw, y=59*ld, txt="on the scorecards relevant "\
                "to this match")
            fpdf.drawText(x=10*cw, y=63*ld, txt="CAPTAIN:   _________________")
            fpdf.drawText(x=26*cw, y=64*ld, txt="(Signature)")
        head = "Match Declaration Forms for %s" % self.disp
        if fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], header=head, pdfnam=pdfnam,
                repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)
        self.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
