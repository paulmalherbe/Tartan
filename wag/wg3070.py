"""
SYNOPSIS
    Salaries and Wages Payslips Reprinting.

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
from TartanClasses import ASD, GetCtl, PrintPayslip, Sql, TartanDialog
from tartanFunctions import getSingleRecords

class wg3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["tplmst", "wagctl", "wagmst",
            "wagtf1"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        wagctl = gc.getCtl("wagctl", self.opts["conum"])
        if not wagctl:
            return
        self.bestac = wagctl["ctw_bestac"]
        self.besttp = wagctl["ctw_besttp"]
        self.tplnam = wagctl["ctw_tplnam"]
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.etotal = 0
        self.empnos = []
        return True

    def mainProcess(self):
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "P"),
                ("tpm_system", "=", "WAG")],
            "order": "tpm_tname"}
        prd = {
            "stype": "R",
            "tables": ("wagtf1",),
            "cols": [
                ("wt1_date", "",  0, "Date"),
                ("wt1_freq", "",  0, "F")],
            "where": [("wt1_cono", "=", self.opts["conum"])],
            "group": "wt1_date, wt1_freq",
            "order": "wt1_date, wt1_freq"}
        r1s = (("Weekly","W"),("Fortnightly","F"),("Monthly","M"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),"INA",20,"Template Name","",
                self.tplnam,"N",self.doTplNam,tpm,None,None),
            (("T",0,1,0),"ID1",10,"Pay-Run Date","",
                "","N",self.doRunDate,prd,None,("efld",)),
            (("T",0,2,0),("IRB",r1s),0,"Frequency","Payment Frequency",
                "M","N",self.doFreq,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Whole File","",
                "N","N",self.doWhole,None,None,None),
            (("T",0,4,0),"IUI",1,"Department","",
                "","N",self.doDept,None,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("N","V"), mail=("B","Y"))

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "P"), ("tpm_system", "=", "WAG")], limit=1)
        if not acc:
            return "Invalid Template Name"
        self.tname = w

    def doRunDate(self, frt, pag, r, c, p, i, w):
        self.rundt = w

    def doFreq(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("wagtf1", where=[("wt1_cono", "=",
            self.opts["conum"]), ("wt1_date", "=", self.rundt),
            ("wt1_freq", "=", w)])
        if not chk:
            return "No Payslips for this Date and Frequency"
        self.freq = w

    def doWhole(self, frt, pag, r, c, p, i, w):
        self.whole = w
        if self.whole == "Y":
            self.dept = ""
            return "sk1"

    def doDept(self, frt, pag, r, c, p, i, w):
        self.dept = w

    def doEnd(self):
        self.df.closeProcess()
        # Export File for Bank
        if self.bestac:
            self.export = open(os.path.join(self.opts["mf"].rcdic["wrkdir"],
                "best%03d_%s.txt" % (self.opts["conum"], self.sysdtw)), "w")
            self.export.write("%1s%4s%-40s%8s%1s%8s%-15s%1s%2s%1s%9s%2s%4s"\
                "\r\n" % ("*", self.bestac, self.opts["conam"], self.sysdtw,
                "Y", "", "SALARIES EFT", "+", self.besttp, 0, "", "01",
                "LIVE"))
        else:
            self.export = None
        whr = [
            ("wgm_cono", "=", self.opts["conum"]),
            ("wgm_freq", "=", self.freq),
            ("wgm_term", "=", 0, "or", "wgm_term", ">=", self.rundt)]
        if self.dept:
            whr.append(("wgm_dept", "=", self.dept))
        if self.whole == "N":
            recs = getSingleRecords(self.opts["mf"], "wagmst",
                ("wgm_empno", "wgm_sname"), where=whr)
            for emp in recs:
                self.empnos.append(emp[1])
        else:
            recs = self.sql.getRec("wagmst", cols=["wgm_empno"],
                where=whr, order="wgm_empno")
            for emp in recs:
                self.empnos.append(emp[0])
        if self.empnos:
            self.doPrint()
            if self.export:
                value = int(round((self.etotal * 100), 0))
                self.export.write("%1s%4s%1s%30s%013u%47s\r\n" % \
                    (2, self.bestac, "T", "", value, ""))
                self.export.close()
        self.opts["mf"].closeLoop()

    def doPrint(self):
        psl = PrintPayslip(self.opts["mf"], self.opts["conum"],
            self.opts["conam"], self.empnos, self.rundt, progs="y",
            runtp="c", tname=self.tname, repprt=self.df.repprt,
            repeml=self.df.repeml, export=self.export, bestac=self.bestac)
        self.etotal = float(ASD(self.etotal) + ASD(psl.etotal))

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
