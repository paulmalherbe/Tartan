"""
SYNOPSIS
    Stores Revalue at Average or Last Cost and Optionally Calculate Selling
    Prices and Eradicate All Minus Balances.

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

import time
from TartanClasses import ASD, Balances, CCD, GetCtl, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import showError

class st6020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in opts:
                self.loc, self.date, self.hist, mths = opts["args"]
                self.curdt = int(self.date / 100)
                self.minus = "Y"
                if self.hist == "Y":
                    self.loadPers(mths)
                self.doEnd()
            else:
                self.dataHeader()
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["gentrn", "strloc", "strmf1",
            "strmf2", "strtrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.locs = strctl["cts_locs"]
        self.plevs = strctl["cts_plevs"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["stk_soh", "stk_susp"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.stk_soh = ctlctl["stk_soh"]
            self.stk_susp = ctlctl["stk_susp"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sper = int(self.opts["period"][1][0] / 100)
        return True

    def dataHeader(self):
        r1s = (("Yes", "Y"), ("No", "N"))
        if self.locs == "Y":
            idx = 1
            fld = [(("T",0,0,0),"IUA",1,"Location","",
                "1","Y",self.doLoc,None,None,("efld",))]
        else:
            idx = 0
            fld = []
            self.loc = "1"
        fld.extend([
            (("T",0,idx,0),"ID1",10,"Effective Date","",
                self.sysdtw,"Y",self.doDate,None,None,("efld",)),
            (("T",0,idx+1,0),("IRB",r1s),0,"Change History","",
                "N","N",self.doHist,None,None,None),
            (("T",0,idx+2,0),"IUI",2,"Number of Months","",
                0,"N",self.doMths,None,None,("efld",)),
            (("T",0,idx+3,0),("IRB",r1s),0,"Clear Minuses","",
                "Y","N",self.doMinus,None,None,None)])
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doLoc(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("strloc", where=[("srl_cono", "=",
            self.opts["conum"]), ("srl_loc", "=", w)], limit=1)
        if not chk:
            return "Invalid Location"
        self.loc = w

    def doDate(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0] or w > self.opts["period"][2][0]:
            return "Invalid Date, Not in Financial Period"
        self.date = w
        self.curdt = int(w / 100)

    def doHist(self, frt, pag, r, c, p, i, w):
        self.hist = w
        if self.hist == "N":
            return "sk1"

    def doMths(self, frt, pag, r, c, p, i, w):
        self.loadPers(w)

    def doMinus(self, frt, pag, r, c, p, i, w):
        self.minus = w

    def loadPers(self, mths):
        yr = int(self.curdt / 100)
        mt = (self.curdt % 100) - mths
        if mt < 1:
            yr -= 1
            mt += 12
        hper = (yr * 100) + mt
        if hper < self.sper:
            return "Out of Financial Period"
        self.pers = [hper]
        while hper < self.curdt:
            yr = int(hper / 100)
            mt = (hper % 100) + 1
            if mt > 12:
                yr += 1
                mt -= 12
            hper = (yr * 100) + mt
            self.pers.append(hper)
        self.pers.append(self.curdt)

    def doEnd(self):
        if "args" not in self.opts:
            self.df.closeProcess()
        whr = [
            ("st2_cono", "=", self.opts["conum"]),
            ("st1_cono=st2_cono",),
            ("st1_group=st2_group",),
            ("st1_code=st2_code",),
            ("st1_type", "<>", "X"),
            ("st1_value_ind", "<>", "N")]
        recs = self.sql.getRec(tables=["strmf1", "strmf2"], cols=["st2_group",
            "st2_code", "st2_loc"], where=whr, order="st2_group, st2_code")
        if not recs:
            if "args" not in self.opts:
                showError(self.opts["mf"].body, "Processing Error",
                    "No Stock Records")
            else:
                print("No Stock Records")
        else:
            self.cnt = 0
            txt = "Re-Valuation of Stock at Last Cost"
            if "args" not in self.opts:
                p = ProgressBar(self.opts["mf"].body, mxs=len(recs), typ=txt)
            obal = self.sql.getRec("strtrn", cols=["sum(stt_cost)"],
                where=[("stt_cono", "=", self.opts["conum"]), ("stt_loc",
                "=", self.loc)], limit=1)[0]
            for num, rec in enumerate(recs):
                if "args" not in self.opts:
                    p.displayProgress(num)
                if self.hist == "Y":
                    self.doHistory(rec)
                self.doCurrent(rec)
            if "args" not in self.opts:
                p.closeProgress()
            cbal = self.sql.getRec("strtrn", cols=["sum(stt_cost)"],
                where=[("stt_cono", "=", self.opts["conum"]), ("stt_loc",
                "=", self.loc)], limit=1)[0]
            tval = float(ASD(cbal) - ASD(obal))
            if self.glint == "Y" and tval:
                # Next automatic reference
                acc = self.sql.getRec("gentrn",
                    cols=["max(glt_refno)"], where=[("glt_cono", "=",
                    self.opts["conum"]), ("glt_acno", "=", self.stk_susp),
                    ("glt_refno", "like", "SR_______"), ("glt_batch", "=",
                    "ST-RVAL")], limit=1)
                if acc:
                    try:
                        auto = int(acc[0][2:]) + 1
                    except:
                        auto = 1
                else:
                    auto = 1
                refno = "SR%07d" % auto
                # General Ledger Control Transaction (Stock On Hand)
                self.sql.insRec("gentrn", data=[self.opts["conum"],
                    self.stk_soh, self.curdt, self.date, 4, refno,
                    "ST-RVAL", tval, 0, txt, "N", "", 0,
                    self.opts["capnm"], self.sysdtw, 0])
                # General Ledger Control Transaction (Stock Reconciliation)
                val = float(ASD(0) - ASD(tval))
                self.sql.insRec("gentrn", data=[self.opts["conum"],
                    self.stk_susp, self.curdt, self.date, 4, refno,
                    "ST-RVAL", val, 0, txt, "N", "", 0,
                    self.opts["capnm"], self.sysdtw, 0])
            txt = """Old Stock Balance:    %s
New Stock Balance:    %s\n""" % (CCD(obal, "SD", 12.2).disp,
        CCD(cbal, "SD", 12.2).disp)
            self.opts["mf"].dbm.commitDbase(ask=True, mess=txt)
        if "args" not in self.opts:
            self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doHistory(self, rec):
        grp, cod, loc = rec
        whr = [
            ("stt_cono", "=", self.opts["conum"]),
            ("stt_group", "=", grp),
            ("stt_code", "=", cod),
            ("stt_loc", "=", loc),
            ("stt_type", "in", (1, 3))]
        for per in self.pers:
            w = whr[:]
            w.append(("stt_curdt", "<=", per))
            chk = self.sql.getRec("strtrn", cols=["max(stt_curdt)", "stt_qty",
                "stt_cost"], where=whr, group="stt_curdt, stt_qty, stt_cost",
                order="stt_curdt desc", limit=1)
            if not chk:
                continue
            cst = round((chk[2] / chk[1]), 2)
            self.sql.sqlRec("Update strtrn set stt_cost = stt_qty * %s "\
                "where stt_cono = %s and stt_group = '%s' and "\
                "stt_code = '%s' and stt_loc = '%s' and stt_type not in "\
                "(1,3) and stt_curdt = %s" % (cst, self.opts["conum"], grp,
                cod, loc, per))

    def doCurrent(self, rec):
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
            self.curdt, keys=(rec[0], rec[1], rec[2],
            ("P", self.opts["period"][0])))
        m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
        fqty, fval = y_cb
        if self.minus == "N" and not ac and not lc:
            return
        if self.minus == "Y" and fqty < 0:
            nqty = 0
        else:
            nqty = fqty
        if lc:
            ncst = lc
        else:
            ncst = ac
        nval = round((nqty * ncst), 2)
        dqty = float(ASD(nqty) - ASD(fqty))
        dval = float(ASD(nval) - ASD(fval))
        if not dqty and not dval:
            return
        # Stores Ledger Transaction
        if dqty >= 0:
            rtn = 5
        else:
            rtn = 6
        self.cnt += 1
        txt = "Revaluation"
        self.sql.insRec("strtrn", data=[self.opts["conum"], rec[0], rec[1],
            rec[2], self.date, rtn, self.cnt, "ST-RVAL", "", dqty, dval, 0,
            self.curdt, txt, 0, "", "", "STR", 0, "", self.opts["capnm"],
            self.sysdtw, 0])

if __name__ == "__main__":
    import getopt, sys
    from TartanClasses import Dbase, MainFrame
    from tartanFunctions import getPeriods, loadRcFile
    try:
        opts, args = getopt.getopt(sys.argv[1:],"c:d:h:l:m:p:r:")
    except:
        print("")
        print("Usage: -cconum -pperiod -rrcfile -llocation -ddate -hhistory -mmonths")
        print("")
        sys.exit()
    coy = 1
    num = None
    rcf = None
    loc = "1"
    t = time.localtime()
    dte = (t[0] * 10000) + (t[1] * 100) + t[2]
    hst = "N"
    mth = 0
    for o, v in opts:
        if o == "-c":
            coy = int(v)
        elif o == "-d":
            dte = int(v)
        elif o == "-h":
            hst = v
        elif o == "-l":
            loc = v
        elif o == "-m":
            mth = int(v)
        elif o == "-p":
            num = int(v)
        elif o == "-r":
            rcf = v
    mf = MainFrame(xdisplay=False)
    mf.dbm = Dbase(rcdic=loadRcFile(rcfile=rcf))
    if not mf.dbm.err:
        mf.dbm.openDbase()
        sql = Sql(mf.dbm, "ctlynd")
        if not num:
            num = sql.getRec("ctlynd", cols=["max(cye_period)"],
                where=[("cye_cono", "=", coy)], limit=1)[0]
        per = getPeriods(mf, coy, num)
        if per[1] and per[2]:
            per = (num, (per[0].work, per[0].disp), (per[1].work, per[1].disp))
            ex = st6020(**{"mf": mf, "conum": coy, "period": per,
                "capnm": "paul", "args": (loc, dte, hst, mth)})
        else:
            print("Invalid Period %s for Company %s" % (num, coy))
        mf.dbm.closeDbase()

# vim:set ts=4 sw=4 sts=4 expandtab:
