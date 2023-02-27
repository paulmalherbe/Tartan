"""
SYNOPSIS
    Salaries and Wages EMP201 Report.

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

from TartanClasses import ASD, CCD, GetCtl, MyFpdf, Sql, TartanDialog
from tartanFunctions import doPrinter, getModName

class wg3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagtxa", "wagedc", "wagmst",
            "wagtf2"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.fromad = wagctl["ctw_emadd"]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Salaries and Wages SARS EMP201 Report")
        fld = (
            (("T",0,0,0),"ID1",10,"Start Date","",
                "","N",self.doSDate,None,None,None),
            (("T",0,1,0),"ID1",10,"End Date","",
                "","N",self.doEDate,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("Y","N"))

    def doSDate(self, frt, pag, r, c, p, i, w):
        self.sdatew = w
        self.sdated = self.df.t_disp[pag][0][i]

    def doEDate(self, frt, pag, r, c, p, i, w):
        if w < self.sdatew:
            return "Invalid Date"
        self.edatew = w
        self.edated = self.df.t_disp[pag][0][i]
        yr = int(w / 10000)
        mt = int(w / 100) % 100
        if mt > 2:
            yr += 1
        self.txa = self.sql.getRec("wagtxa",
            where=[("wta_year", "=", yr)], limit=1)

    def doEnd(self):
        self.df.closeProcess()
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        self.head = "%03u %-80s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        cod = self.sql.getRec("wagedc", cols=["ced_code"],
            where=[("ced_cono", "=", self.opts["conum"]), ("ced_type",
            "=", "E"), ("ced_taxcode", "<>", "N")])
        txbl = 0
        for c in cod:
            pay = self.sql.getRec("wagtf2", cols=["sum(wt2_eamt)"],
                where=[("wt2_cono", "=", self.opts["conum"]), ("wt2_type",
                "=", "E"), ("wt2_code", "=", c[0]), ("wt2_date", "between",
                self.sdatew, self.edatew)], limit=1)
            if pay and pay[0]:
                txbl = float(ASD(txbl) + ASD(pay[0]))
        amt = self.sql.getRec("wagtf2", cols=["sum(wt2_eamt)"],
            where=[("wt2_cono", "=", self.opts["conum"]), ("wt2_type",
            "=", "D"), ("wt2_code", "=", 1), ("wt2_date", "between",
            self.sdatew, self.edatew)], limit=1)
        if amt and amt[0]:
            paye = amt[0]
        else:
            paye = 0
        cod = self.sql.getRec("wagedc", cols=["ced_code",
            "ced_sdlportion"], where=[("ced_cono", "=", self.opts["conum"]),
            ("ced_type", "=", "E"), ("ced_sdlportion", "<>", 0)])
        sdl = 0
        emp = {}
        for c in cod:
            pay = self.sql.getRec("wagtf2", cols=["wt2_empno",
                "sum(wt2_eamt)"], where=[("wt2_cono", "=", self.opts["conum"]),
                ("wt2_type", "=", "E"), ("wt2_code", "=", c[0]), ("wt2_date",
                "between", self.sdatew, self.edatew)], group="wt2_empno")
            for p in pay:
                if p[1]:
                    num = p[0]
                    edl = (p[1] * c[1]) / 100.0
                    sdl = float(ASD(sdl) + ASD(edl))
                    if num not in emp:
                        emp[num] = [p[1], edl]
                    else:
                        emp[num][0] = float(ASD(emp[num][0]) + ASD(p[1]))
                        emp[num][1] = float(ASD(emp[num][1]) + ASD(edl))
        uifr = float(ASD(self.txa[6]) + ASD(self.txa[7]))
        uifa = 0
        uifp = 0
        cod = self.sql.getRec("wagedc", cols=["ced_code", "ced_eamt",
            "ced_ramt"], where=[("ced_cono", "=", self.opts["conum"]),
            ("ced_type", "=", "D"), ("ced_ebase", "=", 6)], limit=1)
        if cod:
            amt = self.sql.getRec("wagtf2", cols=["sum(wt2_eamt)",
                "sum(wt2_ramt)"], where=[("wt2_cono", "=", self.opts["conum"]),
                ("wt2_type", "=", "D"), ("wt2_code", "=", cod[0]),
                ("wt2_date", "between", self.sdatew, self.edatew)], limit=1)
            if amt and amt[0]:
                uifa = float(ASD(uifa) + ASD(amt[0]) + ASD(amt[1]))
        txbl = CCD(txbl, "SD", 13.2)
        paye = CCD(paye, "SD", 13.2)
        sdlp = CCD(sdl, "SD", 13.2)
        sdla = CCD((int(sdl) / 100.0), "SD", 13.2)
        if uifa:
            uifa = CCD(uifa, "SD", 13.2)
            uifp = CCD(int(uifa.work * 100.0) / uifr, "SD", 13.2)
        else:
            uifa = CCD(0, "SD", 13.2)
            uifp = CCD(0, "SD", 13.2)
        # Print the Report
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-29s %-10s %-2s %-10s" % \
            ("SARS EMP201 Report for period", self.sdated, "to", self.edated))
        self.fpdf.drawText()
        self.fpdf.drawText("%-43s %12s %13s %13s" % \
            ("Details", "PAYE", "SDL", "UIF"))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.fpdf.drawText("%-43s %13s %13s %13s" % \
            ("Remuneration/Leviable Amount", txbl.disp, sdlp.disp, uifp.disp))
        self.fpdf.drawText()
        self.fpdf.drawText("%-43s %13s %13s %13s" % \
            ("Amounts Payable", paye.disp, sdla.disp, uifa.disp))
        self.fpdf.drawText()
        totl = CCD(float(ASD(paye.work) + ASD(sdla.work) + ASD(uifa.work)),
            "SD", 13.2)
        self.fpdf.drawText("%-71s %13s" % ("Control Total", totl.disp))
        self.fpdf.drawText()
        self.fpdf.drawText("Summary of SDL Payment", font="B")
        self.fpdf.underLine(txt="X" * 84)
        keys = list(emp.keys())
        keys.sort()
        for k in keys:
            name = self.sql.getRec("wagmst", cols=["wgm_sname",
                "wgm_fname"], where=[("wgm_cono", "=", self.opts["conum"]),
                ("wgm_empno", "=", k)], limit=1)
            n = "%s, %s" % (name[0].strip(), name[1].strip())
            t = CCD(emp[k][0], "SD", 13.2)
            s = CCD((int(emp[k][1]) / 100.0), "SD", 13.2)
            self.fpdf.drawText("%2s %-54s %13s %13s" % (k, n, t.disp, s.disp))
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header=self.tit, repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
