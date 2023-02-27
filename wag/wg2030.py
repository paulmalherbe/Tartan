"""
SYNOPSIS
    Employee Terminations.

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

from TartanClasses import Sql, TartanDialog

class wg2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "wagmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        wgm = {
            "stype": "R",
            "tables": ("wagmst",),
            "cols": (
                ("wgm_empno", "", 0, "EmpNo"),
                ("wgm_sname", "", 0, "Surname"),
                ("wgm_fname", "", 0, "Names"),
                ("wgm_start", "", 0, "Start-Date"),
                ("wgm_term", "", 0, "Term-Date")),
            "where": [
                ("wgm_cono", "=", self.opts["conum"]),
                ("wgm_term", "=", 0)]}
        fld = (
            (("T",0,0,0),"I@wgm_empno",7,"","",
                "","Y",self.doEmpNo,wgm,None,None),
            (("T",0,1,0),"O@wgm_sname",0,"","","","N",None,None,None,None),
            (("T",0,2,0),"O@wgm_fname",0,"","","","N",None,None,None,None),
            (("T",0,3,0),"ID1",10,"Termination Date","",
                "","N",self.doTermDate,None,None,("efld",)))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doEmpNo(self, frt, pag, r, c, p, i, w):
        self.emp = self.sql.getRec("wagmst", cols=["wgm_sname",
            "wgm_fname", "wgm_start", "wgm_term"], where=[("wgm_cono", "=",
            self.opts["conum"]), ("wgm_empno", "=", w)], limit=1)
        if not self.emp:
            return "Invalid Employee"
        if self.emp[3]:
            return "Employment Already Terminated"
        self.empno = w
        self.df.loadEntry(frt, pag, 1, data=self.emp[0])
        self.df.loadEntry(frt, pag, 2, data=self.emp[1])

    def doTermDate(self, frt, pag, r, c, p, i, w):
        if w <= self.emp[2]:
            return "Invalid Termination Date"
        self.term = w

    def doEnd(self):
        self.sql.updRec("wagmst", cols=["wgm_term"], data=[self.term],
            where=[("wgm_cono", "=", self.opts["conum"]), ("wgm_empno", "=",
            self.empno)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
