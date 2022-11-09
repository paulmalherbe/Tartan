"""
SYNOPSIS
    Salaries and Wages Master Report.

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

from TartanClasses import CCD, GetCtl, MyFpdf, RepPrt, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName

class wg3010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        return True

    def mainProcess(self):
        dep = {
            "stype": "R",
            "tables": ("ctldep",),
            "cols": (
                ("dep_code", "", 0, "Cod"),
                ("dep_name", "", 0, "Name", "Y")),
            "where": [("dep_cono", "=", self.opts["conum"])]}
        r1s = (("List","L"), ("Card","C"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Report Type","",
                "L","N",self.doRptTyp,None,None,None,None),
            (("T",0,1,0),"I@dep_code",0,"Department Code","",
                "","N",self.doDepCod,dep,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, view=("Y","V"), mail=("Y","Y"))

    def doRptTyp(self, frt, pag, r, c, p, i, w):
        self.typ = w
        if len(self.df.topEntry[0][2]) > 3:
            if self.typ == "C":
                state = "hide"
            else:
                state = "show"
            if len(self.df.topEntry[0][2]) == 5:
                self.df.setWidget(self.df.topEntry[0][2][4][0], state=state)
            self.df.setWidget(self.df.topEntry[0][2][3][0], state=state)

    def doDepCod(self, frt, pag, r, c, p, i, w):
        self.dep = w

    def doEnd(self):
        self.df.closeProcess()
        tabs = ["wagmst"]
        self.head = "Salaries and Wages - Employee Master Report"
        whr = [("wgm_cono", "=", self.opts["conum"])]
        if self.dep:
            whr.append(("wgm_dept", "=", self.dep))
            opts = "Dept: %s" % self.dep
        else:
            opts = None
        odr = "wgm_empno"
        if self.typ == "C":
            sql = Sql(self.opts["mf"].dbm, "wagmst",
                prog=self.__class__.__name__)
            recs = sql.getRec(tables=tabs, where=whr)
            if not recs:
                self.closeProcess()
                return
            col = sql.wagmst_col
            dic = sql.wagmst_dic
            self.fpdf = MyFpdf(name=self.__class__.__name__, head=80, auto=True)
            self.fpdf.header = self.doHead
            self.fpdf.set_font("Courier", "B", 12)
            cwth = self.fpdf.get_string_width("X")
            for rec in recs:
                self.fpdf.add_page()
                max1, max2 = 0, 0
                for c in col[:-1]:
                    if max1 < len(dic[c][4]):
                        max1 = len(dic[c][4])
                    if max2 < int(dic[c][3]):
                        max2 = int(dic[c][3])
                    self.fpdf.set_font("Courier", "B", 12)
                    self.fpdf.drawText(h=5, txt="%-20s" % dic[c][4], ln=0)
                    self.fpdf.set_font("Courier", "", 12)
                    if dic[c][4] == "Pay Frequency":
                        if rec[col.index(c)] == "F":
                            txt = "Fortnightly"
                        elif rec[col.index(c)] == "M":
                            txt = "Monthly"
                        else:
                            txt = "Weekly"
                        self.fpdf.drawText(h=5, x=cwth*40, txt=txt)
                    elif dic[c][4] == "Pay Type":
                        if rec[col.index(c)] == "C":
                            txt = "Cash"
                        elif rec[col.index(c)] == "Q":
                            txt = "Cheque"
                        else:
                            txt = "Electronic"
                        self.fpdf.drawText(h=5, x=cwth*40, txt=txt)
                    elif dic[c][4] == "Account Type":
                        if rec[col.index(c)] == "1":
                            txt = "Current"
                        elif rec[col.index(c)] == "2":
                            txt = "Transmission"
                        else:
                            txt = "Savings"
                        self.fpdf.drawText(h=5, x=cwth*40, txt=txt)
                    else:
                        self.fpdf.drawText(h=5, x=cwth*40,
                            txt=CCD(rec[col.index(c)],
                            dic[c][2], dic[c][3]).disp)
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, self.opts["conum"], ext="pdf")
            if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.head, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)
        else:
            cols = [
                ["wgm_empno",  "UI",  5, "EmpNo", "y"],
                ["wgm_sname",  "NA", 30, "Surname", "y"],
                ["wgm_fname",  "NA", 30, "Names", "y"],
                ["wgm_freq",  "UA", 1, "F", "y"],
                ["wgm_start",  "D1", 10, "Comm-Date", "y"],
                ["wgm_term",   "d1", 10, "Term-Date", "y"]]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                tables=tabs, heads=[self.head], cols=cols, where=whr,
                order=odr, opts=opts, repprt=self.df.repprt,
                repeml=self.df.repeml, fromad=self.fromad)
        self.closeProcess()

    def doHead(self):
        cdes = "%-30s" % self.opts["conam"]
        self.fpdf.drawText(cdes, font=["courier", "B", 24])
        self.fpdf.drawText(font=["courier", "B", 14])
        self.fpdf.drawText(self.head, font=["courier", "B", 16])
        self.fpdf.underLine(txt=self.head)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
