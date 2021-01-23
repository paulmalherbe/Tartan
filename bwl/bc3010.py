"""
SYNOPSIS
    Bowls Random Tabs Draw Re-Print.

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

import time
from TartanClasses import CCD, PrintDraw, Sql, TartanDialog

class bc3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwldrm", "bwldrt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdt = ((t[0] * 10000) + (t[1] * 100) + t[2])
        return True

    def mainProcess(self):
        dte = {
            "stype": "R",
            "tables": ("bwldrm",),
            "cols": (
                ("bdm_date", "", 0, ""),
                ("bdm_time", "", 0, ""),
                ("bdm_mixed", "", 0, ""),
                ("bdm_rating", "", 0, ""),
                ("bdm_dbase", "", 0, ""),
                ("bdm_tsize", "", 0, "")),
            "where": [("bdm_cono", "=", self.opts["conum"])],
            "order": "bdm_date, bdm_time desc"}

        r1s = (("Morning", "M"), ("Afternoon", "A"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Position", "P"), ("Rating", "R"), ("Combination", "C"))
        fld = (
            (("T",0,0,0),"ID1",10,"Date","",
                self.sysdt,"Y",self.doDate,dte,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Time","",
                "A","N",self.doTime,None,None,None),
            (("T",0,2,0),("ORB",r2s),0,"Mixed Gender"),
            (("T",0,3,0),("ORB",r2s),0,"Mixed Rating"),
            (("T",0,4,0),("ORB",r3s),0,"Draw By"),
            (("T",0,5,0),("IRB",r2s),0,"Cash Takings Sheet","",
                "N","Y",self.doTakings,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"Tabs Draw Listing","",
                "N","Y",self.doListing,None,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Tabs Draw Board","",
                "Y","Y",self.doBoard,None,None,None),
            (("T",0,8,0),("IRB",r2s),0,"Include Empty Rinks","",
                "N","Y",self.doEmpty,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.dated = CCD(w, "D1", 10).disp

    def doTime(self, frt, pag, r, c, p, i, w):
        self.time = w
        if self.time == "A":
            self.timed = "Afternoon"
        else:
            self.timed = "Morning"
        chk = self.sql.getRec("bwldrm", cols=["bdm_mixed",
            "bdm_rating", "bdm_dbase"], where=[("bdm_cono", "=",
            self.opts["conum"]), ("bdm_date", "=", self.date),
            ("bdm_time", "=", self.time)], limit=1)
        if not chk:
            return "A Draw for this Date and Time Does Not Exist"
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        self.df.loadEntry(frt, pag, p+2, data=chk[1])
        self.df.loadEntry(frt, pag, p+3, data=chk[2])

    def doTakings(self, frt, pag, r, c, p, i, w):
        self.takings = w

    def doListing(self, frt, pag, r, c, p, i, w):
        self.listing = w

    def doBoard(self, frt, pag, r, c, p, i, w):
        self.board = w
        if self.board == "N":
            if (self.takings, self.listing) == ("N", "N"):
                return "xt"
            self.empty = "N"
            return "sk1"

    def doEmpty(self, frt, pag, r, c, p, i, w):
        self.empty = w

    def doEnd(self):
        self.df.closeProcess()
        PrintDraw(self.opts["mf"], self.opts["conum"], self.date, self.time,
            takings=self.takings, listing=self.listing, board=self.board,
            empty=self.empty, repprt=self.df.repprt)
        self.printed = True
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
