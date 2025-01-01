"""
SYNOPSIS
    Rental System Premises Maintenance.

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

import time
from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import copyList

class rtc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "genmst", "rtlprm",
            "rtlmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        self.glint = rtlctl["ctr_glint"]
        return True

    def mainProcess(self):
        prm = {
            "stype": "R",
            "tables": ("rtlprm",),
            "cols": (
                ("rtp_code", "", 0, "Prm-Code"),
                ("rtp_desc", "", 0, "Description", "Y")),
            "where": [("rtp_cono", "=", self.opts["conum"])]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])],
            "order": "glm_acno"}
        self.fld = [
            (("T",0,0,0),"INA",7,"Premises Code","Premises",
                "","N",self.doPrmCod,prm,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"INA",4,"Postal Code","PCod",
                "","N",None,None,None,("notblank",))]
        if self.glint == "Y":
            self.fld.append((("T",0,6,0),"IUI",7,"Rental Account","",
                "","N",self.doRental,glm,None,("notzero",),None,
                "Rental Control Account in the General Ledger."))
            self.fld.append((("T",0,6,0),"ONA",30,""))
            self.fld.append((("T",0,7,0),"IUI",7,"Income Account","",
                "","N",self.doIncome,glm,None,("notzero",), None,
                "Rental Income Account in the General Ledger."))
            self.fld.append((("T",0,7,0),"ONA",30,""))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doPrmCod(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.old = self.sql.getRec("rtlprm", where=[("rtp_cono", "=",
            self.opts["conum"]), ("rtp_code", "=", self.code)], limit=1)
        if not self.old:
            self.new = "y"
        else:
            self.new = "n"
            acc = copyList(self.old[:-1])
            acc.append("")
            acc.insert(8, "")
            for x in range(0, self.df.topq[pag]):
                self.df.loadEntry(frt, pag, p+x, data=acc[x+1])
            if self.glint == "N":
                return
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                acc[7])], limit=1)
            if des:
                self.df.loadEntry("T", 0, 7, data=des[0])
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
                acc[9])], limit=1)
            if des:
                self.df.loadEntry("T", 0, 9, data=des[0])

    def doRental(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry("T", 0, 7, data=acc[0])

    def doIncome(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry("T", 0, 9, data=acc[0])

    def doDelete(self):
        mst = self.sql.getRec("rtlmst", cols=["count(*)"],
            where=[("rtm_cono", "=", self.opts["conum"]), ("rtm_code", "=",
            self.code)], limit=1)
        if mst[0]:
            return "Accounts Exist, Not Deleted"
        self.sql.delRec("rtlprm", where=[("rtp_cono", "=", self.opts["conum"]),
            ("rtp_code", "=", self.code)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rtlprm", "D", "%03i%-7s" %
            (self.opts["conum"], self.code), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if self.glint == "Y" and x in (7, 9):
                continue
            data.append(self.df.t_work[0][0][x])
        if self.glint == "N":
            data.extend([0, 0])
        if self.new == "y":
            self.sql.insRec("rtlprm", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.rtlprm_col
            data.append(self.old[col.index("rtp_xflag")])
            self.sql.updRec("rtlprm", data=data, where=[("rtp_cono", "=",
                self.opts["conum"]), ("rtp_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["rtlprm",
                    "U", "%03i%-7s" % (self.opts["conum"], self.code),
                    col[num], dte, self.opts["capnm"], str(dat),
                    str(data[num]), "", 0])
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
