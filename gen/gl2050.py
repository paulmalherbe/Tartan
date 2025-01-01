"""
SYNOPSIS
    General Ledger Standard Journals.

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
from TartanClasses import ASD, Batches, GetCtl, Sql, TartanDialog
from tartanFunctions import getSingleRecords, getVatRate, mthendDate

class gl2050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for Company Record
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        # Check and Load VAT Control
        self.ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
        if not self.ctlctl:
            return
        if self.gc.chkRec(self.opts["conum"], self.ctlctl, ["vat_ctl"]):
            return
        self.convat = self.ctlctl["vat_ctl"]
        # Set Batch Indicator
        self.batind = "Y"
        # Create SQL Object
        tabs = ["ctlctl", "ctlmst", "ctlvmf", "ctlvrf", "ctlvtf", "genint",
            "genjlm", "genjlt", "genmst", "gentrn", "assgrp", "rtlprm"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "GEN",
            self.opts["rtn"], multi="Y")
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][1][0] / 100)
        return True

    def doProcess(self):
        r1s = (
            ("Monthly", "M"),
            ("Quarterly", "3"),
            ("Bi-Annually", "6"),
            ("Annually", "Y"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Frequency","",
                "M","N",self.doFreq,None,None,None),
            (("T",0,1,0),("IRB",r2s),9,"All Journals","",
                "N","N",self.doAllJnl,None,None,None),
            (("T",0,2,0),("IRB",r2s),1,"All Periods","",
                "N","N",self.doAllPer,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd, txit=txt)

    def doFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w
        self.wher = [("gjm_cono", "=", self.opts["conum"]), ("gjm_freq", "=",
            self.freq), ("gjm_start","<=",self.bh.curdt), ("gjm_end", ">=",
            self.bh.curdt), ("gjm_last", "<", self.bh.curdt)]
        data = self.sql.getRec("genjlm", cols=["gjm_num", "gjm_desc"],
            where=self.wher)
        if not data:
            return "No Valid Standard Journals"
        if self.freq == "M":
            self.mths = 1
        elif self.freq == "3":
            self.mths = 3
        elif self.freq == "6":
            self.mths = 6
        else:
            self.mths = 12

    def doAllJnl(self, frt, pag, r, c, p, i, w):
        self.alljnl = w

    def doAllPer(self, frt, pag, r, c, p, i, w):
        self.allper = w

    def doEnd(self):
        self.df.closeProcess()
        if self.alljnl == "N":
            recs = getSingleRecords(self.opts["mf"], "genjlm", ("gjm_num",
                "gjm_desc"), where=self.wher)
        else:
            recs = self.sql.getRec("genjlm", where=self.wher)
        if not recs:
            self.opts["mf"].closeLoop()
            return
        for gjm in recs:
            self.trnref = gjm[self.sql.genjlm_col.index("gjm_num")]
            self.trndet = gjm[self.sql.genjlm_col.index("gjm_desc")]
            start = gjm[self.sql.genjlm_col.index("gjm_start")]
            last = gjm[self.sql.genjlm_col.index("gjm_last")]
            dates = []
            while start <= self.bh.curdt:
                if start < self.s_per or start <= last:
                    pass
                elif self.allper == "N" and start == self.bh.curdt:
                    dates.append(start)
                elif self.allper == "Y" and start <= self.bh.curdt:
                    dates.append(start)
                start = self.nextPeriod(start)
            for self.curdt in dates:
                self.trndat = mthendDate((self.curdt * 100))
                data = self.sql.getRec("genjlt",
                    cols=["gjt_acno", "gjt_amnt", "gjt_vatc"],
                    where=[("gjt_cono", "=", self.opts["conum"]),
                        ("gjt_num", "=", self.trnref),
                        ("gjt_amnt", "<>", 0)])
                if not data:
                    continue
                for tran in data:
                    self.acno = tran[0]
                    self.trnamt = tran[1]
                    self.vatcod = tran[2]
                    vrte = getVatRate(self.sql, self.opts["conum"],
                        self.vatcod, self.trndat)
                    if vrte is None:
                        vrte = 0.0
                    self.vatamt = round(
                        (self.trnamt * vrte / (vrte + 100)), 2)
                    self.updateTables()
                    self.updateBatch()
                self.sql.updRec("genjlm", cols=["gjm_last"],
                    data=[self.curdt], where=[("gjm_cono", "=",
                    self.opts["conum"]), ("gjm_num", "=", self.trnref),
                    ("gjm_freq", "=", self.freq)])
        self.opts["mf"].dbm.commitDbase()
        self.opts["mf"].closeLoop()

    def nextPeriod(self, period):
        yy = int(period / 100)
        mm = (period % 100) + self.mths
        if mm > 12:
            yy += 1
            mm -= 12
        return (yy * 100) + mm

    def updateTables(self):
        amt = float(ASD(self.trnamt) - ASD(self.vatamt))
        data = (self.opts["conum"], self.acno, self.curdt, self.trndat,
            self.opts["rtn"], self.trnref, self.bh.batno, amt, self.vatamt,
            self.trndet, self.vatcod, self.batind, 0, self.opts["capnm"],
            self.sysdtw, 0)
        self.sql.insRec("gentrn", data=data)
        if self.vatcod:
            if self.vatamt:
                data = (self.opts["conum"], self.convat, self.curdt,
                    self.trndat, self.opts["rtn"], self.trnref, self.bh.batno,
                    self.vatamt, 0.00, self.trndet, self.vatcod, self.batind,
                    0, self.opts["capnm"], self.sysdtw, 0)
                self.sql.insRec("gentrn", data=data)
            if amt < 0:
                vtyp = "O"
            else:
                vtyp = "I"
            data = (self.opts["conum"], self.vatcod, vtyp, self.curdt, "G",
                self.opts["rtn"], self.bh.batno, self.trnref, self.trndat,
                self.acno, self.trndet, amt, self.vatamt, 0,
                self.opts["capnm"], self.sysdtw, 0)
            self.sql.insRec("ctlvtf", data=data)

    def updateBatch(self, rev=False):
        if rev:
            self.bh.batqty = self.bh.batqty - 1
            self.bh.batval = float(ASD(self.bh.batval) - ASD(self.trnamt))
        else:
            self.bh.batqty = self.bh.batqty + 1
            self.bh.batval = float(ASD(self.bh.batval) + ASD(self.trnamt))

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
