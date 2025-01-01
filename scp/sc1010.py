"""
SYNOPSIS
    Sectional Competition Player's Maintenance.

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

from TartanClasses import FileImport, ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, getNextCode, showError

class sc1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "args" in self.opts:
                self.newskp = True
                self.newclb = False
                self.club = None
                if self.opts["args"][0]:
                    self.skip = self.opts["args"][0]
                    self.df.loadEntry("T", 0, 0, data=self.skip)
                    self.df.focusField("T", 0, 2)
                else:
                    self.df.focusField("T", 0, 1)
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["scpclb", "scpent", "scpgme",
            "scpmem"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        skp = {
            "stype": "R",
            "tables": ("scpmem",),
            "cols": (
                ("scm_scod", "", 0, "Cod"),
                ("scm_surname", "", 0, "Surname", "Y"),
                ("scm_names", "", 0, "Names")),
            "where": [("scm_cono", "=", self.opts["conum"])],
            "order": "scm_surname"}
        clb = {
            "stype": "R",
            "tables": ("scpclb",),
            "cols": (
                ("scc_club", "", 0, "Cod"),
                ("scc_name", "", 0, "Name", "Y")),
            "butt": [("New Club", self.doNewClub)],
            "order": "scc_name"}
        r1s = (("Male", "M"), ("Female", "F"))
        if "args" in self.opts:
            fld = [(("T",0,0,0),"O@scm_scod",0,"")]
        else:
            fld = [(("T",0,0,0),"I@scm_scod",0,"","",
                "","Y",self.doSkpCod,skp,None,("efld",))]
        fld.extend([
            (("T",0,1,0),"I@scm_surname",0,"","",
                "","N",self.doSurname,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"I@scm_names",0,"","",
                "","N",self.doNames,None,None,("notblank",)),
            (("T",0,3,0),("IRB",r1s),0,"Gender","",
                "M","N",None,None,None,None),
            (("T",0,4,0),"I@scm_club",0,"","",
                "","N",self.doClbCod,clb,None,("efld",)),
            (("T",0,4,0),"INA",30,"","Club Name",
                "","N",self.doClbNam,None,None,("notblank",)),
            (("T",0,5,0),"I@scm_email",30,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"I@scm_phone",0,"","",
                "","N",None,None,None,("efld",))])
        but = (
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),
                "Import Members from a CSV or XLS File."),
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt, clicks=self.doClick)

    def doClick(self, *opts):
        if self.df.col == 1:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.skip = getNextCode(self.sql, "scpmem", "scm_scod",
                where=[("scm_cono", "=", self.opts["conum"])], last=899999)
            self.df.loadEntry(frt, pag, p, data=self.skip)
        else:
            self.skip = w
        self.newclb = False
        self.club = None
        self.old = self.sql.getRec("scpmem", where=[("scm_cono", "=",
            self.opts["conum"]), ("scm_scod", "=", self.skip)], limit=1)
        if not self.old:
            self.newskp = True
        else:
            self.newskp = False
            for num, fld in enumerate(self.old[2:-1]):
                if num > 3:
                    pos = num + 2
                else:
                    pos = num + 1
                self.df.loadEntry(frt, pag, pos, data=fld)
                if num == 3:
                    self.club = fld
                    clb = self.sql.getRec("scpclb",
                        where=[("scc_club", "=", fld)], limit=1)
                    self.df.loadEntry(frt, pag, pos+1, data=clb[1])

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        if self.newskp:
            chk = self.sql.getRec("scpmem", where=[("scm_cono", "=",
                self.opts["conum"]), ("scm_surname", "ilike", self.sname,
                "and", "scm_names", "ilike", "%s%s" % (w.split()[0], "%"))])
            if chk:
                return "A Player with this Name Already Exists"

    def doDelete(self):
        if self.newskp:
            return
        error = False
        for tab in (("scpent", "sce_cono", "sce_scod"),
                    ("scpgme", "scg_cono", "scg_scod")):
            chk = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                self.opts["conum"]), (tab[2], "=", self.skip)], limit=1)
            if chk:
                error = True
                break
        if error:
            return "There are Movements for this Player, Not Deleted"
        self.sql.delRec("scpmem", where=[("scm_cono", "=", self.opts["conum"]),
            ("scm_scod", "=", self.skip)])
        self.opts["mf"].dbm.commitDbase()

    def doClbCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.club = getNextCode(self.sql, "scpclb", "scc_club", last=999)
            self.df.loadEntry(frt, pag, p, data=self.club)
        else:
            self.club = w
        chk = self.sql.getRec("scpclb", where=[("scc_club", "=",
            self.club)], limit=1)
        if not chk:
            ok = askQuestion(self.opts["mf"].body, head="New Club",
                mess="This Club Code Does Not Exist, Create It?")
            if ok == "no":
                return "rf"
            self.doNewClub(self.club)
        else:
            self.newclb = False
            self.df.loadEntry(frt, pag, p+1, data=chk[1])
            return "sk1"

    def doNewClub(self, club=None):
        self.newclb = True
        if not club:
            self.club = getNextCode(self.sql, "scpclb", "scc_club", last=999)
            self.df.loadEntry("T", 0, 5, data=self.club)
            self.df.clearEntry("T", 0, 7)
            self.df.focusField("T", 0, 7)
        else:
            self.club = club

    def doClbNam(self, frt, pag, r, c, p, i, w):
        if not self.club:
            return "ff6|Invalid Club Code"

    def doImport(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="scpmem", impskp=["scm_cono"])
        sp = ProgressBar(self.opts["mf"].body,
            typ="Importing Member's Records", mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            if not line[0]:
                continue
            chk = self.sql.getRec("scpmem", where=[("scm_cono",
                "=", self.opts["conum"]), ("scm_scod", "=", line[0])], limit=1)
            if chk:
                err = "%s %s Already Exists" % (fi.impcol[0][0], line[0])
                break
            if not line[1]:
                err = "Blank Surname"
                break
            if not line[2]:
                err = "Blank Names"
                break
            if not line[3]:
                err = "Invalid Gender"
                break
            line.insert(0, self.opts["conum"])
            self.sql.insRec("scpmem", data=line)
        sp.closeProgress()
        if err:
            err = "Line %s: %s" % ((num + 1), err)
            showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            if col == 6:
                self.df.focusField(frt, pag, (col), err=mes)
            else:
                self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.doEnd()

    def doEnd(self):
        data = [self.opts["conum"], self.skip]
        data.extend(self.df.t_work[0][0][1:5])
        data.extend(self.df.t_work[0][0][6:])
        if self.newskp:
            self.sql.insRec("scpmem", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.scpmem_col
            data.append(self.old[col.index("scm_xflag")])
            self.sql.updRec("scpmem", data=data, where=[("scm_cono",
                "=", self.opts["conum"]), ("scm_scod", "=", self.skip)])
        if self.newclb:
            self.sql.insRec("scpclb", data=[self.club,
                self.df.t_work[0][0][5]])
        self.opts["mf"].dbm.commitDbase()
        if "args" in self.opts:
            self.doExit()
        else:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
