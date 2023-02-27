"""
SYNOPSIS
    Reprinting of Charges Documents.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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

from TartanClasses import PrintCharges, Sql, TartanDialog
from tartanFunctions import getSingleRecords

class dr3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["drsctl", "drsmst", "drsrci",
            "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        ctl = self.sql.getRec("drsctl", where=[("ctd_cono", "=",
            self.opts["conum"])], limit=1)
        if not ctl:
            self.tplnam = "sales_document"
        else:
            self.tplnam = ctl[self.sql.drsctl_col.index("ctd_chgtpl")]
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
                ("tpm_system", "=", "DRS")],
            "order": "tpm_tname"}
        rci = {
            "stype": "R",
            "tables": ("drsrci","drsmst"),
            "cols": [
                ("dci_docno", "",  0, "Doc-Num"),
                ("dci_date", "",  0, "Date"),
                ("dci_chain", "",  0, "Chn"),
                ("dci_acno",  "", 0, "Acc-Num"),
                ("drm_name",  "", 0, "Name", "Y")],
            "where": [
                ("dci_cono", "=", self.opts["conum"]),
                ("dci_cono=drm_cono",),
                ("dci_chain=drm_chain",),
                ("dci_acno=drm_acno",)],
            "screen": self.opts["mf"].body}
        r1s = (("Copies", "C"), ("Originals", "O"))
        r2s = (("Range","R"),("Singles", "S"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Document Mode","",
                "C","N",self.doMode,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Documents","",
                "S","Y",self.doSelect,None,None,None),
            (("T",0,3,0),"INA",9,"From Number","From Document Number",
                "","N",self.doDocno,rci,None,("notzero",)),
            [("T",0,4,0),"INA",9,"To   Number","To Document Number",
                "","N",self.doDocno,rci,None,("notzero",)])
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doEnd, "y"),), txit=(self.doExit,),
            view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "DRS")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doMode(self, frt, pag, r, c, p, i, w):
        if w == "C":
            self.copy = "y"
        else:
            self.copy = "n"

    def doType(self, frt, pag, r, c, p, i, w):
        self.typ = w

    def doSelect(self, frt, pag, r, c, p, i, w):
        self.select = w
        if self.select == "S":
            self.frm = 0
            self.to = 0
            return "sk2"

    def doDocno(self, frt, pag, r, c, p, i, w):
        if w:
            doc = self.sql.getRec("drsrci", where=[("dci_cono", "=",
                self.opts["conum"]), ("dci_docno", "=", w)])
            if not doc:
                return "Document Number Does Not Exist"
        if p == 3:
            self.frm = w
            self.df.topf[pag][4][5] = self.frm
        elif w < self.frm:
            return "Document Number Before From Number"
        else:
            self.to = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["drsrci", "drsmst"]
        col = ["dci_docno", "dci_date", "dci_chain", "dci_acno", "drm_name"]
        dic = {}
        for c in col:
            for t in tab:
                d = getattr(self.sql, "%s_dic" % t)
                if c in d:
                    dic[c] = d[c]
        docs = []
        if self.select == "S":
            recs = self.sql.getRec(tables=tab, cols=col, where=[("dci_cono",
                "=", self.opts["conum"]), ("drm_cono=dci_cono",),
                ("drm_chain=dci_chain",), ("drm_acno=dci_acno",)],
                order="dci_docno")
            recs = getSingleRecords(self.opts["mf"], tab, col, dic=dic,
                where=recs, ttype="D")
            if recs:
                for rec in recs:
                    docs.append(rec[0])
        else:
            recs = self.sql.getRec("drsrci", cols=["dci_docno"],
                where=[("dci_cono", "=", self.opts["conum"]),
                ("dci_docno", ">=", self.frm), ("dci_docno", "<=", self.to)])
            for rec in recs:
                docs.append(rec[0])
        if docs:
            PrintCharges(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], docs, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml,
                copy=self.copy)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
