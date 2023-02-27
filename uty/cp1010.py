"""
SYNOPSIS
    Change Batch Period.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanWork import allsys

class cp1010:
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.mods = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            self.mods.append(ctlmst["ctm_modules"][x:x+2])
        tabs = ["ctlmst", "ctlynd", "ctlvtf", "ctlbat", "asstrn", "bkmtrn",
            "crstrn", "crsage", "drstrn", "drsage", "gentrn", "lontrn",
            "memtrn", "memage", "rcaowt", "rcatnt", "rtltrn", "wagltf"]
        self.syss = {
            "ASS": ["assctl", "cta_glint", [0, 2, 6, 4, 4],
                [["ast_cono", "ast_type", "ast_batch", "ast_curdt"]]],
            "BKM": ["bkmctl", "cbk_glint", [0, 0, 1, 6, 2, 4, 1, 6],
                [["bkt_cono", "bkt_type", "bkt_batch", "bkt_curdt"]]],
            "CRS": ["crsctl", "ctc_glint", [0, 5, 6, 4, 5, 2, 2],
                [["crt_cono", "crt_type", "crt_batch", "crt_curdt"]],
                ["crt_ref1", "cra_cono", "cra_curdt", "cra_atyp", "cra_aref"]],
            "DRS": ["drsctl", "ctd_glint", [0, 1, 6, 4, 1, 2, 6],
                [["drt_cono", "drt_type", "drt_batch", "drt_curdt"]],
                ["drt_ref1", "dra_cono", "dra_curdt", "dra_atyp", "dra_aref"]],
            "GEN": [],
            "LON": ["lonctl", "cln_glint", [0, 2, 6, 4, 4],
                [["lnt_cono", "lnt_type", "lnt_batch", "lnt_curdt"]]],
            "MEM": ["memctl", "mcm_glint", [0, 1, 2, 4, 1, 6, 6],
                [["mlt_cono", "mlt_type", "mlt_batch", "mlt_curdt"]],
                ["mlt_refno", "mta_cono", "mta_curdt", "mta_atyp", "mta_aref"]],
            "RCA": ["rcactl", "cte_glint", [0, 1, 6, 2, 4], [
                ["rot_cono", "rot_type", "rot_batch", "rot_curdt"],
                ["rtu_cono", "rtu_type", "rtu_batch", "rtu_curdt"]]],
            "RTL": ["rtlctl", "ctr_glint", [0, 1, 6, 2, 4],
                [["rtt_cono", "rtt_type", "rtt_batch", "rtt_curdt"]]],
            "SLN": ["wagctl", "ctw_glint", [0, 4, 2, 2, 6, 4],
                [["wlt_cono", "wlt_type", "wlt_batch", "wlt_curdt"]]]}
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=__name__)
        if self.sql.error:
            return
        self.i_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        return True

    def mainProcess(self):
        tit = "Change Batch Current Period"
        data = []
        for ss in allsys:
            if ss not in self.syss:
                continue
            if allsys[ss][1] not in self.mods:
                continue
            data.append((ss, allsys[ss][0]))
        data.sort()
        sss = {
            "stype": "C",
            "titl": "Systems",
            "head": ["COD", "Description"],
            "data": data}
        self.ttt = {
            "stype": "C",
            "titl": "Batch Types",
            "head": ["BT", "Description"],
            "data": []}
        self.bat = {
            "stype": "R",
            "tables": ("ctlbat",),
            "cols": (
                ("btm_batno", "", 0, "Bat-Num"),
                ("btm_curdt", "", 0, "Cur-Dte")),
            "where": [
                ("btm_cono", "=", self.opts["conum"]),
                ("btm_curdt", "between", self.i_per, self.e_per)],
            "whera": (
                ("T", "btm_styp", 0, 0),
                ("T", "btm_rtyp", 2, 0)),
            "order": "btm_curdt, btm_batno"}
        fld = (
            (("T",0,0,0),"IUA",3,"System Code","",
                "","N",self.doSysCod,sss,None,("notblank",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUI",2,"Transaction Type","",
                "","N",self.doTrnTyp,self.ttt,None,("notzero",)),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),"INa",7,"Batch Number","",
                "","N",self.doBatNum,self.bat,None,("notblank",)),
            (("T",0,3,0),"OD2",7,"Captured Period"),
            (("T",0,4,0),"ID2",7,"Change to Period","",
                "","N",self.doNewPer,None,None,("efld",)))
        but = (("Exit", None, self.doExit, 0, ("T",0,1), ("T",0,0)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt)

    def doSysCod(self, frt, pag, r, c, p, i, w):
        if w not in self.syss:
            return "Invalid System"
        if allsys[w][1] not in self.mods:
            return "Invalid System"
        self.syscod = w
        self.ttt["data"] = []
        exec("from tartanWork import %strtp as trtp" % allsys[w][1].lower())
        setattr(self, "trtp", locals()["trtp"])
        for n, t in enumerate(self.trtp):
            self.ttt["data"].append((n+1, t[1]))
        self.df.loadEntry(frt, pag, p+1, data=allsys[self.syscod][0])

    def doTrnTyp(self, frt, pag, r, c, p, i, w):
        if (w < 1 or w > len(self.trtp)):
            return "Invalid Type"
        self.battyp = w
        rtn = self.trtp[w-1][1]
        self.df.loadEntry(frt, pag, p+1, data=rtn)

    def doBatNum(self, frt, pag, r, c, p, i, w):
        self.batnum = w
        self.btm = [
            ("btm_cono", "=", self.opts["conum"]),
            ("btm_styp", "=", self.syscod),
            ("btm_rtyp", "=", self.battyp),
            ("btm_batno", "=", self.batnum)]
        chk = self.sql.getRec("ctlbat", cols=["btm_curdt"], where=self.btm,
            limit=1)
        if not chk:
            return "Invalid Batch(B)"
        per = self.doChkPer(chk[0])
        if per:
            return per
        self.oldper = chk[0]
        self.df.loadEntry(frt, pag, p+1, data=self.oldper)

    def doNewPer(self, frt, pag, r, c, p, i, w):
        per = self.doChkPer(w)
        if per:
            return per
        self.newper = w

    def doChkPer(self, per):
        if per < self.i_per or per > self.e_per:
            return "Invalid Period(P)"
        whr = (
            ("cye_cono", "=", self.opts["conum"]),
            ("cye_start", ">=", per),
            ("cye_end", "<=", per))
        chk = self.sql.getRec("ctlynd", cols=["cye_final"], where=whr, limit=1)
        if chk and chk[0] == "Y":
            return "Invalid Period(F)"

    def doEnd(self):
        self.sql.updRec("ctlbat", cols=["btm_curdt"], data=[self.newper],
            where=self.btm)
        if self.syscod == "GEN":
            if self.battyp not in list(range(1, 8)):
                raise Exception
            if self.battyp == 7:
                gltyp = (2, 6)
            else:
                gltyp = (self.battyp,)
            glint = "N"
        else:
            ctl = self.syss[self.syscod]
            glint = self.gc.getCtl(ctl[0], self.opts["conum"])[ctl[1]]
            if glint == "Y":
                gltyp = (ctl[2][self.battyp],)
        sqv = [
            ("vtt_cono", "=", self.opts["conum"]),
            ("vtt_curdt", "=", self.oldper),
            ("vtt_styp", "=", self.syscod[0])]
        if self.syscod == "GEN":
            sqv.append(("vtt_ttyp", "in", gltyp))
        else:
            sqv.append(("vtt_ttyp", "=", self.battyp))
        sqv.append(("vtt_batch", "=", self.batnum))
        self.sql.updRec("ctlvtf", cols=["vtt_curdt"], data=[self.newper],
            where=sqv)
        if self.syscod == "GEN" or glint == "Y":
            sqt = [
                ("glt_cono", "=", self.opts["conum"]),
                ("glt_curdt", "=", self.oldper),
                ("glt_type", "in", gltyp),
                ("glt_batch", "=", self.batnum)]
            tmp = sqt[:]
            tmp.append(("glt_recon", "=", self.oldper))
            self.sql.updRec("gentrn", cols=["glt_recon"], data=[self.newper],
                where=tmp)
            self.sql.updRec("gentrn", cols=["glt_curdt"], data=[self.newper],
                where=sqt)
        if self.syscod == "GEN":
            codes = list(self.syss.keys())
        else:
            codes = [self.syscod]
        for syscod in codes:
            if syscod == "GEN":
                continue
            ctl = self.syss[syscod]
            if self.syscod == "GEN":
                trtyp = []
                for cod in gltyp:
                    trtyp.append(self.syss[syscod][2].index(cod))
            else:
                trtyp = (self.battyp,)
            if syscod == "RCA":
                tabs = ["rcaowt", "rcatnt"]
            elif syscod == "SLN":
                tabs = ["wagltf"]
            else:
                tabs = ["%strn" % syscod.lower()]
            for seq, tab in enumerate(tabs):
                sqt = [
                    (ctl[3][seq][0], "=", self.opts["conum"]),
                    (ctl[3][seq][1], "in", trtyp),
                    (ctl[3][seq][2], "=", self.batnum),
                    (ctl[3][seq][3], "=", self.oldper)]
                if syscod in ("CRS", "DRS", "MEM"):
                    recs = self.sql.getRec(tab, cols=[ctl[4][0]], where=sqt)
                self.sql.updRec(tab, cols=[ctl[3][seq][3]],
                    data=[self.newper], where=sqt)
            if syscod in ("CRS", "DRS", "MEM"):
                tab = "%sage" % syscod.lower()
                for rec in recs:
                    sqa = (
                        (ctl[4][1], "=", self.opts["conum"]),
                        (ctl[4][2], "=", self.oldper),
                        (ctl[4][3], "in", trtyp),
                        (ctl[4][4], "=", rec[0]))
                    self.sql.updRec("%sage" % syscod.lower(), cols=[ctl[4][2]],
                        data=[self.newper], where=sqa)
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

if __name__ == "__main__":
    from TartanClasses import Dbase, MainFrame
    from tartanFunctions import loadRcFile
    mf = MainFrame(rcdic=loadRcFile("/home/paul/rcf/newbrm"))
    mf.dbm = Dbase(rcdic=mf.rcdic, screen=mf.window)
    mf.dbm.openDbase()
    rpt = cp1010(**{"mf": mf, "conum": 1, "conam": "Company One"})

# vim:set ts=4 sw=4 sts=4 expandtab:
