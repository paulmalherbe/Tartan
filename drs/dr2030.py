"""
SYNOPSIS
    Debtors Ledger - Raising Recurring Charges.

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
from TartanClasses import ASD, Batches, CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import doDrawTable, doPrinter, getModName
from tartanFunctions import getSingleRecords, getVatRate, mthendDate
from tartanFunctions import textFormat

class dr2030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.doProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlvrf", "ctlvtf",
            "drsmst", "drstrn", "drsrcm", "drsrct", "genmst", "gentrn"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.glint = drsctl["ctd_glint"]
        self.fromad = drsctl["ctd_emadd"]
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            if self.gc.chkRec(self.opts["conum"],ctlctl,["drs_ctl","vat_ctl"]):
                return
            self.drsctl = ctlctl["drs_ctl"]
            self.vatctl = ctlctl["vat_ctl"]
        ctl = self.sql.getRec("ctlmst",
            where=[("ctm_cono", "=", self.opts["conum"])], limit=1)
        for col in ("ctm_name", "ctm_add1", "ctm_add2", "ctm_add3",
                    "ctm_pcode", "ctm_regno", "ctm_taxno", "ctm_tel",
                    "ctm_fax", "ctm_b_name", "ctm_b_ibt", "ctm_b_acno",
                    "ctm_logo"):
            setattr(self, "%s" % col, ctl[self.sql.ctlmst_col.index(col)])
        if "LETTERHEAD" in os.environ:
            self.ctm_logo = os.environ["LETTERHEAD"]
        if not self.ctm_logo or not os.path.exists(self.ctm_logo):
            self.ctm_logo = None
        self.batchHeader()
        if not self.bh.batno:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def batchHeader(self):
        self.bh = Batches(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.opts["period"], "DRS", self.opts["rtn"],
            multi="N", glint=self.glint)
        self.bh.doBatchHeader()
        if not self.bh.batno:
            return

    def doProcess(self):
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually","6"),
            ("Annually","Y"))
        r2s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Frequency","",
                "M","N",self.doFreq,None,None,None),
            (("T",0,1,0),("IRB",r2s),1,"All Charges","",
                "N","N",self.doAll,None,None,None),
            (("T",0,2,0),"INa",9,"2nd Reference","",
                "","N",self.doRef2,None,None,None),
            (("T",0,3,0),("IRB",r2s),1,"Invoices","",
                "N","N",self.doInv,None,None,None))
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","P"), mail=("N","Y"))

    def doFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w
        self.wher = [("dcm_cono", "=", self.opts["conum"]), ("dcm_freq", "=",
            self.freq), ("dcm_last", "<", self.bh.curdt)]
        data = self.sql.getRec("drsrcm", where=self.wher)
        if not data:
            return "No Valid Recurring Charges"
        if self.freq == "M":
            self.mths = 1
        elif self.freq == "3":
            self.mths = 3
        elif self.freq == "6":
            self.mths = 6
        else:
            self.mths = 12

    def doAll(self, frt, pag, r, c, p, i, w):
        self.allc = w

    def doRef2(self, frt, pag, r, c, p, i, w):
        self.ref2 = w

    def doInv(self, frt, pag, r, c, p, i, w):
        self.inv = w
        if self.inv == "N":
            self.df.loadEntry(frt, pag, p+2, data="")
            return "nd"

    def doEml(self, frt, pag, r, c, p, i, w):
        self.eml = w

    def doEnd(self):
        self.df.closeProcess()
        if self.allc == "N":
            recs = getSingleRecords(self.opts["mf"], "drsrcm", ("dcm_num",
                "dcm_desc"), where=self.wher)
        else:
            recs = self.sql.getRec("drsrcm", where=self.wher)
        if recs:
            if self.inv == "Y" and self.df.repeml[1] == "N":
                self.fpdf = MyFpdf(orientation="L", fmat="A4",
                    name=self.__class__.__name__, head=128)
            for dcm in recs:
                num = dcm[self.sql.drsrcm_col.index("dcm_num")]
                desc = dcm[self.sql.drsrcm_col.index("dcm_desc")]
                day = dcm[self.sql.drsrcm_col.index("dcm_day")]
                if day == 30:
                    self.trdt = mthendDate((self.bh.curdt * 100) + 1)
                else:
                    self.trdt = (self.bh.curdt * 100) + day
                vat = dcm[self.sql.drsrcm_col.index("dcm_vat")]
                self.vatrte = getVatRate(self.sql, self.opts["conum"],
                    vat, self.trdt)
                glac = dcm[self.sql.drsrcm_col.index("dcm_glac")]
                nxt = self.sql.getRec("drstrn", cols=["max(drt_ref1)"],
                    where=[("drt_cono", "=", self.opts["conum"]), ("drt_ref1",
                    "like", "RC%03i%s" % (num, "%"))], limit=1)
                if not nxt[0]:
                    nxt = 0
                else:
                    nxt = int(nxt[0][5:])
                tot_val = 0
                tot_vat = 0
                rec = self.sql.getRec("drsrct", where=[("dct_cono", "=",
                    self.opts["conum"]), ("dct_num", "=", num), ("dct_start",
                    "<=", self.bh.curdt), ("dct_end", ">=", self.bh.curdt)])
                col = self.sql.drsrct_col
                for dct in rec:
                    self.chain = dct[col.index("dct_chain")]
                    self.acno = dct[col.index("dct_acno")]
                    # Check for Redundancy
                    chk = self.sql.getRec("drsmst", cols=["drm_stat"],
                        where=[("drm_cono", "=", self.opts["conum"]),
                        ("drm_chain", "=", self.chain), ("drm_acno", "=",
                        self.acno)], limit=1)
                    if chk[0] == "X":
                        continue
                    # Check for Valid Period
                    charge = False
                    start = dct[col.index("dct_start")]
                    year = int(start / 100)
                    month = start % 100
                    while start <= self.bh.curdt:
                        if start == self.bh.curdt:
                            charge = True
                            break
                        month += self.mths
                        if month > 12:
                            year += 1
                            month -= 12
                        start = (year * 100) + month
                    if not charge:
                        continue
                    # Create Transactions
                    nxt += 1
                    self.ref = "RC%03i%04i" % (num, nxt)
                    self.detail = textFormat(dct[col.index("dct_detail")], 73)
                    self.amnt = dct[col.index("dct_amnt")]
                    self.vmnt = round(self.amnt * self.vatrte / 100, 2)
                    self.tmnt = float(ASD(self.amnt) + ASD(self.vmnt))
                    tot_val = float(ASD(tot_val) + ASD(self.amnt))
                    tot_vat = float(ASD(tot_vat) + ASD(self.vmnt))
                    # Debtors (drstrn)
                    self.sql.insRec("drstrn", data=[self.opts["conum"],
                        self.chain, self.acno, 1, self.ref, self.bh.batno,
                        self.trdt, self.ref2, self.tmnt, self.vmnt,
                        self.bh.curdt, self.detail[0], vat, "Y",
                        self.opts["capnm"], self.sysdtw, 0])
                    if self.inv == "Y":
                        # Create Invoice
                        self.doInvoice()
                    # VAT (ctlvtf)
                    amnt = float(ASD(0) - ASD(self.amnt))
                    vmnt = float(ASD(0) - ASD(self.vmnt))
                    data = [self.opts["conum"], vat, "O", self.bh.curdt,
                        "D", 1, self.bh.batno, self.ref, self.trdt, self.acno,
                        self.detail[0], amnt, vmnt, 0, self.opts["capnm"],
                        self.sysdtw, 0]
                    self.sql.insRec("ctlvtf", data=data)
                if self.glint == "Y":
                    ref = "RC%07i" % num
                    # Update Debtors Control
                    amnt = float(ASD(tot_val) + ASD(tot_vat))
                    data = (self.opts["conum"], self.drsctl, self.bh.curdt,
                        self.trdt, 1, ref, self.bh.batno, amnt, 0, desc,
                        "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                    self.sql.insRec("gentrn", data=data)
                    # Update Sales Account
                    amnt = float(ASD(0) - ASD(tot_val))
                    data = (self.opts["conum"], glac, self.bh.curdt, self.trdt,
                        1, ref, self.bh.batno, amnt, 0, desc, "", "", 0,
                        self.opts["capnm"], self.sysdtw, 0)
                    self.sql.insRec("gentrn", data=data)
                    amnt = float(ASD(0) - ASD(tot_vat))
                    if amnt:
                        # Update VAT Control
                        data = (self.opts["conum"], self.vatctl, self.bh.curdt,
                            self.trdt, 1, ref, self.bh.batno, amnt, 0, desc,
                            "", "", 0, self.opts["capnm"], self.sysdtw, 0)
                        self.sql.insRec("gentrn", data=data)
                # Update Recurring Charge (drsrcm)
                self.sql.updRec("drsrcm", cols=["dcm_last"],
                    data=[self.bh.curdt], where=[("dcm_cono", "=",
                    self.opts["conum"]), ("dcm_num", "=", num), ("dcm_freq",
                    "=", self.freq)])
            self.opts["mf"].dbm.commitDbase()
            if self.inv == "Y" and self.df.repeml[1] == "N":
                self.doPrint()
        self.opts["mf"].closeLoop()

    def doInvoice(self):
        if self.df.repeml[1] == "Y":
            self.fpdf = MyFpdf(orientation="L", fmat="A4",
                name=self.__class__.__name__, head=128)
        cw = self.fpdf.get_string_width("X")
        ld = self.fpdf.font[2]
        ica = CCD(self.tmnt, "SD", 13.2)
        iva = CCD(float(ASD(self.tmnt) - ASD(self.amnt)), "SD", 13.2)
        ivr = CCD(self.vatrte, "UD", 5.2)
        self.drawInvoice(cw, ld)
        row = 20
        for detail in self.detail:
            row += 1
            self.fpdf.drawText(x=22.2*cw, y=row*ld, txt=detail)
        self.fpdf.drawText(x=97*cw, y=row*ld, txt=ivr.disp)
        self.fpdf.drawText(x=103*cw, y=row*ld, txt=ica.disp)
        self.printTotals(cw, ld, ica, iva)
        if self.df.repeml[1] == "Y":
            self.doPrint()

    def drawInvoice(self, cw, ld):
        self.fpdf.add_page()
        self.fpdf.setFont("courier", "B", 16)
        self.fpdf.drawText(x=22*cw, y=1*ld, txt=self.ctm_name)
        self.fpdf.setFont("courier", "B", 14)
        self.fpdf.drawText(x=108*cw, y=2*ld, w=16, align="R", txt="Tax Invoice")
        self.fpdf.setFont("courier", "B", self.fpdf.font[1])
        if self.ctm_logo:
            self.fpdf.image(self.ctm_logo, 45, 3, 138, 28)
        else:
            self.fpdf.drawText(x=22*cw, y=2.5*ld, txt=self.ctm_add1)
            self.fpdf.drawText(x=22*cw, y=3.5*ld, txt=self.ctm_add2)
            self.fpdf.drawText(x=22*cw, y=4.5*ld, txt=self.ctm_add3)
            self.fpdf.drawText(x=22*cw, y=5.5*ld, txt=self.ctm_pcode)
            self.fpdf.drawText(x=54*cw, y=2.5*ld,
                txt="RegNo: %s" % self.ctm_regno)
            self.fpdf.drawText(x=54*cw, y=3.5*ld,
                txt="TaxNo: %s" % self.ctm_taxno)
            self.fpdf.drawText(x=54*cw, y=4.5*ld,
                txt="TelNo: %s" % self.ctm_tel)
            self.fpdf.drawText(x=54*cw, y=5.5*ld,
                txt="FaxNo: %s" % self.ctm_fax)
        drm = self.sql.getRec("drsmst", where=[("drm_cono", "=",
            self.opts["conum"]), ("drm_chain", "=", self.chain), ("drm_acno",
            "=", self.acno)], limit=1)
        col = self.sql.drsmst_col
        self.fpdf.drawText(x=22.5*cw, y=10.5*ld, txt=drm[col.index("drm_name")])
        self.fpdf.drawText(x=22.5*cw, y=11.5*ld, txt=drm[col.index("drm_add1")])
        self.fpdf.drawText(x=22.5*cw, y=12.5*ld, txt=drm[col.index("drm_add2")])
        self.fpdf.drawText(x=22.5*cw, y=13.5*ld, txt=drm[col.index("drm_add3")])
        self.fpdf.drawText(x=22.5*cw, y=14.5*ld, txt=drm[col.index("drm_pcod")])
        self.emadd = CCD(drm[col.index("drm_acc_email")], "TX")
        # Tables
        r1 = {
            "margins": ((22.5, 53), (8, 9)),
            "repeat": (1, 1),
            "rows": [
                [22, 8.5, [[32, 1.5, .8, "Charge To:", False]]],
                [22, 10, [[32, 5.5]]],
                [22, 16, [
                    [9, 1.5, .8, "Acc-Num", True],
                    [20, 1.5, .8, "V.A.T. Number", True],
                    [42, 1.5, .8, "Contact Person", True],
                    [12, 1.5, .8, "Date", True],
                    [11, 1.5, .8, "Inv-Number", True]]],
                [22, 17.5, [
                    [9, 1.5, 0, self.acno, True],
                    [20, 1.5, 0, drm[col.index("drm_vatno")], True],
                    [42, 1.5, 0, drm[col.index("drm_sls")]],
                    [12, 1.5, 0, CCD(self.trdt, "D1", 10).disp, True],
                    [11, 1.5, 0, "%10s" % self.ref]]],
                [22, 19, [
                    [74, 1.5, .8, "Description", False],
                    [7, 1.5, .8, " Tax-%", False],
                    [13, 1.5, .8, "       Value", False]]],
                [22, 20.5, [
                    [74, 12.5],
                    [7, 12.5],
                    [13, 12.5]]],
                [22, 33, [
                    [11, 1.5, .8, "Taxable"],
                    [12, 1.5],
                    [12, 1.5, .8, "Non-Taxable"],
                    [12, 1.5],
                    [11, 1.5, .8, "Total Tax"],
                    [11, 1.5],
                    [12, 1.5, .8, "Total Value"],
                    [13, 1.5]]]]}
        doDrawTable(self.fpdf, r1, cw=cw, ld=ld, font=False)

    def printTotals(self, cw, ld, ica, iva):
        tot = [0, 0, iva.work, ica.work]
        if iva.work:
            tot[0] = float(ASD(ica.work) - ASD(iva.work))
        else:
            tot[1] = ica.work
        self.fpdf.drawText(x=32*cw, y=33.2*ld, txt=CCD(tot[0],"SD",13.2).disp)
        self.fpdf.drawText(x=56*cw, y=33.2*ld, txt=CCD(tot[1],"SD",13.2).disp)
        self.fpdf.drawText(x=78*cw, y=33.2*ld, txt=CCD(tot[2],"SD",13.2).disp)
        self.fpdf.drawText(x=103*cw, y=33.2*ld, txt=CCD(tot[3],"SD",13.2).disp)

    def doPrint(self):
        if not self.fpdf.page:
            return
        if self.df.repeml[1] == "Y":
            self.df.repeml[2] = self.emadd.work
            key = "%s_%s_%s" % (self.opts["conum"], self.chain, self.acno)
        else:
            key = "%s_all_all" % self.opts["conum"]
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, key, ext="pdf")
        self.fpdf.output(pdfnam, "F")
        doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
            header="%s Invoice" % self.opts["conam"], repprt=self.df.repprt,
            fromad=self.fromad, repeml=self.df.repeml)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
