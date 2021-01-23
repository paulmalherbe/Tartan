"""
SYNOPSIS
    Asset Register Raise Depreciation.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import dateDiff, copyList, mthendDate, showError

class ar2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if "args" in self.opts:
            self.args = self.opts["args"]
        else:
            self.args = None
        if self.setVariables():
            if self.args:
                self.curdt = self.args[0]
                self.endPage0()
            else:
                self.dataHeader()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.glint = assctl["cta_glint"]
        self.rordp = assctl["cta_rordp"]
        self.lastp = assctl["cta_lastp"]
        self.sper = int(self.opts["period"][1][0] / 100)
        self.eper = int(self.opts["period"][2][0] / 100)
        yr = int(self.lastp / 100)
        mt = (self.lastp % 100) + 1
        if mt > 12:
            yr += 1
            mt = 1
        self.curdt = (yr * 100) + mt
        if self.curdt > self.eper:
            self.curdt = self.eper
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        tabs = ["assctl", "assgrp", "assmst", "assdep", "asstrn", "gentrn"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        chk = self.sql.getRec("asstrn", where=[("ast_cono", "=",
            self.opts["conum"]), ("ast_mtyp", "=", 4), ("ast_curdt", ">",
            self.eper)])
        if chk:
            if not self.args:
                showError(self.opts["mf"].body, "Period Error",
                    "Depreciation Has Already Been Raised in "\
                    "the Next Financial Period")
            return
        return True

    def dataHeader(self):
        fld = (
            (("T",0,0,0),"ID2",7,"Cut-off Period","",
                self.curdt,"N",self.doTrdate,None,None,None),)
        tnd = ((self.endPage0, "y"),)
        txt = (self.exitPage0,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doTrdate(self, frt, pag, r, c, p, i, w):
        if w < self.sper or w > self.eper:
            return "Invalid Date, Not in Financial Period"
        if self.lastp and self.lastp < self.sper:
            dte1 = mthendDate(self.lastp * 100)
            dte2 = mthendDate(self.sper * 100)
            if dateDiff(dte1, dte2, "months") > 1:
                return "Missing Depreciation for Previous Period"
        self.curdt = w

    def endPage0(self):
        if self.args:
            recs = self.sql.getRec("assmst", where=[("asm_cono", "=",
                self.opts["conum"]), ("asm_group", "=", self.args[1]),
                ("asm_code", "=", self.args[2])])
        else:
            self.df.closeProcess()
            recs = self.sql.getRec("assmst", where=[("asm_cono", "=",
                self.opts["conum"])])
        if recs:
            self.doRaiseAll(recs)
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doRaiseAll(self, recs):
        if not self.args:
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs),
                typ="Raising Depreciation ... Please Wait")
        for num, dat in enumerate(recs):
            if not self.args:
                p.displayProgress(num)
            self.group = CCD(dat[self.sql.assmst_col.index("asm_group")],
                "UA", 3)
            grp = self.sql.getRec("assgrp", where=[("asg_cono", "=",
                self.opts["conum"]), ("asg_group", "=", self.group.work)],
                limit=1)
            if not grp:
                if not self.args:
                    showError(self.opts["mf"].body, "Group Error",
                        "Missing Group (%s) Record" % self.group.disp)
                abort = True
                break
            self.depacc = grp[self.sql.assgrp_col.index("asg_depacc")]
            self.expacc = grp[self.sql.assgrp_col.index("asg_expacc")]
            self.code = dat[self.sql.assmst_col.index("asm_code")]
            self.depcod = dat[self.sql.assmst_col.index("asm_depcod")]
            bals = Balances(self.opts["mf"], "ASS", self.opts["conum"],
                self.sper, keys=(self.group.work, self.code))
            asset = bals.doAssBals()
            if not asset:
                continue
            self.cap, cdp, rdp, cbl, rbl, mov = asset
            # Raise depreciation from start period to curdt or sale date
            self.lurdt = self.sper
            sales = False
            while not sales and self.lurdt <= self.curdt:
                trans = self.sql.getRec("asstrn", cols=["ast_mtyp",
                    "round(sum(ast_amt1), 2)"], where=[("ast_cono", "=",
                    self.opts["conum"]), ("ast_group", "=",
                    self.group.work), ("ast_code", "=", self.code),
                    ("ast_curdt", "=", self.lurdt), ("ast_mtyp", "<>", 4)],
                    group="ast_mtyp")
                if trans:
                    for mov, amt in trans:
                        if mov == 5:
                            sales = True
                            self.cap = 0
                            break
                        self.cap = float(ASD(self.cap) + ASD(amt))
                if self.cap:
                    self.doRaiseDep()
                self.lurdt = self.doIncrCurdt()
        if not self.args:
            p.closeProgress()
        if abort:
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.sql.updRec("assctl", cols=["cta_lastp"], data=[self.curdt],
                where=[("cta_cono", "=", self.opts["conum"])])
            self.opts["mf"].dbm.commitDbase()

    def doIncrCurdt(self):
        yr = int(self.lurdt / 100)
        mt = self.lurdt % 100
        if mt == 12:
            yr += 1
            mt = 1
        else:
            mt += 1
        return (yr * 100) + mt

    def doRaiseDep(self):
        # Calculate Depreciations and check if Raised
        # else create transaction and accumulate variables
        #
        # Extract Closing Balance at lurdt
        where = [("ast_cono", "=", self.opts["conum"]), ("ast_group", "=",
            self.group.work), ("ast_code", "=", self.code)]
        whr = copyList(where)
        whr.append(("ast_curdt", "<=", self.lurdt))
        bal = self.sql.getRec("asstrn", cols=["round(sum(ast_amt1), 2)",
            "round(sum(ast_amt2), 2)"], where=whr, limit=1)
        if bal and bal[0] <= 0:
            return
        # Get Date Purchased and Months to trdt
        self.trdt = mthendDate(self.lurdt * 100)
        acc = self.sql.getRec("asstrn", cols=["min(ast_date)"],
            where=[("ast_cono", "=", self.opts["conum"]), ("ast_group", "=",
            self.group.work), ("ast_code", "=", self.code), ("ast_mtyp",
            "=", 1)], limit=1)
        years = dateDiff(acc[0], self.trdt, "years")
        if years > 6:
            # Maximum of 7 variable rates in assdep record
            years = 6
        # Get Depreciation Record
        dep = self.sql.getRec("assdep", where=[("asd_cono", "=",
            self.opts["conum"]), ("asd_code", "=", self.depcod)], limit=1)
        #
        # Extract Depreciation up to previous year end
        whr = copyList(where)
        whr.extend([("ast_mtyp", "=", 4), ("ast_curdt", "<", self.sper)])
        pmd = self.sql.getRec("asstrn", cols=["round(sum(ast_amt1), 2)",
            "round(sum(ast_amt2), 2)"], where=whr, limit=1)
        if not pmd[0]:
            pmd[0] = 0
        if not pmd[1]:
            pmd[1] = 0
        #
        # Extract Depreciation for lurdt
        whr = copyList(where)
        whr.extend([("ast_mtyp", "=", 4), ("ast_curdt", "=", self.lurdt)])
        cmd = self.sql.getRec("asstrn", cols=["max(ast_refno)",
            "round(sum(ast_amt1), 2)", "round(sum(ast_amt2), 2)"], where=whr,
            limit=1)
        if not cmd[0] or cmd[0] == "Take-On":
            self.refno = CCD(1, "Na", 9).work
        else:
            self.refno = CCD(cmd[0], "Na", 9).work
        if not cmd[1]:
            cmd[1] = 0
        if not cmd[2]:
            cmd[2] = 0
        if dep[self.sql.assdep_col.index("asd_typec")] == "S":
            # Straight Line
            cval = self.cap
            crat = dep[self.sql.assdep_col.index("asd_rate1c")]
            for x in range(2, years + 2):
                n = dep[self.sql.assdep_col.index("asd_rate%sc" % x)]
                if n:
                    crat = n
        else:
            # Depreciating Balance
            cval = float(ASD(self.cap) + ASD(pmd[0]))
            crat = dep[self.sql.assdep_col.index("asd_rate1c")]
        if cval:
            if cval < 0:
                cdep = 0
            else:
                cdep = round((cval * crat / 100.0 / 12), 2)
                cdep = float(ASD(cdep) + ASD(cmd[1]))
                cbal = float(ASD(bal[0]) - ASD(cdep))
                if cbal < 0:
                    cdep = float(ASD(cdep) + ASD(cbal))
                cdep = float(ASD(0) - ASD(cdep))
        typer = dep[self.sql.assdep_col.index("asd_typer")]
        if self.rordp == "N" or typer == "N":
            rdep = 0
        else:
            if typer == "S":
                # Straight Line
                rval = self.cap
                rrat = dep[self.sql.assdep_col.index("asd_rate1r")]
                for x in range(2, years + 2):
                    n = dep[self.sql.assdep_col.index("asd_rate%sr" % x)]
                    if n:
                        rrat = n
            else:
                # Depreciating Balance
                rval = float(ASD(self.cap) + ASD(pmd[1]))
                rrat = dep[self.sql.assdep_col.index("asd_rate1r")]
            if rval:
                if rval < 0:
                    rdep = 0
                else:
                    rdep = round((rval * rrat / 100.0 / 12), 2)
                    rdep = float(ASD(rdep) + ASD(cmd[2]))
                    rbal = float(ASD(bal[1]) - ASD(rdep))
                    if rbal < 0:
                        rdep = float(ASD(rdep) + ASD(rbal))
                    rdep = float(ASD(0) - ASD(rdep))
        if cdep or rdep:
            data = [self.opts["conum"], self.group.work, self.code, 4,
                self.refno, "AutoDep", self.trdt, 4, cdep, rdep, 0, self.lurdt,
                "Auto Raising of Depreciation", "", "", self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("asstrn", data=data)
            if self.glint == "Y" and cdep:
                self.doWriteGen(self.depacc, cdep)
                cdep = float(ASD(0) - ASD(cdep))
                self.doWriteGen(self.expacc, cdep)

    def doWriteGen(self, accno, amnt):
        whr = [("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=", accno),
            ("glt_batch", "=", "AutoDep"), ("glt_curdt", "=", self.lurdt),
            ("glt_trdt", "=", self.trdt), ("glt_type", "=", 4)]
        acc = self.sql.getRec("gentrn", where=whr)
        if acc and len(acc) == 1:
            amt = acc[0][self.sql.gentrn_col.index("glt_tramt")]
            amt = float(ASD(amt) + ASD(amnt))
            self.sql.updRec("gentrn", cols=["glt_tramt"], data=[amt], where=whr)
        else:
            data = [self.opts["conum"], accno, self.lurdt, self.trdt, 4,
                self.refno, "AutoDep", amnt, 0, "Auto Raising of Depreciation",
                "", "", 0, self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)

    def exitPage0(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
