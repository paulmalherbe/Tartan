"""
SYNOPSIS
    Book Library List.

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

import os, requests, time
from TartanClasses import CCD, MyFpdf, SplashScreen, Sql, TartanDialog
from tartanFunctions import doPrinter, getImage, getModName, showError

class bs3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bksmst", "bksaut", "bksown"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.curdt = time.strftime("%Y-%m", t)
        self.image = os.path.join(self.opts["mf"].rcdic["wrkdir"], "books.png")
        if not os.path.exists(self.image):
            getImage("books", fle=self.image)
        if not os.path.exists(self.image):
            self.image = None
        return True

    def mainProcess(self):
        lst = {
            "stype": "R",
            "tables": ("bksmst",),
            "cols": (("bmf_mnth", "", 0, "Month"),),
            "where": [("bmf_cono", "=", self.opts["conum"])],
            "group": "bmf_mnth",
            "order": "bmf_mnth"}
        r1s = (("All","A"), ("Current","C"), ("Removed","R"))
        r2s = (("Title","T"), ("Date","D"),("Author","A"),("Owner","O"))
        fld = (
            (("T",0,0,0),"ID2",7,"Last Meeting","",
                "","N",self.doLast,lst,None,("efld",)),
            (("T",0,1,0),("IRB",r1s),0,"Status","",
                "A","N",self.doStatus,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Order","",
                "T","N",self.doOrder,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doLast(self, frt, pag, r, c, p, i, w):
        self.last = w
        self.new = False

    def doStatus(self, frt, pag, r, c, p, i, w):
        self.status = w

    def doOrder(self, frt, pag, r, c, p, i, w):
        self.order = w

    def doEnd(self):
        self.df.closeProcess()
        if self.df.repeml[1] == "Y":
            if not self.df.repeml[2]:
                owns = self.sql.getRec("bksown", cols=["bof_mail"],
                    where=[("bof_mail", "<>", ""), ("bof_stat", "=", "C")])
                adds = None
                for own in owns:
                    if not adds:
                        adds = own[0]
                    else:
                        adds = "%s,%s" % (adds, own[0])
                self.df.repeml[2] = adds
            if not self.df.repeml[3]:
                self.df.repeml[3] = """Dear Member

Attached please find the latest list of books.

All books which came onto the list at the last meeting are highlighted and, if available, a precis will be printed at the end.

Thanks and Regards.
"""
        tab = ["bksmst", "bksaut", "bksown"]
        col = ["bmf_stat", "bmf_titl", "bmf_code", "baf_snam", "baf_fnam",
            "bmf_mnth", "bof_fnam", "bof_snam"]
        odr = ""
        if self.status == "C":
            whr = [("bmf_stat", "=", "C")]
        elif self.status == "R":
            whr = [("bmf_stat", "=", "X")]
        else:
            whr = []
            odr = "bmf_stat"
        whr.extend([
            ("baf_code=bmf_auth",),
            ("bof_code=bmf_ownr",)])
        if self.order == "T":
            if odr:
                odr = "%s, bmf_titl" % odr
            else:
                odr = "bmf_titl"
        elif self.order == "D":
            if odr:
                odr = "%s, bmf_mnth, bmf_titl" % odr
            else:
                odr = "bmf_mnth, bmf_titl"
        elif self.order == "A":
            if odr:
                odr = "%s, baf_snam, baf_fnam, bmf_titl" % odr
            else:
                odr = "baf_snam, baf_fnam, bmf_titl"
        elif self.order == "O":
            if odr:
                odr = "%s, bmf_ownr, bmf_titl" % odr
            else:
                odr = "bmf_ownr, bmf_titl"
        recs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
                "No Records Selected")
            self.opts["mf"].closeLoop()
            return
        self.fpdf = MyFpdf(name="bs3010", head=90, auto=True)
        self.fpdf.header = self.pageHeading
        self.stat = recs[0][0]
        self.fpdf.add_page()
        new = []
        for rec in recs:
            stat = CCD(rec[0], "UA", 1).disp
            if stat != self.stat:
                self.stat = stat
                self.fpdf.add_page()
            titl = CCD(rec[1], "NA", 30).disp
            code = CCD(rec[2], "UI", 4).disp
            auth = CCD("%s, %s" % (rec[3], rec[4]), "NA", 30).disp
            mnth = CCD(rec[5], "D2", 7).disp
            ownr = CCD("%s %s" % (rec[6], rec[7][0]), "NA", 12).disp
            if rec[5] < self.last:
                fill = 0
            else:
                new.append([auth, titl])
                fill = 1
            self.fpdf.drawText("%1s %30s %4s %30s %7s %10s" % (stat, titl,
                code, auth, mnth, ownr), h=5, fill=fill)
        if new:
            sp = SplashScreen(self.opts["mf"].body,
                "Preparing Summary of New Books ... Please Wait")
            self.new = True
            self.fpdf.add_page()
            for book in new:
                try:
                    if self.fpdf.get_y() > 260:
                        self.fpdf.add_page()
                    desc = self.getDesc(book)
                    if desc:
                        w = self.fpdf.cwth * 9
                        desc = desc.rstrip().encode("latin-1",
                            "ignore").decode("latin-1", "ignore")
                        self.fpdf.drawText(w=w, txt="Title: ", font="B", ln=0)
                        self.fpdf.drawText(txt=book[1].rstrip(), font="I")
                        self.fpdf.drawText(w=w, txt="Author: ", font="B", ln=0)
                        self.fpdf.drawText(txt=book[0].rstrip(), font="I")
                        self.fpdf.drawText(w=w, txt="Details: ", font="B", ln=0)
                        self.fpdf.drawText(txt=desc, font="I", ctyp="M")
                        if book != new[-1]:
                            self.fpdf.drawText()
                except:
                    pass
            sp.closeSplash()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        head = "Book List as at %s" % (self.curdt)
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header=head, repprt=self.df.repprt, repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def pageHeading(self, new=False):
        self.fpdf.setFont("Arial", "B", 15)
        x = self.fpdf.get_x()
        if self.image:
            self.fpdf.image(self.image, 11, 10, 15, 20)
            self.fpdf.image(self.image, 185, 10, 15, 20)
            self.fpdf.cell(20)
        self.fpdf.set_x(x)
        self.fpdf.cell(0, 10, self.opts["conam"],"TLR",1,"C")
        if self.new:
            txt = "Summary of New Books"
        elif self.stat == "C":
            txt = "Current Books as at %s" % self.curdt
        else:
            txt = "Removed Books as at %s" % self.curdt
        self.fpdf.cell(0, 10, txt, "LRB", 1, "C")
        self.fpdf.ln(8)
        self.fpdf.setFont(style="B")
        if not self.new:
            self.fpdf.cell(0, 5, "%-1s %-30s %-4s %-30s %-7s %-12s" % ("S",
                "Title", "Code", "Author", "Mth-Rec", "Owner"), "B")
        self.fpdf.ln(5)

    def getDesc(self, book):
        auth = book[0].strip().lower()
        titl = book[1].strip().lower().replace(",", "")
        if titl[:4] == "the ":
            titl = titl[4:]
        elif titl[-4:] == " the":
            titl = titl[:-4]
        get = requests.get("https://www.googleapis.com/books/v1/volumes?q="\
            "{intitle:'%s'+inauthor:'%s'" % (titl, auth), timeout=5)
        if get.status_code == 200 and get.json()["totalItems"]:
            ok = False
            for item in get.json()["items"]:
                tita = titl.lower().\
                    replace("the ","").replace(", the", "")
                titb = item["volumeInfo"]["title"].lower().\
                    replace("the ","").replace(", the", "")
                if titb.count(tita):
                    if "description" in item["volumeInfo"]:
                        ok = True
                        break
            if ok:
                return item["volumeInfo"]["description"]

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
