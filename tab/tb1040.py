"""
SYNOPSIS
    Utility to copy Tables from one database to another using different
    rcfiles.

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

import sys
from TartanClasses import DBCreate, Dbase, ProgressBar, Sql, TartanDialog
from tartanFunctions import getSingleRecords, loadRcFile, showError
from tartanWork import tabdic

class tb1040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.rcf = None
                self.tables = None
                for o, v in self.opts["args"]:
                    if o == "-r":
                        self.rcf = v
                    elif o == "-t":
                        self.tables = []
                        tb = v.split(",")
                        for t in tb:
                            self.tables.append([t.strip()])
                if self.rcf and self.tables:
                    check = self.doFrom("T", 0, 0, 1, 0, 0, self.rcf)
                    if check:
                        showError(self.opts["mf"].body, "Options Error", check)
                    else:
                        self.doCopyTables()
                        self.dbm.closeDbase()
            else:
                self.doDialog()
                self.opts["mf"].startLoop()

    def setVariables(self):
        sql = Sql(self.opts["mf"].dbm, "verupd", prog=self.__class__.__name__)
        if sql.error:
            return
        vera = sql.getRec("verupd", limit=1)
        if vera:
            self.vera = vera[0]
        return True

    def doDialog(self):
        tit = ("Database/Table Copying",)
        fle = {
            "stype": "F",
            "types": "fle",
            "initd": None,
            "ftype": [["RC Files", "*"]],
            "showh": "Y"}                        # Show hidden files
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IFF",50,"From RC File","",
                "","Y",self.doFrom,fle,None,("fle",)),
            (("T",0,1,0),("IRB",r1s),0,"Whole Database","",
                "N","N",self.doWhole,None,None,None))
        but = (("Cancel",None,self.doCloseProcess,1,None,None),)
        tnd = ((self.doProcess,"y"), )
        txt = (self.doCloseProcess, )
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt)

    def doFrom(self, frt, pag, r, c, p, i, w):
        if sys.platform == "win32":
            if w.lower() == self.opts["mf"].rcdic["name"].lower():
                return "Invalid RC File (1)"
        elif w == self.opts["mf"].rcdic["name"]:
            return "Invalid RC File (2)"
        rcdic = loadRcFile(w)
        if rcdic == "error":
            return "Invalid RC File Format"
        elif not rcdic:
            return "Invalid RC File (3)"
        try:
            self.dbm = Dbase(rcdic)
            if self.dbm.err:
                raise Exception
            self.dbm.openDbase()
            self.sql = Sql(self.dbm, ["verupd", "ftable", "ffield"],
                prog=self.__class__.__name__)
            verb = self.sql.getRec("verupd", limit=1)
            if verb:
                verb = verb[0]
            if verb != self.vera:
                showError(self.opts["mf"].body, "Version Error",
                    "The version (%s) of the source database does not agree "\
                    "with the version (%s) of the receiving database.\n\n"\
                    "You must ensure that these versions do agree before "\
                    "attempting to copy tables." % (verb, self.vera))
                return "Version Error"
        except:
            return "Invalid RC File (4)"
        if not self.dbm.db:
            return "Invalid RC File (5)"

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

    def doProcess(self):
        self.df.closeProcess()
        if self.whole == "Y":
            self.tables = self.sql.getRec("ftable", cols=["ft_tabl"],
                where=[("ft_seq", "=", 1)], order="ft_tabl")
        else:
            self.tables = getSingleRecords(self.opts["mf"], "ftable",
                ("ft_tabl", "ft_desc"), where=[("ft_seq", "=", 1)],
                order="ft_tabl")
        if not self.tables:
            showError(self.opts["mf"].body, "Table Error", "No Tables "\
                "Selected for Copying %s" % self.opts["mf"].rcdic["dbname"])
        else:
            self.doCopyTables()
        self.doCloseProcess()

    def doCopyTables(self):
        p1 = ProgressBar(self.opts["mf"].body, mxs=len(self.tables),
            typ="Copying Database")
        for num, tab in enumerate(self.tables):
            p1.displayProgress(num)
            if tab[0] not in ("ftable", "ffield"):
                if tab[0] not in tabdic:
                    print("NO", tab, "in tabdic")
                    continue
                self.opts["mf"].updateStatus("Adding Table %s" % tab[0])
                opts = [("-t", tab[0]), ("-x", False)]
                DBCreate(dbm=self.opts["mf"].dbm, opts=opts)
            self.opts["mf"].updateStatus("Populating Table %s" % tab[0])
            sqt = Sql(self.opts["mf"].dbm, tab[0], prog=self.__class__.__name__)
            try:
                sqt.delRec(tab[0])
            except:
                pass
            sqf = Sql(self.dbm, tab[0], prog=self.__class__.__name__)
            dat = sqf.getRec(tables=tab[0])
            if dat:
                p2 = ProgressBar(self.opts["mf"].body, inn=p1, mxs=len(dat),
                    typ="Populating Table %s" % tab[0])
                sqt.insRec(tab[0], data=dat, dofmt=False, pbar=p2)
                self.opts["mf"].dbm.commitDbase()
                p2.closeProgress()
        p1.closeProgress()

    def doCloseProcess(self):
        self.df.closeProcess()
        try:
            self.dbm.closeDbase()
        except:
            pass
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
