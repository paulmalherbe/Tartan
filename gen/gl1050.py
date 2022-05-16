"""
SYNOPSIS
    General Ledger - Capturing Stream Records.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import getPrinters

class gl1050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        # Check for control record and departments
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        # Check for multiple companies
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "genrpc", "genstr",
            "gendtm", "genrpt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        acc = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if acc[0] > 1:
            self.coys = True
        else:
            self.coys = False
        self.strm = 0
        return True

    def doProcess(self):
        st1 = {
            "stype": "R",
            "tables": ("genstr",),
            "cols": (
                ("gls_strm", "", 0, "Str"),
                ("gls_desc", "", 0, "Description", "Y")),
            "where": [("gls_cono", "=", self.opts["conum"])],
            "group": "gls_strm, gls_desc"}
        st2 = {
            "stype": "R",
            "tables": ("genstr",),
            "cols": (
                ("gls_seq", "", 0, "Seq"),
                ("gls_typ", "", 0, "T"),
                ("gls_cno", "", 0, "CN"),
                ("gls_con", "", 0, "C"),
                ("gls_rep", "", 0, "Rep"),
                ("gls_gen", "", 0, "G"),
                ("gls_val", "", 0, "V"),
                ("gls_det", "", 0, "Det"),
                ("gls_var", "", 0, "B"),
                ("gls_zer", "", 0, "Z"),
                ("gls_opt", "", 0, "O"),
                ("gls_num", "", 0, "N"),
                ("gls_prnt", "", 20, "Printer-Name"),
                ("gls_mail", "", 20, "E-Mail-Address")),
            "where": [("gls_cono", "=", self.opts["conum"])],
            "whera": (("T", "gls_strm", 0, 0),),
            "comnd": self.doSelTyp}
        typ = {
            "stype": "C",
            "title": "Available Types",
            "head": ("C", "Description"),
            "data": (
                ("S", "YTD Report"),
                ("H", "Last 3 Years YTD Report"),
                ("L", "MTD and YTD Report"),
                ("M", "Monthly Report"),
                ("C", "Customised Report"))}
        rpc = {
            "stype": "R",
            "tables": ("genrpc",),
            "cols": (
                ("glc_cusno", "", 0, "CN"),
                ("glc_head1", "", 0, "Heading-1"),
                ("glc_head2", "", 0, "Heading-2"),
                ("glc_head3", "", 0, "Heading-3"),
                ("glc_head4", "", 0, "Heading-4")),
            "where": [("glc_cono", "=", self.opts["conum"])]}
        rpt = {
            "stype": "R",
            "tables": ("genrpt",),
            "cols": (
                ("glr_cono", "", 0, "Coy"),
                ("glr_repno", "", 0, "Rep"),
                ("glr_type", "", 0, "T"),
                ("glr_desc", "", 0, "Description", "Y")),
            "where": [("(", "glr_cono", "=", 0, "or", "glr_cono", "=",
                self.opts["conum"], ")"), ("glr_seq", "=", 0)],
            "group": "glr_cono, glr_repno, glr_type, glr_desc",
            "index": 1}
        con = {
            "stype": "C",
            "title": "Available Options",
            "head": ("C", "Description"),
            "data": (
                ("V", "Actuals"),
                ("B", "Budgets"),
                ("C", "Actuals and Budgets"),
                ("X", "Variance to Budget"),
                ("D", "Detail"))}
        det = {
            "stype": "R",
            "tables": ("gendtm",),
            "cols": (
                ("gdm_code", "", 0, "Cod"),
                ("gdm_desc", "", 0, "Description")),
            "where": [("gdm_cono", "=", self.opts["conum"])]}
        prts = getPrinters(wrkdir=self.opts["mf"].rcdic["wrkdir"])
        prts.insert(1, "Export")
        if "None" not in prts:
            prts.append("None")
        prt = {
            "stype": "C",
            "titl": "Select Required Printer",
            "head": ("Name", "Description"),
            "data": prts}
        cts = ("V", "B", "C", "X", "D")
        fld = (
            (("T",0,0,0),"IUI",3,"Stream-Number","Stream Number",
                0,"Y",self.doStr,st1,None,("notzero",)),
            (("T",0,0,0),"INA",30,"Description","",
                "","N",self.doDsc,None,self.doDelStr,("notblank",)),
            (("C",0,0,0),"IUI",3,"Seq","Sequence Number",
                "i","N",self.doSeq,st2,None,("efld",)),
            (("C",0,0,1),"IUA",1,"T","Report Type",
                "S","N",self.doTyp,typ,self.doDelLin,
                ("in",("S","H","L","M","C"))),
            (("C",0,0,2),"IUI",2,"CN","Custom Number",
                0,"N",self.doCus,rpc,None,("efld",)),
            (("C",0,0,3),"IUA",1,"C","Consolidate (Y/N)",
                "N","N",self.doCon,None,None,("in",("Y","N"))),
            (("C",0,0,4),"IUI",3,"Rep","Report Number",
                0,"N",self.doRep,rpt,None,("notzero",)),
            (("C",0,0,5),"IUA",1,"G","General Report (Y/N)",
                "N","N",self.doGen,None,None,("in",("Y","N"))),
            (("C",0,0,6),"IUA",1,"V","Report Contents",
                "V","N",self.doContent,con,None,("in",cts)),
            (("C",0,0,7),"INa",2,"Cod","Details Code",
                "","N",self.doCod,det,None,None),
            (("C",0,0,8),"IUA",1,"V","Variance (B/P/N)",
                "B","N",self.doVar,None,None,("in",("B","P","N"))),
            (("C",0,0,9),"IUA",1,"Z","Ignore Zeros (Y/N)",
                "Y","N",None,None,None,("in",("Y","N"))),
            (("C",0,0,10),"IUA",1,"O","Print Options (Y/N)",
                "N","N",None,None,None,("in",("Y","N"))),
            (("C",0,0,11),"IUA",1,"N","Print Numbers (Y/N)",
                "N","N",None,None,None,("in",("Y","N"))),
            (("C",0,0,12),"ITX",30,"Printer Name","Printer-Name",
                "Default","N",self.doPrt,prt,None,("in",prts)),
            (("C",0,0,13),"ITX",30,"E-Mail Address","E-Mail-Address",
                "","N",None,None,None,("email",)))
        but = (
            ("Cancel",None,self.doCancel,0,("C",0,1),("T",0,1)),
            ("Quit",None,self.exitTops,1,None,None))
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.endTops,"n"),), txit=(self.exitTops,),
            cend=((self.endData,"y"),), cxit=(self.exitData,), butt=but)
        self.df.focusField("T", 0, 1)

    def doStr(self, frt, pag, r, c, p, i, w):
        self.strm = w
        self.old = self.sql.getRec("genstr", where=[("gls_cono",
            "=", self.opts["conum"]), ("gls_strm", "=", self.strm)], limit=1)
        if not self.old:
            self.new = "y"
        else:
            self.new = "n"
            self.desc = self.old[self.sql.genstr_col.index("gls_desc")]
            self.df.loadEntry(frt, pag, p+1, self.desc)

    def doDelStr(self):
        if self.new == "y":
            return
        self.sql.delRec("genstr", where=[("gls_cono", "=", self.opts["conum"]),
            ("gls_strm", "=", self.strm)])

    def doDsc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doSeq(self, frt, pag, r, c, p, i, w):
        self.seq = w
        dt = self.sql.getRec("genstr", where=[("gls_cono", "=",
            self.opts["conum"]), ("gls_strm", "=", self.strm), ("gls_seq", "=",
            self.seq)], limit=1)
        if not dt:
            self.newlin = "y"
        else:
            self.newlin = "n"
            for n, d in enumerate(dt[3:-1]):
                self.df.loadEntry(frt, pag, p+n, data=d)

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w
        if self.typ != "C":
            self.cno = 0
            if not self.coys:
                self.con = "N"
                self.df.loadEntry(frt, pag, p+2, data="N")
                return "sk2"
            return "sk1"

    def doCus(self, frt, pag, r, c, p, i, w):
        cn = self.sql.getRec("genrpc", where=[("glc_cono", "=",
            self.opts["conum"]), ("glc_cusno", "=", w)], limit=1)
        if not cn:
            return "Invalid Custom Report Number"
        self.cno = w
        if not self.coys:
            self.con = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            return "sk1"

    def doCon(self, frt, pag, r, c, p, i, w):
        self.con = w

    def doRep(self, frt, pag, r, c, p, i, w):
        rp = self.sql.getRec("genrpt", cols=["glr_cono", "glr_repno"],
            where=[("(", "glr_cono", "=", 0, "or", "glr_cono", "=",
            self.opts["conum"], ")"), ("glr_repno", "=", w)], limit=1)
        if not rp:
            return "No Such Report"
        self.rep = w

    def doGen(self, frt, pag, r, c, p, i, w):
        if w == "Y":
            c = 0
        else:
            c = self.opts["conum"]
        rp = self.sql.getRec("genrpt", cols=["glr_cono", "glr_repno"],
            where=[("glr_cono", "=", c), ("glr_repno", "=", self.rep)],
            limit=1)
        if not rp:
            return "No Such Report"
        self.gen = w

    def doContent(self, frt, pag, r, c, p, i, w):
        if w in ("B", "C", "X") and self.typ in ("S", "L", "C"):
            return "Invalid Choice for this Report Type"
        if w == "D":
            return
        self.df.loadEntry(frt, pag, p+1, data="")
        return "sk1"

    def doCod(self, frt, pag, r, c, p, i, w):
        d = self.sql.getRec("gendtm", cols=["gdm_desc"],
            where=[("gdm_cono", "=", self.opts["conum"]), ("gdm_code", "=",
            w)], limit=1)
        if not d:
            return "Invalid Detail Code"

    def doVar(self, frt, pag, r, c, p, i, w):
        if self.typ == "C" and w not in ("B", "P"):
            return "Invalid Variance, Only B or P"

    def doPrt(self, frt, pag, r, c, p, i, w):
        if w == "Export":
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"

    def endTops(self):
        if self.new == "y":
            self.df.focusField("C", 0, 1)
        else:
            self.doLoadLines()

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def exitTops(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doSelTyp(self, frt, pag, r, c, p, i, w):
        self.newlin = "n"
        self.seq = w[0]
        self.typ = w[1]
        self.cno = w[2]
        self.con = w[3]
        self.rep = w[4]
        self.gen = w[5]
        for x, d in enumerate(w):
            self.df.loadEntry(frt, pag, p+x, data=d)
        self.df.focusField(frt, pag, c+1)

    def doDelLin(self):
        if self.newlin == "y":
            return
        self.sql.delRec("genstr", where=[("gls_cono", "=", self.opts["conum"]),
            ("gls_strm", "=", self.strm), ("gls_seq", "=", self.seq)])
        self.doReSeq()

    def endData(self):
        data = [self.opts["conum"], self.strm, self.desc, self.seq, self.typ,
            self.cno, self.con, self.rep, self.gen]
        for x in range(6, 14):
            data.append(self.df.c_work[self.df.pag][self.df.row][x])
        if self.newlin == "y":
            self.sql.insRec("genstr", data=data)
        elif data != self.old[:len(data)]:
            col = self.sql.genstr_col
            data.append(self.old[col.index("gls_xflag")])
            self.sql.updRec("genstr", data=data, where=[("gls_cono",
                "=", self.opts["conum"]), ("gls_strm", "=", self.strm),
                ("gls_seq", "=", self.seq)])
        self.doLoadLines()

    def exitData(self):
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doReSeq(self):
        recs = self.sql.getRec("genstr", where=[("gls_cono", "=",
            self.opts["conum"]), ("gls_strm", "=", self.strm)],
            order="gls_seq")
        if not recs:
            self.newlin = "y"
            self.df.focusField("C", 0, 1)
            return
        self.sql.delRec("genstr", where=[("gls_cono", "=", self.opts["conum"]),
            ("gls_strm", "=", self.strm)])
        for seq, acc in enumerate(recs):
            acc[3] = seq
            self.sql.insRec("genstr", data=acc)
        self.doLoadLines()

    def doLoadLines(self):
        self.df.clearFrame("C", 0)
        pos = 0
        recs = self.sql.getRec("genstr", where=[("gls_cono", "=",
            self.opts["conum"]), ("gls_strm", "=", self.strm)],
            order="gls_seq")
        for row, rec in enumerate(recs):
            for num, dat in enumerate(rec[3:-1]):
                self.df.loadEntry("C", 0, pos, data=dat)
                pos += 1
                if pos == (self.df.rows[0] * self.df.colq[0]):
                    self.df.scrollScreen(0)
                    pos = pos - self.df.colq[0]
        pos += 1
        self.df.focusField("C", 0, pos)

# vim:set ts=4 sw=4 sts=4 expandtab:
