"""
SYNOPSIS
    Bowls Tab Draws Summary.

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

import os, time
from TartanClasses import CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import doPrinter, copyList, getImage, getModName
from tartanFunctions import getSingleRecords, mthendDate

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
        t = time.localtime()
        self.sysdt = time.strftime("%d %B %Y %H:%M:%S", t)
        self.curdt = time.strftime("%Y-%m", t)
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
        r1s = (("Yes","Y"), ("No","N"))
        fld = (
            (("T",0,0,0),"Id2",7,"Starting Period","",
                "","N",self.doStartPeriod,None,None,("efld",)),
            (("T",0,1,0),"Id2",7,"Ending Period","",
                "","N",self.doEndPeriod,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"All Tabs","",
                "Y","N",self.doTabs,None,None,None),
            (("T",0,3,0),("ICB","Tabs-In"),0,"Draw Types","",
                self.drawn,"N",self.doType,None,None,None),
            (("T",0,3,0),("ICB","Bounce"),0,"","",
                self.bounce,"N",self.doType,None,None,None),
            (("T",0,3,0),("ICB","Teams"),0,"","",
                self.teams,"N",self.doType,None,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Totals Only","",
                "N","N",self.doTots,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("Y","Y"))

    def doStartPeriod(self, frt, pag, r, c, p, i, w):
        if w:
            self.start = CCD((w * 100) + 1, "D1", 7)
        else:
            self.start = CCD(0, "UI", 1)

    def doEndPeriod(self, frt, pag, r, c, p, i, w):
        if w:
            self.end = CCD(mthendDate((w * 100) + 1), "D1", 7)
        else:
            self.end = CCD(0, "d1", 7)
            self.end.disp = self.curdt

    def doTabs(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doType(self, frt, pag, r, c, p, i, w):
        if p == 3:
            self.drawn = w
        elif p == 4:
            self.bounce = w
        else:
            self.teams = w

    def doTots(self, frt, pag, r, c, p, i, w):
        self.tots = w

    def doEnd(self):
        self.df.closeProcess()
        dat = []
        tps = []
        if self.drawn == "Y":
            tps.extend(["B", "D", "P"])
        if self.bounce == "Y":
            tps.append("A")
        if self.teams == "Y":
            tps.append("C")
        where = [
            ("bdt_cono", "=", self.opts["conum"]),
            ("bdt_tab", "<", self.nstart),
            ("bdt_flag", "in", tps)]
        if self.start.work:
            where.append(("bdt_date", ">=", self.start.work))
        if self.end.work:
            where.append(("bdt_date", "<=", self.end.work))
        whr = copyList(where)
        if self.whole == "N":
            tab = []
            rec = getSingleRecords(self.opts["mf"], "bwldrt", ("bdt_tab",
                "bdt_name"), head=["X", "Tab-No", "Name"], where=whr,
                group="bdt_tab, bdt_name", order="bdt_name",
                selcol="bdt_name")
            if not rec:
                self.opts["mf"].closeLoop()
                return
            for r in rec:
                tab.append(r[1])
            whr.append(("bdt_tab", "in", tab))
        odr = "bdt_name, bdt_date"
        rec = self.sql.getRec("bwldrt", where=whr, order=odr)
        c = self.sql.bwldrt_col
        l = ""
        self.dic = {}
        for r in rec:
            self.clash = ""
            dte = CCD(r[c.index("bdt_date")], "D1", 10)
            side = [["", ""], ["", ""], ["", ""], ["", ""]]
            self.tab = r[c.index("bdt_tab")]
            if self.tab not in self.dic:
                self.dic[self.tab] = []
            nam = self.getName(self.tab)
            pos = (0 - (r[c.index("bdt_pos")] - 4))
            side[pos] = ["", nam]
            for x in range(1, 4):
                tm = self.getName(r[c.index("bdt_team%s" % x)])
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
            d.extend([dte.disp, side[0], side[1], side[2], side[3]])
            dat.append(d)
            l = self.tab
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=120, auto=True)
        self.fpdf.header = self.pageHeading
        if self.tots == "N":
            # Print teams
            self.heading = "main"
            self.fpdf.add_page()
            cwth = self.fpdf.get_string_width("X")
            for d in dat:
                if not d:
                    self.fpdf.drawText(txt="", w=0, h=5, border=0, ln=1)
                else:
                    self.fpdf.cell(w=cwth*21, h=5, txt=d[0], border=0, ln=0)
                    self.fpdf.cell(w=cwth*11, h=5, txt=d[1], border=0, ln=0)
                    if d[2][0]:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[2][1], border=1,
                            ln=0)
                    else:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[2][1], border=0,
                            ln=0)
                    if d[3][0]:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[3][1], border=1,
                            ln=0)
                    else:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[3][1], border=0,
                            ln=0)
                    if d[4][0]:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[4][1], border=1,
                            ln=0)
                    else:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[4][1], border=0,
                            ln=0)
                    if d[5][0]:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[5][1], border=1,
                            ln=1)
                    else:
                        self.fpdf.cell(w=cwth*21, h=5, txt=d[5][1], border=0,
                            ln=1)
        if self.whole == "Y" or self.tots == "Y":
            # Print top attendees
            self.heading = "summary"
            whr = copyList(where)
            whr.append(("bdt_tab", "<", self.nstart))
            self.cnt = self.sql.getRec("bwldrt",
                    cols=["count(*) as count", "bdt_tab"],
                    where=whr, group="bdt_tab",
                    order="count desc, bdt_name")
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
        head = "Tabs Draw Summary for the period %s to %s" % (self.start.disp,
            self.end.disp)
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header=head, repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def getName(self, tab, cls=True):
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
        if cls:
            if tab in self.dic[self.tab]:
                self.clash = True
            self.dic[self.tab].append(tab)
        return nam

    def pageHeading(self):
        self.fpdf.setFont("Arial", "B", 15)
        if os.path.isfile(self.image):
            self.fpdf.image(self.image, 10, 10, 15, 11)
            self.fpdf.cell(20)
        x = self.fpdf.get_x()
        self.fpdf.cell(0, 10, self.opts["conam"],"TLR",1,"C")
        self.fpdf.set_x(x)
        if self.heading == "main":
            self.fpdf.cell(0, 10, "Tabs-In for the period %s to %s" % \
                (self.start.disp, self.end.disp), "LRB", 1, "C")
            self.fpdf.ln(8)
            self.fpdf.setFont(style="B")
            self.fpdf.cell(0, 5, "%-20s %-10s %-20s %-20s %-20s %-20s" % \
                ("Member", "   Date", "Skip", "Third", "Second", "Lead"), "B")
            self.fpdf.ln(5)
        else:
            self.fpdf.cell(0, 10, "Top Attendees for the period "\
                "%s to %s" % (self.start.disp, self.end.disp),
                "LRB", 0, "C")
            self.fpdf.ln(15)
            self.fpdf.cell(0, 5, "%5s %-50s %5s %-30s" % ("Count", "Member",
                "Count", "Member"), "B")
            self.fpdf.ln(10)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
