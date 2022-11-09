"""
SYNOPSIS
    Bookings Deposits Listing.

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

import time
from operator import itemgetter
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName

class bk3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bkmmst", "bkmcon", "bkmtrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        mc = GetCtl(self.opts["mf"])
        bkmctl = mc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.fromad = bkmctl["cbk_emadd"]
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        return True

    def mainProcess(self):
        tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Deposits Due")
        r1s = (("No","N"), ("Yes","Y"))
        r2s = (("Arrival","A"), ("Due","D"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Expired Only","",
                "N","Y",self.doExpired,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Order","",
                "A","Y",self.doOrder,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        if "args" in self.opts:
            tops = self.opts["args"]
        else:
            tops = False
        self.df = TartanDialog(self.opts["mf"], tops=tops, title=tit,
            eflds=fld, tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doExpired(self, frt, pag, r, c, p, i, w):
        self.expired = w

    def doOrder(self, frt, pag, r, c, p, i, w):
        self.order = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["bkmmst"]
        col = [
            "bkm_number",
            "bkm_group",
            "bkm_ccode",
            "bkm_arrive",
            "bkm_depart",
            "bkm_stddep",
            "bkm_stddte",
            "bkm_grpdep",
            "bkm_grpdte",
            "bkm_state"]
        whr = [
            ("bkm_cono", "=", self.opts["conum"]),
            ("bkm_state", "in", ("C", "Q"))]
        if self.order == "A":
            odr = "bkm_arrive, bkm_ccode"
        else:
            odr = "bkm_stddte, bkm_grpdte, bkm_ccode"
        recs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=80, auto=True)
        self.fpdf.header = self.pageHeading
        self.fpdf.add_page()
        newrec = []
        for rec in recs:
            if not rec[5] and not rec[7]:
                continue
            num = CCD(rec[0], "UI", 6)
            trn = self.sql.getRec("bkmtrn", where=[("bkt_cono", "=",
                self.opts["conum"]), ("bkt_number", "=", num.work)])
            inv = False
            bal = 0.0
            for tr in trn:
                typ = tr[self.sql.bkmtrn_col.index("bkt_type")]
                amt = tr[self.sql.bkmtrn_col.index("bkt_tramt")]
                bal = float(ASD(bal) + ASD(amt))
                if typ == 2:
                    inv = True
            if inv:
                continue
            dp1 = float(ASD(rec[5]) + ASD(bal))
            dt1 = rec[6]
            if dp1 > 0:
                dp2 = rec[7]
                dt2 = rec[8]
            elif rec[7]:
                dp2 = float(ASD(rec[7]) + ASD(dp1))
                dt2 = rec[8]
                dp1 = 0
            else:
                dp1 = 0
                dp2 = 0
                dt2 = 0
            if self.expired == "Y":
                if dp1 and dt1 > self.sysdtw:
                    continue
                if not dp1 and dp2 and dt2 > self.sysdtw:
                    continue
            elif dp1 <= 0 and dp2 <= 0:
                continue
            if dp1 and dp1 > 0:
                b = CCD(dt1, "D1", 10).disp
                if dp2:
                    b = "%s\n%s" % (b, CCD(dt2, "D1", 10).disp)
            elif dp2 and dp2 > 0:
                b = CCD(dt2, "D1", 10).disp
            else:
                continue
            con = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
                self.opts["conum"]), ("bkc_ccode", "=", rec[2])], limit=1)
            snam = con[self.sql.bkmcon_col.index("bkc_sname")]
            fnam = con[self.sql.bkmcon_col.index("bkc_names")]
            if fnam:
                c = "%s %s" % (fnam.split()[0], snam)
            else:
                c = snam
            l = 8
            if rec[1]:
                c = "%s\n%s" % (c, rec[1])
                l = 16
            d = CCD(rec[3], "D1", 10).disp
            e = CCD(rec[4], "D1", 10).disp
            if dp1:
                f = CCD(dp1, "UD", 10.2).disp
                if dp2:
                    f = "%s\n%s" % (f, CCD(dp2, "UD", 10.2).disp)
                    l = 16
            else:
                f = CCD(dp2, "UD", 10.2).disp
            newrec.append([num.disp, b, c, d, e, f])
        if newrec:
            if self.order == "D":
                newrec = sorted(newrec, key=itemgetter(1))
            for rec in newrec:
                if self.fpdf.get_y() + l > 260:
                    self.fpdf.add_page()
                self.printLine(rec[0], rec[1], rec[2], rec[3], rec[4], rec[5])
        if self.fpdf.page:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    header=self.head, pdfnam=pdfnam, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def pageHeading(self):
        cd1 = "%-30s" % self.opts["conam"]
        self.fpdf.drawText(cd1, x=7, font=["courier", "B", 24])
        self.fpdf.drawText(font=["courier", "B", 14])
        if self.expired == "N":
            cd2 = "Deposits Due Report"
        else:
            cd2 = "Deposits Expired Report"
        self.head = "%s - %s" % (cd1, cd2)
        self.fpdf.drawText(cd2, x=7, font=["courier", "B", 16])
        self.fpdf.drawText(font=["courier", "B", 14])
        self.printLine("Number", " Due-Date ", "%-20s" % "Name & Group",
            "  Arrive  ", "  Depart  ", "    Amount", fill=1)

    def printLine(self, a, b, c, d, e, f, fill=0):
        ft = ["courier", "B", 13]
        self.fpdf.set_font(ft[0], ft[1], ft[2])
        c, cq = self.getLines(c, self.fpdf.get_string_width("X"*21))
        f, fq = self.getLines(f, self.fpdf.get_string_width("X"*11))
        if cq > fq:
            ch = 8
            h = cq * 8
            fh = int(h / fq)
        elif fq > cq:
            fh = 8
            h = fq * 8
            ch = int(h / cq)
        else:
            h = cq * 8
            ch = fh = 8
        if cq > 1 or fq > 1:
            ctyp = "M"
        else:
            ctyp = "S"
        # Booking number
        x = 7
        y = self.fpdf.get_y()
        w = self.fpdf.get_string_width("X"*7)
        self.fpdf.drawText(a, x=x, y=y, w=w, h=h, border="TLB",
            fill=fill, ctyp=ctyp, font=ft)
        # Name and group
        x += w
        w = self.fpdf.get_string_width("X"*21)
        self.fpdf.drawText(c, x=x, y=y, w=w, h=ch, border="TLB",
            fill=fill, ctyp=ctyp, font=ft)
        # Arrival date
        x += w
        w = self.fpdf.get_string_width("X"*11)
        self.fpdf.drawText(d, x=x, y=y, w=w, h=h, border="TLB",
            fill=fill, ctyp=ctyp, font=ft)
        # Departure date
        x += w
        w = self.fpdf.get_string_width("X"*11)
        self.fpdf.drawText(e, x=x, y=y, w=w, h=h, border="TLB",
            fill=fill, ctyp=ctyp, font=ft)
        # Deposit due date
        x += w
        w = self.fpdf.get_string_width("X"*11)
        self.fpdf.drawText(b, x=x, y=y, w=0, h=fh, border="TLB",
            fill=fill, ctyp=ctyp, font=ft)
        # Deposit amount
        x += w
        w = self.fpdf.get_string_width("X"*11)
        self.fpdf.drawText(f, x=x, y=y, w=w, h=fh, border="TLRB",
            fill=fill, ctyp=ctyp, font=ft)

    def getLines(self, t, w):
        tmp = t.split("\n")
        nam = self.fpdf.multi_cell(w, 8, tmp[0], split_only=True)
        t = nam[0]
        q = 1
        for n in nam[1:]:
            t = "%s\n%s" % (t, n)
            q += 1
        if len(tmp) > 1:
            nam = self.fpdf.multi_cell(w, 8, tmp[1], split_only=True)
            for n in nam:
                t = "%s\n%s" % (t, n)
                q += 1
        return t, q

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
