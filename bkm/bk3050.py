"""
SYNOPSIS
    Bookings Ledger Print Labels. L7159

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

from TartanClasses import GetCtl, TartanLabel, ProgressBar, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName, getSingleRecords, showError
from tartanWork import labels

class bk3050(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "bkmcon",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Print Contacts Labels (%s)" % self.__class__.__name__)
        lab = {
            "stype": "C",
            "head": ("Codes",),
            "data": list(labels.keys())}
        r1s = (("Yes","Y"),("Singles","S"))
        r2s = (("Number","N"),("Name","M"),("Postal Code","P"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Whole File","",
                "S","Y",self.doWhole,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,2,0),"IUA",5,"Avery A4 Code","",
                "L7159","Y",self.doAvery,lab,None,("in",labels)),
            (("T",0,3,0),"IUI",2,"First Label Row","",
                1,"Y",self.doRow,None,None,("notzero",)),
            (("T",0,4,0),"IUI",2,"First Label Column","",
                1,"Y",self.doCol,None,None,("notzero",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"))

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w

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
        tab = ["bkmcon"]
        whr = [("bkc_cono", "=", self.opts["conum"])]
        if self.sort == "N":
            odr = "bkc_ccode"
        elif self.sort == "M":
            odr = "bkc_name"
        else:
            odr = "bkc_pcod"
        if self.whole == "S":
            recs = getSingleRecords(self.opts["mf"], "bkmcon",
                ("bkc_ccode", "bkc_name"), where=whr, order=odr)
        else:
            recs = self.sql.getRec(tables=tab, where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Error", "No Accounts Selected")
        else:
            self.fpdf = TartanLabel(self.label, posY=self.srow, posX=self.scol)
            self.fpdf.add_page()
            p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
            for num, dat in enumerate(recs):
                p.displayProgress(num)
                if p.quit:
                    break
                self.doProcess(dat)
            p.closeProgress()
            if self.fpdf.page and not p.quit:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt)
        self.closeProcess()

    def doProcess(self, dat):
        bkc = self.sql.bkmcon_col
        lab = "%50s" % dat[bkc.index("bkc_ccode")]
        lab = "%s\n%s" % (lab, dat[bkc.index("bkc_title")])
        nam = dat[bkc.index("bkc_names")].split()
        for n in nam:
            lab = "%s %s" % (lab, n[0].capitalize())
        lab = "%s %s" % (lab, dat[bkc.index("bkc_sname")].strip())
        txt = dat[bkc.index("bkc_addr1")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = dat[bkc.index("bkc_addr2")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = dat[bkc.index("bkc_addr3")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        txt = dat[bkc.index("bkc_pcode")]
        if txt:
            lab = "%s\n%s" % (lab, txt)
        self.fpdf.add_label(lab)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
