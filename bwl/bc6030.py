"""
SYNOPSIS
    Bowls Competition Orize Envelopes.

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

from TartanClasses import MyFpdf, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName

class bc6030:
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwltyp"], prog=__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Bowls Prize Envelopes")
        cde = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name")),
            "where": [("bcm_cono", "=", self.opts["conum"])],
            "order": "bcm_code"}
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","N",self.doComp,cde,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUI",1,"Groups","Number of Groups",
                0,"N",self.doGrps,None,None,("notzero",)),
            (("T",0,2,0),"IUI",1,"Prizes","Prizes per Group",
                3,"N",self.doPrzs,None,None,("notzero",)),
            (("T",0,3,0),"IUI",1,"Members","Team Members",
                0,"N",self.doMems,None,None,("notzero",)))
        but = (("Exit", None, self.doExit, 0, ("T",0,1), ("T",0,0)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt, view=("N", "V"))

    def doComp(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec(tables="bwlcmp", where=[("bcm_cono", "=",
            self.opts["conum"]), ("bcm_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Competition"
        self.comp = w
        self.name = acc[self.sql.bwlcmp_col.index("bcm_name")]
        self.type = acc[self.sql.bwlcmp_col.index("bcm_type")]
        self.df.loadEntry(frt, pag, p+1, data=self.name)
        typ = self.sql.getRec(tables="bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", self.type)], limit=1)
        self.tsiz = typ[self.sql.bwltyp_col.index("bct_tsize")]
        grps = typ[self.sql.bwltyp_col.index("bct_groups")]
        if grps == "N":
            self.grps = 1
            self.df.loadEntry(frt, pag, p+2, data=self.grps)
            return "sk2"

    def doGrps(self, frt, pag, r, c, p, i, w):
        self.grps = w

    def doPrzs(self, frt, pag, r, c, p, i, w):
        self.przs = w
        self.df.loadEntry(frt, pag, p+1, data=self.tsiz)

    def doMems(self, frt, pag, r, c, p, i, w):
        self.mems = w

    def doEnd(self):
        self.df.closeProcess()
        grps = ("A", "B", "C")
        poss = ("First Place", "Second Place", "Third Place")
        if self.mems == 2:
            mems = ("Skip", "Lead")
        elif self.mems == 3:
            mems = ("Skip", "Second", "Lead")
        elif self.mems == 4:
            mems = ("Skip", "Third", "Second", "Lead")
        font=("Courier", "B", 24)
        fpdf = MyFpdf(name=__name__, orientation="P", fmat="A4", head=80,
            foot=False)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        for x in range(self.grps):
            for y in range(self.przs):
                for z in range(self.mems):
                    fpdf.add_page()
                    fpdf.drawText(x=0, y=30, align="C", txt=self.name,
                        font=font)
                    fpdf.drawText(x=0, y=45, align="C", txt="Group %s - %s" %
                        (grps[x], poss[y]), font=font)
                    if self.mems > 1:
                        fpdf.drawText(x=0, y=60, align="C", txt=mems[z],
                            font=font)
        fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
            pdfnam=pdfnam, header="Envelopes", repprt=self.df.repprt)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
