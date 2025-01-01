"""
SYNOPSIS
    Bowls Control File Maintenance.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2025 Paul Malherbe.

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
from TartanClasses import ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule

class bcc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["memctl", "memctc", "memmst",
            "memadd", "memkon", "bwlctl", "bwltab", "chglog", "tplmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            if self.sql.error == ["memctl"]:
                self.memctl = False
                self.chgint = False
                self.mlint = None
                self.same = "N"
            else:
                return
        else:
            self.memctl = True
        self.acc = self.sql.getRec("bwlctl", where=[("ctb_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.acc:
            self.new = True
            self.acc = [self.opts["conum"], "N", "N", 0, 0, 0, 0, "C",
                "A", "N", 4, "Y", 4, 0, 0, "A", "B", "comp_cards", "", ""]
        else:
            self.new = False
            self.oldm = self.acc[self.sql.bwlctl_col.index("ctb_mstart")]
            self.oldf = self.acc[self.sql.bwlctl_col.index("ctb_fstart")]
            self.oldn = self.acc[self.sql.bwlctl_col.index("ctb_nstart")]
        if self.memctl:
            self.mlint = self.sql.getRec("memctl", where=[("mcm_cono",
                "=", self.opts["conum"])], limit=1)
        return True

    def drawDialog(self):
        cat = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Code"),
                ("mcc_desc", "", 0, "Description")),
            "where": (
                ("mcc_cono", "=", self.opts["conum"]),
                ("mcc_type", "=", "C"))}
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "where": [
                ("tpm_type", "=", "C"),
                ("tpm_system", "=", "BWL")],
            "order": "tpm_tname"}
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("Position","P"),("Rating","R"),("Combined","C"))
        r3s = (("Ascending","A"),("Descending","D"))
        r4s = (("S32L-L23S","B"),("S32L-S32L","A"))
        if self.memctl:
            self.fld = [
                (("T",0,0,0),["IRB",r1s],0,"M/L Integration","",
                    self.acc[1],"N",self.doMlint,None,None,None,None,
                    "Select whether to Integrate this system with the "\
                    "Members Ledger System."),
                (("T",0,1,0),("IRB",r1s),0,"Same Numbers","",
                    self.acc[2],"N",self.doSame,None,None,None,None,
                    "If the Members Ledger is Integrated select "\
                    "whether the Tab numbers and Members Ledger numbers "\
                    "are the Same."),
                (("T",0,2,0),"IUI",2,"Category Code","",
                    self.acc[3],"N",self.doCat,cat,None,None,None,
                    "If the Members Ledger is Integrated enter which "\
                    "Members Ledger Sports category is for Bowls.")]
            seq = 3
        else:
            self.fld = []
            seq = 0
        self.fld.extend([
            (("T",0,seq,0),"IUI",6,"Male Start Seq","",
                self.acc[4],"N",self.doMStart,None,None,("notzero",),None,
                "The Starting Tab number for Males."),
            (("T",0,seq + 1,0),"IUI",6,"Female Start Seq","",
                self.acc[5],"N",self.doFStart,None,None,("notzero",),None,
                "The Starting Tab number for Females."),
            (("T",0,seq + 2,0),"IUI",6,"Non-Member Start Seq","",
                self.acc[6],"N",self.doNStart,None,None,("notzero",),None,
                "The Starting Tab number for Visitors."),
            (("T",0,seq + 3,0),("IRB",r2s),0,"Draw Base","",
                self.acc[7],"N",self.doBase,None,None,None,None,
                "The Default method of doing Draws."),
            (("T",0,seq + 4,0),("IRB",r3s),0,"Rating Order","",
                self.acc[8],"N",None,None,None,None,None,
                "With Ratings select whether Ratings are Ascending "\
                "or Descending in strength. Ascending means the Higher the "\
                "Rating the Better the player. Descending is like Golf "\
                "Handicaps i.e. the Best players have the Lowest ratings."),
            (("T",0,seq + 5,0),("IRB",r1s),0,"Mixed Ratings","",
                self.acc[9],"N",None,None,None,None,None,
                "Select if Different Ladies Ratings are Used for Mixed "\
                "Gender Draws."),
            (("T",0,seq + 6,0),"IUI",1,"Default Team Size","",
                self.acc[10],"N",None,None,None,None,None,
                "When the Draw is Done, Default to this Size."),
            (("T",0,seq + 7,0),("IRB",r1s),0,"Replace Fours","",
                self.acc[11],"N",None,None,None,None,None,
                "When the Draw is Trips Use Pairs Instead of Fours "\
                "when Applicable."),
            (("T",0,seq + 8,0),"IUI",2,"Weeks Between Draws","",
                self.acc[12],"N",None,None,None,("between", 0, 9),None,
                "Minimum number of Weeks that Players Should Not be "\
                "Drawn in the Same Team."),
            (("T",0,seq + 9,0),"IUD",5.2,"Rate - Member","",
                self.acc[13],"N",None,None,None,("efld",),None,
                "Member's Tabs-Inn Fee."),
            (("T",0,seq + 10,0),"IUD",5.2,"Rate - Visitor","",
                self.acc[14],"N",None,None,None,("efld",),None,
                "Visitor's Tabs-Inn Fee."),
            (("T",0,seq + 11,0),"IUA",6,"Greens","",
                self.acc[15],"N",self.doGreens,None,None,("notblank",)),
            (("T",0,seq + 12,0),("IRB",r4s),0,"Draw Format","",
                self.acc[16],"N",None,None,None,None),
            (("T",0,seq + 13,0),"INA",20,"Cards Template","",
                self.acc[17],"N",self.doTplNam,tpm,None,("efld",)),
            (("T",0,seq + 14,0),"ITX",50,"Email Address","",
                self.acc[18],"N",None,None,None,("email",))])
        but = (
            ("Accept",None,self.doAccept,0,("T",0,1),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)
        if not self.new:
            if self.memctl:
                seq = 1
                self.oldint = self.acc[0]
            else:
                seq = 4
            for n, f in enumerate(self.acc[seq:-1]):
                self.df.loadEntry("T", 0, n, data=f)
        if not self.memctl:
            self.chgint = False
            self.same = "N"
        self.df.focusField("T", 0, 1, clr=False)

    def doMlint(self, frt, pag, r, c, p, i, w):
        if w == "Y" and not self.mlint:
            return "Invalid Selection, Member's System Not Set Up"
        if not self.new and w != self.oldint:
            self.chgint = True
        else:
            self.chgint = False
        if w == "N":
            self.same = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.same)
            self.mcat = 0
            self.df.loadEntry(frt, pag, p+2, data=self.mcat)
            return "sk2"

    def doSame(self, frt, pag, r, c, p, i, w):
        self.same = w

    def doCat(self, frt, pag, r, c, p, i, w):
        chk = self.sql.getRec("memctc", where=[("mcc_cono",
            "=", self.opts["conum"]), ("mcc_type", "=", "C"),
            ("mcc_code", "=", w)], limit=1)
        if not chk:
            return "Invalid Code"
        self.mcat = w

    def doMStart(self, frt, pag, r, c, p, i, w):
        self.mstart = w

    def doFStart(self, frt, pag, r, c, p, i, w):
        if w == self.mstart and self.same == "N":
            return "Invalid Number, Same as Male"
        if w != self.mstart:
            if w < self.mstart:
                r = self.mstart - w
                g = "Female"
            else:
                r = w - self.mstart
                g = "Male"
            if r < 200:
                return "ff5|Invalid Numbers, Too Few %s Tabs. (Minimum 200)" % g
        self.fstart = w

    def doNStart(self, frt, pag, r, c, p, i, w):
        if w < self.mstart or w < self.fstart or w > 890000:
            return "Invalid Number, Less than Male or Female or > 890000"
        if self.mstart == self.fstart:
            t = "Members"
            r = w - self.mstart
            m = 400
        elif self.fstart < self.mstart:
            t = "Male"
            r = w - self.mstart
            m = 200
        else:
            t = "Female"
            r = w - self.fstart
            m = 200
        if r < m:
            return "Invalid Number, Too Few %s Tabs. (Minimum %s)" % (t, m)
        self.nstart = w

    def doBase(self, frt, pag, r, c, p, i, w):
        if w == "P":
            self.df.loadEntry(frt, pag, p+1, data="A")
            return "sk1"
        if not self.acc[7]:
            self.df.t_work[0][0][p+1] = "A"

    def doGreens(self, frt, pag, r, c, p, i, w):
        w = w.strip().replace(" ", "")
        self.df.loadEntry(frt, pag, p, data=w)

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "C"), ("tpm_system", "=", "BWL")], limit=1)
        if not acc:
            return "Invalid Template Name"

    def doEnd(self):
        err = None
        if self.same == "Y":
            if self.mstart + 400 > self.nstart:
                err = "Invalid Range, Too Few Members Allowed For"
        elif self.mstart == self.fstart and self.same == "N":
            err = "Same Male and Female Starting Numbers"
        elif self.mstart < self.fstart:
            if self.fstart - self.mstart < 200:
                err = "Invalid Range, Too Few Male Numbers"
            elif self.nstart < self.fstart + 200:
                err = "Invalid Range, Too Few Female Numbers"
        elif self.mstart - self.fstart < 200:
            err = "Invalid Range, Too Few Female Numbers"
        elif self.nstart < self.mstart + 200:
            err = "Invalid Range, Too Few Male Numbers"
        if err:
            self.df.focusField("T", 0, 3, err=err)
        else:
            data = [self.opts["conum"]]
            if not self.memctl:
                data.extend(["N", "N"])
            for x in range(0, len(self.df.t_work[0][0])):
                data.append(self.df.t_work[0][0][x])
            if self.new:
                self.sql.insRec("bwlctl", data=data)
            elif data != self.acc[:len(data)]:
                col = self.sql.bwlctl_col
                data.append(self.acc[col.index("ctb_xflag")])
                self.sql.updRec("bwlctl", data=data, where=[("ctb_cono", "=",
                    self.opts["conum"])])
                dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
                for num, dat in enumerate(self.acc):
                    if dat != data[num]:
                        self.sql.insRec("chglog", data=["bwlctl", "U",
                            "%03i" % self.opts["conum"], col[num], dte,
                            self.opts["capnm"], str(dat), str(data[num]),
                            "", 0])
            if self.chgint and self.oldint == "Y":
                recs = self.sql.getRec("bwltab", cols=["btb_memno"],
                    where=[("btb_cono", "=", self.opts["conum"])])
                for rec in recs:
                    data = self.doLoadMember(rec[0])
                    if data == [0, "", "", "", "", "", "", "", ""]:
                        continue
                    self.sql.updRec("bwltab", cols=["btb_memno", "btb_add1",
                        "btb_add2", "btb_add3", "btb_pcod", "btb_home",
                        "btb_work", "btb_cell", "btb_mail"], data=data,
                        where=[("btb_cono", "=", self.opts["conum"]),
                        ("btb_memno", "=", rec[0])])
            if not self.new and (self.mstart != self.oldm or \
                    self.fstart != self.oldf or self.nstart != self.oldn):
                # Tab ranges changed
                ok = askQuestion(self.opts["mf"].body, "Ranges", "Tab Ranges "\
                    "Have Changed, Do You Want to Change the Tabs to the "\
                    "New Ranges?", default="no")
                if ok == "yes":
                    mdif = self.mstart - self.oldm
                    fdif = self.fstart - self.oldf
                    ndif = self.nstart - self.oldn
                    recs = []
                    if ndif > 0:
                        recs.extend(self.getNon())
                    if self.oldm > self.oldf:
                        recs.extend(self.getWom())
                        recs.extend(self.getMen())
                    else:
                        recs.extend(self.getMen())
                        recs.extend(self.getWom())
                    if ndif < 0:
                        recs.extend(self.getNon())
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    pb = ProgressBar(self.opts["mf"].body,
                        typ="Changing Tabs", mxs=len(recs))
                    for num, rec in enumerate(recs):
                        pb.displayProgress(num)
                        tab = rec[self.sql.bwltab_col.index("btb_tab")]
                        gdr = rec[self.sql.bwltab_col.index("btb_gender")]
                        if tab < self.oldn:
                            if gdr == "M":
                                new = tab + mdif
                            else:
                                new = tab + fdif
                        else:
                            new = tab + ndif
                        callModule(self.opts["mf"], None, "bc6010",
                            coy=[self.opts["conum"], self.opts["conam"]],
                            args=[tab, new])
                    pb.closeProgress()
                    self.df.setWidget(self.df.mstFrame, state="show")
            self.opts["mf"].dbm.commitDbase()
            self.doExit()

    def getMen(self):
        recs = self.sql.getRec("bwltab", where=[("btb_cono",
            "=", self.opts["conum"]), ("btb_tab", "<", self.oldn),
            ("btb_gender", "=", "M")], order="btb_tab")
        return recs

    def getWom(self):
        recs = self.sql.getRec("bwltab", where=[("btb_cono",
            "=", self.opts["conum"]), ("btb_tab", "<", self.oldn),
            ("btb_gender", "=", "F")], order="btb_tab")
        return recs

    def getNon(self):
        end = self.oldm
        if self.oldf > end:
            end = self.oldf
        recs = self.sql.getRec("bwltab", where=[("btb_cono",
            "=", self.opts["conum"]), ("btb_tab", ">=", self.oldn)],
            order="btb_tab")
        return recs

    def doLoadMember(self, memno):
        acc = self.sql.getRec("memmst", cols=["mlm_surname",
            "mlm_names", "mlm_gender"], where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", memno)], limit=1)
        if not acc:
            return [0, "", "", "", "", "", "", "", ""]
        self.df.loadEntry("T", 0, 1, data=memno)
        self.df.loadEntry("T", 0, 2, data=acc[0])
        self.df.loadEntry("T", 0, 3, data=acc[1])
        self.gender = acc[2]
        self.df.loadEntry("T", 0, 4, data=self.gender)
        for typ in ("A", "P"):
            data = self.sql.getRec("memadd", cols=["mla_add1",
                "mla_add2", "mla_add3", "mla_code"], where=[("mla_cono", "=",
                self.opts["conum"]), ("mla_memno", "=", memno), ("mla_type",
                "=", typ)], limit=1)
            if data:
                break
        if data:
            data.insert(0, 0)
        else:
            data = ["", "", "", "", ""]
        for num, cod in enumerate((1, 2, 3, 5)):
            kk = self.sql.getRec("memkon", cols=["mlk_detail"],
                where=[("mlk_cono", "=", self.opts["conum"]),
                ("mlk_memno", "=", memno), ("mlk_code", "=", cod)], limit=1)
            if kk:
                data.append(kk[0])
            else:
                data.append("")
        return data

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.same = self.df.t_work[0][0][1]
            self.mcat = self.df.t_work[0][0][2]
            self.mstart = self.df.t_work[0][0][3]
            self.fstart = self.df.t_work[0][0][4]
            self.nstart = self.df.t_work[0][0][5]
            self.df.doEndFrame("T", 0, cnf="N")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
