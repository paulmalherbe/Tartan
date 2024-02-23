"""
SYNOPSIS
    Print Cancelled Sales Documnents

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

from TartanClasses import RepPrt, Sql, TartanDialog

class si3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["slsiv1", "drsmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.s_dte = int(self.opts["period"][1][0])
        self.e_dte = int(self.opts["period"][2][0])
        return True

    def mainProcess(self):
        r1s = (("Both", "B"), ("Invoices", "I"), ("Credit Notes", "C"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Document Type","",
                "B","Y",self.doType,None,None,None),
            (("T",0,1,0),"ID1",10,"From Date","",
                self.s_dte,"N",self.doDate,None,None,("notzero",)),
            (("T",0,2,0),"ID1",10,"To   Date","",
                self.e_dte,"N",self.doDate,None,None,("notzero",)))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doType(self, frt, pag, r, c, p, i, w):
        self.type = w
        if self.type == "C":
            self.dtyp = "Credit Notes"
        elif self.type == "I":
            self.dtyp = "Invoices"
        else:
            self.dtyp = "Documents"

    def doDate(self, frt, pag, r, c, p, i, w):
        if p == 1:
            self.sdte = w
        else:
            self.edte = w

    def doEnd(self):
        data = []
        self.df.closeProcess()
        hed = ["Cancelled Sales %s" % self.dtyp]
        tab = ["slsiv1", "drsmst"]
        col = ["si1_rtn", "si1_docno", "si1_date", "si1_acno",
            "drm_name", "si1_invno"]
        whr = [
            ("si1_cono", "=", self.opts["conum"]),
            ("si1_date", "between", self.sdte, self.edte),
            ("drm_cono=si1_cono",), ("drm_chain=si1_chain",),
            ("drm_acno=si1_acno",)]
        if self.type == "B":
            whr.append(("si1_rtn", "in", ("C", "I")))
        else:
            whr.append(("si1_rtn", "=", self.type))
        whr.append(("si1_invno", "=", "cancel"))
        odr = "si1_rtn, si1_docno"
        data = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        cols = []
        dics = self.sql.slsiv1_dic.copy()
        dics.update(self.sql.drsmst_dic)
        for c in col[:5]:
            cols.append((c, dics[c][2], dics[c][3], dics[c][5]))
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            ttype="D", heads=hed, cols=cols, repprt=self.df.repprt,
            repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
