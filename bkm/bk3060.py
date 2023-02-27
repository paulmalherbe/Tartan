"""
SYNOPSIS
    Bookings Master Notes Listing.

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

from TartanClasses import CCD, GetCtl, NotesPrint, ProgressBar, RepPrt, Sql
from tartanFunctions import textFormat

class bk3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "memmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.fromad = bkmctl["cbk_emadd"]
        self.notes = NotesPrint(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], "BKM")
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
                    bkn = dat[2]
                    des = self.sql.getRec(tables=["bkmmst", "bkmcon"],
                        cols=["bkc_title", "bkc_sname", "bkc_names"],
                        where=[("bkm_cono", "=", self.opts["conum"]),
                        ("bkm_number", "=", int(bkn)), ("bkc_cono=bkm_cono",),
                        ("bkc_ccode=bkm_ccode",)], limit=1)
                    data.append([bkn, "%s %s %s" % (des[0], des[2][0],
                        des[1]), dat[4], CCD(dat[3], "d1", 10).disp,
                        dat[6], CCD(dat[7], "d1", 10).disp, d])
                else:
                    data.append(["", "", "", "", "", "", d])
        p.closeProgress()
        if not p.quit:
            name = self.__class__.__name__
            head = ["Booking Master Notes Listing"]
            cols = [
                ["a", "NA",  7, "Booking",    "y"],
                ["b", "NA", 30, "Name",        "y"],
                ["c", "NA", 20, "User-Name",   "y"],
                ["d", "NA", 10, "Capt-Date",   "y"],
                ["e", "UA",  1, "F",           "y"],
                ["f", "NA", 10, "Actn-Date",   "y"],
                ["g", "NA", 50, "Details",     "y"]]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=name, tables=data, heads=head,
                cols=cols, ttype="D", repprt=self.notes.df.repprt,
                repeml=self.notes.df.repeml, fromad=self.fromad)

# vim:set ts=4 sw=4 sts=4 expandtab:
