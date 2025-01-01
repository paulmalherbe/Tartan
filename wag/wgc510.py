"""
SYNOPSIS
    Salaries & Wages PAYE, UIF and SDL Tables.

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

from TartanClasses import GetCtl, Sql, TartanDialog

class wgc510(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagtxa", "wagtxr"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", 1)
        if not wagctl:
            return
        self.fr = self.to = self.tx = self.rt = 0
        return True

    def mainProcess(self):
        tyr = {
            "stype": "R",
            "tables": ("wagtxa",),
            "cols": (("wta_year", "", 0, "Year"),)}
        fld = (
            (("T",0,0,0),"IUI",4,"Tax Year","",
                0,"Y",self.doYear,tyr,None,("notzero",)),
            (("T",0,1,0),"IUI",7,"Rebate - Primary","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,2,0),"IUI",7,"Rebate - 65 and Older","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,3,0),"IUI",7,"Rebate - 75 and Older","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,4,0),"IUI",7,"Gratuity Exemption","",
                0,"N",None,None,None,("efld",)),
            (("T",0,5,0),"IUI",7,"SITE Limit","",
                0,"N",None,None,None,("efld",)),
            (("T",0,6,0),"IUD",5.2,"UIF Rates - Employee","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,6,0),"IUD",5.2,"Employer","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,7,0),"IUD",5.2,"SDL Rates - Employee","",
                0,"N",None,None,None,("efld",)),
            (("T",0,7,0),"IUD",5.2,"Employer","",
                0,"N",None,None,None,("notzero",)),
            (("C",0,0,0),"IUI",12,"Inc-Fr","",
                0,"N",self.doIncome,None,None,("efld",)),
            (("C",0,0,1),"IUI",12,"Inc-To","",
                0,"N",self.doIncome,None,None,("efld",)),
            (("C",0,0,2),"IUI",12,"Tax-Amt","",
                0,"N",self.doIncome,None,None,("efld",)),
            (("C",0,0,3),"IUD",7.2,"Rate","",
                0,"N",self.doIncome,None,None,("efld",)))
        row = (10,)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"y"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, rows=row,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doYear(self, frt, pag, r, c, p, i, w):
        txa = self.sql.getRec("wagtxa", where=[("wta_year", "=", w)],
            limit=1)
        if not txa:
            self.new = True
        else:
            txr = self.sql.getRec("wagtxr",
                where=[("wtr_year", "=", w)],
                order="wtr_from")
            if not txr:
                return "ERROR, Missing wagtxr File"
            self.new = False
            for n, d in enumerate(txa):
                self.df.loadEntry("T", 0, n, data=d)
            for n, t in enumerate(txr):
                for x, d in enumerate(t[1:]):
                    self.df.loadEntry("C", 0, (n*4)+x, data=d)

    def doIncome(self, frt, pag, r, c, p, i, w):
        if i == 0:
            if p == 0 and w:
                return "Invalid From Income, Should be Zero"
            if p > 0 and w != (self.to + 1):
                return "Invalid To Income, Should Be %s" % (self.to + 1)
            self.fr = w
        elif i == 1:
            if w <= self.fr:
                return "Invalid To Income, Less Than From"
            self.to = w
        elif i == 2:
            if p != 2 and w <= self.tx:
                return "Invalid Tax, Less Than Previous"
            self.tx = w
        else:
            if p != 3 and w <= self.rt:
                return "Invalid Rate, Less Than Previous"
            self.rt = w

    def doEnd(self):
        if self.df.frt == "T":
            self.fr = 0
            self.df.loadEntry("C", 0, 0, data=self.fr)
            self.df.focusField("C", 0, 2)
        elif self.df.row != 9:
            if self.to == 9999999:
                self.doExit()
            else:
                self.df.advanceLine(0)
                self.fr = self.to + 1
                self.df.loadEntry("C", 0, self.df.pos, data=self.fr)
                self.df.focusField("C", 0, self.df.col + 1)
        else:
            self.doExit()

    def doExit(self):
        if self.df.frt == "C":
            reb = []
            for d in self.df.t_work[0][0]:
                reb.append(d)
            if not self.new:
                self.sql.delRec("wagtxa", where=[("wta_year", "=", reb[0])])
                self.sql.delRec("wagtxr", where=[("wtr_year", "=", reb[0])])
            self.sql.insRec("wagtxa", data=reb)
            for d in self.df.c_work[0]:
                rte = [reb[0]]
                for c in d:
                    rte.append(c)
                self.sql.insRec("wagtxr", data=rte)
                if d[1] == 9999999:
                    break
            self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
