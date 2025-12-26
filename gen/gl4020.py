"""
SYNOPSIS
    General Ledger Financial Statement Viewer.

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

from operator import itemgetter
from TartanClasses import ASD, GetCtl, ScrollGrid, SplashScreen, Sql, SRec
from TartanClasses import TartanDialog
from tartanFunctions import getPeriods, copyList, dateDiff, makeArray
from tartanFunctions import mthendDate
from tartanWork import gltrtp, mthnam

class gl4020(object):
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
        self.gldep = ctlsys["sys_gl_dep"]
        self.gldig = ctlsys["sys_gl_dig"]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctldep", "genbal",
            "genbud", "genmst", "genrpt", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        if self.gldep == "Y":
            self.alldeps = [0]
            deps = self.sql.getRec("ctldep", cols=["dep_code",
                "dep_name"], where=[("dep_cono", "=", self.opts["conum"])],
                order="dep_code")
            for dep in deps:
                self.alldeps.append(dep[0])
        chk = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if chk[0] == 1:
            self.cons = False
        else:
            self.cons = True
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        if self.opts["period"][0]:
            self.s_lyr, e_lyr, fin = getPeriods(self.opts["mf"],
                self.opts["conum"], (self.opts["period"][0] - 1))
        self.trans = {}
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "General Ledger Financial Viewer (%s)" % self.__class__.__name__)
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
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Budget","B"),("Last Year","L"))
        fld = [(("T",0,0,0),"ID2",7,"Ending Period","Ending Period (YYYYMM)",
            self.e_per,"Y",self.doRepPer,None,None,None)]
        if self.cons:
            fld.append((("T",0,1,0),("IRB",r1s),0,"Consolidate Companies","",
                "N","Y",self.doCons,None,None,None))
            x = 2
        else:
            self.con = "N"
            x = 1
        if self.gldep == "Y":
            fld.append((("T",0,x,0),"IUI",3,"Department","",
                0,"Y",self.doDept,None,None,None,None,
                "Department Number or 0 for All Departments"))
            x += 1
        fld.extend([
            (("T",0,x,0),("IRB",r2s),0,"Variance","",
                "B","Y",self.doRepVar,None,None,None),
            (("T",0,x+1,0),"IUI",3,"Report Number","",
                1,"N",self.doRepNum,rpt,None,("notzero",)),
            (("T",0,x+2,0),("IRB",r1s),0,"General Report","",
                "N","N",self.doRepGen,None,None,None),
            (("T",0,x+3,0),("IRB",r1s),0,"Ignore Zeros","",
                "Y","N",self.doIgnore,None,None,None)])
        tnd = ((self.doMainEnd,"y"), )
        txt = (self.doMainExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doRepPer(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.end = w
        self.mths = dateDiff(self.opts["period"][1][0],
            mthendDate((self.end * 100) + 1), "months") + 1
        bud = self.sql.getRec("genbud", where=[("glb_cono", "=",
            self.opts["conum"]), ("glb_curdt", "between", self.s_per,
            self.end)])
        if self.cons:
            x = 2
        else:
            x = 1
        if bud:
            self.df.topf[pag][x][5] = "B"
        else:
            self.df.topf[pag][x][5] = "L"

    def doCons(self, frt, pag, r, c, p, i, w):
        self.con = w
        if self.con == "Y" and self.gldep == "N":
            self.dep = 0

    def doDept(self, frt, pag, r, c, p, i, w):
        if w:
            chk = self.sql.getRec("ctldep", cols=["dep_name"],
                where=[("dep_cono", "=", self.opts["conum"]), ("dep_code",
                "=", w)], limit=1)
            if not chk:
                return "Invalid Department Code"
            self.depnam = chk[0]
        self.dep = w

    def doRepVar(self, frt, pag, r, c, p, i, w):
        self.repvar = w

    def doRepNum(self, frt, pag, r, c, p, i, w):
        if self.con == "Y":
            whr = [
                ("glr_cono", "=", 0),
                ("glr_repno", "=", w)]
        else:
            whr = [
                ("glr_cono", "in", (0, self.opts["conum"])),
                ("glr_repno", "=", w)]
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
            else:
                self.df.loadEntry(frt, pag, p+1, data=self.gen)
                return "sk1"
        elif self.con == "Y":
            return "Invalid Report, Not A General Report"

    def doRepGen(self, frt, pag, r, c, p, i, w):
        if self.con == "Y" and w == "N":
            return "Invalid"
        self.gen = w
        return self.getRepDetails()

    def doIgnore(self, frt, pag, r, c, p, i, w):
        self.zero = w

    def doMainEnd(self):
        self.df.closeProcess()
        if self.con == "Y":
            self.doConCoy()
            if self.con == "X":
                self.opts["mf"].closeLoop()
                return
        self.sp = SplashScreen(self.opts["mf"].body,
            "Generating and Formatting the Report\n\nPlease Wait ...")
        self.doGenerateReport()
        self.sp.closeSplash()
        self.doDisplayReport()
        self.opts["mf"].closeLoop()

    def doConCoy(self):
        self.coys = self.sql.getRec("ctlmst", cols=["ctm_cono",
            "ctm_name"], order="ctm_cono")
        coy = {
            "stype": "C",
            "titl": "",
            "head": ("Coy", "Name"),
            "typs": (("UI", 3), ("NA", 30)),
            "data": self.coys,
            "mode": "M",
            "comnd": self.doCoyCmd}
        r1s = (("Yes","Y"),("Include","I"),("Exclude","E"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"All Companies","",
                "Y","N",self.doAllCoy,None,None,None,None),
            (("T",0,1,0),"INA",(30,100),"Companies","",
                "","N",self.doCoySel,coy,None,None,None))
        state = self.df.disableButtonsTags()
        self.cf = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doCoyEnd, "y"),), txit=(self.doCoyExit,))
        self.cf.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doAllCoy(self, frt, pag, r, c, p, i, w):
        self.con = w
        if self.con == "Y":
            return "nd"
        if self.con == "I":
            self.cf.topf[pag][1][8]["titl"] = "Select Companies to Include"
        else:
            self.cf.topf[pag][1][8]["titl"] = "Select Companies to Exclude"

    def doCoyCmd(self, frt, pag, r, c, p, i, w):
        c = ""
        for co in w:
            if int(co[0]) != 0:
                c = c + str(int(co[0])) + ","
        if len(c) > 1:
            c = c[:-1]
        self.cf.loadEntry(frt, pag, p, data=c)

    def doCoySel(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid List of Companies"
        if w[-1:] == ",":
            w = w[:-1]
        self.coy = w.split(",")

    def doCoyEnd(self):
        if self.con == "I":
            self.scon = self.coy
        elif self.con == "E":
            self.scon = []
            for co in self.coys:
                self.scon.append(int(co[0]))
            for co in self.coy:
                del self.scon[self.scon.index(int(co))]
            self.scon.sort()
        self.doCoyClose()

    def doCoyExit(self):
        self.con = "X"
        self.doCoyClose()

    def doCoyClose(self):
        self.cf.closeProcess()

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

    def doGenerateReport(self):
        if self.gen == "Y":
            self.repco = 0
        else:
            self.repco = self.opts["conum"]
        self.grpind = False
        self.xits = False
        self.clearData()
        self.allFields = []
        self.mth_tot = makeArray(self.mths + 2, 10, 1)
        self.mth_str = makeArray(self.mths + 2, 100, 1)
        self.lyr_tot = makeArray(self.mths + 2, 10, 1)
        self.lyr_str = makeArray(self.mths + 2, 100, 1)
        self.bud_tot = makeArray(self.mths + 2, 10, 1)
        self.bud_str = makeArray(self.mths + 2, 100, 1)
        self.var_tot = makeArray(self.mths + 2, 10, 1)
        self.var_str = makeArray(self.mths + 2, 100, 1)
        if self.con == "N":
            self.scon = None
        elif self.con == "Y":
            coy = self.sql.getRec("ctlmst", cols=["ctm_cono"],
                order="ctm_cono")
            if not coy:
                self.scon = None
                return
            self.scon = []
            for c in coy:
                self.scon.append(c[0])
        self.rep_num = 0
        self.rpt_lst = self.sql.getRec("genrpt", where=[("glr_cono",
            "=", self.repco), ("glr_repno", "=", self.rep)], order="glr_seq")
        if self.rpt_lst:
            self.s_type = self.rpt_lst[0][3]
            self.atype = self.s_type
            while not self.xits:
                self.processRecords()

    def processRecords(self):
        if self.grpind:
            self.grpind = False
        else:
            self.nextRepRecord()
            self.storeRepRecord()
            if self.rpt_dic == {}:
                self.xits = True
        if not self.xits:
            if self.s_type == "H":
                self.doHead()
            elif self.s_type == "L":
                self.doLedger()
            elif self.s_type == "G":
                self.doGroup()
            elif self.s_type == "T":
                self.doTotal()
            elif self.s_type == "S":
                self.doStore()
            elif self.s_type == "U":
                self.doUnderline()

    def doHead(self):
        self.printLine()
        self.clearData()

    def doLedger(self):
        accs = self.readGenmst()
        for acc in accs:
            self.dicGenmst(acc)
            self.s_cono = self.gen_dic["glm_cono"]
            self.s_acno = self.gen_dic["glm_acno"]
            self.s_desc = self.gen_dic["glm_desc"]
            self.accumData()
            amt = self.mth[self.mths + 1]
            if self.s_print == "N":
                pass
            elif self.s_print == "+" and amt < 0:
                self.clearData()
                continue
            elif self.s_print == "-" and amt >= 0:
                self.clearData()
                continue
            else:
                if self.trn:
                    self.trans.update(self.trn)
                self.printLine()
            self.accumTotals(self.s_acbal)
            if self.s_store == "Y":
                self.storeBalances()
            self.clearData()

    def doGroup(self):
        self.grpind = True
        while self.rpt_dic and self.rpt_dic["glr_type"] == "G" and \
                        self.rpt_dic["glr_group"] == self.s_group:
            accs = self.readGenmst()
            for acc in accs:
                self.dicGenmst(acc)
                self.s_cono = self.gen_dic["glm_cono"]
                self.s_acno = self.gen_dic["glm_acno"]
                self.accumData()
            self.nextRepRecord()
        amt = self.mth[self.mths + 1]
        if self.s_print == "N":
            pass
        elif self.s_print == "+" and amt < 0:
            self.clearData()
            return
        elif self.s_print == "-" and amt >= 0:
            self.clearData()
            return
        else:
            if self.trn:
                self.trans.update(self.trn)
            self.printLine()
        self.accumTotals(self.s_acbal)
        if self.s_store == "Y":
            self.storeBalances()
        self.clearData()
        self.storeRepRecord()

    def doTotal(self):
        for x in range(0, self.mths + 2):
            self.mth[x] = self.mth_tot[self.s_total][x]
            self.lyr[x] = self.lyr_tot[self.s_total][x]
            self.bud[x] = self.bud_tot[self.s_total][x]
            self.var[x] = self.var_tot[self.s_total][x]
        amt = self.mth[self.mths + 1]
        if self.s_print == "+" and amt < 0:
            self.clearData()
            return
        elif self.s_print == "-" and amt >= 0:
            self.clearData()
            return
        elif self.s_print == "N":
            pass
        else:
            self.printLine()
        if self.s_store == "Y":
            self.storeBalances()
        self.clearData()
        if self.s_clear == "Y":
            for x in range(0, self.s_total+1):
                for y in range(0, self.mths + 2):
                    self.mth_tot[x][y] = 0
                    self.lyr_tot[x][y] = 0
                    self.bud_tot[x][y] = 0
                    self.var_tot[x][y] = 0

    def doStore(self):
        for x in range(0, self.mths + 1):
            if self.mth_str[self.s_snum1][x] == 0:
                self.mth[x] = 0
            else:
                self.mth[x] = round((self.mth_str[self.s_snum1][x] *
                    self.s_strper / 100.0), 2)
                self.mth[self.mths + 1] = float(ASD(self.mth[self.mths + 1]) +
                    ASD(self.mth[x]))
            if self.lyr_str[self.s_snum1][x] == 0:
                self.lyr[x] = 0
            else:
                self.lyr[x] = round((self.lyr_str[self.s_snum1][x] *
                    self.s_strper / 100.0), 2)
                self.lyr[self.mths + 1] = float(ASD(self.lyr[self.mths + 1]) +
                    ASD(self.lyr[x]))
            if self.bud_str[self.s_snum1][x] == 0:
                self.bud[x] = 0
            else:
                self.bud[x] = round((self.bud_str[self.s_snum1][x] *
                    self.s_strper / 100.0), 2)
                self.bud[self.mths + 1] = float(ASD(self.bud[self.mths + 1]) +
                    ASD(self.bud[x]))
        amt = self.mth[self.mths + 1]
        if self.s_print == "+" and amt < 0:
            self.clearData()
            return
        elif self.s_print == "-" and amt >= 0:
            self.clearData()
            return
        elif self.s_print == "N":
            pass
        else:
            self.printLine()
        self.accumTotals(self.s_acbal)
        self.clearData()
        if self.s_clear == "Y":
            for x in range(0, self.mths + 2):
                self.mth_str[self.s_snum1][x] = 0
                self.lyr_str[self.s_snum1][x] = 0
                self.bud_str[self.s_snum1][x] = 0

    def doUnderline(self):
        if self.rpt_dic["glr_uline"] == "B":
            self.s_desc = "Blank"
        elif self.rpt_dic["glr_uline"] == "S":
            self.s_desc = "Single"
        else:
            self.s_desc = "Double"
        self.printLine(inc=0)
        self.clearData()

    def readGenmst(self):
        glfrom = self.rpt_dic["glr_from"]
        glto = self.rpt_dic["glr_to"]
        if self.gldep == "Y":
            if self.dep:
                deps = [self.dep]
            else:
                deps = copyList(self.alldeps)
        if not self.scon:
            if self.gldep == "Y":
                accs = []
                for dep in deps:
                    glf = (dep * (10 ** (7 - self.gldig))) + glfrom
                    if glto:
                        glt = (dep * (10 ** (7 - self.gldig))) + glto
                        acs = self.sql.getRec("genmst",
                            where=[("glm_cono", "=", self.opts["conum"]),
                            ("glm_acno", ">=", glf),
                            ("glm_acno", "<=", glt)],
                            order="glm_acno")
                        if acs:
                            accs.extend(acs)
                    else:
                        acs = self.sql.getRec("genmst",
                            where=[("glm_cono", "=", self.opts["conum"]),
                            ("glm_acno", "=", glf)])
                        if acs:
                            accs.extend(acs)
            else:
                if not glto:
                    accs = self.sql.getRec("genmst",
                        where=[("glm_cono", "=", self.opts["conum"]),
                        ("glm_acno", "=", glfrom)])
                else:
                    accs = self.sql.getRec("genmst",
                        where=[("glm_cono", "=", self.opts["conum"]),
                        ("glm_acno", ">=", glfrom),
                        ("glm_acno", "<=", glto)],
                        order="glm_acno")
                if not accs:
                    accs = []
        else:
            accs = []
            if self.gldep == "Y":
                for dep in deps:
                    glf = (dep * (10 ** (7 - self.gldig))) + glfrom
                    if glto:
                        glt = (dep * (10 ** (7 - self.gldig))) + glto
                        acs = self.sql.getRec("genmst",
                            cols=["glm_acno"], where=[("glm_cono", "in",
                            self.scon), ("glm_acno", ">=", glf),
                            ("glm_acno", "<=", glt)], group="glm_acno",
                            order="glm_acno")
                    else:
                        acs = self.sql.getRec("genmst",
                            cols=["glm_acno"], where=[("glm_cono", "in",
                            self.scon), ("glm_acno", "=", glf)],
                            group="glm_acno")
                    if acs:
                        for ac in acs:
                            accs.append(self.sql.getRec("genmst",
                                where=[("glm_cono", "in", self.scon),
                                ("glm_acno", "=", ac[0])], limit=1))
            else:
                if not glto:
                    acs = self.sql.getRec("genmst",
                        cols=["glm_acno"], where=[("glm_cono", "in",
                        self.scon), ("glm_acno", "=", glfrom)],
                        group="glm_acno")
                else:
                    acs = self.sql.getRec("genmst",
                        cols=["glm_acno"], where=[("glm_cono", "in",
                        self.scon), ("glm_acno", ">=", glfrom),
                        ("glm_acno", "<=", glto)], group="glm_acno",
                        order="glm_acno")
                if acs:
                    for ac in acs:
                        accs.append(self.sql.getRec("genmst",
                            where=[("glm_cono", "in", self.scon),
                            ("glm_acno", "=", ac[0])], limit=1))
        return accs

    def dicGenmst(self, acc):
        self.gen_dic = {}
        num = 0
        for fld in self.sql.genmst_col:
            self.gen_dic[fld] = acc[num]
            num += 1

    def clearData(self):
        self.o_cyr = 0
        self.mth = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.lyr = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.bud = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.var = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.trn = None

    def accumData(self):
        if not self.trn:
            exists = False
            self.trn = {self.s_desc: {}}
        else:
            exists = True
        if self.rpt_dic["glr_obal"] == "Y":
            o_lyr, self.o_cyr = self.getObal()
            self.mth[1] = float(ASD(self.mth[1]) + ASD(self.o_cyr))
            self.mth[self.mths + 1] = float(ASD(self.mth[self.mths + 1]) +
                ASD(self.o_cyr))
            self.lyr[1] = float(ASD(self.lyr[1]) + ASD(o_lyr))
            self.lyr[self.mths + 1] = float(ASD(self.lyr[self.mths + 1]) +
                ASD(o_lyr))
            if self.repvar == "B":
                self.var[1] = float(ASD(self.var[1]) - ASD(self.o_cyr))
                self.var[self.mths + 1] = float(ASD(self.var[self.mths + 1]) -
                    ASD(self.o_cyr))
            else:
                self.var[1] = float(ASD(self.var[1]) - ASD(self.o_cyr) +
                    ASD(o_lyr))
                self.var[self.mths + 1] = float(ASD(self.var[self.mths + 1]) -
                    ASD(self.o_cyr) + ASD(o_lyr))
            if not exists:
                trn = [0, 0, int(self.opts["period"][1][0] / 100),
                    self.opts["period"][1][0], 4, "O/Balance", "B/Fwd",
                    self.o_cyr, 0, "Opening Balance", "", "", 0, 0, 0]
                self.trn[self.s_desc][1] = [trn]
                self.trn[self.s_desc][self.mths + 1] = [trn]
            else:
                a = copyList(self.trn[self.s_desc][1][0])
                a[7] = float(ASD(a[7]) + ASD(self.o_cyr))
                self.trn[self.s_desc][1][0] = a
                b = copyList(self.trn[self.s_desc][self.mths + 1][0])
                b[7] = float(ASD(b[7]) + ASD(self.o_cyr))
                self.trn[self.s_desc][self.mths + 1][0] = b
        elif not exists:
            self.trn[self.s_desc][1][0] = [[]]
            self.trn[self.s_desc][self.mths + 1][0] = [[]]
        curdt = self.s_per
        for mth in range(1, self.mths + 1):
            lyr, cyr, bud, trn = self.getMbal(curdt)
            self.mth[mth] = float(ASD(self.mth[mth]) + ASD(cyr))
            self.mth[self.mths + 1] = float(ASD(self.mth[self.mths + 1]) +
                ASD(cyr))
            self.lyr[mth] = float(ASD(self.lyr[mth]) + ASD(lyr))
            self.lyr[self.mths + 1] = float(ASD(self.lyr[self.mths + 1]) +
                ASD(lyr))
            self.bud[mth] = float(ASD(self.bud[mth]) + ASD(bud))
            self.bud[self.mths + 1] = float(ASD(self.bud[self.mths + 1]) +
                ASD(bud))
            if self.repvar == "B":
                self.var[mth] = float(ASD(self.var[mth]) + ASD(bud) - ASD(cyr))
                self.var[self.mths + 1] = float(ASD(self.var[self.mths + 1]) +
                    ASD(bud) - ASD(cyr))
            else:
                self.var[mth] = float(ASD(self.var[mth]) + ASD(lyr) - ASD(cyr))
                self.var[self.mths + 1] = float(ASD(self.var[self.mths + 1]) +
                    ASD(lyr) - ASD(cyr))
            y = int(curdt / 100)
            m = (curdt % 100) + 1
            if m > 12:
                y += 1
                m -= 12
            curdt = (y * 100) + m
            if mth not in self.trn[self.s_desc]:
                self.trn[self.s_desc][mth] = []
            if trn:
                self.trn[self.s_desc][mth].extend(trn)
                self.trn[self.s_desc][self.mths + 1].extend(trn)

    def getObal(self):
        if not self.scon:
            if not self.opts["period"][0]:
                lyr = None
            else:
                lyr = self.sql.getRec("genbal",
                    cols=["round(sum(glo_cyr), 2)"], where=[("glo_cono", "=",
                    self.s_cono), ("glo_acno", "=", self.s_acno), ("glo_trdt",
                    "=", self.s_lyr.work)], limit=1)[0]
            cyr = self.sql.getRec("genbal",
                cols=["round(sum(glo_cyr), 2)"], where=[("glo_cono", "=",
                self.s_cono), ("glo_acno", "=", self.s_acno), ("glo_trdt",
                "=", self.opts["period"][1][0])], limit=1)[0]
        else:
            if not self.opts["period"][0]:
                lyr = None
            else:
                lyr = self.sql.getRec("genbal",
                    cols=["round(sum(glo_cyr), 2)"], where=[("glo_cono", "in",
                    self.scon), ("glo_acno", "=", self.s_acno), ("glo_trdt",
                    "=", self.s_lyr.work)], limit=1)[0]
            cyr = self.sql.getRec("genbal",
                cols=["round(sum(glo_cyr), 2)"], where=[("glo_cono", "in",
                self.scon), ("glo_acno", "=", self.s_acno), ("glo_trdt",
                "=", self.opts["period"][1][0])], limit=1)[0]
        if not lyr:
            lyr = 0
        else:
            lyr = float(lyr)
        if not cyr:
            cyr = 0
        else:
            cyr = float(cyr)
        return (lyr, cyr)

    def getMbal(self, curdt):
        if not self.scon:
            lyr = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.s_cono), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", (curdt - 100))], limit=1)[0]
            cyr = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "=",
                self.s_cono), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", curdt)], limit=1)[0]
            bud = self.sql.getRec("genbud", cols=["sum(glb_tramt)"],
                where=[("glb_cono", "=", self.s_cono), ("glb_acno", "=",
                self.s_acno), ("glb_curdt", "=", curdt)], limit=1)[0]
            trn = self.sql.getRec("gentrn", where=[("glt_cono", "=",
                self.s_cono), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", curdt)], order="glt_trdt")
        else:
            lyr = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "in",
                self.scon), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", (curdt - 100))], limit=1)[0]
            cyr = self.sql.getRec("gentrn",
                cols=["round(sum(glt_tramt), 2)"], where=[("glt_cono", "in",
                self.scon), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", curdt)], limit=1)[0]
            bud = self.sql.getRec("genbud", cols=["sum(glb_tramt)"],
                where=[("glb_cono", "in", self.scon), ("glb_acno", "=",
                self.s_acno), ("glb_curdt", "=", curdt)], limit=1)[0]
            trn = self.sql.getRec("gentrn", where=[("glt_cono", "in",
                self.scon), ("glt_acno", "=", self.s_acno), ("glt_curdt",
                "=", curdt)], order="glt_trdt")
        if not lyr:
            lyr = 0
        else:
            lyr = float(lyr)
        if not cyr:
            cyr = 0
        else:
            cyr = float(cyr)
        if not bud:
            bud = 0
        else:
            bud = int(bud)
        return (lyr, cyr, bud, trn)

    def printLine(self, inc=1):
        mth = copyList(self.mth)
        lyr = copyList(self.lyr)
        bud = copyList(self.bud)
        var = copyList(self.var)
        if self.s_type != "L":
            self.s_acno = 0
        self.allFields.append([self.s_type, self.s_desc, mth, lyr, bud, var])

    def accumTotals(self, acbal):
        for x in range(1, 10):
            if acbal == "A":
                for y in range(0, self.mths + 2):
                    self.mth_tot[x][y] = \
                        float(ASD(self.mth_tot[x][y]) + ASD(self.mth[y]))
                    self.lyr_tot[x][y] = \
                        float(ASD(self.lyr_tot[x][y]) + ASD(self.lyr[y]))
                    self.bud_tot[x][y] = \
                        float(ASD(self.bud_tot[x][y]) + ASD(self.bud[y]))
                    self.var_tot[x][y] = \
                        float(ASD(self.var_tot[x][y]) + ASD(self.var[y]))
            elif acbal == "S":
                for y in range(0, self.mths + 2):
                    self.mth_tot[x][y] = \
                        float(ASD(self.mth_tot[x][y]) - ASD(self.mth[y]))
                    self.lyr_tot[x][y] = \
                        float(ASD(self.lyr_tot[x][y]) - ASD(self.lyr[y]))
                    self.bud_tot[x][y] = \
                        float(ASD(self.bud_tot[x][y]) - ASD(self.bud[y]))
                    self.var_tot[x][y] = \
                        float(ASD(self.var_tot[x][y]) - ASD(self.var[y]))

    def storeBalances(self):
        if self.s_acstr == "A":
            for x in range(0, self.mths + 2):
                self.mth_str[self.s_snum1][x] = \
                    float(ASD(self.mth_str[self.s_snum1][x]) + \
                        ASD(self.mth[x]))
                self.lyr_str[self.s_snum1][x] = \
                    float(ASD(self.lyr_str[self.s_snum1][x]) + \
                        ASD(self.lyr[x]))
                self.bud_str[self.s_snum1][x] = \
                    float(ASD(self.bud_str[self.s_snum1][x]) + \
                        ASD(self.bud[x]))
                self.var_str[self.s_snum1][x] = \
                    float(ASD(self.var_str[self.s_snum1][x]) + \
                        ASD(self.var[x]))
        elif self.s_acstr == "S":
            for x in range(0, self.mths + 2):
                self.mth_str[self.s_snum1][x] = \
                    float(ASD(self.mth_str[self.s_snum1][x]) - \
                        ASD(self.mth[x]))
                self.lyr_str[self.s_snum1][x] = \
                    float(ASD(self.lyr_str[self.s_snum1][x]) - \
                        ASD(self.lyr[x]))
                self.bud_str[self.s_snum1][x] = \
                    float(ASD(self.bud_str[self.s_snum1][x]) - \
                        ASD(self.bud[x]))
                self.var_str[self.s_snum1][x] = \
                    float(ASD(self.var_str[self.s_snum1][x]) - \
                        ASD(self.var[x]))

    def nextRepRecord(self):
        self.rpt_dic = {}
        if self.rep_num == len(self.rpt_lst) - 1:
            self.xits = True
        else:
            self.rep_num += 1
            num = 0
            for fld in self.sql.genrpt_col:
                self.rpt_dic[fld] = self.rpt_lst[self.rep_num][num]
                num += 1

    def storeRepRecord(self):
        self.s_acno = 0
        for key in self.rpt_dic:
            setattr(self, "s_%s" % key.split("_")[1], self.rpt_dic[key])

    def doDisplayReport(self):
        if not self.allFields:
            return
        head = []
        head.append("%03u %-s" % (self.opts["conum"], self.opts["conam"]))
        head.append("%-s for the period %s to %s" % ("Financials",
            self.opts["period"][1][1], self.opts["period"][2][1]))
        if not self.scon:
            pass
        elif self.con == "Y":
            head.append("Consolidated Companies (All)")
        else:
            con = str(tuple(self.scon)).replace("'", "").replace(" ", "")
            head.append("Consolidated Companies %s" % con)
        labs = (("Description", 30),)
        tags = (
            ("label", ("black", "lightgray")),
            ("actual", ("black", "lightyellow")),
            ("budget", ("black", "lightblue")),
            ("variance", ("black", "lightpink")))
        cols = [[], []]
        m = self.s_per % 100
        for _ in range(0, self.mths):
            cols[0].append((mthnam[m][1], 3))
            m += 1
            if m > 12:
                m = 1
        cols[0].append(("Year-Total", 3))
        for _ in range(0, self.mths + 1):
            cols[1].append(("%9s " % "Actual", ("SI", 11)))
            if self.repvar == "B":
                cols[1].append(("%9s " % "Budget", ("SI", 11)))
            else:
                cols[1].append(("%9s " % "Last-Year", ("SI", 11)))
            cols[1].append(("%9s " % "Variance", ("SI", 11)))
        self.data = []
        self.count = 0
        for fld in self.allFields:
            if fld[0] == "H":
                self.doHeading(fld)
            elif fld[0] in ("C","G","L","P","S","T"):
                self.doValues(fld)
            elif fld[0] == "U":
                self.doDisplayUnderline(fld)
            self.count += 1
        self.opts["mf"].window.withdraw()
        ScrollGrid(**{
            "mf": self.opts["mf"],
            "titl": head,
            "tags": tags,
            "labs": labs,
            "cols": cols,
            "data": self.data,
            "cmds": (("<Double-1>", self.doTrans),)})
        self.opts["mf"].window.deiconify()

    def doHeading(self, line):
        lab = ((line[1], None),)
        col = []
        for _ in range(1, self.mths + 2):
            col.append(("", "label"))
            col.append(("", "label"))
            col.append(("", "label"))
        self.data.append((lab, col))

    def doValues(self, line):
        if self.zero == "Y":
            p = False
            for x in range(0, self.mths + 2):
                if line[2][x] or line[4][x] or line[5][x]:
                    p = True
        else:
            p = True
        if not p:
            return
        if line[0] == "T":
            lab = ((line[1], None),)
        else:
            lab = ((line[1], "label"),)
        col = []
        for x in range(1, self.mths + 2):
            if line[0] == "T":
                col.append((line[2][x], None))
                if self.repvar == "B":
                    col.append((line[4][x], None))
                else:
                    col.append((line[3][x], None))
                col.append((line[5][x], None))
            else:
                col.append((line[2][x], "actual"))
                if self.repvar == "B":
                    col.append((line[4][x], "budget"))
                else:
                    col.append((line[3][x], "budget"))
                col.append((line[5][x], "variance"))
        self.data.append((lab, col))

    def doDisplayUnderline(self, line):
        lab = (("", "label"),)
        if line[1] == "Blank":
            txt = ""
        else:
            return
        col = []
        for _ in range(1, self.mths + 2):
            col.append((txt, "label"))
            col.append((txt, "label"))
            col.append((txt, "label"))
        self.data.append((lab, col))

    def doTrans(self, *args):
        row, col = args[0]
        glc = self.sql.gentrn_col
        des = self.data[row][0][0][0]
        try:
            trans = self.trans[des][int(col / 3) + 1]
            if not trans:
                raise Exception
            if not trans[0]:
                trans.pop(0)
            trans = sorted(trans, key=itemgetter(glc.index("glt_trdt"),))
        except:
            return
        tit = "Transactions for %s" % des
        gtt = ["gentrn"]
        gtc = (
            ("glt_trdt", "", 0, "   Date"),
            ("glt_refno", "", 0, "Reference"),
            ("glt_type", ("XX", gltrtp), 3, "Typ"),
            ("glt_batch", "", 0, "Batch"),
            ("glt_tramt", "", 0, "       Debit"),
            ("glt_tramt", "", 0, "      Credit"),
            ("balance", "SD", 13.2, "     Balance"),
            ("glt_desc", "", 30, "Remarks"))
        data = []
        acctot = 0
        for rec in trans:
            if not rec:
                continue
            acctot = float(ASD(acctot) + ASD(rec[glc.index("glt_tramt")]))
            if rec[glc.index("glt_tramt")] < 0:
                dr = 0
                cr = rec[glc.index("glt_tramt")]
            else:
                dr = rec[glc.index("glt_tramt")]
                cr = 0
            data.append([
                rec[glc.index("glt_trdt")],
                rec[glc.index("glt_refno")],
                rec[glc.index("glt_type")],
                rec[glc.index("glt_batch")],
                dr, cr, acctot,
                rec[glc.index("glt_desc")]])
        rec = SRec(self.opts["mf"], screen=None, title=tit, tables=gtt,
            cols=gtc, where=data, wtype="D", sort=False)

    def doMainExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
