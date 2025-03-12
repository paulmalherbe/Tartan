"""
SYNOPSIS
    District Competition Draw.

    Formulas for Single Elimination Tournaments:

    N = Total number of entries.
    P = The power of 2 to equal or exceed N.
    X = The number of times 2 was raised to get P.

    Number of games             = N - 1
    Number of Byes              = P - N
    Number of Rounds            = X
    Number of First Round Games = N - (P / 2)

    Formulas for Round Robin Tournaments:

    N = Number of entries.

    Number of games             = (N x (N - 1)) / 2

    Status Flags:   0 = No Draw done
                    1 = Main Draw done without Results
                    2 = Main Draw done with Results
                    3 = Main Draw Completed
                    4 = Playoff Draw without Results
                    5 = Playoff Draw with Results
                    6 = Match Complete

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

import copy, os, random, time
from TartanClasses import ASD, CCD, MyFpdf, TartanDialog, Sql
from tartanFunctions import askChoice, askQuestion, doDrawTable, doPrinter
from tartanFunctions import getModName, copyList, showError

class sc2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["scpclb", "scpcmp", "scpent",
            "scpgme", "scpmem", "scprnd", "scpsec"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.today = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.sysdt = time.strftime("%d %B %Y %H:%M:%S", t)
        self.sysdw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.codes = ["A","B","C","D","E","F","G","H","I","J","K","L"]
        self.byenum = 900000
        random.seed()
        return True

    def mainProcess(self):
        cpt = {
            "stype": "R",
            "tables": ("scpcmp",),
            "cols": (
                ("scp_ccod", "", 0, "Cod"),
                ("scp_name", "", 0, "Name", "Y")),
            "where": [("scp_cono", "=", self.opts["conum"])]}
        r1s = (("Main","M"), ("Play-Offs","P"))
        r2s = (("Yes","Y"), ("No", "N"))
        r3s = (("Single","S"), ("Multiple", "M"))
        fld = [
            [("T",0,0,0),"I@scp_ccod",0,"","",
                "","N",self.doCmpCod,cpt,None,None],
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "M","N",self.doCmpTyp,None,None,None),
            (("T",0,2,0),"OUI",3,"Number of Entries"),
            (("T",0,3,0),"IUI",2,"Entries per Section","",
                0,"N",self.doNumEnt,None,None,("efld",)),
            (("T",0,4,0),"IUI",2,"Number of Sections","",
                0,"N",self.doNumSec,None,None,("notzero",)),
            (("T",0,5,0),("IRB",r2s),0,"Sub-Sections","",
                "N","N",self.doSubSec,None,None,None),
            (("T",0,6,0),("IRB",r3s),0,"Possible Qualifiers","",
                "S","N",self.doQuaSec,None,None,None),
            (("T",0,7,0),("IRB",r2s),0,"Closed-Up","",
                "Y","N",self.doClosed,None,None,None)]
        if "test"in self.opts:
            fld[0][5] = self.opts["test"]
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        scpcmp = self.sql.getRec("scpcmp", where=[("scp_cono", "=",
            self.opts["conum"]), ("scp_ccod", "=", w)], limit=1)
        if not scpcmp:
            return "Invalid Competition Code"
        self.ccod = w
        self.cdes = scpcmp[self.sql.scpcmp_col.index("scp_name")]
        self.tsiz = scpcmp[self.sql.scpcmp_col.index("scp_tsiz")]
        self.fmat = scpcmp[self.sql.scpcmp_col.index("scp_fmat")]
        self.logo = scpcmp[self.sql.scpcmp_col.index("scp_logo")]
        self.numsec = scpcmp[self.sql.scpcmp_col.index("scp_nsec")]
        self.entsec = scpcmp[self.sql.scpcmp_col.index("scp_nent")]
        self.subsec = scpcmp[self.sql.scpcmp_col.index("scp_subs")]
        self.quasec = scpcmp[self.sql.scpcmp_col.index("scp_qual")]
        self.clup = scpcmp[self.sql.scpcmp_col.index("scp_clup")]
        self.state = scpcmp[self.sql.scpcmp_col.index("scp_state")]
        self.prnds = scpcmp[self.sql.scpcmp_col.index("scp_prnds")]
        self.df.loadEntry(frt, pag, p+1, data=self.cdes)
        if self.state > 2:
            self.df.loadEntry(frt, pag, p+2, data="P")

    def doCmpTyp(self, frt, pag, r, c, p, i, w):
        self.ctyp = w
        if self.clup == "Y" and self.ctyp == "M" and self.state > 1:
            showError(self.opts["mf"].body, "Error",
                "This Closed-Up Competition is Already Underway")
            return "rf"
        if self.ctyp == "P":
            if self.numsec < 3:
                return "No Playoff Grid Available (Less than 3 Sections)"
            if self.state <= 2:
                showError(self.opts["mf"].window, "Invalid Type",
                    "Main not Completed or All results Not yet Entered")
                return "Main Not Completed"
        self.gwhr = [
            ("scg_cono", "=", self.opts["conum"]),
            ("scg_ccod", "=", self.ccod),
            ("scg_ctyp", "=", self.ctyp)]
        if self.state == 3 and self.quasec == "M" and self.numsec > 2:
            # Playoff records for 1st round of ctyp="P" and no "P" records
            chk = self.sql.getRec("scpgme", cols=["count(*)"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1)],
                limit=1)[0]
            if not chk:
                tot = 0
                data = [self.opts["conum"], self.ccod, "P", 1, "", 1, "M", 0,
                    0, "", 0, 0, 0, 0, 0, 0]
                self.doGetNewWin()
                for sec in self.newwin:
                    tot += 1
                    data[7] = self.newwin[sec]
                    self.sql.insRec("scpgme", data=data)
                self.seeds = []
                self.where = copyList(self.gwhr[:2])
                self.append(("scg_ctyp", "=", "P"))
                self.where.append(("scg_snum", "=", 1))
                self.createKnockout("P", 1, "", self.numsec)
                self.state = 5
                self.sql.updRec("scpcmp", cols=["scp_state"],
                    data=[self.state], where=[("scp_cono", "=",
                    self.opts["conum"]), ("scp_ccod", "=", self.ccod)])
                self.opts["mf"].dbm.commitDbase()
        self.getTotalSkips()
        self.df.loadEntry(frt, pag, p+1, data=self.totskp)
        self.redraw = False
        self.reprint = False
        if self.state:
            but = [("Exit", "E")]
            dflt = "Exit"
            if self.state:
                but.append(("Reprint", "R"))
                dflt = "Reprint"
            if self.ctyp == "M" and self.state == 1:
                but.append(("Redraw", "D"))
            if self.state == 1:
                txt = "This Draw Has Already Been Done."
            elif self.state == 6:
                txt = "This Competition has been Completed."
            else:
                txt = "This Competition is Underway."
            ok = askChoice(self.opts["mf"].body, "Drawn", txt,
                butt=but, default=dflt)
            if ok == "E":
                return "rf"
            elif ok == "R":
                self.reprint = True
            else:
                self.redraw = True
        if self.reprint or self.ctyp == "P":
            self.df.loadEntry(frt, pag, p+2, data=self.entsec)
            self.df.loadEntry(frt, pag, p+3, data=self.numsec)
            self.df.loadEntry(frt, pag, p+4, data=self.subsec)
            self.df.loadEntry(frt, pag, p+5, data=self.quasec)
            self.df.loadEntry(frt, pag, p+6, data=self.clup)
            return "sk6"

    def doGetNewWin(self, sect=None):
        # Get Leaders
        self.newwin = {}
        if sect is None:
            secs = []
            for x in range(self.numsec):
                secs.append(x + 1)
        else:
            secs = [sect]
        for sec in secs:
            col = [
                "scg_scod",
                "sum(scg_pnts) as a",
                "sum(scg_sfor - scg_sagt) as b",
                "round(sum(scg_sfor) / sum(scg_sagt), 2) as c"]
            whr = [
                ("scg_cono", "=", self.opts["conum"]),
                ("scg_ccod", "=", self.ccod),
                ("scg_ctyp", "=", "M"),
                ("scg_snum", "=", sec)]
            grp = "scg_scod"
            odr = "a desc, b desc, c desc"
            rec = self.sql.getRec("scpgme", cols=col, where=whr, group=grp,
                order=odr, limit=1)
            self.newwin[sec] = rec[0]

    def doNumEnt(self, frt, pag, r, c, p, i, w):
        if w:
            self.entsec = w
            self.numsec = int(self.totskp / self.entsec)
            if self.totskp % self.entsec:
                self.numsec += 1
            self.df.loadEntry(frt, pag, p+1, data=self.numsec)

    def doNumSec(self, frt, pag, r, c, p, i, w):
        self.numsec = w                         # Number of sections
        self.entsec = int(self.totskp / w)      # Entries per section
        if self.totskp % self.numsec:
            self.entsec += 1
        if self.entsec % 2:
            self.entsec += 1
        self.df.loadEntry(frt, pag, p-1, data=self.entsec)
        if self.numsec > 64:
            return "ff5|Too Many Sections (>64)"
        if self.fmat == "R":
            if self.entsec not in (4, 6, 8):
                return "ff5|Entries/Section Must be 4, 6 or 8"
            if ((self.numsec * self.entsec) - self.totskp) > self.numsec:
                return "ff5|Number of Byes Exceeds the Number of Sections"
        else:
            if self.entsec < 3:
                return "ff5|Too Few Entries/Section (<3)"
            if self.entsec > 32:
                return "ff5|There are Too Many Entries/Section (>32)"
        if self.fmat == "K":
            self.subsec = "N"
            self.quasec = "S"
            self.df.loadEntry(frt, pag, p+1, data=self.subsec)
            self.df.loadEntry(frt, pag, p+2, data=self.quasec)
            if self.entsec > 16:
                self.clup = "N"
                self.df.loadEntry(frt, pag, p+2, data=self.clup)
                return "sk3"
            else:
                return "sk2"
        if self.entsec > 6:
            self.subsec = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.subsec)
            return "sk1"

    def doSubSec(self, frt, pag, r, c, p, i, w):
        if w == "Y" and self.numsec != 2 and (self.numsec % 2):
            return "ff5|Uneven Number of Sections"
        self.subsec = w
        if self.subsec == "Y":
            self.quasec = "S"
            self.clup = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.quasec)
            self.df.loadEntry(frt, pag, p+2, data=self.clup)
            return "sk2"

    def doQuaSec(self, frt, pag, r, c, p, i, w):
        self.quasec = w
        self.clup = "N"
        self.df.loadEntry(frt, pag, p+1, data=self.clup)
        return "sk1"

    def doClosed(self, frt, pag, r, c, p, i, w):
        self.clup = w
        if self.clup == "Y":
            if self.entsec < 6:
                return "ff5|There are Too Few Entries/Section (<6)"
            if self.entsec > 16:
                return "ff5|There are Too Many Entries/Section (>16)"

    def doEnd(self):
        self.df.closeProcess()
        self.playoff = False
        self.quit = False
        self.populateGames()
        if not self.quit:
            self.doEnder()
        self.opts["mf"].closeLoop()

    def getTotalSkips(self):
        if self.ctyp == "M":
            self.totskp = self.sql.getRec("scpent", cols=["count(*)"],
                where=[("sce_cono", "=", self.opts["conum"]), ("sce_ccod", "=",
                self.ccod)], limit=1)[0]
        else:
            self.totskp = self.sql.getRec("scpgme", cols=["count(*)"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1)],
                limit=1)[0] * 2

    def populateGames(self):
        # Calculate Number of Rounds
        if self.ctyp == "P":
            self.rnds = self.prnds
        elif self.fmat == "K":
            self.rnds = self.getRounds(self.entsec)
        else:
            self.rnds = self.entsec - 1
        if self.numsec == 1:
            self.xtra = self.rnds
        else:
            self.xtra = self.rnds + self.getRounds(self.numsec)
        if self.reprint or self.ctyp == "P":
            return
        # Update scpcmp
        self.sql.updRec("scpcmp", cols=["scp_nsec", "scp_nent", "scp_subs",
            "scp_qual", "scp_clup", "scp_mrnds", "scp_prnds"],
            data=[self.numsec, self.entsec, self.subsec, self.quasec,
            self.clup, self.rnds, self.xtra - self.rnds], where=[("scp_cono",
            "=", self.opts["conum"]), ("scp_ccod", "=", self.ccod)])
        # If Re-Draw, clear tables
        if self.redraw:
            self.sql.delRec("scpgme", where=[("scg_cono", "=",
                self.opts["conum"]), ("scg_ccod", "=", self.ccod)])
            self.sql.delRec("scprnd", where=[("scr_cono", "=",
                self.opts["conum"]), ("scr_ccod", "=", self.ccod)])
            self.sql.delRec("scpsec", where=[("scs_cono", "=",
                self.opts["conum"]), ("scs_ccod", "=", self.ccod)])
        if self.clup == "Y":
            self.seeds = []
        else:
            # Get Seeds
            self.doSeeds()
            if self.quit:
                self.doExit()
                return
        # Enter Competition and Section Details
        self.doMatchDetails()
        if not self.quit:
            if self.subsec == "Y":
                for x in range(0, self.numsec, 2):
                    self.rsecnum = int(x / 2) + 1
                    if self.rsecnum == 1:
                        self.rnum = self.xtra
                    else:
                        self.rnum = self.rnds + 1
                    self.doSectionDetails()
                    if self.quit:
                        break
            else:
                for x in range(self.numsec):
                    self.rsecnum = x + 1
                    if self.rsecnum == 1:
                        self.rnum = self.xtra
                    else:
                        self.rnum = self.rnds
                    self.doSectionDetails()
                    if self.quit:
                        break
        if self.quit:
            self.doExit()
            return
        # Create Section Dictionaries
        sections = {}
        secqty = {}
        sectot = {}
        if self.totskp % self.numsec:
            add = True
            byes = self.numsec - (self.totskp % self.numsec)
        else:
            add = False
            byes = 0
        bent = int(self.totskp / self.numsec)
        for x in range(self.numsec):
            sections[x + 1] = []
            sectot[x + 1] = 0
            if byes:
                secqty[x + 1] = [bent, 0]
                byes -= 1
            elif add:
                secqty[x + 1] = [bent + 1, 0]
            else:
                secqty[x + 1] = [bent, 0]
        # Create Club Dictionaries by Section
        clbqty = {}
        clubs = self.sql.getRec(tables=["scpent", "scpmem"], cols=["scm_club",
            "count(*) as count"], where=[("sce_cono", "=", self.opts["conum"]),
            ("sce_ccod", "=", self.ccod), ("scm_cono=sce_cono",),
            ("scm_scod=sce_scod",)], group="scm_club", order="count desc")
        for club in clubs:
            clbqty[club[0]] = {}
            for sec in sections:
                clbqty[club[0]][sec] = 0
            qty = club[1]
            while qty:
                for sec in sections:
                    if sectot[sec] == secqty[sec][0]:
                        continue
                    sectot[sec] += 1
                    clbqty[club[0]][sec] += 1
                    qty -= 1
                    if not qty:
                        break
        # Allocate Seeds to Sections
        seeds = copyList(self.seeds)
        if seeds:
            for sec in sections:
                seed = seeds.pop(0)
                club = self.sql.getRec("scpmem", cols=["scm_club"],
                    where=[("scm_cono", "=", self.opts["conum"]), ("scm_scod",
                    "=", seed)], limit=1)
                sections[sec] = [seed]
                secqty[sec][1] += 1
                clbqty[club[0]][sec] -= 1
                if not seeds:
                    break
        # Allocate Rest of Entries to Sections
        clubs = self.sql.getRec(tables=["scpent", "scpmem"], cols=["scm_club",
            "count(*) as count"], where=[("sce_cono", "=", self.opts["conum"]),
            ("sce_ccod", "=", self.ccod), ("scm_cono=sce_cono",),
            ("scm_scod=sce_scod",)], group="scm_club", order="count desc")
        for club in clubs:
            skips = self.sql.getRec(tables=["scpent", "scpmem"],
                cols=["sce_scod"], where=[("sce_cono", "=",
                self.opts["conum"]), ("sce_ccod", "=", self.ccod),
                ("scm_cono=sce_cono",), ("scm_scod=sce_scod",), ("scm_club",
                "=", club[0])])
            random.shuffle(skips)
            while skips:
                skip = skips.pop(0)
                if skip[0] not in self.seeds:
                    for sec in sections:
                        if secqty[sec][1] == secqty[sec][0]:
                            continue
                        if not clbqty[club[0]][sec]:
                            continue
                        sections[sec].append(skip[0])
                        secqty[sec][1] += 1
                        clbqty[club[0]][sec] -= 1
                        break
        # Create Game Records (scpgme) and Split into Sub-Sections
        for sec in sections:
            if self.subsec == "Y":
                snum = int(sec / 2)
                if sec % 2:
                    snum += 1
                    ssec = "A"
                else:
                    ssec = "B"
            else:
                snum = sec
                ssec = ""
            data = [self.opts["conum"], self.ccod, "M", snum, ssec, 1, "M", 0,
                0, "", 0, 0, 0, 0, 0, 0]
            for plr in sections[sec]:
                data[7] = plr
                self.sql.insRec("scpgme", data=data)

    def getRounds(self, entsec):
        pwrs = 2
        rnds = 1
        while pwrs < entsec:
            rnds += 1
            pwrs = pwrs * 2
        return rnds

    def doSeeds(self):
        tit = ("Seeded Players",)
        skp = {
            "stype": "R",
            "tables": ("scpent", "scpmem"),
            "cols": (
                ("scm_scod", "", 0, "S-Code"),
                ("scm_surname", "", 0, "Surname","Y"),
                ("scm_names", "", 0, "Names")),
            "where": [
                ("sce_cono", "=", self.opts["conum"]),
                ("sce_ccod", "=", self.ccod),
                ("scm_cono=sce_cono",),
                ("scm_scod=sce_scod",)],
            "order": "scm_surname, scm_names"}
        fld = (
            (("T",0,0,0),"IUI",2,"Number of Seeds","",
                0,"N",self.doSeedNum,None,None,("efld",)),
            (("T",0,1,0),"IUI",6,"1st Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,1,0),"OUA",20,""),
            (("T",0,2,0),"IUI",6,"2nd Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,2,0),"OUA",20,""),
            (("T",0,3,0),"IUI",6,"3rd Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,3,0),"OUA",20,""),
            (("T",0,4,0),"IUI",6,"4th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,4,0),"OUA",20,""),
            (("T",0,5,0),"IUI",6,"5th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,5,0),"OUA",20,""),
            (("T",0,6,0),"IUI",6,"6th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,6,0),"OUA",20,""),
            (("T",0,7,0),"IUI",6,"7th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,7,0),"OUA",20,""),
            (("T",0,8,0),"IUI",6,"8th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,8,0),"OUA",20,""),
            (("T",0,9,0),"IUI",6,"9th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,9,0),"OUA",20,""),
            (("T",0,10,0),"IUI",6,"10th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,10,0),"OUA",20,""),
            (("T",0,11,0),"IUI",6,"11th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,11,0),"OUA",20,""),
            (("T",0,12,0),"IUI",6,"12th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,12,0),"OUA",20,""),
            (("T",0,13,0),"IUI",6,"13th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,13,0),"OUA",20,""),
            (("T",0,14,0),"IUI",6,"14th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,14,0),"OUA",20,""),
            (("T",0,15,0),"IUI",6,"15th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,15,0),"OUA",20,""),
            (("T",0,16,0),"IUI",6,"16th Seed","",
                0,"N",self.doSeedTab,skp,None,("efld",)),
            (("T",0,16,0),"OUA",20,""))
        but = (("Quit",None,self.doSeedsQuit,1,None,None),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.sp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doSeedEnd,"y"),))
        self.sp.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doSeedNum(self, frt, pag, r, c, p, i, w):
        if w > 16 or w > self.numsec:
            return "Invalid Number of Seeds"
        self.seednum = w
        if not w:
            return "nd"

    def doSeedTab(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec(tables=["scpent", "scpmem"], cols=["scm_surname",
            "scm_names"], where=[("sce_cono", "=", self.opts["conum"]),
            ("sce_ccod", "=", self.ccod), ("sce_scod", "=", w),
            ("scm_cono=sce_cono",), ("scm_scod=sce_scod",)], limit=1)
        if not chk:
            return "Not a Valid Entered Member"
        seeds = []
        for x in range(self.seednum):
            if ((x * 2) + 1) == p:
                continue
            if self.sp.t_work[0][0][(x * 2) + 1]:
                seeds.append(self.sp.t_work[0][0][(x * 2) + 1])
        if w in seeds:
            return "Invalid Seed, Already Seeded"
        nam = chk[0] + ", " + chk[1][0]
        self.sp.loadEntry(frt, pag, p+1, data=nam)
        if int((p + 1) / 2) == self.seednum:
            return "nd"

    def doSeedEnd(self):
        self.quit = False
        self.sp.closeProcess()
        self.seeds = []
        for x in range(self.seednum):
            self.seeds.append(self.sp.t_work[0][0][(x * 2) + 1])

    def doSeedsQuit(self):
        self.quit = True
        self.sp.closeProcess()

    def doMatchDetails(self):
        tit = ("Match Details",)
        fld = (
            (("C",0,0,0),"ID1",10,"Date","",
                0,"N",self.doMatchDate,None,None,("efld",),("Rnd", self.xtra)),
            (("C",0,0,1),"ITM",5,"Time","",
                1415,"N",self.doMatchTime,None,None,("efld",)))
        but = (("Quit",None,self.doMatchQuit,1,None,None),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.md = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, cend=((self.doMatchEnd,"n"),),
            cxit=(self.doMatchExit,))
        for x in range(self.xtra):
            self.md.colLabel[0][x].configure(text=self.getRndTxt(x + 1)[0])
        self.md.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doMatchDate(self, frt, pag, r, c, p, i, w):
        if w < self.today:
            return "Date in the Past"
        if i and w < self.md.t_work[0][0][i-1]:
            return "Date Before Previous Date"
        self.rdate = w

    def doMatchTime(self, frt, pag, r, c, p, i, w):
        self.rtime = w

    def doMatchEnd(self):
        if self.md.col < self.xtra * 2:
            self.md.advanceLine(0)
        else:
            self.md.closeProcess()
            for num, dat in enumerate(self.md.c_work[0]):
                self.sql.insRec("scprnd", data=[self.opts["conum"], self.ccod,
                    num+1, dat[0], dat[1]])
            self.quit = False

    def doMatchExit(self):
        if self.md.col != 1:
            self.md.focusField(self.md.frt, self.md.pag, self.md.col - 2)

    def doMatchQuit(self):
        self.quit = True
        self.md.closeProcess()

    def doSectionDetails(self):
        tit = ("Section %s Details" % self.rsecnum,)
        clb = {
            "stype": "R",
            "tables": ("scpclb",),
            "cols": (
                ("scc_club", "", 0, "Cod"),
                ("scc_name", "", 0, "Name", "Y"))}
        fld = (
            (("C",0,0,0),"IUI",3,"VCC","Venue Club Code",
                0,"N",self.doSecClub,clb,None,("efld",),("Rnd", self.rnum)),
            (("C",0,0,1),"ONA",30,"Venue Name"))
        but = (("Quit",None,self.doSecQuit,1,None,None),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.sd = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, cend=((self.doSecEnd,"n"),),
            cxit=(self.doSecExit,))
        for x in range(self.rnum):
            self.sd.colLabel[0][x].configure(text=self.getRndTxt(x + 1)[0])
        self.sd.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doSecClub(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("scpclb", where=[("scc_club", "=", w)],
            limit=1)
        if not chk:
            return "Invalid Club Code"
        self.rclub = w
        self.sd.loadEntry(frt, pag, p+1, data=chk[1])

    def doSecEnd(self):
        if self.sd.col < self.rnum * 2:
            self.sd.advanceLine(0)
        else:
            if self.rsecnum == 1:
                self.extra = []
                mrnds = self.rnds
                if self.subsec == "Y":
                    mrnds += 1
            for num, venue in enumerate(self.sd.c_work[0]):
                self.sql.insRec("scpsec", data=[self.opts["conum"], self.ccod,
                    self.rsecnum, num + 1, venue[0], venue[1]])
                if self.rsecnum == 1 and (num + 1) > mrnds:
                    self.extra.append(venue)
            if self.rsecnum > 1:
                for num, venue in enumerate(self.extra):
                    self.sql.insRec("scpsec", data=[self.opts["conum"],
                        self.ccod, self.rsecnum, self.rnum + num + 1, venue[0],
                        venue[1]])
            self.quit = False
            self.sd.closeProcess()

    def doSecExit(self):
        if self.sd.col != 1:
            self.sd.focusField(self.sd.frt, self.sd.pag, self.sd.col - 2)

    def doSecQuit(self):
        self.quit = True
        self.sd.closeProcess()

    def doEnder(self):
        if not self.reprint and self.ctyp == "M":
            if self.clup == "N":
                recs = self.sql.getRec("scpgme", cols=["scg_snum",
                    "scg_subs", "count(*)"], where=self.gwhr,
                    group="scg_snum, scg_subs", order="scg_snum, scg_subs")
                for sec, sub, tot in recs:
                    self.where = copyList(self.gwhr)
                    self.where.extend([("scg_snum","=",sec),
                        ("scg_subs","=",sub)])
                    if self.fmat == "K":
                        self.createKnockout(self.ctyp, sec, sub, tot)
                    else:
                        self.createRoundRobin(sec, sub)
                if self.fmat == "R":
                    self.allocateRinks()
            self.state = 1
            self.sql.updRec("scpcmp", cols=["scp_state"], data=[self.state],
                where=[("scp_cono", "=", self.opts["conum"]), ("scp_ccod",
                "=", self.ccod)])
        if self.fmat == "K" or self.ctyp == "P":
            if self.ctyp == "M" and self.clup == "Y":
                head = (4 * 26) + 25
            else:
                head = (self.rnds * 26) + 25
            self.fpdf = MyFpdf(name=self.__class__.__name__, head=head,
                font="Helvetica")
            self.fpdf.def_orientation = "P"
            self.fpdf.font[2] = 5
        else:
            self.fpdf = MyFpdf(name=self.__class__.__name__, head=65,
                font="Helvetica")
        recs = self.sql.getRec("scpgme", cols=["scg_snum", "scg_subs"],
            where=self.gwhr, group="scg_snum, scg_subs",
            order="scg_snum, scg_subs")
        for sec, sub in recs:
            self.where = copyList(self.gwhr)
            self.where.extend([
                ("scg_snum", "=", sec),
                ("scg_subs", "=", sub)])
            if self.fmat == "K" or self.ctyp == "P":
                self.printKnockout(sec, sub)
            else:
                self.printRoundRobin(sec, sub)
        if self.ctyp == "M" and self.numsec > 2 and \
                (self.quasec == "S" or self.state > 2):
            # Print sectional playoff sheet
            self.clup = "N"
            if self.state > 2:
                self.ctyp = "P"
                self.rnds = self.prnds
                self.gwhr = [
                    ("scg_cono", "=", self.opts["conum"]),
                    ("scg_ccod", "=", self.ccod),
                    ("scg_ctyp", "=", self.ctyp)]
                self.where = copyList(self.gwhr)
                self.where.extend([
                    ("scg_snum", "=", 1),
                    ("scg_subs", "=", "")])
                self.printKnockout(1, "")
            else:
                self.playoff = True
                self.printPlayOffs()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=1, pdfnam=pdfnam,
                repprt=self.df.repprt)
        if not self.reprint:
            if "test" in self.opts:
                self.opts["mf"].dbm.commitDbase()
            else:
                self.opts["mf"].dbm.commitDbase(ask=True)

    def createKnockout(self, ctyp, sec, sub, tot):
        pwrs = 2
        if ctyp == "P":
            if not tot % 2:
                entsec = tot
            else:
                entsec = tot + 1
            self.prnds = self.getRounds(entsec)
            self.sql.updRec("scpcmp", cols=["scp_prnds"], data=[self.prnds],
                where=[("scp_cono", "=", self.opts["conum"]), ("scp_ccod", "=",
                self.ccod)])
        else:
            entsec = self.entsec
        while pwrs < entsec:
            pwrs = pwrs * 2
        byes = pwrs - tot
        frg = tot - int(pwrs / 2)
        prs = int((frg + byes) / 4)
        grps = [0, 0]
        # Create shadow players for byes in groups
        data = [self.opts["conum"], self.ccod, ctyp, sec, sub, 1, "M",
            0, 0, "", 0, 0, 0, 0, 0, 0]
        for bye in range(byes):
            self.byenum += 1
            data[7] = self.byenum
            if bye % 2:
                grp = 1
            else:
                grp = 2
            data[13] = grp
            grps[grp-1] += 1
            self.sql.insRec("scpgme", data=data)
        # Create Lists of Skips and Seeds
        whr = copyList(self.where)
        whr.append(("scg_group", "=", 0))
        chk = self.sql.getRec("scpgme", cols=["scg_scod"], where=whr,
            order="scg_scod")
        skips = []
        sseed = []
        for c in chk:
            skips.append(c[0])
            if c[0] in self.seeds:
                sseed.append(c[0])
        random.shuffle(skips)
        # Allocate seeded players to groups
        sgrps = [[], []]
        whr = copyList(self.where)
        whr.extend([("scg_scod", ">", 900000), ("scg_group", "=", 0)])
        chk = self.sql.getRec("scpgme", cols=["scg_group"], where=whr,
            order="scg_group")
        if chk:
            grp = chk[0][0]
        else:
            grp = 2
        for num in range(0, len(sseed), 2):
            grps[grp-1] += 1
            sgrps[grp-1].append(sseed[num])
            whr = copyList(self.where)
            whr.append(("scg_scod", "=", sseed[num]))
            self.sql.updRec("scpgme", cols=["scg_group"], data=[grp],
                where=whr)
            if num == len(sseed) - 1:
                break
            if grp == 1:
                grp = 2
            else:
                grp = 1
            grps[grp-1] += 1
            sgrps[grp-1].append(sseed[num+1])
            whr = copyList(self.where)
            whr.append(("scg_scod", "=", sseed[num+1]))
            self.sql.updRec("scpgme", cols=["scg_group"], data=[grp],
                where=whr)
        # Allocate balance of players to groups
        whr = copyList(self.where)
        whr.append(("scg_group", "=", 0))
        chk = self.sql.getRec("scpgme", cols=["scg_scod"], where=whr,
            order="scg_scod")
        skips = []
        for c in chk:
            skips.append(c[0])
        random.shuffle(skips)
        for skip in skips:
            if grps[0] < grps[1]:
                grp = 1
            else:
                grp = 2
            grps[grp-1] += 1
            whr = copyList(self.where)
            whr.append(("scg_scod", "=", skip))
            self.sql.updRec("scpgme", cols=["scg_group"], data=[grp],
                where=whr)
        # Allocate opponents
        for grp in range(1, 3):
            # Allocate seeded players to byes
            for seed in sgrps[grp-1]:
                self.doAllocateBye(sec, sub, seed, grp)
            # Allocate balance of byes randomly
            whr = copyList(self.where)
            whr.extend([("scg_scod", "<", 900000), ("scg_ocod = 0",),
                ("scg_group", "=", grp)])
            chk = self.sql.getRec("scpgme", cols=["scg_scod"],
                where=whr)
            temp = []
            for c in chk:
                temp.append(c[0])
            random.shuffle(temp)
            for skip in temp:
                self.doAllocateBye(sec, sub, skip, grp)
            # Allocate opponents to balance of players randomly
            whr = copyList(self.where)
            whr.extend([("scg_ocod = 0",), ("scg_group", "=", grp)])
            chk = self.sql.getRec("scpgme", cols=["scg_scod"],
                where=whr)
            temp = []
            for c in chk:
                temp.append(c[0])
            random.shuffle(temp)
            for p1 in sseed:
                # Pair seeded player with unseeded player
                if p1 not in temp:
                    continue
                for rec in temp:
                    if rec not in sseed:
                        p2 = rec
                        break
                temp.remove(p1)
                temp.remove(p2)
                whr = copyList(self.where)
                whr.append(("scg_scod", "=", p1))
                self.sql.updRec("scpgme", cols=["scg_ocod"], data=[p2],
                    where=whr)
                whr = copyList(self.where)
                whr.append(("scg_scod", "=", p2))
                self.sql.delRec("scpgme", where=whr)
            while temp:
                p1 = temp.pop(0)
                p2 = temp.pop(0)
                whr = copyList(self.where)
                whr.append(("scg_scod", "=", p1))
                self.sql.updRec("scpgme", cols=["scg_ocod"], data=[p2],
                    where=whr)
                whr = copyList(self.where)
                whr.append(("scg_scod", "=", p2))
                self.sql.delRec("scpgme", where=whr)
            whr = copyList(self.where)
            whr.append(("scg_group", "=", grp))
            skips = self.sql.getRec("scpgme", cols=["scg_scod",
                "scg_ocod"], where=whr, order="scg_ocod")
            if prs:
                # Allocate seeds into pair groups
                if prs == 1:
                    p1 = [1]
                elif prs == 2:
                    p1 = [1, 2]
                elif prs == 4:
                    p1 = [1, 3, 4, 2]
                elif prs == 8:
                    p1 = [1, 5, 7, 3, 4, 8, 6, 2]
                tot = int(len(skips) / prs)
                p2 = [tot] * prs
                if len(skips) % prs:
                    p2[0] += 1
                for sd, seed in enumerate(self.seeds):
                    for skp in skips:
                        if skp[0] == seed:
                            pos = p1.pop(0)
                            whr = copyList(self.where)
                            whr.append(("scg_scod", "=", skp[0]))
                            self.sql.updRec("scpgme", cols=["scg_seed",
                                "scg_pair"], data=[sd+1, pos], where=whr)
                            p2[pos - 1] -= 1
                            break
                # Allocate byes into pair groups
                if byes == 1:
                    p1 = [1]
                elif byes == 2:
                    p1 = [1, 2]
                elif byes == 4:
                    p1 = [1, 3, 4, 2]
                elif byes == 8:
                    p1 = [1, 5, 7, 3, 4, 8, 6, 2]
                tot = int(len(skips) / prs)
                p2 = [tot] * prs
                if len(skips) % prs:
                    p2[0] += 1
                for sd, seed in enumerate(self.seeds):
                    for skp in skips:
                        if skp[0] == seed:
                            pos = p1.pop(0)
                            whr = copyList(self.where)
                            whr.append(("scg_scod", "=", skp[0]))
                            self.sql.updRec("scpgme", cols=["scg_seed",
                                "scg_pair"], data=[sd+1, pos], where=whr)
                            p2[pos - 1] -= 1
                            break
                # Allocate rest into pair groups
                for skp in skips:
                    if skp[0] in sseed:
                        continue
                    for n, p in enumerate(p2):
                        if p:
                            whr = copyList(self.where)
                            whr.append(("scg_scod", "=", skp[0]))
                            self.sql.updRec("scpgme", cols=["scg_seed",
                                "scg_pair"], data=[0, n+1], where=whr)
                            p2[n] -= 1
                            break

    def doAllocateBye(self, sec, sub, one, grp):
        whr = copyList(self.gwhr)
        whr.extend([
            ("scg_scod > 900000",), ("scg_snum", "=", sec),
            ("scg_subs", "=", sub), ("scg_rnum", "=", 1),
            ("scg_group", "=", grp), ("scg_ocod = 0",)])
        chk = self.sql.getRec("scpgme", cols=["scg_scod"],
            where=whr, order="scg_scod")
        if chk:
            whr = copyList(self.gwhr)
            whr.extend([
                ("scg_scod", "=", one), ("scg_snum", "=", sec),
                ("scg_subs", "=", sub), ("scg_rnum", "=", 1)])
            self.sql.updRec("scpgme", cols=["scg_ocod"], data=[chk[0][0]],
                where=whr)
            whr = copyList(self.gwhr)
            whr.extend([
                ("scg_scod", "=", chk[0][0]), ("scg_snum", "=", sec),
                ("scg_subs", "=", sub), ("scg_rnum", "=", 1)])
            self.sql.delRec("scpgme", where=whr)

    def printKnockout(self, sec, sub):
        cod = 0
        self.two = False
        self.printHeading(sec, sub, date=True)
        if self.clup == "Y" and self.ctyp == "M":
            self.second = [17, 18, 19, 20, 21, 22, 23, 24]
            self.third = [25, 26, 27, 28]
        for grp in range(1, 3):
            if self.clup == "Y" and self.ctyp == "M":
                skips = []
                p = 1
                for _ in range(2):
                    skips.append([(cod * 2) + 1, (cod * 2) + 2, 0, p])
                    cod += 1
                    skips.append([(cod * 2) + 1, (cod * 2) + 2, 0, p])
                    cod += 1
                    p += 1
            else:
                whr = copyList(self.where)
                whr.extend([
                    ("scg_rnum", "=", 1),
                    ("scg_group", "=", grp)])
                skips = self.sql.getRec("scpgme", cols=["scg_scod",
                    "scg_ocod", "scg_seed", "scg_pair"], where=whr,
                    order="scg_pair, scg_scod")
            self.printBracket(sec, sub, grp, skips)
        if self.clup == "Y" and self.ctyp == "M":
            whr = copyList(self.where)
            whr.extend([("scm_cono=scg_cono",), ("scm_scod=scg_scod",)])
            skips = self.sql.getRec(tables=["scpgme", "scpmem"],
                cols=["scg_scod", "scm_surname", "scm_names"], where=whr,
                order="scg_pair")
            if not self.reprint:
                random.shuffle(skips)
            self.printClosed(skips)

    def printBracket(self, sec, sub, grp, skips):
        cwth, chgt = self.setBracketFont()
        ohgt = self.fpdf.font[2]
        self.fpdf.font[2] = chgt
        if grp == 2 and self.rnds == 2:
            last = "down"
        else:
            last = ""
        rnds = []
        nm = 25
        l1 = 0
        l2 = 1
        n1 = nm + l1
        n2 = nm + l1 + l2
        nx = (nm * 2) + l1 + l2
        for skip in skips:
            # Print Round 1 and Round 2 if more than 2 Rounds
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] == "Bye" or (not self.playoff and skip[1] > 900000):
                self.fpdf.drawText("", w=(cwth * nm))
            else:
                txt, bdr = self.getSkip(skip[0], skip[2], 1)
                self.fpdf.drawText(txt, w=(cwth * nm), border=bdr)
                self.drawLink(cwth, l1, l2, x + (cwth * nm), y + int(chgt / 2),
                    y + (chgt * 1.5))
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] == "Bye" or (not self.playoff and skip[1] > 900000):
                txt, bdr = self.getSkip(skip[0], skip[2], 2)
                self.fpdf.drawText(txt, x + (cwth * n2), w=(cwth * nm),
                    border=bdr)
            else:
                if self.clup == "Y" and self.ctyp == "M":
                    txt, bdr = self.getSkip(self.second.pop(0), 0, 1)
                else:
                    txt, bdr = self.getGameWinner(skip[0], 0, 0, 0, 1, 0, 0)
                self.fpdf.drawText(txt, x + (cwth * n2), w=(cwth * nm),
                    border=bdr)
            if not last or last == "up":
                self.drawLink(cwth, l1, l2, x + (cwth * nx), y + int(chgt / 2),
                    y + (chgt * 2.5))
                rnds.append([x+(cwth*nx), y+(chgt*2)])
                last = "down"
            else:
                self.drawLink(cwth, l1, l2, x + (cwth * nx), y + int(chgt / 2),
                    y - (chgt * 1.5))
                if self.rnds == 2:
                    rnds.append([x + (cwth * nx), y + (chgt * 2)])
                last = "up"
            x = self.fpdf.get_x()
            y = self.fpdf.get_y()
            if skip[1] == "Bye" or (not self.playoff and skip[1] > 900000):
                self.fpdf.drawText("", w=(cwth*nm))
            else:
                txt, bdr = self.getSkip(skip[1], 0, 1)
                self.fpdf.drawText(txt, w=(cwth*nm), border=bdr)
                self.fpdf.line(x+(cwth*nm), y+int(chgt / 2), x+(cwth*n1),
                    y+int(chgt / 2))
                self.fpdf.line(x+(cwth*n1), y+int(chgt / 2), x+(cwth*n1),
                    y-int(chgt / 2))
            self.fpdf.drawText("")
            lasty = self.fpdf.get_y()
        inc = 4
        if self.ctyp == "M" and self.clup == "Y":
            prnd = 4
        else:
            prnd = self.rnds
        for aa in range(prnd - 3):
            # Print Rounds > 3 but Not the Last 2 Rounds
            bb = []
            cnt = 1
            for rnd in range(0, len(rnds), 2):
                x = rnds[rnd][0]
                y = rnds[rnd][1]
                if self.clup == "Y" and self.ctyp == "M":
                    txt, bdr = self.getSkip(self.third.pop(0), 0, 0)
                else:
                    txt, bdr = self.getGameWinner(
                        None, sec, sub, grp, aa + 3, cnt, 0)
                self.fpdf.drawText(txt, x+(cwth*(l1+l2)), y, w=(cwth*nm),
                    border=bdr)
                inc1 = inc + .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y +
                    int(chgt / 2), y + (chgt * inc1))
                bb.append([x + (cwth * n2), y + (chgt * (4 * (aa + 1)))])
                x = rnds[rnd + 1][0]
                y = rnds[rnd + 1][1]
                if self.clup == "Y" and self.ctyp == "M":
                    txt, bdr = self.getSkip(self.third.pop(0), 0, aa+1)
                else:
                    txt, bdr = self.getGameWinner(
                        None, sec, sub, grp, aa + 3, cnt, 1)
                self.fpdf.drawText(txt, x + (cwth * (l1 + l2)), y,
                    w=(cwth * nm), border=bdr)
                inc1 -= 1
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y +
                    int(chgt / 2), y - (chgt * inc1))
                cnt += 1
            inc = inc * 2
            rnds = bb
        x = rnds[0][0]
        y = rnds[0][1]
        rnd = 2
        if self.rnds == 2:
            # Last Round if Only 2 Rounds
            if grp == 1:
                txt, bdr = self.getGameWinner(
                    None, sec, sub, 1, 3, 1, grp - 1)
                self.fpdf.drawText(txt, x + (cwth * (l1 + l2)), y,
                    w=(cwth * nm), border=bdr)
        else:
            # Last Two Rounds
            if self.rnds > 5:
                y += (chgt*4)
            # Second Last Round
            txt, bdr = self.getGameWinner(
                None, sec, sub, 1, self.rnds, 1, grp - 1)
            self.fpdf.drawText(txt, x + (cwth * (l1 + l2)), y, w=(cwth * nm),
                    border=bdr)
            # Last Round
            if grp == 1:
                inc += .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                        y + (chgt * inc))
            else:
                x1 = x + (cwth * (l1 + l2 + nm))
                y1 = y - (chgt * inc)
                txt, bdr = self.getGameWinner(
                    None, sec, sub, 1, self.rnds + 1, 1, 0)
                if self.rnds < 6:
                    self.fpdf.drawText(txt, x1 + (cwth * (l1 + l2)), y1,
                            w=(cwth * nm), border=bdr)
                inc = 0 - inc + .5
                self.drawLink(cwth, l1, l2, x + (cwth * n2), y + int(chgt / 2),
                        y + (chgt * inc))
        if grp == 1 and len(skips) == 16:
            self.fpdf.add_page()
            self.fpdf.drawText()
            self.fpdf.drawText()
        else:
            self.fpdf.set_y(lasty)
        self.fpdf.font[2] = ohgt

    def getGameWinner(self, skp, sec, sub, grp, rnd, pair, pos):
        if not skp:
            whr = copyList(self.gwhr)
            whr.extend([
                ("scg_snum", "=", sec), ("scg_subs", "=", sub),
                ("scg_rnum", "=", rnd), ("scg_group", "=", grp),
                ("scg_pair", "=", pair)])
            skp = self.sql.getRec("scpgme", cols=["scg_scod",
                "scg_ocod"], where=whr, limit=1)
            if not skp:
                return "", "LRB"
            return self.getSkip(skp[pos], 0, rnd)
        whr = copyList(self.gwhr)
        whr.extend([("scg_rnum", "=", rnd), ("scg_scod", "=", skp)])
        win = self.sql.getRec("scpgme", cols=["scg_ocod", "scg_sfor",
            "scg_sagt"], where=whr, limit=1)
        if not win or (win[1] == 0 and win[2] == 0):
            return "", "LRB"
        if win[1] > win[2]:
            return self.getSkip(skp, 0, rnd+1)
        else:
            return self.getSkip(win[0], 0, rnd+1)

    def drawLink(self, cwth, l1, l2, x, y, inc):
        self.fpdf.line(x, y, x + (cwth * l1), y)
        self.fpdf.line(x + (cwth * l1), y, x + (cwth * l1), inc)
        self.fpdf.line(x + (cwth * l1), inc, x + (cwth * (l1 + l2)), inc)

    def printClosed(self, skips):
        self.fpdf.drawText()
        self.fpdf.drawText()
        self.fpdf.setFont(style="B", size=8.5)
        cw = self.fpdf.get_string_width("X")
        y = self.fpdf.get_y()
        self.fpdf.drawText(self.cdes, w=58*cw, h=5, border="TLRB", fill=1,
            align="C")
        self.fpdf.drawText("Seq", w=4*cw, h=5, ln=0, border="TLRB", fill=1,
            align="C")
        self.fpdf.drawText("New", w=4*cw, h=5, ln=0, border="TLRB", fill=1,
            align="C")
        self.fpdf.drawText("Name", w=30*cw, h=5, ln=0, border="TLRB", fill=1,
            align="C")
        self.fpdf.drawText("Club", w=20*cw, h=5, border="TLRB", fill=1,
            align="C")
        self.fpdf.setFont(size=8.5)
        pair = 0
        for x in range(16):
            self.fpdf.drawText(x+1, w=4*cw, h=5, ln=0, border="TLRB",
                align="C")
            self.fpdf.drawText("", w=4*cw, h=5, ln=0, border="TLRB", align="C")
            if x < len(skips):
                pair += 1
                self.sql.updRec("scpgme", cols=["scg_pair"], data=[pair],
                    where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                    "=", self.ccod), ("scg_scod", "=", skips[x][0])])
                nam = self.getName(skips[x][1], skips[x][2])
                clb = self.getClub(mem=skips[x][0])
            else:
                nam = ""
                clb = ""
            self.fpdf.drawText(nam, w=30*cw, h=5, ln=0, border="TLRB")
            self.fpdf.drawText(clb, w=20*cw, h=5, border="TLRB")
        txt = "If any players withdraw, delete their names neatly and "\
            "re-number the remaining players (from the top down), in the "\
            "NEW column."
        self.fpdf.drawText(txt, w=58*cw, border="TLRB", ctyp="M")
        detail = (
            ("16", "1 - 16", "", "", "8"),
            ("15", "1 - 14", "24", "", "7"),
            ("14", "17 + 18", "5 - 16", "", "7"),
            ("13", "17", "3 - 12", "23 + 24", "6"),
            ("12", "17 + 18", "5 - 12", "23 + 24", "6"),
            ("11", "17 - 19", "7 - 12", "23 + 24", "5"),
            ("10", "17 + 18", "5 - 8", "21 - 24", "5"),
            ("9", "17 - 20", "9 + 10", "22 - 24", "4"),
            ("8", "17 - 24", "", "", "4"),
            ("7", "17 - 22", "28", "", "3"),
            ("6", "17 - 20", "27 + 28", "", "2"))
        self.fpdf.setFont(style="B", size=8.5)
        self.fpdf.drawText("Closed-up Draw Chart", x=65*cw, y=y, w=37*cw, h=5,
            border="TLRB", fill=1, align="C")
        self.fpdf.drawText("Qty", x=65*cw, w=4*cw, h=5, ln=0, border="TLRB",
            fill=1, align="C")
        self.fpdf.drawText("Use Positions", w=30*cw, h=5, ln=0, border="TLRB",
            fill=1, align="C")
        self.fpdf.drawText("Rks", w=3*cw, h=5, border="TLRB", fill=1,
            align="C")
        self.fpdf.setFont(size=8.5)
        for d in detail:
            self.fpdf.drawText(d[0], x=65*cw, w=4*cw, h=5, ln=0, border="TLRB",
                align="C")
            self.fpdf.drawText(d[1], w=10*cw, h=5, ln=0, border="TLRB",
                align="C")
            self.fpdf.drawText(d[2], w=10*cw, h=5, ln=0, border="TLRB",
                align="C")
            self.fpdf.drawText(d[3], w=10*cw, h=5, ln=0, border="TLRB",
                align="C")
            self.fpdf.drawText(d[4], w=3*cw, h=5, border="TLRB", align="C")
        txt = "Use the positions on the chart, after determining the number "\
            "of players who are present, to populate the competition bracket."
        self.fpdf.drawText(txt, x=65*cw, w=37*cw, border="TLRB", ctyp="M")

    def createRoundRobin(self, sec, sub):
        # Allocate Byes
        whr = copyList(self.where)
        recs = self.sql.getRec("scpgme", cols=["scg_scod"], where=whr)
        byes = self.entsec - len(recs)
        if byes == 2:
            byes = 0
            entsec = len(recs)
            rnds = self.rnds - 1
        else:
            entsec = self.entsec
            rnds = self.rnds
        skps = []
        for rec in recs:
            skps.append(rec[0])
        random.shuffle(skps)
        data = [self.opts["conum"], self.ccod, "M", sec, sub, 1, "M",
            0, 0, "", 0, 0, 0, 0, 0, 0]
        if byes == 1:
            for _ in range(byes):
                self.byenum += 1
                data[7] = self.byenum
                skps.append(self.byenum)
                self.sql.insRec("scpgme", data=data)
        # Allocate Opponents
        count = entsec
        grps = [0+i for i in range(entsec)]
        half = int(count / 2)
        schedule = []
        for _ in range(rnds):
            pairings = []
            for i in range(half):
                pairings.append([grps[i], grps[count-i-1]])
            grps.insert(1, grps.pop())
            schedule.append(pairings)
        for num, dat in enumerate(schedule):
            rnd = num + 1
            for pair in dat:
                pair[0] = skps[pair[0]]
                pair[1] = skps[pair[1]]
                if pair[0] > 900000:
                    skp = pair[1]
                    opp = pair[0]
                else:
                    skp, opp = pair
                if rnd == 1:
                    whr = copyList(self.where)
                    whr.append(("scg_scod", "=", skp))
                    self.sql.updRec("scpgme", cols=["scg_ocod"], data=[opp],
                        where=whr)
                    whr = copyList(self.where)
                    whr.append(("scg_scod", "=", opp))
                    self.sql.updRec("scpgme", cols=["scg_ocod"], data=[skp],
                        where=whr)
                else:
                    data[5] = rnd
                    data[7] = skp
                    data[8] = opp
                    self.sql.insRec("scpgme", data=data)
                    data[8] = skp
                    data[7] = opp
                    self.sql.insRec("scpgme", data=data)
        # Allocate Group Numbers
        for grp, skp in enumerate(skps):
            whr = copyList(self.where)
            whr.append(("scg_scod", "=", skp))
            self.sql.updRec("scpgme", cols=["scg_group"], data=[grp],
                where=whr)

    def allocateRinks(self):
        def doShuffle():
            rnks = self.rinks[:]
            ends = self.rinke[:]
            random.shuffle(rnks)
            random.shuffle(ends)
            rnks.extend(ends)
            return rnks

        clubs = {}
        secs = self.sql.getRec("scpsec", cols=["scs_snum", "scs_rnum",
            "scs_club"], where=[("scs_cono", "=", self.opts["conum"]),
            ("scs_ccod", "=", self.ccod), ("scs_rnum", "<=", self.rnds)],
            order="scs_club")
        for sec, rnd, clb in secs:
            if clb not in clubs:
                clubs[clb] = {}
            day = self.sql.getRec("scprnd", cols=["scr_date"],
                where=[("scr_cono", "=", self.opts["conum"]), ("scr_ccod",
                "=", self.ccod), ("scr_rnum", "=", rnd)], limit=1)[0]
            if day not in clubs[clb]:
                clubs[clb][day] = {}
            if sec not in clubs[clb][day]:
                clubs[clb][day][sec] = {}
            if rnd not in clubs[clb][day][sec]:
                clubs[clb][day][sec][rnd] = []
        for club in clubs:
            for day in clubs[club]:
                rnds = {}
                for sec in clubs[club][day]:
                    for rnd in clubs[club][day][sec]:
                        if rnd > self.rnds:
                            continue
                        if rnd not in rnds:
                            rnds[rnd] = []
                        hist = []
                        skps = self.sql.getRec("scpgme",
                            cols=["scg_scod", "scg_ocod"], where=[
                            ("scg_cono", "=", self.opts["conum"]),
                            ("scg_ccod", "=", self.ccod),
                            ("scg_snum", "=", sec),
                            ("scg_rnum", "=", rnd)])
                        for skp in skps:
                            if skp[0] in hist:
                                continue
                            if skp[0] > 900000 or skp[1] > 900000:
                                continue
                            if skp not in rnds[rnd]:
                                rnds[rnd].append(skp)
                            hist.extend(skp)
                self.again = True
                while self.again:
                    self.getRinks(club, day)
                    for x in range(5000):
                        clash = 0
                        draws = []
                        rhist = {}
                        least = [999, []]
                        for rnd in rnds:
                            allrk = []
                            arink = []
                            for pair in rnds[rnd]:
                                done = False
                                if pair[0] not in rhist:
                                    rhist[pair[0]] = []
                                if pair[1] not in rhist:
                                    rhist[pair[1]] = []
                                rnks = doShuffle()
                                for rnk in rnks:
                                    if rnk in arink:
                                        continue
                                    if rnk in rhist[pair[0]]:
                                        continue
                                    if rnk in rhist[pair[1]]:
                                        continue
                                    allrk.append(pair + [rnk])
                                    rhist[pair[0]].append(rnk)
                                    rhist[pair[1]].append(rnk)
                                    arink.append(rnk)
                                    done = True
                                    break
                                if not done:
                                    for rnk in rnks:
                                        if rnk not in arink:
                                            allrk.append(pair + [rnk])
                                            rhist[pair[0]].append(rnk)
                                            rhist[pair[1]].append(rnk)
                                            arink.append(rnk)
                                            clash += 1
                                            break
                            draws.extend(allrk)
                        if clash < least[0]:
                            least = [clash, copy.deepcopy(draws)]
                    if least[0]:
                        ok = askQuestion(self.opts["mf"].body, "Rinks Error",
                            """There are Insufficient Rinks to Avoid Clashes (%s).

Do you want to Re-Allocate Rinks for %s on %s?""" % (
                            least[0], self.club[1], self.day[1]), default="no")
                        if ok == "no":
                            self.again = False
                    else:
                        self.again = False
                for tm in least[1]:
                    where = [
                        ("scg_cono", "=", self.opts["conum"]),
                        ("scg_ccod", "=", self.ccod)]
                    whr = where[:]
                    whr.append(("scg_scod", "=", tm[0]))
                    whr.append(("scg_ocod", "=", tm[1]))
                    self.sql.updRec("scpgme", cols=["scg_rink"], data=[tm[2]],
                        where=whr)
                    whr = where[:]
                    whr.append(("scg_scod", "=", tm[1]))
                    whr.append(("scg_ocod", "=", tm[0]))
                    self.sql.updRec("scpgme", cols=["scg_rink"], data=[tm[2]],
                        where=whr)

    def getRinks(self, club, day):
        self.club = [club, self.sql.getRec("scpclb", cols=["scc_name"],
            where=[("scc_club", "=", club)], limit=1)[0]]
        self.day = [day, CCD(day, "D1", 10).disp]
        tit = ("{:^22}\n{:^22}".format(
            "Rinks for %s" % self.club[1], self.day[1]))
        fld = (
            (("T",0,0,0),"IUA",20,"Greens","",
                "A","N",self.doGreen,None,None,("notblank",)),)
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.rk = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doRnkEnd,"n"),), rxit=(self.doRnkExit,))
        self.rk.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")

    def doGreen(self, frt, pag, r, c, p, i, w):
        grns = w.split(",")
        self.rnks = []
        for grn in grns:
            if grn in ("A", "B", "C", "D"):
                for rnk in range(1, 7):
                    self.rnks.append("%s%s" % (grn, rnk))
            else:
                for rnk in grn[1:]:
                    self.rnks.append("%s%s" % (grn[0], rnk))

    def doRnkEnd(self):
        self.rinks = []
        self.rinke = []
        for rnk in self.rnks:
            if rnk[1] == "1":
                self.rinke.append(rnk)
            elif rnk[1] == "6" and not self.rnks.count("7"):
                self.rinke.append(rnk)
            elif rnk[1] == "7":
                self.rinke.append(rnk)
            else:
                self.rinks.append(rnk)
        self.rk.closeProcess()

    def doRnkExit(self):
        self.rk.closeProcess()

    def printRoundRobin(self, sec, sub):
        self.printHeading(sec, sub)
        self.fpdf.setFont(style="B", size=10)
        self.fpdf.drawText("TEAM", w=15, border="TLRB", ln=0, align="C",
            fill=1)
        self.fpdf.drawText("SKIP", w=45, border="TLRB", ln=0, align="C",
            fill=1)
        self.fpdf.drawText("CLUB", w=40, border="TLRB", ln=0, align="C",
            fill=1)
        self.fpdf.drawText("", w=10, ln=0)
        x = self.fpdf.get_x()
        self.fpdf.drawText("RND", w=10, border="TLRB", ln=0, align="C", fill=1)
        self.fpdf.drawText("DATE & TIME", w=32, border="TLRB", ln=0, align="C",
            fill=1)
        self.fpdf.drawText("VENUE", w=38, border="TLRB", align="C", fill=1)
        self.fpdf.setFont(size=10)
        y1 = self.fpdf.get_y()
        whr = copyList(self.where)
        whr.append(("scg_rnum", "=", 1))
        plrs = self.sql.getRec("scpgme", where=whr, order="scg_group")
        for n, p in enumerate(plrs):
            self.fpdf.drawText(self.codes[p[13]], w=15, border="TLRB", ln=0,
                align="C")
            txt, bdr = self.getSkip(p[7],0,0)
            self.fpdf.drawText(txt, w=45, border=bdr, ln=0)
            self.fpdf.drawText(self.getClub(mem=p[7]), w=40, border="TLRB")
        # Draw Forms
        rnds = self.sql.getRec(tables=["scprnd", "scpsec"], cols=["scr_rnum",
            "scr_date", "scr_time", "scs_name"], where=[("scs_cono", "=",
            self.opts["conum"]), ("scs_ccod", "=", self.ccod), ("scs_snum",
            "=", sec), ("scr_cono=scs_cono",), ("scr_ccod=scs_ccod",),
            ("scs_rnum=scr_rnum",)], order="scr_rnum, scr_date")
        for r in rnds:
            self.fpdf.set_xy(x, y1)
            txt = self.getRndTxt(r[0])[0]
            self.fpdf.drawText(txt, w=10, border="TLRB", ln=0, align="C")
            date = CCD(r[1], "D1", 10).disp
            dtim = CCD(r[2], "TM",  5).disp
            dt = "%s %s" % (date, dtim)
            self.fpdf.drawText(dt, w=32, border="TLRB", ln=0, align="C")
            txt = r[3].replace("Bowling Club", "BC")
            self.fpdf.drawText(txt, w=38, border="TLRB")
            y1 = self.fpdf.get_y()
        self.fpdf.set_xy(x, y1)
        self.fpdf.drawText()
        self.printBoxes(sec, sub)
        if self.subsec == "Y":
            self.fpdf.drawText()
            self.fpdf.drawText()
            self.fpdf.set_x(9.5)
            self.fpdf.setFont(style="B", size=10)
            if self.numsec == 2:
                mess = "Finals Play-Off"
            else:
                mess = "Sub-Sections Play-Off"
            self.fpdf.drawText(mess, w=190.5, border="TLRB", align="C", fill=1)
            self.fpdf.set_x(9.5)
            self.fpdf.drawText("%s%s" % (sec, sub), w=10, border="TLRB", ln=0,
                align="C", fill=1)
            self.fpdf.drawText(self.getSubSecWin(sec, sub), w=63.25,
                    font=["", 10], border="TLRB", ln=0)
            self.fpdf.drawText("Shots", w=12, border="TLRB", ln=0, align="C",
                font=["B", 10], fill=1)
            self.fpdf.drawText("", w=10, border="TLRB", ln=0,)
            if sub == "A":
                sub = "B"
            else:
                sub = "A"
            self.fpdf.drawText("%s%s" % (sec, sub), w=10, border="TLRB", ln=0,
                align="C", fill=1)
            self.fpdf.drawText(self.getSubSecWin(sec, sub), w=63.25,
                    font=["", 10], border="TLRB", ln=0,)
            self.fpdf.drawText("Shots", w=12, border="TLRB", ln=0, align="C",
                font=["B", 10], fill=1)
            self.fpdf.drawText("", w=10, border="TLRB")
            self.fpdf.setFont(size=10)

    def getSubSecWin(self, sec, sub):
        if self.state < 3:
            return ""
        wins = self.sql.getRec("scpgme", cols=["scg_scod",
            "sum(scg_pnts) as pnts", "sum(scg_sfor) as sfor",
            "sum(scg_sagt) as sagt", "sum(scg_sfor) - sum(scg_sagt) as agg"],
            where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
            self.ccod), ("scg_ctyp", "=", "M"), ("scg_snum", "=", sec),
            ("scg_subs", "=", sub)], group="scg_scod",
            order="pnts desc, agg desc, sagt asc", limit=1)
        nams = self.sql.getRec("scpmem", cols=["scm_surname",
            "scm_names"], where=[("scm_cono", "=", self.opts["conum"]),
            ("scm_scod", "=", wins[0])], limit=1)
        return self.getName(nams[0], nams[1])

    def printHeading(self, sec=0, sub="", date=False):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B", size=10)
        self.fpdf.drawText()
        x = self.fpdf.get_x()
        y = self.fpdf.get_y()
        if os.path.isfile(self.logo):
            self.fpdf.image(self.logo, x, y, 29.375, 13.65)
            self.fpdf.set_xy(x, y)
            self.fpdf.image(self.logo, x+160, y, 29.375, 13.65)
        self.fpdf.set_xy(x, y)
        self.fpdf.drawText(self.opts["conam"], font=["Helvetica", "B", 16],
            align="C")
        self.fpdf.drawText()
        if self.ctyp == "P" or self.playoff:
            self.fpdf.drawText("%s - Play-Offs" % (self.cdes),
                font=["Helvetica", "B", 14], align="C")
        else:
            self.fpdf.drawText("%s - Section %s%s" % (self.cdes, sec, sub),
                font=["Helvetica", "B", 14], align="C")
        self.fpdf.drawText()
        if not date:
            return
        cwth, chgt = self.setBracketFont()
        self.fpdf.setFont(style="B", size=8)
        text = []
        skip = []
        if not self.playoff and self.ctyp == "M" and self.clup == "Y":
            if self.rnds < 4:
                skip.append(1)
            if self.rnds < 3:
                skip.append(2)
            if self.rnds < 2:
                skip.append(3)
            prnd = 4
        else:
            prnd = self.rnds
        nrnd = 1
        for x in range(prnd):
            if self.playoff:
                rnum = self.save + x
                num = rnum + 1
                txt = self.getRndTxt(num)[1]
            elif self.ctyp == "P":
                if x == (prnd - 1):
                    txt = "Final"
                elif x == (prnd - 2):
                    txt = "Semi-Final"
                elif x == (prnd - 3):
                    txt = "Quarter-Final"
                elif x == (prnd - 4):
                    if prnd == 4:
                        txt = "1st Round"
                    elif prnd == 5:
                        txt = "2nd Round"
                    elif prnd == 6:
                        txt = "3rd Round"
                elif x == (prnd - 5):
                    if prnd == 5:
                        txt = "1st Round"
                    elif prnd == 6:
                        txt = "2nd Round"
                elif x == (prnd - 6):
                    txt = "1st Round"
            elif (x + 1) in skip:
                txt = ""
            else:
                txt = "Round %s" % nrnd
                nrnd += 1
            text.append(txt)
        if self.playoff:
            start = self.save + 1
            end = self.xtra + 1
        elif self.ctyp == "P":
            rnds = self.sql.getRec("scprnd", cols=["count(*)"],
                where=[("scr_cono", "=", self.opts["conum"]), ("scr_ccod", "=",
                self.ccod)], limit=1)
            start = rnds[0] - prnd + 1
            end = rnds[0] + 1
        else:
            start = 1
            end = prnd + 1
        nrec = start
        for x in range(start, end):
            if x in skip:
                venue = "Not Applicable"
                date = ""
                dtim = ""
            else:
                rec = self.sql.getRec("scpsec", cols=["scs_name"],
                    where=[("scs_cono", "=", self.opts["conum"]),
                    ("scs_ccod", "=", self.ccod), ("scs_snum",
                    "=", sec), ("scs_rnum", "=", nrec)], limit=1)
                venue = rec[0].replace("Bowling Club", "BC")
                rec = self.sql.getRec("scprnd", cols=["scr_date", "scr_time"],
                    where=[("scr_cono", "=", self.opts["conum"]), ("scr_ccod",
                    "=", self.ccod), ("scr_rnum", "=", nrec)], limit=1)
                date = CCD(rec[0], "D1", 10).disp
                dtim = CCD(rec[1], "TM", 5).disp
                nrec += 1
            if self.playoff:
                idx = x - self.save - 1
            elif self.ctyp == "P":
                idx = x - start
            else:
                idx = x - 1
            text[idx] = "%s\n%s\n%s %s" % (text[idx], venue, date, dtim)
        if self.numsec == 1 or self.playoff or self.ctyp == "P":
            if prnd <= 5:
                text.append("\nCompetition\nWinner")
        else:
            text.append("\nSection\nWinner")
        x = self.fpdf.get_x()
        y = self.fpdf.get_y()
        for txt in text:
            self.fpdf.drawText(txt, x=x, y=y, w=(cwth*25), border="TLRB",
                fill=1, align="C", ctyp="M", font=["Helvetica", "B", 10])
            x += (cwth * 26)
        self.fpdf.drawText()

    def setBracketFont(self):
        if self.clup == "Y" and self.ctyp == "M":
            siz = self.fpdf.font[1]
            chgt = self.fpdf.chgt
        elif self.rnds == 2:
            siz = 10.5
            chgt = 12
        elif self.rnds == 3:
            siz = 7.8
            chgt = 12
        elif self.rnds == 4:
            siz = 6.3
            chgt = 6
        else:
            siz = 5.2
            chgt = 3.5
        self.fpdf.setFont(size=siz)
        return self.fpdf.cwth, chgt

    def printBoxes(self, sec, sub):
        # h = row height
        # ld = line depth
        # ad = additional depth
        # qt = number of rows
        # ft = font size
        whr = copyList(self.gwhr)
        whr.extend([("scg_snum", "=", sec), ("scg_subs", "=", sub)])
        skps = self.sql.getRec("scpgme", cols=["max(scg_rnum)"],
            where=whr, limit=1)
        if skps[0] < self.rnds:
            rnds = skps[0] - 1
        else:
            rnds = self.rnds
        h = 1.5
        if rnds == 3:
            ld = 5
            ad = 10
            qt = 2
            ft = 10
        elif rnds == 5:
            ld = 4
            ad = 13
            qt = 3
            ft = 10
        else:
            ld = 2.7
            ad = 16
            qt = 4
            ft = 9
        self.fpdf.setFont(style="", size=10)
        cw = self.fpdf.get_string_width("X")
        self.fpdf.setFont(style="B", size=ft)
        ox = int(self.fpdf.get_x() / cw)
        oy = int(self.fpdf.get_y() / ld)
        rr = {
            "margins": ((ox, ox+36), (oy, oy+ad)),
            "repeat": (2, qt),
            "rows": [
                (ox, oy, 5, h*2),
                (ox+5, oy, (
                    (5, h, 0.8, "Skip", True),
                    (30, h, 0, ""))),
                (ox+5, oy+h, (
                    (5, h, 0.8, "Club", True),
                    (30, h, 0, ""))),
                (ox, oy+3, (
                    (5, h, 0.8, "RND",  True),
                    (5, h, 0.8, "OPP",  True),
                    (5, h, 0.8, "RNK",  True),
                    (7, h, 0.8, "For",  True),
                    (7, h, 0.8, "Agt",  True),
                    (6, h, 0.8, "Diff", True),
                    (5, h, 0.8, "Pts",  True)))]}
        x = ox
        y = oy + 4.5
        w = [5, 5, 5, 7, 7, 6, 5]
        for z in range(1, rnds + 2):
            row = [x, y, []]
            if z == (rnds + 1):
                row[2].append((w[0]+w[1]+w[2], h, 0.8, "Totals", True))
                for l in range(3, 7):
                    row[2].append((w[l], h, 0, ""))
            else:
                for l in range(7):
                    row[2].append((w[l], h, 0, ""))
            rr["rows"].append(row)
            y += h
        doDrawTable(self.fpdf, rr, ppad=1, spad=1, cw=cw, ld=ld, font=False)
        whr = copyList(self.gwhr)
        whr.extend([("scg_snum", "=", sec), ("scg_subs", "=", sub)])
        skps = self.sql.getRec("scpgme", cols=["scg_group", "scg_scod",
            "scg_rnum", "scg_ocod", "scg_rink", "scg_sfor", "scg_sagt",
            "scg_pnts"], where=whr, order="scg_group, scg_rnum")
        nskp = {}   # {group: [scod, name, club,
                    #       {rnum: ocod, ogrp, rink, sfor, sagt, pnts}]}
        for skp in skps:
            if skp[0] not in nskp:
                if skp[1] > 900000:
                    mem = ["", "", ""]
                else:
                    mem = self.sql.getRec("scpmem", cols=["scm_surname",
                        "scm_names", "scm_club"], where=[("scm_cono", "=",
                        self.opts["conum"]), ("scm_scod", "=", skp[1])],
                        limit=1)
                nskp[skp[0]] = [skp[1], self.getName(mem[0], mem[1]),
                    self.getClub(club=mem[2]), {}]
            opp = self.sql.getRec("scpgme", cols=["scg_group"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_snum", "=", sec), ("scg_subs", "=", sub),
                ("scg_scod", "=", skp[3])], limit=1)
            nskp[skp[0]][3][skp[2]] = [skp[3], opp[0]] + skp[4:8]
        po = ["A", "B", "C", "D", "E", "F", "G", "H"]
        ox = cw * ox
        oy = ld * oy
        sk = 0
        for row in range(qt):
            x = ox
            y = oy
            for col in range(2):
                tot = [0, 0, 0, 0.0]
                skp = nskp[sk]
                self.fpdf.set_font_size(20)
                cd = po[sk]
                self.fpdf.drawText(cd,x=x+cw,y=y,w=5,h=(ld*h*2),align="C")
                self.fpdf.setFont(style="", size=ft)
                self.fpdf.drawText(skp[1], x=x+(cw*10), y=y, w=30, h=(ld*h))
                self.fpdf.drawText(skp[2], x=x+(cw*10), w=30, h=(ld*h))
                self.fpdf.drawText(h=(ld*h))
                for rnd in range(1, rnds + 1):
                    self.fpdf.drawText(rnd, x=x, w=(cw*5), h=(ld*h),
                        ln=0, align="C")
                    cd = po[skp[3][rnd][1]]
                    self.fpdf.drawText(cd, w=(cw*5), h=(ld*h),
                        ln=0, align="C")
                    rk = skp[3][rnd][2]
                    if not rk:
                        rk = ""
                    self.fpdf.drawText(rk, w=(cw*5), h=(ld*h),
                        ln=0, align="C")
                    if skp[0] > 900000 or skp[3][rnd][0] > 900000:
                        txt = ["Bye", "Bye", "", ""]
                    elif self.state > 1:
                        f = skp[3][rnd][3]
                        a = skp[3][rnd][4]
                        n = (f - a)
                        p = skp[3][rnd][5]
                        txt = [f, a, n, p]
                        tot[0] += f
                        tot[1] += a
                        tot[2] += n
                        tot[3] = float(ASD(tot[3]) + ASD(p))
                    else:
                        txt = ["", "", "", ""]
                    tx = self.fpdf.get_x()
                    self.fpdf.drawText(txt[0], w=(cw*7), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(txt[1], w=(cw*7), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(txt[2], w=(cw*6), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(txt[3], w=(cw*5), h=(ld*h),
                        align="R")
                if self.state > 1:
                    self.fpdf.drawText(tot[0], x=tx, w=(cw*7), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(tot[1], w=(cw*7), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(tot[2], w=(cw*6), h=(ld*h),
                        ln=0, align="C")
                    self.fpdf.drawText(tot[3], w=(cw*5), h=(ld*h),
                        align="R")
                x = x + (cw * 41)
                sk += 1
            oy += ld * (ad + 1)

    def printPlayOffs(self):
        self.save = self.rnds
        self.rnds = self.xtra - self.rnds
        self.printHeading(1, "", True)
        self.numsec = 1
        if not self.reprint:
            # Create Lists of Sections
            secs = self.sql.getRec("scpgme", cols=["scg_snum",
                "scg_subs"], where=self.gwhr, group="scg_snum, scg_subs",
                order="scg_snum, scg_subs")
            if self.subsec == "Y":
                nsec = []
                for x in range(0, len(secs), 2):
                    nsec.append(secs[x][0])
                random.shuffle(nsec)
                secs = []
                for sec in nsec:
                    secs.append([sec, "A"])
                    secs.append([sec, "B"])
            else:
                random.shuffle(secs)
            # Byes
            byes = 0
            for mx in (4, 8, 16, 32, 64):
                if len(secs) <= mx:
                    byes = mx - len(secs)
                    break
            byen = 900000
            pair = 0
            self.two = False
            nsec = [secs[:int(len(secs) / 2)], secs[int(len(secs) / 2):]]
            data = [self.opts["conum"], self.ccod, "P", 1, "", 1, "S", 0,
                0, 0, 0, 0, 0, 0, 0, 0]
        for grp in range(1, 3):
            skips = []
            if self.reprint:
                # Reprint
                skps = self.sql.getRec("scpgme", cols=["scg_scod",
                    "scg_ocod"], where=[("scg_cono", "=", self.opts["conum"]),
                    ("scg_ccod", "=", self.ccod), ("scg_ctyp", "=", "P"),
                    ("scg_group", "=", grp)], order="scg_pair")
                for skp in skps:
                    if self.subsec == "Y":
                        if skp[0] > 800000:
                            s1 = "%sB" % (skp[0] - 800000)
                        else:
                            s1 = "%sA" % (skp[0] - 700000)
                        if skp[1] > 900000:
                            s2 = "Bye"
                        elif skp[1] > 800000:
                            s2 = "%sB" % (skp[1] - 800000)
                        else:
                            s2 = "%sA" % (skp[1] - 700000)
                        skips.append([s1, s2, 0, 1])
                    else:
                        if skp[0] > 800000:
                            s1 = skp[0] - 800000
                        else:
                            s1 = skp[0] - 700000
                        if skp[1] > 900000:
                            s2 = "Bye"
                        elif skp[1] > 800000:
                            s2 = skp[1] - 800000
                        else:
                            s2 = skp[1] - 700000
                        skips.append(["%s" % s1, "%s" % s2, 0, 1])
            else:
                # Allocate to pair groups
                bye = int(byes / 2)
                qty = len(nsec[grp - 1])
                if self.subsec == "Y" and qty % 2:
                    if grp == 1:
                        nsec[grp - 1].insert(bye - 1, nsec[grp - 1].pop())
                    else:
                        nsec[grp - 1].insert(bye - 1, nsec[grp - 1].pop(0))
                while nsec[grp - 1]:
                    skp = nsec[grp - 1].pop(0)
                    if bye or not nsec[grp - 1]:
                        skips.append(["%s%s" % tuple(skp),"Bye", 0, 1])
                        if skp[1] == "B":
                            data[7] = skp[0] + 800000
                        else:
                            data[7] = skp[0] + 700000
                        byen += 1
                        data[8] = byen
                        bye -= 1
                    else:
                        opp = nsec[grp - 1].pop(0)
                        skips.append(["%s%s" % tuple(skp),
                            "%s%s" % tuple(opp), 0,1])
                        if skp[1] == "B":
                            data[7] = skp[0] + 800000
                        else:
                            data[7] = skp[0] + 700000
                        if opp[1] == "B":
                            data[8] = opp[0] + 800000
                        else:
                            data[8] = opp[0] + 700000
                    data[13] = grp
                    pair += 1
                    data[15] = pair
                    self.sql.insRec("scpgme", data=data)
            self.printBracket(1, "", grp, skips)

    def getSkip(self, skip, seed, rnd):
        if self.clup == "Y" and self.ctyp == "M":
            return str(skip), "LRB"
        if type(skip) == str:
            return str(skip), "LRB"
        if skip > 900000:
            return "Bye", "TLRB"
        if self.playoff and self.ctyp == "M" and self.state < 3:
            if self.subsec == "Y":
                if skip > 800000:
                    return "%sB" % (skip - 800000), "LRB"
                else:
                    return "%sA" % (skip - 700000), "LRB"
            else:
                return str(skip), "LRB"
        if skip > 800000:
            skip = skip - 800000
        elif skip > 700000:
            skip = skip - 700000
        col = ["scm_surname", "scm_names"]
        whr = [
            ("scm_cono", "=", self.opts["conum"]),
            ("scm_scod", "=", skip)]
        skp = self.sql.getRec("scpmem", cols=col, where=whr, limit=1)
        if skp:
            name = "%s, %s" % (skp[0], skp[1][0])
        else:
            name = "Unknown"
        if rnd and self.state > 1:
            col = ["scg_scod", "scg_ocod", "scg_sfor", "scg_sagt"]
            whr = [
                ("scg_cono", "=", self.opts["conum"]),
                ("scg_ccod", "=", self.ccod),
                ("scg_ctyp", "=", self.ctyp),
                ("scg_rnum", "=", rnd),
                ("(", "scg_scod", "=", skip, "or", "scg_ocod", "=", skip, ")")]
            skp = self.sql.getRec("scpgme", cols=col, where=whr,
                limit=1)
            if skp and skip == skp[0]:
                if skp[2]:
                    name = "%s - %s" % (name, skp[2])
            elif skp and skp[3]:
                name = "%s - %s" % (name, skp[3])
        elif seed:
            name = "%s (%s)" % (name, seed)
        return name, "TLRB"

    def getName(self, snam, fnam):
        if snam:
            return "%s, %s" % (snam, fnam.split()[0][0])
        else:
            return "Bye"

    def getClub(self, mem=None, club=None):
        if mem and mem > 900000:
            return "Bye"
        if club:
            clb = self.sql.getRec("scpclb", cols=["scc_name"],
                where=[("scc_club", "=", club)], limit=1)
        elif mem:
            clb = self.sql.getRec(tables=["scpmem", "scpclb"],
                cols=["scc_name"], where=[("scm_cono", "=",
                self.opts["conum"]), ("scm_scod", "=", mem),
                ("scc_club=scm_club",)], limit=1)
        else:
            clb = ["Bye"]
        return clb[0].replace("Bowling Club", "BC")

    def getRndTxt(self, rnd):
        if self.subsec == "Y" and rnd == self.rnds + 1:
            return ("P1", "Round 1")
        if not self.playoff and rnd <= self.rnds:
            return (str(rnd), "%s Round" % rnd)
        if rnd == self.xtra:
            return ("F", "Final")
        if rnd == (self.xtra - 1):
            return ("SF", "Semi-Final")
        if rnd == (self.xtra - 2):
            return ("QF", "Quarter-Final")
        if self.playoff == "N":
            qpo = rnd - self.rnds
        else:
            qpo = (self.rnds + rnd) - self.xtra
        return ("P%s" % qpo, "Round %s" % qpo)

    def doExit(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
