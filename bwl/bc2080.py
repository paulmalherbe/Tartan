"""
SYNOPSIS
    Bowls 321 Draw.

    This file is part of Tartan Systems (TARTAN).

    Draw Parameters
    ---------------
    1) Apply history i.e. use historical data to determine draw.
    2) Enter preferred number of players i.e.  2, 3 or 4

    Variables:
    ----------
    self.alltabs: {"tab": [surname, names, paid]}
    self.hist: Dictionary of all tabs for the past x weeks as follows:
        {tab: [opponents], ...}
    self.quant = Number of Players per Rink: 2, 3, 4

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

import random, time
from TartanClasses import CCD, GetCtl, MyFpdf
from TartanClasses import SelectChoice, Sql, TartanDialog
from tartanFunctions import askChoice, askQuestion, callModule, copyList
from tartanFunctions import doPrinter, getGreens, getModName, getNextCode
from tartanFunctions import projectDate, showError

class bc2080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwltab", "bwlsdm", "bwlsdt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.mlint = bwlctl["ctb_mlint"]
        self.samen = bwlctl["ctb_samen"]
        self.weeks = bwlctl["ctb_weeks"]
        self.nstart = bwlctl["ctb_nstart"]
        self.ratem = bwlctl["ctb_ratem"]
        self.ratev = bwlctl["ctb_ratev"]
        self.greens = bwlctl["ctb_greens"]
        t = time.localtime()
        self.sysdt = ((t[0] * 10000) + (t[1] * 100) + t[2])
        if t[3] >= 12:
            self.stime = "A"
        else:
            self.stime = "M"
        self.alltabs = {}
        random.seed()
        return True

    def mainProcess(self):
        r1s = (("Morning", "M"), ("Afternoon", "A"))
        fld = (
            (("T",0,0,0),"ID1",10,"Date","",
                self.sysdt,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Time","",
                self.stime,"N",self.doTime,None,None,None),
            (("T",0,2,0),"IUD",5.2,"Fees - Member R","",
                self.ratem,"N",self.doRate,None,None,("efld",)),
            (("T",0,2,0),"IUD",5.2," Visitor R","",
                self.ratev,"N",self.doRate,None,None,("efld",)))
        tnd = ((self.doMEnd,"y"),)
        txt = (self.doMExit,)
        # Set font as big as possible up to 24pts
        self.dfs = self.opts["mf"].rcdic["dfs"]
        if self.dfs < 24:
            self.doSetFont()
        self.nfs = self.opts["mf"].rcdic["dfs"]
        # Create dialog
        self.mf = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, eframe=True)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.dated = CCD(w, "D1", 10).disp
        self.alltabs = {}
        self.drawn = False
        self.saved = False
        self.viewer = False
        self.reprint = False
        self.lasttab = self.nstart - 1
        self.position = ["Skip", "Third", "Second", "Lead"]

    def doTime(self, frt, pag, r, c, p, i, w):
        self.time = w
        self.alter = False
        if self.time == "A":
            self.timed = "Afternoon"
        else:
            self.timed = "Morning"
        self.drm = self.sql.getRec("bwlsdm", where=[("bsm_cono", "=",
            self.opts["conum"]), ("bsm_date", "=", self.date), ("bsm_time",
            "=", self.time)], limit=1)
        if self.drm:
            state = self.mf.disableButtonsTags()
            self.mf.setWidget(self.mf.mstFrame, state="hide")
            butt = [("None", "N"), ("View", "V"), ("Reprint", "R")]
            dnxt = self.sql.getRec("bwlsdm", where=[("bsm_cono", "=",
                self.opts["conum"]), ("bsm_date", ">", self.date)],
                limit=1)
            if not dnxt:
                butt.extend([("Alter", "A"), ("Delete", "X")])
                text = "Would you like to View, Reprint, Alter or "\
                    "Delete the Draw?"
            else:
                text = "Would you like to View or Reprint It?"
            ok = askChoice(self.opts["mf"].body, "Already Exists",
                "A Draw or Entries for this Date and Time Already "\
                "Exists.\n\n%s" % text, butt=butt, default="None")
            self.mf.setWidget(self.mf.mstFrame, state="show")
            self.mf.enableButtonsTags(state=state)
            if ok == "N":
                return "ff1"
            elif ok == "V":
                self.viewer = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
                self.drawn = True
                return "nc"
            elif ok == "R":
                self.reprint = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
                self.drawn = True
                return "nc"
            elif ok == "A":
                self.alter = True
                self.doLoadMst(self.drm)
                self.doLoadTabs()
            elif ok == "X":
                self.sql.delRec("bwlsdm", where=[("bsm_cono", "=",
                    self.opts["conum"]), ("bsm_date", "=", self.date),
                    ("bsm_time", "=", self.time)])
                self.sql.delRec("bwlsdt", where=[("bst_cono", "=",
                    self.opts["conum"]), ("bst_date", "=", self.date),
                    ("bst_time", "=", self.time)])
                self.opts["mf"].dbm.commitDbase()
                return "ff1"

    def doLoadMst(self, drm):
        self.dhist = drm[self.sql.bwlsdm_col.index("bsm_dhist")]
        self.quant = drm[self.sql.bwlsdm_col.index("bsm_quant")]
        self.mrate = CCD(drm[self.sql.bwlsdm_col.index("bsm_mrate")], "UD", 6.2)
        self.mf.loadEntry("T", 0, 2, data=self.mrate.work)
        self.vrate = CCD(drm[self.sql.bwlsdm_col.index("bsm_vrate")], "UD", 6.2)
        self.mf.loadEntry("T", 0, 3, data=self.vrate.work)

    def doLoadTabs(self):
        draws = self.sql.getRec("bwlsdt", cols=["bst_tab", "bst_name",
            "bst_rink", "bst_opp1", "bst_opp2", "bst_opp3"],
            where=[("bst_cono", "=", self.opts["conum"]), ("bst_date",
            "=", self.date), ("bst_time", "=", self.time)],
            order="bst_rink")
        self.games = []
        self.drawn = True
        lrk = None
        gme = []
        for draw in draws:
            if draw[2] != lrk:
                if lrk is not None:
                    gme.insert(0, lrk)
                    self.games.append(gme)
                lrk = draw[2]
                gme = []
            gme.append(draw[0])
            tab = self.sql.getRec("bwltab", cols=["btb_surname",
                "btb_names", "btb_gender", "btb_pos1", "btb_rate1",
                "btb_pos2", "btb_rate2"], where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", draw[0])],
                limit=1)
            if tab:
                self.alltabs[draw[0]] = [tab[0], tab[1], "Y"]
                if not draw[2]:
                    continue
        if gme:
            gme.insert(0, lrk)
            self.games.append(gme)

    def doRate(self, frt, pag, r, c, p, i, w):
        if p == 2:
            self.mrate = CCD(w, "UD", 6.2)
        else:
            self.vrate = CCD(w, "UD", 6.2)

    def doMEnd(self):
        if self.viewer:
            self.doShowDraw("Current Draw", self.games)
            self.mf.focusField("T", 0, 1)
        elif self.reprint:
            self.doPrint(self.mf)
            self.mf.focusField("T", 0, 1)
        else:
            self.mf.closeProcess()
            self.doTabs()

    def doMExit(self):
        self.mf.closeProcess()
        self.opts["mf"].closeLoop()

    def doTabs(self):
        tit = "321 Draw for the %s of %s" % (self.timed, self.dated)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        v1 = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_tab", "", 0, "Tab")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", ">=", self.nstart)],
            "order": "btb_surname, btb_names"}
        v2 = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_names", "", 0, "Names"),
                ("btb_tab", "", 0, "Tab")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_tab", ">=", self.nstart)],
            "whera": [("T", "btb_surname", 1, 1)],
            "order": "btb_names"}
        r2s = (("Yes", "Y"), ("No", "N"))
        tag = (("", None, None, None, False),)
        fld = (
            (("T",0,0,0),"OUI",3,"Tabs Entered:"),
            (("T",1,0,0),"I@btb_tab",0,"","Tab Number(noesc)",
                "","Y",self.doTab,mem,None,("efld",)),
            (("T",1,1,0),"I@btb_surname",0,"","",
                "","N",self.doSurname,v1,None,("notblank",)),
            (("T",1,2,0),"I@btb_names",0,"","",
                "","N",self.doNames,v2,None,("efld",)),
            (("T",1,3,0),("IRB",r2s),0,"Paid","",
                "Y","N",None,None,self.doDelete,None))
        but = (
            ("Entered",None,self.doEntered,0,("T",1,1),None,
                "Display a list of Entered Tabs",1),
            ("Do Draw",None,self.doDraw,0,("T",1,1),None,
                "Genetrate a New Draw",1),
            ("View",None,self.doView,0,("T",1,1),None,
                "View and/or Change the Draw",1),
            ("Print",None,self.doPrint,0,("T",1,1),None,
                "Print the Draw",1),
            ("Exit",None,self.doExit,1,None,None,None,1))
        tnd = (None, (self.doEnd,"n"))
        txt = (None, self.doExit)
        # Create dialog
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit,
            tags=tag, eflds=fld, butt=but, tend=tnd, txit=txt, eframe=True)
        if self.alter:
            for b in range(1, 4):
                wid = getattr(self.df, "B%i" % b)
                self.df.setWidget(wid, "normal")
        else:
            self.alltabs = {}
        self.doShowQuantity()
        self.df.focusField("T", 1, 1)

    def doTab(self, frt, pag, r, c, p, i, w):
        self.modify = False
        self.visitor = False
        if w == 999999:
            self.doTestDraw()
            return "rf"
        elif w > 999900:
            self.doTestTabs(w % 100)
            return "rf"
        elif not w:
            yn = askQuestion(self.opts["mf"].body, "Missing Tab",
                "Is This a Visitor?", default="no")
            if yn == "yes":
                self.visitor = True
                self.tab = getNextCode(self.sql, "bwltab", "btb_tab",
                    where=[("btb_cono", "=", self.opts["conum"])],
                    start=self.nstart, last=899999)
                self.df.loadEntry(frt, pag, p, data=self.tab)
            else:
                return "rf"
        elif not self.doLoadTab(w, frt):
            return "Invalid Tab Number"
        else:
            return "sk2"

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwltab", cols=["btb_tab", ],
            where=[("btb_cono", "=", self.opts["conum"]), ("btb_surname",
            "ilike", self.sname, "and", "btb_names", "ilike", w),
            ("btb_tab", ">=", self.nstart)], order="btb_tab", limit=1)
        if chk:
            self.df.loadEntry(frt, pag, 0, data=chk[0])
            self.doLoadTab(chk[0], frt)
            self.visitor = False
            return "sk3"

    def doEntered(self):
        data = []
        for tab in self.alltabs:
            data.append([tab] + self.alltabs[tab])
        data.sort()
        titl = "List of All Entered Tabs"
        head = ("Tab", "Surname", "Names", "G", "P", "RT", "P")
        line = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": [("UI", 3), ("NA", 20, "Y"), ("NA", 20),
                ("UA", 1), ("UI", 1), ("UI", 2), ("UA", 1)],
            "data": data,
            "sort": True}
        self.opts["mf"].updateStatus("")
        state = self.df.disableButtonsTags()
        show = self.df.selChoice(line)
        self.df.enableButtonsTags(state=state)
        if self.saved:
            self.df.focusField("T", 1, 1)
            return
        if show.selection:
            self.modify = False
            self.visitor = False
            self.df.loadEntry("T", 1, 0, data=show.selection[0])
            self.doLoadTab(show.selection[0], "T")
            self.df.focusField("T", 1, 7)
        else:
            self.df.focusField("T", 1, 1)

    def doLoadTab(self, tab, form="T", err=True):
        c = self.sql.bwltab_col
        acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
        if not acc and not err:
            return
        elif not acc and tab >= self.nstart:
            showError(self.opts["mf"].body, "Visitor's Tab",
                "This Tab Number is Reserved for Visitors")
            return
        elif not acc and self.mlint == "Y" and self.samen == "Y":
            return
        elif not acc:
            ok = askQuestion(self.opts["mf"].body, "Missing Tab",
                "This Tab Does Not Exist, Is It a New Member?", default="no")
            if ok == "no":
                return
            callModule(self.opts["mf"], self.df, "bc1010",
                coy=[self.opts["conum"], self.opts["conam"]], args=tab)
            acc = self.sql.getRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
            if not acc:
                return
            self.df.loadEntry("T", 1, 0, data=tab)
        snam = acc[c.index("btb_surname")]
        fnam = acc[c.index("btb_names")]
        if form == "T":
            self.tab = int(tab)
            self.df.loadEntry("T", 1, 1, data=snam)
            self.df.loadEntry("T", 1, 2, data=fnam)
        else:
            if fnam:
                name = snam.upper() + ", " + fnam[0][0].upper()
            else:
                name = snam.upper()
            if form == "A":
                self.at.loadEntry("C", 0, self.at.pos + 1, data=name)
            elif form == "B":
                self.bg.loadEntry("C", 0, self.bg.pos + 1, data=name)
            else:
                return name
        return True

    def doDelete(self):
        if self.tab in self.alltabs:
            del self.alltabs[self.tab]
            self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)
        return ("T", 1, 1)

    def doEnd(self):
        if self.df.pag == 0:
            return
        else:
            if self.tab in self.alltabs:
                del self.alltabs[self.tab]
            self.alltabs[self.tab] = self.df.t_work[1][0][1:]
            if self.visitor:
                data = [self.opts["conum"], self.df.t_work[1][0][0], 0]
                data.extend(self.df.t_work[1][0][1:4])
                data.extend(["", "", "", "", "", "", "", ""])
                data.extend(self.df.t_work[1][0][4:6])
                data.extend(self.df.t_work[1][0][4:6])
                data.append(0)
                self.sql.insRec("bwltab", data=data)
                self.lasttab += 1
            self.drawn = False
            self.doShowQuantity()
            self.df.clearFrame("T", 1)
            self.df.focusField("T", 1, 1)

    def doDraw(self):
        if self.drawn:
            yn = askQuestion(self.opts["mf"].body, "Drawn",
                "This Draw has Already Been Done, Do You Want to Re-Draw?",
                default="no")
            if yn == "no":
                self.df.focusField("T", 1, 1)
                return
            else:
                self.sql.delRec("bwlsdt", where=[("bst_cono", "=",
                    self.opts["conum"]), ("bst_date", "=", self.date),
                    ("bst_time", "=", self.time)])
                self.drawn = False
        np = ""
        for tab in self.alltabs:
            if self.alltabs[tab][2] == "N":
                # Not paid
                np = "%s\n%3i %s, %s" % (np, tab, self.alltabs[tab][0],
                    self.alltabs[tab][1])
        if np:
            # Not paid
            yn = askQuestion(self.opts["mf"].body, "Non Payments",
                """The following People have Not yet Paid:
%s

Do you still want to continue?""" % np, default="no")
            if yn == "no":
                return
        tit = ("Draw Parameters",)
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = [
            (("T",0,0,0),("IRB",r2s),0,"Apply History","",
                "Y","N",self.doHist,None,None,None,None,
                """For at Least %s Weeks:
Try Not to Pair the Same Skips
Try to Avoid Broken Rink Repeats
Try to Allocate Different Rinks""" % self.weeks),
            (("T",0,1,0),"IUI",1,"Competitors","",
                3,"N",self.doSize,None,None,("in", (2,3,4))),
            (("T",0,2,0),"IUA",40,"Greens","Greens (A,B,C)",
                "","N",self.doGreens,None,None,("notblank",),None,
                "Available Greens in the format A,B or A,B345 showing "\
                "Green Code and Rinks. If the Rinks are Not Entered they "\
                "will Default to 6. To enter 7 rinks enter A7, B7 etc.")]
        but = (("Cancel",None,self.doCancel,1,None,None,None,1),)
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.dw = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doDrawEnd,"y"),), txit=(self.doCancel,),
            butt=but)
        self.dw.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state)
        self.df.focusField("T", 1, 1)

    def doDelTabs(self):
        for tab in self.tdata:
            del self.alltabs[tab[0]]
        self.doShowQuantity()
        self.doDraw()

    def doCancel(self):
        self.dw.closeProcess()

    def doHist(self, frt, pag, r, c, p, i, w):
        self.dhist = w

    def doSize(self, frt, pag, r, c, p, i, w):
        self.quant = w
        self.dw.topf[0][2][4] = ""
        if (len(self.alltabs) % self.quant) == 1:
            showError(self.opts["mf"].body, "Error",
                "Invalid Number of Entries")
            return "rf"
        self.getNeeded(len(self.alltabs))
        self.dw.topf[0][2][4] = "Greens (%s Rinks Needed)" % self.needed

    def getNeeded(self, qty):
        self.needed = int(qty / self.quant)
        if qty % self.quant:
            self.needed += 1

    def doGreens(self, frt, pag, r, c, p, i, w):
        w = w.strip(",")
        for green in w.split(","):
            if not green or green[0] not in self.greens:
                return "Invalid Green (%s)" % green
        greens, first, endrnk, error = getGreens(w, self.needed, [])
        if error:
            return error
        self.rinks = []
        used = []
        for green in greens:
            for rink in greens[green]:
                self.rinks.append("%s%s" % (green, rink))
        if used:
            return "Missing Rinks %s" % str(tuple(used)).replace("'", "")
        if len(self.rinks) < self.needed:
            return "Invalid Number of Rinks"

    def doDrawEnd(self):
        self.dw.closeProcess()
        if self.dhist == "Y":
            again = 5000
            self.doHistory(self.weeks * -7)
        else:
            again = 1
        self.rinks1 = copyList(self.rinks)
        self.ndict = copyList(self.alltabs)
        random.shuffle(self.rinks1)
        draws = {}
        for rpt in range(again):
            tabs = list(self.ndict.keys())
            random.shuffle(tabs)
            draws[rpt] = [0, []]
            count = 0
            temp = copyList(tabs)
            for tab in temp:
                if not count:
                    gme = [tab]
                    count += 1
                    continue
                gme.append(tab)
                tabs.remove(tab)
                count += 1
                if self.dhist == "Y":
                    for t in gme:
                        if t in self.hist and tab in self.hist[t]:
                            draws[rpt][0] += 1
                if count == self.quant or not tabs:
                    draws[rpt][1].append(gme)
                    count = 0
        best = 999
        for draw in draws:
            if draws[draw][0] < best:
                best = draws[draw][0]
                self.games = copyList(draws[draw][1])
                if best == 0:
                    break
        for gme in self.games:
            gme.insert(0, self.rinks1.pop())
        self.games.sort()
        self.drawn = True
        txt = "Random 321 Draw"
        self.doShowDraw(txt, self.games)
        self.doSave()

    def doHistory(self, days):
        self.hist = {}
        ldate = projectDate(self.date, days)
        atabs = list(self.alltabs.keys())
        # Get records for past x days excluding bounce, team games and svs
        recs = self.sql.getRec("bwlsdt", where=[("bst_cono", "=",
            self.opts["conum"]), ("bst_tab", "in", atabs),
            ("bst_date", ">=", ldate)])
        for rec in recs:
            dte = rec[self.sql.bwlsdt_col.index("bst_date")]
            tim = rec[self.sql.bwlsdt_col.index("bst_time")]
            if dte == self.date and tim == self.time:
                # Current draw
                continue
            tab = rec[self.sql.bwlsdt_col.index("bst_tab")]
            if tab not in self.hist:
                self.hist[tab] = []
            p1 = self.sql.bwlsdt_col.index("bst_opp1")
            p2 = self.sql.bwlsdt_col.index("bst_opp2")
            p3 = self.sql.bwlsdt_col.index("bst_opp3")
            for r in (p1, p2, p3):
                if rec[r] and rec[r] not in self.hist[tab]:
                    self.hist[tab].append(rec[r])

    def doSave(self):
        # Delete all existing records
        self.sql.delRec("bwlsdm", where=[("bsm_cono", "=", self.opts["conum"]),
            ("bsm_date", "=", self.date), ("bsm_time", "=", self.time)])
        self.sql.delRec("bwlsdt", where=[("bst_cono", "=", self.opts["conum"]),
            ("bst_date", "=", self.date), ("bst_time", "=", self.time)])
        # Insert bwlsdm
        self.sql.insRec("bwlsdm", data=[self.opts["conum"], self.date,
            self.time, self.dhist, self.quant, self.mrate.work,
            self.vrate.work])
        if not self.drawn:
            return
        # Insert bwlsdt
        for g in self.games:
            for n, t in enumerate(g[1:]):
                nam = self.doGetName(t)
                opps = []
                for o in g[1:]:
                    if o != t:
                        opps.append(o)
                while len(opps) != 3:
                    opps.append(0)
                rec = [self.opts["conum"], t, self.date, self.time, g[0], nam]
                rec.extend(opps)
                self.sql.insRec("bwlsdt", data=rec)
        self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.topEntry[1][0], state="disabled")

    def doPrint(self, dg=None):
        if not dg:
            dg = self.df
        if not self.drawn:
            showError(self.opts["mf"].body, "Error",
                "The Draw Has Not Yet Been Done")
            dg.focusField("T", 1, 1)
            return
        dg.setWidget(dg.mstFrame, state="hide")
        fld = []
        if self.mrate.work or self.vrate.work:
            r1s = (("Yes", "Y"), ("No", "N"))
            fld.append(
                (("T",0,0,0),("IRB",r1s),0,"Cash Takings Sheet","",
                    "N","Y",self.doTakings,None,None,None))
        else:
            self.takings = "N"
        self.pd = TartanDialog(self.opts["mf"], tops=True,
            title="Print Dialog", eflds=fld, tend=((self.doPEnd, "n"),),
            txit=(self.doPExit,), view=("N","V"))
        self.pd.mstFrame.wait_window()
        dg.setWidget(dg.mstFrame, state="show")
        if not self.reprint:
            dg.focusField("T", 1, 1)

    def doTakings(self, frt, pag, r, c, p, i, w):
        self.takings = w

    def doPEnd(self):
        self.pd.closeProcess()
        siz = (0, 0, 22, 15, 11.5)
        self.fsiz = siz[self.quant]
        self.fpdf = MyFpdf(name=self.__class__.__name__, orientation="L",
            head=90, auto=True, foot=True)
        self.fpdf.header = self.doPHead
        if self.takings == "Y":
            self.ptyp = "A"
            self.fpdf.add_page()
            self.fpdf.setFont(size=self.fsiz)
            for gme in self.games:
                txt = "%2s"
                dat = [gme[0]]
                for n, t in enumerate(gme[1:]):
                    txt += " %3s %-20s"
                    dat.extend([t, self.doGetName(t)])
                while n < (self.quant - 1):
                    txt += " %3s %-20s"
                    dat.extend(["", ""])
                    n += 1
                self.fpdf.drawText(txt % tuple(dat), border="TBLR")
            mem = 0
            vis = 0
            for m in self.games:
                for t in m[1:]:
                    if not t:
                        continue
                    if t < self.nstart:
                        mem += 1
                    else:
                        vis += 1
            self.fpdf.setFont(style="B", size=14)
            self.fpdf.drawText()
            self.fpdf.drawText()
            ul = "                               ---------"
            txt = ul.replace("-", self.fpdf.suc)
            self.fpdf.drawText("%3s Members  @ R%2s         R %7.2f" % \
                (mem, self.mrate.disp, mem*self.mrate.work), h=5)
            self.fpdf.drawText("%3s Visitors @ R%2s         R %7.2f" % \
                (vis, self.vrate.disp, vis*self.vrate.work), h=5)
            self.fpdf.underLine(t="S", txt=txt)
            self.fpdf.drawText("    Total Takings              R %7.2f" % \
                ((mem*self.mrate.work)+(vis*self.vrate.work)), h=5)
            self.fpdf.underLine(t="D", txt=txt)
        self.ww = (3, 4, 21, 4, 21, 4, 21, 4, 21)
        self.ptyp = "B"
        self.fpdf.add_page()
        self.fpdf.setFont("Arial", "B", self.fsiz)
        for gme in self.games:
            txt = ["%2s"]
            dat = [gme[0]]
            for n, t in enumerate(gme[1:]):
                nam = self.doGetName(t)
                dat.extend([t, nam])
                txt.extend(["%3s", "%-20s"])
            while n < self.quant - 1:
                dat.extend(["", ""])
                txt.extend(["%3s", "%-20s"])
                n += 1
            for n, d in enumerate(dat):
                w = self.fpdf.cwth * self.ww[n]
                if n == len(dat) - 1:
                    ln = 1
                else:
                    ln = 0
                self.fpdf.drawText(txt[n] % d, w=w, h=10, fill=0,
                    font=["Arial", "B", self.fsiz], border="TLRB", ln=ln)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"], "draw",
            "%s_%s" % (self.opts["conum"], self.date), ext="pdf")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                repprt=self.pd.repprt)

    def doPHead(self, htyp="A", ww=None):
        hd1 = "321 Draw for the %s of %s (History %s)" % (self.timed,
            self.dated, self.dhist)
        tx2 = "%2s %3s %-20s %3s %-20s"
        dt2 = ["RK", "Tab", "Name", "Tab", "Name"]
        if self.quant > 2:
            tx2 += " %3s %-20s"
            dt2.extend(["Tab", "Name"])
        if self.quant > 3:
            tx2 += " %3s %-20s"
            dt2.extend(["Tab", "Name"])
        if self.ptyp == "A":
            pad = " " * (55 - len(hd1))
            self.fpdf.drawText("%s %s" % (hd1, pad),
                font=["courier", "B", 14])
            self.fpdf.drawText()
            self.fpdf.setFont(style="B", size=self.fsiz)
            self.fpdf.drawText(tx2 % tuple(dt2), border="TBLR", fill=1)
        else:
            self.fpdf.setFont("Arial", "B", 24)
            self.fpdf.drawText(hd1, align="C")
            self.fpdf.drawText(" ")
            self.fpdf.drawText(" ")
            self.fpdf.setFont("Arial", "B", self.fsiz)
            t = tx2.split()
            for n, d in enumerate(dt2):
                w = self.fpdf.cwth * self.ww[n]
                if n == len(dt2) - 1:
                    ln = 1
                else:
                    ln = 0
                self.fpdf.drawText(t[n] % d, w=w, h=10, fill=1,
                    font=["Arial", "B", self.fsiz], border="TLRB", ln=ln)

    def doPExit(self):
        self.pd.closeProcess()

    def doView(self):
        if not self.drawn:
            showError(self.opts["mf"].body, "Error",
                "The Draw Has Not Yet Been Done")
            self.df.focusField("T", 1, 1)
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.doShowDraw("View of Draw", self.games)
        self.df.enableButtonsTags(state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.doShowQuantity()
        self.df.focusField("T", 1, 1)

    def doShowDraw(self, title, draw, select=False):
        cols = [
            ("rink", "RK", 2, "UA", "N"),
            ("opp1", "Player 1", 24, "UA", "N"),
            ("opp2", "Player 2", 24, "UA", "N")]
        if self.quant > 2:
            cols.append(("opp3", "Player 3", 24, "UA", "N"))
        if self.quant > 3:
            cols.append(("opp4", "Player 4", 24, "UA", "N"))
        data = []
        for d in draw:
            dat = [d[0]]
            for n, t in enumerate(d[1:]):
                nam = self.doGetName(t)
                dat.append("%3s %-20s" % (t, nam[:16]))
            while (n + 1) < self.quant:
                dat.append("%24s" % "")
                n += 1
            data.append(dat)
        sel = SelectChoice(self.opts["mf"].window, title, cols, data,
            live=select, rowc=1)
        if select:
            return sel.selection

    def doChange(self, draw):
        for self.seq in range(0, len(self.games1)):
            if self.games1[self.seq][0] == draw[1]:
                self.cdraw = self.games1[self.seq]
                break
        tit = ("Change Draw",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        fld = [
            (("T",0,0,0),"OUA",2,"RK"),
            (("T",0,1,0),"IUI",6,"Player 1","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,1,0),"OUA",20,""),
            (("T",0,2,0),"IUI",6,"Player 2","",
                0,"N",self.doChgTab,mem,None,("efld",)),
            (("T",0,2,0),"OUA",20,"")]
        if self.quant > 2:
            fld.extend([
                (("T",0,3,0),"IUI",6,"Player 3","",
                    0,"N",self.doChgTab,mem,None,("efld",)),
                (("T",0,3,0),"OUA",20,"")])
        if self.quant > 3:
            fld.extend([
                (("T",0,4,0),"IUI",6,"Player 4","",
                    0,"N",self.doChgTab,mem,None,("efld",)),
                (("T",0,4,0),"OUA",20,"")])
        but = (("Replace Tab with New Tab",None,self.doRepTab,1,None,None,
            "This will Remove the Existing Tab and Replace it with a New "\
            "Uncaptured Tab."),)
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doChgEnd,"n"),), txit=(self.doChgExit,),
            butt=but, focus=False)
        self.cg.loadEntry("T", 0, 0, data=self.cdraw[0])
        for n, d in enumerate(self.cdraw[1:]):
            self.cg.loadEntry("T", 0, 1 + (2 * n), data=d)
            nam = self.doGetTabs(d)
            self.cg.loadEntry("T", 0, 2 + (2 * n), data=nam)
        self.cg.focusField("T", 0, 1, clr=False)
        self.cg.mstFrame.wait_window()

    def doRepTab(self):
        self.oldtab = self.cg.getEntry("T", 0, self.cg.pos, False)
        oldnam = self.cg.getEntry("T", 0, self.cg.pos + 1, False)
        if not self.oldtab:
            return
        self.oldtab = int(self.oldtab)
        state = self.cg.disableButtonsTags()
        self.cg.setWidget(self.cg.mstFrame, state="hide")
        tit = ("Replace Tab",)
        mem = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname","Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_pos1", "", 0, "P"),
                ("btb_rate1", "", 0, "RP")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname, btb_names"}
        fld = (
            (("T",0,0,0),"OUI",6,"Old Tab"),
            (("T",0,0,0),"OUA",20,""),
            (("T",0,1,0),"IUI",6,"New Tab","",
                0,"N",self.doNewTab,mem,None,("notzero",)),
            (("T",0,1,0),"OUA",20,""))
        self.nt = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRepEnd,"y"),), txit=(self.doRepExit,))
        self.nt.loadEntry("T", 0, 0, data=self.oldtab)
        self.nt.loadEntry("T", 0, 1, data=oldnam)
        self.nt.mstFrame.wait_window()
        self.cg.setWidget(self.cg.mstFrame, state="show")
        self.cg.enableButtonsTags(state=state)
        self.cg.focusField("T", 0, self.cg.col, clr=False)

    def doNewTab(self, frt, pag, r, c, p, i, w):
        if w in self.alltabs:
            return "Invalid Tab, Already Entered"
        self.newtab = self.sql.getRec("bwltab", where=[("btb_cono", "=",
            self.opts["conum"]), ("btb_tab", "=", w)], limit=1)
        if not self.newtab:
            return "Invalid Tab Number"
        a = self.newtab[self.sql.bwltab_col.index("btb_surname")]
        b = self.newtab[self.sql.bwltab_col.index("btb_names")]
        self.nam = a.upper()
        if b:
            self.nam = "%s, %s" % (self.nam, b[0].upper())
        self.nt.loadEntry(frt, pag, p+1, data=self.nam)

    def doRepEnd(self):
        old = self.alltabs[self.oldtab]
        del self.alltabs[self.oldtab]
        tab = self.newtab[self.sql.bwltab_col.index("btb_tab")]
        a = self.newtab[self.sql.bwltab_col.index("btb_surname")]
        b = self.newtab[self.sql.bwltab_col.index("btb_names")]
        c = self.newtab[self.sql.bwltab_col.index("btb_gender")]
        d = self.newtab[self.sql.bwltab_col.index("btb_pos1")]
        e = self.newtab[self.sql.bwltab_col.index("btb_rate1")]
        self.alltabs[tab] = [a, b, c, d, e, "Y"]
        self.reptabs.append((self.oldtab, old, tab))
        self.cg.loadEntry("T", 0, self.cg.pos, data=tab)
        self.cg.loadEntry("T", 0, self.cg.pos + 1, data=self.nam)
        fini = False
        for x, d in enumerate(self.games1):
            for y, t in enumerate(d[2:]):
                if t[0] == self.oldtab:
                    self.games1[x][2+y][0] = tab
                    self.games1[x][2+y][1] = self.nam
                    self.games1[x][2+y][2] = e
                    fini = True
                    break
            if fini:
                break
        self.nt.closeProcess()

    def doRepExit(self):
        self.cg.loadEntry("T", 0, self.cg.pos, data=self.oldtab)
        self.nt.closeProcess()

    def doChgTab(self, frt, pag, r, c, p, i, w):
        if w and w not in self.alltabs:
            if p < 9:
                tab = self.games1[self.seq][2+(p//2)][0]
            else:
                tab = self.games1[self.seq+1][2+((p-8)//2)][0]
            self.cg.loadEntry(frt, pag, p, data=tab)
            return "Invalid Tab (%s), Not Entered" % w
        if not w:
            nam = ""
        else:
            nam = self.doGetName(w)
        self.cg.loadEntry(frt, pag, p + 1, data=nam)

    def doChgEnd(self):
        q = 0
        a = 0
        z = 0
        for x in range(1, 17, 2):
            if x == 9:
                z = 1
            if z == 1:
                y = int((x - 8) / 2) + 2
            else:
                y = int(x / 2) + 2
            tab = self.cg.t_work[0][0][x]
            if not tab:
                self.games1[self.seq + z][y] = [0, "", 0]
            else:
                fini = False
                for d in self.games:
                    for t in d[2:]:
                        if t[0] == self.cg.t_work[0][0][x]:
                            self.games1[self.seq + z][y] = copyList(t)
                            q += 1
                            a += t[2]
                            fini = True
                            break
                    if fini:
                        break
        for x in range(0, len(self.games1), 2):
            self.doAverage(self.games1[x], self.games1[x + 1])
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def doExit(self):
        if self.alltabs and not self.drawn:
            but = [
                ("Exit Without Saving", "E"),
                ("Save and Exit", "S"),
                ("Neither", "N")]
            txt = "This Draw Has Not Been Done"
            ok = askChoice(self.opts["mf"].body, "Exit",
                mess=txt, butt=but, default="None")
            if ok == "N":
                self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                return
            if ok == "S":
                self.dhist = "N"
                self.quant = 0
                self.doSave()
                for tab in self.alltabs:
                    data = [self.opts["conum"], tab, self.date, self.time,
                        "", "", "", 0, 0, 0, 0, 0, 0, 0, 0, "", ""]
                    self.sql.insRec("bwlsdt", data=data)
                self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.doSetFont(self.dfs)
        self.opts["mf"].closeLoop()

    def doSetFont(self, size=24):
        self.opts["mf"].rcdic["dfs"] = size
        self.opts["mf"].setThemeFont(butt=False)
        self.opts["mf"].resizeChildren()

    def doTestDraw(self):
        # Reload an existing draw for testing purposes
        titl = "Select Draw to Load"
        cols = (
            ("date", "Date", 10, "D1", "N"),
            ("time", "T", 1, "UA", "N"),
            ("qty", "Qty", 3, "UI", "N"))
        data = self.sql.getRec("bwlsdt", cols=["bst_date", "bst_time",
            "count(*)"], group="bst_date, bst_time", order="bst_date, bst_time")
        sel = SelectChoice(self.opts["mf"].window, titl, cols, data)
        if not sel.selection:
            return
        self.teams = {}
        self.bounce = {}
        self.alltabs = {}
        tabs = self.sql.getRec("bwlsdt", cols=["bst_tab"],
            where=[("bst_cono", "=", self.opts["conum"]), ("bst_date",
            "=", sel.selection[1]), ("bst_time", "=", sel.selection[2])])
        for tab in tabs:
            self.doLoadTab(tab[0], "T", err=False)
            self.df.loadEntry("T", 1, 3, data="Y")
            self.alltabs[tab[0]] = self.df.t_work[1][0][1:]
        self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)

    def doTestTabs(self, qty):
        # Load a random selection of tabs for testing purposes
        tabs = []
        self.teams = {}
        self.bounce = {}
        self.alltabs = {}
        recs = self.sql.getRec("bwltab", cols=["btb_tab"],
            where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "<", self.nstart)], group="btb_tab")
        if len(recs) < qty:
            qty = len(recs)
        for rec in recs:
            tabs.append(rec[0])
        random.shuffle(tabs)
        while len(self.alltabs) < qty:
            tab = tabs.pop()
            if self.doLoadTab(tab, "T", err=False):
                self.df.loadEntry("T", 1, 3, data="Y")
                self.alltabs[tab] = self.df.t_work[1][0][1:]
        self.drawn = False
        self.doShowQuantity()
        self.df.clearFrame("T", 1)

    def doShowQuantity(self):
        self.df.loadEntry("T", 0, 0, data=len(self.alltabs))

    def doGetName(self, tab):
        nam = "%s, %s" % (self.alltabs[tab][0], self.alltabs[tab][1][0])
        nam = nam.replace("VAN DER", "V D")
        nam = nam.replace("JANSE VAN", "J V")
        return nam


if __name__ == "__main__":
    import getopt, sys
    from TartanClasses import MainFrame, Dbase
    from tartanFunctions import loadRcFile
    opts, args = getopt.getopt(sys.argv[1:], "r:", [])
    rcf = None
    for o, v in opts:
        if o == "-r":
            rcf = v
    rcdic = loadRcFile(rcf)
    mf = MainFrame(rcdic=rcdic)
    mf.dbm = Dbase(rcdic=rcdic)
    mf.dbm.openDbase()
    imp = bc2080(**{"mf": mf, "conum": 1})
    mf.dbm.closeDbase()
    mf.window.destroy()
# vim:set ts=4 sw=4 sts=4 expandtab:
