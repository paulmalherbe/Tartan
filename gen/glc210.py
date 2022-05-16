"""
SYNOPSIS
    General Ledger Intercompany Records Maintenance.

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
from tartanFunctions import showInfo

class glc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genmst", "genint"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if chk[0] == 1:
            showInfo(self.opts["mf"].body, "Intercompany",
                "There is Only 1 Company Record")
            return
        return True

    def mainProcess(self):
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy-Num"),
                ("ctm_name", "", 0, "Name", "Y")),
            "where": [("ctm_cono", "!=", self.opts["conum"])]}
        gl1 = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        gl2 = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "whera": [["T", "glm_cono", 0, 0]]}
        data = self.sql.getRec(tables=["genint", "genmst"], cols=["cti_inco",
            "glm_desc"], where=[("cti_cono", "=", self.opts["conum"]),
            ("glm_cono=cti_cono",), ("glm_acno=cti_acno",)], order="cti_inco")
        self.gl3 = {
            "stype": "C",
            "titl": "Existing Companies",
            "head": ("Coy","Name"),
            "typs": (("UI", 3), ("NA", 30)),
            "data": data}
        fld = (
            (("T",0,0,0,14),"IUI",3,"Coy-Num","Company Number",
                "","Y",self.doCoyNum,coy,None,None),
            (("T",0,0,17),"ONA",30,""),
            (("T",0,1,0,10),"IUI",7,"Acc-Num-1","G/L Account Number",
                "","N",self.doAccNum1,gl1,self.doDelete,("notzero",),None,
                "The above company's account number in company %s." %
                self.opts["conum"]),
            (("T",0,1,17),"ONA",30,""),
            (("T",0,2,0,10),"IUI",7,"Acc-Num-2","G/L Account Number",
                "","N",self.doAccNum2,gl2,None,("notzero",),None,
                "Company %s's account number in the above company." %
                self.opts["conum"]),
            (("T",0,2,17),"ONA",30,""))
        but = (
            ("Show All",self.gl3,None,0,("T",0,1),("T",0,2)),
            ("Cancel",None,self.doCancel,0,("T",0,3),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        if w == 0:
            return "Invalid Company Number"
        if w == self.opts["conum"]:
            return "Invalid Company, Same Company Not Allowed"
        self.cono2 = w
        acc = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", self.cono2)], limit=1)
        if not acc:
            return "Invalid Company Number"
        self.df.loadEntry(frt, pag, 1, data=acc[0])
        self.acc1 = self.sql.getRec("genint", where=[("cti_cono",
            "=", self.opts["conum"]), ("cti_inco", "=", self.cono2)], limit=1)
        if not self.acc1:
            self.new1 = "y"
        else:
            self.new1 = "n"
            self.acno1 = self.acc1[self.sql.genint_col.index("cti_acno")]
            desc = self.readAcno(self.opts["conum"], self.acno1)
            self.df.loadEntry(frt, pag, 2, data=self.acno1)
            self.df.loadEntry(frt, pag, 3, data=desc[0])
        self.acc2 = self.sql.getRec("genint", where=[("cti_cono",
            "=", self.cono2), ("cti_inco", "=", self.opts["conum"])], limit=1)
        if not self.acc2:
            self.new2 = "y"
        else:
            self.new2 = "n"
            self.acno2 = self.acc2[self.sql.genint_col.index("cti_acno")]
            desc = self.readAcno(self.cono2, self.acno2)
            self.df.loadEntry(frt, pag, 4, data=self.acno2)
            self.df.loadEntry(frt, pag, 5, data=desc[0])

    def doDelete(self):
        if self.new1 == "n":
            self.sql.delRec("genint", where=[("cti_cono", "=",
                self.opts["conum"]), ("cti_inco", "=", self.cono2)])
        if self.new2 == "n":
            self.sql.delRec("genint", where=[("cti_cono", "=", self.cono2),
                ("cti_inco", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccNum1(self, frt, pag, r, c, p, i, w):
        desc = self.readAcno(self.opts["conum"], w)
        if not desc:
            return "Invalid Account Number"
        self.acno1 = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])

    def doAccNum2(self, frt, pag, r, c, p, i, w):
        desc = self.readAcno(self.cono2, w)
        if not desc:
            return "Invalid Account Number"
        self.acno2 = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])

    def readAcno(self, cono, acno):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", cono), ("glm_acno", "=", acno)], limit=1)
        return acc

    def doEnd(self):
        data1 = [self.opts["conum"], self.cono2, self.acno1]
        data2 = [self.cono2, self.opts["conum"], self.acno2]
        if self.new1 == "y":
            self.sql.insRec("genint", data=data1)
        elif data1 != self.acc1[:len(data1)]:
            col = self.sql.genint_col
            data1.append(self.acc1[col.index("cti_xflag")])
            self.sql.updRec("genint", data=data1, where=[("cti_cono", "=",
                self.opts["conum"]), ("cti_inco", "=", self.cono2)])
        if self.new2 == "y":
            self.sql.insRec("genint", data=data2)
        elif data2 != self.acc2[:len(data2)]:
            col = self.sql.genint_col
            data2.append(self.acc2[col.index("cti_xflag")])
            self.sql.updRec("genint", data=data2, where=[("cti_cono", "=",
                self.cono2), ("cti_inco", "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase()
        data = self.sql.getRec(tables=["genint", "genmst"], cols=["cti_cono",
            "glm_desc"], where=[("cti_cono", "=", self.opts["conum"]),
            ("glm_cono=cti_inco",)], order="cti_inco")
        self.gl3["data"] = data
        self.df.focusField("T", 0, 1)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
