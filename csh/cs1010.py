"""
SYNOPSIS
    Cash Takings Accounts Maintenance.

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

import time
from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import showError

class cs1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        cshctl = gc.getCtl("cshctl", self.opts["conum"])
        if not cshctl:
            return
        glint = cshctl["ccc_glint"]
        if glint == "Y":
            showError(self.opts["mf"].window, "Error",
                "Cash Analysis is Integrated with General Ledger.")
            return
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
        self.mods = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            self.mods.append(ctlmst["ctm_modules"][x:x+2])
        tabs = ["ctlvmf", "cshmst", "genbal", "genbud",
                "genrpt", "gentrn", "chglog"]
        if "CR" in self.mods:
            tabs.append("crsctl")
        if "DR" in self.mods:
            tabs.append("drsctl")
        if "ST" in self.mods:
            tabs.extend(["strctl", "strloc"])
        if "SI" in self.mods:
            tabs.append("slsctl")
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("cshmst", cols=["count(*)"],
            where=[("ccm_cono", "=", self.opts["conum"])], limit=1)
        if chk[0]:
            self.newgen = False
        else:
            self.newgen = True
        if "args" in self.opts:
            self.acno = None
        return True

    def mainProcess(self):
        glm = {
            "stype": "R",
            "tables": ("cshmst",),
            "cols": (
                ("ccm_acno", "", 0, "Acc-Num"),
                ("ccm_desc", "", 0, "Description", "Y")),
            "where": [("ccm_cono", "=", self.opts["conum"])]}
        vat = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "Acc-Num"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "","Y",self.doAccNum,glm,None,("notzero",)),
            (("T",0,1,0),"INA",30,"Description","Account Description",
                "","N",None,None,None,("notblank",)),
            (("T",0,2,0),"IUA",1,"Tax Default","",
                self.taxdf,"N",self.doVatCod,vat,None,("notblank",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),(("T",0,0),("T",0,1))),
            ("Cancel",None,self.doCancel,0,("T",0,2),(("T",0,0),("T",0,1))),
            ("Quit",None,self.doQuit,1,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doQuit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doAccNum(self, frt, pag, r, c, p, i, w):
        self.acno = w
        self.old = self.sql.getRec("cshmst", where=[("ccm_cono", "=",
            self.opts["conum"]), ("ccm_acno", "=", self.acno)], limit=1)
        if not self.old:
            self.new = True
        elif "args" in self.opts:
            showError(self.opts["mf"].body, "Error",
                "Only a New Account is Allowed")
            return "rf"
        else:
            self.new = False
            for x in range(0, self.df.topq[pag]):
                self.df.loadEntry(frt, pag, p+x, data=self.old[x+1])

    def doTypCod(self, frt, pag, r, c, p, i, w):
        if self.new:
            if w == "P":
                self.df.topf[pag][4][5] = self.taxdf
            else:
                self.df.topf[pag][4][5] = "N"
        elif not self.df.topf[pag][4][5]:
            self.df.topf[pag][4][5] = "N"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"], where=[("vtm_cono",
            "=", self.opts["conum"]), ("vtm_code", "=", w)], limit=1)
        if not acc:
            return "Invalid VAT Code"

    def doDelete(self):
        t = self.sql.getRec("cshana", cols=["count(*)"], where=[("can_cono",
            "=", self.opts["conum"]), ("can_code", "=", self.acno)], limit=1)
        if t[0]:
            return "Transactions Exist, Not Deleted"
        self.sql.delRec("cshmst", where=[("ccm_cono", "=", self.opts["conum"]),
            ("ccm_code", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["cshmst", "D", "%03i%07i" %
            (self.opts["conum"], self.acno), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        if self.newgen:
            self.df.butt[1][4] = None
            self.df.butt[1][5] = None
        data = [self.opts["conum"], self.acno,
            self.df.t_work[0][0][1], self.df.t_work[0][0][2]]
        if self.new:
            self.sql.insRec("cshmst", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.cshmst_col
            data.append(self.old[col.index("ccm_xflag")])
            self.sql.updRec("cshmst", data=data, where=[("ccm_cono", "=",
                self.opts["conum"]), ("ccm_acno", "=", self.acno)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["cshmst", "U",
                        "%03i%07i" % (self.opts["conum"], self.acno),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        if "args" in self.opts:
            self.doQuit()
        else:
            self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.last[0] = [0, 0]
        self.df.focusField("T", 0, 1)

    def doIgExit(self):
        self.igexit = True
        self.ig.closeProcess()

    def doQuit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
