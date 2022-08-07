"""
SYNOPSIS
    General Ledger Interrogation.

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
from TartanClasses import ASD, CCD, MyFpdf, NotesCreate, RepPrt, Sql, SRec
from TartanClasses import TabPrt, TartanDialog
from tartanFunctions import getPeriods, getModName, doPrinter
from tartanWork import gltrtp, mthnam

class gl4010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "genbal", "genbud",
            "gentrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.i_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        df = self.e_per - self.i_per - 87
        if df > 12:
            self.d_per = df - 12
            yr = int(self.i_per / 100)
            mt = int(self.i_per % 100)
            for _ in range(self.d_per):
                mt += 1
                if mt > 12:
                    mt -= 12
                    yr += 1
            self.s_per = (yr * 100) + mt
        else:
            self.d_per = 0
            self.s_per = self.i_per
        self.d_pyr = 0
        if self.opts["period"][0]:
            s, e, f = getPeriods(self.opts["mf"], self.opts["conum"],
                (self.opts["period"][0] - 1))
            if (s, e, f) == (None, None, None):
                return
            self.s_lyr = s.work
            self.i_pyr = int(s.work / 100)
            self.e_pyr = int(e.work / 100)
            df = self.e_pyr - self.i_pyr - 87
            if df > 12:
                self.d_pyr = df - 12
                yr = int(self.i_pyr / 100)
                mt = self.i_pyr % 100
                for _ in range(self.d_pyr):
                    mt += 1
                    if mt > 12:
                        mt -= 12
                        yr += 1
                self.s_pyr = (yr * 100) + mt
            else:
                self.s_pyr = self.i_pyr
        self.trnper = 0
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Interrogation (%s)" % self.__class__.__name__)
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])],
            "order": "glm_acno"}
        fld = (
            (("T",0,0,0,7),"IUI",7,"Acc-Num","Account Number",
                "","N",self.doAccNum,glm,None,None),
            (("T",0,0,0),"ONA",30,"Description"),
            (("T",0,0,0),"OUA",1,"Type"),
            (("T",0,0,0),"OUA",1,"Indicator"),
            (("C",1,0,0),"OSD",13.2,"Actual","","","N",
                None,None,None,None,("Months",14)),
            (("C",1,0,1),"OSD",13.2,"Budget"),
            (("C",1,0,2),"OSD",13.2,"Variance"),
            (("C",1,0,3),"OSD",13.2,"Last-Year"),
            (("T",2,0,0),"Id2",7,"Period (YYYYMM)","Financial Period (0=All)",
                self.trnper,"Y",self.doPeriod,None,None,None))
        tag = (
            ("Balances",self.doBals,("T",0,2),("T",0,1)),
            ("Transactions",self.doTrans1,("T",0,2),("T",0,1)))
        but = (
            ("Clear",None,self.doClear,0,("T",0,0),("T",0,1)),
            ("Notes",None,self.doNotes,0,("T",0,0),("T",0,1)),
            ("Print",None,self.doPrint,1,("T",0,0),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doTopEnd, "N"), None, (self.doTrans2, "N"))
        txt = (self.doExit, None, self.doExit)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        mon = self.s_per % 100
        yer = int(self.s_per / 100)
        for x in range(14):
            if x == 0:
                txt = "Opening Balance"
                self.df.colLabel[1][x].configure(text=txt)
            elif x == 13:
                txt = "Closing Balance"
                self.df.colLabel[1][x].configure(text=txt)
            else:
                nam = mthnam[mon][1]
                nam = nam + (" " * (11-len(nam))) + str(yer)
                self.df.colLabel[1][x].configure(text=nam)
            if x not in (0, 13):
                mon = mon + 1
                if mon > 12:
                    mon = mon - 12
                    yer = yer + 1
        txt = "Closing Balance"
        self.df.colLabel[1][13].configure(text=txt)

    def doAccNum(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", cols=["glm_desc", "glm_type",
            "glm_ind"], where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account"
        self.acno = w
        self.desc = acc[0]
        for x in range(1, self.df.topq[pag]):
            self.df.loadEntry(frt, pag, p+x, data=acc[x-1])
        if self.opts["period"][0]:
            gp = self.sql.getRec("genbal", cols=["glo_cyr"],
                where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
                self.acno), ("glo_trdt", "=", self.s_lyr)])
        gc = self.sql.getRec("genbal", cols=["glo_cyr"],
            where=[("glo_cono", "=", self.opts["conum"]), ("glo_acno", "=",
            self.acno), ("glo_trdt", "=", self.opts["period"][1][0])])
        gt = self.sql.getRec("gentrn", cols=["glt_type", "glt_curdt",
            "glt_tramt"], where=[("glt_cono", "=", self.opts["conum"]),
            ("glt_acno", "=", self.acno), ("glt_curdt", "between", self.i_per,
            self.e_per)])
        gb = self.sql.getRec("genbud", cols=["glb_curdt", "glb_tramt"],
            where=[("glb_cono", "=", self.opts["conum"]), ("glb_acno", "=",
            self.acno), ("glb_curdt", "between", self.i_per, self.e_per)])
        if self.opts["period"][0]:
            gl = self.sql.getRec("gentrn", cols=["glt_curdt",
                "glt_tramt"], where=[("glt_cono", "=", self.opts["conum"]),
                ("glt_acno", "=", self.acno), ("glt_curdt", "between",
                self.i_pyr, self.e_pyr)])
        act = [0] * 14
        bud = [0] * 14
        lyr = [0] * 14
        adc = []
        adl = []
        if self.d_per:
            # Current period more than 12 months
            sy = sy = int(self.i_per / 100)
            sm = self.i_per % 100
            for _ in range(self.d_per):
                adc.append(sm)
                sm += 1
                if sm > 12:
                    sy += 1
                    sm = 1
        elif self.d_pyr:
            # Previous period more than 12 months
            sy = sy = int(self.i_pyr / 100)
            sm = self.i_pyr % 100
            for _ in range(self.d_pyr):
                adl.append(sm)
                sm += 1
                if sm > 12:
                    sy += 1
                    sm = 1
        if gc:
            self.obal = gc[0][0]
            act[0] = float(ASD(act[0]) + ASD(self.obal))
            act[13] = float(ASD(act[13]) + ASD(self.obal))
            if self.opts["period"][0] and gp:
                lyr[0] = float(ASD(lyr[0]) + ASD(float(gp[0][0])))
                lyr[13] = float(ASD(lyr[13]) + ASD(float(gp[0][0])))
        else:
            self.obal = 0
        yre = self.e_per % 100
        if gt:
            for x, t in enumerate(gt):
                cyr = int(t[1] / 100)
                mon = t[1] % 100
                if adc and cyr == sy and mon in adc:
                    col = 1
                else:
                    col = mon - yre
                    if col <= 0:
                        col = col + 12
                act[col] = float(ASD(act[col]) + ASD(float(t[2])))
                act[13] = float(ASD(act[13]) + ASD(float(t[2])))
        if gb:
            for x, t in enumerate(gb):
                mon = int(str(t[0])[4:6])
                col = mon - yre
                if col <= 0:
                    col = col + 12
                bud[col] = float(ASD(bud[col]) + ASD(float(t[1])))
                bud[13] = float(ASD(bud[13]) + ASD(float(t[1])))
        if self.opts["period"][0] and gl:
            for x, t in enumerate(gl):
                cyr = int(t[0] / 100)
                mon = t[0] % 100
                if adl and cyr == sy and mon in adl:
                    col = 1
                else:
                    col = mon - yre
                    if col <= 0:
                        col = col + 12
                lyr[col] = float(ASD(lyr[col]) + ASD(float(t[1])))
                lyr[13] = float(ASD(lyr[13]) + ASD(float(t[1])))
        p = 0
        for x in range(14):
            i = 0
            self.df.loadEntry("C", 1, p, data=act[x])
            p = p + 1
            i = i + 1
            self.df.loadEntry("C", 1, p, data=bud[x])
            p = p + 1
            i = i + 1
            data = float(ASD(bud[x])-ASD(act[x]))
            self.df.loadEntry("C", 1, p, data=data)
            p = p + 1
            i = i + 1
            self.df.loadEntry("C", 1, p, data=lyr[x])
            p = p + 1
        self.df.last[0] = [0, 0]
        self.opts["mf"].updateStatus("")

    def doBals(self):
        self.opts["mf"].updateStatus("")

    def doTrans1(self):
        self.df.focusField("T", 2, 1)

    def doTrans2(self):
        tit = "Transactions for Account: %s - %s" % (self.acno, self.desc)
        gtt = ["gentrn"]
        gtc = (
            ("glt_trdt", "", 0, "   Date"),
            ("glt_refno", "", 0, "Reference", "Y"),
            ("glt_type", ("XX", gltrtp), 3, "Typ"),
            ("glt_batch", "", 0, "Batch"),
            ("glt_tramt", "", 0, "       Debit"),
            ("glt_tramt", "", 0, "      Credit"),
            ("balance", "SD", 13.2, "     Balance"),
            ("glt_desc", "", 0, "Remarks"),
            ("glt_seq", "", 0, "Sequence"))
        mthno, acctot = self.getObal()
        if mthno.work == 0:
            d = self.opts["period"][1][0]
        else:
            d = (self.trnper * 100) + 1
        if acctot:
            if acctot < 0:
                dr = 0
                cr = acctot
            else:
                dr = acctot
                cr = 0
            data = [[d, "B/Fwd", 4, "", dr, cr, acctot, "Opening Balance", 0]]
        else:
            data = []
        trn = self.getTrans()
        if trn:
            col = self.sql.gentrn_col
            for rec in trn:
                acctot = float(ASD(acctot) + ASD(rec[col.index("glt_tramt")]))
                if rec[col.index("glt_tramt")] < 0:
                    dr = 0
                    cr = rec[col.index("glt_tramt")]
                else:
                    dr = rec[col.index("glt_tramt")]
                    cr = 0
                data.append([
                    rec[col.index("glt_trdt")],
                    rec[col.index("glt_refno")],
                    rec[col.index("glt_type")],
                    rec[col.index("glt_batch")],
                    dr, cr, acctot,
                    rec[col.index("glt_desc")],
                    rec[col.index("glt_seq")]])
        state = self.df.disableButtonsTags()
        while True:
            rec = SRec(self.opts["mf"], screen=self.df.nb.Page2, title=tit,
                tables=gtt, cols=gtc, where=data, wtype="D", sort=False)
            # Display all transaction details
            if rec.selection:
                self.df.setWidget(self.df.mstFrame, state="hide")
                whr = [("glt_seq", "=", rec.selection[8])]
                TabPrt(self.opts["mf"], tabs="gentrn", where=whr, pdia=False)
                self.df.setWidget(self.df.mstFrame, state="show")
            else:
                break
        self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "GEN", self.acno)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doTopEnd(self):
        self.df.last[0] = [0, 0]
        self.df.setWidget(self.df.topEntry[0][0], state="disabled")

    def doClear(self):
        self.df.selPage("Balances")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Printer/Email Selection",)
        r1s = (("Info","I"), ("Trans","T"))
        fld = (
            (("T",0,1,0),("IRB",r1s),0,"Selection","",
                "I","N",self.doPrtSel,None,None,None),
            (("T",0,2,0),"Id2",7,"Period (YYYYMM)","Financial Period (0=All)",
                self.trnper,"Y",self.doPeriod,None,None,None))
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doPrtEnd,"y"),), txit=(self.doPrtExit,),
            view=("Y","V"), mail=("Y","N"))
        self.pr.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField("T", 2, 1)

    def doPrtSel(self, frt, pag, r, c, p, i, w):
        self.sel = w
        for x in (2, 3):
            if bool(self.sel == "I"):
                self.pr.setWidget(self.pr.topEntry[0][2][x][0], state="hide")
            else:
                self.pr.setWidget(self.pr.topEntry[0][2][x][0], state="show")
        if self.sel == "I":
            return "sk1"

    def doPrtEnd(self):
        self.pr.closeProcess()
        self.head = "%03u %-99s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.num = self.df.t_disp[0][0][0]
        self.dsc = self.df.t_disp[0][0][1]
        atype = self.df.t_disp[0][0][2]
        ind = self.df.t_disp[0][0][3]
        if self.pr.t_work[0][0][0] == "I":
            self.pageHeading()
            self.fpdf.drawText("%-8s %-12s %-6s %-35s %-6s %-7s %-11s %s" % \
                ("Acc No:", self.num, "Desc:", self.dsc, "Type:", atype,
                "Indicator:", ind))
            self.fpdf.drawText()
            self.fpdf.drawText("%-21s %-20s %-18s %-19s %-18s" % \
                ("", "Actual", "Budget", "Variance", "Last Year"))
            self.fpdf.drawText()
            m = self.s_per % 100
            for x in range(14):
                if x == 0:
                    mon = "Opening"
                elif x == 13:
                    mon = "Closing"
                else:
                    mon = mthnam[m][1]
                    m = m + 1
                    if m > 12:
                        m = m - 12
                act = self.df.c_disp[1][x][0]
                bud = self.df.c_disp[1][x][1]
                var = self.df.c_disp[1][x][2]
                lyr = self.df.c_disp[1][x][3]
                self.fpdf.drawText("%-15s %-20s %-20s %-20s %-20s" % (mon,
                    act, bud, var, lyr))
                if x in (0, 12):
                    self.fpdf.drawText()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.pr.repprt,
                repeml=self.pr.repeml)
        else:
            trn = self.getTrans()
            if trn:
                heads = ["General Ledger Interrogation as at %s" % self.sysdtd]
                mthno, acctot = self.getObal()
                if mthno.work == 0:
                    x = "(For all months)"
                    d = self.opts["period"][1][0]
                else:
                    x = "(For month " + mthno.disp + ")"
                    d = (self.trnper * 100) + 1
                heads.append("Account %s %s %s" % (self.num, self.dsc, x))
                cols = [
                    ["glt_trdt", "D1", 10, "   Date"],
                    ["glt_refno", "Na", 9, "Reference"],
                    ["glt_type", "NA", 3, "Typ"],
                    ["glt_batch", "Na", 7, "BatchNo"],
                    ["debit", "SD", 13.2, "       Debit "],
                    ["credit", "SD", 13.2, "      Credit "],
                    ["balance", "SD", 13.2, "     Balance "],
                    ["glt_desc", "NA", 30, "Remarks"]]
                if acctot:
                    if acctot < 0:
                        dr = 0
                        cr = acctot
                    else:
                        dr = acctot
                        cr = 0
                    data = [(d,"B/Fwd","","",dr,cr,acctot,"Opening Balance")]
                else:
                    data = []
                col = self.sql.gentrn_col
                for num, rec in enumerate(trn):
                    trdt = rec[col.index("glt_trdt")]
                    refno = rec[col.index("glt_refno")]
                    trtp = gltrtp[(rec[col.index("glt_type")]) - 1][0]
                    batch = rec[col.index("glt_batch")]
                    tramt = rec[col.index("glt_tramt")]
                    if tramt < 0:
                        debit = 0
                        credit = tramt
                    else:
                        debit = tramt
                        credit = 0
                    detail = rec[col.index("glt_desc")]
                    acctot = float(ASD(acctot) + ASD(tramt))
                    data.append((trdt, refno, trtp, batch, debit, credit,
                        acctot, detail))
                RepPrt(self.opts["mf"], name=self.__class__.__name__,
                    conum=self.opts["conum"], conam=self.opts["conam"],
                    tables=data, heads=heads, cols=cols, ttype="D",
                    repprt=self.pr.repprt, repeml=self.pr.repeml)

    def doPrtExit(self):
        self.pr.closeProcess()

    def doPeriod(self, frt, pag, r, c, p, i, w):
        if w != 0 and (w < self.i_per or w > self.e_per):
            return "Invalid Period"
        self.trnper = w

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-10s %51s %5s" % \
            ("General Ledger Interrogation as at", self.sysdtd,
            "Page", self.pgnum))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()

    def getObal(self):
        acbal = self.obal
        if self.trnper:
            o = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"],
                where=[("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
                self.acno), ("glt_curdt", ">=", self.i_per), ("glt_curdt",
                "<", self.trnper)], limit=1)
            if o[0]:
                acbal = float(ASD(acbal) + ASD(o[0]))
        mthno = CCD(self.trnper % 100, "UI", 2.0)
        return mthno, acbal

    def getTrans(self):
        odr = "glt_acno, glt_curdt, glt_trdt, glt_type, glt_refno, glt_batch"
        if not self.trnper:
            whr = [("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
                self.acno), ("glt_curdt", "between", self.i_per, self.e_per)]
        else:
            whr = [("glt_cono", "=", self.opts["conum"]), ("glt_acno", "=",
                self.acno), ("glt_curdt", "=", self.trnper)]
        return self.sql.getRec("gentrn", where=whr, order=odr)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
