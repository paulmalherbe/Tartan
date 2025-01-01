"""
SYNOPSIS
    Creditors Ledger Change Status to Redundant for all Accounts having had No
    Movement for a Period of Time and with a Zero Balance.

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
from TartanClasses import GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import showError

class cr6030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["crsmst", "crstrn", "chglog"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        return True

    def dataHeader(self):
        self.crm = {
            "stype": "R",
            "tables": ("crsmst",),
            "cols": [
                ("crm_acno", "", 0, "Acc-Num"),
                ("crm_name", "", 0, "Name", "Y")],
            "where": [],
            "index": 0}
        fld = [
            (("T",0,0,0),"INA",7,"Acc-Num","Account Number",
                "","N",self.doAcno,self.crm,None,("notblank",)),
            (("T",0,1,0),"ONA",30,"Name")]
        but = (
            ("Generate",None,self.doGenerate,1,None,(("T",0,1),("T",0,2)),
                "Mark zero items, which have been inactive, as redundant"),
            ("Create",None,self.doCreate,1,None,(("T",0,1),("T",0,2)),
                "Mark a zero item as redundant"),
            ("Restore",None,self.doRestore,1,None,(("T",0,1),("T",0,2)),
                "Mark a redundant item as normal"),
            ("Exit",None,self.exitPage,1,None,(("T",0,1),("T",0,2))))
        tnd = ((self.endPage, "y"),)
        txt = (self.exitPage,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt, focus=False)
        self.df.setWidget(self.df.B0, state="normal")
        self.df.setWidget(self.df.B1, state="normal")
        self.df.setWidget(self.df.B2, state="normal")
        self.df.setWidget(self.df.B3, state="normal")

    def doGenerate(self):
        tit = "Generate Redundant Accounts"
        fld = (
            (("T",0,0,0),"IUI",2,"Months Inactive","",
                24,"Y",self.doMonths,None,None,("efld",)),)
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.mt = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doMthEnd, "y"),), txit=(self.doMthExit,))
        self.mt.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doMonths(self, frt, pag, r, c, p, i, w):
        months = w
        yr = int(self.curdt / 100)
        mt = self.curdt % 100
        for mth in range(months):
            mt -= 1
            if not mt:
                mt = 12
                yr -= 1
        self.startp = (yr * 100) + mt

    def doMthEnd(self):
        self.mt.closeProcess()
        whr = [
            ("crm_cono", "=", self.opts["conum"]),
            ("crm_stat", "=", "N")]
        msts = self.sql.getRec("crsmst", cols=["crm_acno",
            "crm_opened"], where=whr, order="crm_acno")
        chgs = []
        for mst in msts:
            whr = [
                ("crt_cono", "=", self.opts["conum"]),
                ("crt_acno", "=", mst[0])]
            rec = self.sql.getRec("crstrn", cols=["max(crt_curdt)",
                "sum(crt_tramt)"], where=whr, limit=1)
            if rec[0] and rec[0] < self.startp and not rec[1]:
                chgs.append(mst[0])
            elif not rec[0] and int(mst[1] / 100) < self.startp:
                chgs.append(mst[0])
        if not chgs:
            showError(self.opts["mf"].body, "Processing Error",
                "No New Redundant Accounts")
        else:
            self.cnt = 0
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            p = ProgressBar(self.opts["mf"].body, mxs=len(chgs),
                typ="Flagging Redundant Accounts")
            for num, rec in enumerate(chgs):
                p.displayProgress(num)
                self.sql.updRec("crsmst", cols=["crm_stat"], data=["X"],
                    where=[("crm_cono", "=", self.opts["conum"]),
                    ("crm_acno", "=", rec)])
                key = "%03i%-7s" % (self.opts["conum"], rec)
                self.sql.insRec("chglog", data=["crsmst", "U", key,
                    "crm_stat", dte, self.opts["capnm"], "N", "X", "", 0])
            p.closeProgress()
            mess = """%s Accounts Will be Flagged as Redundant.

Would you like to COMMIT these Changes?""" % len(chgs)
            self.opts["mf"].dbm.commitDbase(ask=True, mess=mess, default="no")

    def doMthExit(self):
        self.mt.closeProcess()

    def doCreate(self):
        self.flag = "C"
        self.crm["where"] = [
            ("crm_cono", "=", self.opts["conum"]),
            ("crm_stat", "<>", "X")]
        self.df.focusField("T", 0, 1)

    def doRestore(self):
        self.flag = "R"
        self.crm["where"] = [
            ("crm_cono", "=", self.opts["conum"]),
            ("crm_stat", "=", "X")]
        self.df.focusField("T", 0, 1)

    def doAcno(self, frt, pag, r, c, p, i, w):
        if self.flag == "C":
            typ = "<>"
        else:
            typ = "="
        chk = self.sql.getRec("crsmst", where=[("crm_cono",
            "=", self.opts["conum"]), ("crm_acno", "=", w),
            ("crm_stat", typ, "X")], limit=1)
        if not chk:
            return "Invalid Code"
        if self.flag == "C":
            bal = self.sql.getRec("crstrn", cols=["sum(crt_tramt)"],
                where=[("crt_cono", "=", self.opts["conum"]),
                ("crt_acno", "=", w)], limit=1)
            if bal[0]:
                return "Balance Exists"
        self.acno = w
        name = chk[self.sql.crsmst_col.index("crm_name")]
        self.df.loadEntry(frt, pag, p+1, data=name)

    def endPage(self):
        if self.flag == "C":
            old = "N"
            new = "X"
        else:
            old = "X"
            new = "N"
        self.sql.updRec("crsmst", cols=["crm_stat"], data=[new],
            where=[("crm_cono", "=", self.opts["conum"]),
            ("crm_acno", "=", self.acno)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        key = "%03i%-7s" % (self.opts["conum"], self.acno)
        self.sql.insRec("chglog", data=["crsmst", "U", key, "crm_stat",
            dte, self.opts["capnm"], old, new, 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.clearFrame("T", 0)
        self.flag = ""

    def exitPage(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
