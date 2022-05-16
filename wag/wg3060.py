"""
SYNOPSIS
    Salaries and Wages Notes Listing.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2022 Paul Malherbe.

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

from TartanClasses import CCD, GetCtl, NotesPrint, ProgressBar, RepPrt, Sql
from tartanFunctions import textFormat

class wg3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "wagmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        self.notes = NotesPrint(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], "WAG")
        if not self.notes.data:
            return
        return True

    def mainProcess(self):
        data = []
        p = ProgressBar(self.opts["mf"].body, typ="Generating the Report",
            mxs=len(self.notes.data), esc=True)
        for num, dat in enumerate(self.notes.data):
            p.displayProgress(num)
            if p.quit:
                break
            desc = textFormat(dat[5], width=50)
            for n, d in enumerate(desc):
                if not n:
                    acc = int(dat[2].strip())
                    nam = self.sql.getRec("wagmst", cols=["wgm_sname"],
                        where=[("wgm_cono", "=", self.opts["conum"]),
                        ("wgm_empno", "=", acc)], limit=1)
                    data.append([acc, nam[0], dat[4],
                        CCD(dat[3], "d1", 10).disp, dat[6],
                        CCD(dat[7], "d1", 10).disp, d])
                else:
                    data.append(["", "", "", "", "", "", d])
        p.closeProgress()
        if not p.quit:
            name = self.__class__.__name__
            head = ["Salaries Masterfile Notes Listing"]
            cols = [
                ["a", "NA",  5, "Emp-Num",     "y"],
                ["b", "NA", 30, "Name",        "y"],
                ["c", "NA", 20, "User-Name",   "y"],
                ["d", "NA", 10, "Cap-Date",    "y"],
                ["e", "UA",  1, "F",           "y"],
                ["f", "NA", 10, "Act-Date",    "y"],
                ["g", "NA", 50, "Details",     "y"]]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=name, tables=data, heads=head,
                cols=cols, ttype="D", repprt=self.notes.df.repprt,
                repeml=self.notes.df.repeml, fromad=self.fromad)

# vim:set ts=4 sw=4 sts=4 expandtab:
