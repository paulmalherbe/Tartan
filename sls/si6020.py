"""
SYNOPSIS
    Sales Document Deletions.

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

import time
from TartanClasses import GetCtl, Sql, TartanDialog

class si6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["slsiv1", "slsiv2", "slsiv3"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Outstanding Sales Document Cancellations (%s)" %
                self.__class__.__name__)
        r1s = (("All", "A"), ("Orders", "O"), ("Works", "W"), ("Quotes", "Q"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Documents","",
                "A","Y",self.doType,None,None,None),
            (("T",0,1,0),"IUI",2,"Months Outstanding","",
                24,"Y",self.doMonths,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doType(self, frt, pag, r, c, p, i, w):
        self.dtyp = w

    def doMonths(self, frt, pag, r, c, p, i, w):
        months = w
        yr = int(self.curdt / 100)
        mt = self.curdt % 100
        for mth in range(months):
            mt -= 1
            if not mt:
                mt = 12
                yr -= 1
        self.startd = (yr * 10000) + mt * 100 + 1

    def doEnd(self):
        self.df.closeProcess()
        col = ["si1_invno"]
        dat = ["cancel"]
        whr = [("si1_cono", "=", self.opts["conum"])]
        if self.dtyp == "A":
            whr.append(("si1_rtn", "in", ("O", "Q", "W")))
        else:
            whr.append(("si1_rtn", "=", self.dtyp))
        whr.append(("si1_date", "<", self.startd))
        whr.append(("si1_invno", "=", ""))
        recs = self.sql.getRec("slsiv1", cols=["count(*)"], where=whr,
            limit=1)
        if recs[0]:
            self.sql.updRec("slsiv1", cols=col, data=dat, where=whr)
            mess = """%s Documents Will be Cancelled.

Would you like to COMMIT these Cancellations?""" % recs[0]
            self.opts["mf"].dbm.commitDbase(ask=True, mess=mess, default="no")
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
