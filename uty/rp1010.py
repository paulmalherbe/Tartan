"""
SYNOPSIS
    Report Printer Front End.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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

import os
from TartanClasses import CCD, FileDialog, RepPrt, TartanDialog, SChoice
from TartanClasses import SplashScreen, Sql
from tartanFunctions import askQuestion, chkAggregate, copyList, showError
from tartanFunctions import showInfo
from tartanWork import dattyp

class rp1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlpwm", "ffield", "ftable",
            "frelat", "rptmst", "rpttab", "rptjon", "rptcol", "rptexc",
            "rptord", "rptvar"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        # ======================================================================
        # Get list of available tables
        # ======================================================================
        exc = (
            "ffield", "frelat", "ftable", "verupd", "ctlpwm", "ctlpwr",
            "ctlpwu", "ctlynd", "genrpc", "genrpt", "rptcol", "rptexc",
            "rptjon", "rptmst", "rptord", "rptstm", "rptstr", "rpttab",
            "rptvar")
        whr = [
            ("ft_seq", "=", 1),
            ("ft_tabl", "not", "in", exc),
            ("ft_tabl", "not", "like", "rpt%"),
            ("ft_tabl", "not", "like", "%sctl")]
        if self.opts["capnm"]:
            syss = self.sql.getRec("ctlpwm", cols=["mpw_sys"],
                where=[("mpw_usr", "=", self.opts["capnm"]), ("mpw_prg",
                "=", "")])
            if syss:
                recs = {"ar": "ass", "bk": "bkm", "bs": "bks", "bc": "bwl",
                    "cr": "crs", "cs": "csh", "dr": "drs", "gl": "gen",
                    "ln": "lon", "ml": "mem", "ms": "ctl", "ps": "pos",
                    "rc": "rca", "rt": "rtl", "sc": "scp", "si": "sls",
                    "sl": "wag", "st": "str", "wg": "wag"}
                for sys in syss:
                    whr.append(("ft_tabl", "not", "like", recs[sys[0]] + "%"))
        self.tables = self.sql.getRec("ftable", cols=["ft_tabl",
            "ft_desc"], where=whr, order="ft_tabl")
        if not self.tables:
            return
        # ======================================================================
        self.expl1 = ("Column","Integer","Decimal","String","Variable",
            "Subquery","Avg()","Count(*)","Max()","Min()","Sum()")
        self.expl2 = ("+","-","*","/","Stop")
        self.expl3 = ("Column","Integer","Decimal","String")
        self.excl1 = ("=","<","<=",">",">=","<>","In","Like","SLike","ELike")
        self.excl2 = ("Column","Integer","Decimal","String","Variable")
        self.excl3 = ("and","or","Stop")
        return True

    def mainProcess(self):
        rpt = {
            "stype": "R",
            "tables": ("rptmst",),
            "cols": (
                ("rpm_rnam", "", 0, "Name"),
                ("rpm_desc", "", 0, "Description", "Y")),
            "order": "rpm_rnam"}
        self.tabs = {
            "stype": "C",
            "titl": "Select the Required Table",
            "head": ("Table", "Description"),
            "data": self.tables}
        self.cols = {
            "stype": "C",
            "titl": "Select the Required Column",
            "head": ("Name",),
            "data": []}
        dtp = {
            "stype": "C",
            "titl": "Select the Required Data Type",
            "head": ("Cd", "Description"),
            "data": dattyp,
            "index": 0}
        self.exps = {
            "stype": "C",
            "titl": "Select Option",
            "head": ("Expression",),
            "data": []}
        jon = {
            "stype": "C",
            "titl": "Select Where Type",
            "head": ("C", "Description"),
            "data": [
                ("I", "Inner Join"),
                ("L", "Left Outer Join"),
                ("R", "Right Outer Join"),
                ("F", "Full Outer Join")]}
        typ = []
        for t in dattyp:
            typ.append(t[0])
        self.typ = tuple(typ)
        tag = (
            ("Tables",None,("T",1,1),("T",0,1)),
            ("Joins",None,("T",1,1),("T",0,1)),
            ("Columns",None,("T",1,1),("T",0,1)),
            ("Variables",None,("T",1,1),("T",0,1)),
            ("Exceptions",None,("T",1,1),("T",0,1)),
            ("Order",None,("T",1,1),("T",0,1)))
        fld = (
            # Details
            (("T",0,0,0),"INA",10,"Name","Report Name",
                "","Y",self.doRepNam,rpt,None,("notblank", "nospaces")),
            (("T",0,1,0),"INA",30,"Description","Report Description",
                "","N",self.doRepDes,None,self.doRepDel,("notblank",)),
            (("T",0,2,0),"INA",50,"Heading-1","Heading One",
                "","N",None,None,None,("notblank",)),
            (("T",0,3,0),"INA",50,"Heading-2","Heading Two",
                "","N",None,None,None,None),
            # Tables
            (("T",1,0,0),"IUI",2,"Table Sequence","",
                "","N",self.doTabSeq,None,None,("between",0,14)),
            (("C",1,0,0),"OUI",2,"Sq","","","N",self.doTable,None,None,None),
            (("C",1,0,1),"INA",6,"Tables","Table Name",
                "","N",self.doRepTab,self.tabs,self.doColDel,("notblank",)),
            (("C",1,0,2),"ONA",30,"Description"),
            # Joins
            (("T",2,0,0),"IUI",2,"Join Sequence","",
                "","N",self.doJoinSeq,None,None,("between",0,14)),
            (("C",2,0,0),"OUI",2,"Sq","","","N",self.doJoin,None,None,None),
            (("C",2,0,1),"IUA",1,"T","Join Type","I","N",self.doJoinTyp,
                jon,self.doColDel,("in",("N","I","L","R","F"))),
            (("C",2,0,2),"INA",6,"Tables","Join Table Name",
                "","N",self.doJoinTab,self.tabs,None,("notblank",)),
            (("C",2,0,3),"INA",(70,100),"Join Columns","",
                "","N",None,None,None,("notblank",)),
            # Columns
            (("T",3,0,0),"IUI",2,"Column Sequence","",
                "","N",self.doColSeq,None,None,("between",0,14)),
            (("C",3,0,0),"OUI",2,"Sq","","","N",None,None,None,None),
            (("C",3,0,1),"IUA",1,"T","Type (C/E)",
                "C","N",self.doType,None,self.doColDel,("in",("C","E"))),
            (("C",3,0,2),"ILA",(15,20),"Label","Column or Expression Label",
                "","N",self.doExpLab,self.cols,None,("notblank",)),
            (("C",3,0,3),"ITv",15,"Expression","Expression Detail",
                "","N",self.doExpDet,None,None,None),
            (("C",3,0,4),"INA",(15,50),"Heading","Column Heading",
                "","N",None,None,None,None),
            (("C",3,0,5),"INA",2,"Tp","Display Type",
                "","N",self.doColTyp,dtp,None,("in",self.typ)),
            (("C",3,0,6),"IUD",6.1,"Size","Display Size",
                "","N",self.doColSiz,None,None,("notzero",)),
            [("C",3,0,7),"IUA",1,"G","Group",
                "N","N",None,None,None,("in",("Y","N"))],
            (("C",3,0,8),"IUA",1,"S","Sub Total",
                "N","N",self.doSubTot,None,None,("in",("Y","N"))),
            (("C",3,0,9),"INA",(15,30),"Narration","Sub-Total Narration",
                "","N",None,None,None,("notblank",)),
            (("C",3,0,10),"IUA",1,"P","Advance Page After Sub-Total",
                "","N",self.doPagAdv,None,None,("in",("Y","N"))),
            (("C",3,0,11),"IUA",1,"G","Grand Total",
                "N","N",None,None,None,("in",("Y","N"))),
            (("C",3,0,12),"IUA",1,"D","Display Column",
                "Y","N",None,None,None,("in",("Y","N"))),
            # Variables
            (("T",4,0,0),"IUI",1,"Variable Sequence","",
                "","N",self.doVarSeq,None,None,("between",0,9)),
            (("C",4,0,0),"OUI",1,"V","","","N",self.doVariable,None,None,None),
            (("C",4,0,1),"INA",30,"Description","Variable Description",
                "","N",self.doVarDesc,None,self.doColDel,("notblank",)),
            (("C",4,0,2),"ONA",2,"Tp","Display Type",
                "","N",None,None,None,("notblank",)),
            (("C",4,0,3),"OUD",6.1,"Size","Display Size",
                "","N",None,None,None,("notzero",)),
            # Exceptions
            (("T",5,0,0),"IUI",2,"Exception Sequence","",
                "","N",self.doExcSeq,None,None,("between",0,14)),
            (("C",5,0,0),"OUI",2,"Sq","","","N",self.doExcept,None,None,None),
            (("C",5,0,1),"ITv",70,"Exception","Exception Detail",
                "","N",self.doExpDet,None,self.doColDel,None),
            # Orders
            (("T",6,0,0),"IUI",2,"Order Sequence","",
                "","N",self.doOrdSeq,None,None,("between",0,14)),
            (("C",6,0,0),"OUI",2,"Sq","","","N",self.doOrder,None,None,None),
            (("C",6,0,1),"ITX",(20,50),"Column","Column Name",
                "","N",self.doRepOrd,self.cols,self.doColDel,("notblank",)),
            (("C",6,0,2),"ONA",30,"Description"),
            (("C",6,0,3),"IUA",1,"D","Ascending or Descending",
                "A","N",None,None,None,("in",("A","D"))))
        row = (0,14,14,14,14,14,14)
        but = (
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),None,0),
            ("Copy",None,self.doCopy,2,None,None,None,0),
            ("Export",None,self.doExport,0,None,None,None,0),
            ("Execute",None,self.doExecute,0,None,None,None,0),
            ("Insert",None,self.doInsert,0,None,None,None,0),
            ("Exit",None,self.doExit,0,None,None,None,0),
            ("Quit",None,self.doQuit,1,None,None,None,0))
        tnd = (
            (self.doTopEnd,"y"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"))
        txt = (
            self.doQuit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit)
        cnd = (
            None,
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            (self.doColEnd,"n"))
        cxt = (
            None,
            self.doColExit,
            self.doColExit,
            self.doColExit,
            self.doColExit,
            self.doColExit,
            self.doColExit)
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt, rows=row, tags=tag, cend=cnd, cxit=cxt)

    def doRepNam(self, frt, pag, r, c, p, i, w):
        self.repnam = w
        rep = self.sql.getRec("rptmst", where=[("rpm_rnam", "=",
            self.repnam)], limit=1)
        if not rep:
            self.newrep = "y"
            self.df.setWidget(self.df.B1, "normal")
        else:
            self.newrep = "n"
            for num, dat in enumerate(rep[1:-1]):
                self.df.loadEntry(frt, pag, p+num+1, data=dat)
            self.doLoadReport(self.repnam)
            self.df.setWidget(self.df.B3, "normal")

    def doRepDes(self, frt, pag, r, c, p, i, w):
        self.df.setWidget(self.df.B1, "disabled")

    def doImport(self):
        self.df.setWidget(self.df.mstFrame, "hide")
        sel = FileDialog(parent=self.opts["mf"].body, title="Import File",
            initd=self.opts["mf"].rcdic["wrkdir"], ftype=[("Report", "*.rpt")])
        nam = sel.askopenfilename()
        self.df.setWidget(self.df.mstFrame, "show")
        err = None
        if nam:
            fle = open(nam, "r")
            for num, line in enumerate(fle):
                dat = line.split("|")
                if not num:
                    if dat[0] != "rptmst":
                        err = "This File Does Not Contain a Valid Format"
                        break
                    chk = self.sql.getRec("rptmst",
                        where=[("rpm_rnam", "=", dat[1])], limit=1)
                    if chk:
                        err = "This Report Name Already Exists"
                        break
                    self.sql.insRec("rptmst", data=dat[1:])
                else:
                    self.sql.insRec(dat[0], data=dat[1:])
        if not err:
            self.opts["mf"].dbm.commitDbase()
        else:
            showError(self.opts["mf"].body, "Invalid Import", err)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doCopy(self):
        self.df.setWidget(self.df.B1, "disabled")
        self.cpynam = None
        tit = ("Copy Report",)
        rpt = {
            "stype": "R",
            "tables": ("rptmst",),
            "cols": (
                ("rpm_rnam", "", 0, "Name"),
                ("rpm_desc", "", 0, "Description", "Y")),
            "order": "rpm_rnam"}
        fld = (
            (("T",0,0,0),"INA",10,"Name","Report Name",
                "","Y",self.doCpyNam,rpt,None,("notblank",)),
            (("T",0,1,0),"ONA",30,"Description"))
        tnd = ((self.doCpyEnd,"n"),)
        txt = (self.doCpyExit,)
        self.cp = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.cp.mstFrame.wait_window()

    def doCpyNam(self, frt, pag, r, c, p, i, w):
        rep = self.sql.getRec("rptmst", where=[("rpm_rnam", "=", w)],
            limit=1)
        if not rep:
            return "Invalid Report"
        self.cpynam = w
        for num, dat in enumerate(rep[1:-1]):
            self.df.loadEntry(frt, pag, p+num+1, data=dat)

    def doCpyEnd(self):
        self.doLoadReport(self.cpynam)
        self.doCpyExit()

    def doCpyExit(self):
        self.cp.closeProcess()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)
        if not self.cpynam:
            self.df.setWidget(self.df.B1, "normal")

    def doExport(self):
        repnam = self.repnam.replace(" ", "_")
        fle = open(os.path.join(self.opts["mf"].rcdic["wrkdir"],
            "%s.rpt" % repnam), "w")
        mst = self.sql.getRec("rptmst", where=[("rpm_rnam", "=",
            repnam)], limit=1)
        mes = "rptmst"
        for dat in mst:
            mes = "%s|%s" % (mes, str(dat))
        fle.write("%s\n" % mes)
        for tab in (
                ("rptcol", "rpc_rnam", "rpc_seq"),
                ("rptexc", "rpx_rnam", "rpx_seq"),
                ("rptjon", "rpj_rnam", "rpj_seq"),
                ("rptord", "rpo_rnam", "rpo_seq"),
                ("rpttab", "rpt_rnam", "rpt_tabl"),
                ("rptvar", "rpv_rnam", "rpv_seq")):
            det = self.sql.getRec(tables=tab[0], where=[(tab[1], "=",
                repnam)], order=tab[2])
            for rec in det:
                mes = tab[0]
                for dat in rec:
                    mes = "%s|%s" % (mes, str(dat))
                fle.write("%s\n" % mes)
        fle.close()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doLoadReport(self, repnam):
        # Tables
        dat = self.sql.getRec("rpttab", where=[("rpt_rnam","=",repnam)])
        if dat:
            for d1, d2 in enumerate(dat):
                p = d1 * self.df.colq[1]
                self.df.loadEntry("C", 1, p, data=d1)
                self.df.loadEntry("C", 1, p+1, data=d2[1])
                dsc = self.doGetTableDesc(d2[1])
                if dsc:
                    self.df.loadEntry("C", 1, p+2, data=dsc)

        # Joins
        dat = self.sql.getRec("rptjon", where=[("rpj_rnam","=",repnam)],
            order="rpj_seq")
        if dat:
            for d in dat:
                r = int(d[1])
                p = r * self.df.colq[2]
                for i in range(0, self.df.colq[2]):
                    self.df.loadEntry("C", 2, p+i, data=d[i+1])

        # Columns
        dat = self.sql.getRec("rptcol", where=[("rpc_rnam","=",repnam)],
            order="rpc_seq")
        if dat:
            for d in dat:
                r = int(d[1])
                p = r * self.df.colq[3]
                for i in range(0, self.df.colq[3]):
                    if i == 4:
                        data = d[7]
                    elif i == 5:
                        data = d[5]
                    elif i == 6:
                        data = d[6]
                    else:
                        data = d[i+1]
                    self.df.loadEntry("C", 3, p+i, data=data)

        # Variables
        dat = self.sql.getRec("rptvar", where=[("rpv_rnam","=",repnam)],
            order="rpv_seq")
        if dat:
            for d in dat:
                r = int(d[1])
                p = r * self.df.colq[4]
                for i in range(0, self.df.colq[4]):
                    self.df.loadEntry("C", 4, p+i, data=d[i+1])

        # Exceptions
        dat = self.sql.getRec("rptexc", where=[("rpx_rnam","=",repnam)],
            order="rpx_seq")
        if dat:
            for d in dat:
                r = int(d[1])
                p = r * self.df.colq[5]
                for i in range(0, self.df.colq[5]):
                    self.df.loadEntry("C", 5, p+i, data=d[i+1])

        # Order
        dat = self.sql.getRec("rptord", where=[("rpo_rnam","=",repnam)],
            order="rpo_seq")
        if dat:
            for d in dat:
                r = int(d[1])
                p = r * self.df.colq[6]
                self.df.loadEntry("C", 6, p+0, data=d[1])
                self.df.loadEntry("C", 6, p+1, data=d[2])
                dsc = self.doGetColDetail(d[2])
                if dsc:
                    self.df.loadEntry("C", 6, p+2, data=dsc[0])
                self.df.loadEntry("C", 6, p+3, data=d[3])

    def doTabSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs

    def doTable(self, frt, pag, r, c, p, i, w):
        if not self.df.c_work[pag][r][i+1]:
            tab = self.df.selectItem(pag, self.tabs)
            if tab is None:
                self.df.clearLine(pag)
                return "xt"
            else:
                err = False
                for t in self.df.c_work[pag]:
                    if not t[1]:
                        break
                    elif t[1] == tab:
                        err = True
                if err:
                    showError(self.opts["mf"].body, "Error",
                        "Table Already Exists")
                    return "xt"
                self.df.loadEntry(frt, pag, p+1, data=tab)
                dsc = self.doGetTableDesc(tab)
                self.df.loadEntry(frt, pag, p+2, data=dsc)

    def doRepTab(self, frt, pag, r, c, p, i, w):
        dsc = self.doGetTableDesc(w)
        if dsc is None:
            return "Invalid Table"
        self.df.loadEntry(frt, pag, p+1, data=dsc)

    def doGetTableDesc(self, table):
        dsc = self.sql.getRec("ftable", cols=["ft_desc"],
            where=[("ft_tabl", "=", table), ("ft_seq", "=", 1)], limit=1)
        if dsc:
            return dsc[0]

    def doJoinSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs
        cd = self.doLoadColData()
        if cd:
            return cd

    def doJoin(self, frt, pag, r, c, p, i, w):
        pass

    def doJoinTyp(self, frt, pag, r, c, p, i, w):
        pass

    def doJoinTab(self, frt, pag, r, c, p, i, w):
        if self.df.c_work[pag][r][i+1]:
            return
        col1 = self.sql.getRec("ffield", cols=["ff_name"],
            where=[("ff_tabl", "=", w)], order="ff_name")
        col2 = self.cols["data"]
        jon = ""
        tab = "Column"
        c1 = "y"
        while tab != "Stop":
            if tab == "Column":
                if c1 == "y":
                    self.cols["data"] = col1
                else:
                    self.cols["data"] = col2
                tab = self.df.selectItem(pag, self.cols)
                if tab is None:
                    jon = ""
                    break
                if not jon:
                    jon = tab
                else:
                    jon = jon + " %s" % tab
                if c1 == "y":
                    c1 = "n"
                    self.exps["data"] = ("=",)
                else:
                    c1 = "y"
                    self.exps["data"] = ("and", "Stop")
            else:
                if tab == "=":
                    self.exps["data"] = ("Column",)
                elif tab == "Column":
                    self.exps["data"] = ("and", "Stop")
                elif tab in ("and", "Stop"):
                    self.exps["data"] = ("Column",)
            tab = self.df.selectItem(pag, self.exps)
            if tab is None:
                jon = ""
                break
            if tab != "Stop" and tab not in ("Column",):
                jon = jon + " %s" % tab
        if jon:
            self.df.loadEntry(frt, pag, p+1, data=jon)
        else:
            if not self.df.c_work[pag][r][i+1]:
                self.df.clearLine(pag)
            return "xt"

    def doJoinDel(self):
        pass

    def doVarSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs
        cd = self.doLoadColData()
        if cd:
            return cd

    def doVariable(self, frt, pag, r, c, p, i, w):
        if not self.df.c_work[pag][r][i+1]:
            col = self.df.selectItem(pag, self.cols)
            if col is None:
                self.df.clearLine(pag)
                return "xt"
            else:
                dsc = self.doGetColDetail(col)
                self.df.loadEntry(frt, pag, p+1, data=dsc[0])
                self.df.loadEntry(frt, pag, p+2, data=dsc[1])
                self.df.loadEntry(frt, pag, p+3, data=dsc[2])

    def doVarDesc(self, frt, pag, r, c, p, i, w):
        return "nd"

    def doGetColDetail(self, col):
        if col.count("format"):
            col = col.split()[1].replace(")","")
        dsc = self.sql.getRec("ffield", cols=["ff_desc", "ff_type",
            "ff_size"], where=[("ff_name", "=", col)], limit=1)
        return dsc

    def doRepDel(self):
        self.doDeleteAllRecords()
        self.opts["mf"].dbm.commitDbase()
        self.df.selPage("Tables")
        self.df.focusField("T", 0, 1)

    def doDeleteAllRecords(self):
        self.sql.delRec("rptmst", where=[("rpm_rnam", "=", self.repnam)])
        self.sql.delRec("rpttab", where=[("rpt_rnam", "=", self.repnam)])
        self.sql.delRec("rptjon", where=[("rpj_rnam", "=", self.repnam)])
        self.sql.delRec("rptcol", where=[("rpc_rnam", "=", self.repnam)])
        self.sql.delRec("rptexc", where=[("rpx_rnam", "=", self.repnam)])
        self.sql.delRec("rptvar", where=[("rpv_rnam", "=", self.repnam)])
        self.sql.delRec("rptord", where=[("rpo_rnam", "=", self.repnam)])

    def doTopEnd(self):
        pag = self.df.pag
        if not pag:
            self.doAllTabs("normal")
            self.doSetNextSeq()
            self.df.focusField("T", 1, 1)
        else:
            self.doAllTabs("disabled")
            mxs = self.df.colq[pag]
            seq = self.df.t_work[pag][0][0]
            self.df.loadEntry("C", pag, seq*mxs, data=seq)
            self.df.focusField("C", pag, ((seq*mxs)+1))

    def doTopExit(self):
        self.doAllTabs("disabled")
        self.doRptAskSave()
        self.df.selPage("Tables")
        self.df.focusField("T", 0, 1)

    def doColSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs
        cd = self.doLoadColData()
        if cd:
            return cd

    def doType(self, frt, pag, r, c, p, i, w):
        self.ctyp = w
        if self.ctyp == "C" and not self.df.c_work[pag][r][i+1]:
            col = self.df.selectItem(pag, self.cols)
            if col is None:
                return ""
            else:
                self.df.loadEntry(frt, pag, p+1, data=col)

    def doExpLab(self, frt, pag, r, c, p, i, w):
        self.lab = w
        if self.ctyp == "C":
            col = self.sql.getRec("ffield",
                cols=["ff_name", "ff_head", "ff_type", "ff_size"],
                where=[("ff_name", "=", self.lab)], limit=1)
            if not col:
                return "Invalid Column"
            for x in range(1, 5):
                self.df.loadEntry(frt, pag, p+x, data=col[x-1])
            return "sk1"
        elif self.ctyp == "E" and not self.df.c_work[pag][r][i+1]:
            self.exp = ""
            tab = ""
            br = "n"
            ex = "n"
            while tab != "Stop":
                if not tab:
                    self.exps["data"] = copyList(self.expl1)
                    tab = self.df.selectItem(pag, self.exps)
                    if tab is None:
                        return ""
                elif tab == "Column":
                    tab = self.df.selectItem(pag, self.cols)
                    if tab is None:
                        return ""
                    self.exp = self.exp + tab
                    if br == "y":
                        self.exp = self.exp + ")"
                        br = "n"
                        if ex == "y":
                            break
                    self.exps["data"] = copyList(self.expl2)
                    tab = self.df.selectItem(pag, self.exps)
                    if tab is None:
                        return ""
                elif tab == "Subquery":
                    self.doConstantInput(3, tab)
                    if self.cons is None:
                        return self.cons
                    self.exp = self.exp + "(%s)" % self.cons
                    break
                elif tab != "Stop":
                    if tab.find("()") != -1:
                        br = "y"
                        self.exp = self.exp + tab.replace(")", "")
                        if tab in ("Avg()", "Max()", "Min()", "Sum()"):
                            ex = "y"
                        else:
                            ex = "n"
                        tab = "Column"
                    elif tab == "Count(*)":
                        self.exp = self.exp + tab
                        break
                    elif tab in ("Integer", "Decimal", "String", "Variable"):
                        self.doConstantInput(3, tab)
                        if self.cons is None:
                            return self.cons
                        if tab == "String":
                            self.exp = self.exp + '"%s"' % self.cons
                        elif tab == "Variable":
                            ok = self.doLoadVarData()
                            if ok != "ok":
                                return ""
                            self.exp = self.exp + "(v)%s" % self.cons
                        else:
                            self.exp = self.exp + "%s" % self.cons
                        self.exps["data"] = copyList(self.expl2)
                        tab = self.df.selectItem(pag, self.exps)
                        if tab is None:
                            return ""
                    else:
                        self.exp = self.exp + tab
                        tab = ""
            self.df.loadEntry(frt, pag, p+1, data=self.exp)
        elif self.ctyp == "E":
            self.exp = self.df.c_work[pag][r][i+1]

    def doExpDet(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Blank Exception"

    def doColTyp(self, frt, pag, r, c, p, i, w):
        self.coltyp = w

    def doColSiz(self, frt, pag, r, c, p, i, w):
        skp = "N"
        if self.ctyp == "E":
            for exp in ("Avg(","Max(","Min(","Sum(","Count(*)"):
                if self.exp.find(exp) != -1:
                    skp = "Y"
                    break
        if skp == "Y":
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doConstantInput(self, pag, tab):
        if tab == "Variable":
            v = []
            for x in range(0, len(self.df.c_work[4])):
                if not self.df.c_work[4][x][1]:
                    break
                v.append([x, self.df.c_work[4][x][1]])
            tit = "Select Variable"
            hd = ("V", "Description")
            state = self.df.disableButtonsTags()
            sc = SChoice(self.opts["mf"], titl=tit, head=hd, data=v)
            self.df.enableButtonsTags(state=state)
            if sc.selection in (None, []):
                self.cons = ""
            else:
                self.cons = sc.selection[0]
        else:
            tit = ("Enter %s" % tab,)
            if tab == "Integer":
                typ = "ISI"
                siz = 10
                chk = ("efld",)
            elif tab == "Decimal":
                typ = "ISD"
                siz = 13.2
                chk = ("efld",)
            elif tab == "String":
                typ = "INA"
                siz = 30
                chk = ("efld",)
            elif tab == "Subquery":
                typ = "ITv"
                siz = 50
                chk = None
            self.cons = ""
            fld = ((("T",0,0,0), typ, siz, "%s" % tab, tab,
                "", "N", None, None, None, chk),)
            tnd = ((self.doConEnd,"n"),)
            txt = (self.doConExit,)
            self.cf = TartanDialog(self.opts["mf"], tops=True,
                title=tit, eflds=fld, tend=tnd, txit=txt)
            self.cf.mstFrame.wait_window()

    def doConEnd(self):
        self.cons = self.cf.t_work[0][0][0]
        self.cf.closeProcess()

    def doConExit(self):
        self.cons = None
        self.cf.closeProcess()

    def doExcSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs
        cd = self.doLoadColData()
        if cd:
            return cd

    def doExcept(self, frt, pag, r, c, p, i, w):
        if self.df.c_work[pag][r][i+1]:
            return
        exc = ""
        tab = "Column"
        c1 = "y"
        while tab != "Stop":
            if tab == "Column":
                tab = self.df.selectItem(pag, self.cols)
                if tab is None:
                    exc = ""
                    break
                # Column type for the 'In' clause
                ctp = self.sql.getRec("ffield", cols=["ff_type"],
                    where=[("ff_name", "=", tab)], limit=1)[0]
                if not exc:
                    exc = tab
                else:
                    exc = exc + " %s" % tab
                if c1 == "y":
                    c1 = "n"
                    self.exps["data"] = copyList(self.excl1)
                else:
                    c1 = "y"
                    self.exps["data"] = copyList(self.excl3)
            elif tab in ("Integer", "Decimal", "String", "Variable"):
                c1 = "y"
                self.doConstantInput(4, tab)
                if self.cons is None:
                    return self.cons
                else:
                    if tab == "String":
                        if exc[-2:] == "In":
                            con = tuple(self.cons.split(","))
                            if ctp[1].upper() == "A":
                                exc = exc + " %s" % str(con)
                            else:
                                exc = exc + " %s" % str(con).replace("'", "")
                        elif self.cons in ('""', "''"):
                            exc = exc + ' ""'
                        elif exc[-4:] == "Like":
                            exc = exc + ' "%s%s%s"' % ("%", self.cons, "%")
                        elif exc[-5:] == "SLike":
                            exc = exc + ' "%s%s"' % (self.cons, "%")
                        elif exc[-5:] == "ELike":
                            exc = exc + ' "%s%s"' % ("%", self.cons)
                        else:
                            exc = exc + ' "%s"' % self.cons
                    elif tab == "Variable":
                        ok = self.doLoadVarData()
                        if ok != "ok":
                            return ""
                        exc = exc + " (v)%s" % self.cons
                    else:
                        exc = exc + " %s" % self.cons
                    self.exps["data"] = copyList(self.excl3)
            else:
                if tab in self.excl1:
                    self.exps["data"] = list(copyList(self.excl2))
                    if ctp[1].upper() == "A":
                        self.exps["data"].remove("Integer")
                        self.exps["data"].remove("Decimal")
                    elif ctp[1].upper() in ("1", "2", "D", "I"):
                        self.exps["data"].remove("String")
                        if ctp[1].upper() == "D":
                            self.exps["data"].remove("Integer")
                        else:
                            self.exps["data"].remove("Decimal")
                elif tab in self.excl2:
                    self.exps["data"] = copyList(self.excl3)
                elif tab in self.excl3:
                    tab = "Column"
            if len(exc) > 100:
                showError(self.opts["mf"].body, "Exception Error",
                    "Exception Statement Exceeds 100 Characters")
                tab = None
            if tab == "In":
                tab = "String"
            elif tab in ("Like", "SLike", "ELike"):
                self.exps["data"].remove("Column")
                tab = self.df.selectItem(pag, self.exps)
            elif tab and tab != "Column":
                tab = self.df.selectItem(pag, self.exps)
            if tab is None:
                exc = ""
                break
            if tab != "Stop" and tab not in self.excl2:
                exc = exc + " %s" % tab
        if exc:
            self.df.loadEntry(frt, pag, p+1, data=exc)
        else:
            if not self.df.c_work[pag][r][i+1]:
                self.df.clearLine(pag)
            return "xt"

    def doOrdSeq(self, frt, pag, r, c, p, i, w):
        cs = self.doChkSeq(pag, w)
        if cs:
            return cs
        cd = self.doLoadColData()
        if cd:
            return cd

    def doOrder(self, frt, pag, r, c, p, i, w):
        if not self.df.c_work[pag][r][i+1]:
            col = self.df.selectItem(pag, self.cols)
            if col is None:
                self.df.clearLine(pag)
                return "xt"
            else:
                self.df.loadEntry(frt, pag, p+1, data=col)
                dsc = self.doGetColDetail(col)
                self.df.loadEntry(frt, pag, p+2, data=dsc[0])

    def doRepOrd(self, frt, pag, r, c, p, i, w):
        dsc = self.doGetColDetail(w)
        if not dsc:
            return "Invalid Column"
        self.df.loadEntry(frt, pag, p+1, data=dsc[0])

    def doChkSeq(self, pag, seq):
        if seq > 0 and not self.df.c_work[pag][seq-1][1]:
            return "Invalid Sequence"
        if not self.df.c_work[pag][seq][1]:
            self.newrow = "Y"
        else:
            self.newrow = "N"

    def doLoadColData(self):
        tab = []
        for r in self.df.c_work[1]:
            if not r[1]:
                break
            tab.append(r[1])
        for r in self.df.c_work[2]:
            if not r[2]:
                break
            tab.append(r[2])
        if not tab:
            return "No Tables Selected"
        dat = tuple(tab)
        data = self.sql.getRec("ffield", cols=["ff_name", "ff_desc"],
            where=[("ff_tabl", "in", dat)], order="ff_name")
        if not data:
            return "No Columns to Select"
        self.cols["data"] = data

    def doLoadVarData(self):
        data = []
        for col in self.df.c_work[4]:
            if not col[1]:
                break
            data.append((col[0], col[1]))
        if not data:
            return "No Variables to Select"
        self.exps["data"] = data
        return "ok"

    def doSubTot(self, frt, pag, r, c, p, i, w):
        self.stot = w
        if self.stot == "N":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="N")
            if self.coltyp[1] not in ("I", "D"):
                self.df.loadEntry(frt, pag, p+3, data="N")
                return "sk3"
            else:
                return "sk2"

    def doPagAdv(self, frt, pag, r, c, p, i, w):
        if self.stot == "Y":
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doColDel(self):
        pag = self.df.pag
        tot = self.df.rows[pag] - 1
        mxs = self.df.colq[pag]
        row = int(self.df.pos / mxs)
        seq = self.df.t_work[pag][0][0]
        for row in range(seq, tot):
            if not self.df.c_work[pag][row+1][1]:
                self.df.clearLine(self.df.pag, row=tot)
                break
            pos = row * mxs
            self.df.loadEntry("C", pag, pos, data=row)
            for col in range(1, mxs):
                data = self.df.c_work[pag][row+1][col]
                self.df.loadEntry("C", pag, pos+col, data=data)
        self.df.clearLine(self.df.pag, row=row)
        self.doAllTabs("normal")
        self.doSetNextSeq()
        self.df.focusField("T", pag, 1)
        return "nf"

    def doColEnd(self):
        self.doAllTabs("normal")
        self.doSetNextSeq()
        self.df.last[self.df.pag] = [0, 0]
        self.df.focusField("T", self.df.pag, 1)

    def doColExit(self):
        self.doAllTabs("normal")
        if not self.df.idx:
            if self.newrow == "Y":
                self.df.clearLine(self.df.pag)
            self.df.last[self.df.pag] = [0, 0]
            self.df.focusField("T", self.df.pag, 1)

    def doSetNextSeq(self):
        for pag in range(1, (len(self.df.tags) + 1)):
            for seq, dat in enumerate(self.df.c_work[pag]):
                if not dat[1]:
                    break
            self.df.loadEntry("T", pag, 0, data=seq)

    def doRptAskSave(self):
        answer = askQuestion(self.opts["mf"].body, "Save?",
            "Would you like to Save this Report Layout (%s)?" % self.repnam)
        if answer == "yes":
            self.doSave()

    def doAllTabs(self, state="normal"):
        for num, tag in enumerate(self.df.tags):
            if state == "normal":
                self.df.enableTag(num)
            else:
                self.df.disableTag(num)
        for num, but in enumerate(self.df.butt):
            if num in (0, 1):
                continue
            if state == "normal":
                but[3] = 1
            else:
                but[3] = 0
            wid = getattr(self.df, "B%s" % num)
            self.df.setWidget(wid, state)

    def doSave(self):
        self.doDeleteAllRecords()
        val = tuple(self.df.t_work[0][0])
        self.sql.insRec("rptmst", data=val)

        for v in self.df.c_work[1]:
            if not v[1]:
                break
            val = (self.repnam, v[1])
            self.sql.insRec("rpttab", data=val)

        for v in self.df.c_work[2]:
            if not v[1]:
                break
            val = (self.repnam, v[0], v[1], v[2], v[3])
            self.sql.insRec("rptjon", data=val)

        for v in self.df.c_work[3]:
            if not v[1]:
                break
            val = [self.repnam]
            val.extend(v[0:4])
            val.extend(v[5:7])
            val.append(v[4])
            val.extend(v[7:13])
            val = tuple(val)
            self.sql.insRec("rptcol", data=val)

        for v in self.df.c_work[4]:
            if not v[1]:
                break
            val = (self.repnam, v[0], v[1], v[2], v[3])
            self.sql.insRec("rptvar", data=val)

        for v in self.df.c_work[5]:
            if not v[1]:
                break
            val = (self.repnam, v[0], v[1])
            self.sql.insRec("rptexc", data=val)

        for v in self.df.c_work[6]:
            if not v[1]:
                break
            val = (self.repnam, v[0], v[1], v[3])
            self.sql.insRec("rptord", data=val)
        self.opts["mf"].dbm.commitDbase()
        showInfo(self.opts["mf"].body, "Save", "Report Successfully Saved")

    def doExecute(self):
        self.opts["mf"].updateStatus("")
        self.doRptAskSave()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.doVariables()
        if not self.xits:
            err = self.doRest()
            if err:
                showError(self.opts["mf"].body,
                    "Report %s Error" % self.repnam, err)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField("T", self.df.pag, 1)

    def doInsert(self):
        if self.df.frt != "T" or not self.df.pag or self.df.col != 1:
            return
        tit = ("Insert Column",)
        fld = ((("T",0,0,0), "IUI", 2, "Before Sq","Insert Before Sq",
            "", "N",self.doInsSeq,None,None,("efld",)),)
        tnd = ((self.doInsEnd,"n"),)
        txt = (self.doInsExit,)
        self.ic = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.ic.mstFrame.wait_window()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doInsSeq(self, frt, pag, r, c, p, i, w):
        self.insseq = w

    def doInsEnd(self):
        self.ic.closeProcess()
        wrk = []
        for num, col in enumerate(self.df.c_work[self.df.pag]):
            if not col[1]:
                break
            if num == self.insseq:
                if self.df.pag == 1:
                    wrk.append([num,"",""])
                elif self.df.pag == 2:
                    wrk.append([num,"","",""])
                elif self.df.pag == 3:
                    wrk.append([num,"C","","","","",0,"","","","","",""])
                elif self.df.pag == 4:
                    wrk.append([num,"","",0])
                elif self.df.pag == 5:
                    wrk.append([num,""])
                elif self.df.pag == 6:
                    wrk.append([num,"","",""])
            wrk.append(copyList(col))
        self.df.clearFrame("C", self.df.pag)
        for num, col in enumerate(wrk):
            col[0] = num
            for n, d in enumerate(col):
                self.df.loadEntry("C", self.df.pag,
                    ((num * self.df.colq[self.df.pag]) + n), data=d)
        self.df.loadEntry("T", self.df.pag, 0, data=self.insseq)
        self.df.focusField("T", self.df.pag, 1)

    def doInsExit(self):
        self.ic.closeProcess()

    def doVariables(self):
        # VARIABLES
        self.var_det = []
        for x in range(0, len(self.df.c_work[4])):
            if not self.df.c_work[4][x][1]:
                break
            self.var_det.append([self.df.c_work[4][x][1],
                self.df.c_work[4][x][2], self.df.c_work[4][x][3], ""])
        tit = ("Report Variables",)
        fld = []
        for x in range(0, len(self.var_det)):
            var = self.var_det[x]
            tex = var[0] + " " * (30 - len(var[0]))
            fld.append((("T",0,x,0),"I%s" % var[1],var[2],"%s" % tex,
                "%s" % var[0],"","N",None,None,None,("efld",)))
        tnd = ((self.doVarEnd,"n"),)
        txt = (self.doVarExit,)
        self.vf = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))
        self.vf.mstFrame.wait_window()

    def doVarEnd(self):
        for x in range(0, len(self.var_det)):
            self.var_det[x][3] = self.vf.t_work[0][0][x]
        self.xits = None
        self.doVarClose()

    def doVarExit(self):
        self.xits = "y"
        self.doVarClose()

    def doVarClose(self):
        self.vf.closeProcess()

    def doRest(self):
        # TABLES
        tabs = []
        for x in range(0, len(self.df.c_work[1])):
            if not self.df.c_work[1][x][1]:
                break
            tabs.append(self.df.c_work[1][x][1])
        if not tabs:
            return
        # JOINS
        jons = []
        for x in range(0, len(self.df.c_work[2])):
            if not self.df.c_work[2][x][1]:
                break
            # Type, Table Name and Columns
            jons.append([self.df.c_work[2][x][1],
                self.df.c_work[2][x][2], self.df.c_work[2][x][3]])
        # COLUMNS, EXPRESSIONS, GROUPS, STOTS and GTOTS
        cols = []
        temp = []
        grps = []
        stot = []
        gtot = []
        sums = []
        aggr = False
        for col in self.df.c_work[3]:
            if not col[1]:
                break
            if col[1] == "C":
                c = col[3].strip()
                cols.append([c, col[5], col[6], col[4], col[12]])
                temp.append(c)
                if col[7].upper() == "Y":
                    grps.append(c)
                if col[8].upper() == "Y":
                    stot.append([c, col[9], col[10]])
                if col[11].upper() == "Y":
                    gtot.append(c)
            elif col[1] == "E":
                c = col[3].rstrip()
                v = c.split("(v)")
                if not chkAggregate(c):
                    self.doLoadColData()
                    for chk in self.cols["data"]:
                        if chk[0] in c:
                            temp.append(chk[0])
                else:
                    aggr = True
                for x in range(1, len(v)):
                    n = int(v[x][:1])
                    d = self.var_det[n][3]
                    if type(d) == str:
                        d = '"%s"' % d
                    c = c.replace("(v)%s" % str(n), str(d))
                if c[:4].lower() == "sum(":
                    c = c.replace(c[:4], "Round(Sum(")
                    s = str(col[6]).split(".")
                    if len(s) == 1:
                        d = 0
                    else:
                        d = int(s[1])
                    c = c.replace(")", "), %s)" % d)
                if c[:6].lower() == "round(":
                    s = c.lower()
                    s = s.split("round(sum(")
                    s = s[1].split(")")
                    sums.append(s[0])
                c = c + " as %s" % col[2].strip()
                cols.append([c, col[5], col[6], col[4], col[12]])
                if col[8].upper() == "Y":
                    stot.append([col[2].strip(), col[9], col[10]])
                if col[11].upper() == "Y":
                    gtot.append(col[2].strip())
        if stot and not gtot:
            return "You Cannot Have Sub Totals Without a Grand Total"
        if not cols:
            if len(tabs) > 1:
                return "You Have Selected More than One Table But NO COLUMNS!"
            for tab in tabs:
                t = self.sql.getRec("ffield", cols=["ff_name",
                    "ff_type", "ff_size", "ff_head"], where=[("ff_tabl", "=",
                    tab)], order="ff_seq")
                for c in t:
                    c.append("Y")
                    cols.extend([c])
        if sums:
            chk = []
            for sm in sums:
                s = sm.split("_")
                if not chk:
                    chk.append(s[0])
                elif s[0] not in chk:
                    showError(self.opts["mf"].body, "Sum Error",
                        "You are Aggregating More than One Table!\n\n"\
                        "The Results Will Most Probably be Incorrect!")
        if aggr or grps:
            for col in temp:
                if col not in grps:
                    grps.append(col)
            temp = ""
            for grp in grps:
                if not temp:
                    temp = grp
                else:
                    temp = "%s, %s" % (temp, grp)
            grps = temp
        # WHERE
        excs = ""
        # Check table relationships
        rels = []
        for t1 in tabs:
            for t2 in tabs:
                if t2 == t1:
                    continue
                recs = self.sql.getRec("frelat", cols=["rel_col1", "rel_col2"],
                    where=[("rel_tab1", "=", t1), ("rel_tab2", "=", t2)])
                if not recs:
                    recs = self.sql.getRec("frelat", cols=["rel_col1",
                        "rel_col2"], where=[("rel_tab1", "=", t2),
                        ("rel_tab2", "=", t1)])
                for rel in recs:
                    if not rels.count(rel):
                        rels.append(rel)
        if len(tabs) > 1 and not rels:
            showError(self.opts["mf"].body, "Relationship Error",
                "Some Relationships Between Tables %s are Missing" % tabs)
            return "error"
        for rel in rels:
            if not excs:
                excs = "%s = %s" % (rel[0], rel[1])
            else:
                excs = "%s and %s = %s" % (excs, rel[0], rel[1])
        heds = ""
        heads = [self.df.t_work[0][0][2]]
        if self.df.t_work[0][0][3]:
            heads.append(self.df.t_work[0][0][3])
        for exc in self.df.c_work[5]:
            if not exc[1]:
                break
            c = exc[1]
            if self.opts["mf"].dbm.dbase == "PgSQL":
                for ccc in ("si1_docno", "si2_docno"):
                    if c.count("drt_ref1 = %s" % ccc) or \
                            c.count("%s = drt_ref1" % ccc):
                        c = c.replace(ccc, "format('%s', %s)" % ("%9s", ccc))
                    elif c.count("stt_ref1 = %s" % ccc) or \
                            c.count("%s = stt_ref1" % ccc):
                        c = c.replace(ccc, "format('%s', %s)" % ("%9s", ccc))
            v = c.split("(v)")
            for x in range(1, len(v)):
                n = int(v[x][:1])
                d = self.var_det[n][3]
                if type(d) == str:
                    e = c.split()
                    if e[1] == "Like":
                        d = '"%s%s%s"' % ("%", d, "%")
                    elif e[1] == "SLike":
                        d = '"%s%s"' % ("%", d)
                    elif e[1] == "ELike":
                        d = '"%s%s"' % (d, "%")
                    else:
                        d = '"%s"' % d
                c = c.replace("(v)%s" % n, "%s" % d)
                for y in self.excl1:
                    if v[x-1].find(y) != -1:
                        break
                for z in (" and ", " or "):
                    if v[x].find(z) != -1:
                        break
                h = self.var_det[n][0] + y + CCD(self.var_det[n][3],
                    self.var_det[n][1], self.var_det[n][2]).disp
                h = h.replace("=", ": ")
                if not heds:
                    heds = h
                else:
                    heds = heds + " " + h
            if not excs:
                excs = c
            else:
                excs = excs + " and " + c
        if not excs:
            excs = None
        else:
            excs = excs.replace('"', "'")
        heads.append(heds)
        # ORDER
        order = ""
        for odr in self.df.c_work[6]:
            if not odr[1]:
                break
            if odr[3] == "A":
                order = order + odr[1] + " asc,"
            else:
                order = order + odr[1] + " desc,"
        if not order:
            order = None
        else:
            order = order[:-1]
        # SELECT DATA
        sel = "Select"
        col = ""
        for c in cols:
            if not col:
                col = c[0]
            else:
                col = col + ", " + c[0]
        sel = sel + " " + col + " from"
        tab = ""
        for t in tabs:
            if not tab:
                tab = t
            else:
                tab = tab + ", " + t
        sel = sel + " " + tab
        if jons:
            for j in jons:
                if j[0] == "I":
                    sel = sel + " inner join "
                elif j[0] == "L":
                    sel = sel + " left outer join "
                elif j[0] == "R":
                    sel = sel + " right outer join "
                elif j[0] == "F":
                    sel = sel + "full outer join "
                sel = sel + j[1] + " on " + j[2]
        if excs:
            sel = sel + " where " + excs
        if grps:
            sel = sel + " group by " + grps
        if order:
            sel = sel + " order by " + order
        sp = SplashScreen(self.opts["mf"].body,
            "Generating the Report\n\n         Please Wait....")
        data = self.sql.sqlRec(sel)
        sp.closeSplash()
        if data:
            # PRINT REPORT
            state = self.df.disableButtonsTags()
            self.rpt = RepPrt(self.opts["mf"], name=self.repnam, tables=data,
                ttype="D", heads=heads, cols=cols, stots=stot, gtots=gtot,
                repprt=self.vf.repprt, repeml=self.vf.repeml)
            self.df.enableButtonsTags(state=state)

    def doExit(self):
        self.doAllTabs("disabled")
        self.doRptAskSave()
        self.df.selPage("Tables")
        self.df.focusField("T", 0, 1)

    def doQuit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
