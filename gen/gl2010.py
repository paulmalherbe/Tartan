"""
SYNOPSIS
    General Ledger - Capturing Opening Balances.

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

from TartanClasses import CCD, FileImport, Sql, TartanDialog
from tartanFunctions import showInfo, showError

class gl2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlynd", "genmst", "genbal"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        per = self.sql.getRec("ctlynd", where=[("cye_cono", "=",
            self.opts["conum"]), ("cye_period", "=", 0)], limit=1)
        if not per:
            showError(self.opts["mf"].body, "Period Error", """No Period 0!

Please Contact your Software Support and Quote this Message as this is a Serious Error!""")
            return
        self.start = per[self.sql.ctlynd_col.index("cye_start")]
        return True

    def drawDialog(self):
        sel_acc = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (("glm_acno", "", 0, "Acc-Num"),
                    ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        sel_all = {
            "stype": "R",
            "tables": ("genbal","genmst"),
            "cols": (
                ("glo_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description"),
                ("glo_trdt", "", 0, "Date"),
                ("glo_cyr", "", 0, "Balance")),
            "where": [
                ("glo_cono", "=", self.opts["conum"]),
                ("glm_cono=glo_cono",),
                ("glm_acno=glo_acno",),
                ("glo_trdt", "=", self.start)]}
        fld = (
            (("C",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "","N",self.doAcc,sel_acc,None,None),
            (("C",0,0,1),"ONA",30,"Description"),
            (("C",0,0,2),"ISD",13.2,"Balance","Balance Value",
                "","N",self.doBal,None,None,None))
        but = (
            ("Import File",None,self.doImport,0,("C",0,1),("C",0,2),
                "Import Opening Balances from a CSV or XLS File."),
            ("All Entries", sel_all, None, 1, ("C", 0, 1), None,
                "Display All Existing Balances"),
            ("Exit", None, self.exitData, 1, ("C", 0, 1), ("C", 0, 2)))
        row = (20,)
        self.df = TartanDialog(self.opts["mf"], rows=row, eflds=fld,
            cend=((self.endData,"y"),), cxit=(self.exitData,), butt=but)

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        impcol = [
            ["Account Number", 0, "UI", 7],
            ["Opening Balance", 1, "SD", 13.2]]
        fi = FileImport(self.opts["mf"], impcol=impcol)
        err = None
        for num, line in enumerate(fi.impdat):
            if len(line) != 2:
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, 2, len(line))
                break
            self.acc = line[0]
            chk = self.sql.getRec("genmst", where=[("glm_cono", "=",
                self.opts["conum"]), ("glm_acno", "=", self.acc)], limit=1)
            if not chk:
                err = "Line %s: Invalid Account %s" % ((num + 1), self.acc)
                break
            self.bal = line[1]
            self.old = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno",
                "=", self.acc), ("glo_trdt", "=", self.start)], limit=1)
            if not self.old:
                self.new_acc = "y"
            else:
                self.new_acc = "n"
            self.endData(det=True)
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        elif fi.impdat:
            self.opts["mf"].dbm.commitDbase()
        self.df.enableButtonsTags(state=state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doAcc(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not desc:
            return "Invalid Account Number"
        self.acc = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])
        self.old = self.sql.getRec("genbal", where=[("glo_cono", "=",
            self.opts["conum"]), ("glo_acno", "=", self.acc),
            ("glo_trdt", "=", self.start)], limit=1)
        if not self.old:
            self.new_acc = "y"
        else:
            self.new_acc = "n"
            bal = self.old[self.sql.genbal_col.index("glo_cyr")]
            self.df.loadEntry(frt, pag, p+2, data=bal)

    def doBal(self, frt, pag, r, c, p, i, w):
        self.bal = w

    def endData(self, det=False):
        data = [self.opts["conum"], self.acc, self.start, self.bal]
        if self.new_acc == "y":
            self.sql.insRec("genbal", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.genbal_col
            data.append(self.old[col.index("glo_xflag")])
            self.sql.updRec("genbal", data=data, where=[("glo_cono",
                "=", self.opts["conum"]), ("glo_acno", "=", self.acc),
                ("glo_trdt", "=", self.start)])
        if det:
            return
        self.opts["mf"].dbm.commitDbase()
        nxt = self.sql.getRec("genmst", cols=["glm_acno"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", ">",
            self.acc)], limit=1)
        if nxt:
            self.df.colf[0][0][5] = nxt[0]
        else:
            self.df.colf[0][0][5] = 0
        self.df.advanceLine(0)

    def exitData(self):
        bals = self.sql.getRec("genbal", cols=["sum(glo_cyr)"],
            where=[("glo_cono", "=", self.opts["conum"]), ("glo_trdt", "=",
            self.start)], limit=1)
        if bals[0]:
            diff = CCD(bals[0], "SD", 13.2)
            showError(self.opts["mf"].body, "Out of Balance",
                "Opening Balances Do Not Balance by %s" % diff.disp)
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        else:
            showInfo(self.opts["mf"].body, "Year End", """A Year End for the Previous Period Must be Executed to Include These Opening Balances.

If the Current Period is 1 then the Year End for Period 0 must be Executed.""")
            self.df.closeProcess()
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
