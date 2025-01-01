"""
SYNOPSIS
    Asset Groups Listing.

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

from TartanClasses import GetCtl, RepPrt, TartanDialog

class arc320(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.fromad = assctl["cta_emadd"]

    def mainProcess(self):
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=[], tend=tnd,
            txit=txt, view=("Y","V"))

    def doEnd(self):
        tables = ["assgrp"]
        heads = ["Asset Groups Master Listing"]
        col = [["asg_group","UA",3.0,"Grp"],
                ["asg_desc","NA",30.0,"Description"],
                ["asg_assacc","UI",7.0,"Ass-Acc"],
                ["asg_depacc","UI",7.0,"Dep-Acc"],
                ["asg_expacc","UI",7.0,"Exp-Acc"]]
        whr = [("asg_cono", "=", self.opts["conum"])]
        odr = "asg_group"
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=tables,
            heads=heads, cols=col, where=whr, order=odr,
            conum=self.opts["conum"], conam=self.opts["conam"],
            repprt=self.df.repprt, repeml=self.df.repeml, fromad=self.fromad)
        self.df.enableButtonsTags(state=state)
        self.closeProcess()

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
