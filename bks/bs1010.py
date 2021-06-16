"""
SYNOPSIS
    Books Masterfile Maintenance.

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
from TartanClasses import GetCtl
from TartanClasses import Sql, TartanDialog
from tartanFunctions import askQuestion, getNextCode

class bs1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        tabs = ["bksmst", "bksown", "bksaut", "chglog"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        bmf = {
            "stype": "R",
            "tables": ("bksmst", "bksown"),
            "cols": (
                ("bmf_stat", "", 0, "S"),
                ("bmf_code", "", 0, "Code"),
                ("bmf_titl", "", 0, "Title", "Y"),
                ("bmf_ownr", "", 0, "Ownr"),
                ("bof_fnam", "", 0, "Name"),
                ("bmf_mnth", "", 0, "Mth-Rec")),
            "where": [
                ("bmf_cono", "=", self.opts["conum"]),
                ("bof_cono=bmf_cono",),
                ("bof_code=bmf_ownr",)],
            "order": "bmf_stat, bmf_titl",
            "index": 1}
        amf = {
            "stype": "R",
            "tables": ("bksaut",),
            "cols": (
                ("baf_code", "", 0, "Code"),
                ("baf_snam", "", 0, "Surname", "Y"),
                ("baf_fnam", "", 0, "Names")),
            "order": "baf_code"}
        omf = {
            "stype": "R",
            "tables": ("bksown",),
            "cols": (
                ("bof_code", "", 0, "Code"),
                ("bof_snam", "", 0, "Surname", "Y"),
                ("bof_fnam", "", 0, "Names")),
            "where": [("bof_cono", "=", self.opts["conum"])],
            "order": "bof_code"}
        r1s = (("Current","C"), ("Removed","X"))
        fld = (
            (("T",0,0,0),"IUI",4,"Code","",
                "","Y",self.doCode,bmf,None,("efld",)),
            (("T",0,1,0),"ITX",30,"Title","",
                "","N",self.doTitle,None,None,("notblank",)),
            (("T",0,2,0),"IUI",4,"Author","",
                "","N",self.doAuthor,amf,None,("efld",)),
            (("T",0,2,0),"ONA",30,""),
            (("T",0,3,0),"IUI",4,"Owner","",
                "","N",self.doOwner,omf,None,("efld",)),
            (("T",0,3,0),"ONA",30,""),
            (("T",0,4,0),"ID2",7,"Month","",
                "","N",self.doMonth,None,None,("efld",)),
            (("T",0,5,0),("IRB",r1s),0,"Status","",
                "C","N",self.doStatus,None,None,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),(("T",0,0),("T",0,1))),
            ("Exit",None,self.doExit,0,("T",0,1),None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.bcode = w
        if not self.bcode:
            ok = askQuestion(self.opts["mf"].body, "New Book",
                "Is This a New Book?", default="no")
            if ok == "no":
                return "Invalid Code"
            self.newbk = True
            self.bcode = getNextCode(self.sql, "bksmst", "bmf_code", start=1,
                last=9999)
            self.df.loadEntry(frt, pag, p, data=self.bcode)
        else:
            self.old = self.sql.getRec("bksmst", where=[("bmf_cono",
                "=", self.opts["conum"]), ("bmf_code", "=", self.bcode)],
                limit=1)
            if not self.old:
                ok = askQuestion(self.opts["mf"].body, "Code",
                    "Is This a Manual Code?", default="no")
                if ok == "no":
                    return "Invalid Code"
                self.newbk = True
                return
            col = 0
            self.newbk = False
            for num, dat in enumerate(self.old[1:-1]):
                self.df.loadEntry(frt, pag, col, data=dat)
                if num == 2:
                    col += 1
                    self.df.loadEntry(frt, pag, col, data=self.getAuthor(dat))
                elif num == 3:
                    col += 1
                    self.df.loadEntry(frt, pag, col, data=self.getOwner(dat))
                col += 1

    def doDelete(self):
        self.sql.delRec("bksmst", where=[("bmf_cono", "=", self.opts["conum"]),
            ("bmf_code", "=", self.bcode)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doTitle(self, frt, pag, r, c, p, i, w):
        self.title = w

    def doAuthor(self, frt, pag, r, c, p, i, w):
        self.acode = w
        if not self.acode:
            ok = askQuestion(self.opts["mf"].body, "New Author",
                "Is This a New Author?", default="no")
            if ok == "no":
                return "Invalid Code"
            self.doNewAuthor()
            if not self.aend:
                return "rf"
            self.df.loadEntry(frt, pag, p, data=self.acode)
        acc = self.sql.getRec("bksaut", where=[("baf_code", "=",
            self.acode)], limit=1)
        if not acc:
            return "Invalid Code"
        self.df.loadEntry(frt, pag, p+1, data=self.getAuthor(self.acode))

    def doNewAuthor(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Author's Details",)
        fld = (
            (("T",0,0,0),"ITX",30,"Surname","",
                "","Y",None,None,None,("notblank",)),
            (("T",0,1,0),"ITX",30,"Names","",
                "","Y",None,None,None,("efld",)))
        self.aa = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doAutEnd,"y"),), txit=(self.doAutExit,))
        self.aa.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doAutEnd(self):
        self.aend = True
        self.acode = getNextCode(self.sql, "bksaut", "baf_code", start=1,
            last=9999)
        data = [self.acode, self.aa.t_work[0][0][0], self.aa.t_work[0][0][1]]
        self.sql.insRec("bksaut", data=data)
        self.aa.closeProcess()

    def doAutExit(self):
        self.aend = False
        self.aa.closeProcess()

    def getAuthor(self, code):
        acc = self.sql.getRec("bksaut", where=[("baf_code", "=", code)],
            limit=1)
        if acc:
            return "%s, %s" % (acc[1], acc[2])
        else:
            return ""

    def doOwner(self, frt, pag, r, c, p, i, w):
        self.ocode = w
        if not self.ocode:
            ok = askQuestion(self.opts["mf"].body, "New Member",
                "Is This a New Member?", default="no")
            if ok == "no":
                return "Invalid Code"
            self.doNewOwner()
            if not self.oend:
                return "rf"
            self.df.loadEntry(frt, pag, p, data=self.ocode)
        acc = self.sql.getRec("bksown", where=[("bof_cono", "=",
            self.opts["conum"]), ("bof_code", "=", self.ocode)], limit=1)
        if not acc:
            return "Invalid Code"
        self.df.loadEntry(frt, pag, p+1, data=self.getOwner(self.ocode))

    def doNewOwner(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Owner's Details",)
        fld = (
            (("T",0,0,0),"ITX",30,"Surname","",
                "","Y",None,None,None,("notblank",)),
            (("T",0,1,0),"ITX",30,"Names","",
                "","Y",None,None,None,("efld",)))
        self.oo = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doOwnEnd,"y"),), txit=(self.doOwnExit,))
        self.oo.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doOwnEnd(self):
        self.oend = True
        self.ocode = getNextCode(self.sql, "bksown", "bof_code", start=1,
            last=9999)
        data = [self.opts["conum"], self.acode, self.oo.t_work[0][0][0],
            self.oo.t_work[0][0][1], "", "", "", "", "", "", "", ""]
        self.sql.insRec("bksown", data=data)
        self.oo.closeProcess()

    def doOwnExit(self):
        self.oend = False
        self.oo.closeProcess()

    def getOwner(self, code):
        acc = self.sql.getRec("bksown", where=[("bof_cono", "=",
            self.opts["conum"]), ("bof_code", "=", code)], limit=1)
        if acc:
            return "%s, %s" % (acc[2], acc[3])
        else:
            return ""

    def doMonth(self, frt, pag, r, c, p, i, w):
        self.month = w

    def doStatus(self, frt, pag, r, c, p, i, w):
        self.status = w

    def doEnd(self):
        data = [self.opts["conum"]]
        for num, dat in enumerate(self.df.t_work[0][0]):
            if num in (3, 5):
                continue
            data.append(dat)
        if self.newbk:
            self.sql.insRec("bksmst", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.bksmst_col
            data.append(self.old[col.index("bmf_xflag")])
            self.sql.updRec("bksmst", data=data, where=[("bmf_cono", "=",
                self.opts["conum"]), ("bmf_code", "=", self.bcode)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.old):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["bksmst", "U",
                        "%03i%04i" % (self.opts["conum"], self.bcode),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

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
