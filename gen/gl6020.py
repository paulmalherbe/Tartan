"""
SYNOPSIS
    General Ledger Copy Accounts From One Company to Another.

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

from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import callModule, getPeriods, showError

class gl6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlctl", "ctlmst", "ctlynd",
            "genbud", "genbal", "gendtm", "gendtt", "genjlm", "genjlt",
            "genmst", "gentrn", "genrpt", "genstr"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("gentrn", where=[("glt_cono", "=",
            self.opts["conum"])])
        if chk:
            showError(self.opts["mf"].body, "Import Error",
                "General Ledger Transactions Exist.")
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
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IUI",3,"Copy From Company","",
                0,"N",self.doCoyNum,coy,None,("notzero",)),
            (("T",0,1,0),("IRB",r1s),1,"Include Control Records","",
                "N","N",None,None,None,None),
            (("T",0,2,0),("IRB",r1s),1,"Include Opening Balances","",
                "N","N",None,None,None,None),
            (("T",0,3,0),("IRB",r1s),1,"Include Transactions","",
                "N","N",None,None,None,None),
            (("T",0,4,0),("IRB",r1s),1,"Include Budgets","",
                "N","N",None,None,None,None),
            (("T",0,5,0),("IRB",r1s),1,"Include Standard Journals","",
                "N","N",None,None,None,None),
            (("T",0,6,0),("IRB",r1s),1,"Include Reports","",
                "N","N",None,None,None,None),
            (("T",0,7,0),("IRB",r1s),1,"Include Detail Records","",
                "N","N",None,None,None,None),
            (("T",0,8,0),("IRB",r1s),1,"Include Stream Records","",
                "N","N",None,None,None,None),
            (("T",0,9,0),("IRB",r1s),1,"Equalise Year Ends","",
                "N","N",None,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        if w == 0:
            return "Invalid Company Number"
        acc = self.sql.getRec("ctlmst", cols=["ctm_name"],
            where=[("ctm_cono", "=", w)], limit=1)
        if not acc:
            return "Invalid Company Number"
        acc = self.sql.getRec("genmst", cols=["count(*)"],
            where=[("glm_cono", "=", w)], limit=1)
        if not acc[0]:
            return "This Company Has No Masterfile Records"
        self.oldco = w

    def doEnd(self):
        self.df.closeProcess()
        tabels = [("genmst", "glm")]
        if self.df.t_work[0][0][1] == "Y":
            tabels.append(("ctlctl", "ctl"))
        if self.df.t_work[0][0][2] == "Y":
            tabels.append(("genbal", "glo"))
        if self.df.t_work[0][0][3] == "Y":
            tabels.append(("gentrn", "glt"))
        if self.df.t_work[0][0][4] == "Y":
            tabels.append(("genbud", "glb"))
        if self.df.t_work[0][0][5] == "Y":
            tabels.append(("genjlm", "gjm"))
            tabels.append(("genjlt", "gjt"))
        if self.df.t_work[0][0][6] == "Y":
            tabels.append(("genrpt", "glr"))
        if self.df.t_work[0][0][7] == "Y":
            tabels.append(("gendtm", "gdm"))
            tabels.append(("gendtt", "gdt"))
        if self.df.t_work[0][0][8] == "Y":
            tabels.append(("genstr", "gls"))
        for tab, ref in tabels:
            self.sql.delRec(tab, where=[("%s_cono" % ref, "=",
                self.opts["conum"])])
            recs = self.sql.getRec(tables=tab, where=[("%s_cono" % ref, "=",
                self.oldco)])
            if recs:
                p = ProgressBar(self.opts["mf"].body, mxs=len(recs),
                    typ="Copying %s" % tab)
                for num, acc in enumerate(recs):
                    p.displayProgress(num)
                    coy = "%s_cono" % ref
                    col = getattr(self.sql, "%s_col" % tab)
                    acc[col.index(coy)] = self.opts["conum"]
                    self.sql.insRec(tab, data=acc)
                p.closeProgress()
        if self.df.t_work[0][0][9] == "Y":
            self.sql.delRec("ctlynd", where=[("cye_cono", "=",
                self.opts["conum"])])
            ynds = self.sql.getRec("ctlynd", where=[("cye_cono",
                "=", self.oldco), ("cye_period", "in", (0, 1))],
                order="cye_period")
            for ynd in ynds:
                ynd[0] = self.opts["conum"]
                self.sql.insRec("ctlynd", data=ynd)
            mxp = self.sql.getRec("ctlynd", cols=["max(cye_period)"],
                where=[("cye_cono", "=", self.oldco)], limit=1)
            for p in range(1, mxp[0]):
                pr = getPeriods(self.opts["mf"], self.oldco, p)
                per = (p, (pr[0].work, pr[0].disp), (pr[1].work, pr[1].disp))
                callModule(self.opts["mf"], None, "msy010",
                    coy=(self.opts["conum"], self.opts["conam"]),
                    period=per, user=self.opts["capnm"], args=pr[2])
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
