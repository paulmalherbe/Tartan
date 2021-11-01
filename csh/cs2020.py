"""
SYNOPSIS
    Cash Merge with General Ledger.

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

import time
from TartanClasses import ASD, CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import showInfo, showError

class cs2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        cshctl = gc.getCtl("cshctl", self.opts["conum"])
        if not cshctl:
            return
        self.glint = cshctl["ccc_glint"]
        if self.glint == "N":
            showError(self.opts["mf"].window, "Error",
                "Cash Analysis Not Integrated.")
            return
        ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
        self.cshctl = ctlctl["csh_ctl"]
        self.vatctl = ctlctl["vat_ctl"]
        tabs = ["cshana", "cshcnt", "gentrn", "ctlvtf"]
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.dte = self.sql.getRec("cshcnt", cols=["max(cct_date)"],
            where=[("cct_cono", "=", self.opts["conum"])], limit=1)[0]
        t = time.localtime()
        self.sysdt = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Cash Merge (%s)" % self.__class__.__name__)
        dte = {
            "stype": "R",
            "tables": ("cshcnt",),
            "cols": (
                ("cct_date", "", 0, "Date"),),
            "where": [("cct_cono", "=", self.opts["conum"])],
            "group": "cct_date"}
        fld = (
            (("T",0,0,0),"ID1",10,"From Date","",
                self.dte,"Y",self.doFrom,dte,None,("efld",)),
            (("T",0,1,0),"Id1",10,"To   Date","To Date",
                "","Y",self.doTo,dte,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doFrom(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.fm = w
        self.fmd = self.df.t_disp[pag][r][p]
        self.df.loadEntry(frt, pag, p+1, data=self.fm)

    def doTo(self, frt, pag, r, c, p, i, w):
        if not w:
            w = self.fm
        elif w < self.fm:
            return "Invalid To Date"
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.to = w
        self.tod = CCD(w, "D1", 10).disp
        csh = self.sql.getRec("cshcnt", where=[("cct_cono", "=",
            self.opts["conum"]), ("cct_type", "=", "T"), ("cct_date",
            "between", self.fm, self.to)])
        if not csh:
            return "ff1|Invalid Cash Capture Dates"

    def doEnd(self):
        self.df.closeProcess()
        recs = self.sql.getRec("cshana", where=[("can_cono", "=",
            self.opts["conum"]), ("can_trdt", "between", self.fm, self.to),
            ("can_gflag", "=", "N")], order="can_trdt")
        if not recs:
            showInfo(self.opts["mf"].window, "Merge",
                "There are No Records to Merge.")
        else:
            for rec in recs:
                # Expense and Income
                acc = self.sql.getRec("gentrn", cols=["max(glt_refno)"],
                    where=[("glt_cono", "=", self.opts["conum"]),
                    ("glt_acno", "=", self.cshctl), ("glt_type", "=", 4),
                    ("glt_refno", "like", "CS_______")], limit=1)
                if acc:
                    try:
                        auto = int(acc[0][2:]) + 1
                    except:
                        auto = 1
                else:
                    auto = 1
                refno = "CS%07d" % auto
                ttyp = rec[self.sql.cshana_col.index("can_type")]
                iamnt = rec[self.sql.cshana_col.index("can_incamt")]
                vamnt = rec[self.sql.cshana_col.index("can_vatamt")]
                eamnt = float(ASD(iamnt) - ASD(vamnt))
                if ttyp == "T":
                    iamnt = float(ASD(0) - ASD(iamnt))
                    vamnt = float(ASD(0) - ASD(vamnt))
                    eamnt = float(ASD(0) - ASD(eamnt))
                vcod = rec[self.sql.cshana_col.index("can_vatcod")]
                data = [rec[self.sql.cshana_col.index("can_cono")]]
                acno = rec[self.sql.cshana_col.index("can_code")]
                trdt = rec[self.sql.cshana_col.index("can_trdt")]
                curdt = int(trdt / 100)
                data.extend([acno, curdt, trdt, 4, refno, "CSHMRGE",
                    eamnt, vamnt, "Cash Analysis", vcod])
                data.extend(["", 0, self.opts["capnm"], self.sysdt])
                self.sql.insRec("gentrn", data=data)
                # VAT Control
                data[1] = self.vatctl
                data[7] = vamnt
                data[8] = 0
                self.sql.insRec("gentrn", data=data)
                # Cash Control
                data[1] = self.cshctl
                data[7] = float(ASD(0) - ASD(iamnt))
                data[8] = 0
                data[9] = rec[self.sql.cshana_col.index("can_desc")]
                self.sql.insRec("gentrn", data=data)
                # VAT Record
                data = [rec[self.sql.cshana_col.index("can_cono")]]
                data.append(vcod)
                if ttyp == "T":
                    data.append("O")
                else:
                    data.append("I")
                data.extend([curdt, "G", 4, "CSHMRG", refno, trdt, acno,
                    "Cash Analysis", eamnt, vamnt, 0, self.opts["capnm"],
                    self.sysdt])
                self.sql.insRec("ctlvtf", data=data)
                # Update
                seq = rec[self.sql.cshana_col.index("can_seq")]
                self.sql.updRec("cshana", cols=["can_gflag"], data=["Y"],
                    where=[("can_seq", "=", seq)])
            self.opts["mf"].dbm.commitDbase(True)
        self.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
