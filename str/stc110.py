"""
SYNOPSIS
    Stores Control File Maintenance.

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
from TartanClasses import GetCtl, Sql, TartanDialog

class stc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        mods = ctlmst["ctm_modules"]
        self.genleg = False
        self.slspos = False
        for x in range(0, len(mods), 2):
            if mods[x:x + 2] == "GL":
                self.genleg = True
            elif mods[x:x + 2] == "PS":
                self.slspos = True
        tabs = ["strctl", "strloc", "strgmu", "strcmu", "strprc",
            "tplmst", "chglog"]
        if self.genleg:
            tabs.extend(["ctlctl", "genmst"])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.acc = self.sql.getRec("strctl", where=[("cts_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "N", "N", 1, "N",
                "purchase_order", "", ""]
        else:
            self.new = False
        if self.genleg:
            self.ctl = [
                ["stk_soh", "Stock on Hand", 0],
                ["stk_susp", "Stock Reconciliation", 0]]
            if self.slspos:
                self.ctl.extend([
                    ["pos_cash", "Cash Takings", 0],
                    ["pos_card", "Card Takings", 0],
                    ["pos_vchr", "Vouchers", 0]])
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            for num, ctl in enumerate(self.ctl):
                if ctl[0] in ctlctl:
                    self.ctl[num][2] = ctlctl[ctl[0]]
        self.locs = self.acc[self.sql.strctl_col.index("cts_locs")]
        return True

    def drawDialog(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "where": [
                ("tpm_type", "=", "O"),
                ("tpm_system", "=", "STR")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("No","N"),("Last Cost","L"),("Average Cost","A"))
        if self.genleg:
            glm = {
                "stype": "R",
                "tables": ("genmst",),
                "cols": (
                    ("glm_acno", "", 0, "G/L-Num"),
                    ("glm_desc", "", 30, "Description")),
                "where": [
                    ("glm_cono", "=", self.opts["conum"])]}
            fld = [
                (("T",0,0,0),("IRB",r1s),0,"G/L Integration","",
                    self.acc[1],"N",self.doGlint,None,None,None),
                (("T",0,1,0),"IUI",7,self.ctl[0][1],"",
                    self.ctl[0][2],"N",self.doGenAcc,glm,None,("efld",)),
                (("T",0,1,0),"ONA",30,""),
                (("T",0,2,0),"IUI",7,self.ctl[1][1],"",
                    self.ctl[1][2],"N",self.doGenAcc,glm,None,("efld",)),
                (("T",0,2,0),"ONA",30,"")]
            if self.slspos:
                fld.extend([
                    (("T",0,3,0),"IUI",7,self.ctl[2][1],"",
                        self.ctl[2][2],"N",self.doGenAcc,glm,None,("efld",)),
                    (("T",0,3,0),"ONA",30,""),
                    (("T",0,4,0),"IUI",7,self.ctl[3][1],"",
                        self.ctl[3][2],"N",self.doGenAcc,glm,None,("efld",)),
                    (("T",0,4,0),"ONA",30,""),
                    (("T",0,5,0),"IUI",7,self.ctl[4][1],"",
                        self.ctl[4][2],"N",self.doGenAcc,glm,None,("efld",)),
                    (("T",0,5,0),"ONA",30,"")])
                seq = 6
            else:
                seq = 3
        else:
            fld = []
            seq = 0
        fld.extend([
            (("T",0,seq,0),("IRB",r1s),0,"Multiple Locations","",
                self.acc[2],"N",self.doLocs,None,None,None),
            (("T",0,seq + 1,0),"IUI",1,"Number of Price Levels","",
                self.acc[3],"N",None,None,None,("between",1,5)),
            (("T",0,seq + 2,0),("IRB",r2s),0,"Automatic Markup","",
                self.acc[4],"N",None,None,None,None,None,
                "Calculate Selling Prices Based on Markup Percentages"),
            (("T",0,seq + 3,0),"INA",20,"Orders Template","",
                self.acc[5],"N",self.doTplNam,tpm,None,None),
            (("T",0,seq + 4,0),"ITX",50,"Email Address","",
                self.acc[6],"N",None,None,None,("email",))])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,1),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt)
        if not self.new:
            s = 0
            for n, f in enumerate(self.acc[1:-1]):
                if not self.genleg and not n:
                    continue
                self.df.loadEntry("T", 0, s, data=f)
                s += 1
                if not n:
                    for c in self.ctl:
                        self.df.loadEntry("T", 0, s, data=c[2])
                        s += 1
                        self.df.loadEntry("T", 0, s, data=self.getDes(c[2]))
                        s += 1
            self.df.focusField("T", 0, 1, clr=False)

    def doGlint(self, frt, pag, r, c, p, i, w):
        if self.slspos:
            idx = 11
            skp = "sk10"
        else:
            idx = 5
            skp = "sk4"
        if w == "N":
            for x in range(1, idx):
                self.df.loadEntry(frt, pag, p+x, data="")
            return skp

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        des = self.getDes(w)
        if not des:
            return "Invalid Account Number"
        self.df.loadEntry(frt, pag, p+1, data=des)

    def getDes(self, acno):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", acno)], limit=1)
        if acc:
            return acc[0]
        else:
            return ""

    def doLocs(self, frt, pag, r, c, p, i, w):
        self.locs = w

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "O"), ("tpm_system", "=", "STR")], limit=1)
        if not acc:
            return "Invalid Template Name"

    def doEnd(self):
        data = [self.opts["conum"]]
        if not self.genleg:
            data.append("N")
        if self.genleg:
            if self.slspos:
                idx = 11
                pos = (1, 3, 5, 7, 9)
            else:
                idx = 5
                pos = (1, 3)
        for x, d in enumerate(self.df.t_work[0][0]):
            if x and self.genleg and x < idx:
                if x in pos:
                    y = int((x - 1) / 2)
                    chk = self.sql.getRec("ctlctl", where=[("ctl_cono",
                        "=", self.opts["conum"]), ("ctl_code", "=",
                        self.ctl[y][0])], limit=1)
                    if chk:
                        self.sql.updRec("ctlctl", cols=["ctl_conacc"], data=[d],
                            where=[("ctl_cono", "=", self.opts["conum"]),
                            ("ctl_code", "=", self.ctl[y][0])])
                    else:
                        self.sql.insRec("ctlctl", data=[self.opts["conum"],
                            self.ctl[y][0], self.ctl[y][1], d, "", "N", "N"])
                else:
                    continue
            else:
                data.append(d)
        if self.new:
            self.sql.insRec("strctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.strctl_col
            data.append(self.acc[col.index("cts_xflag")])
            self.sql.updRec("strctl", data=data, where=[("cts_cono",
                "=", self.opts["conum"])])
            # Check and Fix Markup prices
            plevs = data[self.sql.strctl_col.index("cts_plevs")]
            automu = data[self.sql.strctl_col.index("cts_automu")]
            if automu in ("A", "L"):
                grps = self.sql.getRec("strgrp", cols=["gpm_group"],
                    where=[("gpm_cono", "=", self.opts["conum"])])
                for grp in grps:
                    for lvl in range(1, plevs + 1):
                        self.sql.delRec("strcmu", where=[("smc_cono",
                            "=", self.opts["conum"]), ("smc_group",
                            "=", grp[0]), ("smc_level", "=", lvl),
                            ("smc_markup", "=", 0)])
                        gmu = self.sql.getRec("strgmu", cols=["smg_markup"],
                            where=[("smg_cono", "=", self.opts["conum"]),
                            ("smg_group", "=", grp[0]), ("smg_level", "=",
                            lvl)], limit=1)
                        if gmu:
                            if not gmu[0]:
                                self.sql.delRec("strgmu", where=[("smg_cono",
                                    "=", self.opts["conum"]), ("smg_group",
                                    "=", grp[0]), ("smg_level", "=", lvl)])
                            self.sql.delRec("strcmu", where=[("smc_cono",
                                "=", self.opts["conum"]), ("smc_group", "=",
                                grp[0]), ("smc_level", "=", lvl),
                                ("smc_markup", "=", gmu[0])])
                self.sql.delRec("strprc", where=[("stp_cono", "=",
                    self.opts["conum"])])
            # Chglog
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["strctl", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        if self.locs == "N":
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]),
                ("srl_loc", "=", "1")], limit=1)
            if not acc:
                self.sql.insRec("strloc", data=[self.opts["conum"],
                    "1", "Location Number One", "", "", "", ""])
        self.opts["mf"].dbm.commitDbase()
        self.doExit()

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
