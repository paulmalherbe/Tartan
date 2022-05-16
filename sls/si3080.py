"""
SYNOPSIS
    Reprinting of Sales Documents.

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

from TartanClasses import PrintInvoice, Sql, TartanDialog
from tartanFunctions import getSingleRecords

class si3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["slsctl", "slsiv1", "drsmst",
            "tplmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        ctl = self.sql.getRec("slsctl", where=[("ctv_cono", "=",
            self.opts["conum"])], limit=1)
        if not ctl:
            self.tplnam = "sales_document"
        else:
            self.tplnam = ctl[self.sql.slsctl_col.index("ctv_tplnam")]
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
                ("tpm_system", "=", "INV")],
            "order": "tpm_tname"}
        iv1 = {
            "stype": "R",
            "tables": ("slsiv1","drsmst"),
            "cols": [
                ("si1_docno", "",  0, "Doc-Num"),
                ("si1_date", "",  0, "Date"),
                ("si1_chain", "",  0, "Chn"),
                ("si1_acno",  "", 0, "Acc-Num"),
                ("drm_name",  "", 0, "Name", "Y")],
            "where": [
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_cono=drm_cono",),
                ("si1_chain=drm_chain",),
                ("si1_acno=drm_acno",),
                ("si1_invno", "<>", "cancel")],
            "whera": [["T", "si1_rtn", 2, 0]],
            "screen": self.opts["mf"].body}
        r1s = (("Copies", "C"), ("Originals", "O"))
        r2s = (
            ("Inv","I"),
            ("C-N","C"),
            ("S-O","O"),
            ("W-O","W"),
            ("Qte","Q"))
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
            (("T",0,4,0),"IUI",7,"From Number","From Document Number",
                "","N",self.doDocno,iv1,None,("notzero",)),
            [("T",0,5,0),"IUI",7,"To   Number","To Document Number",
                "","N",self.doDocno,iv1,None,("notzero",)])
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doEnd, "y"),), txit=(self.doExit,),
            view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "I"), ("tpm_system", "=", "INV")], limit=1)
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
            doc = self.sql.getRec("slsiv1", where=[("si1_cono", "=",
                self.opts["conum"]), ("si1_rtn", "=", self.typ), ("si1_docno",
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
        tab = ["slsiv1", "drsmst"]
        col = ["si1_docno", "si1_date", "si1_chain", "si1_acno", "drm_name"]
        dic = {}
        for c in col:
            for t in tab:
                d = getattr(self.sql, "%s_dic" % t)
                if c in d:
                    dic[c] = d[c]
        if self.select == "S":
            recs = self.sql.getRec(tables=tab, cols=col, where=[("si1_cono",
                "=", self.opts["conum"]), ("si1_rtn", "=", self.typ),
                ("si1_invno", "<>", "cancel"), ("drm_cono=si1_cono",),
                ("drm_chain=si1_chain",), ("drm_acno=si1_acno",)],
                order="si1_docno")
            recs = getSingleRecords(self.opts["mf"], tab, col, dic=dic,
                where=recs, ttype="D")
            iv1 = []
            if recs:
                for rec in recs:
                    iv1.append([rec[0]])
        else:
            iv1 = self.sql.getRec("slsiv1", cols=["si1_docno"],
            where=[
                ("si1_cono", "=", self.opts["conum"]),
                ("si1_rtn", "=", self.typ),
                ("si1_docno", ">=", self.frm),
                ("si1_docno", "<=", self.to)])
        if iv1:
            PrintInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], self.typ, iv1, tname=self.tname,
                repprt=self.df.repprt, repeml=self.df.repeml, copy=self.copy)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
