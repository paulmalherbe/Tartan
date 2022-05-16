"""
SYNOPSIS
    Members Ledger Master Report.

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
from TartanClasses import CCD, GetCtl, ProgressBar, RepPrt, Sql, TartanDialog
from tartanFunctions import dateDiff, doChkCatChg, getVatRate, copyList
from tartanFunctions import mthendDate, showError
from tartanWork import countries

class ml3070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlnot", "ctlvrf", "memctc",
            "memctk", "memcto", "memctp", "memmst", "memcat", "memadd",
            "memkon", "memtrn"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        self.ldays = memctl["mcm_ldays"]
        self.fromad = memctl["mcm_emadd"]
        t = time.localtime()
        self.sysdt = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.colsd = {
            0: ["Membership Number", "Y", ["Mem-No", "UI", 6]],
            1: ["Status", "N", ["Status", "NA", 10]],
            2: ["Status Date", "N", ["State-Date", "D1", 10]],
            3: ["Surname/Title/Initials", "Y", ["Name", "TX", 30]],
            4: ["Surname", "N", ["Surname", "TX", 30]],
            5: ["Title", "N", ["Title", "TX", 6]],
            6: ["First Names", "N", ["First-Names", "TX", 30]],
            7: ["Gender", "N", ["G", "UA", 1]],
            8: ["Date of Birth", "N", ["Birth-Date", "D1", 10]],
            9: ["Age", "N", ["Age", "UI", 3]],
            10: ["Identity Number", "N", ["ID-Number", "UI", 13]],
            11: ["Entry Date", "N", ["Entry-Date", "d1", 10]],
            12: ["Entry Years", "N", ["YR", "UI", 2]],
            13: ["Payment Plan", "N", ["P", "UA", 1]],
            14: ["Active Category", "N", ["Active-Category", "TX", 30]],
            15: ["Telephone - Home", "Y", ["Home-Telephone", "TX", 20]],
            16: ["Telephone - Work", "Y", ["Work-Telephone", "TX", 20]],
            17: ["Mobile Number", "Y", ["Mobile-Number", "TX", 20]],
            18: ["Email Address 1", "Y", ["Email-Address-1", "TX", 30]],
            19: ["Email Address 2", "N", ["Email-Address-2", "TX", 30]],
            20: ["Address - Postal", "N", ["Postal-Address", "TX", 120]],
            21: ["Address - Street", "N", ["Street-Address", "TX", 120]],
            22: ["Category Notes", "N", ["Category-Notes", "TX", 50]],
            23: ["Proposer", "N", ["Proposer", "TX", 20], ["YR", "UI", 2]],
            24: ["Seconder", "N", ["Seconder", "TX", 20], ["YR", "UI", 2]],
            25: ["Account Balance", "N", ["Balance", "SD", 13.2]],
            26: ["Sports Categories", "N"],
            27: ["Last Note", "N", ["Last-Text-Note", "TX", 30]],
            28: ["Nationality", "N", ["Nationality", "TX", 30]],
            29: ["Occupation", "N", ["Occupation", "TX", 30]]}
        rgp = self.sql.getRec("memctc", cols=["mcc_rgrp"],
            where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
            "C")], group="mcc_rgrp", order="mcc_rgrp")
        self.rgrps = []
        for g in rgp:
            self.rgrps.append(g[0])
            self.colsd[26].append([g[0], "UA", 2])
        self.padcol = [0, 0, 0, 0, 0, 0, 0]
        self.sadcol = [0, 0, 0, 0, 0, 0, 0]
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Members Ledger Master Listing (%s)" % self.__class__.__name__)
        rgp = {
            "stype": "C",
            "head": ("RG",),
            "data": self.rgrps,
            "retn": "D"}
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [("T", "mcc_type", 2, 0)],
            "order": "mcc_code",
            "size": (400, 600)}
        r1s = (
            ("All", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        r2s = (
            ("All", "Z"),
            ("Active", "A"),
            ("Deceased", "D"),
            ("Inactive", "I"),
            ("Resigned", "R"),
            ("Suspended", "S"),
            ("Defaulted", "X"))
        r3s = (
            ("All", "A"),
            ("Male", "M"),
            ("Female", "F"))
        r4s = (
            ("Number", "N"),
            ("Surname", "M"))
        fld = (
            (("T",0,0,0),"ID1",10,"Report Date","",
                self.sysdt,"Y",self.doDate,None,None,("efld",)),
            (("T",0,1,0),("IRB",r2s),0,"Status","",
                "A","Y",self.doStat,None,None,None),
            (("T",0,2,0),("IRB",r1s),0,"Category","",
                "A","Y",self.doCat,None,None,None),
            (("T",0,3,0),"IUA",2,"Report Group","",
                0,"Y",self.doRgrp,rgp,None,None),
            (("T",0,3,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None),
            (("T",0,3,0),"ONA",30,""),
            (("T",0,4,0),("IRB",r3s),0,"Gender","",
                "A","Y",self.doGender,None,None,None),
            (("T",0,5,0),("IRB",r4s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,6,0),"Id1",10,"From Entry","From Entry Date",
                0,"Y",self.doEFrom,None,None,("efld",)),
            (("T",0,7,0),"ID1",10,"To   Entry","To Entry Date",
                0,"Y",self.doETo,None,None,("efld",)),
            (("T",0,8,0),"Id1",10,"From Status","From Status Date",
                0,"Y",self.doSFrom,None,None,("efld",)),
            (("T",0,9,0),"ID1",10,"To   Status","To Status Date",
                0,"Y",self.doSTo,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doDate(self, frt, pag, r, c, p, i, w):
        self.repdt = w
        self.repdtd = self.df.t_disp[pag][r][i]
        self.df.topf[0][9][5] = self.repdt
        self.df.topf[0][11][5] = self.repdt

    def doStat(self, frt, pag, r, c, p, i, w):
        self.state = w

    def doCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.cat = ""
            self.rgp = ""
            self.cod = ""
            self.df.loadEntry(frt, pag, p+3,
                data="All Categories and Sections")
            return "sk2"
        self.cat = w
        if self.cat not in ("C", "D"):
            self.rgp = ""
            return "sk1"

    def doRgrp(self, frt, pag, r, c, p, i, w):
        if w and w not in self.rgrps:
            return "Invalid Report Group"
        self.rgp = w
        if self.rgp:
            self.cod = 0
            return "sk2"

    def doCod(self, frt, pag, r, c, p, i, w):
        self.codchk = self.sql.getRec("memctc", cols=["mcc_desc"],
            where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
            self.cat), ("mcc_code", "=", w)], limit=1)
        if not self.codchk:
            return "Invalid Category Code"
        self.cod = w
        self.df.loadEntry(frt, pag, p+1, data=self.codchk[0])

    def doGender(self, frt, pag, r, c, p, i, w):
        self.gender = w

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doEFrom(self, frt, pag, r, c, p, i, w):
        self.estart = w
        self.estartd = self.df.t_disp[pag][r][i]

    def doETo(self, frt, pag, r, c, p, i, w):
        self.eend = w
        self.eendd = self.df.t_disp[pag][r][i]
        if self.state == "A":
            self.sstart = 0
            self.send = 0
            return "sk2"

    def doSFrom(self, frt, pag, r, c, p, i, w):
        self.sstart = w
        self.sstartd = self.df.t_disp[pag][r][i]

    def doSTo(self, frt, pag, r, c, p, i, w):
        self.send = w
        self.sendd = self.df.t_disp[pag][r][i]

    def doEnd(self):
        self.df.closeProcess()
        self.doChooseFields()
        if self.cnums:
            # Member's masterfile
            tab = ["memmst"]
            col = self.sql.memmst_col
            whr = [("mlm_cono", "=", self.opts["conum"])]
            if self.gender != "A":
                whr.append(("mlm_gender", "=", self.gender))
            if self.state != "Z":
                whr.append(("mlm_state", "=", self.state))
            if self.estart:
                whr.append(("mlm_entry", ">=", self.estart))
            if self.eend:
                whr.append(("mlm_entry", "<=", self.eend))
            if self.sstart:
                if self.state == "R" and self.cat:
                    pass
                else:
                    whr.append(("mlm_sdate", ">=", self.sstart))
            if self.send:
                if self.state == "R" and self.cat:
                    pass
                else:
                    whr.append(("mlm_sdate", "<=", self.send))
            if self.cat:
                tab.append("memcat")
                whr.append(("mlc_cono=mlm_cono",))
                whr.append(("mlc_memno=mlm_memno",))
                whr.append(("mlc_type", "=", self.cat))
                if self.cod:
                    whr.append(("mlc_code", "=", self.cod))
                if self.rgp:
                    tab.append("memctc")
                    whr.append(("mcc_cono=mlc_cono",))
                    whr.append(("mcc_type=mlc_type",))
                    whr.append(("mcc_code=mlc_code",))
                    whr.append(("mcc_rgrp", "=", self.rgp))
                if self.state == "A":
                    whr.append(("mlc_end", "=", 0))
                elif self.state == "R":
                    whr.append(("(", "mlm_state", "=", "R", "and", "mlm_sdate",
                        "between", self.sstart, self.send, "or", "mlm_state",
                        "=", "A", "and", "mlc_end", "between", self.sstart,
                        self.send, ")"))
                grp = col[0]
                for c in col[1:]:
                    grp = "%s, %s" % (grp, c)
            else:
                grp = None
            if self.sort == "N":
                odr = "mlm_memno"
            else:
                odr = "mlm_surname"
            recs = self.sql.getRec(tables=tab, cols=col, where=whr, group=grp,
                order=odr)
            if not recs:
                showError(self.opts["mf"].body, "Selection Error",
                    "No Accounts Selected")
            else:
                self.printReport(recs)
        self.opts["mf"].closeLoop()

    def printReport(self, recs):
        data = []
        typ = "Generating the Report ... Please Wait"
        p = ProgressBar(self.opts["mf"].body, mxs=len(recs), typ=typ, esc=True)
        for num, dat in enumerate(recs):
            p.displayProgress(num)
            if p.quit:
                break
            data.append(self.getValues(dat))
        p.closeProgress()
        if not p.quit:
            head = ["Member's Master Report as at %s" % self.repdtd]
            colsh = []
            for n1 in self.cnums:
                for n2, d2 in enumerate(self.colsd[n1][2:]):
                    if n1 in (20, 21) and self.df.repprt[2] == "export":
                        if n1 == 20:
                            prefix = "P"
                            col = copyList(self.padcol)
                        else:
                            prefix = "S"
                            col = copyList(self.sadcol)
                        colsh.append(("name1%s_%s" % (n1, n2), "NA",
                            col[0], "%s-Address-Line-1" % prefix, "y"))
                        colsh.append(("name2%s_%s" % (n1, n2), "NA",
                            col[1], "%s-Address-Line-2" % prefix, "y"))
                        colsh.append(("name3%s_%s" % (n1, n2), "NA",
                            col[2], "%s-Address-Line-3" % prefix, "y"))
                        colsh.append(("name4%s_%s" % (n1, n2), "NA",
                            col[3], "%s-City" % prefix, "y"))
                        colsh.append(("name5%s_%s" % (n1, n2), "NA",
                            col[4], "%s-Code" % prefix, "y"))
                        colsh.append(("name6%s_%s" % (n1, n2), "NA",
                            col[5], "%s-Region" % prefix, "y"))
                        colsh.append(("name7%s_%s" % (n1, n2), "NA",
                            col[6], "%s-Country" % prefix, "y"))
                    else:
                        colsh.append(("name%s_%s" % (n1, n2), d2[1],
                            d2[2], d2[0], "y"))
            RepPrt(self.opts["mf"], name=self.__class__.__name__, heads=head,
                tables=data, cols=colsh, opts=self.getDes(), ttype="D",
                conum=self.opts["conum"], conam=self.opts["conam"],
                repprt=self.df.repprt, repeml=self.df.repeml,
                fromad=self.fromad, pbar="P")

    def doChooseFields(self):
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = []
        idx = 0
        for num in range(0, len(self.colsd), 2):
            des = self.colsd[num][0]
            dft = self.colsd[num][1]
            fld.append((("T",0,idx,0,27),("IRB",r1s),0,des,des,
                dft,"N",self.doCField,None,None,None))
            if (num+1) == len(self.colsd):
                continue
            des = "   %s" % self.colsd[num+1][0]
            dft = self.colsd[num+1][1]
            fld.append((("T",0,idx,40,67),("IRB",r1s),0,des,des,
                dft,"N",self.doCField,None,None,None))
            idx += 1
        tnd = ((self.doCEnd,"Y"), )
        txt = (self.doCExit, )
        self.cf = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt)
        self.cf.mstFrame.wait_window()

    def doCField(self, frt, pag, r, c, p, i, w):
        mxs = 0
        for n, x in enumerate(self.cf.t_work[pag][0]):
            if x == "Y":
                for y in self.colsd[n][2:]:
                    if mxs:
                        mxs += 1
                    mxs += y[2]
        if mxs > 210 and self.df.repprt[2] != "export":
            return "Maximum Print Width Exceeded"
        if p == 3 and w == "Y":
            self.cf.loadEntry(frt, pag, p+1, data="N")
            self.cf.loadEntry(frt, pag, p+2, data="N")
            self.cf.loadEntry(frt, pag, p+3, data="N")
            return "sk3"

    def doCEnd(self):
        self.cf.closeProcess()
        self.cnums = []
        for n1, d1 in enumerate(self.cf.t_work[0][0]):
            if d1 == "Y":
                self.cnums.append(n1)

    def doCExit(self):
        self.cnums = []
        self.cf.closeProcess()

    def getDes(self):
        if self.state == "Z":
            des = "All Statuses"
        elif self.state == "A":
            des = "Active Members"
        elif self.state == "D":
            des = "Deceased Members"
        elif self.state == "I":
            des = "Inactive Members"
        elif self.state == "R":
            des = "Resigned Members"
        elif self.state == "S":
            des = "Suspended Members"
        elif self.state == "X":
            des = "Defaulted Members"
        if self.gender == "M":
            des = "%s (Male)" % des
        elif self.gender == "F":
            des = "%s (Female)" % des
        if self.cat in ("", "A"):
            des = "%s for All Categories and Sections" % des
        elif self.cat == "B":
            des = "%s for Main Category" % des
        elif self.cat == "C":
            des = "%s for Sports Category" % des
        elif self.cat == "D":
            des = "%s for Debenture Category" % des
        if self.cat and self.rgp:
            des = "%s: Report Group %s" % (des, self.rgp)
            if self.cod:
                des = "%s: %s" % (des, self.codchk[0])
            else:
                des = "%s: All Sections" % des
        elif self.cat and self.cod:
            des = "%s: %s" % (des, self.codchk[0])
        elif self.cat:
            des = "%s: All Sections" % des
        if self.estart:
            des = "%s who Joined Between %s and %s" % (des, self.estartd,
                self.eendd)
        else:
            des = "%s who Joined On or Before %s" % (des, self.eendd)
        return des

    def getValues(self, data):
        col = self.sql.memmst_col
        # Membership Number
        self.memno = data[col.index("mlm_memno")]
        # Title
        tit = data[col.index("mlm_title")]
        # Surname
        sur = data[col.index("mlm_surname")]
        # First Names
        nam = data[col.index("mlm_names")]
        # Initials
        ini = data[col.index("mlm_initial")]
        # Combined Name
        sti = "%s, %s %s" % (sur, tit, ini)
        # Gender
        gen = data[col.index("mlm_gender")]
        # Date of Birth
        dob = data[col.index("mlm_dob")]
        # Age
        if dob:
            age = dateDiff(dob, self.repdt, "years")
        else:
            age = 0
        # Identity Number
        idn = data[col.index("mlm_idnum")]
        # Entry Date
        doe = data[col.index("mlm_entry")]
        # Payment Plan
        pay = data[col.index("mlm_payplan")]
        # Entry Years
        if doe:
            yrs = dateDiff(doe, self.repdt, "years")
        else:
            yrs = 0
        # Status
        if data[col.index("mlm_state")] == "A":
            sta = "Active"
        elif data[col.index("mlm_state")] == "D":
            sta = "Deceased"
        elif data[col.index("mlm_state")] == "I":
            sta = "Inactive"
        elif data[col.index("mlm_state")] == "R":
            sta = "Resigned"
        elif data[col.index("mlm_state")] == "S":
            sta = "Suspended"
        elif data[col.index("mlm_state")] == "X":
            sta = "Defaulted"
        # Status Date
        sdt = data[col.index("mlm_sdate")]
        # Proposer
        prp = self.sql.getRec("memmst", where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=",
            data[col.index("mlm_proposer")])], limit=1)
        if not prp:
            prn = "Unknown"
            pry = 0
        else:
            prn = "%s, %s %s" % (prp[col.index("mlm_surname")],
                prp[col.index("mlm_title")], prp[col.index("mlm_initial")])
            if prp[col.index("mlm_entry")]:
                pry = dateDiff(prp[col.index("mlm_entry")],self.repdt,"years")
            else:
                pry = 0
        # Seconder
        sec = self.sql.getRec("memmst", where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=",
            data[col.index("mlm_seconder")])], limit=1)
        if not sec:
            sen = "Unknown"
            sey = 0
        else:
            sen = "%s, %s %s" % (sec[col.index("mlm_surname")],
                sec[col.index("mlm_title")], sec[col.index("mlm_initial")])
            if sec[col.index("mlm_entry")]:
                sey = dateDiff(sec[col.index("mlm_entry")],self.repdt,"years")
            else:
                sey = 0
        # Postal Address
        rcp = self.sql.getRec("memadd", where=[("mla_cono", "=",
            self.opts["conum"]), ("mla_memno", "=", self.memno), ("mla_type",
            "=", "P")], limit=1)
        if not rcp:
            rcp = [self.opts["conum"], self.memno, "P", "", "", "", "", "", "",
                ""]
        if self.df.repprt[2] == "export":
            pad = rcp[3:]
            for x in range(3, len(rcp)):
                if self.padcol[x - 3] < len(rcp[x]):
                    self.padcol[x - 3] = len(rcp[x])
        else:
            pad = rcp[3]
            if rcp[4]:
                pad = "%s, %s" % (pad, rcp[4])
            if rcp[5]:
                pad = "%s, %s" % (pad, rcp[5])
            if rcp[7]:
                pad = "%s, %s" % (pad, rcp[7])
        # Street Address
        rcs = self.sql.getRec("memadd", where=[("mla_cono", "=",
            self.opts["conum"]), ("mla_memno", "=", self.memno), ("mla_type",
            "=", "R")], limit=1)
        if not rcs:
            rcs = [self.opts["conum"], self.memno, "R", "", "", "", "", "", "",
                ""]
        if self.df.repprt[2] == "export":
            sad = rcs[3:]
            for x in range(3, len(rcs)):
                if self.sadcol[x - 3] < len(rcs[x]):
                    self.sadcol[x - 3] = len(rcs[x])
        else:
            sad = rcs[3]
            if rcs[4]:
                sad = "%s, %s" % (sad, rcs[4])
            if rcs[5]:
                sad = "%s, %s" % (sad, rcs[5])
            if rcs[7]:
                sad = "%s, %s" % (sad, rcs[7])
        # Active Category
        whr = [
            ("mlc_cono", "=", self.opts["conum"]),
            ("mlc_memno", "=", self.memno),
            ("mlc_type", "=", "B"),
            ("mcc_cono=mlc_cono",),
            ("mcc_type=mlc_type",),
            ("mcc_code=mlc_code",)]
        cat = self.sql.getRec(tables=["memcat", "memctc"], cols=["mcc_desc"],
            where=whr, limit=1)
        if cat:
            cat = cat[0]
        else:
            cat = "Unknown Category"
        # Contact Details
        kon = self.sql.getRec(tables=["memctk", "memkon"], cols=["mck_type",
            "mlk_detail"], where=[("mlk_cono", "=", self.opts["conum"]),
            ("mlk_memno", "=", self.memno), ("mck_code=mlk_code",)])
        # Home Tel
        htl = ""
        # Work Tel
        wtl = ""
        # Mobile
        cel = ""
        # Email
        em1 = ""
        em2 = ""
        for k in kon:
            if k[0] == "H" and not htl:
                htl = k[1]
            if k[0] == "W" and not wtl:
                wtl = k[1]
            if k[0] == "M" and not cel:
                cel = k[1]
            if k[0] == "E":
                if not em1:
                    em1 = k[1]
                else:
                    em2 = k[1]
        nat = countries[data[col.index("mlm_nation")]]
        if nat:
            nat = nat[1]
        else:
            nat = "Unknown"
        occ = self.sql.getRec("memcto", cols=["mco_desc"],
            where=[("mco_code", "=", data[col.index("mlm_occup")])],
            limit=1)
        if occ:
            occ = occ[0]
        else:
            occ = "Unknown"
        if 22 in self.cnums:
            # Category Notes
            if self.cat == "C" or (self.cat == "D" and self.cod):
                nte = self.sql.getRec("memcat", cols=["mlc_note"],
                    where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno",
                    "=", self.memno), ("mlc_type", "=", self.cat), ("mlc_code",
                    "=", self.cod)], limit=1)
                if not nte:
                    nte = [""]
            elif self.cat == "D":
                chk = self.sql.getRec("memcat", cols=["mlc_note"],
                    where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno",
                    "=", self.memno), ("mlc_type", "=", self.cat)])
                if not chk:
                    nte = ["Unknown"]
                else:
                    nte = ""
                    for n in chk:
                        if not n[0]:
                            continue
                        if not nte:
                            nte = n[0]
                        else:
                            nte = "%s, %s" % (nte, n[0])
                    if nte:
                        nte = [nte]
                    else:
                        nte = ["Unknown"]
            else:
                nte = [""]
            nte = nte[0]
        if 25 in self.cnums:
            # Account Balance
            if sta == "Active":
                self.raiseExtraTrans()
            bal = self.sql.getRec("memtrn", cols=["sum(mlt_tramt)"],
                where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_memno",
                "=", self.memno)], limit=1)
            if not bal:
                bal = 0
            else:
                bal = bal[0]
            self.opts["mf"].dbm.rollbackDbase()
        if 26 in self.cnums:
            # Sports Categories
            col = ["mcc_rgrp"]
            whr = [
                ("mlc_cono", "=", self.opts["conum"]),
                ("mlc_memno", "=", self.memno),
                ("mlc_type", "=", "C"),
                ("mlc_end", "=", 0),
                ("mcc_cono=mlc_cono",),
                ("mcc_type=mlc_type",),
                ("mcc_code=mlc_code",)]
            spc = self.sql.getRec(tables=["memcat", "memctc"], cols=col,
                where=whr)
            chk = []
            for s in spc:
                chk.append(s[0])
            asc = []
            for g in self.rgrps:
                if g in chk:
                    asc.append(g)
                else:
                    asc.append("  ")
        val = []
        if 0 in self.cnums:
            val.append(self.memno)
        if 1 in self.cnums:
            val.append(sta)
        if 2 in self.cnums:
            val.append(sdt)
        if 3 in self.cnums:
            val.append(sti)
        if 4 in self.cnums:
            val.append(sur)
        if 5 in self.cnums:
            val.append(tit)
        if 6 in self.cnums:
            val.append(nam)
        if 7 in self.cnums:
            val.append(gen)
        if 8 in self.cnums:
            val.append(dob)
        if 9 in self.cnums:
            val.append(age)
        if 10 in self.cnums:
            val.append(idn)
        if 11 in self.cnums:
            val.append(doe)
        if 12 in self.cnums:
            val.append(yrs)
        if 13 in self.cnums:
            val.append(pay)
        if 14 in self.cnums:
            val.append(cat)
        if 15 in self.cnums:
            val.append(htl)
        if 16 in self.cnums:
            val.append(wtl)
        if 17 in self.cnums:
            val.append(cel)
        if 18 in self.cnums:
            val.append(em1)
        if 19 in self.cnums:
            val.append(em2)
        if 20 in self.cnums:
            if self.df.repprt[2] == "export":
                val.extend(pad)
            else:
                val.append(pad)
        if 21 in self.cnums:
            if self.df.repprt[2] == "export":
                val.extend(sad)
            else:
                val.append(sad)
        if 22 in self.cnums:
            val.append(nte)
        if 23 in self.cnums:
            val.append(prn)
            val.append(pry)
        if 24 in self.cnums:
            val.append(sen)
            val.append(sey)
        if 25 in self.cnums:
            val.append(bal)
        if 26 in self.cnums:
            val.extend(asc)
        if 27 in self.cnums:
            nte = self.sql.getRec("ctlnot", cols=["not_desc"],
                where=[("not_cono", "=", self.opts["conum"]), ("not_sys",
                "=", "MEM"), ("not_key", "=", str(self.memno))],
                order="not_seq desc", limit=1)
            if nte:
                val.append(nte[0])
            else:
                val.append("")
        if 28 in self.cnums:
            val.append(nat)
        if 29 in self.cnums:
            val.append(occ)
        return val

    def getCode(self, desc):
        a = desc.split()
        if len(a) == 1:
            return "%s  " % a[0][0].capitalize()
        if a[1] == "-":
            return "%s%s" % (a[0][0].capitalize(), a[2][0].capitalize())
        return "%s%s" % (a[0][0].capitalize(), a[1][0].capitalize())

    def raiseExtraTrans(self):
        self.tme = mthendDate(self.repdt)
        if int(self.tme / 100) == int(self.opts["period"][2][0] / 100):
            self.ynd = True
        else:
            self.ynd = False
        yy = int(self.tme / 10000)
        mm = (int(self.tme / 100) % 100) + 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nxtdt = (yy * 10000) + (mm * 100) + 1
        self.refno = 0
        if self.ynd:
            data = doChkCatChg(self.opts["mf"], self.opts["conum"],
                self.memno, self.nxtdt)
            if data:
                self.doRaiseCharge("B", data[0], data[1], data[3], data[4],
                    data[5], skip=True)
                self.sql.delRec("memcat", where=[("mlc_cono", "=",
                    self.opts["conum"]), ("mlc_memno", "=", self.memno),
                    ("mlc_type", "=", "B"), ("mlc_code", "=", data[0])])
                self.sql.insRec("memcat", data=[self.opts["conum"], self.memno,
                    "B", data[7], "", self.nxtdt, 0, 0])
        cols = ["mlc_type", "mlc_code", "mcc_desc", "mcc_freq", "mlc_start",
            "mlc_end", "mlc_last"]
        wher = [
            ("mlc_cono", "=", self.opts["conum"]),
            ("mlc_memno", "=", self.memno),
            ("mlc_start", ">", 0),
            ("mlc_start", "<=", self.nxtdt),
            ("mcc_cono=mlc_cono",),
            ("mcc_type=mlc_type",),
            ("mcc_code=mlc_code",),
            ("mcc_freq", "<>", "N")]
        cats = self.sql.getRec(tables=["memcat", "memctc"], cols=cols,
            where=wher, order="mlc_type, mlc_code")
        for ctyp, code, desc, freq, start, end, last in cats:
            if start > self.nxtdt:
                # Not yet Started
                continue
            if last and end and end < self.nxtdt:
                # Ended
                continue
            if last and freq == "O":
                # Once Off
                continue
            if last and last > self.opts["period"][2][0]:
                # Already Raised for Next Period in Advance
                continue
            if not self.ynd and last and freq == "A" and \
                    last >= self.opts["period"][1][0] and \
                    last <= self.opts["period"][2][0]:
                # Already Raised in Financial Period
                continue
            self.doRaiseCharge(ctyp, code, start, last, freq, desc)

    def doRaiseCharge(self, ctyp, code, start, last, freq, desc, skip=False):
        if freq == "O":
            dte = True
            nxt = False
        else:
            dte = False
            nxt = bool(self.ynd or freq == "M")
            if not last:
                if dateDiff(start, self.tme, "days") > self.ldays:
                    dte = True
                else:
                    nxt = True
        if dte:
            trdt = start
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(ctyp, code, desc, trdt, amt)
        if not skip and nxt:
            trdt = self.nxtdt
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(ctyp, code, desc, trdt, amt)
        if dte or (not skip and nxt):
            self.sql.updRec("memcat", cols=["mlc_last"], data=[trdt],
                where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno",
                "=", self.memno), ("mlc_type", "=", ctyp), ("mlc_code", "=",
                code)])

    def doGetCharge(self, ctyp, code, date):
        prc = self.sql.getRec("memctp", where=[("mcp_cono", "=",
            self.opts["conum"]), ("mcp_type", "=", ctyp), ("mcp_code", "=",
            code), ("mcp_date", "<=", date)], order="mcp_date desc", limit=1)
        if not prc:
            # No Price
            return
        if prc[5] == "N" or (self.ynd and date == self.nxtdt):
            # Not Pro Rata or End of Financial Year
            amt = CCD(prc[6], "UD", 12.2).work
        else:
            # Extract Pro Rata Rate
            mths = 17 - dateDiff(date, self.opts["period"][2][0], "months")
            if mths < 1:
                mths = 12
            amt = CCD(prc[mths], "UD", 12.2).work
        if not amt:
            # No Charge
            return
        else:
            return amt

    def doUpdateTables(self, ctyp, code, desc, trdt, amt):
        batch = "PROFORM"
        self.refno += 1
        refno = "PF%07i" % self.refno
        curdt = int(trdt / 100)
        # VAT Rate and Amount
        vrte = getVatRate(self.sql, self.opts["conum"], self.taxdf, trdt)
        if vrte is None:
            vrte = 0.0
        vat = CCD(round(((amt * vrte) / 114), 2), "UD", 12.2).work
        # Members Ledger Transaction (memtrn)
        self.sql.insRec("memtrn", data=[self.opts["conum"], self.memno, 1,
            refno, batch, trdt, amt, vat, curdt, ctyp, code, desc, self.taxdf,
            "", self.opts["capnm"], self.sysdt, 0], unique="mlt_refno")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
