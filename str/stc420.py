"""
SYNOPSIS
    Stores Locations Listing.

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

from TartanClasses import RepPrt, TartanDialog

class stc420(object):
    def __init__(self, **opts):
        self.opts = opts
        self.mainProcess()
        self.opts["mf"].startLoop()

    def mainProcess(self):
        fld = ()
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"))

    def doEnd(self):
        tables = ["strloc"]
        heads = ["Stores Locations Master Listing"]
        col = [["srl_loc","NA",1.0,"L"],
                ["srl_desc","NA",30.0,"Description"]]
        whr = [("srl_cono", "=", self.opts["conum"])]
        odr = "srl_loc"
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=col, order=odr, where=whr,
            conum=self.opts["conum"], conam=self.opts["conam"],
            repprt=self.df.repprt)
        self.df.enableButtonsTags(state=state)
        self.closeProcess()

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
