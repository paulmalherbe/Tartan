"""
SYNOPSIS
    Booking Arrivals Listing.

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

import datetime, os, time
from textwrap import wrap
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, PrintBookingInvoice
from TartanClasses import Sql, TartanDialog
from tartanFunctions import callModule, dateDiff, doPrinter, getModName
from tartanFunctions import getVatRate, copyList, projectDate
from tartanWork import mthnam

class bk3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, tables=["bkmmst", "bkmcon",
            "bkmrtt", "bkmtrn", "bkmunm", "ctlmst", "ctlvtf", "gentrn",
            "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctl = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctl:
            return
        for col in (
                "ctm_name", "ctm_add1", "ctm_add2", "ctm_add3", "ctm_pcode",
                "ctm_regno", "ctm_taxno", "ctm_taxdf", "ctm_tel", "ctm_fax",
                "ctm_b_name", "ctm_b_ibt", "ctm_b_acno", "ctm_logo"):
            setattr(self, col, ctl[col])
        if self.ctm_logo and "LETTERHEAD" in os.environ:
            self.ctm_logo = os.environ["LETTERHEAD"]
        if not self.ctm_logo or not os.path.exists(self.ctm_logo):
            self.ctm_logo = None
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.glint = bkmctl["cbk_glint"]
        self.tplnam = bkmctl["cbk_invtpl"]
        self.fromad = bkmctl["cbk_emadd"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["vat_ctl", "bkm_ctl"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.vatctl = ctlctl["vat_ctl"]
            self.bkmctl = ctlctl["bkm_ctl"]
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Booking Arrivals Listing (%s)" % self.__class__.__name__)
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "I"),
                ("tpm_system", "=", "BKM")],
            "order": "tpm_tname"}
        r1s = (("Weekdays","D"), ("Weekend","E"), ("Range", "R"))
        r2s = (("Yes","Y"), ("No","N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Period","",
                "D","Y",self.doPeriod,None,None,None),
            (("T",0,1,0),"ID1",10,"Starting Date","",
                0,"N",self.doStartDate,None,None,("efld",)),
            (("T",0,2,0),"ID1",10,"Ending Date","",
                0,"N",self.doEndDate,None,None,("efld",)),
            (("T",0,3,0),("IRB",r2s),0,"Include Queries","",
                "N","Y",self.doQuery,None,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Housekeeping Report","",
                "Y","Y",self.doHkRpt,None,None,None),
            (("T",0,5,0),("IRB",r2s),0,"Generate Invoices","",
                "Y","Y",self.doGenInv,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"Print Invoices","",
                "Y","Y",self.doPrtInv,None,None,None),
            (("T",0,7,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        if "args" in self.opts:
            tops = self.opts["args"]
        else:
            tops = False
        self.df = TartanDialog(self.opts["mf"], tops=tops, title=self.tit,
            eflds=fld, tend=tnd, txit=txt, view=("N","P"), mail=("Y","N"))

    def doPeriod(self, frt, pag, r, c, p, i, w):
        self.period = w
        if self.period in ("D", "E"):
            self.start = self.getStart()
            self.df.loadEntry(frt, pag, p+1, data=self.start)

    def doStartDate(self, frt, pag, r, c, p, i, w):
        self.start = w
        if self.period in ("D", "E"):
            if self.getStart(self.start):
                return "Invalid Start Date"
            if self.period == "D":
                self.end = projectDate(self.start, 3)
            else:
                self.end = projectDate(self.start, 2)
            self.df.loadEntry(frt, pag, p+1, data=self.end)
            return "sk1"

    def getStart(self, date=None):
        if self.period == "D":
            chk = 0
        else:
            chk = 4
        if date:
            year = int(date / 10000)
            month = int(date / 100) % 100
            day = date % 100
            if datetime.date(year, month, day).weekday() != chk:
                return True
        else:
            date = projectDate(self.sysdtw, -1)
            dte = 99
            while dte != chk:
                date = projectDate(date, 1)
                year = int(date / 10000)
                month = int(date / 100) % 100
                day = date % 100
                dte = datetime.date(year, month, day).weekday()
            return date

    def doEndDate(self, frt, pag, r, c, p, i, w):
        if w < self.start:
            return "Invalid End Date, Before Start Date"
        days = dateDiff(self.start, w, ptype="days")
        if days > 7:
            return "Range More Than 7 Days"
        self.end = w

    def doQuery(self, frt, pag, r, c, p, i, w):
        self.query = w

    def doHkRpt(self, frt, pag, r, c, p, i, w):
        self.house = w

    def doGenInv(self, frt, pag, r, c, p, i, w):
        self.geninv = w
        if self.geninv == "N":
            self.prtinv = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.prtinv)
            return "sk2"

    def doPrtInv(self, frt, pag, r, c, p, i, w):
        self.prtinv = w
        if self.prtinv == "N":
            return "sk1"

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "BKM")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doEnd(self):
        self.df.closeProcess()
        # Headings and Mail subject
        self.cdes = "%-30s" % self.opts["conam"]
        start = self.getDate(self.start)
        end = self.getDate(projectDate(self.end, 1))
        if self.period == "D":
            self.hdes = "Arrivals for Weekdays %s to %s" % (start, end)
        elif self.period == "E":
            self.hdes = "Arrivals for Weekend %s to %s" % (start, end)
        else:
            self.hdes = "Arrivals for Period %s to %s" % (start, end)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=80, auto=True)
        self.fpdf.header = self.pageHeading
        self.rtyp = "A"
        self.doArrival()
        if self.house == "Y":
            self.rtyp = "H"
            self.hdes = self.hdes.replace("Arrivals", "Units")
            if self.fpdf.page:
                self.fpdf.add_page()
            self.doHKeeping()
        if self.fpdf.page:
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            self.fpdf.output(pdfnam, "F")
            subj = "%s - %s" % (self.cdes, self.hdes)
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                pdfnam=pdfnam, header=subj, repprt=self.df.repprt,
                fromad=self.fromad, repeml=self.df.repeml)
        if self.prtinv == "Y" and self.docs:
            # Print Invoice
            self.docs.sort()
            PrintBookingInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], "I", self.docs, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml)
            # Print Statement
            self.book.sort()
            callModule(self.opts["mf"], None, "bk3070",
                coy=(self.opts["conum"], self.opts["conam"]),
                args=[self.book, self.df.repprt, self.df.repeml])
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

    def doArrival(self):
        state = ["C", "S"]
        if self.query == "Y":
            state.append("Q")
        recs = self.sql.getRec("bkmmst", where=[("bkm_cono", "=",
            self.opts["conum"]), ("bkm_state", "in", tuple(state))],
            order="bkm_ccode")
        self.book = []
        self.docs = []
        last = 0
        for rec in recs:
            number = rec[self.sql.bkmmst_col.index("bkm_number")]
            ccode = rec[self.sql.bkmmst_col.index("bkm_ccode")]
            btype = rec[self.sql.bkmmst_col.index("bkm_btype")]
            arrive = rec[self.sql.bkmmst_col.index("bkm_arrive")]
            depart = rec[self.sql.bkmmst_col.index("bkm_depart")]
            if btype == "A":
                if depart <= self.start or arrive > self.end:
                    continue
            elif depart < self.start or arrive > self.end:
                continue
            if self.geninv == "Y":
                self.doRaiseInvoice(number, arrive)
            con = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
                self.opts["conum"]), ("bkc_ccode", "=", ccode)], limit=1)
            sname = con[self.sql.bkmcon_col.index("bkc_sname")].strip()
            names = con[self.sql.bkmcon_col.index("bkc_names")].strip()
            if names:
                name = "%s %s (%s)" % (names.split()[0], sname, number)
            else:
                name = "%s (%s)" % (sname, number)
            bal = self.sql.getRec("bkmtrn", cols=["sum(bkt_tramt)"],
                where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
                "=", number)], limit=1)
            rtts = self.sql.getRec("bkmrtt", cols=["brt_udesc",
                "brt_uroom", "sum(brt_quant)"], where=[("brt_cono", "=",
                self.opts["conum"]), ("brt_number", "=", number)],
                group="brt_utype, brt_ucode, brt_udesc, brt_uroom",
                order="brt_utype, brt_ucode, brt_uroom")
            if not rtts:
                continue
            units = []
            unt = None
            for rtt in rtts:
                if rtt[1]:
                    if not unt:
                        unt = ["%s - R%s" % (rtt[0], rtt[1]), rtt[2]]
                    else:
                        unt = ["%s & R%s" % (unt[0], rtt[1]), rtt[2]]
                else:
                    unt = (rtt[0], rtt[2])
                units.append(unt)
            namq = len(wrap(name, break_long_words=False, width=25))
            untq = 0
            for unit in units:
                untq += len(wrap(unit[0], break_long_words=False, width=25))
            if namq and untq > namq:
                hh = [(untq * 8.0) / namq, 8, untq * 8]
            elif untq and namq > untq:
                hh = [8, (namq * 8.0) / untq, namq * 8]
            elif namq:
                hh = [8, 8, namq * 8]
            else:
                hh = [8, 8, untq * 8]
            if not self.fpdf.page or self.fpdf.get_y() + hh[0] > 280:
                self.fpdf.add_page()
            oldnm = None
            for unit in units:
                if name == oldnm:
                    name = ""
                else:
                    oldnm = name
                if arrive >= self.start:
                    yr = int(arrive / 10000)
                    mt = int(arrive / 100) % 100
                    dy = arrive % 100
                    d = datetime.date(yr, mt, dy)
                    arr = d.strftime("%a")
                else:
                    arr = "<--"
                if btype == "A":
                    td = projectDate(depart, -1)
                else:
                    td = depart
                if td <= self.end:
                    yr = int(depart / 10000)
                    mt = int(depart / 100) % 100
                    dy = depart % 100
                    e = datetime.date(yr, mt, dy)
                    dep = e.strftime("%a")
                else:
                    dep = "-->"
                if last != number and bal[0]:
                    amt = CCD(bal[0], "SD", 13.2).disp
                else:
                    amt = CCD(0, "SD", 13.2).disp
                self.printLine(name, unit[0], unit[1], arr, dep, amt, hh)
                last = number
        self.opts["mf"].dbm.commitDbase()

    def doHKeeping(self):
        recs = self.sql.getRec("bkmunm", cols=["bum_btyp", "bum_code",
            "bum_desc"], where=[("bum_cono", "=", self.opts["conum"]),
            ("bum_room", "<>", 999)], order="bum_btyp, bum_code")
        for rec in recs:
            col = ["bkm_number", "bkm_btype", "bkm_group", "bkc_sname",
                "bkc_names", "bkm_arrive", "bkm_depart", "sum(brt_quant)"]
            state = ["C", "S"]
            if self.query == "Y":
                state.append("Q")
            bks = self.sql.getRec(tables=["bkmmst", "bkmrtt", "bkmcon"],
                cols=col, where=[("bkm_cono", "=", self.opts["conum"]),
                ("bkm_state", "in", tuple(state)), ("brt_cono=bkm_cono",),
                ("brt_number=bkm_number",), ("brt_utype", "=", rec[0]),
                ("brt_ucode", "=", rec[1]), ("bkc_cono=bkm_cono",),
                ("bkc_ccode=bkm_ccode",)], order="bkm_arrive, bkc_sname")
            qty = ""
            arr = ""
            dep = ""
            amt = ""
            totq = 0
            lines = []
            hh = [8, 8, 8]
            for bk in bks:
                number = bk[0]
                btype = bk[1]
                if bk[2]:
                    name = bk[2]
                elif bk[4]:
                    name = "%s %s" % (bk[4].split()[0], bk[3])
                else:
                    name = bk[3]
                name = "%s\n(%s)" % (name.strip(), number)
                arrive = bk[5]
                depart = bk[6]
                if btype == "A":
                    if depart <= self.start or arrive > self.end:
                        continue
                elif depart < self.start or arrive > self.end:
                    continue
                if arrive >= self.start:
                    yr = int(arrive / 10000)
                    mt = int(arrive / 100) % 100
                    dy = arrive % 100
                    dt = datetime.date(yr, mt, dy)
                    arrive = dt.strftime("%a")
                else:
                    arrive = "<--"
                if btype == "A":
                    td = projectDate(depart, -1)
                else:
                    td = depart
                if td <= self.end:
                    yr = int(depart / 10000)
                    mt = int(depart / 100) % 100
                    dy = depart % 100
                    dt = datetime.date(yr, mt, dy)
                    depart = dt.strftime("%a")
                else:
                    depart = "-->"
                rms = self.sql.getRec("bkmrtt",
                    cols=["brt_uroom"],
                    where=[
                        ("brt_cono", "=", self.opts["conum"]),
                        ("brt_number", "=", number),
                        ("brt_utype", "=", rec[0]),
                        ("brt_ucode", "=", rec[1])],
                    order="brt_uroom")
                rm = False
                for r in rms:
                    if not r[0]:
                        continue
                    if not rm:
                        name = "%s - R%s" % (name, r[0])
                        rm = True
                    else:
                        name = "%s & R%s" % (name, r[0])
                quant = bk[7]
                bal = self.sql.getRec("bkmtrn", cols=["sum(bkt_tramt)"],
                    where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
                    "=", number)], limit=1)
                namq = len(wrap(name, break_long_words=False, width=25))
                totq += namq
                hh[2] = namq * 8
                qty = CCD(quant, "UI", 3).disp
                arr = CCD(arrive, "NA", 3).disp
                dep = CCD(depart, "NA", 3).disp
                amt = CCD(bal[0], "SD", 13.2).disp
                lines.append([name, qty, arr, dep, amt, copyList(hh)])
            if not self.fpdf.page or self.fpdf.get_y() + (totq * 8) > 280:
                self.fpdf.add_page()
            untq = len(wrap(rec[2], break_long_words=False, width=25))
            if not lines:
                hh[1] = hh[2] = 8.0 * untq
                self.y = self.fpdf.get_y()
                self.printLine(rec[2], "", "", "", "", "", hh)
                self.fpdf.set_y(self.y)
                self.printLine(None, "", "", "", "", "", hh)
            else:
                if untq > totq:
                    hh[1] = hh[2] = (untq * 8.0) / totq
                elif totq > untq:
                    hh[0] = (totq * 8.0) / untq
                else:
                    hh[2] = totq * 8
                self.y = self.fpdf.get_y()
                self.printLine(rec[2], "", "", "", "", "", hh)
                self.fpdf.set_y(self.y)
                for l in lines:
                    self.printLine(None, l[0], l[1], l[2], l[3], l[4], l[5])

    def doRaiseInvoice(self, number, trdt):
        # Raise the Invoice
        incamt = 0
        vatamt = 0
        curdt = int(trdt / 100)
        batno = "B%s" % curdt
        gls = {}
        recs = self.sql.getRec("bkmrtt", where=[("brt_cono",
            "=", self.opts["conum"]), ("brt_number", "=", number),
            ("brt_invno", "=", 0)])
        if not recs:
            return
        invno = self.getRef(number)
        self.docs.append(invno)
        if number not in self.book:
            self.book.append(number)
        for rec in recs:
            utyp = rec[self.sql.bkmrtt_col.index("brt_utype")]
            ucod = rec[self.sql.bkmrtt_col.index("brt_ucode")]
            rcod = rec[self.sql.bkmrtt_col.index("brt_rcode")]
            rbas = rec[self.sql.bkmrtt_col.index("brt_rbase")]
            quan = rec[self.sql.bkmrtt_col.index("brt_quant")]
            rate = rec[self.sql.bkmrtt_col.index("brt_arate")]
            days = rec[self.sql.bkmrtt_col.index("brt_bdays")]
            umst = self.sql.getRec("bkmunm", where=[("bum_cono",
                "=", self.opts["conum"]), ("bum_btyp", "=", utyp),
                ("bum_code", "=", ucod)], limit=1)
            vatc = umst[self.sql.bkmunm_col.index("bum_vatc")]
            if not vatc:
                vatc = self.ctm_taxdf
            vrte = getVatRate(self.sql, self.opts["conum"], vatc, trdt)
            if vrte is None:
                vrte = 0.0
            if rbas == "A":
                inca = quan * days * rate
            elif rbas == "B":
                inca = quan * rate
            elif rbas == "C":
                inca = days * rate
            else:
                inca = rate
            vata = round(inca * vrte / (100 + vrte), 2)
            exca = float(ASD(inca) - ASD(vata))
            incamt = float(ASD(incamt) + ASD(inca))
            vatamt = float(ASD(vatamt) - ASD(vata))
            if self.glint == "Y":
                slsa = umst[self.sql.bkmunm_col.index("bum_slsa")]
                if slsa not in gls:
                    gls[slsa] = [0, 0, vatc]
                gls[slsa][0] = float(ASD(gls[slsa][0]) - ASD(exca))
                gls[slsa][1] = float(ASD(gls[slsa][1]) - ASD(vata))
            data = [self.opts["conum"], number, 2, invno, batno, trdt, inca,
                vata, curdt, "Booking %s-%s Raised" % (utyp, ucod), vatc, "",
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("bkmtrn", data=data)
            self.sql.updRec("bkmrtt", cols=["brt_invno", "brt_invdt",
                "brt_vrate"], data=[invno, trdt, vrte],
                where=[("brt_cono", "=", self.opts["conum"]),
                ("brt_number", "=", number), ("brt_utype", "=", utyp),
                ("brt_ucode", "=", ucod), ("brt_rcode", "=", rcod)])
            if vata:
                exc = float(ASD(0) - ASD(exca))
                vat = float(ASD(0) - ASD(vata))
                data = [self.opts["conum"], vatc, "O", curdt, "B", 1, batno,
                    invno, trdt, number, "Booking %s" % number, exc, vat, 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("ctlvtf", data=data)
        if self.glint == "Y":
            data = [self.opts["conum"], self.bkmctl, curdt, trdt, 1, invno,
                batno, incamt, 0, "Booking %s" % number, "", "", 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
            for acc in gls:
                data = [self.opts["conum"], acc, curdt, trdt, 1, invno,
                    batno, gls[acc][0], gls[acc][1], "Booking %s" % number,
                    gls[acc][2], "", 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                if gls[acc][1]:
                    data = [self.opts["conum"], self.vatctl, curdt, trdt, 1,
                        invno, batno, gls[acc][1], 0, "Booking %s" % number,
                        "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
        return True

    def getRef(self, number):
        rec = self.sql.getRec("bkmtrn", cols=["max(bkt_refno)"],
            where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
            "=", number), ("bkt_refno", "like", "%7s%s" % (number, "%"))],
            limit=1)
        if not rec or not rec[0]:
            num = 1
        else:
            num = int(rec[0][-2:]) + 1
        return "%7s%02i" % (number, num)

    def pageHeading(self):
        self.fpdf.drawText(self.cdes, x=7, font=["courier", "B", 24])
        self.fpdf.drawText(font=["courier", "B", 14])
        self.fpdf.drawText(self.hdes, x=7, font=["courier", "B", 16])
        if self.query == "Y":
            ides = "Queries Included"
        else:
            ides = "Queries Not Included"
        if self.rtyp == "A":
            if self.geninv == "Y":
                ides = "%s, Invoices Generated" % ides
            else:
                ides = "%s, Invoices Not Generated" % ides
        self.fpdf.drawText()
        self.fpdf.drawText(ides, x=7, font=["courier", "B", 16])
        if self.rtyp == "A":
            self.fpdf.drawText(font=["courier", "B", 12])
            self.printLine("%-25s" % "Name or Group",
                "%-25s" % "Unit Description", "Qty", "Arr",
                "Dep", "     Balance ", (8, 8, 8), fill=1)
        else:
            self.fpdf.drawText(font=["courier", "B", 12])
            self.printLine("%-25s" % "Unit Description",
                "%-25s" % "Name or Group", "Qty", "Arr",
                "Dep", "     Balance ", (8, 8, 8), fill=1)

    def getDate(self, date):
        if type(date) == str:
            date = int(date.replace("-", ""))
        yy = int(date / 10000)
        mm = int(date / 100) % 100
        dd = date % 100
        return "%s %s %s" % (dd, mthnam[mm][1], yy)

    def printLine(self, a, b, c, d, e, f, hh, bdr="TLB", fill=0):
        if self.rtyp == "H" and a is None:
            if hh[2] > 8:
                ctyp = "M"
            else:
                ctyp = "S"
        elif hh[0] > 8 or hh[1] > 8 or hh[2] > 8:
            ctyp = "M"
        else:
            ctyp = "S"
        ft = ["courier", "B", 12]
        self.fpdf.set_font(ft[0], ft[1], ft[2])
        w = self.fpdf.get_string_width("X" * 26)
        x = 7
        y = self.fpdf.get_y()
        if a:
            self.fpdf.drawText(a, x=x, y=y, w=w, h=hh[0], border=bdr,
                fill=fill, ctyp=ctyp, font=ft)
            if self.rtyp == "H" and not fill:
                return
        x += w
        w = self.fpdf.get_string_width("X" * 26)
        self.fpdf.drawText(b, x=x, y=y, w=w, h=hh[1], border=bdr,
            fill=fill, ctyp=ctyp, font=ft)
        x += w
        w = self.fpdf.get_string_width("X" * 4) + 1
        h = self.fpdf.get_y() - y
        if self.rtyp == "A":
            self.fpdf.drawText(c, x=x, y=y, w=w, h=h, border=bdr,
                align="R", fill=fill, font=ft)
        else:
            self.fpdf.drawText(c, x=x, y=y, w=w, h=hh[2], border=bdr,
                align="R", fill=fill, ctyp=ctyp, font=ft)
        ly = self.fpdf.get_y()
        if a or self.rtyp == "H":
            x += w
            w = self.fpdf.get_string_width("X" * 4)
            if self.rtyp == "A":
                self.fpdf.drawText(d, x=x, y=y, w=w, h=hh[2], border=bdr,
                    fill=fill, font=ft)
            else:
                self.fpdf.drawText(d, x=x, y=y, w=w, h=hh[2], border=bdr,
                    fill=fill, ctyp=ctyp, font=ft)
            x += w
            w = self.fpdf.get_string_width("X" * 4)
            if self.rtyp == "A":
                self.fpdf.drawText(e, x=x, y=y, w=w, h=hh[2], border=bdr,
                    fill=fill, font=ft)
            else:
                self.fpdf.drawText(e, x=x, y=y, w=w, h=hh[2], border=bdr,
                    fill=fill, ctyp=ctyp, font=ft)
            x += w
            w = self.fpdf.get_string_width("X" * 14)
            if self.rtyp == "A":
                self.fpdf.drawText(f, x=x, y=y, w=w, h=hh[2], border="TLRB",
                    fill=fill, font=ft)
            else:
                self.fpdf.drawText(f, x=x, y=y, w=w, h=hh[2], border="TLRB",
                    fill=fill, ctyp=ctyp, font=ft)
        self.fpdf.set_y(ly)

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
