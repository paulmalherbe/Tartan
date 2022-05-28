"""
SYNOPSIS
    General Ledger Financial Statements.

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

from TartanClasses import ASD, CCD, CreateChart, FinReport, GetCtl, MyFpdf
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, doWriteExport, getModName, copyList
from tartanFunctions import mthendDate, showError
from tartanWork import mthnam

class gl3050(object):
    def __init__(self, **opts):
        self.opts = opts
        self.loop = False
        if self.setVariables():
            if "args" in self.opts and "stream" in self.opts["args"]:
                self.strm = 0
                self.repprt = ['N', 'N', '']
                self.repeml = ['N', 'N', '', '', 'Y']
                for arg in self.opts["args"]:
                    if arg in ("stream", "noprint"):
                        continue
                    setattr(self, arg, self.opts["args"][arg])
                self.doMainEnd()
            elif "args" in self.opts and "noprint" not in self.opts["args"]:
                self.end, self.typ, self.rep, self.val, self.var, self.zer, \
                    self.repprt, self.repeml, self.fpdf = self.opts["args"]
                yed = CCD(mthendDate((self.end * 100) + 1), "D1", 10)
                self.yed = "%s %s %s" % ((yed.work % 100),
                    mthnam[int((yed.work % 10000) / 100)][1],
                    int(yed.work / 10000))
                self.cyr = "  %4s" % int(self.end / 100)
                self.pyr = "  %4s" % (int(self.end / 100) - 1)
                self.strm = 0
                self.con = "N"
                self.dep = "N"
                self.gen = "Y"
                self.opt = "N"
                self.num = "N"
                self.doMainEnd()
            elif "wait" in self.opts:
                self.mainProcess()
                self.df.mstFrame.wait_window()
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        self.gldep = ctlsys["sys_gl_dep"]
        self.gldig = ctlsys["sys_gl_dig"]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctldep", "genbud",
            "gendtm", "gendtt", "genrpt", "genrpc", "genstr"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.i_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        df = self.e_per - self.i_per - 87
        if df > 12:
            self.d_per = df - 12
            yr = int(self.i_per / 100)
            mt = self.i_per % 100
            for _ in range(self.d_per):
                mt += 1
                if mt > 12:
                    mt -= 12
                    yr += 1
            self.s_per = (yr * 100) + mt
        else:
            self.d_per = 0
            self.s_per = self.i_per
        self.titles = {
            1: ["Acc-Num", "UI", 7, False, False, True],
            2: ["Description", "NA", 30],
            3: ["Actual", "CD", 17.2],
            4: ["Budget", "CI", 14],
            5: ["Variance", "CI", 14],
            6: ["Var-%", "SD", 7.2],
            7: ["Last-Year", "CD", 17.2],
            8: ["Last-3-Years", "CD", 17.2],
            9: ["Open-Bal", "CD", 17.2],
           10: ["Close-Bal", "CD", 17.2]}
        m = self.s_per % 100
        for x in range(0, 12):
            self.titles[x+11] = [mthnam[m][1], "CD", 17.2]
            m += 1
            if m > 12:
                m = 1
        self.colsn = [7, 2, 3]
        self.colsv = [7, 2, 3, 4, 5, 6]
        self.colsh = [2, 7, 7, 7, 3, 4, 5, 6]
        self.colln = [2, 3, 3, 7]
        self.collv = [2, 3, 4, 5, 6, 3, 4, 5, 6, 7]
        self.colsm = [2, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 10]
        self.colsc = []
        self.ulc = "X"                          # Temporary Underline Character
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Financial Statements (%s)" % self.__class__.__name__)
        stm = {
            "stype": "R",
            "tables": ("genstr",),
            "cols": (
                ("gls_strm", "", 0, "Num"),
                ("gls_desc", "", 0, "Description", "Y"),
                ("count(*)", "UI", 3, "Qty")),
            "where": [("gls_cono", "=", self.opts["conum"])],
            "group": "gls_strm"}
        rpt = {
            "stype": "R",
            "tables": ("genrpt",),
            "cols": (
                ("glr_repno", "", 0, "Num"),
                ("glr_type", "", 0, "T"),
                ("glr_desc", "", 0, "Description", "Y")),
            "where": [
                ("glr_cono", "in", (0, self.opts["conum"])),
                ("glr_seq", "=", 0),
                ("glr_type", "in", ("P", "B", "O"))],
            "group": "glr_repno, glr_type, glr_desc"}
        det = {
            "stype": "R",
            "tables": ("gendtm",),
            "cols": (
                ("gdm_code", "", 0, "T"),
                ("gdm_desc", "", 0, "Description", "Y")),
            "where": [("gdm_cono", "=", self.opts["conum"])]}
        r1s = (
            ("Short","S"),
            ("Long","L"),
            ("History","H"),
            ("Month","M"),
            ("Custom","C"))
        r2s = (("Yes","Y"),("No","N"))
        r3s = (
            ("Values","V"),
            ("Budgets","B"),
            ("Combined","C"),
            ("Variances","X"),
            ("Detail","D"))
        r4s = (
            ("Budgets","B"),
            ("Previous-Year","P"),
            ("None","N"))
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            var[1] = 0
            view = None
            mail = None
        else:
            var = ["",0,"S","N","N",1,"N","V","","","B","Y","N","Y"]
            view = ("Y", "V")
            mail = ("Y", "N")
        fld = (
            (("T",0,0,0),"ID2",7,"Ending Period","Ending Period (YYYYMM)",
                self.e_per,"Y",self.doRepPer,None,None,None),
            (("T",0,1,0),"IUI",3,"Stream Number","",
                var[1],"N",self.doRepStr,stm,None,None,None,
                "Use a Report Stream Record as created using Stream Records"),
            (("T",0,2,0),("IRB",r1s),0,"Report Type","",
                var[2],"N",self.doType,None,None,None,None,
                """Valid Report Types:

Short   - Last-Year, Description, Actual, Budget, Variance
History - Description, Previous 3 Years, Actual, Budget, Variance
Long    - Acc-Num, Description, Current Month, Year-to-Date
Month   - Acc-Num, Description, Opening Balance, Months x 12, Closing Balance
Custom  - Customised Report"""),
            (("T",0,3,0),("IRB",r2s),0,"Consolidate","",
                var[3],"N",self.doCons,None,None,None,None,
                "Print a Consolidated Report of Multiple Companies"),
            (("T",0,4,0),("IRB",r2s),0,"Departments","",
                var[4],"N",self.doDept,None,None,None,None,
                "Departmentalize the report using Department Numbers as "\
                "stipulated in the System Record."),
            (("T",0,5,0),"IUI",3,"Report Number","",
                var[5],"N",self.doRepNum,rpt,None,("notzero",)),
            (("T",0,6,0),("IRB",r2s),0,"General Report","",
                var[6],"N",self.doRepGen,None,None,None),
            (("T",0,7,0),("IRB",r3s),0,"Contents","",
                var[7],"N",self.doRepVal,None,None,None),
            (("T",0,8,0),"INa",2,"Detail Code","",
                var[8],"N",self.doRepDet,det,None,("notblank",)),
            (("T",0,8,0),"ONA",30,""),
            (("T",0,9,0),("IRB",r4s),0,"Variance","",
                var[10],"N",self.doRepVar,None,None,None),
            (("T",0,10,0),("IRB",r2s),0,"Ignore Zeros","",
                var[11],"N",self.doIgnore,None,None,None),
            (("T",0,11,0),("IRB",r2s),0,"Print Options","",
                var[12],"N",self.doOptions,None,None,None),
            (("T",0,12,0),("IRB",r2s),0,"Account Numbers","",
                var[13],"N",self.doNumber,None,None,None))
        tnd = ((self.doMainEnd,"y"), )
        txt = (self.doMainExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doRepPer(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.end = w
        yed = CCD(mthendDate((self.end * 100) + 1), "D1", 10)
        self.yed = "%s %s %s" % ((yed.work % 100),
            mthnam[int((yed.work % 10000) / 100)][1], int(yed.work / 10000))
        self.cyr = "  %4s" % int(self.end / 100)
        self.pyr = "  %4s" % (int(self.end / 100) - 1)
        bud = self.sql.getRec("genbud", where=[("glb_cono", "=",
            self.opts["conum"]), ("glb_curdt", "between", self.s_per,
            self.end)])
        if bud:
            self.df.topf[pag][10][5] = "B"
        else:
            self.df.topf[pag][10][5] = "P"
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.strm = 0
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doRepStr(self, frt, pag, r, c, p, i, w):
        self.strm = w
        if self.strm:
            chk = self.sql.getRec("genstr", where=[("gls_cono", "=",
                self.opts["conum"]), ("gls_strm", "=", self.strm)], limit=1)
            if not chk:
                return "Invalid Stream Number"
            return "nd"

    def doType(self, frt, pag, r, c, p, i, w):
        self.typ = w
        chk = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if chk[0] == 1:
            self.con = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.con)
            if self.gldep == "N":
                self.dep = "N"
                self.df.loadEntry(frt, pag, p+2, data=self.dep)
                return "sk2"
            return "sk1"

    def doCons(self, frt, pag, r, c, p, i, w):
        self.con = w
        if self.con == "Y" or self.gldep == "N":
            self.dep = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.dep)
            return "sk1"

    def doDept(self, frt, pag, r, c, p, i, w):
        self.dep = w

    def doRepNum(self, frt, pag, r, c, p, i, w):
        if self.con == "Y":
            whr = [("glr_cono", "=", 0), ("glr_repno", "=", w)]
        else:
            whr = [("glr_cono", "in", (0, self.opts["conum"])), ("glr_repno",
                "=", w)]
        whr.append(("glr_seq", "=", 0))
        chk = self.sql.getRec("genrpt", cols=["glr_cono"], where=whr,
            order="glr_cono")
        if not chk:
            return "Invalid Report Number"
        self.rep = w
        self.gen = "N"
        for ck in chk:
            if ck[0] == 0:
                self.gen = "Y"
                if self.con == "Y":
                    break
            else:
                self.gen = "N"
        if self.gen == "Y":
            err = self.getRepDetails()
            if err:
                return err
            self.df.loadEntry(frt, pag, p+1, data=self.gen)
            if self.typ == "C":
                self.val = "V"
                self.df.loadEntry(frt, pag, p+2, data=self.val)
                return "sk4"
            else:
                return "sk1"
        elif self.con == "Y":
            return "Invalid Report, Not A General Report"

    def doRepGen(self, frt, pag, r, c, p, i, w):
        if self.con == "Y" and w == "N":
            return "Invalid"
        self.gen = w
        err = self.getRepDetails()
        if err:
            return err
        if self.typ == "C":
            self.val = "V"
            self.df.loadEntry(frt, pag, p+1, data=self.val)
            return "sk3"

    def doRepVal(self, frt, pag, r, c, p, i, w):
        if w in ("B", "C", "X") and self.typ != "M":
            return "Invalid"
        self.val = w
        if self.val == "D":
            return
        self.df.loadEntry(frt, pag, p+1, data="")
        self.df.loadEntry(frt, pag, p+2, data="")
        if self.typ == "M" and self.val != "C":
            self.var = "N"
            self.df.loadEntry(frt, pag, p+3, data=self.var)
            return "sk3"
        return "sk2"

    def doRepDet(self, frt, pag, r, c, p, i, w):
        det = self.sql.getRec("gendtm", cols=["gdm_desc"],
            where=[("gdm_cono", "=", self.opts["conum"]),
            ("gdm_code", "=", w)], limit=1)
        if not det:
            return "Invalid Code"
        self.det = w
        self.df.loadEntry(frt, pag, p+1, data=det[0])

    def doRepVar(self, frt, pag, r, c, p, i, w):
        if self.typ == "M" and w == "N":
            return "Invalid Variance, Only B or P"
        self.var = w

    def doIgnore(self, frt, pag, r, c, p, i, w):
        self.zer = w
        if self.typ == "C":
            self.df.topf[0][11][5] = "N"
        else:
            self.df.topf[0][11][5] = "Y"

    def doOptions(self, frt, pag, r, c, p, i, w):
        self.opt = w
        if self.typ not in ("L", "M"):
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"

    def doNumber(self, frt, pag, r, c, p, i, w):
        self.num = w

    def doMainEnd(self):
        if "args" not in self.opts or "noprint" in self.opts["args"]:
            self.repprt = self.df.repprt
            self.repeml = self.df.repeml
            self.t_work = [self.df.t_work[0][0]]
            self.df.closeProcess()
        if self.strm:
            reps = self.sql.getRec("genstr", where=[("gls_cono", "=",
                self.opts["conum"]), ("gls_strm", "=", self.strm)])
            if reps:
                col = self.sql.genstr_col
                for rep in reps:
                    seq = rep[col.index("gls_seq")]
                    self.typ = rep[col.index("gls_typ")]
                    self.cno = rep[col.index("gls_cno")]
                    self.con = rep[col.index("gls_con")]
                    self.dep = "N"
                    self.dpl = [0]
                    self.rep = rep[col.index("gls_rep")]
                    self.gen = rep[col.index("gls_gen")]
                    err = self.getRepDetails()
                    if err:
                        continue
                    self.val = rep[col.index("gls_val")]
                    self.det = rep[col.index("gls_det")]
                    self.var = rep[col.index("gls_var")]
                    if not self.var:
                        self.var = "B"
                    self.zer = rep[col.index("gls_zer")]
                    self.opt = rep[col.index("gls_opt")]
                    if not self.opt:
                        self.opt = "N"
                    self.num = rep[col.index("gls_num")]
                    if not self.num:
                        self.num = "Y"
                    if not rep[col.index("gls_prnt")]:
                        self.repprt[1] = "N"
                        self.repprt[2] = ""
                        self.pdfnam = getModName(self.opts["mf"].
                            rcdic["wrkdir"], self.__class__.__name__,
                            "%s_%s" % (self.opts["conum"], seq), ext="pdf")
                    elif rep[col.index("gls_prnt")] == "Export":
                        self.repprt[1] = "X"
                        self.repprt[2] = "export"
                        self.pdfnam = getModName(self.opts["mf"].
                            rcdic["wrkdir"], self.__class__.__name__,
                            "%s_%s" % (self.opts["conum"], seq))
                    else:
                        self.repprt[1] = "N"
                        self.repprt[2] = rep[col.index("gls_prnt")]
                        self.pdfnam = getModName(self.opts["mf"].
                            rcdic["wrkdir"], self.__class__.__name__,
                            "%s_%s" % (self.opts["conum"], seq), ext="pdf")
                    if rep[col.index("gls_mail")]:
                        self.repeml[1] = "Y"
                        self.repeml[2] = rep[col.index("gls_mail")]
                    if self.typ == "C":
                        if self.doReadCustomReport("stream") or not self.cols:
                            continue
                    self.doCreateReport()
        else:
            if self.repprt[2] == "export":
                self.pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"])
            else:
                self.pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.con == "Y":
                self.doConCoy()
                if self.con == "X":
                    if "wait" not in self.opts:
                        self.opts["mf"].closeLoop()
                    return
            if self.dep == "Y":
                self.doDepNum()
                if self.dep == "X":
                    if "wait" not in self.opts:
                        self.opts["mf"].closeLoop()
                    return
            else:
                self.dpl = [0]
            if self.typ == "C":
                self.doCustomReport()
                if not self.cols:
                    if "wait" not in self.opts:
                        self.opts["mf"].closeLoop()
                    return
            self.doCreateReport()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def getRepDetails(self):
        if self.gen == "Y":
            self.rco = 0
        else:
            self.rco = self.opts["conum"]
        chk = self.sql.getRec("genrpt", cols=["glr_type", "glr_desc"],
            where=[("glr_cono", "=", self.rco), ("glr_repno", "=", self.rep),
            ("glr_seq", "=", 0)], limit=1)
        if not chk:
            return "Invalid Report Number or Type"
        self.rptyp, self.rpdes = chk

    def doConCoy(self):
        tit = ("Companies to Consolidate",)
        self.coys = self.sql.getRec("ctlmst", cols=["ctm_cono",
            "ctm_name"], order="ctm_cono")
        coy = {
            "stype": "C",
            "titl": "",
            "head": ("Num", "Name"),
            "typs": (("UI",3), ("NA",30)),
            "data": self.coys,
            "mode": "M",
            "comnd": self.doCoyCmd}
        r1s = (("Yes","Y"),("Include","I"),("Exclude","E"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Companies","",
                "Y","N",self.doAllCoy,None,None,None,None),
            (("T",0,1,0),"INA",(30,100),"Companies","",
                "","N",self.doCoySel,coy,None,None,None))
        self.cc = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doCoyEnd, "y"),), txit=(self.doCoyExit,))
        self.cc.mstFrame.wait_window()

    def doAllCoy(self, frt, pag, r, c, p, i, w):
        self.acc = w
        if self.acc == "Y":
            self.con = []
            for coy in self.coys:
                self.con.append(coy[0])
            return "nd"
        if self.acc == "I":
            self.cc.topf[pag][1][8]["titl"] = "Select Companies to Include"
        else:
            self.cc.topf[pag][1][8]["titl"] = "Select Companies to Exclude"

    def doCoyCmd(self, frt, pag, r, c, p, i, w):
        c = ""
        for co in w:
            if int(co[0]):
                c = c + str(int(co[0])) + ","
        if len(c) > 1:
            c = c[:-1]
        self.cc.loadEntry(frt, pag, p, data=c)

    def doCoySel(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid List of Companies"
        if w[-1:] == ",":
            w = w[:-1]
        self.coy = w.split(",")

    def doCoyEnd(self):
        if self.acc == "I":
            self.con = self.coy
        elif self.acc == "E":
            self.con = []
            for co in self.coys:
                self.con.append(int(co[0]))
            for co in self.coy:
                del self.con[self.con.index(int(co))]
            self.con.sort()
        self.doCoyClose()

    def doCoyExit(self):
        self.con = "X"
        self.doCoyClose()

    def doCoyClose(self):
        self.cc.closeProcess()

    def doDepNum(self):
        tit = ("Departments to Print",)
        self.deps = self.sql.getRec("ctldep", cols=["dep_code",
            "dep_name"], where=[("dep_cono", "=", self.opts["conum"])],
            order="dep_code")
        dep = {
            "stype": "C",
            "titl": "",
            "head": ("Num", "Name"),
            "typs": (("UI",3), ("NA",30)),
            "data": self.deps,
            "mode": "M",
            "comnd": self.doDepCmd}
        r1s = (("Yes","Y"),("Include","I"),("Exclude","E"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Departments","",
                "Y","N",self.doAllDep,None,None,None,None),
            (("T",0,1,0),"INA",(30,100),"Departments","",
                "","N",self.doDepSel,dep,None,None,None))
        self.dc = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doDepEnd, "y"),), txit=(self.doDepExit,))
        self.dc.mstFrame.wait_window()

    def doAllDep(self, frt, pag, r, c, p, i, w):
        self.dep = w
        if self.dep == "Y":
            self.dpl = []
            for dep in self.deps:
                self.dpl.append(dep[0])
            return "nd"
        if self.dep == "I":
            self.dc.topf[pag][1][8]["titl"] = "Select Departments to Include"
        else:
            self.dc.topf[pag][1][8]["titl"] = "Select Departments to Exclude"

    def doDepCmd(self, frt, pag, r, c, p, i, w):
        c = ""
        for co in w:
            if int(co):
                c = c + str(int(co)) + ","
        if len(c) > 1:
            c = c[:-1]
        self.dc.loadEntry(frt, pag, p, data=c)

    def doDepSel(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid List of Departments"
        if w[-1:] == ",":
            w = w[:-1]
        self.dpt = w.split(",")

    def doDepEnd(self):
        if self.dep == "I":
            self.dpl = self.dpt
        elif self.dep == "E":
            self.dpl = []
            for dp in self.deps:
                self.dpl.append(int(dp[0]))
            for dp in self.dpt:
                del self.dpl[self.dpl.index(int(dp))]
            self.dpl.sort()
        self.doDepClose()

    def doDepExit(self):
        self.dep = "X"
        self.doDepClose()

    def doDepClose(self):
        self.dc.closeProcess()

    def doCustomReport(self):
        tit = ("Custom Report Headings and Columns to Print",)
        rpc = {
            "stype": "C",
            "titl": "Available Custom Reports",
            "head": ("No", "Heading-1", "Heading-2"),
            "data": self.doLoadReports()}
        var = {
            "stype": "C",
            "titl": "Available Variables",
            "head": ("Code", "Description"),
            "data": (
                ("C-Year", "Prints the Current Year e.g. 2009"),
                ("P-Year", "Prints the Previous Year e.g. 2008)"))}
        data = []
        for d in self.titles:
            if d > 8:
                continue
            data.append(self.titles[d][0])
        col = {
            "stype": "C",
            "titl": "Available Columns",
            "head": ("Heading",),
            "data": data}
        check = [""]
        check.extend(copyList(data))
        self.tag = (
            ("Headings",self.chgPage1,None,None),
            ("Columns",self.chgPage2,None,None))
        fld = [
            [("T",1,0,0),"IUI",2,"Custom Number","",
                "","Y",self.doCusNo,rpc,None,("notblank",)],
            [("T",1,1,0),"INA",50,"Company Name","",
                "","N",self.doHeader,None,self.doDelete,("notblank",)]]
        if self.rptyp in ("B", "P"):
            fld.extend([
            [("T",1,2,0),"ITX",50,"B/S Heading","",
                "","N",self.doHeader,None,None,("notblank",),None,
                "Use %ymd to Insert a Date in the Heading Line e.g. "\
                "28 February 2008"],
            [("T",1,3,0),"ITX",50,"P&L Heading","",
                "","N",self.doHeader,None,None,("notblank",),None,
                "Use %ymd to Insert a Date in the Heading Line e.g. "\
                "28 February 2008"]])
        else:
            fld.append(
            [("T",1,2,0),"ITX",50,"Other Heading","",
                "","N",self.doHeader,None,None,("notblank",),None,
                "Use %ymd to Insert a Date in the Heading Line e.g. "\
                "28 February 2008"])
        fld.extend([
            [("T",2,0,0),"IUI",2,"Position","",
                0,"N",self.doPosition,None,None,("between",0,6)],
            [("C",2,0,0),"OUI",2,"P","P",
                "","N",None,None,None,None],
            [("C",2,0,1),"INA",20,"Column","",
                "","N",self.doColumn,col,None,("in", check)],
            [("C",2,0,2),"INA",20,"Title","",
                "","N",None,var,None,("efld",)]])
        but = (
            ("Accept",None,self.doAccept,2,None,None),
            ("Quit",None,self.doQuit,1,None,None))
        txit = (None,self.doTopExit,self.doTopExit)
        tend = (None,(self.doTopEnd,"n"),(self.doTopEnd,"n"))
        cxit = (None,None,self.doColExit)
        cend = (None,None,(self.doColEnd,"n"))
        self.cr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            tags=self.tag, eflds=fld, rows=(0,0,7), butt=but, tend=tend,
            txit=txit, cend=cend, cxit=cxit)
        self.cr.mstFrame.wait_window()

    def doCusNo(self, frt, pag, r, c, p, i, w):
        self.cno = w
        self.doReadCustomReport()

    def doReadCustomReport(self, ctype=None):
        self.cols = []
        self.whr = [("glc_cono", "=", self.opts["conum"]), ("glc_cusno", "=",
            self.cno)]
        self.old = self.sql.getRec("genrpc", where=self.whr, limit=1)
        self.desc = True
        if self.old:
            if ctype:
                pads = 0
            self.new = False
            self.heds = [self.old[self.sql.genrpc_col.index("glc_head1")]]
            self.heds.append(self.old[self.sql.genrpc_col.index("glc_head2")])
            self.heds.append(self.old[self.sql.genrpc_col.index("glc_head3")])
            self.heds.append(self.old[self.sql.genrpc_col.index("glc_head4")])
            for x in range(6, 19, 2):
                if not self.old[x]:
                    break
                for idx in self.titles:
                    if self.titles[idx][0] == self.old[x]:
                        self.cols.append((idx, self.old[x], self.old[x+1]))
                        break
                if ctype:
                    pads = pads + int(self.titles[idx][2]) + 2
            if ctype:
                if pads < 80:
                    self.titles[2][2] = int(self.titles[2][2]) + 79 - pads
                for col in self.cols:
                    if col[0] == 2 and not col[2]:
                        self.desc = False
                return
        elif ctype:
            return "error"
        else:
            self.new = True
            self.heds = [
                self.opts["conam"],
                "Balance Sheet as at %ymd",
                "Income Statement for the Year Ended %ymd"]
            if self.rptyp in ("B", "P"):
                self.heds.append("")
            else:
                self.heds.append(self.rpdes + " as at %ymd")
        # Populate Fields
        self.cr.topf[1][1][5] = self.heds[0]
        if not self.new:
            self.cr.loadEntry("T", 1, 1, data=self.heds[0])
        if self.rptyp in ("B", "P"):
            self.cr.topf[1][2][5] = self.heds[1]
            self.cr.topf[1][3][5] = self.heds[2]
            if not self.new:
                self.cr.loadEntry("T", 1, 2, data=self.heds[1])
                self.cr.loadEntry("T", 1, 3, data=self.heds[2])
        else:
            self.cr.topf[1][2][5] = self.heds[3]
            if not self.new:
                self.cr.loadEntry("T", 1, 2, data=self.heds[3])
        if not self.new:
            for num, (idx, nam, tit) in enumerate(self.cols):
                self.cr.loadEntry("C", 2, ((num * 3)+1), data=nam)
                self.cr.loadEntry("C", 2, ((num * 3)+2), data=tit)
            # Enable Tags and Accept Button
            self.cr.enableTag(0)
            self.cr.enableTag(1)
            self.cr.B0.configure(state='normal')

    def chgPage1(self):
        self.cr.focusField("T", 1, 2, clr=False)

    def chgPage2(self):
        self.cr.focusField("T", 2, 1, clr=False)

    def doHeader(self, frt, pag, r, c, p, i, w):
        if self.rptyp in ("B", "P"):
            self.heds[p-1] = w
        else:
            self.heds[3] = w

    def doDelete(self):
        self.sql.delRec("genrpc", where=self.whr)
        self.opts["mf"].dbm.commitDbase()
        self.cr.topf[1][0][8]["data"] = self.doLoadReports()
        self.cr.focusField("T", 1, 1)

    def doLoadReports(self):
        data = []
        acc = self.sql.getRec("genrpc", where=[("glc_cono", "=",
            self.opts["conum"])], order="glc_cusno")
        for a in acc:
            if self.rptyp == "B":
                data.append([a[1], a[2], a[3]])
            elif self.rptyp == "P":
                data.append([a[1], a[2], a[4]])
            else:
                data.append([a[1], a[2], a[5]])
        return data

    def doPosition(self, frt, pag, r, c, p, i, w):
        self.seq = w

    def doColumn(self, frt, pag, r, c, p, i, w):
        if not w:
            for x in range(p, 21):
                if not x % 3:
                    continue
                self.cr.loadEntry(frt, pag, x, data="")
            self.seq -= 1
            return "sk1"
        if w == "Description":
            self.desc = True
        if self.new or not self.cr.c_work[pag][r][i+1]:
            self.cr.loadEntry(frt, pag, p+1, data=w)

    def doTopEnd(self):
        if self.cr.pag == 1:
            for pos in range(7):
                self.cr.loadEntry("C", 2, (pos * 3), data=pos)
            self.cr.selPage("Columns")
        elif self.cr.pag == 2:
            self.cr.focusField("C", 2, ((self.seq * 3) + 1), clr=False)

    def doTopExit(self):
        if self.cr.pag == 1:
            self.doQuit()
        elif self.cr.pag == 2:
            if not self.desc:
                showError(self.opts["mf"].body, "Description Error",
                    "You Must Select the Description Column!")
                self.cr.focusField("T", 2, 1, clr=False)
                return
            pads = 0
            self.cols = []
            data = [self.opts["conum"], self.cno] + self.heds
            for row in self.cr.c_work[2]:
                if row[1]:
                    data.extend([row[1], row[2]])
                    for d in self.titles:
                        if self.titles[d][0] == row[1]:
                            self.cols.append((d, row[1], row[2]))
                            pads = pads + int(self.titles[d][2]) + 2
                            break
                    if d == 2 and not row[2]:
                        self.desc = False
            for _ in range(len(data), 20):
                data.append("")
            pads = pads - 2
            if pads < 80:
                self.titles[2][2] = int(self.titles[2][2]) + 79 - pads
            if self.new:
                self.sql.insRec("genrpc", data=data)
            elif data != self.old[:len(data)]:
                col = self.sql.genrpc_col
                data.append(self.old[col.index("glc_xflag")])
                self.sql.updRec("genrpc", data=data, where=self.whr)
            self.opts["mf"].dbm.commitDbase()
            self.cr.closeProcess()

    def doColEnd(self):
        if self.seq != 6:
            self.seq += 1
        self.cr.loadEntry("T", 2, 0, data=self.seq)
        self.cr.focusField("T", 2, 1, clr=False)

    def doColExit(self):
        self.cr.focusField("T", 2, 1, clr=False)

    def doAccept(self):
        frt, pag, col, mes = self.cr.doCheckFields(("T",1,None))
        if mes:
            self.cr.selPage(self.tag[pag - 1][0])
            self.cr.focusField(frt, pag, (col+1), err=mes, clr=False)
        else:
            self.cr.pag = 2
            self.doTopExit()

    def doQuit(self):
        self.cols = []
        self.cr.closeProcess()

    def doCreateReport(self):
        if self.gen == "Y":
            rco = 0
        else:
            rco = self.opts["conum"]
        if self.val != "D":
            self.det = None
        elif not self.det:
            self.val = "V"
            self.det = None
        if self.var == "B":
            self.actdes = "          Actual"
            self.vardes = "       Budget"
        elif self.var == "P":
            self.actdes = "    Current-Year"
            self.vardes = "    Last-Year"
            self.titles[4][0] = "Last-Year"
        elif self.var == "N" and self.typ in ("S", "L"):
            self.actdes = "    Current-Year"
            self.titles[3][0] = "Current-Year"
        ####################################################################
        # RTYPE Determines the basis of the sign check i.e. MTD or YTD value
        # Maybe this should be an interactive request (Y=YTD, M=MTD)
        ####################################################################
        if self.typ in ("C", "L", "S", "H"):
            rtype = "Y"
        else:
            rtype = "Y"
        ####################################################################
        self.allfields = []
        for dep in self.dpl:
            self.fin = FinReport(self.opts["mf"], (self.gldep, self.gldig),
                self.opts["conum"], self.opts["period"], rco, self.rep,
                self.end, vcode=self.val, dcode=self.det, varcd=self.var,
                consol=self.con, depart=int(dep), rtype=rtype)
            if self.fin.allFields:
                self.allfields.extend(self.fin.allFields)
        if not self.allfields:
            return
        if self.repprt[2] == "export":
            self.doExportReport()
        else:
            self.doPrintReport()
            # For type M and a Manual or Auto Chart is selected
            if "args" not in self.opts and not self.strm and \
                    self.gldep == "N" and (self.achart or self.mchart):
                if self.val == "C":
                    end = self.e_per
                else:
                    end = self.end
                CreateChart(self.opts["mf"], self.opts["conum"],
                    self.opts["conam"], [self.s_per, end],
                    [[self.opts["conam"], "Financial Statement"],
                    self.des1], self.achart, self.mchart)

    def doExportReport(self):
        self.expheads = ["%03u %-30s" % (self.opts["conum"],
            self.opts["conam"])]
        self.expheads.append("TYPE")
        self.expcolsh = [[]]
        self.expforms = []
        if self.typ == "S":
            if self.var == "N":
                colss = copyList(self.colsn)
            else:
                colss = copyList(self.colsv)
            for h in colss:
                self.expcolsh[0].append(self.titles[h][0])
                self.expforms.append(self.titles[h][1:])
        elif self.typ == "H":
            for n, h in enumerate(self.colsh):
                if h == 7:
                    if self.fin.pers[n]:
                        ly = CCD(self.fin.pers[n]["e_per"], "D2", 7).disp
                    else:
                        ly = ""
                    self.expcolsh[0].append(ly)
                else:
                    self.expcolsh[0].append(self.titles[h][0])
                self.expforms.append(self.titles[h][1:])
        elif self.typ == "L":
            if self.var == "N":
                colsl = copyList(self.colln)
                if self.num == "Y":
                    colsl.insert(0, 1)
                    self.expcolsh = [["", "", ["", 2, 5], ["", 6, 9], ""], []]
                else:
                    self.expcolsh = [["", ["", 1, 4], ["", 5, 8], ""], []]
                for h in colsl:
                    self.expcolsh[1].append(self.titles[h][0])
                    self.expforms.append(self.titles[h][1:])
            else:
                colsl = copyList(self.collv)
                if self.num == "Y":
                    colsl.insert(0, 1)
                    self.expcolsh = [["", "",
                        ["************** Current-Month **************", 2, 5],
                        ["************** Year-to-Date  **************", 6, 9],
                        ""], []]
                else:
                    self.expcolsh = [["",
                        ["************** Current-Month **************", 1, 4],
                        ["************** Year-to-Date  **************", 5, 8],
                        ""], []]
                for h in colsl:
                    self.expcolsh[1].append(self.titles[h][0])
                    self.expforms.append(self.titles[h][1:])
        elif self.typ == "M":
            if self.num == "Y":
                self.colsm.insert(0, 1)
            for h in self.colsm:
                self.expcolsh[0].append(self.titles[h][0])
                self.expforms.append(self.titles[h][1:])
            if self.val == "V":
                self.des1 = "Actuals"
            elif self.val == "B":
                self.des1 = "Budgets"
            elif self.val == "C":
                self.des1 = "Actuals and Budgets"
            elif self.val == "X":
                self.des1 = "Variance to Budget"
            elif self.val == "D":
                self.des1 = "Details"
            self.lastmth = self.end % 100
        elif self.typ == "C":
            for col in self.cols:
                self.expcolsh[0].append(col[2])
                self.expforms.append(self.titles[col[0]][1:])
        self.expdatas = []
        self.counter = 0
        p = ProgressBar(self.opts["mf"].body, mxs=len(self.allfields), esc=True)
        for num, dat in enumerate(self.allfields):
            p.displayProgress(num)
            if dat[6] < self.counter:
                dat[3] = "Y"
            if not num:
                self.pageHeading(dat)
            if dat[0] == "H":
                self.doHeading(dat)
            elif dat[0] in ("C","G","L","P","S","T"):
                self.doValues(dat)
            elif dat[0] == "U":
                self.doUnderline(dat)
            self.counter = dat[6]
        p.closeProgress()
        if self.strm and self.repprt[2] == "export":
            view = False
        else:
            view = True
        doWriteExport(xtype=self.repprt[1], name=self.pdfnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic, view=view)

    def doPrintReport(self):
        p = ProgressBar(self.opts["mf"].body, mxs=len(self.allfields))
        self.head = []
        self.linb = ""
        self.lind = ""
        self.linh = ""
        self.linu = ""
        self.linw = ""
        self.last = False
        if self.typ == "S":
            if self.var == "N":
                self.width = 75
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            else:
                self.width = 108
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            self.head.append("")
            self.head.append("")
            if self.var == "N":
                self.head.append("%-17s  %-38s  %-17s" % ("       Last-Year",
                    "Description", "    Current-Year"))
                self.linu = "%s  %39s  %s" % (self.ulc*16, "", self.ulc*16)
            else:
                self.head.append("%-17s  %-30s  %-17s  %-14s  %-14s  %-7s" % \
                    ("       Last-Year", "Description", "    Current-Year",
                    self.vardes, "     Variance", " Var-%"))
                self.linu = "%s  %31s  %s  %s  %s  %s" % (self.ulc*16, "",
                    self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7)
        elif self.typ == "H":
            if self.var == "N":
                self.width = 105
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            else:
                self.width = 146
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            self.head.append("")
            self.head.append("")
            hd = "%-30s  " % "Description"
            ln = "%30s  " % ""
            for x in range(3):
                if self.fin.pers[x+1]:
                    hd = "%s%16s   " % (hd,
                        CCD(self.fin.pers[x+1]["e_per"], "D2", 7).disp)
                    ln = "%s%s   " % (ln, self.ulc*16)
                else:
                    hd = "%s%16s   " % (hd, "")
                    ln = "%s%16s   " % (ln, "")
            if self.var == "N":
                self.head.append("%s%-17s" % (hd, "    Current-Year"))
                self.linu = "%s%s" % (ln, self.ulc*16)
            else:
                self.head.append("%s%-17s  %-14s  %-14s  %-7s" % (hd,
                    "    Current-Year", self.vardes, "     Variance", " Var-%"))
                self.linu = "%s%s  %s  %s  %s" % (ln, self.ulc*16, self.ulc*14,
                    self.ulc*14, self.ulc*7)
        elif self.typ == "L":
            if self.var == "N":
                if self.num == "Y":
                    self.width = 95
                    self.head.append("%03u %-30s" % (self.opts["conum"],
                        self.opts["conam"]))
                    hdr = "%-7s  "
                    hdt = ["Acc-Num"]
                    lin = "%7s  "
                    ldt = [""]
                else:
                    self.width = 86
                    self.head.append("%03u %-30s" % (self.opts["conum"],
                        self.opts["conam"]))
                    hdr = ""
                    hdt = []
                    lin = ""
                    ldt = []
                self.head.append("")
                self.head.append("")
                hdr = hdr + "%-30s  %-17s  %-17s %17s"
                hdt.extend(["Description", "   Current-Month",
                    "    Current-Year", "       Last-Year"])
                self.head.append(hdr % tuple(hdt))
                lin = lin + "%30s  %s   %s   %s"
                self.linb = lin % tuple(ldt + ["", " "*16, self.ulc*16,
                    self.ulc*16])
                self.linu = lin % tuple(ldt + ["", self.ulc*16, self.ulc*16,
                    self.ulc*16])
            else:
                if self.var == "P":
                    self.cdes = "    Current-Year"
                else:
                    self.cdes = "          Actual"
                if self.var == "P":
                    hds = 114
                else:
                    hds = 134
                if self.num == "Y":
                    hds += 9
                hft = "%03u %-30s"
                self.head.append(hft % (self.opts["conum"], self.opts["conam"]))
                self.head.append("")
                self.head.append("")
                if self.num == "Y":
                    self.width = 158
                    self.head.append("%-7s  %-30s  %-57s   %-57s" % (
                        "", "",
                        "*********************"\
                        " Current-Month "\
                        "*********************",
                        "*********************"\
                        " Year-to-Date "\
                        "**********************"))
                    hdr = "%-7s  "
                    hdt = ["Acc-Num"]
                    lin = "%7s  "
                    ldt = [""]
                else:
                    self.width = 149
                    self.head.append("%-30s  %-57s   %-57s" % (
                        "",
                        "*********************"\
                        " Current-Month "\
                        "*********************",
                        "*********************"\
                        " Year-to-Date "\
                        "**********************"))
                    hdr = ""
                    hdt = []
                    lin = ""
                    ldt = []
                hdr = hdr + "%-30s  %-17s  %-14s  %-14s  %-7s  %-17s  "\
                    "%-14s  %-14s  %-7s"
                hdt.extend(["Description",
                    self.cdes, self.vardes, "     Variance", " Var-%",
                    self.cdes, self.vardes, "     Variance", " Var-%"])
                lin = lin + "%30s  %s  %s  %s  %s   %s  %s  %s  %s"
                if self.var == "P":
                    self.linu = lin % tuple(ldt + ["",
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7,
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7])
                    self.linb = lin % tuple(ldt + ["",
                        " "*16, " "*14, " "*14, " "*7,
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7])
                else:
                    self.width += 19
                    hdr = hdr + "  %-17s"
                    hdt.extend(["       Last-Year"])
                    lin = lin + "   %s"
                    self.linu = lin % tuple(ldt + ["",
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7,
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7,
                        self.ulc*16])
                    self.linb = lin % tuple(ldt + ["",
                        " "*16, " "*14, " "*14, " "*7,
                        self.ulc*16, self.ulc*14, self.ulc*14, self.ulc*7,
                        self.ulc*16])
                self.head.append(hdr % tuple(hdt))
        elif self.typ == "M":
            if self.num == "Y":
                self.width = 205
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            else:
                self.width = 197
                self.head.append("%03u %-30s" % (self.opts["conum"],
                    self.opts["conam"]))
            self.head.append("")
            self.head.append("")
            if self.val == "V":
                self.des1 = "Actuals"
            elif self.val == "B":
                self.des1 = "Budgets"
            elif self.val == "C":
                self.des1 = "Actuals and Budgets"
            elif self.val == "X":
                self.des1 = "Variances to Budget"
            elif self.val == "D":
                self.des1 = "Details"
            self.lastmth = self.end % 100
            m = self.s_per % 100
            text = ""
            space = " " * 20
            self.cutmth = 11
            for x in range(0, 12):
                text = text + space[0:(10-len(mthnam[m][1]))] + \
                    mthnam[m][1] + "  "
                if self.val == "C" and m == self.lastmth:
                    self.cutmth = x
                m += 1
                if m > 12:
                    m = 1
            if self.num == "Y":
                self.head.append("%-7s %-30s %-11s%-144s%-11s" % ("Acc-Num",
                    "Description", "  Open-Bal  ", text, " Close-Bal  "))
                self.linu = "%7s %30s %s  %s  %s  %s  %s  %s  %s  %s  %s  "\
                    "%s  %s  %s  %s  %s" % ("", "", self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10)
            else:
                self.head.append("%-30s %-11s%-144s%-11s" % ("Description",
                    "  Open-Bal  ", text, " Close-Bal  "))
                self.linu = "%30s %s  %s  %s  %s  %s  %s  %s  %s  %s  %s  "\
                    "%s  %s  %s  %s" % ("",self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10,
                    self.ulc*10, self.ulc*10, self.ulc*10, self.ulc*10)
        elif self.typ == "C":
            self.lhead = ""
            self.ltext = ''
            self.stop = None
            for col in self.cols:
                col = list(col)
                if col[0] == 8:
                    for x in range(3):
                        if self.fin.pers[x+1]:
                            hdr = CCD(self.fin.pers[x+1]["e_per"], "D2", 7)
                        else:
                            hdr = CCD("", "d2", 7)
                        col[2] = hdr.disp
                        self.doLoadLine(col)
                else:
                    if self.var == "P":
                        if col[1] == "Actual":
                            col[1] = col[2] = self.actdes
                        elif col[1] == "Budget":
                            col[1] = col[2] = self.vardes
                    if not col[2]:
                        col[2] = col[1]
                    self.doLoadLine(col)
            self.lhead = self.lhead[:-2]
            self.lhead = self.lhead.replace("C-Year", self.cyr)
            self.ltext = self.ltext.replace("C-Year", self.cyr)
            self.lhead = self.lhead.replace("P-Year", self.pyr)
            self.ltext = self.ltext.replace("P-Year", self.pyr)
            self.lind = self.lind[:-2]
            self.linh = self.linh[:-2]
            self.linw = self.linw[:-1]
            self.heds.append(self.lhead)
            self.width = self.lhead
        if "args" not in self.opts or "noprint" in self.opts["args"] or \
                "stream" in self.opts["args"]:
            self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.width)
        self.pgnum = 0
        self.achart = []
        self.mchart = []
        self.counter = 0
        for num, dat in enumerate(self.allfields):
            p.displayProgress(num)
            if dat[6] < self.counter:
                dat[3] = "Y"
            if self.fpdf.newPage():
                dat[3] = "N"
                self.pageHeading(dat)
            if dat[0] == "H":
                self.doHeading(dat)
            elif dat[0] in ("C","G","L","P","S","T"):
                self.doValues(dat)
                self.fpdf.setFont()
            elif dat[0] == "U":
                self.doUnderline(dat)
            self.counter = dat[6]
        p.closeProgress()
        if "args" not in self.opts and self.fpdf.page:
            self.fpdf.output(self.pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=self.pdfnam, header=self.emlhead,
                repprt=self.repprt, repeml=self.repeml)

    def doLoadLine(self, col):
        text = self.titles[col[0]]
        if text[0] in ("Acc-Num", "Description"):
            hd = "%-" + str(int(text[2])) + "s  "
            self.lhead = self.lhead + hd % col[2]
        else:
            hd = "%" + str(int(text[2]) - 1) + "s   "
            self.lhead = self.lhead + hd % col[2]
        if not self.ltext:
            self.ltext = '"%s"' % col[2]
        else:
            self.ltext = '%s,"%s"' % (self.ltext, col[2])
        self.lind = self.lind + "%" + str(int(text[2])) + "s  "
        if not self.stop:
            self.linh = self.linh + "%-" + str(int(text[2])) + "s  "
        self.linu = self.linu + "%" + str(int(text[2]) - 1) + "s   "
        if text[0] == "Acc-Num":
            if not self.stop:
                self.linh = self.linh % " "
            self.linu = self.linu % " "
            self.linw = self.linw + "%s,"
        elif text[0] == "Description":
            self.linu = self.linu % " "
            self.linw = self.linw + '"%s",'
            self.stop = True
        else:
            if not self.stop:
                self.linh = self.linh % " "
            self.linu = self.linu % ((int(text[2]) - 1) * self.ulc)
            self.linw = self.linw + "%s,"

    def doHeading(self, line):
        if line[3] == "Y":
            if self.repprt[2] == "export":
                if self.oldtyp != line[1]:
                    self.pageHeading(line)
            else:
                self.pageHeading(line)
        if self.repprt[2] == "export":
            data = []
            for num, dat in enumerate(self.expforms):
                if int(self.expforms[num][1]) < 30:
                    data.append("")
                    continue
                data.append(line[5])
                break
            if self.expdatas[-1][0] not in ("PAGE", "BLANK"):
                self.expdatas.append(["BLANK"])
            self.expdatas.append(["HEAD", data])
            self.expdatas.append(["BLANK"])
        else:
            if line[2] == "Y":
                self.fpdf.setFont(style="B")
            if self.typ == "S":
                self.fpdf.drawText("%17s  %s" % ("", line[5]))
            elif self.typ == "H":
                self.fpdf.drawText("%s" % line[5])
            elif self.typ == "L":
                if self.num == "Y":
                    self.fpdf.drawText("%7s  %s" % ("", line[5]))
                else:
                    self.fpdf.drawText("%s" % (line[5]))
            elif self.typ == "M":
                if self.num == "Y":
                    self.fpdf.drawText("%7s %s" % ("", line[5]))
                else:
                    self.fpdf.drawText("%s" % (line[5]))
            elif self.typ == "C":
                self.fpdf.drawText(self.linh % line[5])
            self.fpdf.setFont()
            self.fpdf.drawText()

    def doValues(self, line):
        ldic = {}
        ltp = line[0]
        acc = CCD(line[4], "UI", 7)
        if acc.work == 0:
            acc.disp = "       "
        if self.typ == "C":
            des = CCD(line[5], "NA", self.titles[2][2])
        else:
            des = CCD(line[5], "NA", 30)
        sgn = line[12]
        if self.typ in ("S", "H", "L", "C"):
            if self.typ in ("C", "H"):
                lyr = []
                for x in range(3):
                    if self.fin.pers[x+1]:
                        lyr.append(CCD(line[8][x+1], "CD", 17.2))
                    else:
                        lyr.append(CCD("", "NA", 17))
            else:
                lyr = CCD(line[8][3], "CD", 17.2)
            if self.typ == "L":
                mth = CCD(line[8][4], "CD", 17.2)
                if self.var == "N":
                    bud = CCD(0, "CI", 14)
                    vmt = CCD("", "NA", 14)
                    vmtper = CCD("", "NA", 7)
                else:
                    bud = CCD(int(line[8][5]), "CI", 14)
                    if ltp == "P":
                        vmt = CCD("", "NA", 14)
                        vmtper = CCD("", "NA", 7)
                    else:
                        if sgn == "N" or (self.var == "P" and bud.work < 0):
                            vmt = int(int(mth.work) - bud.work)
                        else:
                            vmt = int(bud.work - int(mth.work))
                        vmt = CCD(vmt, "CI", 14)
                        if bud.work:
                            vmtper = round(vmt.work * 100.0 / bud.work, 2)
                            if vmtper > 0 and vmtper > 999.99:
                                vmtper = 999.99
                            elif vmtper < 0 and vmtper < -999.99:
                                vmtper = -999.99
                        else:
                            vmtper = 0
                        vmtper = CCD(vmtper, "SD", 7.2)
            ytd = CCD(line[8][6], "CD", 17.2)
            if self.var == "N":
                btd = CCD(0, "CI", 14)
                vtd = CCD("", "NA", 14)
                vtdper = CCD("", "NA", 7)
            else:
                btd = CCD(int(line[8][7]), "CI", 14)
                if ltp == "P":
                    vtd = CCD("", "NA", 14)
                    vtdper = CCD("", "NA", 7)
                else:
                    if sgn == "N" or (self.var == "P" and btd.work < 0):
                        vtd = int(int(ytd.work) - btd.work)
                    else:
                        vtd = int(btd.work - int(ytd.work))
                    vtd = CCD(vtd, "CI", 14)
                    if btd.work:
                        vtdper = round(vtd.work * 100.0 / btd.work, 2)
                        if vtdper > 0 and vtdper > 999.99:
                            vtdper = 999.99
                        elif vtdper < 0 and vtdper < -999.99:
                            vtdper = -999.99
                    else:
                        vtdper = 0
                    vtdper = CCD(vtdper, "SD", 7.2)
        else:
            for x in range(14):
                if self.val == "X" and sgn == "N":
                    line[9][x] = float(ASD(0) - ASD(line[9][x]))
                ldic["mp%s" % x] = CCD(int(line[9][x]), "SL", 11)
                ldic["mx%s" % x] = CCD(line[9][x], "SD", 14.2)
        if self.repprt[2] == "export":
            if ltp == "T":
                txt = "TOTAL"
            else:
                txt = "BODY"
        elif line[2] == "Y":
            self.fpdf.setFont(style="B")
        if self.typ == "S":
            if self.zer == "Y" and not lyr.work and not ytd.work \
                    and not btd.work and not vtd.work:
                return
            if self.repprt[2] == "export":
                if self.var == "N":
                    self.expdatas.append([txt, [lyr.work, des.work, ytd.work]])
                else:
                    self.expdatas.append([txt, [lyr.work, des.work, ytd.work,
                        btd.work, vtd.work, vtdper.work]])
            else:
                if self.var == "N":
                    self.fpdf.drawText("%s  %s          %s" % (lyr.disp,
                        des.disp, ytd.disp))
                else:
                    self.fpdf.drawText("%s  %s  %s  %s  %s  %s" % (lyr.disp,
                        des.disp, ytd.disp, btd.disp, vtd.disp, vtdper.disp))
                self.last = True
        elif self.typ == "H":
            if self.zer == "Y" and not lyr[0].work and not lyr[1].work \
                    and not lyr[2].work and not ytd.work and not btd.work \
                    and not vtd.work:
                return
            if self.repprt[2] == "export":
                if self.var == "N":
                    self.expdatas.append([txt, [des.work, lyr[0].work,
                        lyr[1].work, lyr[2].work, ytd.work]])
                else:
                    self.expdatas.append([txt, [des.work, lyr[0].work,
                        lyr[1].work, lyr[2].work, ytd.work, btd.work,
                        vtd.work, vtdper.work]])
            else:
                txt = "%s  %s  %s  %s  %s" % (des.disp, lyr[0].disp,
                    lyr[1].disp, lyr[2].disp, ytd.disp)
                if self.var == "N":
                    self.fpdf.drawText("%s  %s  %s  %s  %s" % (des.disp,
                        lyr[0].disp, lyr[1].disp, lyr[2].disp, ytd.disp))
                else:
                    self.fpdf.drawText("%s  %s  %s  %s  %s  %s  %s  %s" %
                        (des.disp, lyr[0].disp, lyr[1].disp, lyr[2].disp,
                            ytd.disp, btd.disp, vtd.disp, vtdper.disp))
                self.last = True
        elif self.typ == "L":
            if self.zer == "Y" and not mth.work and not bud.work and not \
                    vmt.work and not ytd.work and not btd.work and not \
                    vtd.work and not lyr.work:
                pass
            elif line[1] == "B":
                if self.repprt[2] == "export":
                    if self.var == "N":
                        if self.num == "Y":
                            self.expdatas.append([txt, [acc.work, des.work, "",
                                ytd.work, lyr.work]])
                        else:
                            self.expdatas.append([txt, [des.work, "", ytd.work,
                                lyr.work]])
                    else:
                        if self.num == "Y":
                            self.expdatas.append([txt, [acc.work, des.work, "",
                                "", "", "", ytd.work, btd.work, vtd.work,
                                vtdper.work, lyr.work]])
                        else:
                            self.expdatas.append([txt, [des.work, "", "", "",
                                "", ytd.work, btd.work, vtd.work, vtdper.work,
                                lyr.work]])
                else:
                    if self.var == "N":
                        if self.num == "Y":
                            self.fpdf.drawText("%s  %s  %17s  %s  %s" %
                                (acc.disp, des.disp, "", ytd.disp, lyr.disp))
                        else:
                            self.fpdf.drawText("%s  %17s  %s  %s" %
                                (des.disp, "", ytd.disp, lyr.disp))
                    elif self.var == "P":
                        if self.num == "Y":
                            self.fpdf.drawText("%s  %s  %17s  %-14s  %-14s  "\
                                "%-7s  %s  %s  %s  %s" % (acc.disp,
                                des.disp, "", "", "", "", ytd.disp, btd.disp,
                                vtd.disp, vtdper.disp))
                        else:
                            self.fpdf.drawText("%s  %17s  %-14s  %-14s  %-7s  "\
                                "%s  %s  %s  %s" % (des.disp, "", "", "",
                                "", ytd.disp, btd.disp, vtd.disp, vtdper.disp))
                    else:
                        if self.num == "Y":
                            self.fpdf.drawText("%s  %s  %17s  %-14s  %-14s  "\
                                "%-7s  %s  %s  %s  %s  %s" % (acc.disp,
                                des.disp, "", "", "", "", ytd.disp, btd.disp,
                                vtd.disp, vtdper.disp, lyr.disp))
                        else:
                            self.fpdf.drawText("%s  %17s  %-14s  %-14s  %-7s  "\
                                "%s  %s  %s  %s  %s" % (des.disp, "", "", "",
                                "", ytd.disp, btd.disp, vtd.disp, vtdper.disp,
                                lyr.disp))
                    self.last = True
            else:
                if self.repprt[2] == "export":
                    if self.var == "N":
                        if self.num == "Y":
                            self.expdatas.append([txt, [acc.work, des.work,
                                mth.work, ytd.work, lyr.work]])
                        else:
                            self.expdatas.append([txt, [des.work,
                                mth.work, ytd.work, lyr.work]])
                    else:
                        if self.num == "Y":
                            self.expdatas.append([txt, [acc.work, des.work,
                                mth.work, bud.work, vmt.work, vmtper.work,
                                ytd.work, btd.work, vtd.work, vtdper.work,
                                lyr.work]])
                        else:
                            self.expdatas.append([txt, [des.work,
                                mth.work, bud.work, vmt.work, vmtper.work,
                                ytd.work, btd.work, vtd.work, vtdper.work,
                                lyr.work]])
                else:
                    if self.var == "N":
                        if self.num == "Y":
                            self.fpdf.drawText("%s  %s  %s  %s  %s" % (acc.disp,
                                des.disp, mth.disp, ytd.disp, lyr.disp))
                        else:
                            self.fpdf.drawText("%s  %s  %s  %s" % (des.disp,
                                mth.disp, ytd.disp, lyr.disp))
                    else:
                        if self.num == "Y":
                            self.fpdf.drawText("%s  %s  %s  %s  %s  %s  "\
                                "%s  %s  %s  %s  %s" % (acc.disp, des.disp,
                                mth.disp, bud.disp, vmt.disp, vmtper.disp,
                                ytd.disp, btd.disp, vtd.disp, vtdper.disp,
                                lyr.disp))
                        else:
                            self.fpdf.drawText("%s  %s  %s  %s  %s  %s  "\
                                "%s  %s  %s  %s" % (des.disp, mth.disp,
                                bud.disp, vmt.disp, vmtper.disp, ytd.disp,
                                btd.disp, vtd.disp, vtdper.disp, lyr.disp))
                    self.last = True
        elif self.typ == "M":
            if self.zer == "Y":
                p = "n"
                for x in range(0, 14):
                    if self.repprt[2] == "export":
                        a = ldic["mx%s" % x].work
                    else:
                        a = ldic["mp%s" % x].work
                    if a:
                        p = "y"
            else:
                p = "y"
            if p == "n":
                pass
            elif self.repprt[2] == "export":
                if self.num == "Y":
                    self.expdatas.append([txt, [acc.work, des.work,
                        ldic["mx0"].work, ldic["mx1"].work, ldic["mx2"].work,
                        ldic["mx3"].work, ldic["mx4"].work, ldic["mx5"].work,
                        ldic["mx6"].work, ldic["mx7"].work, ldic["mx8"].work,
                        ldic["mx9"].work, ldic["mx10"].work, ldic["mx11"].work,
                        ldic["mx12"].work, ldic["mx13"].work]])
                else:
                    self.expdatas.append([txt, [des.work, ldic["mx0"].work,
                        ldic["mx1"].work, ldic["mx2"].work, ldic["mx3"].work,
                        ldic["mx4"].work, ldic["mx5"].work, ldic["mx6"].work,
                        ldic["mx7"].work, ldic["mx8"].work, ldic["mx9"].work,
                        ldic["mx10"].work, ldic["mx11"].work, ldic["mx12"].work,
                        ldic["mx13"].work]])
            else:
                if self.num == "Y":
                    txt = "%s %s " % (acc.disp, des.disp)
                else:
                    txt = "%s " % des.disp
                w = self.fpdf.cwth * len(txt)
                self.fpdf.drawText(txt, w=w, ln=0)
                for x in range(14):
                    txt = "%s " % ldic["mp%s" % x].disp
                    w = self.fpdf.cwth * len(txt)
                    p = self.fpdf.get_x()
                    if x == 13:
                        ln = 1
                    else:
                        ln = 0
                    if self.val == "C" and x < 13 and x > self.cutmth + 1:
                        self.fpdf.drawText(txt, x=p, w=w, fill=1, ln=ln)
                    else:
                        self.fpdf.drawText(txt, x=p, w=w, ln=ln)
                self.last = True
                if line[10]:
                    self.achart.append([ltp, line[10], ldic["mp1"].work,
                        ldic["mp2"].work, ldic["mp3"].work, ldic["mp4"].work,
                        ldic["mp5"].work, ldic["mp6"].work, ldic["mp7"].work,
                        ldic["mp8"].work, ldic["mp9"].work, ldic["mp10"].work,
                        ldic["mp11"].work, ldic["mp12"].work])
                if ltp in ("L", "T", "G") and des.work:
                    dsc = des.work
                    for x in ("/", "{", "}"):
                        dsc = dsc.replace(x, "/%s" % x)
                    self.mchart.append([ltp, dsc, ldic["mp1"].work,
                        ldic["mp2"].work, ldic["mp3"].work, ldic["mp4"].work,
                        ldic["mp5"].work, ldic["mp6"].work, ldic["mp7"].work,
                        ldic["mp8"].work, ldic["mp9"].work, ldic["mp10"].work,
                        ldic["mp11"].work, ldic["mp12"].work])
        elif self.typ == "C":
            disp = []
            work = []
            zero = True
            for col in self.cols:
                if self.titles[col[0]][0] == "Acc-Num":
                    disp.append(acc.disp)
                    work.append(acc.work)
                elif self.titles[col[0]][0] == "Description":
                    disp.append(des.disp)
                    work.append(des.work)
                elif self.titles[col[0]][0] in ("Current-Year", "Actual"):
                    disp.append(ytd.disp)
                    work.append(ytd.work)
                    if ytd.work:
                        zero = False
                elif self.titles[col[0]][0] == "Budget":
                    disp.append(btd.disp)
                    work.append(btd.work)
                    if btd.work:
                        zero = False
                elif self.titles[col[0]][0] == "Variance":
                    disp.append(vtd.disp)
                    work.append(vtd.work)
                elif self.titles[col[0]][0] == "Var-%":
                    disp.append(vtdper.disp)
                    work.append(vtdper.work)
                elif self.titles[col[0]][0] == "Last-Year":
                    if self.var == "P":
                        disp.append(btd.disp)
                        work.append(btd.work)
                        if btd.work:
                            zero = False
                    else:
                        disp.append(lyr[2].disp)
                        work.append(lyr[2].work)
                        if lyr[2].work:
                            zero = False
                elif self.titles[col[0]][0] == "Last-3-Years":
                    for x in range(3):
                        disp.append(lyr[x].disp)
                        work.append(lyr[x].work)
                        if lyr[x].work:
                            zero = False
            if self.zer == "Y" and zero:
                pass
            elif self.repprt[2] == "export":
                self.expdatas.append([txt, work])
            else:
                self.fpdf.drawText(self.lind % tuple(disp))
                self.last = True

    def doUnderline(self, line):
        if self.repprt[2] == "export":
            if line[5] == "Blank":
                self.expdatas.append(["BLANK"])
            elif line[5] == "Double":
                self.expdatas.append(["ULINED"])
            else:
                self.expdatas.append(["ULINES"])
            return
        if line[5] == "Blank":
            self.fpdf.drawText()
        elif self.last:
            if line[5] == "Double":
                st = "D"
            else:
                st = "S"
            if self.typ == "L" and line[1] == "B":
                txt = self.linb.replace(self.ulc, self.fpdf.suc)
            elif self.typ == "C":
                txt = self.linu.replace(self.ulc, self.fpdf.suc)
            else:
                txt = self.linu.replace(self.ulc, self.fpdf.suc)
            self.fpdf.underLine(t=st, txt=txt)
        self.last = False

    def pageHeading(self, line):
        if self.repprt[2] == "export":
            expheads = copyList(self.expheads)
            expcolsh = copyList(self.expcolsh)
            if self.typ == "C":
                if self.rptyp in ("B", "P"):
                    if line[11] == "Balance Sheet":
                        head = self.heds[1].replace("%ymd", self.yed)
                    elif line[11] == "Profit and Loss":
                        head = self.heds[2].replace("%ymd", self.yed)
                else:
                    head = self.heds[3].replace("%ymd", self.yed)
            else:
                edate = CCD(self.end, "D2", 7).disp
                head = "%s for period %s to %s" % (line[11],
                    self.opts["period"][1][1][:-3], edate)
                if self.val == "D":
                    head = "%s (%s of %s)" % (head,
                        self.fin.ddet[0].strip(), self.fin.ddet[1].strip())
                elif self.typ == "M":
                    head = "%s (%s)" % (head, self.des1)
                if self.opt == "Y" and len(self.expheads) < 3:
                    expheads.append(self.printOptions())
                if self.typ == "L":
                    if self.num == "Y":
                        start = 2
                    else:
                        start = 1
                    if line[1] == "B":
                        expcolsh[0][start][0] = ""
                        expcolsh[1][start] = ""
                        expcolsh[1][start + 1] = ""
                        expcolsh[1][start + 2] = ""
                        expcolsh[1][start + 3] = ""
            expheads[1] = head
            self.expdatas.append(["PAGE", [expheads, expcolsh]])
            self.oldtyp = line[1]
            return
        self.fpdf.add_page()
        self.pgnum += 1
        if self.typ == "C":
            self.fpdf.setFont(style="B", size=18)
            self.fpdf.drawText(self.heds[0])
            self.fpdf.drawText()
            self.fpdf.setFont(style="B", size=14)
            if self.rptyp in ("B", "P"):
                if line[11] == "Balance Sheet":
                    text = self.heds[1].replace("%ymd", self.yed)
                elif line[11] == "Profit and Loss":
                    text = self.heds[2].replace("%ymd", self.yed)
            else:
                text = self.heds[3].replace("%ymd", self.yed)
            self.fpdf.drawText(text)
            if self.opt == "Y":
                self.printOptions()
            else:
                self.fpdf.drawText()
            self.fpdf.setFont(style="B")
            self.fpdf.drawText(self.heds[4])
            if self.desc:
                self.fpdf.drawText("%s" % (self.fpdf.suc * len(self.width)))
            else:
                self.fpdf.drawText()
            self.emlhead = "Financials for %s as at %s" % (self.opts["conam"],
                self.yed)
        else:
            self.fpdf.setFont(style="B")
            for num, data in enumerate(self.head):
                if num == 2:
                    edate = CCD(self.end, "D2", 7).disp
                    head = "%s for period %s to %s" % (line[11],
                        self.opts["period"][1][1][:-3], edate)
                    if self.val == "D":
                        head = "%s (%s of %s)" % (head,
                            self.fin.ddet[0].strip(), self.fin.ddet[1].strip())
                    if self.typ == "C":
                        self.fpdf.setFont(style="B", size=14)
                        self.fpdf.drawText(head)
                        self.fpdf.setFont(style="B")
                    else:
                        self.fpdf.drawText(head)
                    self.emlhead = head
                    if self.opt == "Y":
                        self.printOptions()
                    self.fpdf.drawText()
                elif line[1] == "B" and num == 3:
                    if self.var == "N":
                        self.fpdf.drawText(data.replace("Current-Month",
                            "             "))
                    else:
                        self.fpdf.drawText(data.replace(
                            "*********************"\
                            " Current-Month "\
                            "*********************",
                            "                     "\
                            "               "\
                            "                     "))
                elif line[1] == "B" and num == 4:
                    if self.var == "B":
                        self.fpdf.drawText(data.replace(
                            "Description                               "\
                            "Actual          Budget        Variance    Var-%",
                            "Description                               "\
                            "                                               "))
                    else:
                        self.fpdf.drawText(data.replace(
                            "Description                         Current-"\
                            "Year       Last-Year        Variance    Var-%",
                            "Description                               "\
                            "                                               "))
                else:
                    self.fpdf.drawText(data)
            self.fpdf.drawText("%s" % (self.fpdf.suc * self.width))
        self.fpdf.setFont()

    def printOptions(self):
        txt = "Options:- "
        if self.strm:
            txt += "Stream: %s " % self.strm
        txt += "Report: %s General: %s " % (self.rep, self.gen)
        if self.typ == "M":
            txt += "Cut-Off: %s " % mthnam[self.lastmth][1]
        if self.val == "V":
            txt += "Content: Actuals"
        elif self.val == "B":
            txt += "Content: Budgets"
        elif self.val == "C":
            txt += "Content: Combination"
        elif self.val == "X":
            txt += "Content: Variances to Budget"
        elif self.val == "D":
            det = self.sql.getRec("gendtt", cols=["gdt_value"],
                where=[("gdt_cono", "=", self.opts["conum"]), ("gdt_code", "=",
                self.det), ("gdt_curdt", "=", self.end)], limit=1)
            if not det:
                mtd = CCD(0, "CD", 17.2).disp
            else:
                mtd = CCD(det[0], "CD", 17.2).disp
            det = self.sql.getRec(tables=["gendtm", "gendtt"],
                cols=["gdm_desc", "sum(gdt_value)"], where=[("gdm_cono", "=",
                self.opts["conum"]), ("gdm_code", "=", self.det),
                ("gdt_cono=gdm_cono",), ("gdt_cono=gdm_cono",),
                ("gdt_code=gdm_code",), ("gdt_curdt", "between", self.s_per,
                self.end)], group="gdm_desc", limit=1)
            des = det[0]
            ytd = CCD(det[1], "CD", 17.2).disp
            if self.typ in ("C", "M", "S", "H"):
                txt += "Detail: %s - Y.T.D. %s" % (des, ytd)
            elif self.typ == "L":
                txt += "Detail: %s - Month %s  Y.T.D. %s" % (des, mtd, ytd)
        if self.con == "N":
            pass
        elif self.acc == "Y":
            txt += " Companies: All "
        else:
            con = str(tuple(self.con)).replace("'", "").replace(" ", "")
            txt += " Companies: %s " % con
        if self.repprt[2] == "export":
            return txt
        self.fpdf.drawText()
        if self.typ == "C":
            self.fpdf.drawText(txt)
            self.fpdf.drawText()
        else:
            self.fpdf.drawText(txt)

    def doMainExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
