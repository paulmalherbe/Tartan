"""
SYNOPSIS
    Create and maintain department records.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import chkGenAcc, showError

class ms1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlsys", "ctlmst",
            "ctldep", "genmst", "wagmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        dept = ctlsys["sys_gl_dep"]
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.glint = "N"
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            if ctlmst["ctm_modules"][x:x+2] in ("SL", "WG"):
                dept = "Y"
                wagctl = gc.getCtl("wagctl", self.opts["conum"])
                if not wagctl:
                    self.glint = "N"
                else:
                    self.glint = wagctl["ctw_glint"]
                break
        if dept == "N":
            showError(self.opts["mf"].body, "Error",
                "Departments have Not been Enabled")
            return
        if self.glint == "N":
            self.co1 = 0
            self.sy1 = 0
            self.cm1 = 0
            self.co2 = 0
            self.sy2 = 0
            self.cm2 = 0
        else:
            self.coys = self.sql.getRec("ctlmst", cols=["count(*)"],
                limit=1)[0]
        return True

    def mainProcess(self):
        dep = {
            "stype": "R",
            "tables": ("ctldep",),
            "cols": (
                ("dep_code", "", 0, "Cod"),
                ("dep_name", "", 0, "Name", "Y")),
            "where": [("dep_cono", "=", self.opts["conum"])]}
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        self.fld = [
            (("T",0,0,0),"IUI",3,"Department","Department Code",
                "","N",self.doDepartment,dep,None,("notzero",)),
            (("T",0,1,0),"INA",30,"Name","",
                "","N",self.doName,None,self.doDelete,("notblank",))]
        if self.glint == "Y":
            if self.coys == 1:
                self.fld.append((("T",0,2,0),"OUI",7,"Debit  Company"))
            else:
                self.fld.append((("T",0,2,0),"IUI",7,"Debit  Company","",
                    self.opts["conum"],"N",self.doCoy,coy,None,None))
            self.fld.append((("T",0,2,0),"ONA",30,""))
            self.fld.extend([
                (("T",0,3,0),"IUI",7,"       Salary A/C","",
                    "","N",self.doSal,glm,None,("notzero",)),
                (("T",0,3,0),"ONA",30,""),
                (("T",0,4,0),"IUI",7,"       Commission A/C","",
                    "","N",self.doCom,glm,None,("efld",)),
                (("T",0,4,0),"ONA",30,"")])
            if self.coys == 1:
                self.fld.append((("T",0,5,0),"OUI",7,"Credit Company"))
            else:
                self.fld.append((("T",0,5,0),"IUI",7,"Credit Company","",
                    self.opts["conum"],"N",self.doCoy,coy,None,None))
            self.fld.append((("T",0,5,0),"ONA",30,""))
            self.fld.extend([
                (("T",0,6,0),"IUI",7,"       Salary A/C","",
                    "","N",self.doSal,glm,None,("notzero",)),
                (("T",0,6,0),"ONA",30,""),
                (("T",0,7,0),"IUI",7,"       Commission A/C","",
                    "","N",self.doCom,glm,None,("efld",)),
                (("T",0,7,0),"ONA",30,"")])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doDepartment(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.old = self.sql.getRec("ctldep", where=[("dep_cono", "=",
            self.opts["conum"]), ("dep_code", "=", self.code)], limit=1)
        if not self.old:
            self.new = "Y"
        else:
            self.new = "N"
        self.doLoadRec(self.old)

    def doLoadRec(self, rec):
        if not rec:
            self.df.clearFrame("T", 0)
            self.df.loadEntry("T", 0, 0, data=self.code)
            return
        for num, dat in enumerate(rec[2:-1]):
            if num == 0:
                seq = 1
                self.df.loadEntry("T", 0, seq, data=dat)
                if self.glint == "N":
                    return
                seq += 1
            elif num in (1, 4):
                coy = dat
                nam = self.sql.getRec("ctlmst", cols=["ctm_name"],
                    where=[("ctm_cono", "=", coy)], limit=1)
                self.df.loadEntry("T", 0, seq, data=coy)
                self.df.loadEntry("T", 0, seq+1, data=nam[0])
                seq += 2
            elif num in (2, 3, 5, 6):
                if dat:
                    dsc = self.sql.getRec("genmst", cols=["glm_desc"],
                        where=[("glm_cono", "=", coy), ("glm_acno",
                        "=", dat)], limit=1)
                else:
                    dsc = [""]
                self.df.loadEntry("T", 0, seq, data=dat)
                self.df.loadEntry("T", 0, seq + 1, data=dsc[0])
                seq += 2

    def doName(self, frt, pag, r, c, p, i, w):
        self.name = w
        if self.glint == "Y" and self.coys == 1:
            self.co1 = self.opts["conum"]
            self.co2 = self.opts["conum"]
            self.df.loadEntry(frt, pag, p+1, data=self.opts["conum"])
            self.df.loadEntry(frt, pag, p+2, data=self.opts["conam"])
            return "sk2"

    def doCoy(self, frt, pag, r, c, p, i, w):
        coy = self.sql.getRec("ctlmst", cols=["ctm_name "],
            where=[("ctm_cono", "=", w)], limit=1)
        if not coy:
            return "Invalid Company Number"
        if p == 2:
            self.co1 = w
        else:
            self.co2 = w
        self.df.loadEntry(frt, pag, p+1, coy[0])

    def doSal(self, frt, pag, r, c, p, i, w):
        if p == 4:
            co = self.co1
        else:
            co = self.co2
        chk = chkGenAcc(self.opts["mf"], co, w)
        if type(chk) is str:
            return chk
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

    def doCom(self, frt, pag, r, c, p, i, w):
        if w:
            if p == 6:
                co = self.co1
            else:
                co = self.co2
            chk = chkGenAcc(self.opts["mf"], co, w)
            if type(chk) is str:
                return chk
            self.df.loadEntry(frt, pag, p+1, data=chk[0])
        if p == 6 and self.coys == 1:
            self.df.loadEntry(frt, pag, p+2, data=self.opts["conum"])
            self.df.loadEntry(frt, pag, p+3, data=self.opts["conam"])
            return "sk2"

    def doDelete(self):
        if self.glint == "Y":
            chk = self.sql.getRec("wagmst", where=[("wgm_dept", "=",
                self.code)])
            if chk:
                return "Department is in Use, Not Deleted"
        self.sql.delRec("ctldep", where=[("dep_cono", "=", self.opts["conum"]),
            ("dep_code", "=", self.code)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for num, dat in enumerate(self.df.t_work[0][0]):
            if num in (3, 5, 7, 9, 11, 13):
                continue
            data.append(dat)
        if self.new == "Y":
            self.sql.insRec("ctldep", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.ctldep_col
            data.append(self.old[col.index("dep_xflag")])
            self.sql.updRec("ctldep", data=data, where=[("dep_cono",
                "=", self.opts["conum"]), ("dep_code", "=", self.code)])
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
