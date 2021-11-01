"""
SYNOPSIS
    Cash Takings and Analysis.

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
from TartanClasses import ASD, GetCtl, TartanDialog, Sql
from tartanFunctions import askQuestion, callModule, getVatRate

class cs2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
        cshctl = gc.getCtl("cshctl", self.opts["conum"])
        if not cshctl:
            return
        self.glint = cshctl["ccc_glint"]
        if self.glint == "Y":
            tabs = ["genmst"]
        else:
            tabs = ["cshmst"]
        tabs.extend(["cshana", "cshcnt"])
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        if self.glint == "Y":
            self.ctl = [["csh_ctl", "Cash Control", 0]]
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            for num, ctl in enumerate(self.ctl):
                if ctl[0] in ctlctl:
                    self.ctl[num][2] = ctlctl[ctl[0]]
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.denoms = (
            ("R200", 200),
            ("R100", 100),
            ("R50", 50),
            ("R20", 20),
            ("R10", 10),
            ("R5", 5),
            ("R2", 2),
            ("R1", 1),
            ("C50", .5),
            ("C20", .2),
            ("C10", .1),
            ("C5", .05),
            ("C2", .02),
            ("C1", .01))
        return True

    def mainProcess(self):
        tag = (
            ("Expenses", None, None, None, False),
            ("Income", None, None, None, False),
            ("Cash", None, None, None, False))
        dte = {
            "stype": "R",
            "tables": ("cshcnt",),
            "cols": (
                ("cct_date", "", 0, "Date"),),
            "where": [("cct_cono", "=", self.opts["conum"])],
            "group": "cct_date"}
        if self.glint == "Y":
            self.cod = {
                "stype": "R",
                "tables": ("genmst",),
                "cols": (
                    ("glm_acno", "", 0, "Acc-Num"),
                    ("glm_desc", "", 0, "Description", "Y")),
                "where": [("glm_cono", "=", self.opts["conum"])],
                "order": "glm_acno"}
        else:
            self.cod = {
                "stype": "R",
                "tables": ("cshmst",),
                "cols": (
                    ("ccm_acno", "", 0, "Acc-Num"),
                    ("ccm_desc", "", 0, "Description", "Y")),
                "where": [("ccm_cono", "=", self.opts["conum"])],
                "order": "ccm_acno"}
        des = {
            "stype": "R",
            "tables": ("cshana",),
            "cols": (
                ("can_desc", "", 0, "Description", "Y"),
                ("can_vatcod", "", 0, "V")),
            "where": [("can_cono", "=", self.opts["conum"])],
            "whera": (("C", "can_code", 1, 1),),
            "group": "can_desc",
            "order": "can_desc"}
        r1s = (("Expenses", "P"), ("Income", "T"), ("Cash", "C"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Type","",
                "P","N",self.doType,None,None,None),
            (("T",0,1,0),"I@cct_date",0,"","",
                self.sysdtw,"N",self.doDate,dte,None,("efld",)),
            (("T",0,2,0),"OSD",13.2,"Expenses Total"),
            (("T",0,3,0),"OSD",13.2,"Income Total"),
            (("T",0,4,0),"OSD",13.2,"Cash Total"),
            (("C",1,0,0),"I@can_trdt",0,"","",
                "","N",None,None,None,("efld",)),
            (("C",1,1,0),"I@can_code",0,"","",
                "","N",self.doCode,self.cod,None,None),
            (("C",1,2,0),"I@can_desc",0,"","",
                "","N",self.doDesc,des,None,("notblank",)),
            (("C",1,3,0),"I@can_vatcod",0,"","",
                "N","N",self.doVCode,None,None,("notblank",)),
            (("C",1,4,0),"I@can_incamt",0,"","",
                "","N",self.doIncAmt,None,None,("efld",)),
            (("C",1,5,0),"I@can_vatamt",0,"","",
                "","N",None,None,None,("efld",)),
            (("C",2,0,0),"I@can_trdt",0,"","",
                "","N",None,None,None,("efld",)),
            (("C",2,1,0),"I@can_code",0,"","",
                "","N",self.doCode,self.cod,None,None),
            (("C",2,2,0),"I@can_desc",0,"","",
                "","N",self.doDesc,des,None,("notblank",)),
            (("C",2,3,0),"I@can_vatcod",0,"","",
                "N","N",self.doVCode,None,None,("notblank",)),
            (("C",2,4,0),"I@can_incamt",0,"","",
                "","N",self.doIncAmt,None,None,("efld",)),
            (("C",2,5,0),"I@can_vatamt",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",3,0,0),"ISD",13.2,"Cheques","",
                "","N",self.doCheq,None,None,("efld",)),
            (("C",3,0,0),"IUI",5,"Quant","Quantity",
                0,"N",self.doQty,None,None,None,("Denomination",14)),
            (("C",3,1,0),"OSD",13.2,"Value","",
                "","N",None,None,None,("efld",)))
        tnd = (
            (self.doTopEnd, "y"),
            None,
            None,
            (self.doTopEnd, "n"))
        txt = (
            self.doTopExit,
            None,
            None,
            None)
        cnd = (
            None,
            (self.doColEnd, "y"),
            (self.doColEnd, "y"),
            (self.doColEnd, "n"))
        cxt = (
            None,
            self.doColExit,
            self.doColExit,
            self.doColExit)
        but = (
            ("Accept",None,self.doColExit,0,
                (("C",1,1),("C",2,1)),
                (("C",1,2),("C",2,2))),
            ("Edit",None,self.doEdit,0,
                (("C",1,1),("C",2,1)),
                (("C",1,2),("C",2,2))),
            ("Quit",None,self.doQuit,0,("T",0,0),("T",0,1)))
        self.df = TartanDialog(self.opts["mf"], tags=tag, eflds=fld,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but, focus=False)
        for x in range(14):
            self.df.colLabel[3][x].configure(text=self.denoms[x][0])
        self.df.focusField("T", 0, 1)

    def doType(self, frt, pag, r, c, p, i, w):
        self.trtp = w
        self.edit = None
        self.amend = False
        self.loader = False
        self.etotal = 0
        self.itotal = 0
        self.ctotal = 0

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        rec = self.sql.getRec("cshana", where=[("can_cono",
            "=", self.opts["conum"]), ("can_type", "=", "P"), ("can_date",
            "=", self.date)])
        if rec and self.trtp == "P":
            self.amend = True
        for rr in rec:
            self.etotal = float(ASD(self.etotal) + ASD(rr[7]))
        self.df.loadEntry(frt, pag, p+1, data=self.etotal)
        rec = self.sql.getRec("cshana", where=[("can_cono",
            "=", self.opts["conum"]), ("can_type", "=", "T"), ("can_date",
            "=", self.date)])
        if rec and self.trtp == "T":
            self.amend = True
        for rr in rec:
            self.itotal = float(ASD(self.itotal) + ASD(rr[7]))
        self.df.loadEntry(frt, pag, p+2, data=self.itotal)
        self.rec = self.sql.getRec("cshcnt", where=[("cct_cono", "=",
            self.opts["conum"]), ("cct_type", "=", "T"), ("cct_date",
            "=", self.date)], limit=1)
        if self.rec and self.trtp == "C":
            self.amend = True
        if self.amend:
            return "nc"

    def doCode(self, frt, pag, r, c, p, i, w):
        if self.glint == "N" and not w:
            ok = askQuestion(self.opts["mf"].body, "Code Maintenance",
                "Do You Want to Add or Edit Codes?", default="no")
            if ok == "no":
                return "rf"
            w = callModule(self.opts["mf"], self.df, "cs1010",
                coy=[self.opts["conum"], self.opts["conam"]],
                user=self.opts["capnm"], args=True, ret="acno")
            self.df.loadEntry(frt, pag, p, data=w)
        if self.glint == "Y":
            acc = self.sql.getRec("genmst", cols=["glm_desc", "glm_vat"],
                where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno",
                "=", w)], limit=1)
        else:
            acc = self.sql.getRec("cshmst", cols=["ccm_desc", "ccm_vat"],
                where=[("ccm_cono", "=", self.opts["conum"]), ("ccm_acno",
                "=", w)], limit=1)
        if not acc:
            return "Invalid Code"
        self.code = w
        self.vcod = acc[1]
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doDesc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("cshana", cols=["can_vatcod"],
            where=[("can_cono", "=", self.opts["conum"]), ("can_code",
            "=", self.code), ("can_desc", "=", w)], order="can_date desc",
            limit=1)
        if acc:
            self.df.loadEntry(frt, pag, p+1, data=acc[0])
        else:
            self.df.loadEntry(frt, pag, p+1, data=self.vcod)

    def doVCode(self, frt, pag, r, c, p, i, w):
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.date)
        if self.vatrte is None:
            ask = askQuestion(self.opts["mf"].body, "New Code",
                "Code Does Not Exist, Create a New Code?", default="no")
            if ask == "no":
                return "Invalid VAT Code"
            w = callModule(self.opts["mf"], self.df, "ms1040",
                coy=[self.opts["conum"], self.opts["conam"]],
                user=self.opts["capnm"], args=w, ret="code")
            self.df.loadEntry(frt, pag, p, data=w)
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.date)
        if self.vatrte is None:
            return "Invalid VAT Code"

    def doIncAmt(self, frt, pag, r, c, p, i, w):
        self.iamt = w
        if self.vatrte:
            vat = self.iamt * self.vatrte / float(ASD(100) + ASD(self.vatrte))
            self.df.loadEntry(frt, pag, p+1, data=round(vat, 2))
        else:
            self.df.loadEntry(frt, pag, p+1, data=0)
            if not self.loader:
                return "sk1"

    def doCheq(self, frt, pag, r, c, p, i, w):
        self.ctotal = w
        self.df.loadEntry("T", 0, 4, data=self.ctotal)

    def doQty(self, frt, pag, r, c, p, i, w):
        val = w * self.denoms[int(p / 2)][1]
        self.df.loadEntry(frt, pag, p+1, val)
        self.ctotal = float(ASD(self.ctotal) + ASD(val))
        self.df.loadEntry("T", 0, 4, data=self.ctotal)

    def doEdit(self):
        if self.df.pag in (1, 2):
            self.doEditPage12()
        else:
            self.doEditPage3()

    def doEditPage12(self):
        ana = self.sql.getRec("cshana", where=[("can_cono", "=",
            self.opts["conum"]), ("can_type", "=", self.trtp), ("can_date",
            "=", self.date)])
        data = []
        for rec in ana:
            dat = []
            for n, d in enumerate(rec):
                if n in (0, 1, 2, 9):
                    continue
                dat.append(d)
            data.append(dat)
        titl = "Analysis"
        head = ("Date", "Code", "Description", "V", "Inc-Amount", "VAT-Amount",
            "Seq")
        lin = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": (("D1", 10), ("UI", 7), ("NA", 30), ("UA", 1),
                ("SD", 13.2), ("SD", 13.2), ("UA", 1), ("US", 10)),
            "data": data}
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select a Line to Edit")
        chg = self.df.selChoice(lin)
        if chg and chg.selection:
            self.edit = self.sql.getRec("cshana", where=[("can_seq",
                "=", chg.selection[-1])], limit=1)
            self.doChgChanges()
        else:
            self.edit = None
        self.doLoadAnalysis()
        self.df.enableButtonsTags(state=state)

    def doChgChanges(self):
        tit = ("Change Line",)
        fld = (
            (("T",0,0,0),"I@can_trdt",10,"","",
                "","N",self.doChgDate,None,None,("efld",)),
            (("T",0,1,0),"I@can_code",0,"","",
                "","N",None,self.cod,None,None),
            (("T",0,2,0),"I@can_desc",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,3,0),"I@can_vatcod",0,"","",
                "","N",self.doChgVCode,None,None,("efld",)),
            (("T",0,4,0),"I@can_incamt",0,"","",
                "","N",self.doChgIncAmt,None,None,("efld",)),
            (("T",0,5,0),"I@can_vatamt",0,"","",
                "","N",None,None,None,("efld",)))
        but = [["Delete",None,self.doChgDel,1,None,None]]
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doChgEnd,"n"),),
            txit=(self.doChgExit,), focus=False)
        for num, dat in enumerate(self.edit[3:9]):
            self.cg.loadEntry("T", 0, num, data=dat)
        self.cg.focusField("T", 0, 1, clr=False)
        self.cg.mstFrame.wait_window()

    def doChgDate(self, frt, pag, r, c, p, i, w):
        self.chgdte = w

    def doChgVCode(self, frt, pag, r, c, p, i, w):
        self.vatrte = getVatRate(self.sql, self.opts["conum"], w, self.chgdte)
        if self.vatrte is None:
            return "Invalid VAT Code"

    def doChgIncAmt(self, frt, pag, r, c, p, i, w):
        self.iamt = w
        if self.vatrte:
            vat = self.iamt * self.vatrte / float(ASD(100) + ASD(self.vatrte))
            self.cg.loadEntry(frt, pag, p+1, data=round(vat, 2))
        else:
            self.cg.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doChgDel(self):
        self.sql.delRec("cshana", data=self.edit)
        self.doChgExit()

    def doChgEnd(self):
        self.sql.delRec("cshana", data=self.edit)
        for num, fld in enumerate(self.cg.t_work[0][0]):
            self.edit[num+3] = fld
        self.sql.insRec("cshana", data=self.edit)
        self.opts["mf"].dbm.commitDbase()
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def doEditPage3(self):
        titl = "Denominations"
        data = []
        for num, rec in enumerate(self.df.c_work[3]):
            data.append([self.denoms[num][0], rec[0], rec[1]])
        lin = {
            "stype": "C",
            "deco": True,
            "titl": titl,
            "head": ("Denom", "Qty", "Value"),
            "typs": (("NA", 4), ("UI", 5), ("SD", 13.2)),
            "data": data,
            "retn": "I"}
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select a Denomination to Edit")
        chg = self.df.selChoice(lin)
        self.df.enableButtonsTags(state=state)
        if chg and chg.selection:
            self.edit = self.df.col
            qty, val = self.df.c_work[3][chg.selection[0]]
            self.ctotal = float(ASD(self.ctotal) - ASD(val))
            self.df.focusField("C", 3, (chg.selection[0] * 2) + 1)
        else:
            self.edit = None
            self.df.focusField("C", 3, self.df.col)

    def doTopEnd(self):
        if self.df.pag == 0:
            if self.trtp == "P":
                self.df.selPage("Expenses")
                if self.amend:
                    self.doLoadAnalysis()
                else:
                    self.df.focusField("C", 1, 1)
            elif self.trtp == "T":
                self.df.selPage("Income")
                if self.amend:
                    self.doLoadAnalysis()
                else:
                    self.df.focusField("C", 2, 1)
            else:
                self.df.selPage("Cash")
                if not self.amend:
                    self.df.focusField("T", 3, 1)
                else:
                    self.doLoadCash()
        elif self.df.pag == 3:
            self.df.focusField("C", 3, 1)

    def doColEnd(self):
        if self.trtp in ("P", "T"):
            if self.trtp == "P":
                data = [self.opts["conum"], self.trtp, self.date]
                data.extend(self.df.c_work[1][self.df.row])
                data.append("N")
                self.sql.insRec("cshana", data=data)
                self.etotal = float(ASD(self.etotal) + ASD(self.iamt))
                self.df.loadEntry("T", 0, 2, data=self.etotal)
                self.df.advanceLine(1)
            else:
                data = [self.opts["conum"], self.trtp, self.date]
                data.extend(self.df.c_work[2][self.df.row])
                data.append("N")
                self.sql.insRec("cshana", data=data)
                self.itotal = float(ASD(self.itotal) + ASD(self.iamt))
                self.df.loadEntry("T", 0, 3, data=self.itotal)
                self.df.advanceLine(2)
        else:
            if self.df.col == 28:
                ask = askQuestion(self.opts["mf"].body, "Accept",
                    "Accept All Entries")
                if ask == "yes":
                    data = [self.opts["conum"], "T", self.date]
                    data.append(self.df.t_work[3][0][0])
                    for x in range(14):
                        data.append(self.df.c_work[3][x][0])
                    if self.amend:
                        self.sql.delRec("cshcnt", where=[("cct_cono", "=",
                            self.opts["conum"]), ("cct_type", "=", "T"),
                            ("cct_date", "=", self.date)])
                    self.sql.insRec("cshcnt", data=data)
                    self.opts["mf"].dbm.commitDbase()
                    self.doRestart()
                else:
                    self.df.focusField("T", 3, 1, clr=False)
            elif self.edit:
                col = self.edit
                self.edit = None
                self.df.focusField("C", 3, col)
            else:
                self.df.advanceLine(self.df.pag)

    def doLoadCash(self):
        self.df.doInvoke(["T", 3, 1, self.doCheq], self.rec[3])
        for num, qty in enumerate(self.rec[4:-1]):
            col = (num * 2) + 1
            self.df.doInvoke(["C", 3, col, self.doQty], qty)

    def doLoadAnalysis(self):
        self.loader = True
        total = 0
        if self.trtp == "P":
            pag = 1
        else:
            pag = 2
        self.df.clearFrame("C", pag)
        ana = self.sql.getRec("cshana", where=[("can_cono", "=",
            self.opts["conum"]), ("can_type", "=", self.trtp),
            ("can_date", "=", self.date)], order="can_seq")
        if not ana:
            self.df.focusField("C", pag, 1)
        else:
            for num, rec in enumerate(ana):
                if num > 14:
                    num = 14
                for pos, dat in enumerate(rec[3:9]):
                    col = (num * 6) + pos + 1
                    if pos == 3:
                        self.df.doInvoke(["C", pag, col, self.doVCode], dat)
                    elif pos == 4:
                        self.df.doInvoke(["C", pag, col, self.doIncAmt], dat)
                    else:
                        self.df.doInvoke(["C", pag, col, "rt"], dat)
                total = float(ASD(total) + ASD(self.iamt))
                self.df.advanceLine(pag)
        if self.trtp == "P":
            self.etotal = total
            self.df.loadEntry("T", 0, 2, data=self.etotal)
        else:
            self.itotal = total
            self.df.loadEntry("T", 0, 3, data=self.itotal)
        self.loader = False

    def doQuit(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.doRestart()

    def doTopExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doColExit(self):
        if self.df.pag != 3:
            self.opts["mf"].dbm.commitDbase()
            self.doRestart()
        elif self.df.pos:
            self.df.loadEntry("C", 3, self.df.pos,
                data=self.df.c_work[3][self.df.row][self.df.idx])
            r = self.df.row - 1
            c = self.df.col - 2
            self.ctotal = float(ASD(self.ctotal)-ASD(self.df.c_work[3][r][1]))
            self.df.focusField("C", 3, c)

    def doRestart(self):
        self.df.clearFrame("C", 1)
        self.df.clearFrame("C", 2)
        self.df.clearFrame("T", 3)
        self.df.clearFrame("C", 3)
        self.df.selPage("Expenses")
        self.df.focusField("T", 0, 1, clr=True)

# vim:set ts=4 sw=4 sts=4 expandtab:
