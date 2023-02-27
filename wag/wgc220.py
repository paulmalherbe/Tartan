"""
SYNOPSIS
    Salaries Receiver of Revenue Codes Listing.

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

from TartanClasses import RepPrt, TartanDialog

class wgc220(object):
    def __init__(self, **opts):
        self.opts = opts
        self.mainProcess()
        self.opts["mf"].startLoop()

    def mainProcess(self):
        r1s = (("Number","N"),("Description","D"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order          ","Sort Order",
                "N","Y",self.doSort,None,None,None),)
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEnd(self):
        self.df.closeProcess()
        tables = ["wagrcv"]
        heads = ["Receiver of Revenue Codes Listing"]
        cols = [["rcv_code","UI",4.0,"Code"],
                ["rcv_desc","NA",50.0,"Description"]]
        if self.sort == "N":
            order = "rcv_code"
        else:
            order = "rcv_desc"
        opts = "Sort Order: %s" % self.sort
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=cols, order=order, opts=opts,
            repprt=self.df.repprt)
        self.df.enableButtonsTags(state=state)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
