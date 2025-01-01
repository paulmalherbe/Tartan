"""
SYNOPSIS
    Clubs's Maintenance.

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

from TartanClasses import FileImport, ProgressBar, TartanDialog, Sql
from tartanFunctions import getNextCode, showError

class scc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "scpclb", "scpmem"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        clb = {
            "stype": "R",
            "tables": ("scpclb",),
            "cols": (
                ("scc_club", "", 0, "Cod"),
                ("scc_name", "", 0, "Name", "Y")),
            "order": "scc_name"}
        fld = (
            (("T",0,0,0),"I@scc_club",0,"","",
                "","Y",self.doClbCod,clb,None,("efld",)),
            (("T",0,1,0),"I@scc_name",0,"","",
                "","N",self.doName,None,self.doDelete,("notblank",)))
        but = (("Import",None,self.doImport,0,("T",0,1),("T",0,2),
            "Import Clubs from a CSV or XLS File.",1),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt)

    def doClbCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.club = getNextCode(self.sql, "scpclb", "scc_club", last=999)
            self.df.loadEntry(frt, pag, p, data=self.club)
        else:
            self.club = w
        self.old = self.sql.getRec("scpclb", where=[("scc_club", "=",
            self.club)], limit=1)
        if not self.old:
            self.newclb = True
        else:
            self.newclb = False
            for num, fld in enumerate(self.old[:-1]):
                self.df.loadEntry(frt, pag, num, data=fld)

    def doName(self, frt, pag, r, c, p, i, w):
        if self.newclb and self.sql.getRec("scpclb", where=[("scc_name",
                                                                "ilike", w)]):
            return "A Club with this Name Already Exists"

    def doDelete(self):
        if self.newclb:
            return
        error = False
        for tab in (("scpmem", "scm_cono", "scm_ccod"),):
            chk = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                self.opts["conum"]), (tab[2], "=", self.club)], limit=1)
            if chk:
                error = True
                break
        if error:
            return "There are Entries for this Club, Not Deleted"
        self.sql.delRec("scpclb", where=[("scc_club", "=", self.club)])
        self.opts["mf"].dbm.commitDbase()

    def doImport(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="scpclb", impskp=[])
        sp = ProgressBar(self.opts["mf"].body, typ="Importing Club Records",
            mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            chk = self.sql.getRec("scpclb", where=[("scc_club",
                "=", line[0])], limit=1)
            if chk:
                err = "%s %s Already Exists" % (fi.impcol[0][0], line[0])
                break
            if not line[1]:
                err = "Blank Name"
                break
            self.sql.insRec("scpclb", data=line)
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

    def doEnd(self):
        data = self.df.t_work[0][0][:]
        if self.newclb:
            self.sql.insRec("scpclb", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.scpclb_col
            data.append(self.old[col.index("scc_xflag")])
            self.sql.updRec("scpclb", data=data, where=[("scc_club",
                "=", self.club)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
