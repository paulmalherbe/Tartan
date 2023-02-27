"""
SYNOPSIS
    Salaries and Wages Summary Report.

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
from tartanFunctions import doPrinter, doWriteExport, getModName

class wg3080(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["wagedc", "wagmst", "wagtf2"],
            prog=self.__class__.__name__)
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
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSDate(self, frt, pag, r, c, p, i, w):
        self.sdatew = w
        self.sdated = self.df.t_disp[pag][0][i]

    def doEDate(self, frt, pag, r, c, p, i, w):
        if w < self.sdatew:
            return "Invalid Period"
        self.edatew = w
        self.edated = self.df.t_disp[pag][0][i]
        sttp = self.sdatew // 100
        endp = self.edatew // 100
        self.mths = []
        while True:
            self.mths.append(sttp)
            if sttp == endp:
                break
            yr = sttp // 100
            mt = sttp % 100
            mt += 1
            if mt > 12:
                yr += 1
                mt = 1
            sttp = (yr * 100) + mt

    def doEnd(self):
        self.df.closeProcess()
        data = self.getValues()
        if self.df.repprt[2] == "export":
            self.exportReport(data)
        else:
            self.printReport(data)
        self.opts["mf"].closeLoop()

    def exportReport(self, data):
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        expheads = ["%s - Salaries Summary from %s to %s" %
            (self.opts["conam"], self.sdated, self.edated)]
        expcolsh = [["Earning/Deduction"]]
        expforms = [("NA", 30)]
        for mth in self.mths:
            expcolsh[0].append(CCD(mth, "D2", 7).disp)
            expforms.append(("SD", 10.2))
        expdatas = []
        for emp in data:
            name = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
                where=[("wgm_cono", "=", self.opts["conum"]),
                ("wgm_empno", "=", emp)], limit=1)
            heads = expheads[:]
            heads.append("%s, %s" % tuple(name))
            expdatas.append(["PAGE", [heads, expcolsh]])
            expdatas.append(["ULINES"])
            etot = ["Total Net"] + ([0] * len(self.mths))
            for r in data[emp]:
                for l in data[emp][r]:
                    expdatas.append(["BODY", data[emp][r][l]])
                    for num, amt in enumerate(data[emp][r][l]):
                        if not num:
                            continue
                        if r == "E":
                            etot[num] = float(ASD(etot[num]) + ASD(amt))
                        else:
                            etot[num] = float(ASD(etot[num]) - ASD(amt))
            expdatas.append(["ULINES"])
            expdatas.append(["BODY", etot])
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=expheads, colsh=expcolsh, forms=expforms,
            datas=expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, data):
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"], ext="pdf")
        spc = 30 + (len(self.mths) * 11)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=spc)
        dsc = "%-30s"
        for _ in range(len(self.mths)):
            dsc += " %s"
        gtot = ["Grand Total"] + ([0] * len(self.mths))
        for emp in data:
            name = self.sql.getRec("wagmst", cols=["wgm_sname", "wgm_fname"],
                where=[("wgm_cono", "=", self.opts["conum"]),
                ("wgm_empno", "=", emp)], limit=1)
            self.fpdf.add_page()
            self.fpdf.drawText(self.opts["conam"], font=["B", 20])
            self.fpdf.drawText()
            self.fpdf.drawText("Salaries Summary from %s to %s" %
                (self.sdated, self.edated), font=["B", 16])
            self.fpdf.drawText()
            self.fpdf.drawText("Employee: %-s, %-s" % (name[0], name[1]),
                font=["B", 14])
            self.fpdf.drawText()
            txt = "%-30s" % "Earning/Deduction"
            for mth in self.mths:
                txt = "%s %9s " % (txt, CCD(mth, "D2", 7).disp)
            self.fpdf.drawText(txt, font="B")
            self.fpdf.underLine()
            reps = data[emp]
            etot = ["Total Net"] + ([0] * len(self.mths))
            for r in reps:
                for l in reps[r]:
                    wrk = reps[r][l][:]
                    for n, w in enumerate(reps[r][l]):
                        if not n:
                            wrk[n] = CCD(w, "NA", 30).disp
                        else:
                            wrk[n] = CCD(w, "SD", 10.2).disp
                            if r == "E":
                                etot[n] = float(ASD(etot[n]) + ASD(w))
                                gtot[n] = float(ASD(gtot[n]) + ASD(w))
                            else:
                                etot[n] = float(ASD(etot[n]) - ASD(w))
                                gtot[n] = float(ASD(gtot[n]) - ASD(w))
                    self.fpdf.drawText(dsc % tuple(wrk), font="")
            self.fpdf.underLine()
            wrk = etot[:]
            for n, w in enumerate(wrk):
                if not n:
                    etot[n] = CCD(w, "NA", 30).disp
                else:
                    etot[n] = CCD(w, "SD", 10.2).disp
            self.fpdf.drawText(dsc % tuple(etot), font="B")
        self.fpdf.underLine()
        wrk = gtot[:]
        for n, w in enumerate(wrk):
            if not n:
                gtot[n] = CCD(w, "NA", 30).disp
            else:
                gtot[n] = CCD(w, "SD", 10.2).disp
        self.fpdf.drawText(dsc % tuple(gtot), font="B")
        if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], conum=self.opts["conum"], pdfnam=pdfnam,
                header=self.tit, repprt=self.df.repprt, fromad=self.fromad,
                repeml=self.df.repeml)

    def getValues(self):
        data = {}
        emps = self.sql.getRec("wagmst", cols=["wgm_empno"],
            where=[("wgm_cono", "=", self.opts["conum"])], order="wgm_empno")
        for emp in emps:
            recs = self.sql.getRec("wagtf2", where=[("wt2_cono", "=",
                self.opts["conum"]), ("wt2_empno", "=", emp[0]),
                ("wt2_date", "between", self.sdatew, self.edatew)],
                order="wt2_date, wt2_type desc, wt2_code")
            if recs:
                data[emp[0]] = {"E": {}, "D": {}}
                cods = self.sql.getRec("wagtf2", cols=["wt2_type",
                    "wt2_code"], where=[("wt2_cono", "=", self.opts["conum"]),
                    ("wt2_empno", "=", emp[0]), ("wt2_date", "between",
                    self.sdatew, self.edatew)], group="wt2_type, wt2_code",
                    order="wt2_type desc, wt2_code")
                work = cods[:]
                for cod in work:
                    desc = self.sql.getRec("wagedc", cols=["ced_desc",
                        "ced_taxcode"], where=[("ced_cono", "=",
                        self.opts["conum"]), ("ced_type", "=", cod[0]),
                        ("ced_code", "=", cod[1])], limit=1)
                    if desc[1] == "T":
                        cods.remove(cod)
                    else:
                        data[emp[0]][cod[0]][cod[1]] = \
                            [desc[0]]+([0]*len(self.mths))
                for rec in recs:
                    dte = rec[self.sql.wagtf2_col.index("wt2_date")]
                    typ = rec[self.sql.wagtf2_col.index("wt2_type")]
                    cod = rec[self.sql.wagtf2_col.index("wt2_code")]
                    if [typ, cod] not in cods:
                        continue
                    amt = rec[self.sql.wagtf2_col.index("wt2_eamt")]
                    cdt = dte // 100
                    idx = self.mths.index(cdt) + 1
                    tot = data[emp[0]][typ][cod][idx]
                    data[emp[0]][typ][cod][idx] = float(ASD(tot) + ASD(amt))
        return data

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
