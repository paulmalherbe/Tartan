"""
SYNOPSIS
    Stores Location File Maintenance.

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

class stc410(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "strloc",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        if self.locs == "N":
            showError(self.opts["mf"].body, "Error",
                "Multiple Locations Are Not Enabled")
            return
        return True

    def mainProcess(self):
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"IUA",1,"Location Code","",
                "","N",self.doLoc,loc,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"INA",30,"Address Line 1","",
                "","N",None,None,None,None),
            (("T",0,3,0),"INA",30,"Address Line 2","",
                "","N",None,None,None,None),
            (("T",0,4,0),"INA",30,"Address Line 3","",
                "","N",None,None,None,None),
            (("T",0,5,0),"INA",30,"Address Line 4","",
                "","N",None,None,None,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doCloseProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doLoc(self, frt, pag, r, c, p, i, w):
        if w == "0":
            return "Invalid Location"
        self.loc = w
        self.acc = self.sql.getRec("strloc", where=[("srl_cono", "=",
            self.opts["conum"]), ("srl_loc", "=", self.loc)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            for x in range(1, self.df.topq[pag]):
                self.df.loadEntry(frt, pag, p+x, data=self.acc[x+1])

    def doDelete(self):
        self.sql.delRec("strloc", where=[("srl_cono", "=", self.opts["conum"]),
            ("srl_loc", "=", self.loc)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("strloc", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.strloc_col
            data.append(self.acc[col.index("srl_xflag")])
            self.sql.updRec("strloc", data=data, where=[("srl_cono",
                "=", self.opts["conum"]), ("srl_loc", "=", self.loc)])
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

    def doCloseProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
