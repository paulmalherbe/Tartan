"""
SYNOPSIS
    General Ledger Report Generator Record Maintenance.
    This program is used to create records used by the general ledger
    financial reports program i.e. gl3050. With these records you can
    design your own layouts of this report.

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

import os
from TartanClasses import FileDialog, GetCtl, RepPrt, SelectChoice, Sql
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, askQuestion, showError

class gl1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.selcoy = self.opts["conum"]
                self.newrep = True
                self.repno = 1
                self.gtyp = "X"
                self.doGenRpt()
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        self.dep = ctlsys["sys_gl_dep"]
        self.dig = ctlsys["sys_gl_dig"]
        self.sql = Sql(self.opts["mf"].dbm, ["genmst", "genrpt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.genrpt_fd = self.sql.genrpt_dic
        self.genrpt_cl = self.sql.genrpt_col
        self.pags = ["","Q","H","L","G","S","T","U","C","P"]
        self.head = ["glr_desc", "glr_high", "glr_ffeed", "glr_ignore"]
        self.ledger = [
            "glr_from", "glr_to", "glr_high", "glr_obal", "glr_accum",
            "glr_print", "glr_norm", "glr_acbal", "glr_ignore",
            "glr_store", "glr_snum1", "glr_acstr"]
        self.group = [
            "glr_group", "glr_desc", "glr_from", "glr_to", "glr_high",
            "glr_obal", "glr_accum", "glr_print", "glr_norm", "glr_acbal",
            "glr_ignore", "glr_store", "glr_snum1", "glr_acstr", "glr_label"]
        self.store = [
            "glr_desc", "glr_high", "glr_print", "glr_norm", "glr_acbal",
            "glr_clear", "glr_snum1", "glr_strper"]
        self.total = [
            "glr_desc", "glr_high", "glr_total", "glr_print", "glr_norm",
            "glr_clear", "glr_store", "glr_snum1", "glr_acstr", "glr_label"]
        self.uline = ["glr_high", "glr_uline"]
        self.calc = [
            "glr_desc", "glr_high", "glr_cbase", "glr_ctype", "glr_snum2",
            "glr_camnt", "glr_snum3"]
        self.percent = ["glr_desc", "glr_high", "glr_snum1", "glr_snum2"]
        return True

    def mainProcess(self):
        data = [
            ("H","Heading"),
            ("L","Ledger Accounts"),
            ("G","Group of Accounts"),
            ("S","Stored Amount"),
            ("T","Total"),
            ("U","Underline"),
            ("C","Calculation"),
            ("P","Percentage")]
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("T", "Description"),
            "data": data}
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Description", "Y")),
            "order": "ctm_cono"}
        glr = {
            "stype": "R",
            "tables": ("genrpt",),
            "cols": (
                ("glr_cono", "", 0, "Coy"),
                ("glr_repno", "", 0, "Rep"),
                ("glr_type", "", 0, "T"),
                ("glr_desc", "", 0, "Description", "Y")),
            "where": [("glr_seq", "=", 0)],
            "whera": (("T", "glr_cono", 0, 0),),
            "order": "glr_cono, glr_repno",
            "index": 1}
        gls = {
            "stype": "R",
            "tables": ("genrpt",),
            "cols": (
                ("glr_seq", "", 0, "Seq"),
                ("glr_type", "", 0, "T"),
                ("glr_group", "", 0, "Grp"),
                ("glr_from", "", 0, "From-Ac"),
                ("glr_to", "", 0, "  To-Ac"),
                ("glr_desc", "", 0, "Description", "Y")),
            "where": [("glr_seq", ">", 0)],
            "whera": (("T", "glr_cono", 0, 0),("T", "glr_repno", 1, 0))}
        self.glm = {
            "stype": "C",
            "titl": "Account Numbers",
            "head": ("Number", "Description"),
            "data": []}
        ryn = (("Yes","Y"),("No","N"))
        rys = (("Yes","Y"),("No","N"),("Debit","+"),("Credit","-"))
        rns = (("Positive","P"),("Negative","N"))
        ras = (("Add","A"),("Subtract","S"))
        rat = (("Add","A"),("Subtract","S"),("Ignore","I"))
        rcb = (("Percentage","P"),("Amount","A"),("Store","S"))
        rct = (("Plus","+"),("Minus","-"),("Multiply","*"),("Divide","/"))
        rsd = (("Single","S"),("Double","D"),("Blank","B"))
        pts = (
            "Accumulate Month Values",
            "Add, Subtract or Ignore",
            "Calculation Base",
            "Calculation Type",
            "Clear Stored Value",
            "Clear Total",
            "Highlight",
            "Ignore Account Type",
            "Include Opening Balance",
            "Normal Sign",
            "Percentage of Stored Value",
            "Print Values",
            "Store Amount",
            "Add or Subtract")
        tag = [
            ("Sequence",None,None,None,False),
            ("Heading",None,None,None,False),
            ("Ledger",None,None,None,False),
            ("Group",None,None,None,False),
            ("Stored",None,None,None,False),
            ("Total",None,None,None,False),
            ("Uline",None,None,None,False),
            ("Calc",None,None,None,False),
            ("Percent",None,None,None,False)]
        fld = (
            (("T",0,0,0),"IUI",3,"Company","Company Number, 0=All",
                self.opts["conum"],"Y",self.doCoyNum,coy,None,
                ("in", (self.opts["conum"], 0))),
            (("T",0,0,0),"IUI",3,"Report","Report Number",
                "","N",self.doRepNum,glr,None,("notzero",)),
            (("T",0,0,0),"IUA",1,"Type","Report Type (B, P, O)",
                "P","N",self.doRepTyp,None,self.doDelRpt,
                ("in", ("O","P","B"))),
            (("T",0,0,0),"INA",30,"Heading","Report Heading",
                "","N",None,None,None,("notblank",)),
            (("T",1,0,0),"IUD",7.2,"Seq-Num","Sequence Number",
                "","N",self.doSeqNum,gls,None,("efld",)),
            (("T",1,1,0),"IUA",1,"Sequence Type","",
                "","N",self.doSeqType,typ,self.doDelSeq,
                ("in",("H","L","G","T","S","U","P","C"))),
            (("T",2,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",2,1,0),("IRB",ryn),0,pts[6],"",
                "Y","N",None,None,None,None),
            (("T",2,2,0),("IRB",ryn),0,"New Page","New Page (Y/N)",
                "N","N",None,None,None,None),
            (("T",2,3,0),("IRB",ryn),0,pts[7],"",
                "N","N",None,None,None,None),
            (("T",3,0,0),"IUI",7,"From Account","From Account Number",
                "","N",self.doAcno,self.glm,None,("notzero",)),
            (("T",3,1,0),"IUI",7,"To Account","To Account Number",
                "","N",self.doAcno,self.glm,None,("efld",)),
            (("T",3,2,0),("IRB",ryn),0,pts[6],"",
                "N","N",None,None,None,None),
            (("T",3,3,0),("IRB",ryn),0,pts[8],"",
                "Y","N",None,None,None,None),
            (("T",3,4,0),("IRB",ryn),0,pts[0],"",
                "N","N",None,None,None,None),
            (("T",3,5,0),("IRB",rys),0,pts[11],"",
                "Y","N",None,None,None,None),
            (("T",3,6,0),("IRB",rns),0,pts[9],"",
                "P","N",None,None,None,None),
            (("T",3,7,0),("IRB",rat),0,pts[1],"",
                "A","N",None,None,None,None),
            (("T",3,8,0),("IRB",ryn),0,pts[7],"",
                "N","N",None,None,None,None),
            (("T",3,9,0),("IRB",ryn),0,pts[12],"",
                "N","N",self.doStore,None,None,None),
            (("T",3,10,0),"IUI",2,"Storage Number","",
                "","N",None,None,None,("notzero",)),
            (("T",3,11,0),("IRB",ras),0,pts[13],"",
                "A","N",None,None,None,None),
            (("T",4,0,0),"IUI",3,"Group Number","",
                "","N",self.doGrpNum,None,None,("efld",)),
            (("T",4,1,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",4,2,0),"IUI",7,"From Account","From Account Number",
                "","N",self.doAcno,self.glm,None,("notzero",)),
            (("T",4,3,0),"IUI",7,"To Account","To Account Number",
                "","N",self.doAcno,self.glm,None,("efld",)),
            (("T",4,4,0),("IRB",ryn),0,pts[6],"",
                "N","N",None,None,None,None),
            (("T",4,5,0),("IRB",ryn),0,pts[8],"",
                "Y","N",None,None,None,None),
            (("T",4,6,0),("IRB",ryn),0,pts[0],"",
                "N","N",None,None,None,None),
            (("T",4,7,0),("IRB",rys),0,pts[11],"",
                "Y","N",None,None,None,None),
            (("T",4,8,0),("IRB",rns),0,pts[9],"",
                "P","N",None,None,None,None),
            (("T",4,9,0),("IRB",rat),0,pts[1],"",
                "A","N",None,None,None,None),
            (("T",4,10,0),("IRB",ryn),0,pts[7],"",
                "N","N",None,None,None,None),
            (("T",4,11,0),("IRB",ryn),0,pts[12],"",
                "N","N",self.doStore,None,None,None),
            (("T",4,12,0),"IUI",2,"Storage Number","",
                "","N",None,None,None,("notzero",)),
            (("T",4,13,0),("IRB",ras),0,pts[13],"",
                "A","N",None,None,None,None),
            (("T",4,14,0),"INA",10,"Chart Label","",
                "","N",None,None,None,None),
            (("T",5,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",5,1,0),("IRB",ryn),0,pts[6],"",
                "N","N",None,None,None,None),
            (("T",5,2,0),("IRB",rys),0,pts[11],"",
                "Y","N",None,None,None,None),
            (("T",5,3,0),("IRB",rns),0,pts[9],"",
                "P","N",None,None,None,None),
            (("T",5,4,0),("IRB",rat),0,pts[1],"",
                "A","N",None,None,None,None),
            (("T",5,5,0),("IRB",ryn),0,pts[4],"",
                "N","N",None,None,None,None),
            (("T",5,6,0),"IUI",2,"Storage Number","",
                "","N",None,None,None,("notzero",)),
            (("T",5,7,0),"IUD",6.2,pts[10],"",
                0,"N",None,None,None,("notzero",)),
            (("T",6,0,0),"INA",30,"Description","",
                "","N",None,None,None,("efld",)),
            (("T",6,1,0),("IRB",ryn),0,pts[6],"",
                "Y","N",None,None,None,None),
            (("T",6,2,0),"IUI",1,"Total Level","",
                "","N",None,None,None,("between",1,9)),
            (("T",6,3,0),("IRB",rys),0,pts[11],"",
                "Y","N",None,None,None,None),
            (("T",6,4,0),("IRB",rns),0,pts[9],"",
                "P","N",None,None,None,None),
            (("T",6,5,0),("IRB",ryn),0,pts[5],"",
                "Y","N",None,None,None,None),
            (("T",6,6,0),("IRB",ryn),0,pts[12],"",
                "N","N",self.doStore,None,None,None),
            (("T",6,7,0),"IUI",2,"Storage Number","",
                "","N",None,None,None,("notzero",)),
            (("T",6,8,0),("IRB",ras),0,pts[13],"",
                "A","N",None,None,None,None),
            (("T",6,9,0),"INA",10,"Chart Label","",
                "","N",None,None,None,None),
            (("T",7,0,0),("IRB",ryn),0,pts[6],"",
                "Y","N",None,None,None,None),
            (("T",7,1,0),("IRB",rsd),0,"Underline Type","",
                "S","N",None,None,None,None),
            (("T",8,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",8,1,0),("IRB",ryn),0,pts[6],"",
                "N","N",None,None,None,None),
            (("T",8,2,0),("IRB",rcb),0,pts[2],"",
                "A","N",self.doPAS,None,None,None),
            (("T",8,3,0),("IRB",rct),0,pts[3],"",
                "+","N",None,None,None,None),
            (("T",8,4,0),"IUI",2,"Storage Number (Base)","",
                "","N",self.doStore1,None,None,("notzero",)),
            (("T",8,5,0),"ISD",13.2,"Amount","Percent/Amount",
                "","N",self.doAmount,None,None,("efld",)),
            (("T",8,6,0),"IUI",2,"Storage Number (Calc)","",
                "","N",None,None,None,("efld",)),
            (("T",9,0,0),"INA",30,"Description","",
                "","N",None,None,None,("notblank",)),
            (("T",9,1,0),("IRB",ryn),0,pts[6],"",
                "N","N",None,None,None,None),
            (("T",9,2,0),"IUI",2,"Storage Number (Base)","",
                "","N",None,None,None,("notzero",)),
            (("T",9,3,0),"IUI",2,"Storage Number (Calc)","",
                "","N",None,None,None,("notzero",)))
        tnd = (
            (self.doT0End,"y"), (self.doT1End,"n"), (self.doT2End,"y"),
            (self.doT2End,"y"), (self.doT2End,"y"), (self.doT2End,"y"),
            (self.doT2End,"y"), (self.doT2End,"y"), (self.doT2End,"y"),
            (self.doT2End,"y"))
        txt = (
            self.doT0Exit, self.doT1Exit, self.doT2Exit, self.doT2Exit,
            self.doT2Exit, self.doT2Exit, self.doT2Exit, self.doT2Exit,
            self.doT2Exit, self.doT2Exit)
        but = (
            ("Generate",None,self.doGenRpt,0,("T",0,3),None),
            ("Copy",None,self.doCpyRpt,0,("T",0,3),None),
            ("Import",None,self.doImpRpt,0,("T",0,1),None),
            ("Export",None,self.doExpRpt,0,("T",1,1),None,None,1),
            ("Preview",None,self.doPreview,0,("T",1,1),None,None,1),
            ("Print",None,self.doPrint,0,("T",1,1),None,None,1))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, tags=tag, butt=but)

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        self.selcoy = w
        if self.selcoy == 0:
            acc = self.sql.getRec("genmst", cols=["glm_acno",
                "glm_desc"], group="glm_acno, glm_desc", order="glm_acno")
        else:
            acc = self.sql.getRec("genmst", cols=["glm_acno",
                "glm_desc"], where=[("glm_cono", "=", self.selcoy)],
                group="glm_acno, glm_desc", order="glm_acno")
        if self.dep == "Y":
            dep = {}
            chs = 10 ** (7 - self.dig)
            for a in acc:
                dep[a[0] % chs] = a[1]
            acc = []
            for a in dep:
                acc.append([a, dep[a]])
            acc.sort()
        self.glm["data"] = acc

    def doRepNum(self, frt, pag, r, c, p, i, w):
        self.repno = w
        rep = self.doReadRep(self.selcoy, self.repno, 0)
        if not rep:
            self.newrep = True
        else:
            self.newrep = False
            self.df.loadEntry(frt, pag, p+1, data=rep[3])
            self.df.loadEntry(frt, pag, p+2, data=rep[4])

    def doRepTyp(self, frt, pag, r, c, p, i, w):
        self.df.setWidget(self.df.B1, "disabled")

    def doGenRpt(self):
        if not "args" in self.opts:
            chk = self.sql.getRec("genmst", where=[("glm_cono", "=",
                self.selcoy), ("glm_fstp", "<>", "N")])
            if not chk:
                showError(self.opts["mf"].body, "Error", "There Are No "\
                    "F/S Account Types in the Masterfile Records.")
                self.df.focusField("T", 0, 3)
                return
            if not self.newrep:
                ok = askQuestion(self.opts["mf"].body, "Re-Generate?",
                    "This Report Already Exists, "\
                    "Do You Want to Re-Generate It?",
                    default="no")
                if ok == "no":
                    self.df.focusField("T", 0, 3)
                    return
            # Select Type
            but = (("Balance Sheet", "B"), ("Profit and Loss", "P"),
                ("Both", "X"), ("None", "N"))
            self.gtyp = askChoice(self.opts["mf"].body, head="Report Type",
                mess="Which Report Must be Generated?", butt=but,
                default="Both")
            if self.gtyp == "N":
                return
            # Check Type
            whr = [("glm_cono", "=", self.selcoy)]
            if self.gtyp == "X":
                whr.append(("glm_type", "in", ("B", "P")))
            else:
                whr.append(("glm_type", "=", self.gtyp))
            whr.append(("glm_fstp", "=", "N"))
            chk = self.sql.getRec("genmst", where=whr)
            if chk:
                showError(self.opts["mf"].body, "Error", "There Are Some "\
                    "Masterfile Accounts Without a F/S Account Type.")
                self.df.focusField("T", 0, 3)
                return
        # Delete old records
        if not self.newrep:
            self.sql.delRec("genrpt", where=[("glr_cono", "=", self.selcoy),
                ("glr_repno", "=", self.repno)])
        # Table genrpt
        self.hhh = {"glr_desc": "X", "glr_high": "Y", "glr_ffeed": "X",
            "glr_ignore": "X"}
        self.lll = {"glr_high": "N", "glr_ignore": "X", "glr_from": "X",
            "glr_to": "X", "glr_obal": "Y", "glr_accum": "N", "glr_print": "X",
            "glr_norm": "X", "glr_acbal": "A", "glr_store": "N", "glr_snum1": 0,
            "glr_acstr": ""}
        self.ggg = {"glr_desc": "X", "glr_high": "N", "glr_ignore": "Y",
            "glr_from": "X", "glr_to": "X", "glr_obal": "Y", "glr_accum": "N",
            "glr_print": "X", "glr_norm": "X", "glr_acbal": "A",
            "glr_store": "N", "glr_snum1": 0, "glr_acstr": "I",
            "glr_group": "X", "glr_label": ""}
        self.ttt = {"glr_desc": "X", "glr_high": "Y", "glr_print": "Y",
            "glr_norm": "X", "glr_store": "N", "glr_snum1": 0, "glr_acstr": "",
            "glr_total": "X", "glr_clear": "X", "glr_label": ""}
        self.uuu = {"glr_high": "Y", "glr_uline": "X"}
        # Codes
        self.codes = {
            "A": ("A", "Capital Employed", "N", "Y", "N"),
            "B": ("B", "Fixed Assets", "N", "+", "P"),
            "C": ("C", "Current Assets", "N", "+", "P"),
            "D": ("B", "Fixed Liabilities", "N", "-", "N"),
            "E": ("C", "Current Liabilities", "N", "-", "N"),
            "F": ["D", "Income", "Y", "Y", "N"],
            "G": ("E", "Expenses", "N", "Y", "P"),
            "H": ("F", "", "N", "Y", "P")}
        # Variables
        self.cnt = 0
        self.grp = []
        # Headings
        if self.gtyp in ("B", "X"):
            self.getList(["B", "Balance Sheet"])
            # Capital
            self.ret = self.sql.getRec("ctlctl", cols=["ctl_conacc"],
                where=[("ctl_cono", "=", self.selcoy), ("ctl_code",
                "=", "ret_inc")], limit=1)
            self.genCode(self.codes["A"])
            self.getList(["U", "S"])
            self.getList(["T", "", "N", 4, "Y"])
            self.getList(["U", "D"])
            self.getList(["H", "Employment of Capital", "N", "N"])
            if self.genCode(self.codes["B"]):
                self.getList(["U", "S"])
                self.getList(["T", "", "P", 1, "Y"])
                self.getList(["U", "D"])
            if self.genCode(self.codes["C"]):
                self.getList(["U", "S"])
                self.getList(["T", "", "P", 1, "Y"])
            if self.genCode(self.codes["D"]):
                self.getList(["U", "S"])
                self.getList(["T", "", "N", 1, "Y"])
            if self.genCode(self.codes["E"]):
                self.getList(["U", "S"])
                self.getList(["T", "", "N", 1, "Y"])
            self.getList(["U", "S"])
            self.getList(["T", "", "P", 4, "Y"])
            self.getList(["U", "D"])
        if self.gtyp in ("P", "X"):
            if self.gtyp == "P":
                self.ret = None
                self.codes["F"][2] = "N"
                self.getList(["P", "Profit and Loss"])
            # P&L
            if self.genCode(self.codes["F"]):
                self.getList(["U", "S"])
                self.getList(["T", "Total Net Income", "N", 1, "Y"])
                self.getList(["U", "B"])
            if self.genCode(self.codes["G"]):
                self.getList(["U", "S"])
                self.getList(["T", "Total Expenses", "P", 1, "Y"])
            self.getList(["U", "S"])
            self.getList(["T", "Net Income Before Taxation", "N", 2, "Y"])
            if self.genCode(self.codes["H"]):
                self.getList(["U", "S"])
                self.getList(["T", "Net Income After Taxation", "N", 3, "Y"])
            if self.ret:
                for gp in range(1, 999):
                    if gp not in self.grp:
                        self.grp.append(gp)
                        break
                self.getList(["G", "Retained Income B/F", self.ret[0],
                    0, "Y", "N", gp])
                self.getList(["U", "S"])
                self.getList(["T", "Retained Income C/F", "N", 4, "Y"])
            self.getList(["U", "D"])
        self.newrep = False
        rep = self.doReadRep(self.selcoy, self.repno, 0)
        if "args" not in self.opts:
            self.df.setWidget(self.df.B1, "disabled")
            self.df.loadEntry("T", 0, 2, data=rep[3])
            self.df.loadEntry("T", 0, 3, data=rep[4])
            self.df.setWidget(self.df.B1, "disabled")
            self.df.selPage("Sequence")
            self.df.focusField("T", 1, 1)

    def genCode(self, args):
        code, head, page, sign, norm = args
        recs = self.sql.getRec("genmst", cols=["glm_acno", "glm_fsgp",
            "glm_desc"], where=[("glm_cono", "=", self.selcoy),
            ("glm_fstp", "=", code)], order="glm_acno")
        acc = []
        lr = lg = 0
        flg = True
        for num, rec in enumerate(recs):
            if flg and head:
                if self.gtyp in ("B", "X") and page == "Y":
                    ign = "Y"
                else:
                    ign = "N"
                self.getList(["H", head, page, ign])
                flg = False
            if code == "A" and self.ret and rec[0] == self.ret[0]:
                if acc:
                    self.getList(["L", "Y", acc[0], acc[1], sign, norm])
                    acc = []
                one = self.sql.getRec("genmst", cols=["min(glm_acno)"],
                    where=[("glm_cono", "=", self.selcoy), ("glm_type",
                    "=", "P")], limit=1)
                two = self.sql.getRec("genmst", cols=["max(glm_acno)"],
                    where=[("glm_cono", "=", self.selcoy), ("glm_type",
                    "=", "P")], limit=1)
                for gp in range(1, 999):
                    if gp not in self.grp:
                        self.grp.append(gp)
                        break
                self.getList(["G", "Retained Earnings", one[0], two[0],
                    sign, norm, gp])
                self.getList(["G", "Retained Earnings", self.ret[0], 0,
                    sign, norm, gp])
            elif rec[1]:
                if acc:
                    self.getList(["L", "N", acc[0], acc[1], sign, norm])
                    acc = []
                if rec[1] not in self.grp:
                    lr = lg = rec[1]
                if rec[1] != lr:
                    for lg in range(1, 999):
                        if lg not in self.grp:
                            lr = rec[1]
                            break
                chk = self.sql.getRec("genrpt", cols=["glr_desc"],
                    where=[("glr_cono", "=", self.selcoy), ("glr_repno",
                    "=", self.repno), ("glr_group", "=", lg)], limit=1)
                if chk:
                     desc = chk[0]
                else:
                    desc = rec[2]
                self.getList(["G", desc, rec[0], 0, sign, norm, lg])
                if lg not in self.grp:
                    self.grp.append(lg)
            elif not acc:
                acc = [rec[0], 0]
            else:
                acc[1] = rec[0]
        if acc:
            self.getList(["L", "N", acc[0], acc[1], sign, norm])
        if recs:
            return True

    def getList(self, args):
        if args[0] in ("B", "P"):
            ff = {"glr_desc": "X"}
        elif args[0] == "H":
            ff = self.hhh
        elif args[0] == "L":
            ff = self.lll
        elif args[0] == "G":
            ff = self.ggg
        elif args[0] == "T":
            ff = self.ttt
        else:
            ff = self.uuu
        data = [self.selcoy, self.repno, self.cnt, args.pop(0)]
        for nm, cl in enumerate(self.sql.genrpt_col[4:]):
            if cl in ff:
                dat = ff[cl]
                if dat == "X":
                    data.append(args.pop(0))
                else:
                    data.append(ff[cl])
            elif self.sql.genrpt_dic[cl][2][1] in ("A", "a"):
                data.append("")
            else:
                data.append(0)
        data.append("")
        self.sql.insRec("genrpt", data=data)
        self.cnt += 1

    def doImpRpt(self):
        self.df.setWidget(self.df.B0, state="disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        sel = FileDialog(parent=self.opts["mf"].body, title="Import File",
            initd=self.opts["mf"].rcdic["wrkdir"], ftype=[("Report", "*.rpt")])
        nam = sel.askopenfilename()
        err = None
        if nam:
            fle = open(nam, "r")
            for num, line in enumerate(fle):
                dat = line.split("|")
                if not num:
                    if dat[0] != "genrpt":
                        err = "This File Does Not Contain a Valid Format"
                        break
                    chk = self.sql.getRec("genrpt",
                        where=[("glr_cono", "=", dat[1]), ("glr_repno", "=",
                            dat[2]), ("glr_seq", "=", 0)], limit=1)
                    if chk:
                        ok = askQuestion(self.opts["mf"].body, "Replace?",
                            "This Report Already Exists, Would you like "\
                            "to Replace It?")
                        if ok == "yes":
                            self.sql.delRec("genrpt", where=[("glr_cono", "=",
                                dat[1]), ("glr_repno", "=", dat[2])])
                        else:
                            err = "Report Already Exists"
                            break
                    self.sql.insRec("genrpt", data=dat[1:])
                else:
                    self.sql.insRec(dat[0], data=dat[1:])
        if nam and not err:
            self.opts["mf"].dbm.commitDbase(ask=True)
        elif err:
            showError(self.opts["mf"].body, "Invalid Import", err)
        self.df.setWidget(self.df.mstFrame, "show")
        self.df.focusField("T", 0, 1)

    def doExpRpt(self):
        fle = open(os.path.join(self.opts["mf"].rcdic["wrkdir"],
            "C%s_R%s.rpt" % (self.selcoy, self.repno)), "w")
        rpt = self.sql.getRec("genrpt", where=[("glr_cono", "=",
            self.selcoy), ("glr_repno", "=", self.repno)], order="glr_seq")
        for lin in rpt:
            mes = "genrpt"
            for dat in lin:
                mes = "%s|%s" % (mes, str(dat))
            fle.write("%s\n" % mes)
        fle.close()
        self.df.focusField("T", 0, 1)

    def doCpyRpt(self):
        if not self.newrep:
            showError(self.opts["mf"].body, "Invalid Copy Request",
                "You can only Copy a report when Creating a New report, "\
                "not when Changing an Existing report!")
            self.df.focusField("T", 0, 3)
            return
        tit = ("Copy Existing Report Layout",)
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name", "Y"))}
        glr = {
            "stype": "R",
            "tables": ("genrpt",),
            "cols": (
                ("glr_cono", "", 0, "Coy"),
                ("glr_repno", "", 0, "Rep"),
                ("glr_type", "", 0, "T"),
                ("glr_desc", "", 0, "Description", "Y")),
            "where": [("glr_seq", "=", 0)],
            "whera": (("T", "glr_cono", 0, 0),),
            "index": 1}
        fld = (
            (("T",0,0,0),"IUI",3,"Company Number","",
                "","N",self.doCpyCoy,coy,None,None),
            (("T",0,1,0),"IUI",3,"Report Number","",
                "","N",self.doRptNum,glr,None,None))
        state = self.df.disableButtonsTags()
        self.cp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doCpyEnd, "n"),), txit=(self.doCpyExit,))
        self.cp.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 0, 1)

    def doCpyCoy(self, frt, pag, r, c, p, i, w):
        self.cpycoy = w

    def doRptNum(self, frt, pag, r, c, p, i, w):
        self.cpynum = w

    def doCpyEnd(self):
        rpt = self.sql.getRec("genrpt", where=[("glr_cono", "=",
            self.cpycoy), ("glr_repno", "=", self.cpynum)])
        if rpt:
            for rec in rpt:
                rec[0] = self.selcoy
                rec[1] = self.repno
                self.sql.insRec("genrpt", data=rec)
            self.opts["mf"].dbm.commitDbase()
        self.doCpyCloseProcess()

    def doCpyExit(self):
        self.doCpyCloseProcess()

    def doCpyCloseProcess(self):
        self.cp.closeProcess()

    def doDelRpt(self):
        self.sql.delRec("genrpt", where=[("glr_cono", "=", self.selcoy),
            ("glr_repno", "=", self.repno)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doT0End(self):
        rtype = self.df.t_work[0][0][2]
        desc = self.df.t_work[0][0][3]
        if self.newrep:
            data = [self.selcoy, self.repno, 0, rtype, desc]
            for x in range(5, len(self.genrpt_cl)):
                if self.genrpt_fd[self.genrpt_cl[x]][2][1] in ("A", "a"):
                    data.append("")
                else:
                    data.append(0)
            self.sql.insRec("genrpt", data=data)
        else:
            self.sql.updRec("genrpt", cols=["glr_type", "glr_desc"],
                data=[rtype, desc], where=[("glr_cono", "=", self.selcoy),
                ("glr_repno", "=", self.repno), ("glr_seq", "=", 0)])
        self.df.selPage("Sequence")
        self.df.focusField("T", 1, 1)

    def doPreview(self):
        self.cols = [
            ("a", "Seq-Num", 7.2, "UD"),
            ("b", "T", 1, "UA"),
            ("c", "Grp", 3, "Na"),
            ("d", "Lvl", 3, "Na"),
            ("e", "Acc-Num", 7, "Na"),
            ("f", "Description", 30, "NA")]
        self.data = []
        self.newp = []
        recs = self.sql.getRec("genrpt", where=[("glr_cono", "=",
            self.selcoy), ("glr_repno", "=", self.repno)], order="glr_seq")
        pgp = 0
        lsq = 0
        rpc = self.sql.genrpt_col
        for num, rec in enumerate(recs):
            seq = rec[rpc.index("glr_seq")]
            rtp = rec[rpc.index("glr_type")]
            if rtp in ("B", "P", "O"):
                self.titl = rec[rpc.index("glr_desc")]
                continue
            des = rec[rpc.index("glr_desc")]
            prt = rec[rpc.index("glr_print")]
            if prt == "N":
                continue
            if rtp == "H":
                if rec[rpc.index("glr_ffeed")] == "Y":
                    self.data.append((seq, "N", "", "", "",
                        "---------- New Page ----------"))
                elif lsq:
                    ptp = recs[lsq][rpc.index("glr_type")]
                    utp = recs[lsq][rpc.index("glr_uline")]
                    if ptp == "H" or (ptp == "U" and utp == "B"):
                        pass
                    else:
                        self.data.append((seq, "", "", "", "", ""))
                self.data.append((seq, rtp, "", "", "", des))
                self.data.append((seq, "", "", "", "", ""))
            elif rtp == "L":
                frm = rec[rpc.index("glr_from")]
                too = rec[rpc.index("glr_to")]
                whr = [("glm_cono", "=", self.selcoy)]
                if too:
                    whr.append(("glm_acno", "between", frm, too))
                else:
                    whr.append(("glm_acno", "=", frm))
                accs = self.sql.getRec("genmst", cols=["glm_acno",
                    "glm_desc"], where=whr, order="glm_acno")
                for acc in accs:
                    self.data.append((seq, rtp, "", "", acc[0], acc[1]))
            elif rtp == "G":
                grp = rec[rpc.index("glr_group")]
                if not pgp or grp != pgp:
                    self.data.append((seq, rtp, grp, "", "", des))
                pgp = grp
            elif rtp == "T":
                tot = rec[rpc.index("glr_total")]
                self.data.append((seq, rtp, "", tot, "", des))
            elif rtp == "S":
                self.data.append((seq, rtp, "", "", "", des))
            elif rtp == "U":
                utp = rec[rpc.index("glr_uline")]
                if utp == "B":
                    des = ""
                elif utp == "S":
                    des = "-" * 30
                else:
                    des = "=" * 30
                self.data.append((seq, rtp, "", "", "", des))
            else:
                continue
            lsq = num
        self.pprt = False
        sc = SelectChoice(self.opts["mf"].window, self.titl, self.cols,
            self.data, sort=False, butt=(("Print", self.doPrePrt),))
        if self.pprt:
            cols = []
            for col in self.cols:
                cols.append([col[0], col[3], col[2], col[1], "y"])
            state = self.df.disableButtonsTags()
            self.df.setWidget(self.df.mstFrame, "hide")
            RepPrt(self.opts["mf"], name=self.__class__.__name__,
                tables=self.data, heads=[self.titl], cols=cols, ttype="D",
                prtdia=(("Y","V"),("Y","N")))
            self.df.setWidget(self.df.mstFrame, "show")
            self.df.enableButtonsTags(state=state)
            self.df.focusField("T", 1, 1)
        elif sc.selection:
            self.df.doKeyPressed("T", 1,  0, sc.selection[1])
            self.df.doKeyPressed("T", 1,  1, sc.selection[2])
        else:
            self.df.focusField("T", 1, 1)

    def doPrePrt(self):
        self.pprt = True

    def doPrint(self):
        table = ["genrpt"]
        heads = ["General Ledger Report %s Layout" % self.repno]
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, "hide")
        RepPrt(self.opts["mf"], name=self.__class__.__name__, tables=table,
            heads=heads, where=[("glr_cono", "=", self.selcoy),
            ("glr_repno", "=", self.repno)], order="glr_seq asc",
            prtdia=(("Y","V"), ("Y","N")))
        self.df.setWidget(self.df.mstFrame, "show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doSeqNum(self, frt, pag, r, c, p, i, w):
        if not w:
            acc = self.sql.getRec("genrpt", cols=["max(glr_seq)"],
                where=[("glr_cono", "=", self.selcoy), ("glr_repno", "=",
                self.repno)], limit=1)
            if not acc:
                w = 1
            else:
                w = int(acc[0] + 1)
            self.df.loadEntry(frt, pag, i, data=w)
        self.seqno = w
        self.seq = self.doReadRep(self.selcoy, self.repno, self.seqno)
        if not self.seq:
            self.newseq = "y"
        else:
            self.newseq = "n"
            self.df.loadEntry(frt, pag, p+1, data=self.seq[3])

    def doSeqType(self, frt, pag, r, c, p, i, w):
        self.stype = w
        if self.newseq == "y":
            return
        if self.stype == self.seq[3]:
            return
        yn = askQuestion(self.opts["mf"].body, "Change Type?",
            "Change the Type?", default="no")
        if yn == "no":
            return "No Change"
        self.newseq = "c"

    def doDelSeq(self):
        if self.newseq == "y":
            showError(self.opts["mf"].body, "Invalid Delete Request",
                "You can only delete Existing report lines.")
            return
        self.sql.delRec("genrpt", where=[("glr_cono", "=", self.selcoy),
            ("glr_repno", "=", self.repno), ("glr_seq", "=", self.seqno)])
        self.df.clearFrame("T", 1)
        self.df.focusField("T", 1, 1)
        return "nf"

    def doT1End(self):
        for x in range(2, 10):
            self.df.clearFrame("T", x)
        pag = self.pags.index(self.stype)
        if self.newseq == "n":
            cl = self.genrpt_cl
            fld = self.doLoadTypes()
            for x, f in enumerate(fld):
                data = self.seq[cl.index(f)]
                self.df.loadEntry("T", pag, x, data=data)
        self.df.selPage(self.df.tags[pag - 1][0])

    def doAcno(self, frt, pag, r, c, p, i, w):
        if w:
            if pag == 3 and p == 1 and w < self.df.t_work[pag][0][0]:
                return "To Account Less Than From Account"
            if pag == 4 and p == 3 and w < self.df.t_work[pag][0][2]:
                return "To Account Less Than From Account"
            found = False
            for acc in self.glm["data"]:
                if w == acc[0]:
                    found = True
            if not found:
                return "Invalid Account Number"

    def doStore(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data="")
            return "sk2"

    def doGrpNum(self, frt, pag, r, c, p, i, w):
        if not w:
            gno = self.sql.getRec("genrpt", cols=["max(glr_group)"],
                where=[("glr_cono", "=", self.selcoy), ("glr_repno", "=",
                self.repno), ("glr_type", "=", "G")], limit=1)
            self.gno = gno[0] + 1
            self.df.loadEntry(frt, pag, p, data=self.gno)
        else:
            self.gno = w
        col = ["glr_desc", "glr_high", "glr_obal", "glr_accum",
            "glr_print", "glr_norm", "glr_acbal", "glr_ignore",
            "glr_store", "glr_snum1", "glr_acstr", "glr_label"]
        grp = ""
        for cc in col:
            grp = "%s%s," % (grp, cc)
        grp = grp[:-1]
        self.grp = self.sql.getRec("genrpt", cols=col,
            where=[("glr_cono", "=", self.selcoy), ("glr_repno", "=",
            self.repno), ("glr_group", "=", self.gno)], group=grp)
        if self.grp:
            for n, f in enumerate(col):
                data = self.grp[0][n]
                self.df.loadEntry("T", pag, self.group.index(f), data=data)

    def doPAS(self, frt, pag, r, c, p, i, w):
        self.pas = w
        if self.pas == "P":
            self.df.loadEntry(frt, pag, p+1, data="*")
            return "sk1"

    def doStore1(self, frt, pag, r, c, p, i, w):
        if self.pas == "S":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doAmount(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry(frt, pag, p+1, data=0)
        return "sk1"

    def doT2End(self):
        ff = self.doLoadTypes()
        data = [self.selcoy, self.repno, self.seqno, self.stype]
        for cl in self.genrpt_cl[4:]:
            if cl in ff:
                data.append(self.df.t_work[self.pags.index(self.stype)]
                        [0][ff.index(cl)])
            elif self.genrpt_fd[cl][2][1] in ("A", "a"):
                data.append("")
            else:
                data.append(0)
        if self.newseq in ("c", "n"):
            self.doDelSeq()
        self.sql.insRec("genrpt", data=data)
        if self.stype == "G" and self.grp:
            grp = self.sql.getRec("genrpt", where=[("glr_cono", "=",
                self.selcoy), ("glr_repno", "=", self.repno),
                ("glr_group", "=", self.gno)], order="glr_seq")
            for g in grp:
                if g[2] == self.seqno:
                    continue
                data[2] = g[2]
                data[8] = g[8]
                data[9] = g[9]
                data[29] = g[29]
                self.sql.updRec("genrpt", data=data, where=[("glr_cono", "=",
                    self.selcoy), ("glr_repno", "=", self.repno), ("glr_group",
                    "=", self.gno), ("glr_seq", "=", g[2])])
        self.doT2Exit()
        if self.newseq == "y":
            self.df.loadEntry("T", 1, 0, data=(self.seqno + 1))
        else:
            self.df.clearEntry("T", 1, 1)
        self.df.clearEntry("T", 1, 2)
        self.df.focusField("T", 1, 1)

    def doLoadTypes(self):
        if self.stype == "H":
            fld = self.head
        elif self.stype == "L":
            fld = self.ledger
        elif self.stype == "G":
            fld = self.group
        elif self.stype == "S":
            fld = self.store
        elif self.stype == "T":
            fld = self.total
        elif self.stype == "U":
            fld = self.uline
        elif self.stype == "C":
            fld = self.calc
        elif self.stype == "P":
            fld = self.percent
        return fld

    def doT0Exit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doT1Exit(self):
        # Check for duplicate group numbers
        errmess = """Group Number %s at Sequence Line %s is Duplicated or is Not Contiguous i.e. All Group Lines Must Follow One Another!

Please Delete, or Correct This Line!"""
        seq = self.sql.getRec("genrpt", cols=["glr_type", "glr_seq",
            "glr_group"], where=[("glr_cono", "=", self.selcoy), ("glr_repno",
            "=", self.repno)], order="glr_seq")
        gp = []
        lg = 0
        for t, s, g in seq:
            if t == "G":
                if not lg and g in gp:
                    showError(
                        self.opts["mf"].body, "Group Error", errmess % (g, s))
                    self.df.loadEntry("T", 1, 0, data=s)
                    self.df.focusField("T", 1, 1)
                    return
                if lg and g != lg:
                    if g in gp:
                        showError(self.opts["mf"].body, "Group Error",
                            errmess % (g, s))
                        self.df.loadEntry("T", 1, 0, data=s)
                        self.df.focusField("T", 1, 1)
                        return
                    lg = g
                    gp.append(g)
                    continue
                if not lg:
                    lg = g
                    gp.append(g)
                    continue
            else:
                lg = 0
        # Re-Sequence
        ok = askQuestion(self.opts["mf"].body, "Re-Sequence?",
            "Would You Like to Re-Sequence All the Lines?", default="yes")
        if ok == "yes":
            whr = [
                ("glr_cono", "=", self.selcoy),
                ("glr_repno", "=", self.repno)]
            recs = self.sql.getRec("genrpt", where=whr, order="glr_seq")
            self.sql.delRec("genrpt", where=whr)
            for seq, rec in enumerate(recs):
                rec = list(rec)
                rec[2] = float(seq)
                self.sql.insRec("genrpt", data=rec)
        self.opts["mf"].dbm.commitDbase(ask=True, mess="Save All Changes?")
        self.df.focusField("T", 0, 1)

    def doT2Exit(self):
        self.df.selPage("Sequence")

    def doReadRep(self, coy, rep, seq):
        rep = self.sql.getRec("genrpt", where=[("glr_cono", "=", coy),
            ("glr_repno", "=", rep), ("glr_seq", "=", seq)], limit=1)
        return rep

# vim:set ts=4 sw=4 sts=4 expandtab:
