"""
SYNOPSIS
    Bowls Tab Draws Summary.

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

import os, time
from TartanClasses import CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import dateDiff, doPrinter, copyList, getImage
from tartanFunctions import getModName, getSingleRecords, mthendDate

class bc3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwldrt", "bwltab"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.nstart = bwlctl["ctb_nstart"]
        self.fromad = bwlctl["ctb_emadd"]
        self.days = bwlctl["ctb_weeks"] * 7
        t = time.localtime()
        self.curdt = int(time.strftime("%Y%m", t))
        self.image = os.path.join(self.opts["mf"].rcdic["wrkdir"], "bowls.png")
        if not os.path.exists(self.image):
            getImage("bowls", fle=self.image)
        if not os.path.exists(self.image):
            self.image = None
        self.drawn = "Y"
        self.bounce = "N"
        self.teams = "N"
        return True

    def mainProcess(self):
        r1s = (("Yes","Y"), ("No","N"), ("Only","O"))
        r2s = (("Yes","Y"), ("No","N"), ("Skips Only","S"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                "","Y",self.doStartPeriod,None,None,("efld",)),
            (("T",0,1,0),"Id2",7,"Ending Period","",
                "","N",self.doEndPeriod,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Top Attendees","",
                "N","N",self.doTots,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"All Tabs","",
                "Y","N",self.doTabs,None,None,None),
            (("T",0,4,0),("ICB","Tabs-In"),0,"Draw Types","",
                self.drawn,"N",self.doType,None,None,None),
            (("T",0,4,0),("ICB","Bounce"),0,"","",
                self.bounce,"N",self.doType,None,None,None),
            (("T",0,4,0),("ICB","Teams"),0,"","",
                self.teams,"N",self.doType,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("Y","Y"))

    def doStartPeriod(self, frt, pag, r, c, p, i, w):
        if w:
            self.start = (w * 100) + 1
        else:
            self.start = w

    def doEndPeriod(self, frt, pag, r, c, p, i, w):
        if w:
            self.end = mthendDate((w * 100) + 1)
        else:
            self.end = mthendDate((self.curdt * 100) + 1)

    def doTots(self, frt, pag, r, c, p, i, w):
        self.tots = w
        if self.tots == "O":
            return "sk4"

    def doTabs(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doType(self, frt, pag, r, c, p, i, w):
        if p == 3:
            self.drawn = w
        elif p == 4:
            self.bounce = w
        else:
            self.teams = w

    def doEnd(self):
        self.df.closeProcess()
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=120,
            auto=True)
        self.fpdf.header = self.pageHeading
        if self.tots != "O":
            tps = []
            if self.drawn == "Y":
                tps.append("D")
            if self.bounce == "Y":
                tps.append("A")
            if self.teams == "Y":
                tps.append("C")
            for self.heading in tps:
                if self.heading == "D":
                    cls = True
                else:
                    cls = False
                where = [
                    ("bdt_cono", "=", self.opts["conum"]),
                    ("bdt_tab", "<", self.nstart)]
                if self.heading == "D":
                    where.append(("bdt_flag", "in", ("B", "D", "P")))
                else:
                    where.append(("bdt_flag", "=", self.heading))
                if self.start:
                    where.append(("bdt_date", ">=", self.start))
                if self.end:
                    where.append(("bdt_date", "<=", self.end))
                whr = copyList(where)
                if self.whole == "S":
                    whr.append(("bdt_pos", "=", 4))
                elif self.whole == "N":
                    tab = []
                    rec = getSingleRecords(self.opts["mf"], "bwldrt",
                        ("bdt_tab", "bdt_name"), head=["X", "Tab-No", "Name"],
                        where=whr, group="bdt_tab, bdt_name", order="bdt_name",
                        selcol="bdt_name")
                    if not rec:
                        self.opts["mf"].closeLoop()
                        return
                    for r in rec:
                        tab.append(r[1])
                    whr.append(("bdt_tab", "in", tab))
                odr = "bdt_name, bdt_date, bdt_time asc"
                rec = self.sql.getRec("bwldrt", where=whr, order=odr)
                c = self.sql.bwldrt_col
                l = ""
                dat = []
                self.dic = {}
                for r in rec:
                    self.clash = ""
                    side = [["", ""], ["", ""], ["", ""], ["", ""]]
                    dte = CCD(r[c.index("bdt_date")], "D1", 10)
                    if r[c.index("bdt_time")] == "M":
                        tim = "AM"
                    else:
                        tim = "PM"
                    self.tab = r[c.index("bdt_tab")]
                    if self.tab not in self.dic:
                        self.dic[self.tab] = {}
                    nam = self.getName(self.tab, dte=dte.work, cls=cls)
                    pos = (0 - (r[c.index("bdt_pos")] - 4))
                    side[pos] = ["", nam]
                    for x in range(1, 4):
                        tm = self.getName(r[c.index("bdt_team%s" % x)],
                            cls=cls, dte=dte.work)
                        if not tm:
                            continue
                        if self.clash:
                            cl = "X"
                        else:
                            cl = ""
                        pos = (0 - (r[c.index("bdt_pos%s" % x)] - 4))
                        side[pos] = [cl, tm]
                    if self.tab != l:
                        if l:
                            dat.append([])
                        d = [nam]
                    else:
                        d = [""]
                    d.extend([dte.disp, tim, side[0], side[1],
                        side[2], side[3]])
                    dat.append(d)
                    l = self.tab
                self.fpdf.add_page()
                cwth = self.fpdf.get_string_width("X")
                for d in dat:
                    if not d:
                        self.fpdf.drawText(txt="", w=0, h=5, border=0, ln=1)
                    else:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[0], border=0, ln=0)
                        self.fpdf.cell(w=cwth*11, h=5, txt=d[1], border=0, ln=0)
                        self.fpdf.cell(w=cwth*3, h=5, txt=d[2], border=0, ln=0)
                        if d[3][0]:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[3][1],
                                border=1, ln=0)
                        else:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[3][1],
                                border=0, ln=0)
                        if d[4][0]:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[4][1],
                                border=1, ln=0)
                        else:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[4][1],
                                border=0, ln=0)
                        if d[5][0]:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[5][1],
                                border=1, ln=0)
                        else:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[5][1],
                                border=0, ln=0)
                        if d[6][0]:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[6][1],
                                border=1, ln=1)
                        else:
                            self.fpdf.cell(w=cwth*21, h=5, txt=d[6][1],
                                border=0, ln=1)
        if self.tots != "N":
            # Print top attendees
            self.heading = "summary"
            whr = [
                ("bdt_cono", "=", self.opts["conum"]),
                ("bdt_tab", "<", self.nstart)]
            if self.start:
                whr.append(("bdt_date", ">=", self.start))
            if self.end:
                whr.append(("bdt_date", "<=", self.end))
            self.cnt = self.sql.getRec("bwldrt",
                cols=["count(*) as count", "bdt_tab"], where=whr,
                group="bdt_tab", order="count desc, bdt_name")
            while self.cnt:
                self.fpdf.add_page()
                if len(self.cnt) < 26:
                    left = copyList(self.cnt)
                    self.cnt = []
                    right = []
                else:
                    left = self.cnt[:25]
                    self.cnt = self.cnt[25:]
                    if len(self.cnt) < 26:
                        right = copyList(self.cnt)
                        self.cnt = []
                    else:
                        right = self.cnt[:25]
                        self.cnt = self.cnt[25:]
                left = left + (25 - len(left)) * [["", ""]]
                right = right + (25 - len(right)) * [["", ""]]
                self.fpdf.set_font("Arial", "", 15)
                cwth = self.fpdf.get_string_width("X")
                for x in range(25):
                    if left[x][1]:
                        left[x][1] = self.getName(left[x][1], cls=False)
                    if right[x][1]:
                        right[x][1] = self.getName(right[x][1], cls=False)
                    self.fpdf.cell(cwth*5, 8, "%5s " % left[x][0], 0, 0, "R")
                    self.fpdf.cell(cwth*24, 8, left[x][1], 0, 0, "L")
                    self.fpdf.cell(cwth*5, 8, "%5s " % right[x][0], 0, 0, "R")
                    self.fpdf.cell(cwth*20, 8, right[x][1], 0, 1, "L")
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        too = CCD(self.end // 100, "D2", 7).disp
        if self.start:
            frm = CCD(self.start // 100, "D2", 7).disp
            head = "Tabs Draw Summary for the period %s to %s" % (frm, too)
        else:
            head = "Tabs Draw Summary up to %s" % too
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def getName(self, tab, cls=True, dte=None):
        self.clash = False
        if not tab:
            return ""
        rec = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names", "btb_rate1"], where=[("btb_tab", "=", tab)],
            limit=1)
        if not rec:
            return "VISITOR, A"
        if rec[1]:
            nam = "%s, %s" % (rec[0], rec[1][0])
        else:
            nam = rec[0]
        nam = nam.replace("VAN DER", "V D")
        nam = nam.replace("JANSE VAN", "J V")
        if cls and tab != self.tab:
            if tab in self.dic[self.tab]:
                lst = self.dic[self.tab][tab][-1]
                dys = dateDiff(lst, dte, "days")
                if dys < self.days:
                    self.clash = True
            else:
                self.dic[self.tab][tab] = []
            self.dic[self.tab][tab].append(dte)
        return nam

    def pageHeading(self):
        frm = CCD(self.start // 100, "d2", 7).disp
        too = CCD(self.end // 100, "D2", 7).disp
        self.fpdf.setFont("Arial", "B", 15)
        if os.path.isfile(self.image):
            self.fpdf.image(self.image, 10, 10, 15, 11)
            self.fpdf.cell(20)
        x = self.fpdf.get_x()
        self.fpdf.cell(0, 10, self.opts["conam"],"TLR",1,"C")
        self.fpdf.set_x(x)
        if self.heading == "summary":
            self.fpdf.cell(0, 10, "Top Attendees for the period "\
                "%s to %s" % (frm, too), "LRB", 0, "C")
            self.fpdf.ln(15)
            self.fpdf.cell(0, 5, "%5s %-50s %5s %-30s" % ("Count", "Member",
                "Count", "Member"), "B")
            self.fpdf.ln(10)
            return
        if self.heading == "D":
            self.fpdf.cell(0, 10, "Tabs-In for the period %s to %s" % \
                (frm, too), "LRB", 1, "C")
        elif self.heading == "A":
            self.fpdf.cell(0, 10, "Arranged Games for the period %s to %s" % \
                (frm, too), "LRB", 1, "C")
        elif self.heading == "C":
            self.fpdf.cell(0, 10, "Team Games for the period %s to %s" % \
                (frm, too), "LRB", 1, "C")
        self.fpdf.ln(8)
        self.fpdf.setFont(style="B")
        self.fpdf.cell(0, 5, "%-20s %-10s %2s %-20s %-20s %-20s %-20s" % \
            ("Member", "   Date", "TM", "Skip", "Third", "Second", "Lead"), "B")
        self.fpdf.ln(5)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
