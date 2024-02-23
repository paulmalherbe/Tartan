"""
SYNOPSIS
    Period Sales By Product Report

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

import datetime, time
from TartanClasses import ASD, CCD, GetCtl, MyFpdf, ProgressBar, RepPrt, Sql
from TartanClasses import TartanDialog
from tartanFunctions import doPrinter, getModName, mthendDate, showError

class si3030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strgrp", "strloc", "strmf1",
            "strtrn"], prog=self.__class__.__name__)
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
        self.head = "%03u %-108s" % (self.opts["conum"], self.opts["conam"])
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Period Sales By Product Report (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        grp = {
            "stype": "S",
            "tables": ("strgrp",),
            "cols": ("gpm_group", "gpm_desc"),
            "where": [("gpm_cono", "=", self.opts["conum"])],
            "order": "gpm_group"}
        if "args" in self.opts and "noprint" in self.opts["args"]:
            var = self.opts["args"]["work"][0]
            view = None
            mail = None
        else:
            var = ["", "", "", "N", "Y", "N"]
            view = ("N","V")
            mail = ("Y","N")
        r1s = (("No", "N"), ("Yes", "Y"))
        fld = (
            (("T",0,0,0),"ID2",7,"Period","",
                int(self.sysdtw / 100),"Y",self.doPer,None,None,("efld",)),
            (("T",0,1,0),"IUA",1,"Location","",
                var[1],"N",self.doLoc,loc,None,("efld",)),
            (("T",0,2,0),"ITX",30,"Product Groups","",
                var[2],"N",self.doGrps,grp,None,None,None,
                "Enter group codes separated by commas e.g. LAZ,LCO"),
            (("T",0,3,0),("IRB",r1s),0,"Weekly","",
                var[3],"N",self.doType,None,None,None),
            (("T",0,4,0),("IRB",r1s),0,"Include Quantity","",
                var[4],"N",self.doValue,None,None,None),
            (("T",0,5,0),("IRB",r1s),0,"Include Profit","",
                var[5],"N",self.doValue,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=view, mail=mail)

    def doPer(self, frt, pag, r, c, p, i, w):
        if w < int(self.opts["period"][1][0] / 100) or \
                w > int(self.opts["period"][2][0] / 100):
            return "Invalid Period"
        self.per = w
        self.perd = CCD(self.per, "D2", 7).disp
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

    def doGrps(self, frt, pag, r, c, p, i, w):
        try:
            grp = eval(w)
            self.grps = ""
            for g in grp:
                if not self.grps:
                    self.grps = g[1]
                else:
                    self.grps = "%s,%s" % (self.grps, g[1])
        except:
            self.grps = w
        self.df.loadEntry(frt, pag, p, data=self.grps)
        if not self.grps:
            return
        check = self.grps.split(",")
        err = None
        for chk in check:
            acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
                where=[("gpm_cono", "=", self.opts["conum"]),
                ("gpm_group", "=", chk)], limit=1)
            if not acc:
                err = "Invalid Group %s" % chk
                break
        return err

    def doType(self, frt, pag, r, c, p, i, w):
        self.weekly = w
        if self.weekly == "N":
            return "sk2"

    def doValue(self, frt, pag, r, c, p, i, w):
        if p == 4:
            self.quant = w
        else:
            self.profit = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("st1_cono", "=", self.opts["conum"])]
        if self.grps:
            whr.append(("st1_group", "in", self.grps.split(",")))
        recs = self.sql.getRec("strmf1", cols=["st1_group", "st1_code",
            "st1_desc", "st1_uoi"], where=whr, order="st1_group, st1_code")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
            "No Records Selected")
        elif self.weekly == "N":
            self.printPeriod(recs)
        else:
            self.printWeekly(recs)
        if "args" in self.opts and "noprint" in self.opts["args"]:
            self.t_work = [self.df.t_work[0][0]]
        self.closeProcess()

    def printPeriod(self, recs):
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.fpdf = MyFpdf(name=self.__class__.__name__, head=self.head)
        self.stot = [0] * 3
        self.gtot = [0] * 3
        lstgrp = ""
        self.pglin = 999
        for num, rec in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            self.grp = CCD(rec[0], "UA", 3)
            code = CCD(rec[1], "NA", 20)
            desc = CCD(rec[2], "NA", 30)
            uoi = CCD(rec[3], "NA", 10)
            whr = [
                ("stt_cono", "=", self.opts["conum"]),
                ("stt_group", "=", self.grp.work),
                ("stt_code", "=", code.work),
                ("stt_curdt", "=", self.per),
                ("stt_type", "=", 7)]
            if self.loc:
                whr.append(("stt_loc", "=", self.loc))
            bals = self.sql.getRec("strtrn", cols=["sum(stt_qty)",
                "sum(stt_cost)", "sum(stt_sell)"], where=whr, limit=1)
            if not bals[0] and not bals[1] and not bals[2]:
                continue
            mq = CCD(float(ASD(0) - ASD(bals[0])), "SD", 13.2)
            mc = CCD(float(ASD(0) - ASD(bals[1])), "SD", 13.2)
            ms = CCD(float(ASD(0) - ASD(bals[2])), "SD", 13.2)
            mp = float(ASD(ms.work) - ASD(mc.work))
            mp = CCD(mp, "SD", 13.2)
            if ms.work == 0:
                mn = 0
            else:
                mn = round((mp.work * 100.0 / ms.work), 2)
            mn = CCD(mn, "SD", 7.2)
            if lstgrp and lstgrp != self.grp.work:
                self.groupTotal()
                self.pglin = 999
            if self.pglin > self.fpdf.lpp:
                self.pageHeading()
            self.fpdf.drawText("%s %s %s %s %s %s %s" % (code.disp,
                desc.disp, uoi.disp, mq.disp, ms.disp, mp.disp, mn.disp))
            self.stot[0] = float(ASD(self.stot[0]) + ASD(mq.work))
            self.stot[1] = float(ASD(self.stot[1]) + ASD(ms.work))
            self.stot[2] = float(ASD(self.stot[2]) + ASD(mp.work))
            self.gtot[0] = float(ASD(self.gtot[0]) + ASD(mq.work))
            self.gtot[1] = float(ASD(self.gtot[1]) + ASD(ms.work))
            self.gtot[2] = float(ASD(self.gtot[2]) + ASD(mp.work))
            self.pglin += 1
            lstgrp = self.grp.work
        p.closeProgress()
        if self.fpdf.page and not p.quit:
            self.groupTotal()
            self.grandTotal()
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.opts["conum"], ext="pdf")
                if self.fpdf.saveFile(pdfnam, self.opts["mf"].window):
                    doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                        pdfnam=pdfnam, header=self.tit, repprt=self.df.repprt,
                        fromad=self.fromad, repeml=self.df.repeml)

    def pageHeading(self):
        self.fpdf.add_page()
        self.fpdf.setFont(style="B")
        self.fpdf.drawText(self.head)
        self.fpdf.drawText()
        self.fpdf.drawText("Period Sales By Product for %s" % self.perd)
        self.fpdf.drawText()
        acc = self.getGroup(self.grp.work)
        if acc:
            grpd = acc[0]
        else:
            grpd = "Missing Group Record"
        self.fpdf.drawText("%s %s %s    %s %s" % \
            ("Group:", self.grp.disp, grpd, "Location:", self.locd))
        self.fpdf.drawText()
        self.fpdf.drawText("%-20s %-30s %-10s %13s %13s %13s %7s" % \
            ("Product-Code", "Description", "U.O.I",
            "Quantity ", "Value ", "Profit ", "Prft-% "))
        self.fpdf.underLine(txt=self.head)
        self.fpdf.setFont()
        self.pglin = 8

    def getGroup(self, grp):
        acc = self.sql.getRec("strgrp", cols=["gpm_desc"],
            where=[("gpm_cono", "=", self.opts["conum"]), ("gpm_group", "=",
            grp)], limit=1)
        return acc

    def groupTotal(self):
        self.fpdf.drawText()
        mq = CCD(self.stot[0], "SD", 13.2)
        ms = CCD(self.stot[1], "SD", 13.2)
        mp = CCD(self.stot[2], "SD", 13.2)
        if ms.work == 0:
            mn = 0
        else:
            mn = round((mp.work * 100.0 / ms.work), 2)
        mn = CCD(mn, "SD", 7.2)
        self.fpdf.drawText("%-20s %-41s %s %s %s %s" % \
            ("", "Group Totals", mq.disp, ms.disp, mp.disp, mn.disp))
        self.stot = [0] * 3

    def grandTotal(self):
        self.fpdf.drawText()
        mq = CCD(self.gtot[0], "SD", 13.2)
        ms = CCD(self.gtot[1], "SD", 13.2)
        mp = CCD(self.gtot[2], "SD", 13.2)
        if ms.work == 0:
            mn = 0
        else:
            mn = round((mp.work * 100.0 / ms.work), 2)
        mn = CCD(mn, "SD", 7.2)
        self.fpdf.drawText("%-20s %-41s %s %s %s %s" % \
            ("", "Grand Totals", mq.disp, ms.disp, mp.disp, mn.disp))

    def printWeekly(self, recs):
        y = int(self.per / 100)
        m = int(self.per % 100)
        start = datetime.date(y, m, 1)
        end = mthendDate(int(start.strftime("%Y%m%d")) )
        end = datetime.date((end // 10000), (end // 100 % 100), end % 100)
        days = start.weekday()
        if days < 5:
            start += datetime.timedelta(days=0-days)
        else:
            start += datetime.timedelta(days=7-days)
        days = end.weekday()
        end += datetime.timedelta(days=6-days)
        weeks = []
        while start < end:
            new = start
            new += datetime.timedelta(days=6)
            weeks.append([int(start.strftime("%Y%m%d")),
                int(new.strftime("%Y%m%d")), start])
            new += datetime.timedelta(days=1)
            start = new
        sql = Sql(self.opts["mf"].dbm, ["strmf1", "strtrn"])
        whr = [("st1_cono", "=", 1)]
        if self.grps:
            whr.append(("st1_group", "in", self.grps.split(",")))
        st1 = sql.getRec("strmf1", cols=["st1_group", "st1_code", "st1_desc"],
            where=whr, order="st1_group, st1_code")
        grp = None
        data = []
        tq = ts = tp = None
        pb = ProgressBar(self.opts["mf"].body, mxs=len(st1), esc=True)
        for seq, rec in enumerate(st1):
            pb.displayProgress(seq)
            if pb.quit:
                break
            val = [[0, 0, 0]] * len(weeks)
            if grp is None or rec[0] != grp:
                tq = ts = tp = [0] * len(weeks)
                grp = rec[0]
            for num, week in enumerate(weeks):
                whr = [
                    ("stt_group", "=", rec[0]),
                    ("stt_code", "=", rec[1]),
                    ("stt_trdt", "between", week[0], week[1]),
                    ("stt_type", "=", 7)]
                if self.loc:
                    whr.append(("stt_loc", "=", self.loc))
                sls = sql.getRec("strtrn", cols=["sum(stt_qty)",
                    "sum(stt_cost)", "sum(stt_sell)"], where=whr, limit=1)
                if sls[0]:
                    qty = CCD(float(ASD(0) - ASD(sls[0])), "SD", 13.2)
                else:
                    qty = CCD(0, "SD", 13.2)
                if sls[1]:
                    cst = CCD(float(ASD(0) - ASD(sls[1])), "SD", 13.2)
                else:
                    cst = CCD(0, "SD", 13.2)
                if sls[2]:
                    sel = CCD(float(ASD(0) - ASD(sls[2])), "SD", 13.2)
                else:
                    sel = CCD(0, "SD", 13.2)
                pft = CCD(float(ASD(sel.work) - ASD(cst.work)), "SD", 13.2)
                val[num] = [qty.work, sel.work, pft.work]
                tq[num] = float(ASD(tq[num]) + ASD(qty.work))
                ts[num] = float(ASD(ts[num]) + ASD(sel.work))
                tp[num] = float(ASD(tp[num]) + ASD(pft.work))
            ign = True
            for v in val:
                if v != [0.0, 0.0, 0.0]:
                    ign = False
                    break
            if not ign:
                dat = [rec[0], rec[1], rec[2]]
                for v in val:
                    if self.quant == "Y":
                        dat.append(v[0])
                    dat.append(v[1])
                    if self.profit == "Y":
                        dat.append(v[2])
                data.append(dat)
        pb.closeProgress()
        if data and not pb.quit:
            txt = "%3s %20s %30s" % ("", "", "")
            for week in weeks:
                if self.quant == "Y" or self.profit == "Y":
                    wk1 = CCD(week[0], "D1", 10).disp
                    wk2 = CCD(week[1], "D1", 10).disp
                    wks = "    %s - %s" % (wk1, wk2)
                    if self.quant == "Y" and self.profit == "Y":
                        txt += '{:^42}'.format(wks)
                    else:
                        txt += '{:^28}'.format(wks)
                else:
                    wn = week[2].strftime("%V")
                    txt += '{:>14}'.format("Week %s " % wn)
            heds = [self.head, "Weekly Sales By Product for "\
                    "Location: %s Period: %s" % (self.locd, self.perd), txt]
            cols = [
                ["a", "NA",  3, "Grp",         "y"],
                ["b", "NA", 20, "Cod-Num",     "y"],
                ["c", "NA", 30, "Description", "y"]]
            gtots = []
            for no in range(len(weeks)):
                if self.quant == "Y":
                    cols.append(["d%s" % no, "SD", 13.2, "    Quantity", "y"])
                    gtots.append("d%s" % no)
                cols.append(["e%s" % no, "SD", 13.2, "   Sales-Val", "y"])
                gtots.append("e%s" % no)
                if self.profit == "Y":
                    cols.append(["f%s" % no, "SD", 13.2, "      Profit", "y"])
                    gtots.append("f%s" % no)
            if "args" not in self.opts or "noprint" not in self.opts["args"]:
                sveprt = True
            else:
                sveprt = False
            RepPrt(self.opts["mf"], name=self.__class__.__name__,
                tables=data, ttype="D", heads=heds, cols=cols,
                stots=[["a", "Group Total", "Y"]], gtots=gtots,
                repprt=self.df.repprt, repeml=self.df.repeml,
                sveprt=sveprt)
        self.opts["mf"].closeLoop()

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
