"""
SYNOPSIS
    Report Stream Utility.

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

import os, shutil, time
from TartanClasses import GetCtl, SelectChoice, SplashScreen, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, doPrinter, sendMail
from tartanFunctions import showError, getPrinters, showWarning
from tartanWork import allsys, tarmen

class rp1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        # Get System Details
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        self.smtp = []
        for fld in ("msvr", "mprt", "msec", "maut", "mnam", "mpwd"):
            self.smtp.append(ctlsys["sys_%s" % fld])
        if not self.smtp[0]:
            showWarning(self.opts["mf"].body, "SMTP Error",
                """There is No SMTP Server Configured,

Therefore No Emailing will be Possible.""")
            self.smtp = None
        # Get Company Details
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.fadd = ctlmst["ctm_email"]
        if self.smtp and not self.fadd:
            showError(self.opts["mf"].body, "From Error",
                "There is NO Email Address on the Company Record!")
            return
        # Modules
        mods = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mods.append(ctlmst["ctm_modules"][x:x+2])
        self.sql = Sql(self.opts["mf"].dbm, tables=["rptstm", "rptstr",
            "genstr", "emllog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        amod = {
            "GL": ["GEN", {
                "gl3020": [
                    ["F", "", "", "", "", "", "", "Y"], []],
                "gl3030": [
                    ["S", "", 0, "", "", "N"], []],
                "gl3040": [
                    ["N", "Y", "", "", "Y"], []],
                "gl3050": [
                    ["",0,"S","N","N",1,"N","V","","","B","Y","Y","Y"], []]}],
            "CR": ["CRS", {
                "cr3020": [
                    ["F", "", "", "", "", "", "", "Y"], []],
                "cr3030": [
                    ["M", "N", "", 0], []],
                "cr3040": [
                    ["Y", "N"], []],
                "cr3050": [
                    ["A", "", "N", "", "", 0, "Y", "Y"], []]}],
            "DR": ["DRS", {
                "dr3020": [
                    ["F", "", "", "", "", "", "", "Y"], []],
                "dr3030": [
                    [], []],
                "dr3040": [
                    ["", "N"], []],
                "dr3050": [
                    ["A", "", "N", "", "", 0, "Y", "Y"], []]}],
            "ST": ["STR", {
                "st3020": [
                    ["F", "", "", "", "", "", "", "Y"], []],
                "st3080": [
                    ["", "", "", "Y", "Y"], []],
                "st3090": [
                    ["", "", "", "", "N", "N"], []]}],
            "SI": ["INV", {
                "si3020": [
                    ["", "", ""], []],
                "si3030": [
                    ["", "", ""], []],
                "si3040": [
                    ["", "V", "", "", 0, "Y"], []],
                "si3050": [
                    ["", "", "", "", "", "", "Y"], []],
                "si3060": [
                    ["", "", ""], []],
                "si3070": [
                    ["", "", ""], []]}]}
        self.mods = []
        self.vars = {}
        for mod in mods:
            if mod not in amod:
                continue
            sss = allsys[amod[mod][0]][0]
            key = list(amod[mod][1].keys())
            key.sort()
            for rpt in key:
                for men in tarmen["%smod" % mod.lower()]:
                    if men[2] == rpt:
                        self.mods.append([rpt, sss, men[4], men[0]])
                        self.vars[rpt] = amod[mod][1][rpt]
        # Periods
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        # Variables
        self.strm = None
        self.tadd = ""
        return True

    def mainProcess(self):
        self.tit = "Stream Reports"
        prts = getPrinters(wrkdir=self.opts["mf"].rcdic["wrkdir"])
        grp = {
            "stype": "R",
            "tables": ("rptstm",),
            "cols": (
                ("rsm_rgrp", "", 0, "Report-Group"),
                ("rsm_emad", "", 0, "Email-Address")),
            "where": (
                ("rsm_cono", "=", self.opts["conum"]),),
            "order": "rsm_rgrp"}
        prt = {
            "stype": "C",
            "titl": "Available Printers",
            "head": ("Name", "Description"),
            "data": prts}
        r1s = (("E-Mail", "E"), ("Print", "P"))
        fld = [
            (("T",0,0,0),"INA",30,"Report Group", "",
                "","Y",self.doGrp,grp,None,("notblank",)),
            (("T",0,1,0),("IRB",r1s),0,"Output","",
                "E","N",self.doTyp,None,self.doDel,None),
            (("T",0,2,0),"INA",(30,50),"Printer Name","",
                "Default","N",self.doPrt,prt,None,("in", prts)),
            (("T",0,3,0),"ITX",50,"From Address","",
                self.fadd,"N",self.doFad,None,None,("email", False),None,
                "From E-Mail Address"),
            (("T",0,4,0),"ITX",50,"To   Address","",
                "","N",self.doTad,None,None,("email", False),None,
                "To E-Mail Address")]
        tnd = ((self.doEnd, "y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], tops=True, title=self.tit,
            eflds=fld, tend=tnd, txit=txt)

    def doGrp(self, frt, pag, r, c, p, i, w):
        self.rgrp = w
        rsm = self.sql.getRec("rptstm", where=[("rsm_cono", "=",
            self.opts["conum"]), ("rsm_rgrp", "=", w)], limit=1)
        if not rsm:
            ok = askQuestion(self.opts["mf"].body, "New Group",
                "In This a New Report Group?", default="no")
            if ok == "no":
                return "Invalid Group"
            self.new = True
        else:
            self.new = False
            self.tadd = rsm[2]
        rsr = self.sql.getRec("rptstr", where=[("rsr_cono", "=",
            self.opts["conum"]), ("rsr_rgrp", "=", w)])
        self.smod = {}
        for rep in rsr:
            self.smod[rep[2]] = rep[3:]
        if not self.smtp:
            self.styp = "P"
            self.df.loadEntry(frt, pag, p+1, data="P")
            return "sk1"

    def doDel(self):
        self.sql.delRec("rptstm", where=[("rsm_cono", "=",
            self.opts["conum"]), ("rsm_rgrp", "=", self.rgrp)])
        self.sql.delRec("rptstr", where=[("rsr_cono", "=",
            self.opts["conum"]), ("rsr_rgrp", "=", self.rgrp)])
        self.opts["mf"].dbm.commitDbase(ask=True, mess="Commit the Deletion?")
        self.df.focusField("T", 0, 1)

    def doTyp(self, frt, pag, r, c, p, i, w):
        self.styp = w
        if self.styp == "E":
            self.sprt = ""
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+3, data=self.tadd)
            return "sk1"

    def doPrt(self, frt, pag, r, c, p, i, w):
        self.sprt = w
        self.fadd = self.tadd = ""
        self.df.loadEntry(frt, pag, p+1, data="")
        self.df.loadEntry(frt, pag, p+2, data="")
        return "nd"

    def doFad(self, frt, pag, r, c, p, i, w):
        self.fadd = w

    def doTad(self, frt, pag, r, c, p, i, w):
        self.tadd = w

    def doEnd(self):
        self.df.closeProcess()
        if not self.new:
            self.sql.delRec("rptstm", where=[("rsm_cono", "=",
                self.opts["conum"]), ("rsm_rgrp", "=", self.rgrp)])
            self.sql.delRec("rptstr", where=[("rsr_cono", "=",
                self.opts["conum"]), ("rsr_rgrp", "=", self.rgrp)])
        self.sql.insRec("rptstm", data=[self.opts["conum"], self.rgrp,
            self.tadd])
        titl = "Report Stream"
        cols = (
            ("a", "", 0, "CB", "N"),
            ("b", "R-Code", 6, "NA", "N"),
            ("c", "System", 25, "NA", "N"),
            ("d", "Report", 30, "NA", "N"))
        data = []
        for mod in self.mods:
            if mod[0] in self.smod:
                data.append(["X", mod[0], mod[1], mod[2]])
            else:
                data.append(["", mod[0], mod[1], mod[2]])
        sc = SelectChoice(self.opts["mf"].body, titl, cols, data)
        if sc.selection:
            self.count = 1
            self.fles = []
            self.tmp = os.path.join(self.opts["mf"].rcdic["wrkdir"], "temp")
            if os.path.exists(self.tmp):
                shutil.rmtree(self.tmp)
            os.mkdir(self.tmp)
            if self.styp == "E":
                self.mess = "Attached please find the following reports:\n"
            else:
                self.mess = "Reports to Print:\n"
            for mod in sc.selection:
                if mod[1] == "gl3050":
                    self.doGetStream()
                if self.strm:
                    self.strm = None
                    continue
                self.opts["mf"].head.configure(text="")
                if mod[1] in self.smod:
                    work = eval(self.smod[mod[1]][-1])
                else:
                    work = self.vars[mod[1]]
                var = callModule(self.opts["mf"], None, mod[1],
                    coy=(self.opts["conum"], self.opts["conam"]),
                    period=self.opts["period"], user=self.opts["capnm"],
                    args={"noprint": True, "work": work}, ret=["fpdf",
                    "t_work"])
                if var:
                    nam = os.path.join(self.tmp, "report%s.pdf" % self.count)
                    self.fles.append(nam)
                    var["fpdf"].output(nam)
                    self.mess = "%s\n%2s) %s - %s" % (self.mess, self.count,
                        mod[2], mod[3])
                    self.sql.insRec("rptstr", data=[self.opts["conum"],
                        self.rgrp, mod[1], str(var["t_work"])])
                    self.count += 1
            if self.fles:
                if self.styp == "E":
                    self.mess = "%s\n\nRegards" % self.mess
                    ok = askQuestion(self.opts["mf"].body, "Mail Reports",
                        self.mess, default="yes")
                    if ok == "yes":
                        self.doEmailReps()
                else:
                    ok = askQuestion(self.opts["mf"].body, "Print Reports",
                        self.mess, default="yes")
                    if ok == "yes":
                        self.doPrintReps()
                for fle in self.fles:
                    os.remove(fle)
        self.opts["mf"].dbm.commitDbase(True)
        self.closeProcess()

    def doGetStream(self):
        chk = self.sql.getRec("genstr", where=[("gls_cono", "=",
            self.opts["conum"])], limit=1)
        if not chk:
            self.strm = None
            return
        if "gl3050" in self.smod:
            var = ["Y", eval(self.smod["gl3050"][0])[0][1]]
        else:
            var = ["N", 0]
        tit = "Financial Statements"
        self.opts["mf"].head.configure(text="%03i %s - %s (%s)" %
            (self.opts["conum"], self.opts["conam"], tit, "gl3050"))
        stm = {
            "stype": "R",
            "tables": ("genstr",),
            "cols": (
                ("gls_strm", "", 0, "Num"),
                ("gls_desc", "", 0, "Description", "Y"),
                ("count(*)", "UI", 3, "Qty")),
            "where": [("gls_cono", "=", self.opts["conum"])],
            "group": "gls_strm"}
        r1s = (("No", "N"), ("Yes", "Y"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Report Stream","",
                var[0],"Y",self.doRepStr,None,None,None),
            (("T",0,1,0),"IUI",3,"Stream Number","",
                var[1],"N",self.doStrNum,stm,None,None),
            (("T",0,2,0),"ID2",7,"Ending Period","",
                self.e_per,"N",self.doStrPer,None,None,None))
        self.rs = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.strEnd,"y"),), txit=(self.strExit,))
        self.rs.mstFrame.wait_window()

    def doRepStr(self, frt, pag, r, c, p, i, w):
        if w == "N":
            return "xt"

    def doStrNum(self, frt, pag, r, c, p, i, w):
        self.strm = self.sql.getRec("genstr", where=[("gls_cono", "=",
            self.opts["conum"]), ("gls_strm", "=", w)], order="gls_seq")
        if not self.strm:
            self.strm = None
            return "Invalid Stream Number"
        self.stno = w

    def doStrPer(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Period"
        self.end = w

    def strEnd(self):
        self.rs.closeProcess()
        col = self.sql.genstr_col
        for rep in self.strm:
            args = {"stream": True}
            args["end"] = self.end
            args["typ"] = rep[col.index("gls_typ")]
            args["cno"] = rep[col.index("gls_cno")]
            args["con"] = rep[col.index("gls_con")]
            args["dep"] = "N"
            args["dpl"] = [0]
            args["rep"] = rep[col.index("gls_rep")]
            args["gen"] = rep[col.index("gls_gen")]
            args["val"] = rep[col.index("gls_val")]
            args["det"] = rep[col.index("gls_det")]
            if args["typ"] == "M":
                args["var"] = "N"
            else:
                args["var"] = rep[col.index("gls_var")]
                if not args["var"]:
                    args["var"] = "B"
            args["zer"] = rep[col.index("gls_zer")]
            args["opt"] = rep[col.index("gls_opt")]
            if not args["opt"]:
                args["opt"] = "N"
            args["num"] = rep[col.index("gls_num")]
            if not args["num"]:
                args["num"] = "Y"
            var = callModule(self.opts["mf"], None, "gl3050",
                coy=(self.opts["conum"], self.opts["conam"]),
                period=self.opts["period"], args=args,
                ret=["fpdf", "emlhead"])
            if var:
                nam = os.path.join(self.tmp, "report%s.pdf" % self.count)
                self.fles.append(nam)
                var["fpdf"].output(nam)
                des = var["emlhead"].lower()
                des = " ".join(w.capitalize() for w in des.split())
                self.mess = "%s\n%2s) %s - %s" % (self.mess, self.count,
                    "General Ledger", des)
                self.count += 1
        if var:
            self.sql.insRec("rptstr", data=[self.opts["conum"],
                self.rgrp, "gl3050", str([[self.end, self.stno, "S", "N",
                "N", 1, "N", "V", "", "", "B", "Y", "Y", "Y"]])])

    def strExit(self):
        self.strm = None
        self.rs.closeProcess()

    def doEmailReps(self):
        subj = "Sundry Reports"
        ok = False
        while not ok:
            emls = self.tadd.split(",")
            for eml in emls:
                sp = SplashScreen(self.opts["mf"].body, "E-Mailing the "\
                    "Message to\n\n%s\n\nPlease Wait........" % eml)
                ok = sendMail(self.smtp, self.fadd, eml, subj, mess=self.mess,
                    attach=self.fles, wrkdir=self.opts["mf"].rcdic["wrkdir"])
                sp.closeSplash()
                if not ok:
                    if self.skip == "Y":
                        ok = "SKIPPED"
                    else:
                        ok = askQuestion(self.opts["mf"].body, "E-Mail Error",
                            "Problem Delivering This Message.\n\nTo: "\
                            "%s\nSubject: %s\n\nWould You Like to Retry?" \
                            % (eml, subj))
                    if ok == "yes":
                        ok = False
                    else:
                        ok = "FAILED"
                else:
                    ok = "OK"
                # Log the email attempt into table emllog.
                self.sql.insRec("emllog", data=[self.fadd, self.tadd, subj,
                    "%04i-%02i-%02i %02i:%02i" % time.localtime()[0:5], ok])

    def doPrintReps(self):
        repprt = ["Y", "P", self.sprt]
        for fle in self.fles:
            doPrinter(mf=self.opts["mf"], pdfnam=fle, repprt=repprt)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
