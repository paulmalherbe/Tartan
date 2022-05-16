"""
SYNOPSIS
    Debtors Ledger Master Listing.

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
from TartanClasses import CCD, GetCtl, MyFpdf, ProgressBar, Sql, TartanDialog
from tartanFunctions import doWriteExport, doPrinter, getModName, showError

class dr3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsact", "drstyp", "drsmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        drsctl = gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.fromad = drsctl["ctd_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i)" % \
            (t[0], t[1], t[2], t[3], t[4])
        self.colsh = ["Chn", "Acc-Num", "Name", "Address", "Code", "Tel-Number",
            "Fax-Number", "Contact Details", "Deliver", "Rep", "Act", "Typ",
            "P", "Rft", "C-Limit"]
        self.forms = [("UI", 3), ("NA", 7), ("NA", 30), ("NA", 30),
            ("NA", 4), ("NA", 12), ("NA", 12), ("NA", 40), ("Na", 7),
            ("Na", 3), ("UA", 3), ("UA", 3), ("UI", 1), ("UI", 3),
            ("UI", 3), ("UI", 7)]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Debtors Master Listing (%s)" % self.__class__.__name__)
        daa = self.sql.getRec("drsmst", cols=["drm_bus_activity",
            "count(*)"], where=[("drm_cono", "=", self.opts["conum"])],
            group="drm_bus_activity", order="drm_bus_activity")
        act = {
            "stype": "C",
            "titl": "Valid Activities",
            "head": ("Act", "Quantity"),
            "data": daa,
            "typs": (("NA", 3), ("UI", 8)),
            "size": (400, 400)}
        dab = self.sql.getRec("drsmst", cols=["drm_bus_type",
            "count(*)"], where=[("drm_cono", "=", self.opts["conum"])],
            group="drm_bus_type", order="drm_bus_type")
        typ = {
            "stype": "C",
            "titl": "Valid Types",
            "head": ("Typ", "Quantity"),
            "data": dab,
            "typs": (("NA", 3), ("UI", 8)),
            "size": (400, 400)}
        r1s = (("Number", "N"), ("Name", "M"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Manager", "M"), ("Accounts", "A"), ("Sales", "S"))
        r4s = (("Yes", "Y"), ("No", "N"), ("Only", "O"))
        fld = (
            (("T",0,0,0),"INA",3,"Activity","Account Activity",
                "","N",self.doAct,act,None,None),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"INA",3,"Type","Account Type",
                "","N",self.doTyp,typ,None,None),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Full Address","",
                "N","Y",self.doAddress,None,None,None),
            (("T",0,4,0),("IRB",r3s),0,"Contact Details","",
                "M","Y",self.doContact,None,None,None),
            (("T",0,5,0),("IRB",r4s),0,"Include Redundant","",
                "N","Y",self.doRedu,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doAct(self, frt, pag, r, c, p, i, w):
        self.act = w
        if not self.act:
            self.df.loadEntry(frt, pag, p+1, "All Activities")
        else:
            chk = self.sql.getRec("drsact", where=[("dac_code", "=",
                self.act)], limit=1)
            if not chk:
                return "Invalid Activity Code"
            self.df.loadEntry(frt, pag, p+1, chk[1])

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w
        if not self.typ:
            self.df.loadEntry(frt, pag, p+1, "All Types")
        else:
            chk = self.sql.getRec("drstyp", where=[("dtp_code", "=",
                self.typ)], limit=1)
            if not chk:
                return "Invalid Type Code"
            self.df.loadEntry(frt, pag, p+1, chk[1])

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
        whr = [("drm_cono", "=", self.opts["conum"])]
        if self.act:
            whr.append(("drm_bus_activity", "=", self.act))
        if self.typ:
            whr.append(("drm_bus_type", "=", self.typ))
        if self.redu == "N":
            whr.append(("drm_stat", "<>", "X"))
        elif self.redu == "O":
            whr.append(("drm_stat", "=", "X"))
        if self.sort == "N":
            odr = "drm_chain, drm_acno"
        else:
            odr = "drm_name"
        recs = self.sql.getRec("drsmst", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        expheads = ["%03u %-30s %s %6s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm, self.__class__.__name__)]
        expheads.append("Debtors Master Code List as at %s" % self.sysdtd)
        expcolsh = [self.colsh]
        expforms = self.forms
        expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            expdatas.append(["BODY", [vals[0].work, vals[1].work,
                vals[2].work, vals[3].work, vals[4].work, vals[5].work,
                vals[6].work, vals[7].work, vals[8].work, vals[9].work,
                vals[10].work, vals[11].work, vals[12].work, vals[13].work,
                vals[14].work, vals[15].work]])
        p.closeProgress()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=expheads, colsh=expcolsh, forms=expforms,
            datas=expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-179s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s %s %s %s %s %s "\
                "%s %s %s %s" % (vals[0].disp, vals[1].disp, vals[2].disp,
                vals[3].disp, vals[4].disp, vals[5].disp, vals[6].disp,
                vals[7].disp, vals[8].disp, vals[9].disp, vals[10].disp,
                vals[11].disp, vals[12].disp, vals[13].disp, vals[14].disp,
                vals[15].disp))
            if self.address == "Y" and vals[16].work:
                self.fpdf.drawText("%42s %-30s" % ("", vals[16].disp))
                self.pglin += 1
            if self.address == "Y" and vals[17].work:
                self.fpdf.drawText("%42s %-30s" % ("", vals[17].disp))
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

    def getValues(self, dat):
        col = self.sql.drsmst_col
        chn = CCD(dat[col.index("drm_chain")], "UI", 3)
        acno = CCD(dat[col.index("drm_acno")], "NA", 7)
        name = CCD(dat[col.index("drm_name")], "NA", 30)
        add1 = CCD(dat[col.index("drm_add1")], "NA", 30)
        pcod = CCD(dat[col.index("drm_pcod")], "NA", 4)
        tel = CCD(dat[col.index("drm_tel")], "NA", 12)
        fax = CCD(dat[col.index("drm_fax")], "NA", 12)
        if self.condet == "M":
            contact = dat[col.index("drm_mgr")]
            email = dat[col.index("drm_mgr_email")].split(",")
        elif self.condet == "A":
            contact = dat[col.index("drm_acc")]
            email = dat[col.index("drm_acc_email")].split(",")
        else:
            contact = dat[col.index("drm_sls")]
            email = dat[col.index("drm_sls_email")].split(",")
        nameml = CCD("%s <%s>" % (contact, email[0]), "NA", 40)
        delv = CCD(dat[col.index("drm_delivery")], "Na", 7)
        rep = CCD(dat[col.index("drm_rep")], "Na", 3)
        bact = CCD(dat[col.index("drm_bus_activity")], "UA", 3)
        btyp = CCD(dat[col.index("drm_bus_type")], "UA", 3)
        prices = CCD(dat[col.index("drm_plev")], "UI", 1)
        rfterm = CCD(dat[col.index("drm_rfterms")], "UI", 3)
        rjterm = CCD(dat[col.index("drm_rjterms")], "UI", 3)
        limit = CCD(dat[col.index("drm_limit")], "UI", 7)
        add2 = CCD(dat[col.index("drm_add2")], "NA", 30)
        add3 = CCD(dat[col.index("drm_add3")], "NA", 30)
        return (chn, acno, name, add1, pcod, tel, fax, nameml, delv, rep,
            bact, btyp, prices, rfterm, rjterm, limit, add2, add3)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-32s %-150s" % \
            ("Debtors Ledger Master List as at", self.sysdtd))
        self.fpdf.drawText()
        self.fpdf.drawText("(%-15s%1s)" % ("Options: Sort-",
            self.df.t_disp[0][0][0]))
        self.fpdf.drawText()
        if self.condet == "M":
            det = "Manager's Contact Details"
        elif self.condet == "A":
            det = "Accounts Contact Details"
        else:
            det = "Orders Contact Details"
        self.fpdf.drawText("%-3s %-7s %-30s %-30s %-4s %-12s %-12s %-40s "\
            "%-7s %-3s %-3s %-3s %1s %-3s %-3s %-7s" % ("Chn", "Acc-Num",
            "Name", "Address", "Code", "Tel-Number", "Fax-Number", det,
            "Deliver", "Rep", "Act", "Typ", "P", "Rft","Rjt","C-Limit"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
