"""
SYNOPSIS
    Sales By Product Report.

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
from TartanClasses import ASD, Balances, CCD, GetCtl, MyFpdf, ProgressBar, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doWriteExport, getModName, doPrinter, showError

class si3020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strloc", "strmf1"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        slsctl = gc.getCtl("slsctl", self.opts["conum"])
        if not slsctl:
            return
        self.fromad = slsctl["ctv_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.colsh = [["", "", "", "",
            ["*********** Month to Date **********", 4, 7],
            ["*********** Year To Date ***********", 8, 11]]]
        self.colsh.append(["Grp", "Product-Code", "Description", "U.O.I",
            "Quantity", "Value", "Profit", "Prft-%", "Quantity", "Value",
            "Profit", "Prft-%"])
        self.forms = [("UA", 3), ("NA", 20), ("NA", 30), ("NA", 10), ("SI", 9),
            ("SI", 9), ("SI", 9), ("SD", 7.2), ("SI", 9), ("SI", 9), ("SI", 9),
            ("SD", 7.2)]
        self.stot = [0] * 6
        self.gtot = [0] * 6
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Sales By Product Report (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        grp = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", ""]
            view = ("Y","V")
            mail = ("Y","N")
        fld = (
            (("T",0,0,0),"ID2",7,"Cut-Off Period","",
                int(self.sysdtw / 100),"Y",self.doCut,None,None,("efld",)),
            (("T",0,1,0),"IUA",1,"Location","",
                var[1],"N",self.doLoc,loc,None,("efld",)),
            (("T",0,2,0),"IUA",3,"Product Group","",
                var[2],"N",self.doGroup,grp,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doCut(self, frt, pag, r, c, p, i, w):
        self.cutoff = w
        self.cutper = self.df.t_disp[pag][r][p]
        if self.locs == "N":
            self.loc = ""
            self.locd = "ALL"
            return "sk1"

    def doLoc(self, frt, pag, r, c, p, i, w):
        if not w:
            self.locd = "ALL"
        else:
            acc = self.sql.getRec("strloc", cols=["srl_desc"],
                where=[("srl_cono", "=", self.opts["conum"]), ("srl_loc", "=",
                w)], limit=1)
            if not acc:
                return "Invalid Location"
            self.locd = "%s %s" % (w, acc[0])
        self.loc = w

    def doGroup(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.getGroup(w)
            if not acc:
                return "Invalid Group"
        self.group = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.group:
            sgrp = ""
            egrp = "zzz"
        else:
            sgrp = egrp = self.group
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=[("st1_cono", "=",
            self.opts["conum"]), ("st1_group", ">=", sgrp), ("st1_group", "<=",
            egrp)], order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        elif self.df.repprt[2] == "export":
            self.exportReport(recs)
        else:
            self.printReport(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def exportReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        expnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.opts["conum"])
        self.expheads = ["%03u %-30s %s" % (self.opts["conum"],
            self.opts["conam"], self.sysdttm)]
        self.expheads.append("Sales Report By Product up to %s" % self.cutper)
        self.expcolsh = self.colsh
        self.expforms = self.forms
        self.expdatas = []
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                p.closeProgress()
                return
            vals = self.getValues(dat)
            if not vals:
                continue
            code, desc, uoi, mq, ms, mp, mn, yq, ys, yp, yn = vals
            self.expdatas.append(["BODY", [self.grp.work, code.work, desc.work,
                uoi.work, mq.work, ms.work, mp.work, mn.work, yq.work, ys.work,
                yp.work, yn.work]])
        p.closeProgress()
        self.grandTotal()
        doWriteExport(xtype=self.df.repprt[1], name=expnam,
            heads=self.expheads, colsh=self.expcolsh, forms=self.expforms,
            datas=self.expdatas, rcdic=self.opts["mf"].rcdic)

    def printReport(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-138s" % (self.opts["conum"], self.opts["conam"])
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        lstgrp = ""
        self.pglin = 999
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            vals = self.getValues(dat)
            if not vals:
                continue
            if lstgrp and lstgrp != self.grp.work:
                self.groupTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            code, desc, uoi, mq, ms, mp, mn, yq, ys, yp, yn = vals
            self.fpdf.drawText("%s %s %s %s %s %s %s     %s %s %s %s" % \
                (code.disp, desc.disp, uoi.disp, mq.disp, ms.disp,
                mp.disp, mn.disp, yq.disp, ys.disp, yp.disp, yn.disp))
            self.stot[0] = float(ASD(self.stot[0]) + ASD(mq.work))
            self.stot[1] = float(ASD(self.stot[1]) + ASD(ms.work))
            self.stot[2] = float(ASD(self.stot[2]) + ASD(mp.work))
            self.stot[3] = float(ASD(self.stot[3]) + ASD(yq.work))
            self.stot[4] = float(ASD(self.stot[4]) + ASD(ys.work))
            self.stot[5] = float(ASD(self.stot[5]) + ASD(yp.work))
            self.pglin += 1
            lstgrp = self.grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.groupTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                self.fpdf.output(pdfnam, "F")
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                    fromad=self.fromad, repeml=self.df.repeml)

    def getValues(self, data):
        self.grp = CCD(data[0], "UA", 3)
        code = CCD(data[1], "NA", 20)
        desc = CCD(data[2], "NA", 30)
        uoi = CCD(data[3], "NA", 10)
        bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
            self.cutoff, keys=(self.grp.work, code.work, self.loc,
            ("P", self.opts["period"][0])))
        m_ob, m_mv, m_cb, y_ob, y_mv, y_cb, ac, lc, ls = bals.doStrBals()
        m_qty = 0
        m_cst = 0
        m_sls = 0
        for t, q, c, s in m_mv:
            if t == 7:
                m_qty = q
                m_cst = c
                m_sls = s
                break
        y_qty = 0
        y_cst = 0
        y_sls = 0
        for t, q, c, s in y_mv:
            if t == 7:
                y_qty = q
                y_cst = c
                y_sls = s
                break
        mq = CCD(float(ASD(0) - ASD(m_qty)), "SI", 9)
        mc = CCD(float(ASD(0) - ASD(m_cst)), "SI", 9)
        ms = CCD(float(ASD(0) - ASD(m_sls)), "SI", 9)
        mp = float(ASD(ms.work) - ASD(mc.work))
        mp = CCD(mp, "SI", 9)
        if ms.work == 0:
            mn = 0
        else:
            mn = round((mp.work * 100 / ms.work), 2)
        mn = CCD(mn, "SD", 7.2)
        yq = CCD(float(ASD(0) - ASD(y_qty)), "SI", 9)
        yc = CCD(float(ASD(0) - ASD(y_cst)), "SI", 9)
        ys = CCD(float(ASD(0) - ASD(y_sls)), "SI", 9)
        yp = float(ASD(ys.work) - ASD(yc.work))
        yp = CCD(yp, "SI", 9)
        if not ys.work:
            yn = 0
        else:
            yn = round((yp.work * 100.0 / ys.work), 2)
        yn = CCD(yn, "SD", 7.2)
        if mq.work == 0 and mc.work == 0 and ms.work == 0 and \
                yq.work == 0 and yc.work == 0 and ys.work == 0:
            return
        self.gtot[0] = float(ASD(self.gtot[0]) + ASD(mq.work))
        self.gtot[1] = float(ASD(self.gtot[1]) + ASD(ms.work))
        self.gtot[2] = float(ASD(self.gtot[2]) + ASD(mp.work))
        self.gtot[3] = float(ASD(self.gtot[3]) + ASD(yq.work))
        self.gtot[4] = float(ASD(self.gtot[4]) + ASD(ys.work))
        self.gtot[5] = float(ASD(self.gtot[5]) + ASD(yp.work))
        return (code, desc, uoi, mq, ms, mp, mn, yq, ys, yp, yn)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("%-29s %-7s" % \
            ("Sales Report By Product up to", self.cutper))
        self.fpdf.drawText()
        acc = self.getGroup(self.grp.work)
        if acc:
            grpd = acc[0]
        else:
            grpd = "Missing Group Record"
        self.fpdf.drawText("%s %s %s     %s %s" % \
            ("Group:", self.grp.disp, grpd, "Location:", self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-62s %-36s %-5s%-36s " % ("",
            "*********** Month T0 Date **********", "",
            "*********** Year To Date ***********"))
        self.fpdf.drawText("%-20s %-30s %-10s %9s %9s %9s %7s     "\
            "%9s %9s %9s %7s" % ("Product-Code", "Description", "U.O.I",
            "Quantity ", "Value ", "Profit ", "Prft-% ",
            "Quantity ", "Value ", "Profit ", "Prft-% "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 9

    def getGroup(self, grp):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            grp)], limit=1)
        return acc

    def groupTotal(self):
        self.fpdf.drawText()
        mq = CCD(self.stot[0], "SI", 9)
        ms = CCD(self.stot[1], "SI", 9)
        mp = CCD(self.stot[2], "SI", 9)
        if ms.work == 0:
            mn = 0
        else:
            mn = round((mp.work * 100 / ms.work), 2)
        mn = CCD(mn, "SD", 7.2)
        yq = CCD(self.stot[3], "SI", 9)
        ys = CCD(self.stot[4], "SI", 9)
        yp = CCD(self.stot[5], "SI", 9)
        if ys.work == 0:
            yn = 0
        else:
            yn = round((yp.work * 100 / ys.work), 2)
        yn = CCD(yn, "SD", 7.2)
        self.fpdf.drawText("%-20s %-41s %s %s %s %s     %s %s %s %s" % \
            ("", "Group Totals", mq.disp, ms.disp, mp.disp, mn.disp,
            yq.disp, ys.disp, yp.disp, yn.disp))
        self.stot = [0] * 6

    def grandTotal(self):
        mq = CCD(self.gtot[0], "SI", 9)
        ms = CCD(self.gtot[1], "SI", 9)
        mp = CCD(self.gtot[2], "SI", 9)
        if ms.work == 0:
            mn = 0
        else:
            mn = round((mp.work * 100 / ms.work), 2)
        mn = CCD(mn, "SD", 7.2)
        yq = CCD(self.gtot[3], "SI", 9)
        ys = CCD(self.gtot[4], "SI", 9)
        yp = CCD(self.gtot[5], "SI", 9)
        if ys.work == 0:
            yn = 0
        else:
            yn = round((yp.work * 100 / ys.work), 2)
        yn = CCD(yn, "SD", 7.2)
        if self.df.repprt[2] == "export":
            self.expdatas.append(["ULINES"])
            self.expdatas.append(["TOTAL", ["", "", "Grand Totals", "",
                mq.work, ms.work, mp.work, mn.work, yq.work, ys.work, yp.work,
                yn.work]])
            self.expdatas.append(["ULINED"])
            return
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-41s %s %s %s %s     %s %s %s %s" % \
            ("", "Grand Totals", mq.disp, ms.disp, mp.disp, mn.disp,
            yq.disp, ys.disp, yp.disp, yn.disp))

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
