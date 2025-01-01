"""
SYNOPSIS
    Book Club Member's Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import getNextCode

class bsc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bksown"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        clb = {
            "stype": "R",
            "tables": ("bksown",),
            "cols": (
                ("bof_code", "", 0, "Cod"),
                ("bof_snam", "", 0, "Surname", "Y"),
                ("bof_fnam", "", 0, "Names")),
            "where": [("bof_cono", "=", self.opts["conum"])],
            "order": "bof_snam"}
        r1s = (("Current","C"), ("Resigned","R"))
        fld = (
            (("T",0,0,0),"I@bof_code",0,"","",
                "","Y",self.doCode,clb,None,("efld",)),
            (("T",0,1,0),"I@bof_snam",0,"","",
                "","N",self.doSnam,None,None,("notblank",)),
            (("T",0,2,0),"I@bof_fnam",0,"","",
                "","N",self.doFnam,None,None,("efld",)),
            (("T",0,3,0),"I@bof_add1",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"I@bof_add2",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"I@bof_add3",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"I@bof_pcod",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"I@bof_home",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"I@bof_work",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"I@bof_cell",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"I@bof_mail",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,11,0),("IRB",r1s),0,"Membersip Status","",
                "C","N",None,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        if not w:
            self.owner = getNextCode(self.sql, "bksown", "bof_code", last=999)
            self.df.loadEntry(frt, pag, p, data=self.owner)
        else:
            self.owner = w
        self.old = self.sql.getRec("bksown", where=[("bof_cono", "=",
            self.opts["conum"]), ("bof_code", "=", self.owner)], limit=1)
        if not self.old:
            self.newown = True
        else:
            self.newown = False
            for num, fld in enumerate(self.old[1:-1]):
                self.df.loadEntry(frt, pag, num, data=fld)

    def doSnam(self, frt, pag, r, c, p, i, w):
        self.snam = w

    def doFnam(self, frt, pag, r, c, p, i, w):
        if self.newown:
            chk = self.sql.getRec("bksown", where=[("bof_cono", "=",
                self.opts["conum"]), ("bof_snam", "=", self.snam),
                ("bof_fnam", "=", w)], limit=1)
            if chk:
                return "A Member with this Name Already Exists"

    def doEnd(self):
        data = [self.opts["conum"]] + self.df.t_work[0][0]
        if self.newown:
            self.sql.insRec("bksown", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bksown_col
            data.append(self.old[col.index("bof_xflag")])
            self.sql.updRec("bksown", data=data, where=[("bof_cono", "=",
                self.opts["conum"]), ("bof_code", "=", self.owner)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
