"""
SYNOPSIS
    Creditors Control File Maintenance.

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

class crc110(object):
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
        for x in range(0, len(mods), 2):
            if mods[x:x + 2] == "GL":
                self.genleg = True
                break
        tabs = ["crsctl", "tplmst", "chglog"]
        if self.genleg:
            tabs.extend(["ctlctl", "genmst"])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.acc = self.sql.getRec("crsctl", where=[("ctc_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "N", "E", "", 0, 0,
                "remittance_advice", "", ""]
        else:
            self.new = False
        if self.genleg:
            self.ctl = [
                ["crs_ctl", "Creditors Control", 0],
                ["dis_rec", "Discount Received", 0]]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            for num, ctl in enumerate(self.ctl):
                if ctl[0] in ctlctl:
                    self.ctl[num][2] = ctlctl[ctl[0]]
        return True

    def drawDialog(self):
        ctl = {
            "stype": "R",
            "tables": ("ctlctl", "genmst"),
            "cols": (
                ("ctl_code", "", 0, "Ctl-Code"),
                ("ctl_conacc", "", 0, "G/L-Num"),
                ("glm_desc", "", 30, "Description")),
            "where": [
                ("ctl_cono", "=", self.opts["conum"]),
                ("ctl_code", "like", "bank_%"),
                ("glm_cono=ctl_cono",),
                ("glm_acno=ctl_conacc",)],
            "index": 1}
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "where": [
                ("tpm_type", "=", "R"),
                ("tpm_system", "=", "CRS")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Exclusive","E"),("Inclusive","I"))
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
                (("T",0,2,0),"ONA",30,""),
                (("T",0,3,0),("IRB",r2s),0,"G/L Input Method","",
                    self.acc[2],"N",None,None,None,None),
                (("T",0,4,0),"INA",4,"Best Account Code","Best",
                    self.acc[3],"N",self.doBestAcc,None,None,("efld",)),
                (("T",0,5,0),"IUI",2,"Best Account Type","BT",
                    self.acc[4],"N",None,None,None,("efld",)),
                (("T",0,6,0),"IUI",7,"Bank Account Code","Bank-Ac",
                    self.acc[5],"N",self.doBankAcc,ctl,None,("efld",))]
            seq = 7
        else:
            fld = []
            seq = 0
        fld.extend([
            (("T",0,seq,0),"INA",20,"Remittance Template","",
                self.acc[6],"N",self.doTplNam,tpm,None,("efld",)),
            (("T",0,seq + 1,0),"ITX",50,"Email Address","",
                self.acc[7],"N",None,None,None,("email",))])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,1),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt)
        if not self.new:
            s = 0
            for n, f in enumerate(self.acc[1:-1]):
                if not self.genleg and n < 5:
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
        self.glint = w
        if self.glint == "N":
            for x in range(1, 5):
                self.df.loadEntry(frt, pag, p+x, data="")
            self.df.loadEntry(frt, pag, p+5, data="E")
            return "sk5"

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

    def doBestAcc(self, frt, pag, r, c, p, i, w):
        if not w or self.glint == "N":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "sk2"

    def doBankAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables=["genmst", "ctlctl"], cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=", w),
                ("ctl_code", "like", "bank_%"), ("ctl_cono=glm_cono",),
                ("ctl_conacc=glm_acno",)], limit=1)
        if not acc:
            return "Invalid Bank Account"

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "R"), ("tpm_system", "=", "CRS")], limit=1)
        if not acc:
            return "Invalid Template"

    def doEnd(self):
        data = [self.opts["conum"]]
        if not self.genleg:
            data.extend(["N", "E", "", 0, 0])
        for x, d in enumerate(self.df.t_work[0][0]):
            if self.genleg and x < 9:
                if x in (1, 3):
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
                elif x in (2, 4):
                    continue
                else:
                    data.append(d)
            else:
                data.append(d)
        if self.new:
            self.sql.insRec("crsctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.crsctl_col
            data.append(self.acc[col.index("ctc_xflag")])
            self.sql.updRec("crsctl", data=data, where=[("ctc_cono", "=",
                self.opts["conum"])])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["crsctl", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
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
