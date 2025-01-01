"""
SYNOPSIS
    Debtors Chainstores File Maintenance.

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
from tartanFunctions import showError

class drc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        if drsctl["ctd_chain"] == "N":
            showError(self.opts["mf"].body, "Error",
                "Chain Stores are Not Enabled")
            return
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "drschn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        chm = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Chn"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"IUI",3,"Chn","Chainstore Number",
                "","N",self.doChain,chm,None,("notzero",)),
            (("T",0,1,0),"INA",30,"Name","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"INA",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"INA",20,"Telephone","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"INA",20,"Fax","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",0,9,0),"INA",30,"Contact","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"IUA",1,"Vat Code","",
                "","N",self.doVat,vtm,None,("notblank",)),
            (("T",0,10,0),"ONA",30,""))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doChain(self, frt, pag, r, c, p, i, w):
        self.chain = w
        self.acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
            self.opts["conum"]), ("chm_chain", "=", self.chain)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
                where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
                self.acc[self.sql.drschn_col.index("chm_vatind")])], limit=1)
            if not vat:
                txt = "Invalid Vat Record"
            else:
                txt = vat[0]
            for x in range(0, self.df.topq[pag]):
                if x == (self.df.topq[pag] - 1):
                    self.df.loadEntry(frt, pag, p+x, data=txt)
                else:
                    self.df.loadEntry(frt, pag, p+x, data=self.acc[x+1])

    def doVat(self, frt, pag, r, c, p, i, w):
        vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            w)], limit=1)
        if not vat:
            return "Invalid Vat Record"
        self.df.loadEntry(frt, pag, p+1, data=vat[0])

    def doDelete(self):
        self.sql.delRec("drschn", where=[("chm_cono", "=", self.opts["conum"]),
            ("chm_chain", "=", self.chain)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        dat = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if x == 11:
                continue
            dat.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("drschn", data=dat)
        elif dat != self.acc[:len(dat)]:
            col = self.sql.drschn_col
            dat.append(self.acc[col.index("chm_xflag")])
            self.sql.updRec("drschn", data=dat, where=[("chm_cono", "=",
            self.opts["conum"]), ("chm_chain", "=", self.chain)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
