"""
SYNOPSIS
    General Ledger Check Integration Control Balances.

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
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter

class gl6030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.checkControls():
            if self.setVariables():
                self.mainProcess()
                self.opts["mf"].startLoop()

    def checkControls(self):
        gc = GetCtl(self.opts["mf"])
        ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
        if not ctlctl:
            return
        check = False
        self.tabs = ["genbal", "gentrn"]
        assctl = gc.getCtl("assctl", self.opts["conum"], error=False)
        if assctl and assctl["cta_glint"] == "Y":
            check = True
            self.arint = "Y"
            self.tabs.extend(["assgrp", "asstrn"])
        else:
            self.arint = "N"
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"], error=False)
        if bkmctl and bkmctl["cbk_glint"] == "Y" and "bkm_ctl" in ctlctl:
            check = True
            self.bkint = "Y"
            self.bkm_ctl = ctlctl["bkm_ctl"]
            self.tabs.append("bkmtrn")
        else:
            self.bkint = "N"
            self.bkm_ctl = None
        crsctl = gc.getCtl("crsctl", self.opts["conum"], error=False)
        if crsctl and crsctl["ctc_glint"] == "Y" and "crs_ctl" in ctlctl:
            check = True
            self.crint = "Y"
            self.crs_ctl = ctlctl["crs_ctl"]
            self.tabs.append("crstrn")
        else:
            self.crint = "N"
            self.crs_ctl = None
        drsctl = gc.getCtl("drsctl", self.opts["conum"], error=False)
        if drsctl and drsctl["ctd_glint"] == "Y" and "drs_ctl" in ctlctl:
            check = True
            self.drint = "Y"
            self.drs_ctl = ctlctl["drs_ctl"]
            self.tabs.append("drstrn")
        else:
            self.drint = "N"
            self.drs_ctl = None
        lonctl = gc.getCtl("lonctl", self.opts["conum"], error=False)
        if lonctl and lonctl["cln_glint"] == "Y" and "lon_ctl" in ctlctl:
            check = True
            self.lnint = "Y"
            self.lon_ctl = ctlctl["lon_ctl"]
            self.tabs.append("lontrn")
        else:
            self.lnint = "N"
            self.lon_ctl = None
        memctl = gc.getCtl("memctl", self.opts["conum"], error=False)
        if memctl and memctl["mcm_glint"] == "Y" and "mem_ctl" in ctlctl:
            check = True
            self.mlint = "Y"
            self.mem_ctl = ctlctl["mem_ctl"]
            self.tabs.append("memtrn")
        else:
            self.mlint = "N"
            self.mem_ctl = None
        rcactl = gc.getCtl("rcactl", self.opts["conum"], error=False)
        if rcactl and rcactl["cte_glint"] == "Y":
            check = True
            self.rcint = "Y"
            self.own_ctl = ctlctl["rca_own"]
            self.tnt_ctl = ctlctl["rca_tnt"]
            self.dep_ctl = ctlctl["rca_dep"]
            self.tabs.extend(["rcaowt", "rcatnt"])
        else:
            self.rcint = "N"
            self.own_ctl = None
            self.tnt_ctl = None
            self.dep_ctl = None
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"], error=False)
        if rtlctl and rtlctl["ctr_glint"] == "Y":
            check = True
            self.rtint = "Y"
            self.tabs.extend(["rtlprm", "rtltrn"])
        else:
            self.rtint = "N"
        strctl = gc.getCtl("strctl", self.opts["conum"], error=False)
        if strctl and strctl["cts_glint"] == "Y" and "stk_soh" in ctlctl:
            check = True
            self.stint = "Y"
            self.str_ctl = ctlctl["stk_soh"]
            self.tabs.append("strtrn")
        else:
            self.stint = "N"
            self.str_ctl = None
        wagctl = gc.getCtl("wagctl", self.opts["conum"], error=False)
        if wagctl and wagctl["ctw_glint"] == "Y" and "wag_slc" in ctlctl:
            check = True
            self.wgint = "Y"
            self.sln_ctl = ctlctl["wag_slc"]
            self.tabs.append("wagltf")
        else:
            self.wgint = "N"
            self.sln_ctl = None
        return check

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, self.tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.start = self.opts["period"][1][0]
        self.s_per = int(self.start / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Check Integrated Controls (%s)" % self.__class__.__name__)
        fld = (
            (("T",0,0,0),"ID2",7,"Cut-Off Period","",
                self.e_per,"N",self.doPeriod,None,None,("efld",)),)
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doPeriod(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.opts["period"] = w

    def doEnd(self):
        self.df.closeProcess()
        if self.arint == "Y":
            self.gar_bal = 0.0
            grp = self.sql.getRec("assgrp", cols=["asg_assacc",
                "asg_depacc"], where=[("asg_cono", "=", self.opts["conum"])])
            if grp:
                done = []
                for g in grp:
                    for acc in g:
                        if acc in done:
                            continue
                        o = self.sql.getRec("genbal", cols=["glo_cyr"],
                            where=[("glo_cono", "=", self.opts["conum"]),
                            ("glo_acno", "=", acc), ("glo_trdt", "=",
                            self.start)], limit=1)
                        if o:
                            b = CCD(o[0], "SD", 14.2)
                        else:
                            b = CCD(0, "SD", 14.2)
                        self.gar_bal = float(ASD(self.gar_bal) + ASD(b.work))
                        o = self.sql.getRec("gentrn",
                            cols=["round(sum(glt_tramt), 2)"],
                            where=[("glt_cono", "=", self.opts["conum"]),
                            ("glt_acno", "=", acc), ("glt_curdt", ">=",
                            self.s_per), ("glt_curdt", "<=",
                            self.opts["period"])], limit=1)
                        if o and o[0]:
                            b = CCD(float(o[0]), "SD", 14.2)
                        else:
                            b = CCD(0, "SD", 14.2)
                        self.gar_bal = float(ASD(self.gar_bal) + ASD(b.work))
                        done.append(acc)
            o = self.sql.getRec("asstrn",
                cols=["round(sum(ast_amt1), 2)"], where=[("ast_cono", "=",
                self.opts["conum"]), ("ast_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                self.ass_bal = o[0]
            else:
                self.ass_bal = 0.00
        else:
            self.gar_bal = 0.00
            self.ass_bal = 0.00
        if self.bkint == "Y":
            self.gbk_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.bkm_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gbk_bal = float(ASD(self.gbk_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.bkm_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gbk_bal = float(ASD(self.gbk_bal) + ASD(b.work))
            bal = self.sql.getRec("bkmtrn",
                cols=["round(sum(bkt_tramt), 2)"], where=[("bkt_cono", "=",
                self.opts["conum"]), ("bkt_curdt", "<=", self.opts["period"])],
                limit=1)
            if bal and bal[0]:
                self.bkm_bal = bal[0]
            else:
                self.bkm_bal = 0.00
        else:
            self.gbk_bal = 0.00
            self.bkm_bal = 0.00
        if self.crint == "Y":
            self.gcr_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.crs_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gcr_bal = float(ASD(self.gcr_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.crs_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gcr_bal = float(ASD(self.gcr_bal) + ASD(b.work))
            bal = self.sql.getRec("crstrn",
                cols=["round(sum(crt_tramt), 2)"], where=[("crt_cono", "=",
                self.opts["conum"]), ("crt_curdt", "<=", self.opts["period"])],
                limit=1)
            if bal and bal[0]:
                self.crs_bal = float(ASD(0) - ASD(bal[0]))
            else:
                self.crs_bal = 0.00
        else:
            self.gcr_bal = 0.00
            self.crs_bal = 0.00
        if self.drint == "Y":
            self.gdr_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.drs_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gdr_bal = float(ASD(self.gdr_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.drs_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gdr_bal = float(ASD(self.gdr_bal) + ASD(b.work))
            bal = self.sql.getRec("drstrn",
                cols=["round(sum(drt_tramt), 2)"], where=[("drt_cono", "=",
                self.opts["conum"]), ("drt_curdt", "<=", self.opts["period"])],
                limit=1)
            if bal and bal[0]:
                self.drs_bal = bal[0]
            else:
                self.drs_bal = 0.00
        else:
            self.gdr_bal = 0.00
            self.drs_bal = 0.00
        if self.lnint == "Y":
            self.gln_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.lon_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gln_bal = float(ASD(self.gln_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.lon_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gln_bal = float(ASD(self.gln_bal) + ASD(b.work))
            bal = self.sql.getRec("lontrn",
                cols=["round(sum(lnt_tramt), 2)"], where=[("lnt_cono", "=",
                self.opts["conum"]), ("lnt_curdt", "<=", self.opts["period"])],
                limit=1)
            if bal and bal[0]:
                self.lon_bal = bal[0]
            else:
                self.lon_bal = 0.00
        else:
            self.gln_bal = 0.00
            self.lon_bal = 0.00
        if self.mlint == "Y":
            self.gml_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.mem_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gml_bal = float(ASD(self.gml_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.mem_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gml_bal = float(ASD(self.gml_bal) + ASD(b.work))
            bal = self.sql.getRec("memtrn",
                cols=["round(sum(mlt_tramt), 2)"], where=[("mlt_cono", "=",
                self.opts["conum"]), ("mlt_curdt", "<=", self.opts["period"])],
                limit=1)
            if bal and bal[0]:
                self.mem_bal = bal[0]
            else:
                self.mem_bal = 0.00
        else:
            self.gml_bal = 0.00
            self.mem_bal = 0.00
        if self.rcint == "Y":
            self.grc_own = 0.00
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]),
                ("glo_acno", "=", self.own_ctl), ("glo_trdt", "=",
                self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_own = float(ASD(self.grc_own) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"],
                where=[("glt_cono", "=", self.opts["conum"]),
                ("glt_acno", "=", self.own_ctl), ("glt_curdt", ">=",
                self.s_per), ("glt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_own = float(ASD(self.grc_own) + ASD(b.work))
            o = self.sql.getRec("rcaowt",
                cols=["round(sum(rot_tramt), 2)"], where=[("rot_cono", "=",
                self.opts["conum"]), ("rot_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                self.rct_own = o[0]
            else:
                self.rct_own = 0.00
            self.grc_tnt = 0.00
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]),
                ("glo_acno", "=", self.tnt_ctl), ("glo_trdt", "=",
                self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_tnt = float(ASD(self.grc_tnt) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"],
                where=[("glt_cono", "=", self.opts["conum"]),
                ("glt_acno", "=", self.tnt_ctl), ("glt_curdt", ">=",
                self.s_per), ("glt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_tnt = float(ASD(self.grc_tnt) + ASD(b.work))
            o = self.sql.getRec("rcatnt",
                cols=["round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
                self.opts["conum"]), ("rtu_curdt", "<=", self.opts["period"]),
                ("rtu_mtyp", "<>", 2)], limit=1)
            if o and o[0]:
                self.rct_tnt = o[0]
            else:
                self.rct_tnt = 0.00
            self.grc_dep = 0.00
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]),
                ("glo_acno", "=", self.dep_ctl), ("glo_trdt", "=",
                self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_dep = float(ASD(self.grc_dep) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"],
                where=[("glt_cono", "=", self.opts["conum"]),
                ("glt_acno", "=", self.dep_ctl), ("glt_curdt", ">=",
                self.s_per), ("glt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.grc_dep = float(ASD(self.grc_dep) + ASD(b.work))
            o = self.sql.getRec("rcatnt",
                cols=["round(sum(rtu_tramt), 2)"], where=[("rtu_cono", "=",
                self.opts["conum"]), ("rtu_curdt", "<=", self.opts["period"]),
                ("rtu_mtyp", "=", 2)], limit=1)
            if o and o[0]:
                self.rct_dep = o[0]
            else:
                self.rct_dep = 0.00
        else:
            self.grc_own = 0.00
            self.grc_tnt = 0.00
            self.grc_dep = 0.00
            self.rct_own = 0.00
            self.rct_tnt = 0.00
            self.rct_dep = 0.00
        if self.rtint == "Y":
            self.grt_bal = 0.0
            prm = self.sql.getRec("rtlprm", cols=["rtp_rtlacc"],
                where=[("rtp_cono", "=", self.opts["conum"])])
            if prm:
                done = []
                for acc in prm:
                    if acc[0] in done:
                        continue
                    o = self.sql.getRec("genbal", cols=["glo_cyr"],
                        where=[("glo_cono", "=", self.opts["conum"]),
                        ("glo_acno", "=", acc[0]), ("glo_trdt", "=",
                        self.start)], limit=1)
                    if o:
                        b = CCD(o[0], "SD", 14.2)
                    else:
                        b = CCD(0, "SD", 14.2)
                    self.grt_bal = float(ASD(self.grt_bal) + ASD(b.work))
                    o = self.sql.getRec("gentrn",
                        cols=["round(sum(glt_tramt), 2)"],
                        where=[("glt_cono", "=", self.opts["conum"]),
                        ("glt_acno", "=", acc[0]), ("glt_curdt", ">=",
                        self.s_per), ("glt_curdt", "<=", self.opts["period"])],
                        limit=1)
                    if o and o[0]:
                        b = CCD(float(o[0]), "SD", 14.2)
                    else:
                        b = CCD(0, "SD", 14.2)
                    self.grt_bal = float(ASD(self.grt_bal) + ASD(b.work))
                    done.append(acc[0])
            o = self.sql.getRec("rtltrn",
                cols=["round(sum(rtt_tramt), 2)"], where=[("rtt_cono", "=",
                self.opts["conum"]), ("rtt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                self.rtl_bal = o[0]
            else:
                self.rtl_bal = 0.00
        else:
            self.grt_bal = 0.00
            self.rtl_bal = 0.00
        if self.stint == "Y":
            self.gst_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.str_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gst_bal = float(ASD(self.gst_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.str_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gst_bal = float(ASD(self.gst_bal) + ASD(b.work))
            o = self.sql.getRec("strtrn",
                cols=["round(sum(stt_cost), 2)"], where=[("stt_cono", "=",
                self.opts["conum"]), ("stt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                self.str_bal = o[0]
            else:
                self.str_bal = 0.00
        else:
            self.gst_bal = 0.00
            self.str_bal = 0.00
        if self.wgint == "Y":
            self.gsl_bal = 0.0
            o = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.sln_ctl), ("glo_trdt", "=", self.start)], limit=1)
            if o:
                b = CCD(o[0], "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gsl_bal = float(ASD(self.gsl_bal) + ASD(b.work))
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.opts["conum"]), ("glt_acno", "=", self.sln_ctl),
                ("glt_curdt", ">=", self.s_per), ("glt_curdt", "<=",
                self.opts["period"])], limit=1)
            if o and o[0]:
                b = CCD(float(o[0]), "SD", 14.2)
            else:
                b = CCD(0, "SD", 14.2)
            self.gsl_bal = float(ASD(self.gsl_bal) + ASD(b.work))
            o = self.sql.getRec("wagltf",
                cols=["round(sum(wlt_amt), 2)"], where=[("wlt_cono", "=",
                self.opts["conum"]), ("wlt_curdt", "<=", self.opts["period"])],
                limit=1)
            if o and o[0]:
                self.sln_bal = o[0]
            else:
                self.sln_bal = 0.00
        else:
            self.gsl_bal = 0.00
            self.sln_bal = 0.00
        head = ("%03u %-30s %2s %33s %3s %6s" % (self.opts["conum"],
            self.opts["conam"], "", self.sysdttm, "", self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=head)
        self.pgnum = 0
        self.pglin = 999
        self.pageHeading(head)
        if self.arint == "Y":
            des = "Assets Register"
            a1 = CCD(self.gar_bal, "SD", 20.2)
            a2 = CCD(self.ass_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.bkint == "Y":
            des = "Bookings Ledger"
            a1 = CCD(self.gbk_bal, "SD", 20.2)
            a2 = CCD(self.bkm_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.crint == "Y":
            des = "Creditors Ledger"
            a1 = CCD(self.gcr_bal, "SD", 20.2)
            a2 = CCD(self.crs_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.drint == "Y":
            des = "Debtors Ledger"
            a1 = CCD(self.gdr_bal, "SD", 20.2)
            a2 = CCD(self.drs_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.lnint == "Y":
            des = "Loans Ledger"
            a1 = CCD(self.gln_bal, "SD", 20.2)
            a2 = CCD(self.lon_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.mlint == "Y":
            des = "Members Ledger"
            a1 = CCD(self.gml_bal, "SD", 20.2)
            a2 = CCD(self.mem_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.rcint == "Y":
            des = "Rental Owners"
            a1 = CCD(self.grc_own, "SD", 20.2)
            a2 = CCD(self.rct_own, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
            des = "Rental Tenants"
            a1 = CCD(self.grc_tnt, "SD", 20.2)
            a2 = CCD(self.rct_tnt, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
            des = "Rental Deposits"
            a1 = CCD(self.grc_dep, "SD", 20.2)
            a2 = CCD(self.rct_dep, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.rtint == "Y":
            des = "Rentals Ledger"
            a1 = CCD(self.grt_bal, "SD", 20.2)
            a2 = CCD(self.rtl_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.stint == "Y":
            des = "Stores Ledger"
            a1 = CCD(self.gst_bal, "SD", 20.2)
            a2 = CCD(self.str_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        if self.wgint == "Y":
            des = "Staff Loans"
            a1 = CCD(self.gsl_bal, "SD", 20.2)
            a2 = CCD(self.sln_bal, "SD", 20.2)
            a = float(ASD(a1.work) - ASD(a2.work))
            a3 = CCD(a, "SD", 20.2)
            self.fpdf.drawText("%-20s %s %s %s" %
                (des, a1.disp, a2.disp, a3.disp))
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header=self.tit, repprt=self.df.repprt, repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def pageHeading(self, desc=None):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(desc)
        self.fpdf.drawText()
        self.fpdf.drawText("%-47s %-7s %20s %5s" % \
            ("General Ledger Integrated Controls up to Period",
            self.df.t_disp[0][0][0], "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText("%-24s %-29s %-16s %-20s" % ("Description",
            "Control Account", "Ledger", "Difference"))
        self.fpdf.underLine(txt=desc)
        self.fpdf.setFont()
        self.pglin = 6

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
