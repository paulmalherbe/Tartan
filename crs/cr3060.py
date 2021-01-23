"""
SYNOPSIS
    Creditors Ledger Master Listing.

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

import time
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import getModName, doPrinter, showError

class cr3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "crsmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Master Listing (%s)" % self.__class__.__name__)
        r1s = (("Number", "N"), ("Name", "M"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Manager", "M"), ("Accounts", "A"), ("Orders", "O"))
        r4s = (("Yes", "Y"), ("No", "N"), ("Only", "O"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Use Full Address","",
                "N","Y",self.doAddress,None,None,None),
            (("T",0,2,0),("IRB",r3s),0,"Contact Details","",
                "M","Y",self.doContact,None,None,None),
            (("T",0,3,0),("IRB",r4s),0,"Include Redundant","",
                "N","Y",self.doRedu,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doAddress(self, frt, pag, r, c, p, i, w):
        self.address = w

    def doContact(self, frt, pag, r, c, p, i, w):
        self.condet = w

    def doRedu(self, frt, pag, r, c, p, i, w):
        self.redu = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("crm_cono", "=", self.opts["conum"])]
        if self.redu == "N":
            whr.append(("crm_stat", "<>", "X"))
        elif self.redu == "O":
            whr.append(("crm_stat", "=", "X"))
        if self.sort == "N":
            odr = "crm_acno"
        else:
            odr = "crm_name"
        recs = self.sql.getRec("crsmst", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = ("%03u %-30s %128s %10s" % \
            (self.opts["conum"], self.opts["conam"], self.sysdttm,
                self.__class__.__name__))
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pgnum = 0
        self.pglin = 999
        col = self.sql.crsmst_col
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            acno = CCD(dat[col.index("crm_acno")], "NA", 7)
            name = CCD(dat[col.index("crm_name")], "NA", 30)
            add1 = CCD(dat[col.index("crm_add1")], "NA", 30)
            add2 = CCD(dat[col.index("crm_add2")], "NA", 30)
            add3 = CCD(dat[col.index("crm_add3")], "NA", 30)
            pcod = CCD(dat[col.index("crm_pcod")], "NA", 4)
            tel = CCD(dat[col.index("crm_tel")], "NA", 12)
            fax = CCD(dat[col.index("crm_fax")], "NA", 12)
            if self.condet == "M":
                contact = dat[col.index("crm_mgr")]
                email = dat[col.index("crm_mgr_email")].split(",")
            elif self.condet == "A":
                contact = dat[col.index("crm_acc")]
                email = dat[col.index("crm_acc_email")].split(",")
            else:
                contact = dat[col.index("crm_ord")]
                email = dat[col.index("crm_ord_email")].split(",")
            nameml = CCD("%s <%s>" % (contact, email[0]), "NA", 40)
            pyind = CCD(dat[col.index("crm_pyind")], "NA", 1)
            terms = CCD(dat[col.index("crm_terms")], "UI", 3)
            termsb = CCD(dat[col.index("crm_termsb")], "NA", 1)
            stday = CCD(dat[col.index("crm_stday")], "UI", 2)
            limit = CCD(dat[col.index("crm_limit")], "UI", 7)
            trdis = CCD(dat[col.index("crm_trdis")], "UD", 6.2)
            pydis = CCD(dat[col.index("crm_pydis")], "UD", 6.2)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s %s %s %s" % \
                (acno.disp, name.disp, add1.disp, pcod.disp, tel.disp,
                fax.disp, nameml.disp, pyind.disp, terms.disp, termsb.disp,
                stday.disp, limit.disp, trdis.disp, pydis.disp))
            if self.address == "Y" and add2.work:
                self.fpdf.drawText("%38s %-30s" % ("", add2.disp))
                self.pglin += 1
            if self.address == "Y" and add3.work:
                self.fpdf.drawText("%38s %-30s" % ("", add3.disp))
                self.pglin += 1
            self.pglin += 1
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        self.closeProcess()

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.pgnum += 1
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-34s %-10s %122s %5s" % \
            ("Creditors Ledger Master List as at", self.sysdtd,
                "Page", self.pgnum))
        self.fpdf.drawText()
        self.fpdf.drawText("%-15s%-1s%-1s" % ("(Options: Sort-",
            self.df.t_disp[0][0][0], ")"))
        self.fpdf.drawText()
        if self.condet == "M":
            det = "Manager's Contact Details"
        elif self.condet == "A":
            det = "Accounts Contact Details"
        else:
            det = "Orders Contact Details"
        self.fpdf.drawText("%-7s %-30s %-30s %-4s %-12s %-12s %-40s %-1s "\
            "%-3s %-1s %-2s %-7s %-6s %-6s" % ("Acc-Num", "Name", "Address",
            "PCod", "Tel-Number", "Fax-Number", "%s" % det, "P", "Trm", "B",
            "St", "CrLimit", "Tr-Dis", "Py-Dis"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
