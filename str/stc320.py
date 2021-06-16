"""
SYNOPSIS
    Product Groups Listing.

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

from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog

class stc320(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "strgrp"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        return True

    def mainProcess(self):
        fld = ()
        tnd = ((self.doEnd,"Y"), )
        txt = (self.closeProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"))

    def doEnd(self):
        heads = ["Product Groups Master Listing"]
        grps = self.sql.getRec("strgrp", cols=["gpm_group",
            "gpm_desc", "gpm_vatcode", "gpm_sales", "gpm_costs"],
            where=[("gpm_cono", "=", self.opts["conum"])],
            order="gpm_group")
        data = []
        for grp in grps:
            if self.glint == "Y":
                ac1 = self.getGenDesc(grp[3])
                if not ac1:
                    ac1 = [""]
                ac2 = self.getGenDesc(grp[4])
                if not ac2:
                    ac2 = [""]
            else:
                ac1 = ac2 = [""]
            gp = grp[:4]
            gp.extend([ac1[0], grp[4], ac2[0]])
            data.append(gp)
        cols = [
            ["a","UA",3.0,"Grp"],
            ["b","NA",30.0,"Description"],
            ["c","UA",1.0,"V"],
            ["d","UI",7.0,"SLS-Acc"],
            ["e","NA",30.0,"Description"],
            ["f","UI",7.0,"COS-Acc"],
            ["g","NA",30.0,"Description"]]
        state = self.df.disableButtonsTags()
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=heads, cols=cols, conum=self.opts["conum"],
            conam=self.opts["conam"], ttype="D", repprt=self.df.repprt)
        self.df.enableButtonsTags(state=state)
        self.closeProcess()

    def getGenDesc(self, acc):
        des = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            acc)], limit=1)
        return des

    def closeProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
