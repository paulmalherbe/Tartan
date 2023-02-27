"""
SYNOPSIS
    Stores Ledger Change Type to Redundant for all Items having had No
    Movement for a Period of Time and with a Zero Quantity.

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

import time
from TartanClasses import GetCtl, ProgressBar, Sql, TartanDialog
from tartanFunctions import showError

class st6030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.dataHeader()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strmf1", "strtrn", "chglog"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.curdt = int(self.sysdtw / 100)
        return True

    def dataHeader(self):
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        self.stm = {
            "stype": "R",
            "tables": ("strmf1",),
            "cols": (
                ("st1_code", "", 0, "Product Code"),
                ("st1_desc", "", 0, "Description", "Y")),
            "where": [],
            "whera": [["T", "st1_group", 0, 0]],
            "index": 0}
        fld = [
            (("T",0,0,0),"INA",3,"Group","Product Group",
                "","Y",self.doGroup,grp,None,("notblank",)),
            (("T",0,1,0),"INA",20,"Code","Product Code",
                "","N",self.doCode,self.stm,None,("notblank",)),
            (("T",0,2,0),"ONA",30,"Description")]
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
        tit = "Generate Redundant Items"
        fld = (
            (("T",0,0,0),"IUI",3,"Months Inactive","",
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
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_type", "=", "N"),
            ("stt_cono=st1_cono",),
            ("stt_group=st1_group",),
            ("stt_code=st1_code",)]
        accs = self.sql.getRec(tables=["strmf1", "strtrn"], cols=["st1_group",
            "st1_code", "max(stt_curdt)", "sum(stt_qty)", "sum(stt_cost)"],
            where=whr, order="st1_group, st1_code")
        chgs = []
        for acc in accs:
            if acc[2] < self.startp and not acc[3] and not acc[4]:
                chgs.append(acc[:2])
        if not chgs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Redundant Records")
        else:
            self.cnt = 0
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            p = ProgressBar(self.opts["mf"].body, mxs=len(chgs),
                typ="Redundant Items")
            for num, rec in enumerate(chgs):
                p.displayProgress(num)
                self.sql.updRec("strmf1", cols=["st1_type"], data=["X"],
                    where=[("st1_cono", "=", self.opts["conum"]),
                    ("st1_group", "=", rec[0]), ("st1_code", "=", rec[1])])
                key = "%03i%-3s%-20s" % (self.opts["conum"], rec[0], rec[1])
                self.sql.insRec("chglog", data=["strmf1", "U", key,
                    "st1_type", dte, self.opts["capnm"], "N", "X", "", 0])
            p.closeProgress()
            mess = """%s Items Will be Marked as Redundant.

Would you like to COMMIT these Changes?""" % len(chgs)
            self.opts["mf"].dbm.commitDbase(ask=True, mess=mess)

    def doMthExit(self):
        self.mt.closeProcess()

    def doCreate(self):
        self.flag = "C"
        self.stm["where"] = [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "<>", "X")]
        self.df.focusField("T", 0, 1)

    def doRestore(self):
        self.flag = "R"
        self.stm["where"] = [
                ("st1_cono", "=", self.opts["conum"]),
                ("st1_type", "=", "X")]
        self.df.focusField("T", 0, 1)

    def doGroup(self, frt, pag, r, c, p, i, w):
        if self.flag == "C":
            chk = self.sql.getRec("strmf1", where=[("st1_cono",
                "=", self.opts["conum"]), ("st1_group", "=", w),
                ("st1_type", "<>", "X")], limit=1)
        else:
            chk = self.sql.getRec("strmf1", where=[("st1_cono",
                "=", self.opts["conum"]), ("st1_group", "=", w),
                ("st1_type", "=", "X")], limit=1)
        if not chk:
            return "Invalid Group"
        self.grp = w

    def doCode(self, frt, pag, r, c, p, i, w):
        whr = [
            ("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.grp),
            ("st1_code", "=", w)]
        if self.flag == "C":
            err = "Invalid, Not Normal"
            whr.append(("st1_type", "=", "N"))
        else:
            err = "Invalid, Not Redundant"
            whr.append(("st1_type", "=", "X"))
        chk = self.sql.getRec("strmf1", where=whr, limit=1)
        if not chk:
            return err
        if self.flag == "C":
            qty = self.sql.getRec("strtrn", cols=["sum(stt_qty)"],
                where=[("stt_cono", "=", self.opts["conum"]),
                ("stt_group", "=", self.grp), ("stt_code", "=", w)],
                limit=1)
            if qty[0]:
                return "Balance Exists"
        self.cod = w
        desc = chk[self.sql.strmf1_col.index("st1_desc")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def endPage(self):
        if self.flag == "C":
            old = "N"
            new = "X"
        else:
            old = "X"
            new = "N"
        self.sql.updRec("strmf1", cols=["st1_type"], data=[new],
            where=[("st1_cono", "=", self.opts["conum"]),
            ("st1_group", "=", self.grp), ("st1_code", "=", self.cod)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        key = "%03i%-3s%-20s" % (self.opts["conum"], self.grp, self.cod)
        self.sql.insRec("chglog", data=["strmf1", "U", key,
            "st1_type", dte, self.opts["capnm"], old, new, "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.clearFrame("T", 0)
        self.flag = ""

    def exitPage(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
