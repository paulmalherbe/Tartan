"""
SYNOPSIS
    Members Ledger Print Labels.

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

from TartanClasses import GetCtl, TartanLabel, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName, showError
from tartanWork import labels

class ml3110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ("memctc", "memmst", "memadd"),
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Print Member's Labels (%s)" % self.__class__.__name__)
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [],
            "order": "mcc_code",
            "size": (400, 600)}
        lab = {
            "stype": "C",
            "head": ("Codes",),
            "data": list(labels.keys())}
        r1s = (
            ("All", "Z"),
            ("Active", "A"),
            ("Deceased", "D"),
            ("Inactive", "I"),
            ("Resigned", "R"),
            ("Suspended", "S"),
            ("Defaulted", "X"))
        r2s = (
            ("All", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        r3s = (("Number","N"),("Name","M"),("Postal Code","P"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Status","",
                "A","Y",self.doStat,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Category","",
                "A","Y",self.doCat,None,None,None),
            (("T",0,2,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None),
            (("T",0,2,0),"ONA",30,""),
            (("T",0,3,0),("IRB",r3s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,4,0),"IUA",5,"Avery A4 Code","",
                "L7159","Y",self.doAvery,lab,None,("in",labels)),
            (("T",0,5,0),"IUI",2,"First Label Row","",
                1,"Y",self.doRow,None,None,("notzero",)),
            (("T",0,6,0),"IUI",2,"First Label Column","",
                1,"Y",self.doCol,None,None,("notzero",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"))

    def doStat(self, frt, pag, r, c, p, i, w):
        self.state = w

    def doCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.cat = ""
            self.cod = ""
            self.df.loadEntry(frt, pag, p+2,
                data="All Categories and Sections")
            return "sk1"
        self.cat = w
        self.whr = [
            ("mcc_cono", "=", self.opts["conum"]),
            ("mcc_type", "=", self.cat)]

    def doCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("memctc", cols=["mcc_desc"],
            where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
            self.cat), ("mcc_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Category Code"
        self.cod = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doAvery(self, frt, pag, r, c, p, i, w):
        self.label = w

    def doRow(self, frt, pag, r, c, p, i, w):
        if w > labels[self.label]["NY"]:
            return "Out of Range"
        self.srow = w

    def doCol(self, frt, pag, r, c, p, i, w):
        if w > labels[self.label]["NX"]:
            return "Out of Range"
        self.scol = w

    def doEnd(self):
        self.df.closeProcess()
        self.prnt = False
        whr = [("mlm_cono", "=", self.opts["conum"])]
        if self.state != "Z":
            if self.state == "R" and self.cat:
                whr.append(("mlm_state", "in", ("A", "R")))
            else:
                whr.append(("mlm_state", "=", self.state))
        tab = ["memmst"]
        if self.cat:
            tab.append("memcat")
            whr.append(("mlc_cono=mlm_cono",))
            whr.append(("mlc_memno=mlm_memno",))
            whr.append(("mlc_type", "=", self.cat))
            if self.cod:
                whr.append(("mlc_code", "=", self.cod))
            if self.state == "A":
                whr.append(("mlc_end", "=", 0))
            grp = self.sql.memmst_col[0]
            for c in self.sql.memmst_col[1:]:
                grp = "%s, %s" % (grp, c)
        else:
            grp = None
        if self.sort == "N":
            odr = "mlm_memno"
        elif self.sort == "M":
            odr = "mlm_name"
        else:
            odr = "mlm_pcod"
        rec = self.sql.getRec(tables=tab, cols=self.sql.memmst_col, where=whr,
            group=grp, order=odr)
        if not rec:
            showError(self.opts["mf"].body, "Error", "No Accounts Selected")
        else:
            self.fpdf = TartanLabel(self.label, posY=self.srow, posX=self.scol)
            self.fpdf.add_page()
            p = ProgressBar(self.opts["mf"].body, mxs=len(rec), esc=True)
            for num, dat in enumerate(rec):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(dat)
            p.closeProgress()
            if self.fpdf.page and not p.quit:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt)
        self.closeProcess()

    def doProcess(self, mlm):
        dmm = self.sql.memmst_col
        dma = self.sql.memadd_col
        memno = mlm[dmm.index("mlm_memno")]
        add = self.sql.getRec("memadd", where=[("mla_cono", "=",
            self.opts["conum"]), ("mla_memno", "=", memno), ("mla_type", "=",
            "P")], limit=1)
        if not add:
            return
        tit = mlm[dmm.index("mlm_title")].strip()
        sur = mlm[dmm.index("mlm_surname")].strip()
        nam = mlm[dmm.index("mlm_names")].strip()
        ini = ""
        for n, d in enumerate(nam.split()):
            if n < 3:
                if not ini:
                    ini = d[0].upper().strip()
                else:
                    ini = "%s %s" % (ini, d[0].upper().strip())
        lab = "%50s" % memno
        lab = "%s\n%s %s %s" % (lab, tit, ini, sur)
        txt = add[dma.index("mla_add1")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = add[dma.index("mla_add2")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = add[dma.index("mla_add3")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = add[dma.index("mla_city")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = add[dma.index("mla_country")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = add[dma.index("mla_code")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        self.fpdf.add_label(lab)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
