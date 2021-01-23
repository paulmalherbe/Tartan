"""
SYNOPSIS
    Rental Tenants Notes Listing.

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

from TartanClasses import CCD, GetCtl, NotesPrint, ProgressBar, RepPrt, Sql
from tartanFunctions import textFormat

class rc3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "rcatnm",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rcactl = gc.getCtl("rcactl", self.opts["conum"])
        if not rcactl:
            return
        self.fromad = rcactl["cte_emadd"]
        self.notes = NotesPrint(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], "RCA")
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
            if len(dat[2].strip()) < 14:
                continue
            desc = textFormat(dat[5], width=50)
            for n, d in enumerate(desc):
                if not n:
                    own = dat[2][:7].strip()
                    cod = dat[2][7:14].strip()
                    acc = dat[2][14:].strip()
                    nam = self.sql.getRec("rcatnm", cols=["rtn_name"],
                        where=[("rtn_cono", "=", self.opts["conum"]),
                        ("rtn_owner", "=", own), ("rtn_code", "=", cod),
                        ("rtn_acno", "=", acc)], limit=1)
                    if not nam:
                        continue
                    data.append([own, cod, acc, nam[0], dat[4],
                        CCD(dat[3], "d1", 10).disp, dat[6],
                        CCD(dat[7], "d1", 10).disp, d])
                else:
                    data.append(["", "", "", "", "", "", "", "", d])
        p.closeProgress()
        if not p.quit:
            name = self.__class__.__name__
            head = ["Rental's Masterfile Notes Listing"]
            cols = [
                ["a", "NA",  7, "Own-Cod",   "y"],
                ["b", "NA",  7, "Prm-Cod",   "y"],
                ["c", "NA",  7, "Acc-Num",   "y"],
                ["d", "NA", 30, "Acc-Name",  "y"],
                ["e", "NA", 20, "User-Name", "y"],
                ["f", "NA", 10, "Cap-Date",  "y"],
                ["g", "UA",  1, "F",         "y"],
                ["h", "NA", 10, "Act-Date",  "y"],
                ["i", "NA", 50, "Details",   "y"]]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=name, tables=data, heads=head,
                cols=cols, ttype="D", repprt=self.notes.df.repprt,
                repeml=self.notes.df.repeml, fromad=self.fromad)

# vim:set ts=4 sw=4 sts=4 expandtab:
