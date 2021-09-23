"""
SYNOPSIS
    Sectional Competition Capture Match Results.

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

from TartanClasses import FileImport, ProgressBar, SelectChoice, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, askQuestion, showError

class sc2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if "test" not in opts:
            self.opts["test"] = None
        if self.setVariables():
            if self.opts["test"]:
                self.doImport()
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["scpcmp", "scpmem", "scpent",
            "scpgme"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.pair = 0
        self.doimport = False
        return True

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("scpcmp",),
            "cols": (
                ("scp_ccod", "", 0, "CCD"),
                ("scp_name", "", 0, "Name", "Y"),
                ("scp_tsiz", "", 0, "S"),
                ("scp_fmat", "", 0, "F"),
                ("scp_nsec", "", 0, "NS"),
                ("scp_nent", "", 0, "NE")),
            "where": [("scp_cono", "=", self.opts["conum"])]}
        self.sec = {
            "stype": "C",
            "titl": "Available Sections",
            "head": ("Sec", "Club"),
            "typs": (("Ua", 3), ("NA", 30)),
            "data": []}
        self.skp = {
            "stype": "R",
            "tables": ("scpmem", "scpgme"),
            "cols": (
                ("a", "UI", 6, "S-Code"),
                ("b", "NA", 30, "Name", "Y"),
                ("c", "UI", 6, "O-Code"),
                ("d", "NA", 30, "Name"),
                ("e", "UI", 3, "For"),
                ("f", "UI", 3, "Agt")),
            "where": [],
            "wtype": "D"}
        tag = (("Results", None, ("T",0,0), ("T",0,1)),)
        r1s = (("Main","M"), ("Play-Offs","P"))
        fld = (
            (("T",0,0,0),"I@scp_ccod",0,"","",
                "","Y",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"O@scp_name",0,""),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "","N",self.doCmpTyp,None,None,None),
            (("T",0,2,0),"I@scg_rnum",0,"Round","",
                "","N",self.doRndNum,None,None,("notzero",)),
            (("T",1,0,0),"IUI",2,"Section Number", "",
                "","N",self.doSecNum,None,None,("notzero",)),
            (("T",1,0,0),"IUA",1,"Sub-Section", "",
                "","N",self.doSubNum,None,None,("in",("A","B"))),
            (("C",1,0,0),"I@scg_scod",0,"","",
                0,"N",self.doSkpCod,self.skp,None,("notzero",)),
            (("C",1,0,0),"ONA",30,"Skp-Name"),
            (("C",1,0,0),"I@scg_sfor",0,"","",
                "","N",self.doShots,None,None,("efld",)),
            (("C",1,0,0),"I@scg_ocod",0,"","",
                0,"N",self.doSkpCod,self.skp,None,("notzero",)),
            (("C",1,0,0),"ONA",30,"Opp-Name"),
            (("C",1,0,0),"I@scg_sagt",0,"","",
                "","N",self.doShots,None,None,("efld",)))
        tnd = ((self.doTopEnd,"y"), (self.doTopEnd,"n"))
        txt = (self.doTopExit, self.doTopExit)
        cnd = (None, (self.doColEnd,"n"))
        cxt = (None, self.doColExit)
        but = (
            ("Import Results",None,self.doImport,0,("T",1,1),
                (("T",1,2),("T",1,0))),
            ("Show Entries",None,self.doShow,0,("C",1,1),
                ("C",1,2)))
        self.df = TartanDialog(self.opts["mf"], tags=tag, eflds=fld,
            rows=(0,16), tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        com = self.sql.getRec("scpcmp", where=[("scp_cono", "=",
            self.opts["conum"]), ("scp_ccod", "=", w)], limit=1)
        if not com:
            return "Invalid Competition Code"
        if not com[2]:
            return "Competiton Draw Not Yet Done"
        chk = self.sql.getRec("scpent", cols=["count(*)"],
            where=[("sce_cono", "=", self.opts["conum"]), ("sce_ccod", "=",
            w)], limit=1)
        if not chk[0]:
            return "There are No Entries for this Competition"
        self.ccod = w
        self.name = com[self.sql.scpcmp_col.index("scp_name")]
        self.fmat = com[self.sql.scpcmp_col.index("scp_fmat")]
        self.nsec = com[self.sql.scpcmp_col.index("scp_nsec")]
        self.nent = com[self.sql.scpcmp_col.index("scp_nent")]
        self.ssub = com[self.sql.scpcmp_col.index("scp_subs")]
        self.squa = com[self.sql.scpcmp_col.index("scp_qual")]
        self.clup = com[self.sql.scpcmp_col.index("scp_clup")]
        self.mrnds = com[self.sql.scpcmp_col.index("scp_mrnds")]
        self.prnds = com[self.sql.scpcmp_col.index("scp_prnds")]
        self.state = com[self.sql.scpcmp_col.index("scp_state")]
        if not self.doimport:
            self.df.loadEntry(frt, pag, p+1, data=self.name)
        self.byenum = 900000
        if self.state < 3:
            self.ctyp = "M"
            self.lrnd = self.mrnds
            if not self.doimport:
                self.df.loadEntry(frt, pag, p+2, data=self.ctyp)
                return "sk2"
        elif self.state == 6:
            return "All Results Already Captured"
        else:
            self.ctyp = "P"
            self.lrnd = self.prnds
            if not self.doimport:
                self.df.loadEntry(frt, pag, p+2, data=self.ctyp)

    def doCmpTyp(self, frt, pag, r, c, p, i, w):
        self.ctyp = w
        chk = self.sql.getRec("scpgme", cols=["count(*)", "sum(scg_sfor)",
            "sum(scg_sagt)"], where=[("scg_cono", "=", self.opts["conum"]),
            ("scg_ccod", "=", self.ccod), ("scg_ctyp", "=", "P")], limit=1)
        if self.ctyp == "M":
            if chk[0] and (chk[1] or chk[2]):
                return "Play-Offs Already Started"
            self.lrnd = self.mrnds
        elif not chk[0]:
            return "Play-Offs Draw Not Yet Done"
        else:
            self.lrnd = self.prnds

    def doRndNum(self, frt, pag, r, c, p, i, w):
        if self.ctyp == "M" and self.clup == "Y" and w > 1:
            more = self.sql.getRec("scpgme", cols=["count(*)"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_rnum", "=", w-1), ("scg_ocod", "=", 0)],
                limit=1)[0]
            if more:
                return "Closed-Up Draw, Round %s Results Missing" % (w - 1)
        if w > self.lrnd:
            return "Invalid Round, Exceeds Maximum (%s)" % self.lrnd
        if w > 1:
            chk = self.sql.getRec("scpgme", cols=["scg_scod",
                "scg_ocod", "sum(scg_sfor)", "sum(scg_sagt)"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_rnum", "=",
                w - 1)])
            for s in chk:
                if s[0] < 900000 and s[1] < 900000 and not s[2] and not s[3]:
                    return "Invalid Round, Previous Round Missing"
            chk = self.sql.getRec("scpgme", where=[("scg_cono", "=",
                self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
                "=", self.ctyp), ("scg_rnum", "<", w), ("scg_scod", "<",
                900000), ("scg_ocod", "<", 900000), ("(", "scg_sfor", "=", 0,
                "and", "scg_sagt", "=", 0, ")")])
            if chk:
                return "Previous Round Not Yet Completely Captured"
        chk = self.sql.getRec("scpgme", cols=["sum(scg_sfor)",
            "sum(scg_sagt)"], where=[("scg_cono", "=", self.opts["conum"]),
            ("scg_ccod", "=", self.ccod), ("scg_ctyp", "=", self.ctyp),
            ("scg_rnum", ">", w)], limit=1)
        if chk[0] or chk[1]:
            return "Invalid Round, Later Rounds Captured"
        chk = self.sql.getRec("scpgme", cols=["count(*)"],
            where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
            self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_rnum", "=", w),
            ("scg_scod", "<", 900000), ("scg_ocod", "<", 900000),("scg_sfor",
            "=", 0), ("scg_sagt", "=", 0)])[0]
        if not chk:
            ok = askQuestion(self.opts["mf"].body, "Already Entered",
                """All Results for this Round Already Captured.

Would you Like to Recapture this Round?""", default="no")
            if ok == "no":
                return "Already Captured"
            if self.fmat == "K" or self.ctyp == "R":
                if self.ctyp == "M" and w == self.mrnds:
                    self.sql.delRec("scpgme", where=[("scg_cono", "=",
                        self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                        ("scg_ctyp", "=", "R")])
                else:
                    self.sql.delRec("scpgme", where=[("scg_cono", "=",
                        self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                        ("scg_ctyp", "=", self.ctyp), ("scg_rnum", "=",
                        w+1)])
        self.rnum = w
        self.doimport = False

    def doImport(self):
        self.doimport = True
        if self.opts["test"]:
            self.ccod, self.rnum, impfle = self.opts["test"]
            err = self.doCmpCod("T", 0, 0, 0, 0, 0, self.ccod)
            if err:
                print(err)
                return
            self.doGetOldWin()
            impdlg = False
        else:
            impfle = None
            impdlg = True
            self.df.setWidget(self.df.mstFrame, state="hide")
        cols = [
            ["scg_snum", 0, "UI", 2],
            ["scg_subs", 1, "UA", 1],
            ["scg_scod", 2, "UI", 6],
            ["scg_ocod", 3, "UI", 6],
            ["scg_sfor", 4, "UI", 2],
            ["scg_sagt", 5, "UI", 2]]
        fi = FileImport(self.opts["mf"], impcol=cols, impfle=impfle,
            impdlg=impdlg)
        if fi.impdat:
            if not self.opts["test"]:
                sp = ProgressBar(self.opts["mf"].body, typ="Importing Results",
                    mxs=len(fi.impdat))
            err = None
            for num, line in enumerate(fi.impdat):
                if not self.opts["test"]:
                    sp.displayProgress(num)
                if not line[0]:
                    continue
                whr = [
                    ("scg_cono", "=", self.opts["conum"]),
                    ("scg_ccod", "=", self.ccod),
                    ("scg_ctyp", "=", self.ctyp),
                    ("scg_snum", "=", line[0]),
                    ("scg_subs", "=", line[1]),
                    ("scg_rnum", "=", self.rnum)]
                if self.clup == "Y":
                    self.newo = True
                    whr.append(("scg_scod", "in", (line[2], line[3])))
                else:
                    self.newo = False
                    whr.append(("scg_scod", "=", line[2]))
                    whr.append(("scg_ocod", "=", line[3]))
                chk = self.sql.getRec("scpgme", where=whr)
                if not chk:
                    err = "Invalid Skip %s, Opponent %s" % (line[2], line[3])
                    break
                if line[2] > 900000 or line[3] > 900000:
                    pass
                elif not line[4] and not line[5]:
                    err = "Zero Results"
                    break
                self.snum = line[0]
                self.subs = line[1]
                self.scod = line[2]
                self.ocod = line[3]
                self.sfor = line[4]
                self.sagt = line[5]
                self.doColEnd()
            if not self.opts["test"]:
                sp.closeProgress()
            if err:
                err = "Line %s: %s" % ((num + 1), err)
                showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
                self.opts["mf"].dbm.rollbackDbase()
            else:
                self.ierr = False
                if self.ssub == "Y":
                    secs = int(self.nsec / 2)
                else:
                    secs = self.nsec
                for self.snum in range(1, secs + 1):
                    if self.ssub == "Y":
                        for self.subs in ("A", "B"):
                            self.doColExit()
                            if self.ierr:
                                break
                        if self.ierr:
                            break
                    else:
                        self.subs = ""
                        self.doColExit()
                        if self.ierr:
                            break
                if not self.ierr:
                    self.opts["mf"].dbm.commitDbase()
        self.doTopExit()
        if not self.opts["test"]:
            self.df.setWidget(self.df.mstFrame, state="show")
            self.df.focusField("T", 0, 1)

    def doSecNum(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("scpgme", where=[("scg_cono", "=",
            self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
            "=", self.ctyp), ("scg_snum", "=", w)], limit=1)
        if not chk:
            return "Invalid Section Number"
        self.snum = w
        if self.ssub == "N" or self.ctyp == "P":
            self.subs = ""
            self.df.loadEntry(frt, pag, p+1, data=self.subs)
            self.doLoadSkips()
            return "sk1"

    def doSubNum(self, frt, pag, r, c, p, i, w):
        self.subs = w
        self.doLoadSkips()

    def doTopEnd(self):
        if self.df.pag == 0:
            if self.ctyp == "P":
                self.snum = 1
                self.df.loadEntry("T", 1, 0, data=self.snum)
                self.subs = ""
                self.df.loadEntry("T", 1, 1, data=self.subs)
                self.doLoadSkips()
                self.df.focusField("C", 1, 1)
            else:
                self.doGetOldWin()
                self.df.focusField("T", 1, 1)
        else:
            self.df.focusField("C", 1, 1)

    def doLoadSkips(self):
        col = ["scg_scod", "scg_ocod", "scg_sfor", "scg_sagt"]
        whr = [
            ("scg_cono", "=", self.opts["conum"]),
            ("scg_ccod", "=", self.ccod),
            ("scg_ctyp", "=", self.ctyp),
            ("scg_rnum", "=", self.rnum),
            ("scg_snum", "=", self.snum),
            ("scg_subs", "=", self.subs),
            ("scg_ocod", "<", 900000)]
        data = []
        recs = self.sql.getRec("scpgme", cols=col, where=whr)
        for rec in recs:
            data.append((rec[0], self.getName(rec[0]), rec[1],
                self.getName(rec[1]), rec[2], rec[3]))
        self.skp["where"] = data

    def doTopExit(self):
        if not self.opts["test"] and self.df.pag == 0:
            self.df.closeProcess()
            self.opts["mf"].closeLoop()
        else:
            # Check all entries for round
            chk = self.sql.getRec("scpgme", cols=["count(*)"],
                where=[("scg_cono", "=", self.opts["conum"]),
                ("scg_ccod", "=", self.ccod), ("scg_ctyp",
                "=", self.ctyp), ("scg_rnum", "=", self.rnum),
                ("scg_scod", "<", 900000), ("scg_ocod", "<", 900000),
                ("scg_sfor", "=", 0), ("scg_sagt", "=", 0)], limit=1)[0]
            if chk:
                txt = "Not All the Results for Round %s Captured" % self.rnum
                if self.opts["test"]:
                    self.opts["mf"].dbm.rollbackDbase()
                    return
                txt = "%s\n\nDo You want to Exit and Lose All Results for "\
                    "this Round?" % txt
                ok = askQuestion(self.opts["mf"].body, "Missing Results", txt,
                    default="no")
                if ok == "yes":
                    self.opts["mf"].dbm.rollbackDbase()
                    self.df.focusField("T", 0, 4)
                else:
                    self.df.focusField("T", 1, 1)
                return
            if self.rnum == self.lrnd:
                chk = self.sql.getRec("scpgme", cols=["count(*)"],
                    where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                    "=", self.ccod), ("scg_ctyp", "=", "M"), ("scg_scod", "<",
                    900000), ("scg_ocod", "<", 900000), ("scg_sfor", "=", 0),
                    ("scg_sagt", "=", 0)], limit=1)[0]
                if not chk:
                    # Update scpcmp if no missing entries
                    self.sql.updRec("scpcmp", cols=["scp_state"], data=[3],
                        where=[("scp_cono", "=", self.opts["conum"]),
                        ("scp_ccod", "=", self.ccod)])
                    self.opts["mf"].dbm.commitDbase()
            if not self.doimport:
                if self.ctyp == "P":
                    self.df.focusField("T", 0, 4)
                else:
                    self.df.focusField("T", 0, 1)

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        skp = self.sql.getRec("scpgme", where=[("scg_cono", "=",
            self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
            "=", self.ctyp), ("scg_snum", "=", self.snum), ("scg_subs", "=",
            self.subs), ("scg_rnum", "=", self.rnum), ("scg_scod", "=", w)],
            limit=1)
        if not skp:
            return "Invalid Skip"
        if skp[self.sql.scpgme_col.index("scg_ocod")] > 900000:
            return "Skip has a Bye"
        if i == 3:
            if w == self.scod:
                return "Playing Against Himself?"
            if skp[self.sql.scpgme_col.index("scg_ocod")]:
                return "Already Paired"
            self.ocod = w
            onam = self.getName(self.ocod)
            self.df.loadEntry("C", 1, p+1, data=onam)
            self.df.loadEntry("C", 1, p+2, data=0)
            return
        self.scod = w
        snam = self.getName(w)
        self.df.loadEntry("C", 1, p+1, data=snam)
        sfor = skp[self.sql.scpgme_col.index("scg_sfor")]
        self.df.loadEntry("C", 1, p+2, data=sfor)
        self.ocod = skp[self.sql.scpgme_col.index("scg_ocod")]
        if self.ocod:
            self.newo = False
            self.df.loadEntry("C", 1, p+3, data=self.ocod)
            onam = self.getName(self.ocod)
            self.df.loadEntry("C", 1, p+4, data=onam)
            ofor = skp[self.sql.scpgme_col.index("scg_sagt")]
            self.df.loadEntry("C", 1, p+5, data=ofor)
        else:
            self.newo = True

    def getName(self, code):
        if code > 900000:
            return "Bye"
        nam = self.sql.getRec("scpmem", cols=["scm_surname",
            "scm_names"], where=[("scm_cono", "=", self.opts["conum"]),
            ("scm_scod", "=", code)], limit=1)
        return "%s, %s" % (nam[0], nam[1][0])

    def doShots(self, frt, pag, r, c, p, i, w):
        if i == 2:
            self.sfor = w
            if not self.newo:
                return "sk2"
        else:
            self.sagt = w

    def doPoints(self, frt, pag, r, c, p, i, w):
        pass

    def doColEnd(self):
        if self.fmat == "K":
            if self.newo:
                self.sql.delRec("scpgme", where=[("scg_cono", "=",
                    self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                    ("scg_ctyp", "=", self.ctyp), ("scg_snum", "=", self.snum),
                    ("scg_subs", "=", self.subs), ("scg_rnum", "=", self.rnum),
                    ("scg_scod", "=", self.ocod)])
                cols = ["scg_ocod"]
                data = [self.ocod]
            else:
                cols = []
                data = []
            if self.clup == "Y":
                cols.extend(["scg_sfor", "scg_sagt", "scg_pair"])
                self.pair += 1
                data.extend([self.sfor, self.sagt, self.pair])
            else:
                cols.extend(["scg_sfor", "scg_sagt"])
                data.extend([self.sfor, self.sagt])
            self.sql.updRec("scpgme", cols=cols, data=data, where=[("scg_cono",
                "=", self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                ("scg_ctyp", "=", self.ctyp), ("scg_snum", "=", self.snum),
                ("scg_subs", "=", self.subs), ("scg_rnum", "=", self.rnum),
                ("scg_scod", "=", self.scod)])
        else:
            if self.sfor == self.sagt:
                pfor = .5
                pagt = .5
            elif self.sfor > self.sagt:
                pfor = 1
                pagt = 0
            else:
                pfor = 0
                pagt = 1
            self.sql.updRec("scpgme", cols=["scg_sfor", "scg_sagt",
                "scg_pnts"], data=[self.sfor, self.sagt, pfor],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_snum", "=",
                self.snum), ("scg_subs", "=", self.subs), ("scg_rnum", "=",
                self.rnum), ("scg_scod", "=", self.scod)])
            self.sql.updRec("scpgme", cols=["scg_sfor", "scg_sagt",
                "scg_pnts"], data=[self.sagt, self.sfor, pagt],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
                self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_snum", "=",
                self.snum), ("scg_subs", "=", self.subs), ("scg_rnum", "=",
                self.rnum), ("scg_scod", "=", self.ocod)])
        self.scod = 0
        if not self.doimport:
            self.doLoadSkips()
            self.df.advanceLine(1)

    def doShow(self):
        cols = (
            ("scod", "Skip", 6, "UI", "N"),
            ("sname", "Name", 30, "NA", "N"),
            ("sfor", "Shots", 5, "UI", "N"),
            ("ocod", "Oppt", 6, "UI", "N"),
            ("oname", "Name", 30, "NA", "N"),
            ("sagt", "Shots", 5, "UI", "N"))
        recs = self.sql.getRec("scpgme", where=[("scg_cono", "=",
            self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
            "=", self.ctyp), ("scg_snum", "=", self.snum), ("scg_subs", "=",
            self.subs), ("scg_rnum", "=", self.rnum)])
        done = []
        data = []
        for rec in recs:
            scod = rec[self.sql.scpgme_col.index("scg_scod")]
            ocod = rec[self.sql.scpgme_col.index("scg_ocod")]
            if scod in done or scod > 900000 or ocod in done or ocod > 900000:
                continue
            sfor = rec[self.sql.scpgme_col.index("scg_sfor")]
            sagt = rec[self.sql.scpgme_col.index("scg_sagt")]
            data.append((scod, self.getName(scod), sfor, ocod,
                self.getName(ocod), sagt))
        SelectChoice(self.opts["mf"].window, "Results", cols, data)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doColExit(self):
        chk = self.sql.getRec("scpgme", cols=["count(*)"],
            where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
            self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_rnum", "=",
            self.rnum), ("scg_snum", "=", self.snum), ("scg_subs", "=",
            self.subs), ("scg_scod", "<", 900000), ("scg_ocod", "<", 900000),
            ("(", "scg_sfor", "=", 0, "and", "scg_sagt", "=", 0, ")")],
            limit=1)
        if chk[0] and (self.clup == "N" or self.ctyp == "P" or \
                            (self.clup == "Y" and self.rnum > 1)):
            # All results for section not yet entered
            if self.doimport:
                showError(self.opts["mf"].body, "Missing Results",
                    "Some Results are Missing, Please Check Import "\
                    "File and Retry")
                self.opts["mf"].dbm.rollbackDbase()
                self.ierr = True
                return
            ok = askQuestion(self.opts["mf"].body, "Missing Results",
                "Some Result are Missing. Do You want to Exit and Lose "\
                "the Results for this Section?")
            if ok == "no":
                self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                return
            self.opts["mf"].dbm.rollbackDbase()
        else:
            chk = self.doUpdateTables()
            if not self.doimport:
                if chk == "continue":
                    self.df.focusField(self.df.frt, self.df.pag, self.df.col)
                    return
                if chk == "abort":
                    self.opts["mf"].dbm.rollbackDbase()
                else:
                    self.opts["mf"].dbm.commitDbase()
        if not self.doimport:
            self.df.clearFrame("T", 1)
            self.df.clearFrame("C", 1)
            if self.ctyp == "P":
                self.df.focusField("T", 0, 4)
            else:
                self.df.focusField("T", 1, 1)

    def doUpdateTables(self):
        nrnd = self.rnum + 1
        if self.fmat == "K" and self.clup == "Y" and self.ctyp == "M":
            # Closed up draw (1st and maybe 2nd Round)
            skps = self.sql.getRec("scpgme", where=[("scg_cono", "=",
                self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
                "=", self.ctyp), ("scg_snum", "=", self.snum), ("scg_subs",
                "=", self.subs), ("scg_rnum", "=", self.rnum)])
            byes = []
            nums = {}
            for skp in skps:
                scod = skp[self.sql.scpgme_col.index("scg_scod")]
                ocod = skp[self.sql.scpgme_col.index("scg_ocod")]
                if not ocod:
                    byes.append(scod)
                nums[scod] = skp
            for skp in byes:
                if self.opts["test"]:
                    ok = "B"
                else:
                    ok = askChoice(self.opts["mf"].body, "Capture Error",
                        "The Results for Skip %s - %s is Missing. Did he/she "\
                        "Withdraw or have a Bye?" % (skp, self.getName(skp)),
                        butt=(("No", "N"), ("Withdraw", "W"), ("Bye", "B"),
                        ("Abort", "A")), default="Bye")
                if ok == "N":
                    return "continue"
                if ok == "A":
                    return "abort"
                if ok == "W":
                    self.sql.delRec("scpgme", where=[("scg_cono", "=",
                        self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                        ("scg_scod", "=", skp)])
                    byes.remove(skp)
                    del nums[skp]
                    continue
            for scod in nums:
                rec = nums[scod]
                scod = rec[self.sql.scpgme_col.index("scg_scod")]
                ocod = rec[self.sql.scpgme_col.index("scg_ocod")]
                sfor = rec[self.sql.scpgme_col.index("scg_sfor")]
                sagt = rec[self.sql.scpgme_col.index("scg_sagt")]
                where = [
                    ("scg_cono", "=", self.opts["conum"]),
                    ("scg_ccod", "=", self.ccod),
                    ("scg_ctyp", "=", self.ctyp),
                    ("scg_snum", "=", self.snum),
                    ("scg_subs", "=", self.subs),
                    ("scg_rnum", "=", nrnd),
                    ("scg_scod", "=", scod)]
                if scod in byes:
                    self.byenum += 1
                    # Create bye
                    self.sql.updRec("scpgme", cols=["scg_ocod"],
                        data=[self.byenum], where=where)
                if nrnd < self.lrnd:
                    # Create next round record
                    rec[self.sql.scpgme_col.index("scg_rnum")] = nrnd
                    rec[self.sql.scpgme_col.index("scg_ocod")] = 0
                    rec[self.sql.scpgme_col.index("scg_sfor")] = 0
                    rec[self.sql.scpgme_col.index("scg_sagt")] = 0
                    rec[self.sql.scpgme_col.index("scg_seed")] = 0
                    rec[self.sql.scpgme_col.index("scg_pair")] = 0
                    if scod not in byes and sfor < sagt and ocod:
                        scod = ocod
                        rec[self.sql.scpgme_col.index("scg_scod")] = scod
                    chk = self.sql.getRec("scpgme", where=where, limit=1)
                    if not chk:
                        self.sql.insRec("scpgme", data=rec)
                    else:
                        self.sql.updRec("scpgme", data=rec, where=where)
                else:
                    # Update playoff records
                    cod = self.snum + 700000
                    if sfor > sagt:
                        win = scod
                    else:
                        win = ocod
                    whr = where[:6]
                    whr[2] = ("scg_ctyp", "=", "P")
                    whr[3] = ("scg_snum", "=", 1)
                    whr[5] = ("scg_rnum", "=", 1)
                    whr.append(("scg_scod", "=", cod))
                    self.sql.updRec("scpgme", cols=["scg_scod"], data=[win],
                        where=whr)
                    whr[6] = ("scg_ocod", "=", cod)
                    self.sql.updRec("scpgme", cols=["scg_ocod"], data=[win],
                        where=whr)
        if (self.fmat == "K" and self.clup == "N") or self.ctyp == "P":
            recs = self.sql.getRec("scpgme", where=[("scg_cono", "=",
                self.opts["conum"]), ("scg_ccod", "=", self.ccod), ("scg_ctyp",
                "=", self.ctyp), ("scg_snum", "=", self.snum), ("scg_rnum",
                "=", self.rnum)], order="scg_group, scg_pair")
            group = 0
            for num in range(0, len(recs), 2):
                one = recs[num]
                snum = one[self.sql.scpgme_col.index("scg_snum")]
                subs = one[self.sql.scpgme_col.index("scg_subs")]
                if group != one[self.sql.scpgme_col.index("scg_group")]:
                    group = one[self.sql.scpgme_col.index("scg_group")]
                    pair = 1
                else:
                    pair += 1
                cod1 = one[self.sql.scpgme_col.index("scg_scod")]
                opp1 = one[self.sql.scpgme_col.index("scg_ocod")]
                for1 = one[self.sql.scpgme_col.index("scg_sfor")]
                agt1 = one[self.sql.scpgme_col.index("scg_sagt")]
                if opp1 > 900000 or for1 > agt1:
                    win1 = cod1
                else:
                    win1 = opp1
                if len(recs[num:]) > 1:
                    two = recs[num + 1]
                    cod2 = two[self.sql.scpgme_col.index("scg_scod")]
                    opp2 = two[self.sql.scpgme_col.index("scg_ocod")]
                    for2 = two[self.sql.scpgme_col.index("scg_sfor")]
                    agt2 = two[self.sql.scpgme_col.index("scg_sagt")]
                    if opp2 > 900000 or for2 > agt2:
                        win2 = cod2
                    else:
                        win2 = opp2
                else:
                    win2 = 0
                # Create next round record
                sgc = self.sql.scpgme_col
                whr = [
                    ("scg_cono", "=", one[sgc.index("scg_cono")]),
                    ("scg_ccod", "=", one[sgc.index("scg_ccod")]),
                    ("scg_ctyp", "=", one[sgc.index("scg_ctyp")]),
                    ("scg_snum", "=", one[sgc.index("scg_snum")]),
                    ("scg_subs", "=", one[sgc.index("scg_subs")]),
                    ("scg_rnum", "=", nrnd),
                    ("scg_ktyp", "=", one[sgc.index("scg_ktyp")]),
                    ("scg_scod", "=", win1)]
                one[sgc.index("scg_rnum")] = nrnd
                one[sgc.index("scg_scod")] = win1
                one[sgc.index("scg_ocod")] = win2
                one[sgc.index("scg_sfor")] = 0
                one[sgc.index("scg_sagt")] = 0
                one[sgc.index("scg_pnts")] = 0
                one[sgc.index("scg_pair")] = pair
                if not self.sql.getRec("scpgme", where=whr, limit=1):
                    self.sql.insRec("scpgme", data=one)
                else:
                    self.sql.updRec("scpgme", cols=["scg_ocod", "scg_pair"],
                        data=[win2, pair], where=whr)
                if self.rnum == self.lrnd and \
                        self.ctyp == "M" and self.nsec > 2:
                    # Create playoff records with winners codes
                    if not self.oldwin:
                        if subs == "B":
                            key = snum + 800000
                        else:
                            key = snum + 700000
                    else:
                        key = self.oldwin[snum]
                    self.sql.updRec("scpgme", cols=["scg_scod"],
                        data=[win1], where=[("scg_cono", "=",
                        self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                        ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1),
                        ("scg_scod", "=", key)])
                    self.sql.updRec("scpgme", cols=["scg_ocod"],
                        data=[win1], where=[("scg_cono", "=",
                        self.opts["conum"]), ("scg_ccod", "=", self.ccod),
                        ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1),
                        ("scg_ocod", "=", key)])
        elif self.squa == "S" and self.rnum == self.lrnd:
            # Update playoff records with winners codes
            if self.ssub == "Y":
                lsub = "B"
            else:
                lsub = ""
            whr = [
                ("scg_cono", "=", self.opts["conum"]),
                ("scg_ccod", "=", self.ccod),
                ("scg_ctyp", "=", self.ctyp),
                ("scg_snum", "=", self.snum),
                ("scg_subs", "=", self.subs)]
            if self.fmat == "K":
                col = ["scg_scod", "scg_ocod", "scg_sfor", "scg_sagt"]
                whr.append(("scg_rnum", "=", self.lrnd))
                rec = self.sql.getRec("scpgme", cols=col,
                    where=whr, limit=1)
                if rec[2] > rec[3]:
                    win = rec[0]
                else:
                    win = rec[1]
            else:
                self.doGetNewWin(sect=self.snum, sub=self.subs)
                win = self.newwin[self.snum]
            if not self.oldwin:
                if self.subs == "B":
                    key = self.snum + 800000
                else:
                    key = self.snum + 700000
            else:
                key = self.oldwin[self.snum]
            self.sql.updRec("scpgme", cols=["scg_scod"], data=[win],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                "=", self.ccod), ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1),
                ("scg_scod", "=", key)])
            self.sql.updRec("scpgme", cols=["scg_ocod"], data=[win],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                "=", self.ccod), ("scg_ctyp", "=", "P"), ("scg_rnum", "=", 1),
                ("scg_ocod", "=", key)])
            if self.snum == self.nsec and self.subs == lsub:
                self.sql.updRec("scpgme", cols=["scg_ktyp"], data=["M"],
                    where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                    "=", self.ccod), ("scg_ctyp", "=", "P")])
        # Check if all results for the round are captured
        chek = self.sql.getRec("scpgme", cols=["count(*)"],
            where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod", "=",
            self.ccod), ("scg_ctyp", "=", self.ctyp), ("scg_rnum", "=",
            self.rnum), ("scg_scod", "<", 900000), ("scg_ocod", "<", 900000),
            ("scg_sfor", "=", 0), ("scg_sagt", "=", 0)], limit=1)
        if chek[0]:
            return
        if self.clup == "Y" and self.ctyp == "M" and nrnd == self.lrnd:
            state = 3
        elif self.rnum == self.lrnd:
            if self.ctyp == "M":
                state = 3
            else:
                state = 6
        elif self.ctyp == "M":
            state = 2
        else:
            state = 5
        self.sql.updRec("scpcmp", cols=["scp_state"], data=[state],
            where=[("scp_cono", "=", self.opts["conum"]), ("scp_ccod",
            "=", self.ccod)])

    def doGetOldWin(self):
        self.oldwin = {}
        if self.ctyp == "M" and self.rnum == self.lrnd:
            recs = self.sql.getRec("scpgme", cols=["scg_scod", "scg_ocod"],
                where=[("scg_cono", "=", self.opts["conum"]), ("scg_ccod",
                "=", self.ccod), ("scg_ctyp", "=", "P"), ("scg_snum", "=", 1)])
            for rec in recs:
                for cod in rec:
                    if cod < 900000:
                        sec = self.sql.getRec("scpgme", cols=["scg_snum"],
                            where=[("scg_cono", "=", self.opts["conum"]),
                            ("scg_ccod", "=", self.ccod), ("scg_ctyp", "=",
                            "M"), ("scg_scod", "=", cod)], limit=1)
                        if sec:
                            self.oldwin[sec[0]] = cod

    def doGetNewWin(self, sect=None, sub=""):
        # Get Leaders
        self.newwin = {}
        if sect is None:
            secs = []
            for x in range(self.nsec):
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
                ("scg_snum", "=", sec),
                ("scg_subs", "=", sub)]
            grp = "scg_scod"
            odr = "a desc, b desc, c desc"
            rec = self.sql.getRec("scpgme", cols=col, where=whr, group=grp,
                order=odr, limit=1)
            self.newwin[sec] = rec[0]

# vim:set ts=4 sw=4 sts=4 expandtab:
