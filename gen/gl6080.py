"""
SYNOPSIS
    General Ledger - List Missing Account Numbers i.e.
    Accounts that have Transactions but no Masterfile.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2021 Paul Malherbe.

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

from TartanClasses import ProgressBar, RepPrt, Sql, TartanDialog
from tartanFunctions import getSingleRecords

class gl6080:
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genmst", "gentrn"],
            prog=__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        ctm = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name")),
            "order": "ctm_cono",
            "index": 0}
        r1s = (("All", "A"), ("Range", "R"), ("Selection", "S"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Company","",
                "A","Y",self.doCoySel,None,None,None),
            (("T",0,1,0),"IUI",3,"From Company","",
                "","N",self.doCoyNo,ctm,None,("notzero",)),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),"IUI",3,"To   Company","",
                "","N",self.doCoyNo,ctm,None,("notzero",)),
            (("T",0,2,0),"ONA",30,""))
        but = (("Exit", None, self.doExit, 0, ("T",0,1), ("T",0,0)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, eflds=fld,
            butt=but, tend=tnd, txit=txt, view=("Y", "V"))

    def doCoySel(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.coys = []
            for coy in self.sql.getRec("ctlmst", cols=["ctm_cono"],
                    order="ctm_cono"):
                self.coys.append(coy[0])
            return "sk4"
        elif w == "S":
            self.coys = []
            coys = getSingleRecords(self.opts["mf"], "ctlmst",
                ("ctm_cono", "ctm_name"))
            for coy in coys:
                self.coys.append(coy[0])
            if not self.coys:
                return "No Company Selected"
            return "sk4"

    def doCoyNo(self, frt, pag, r, c, p, i, w):
        nam = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)], limit=1)
        if not nam:
            return "Invalid Company"
        self.df.loadEntry(frt, pag, p+1, data=nam[0])
        if p == 1:
            self.fcoy = w
        elif w < self.fcoy:
            return "Invalid Selection"
        else:
            self.tcoy = w
            self.coys = []
            coys = self.sql.getRec("ctlmst", cols=["ctm_cono"],
                where=[("ctm_cono", "between", self.fcoy, self.tcoy)],
                order="ctm_cono")
            for coy in coys:
                self.coys.append(coy[0])

    def doEnd(self):
        self.df.closeProcess()
        pb = ProgressBar(self.opts["mf"].body, mxs=len(self.coys), esc=True)
        miss = {}
        for num, coy in enumerate(self.coys):
            pb.displayProgress(num)
            nam = self.sql.getRec("ctlmst", cols=["ctm_name"],
                where=[("ctm_cono", "=", coy)], limit=1)
            accs = self.sql.getRec("gentrn", cols=["glt_acno"],
                where=[("glt_cono", "=", coy)], group="glt_acno",
                order="glt_acno")
            for acc in accs:
                glm = self.sql.getRec("genmst", where=[("glm_cono",
                    "=", coy), ("glm_acno", "=", acc[0])], limit=1)
                if not glm:
                    if coy not in miss:
                        miss[coy] = []
                    miss[coy].append((nam[0], acc[0]))
        pb.closeProgress()
        keys = list(miss.keys())
        keys.sort()
        data = []
        for k in keys:
            for a in miss[k]:
                data.append((k, a[0], a[1]))
        if data:
            head = ["Missing Account Numbers"]
            cols = [
                ("a", "NA", 3, "Coy", "y"),
                ("b", "NA", 30, "Name", "y"),
                ("c", "UI", 7, "Acc-Num", "y")]
            RepPrt(self.opts["mf"], name="gl6080", tables=data, heads=head,
                cols=cols, repprt=self.df.repprt, ttype="D")
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
