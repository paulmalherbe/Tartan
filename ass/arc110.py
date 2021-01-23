"""
SYNOPSIS
    Asset Control File Maintenance.

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

class arc110(object):
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
        tabs = ["assctl", "chglog"]
        if self.genleg:
            tabs.extend(["ctlctl", "genmst"])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.acc = self.sql.getRec("assctl", where=[("cta_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "N", "N", 0, "", ""]
        else:
            self.new = False
        if self.genleg:
            self.ctl = [["ass_sls", "Sale of Assets", 0]]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            for num, ctl in enumerate(self.ctl):
                if ctl[0] in ctlctl:
                    self.ctl[num][2] = ctlctl[ctl[0]]
        return True

    def drawDialog(self):
        r1s = (("Yes","Y"),("No","N"))
        if self.genleg:
            glm = {
                "stype": "R",
                "tables": ("genmst",),
                "cols": (
                    ("glm_acno", "", 0, "G/L-Num"),
                    ("glm_desc", "", 30, "Description")),
                "where": [("glm_cono", "=", self.opts["conum"])]}
            fld = [
                (("T",0,0,0),("IRB",r1s),0,"G/L Integration","",
                    self.acc[1],"N",self.doGlint,None,None,None),
                (("T",0,1,0),"IUI",7,self.ctl[0][1],"",
                    self.ctl[0][2],"N",self.doGenAcc,glm,None,("efld",)),
                (("T",0,1,0),"ONA",30,"")]
            seq = 2
        else:
            fld = []
            seq = 0
        fld.extend([
            (("T",0,seq,0),("IRB",r1s),0,"Receiver Dep","",
                self.acc[2],"N",None,None,None,None),
            (("T",0,seq + 1,0),"Id2",7,"Last Dep Period","",
                self.acc[3],"N",None,None,None,None),
            (("T",0,seq + 2,0),"ITX",50,"Email Address","",
                self.acc[4],"N",None,None,None,("email",))])
        but = (("Quit",None,self.doExit,1,None,None),)
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
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

    def getDes(self, acno):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", acno)], limit=1)
        if acc:
            return acc[0]
        return ""

    def doGlint(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            return "sk2"

    def doGenAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid G/L Account"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doEnd(self):
        data = [self.opts["conum"]]
        if not self.genleg:
            data.append("N")
        for x, d in enumerate(self.df.t_work[0][0]):
            if self.genleg and x < 3:
                if x in (1,):
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
                elif x in (2,):
                    continue
                else:
                    data.append(d)
            else:
                data.append(d)
        if self.new:
            self.sql.insRec("assctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.assctl_col
            data.append(self.acc[col.index("cta_xflag")])
            self.sql.updRec("assctl", data=data, where=[("cta_cono",
                "=", self.opts["conum"])])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["assctl", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]), 0])
        self.opts["mf"].dbm.commitDbase()
        self.doExit()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
