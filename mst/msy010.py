"""
SYNOPSIS
    Financial Year End routine.

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
from TartanClasses import ASD, CCD, GetCtl, ProgressBar, PwdConfirm, Sql
from TartanClasses import TartanDialog
from tartanFunctions import getPeriods, copyList, doAutoAge, mthendDate
from tartanFunctions import showError
from tartanWork import tabdic

class msy010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.final = self.opts["args"]
                self.doEnd()
            else:
                self.drawScreen()
                if "wait" in self.opts:
                    self.df.mstFrame.wait_window()
                else:
                    self.opts["mf"].startLoop()

    def setVariables(self):
        self.gc = GetCtl(self.opts["mf"])
        ctlsys = self.gc.getCtl("ctlsys", self.opts["conum"])
        if not ctlsys:
            return
        self.years = ctlsys["sys_years"]
        if self.years and self.years < 7:
            showError(self.opts["mf"].body, "History",
                """At least 7 years history should be retained.

Please select Control --> System Record Maintenance and change the Years to Keep field""")
            return
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        tabs = ["ctlsys", "ctlynd", "ftable"]
        self.mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            self.mod.append(ctlmst["ctm_modules"][x:x+2])
        if "AR" in self.mod:
            tabs.append("assctl")
        if "CR" in self.mod:
            tabs.append("crsage")
        if "DR" in self.mod:
            tabs.append("drsage")
        if "GL" in self.mod:
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"], ctlctl, ["ret_inc"]):
                return
            self.ri_acc = ctlctl["ret_inc"]
            tabs.extend(["genbal", "genmst", "gentrn"])
        if "LN" in self.mod:
            tabs.append("lonctl")
        if "ML" in self.mod:
            tabs.append("memage")
            tabs.append("memctl")
        if "RC" in self.mod:
            tabs.append("rcactl")
        if "RT" in self.mod:
            tabs.append("rtlctl")
        if "WG" in self.mod:
            tabs.append("wagctl")
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.c_per = int(self.opts["period"][0])
        self.start = self.opts["period"][1][0]
        self.end = self.opts["period"][2][0]
        self.cur = int(self.opts["period"][2][0] / 100)
        self.l_per = self.sql.getRec("ctlynd", cols=["max(cye_period)"],
            where=[("cye_cono", "=", self.opts["conum"])], limit=1)[0]
        self.last, self.oldf = self.sql.getRec("ctlynd",
            cols=["cye_last", "cye_final"], where=[("cye_cono", "=",
            self.opts["conum"]), ("cye_period", "=", self.opts["period"][0])],
            limit=1)[:2]
        if self.oldf == "Y" and "args" not in self.opts:
            cf = PwdConfirm(self.opts["mf"], conum=0, system="MST",
                code="YearEnd")
            if cf.pwd and cf.flag == "ok":
                return True
            if not cf.pwd:
                showError(self.opts["mf"].body, "Year-End Error",
                    "This Period Has Already Been Finalised")
            return
        return True

    def drawScreen(self):
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = [
            (("T",0,0,0),"OD1",10,"Starting Date","",
                self.start,"N",None,None,None,None,("efld",)),
            [("T",0,1,0),"ID1",10,"Ending Date ","Ending Date",
                self.end,"N",self.doDate,None,None,None,("efld",)],
            (("T",0,2,0),("IRB",r1s),0,"Finalise","",
                self.oldf,"N",self.doFinal,None,None,None,None,"""Finalising a financial period prevents any further data capture for that period as well as any previous periods i.e. if you finalise a period all previous financial periods are also automatically finalised.""")]
        if self.last:
            fld[1][1] = "OD1"
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doEnd,"y"),), txit=(self.doExit,))

    def doDate(self, frt, pag, r, c, p, i, w):
        if w <= self.start:
            return "Invalid Year End Date"
        self.end = w
        self.cur = int(w / 100)

    def doFinal(self, frt, pag, r, c, p, i, w):
        if w == "Y":
            if "AR" in self.mod:
                c = self.gc.getCtl("assctl", self.opts["conum"])
                if not c:
                    return "Missing Asset Control"
                if c["cta_glint"] == "Y" and c["cta_lastp"] < self.cur:
                    return "Depreciation Has Not Been Raised for Assets"
            if "LN" in self.mod:
                c = self.gc.getCtl("lonctl", self.opts["conum"])
                if not c:
                    return "Missing Loans Control"
                lst = c["cln_last"]
                glt = c["cln_glint"]
                drt = c["cln_drte"]
                crt = c["cln_crte"]
                lst = c["cln_last"]
                if glt == "Y" and (drt or crt) and lst < self.end:
                    return "Interest Has Not Been Raised for Loans"
            if "ML" in self.mod:
                c = self.gc.getCtl("memctl", self.opts["conum"])
                if not c:
                    return "Missing Members Control"
                if c["mcm_glint"] == "Y" and c["mcm_lme"] < self.end:
                    return "A Month-End Has Not Been Completed for Members"
            if "RC" in self.mod:
                c = self.gc.getCtl("rcactl", self.opts["conum"])
                if not c:
                    return "Missing Rentals Control"
                if c["cte_glint"] == "Y" and c["cte_lme"] < self.end:
                    return "A Month-End Has Not Been Completed for Rentals"
            if "RT" in self.mod:
                c = self.gc.getCtl("rtlctl", self.opts["conum"])
                if not c:
                    return "Missing Rentals Control"
                if c["ctr_glint"] == "Y" and c["ctr_lme"] < self.end:
                    return "A Month-End Has Not Been Completed for Rentals"
            if "WG" in self.mod:
                c = self.gc.getCtl("wagctl", self.opts["conum"])
                if not c:
                    return "Missing Salaries Control"
                glt = c["ctw_glint"]
                rte = c["ctw_i_rate"]
                lst = c["ctw_i_date"]
                if glt == "Y" and rte and lst < self.end:
                    return "Interest Has Not Been Raised for Staff Loans"
        self.final = w

    def doEnd(self):
        if "args" not in self.opts:
            self.df.closeProcess()
            pb = ProgressBar(self.opts["mf"].body, mxs=self.c_per,
                typ=("F", "Processing Periods"))
        for per in range(0, self.c_per + 1):
            if "args" not in self.opts:
                pb.displayProgress(per)
            chk = self.sql.getRec("ctlynd", cols=["cye_final"],
                where=[("cye_cono", "=", self.opts["conum"]), ("cye_period",
                "=", per)], limit=1)
            if self.oldf == "Y" or chk[0] != "Y":
                self.retinc = 0
                self.doYearEnd(per)
        if "args" not in self.opts:
            pb.closeProgress()
        if self.years:
            self.doDropYears()
        self.opts["mf"].dbm.commitDbase()
        if "args" not in self.opts:
            self.doExit()

    def doYearEnd(self, per):
        self.sql.updRec("ctlynd", cols=["cye_last", "cye_final"],
            data=[self.sysdtw, self.final], where=[("cye_cono", "=",
            self.opts["conum"]), ("cye_period", "=", per)])
        if per == self.c_per:
            start_c = self.start
            end_c = self.end
            if (per + 1) > self.l_per:
                newy = int(end_c / 10000)
                newm = (int(end_c / 100) % 100) + 1
                if newm > 12:
                    newy += 1
                    newm -= 12
                news = (newy * 10000) + (newm * 100) + 1
                newy = int(end_c / 10000) + 1
                newm = int(end_c / 100) % 100
                newe = (newy * 10000) + (newm * 100) + 1
                newe = mthendDate(newe)
                self.sql.insRec("ctlynd", data=[self.opts["conum"], (per + 1),
                    news, newe, 0, "N"])
        else:
            s, e, f = getPeriods(self.opts["mf"], self.opts["conum"], per)
            if s is None or e is None:
                return
            start_c = s.work
            end_c = e.work
        sp = int(start_c / 100)
        ep = int(end_c / 100)
        s, e, f = getPeriods(self.opts["mf"], self.opts["conum"], (per + 1))
        start_n = s.work
        if "GL" not in self.mod:
            return
        self.sql.delRec("genbal", where=[("glo_cono", "=", self.opts["conum"]),
            ("glo_trdt", "=", start_n)])
        gm = self.sql.getRec("genmst", cols=["glm_acno, glm_type"],
            where=[("glm_cono", "=", self.opts["conum"])])
        if gm:
            for ac in gm:
                ov = self.sql.getRec("genbal", cols=["glo_cyr"],
                    where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno",
                    "=", ac[0]), ("glo_trdt", "=", start_c)], limit=1)
                if not ov:
                    ov = CCD(0, "SD", 13.2)
                else:
                    ov = CCD(ov[0], "SD", 13.2)
                cy = self.sql.getRec("gentrn",
                    cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono",
                    "=", self.opts["conum"]), ("glt_acno", "=", ac[0]),
                    ("glt_curdt", "between", sp, ep)], limit=1)
                if not cy[0]:
                    cy = CCD(0, "SD", 13.2)
                else:
                    cy = CCD(cy[0], "SD", 13.2)
                bal = float(ASD(ov.work) + ASD(cy.work))
                if ac[1] == "P":
                    self.retinc = float(ASD(self.retinc) + ASD(bal))
                    bal = 0.00
                self.sql.insRec("genbal", data=[self.opts["conum"], ac[0],
                    start_n,bal])
            ri_bal = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.ri_acc), ("glo_trdt", "=", start_n)], limit=1)
            if not ri_bal:
                self.sql.insRec("genbal", data=[self.opts["conum"],
                    self.ri_acc, start_n, self.retinc])
            else:
                bal = float(ASD(ri_bal[0]) + ASD(self.retinc))
                self.sql.updRec("genbal", cols=["glo_cyr"], data=[bal],
                    where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno",
                    "=", self.ri_acc), ("glo_trdt", "=", start_n)])

    def doDropYears(self):
        """
        TABLES is a list of tables to be actioned as follows:

        [tran_table, date_column, [amount columns], mfile_table]
        """
        TABLES = [
            ["asstrn", "ast_curdt", ["ast_amt1", "ast_amt2"], "assmst"],
            ["bkmtrn", "bkt_curdt", ["bkt_tramt"], "bkmmst"],
            ["chglog"],
            ["crspay", "cpt_date", []],
            ["crstrn", "crt_curdt", ["crt_tramt"], "crsmst"],
            ["ctlbat", "btm_curdt", []],
            ["ctllog"],
            ["ctlnot"],
            ["ctlvtf", "vtt_curdt", []],
            ["drstrn", "drt_curdt", ["drt_tramt"], "drsmst"],
            ["emllog"],
            ["genbal", "glo_trdt", []],
            ["genbud", "glb_curdt", []],
            ["gendtt", "gdt_curdt", []],
            ["genrct", "grt_date", []],
            ["gentrn", "glt_curdt", ["glt_tramt"], "genmst"],
            ["lontrn", "lnt_curdt", ["lnt_tramt"], "lonmf2"],
            ["memtrn", "mlt_curdt", ["mlt_tramt"], "memmst"],
            ["memtrs", "mst_trdt", []],
            ["rcaowt", "rot_curdt", ["rot_tramt"], "rcaowm"],
            ["rcatnt", "rtu_curdt", ["rtu_tramt"], "rcatnm"],
            ["rtltrn", "rtt_curdt", ["rtt_tramt"], "rtlmst"],
            ["slsiv1", "si1_date", []],
            ["strpom", "pom_date", []],
            ["strtrn", "stt_curdt", ["stt_qty", "stt_cost"], "strmf1"],
            ["wagltf", "wlt_curdt", ["wlt_amt"], "waglmf"],
            ["wagtf1", "wt1_date", []],
            ["wagtf2", "wt2_date", []]]
        ynds = self.sql.getRec("ctlynd", where=[("cye_cono", "=",
            self.opts["conum"])], order="cye_period")
        if len(ynds) <= self.years:
            return
        last = ynds[len(ynds) - (self.years + 1)]
        sdate = last[self.sql.ctlynd_col.index("cye_start")]
        edate = last[self.sql.ctlynd_col.index("cye_end")]
        etime = (edate * 10000) + 9999
        emldt = "%04i-%02i-99 99:99" % (int(edate / 10000),
            (int(edate / 100) % 100))
        ecurdt = int(edate / 100)
        count = 0
        for ynd in ynds:
            if ynd[1] < last[1]:
                self.sql.delRec("ctlynd", where=[("cye_cono", "=",
                    self.opts["conum"]), ("cye_period", "=", ynd[1])])
            else:
                self.sql.updRec("ctlynd", cols=["cye_period"], data=[count],
                    where=[("cye_cono", "=", self.opts["conum"]),
                    ("cye_period", "=", ynd[1])])
                count += 1
        tables = self.sql.getRec("ftable", order="ft_tabl")
        ourtab = []
        for tab in tables:
            ourtab.append(tab[0])
        tabs = list(tabdic.keys())
        if "args" not in self.opts:
            pb = ProgressBar(self.opts["mf"].body, typ=("G",
                "Dropping Periods Older Than %s Years" % self.years))
        sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        for tab in TABLES:
            if "args" not in self.opts:
                pb.displayProgress()
            if tab[0] not in ourtab:
                continue
            if tab[0] == "chglog":
                key = "%03i%s" % (self.opts["conum"], "%")
                sql.delRec(tab[0], where=[("chg_key", "like", key),
                    ("chg_dte", "<=", etime)])
                continue
            if tab[0] == "ctllog":
                sql.delRec(tab[0], where=[("clg_start", "<=", etime)])
                continue
            if tab[0] == "ctlnot":
                sql.delRec(tab[0], where=[("not_cono", "=",
                    self.opts["conum"]), ("not_date", "<=", edate)])
                continue
            if tab[0] == "emllog":
                sql.delRec(tab[0], where=[("eml_dtt", "<=", emldt)])
                continue
            ftt = self.sql.getRec("ftable", where=[("ft_tabl",
                "=", tab[0])])
            pfxt = ftt[0][4].split("_")[0]
            coyt = None
            for k in ftt:
                for f in k[4:]:
                    if f.count("_cono"):
                        coyt = f
                        break
                if coyt:
                    break
            if coyt:
                whrt = [(coyt, "=", self.opts["conum"])]
            else:
                whrt = []
            if tab[2]:
                ftm = self.sql.getRec("ftable", where=[("ft_tabl",
                    "=", tab[3]), ("ft_seq=1",)], limit=1)
                pfxm = ftm[4].split("_")[0]
                keyt = []
                keym = []
                coym = None
                for c in ftm[4:]:
                    if c:
                        if c.count("_cono"):
                            coym = c
                        keym.append(c)
                        t = c.replace(pfxm, pfxt)
                        keyt.append(t)
                if coym:
                    whrm = [(coym, "=", self.opts["conum"])]
                else:
                    whrm = []
            if not tab[2]:
                if tab[1].count("_curdt"):
                    whrt.append((tab[1], "<=", ecurdt))
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "crspay":
                    whrt.extend([("cpt_date", "<=", edate), ("cpt_flag",
                        "=", "Y")])
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "drsrcm":
                    whrt.append((tab[1], "<=", ecurdt))
                    recs = sql.getRec(tables=tab[0], where=whrt)
                    for num, rec in enumerate(recs):
                        if "args" not in self.opts and not num % 10:
                            pb.displayProgress()
                        sql.delRec(tab[0], where=[("dcm_cono", "=", rec[0]),
                            ("dcm_num", "=", rec[1])])
                        sql.delRec("drsrct", where=[("dct_cono", "=", rec[0]),
                            ("dct_num", "=", rec[1])])
                elif tab[0] == "genbal":
                    whrt.append((tab[1], "<=", sdate))
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "genrct":
                    whrt.append((tab[1], "<=", sdate))
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "memtrs":
                    whrt.append((tab[1], "<=", sdate))
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "strpom":
                    whrt.append((tab[1], "<=", edate))
                    recs = sql.getRec(tables=tab[0], where=whrt)
                    for num, rec in enumerate(recs):
                        if "args" not in self.opts and not num % 10:
                            pb.displayProgress()
                        sql.delRec(tab[0], where=[("pom_cono", "=", rec[0]),
                            ("pom_ordno", "=", rec[1])])
                        sql.delRec("strpot", where=[("pot_cono", "=", rec[0]),
                            ("pot_ordno", "=", rec[1])])
                elif tab[0] == "slsiv1":
                    whrt.append((tab[1], "<=", edate))
                    recs = sql.getRec(tables=tab[0], where=whrt)
                    for num, rec in enumerate(recs):
                        if "args" not in self.opts and not num % 10:
                            pb.displayProgress()
                        sql.delRec(tab[0], where=[("si1_cono", "=", rec[0]),
                            ("si1_rtn", "=", rec[1]), ("si1_docno", "=",
                            rec[2])])
                        sql.delRec("slsiv2", where=[("si2_cono", "=", rec[0]),
                            ("si2_rtn", "=", rec[1]), ("si2_docno", "=",
                            rec[2])])
                        sql.delRec("slsiv3", where=[("si3_cono", "=", rec[0]),
                            ("si3_rtn", "=", rec[1]), ("si3_docno", "=",
                            rec[2])])
                elif tab[0] == "strpom":
                    whrt.append((tab[1], "<=", edate))
                    recs = sql.getRec(tables=tab[0], where=whrt)
                    for num, rec in enumerate(recs):
                        if "args" not in self.opts and not num % 10:
                            pb.displayProgress()
                        sql.delRec(tab[0], where=[("pom_cono", "=", rec[0]),
                            ("pom_ordno", "=", rec[1])])
                        sql.delRec("strpot", where=[("pot_cono", "=", rec[0]),
                            ("pot_ordno", "=", rec[1])])
                elif tab[0] == "wagtf1":
                    whrt.append((tab[1], "<=", sdate))
                    sql.delRec(tab[0], where=whrt)
                elif tab[0] == "wagtf2":
                    whrt.append((tab[1], "<=", sdate))
                    sql.delRec(tab[0], where=whrt)
            else:
                recs = sql.getRec(tables=tab[3], where=whrm)
                for num, rec in enumerate(recs):
                    if "args" not in self.opts and not num % 10:
                        pb.displayProgress()
                    whr = copyList(whrt)
                    for k in keyt:
                        if not k.count("_cono"):
                            dat = rec[getattr(sql, "%s_col" % tab[0]).index(k)]
                            whr.append((k, '=', dat))
                    if tab[0] == "asstrn":
                        whr.append(("ast_mtyp", "<>", 1))
                        col = ["ast_mtyp"]
                        grp = "ast_cono, ast_group, ast_code, ast_mtyp"
                        lim = 0
                    elif tab[0] == "rcatnt":
                        col = ["rtu_cnum", "rtu_mtyp"]
                        grp = "rtu_cono, rtu_owner, rtu_code, rtu_acno, "\
                            "rtu_cnum, rtu_mtyp"
                        lim = 0
                    elif tab[0] == "rtltrn":
                        col = ["rtt_cnum"]
                        grp = "rtt_cono, rtt_code, rtt_acno, rtt_cnum"
                        lim = 0
                    elif tab[0] == "strtrn":
                        col = ["stt_loc"]
                        grp = "stt_cono, stt_group, stt_code, stt_loc"
                        lim = 0
                    elif tab[0] == "wagltf":
                        mt = sql.getRec("wagltf", cols=["wlt_loan",
                            "max(wlt_curdt)"], where=[("wlt_cono", "=",
                            rec[0]), ("wlt_empno", "=", rec[1])],
                            group="wlt_cono, wlt_empno, wlt_loan",
                            order="wlt_cono, wlt_empno, wlt_loan")
                        for m in mt:
                            if m[1] >= ecurdt:
                                continue
                            b = sql.getRec("wagltf",
                                cols=["sum(wlt_amt)"],
                                where=[
                                    ("wlt_cono", "=", rec[0]),
                                    ("wlt_empno", "=", rec[1]),
                                    ("wlt_loan", "=", m[0])],
                                limit=1)
                            if not b[0]:
                                continue
                            sql.delRec("waglmf", where=[("wlm_cono", "=",
                                rec[0]), ("wlm_empno", "=", rec[1]),
                                ("wlm_loan", "=", m[0])])
                            sql.delRec("wagltf", where=[("wlt_cono", "=",
                                rec[0]), ("wlt_empno", "=", rec[1]),
                                ("wlt_loan", "=", m[0])])
                        continue
                    else:
                        col = []
                        grp = None
                        lim = 1
                    for c in tab[2]:
                        col.append("sum(%s)" % c)
                    whr.append((tab[1], "<=", ecurdt))
                    bals = sql.getRec(tables=tab[0], cols=col, where=whr,
                        group=grp, order=grp, limit=lim)
                    if not bals:
                        continue
                    sql.delRec(tab[0], where=whr)
                    if tab[0] == "asstrn":
                        from tartanWork import armvtp
                        for bal in bals:
                            # Create Transactions
                            if not bal[1] and not bal[2]:
                                continue
                            data = rec[:3]
                            data.extend([3, "Bal-Fwd", "Bal-Fwd", edate,
                                bal[0], bal[1], bal[2], 0, ecurdt,
                                "%s Brought Forward" % armvtp[bal[0]-1][1],
                                "", "", self.opts["capnm"], self.sysdtw, 0])
                            sql.insRec(tab[0], data=data)
                    elif tab[0] == "bkmtrn" and bals[0]:
                        data = rec[:2]
                        data.extend([5, "Bal-Fwd", "Bal-Fwd", edate, "",
                            bals[0], 0, ecurdt, "Brought Forward", "", "",
                            self.opts["capnm"], self.sysdtw, 0])
                        sql.insRec(tab[0], data=data)
                    elif tab[0] == "crstrn" and bals[0]:
                        data = rec[:2]
                        data.extend([3, "Bal-Fwd", "Bal-Fwd", edate, "",
                            bals[0], 0, 0, ecurdt, self.sysdtw, "Y", bals[0],
                            "Brought Forward", "", "", self.opts["capnm"],
                            self.sysdtw, 0])
                        sql.insRec(tab[0], data=data)
                        # Re-Age Transactions
                        doAutoAge(self.opts["mf"].dbm, "crs", rec[0], rec[1])
                    elif tab[0] == "drstrn" and bals[0]:
                        data = rec[:3]
                        data.extend([3, "Bal-Fwd", "Bal-Fwd", edate, "",
                            bals[0], 0, ecurdt, "Brought Forward", "", "",
                            self.opts["capnm"], self.sysdtw, 0])
                        sql.insRec(tab[0], data=data)
                        # Re-Age Transactions
                        doAutoAge(self.opts["mf"].dbm, "drs", rec[0], rec[1],
                            rec[2])
                    elif tab[0] == "gentrn" and bals[0]:
                        continue
                    elif tab[0] == "memtrn" and bals[0]:
                        data = rec[:2]
                        data.extend([3, "Bal-Fwd", "Bal-Fwd", edate, bals[0],
                            0, ecurdt, "", 0, "Brought Forward", "", "",
                            self.opts["capnm"], self.sysdtw, 0])
                        sql.insRec(tab[0], data=data)
                        # Re-Age Transactions
                        doAutoAge(self.opts["mf"].dbm, "mem", rec[0], rec[1])
                    elif tab[0] == "rcaowt" and bals[0]:
                        data = rec[:2]
                        data.extend([4, "Bal-Fwd", "Bal-Fwd", edate, bals[0],
                            0, ecurdt, "Brought Forward", "", "",
                            self.opts["capnm"], self.sysdtw, 0])
                        sql.insRec(tab[0], data=data)
                    elif tab[0] == "rcatnt":
                        from tartanWork import rcmvtp
                        for bal in bals:
                            # Create Transactions
                            if not bal[2]:
                                continue
                            data = rec[:4]
                            data.extend([bal[0], 4, "Bal-Fwd", "Bal-Fwd",
                                edate, bal[1], bal[2], 0, ecurdt,
                                "%s Brought Forward" % rcmvtp[bal[1]-1][1],
                                "", "", self.opts["capnm"], self.sysdtw, 0])
                            sql.insRec(tab[0], data=data)
                    elif tab[0] == "rtltrn":
                        for bal in bals:
                            # Create Transactions
                            if not bal[1]:
                                continue
                            data = rec[:3]
                            data.extend([bal[0], 4, "Bal-Fwd", "Bal-Fwd",
                                edate, bal[1], 0, ecurdt, "Brought Forward",
                                "", "", self.opts["capnm"], self.sysdtw, 0])
                            sql.insRec(tab[0], data=data)
                    elif tab[0] == "strtrn":
                        for bal in bals:
                            # Create Transactions
                            if not bal[1] and not bal[2]:
                                continue
                            data = rec[:3]
                            if bal[1] < 0:
                                typ = 6
                            else:
                                typ = 5
                            data.extend([bal[0], edate, typ, "Bal-Fwd",
                                "Bal-Fwd", "", bal[1], bal[2], 0, ecurdt,
                                "Brought Forward", 0, "", "", "", 0, "",
                                self.opts["capnm"], self.sysdtw, 0])
                            sql.insRec(tab[0], data=data)
        if "args" not in self.opts:
            pb.closeProgress()

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

if __name__ == "__main__":
    import getopt, sys
    from TartanClasses import Dbase, MainFrame
    from tartanFunctions import loadRcFile
    try:
        opts, args = getopt.getopt(sys.argv[1:],"c:p:f:r:")
    except:
        print("")
        print("Usage: -c conum -p period -f final -r rcfile")
        print("")
        sys.exit()
    coy = 1
    num = None
    fin = "N"
    rcf = None
    for o, v in opts:
        if o == "-c":
            coy = int(v)
        elif o == "-p":
            num = int(v)
        elif o == "-f":
            fin = v.upper()
        elif o == "-r":
            rcf = v
    if not num:
        num = 0
    mf = MainFrame(xdisplay=False)
    mf.dbm = Dbase(rcdic=loadRcFile(rcfile=rcf))
    if not mf.dbm.err:
        mf.dbm.openDbase()
        per = getPeriods(mf, coy, num)
        if per[1] and per[2]:
            per = (num, (per[0].work, per[0].disp), (per[1].work, per[1].disp))
            ex = msy010(**{"mf": mf, "conum": coy, "period": per,
            "capnm": "paul", "args": fin})
        else:
            print("Invalid Period %s for Company %s" % (num, coy))
        mf.dbm.closeDbase()

# vim:set ts=4 sw=4 sts=4 expandtab:
