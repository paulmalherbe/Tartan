"""
SYNOPSIS
    Value Added Tax Records Maintenance.

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
from TartanClasses import GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import askQuestion, copyList, showError

class ms1040(object):
    def __init__(self, **opts):
        self.opts = opts
        if "args" in opts:
            self.code = opts["args"]
        else:
            self.code = None
        if self.setVariables():
            self.mainProcess()
            if self.code:
                self.df.doKeyPressed("T", 0, 0, self.code)
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "ctlvrf", "ctlvtf",
            "chglog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        if not self.code:
            gc = GetCtl(self.opts["mf"])
            ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
            if not ctlmst:
                return
            if not ctlmst["ctm_taxno"]:
                showError(self.opts["mf"].body, "Unregistered",
                    "The Company Record Does Not Have a V.A.T. Number")
                return
        return True

    def mainProcess(self):
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y"),
                ("vtm_cat", "", 0, "C")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        vtr = {
            "stype": "R",
            "tables": ("ctlvrf",),
            "cols": (
                ("vtr_date", "", 0, "Start-Date"),
                ("vtr_rate", "", 0, "Rate")),
            "where": [("vtr_cono", "=", self.opts["conum"])],
            "whera": [["T", "vtr_code", 0, 0]]}
        vtt = {
            "stype": "C",
            "titl": "VAT Types",
            "head": ("C", "Description"),
            "data": [
                ["N", "None"],
                ["S", "Standard"],
                ["Z", "Zero Rated"],
                ["C", "Capital Item"],
                ["X", "Excluded Item"]]}
        fld = (
            (("T",0,0,0),"IUA",1,"V.A.T. Code","",
                "","Y",self.doCode,vtm,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",self.doDesc,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"IUA",1,"Category","",
                "S","N",self.doCat,vtt,None,("in", ("C","N","S","X","Z"))),
            (("C",0,0,0),"Id1",10,"Start-Date","The Starting Date",
                "","N",self.doStart,vtr,None,("efld",)),
            (("C",0,0,1),"IUD",6.2,"Rate-%","The Rate",
                "","N",self.doRate,None,None,("efld",)))
        but = (
            ("Print",None,self.doPrint,0,("T",0,1),(("T",0,0),("T",0,2))),
            ("Add",None,self.doAdd,0,("T",0,0),None),
            ("Edit",None,self.doEdit,0,("T",0,0),None),
            ("Exit",None,self.doExit,0,("T",0,0),(("T",0,1),("C",0,1))))
        tnd = ((self.doTEnd,"y"), )
        txt = (self.doTExit, )
        cnd = ((self.doCEnd,"y"), )
        cxt = (self.doCExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt, rows=(15,))

    def doPrint(self):
        hds = "V.A.T. Records"
        col = [
            ["vtm_code", "UA",  1,   "C"],
            ["vtm_desc", "NA", 30,   "Description"],
            ["vtm_cat", "UA",   1,   "T"],
            ["vtr_date", "d1", 10,   "Start-Date"],
            ["vtr_rate", "UD",  6.2, "Rate"]]
        recs = self.sql.getRec(tables=["ctlvmf", "ctlvrf"], cols=["vtm_code",
            "vtm_desc", "vtm_cat", "vtr_date", "vtr_rate"], where=[("vtm_cono",
            "=", self.opts["conum"]), ("vtr_cono=vtm_cono",),
            ("vtr_code=vtm_code",)], order="vtm_code, vtr_date")
        code = None
        data = copyList(recs)
        for num, rec in enumerate(recs):
            if rec[0] == code:
                data[num][0] = ""
                data[num][1] = ""
                data[num][2] = ""
            code = rec[0]
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=data,
            heads=[hds], ttype="D", cols=col, prtdia=(("Y","V"), ("Y","N")))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 0, 1)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.oldm = self.sql.getRec("ctlvmf", where=[("vtm_cono", "=",
            self.opts["conum"]), ("vtm_code", "=", self.code)], limit=1)
        if not self.oldm:
            self.newm = True
        else:
            self.newm = False
            self.desc = self.oldm[self.sql.ctlvmf_col.index("vtm_desc")]
            self.df.loadEntry(frt, pag, p+1, data=self.desc)
            self.cat = self.oldm[self.sql.ctlvmf_col.index("vtm_cat")]
            self.df.loadEntry(frt, pag, p+2, data=self.cat)
            self.doLoadRates()
            return "ff2"

    def doDelete(self):
        if self.df.frt == "T":
            if self.doCheckTrn():
                showError(self.opts["mf"].body, "Exists",
                    "Transactions Exist for this Code, Not Deleted")
                return
            self.sql.delRec("ctlvmf", where=[("vtm_cono", "=",
                self.opts["conum"]), ("vtm_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            self.sql.insRec("chglog", data=["ctlvmf", "D", "%03i%-1s" % \
                (self.opts["conum"], self.code), "", dte, self.opts["capnm"],
                "", "", "", 0])
            self.sql.delRec("ctlvrf", where=[("vtr_cono", "=",
                self.opts["conum"]), ("vtr_code", "=", self.code)])
            self.opts["mf"].dbm.commitDbase()

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doCat(self, frt, pag, r, c, p, i, w):
        self.cat = w

    def doTEnd(self):
        self.edit = False
        datm = [self.opts["conum"]]
        datm.extend(self.df.t_work[0][0][:3])
        if self.newm:
            self.sql.insRec("ctlvmf", data=datm)
            if self.cat in ("N", "X", "Z"):
                newr = [self.opts["conum"], self.code, 0, 0]
                self.sql.insRec("ctlvrf", data=newr)
                self.opts["mf"].dbm.commitDbase()
                self.df.focusField("T", 0, 1)
            else:
                self.doButtons()
                self.df.focusField("C", 0, 1)
        elif self.cat in ("N", "X", "Z"):
            self.df.focusField("T", 0, 1)
        elif datm != self.oldm[:len(datm)]:
            col = self.sql.ctlvmf_col
            datm.append(self.oldm[col.index("vtm_xflag")])
            self.sql.updRec("ctlvmf", data=datm, where=[("vtm_cono", "=",
                self.opts["conum"]), ("vtm_code", "=", self.code)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.oldm):
                if dat != datm[num]:
                    self.sql.insRec("chglog", data=["ctlvmf",
                    "U", "%03i%-1s" % (self.opts["conum"], self.code),
                    col[num], dte, self.opts["capnm"], str(dat),
                    str(datm[num]), "", 0])
            self.doButtons()
        self.opts["mf"].dbm.commitDbase()

    def doTExit(self):
        chks = ""
        recs = self.sql.getRec("ctlvmf", where=[("vtm_cono", "=",
            self.opts["conum"])])
        for rec in recs:
            rte = self.sql.getRec("ctlvrf", where=[("vtr_cono",
                "=", self.opts["conum"]), ("vtr_code", "=", rec[1])])
            if not rte:
                if rec[3] in ("N", "X", "Z"):
                    self.sql.insRec("ctlvrf", data=[rec[0], rec[1], 0, 0])
                    self.opts["mf"].dbm.commitDbase()
                    continue
                chks = "%s\n%1s %-30s %1s" % (chks, rec[1], rec[2], rec[3])
        if chks:
            showError(self.opts["mf"].body, "Missing Rate Record", "The "\
                "following VAT Codes do Not have Rate Records:\n%s\n\n"\
                "You will Not be able to Exit until you either Create "\
                "Rate Records or Delete these codes." % chks)
            self.df.focusField("T", 0, 1)
        else:
            self.df.closeProcess()
            if "wait" not in self.opts:
                self.opts["mf"].closeLoop()

    def doAdd(self):
        for num, rec in enumerate(self.df.c_work[0]):
            if not rec[0] and not rec[1]:
                pos = (num * 2) + 1
                self.df.focusField("C", 0, pos)
                break

    def doEdit(self):
        self.edit = True
        self.newr = False
        tit = "Edit Rate"
        vtr = {
            "stype": "R",
            "tables": ("ctlvrf",),
            "cols": (
                ("vtr_date", "", 0, "Start-Date"),
                ("vtr_rate", "", 0, "Rate")),
            "where": [
                ("vtr_cono", "=", self.opts["conum"]),
                ("vtr_code", "=", self.code)]}
        fld = (
            (("T",0,0,0),"OUA",1,"V.A.T. Code"),
            (("T",0,1,0),"ONA",30,"Description"),
            (("T",0,2,0),"OUA",1,"Category"),
            (("T",0,3,0),"Id1",10,"Start-Date","The Starting Date",
                "","N",self.doEStart,vtr,self.doEDelete,("efld",)),
            (("T",0,4,0),"IUD",6.2,"Rate-%","The Rate",
                "","N",self.doERate,None,self.doEDelete,("notzero",)))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.ed = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doEEnd,"n"),), txit=(self.doEExit,))
        self.ed.loadEntry("T", 0, 0, data=self.code)
        self.ed.loadEntry("T", 0, 1, data=self.desc)
        self.ed.loadEntry("T", 0, 2, data=self.cat)
        self.ed.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        if self.exit:
            self.df.focusField("T", 0, 1)
        else:
            self.doExit()

    def doEDelete(self):
        self.exit = False
        if self.ed.pos == 3:
            if self.doCheckTrn():
                return ("T", 0, 4, "Transactions Exist, Not Deleted")
            self.sql.delRec("ctlvmf", where=[("vtm_cono", "=",
                self.opts["conum"]), ("vtm_code", "=", self.code)])
            self.sql.delRec("ctlvrf", where=[("vtr_cono", "=",
                self.opts["conum"]), ("vtr_code", "=", self.code)])
        else:
            if self.doCheckTrn(self.start):
                return ("T", 0, 5, "Transactions Exist, Not Deleted")
            self.sql.delRec("ctlvrf", where=[("vtr_cono", "=",
                self.opts["conum"]), ("vtr_code", "=", self.code),
                ("vtr_date", "=", self.start)])
        self.ed.closeProcess()
        chk = self.sql.getRec("ctlvrf", cols=["count(*)"],
            where=[("vtr_cono", "=", self.opts["conum"]),
            ("vtr_code", "=", self.code)], limit=1)
        if not chk[0]:
            self.sql.delRec("ctlvmf", where=[("vtm_cono", "=",
                self.opts["conum"]), ("vtm_code", "=", self.code)])
            self.exit = True
        self.opts["mf"].dbm.commitDbase()
        return "nf"

    def doEStart(self, frt, pag, r, c, p, i, w):
        self.oldr = self.sql.getRec("ctlvrf", where=[("vtr_cono",
            "=", self.opts["conum"]), ("vtr_code", "=", self.code),
            ("vtr_date", "=", w)], limit=1)
        if not self.oldr:
            return "Date Does Not Exist"
        if self.doCheckTrn(w):
            showError(self.opts["mf"].body, "Date Error",
                "Transactions Exist for Date, Editing Not Allowed.")
            return "Invalid Date"
        self.start = w
        self.rate = self.oldr[3]
        self.ed.loadEntry(frt, pag, p+1, data=self.rate)

    def doERate(self, frt, pag, r, c, p, i, w):
        if not w:
            yes = askQuestion(self.opts["mf"].body, "Zero Rate",
                "Are You Sure That This Rate is Correct?", default="no")
            if yes == "no":
                return "Invalid Rate"
        self.rate = w

    def doEEnd(self):
        self.ed.closeProcess()
        self.doCEnd()

    def doEExit(self):
        self.ed.closeProcess()

    def doStart(self, frt, pag, r, c, p, i, w):
        if self.doCheckTrn(w):
            showError(self.opts["mf"].body, "Date Error",
                "Transactions Exist On or After This Starting Date.")
            return "Invalid Date"
        self.start = w
        self.oldr = self.sql.getRec("ctlvrf", where=[("vtr_cono",
            "=", self.opts["conum"]), ("vtr_code", "=", self.code),
            ("vtr_date", "=", self.start)], limit=1)
        if not self.oldr:
            self.newr = True
            if self.cat in ("N", "X", "Z"):
                if self.edit:
                    self.ed.loadEntry(frt, pag, p+1, data=0)
                else:
                    self.df.loadEntry(frt, pag, p+1, data=0)
                return "nd"
        else:
            self.newr = False
            if self.edit:
                self.ed.loadEntry(frt, pag, p+1,
                    data=self.oldr[self.sql.ctlvrf_col.index("vtr_rate")])
            else:
                self.df.loadEntry(frt, pag, p+1,
                    data=self.oldr[self.sql.ctlvrf_col.index("vtr_rate")])

    def doRate(self, frt, pag, r, c, p, i, w):
        if not w:
            yes = askQuestion(self.opts["mf"].body, "Zero Rate",
                "Are You Sure That This Rate is Correct?", default="no")
            if yes == "no":
                return "Invalid Rate"
        self.rate = w

    def doCheckTrn(self, date=None):
        where = [
            ("vtt_cono", "=", self.opts["conum"]),
            ("vtt_code", "=", self.code)]
        if date:
            where.append(("vtt_refdt", ">=", date))
        return self.sql.getRec("ctlvtf", cols=["count(*)"],
            where=where, limit=1)[0]

    def doCEnd(self):
        datr = [self.opts["conum"], self.code, self.start, self.rate]
        if self.newr:
            self.sql.insRec("ctlvrf", data=datr)
        elif datr != self.oldr[:len(datr)]:
            col = self.sql.ctlvrf_col
            datr.append(self.oldr[col.index("vtr_xflag")])
            self.sql.updRec("ctlvrf", data=datr, where=[("vtr_cono", "=",
                self.opts["conum"]), ("vtr_code", "=", self.code),
                ("vtr_date", "=", self.start)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.oldr):
                if dat != datr[num]:
                    self.sql.insRec("chglog", data=["ctlvrf", "U",
                        "%03i%-1s" % (self.opts["conum"], self.code),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(datr[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.edit = False
        self.doExit()

    def doCExit(self):
        self.edit = False
        self.doExit()

    def doLoadRates(self):
        self.df.clearFrame("C", 0)
        recs = self.sql.getRec("ctlvrf",
            cols=["vtr_date", "vtr_rate"],
            where=[("vtr_cono", "=", self.opts["conum"]),
            ("vtr_code", "=", self.code)], order="vtr_date")
        for num, rec in enumerate(recs):
            pos = (num * 2)
            if pos > 27:
                self.df.scrollScreen(0)
                pos = 26
            self.df.focusField("C", 0, pos + 1)
            self.df.loadEntry("C", 0, pos, data=rec[0])
            self.df.focusField("C", 0, pos + 2)
            self.df.loadEntry("C", 0, pos + 1, data=rec[1], zero=True)

    def doButtons(self):
        self.df.setWidget(self.df.B1, "normal")
        self.df.setWidget(self.df.B2, "normal")
        self.df.setWidget(self.df.B3, "normal")
        self.opts["mf"].window.focus_set()

    def doExit(self):
        self.df.setWidget(self.df.B3, "disabled")
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
