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
from TartanClasses import CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import getImage, getModName, doPrinter

class bc3070(object):
    def __init__(self, **opts):
        self.opts = opts
        self.setVariables()
        self.mainProcess()
        self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwlent", "bwltab"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.fromad = bwlctl["ctb_emadd"]
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
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        r1s = (("Alphabtic", "A"), ("Numeric", "N"))
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"","",
                "","N",self.doCmpCod,com,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),("IRB",r1s),0,"Order","",
                "A","N",self.doCmpOrd,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("Y","Y"))

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("bwlcmp", cols=["bcm_name"],
            where=[("bcm_cono", "=", self.opts["conum"]), ("bcm_code", "=",
            w)], limit=1)
        if not chk:
            return "Invalid Competition Code"
        self.ccod = w
        self.cnam = chk[0]
        self.df.loadEntry(frt, pag, p+1, data=self.cnam)

    def doCmpOrd(self, frt, pag, r, c, p, i, w):
        self.cord = w

    def doEnd(self):
        self.df.closeProcess()
        col = ["btb_tab", "btb_surname", "btb_names", "btb_cell",
            "btb_mail", "bce_tcod"]
        whr = [
            ("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod),
            ("btb_cono=bce_cono",),
            ("btb_tab=bce_scod",)]
        if self.cord == "A":
            odr = "btb_surname"
        else:
            odr = "btb_tab"
        recs = self.sql.getRec(tables=["bwlent", "bwltab"], cols=col,
            where=whr, order=odr)
        if recs:
            self.fpdf = MyFpdf(auto=True, foot=True)
            self.fpdf.header = self.doHead
            self.fpdf.add_page()
            self.fpdf.set_font("Courier","",9)
            cwth = self.fpdf.get_string_width("X")
            for num, rec in enumerate(recs):
                tab = CCD(rec[0], "UI", 6).disp
                self.fpdf.drawText(txt=tab, w=cwth*7, h=5, ln=0)
                nm = rec[1].strip()
                if rec[2]:
                    nm += ", %s" % rec[2].split()[0].upper()
                self.fpdf.drawText(txt=nm, w=cwth*31, h=5, ln=0)
                self.fpdf.drawText(txt=rec[3], w=cwth*16, h=5, ln=0)
                self.fpdf.drawText(txt=rec[4], w=cwth*41, h=5, ln=0)
                self.fpdf.drawText(txt=rec[5], w=cwth*2, h=5, ln=1)
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            head = "%s - Entered Teams" % self.cnam
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=head, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doHead(self):
        if os.path.isfile(self.image):
            self.fpdf.image(self.image, 10, 10, 15, 11)
        self.fpdf.set_font("Arial","B",15)
        self.fpdf.cell(20)
        self.fpdf.cell(0,10,"Players Entered in the %s" % self.cnam,1,0,"C")
        self.fpdf.ln(20)
        self.fpdf.set_font("Courier","B",9)
        self.fpdf.cell(0, 5, "%-6s %-30s %-15s %-40s %1s" % \
            ("Number", "Name", "Mobile", "Email", "T"), "B")
        self.fpdf.ln(5)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
