"""
SYNOPSIS
    Financial Loan Calculator.

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

from TartanClasses import TartanDialog

class fc1010(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        pass

    def mainProcess(self):
        tit = ("Loans and Leases",)
        fld = (
            (("T",0,0,0),"ISD",14.2,"Capital Amount","",
                "","Y",self.doCap,None,None,("efld",)),
            (("T",0,1,0),"ISD",14.2,"Residual Value","",
                "","N",None,None,None,("efld",)),
            (("T",0,2,0),"ISI",14.2,"Number of Months","",
                "","N",None,None,None,("notzero",)),
            (("T",0,3,0),"ISD",14.2,"Repay Amount","",
                "","N",self.doRep,None,None,("efld",)),
            (("T",0,4,0),"ISD",14.4,"Interest Rate","",
                "","N",self.doInt,None,None,("efld",)))
        tnd = ((self.doEnd, "y"), )
        txt = (self.doExit, )
        but = (
            ("New", None, self.doMore, 1, None, None),
            ("Quit", None, self.doExit, 1, None, None))
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt, butt=but)

    def doCap(self, frt, pag, r, c, p, i, w):
        self.cap = w

    def doRep(self, frt, pag, r, c, p, i, w):
        if self.cap and w != 0:
            return "nd"

    def doInt(self, frt, pag, r, c, p, i, w):
        if not self.cap and not w:
            return "Invalid Rate"

    def doEnd(self):
        cap, res, mth, rep, rte = self.df.t_work[0][0]
        if not cap and mth and rep and rte:
            self.doCapital(res, mth, rep, rte)
        elif rep:
            self.doRate(cap, res, mth, rep)
        else:
            self.doRepay(cap, res, mth, rte)

    def doMore(self):
        self.df.setWidget(self.df.topEntry[0][3], state="normal")
        self.df.setWidget(self.df.topEntry[0][4], state="normal")
        self.df.setWidget(self.df.B0, "normal")
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doCapital(self, res, mth, rep, rte):
        cap = 100.0
        rate = (rte / 1200.0)
        while round((((cap * rate) * ((1 + rate) ** mth)) - (res * rate)) /
                (((1 + rate) ** mth) - 1), 2) < rep:
            cap += 100
        self.df.loadEntry("T", 0, 0, data=round(cap, 2))
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def doRepay(self, cap, res, mth, rte):
        rate = (rte / 1200.0)
        rep = round((((cap * rate) * ((1 + rate) ** mth)) - (res * rate)) /
            (((1 + rate) ** mth) - 1), 2)
        self.df.loadEntry("T", 0, 3, data=round(rep, 2))
        self.df.setWidget(self.df.topEntry[0][3], state="disabled")

    def doRate(self, cap, res, mth, rep):
        rte = 0.0000
        pay = 0.0
        while pay < rep:
            rte += .0001
            rate = (rte / 1200.0)
            pay = round((((cap * rate) * ((1 + rate) ** mth)) - (res * rate)) /
                (((1 + rate) ** mth) - 1), 2)
        self.df.loadEntry("T", 0, 4, data=round(rte, 4))
        self.df.setWidget(self.df.topEntry[0][4], state="disabled")

# vim:set ts=4 sw=4 sts=4 expandtab:
