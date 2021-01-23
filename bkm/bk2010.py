"""
SYNOPSIS
    Booking Invoice Raising.

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
from TartanClasses import ASD, GetCtl, PrintBookingInvoice, Sql, TartanDialog
from tartanFunctions import getSingleRecords, getVatRate

class bk2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
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
            setattr(self, "%s" % col, ctl[col])
        if self.ctm_logo and "LETTERHEAD" in os.environ:
            self.ctm_logo = os.environ["LETTERHEAD"]
        if not self.ctm_logo or not os.path.exists(self.ctm_logo):
            self.ctm_logo = None
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.glint = bkmctl["cbk_glint"]
        self.tplnam = bkmctl["cbk_invtpl"]
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
            "Booking Invoices (%s)" % self.__class__.__name__)
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
        r1s = (("Yes","Y"), ("No","N"))
        r2s = (("Singles","S"), ("All","A"))
        fld = (
            (("T",0,0,0),"Id1",10,"Starting Date","",
                0,"Y",self.doSDate,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Ending Date","",
                self.sysdtw,"Y",self.doEDate,None,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Include Queries","",
                "N","Y",self.doBkmQry,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Bookings","",
                "S","Y",self.doBkmDoc,None,None,None),
            (("T",0,4,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("N","Y"))

    def doSDate(self, frt, pag, r, c, p, i, w):
        self.sdate = w

    def doEDate(self, frt, pag, r, c, p, i, w):
        self.edate = w

    def doBkmQry(self, frt, pag, r, c, p, i, w):
        self.bkmqry = w

    def doBkmDoc(self, frt, pag, r, c, p, i, w):
        self.bkmdoc = w

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "BKM")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["bkmmst", "bkmcon", "bkmrtt"]
        col = ["bkm_number", "bkc_sname", "bkc_names", "bkm_arrive"]
        whr = [("bkm_cono", "=", self.opts["conum"])]
        if self.bkmqry == "N":
            whr.append(("bkm_state", "in", ("C", "S")))
        else:
            whr.append(("bkm_state", "in", ("C", "Q", "S")))
        whr.extend([
            ("bkm_arrive", "between", self.sdate, self.edate),
            ("bkc_cono=bkm_cono",), ("bkc_ccode=bkm_ccode",),
            ("brt_cono=bkm_cono",), ("brt_number=bkm_number",),
            ("brt_invno", "=", 0)])
        grp = "bkm_number, bkm_arrive, bkm_ccode, bkc_sname, bkc_names"
        odr = "bkm_arrive, bkm_ccode"
        dic = {}
        for c in col:
            for t in tab:
                d = getattr(self.sql, "%s_dic" % t)
                if c in d:
                    dic[c] = d[c]
        if self.bkmdoc == "S":
            recs = self.sql.getRec(tables=tab, cols=col, where=whr,
                group=grp, order=odr)
            recs = getSingleRecords(self.opts["mf"], tab, col, dic=dic,
                where=recs, ttype="D")
        else:
            recs = self.sql.getRec(tables=tab, cols=col, where=whr,
                group=grp, order=odr)
        docs = []
        for rec in recs:
            # Raise the Invoice
            bkno = rec[0]
            trdt = rec[3]
            incamt = 0
            vatamt = 0
            curdt = int(trdt / 100)
            batno = "B%s" % curdt
            gls = {}
            trns = self.sql.getRec("bkmrtt", where=[("brt_cono",
                "=", self.opts["conum"]), ("brt_number", "=", bkno),
                ("brt_invno", "=", 0)])
            if not trns:
                continue
            invno = self.getRef(bkno)
            for trn in trns:
                utyp = trn[self.sql.bkmrtt_col.index("brt_utype")]
                ucod = trn[self.sql.bkmrtt_col.index("brt_ucode")]
                rcod = trn[self.sql.bkmrtt_col.index("brt_rcode")]
                rbas = trn[self.sql.bkmrtt_col.index("brt_rbase")]
                quan = trn[self.sql.bkmrtt_col.index("brt_quant")]
                rate = trn[self.sql.bkmrtt_col.index("brt_arate")]
                days = trn[self.sql.bkmrtt_col.index("brt_bdays")]
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
                data = [self.opts["conum"], bkno, 2, invno, batno, trdt,
                    inca, vata, curdt, "Booking %s-%s Raised" % (utyp, ucod),
                    vatc, "", self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("bkmtrn", data=data)
                self.sql.updRec("bkmrtt", cols=["brt_vrate", "brt_invno",
                    "brt_invdt"], data=[vrte, invno, trdt],
                    where=[("brt_cono", "=", self.opts["conum"]),
                    ("brt_number", "=", bkno), ("brt_utype", "=", utyp),
                    ("brt_ucode", "=", ucod), ("brt_rcode", "=", rcod)])
                if vata:
                    exc = float(ASD(0) - ASD(exca))
                    vat = float(ASD(0) - ASD(vata))
                    data = [self.opts["conum"], vatc, "O", curdt, "B", 1, batno,
                        invno, trdt, bkno, "Booking %s" % bkno, exc, vat, 0,
                        self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("ctlvtf", data=data)
            if self.glint == "Y":
                data = [self.opts["conum"], self.bkmctl, curdt, trdt, 1, invno,
                    batno, incamt, 0, "Booking %s" % bkno, "", "", 0,
                    self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                for acc in gls:
                    data = [self.opts["conum"], acc, curdt, trdt, 1, invno,
                        batno, gls[acc][0], gls[acc][1], "Booking %s" % bkno,
                        gls[acc][2], "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                    if gls[acc][1]:
                        data = [self.opts["conum"], self.vatctl, curdt, trdt, 1,
                            invno, batno, gls[acc][1], 0, "Booking %s" % bkno,
                            "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                        self.sql.insRec("gentrn", data=data)
            if invno not in docs:
                docs.append(invno)
        self.opts["mf"].dbm.commitDbase()
        if docs:
            PrintBookingInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], "I", docs, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml, copy="O")
        self.doExit()

    def getRef(self, bkno):
        rec = self.sql.getRec("bkmtrn", cols=["max(bkt_refno)"],
            where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
            "=", bkno), ("bkt_refno", "like", "%7s%s" % (bkno, "%"))],
            limit=1)
        if not rec or not rec[0]:
            num = 1
        else:
            num = int(rec[0][-2:]) + 1
        return "%7s%02i" % (bkno, num)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
