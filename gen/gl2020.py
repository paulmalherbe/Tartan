"""
SYNOPSIS
    General Ledger - Capturing Budgets.

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

from TartanClasses import ASD, FileImport, ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, showError

class gl2020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "genbud", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.s_cur = int(self.opts["period"][1][0] / 100)
        self.e_cur = int(self.opts["period"][2][0] / 100)
        self.s_old = self.s_cur - 100
        self.e_old = self.e_cur - 100
        return True

    def drawDialog(self):
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (("glm_acno", "", 0, "Acc-Num"),
                    ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        tot = {
            "stype": "R",
            "tables": ("genbud","genmst"),
            "cols": (
                ("glb_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description"),
                ("sum(glb_tramt) as tramt", "SI", 10, "Budget")),
            "where": [
                ("glb_cono", "=", self.opts["conum"]),
                ("glm_cono=glb_cono",),
                ("glb_acno=glm_acno",),
                ("glb_curdt", "between",
                    int(self.opts["period"][1][0] / 100),
                    int(self.opts["period"][2][0] / 100))],
            "group": "glb_cono, glb_acno, glm_desc",
            "order": "glb_acno"}
        bud = {
            "stype": "R",
            "tables": ("genbud",),
            "cols": (("glb_curdt", "", 0, "Period"),
                    ("glb_tramt", "", 0, "Budget")),
            "where": [
                ("glb_cono", "=", self.opts["conum"]),
                ("glb_curdt", "between",
                    int(self.opts["period"][1][0] / 100),
                    int(self.opts["period"][2][0] / 100))],
            "whera": (("C", "glb_acno", 0),)}
        fld = (
            (("C",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "r","N",self.doAcc,glm,None,None),
            (("C",0,0,1),"ONA",30,"Description"),
            (("C",0,0,2),"IUA",1,"F","(M)onth or (A)nnual Budget",
                "M","N",self.doFrq,None,None,None),
            (("C",0,0,3),"ID2",7,"Period","Month Period",
                "p","N",self.doPer,bud,None,None),
            (("C",0,0,4),"ISI",10,"Budget","Budget Value",
                "","N",self.doBud,None,None,None))
        row = (20,)
        but = (
            ("_Import File",None,self.doImport,0,("C", 0, 1),("C", 0, 2),
            """Import a File with the Correct Format i.e. Account Number and Annual Budget or Account Number and 12 Monthly Budgets"""),
            ("Auto _Populate",None,self.doPopulate,0,("C", 0, 1),("C", 0, 2),
            """Automatically populate all account budgets with the previous financial period actuals or budgets. This only applies to Profit and Loss accounts. Please Note that All Existing Budgets for the period will be Replaced."""),
            ("Show Budgets",tot,None,0,("C", 0, 1),("C", 0, 2),
            "Display all annual budgets for all accounts"),
            ("Exit",None,self.exitData,0,("C", 0, 1),("C", 0, 2)))
        self.df = TartanDialog(self.opts["mf"], rows=row, eflds=fld,
            cend=((self.endData,"y"),), cxit=(self.exitData,), butt=but)

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Budget File Import",)
        r1s = (("Annual", "A"), ("Monthly", "M"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Import Format","",
                "A","N",self.doImpTyp,None,None,None),)
        tnd = ((self.doImpEnd,"n"), )
        txt = (self.doImpExit, )
        self.ip = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.ip.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doImpTyp(self, frt, pag, r, c, p, i, w):
        self.frq = w

    def doImpEnd(self):
        self.ip.closeProcess()
        impcol = [
            ["Account Number", 0, "UI", 7]]
        if self.frq == "A":
            impcol.append(["Annual Budget", 1, "SI", 10])
        else:
            for x in range(1, 13):
                impcol.append(["Month %2s" % x, x, "SI", 10])
        fi = FileImport(self.opts["mf"], impcol=impcol)
        err = None
        for num, line in enumerate(fi.impdat):
            if self.frq == "A":
                chk = 2
            else:
                chk = 13
            if len(line) != chk:
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, chk, len(line))
                break
            self.acc = line[0]
            acc = self.sql.getRec("genmst", where=[("glm_cono", "=",
                self.opts["conum"]), ("glm_acno", "=", self.acc)], limit=1)
            if not acc:
                err = "Line %s: Invalid Account %s" % ((num + 1), self.acc)
                break
            if self.frq == "A":
                self.bud = line[1]
                self.endData(det=True)
                continue
            sy = int(self.s_cur / 100)
            sm = int(self.s_cur % 100)
            for b in line[1:]:
                self.per = (sy * 100) + sm
                self.bud = b
                self.endData(det=True)
                sm += 1
                if sm > 12:
                    sm = 1
                    sy += 1
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        elif fi.impdat:
            self.opts["mf"].dbm.commitDbase()

    def doImpExit(self):
        self.ip.closeProcess()

    def doPopulate(self):
        answer = askQuestion(self.opts["mf"].body, "Are You Sure?", """Are You Sure This is what you want to do!!

Remember that all existing budgets for this financial period will be replaced!""")
        if answer == "no":
            return
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.rates = {}
        tit = ("Budget Variables",)
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (("glm_acno", "", 0, "Acc-Num"),
                    ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        r1s = (("Actuals", "A"), ("Budgets", "B"))
        r2s = (
            ("R1","0"),
            ("R10","1"),
            ("R50","2"),
            ("R100","3"),
            ("R1000","4"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Use Previous Year's","",
                "A","N",self.doUse,None,None,None),
            (("T",0,1,0),"ISD",7.2,"Standard Rate (+-)","",
                "","N",self.doRate,None,None,("efld",),None,
                """The percentage by which the actual must be increased or decreased."""),
            (("T",0,2,0),("IRB",r2s),0,"Rounding to Nearest","",
                "0","N",self.doRound,None,None,None),
            (("C",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "","N",self.doAccNo,glm,None,None),
            (("C",0,0,1),"ONA",30,"Description"),
            (("C",0,0,2),"ISD",7.2,"Rate","Rate (+-)",
                "","N",self.doRates,None,None,("efld",),None,
                """The percentage by which the actual must be increased or decreased."""))
        tnd = ((self.doEnd,"n"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"n"),)
        cxt = (self.doExit,)
        but = (
            ("Show",None,self.doShow,1,("C", 0, 1),("C", 0, 2)),
            ("Quit",None,self.doQuit,1,("C", 0, 1),None))
        state = self.df.disableButtonsTags()
        self.rr = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)
        self.rr.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        if not self.xits:
            self.doPopulation()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doUse(self, frt, pag, r, c, p, i, w):
        self.use = w

    def doRate(self, frt, pag, r, c, p, i, w):
        if not w:
            self.rate = 100
        else:
            self.rate = float(ASD(100) + ASD(w))

    def doRound(self, frt, pag, r, c, p, i, w):
        self.rnd = [0, 10, 50, 100, 1000][int(w)]

    def doExcept(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.rr.closeProcess()
        else:
            self.rr.focusField("C", 0, 1)

    def doAccNo(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not desc:
            return "Invalid Account Number"
        self.acno = w
        self.desc = desc[0]
        self.rr.loadEntry(frt, pag, p+1, data=self.desc)

    def doRates(self, frt, pag, r, c, p, i, w):
        self.rates[self.acno] = (self.desc, w)

    def doEnd(self):
        if self.rr.frt == "T":
            self.xits = False
            self.rr.focusField("C", 0, 1)
        else:
            self.rr.advanceLine(0)

    def doExit(self):
        if self.rr.frt == "T":
            self.xits = True
            self.rate = 0
        self.rr.closeProcess()

    def doShow(self):
        data = []
        keys = list(self.rates.keys())
        keys.sort()
        for key in keys:
            data.append((key, self.rates[key][0], self.rates[key][1]))
        titl = "Exceptions"
        head = ("Acc-Num", "Description", "Rate")
        line = {
            "stype": "C",
            "titl": titl,
            "head": head,
            "typs": (("UI", 7), ("NA", 30), ("SD", 7.2)),
            "data": data}
        state = self.rr.disableButtonsTags()
        self.opts["mf"].updateStatus("")
        self.rr.selChoice(line)
        self.rr.enableButtonsTags(state=state)
        self.rr.focusField("C", 0, self.rr.col)

    def doQuit(self):
        self.xits = True
        self.rate = 0
        self.rr.closeProcess()

    def doPopulation(self):
        recs = self.sql.getRec("genmst", cols=["glm_acno"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_type", "=", "P")], order="glm_acno")
        if not recs:
            return
        exc = list(self.rates.keys())
        p = ProgressBar(self.opts["mf"].body, typ="Populating Budgets",
            mxs=len(recs))
        for num, acc in enumerate(recs):
            p.displayProgress(num)
            self.sql.delRec("genbud", where=[("glb_cono", "=",
                self.opts["conum"]), ("glb_acno", "=", acc[0]),
                ("glb_curdt", "between", self.s_cur, self.e_cur)])
            if self.use == "A":
                bals = self.sql.getRec("gentrn", cols=["glt_curdt",
                    "round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                    self.opts["conum"]), ("glt_acno", "=", acc[0]),
                    ("glt_curdt", "between", self.s_old, self.e_old)],
                    group="glt_curdt", order="glt_curdt")
            else:
                bals = self.sql.getRec("genbud", cols=["glb_curdt",
                    "glb_tramt"], where=[("glb_cono", "=", self.opts["conum"]),
                    ("glb_acno", "=", acc[0]), ("glb_curdt", "between",
                    self.s_old, self.e_old)], order="glb_curdt")
            for bal in bals:
                cur = bal[0] + 100
                if acc[0] in exc:
                    rate = self.rates
                    rate = float(ASD(100) + ASD(self.rates[acc[0]][1]))
                    amt = round(int(((bal[1] * rate) / 100)), 2)
                else:
                    amt = round(int(((bal[1] * self.rate) / 100)), 2)
                if self.rnd:
                    dif = amt % self.rnd
                    amt = amt - dif
                    if amt < 0 and dif > int(self.rnd / 2):
                        amt = amt + self.rnd
                    elif amt > 0 and dif >= int(self.rnd / 2):
                        amt = amt + self.rnd
                self.sql.insRec("genbud", data=[self.opts["conum"],
                    acc[0], cur, amt])
        p.closeProgress()
        self.opts["mf"].dbm.commitDbase()

    def doAcc(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            w)], limit=1)
        if not desc:
            return "Invalid Account Number"
        self.acc = w
        self.df.loadEntry(frt, pag, p+1, data=desc[0])

    def doFrq(self, frt, pag, r, c, p, i, w):
        if w not in ("M", "A"):
            return "Invalid Frequency (M/A)"
        self.frq = w
        if self.frq == "A":
            bud = self.sql.getRec("genbud", cols=["sum(glb_tramt)"],
                where=[("glb_cono", "=", self.opts["conum"]), ("glb_acno", "=",
                self.acc), ("glb_curdt", "between", self.s_cur, self.e_cur)],
                limit=1)
            if bud:
                self.df.loadEntry(frt, pag, p+2, data=bud[0])
            return "sk1"

    def doPer(self, frt, pag, r, c, p, i, w):
        if w < int(self.opts["period"][1][0] / 100) or \
                w > int(self.opts["period"][2][0] / 100):
            return "Invalid Period"
        self.per = w
        bud = self.sql.getRec("genbud", cols=["glb_tramt"],
            where=[("glb_cono", "=", self.opts["conum"]), ("glb_acno",
            "=", self.acc), ("glb_curdt", "=", self.per)], limit=1)
        if bud:
            self.df.loadEntry(frt, pag, p+1, data=bud[0])

    def doBud(self, frt, pag, r, c, p, i, w):
        self.bud = w

    def endData(self, det=False):
        if self.frq == "A":
            amts = [int(round(self.bud / 12.0, 0))] * 12
            amts[0] += (self.bud - sum(amts))
            p = int(self.opts["period"][1][0] / 100)
            y = int(p / 100)
            m = p % 100
            for x in range(12):
                per = (y * 100) + m
                whr = [("glb_cono", "=", self.opts["conum"]), ("glb_acno",
                    "=", self.acc), ("glb_curdt", "=", per)]
                exst = self.sql.getRec("genbud", cols=["count(*)"],
                    where=whr, limit=1)
                if exst[0]:
                    self.sql.updRec("genbud", cols=["glb_tramt"],
                        data=[amts[x]], where=whr)
                else:
                    data = [self.opts["conum"], self.acc, per, amts[x]]
                    self.sql.insRec("genbud", data=data)
                m = m + 1
                if m > 12:
                    y = y + 1
                    m = m - 12
        else:
            whr = [("glb_cono", "=", self.opts["conum"]), ("glb_acno",
                "=", self.acc), ("glb_curdt", "=", self.per)]
            exst = self.sql.getRec("genbud", cols=["count(*)"],
                where=whr, limit=1)
            if exst[0]:
                self.sql.updRec("genbud", cols=["glb_tramt"],
                data=[self.bud], where=whr)
            else:
                data = [self.opts["conum"], self.acc, self.per, self.bud]
                self.sql.insRec("genbud", data=data)
        if not det:
            self.opts["mf"].dbm.commitDbase()
            self.df.advanceLine(0)

    def exitData(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
