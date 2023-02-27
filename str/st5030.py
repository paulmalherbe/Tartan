"""
SYNOPSIS
    Stores Stock Take Variance Report.

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

import time
from TartanClasses import ASD, Balances, CCD, GetCtl, ProgressBar, RepPrt, Sql
from TartanClasses import TartanDialog
from tartanFunctions import showError

class st5030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["strloc", "strmf1", "strtrn",
            "strvar"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.fromad = strctl["cts_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
                "Stock Take Variance Report (%s)" % self.__class__.__name__)
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])]}
        self.dte = {
            "stype": "R",
            "tables": ("strvar",),
            "cols": (
                ("stv_mrgdt", "", 0, "Mrg-Date"),),
            "where": [("stv_cono", "=", self.opts["conum"])],
            "group": "stv_mrgdt",
            "order": "stv_mrgdt"}
        r1s = (("Yes",  "Y"), ("No", "N"))
        fld = [
            [("T",0,0,0),("IRB",r1s),0,"Reprint Report","",
                "N","Y",self.doReprint,None,None,None],
            [("T",0,1,0),"ID1",10,"Enter Date","",
                0,"N",self.doDate,self.dte,None,("efld",)],
            [("T",0,2,0),"IUA",1,"Location","",
                "","Y",self.doLoc,loc,None,("efld",)]]
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doReprint(self, frt, pag, r, c, p, i, w):
        self.reprt = w
        if self.reprt == "N":
            self.df.topf[0][1][4] = "Reporting Date"
            self.dte["where"].append(("stv_mrgdt", "=", 0))
            self.df.loadEntry(frt, pag, p+1, data=self.sysdtw)
        else:
            self.df.topf[0][1][4] = "Merged Date"
            if ("stv_mrgdt", "=", 0) in self.dte["where"]:
                self.dte["where"].remove(("stv_mrgdt", "=", 0))

    def doDate(self, frt, pag, r, c, p, i, w):
        if self.reprt == "N" and (w < self.opts["period"][1][0] or \
                w > self.opts["period"][2][0]):
            return "Invalid Date, Not in Financial Period"
        self.date = w
        self.dated = self.df.t_disp[pag][0][p]
        if self.reprt == "N":
            self.curdt = int(self.date / 100)

    def doLoc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]),
            ("srl_loc", "=", w)], limit=1)
        if not acc:
            return "Invalid Location Code"
        self.loc = w
        self.locd = acc[0]

    def doEnd(self):
        self.df.closeProcess()
        whr = [
            ("stv_cono", "=", self.opts["conum"]),
            ("stv_loc", "=", self.loc)]
        if self.reprt == "N":
            whr.append(("stv_mrgdt", "=", 0))
        else:
            whr.append(("stv_mrgdt", "=", self.date))
        recs = self.sql.getRec("strvar", where=whr,
            order="stv_group, stv_code, stv_seq")
        if not recs:
            showError(self.opts["mf"].body, "Processing Error",
                "No Records Selected")
        else:
            self.printReport(recs)
        self.opts["mf"].closeLoop()

    def printReport(self, recs):
        data = []
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), esc=True)
        self.head = "%03u %-135s" % (self.opts["conum"], self.opts["conam"])
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            grp = dat[self.sql.strvar_col.index("stv_group")]
            code = dat[self.sql.strvar_col.index("stv_code")]
            vbin = dat[self.sql.strvar_col.index("stv_bin")]
            vqty = dat[self.sql.strvar_col.index("stv_qty")]
            vprc = dat[self.sql.strvar_col.index("stv_ucost")]
            if self.reprt == "N":
                bals = Balances(self.opts["mf"], "STR", self.opts["conum"],
                    self.curdt, keys=(grp, code, self.loc,
                    ("P", self.opts["period"][0])))
                mob, mmv, mcb, yob, ymv, ycb, ac, lc, ls = bals.doStrBals()
                fqty, fval = ycb
                if fval and fqty:
                    fprc = round((fval / fqty), 2)
                else:
                    fprc = 0
                if fprc != vprc and vprc:
                    prc = vprc
                else:
                    prc = fprc
                vval = round((prc * vqty),2)
                qdif = float(ASD(vqty) - ASD(fqty))
                vdif = float(ASD(vval) - ASD(fval))
            else:
                qdif = dat[self.sql.strvar_col.index("stv_qdif")]
                vdif = dat[self.sql.strvar_col.index("stv_vdif")]
                fqty = float(ASD(vqty) - ASD(qdif))
                prc = float(ASD(round(vqty * vprc, 2)) - ASD(vdif))
                if fqty:
                    prc = round(prc / fqty, 2)
            if not qdif and not vdif:
                continue
            rslt = self.sql.getRec("strmf1", cols=["st1_desc", "st1_uoi"],
                where=[("st1_cono", "=", self.opts["conum"]),
                ("st1_group", "=", grp), ("st1_code", "=", code)],
                limit=1)
            desc = rslt[0]
            uoi = rslt[1]
            data.append([grp,code,desc,uoi,vbin,prc,prc,fqty,vqty,qdif,vdif])
        p.closeProgress()
        if not p.quit:
            name = self.__class__.__name__
            head = ["Stock Take Variance Report as at %s" % self.dated,
                "Location %s  %s" % (self.loc, self.locd)]
            cols = [
                ["a", "NA",  3,   "Grp",          "y"],
                ["b", "NA", 20,   "Product-Code", "y"],
                ["c", "NA", 30,   "Description",  "y"],
                ["d", "NA", 10,   "U.O.I",        "y"],
                ["e", "NA",  8,   "Bin-Loc",      "y"],
                ["f", "SD", 12.2, "File-Cost",    "y"],
                ["g", "SD", 12.2, "Stkt-Cost",    "y"],
                ["h", "SD", 12.2, "File-Qty",     "y"],
                ["i", "SD", 12.2, "Stkt-Qty",     "y"],
                ["j", "SD", 12.2, "Qty-Diff",     "y"],
                ["k", "SD", 12.2, "Val-Diff",     "y"]]
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=name, tables=data,
                heads=head, cols=cols, ttype="D", gtots=["j", "k"],
                repprt=self.df.repprt, repeml=self.df.repeml,
                fromad=self.fromad)

    def extractBals(self, grp, code, loc):
        qbal = 0
        vbal = 0
        rslt = self.sql.getRec("strtrn", cols=["stt_qty", "stt_cost"],
            where=[("stt_cono", "=", self.opts["conum"]), ("stt_group", "=",
            grp), ("stt_code", "=", code), ("stt_loc", "=", loc), ("stt_trdt",
            "<=", self.date)])
        if rslt:
            for dat in rslt:
                qty = CCD(dat[1], "SD", 12.2)
                cst = CCD(dat[2], "SD", 12.2)
                qbal = float(ASD(qbal) + ASD(qty))
                vbal = float(ASD(vbal) + ASD(cst))
        if vbal and qbal:
            fprc = round((vbal / qbal), 2)
        else:
            fprc = 0
        return qbal, vbal, fprc

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
