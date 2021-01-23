"""
SYNOPSIS
    Members Ledger Category Maintenance.

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
from TartanClasses import GetCtl, Sql, TartanDialog

class mlc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "genmst", "memctc",
            "memcat", "memtrn", "memctp"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.glint = memctl["mcm_glint"]
        return True

    def mainProcess(self):
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "CD"),
                ("mcc_freq", "", 0, "F"),
                ("mcc_desc", "", 0, "Description", "Y"),
                ("mcc_rgrp", "", 0, "RG")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "mcc_type", 0, 0]]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        prc = {
            "stype": "R",
            "tables": ("memctp",),
            "cols": (
                ("mcp_date", "", 0, "CD"),
                ("mcp_penalty", "", 0, "P-Rte"),
                ("mcp_prorata", "", 0, "P"),
                ("mcp_rate_01", "", 0, "Month-01")),
            "where": [("mcp_cono", "=", self.opts["conum"])],
            "whera": [
                ["T", "mcp_type", 0, 0],
                ["T", "mcp_code", 1, 0]],
            "order": "mcp_date"}
        r1s = (
            ("Fees", "A"),
            ("Category", "B"),
            ("Sports", "C"),
            ("Debentures", "D"))
        r2s = (
            ("Annually", "A"),
            ("Monthly", "M"),
            ("Once Off", "O"),
            ("Never", "N"))
        r3s = (
            ("No", "N"),
            ("1M", "1"),
            ("3M", "3"),
            ("6M", "6"),
            ("Manual", "M"))
        fld = [
            (("T",0,0,0),("IRB",r1s),0,"Category Type","",
                "A","Y",self.doCatType,None,None,None),
            (("T",0,1,0),"I@mcc_code",0,"","",
                "","N",self.doCatCode,cod,None,("notzero",)),
            (("T",0,2,0),"I@mcc_desc",0,"","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"I@mcc_rgrp",0,"","",
                "","N",self.doRgrp,None,None,("notblank",)),
            (("T",0,4,0),("IRB",r2s),0,"Frequency","",
                "A","N",self.doCatFreq,None,None,None),
            (("T",0,5,0),"I@mcc_age_l",0,"","",
                "","N",self.doCatLimit,None,None,("efld",)),
            (("T",0,5,0),"I@mcc_and_s",0,"And Mship","And Length of Service",
                "","N",self.doCatLimit,None,None,("efld",)),
            (("T",0,5,0),"I@mcc_or_s",0,"Or Mship","Or Length of Service",
                "","N",self.doCatLimit,None,None,("efld",)),
            (("T",0,6,0),"I@mcc_ncode",0,"Next Code","",
                "","N",self.doCatNcode,cod,None,None)]
        idx = 7
        if self.glint == "Y":
            fld.extend([
                (("T",0,idx,0),"I@mcc_glac",0,"","",
                    "","N",self.doGlac,glm,None,("efld",)),
                (("T",0,idx,0),"ONA",30,"")])
            idx += 1
        fld.extend([
            (("T",0,idx,0),"I@mcp_date",0,"","",
                "","N",self.doDate,prc,None,("efld",)),
            (("T",0,idx+1,0),"I@mcp_penalty",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+2,0),("IRB",r3s),0,"Pro-Rata","Pro-Rata",
                "N","N",self.doProRata,None,None,None),
            (("T",0,idx+3,0),"I@mcp_rate_01",0,"","",
                "","N",self.doMonth,None,None,("efld",)),
            (("T",0,idx+3,34,46),"I@mcp_rate_02",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+4,0),"I@mcp_rate_03",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+4,34,46),"I@mcp_rate_04",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+5,0),"I@mcp_rate_05",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+5,34,46),"I@mcp_rate_06",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+6,0),"I@mcp_rate_07",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+6,34,46),"I@mcp_rate_08",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+7,0),"I@mcp_rate_09",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+7,34,46),"I@mcp_rate_10",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+8,0),"I@mcp_rate_11",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,idx+8,34,46),"I@mcp_rate_12",0,"","",
                "","N",None,None,None,("efld",))])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCatType(self, frt, pag, r, c, p, i, w):
        self.ctyp = w

    def doCatCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.oldcat = self.sql.getRec("memctc", where=[("mcc_cono", "=",
            self.opts["conum"]), ("mcc_type", "=", self.ctyp), ("mcc_code",
            "=", self.code)], limit=1)
        if self.oldcat:
            self.desc = self.oldcat[self.sql.memctc_col.index("mcc_desc")]
            self.rgrp = self.oldcat[self.sql.memctc_col.index("mcc_rgrp")]
            self.freq = self.oldcat[self.sql.memctc_col.index("mcc_freq")]
            self.age_l = self.oldcat[self.sql.memctc_col.index("mcc_age_l")]
            self.and_s = self.oldcat[self.sql.memctc_col.index("mcc_and_s")]
            self.or_s = self.oldcat[self.sql.memctc_col.index("mcc_or_s")]
            self.ncode = self.oldcat[self.sql.memctc_col.index("mcc_ncode")]
            self.df.loadEntry(frt, pag, p+1, data=self.desc)
            self.df.loadEntry(frt, pag, p+2, data=self.rgrp)
            self.df.loadEntry(frt, pag, p+3, data=self.freq)
            self.df.loadEntry(frt, pag, p+4, data=self.age_l)
            self.df.loadEntry(frt, pag, p+5, data=self.and_s)
            self.df.loadEntry(frt, pag, p+6, data=self.or_s)
            self.df.loadEntry(frt, pag, p+7, data=self.ncode)
            if self.glint == "Y":
                self.glno = self.oldcat[self.sql.memctc_col.index("mcc_glac")]
                self.df.loadEntry(frt, pag, p+8, data=self.glno)
                des = self.sql.getRec("genmst", cols=["glm_desc"],
                    where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno",
                    "=", self.glno)], limit=1)
                if des:
                    self.df.loadEntry("T", 0, p+9, data=des[0])
                idx = 11
            else:
                idx = 9
            if self.freq == "N":
                self.date = 0
                self.oldprc = []
                for x in range(idx, len(self.df.t_work[0][0])):
                    self.df.loadEntry("T", 0, x, data="")
            else:
                self.oldprc = self.sql.getRec("memctp",
                    where=[("mcp_cono", "=", self.opts["conum"]), ("mcp_type",
                    "=", self.ctyp), ("mcp_code", "=", self.code)],
                    order="mcp_date desc", limit=1)
                self.date = self.oldprc[self.sql.memctp_col.index("mcp_date")]
                for n, d in enumerate(self.oldprc[3:-1]):
                    self.df.loadEntry("T", 0, idx+n, data=d)

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w
        if self.ctyp != "C":
            self.rgrp = "NA"
            return "sk1"

    def doRgrp(self, frt, pag, r, c, p, i, w):
        self.rgrp = w

    def doCatFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w
        if self.freq == "N":
            self.age_l = 0
            self.and_s = 0
            self.or_s = 0
            self.ncode = 0
            self.glno = 0
            for x in range(p+1, len(self.df.t_work[0][0])):
                self.df.loadEntry("T", 0, x, data="")
            return "nd"
        if self.ctyp != "B":
            self.age_l = 0
            self.and_s = 0
            self.or_s = 0
            self.ncode = 0
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            self.df.loadEntry(frt, pag, p+3, data=0)
            self.df.loadEntry(frt, pag, p+4, data=0)
            return "sk4"

    def doCatLimit(self, frt, pag, r, c, p, i, w):
        if p == 5:
            self.age_l = w
        elif p == 6:
            self.and_s = w
        else:
            self.or_s = w
            if not self.age_l and not self.and_s and not self.or_s:
                self.ncode = 0
                self.df.loadEntry(frt, pag, p+1, data=0)
                return "sk1"

    def doCatNcode(self, frt, pag, r, c, p, i, w):
        self.ncode = w

    def doGlac(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.glno = w
        self.df.loadEntry("T", 0, p+1, data=acc[0])

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        if not self.oldcat:
            self.oldprc = []
        else:
            self.oldprc = self.sql.getRec("memctp", where=[("mcp_cono",
                "=", self.opts["conum"]), ("mcp_code", "=", self.code),
                ("mcp_type", "=", self.ctyp), ("mcp_date", "=", self.date)],
                limit=1)
        if self.oldprc:
            for n, d in enumerate(self.oldprc[4:-1]):
                self.df.loadEntry(frt, pag, p+1+n, data=d)
        else:
            for n in range(14):
                self.df.clearEntry(frt, pag, c+1+n)

    def doProRata(self, frt, pag, r, c, p, i, w):
        self.prorata = w

    def doMonth(self, frt, pag, r, c, p, i, w):
        if self.oldprc or self.prorata == "M":
            return
        if self.prorata == "N":
            mths = [w] * 12
        elif self.prorata == "1":
            mths = [w]
            for x in range(11, 0, -1):
                mths = mths + [round(w / 12.0 * x, 0)]
        elif self.prorata == "3":
            mths = [w, w, w]
            for x in range(3, 0, -1):
                for _ in range(3):
                    mths = mths + [round(w / 4.0 * x, 0)]
        elif self.prorata == "6":
            mths = [w, w, w, w, w, w]
            for x in range(6):
                mths = mths + [round(w / 2.0, 0)]
        for n, d in enumerate(mths):
            self.df.loadEntry(frt, pag, p+n, data=d)
        if self.prorata == "N":
            return "sk11"

    def doDelete(self):
        mst = self.sql.getRec("memcat", cols=["count(*)"],
            where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_type", "=",
            self.ctyp), ("mlc_code", "=", self.code)], limit=1)
        if mst[0]:
            return "Code in Use (memcat), Not Deleted"
        trn = self.sql.getRec("memtrn", cols=["count(*)"],
            where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_ctyp", "=",
            self.ctyp), ("mlt_ccod", "=", self.code)], limit=1)
        if trn[0]:
            return "Code in Use (memtrn), Not Deleted"
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.delRec("memctc", where=[("mcc_cono", "=", self.opts["conum"]),
            ("mcc_type", "=", self.ctyp), ("mcc_code", "=", self.code)])
        self.sql.insRec("chglog", data=["memctc", "D", "%03i%1s%02i" % \
            (self.opts["conum"], self.ctyp, self.code), "", dte,
            self.opts["capnm"], "", "", "", 0])
        prc = self.sql.getRec("memctp", cols=["mcp_date"],
            where=[("mcp_cono", "=", self.opts["conum"]), ("mcp_type", "=",
            self.ctyp), ("mcp_code", "=", self.code)])
        for date in prc:
            self.sql.delRec("memctp", where=[("mcp_cono", "=",
                self.opts["conum"]), ("mcp_code", "=", self.code), ("mcp_code",
                "=", self.code), ("mcp_date", "=", date)])
            self.sql.insRec("chglog", data=["memctp", "D", "%03i%1s%02i%8s" % \
                (self.opts["conum"], self.ctyp, self.code, date), "", dte,
                self.opts["capnm"], "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        data = [self.opts["conum"], self.ctyp, self.code, self.desc, self.rgrp,
            self.freq, self.age_l, self.and_s, self.or_s, self.ncode]
        if self.glint == "N":
            data.append(0)
        else:
            data.append(self.glno)
        if not self.oldcat:
            self.sql.insRec("memctc", data=data)
        elif data != self.oldcat[:len(data)]:
            col = self.sql.memctc_col
            data.append(self.oldcat[col.index("mcc_xflag")])
            self.sql.updRec("memctc", data=data, where=[("mcc_cono", "=",
                self.opts["conum"]), ("mcc_type", "=", self.ctyp),
                ("mcc_code", "=", self.code)])
            for num, dat in enumerate(self.oldcat):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["memctc", "U",
                        "%03i%1s%02i" % (self.opts["conum"], self.ctyp,
                        self.code), col[num], dte, self.opts["capnm"],
                        str(dat), str(data[num]), "", 0])
        if self.freq != "N":
            data = [self.opts["conum"], self.ctyp, self.code]
            if self.glint == "Y":
                idx = 11
            else:
                idx = 9
            for x in range(idx, idx+15):
                data.append(self.df.t_work[0][0][x])
            if not self.oldprc:
                self.sql.insRec("memctp", data=data)
            elif data != self.oldprc[:len(data)]:
                col = self.sql.memctp_col
                data.append(self.oldcat[col.index("mcp_xflag")])
                self.sql.updRec("memctp", data=data, where=[("mcp_cono", "=",
                    self.opts["conum"]), ("mcp_type", "=", self.ctyp),
                    ("mcp_code", "=", self.code), ("mcp_date", "=",
                    self.date)])
                for num, dat in enumerate(self.oldprc):
                    if dat != data[num]:
                        self.sql.insRec("chglog", data=["memctp", "U",
                            "%03i%1s%02i%8s" % (self.opts["conum"], self.ctyp,
                            self.code, str(self.date)), col[num], dte,
                            self.opts["capnm"], str(dat), str(data[num]),
                            "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
