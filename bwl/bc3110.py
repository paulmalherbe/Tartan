"""
SYNOPSIS
    Player's Contact Request Forms.

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

from TartanClasses import MyFpdf, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter

class bc3110(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwlent", "bwltab"],
            prog=self.__class__.__name__)

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","N",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlcmp", cols=["bcm_name"],
            where=[("bcm_cono", "=", self.opts["conum"]), ("bcm_code", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])

    def doEnd(self):
        self.df.closeProcess()
        col = ["btb_surname", "btb_names", "btb_mail", "btb_cell"]
        whr = [
            ("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod),
            ("btb_cono=bce_cono",),
            ("btb_tab=bce_scod",)]
        recs = self.sql.getRec(tables=["bwlent", "bwltab"], cols=col,
            where=whr, order="btb_surname")
        if recs:
            fpdf = MyFpdf(name=self.__class__.__name__, head=90, foot=False)
            for num, rec in enumerate(recs):
                if not num % 5:
                    fpdf.add_page()
                fpdf.drawText("Contact Details", h=12, align="C",
                    font=["courier", "B", 24], border="TLRB", fill=1)
                fpdf.drawText("Name", w=50, h=10, fill=1, ln=0,
                    font=["courier", "B", 18], border="TLRB")
                if rec[1]:
                    nam = "%s, %s" % (rec[0].upper(), rec[1].split()[0].upper())
                else:
                    nam = rec[0].upper()
                fpdf.drawText(nam, h=10, border="TLRB")
                fpdf.drawText("Email", w=50, h=10, border="TLRB", fill=1, ln=0)
                fpdf.drawText(rec[2], h=10, border="TLRB")
                fpdf.drawText("Phone", w=50, h=10, border="TLRB", fill=1, ln=0)
                fpdf.drawText(rec[3], h=10, border="TLRB")
                fpdf.drawText()
                fpdf.drawText()
                fpdf.drawText()
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], pdfnam=pdfnam,
                    repprt=self.df.repprt)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
