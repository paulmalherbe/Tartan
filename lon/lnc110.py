"""
SYNOPSIS
    Loans Control File Maintenance.

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
from TartanClasses import GetCtl, Sql, TartanDialog

class lnc110(object):
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
        tabs = ["lonctl", "tplmst", "chglog"]
        if self.genleg:
            tabs.extend(["ctlctl", "genmst"])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.acc = self.sql.getRec("lonctl", where=[("cln_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "N", "D", "A", "A", 0, 0, 0,
                "statement_loan", "", ""]
        else:
            self.new = False
        if self.genleg:
            self.ctl = [
                ["lon_ctl", "Loans Control", 0],
                ["int_rec", "Interest Received", 0],
                ["int_pay", "Interest Paid", 0]]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            for num, ctl in enumerate(self.ctl):
                if ctl[0] in ctlctl:
                    self.ctl[num][2] = ctlctl[ctl[0]]
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
                ("tpm_type", "=", "S"),
                ("tpm_system", "=", "LON")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Daily","D"),("Monthly","M"))
        r3s = (("Anniversary","A"),("Financial","F"))
        r4s = (("Annual","A"),("Bi-Annual","B"))
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
                (("T",0,3,0),"IUI",7,self.ctl[2][1],"",
                    self.ctl[2][2],"N",self.doGenAcc,glm,None,("efld",)),
                (("T",0,3,0),"ONA",30,"")]
            seq = 4
        else:
            fld = []
            seq = 0
        fld.extend([
            (("T",0,seq,0),("IRB",r2s),0,"Interest Method","",
                self.acc[2],"N",None,None,None,None),
            (("T",0,seq + 1,0),("IRB",r3s),0,"Capitalisation Base","",
                self.acc[3],"N",None,None,None,None),
            (("T",0,seq + 2,0),("IRB",r4s),0,"Capitalisation Freq","",
                self.acc[4],"N",None,None,None,None),
            (("T",0,seq + 3,0),"IUD",6.2,"Debit Rate","",
                self.acc[5],"N",None,None,None,("efld",)),
            (("T",0,seq + 4,0),"IUD",6.2,"Credit Rate","",
                self.acc[6],"N",None,None,None,("efld",)),
            (("T",0,seq + 5,0),"Id1",10.0,"Last Interest Date","",
                self.acc[7],"N",None,None,None,("efld",)),
            (("T",0,seq + 6,0),"INA",20,"Statement Template","",
                self.acc[8],"N",self.doTplNam,tpm,None,("efld",)),
            (("T",0,seq + 7,0),"ITX",50,"Email Address","",
                self.acc[9],"N",None,None,None,("email",))])
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
                if n == 0:
                    for c in self.ctl:
                        self.df.loadEntry("T", 0, s, data=c[2])
                        s += 1
                        self.df.loadEntry("T", 0, s, data=self.getDes(c[2]))
                        s += 1
            self.df.focusField("T", 0, 1, clr=False)

    def doGlint(self, frt, pag, r, c, p, i, w):
        if w == "N":
            for x in range(1, 7):
                self.df.loadEntry(frt, pag, p+x, data="")
            return "sk6"

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

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "S"), ("tpm_system", "=", "LON")], limit=1)
        if not acc:
            return "Invalid Template"

    def doEnd(self):
        data = [self.opts["conum"]]
        if not self.genleg:
            data.append("N")
        for x, d in enumerate(self.df.t_work[0][0]):
            if self.genleg and x < 7:
                if x in (1, 3, 5):
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
                elif x in (2, 4, 6):
                    continue
                else:
                    data.append(d)
            else:
                data.append(d)
        if self.new:
            self.sql.insRec("lonctl", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.lonctl_col
            data.append(self.acc[col.index("cln_xflag")])
            self.sql.updRec("lonctl", data=data, where=[("cln_cono",
                "=", self.opts["conum"])])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["lonctl", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.doExit()

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col + 1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
