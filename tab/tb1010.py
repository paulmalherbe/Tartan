"""
SYNOPSIS
    Tartan Systems Table Creation GUI.

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

import json, os
from TartanClasses import RepPrt, Sql, TartanDialog
from tartanFunctions import askQuestion, copyList, makeArray, getPrgPath
from tartanWork import dattyp, tabdic

class tb1010(object):
    def __init__(self, **opts):
        self.opts = opts
        self.opts["mf"].dbm.openDbase()
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ftable", "ffield"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def doProcess(self):
        fft = {
            "stype": "R",
            "tables": ("ftable",),
            "cols": (
                ("ft_tabl", "", 0, "Table"),
                ("ft_desc", "", 0, "Description", "Y")),
            "where": [("ft_seq", "=", 1)]}
        ffl = {
            "stype": "R",
            "tables": ("ffield",),
            "cols": (
                ("ff_seq", "", 0, "Seq"),
                ("ff_name", "", 0, "Name"),
                ("ff_desc", "", 0, "Description", "Y"),
                ("ff_type", "", 0, "Tp"),
                ("ff_size", "", 0, "Size")),
            "whera": (("T", "ff_tabl", 0, 0),),
            "index": 0}
        ffi = {
            "stype": "R",
            "tables": ("ftable",),
            "cols": (
                ("ft_seq", "", 0, "Seq"),
                ("ft_type", "", 0, "T"),
                ("ft_key0", "", 0, "Column-1"),
                ("ft_key1", "", 0, "Column-2"),
                ("ft_key2", "", 0, "Column-3"),
                ("ft_key3", "", 0, "Column-4"),
                ("ft_key4", "", 0, "Column-5"),
                ("ft_key4", "", 0, "Column-6"),
                ("ft_key4", "", 0, "Column-7")),
            "whera": (("T", "ft_tabl", 0, 0),),
            "comnd": self.doIdxCmd}
        typ = {
            "stype": "C",
            "titl": "Select the Required Data Type",
            "head": ("Cd", "Description"),
            "data": dattyp,
            "index": 0}
        valtyp = []
        for t in dattyp:
            valtyp.append(t[0])
        self.col = {
            "stype": "C",
            "titl": "Select the Required Column",
            "head": ("Table", "Description"),
            "data": []}
        fld = [
            (("T",0,0,0),"INA",20,"Table ","Table Name",
                "","Y",self.doTable,fft,None,("notin",("","ftable","ffield"))),
            (("T",0,0,0),"INA",30," Description ","Description",
                "","N",self.doDesc,None,None,None),
            (("C",1,0,0),"IUI",3,"Seq","Column Sequence",
                "i","N",self.doColSeq,ffl,None,("between",0,999)),
            (("C",1,0,1),"INA",20,"Column","Column Name",
                "","N",None,None,None,("notblank",)),
            (("C",1,0,2),"INA",2,"Tp","Data Type",
                "","N",None,typ,None,("in", valtyp)),
            (("C",1,0,3),"IUD",6.1,"Size","Field Size",
                "","N",None,None,None,("notzero",)),
            (("C",1,0,4),"INA",30,"Description","",
                "","N",None,None,None,None),
            (("C",1,0,5),"INA",30,"Heading","Report Heading",
                "","N",None,None,None,("notblank",)),
            (("C",2,0,0),"IUI",1,"S","Sequence",
                "i","N",self.doIdxSeq,ffi,None,("efld",)),
            (("C",2,0,1),"IUA",1,"T","Type (U/N)",
                "","N",None,None,None,("in", ("U","N"))),
            (("C",2,0,2),"INA",(14,20),"Column-0","",
                "","N",self.doIdxCol,self.col,None,("notblank",)),
            (("C",2,0,3),"INA",(14,20),"Column-1","",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,4),"INA",(14,20),"Column-2","",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,5),"INA",(14,20),"Column-3","",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,6),"INA",(14,20),"Column-4","",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,7),"INA",(5,20),"Col-5","Column-5",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,8),"INA",(5,20),"Col-6","Column-6",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,9),"INA",(5,20),"Col-7","Column-7",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,10),"INA",(5,20),"Col-8","Column-8",
                "","N",self.doIdxCol,self.col,None,("efld",)),
            (("C",2,0,11),"INA",(5,20),"Col-9","Column-9",
                "","N",self.doIdxCol,self.col,None,("efld",))]
        tag = (
            ("Columns",None,("C",1,1),("T",0,1)),
            ("Indexes",None,("C",1,1),("T",0,1)))
        row = (0,15,5)
        tnd = ((self.endTop, "y"),)
        txt = (self.exitTop,)
        cnd = ((None,"n"), (self.endPage1,"y"), (self.endPage2,"y"))
        cxt = (None, self.exitPage1, self.exitPage2)
        but = (
            ("Print",None,self.doPrint,0,("T",0,2),("T",0,1)),
            ("Cancel",None,self.doRestart,0,("T",0,2),("T",0,1)))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag,
            rows=row, tend=tnd, txit=txt, cend=cnd, cxit=cxt, butt=but)

    def doTable(self, frt, pag, r, c, p, i, w):
        self.tab = w
        tab = self.sql.getRec("ftable", cols=["ft_tabl", "ft_desc"],
            where=[("ft_tabl", "=", w), ("ft_seq", "=", 1)], limit=1)
        if not tab:
            self.new = "y"
        else:
            self.new = "n"
            self.df.loadEntry(frt, pag, p + 1, data=tab[1])
            yn = askQuestion(screen=self.opts["mf"].body, head="Table Exists",
                mess="Changing This Record Could Result In Loss of Data, "\
                "Are You Sure You Want to Continue?", default="no")
            if yn == "no":
                return yn

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def endTop(self):
        self.fld = makeArray(6, 100, 1, "S")
        self.idx = makeArray(12, 20, 1, "S")
        if self.new == "n":
            fld = self.sql.getRec("ffield", where=[("ff_tabl", "=",
                self.tab)], order="ff_seq")
            for n, f in enumerate(fld):
                self.fld[n] = f[1:]
            idx = self.sql.getRec("ftable", where=[("ft_tabl", "=",
                self.tab)], order="ft_seq")
            for n, f in enumerate(idx):
                self.idx[n] = f[2:]
                self.idx[n][0] = n
            self.doPopulate("fld")
        else:
            self.df.focusField("C", 1, 1)

    def exitTop(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doColSeq(self, frt, pag, r, c, p, i, w):
        self.colseq = w
        for n, s in enumerate(self.fld[self.colseq][1:]):
            self.df.loadEntry("C", 1, p + n + 1, data=s)

    def endPage1(self):
        pos = int(self.df.col / self.df.colq[1]) - 1
        self.fld[self.colseq] = copyList(self.df.c_work[1][pos])
        self.doPopulate("fld")

    def exitPage1(self):
        self.createCols()
        self.df.selPage("Indexes")
        self.doPopulate("idx")

    def createCols(self):
        self.valcol = []
        self.col["data"] = []
        for fld in self.fld:
            self.valcol.append(fld[1])
            self.col["data"].append([fld[1], fld[4]])

    def doIdxCmd(self, frt, pag, r, c, p, i, w):
        idxseq = int(w[0]) - 1
        self.doIdxSeq(frt, pag, r, c, p, i, idxseq)
        self.df.focusField(frt, pag, c + 1)

    def doIdxSeq(self, frt, pag, r, c, p, i, w):
        self.idxseq = w
        for n, s in enumerate(self.idx[self.idxseq][1:]):
            self.df.loadEntry("C", 2, p + n + 1, data=s)

    def doIdxCol(self, frt, pag, r, c, p, i, w):
        if w and w not in self.valcol:
            return "Invalid Column"

    def endPage2(self):
        pos = int(self.df.col / self.df.colq[2]) - 1
        self.idx[self.idxseq] = copyList(self.df.c_work[2][pos])
        self.doPopulate("idx")

    def exitPage2(self):
        if self.new == "y" and self.df.col == 1:
            self.df.selPage("Columns")
        else:
            if self.tab in tabdic:
                tabdic[self.tab]["fld"] = []
                tabdic[self.tab]["idx"] = []
            else:
                tabdic[self.tab] = {"fld": [], "idx": []}
            for dat in self.fld:
                if dat == [""] * 6:
                    break
                tabdic[self.tab]["fld"].append(dat)
            for num, dat in enumerate(self.idx):
                if dat == [""] * 12:
                    break
                if num == 0:
                    dat.insert(0, self.df.t_work[0][0][1])
                else:
                    dat.insert(0, "")
                dat[1] = num + 1
                fmt = '"%s",%s,"%s"'
                ddd = dat[:3]
                for n, d in enumerate(dat[3:]):
                    if d:
                        fmt += ',"%s"'
                        ddd.append(d)
                fmt += "\n"
                tabdic[self.tab]["idx"].append(ddd)
            fle = os.path.join(getPrgPath(), "stdtab.py")
            outf = open(fle, "w")
            outf.write("""tabdic = {""")
            tabs = list(tabdic.keys())
            tabs.sort()
            for tab in tabs:
                outf.write("""
    "%s": {""" % tab)
                for key in ("fld", "idx"):
                    outf.write("""
        "%s": [""" % key)
                    for fld in tabdic[tab][key]:
                        outf.write("""
            %s""" % json.dumps(fld))
                        if fld == tabdic[tab][key][-1]:
                            outf.write("""]""")
                        else:
                            outf.write(""",""")
                    if key == "fld":
                        outf.write(""",""")
                outf.write("""}""")
                if tab != tabs[-1]:
                    outf.write(""",""")
            outf.write("""}""")
            outf.close()
            self.doRestart()

    def doPopulate(self, ftyp=None):
        if ftyp == "fld":
            self.df.clearFrame("C", 1)
            for num, dat in enumerate(self.fld):
                if dat == [""] * 6:
                    break
                if num > 14:
                    self.df.scrollScreen(1)
                    pos = 14
                else:
                    pos = num
                self.df.focusField("C", 1, (pos * 6) + 1)
                for n, c in enumerate(dat):
                    self.df.loadEntry("C", 1, (pos * 6) + n, data=c)
            self.df.advanceLine(1)
            return
        self.df.clearFrame("C", 2)
        for num, dat in enumerate(self.idx):
            if dat == [""] * 12:
                break
            if num > 4:
                self.df.scrollScreen(2)
                pos = 4
            else:
                pos = num
            self.df.focusField("C", 2, (pos * 12) + 1)
            for n, c in enumerate(dat):
                self.df.loadEntry("C", 2, (pos * 12) + n, data=c)
            self.df.advanceLine(2)
        self.df.focusField("C", 2, self.df.col)

    def doRestart(self):
        self.df.last[0] = [0, 0]
        self.df.selPage("Columns")
        self.df.focusField("T", 0, 1)

    def doPrint(self):
        state = self.df.disableButtonsTags()
        cols = [["ff_seq","UI",3.0,"Seq"],
            ["ff_name","NA",20.0,"Field Name"],
            ["ff_type","NA",2.0,"Tp"],
            ["ff_size","NA",6.1,"Size"],
            ["ff_desc","NA",30.0,"Description"],
            ["ff_head","NA",20.0,"Heading"]]
        whr = [("ff_tabl", "=", self.tab)]
        RepPrt(self.opts["mf"], name=self.tab + "_fld", tables=["ffield"],
            heads=["Table Fields for Table %s" % self.tab,], cols=cols,
            where=whr)
        cols = [["ft_desc","NA",30.0,"Table Description"],
            ["ft_seq","UI",2.0,"Sq"],
            ["ft_type","NA",1.0,"T"],
            ["ft_key0","NA",10.0,"1st-Key"],
            ["ft_key1","NA",10.0,"2nd-Key"],
            ["ft_key2","NA",10.0,"3rd-Key"],
            ["ft_key3","NA",10.0,"4th-Key"],
            ["ft_key4","NA",10.0,"5th-Key"],
            ["ft_key5","NA",10.0,"6th-Key"],
            ["ft_key6","NA",10.0,"7th-Key"],
            ["ft_key7","NA",10.0,"8th-Key"],
            ["ft_key8","NA",10.0,"9th-Key"],
            ["ft_key9","NA",10.0,"10th-Key"]]
        whr = [("ft_tabl", "=", self.tab)]
        RepPrt(self.opts["mf"], name=self.tab + "_idx", tables=["ftable"],
            heads=["Table Keys for Table %s" % self.tab,], cols=cols,
            where=whr)
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

# vim:set ts=4 sw=4 sts=4 expandtab:
