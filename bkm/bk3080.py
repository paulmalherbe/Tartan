"""
SYNOPSIS
    Reprinting of Booking Invoices.

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

from TartanClasses import PrintBookingInvoice, Sql, TartanDialog
from tartanFunctions import getSingleRecords

class bk3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bkmctl", "bkmmst", "bkmcon",
            "bkmtrn", "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        ctl = self.sql.getRec("bkmctl", where=[("cbk_cono", "=",
            self.opts["conum"])], limit=1)
        if not ctl:
            self.tplnam = "booking_invoice"
        else:
            self.tplnam = ctl[self.sql.bkmctl_col.index("cbk_invtpl")]
        return True

    def mainProcess(self):
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
        trn = {
            "stype": "R",
            "tables": ("bkmtrn", "bkmmst", "bkmcon"),
            "cols": [
                ("bkt_refno", "",  0, "Invoice-N"),
                ("bkt_date", "",  0, "Invoice-Dt"),
                ("bkt_number",  "", 0, "Booking"),
                ("bkc_sname",  "", 0, "Surname", "Y"),
                ("bkc_names",  "", 0, "Names", "F")],
            "where": [
                ("bkt_cono", "=", self.opts["conum"]),
                ("bkt_type", "=", 2),
                ("bkm_cono=bkt_cono",),
                ("bkm_number=bkt_number",),
                ("bkc_cono=bkt_cono",),
                ("bkc_ccode=bkm_ccode",)],
            "group": "bkt_refno",
            "screen": self.opts["mf"].body}
        r1s = (("Copies", "C"), ("Originals", "O"))
        r2s = (("Invoices","I"),("C/Notes", "C"))
        r3s = (("Range","R"),("Singles", "S"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Document Mode","",
                "C","N",self.doMode,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Document Type","",
                "I","N",self.doType,None,None,None),
            (("T",0,3,0),("IRB",r3s),0,"Documents","",
                "S","Y",self.doSelect,None,None,None),
            (("T",0,4,0),"INa",9,"From Number","From Document Number",
                "","N",self.doDocno,trn,None,("notzero",)),
            [("T",0,5,0),"INa",9,"To   Number","To Document Number",
                "","N",self.doDocno,trn,None,("notzero",)])
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doEnd, "y"),), txit=(self.doExit,),
            view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "BKM")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doMode(self, frt, pag, r, c, p, i, w):
        if w == "C":
            self.copy = "y"
        else:
            self.copy = "n"

    def doType(self, frt, pag, r, c, p, i, w):
        self.dtyp = w

    def doSelect(self, frt, pag, r, c, p, i, w):
        self.select = w
        if self.select == "S":
            self.frm = 0
            self.to = 0
            return "sk2"

    def doDocno(self, frt, pag, r, c, p, i, w):
        if w:
            doc = self.sql.getRec("bkmtrn", where=[("bkt_cono", "=",
                self.opts["conum"]), ("bkt_type", "=", 2), ("bkt_refno",
                "=", w)])
            if not doc:
                return "Document Number Does Not Exist"
        if p == 4:
            self.frm = w
            self.df.topf[pag][5][5] = self.frm
        elif w < self.frm:
            return "Document Number Before From Number"
        else:
            self.to = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["bkmtrn", "bkmmst", "bkmcon"]
        col = ["bkt_refno", "bkt_date", "bkc_sname", "bkc_names"]
        dic = {}
        for c in col:
            for t in tab:
                d = getattr(self.sql, "%s_dic" % t)
                if c in d:
                    dic[c] = d[c]
        if self.dtyp == "I":
            ttp = 2
        else:
            ttp = 6
        if self.select == "S":
            recs = self.sql.getRec(tables=tab, cols=col, where=[("bkt_cono",
                "=", self.opts["conum"]), ("bkt_type", "=", ttp),
                ("bkm_cono=bkt_cono",), ("bkm_number=bkt_number",),
                ("bkc_cono=bkt_cono",), ("bkc_ccode=bkm_ccode",)],
                group="bkt_refno, bkt_date, bkc_sname, bkc_names")
            recs = getSingleRecords(self.opts["mf"], tab, col, dic=dic,
                where=recs, ttype="D", selcol="bkc_sname")
        else:
            recs = self.sql.getRec("bkmtrn", cols=["bkt_refno"],
                where=[("bkt_cono", "=", self.opts["conum"]),
                ("bkt_type", "=", ttp), ("bkt_refno", ">=", self.frm),
                ("bkt_refno", "<=", self.to)], group="bkt_refno",
                order="bkt_refno")
        docs = []
        if recs:
            for rec in recs:
                docs.append(rec[0])
        if docs:
            PrintBookingInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], self.dtyp, docs, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml, copy=self.copy)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
