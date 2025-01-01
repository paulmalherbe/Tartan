"""
SYNOPSIS
    Members Ledger Suspension Report.

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
from TartanClasses import ASD, GetCtl, ProgressBar, RepPrt, Sql, SplashScreen
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, getSingleRecords, getTrn

class ml3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["memmst", "memsta", "memtrn",
            "memcat", "memctc", "memctp"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        mc = GetCtl(self.opts["mf"])
        memctl = mc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.fromad = memctl["mcm_emadd"]
        self.s_per = int(self.opts["period"][1][0] / 100)
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        r1s = (("Number", "N"), ("Surname", "M"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Include Pay Plan","",
                "N","Y",self.doPayPlan,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doPayPlan(self, frt, pag, r, c, p, i, w):
        self.plan = w

    def doEnd(self):
        self.df.closeProcess()
        col = ["mlm_memno", "mlm_surname", "mlm_names", "mlm_payplan",
            "mlc_code"]
        whr = [("mlm_cono", "=", self.opts["conum"]), ("mlm_state", "=", "A")]
        if self.plan == "N":
            whr.append(("mlm_payplan", "=", "N"))
        whr.extend([("mlc_cono=mlm_cono",), ("mlc_memno=mlm_memno",),
            ("mlc_type", "=", "B")])
        grp = "mlm_memno, mlm_surname, mlm_names, mlm_payplan, mlc_code"
        if self.sort == "N":
            odr = "mlm_memno"
        else:
            odr = "mlm_surname"
        sp = SplashScreen(self.opts["mf"].body,
            "Preparing Report ... Please Wait")
        recs = self.sql.getRec(tables=["memmst", "memcat"], cols=col,
            where=whr, group=grp, order=odr)
        sp.closeSplash()
        if not recs:
            self.opts["mf"].closeLoop()
            return
        p = ProgressBar(self.opts["mf"].body, typ="Generating the Report",
            mxs=len(recs), esc=True)
        data = []
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            whr = [
                ("mlt_cono", "=", self.opts["conum"]),
                ("mlt_memno", "=", rec[0])]
            trn = getTrn(self.opts["mf"].dbm, "mem", whr=whr, zer="N")
            bal = 0
            inv = 0
            for t in trn[1]:
                c = trn[0]
                bal = float(ASD(bal) + ASD(t[c.index("mlt_tramt")]))
                if t[c.index("mlt_type")] == 1 and \
                        t[c.index("mlt_curdt")] >= self.s_per:
                    inv = float(ASD(inv) + ASD(t[c.index("mlt_tramt")]))
            if not bal or bal < inv:
                continue
            cat = self.sql.getRec(tables=["memctc", "memctp"],
                cols=["mcc_desc", "mcp_rate_01"], where=[("mcc_cono", "=",
                self.opts["conum"]), ("mcc_type", "=", "B"), ("mcc_code",
                "=", rec[4]), ("mcp_cono=mcc_cono",), ("mcp_type=mcc_type",),
                ("mcp_code=mcc_code",)], order="mcp_date desc", limit=1)
            if not cat or bal < cat[1]:
                continue
            rec[1] = "%s, %s" % (rec[1], rec[2])
            del rec[2]
            rec[3] = cat[0]
            rec.append(cat[1])
            rec.append(inv)
            rec.append(bal)
            data.append(rec)
        p.closeProgress()
        if p.quit:
            self.opts["mf"].closeLoop()
            return
        name = self.__class__.__name__
        head = ["Members Suspension Report"]
        cols = [
            ["a", "NA",  7,   "Mem-No",          "y"],
            ["b", "NA", 50,   "Name",            "y"],
            ["d", "UA", 1,    "P",               "y"],
            ["c", "NA", 30,   "Active-Category", "y"],
            ["e", "SD", 13.2, "Subscription",    "y"],
            ["f", "SD", 13.2, "Tot-Invoiced",    "y"],
            ["g", "SD", 13.2, "Tot-Balance",     "y"]]
        rep = RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=name, tables=data,
            heads=head, cols=cols, gtots=("e", "f", "g"), ttype="D",
            repprt=self.df.repprt, repeml=self.df.repeml, fromad=self.fromad)
        if not rep.xits:
            ask = askChoice(self.opts["mf"].body, "Suspend Members",
                "Select Members to Suspend", butt=(("All","A"), ("Some","S"),
                ("None","N")), default="None")
            if ask in ("A", "S"):
                if ask == "S":
                    cols = ["memno", "name"]
                    dics = {
                        "memno": ("",0,"UI",6,"Member Number","Mem-No"),
                        "name": ("",1,"NA",50,"Member Name","Name")}
                    newd = []
                    for dat in data:
                        newd.append((dat[0], dat[1]))
                    data = getSingleRecords(self.opts["mf"], "", cols,
                        where=newd, ttype="D", dic=dics)
                if data:
                    p = ProgressBar(self.opts["mf"].body,
                        typ="Suspending Members", mxs=len(data))
                    for num, rec in enumerate(data):
                        p.displayProgress(num)
                        self.sql.updRec("memmst", cols=["mlm_state",
                            "mlm_sdate"], data=["S", self.sysdtw],
                            where=[("mlm_cono", "=", self.opts["conum"]),
                            ("mlm_memno", "=", rec[0])])
                        self.sql.insRec("memsta", data=[self.opts["conum"],
                            rec[0], "S", self.sysdtw, self.opts["capnm"],
                            self.sysdtw, 0])
                    self.opts["mf"].dbm.commitDbase()
        p.closeProgress()
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
