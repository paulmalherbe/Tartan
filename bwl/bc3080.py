"""
SYNOPSIS
    Competition Format Sheet.

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

import os, time
from TartanClasses import GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import copyList, getImage, getModName, doPrinter

class bc3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.ctyp = self.opts["args"][0]
                self.cnam = self.opts["args"][1]
                self.notes = False
                self.card = False
                self.qty = 1
                self.doEnd()
            else:
                self.mainProcess()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwltyp", "bwlpts",
            "bwlnot"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
        t = time.localtime()
        self.sysdt = time.strftime("%d %B %Y %H:%M:%S", t)
        self.image = os.path.join(self.opts["mf"].rcdic["wrkdir"], "bowls.png")
        if not os.path.exists(self.image):
            getImage("bowls", fle=self.image)
        if not os.path.exists(self.image):
            self.image = None
        self.card = True
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Competition Format")
        com = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        r1s = (("A4 Page", "P"), ("A6 Card", "C"))
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","Y",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"ITV",(50,10),"Notes","",
                "","N",self.doNotes,None,None,None,None,"""Enter All Additional Rules and Notes for the Competition e.g. what to do in these cases:

Trial Ends - Only 1 trial end per game.
Burnt Ends - Replay the end."""),
            (("T",0,2,0),("IRB",r1s),0,"Paper Type","",
                "P","N",self.doPaper,None,None,None),
            (("T",0,3,0),"IUI",2,"Quantity","",
                1,"N",self.doQty,None,None,("notzero",)))
        but = (("Edit Notes", None, self.doEdit, 0, ("T",0,4), ("T",0,5)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], title=self.tit,
            eflds=fld, butt=but, tend=tnd, txit=txt, view=("N","V"),
            mail=("Y","N"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlcmp", cols=["bcm_name", "bcm_type"],
            where=[("bcm_cono", "=", self.opts["conum"]), ("bcm_code", "=", w)],
            limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.cnam = chk[0]
        self.ctyp = chk[1]
        self.df.loadEntry(frt, pag, p+1, data=self.cnam)
        nte = self.sql.getRec("bwlnot", where=[("bcn_cono", "=",
            self.opts["conum"]), ("bcn_ccod", "=", self.ccod)], limit=1)
        if nte:
            self.notes = nte[2]
            self.df.loadEntry(frt, pag, p+2, self.notes)
            return "sk2"

    def doEdit(self):
        self.df.focusField("T", 0, 3, tag=False)

    def doNotes(self, frt, pag, r, c, p, i, w):
        self.notes = w

    def doPaper(self, frt, pag, r, c, p, i, w):
        if w == "P":
            self.card = False
        else:
            self.card = True

    def doQty(self, frt, pag, r, c, p, i, w):
        self.qty = w

    def doEnd(self):
        if "args" not in self.opts:
            hdr = self.tit
            prt = copyList(self.df.repprt)
            eml = copyList(self.df.repeml)
            self.df.closeProcess()
        else:
            hdr = "%03i %s - %s" % (self.opts["conum"], self.opts["conam"],
            "Competition Format")
            prt = ["Y", "V", "view"]
            eml = None
        self.drawFormat()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], pdfnam=pdfnam, header=hdr,
            repprt=prt, fromad=self.fromad, repeml=eml)
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def drawFormat(self):
        whr = [
            ("bct_cono", "=", self.opts["conum"]),
            ("bct_code", "=", self.ctyp)]
        rec = self.sql.getRec("bwltyp", where=whr, limit=1)
        ldic = {}
        for col in self.sql.bwltyp_col[3:]:
            ldic[col] = rec[self.sql.bwltyp_col.index(col)]
        whr = [
            ("bcp_cono", "=", self.opts["conum"]),
            ("bcp_code", "=", self.ctyp)]
        rec = self.sql.getRec("bwlpts", where=whr)
        for r in rec:
            if r[self.sql.bwlpts_col.index("bcp_ptyp")] == "D":
                ptyp = "drawn"
            else:
                ptyp = "svs"
            ldic[ptyp] = {}
            for col in self.sql.bwlpts_col[3:]:
                ldic[ptyp][col] = r[self.sql.bwlpts_col.index(col)]
        if self.card:
            self.fpdf = MyFpdf(auto=True)
            self.fpdf.set_margins(55, 5, 55)
            self.fpdf.c_margin = self.fpdf.c_margin * 2
            self.fpdf.set_font("Arial","",8)
            h = 3.5
        else:
            self.fpdf = MyFpdf(auto=True)
            self.fpdf.set_font("Arial","",14)
            h = 6
        self.fpdf.header = self.pageHeading
        cwth = self.fpdf.get_string_width("X")
        x1 = self.fpdf.l_margin + (cwth * 20)
        x2 = self.fpdf.l_margin + (cwth * 22)
        for page in range(self.qty):
            self.fpdf.add_page()
            self.fpdf.drawText(txt=self.sql.bwltyp_dic["bct_cfmat"][4],
                h=h, ln=0)
            if ldic["bct_cfmat"] == "T":
                txt = "Tournament"
            elif ldic["bct_cfmat"] in ("D", "K"):
                txt = "Knockout"
            elif ldic["bct_cfmat"] == "R":
                txt = "Round Robin"
            else:
                txt = "Match"
            self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
            self.fpdf.drawText(txt=self.sql.bwltyp_dic["bct_tsize"][4],
                h=h, ln=0)
            self.fpdf.drawText(txt=ldic["bct_tsize"], x=x1, h=h, ctyp="M")
            #if ldic["bct_cfmat"] in ("D", "K", "R"):
            #    return
            self.fpdf.drawText(txt="Draw", h=h, ln=0)
            if ldic["bct_drawn"] == ldic["bct_games"]:
                txt = "All Games will be Random Draws."
            else:
                if ldic["bct_drawn"] == 1:
                    txt = "The First Game will be a Random Draw and "\
                        "thereafter Strength v Strength."
                else:
                    txt = "The First %s Games will be Random Draws and "\
                        "thereafter Strength v Strength." % ldic["bct_drawn"]
            self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
            if ldic["bct_games"]:
                self.fpdf.drawText(txt=self.sql.bwltyp_dic["bct_games"][4],
                    h=h, ln=0)
                self.fpdf.drawText(txt=ldic["bct_games"], x=x1, h=h, ctyp="M")
            self.fpdf.drawText(txt=self.sql.bwltyp_dic["bct_ends"][4],h=h,ln=0)
            self.fpdf.drawText(txt=ldic["bct_ends"], x=x1, h=h, ctyp="M")
            if ldic["bct_grgame"]:
                self.fpdf.drawText(txt="Groups", h=h, ln=0)
                txt = "Teams will be Split into Groups After Game %s." % \
                    ldic["bct_grgame"]
                self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                if ldic["bct_adjust"] == "Y":
                    txt = "With the Exception of Group A, the Scores will be "\
                        "Adjusted as follows:"
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                    if ldic["bct_expunge"]:
                        gms = ldic["bct_expunge"].split(",")
                        if len(gms) == 1:
                            txt = "Game %s will be Expunged" % gms[0]
                        else:
                            txt = "Games %s" % gms[0]
                            for n, g in enumerate(gms[1:]):
                                if n == len(gms) - 2:
                                    txt = "%s and %s" % (txt, g)
                                else:
                                    txt = "%s, %s" % (txt, g)
                            txt = "%s will be Expunged." % txt
                        self.fpdf.drawText(txt=txt, x=x2, h=h, ctyp="M")
                    if ldic["bct_percent"]:
                        if ldic["bct_expunge"]:
                            txt = "The Balance of the Games"
                        else:
                            txt = "All Games"
                        txt = "%s will Retain %s%s of their score." % (txt,
                            ldic["bct_percent"], "%")
                        self.fpdf.drawText(txt=txt, x=x2, h=h, ctyp="M")
            # Points
            self.fpdf.drawText(h=h)
            if ldic["bct_pdiff"] == "Y":
                nums = ["drawn", "svs"]
            else:
                nums = ["drawn"]
            for ptyp in nums:
                if ldic["bct_pdiff"] == "N":
                    txt = "Scoring for All Games"
                elif ptyp == "drawn":
                    txt = "Scoring for Drawn Games"
                else:
                    txt = "Scoring for S v S Games"
                self.fpdf.drawText(txt=txt, h=h)
                self.fpdf.underLine(h=h, txt=txt)
                if ldic[ptyp]["bcp_sends"]:
                    self.fpdf.drawText(txt="Skins", h=h, ln=0)
                    self.fpdf.drawText(txt="Each Set of %s Ends will "\
                        "Constitute a Skin." % ldic[ptyp]["bcp_sends"], x=x1,
                        h=h, ctyp="M")
                self.fpdf.drawText(txt="Points", h=h, ln=0)
                txt = ""
                pts = 0
                if ldic[ptyp]["bcp_e_points"]:
                    if ldic[ptyp]["bcp_e_points"] == 1:
                        txt = "%s Point per End" % ldic[ptyp]["bcp_e_points"]
                    else:
                        txt = "%s Points per End" % ldic[ptyp]["bcp_e_points"]
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                    pts += (ldic[ptyp]["bcp_e_points"] * ldic["bct_ends"])
                if ldic[ptyp]["bcp_s_points"]:
                    if ldic[ptyp]["bcp_s_points"] == 1:
                        txt = "%s Point per Skin" % ldic[ptyp]["bcp_s_points"]
                    else:
                        txt = "%s Points per Skin" % ldic[ptyp]["bcp_s_points"]
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                    pts += (ldic[ptyp]["bcp_s_points"] *
                        int(ldic["bct_ends"] / ldic[ptyp]["bcp_sends"]))
                if ldic[ptyp]["bcp_g_points"]:
                    if ldic[ptyp]["bcp_g_points"] == 1:
                        txt = "%s Point per Game" % ldic[ptyp]["bcp_g_points"]
                    else:
                        txt = "%s Points per Game" % ldic[ptyp]["bcp_g_points"]
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                    pts += ldic[ptyp]["bcp_g_points"]
                if ldic[ptyp]["bcp_bonus"] == "Y":
                    txt = "1 Bonus Point will be Awarded as Follows:"
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
                    txt = "Winning by %s or More Shots or" % \
                        (ldic[ptyp]["bcp_win_by"] + 1)
                    self.fpdf.drawText(txt=txt, x=x2, h=h, ctyp="M")
                    txt = "Losing by %s or Less Shots" % \
                        (ldic[ptyp]["bcp_lose_by"] - 1)
                    self.fpdf.drawText(txt=txt, x=x2, h=h, ctyp="M")
                    pts += 1
                if pts:
                    if pts == 1:
                        txt = "Point"
                    else:
                        txt = "Points"
                    txt = "Therefore a Maximum of %s %s per Game." % (pts, txt)
                    self.fpdf.drawText(txt=txt, x=x1, h=h, ctyp="M")
            if self.notes:
                txt = "Notes"
                self.fpdf.drawText(h=h)
                self.fpdf.drawText(txt=txt, h=h)
                self.fpdf.underLine(h=h, txt=txt)
                self.fpdf.drawText(txt=self.notes, h=h, ctyp="M")
                self.sql.delRec("bwlnot", where=[("bcn_cono", "=",
                    self.opts["conum"]), ("bcn_ccod", "=", self.ccod)])
                self.sql.insRec("bwlnot", data=[self.opts["conum"],
                    self.ccod, self.notes])
                self.opts["mf"].dbm.commitDbase()

    def pageHeading(self):
        if self.card:
            self.fpdf.set_fill_color(220)
            self.fpdf.set_font("Arial","B",12)
            self.fpdf.drawText("Competiton Format and Points", h=6, align="C",
                border="TLRB", fill=True)
            self.fpdf.set_line_width(1)
            self.fpdf.rect(self.fpdf.l_margin, self.fpdf.t_margin, 100, 140)
            self.fpdf.set_line_width(0)
            self.fpdf.ln(4)
            return
        if self.image:
            if self.card:
                self.fpdf.image(self.image, x=10, y=10, w=7, h=5)
            else:
                self.fpdf.image(self.image, x=10, y=10, w=15, h=11)
        self.fpdf.set_font("Arial","B",15)
        self.fpdf.cell(20)
        self.fpdf.cell(0,10,"Format Sheet for the %s" % self.cnam,1,0,"C")
        self.fpdf.ln(20)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
