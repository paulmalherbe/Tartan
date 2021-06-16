"""
SYNOPSIS
    List of Entered Players.

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

import os, time
from TartanClasses import MyFpdf, Sql, TartanDialog
from tartanFunctions import getImage, getModName, doPrinter

class sc3010(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "scpcmp",
            prog=self.__class__.__name__)
        t = time.localtime()
        self.sysdt = time.strftime("%d %B %Y %H:%M:%S", t)
        self.image = os.path.join(self.opts["mf"].rcdic["wrkdir"], "bowls.png")
        if not os.path.exists(self.image):
            getImage("bowls", fle=self.image)
        if not os.path.exists(self.image):
            self.image = None

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("scpcmp",),
            "cols": (
                ("scp_ccod", "", 0, "Cod"),
                ("scp_name", "", 0, "Name", "Y")),
            "where": [("scp_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"I@scp_ccod",0,"Code","",
                "","N",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("scpcmp", cols=["scp_name"],
            where=[("scp_cono", "=", self.opts["conum"]), ("scp_ccod", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.cnam = chk[0]
        self.df.loadEntry(frt, pag, p+1, data=self.cnam)

    def doEnd(self):
        self.df.closeProcess()
        col = ["scm_scod", "scm_surname", "scm_names", "scm_gender",
            "scc_name", "scm_phone"]
        whr = [
            ("sce_cono", "=", self.opts["conum"]),
            ("sce_ccod", "=", self.ccod),
            ("scm_cono=sce_cono",),
            ("scm_scod=sce_scod",),
            ("scc_club=scm_club",)]
        recs = self.sql.getRec(tables=["scpent", "scpmem", "scpclb"], cols=col,
            where=whr, order="scm_surname")
        if recs:
            self.fpdf = MyFpdf(auto=True, name="sc3010", head=90)
            self.fpdf.header = self.doHead
            self.fpdf.add_page()
            cwth = self.fpdf.cwth
            for num, rec in enumerate(recs):
                self.fpdf.drawText(txt="%6s" % rec[0], w=cwth*7, h=5, ln=0)
                nm = rec[1].strip() + ", %s" % rec[2].split()[0]
                self.fpdf.drawText(txt=nm, w=cwth*31, h=5, ln=0)
                self.fpdf.drawText(txt=rec[3], w=cwth*2, h=5, ln=0)
                self.fpdf.drawText(txt=rec[4], w=cwth*31, h=5, ln=0)
                ph = rec[5].replace(" ", "").strip()
                self.fpdf.drawText(txt=ph, w=cwth*16, h=5, ln=1)
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], pdfnam=pdfnam,
                repprt=self.df.repprt,
                repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doHead(self):
        if os.path.isfile(self.image):
            self.fpdf.image(self.image, 10, 10, 15, 11)
        self.fpdf.set_font("Arial","B",15)
        self.fpdf.cell(20)
        self.fpdf.cell(0,10,"Players Entered in the %s" % self.cnam,1,0,"C")
        self.fpdf.ln(20)
        self.fpdf.setFont(style="B")
        self.fpdf.cell(0, 5, "%-6s %-30s %-1s %-30s %-15s" % \
            ("Reg-No", "Name", "G", "Club", "Contact"), "B")
        self.fpdf.ln(5)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
