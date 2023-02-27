"""
SYNOPSIS
    League Format Maintenance.

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

from TartanClasses import TartanDialog, Sql
from tartanFunctions import getNextCode

class bc1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlflf", "bwlflm", "bwlflo",
            "bwlfls", "bwlflt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        typ = {
            "stype": "R",
            "tables": ("bwlflf",),
            "cols": (
                ("bff_code", "", 0, "Cod"),
                ("bff_desc", "", 0, "Description", "Y")),
            "where": [("bff_cono", "=", self.opts["conum"])]}
        fle = {
            "stype":  "F",
            "types":  "fle",
            "ftype":  (("JPG Files", "*.jpg"),)}
        r1s = (("Male", "M"), ("Female", "F"), ("Mixed", "B"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("One", "1"), ("Four", "4"))
        fld = (
            (("T",0,0,0),"I@bff_code",0,"","",
                0,"Y",self.doTypCod,typ,None,("efld",)),
            (("T",0,1,0),"I@bff_desc",0,"","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),("IRB",r1s),0,"Gender","",
                "M","N",None,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Assessment Forms","",
                "N","N",self.doAssess,None,None,None),
            (("T",0,4,0),("IRB",r3s),0,"Number of Forms","",
                "1","N",self.doForms,None,None,None),
            (("T",0,5,0),("IRB",r2s),0,"Assess Self","",
                "Y","N",None,None,None,None),
            (("T",0,6,0),"I@bff_rate",0,"","",
                10,"N",None,None,None,("notzero",)),
            (("T",0,7,0),("IRB",r2s),0,"Sets Format","",
                "N","N",None,None,self.doDelete,None),
            (("T",0,8,0),"I@bff_logo",0,"","",
                "","N",self.doLogo,fle,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt)

    def doTypCod(self, frt, pag, r, c, p, i, w):
        if not w:
            self.code = getNextCode(self.sql, "bwlflf", "bff_code",
                where=[("bff_cono", "=", self.opts["conum"])], last=9)
            self.df.loadEntry(frt, pag, p, data=self.code)
        else:
            self.code = w
        self.old = self.sql.getRec("bwlflf", where=[("bff_cono", "=",
            self.opts["conum"]), ("bff_code", "=", self.code)], limit=1)
        if not self.old:
            self.newtyp = True
        else:
            self.newtyp = False
            idx = self.sql.bwlflf_col.index("bff_forms")
            for num, fld in enumerate(self.old[1:-1]):
                if num == idx:
                    self.df.loadEntry(frt, pag, num, data=str(fld))
                else:
                    self.df.loadEntry(frt, pag, num, data=fld)

    def doDelete(self):
        if self.newtyp:
            return
        error = False
        for tab in (("bwlflm", "bfm_cono", "bfm_fmat"),
                    ("bwlflo", "bfo_cono", "bfo_fmat"),
                    ("bwlfls", "bfs_cono", "bfs_fmat"),
                    ("bwlflt", "bft_cono", "bft_fmat")):
            chk = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                self.opts["conum"]), (tab[2], "=", self.code)], limit=1)
            if chk:
                error = True
                break
        if error:
            return "There are Movements for this Format, Not Deleted"
        self.sql.delRec("bwlflf", where=[("bff_cono", "=", self.opts["conum"]),
            ("bff_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()

    def doAssess(self, frt, pag, r, c, p, i, w):
        self.assess = w
        if self.assess == "N":
            self.df.loadEntry(frt, pag, p+1, data="4")
            self.df.loadEntry(frt, pag, p+2, data="N")
            self.df.loadEntry(frt, pag, p+3, data=0)
            self.df.loadEntry(frt, pag, p+4, data="N")
            return "sk4"

    def doForms(self, frt, pag, r, c, p, i, w):
        if w == "1":
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doLogo(self, frt, pag, r, c, p, i, w):
        self.logo = w

    def doEnd(self):
        data = [self.opts["conum"]] + self.df.t_work[0][0]
        idx = self.sql.bwlflf_col.index("bff_forms")
        data[idx] = int(data[idx])
        if self.newtyp:
            self.sql.insRec("bwlflf", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bwlflf_col
            data.append(self.old[col.index("bff_xflag")])
            self.sql.updRec("bwlflf", data=data, where=[("bff_cono", "=",
                self.opts["conum"]), ("bff_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
