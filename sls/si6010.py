"""
SYNOPSIS
    Sales Invoicing - Change Customer's Order Number

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2022 Paul Malherbe.

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

from TartanClasses import Sql, TartanDialog

class si6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsmst", "slsiv1"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        iv1 = {
            "stype": "R",
            "tables": ("drsmst", "slsiv1"),
            "cols": (
                ("si1_docno", "", 0, "Inv-Numbr"),
                ("si1_date", "", 0, "Invoice-Dt"),
                ("si1_chain", "", 0, "Chn"),
                ("si1_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name"),
                ("si1_cus_ord", "", 0, "Cust-Ord-Num")),
            "where": [
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_rtn", "=", "I"),
                ("si1_invno", "<>", "cancel"),
                ("drm_cono=si1_cono",),
                ("drm_chain=si1_chain",),
                ("drm_acno=si1_acno",)],
            "order": "si1_docno"}
        fld = (
            (("T",0,0,0),"IUI",9,"Invoice Number","",
                "","Y",self.doInvNum,iv1,None,("notzero",)),
            (("T",0,1,0),"O@si1_date",0,""),
            (("T",0,2,0),"O@si1_chain",0,""),
            (("T",0,3,0),"O@si1_acno",0,""),
            (("T",0,4,0),"O@drm_name",0,""),
            (("T",0,5,0),"I@si1_cus_ord",0,"","",
                "","N",self.doNewOrd,None,None,("efld",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doInvNum(self, frt, pag, r, c, p, i, w):
        whr = [
            ("si1_cono", "=", self.opts["conum"]),
            ("si1_rtn", "=", "I"),
            ("si1_docno", "=", w),
            ("drm_cono=si1_cono",),
            ("drm_chain=si1_chain",),
            ("drm_acno=si1_acno",)]
        acc = self.sql.getRec(tables=["slsiv1", "drsmst"], cols=["si1_date",
            "si1_chain", "si1_acno", "drm_name", "si1_cus_ord"], where=whr,
            limit=1)
        if not acc:
            return "Invalid Invoice Number"
        self.invno = w
        for n, a in enumerate(acc):
            self.df.loadEntry(frt, pag, p+1+n, data=a)

    def doNewOrd(self, frt, pag, r, c, p, i, w):
        self.ordno = w

    def doEnd(self):
        self.sql.updRec("slsiv1", cols=["si1_cus_ord"], data=[self.ordno],
            where=[("si1_cono", "=", self.opts["conum"]), ("si1_rtn", "=",
            "I"), ("si1_docno", "=", self.invno)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
