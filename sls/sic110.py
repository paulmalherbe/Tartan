"""
SYNOPSIS
    Sales Invoicing Control File Maintenance.

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

import time
from TartanClasses import Sql, TartanDialog

class sic110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["slsctl", "tplmst", "chglog"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.acc = self.sql.getRec("slsctl", where=[("ctv_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "Y", "Y", "sales_document", "", ""]
        else:
            self.new = False
        return True

    def drawDialog(self):
        tpl = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "where": [
                ("tpm_type", "=", "I"),
                ("tpm_system", "=", "INV")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        self.fld = (
            (("T",0,0,0),("IRB",r1s),0,"Delivery Notes","",
                self.acc[1],"N",self.doDelNo,None,None,None,None,
                "Generate Delivery Notes as well as the Sales Document"),
            (("T",0,1,0),("IRB",r1s),0,"Print Values","",
                self.acc[2],"N",None,None,None,None,None,
                "Whether to Print Values on the Delivery Note."),
            (("T",0,2,0),"INA",20,"Invoice Template","",
                self.acc[3],"N",self.doTplNam,tpl,None,None),
            (("T",0,3,0),"ITX",50,"Email Address","",
                self.acc[4],"N",None,None,None,("email",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,1),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)
        if not self.new:
            for n, f in enumerate(self.acc[1:-1]):
                self.df.loadEntry("T", 0, n, data=f)

    def doDelNo(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "INV")], limit=1)
        if not acc:
            return "Invalid Template Name"

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new:
            self.sql.insRec("slsctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.slsctl_col
            data.append(self.acc[col.index("ctv_xflag")])
            self.sql.updRec("slsctl", data=data, where=[("ctv_cono", "=",
                self.opts["conum"])])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["slsctl", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.doExit()

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
