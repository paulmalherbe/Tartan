"""
SYNOPSIS
    Membership Maintenance.

    This file is part of Tartan Systems (TARTAN).

    The PHOTODIR environment variable is as follows:

        Linux:
            export PHOTODIR="path_to_photo_images"

        Windows:
            set PHOTODIR=path_to_photo_images

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

import os, time
from TartanClasses import CCD, DrawForm, GetCtl, NotesCreate, PwdConfirm
from TartanClasses import RepPrt, Sql, SelectChoice, ShowImage, TabPrt
from TartanClasses import TartanDialog
from tartanFunctions import askChoice, askQuestion, callModule, copyList
from tartanFunctions import dateDiff, doChkCatChg, doPrinter, getModName
from tartanFunctions import getNextCode, getTrn, getVatRate, mthendDate
from tartanFunctions import showError, showWarning
from tartanWork import countries, mltrtp

class ml1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        tabs = ["chglog", "ctlvrf", "memadd", "memcat", "memctc", "memctk",
            "memctp", "memctl", "memcto", "memkon", "memlnk", "memmst",
            "memsta", "memtrn", "memtrs", "bwltab", "tplmst"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        mc = GetCtl(self.opts["mf"])
        ctlmst = mc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        mods = ctlmst["ctm_modules"]
        mods = [mods[i:i+2] for i in range(0, len(mods), 2)]
        if "BC" in mods:
            bwlctl = mc.getCtl("bwlctl", self.opts["conum"])
            self.mlint = bwlctl["ctb_mlint"]
            self.samen = bwlctl["ctb_samen"]
            self.mscat = bwlctl["ctb_mscat"]
            self.mstart = bwlctl["ctb_mstart"]
            self.fstart = bwlctl["ctb_fstart"]
            self.nstart = bwlctl["ctb_nstart"]
        else:
            self.mlint = "N"
        memctl = mc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        memcat = self.sql.getRec("memctc", cols=["count(*)"],
            where=[("mcc_cono", "=", self.opts["conum"]),
            ("mcc_type", "=", "B")], limit=1)
        if not memcat[0]:
            showError(self.opts["mf"].body, "Missing Category",
                "There Are No Membership Category Records.")
            return
        self.ldays = memctl["mcm_ldays"]
        self.lme = memctl["mcm_lme"]
        if "PHOTODIR" in os.environ:
            self.photo = os.environ["PHOTODIR"]
        else:
            self.photo = memctl["mcm_photo"]
        self.logo = memctl["mcm_logo"]
        self.cftpl = memctl["mcm_cftpl"]
        self.cbtpl = memctl["mcm_cbtpl"]
        self.fromad = memctl["mcm_emadd"]
        yy = int(self.lme / 10000)
        mm = (int(self.lme / 100) % 100) + 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.tme = mthendDate((yy*10000) + (mm*100) + 1)
        if int(self.tme / 100) == int(self.opts["period"][2][0] / 100):
            self.ynd = True
        else:
            self.ynd = False
        self.curdt = int(self.tme / 100)
        mm += 1
        while mm > 12:
            yy += 1
            mm -= 12
        self.nxtdt = (yy * 10000) + (mm * 100) + 1
        tst = self.sql.getRec("memmst", cols=["count(*)"],
            where=[("mlm_cono", "=", self.opts["conum"]),
            ("mlm_oldno", "<>", 0)], limit=1)
        if tst[0]:
            self.oldno = True
        else:
            self.oldno = False
        t = time.localtime()
        self.sysdt = ((t[0] * 10000) + (t[1] * 100) + t[2])
        if dateDiff(self.tme, self.sysdt, "months") > 1:
            showError(self.opts["mf"].body, "Date Error",
                """More than Two Month Ends Have Not Been Run.

This Could Have Serious Date and Transaction Issues.

Please Contact your Accounts Manager and Report This.""")
        self.new = False
        self.edit = False
        self.idnum = 0
        self.proposer = 0
        self.seconder = 0
        self.years = 0
        self.select = "T"
        self.image = None
        return True

    def mainProcess(self):
        cols = [("mlm_memno", "", 0, "Mem-No")]
        if self.oldno:
            cols.append(("mlm_oldno", "", 0, "Old-No", "F"))
        cols.extend([
                ("mlm_idnum", "", 0, "Identity-Numb"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")])
        mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": cols,
            "where": [("mlm_cono", "=", self.opts["conum"])],
            "order": "mlm_surname, mlm_names"}
        data = []
        keys = list(countries.keys())
        keys.sort()
        for key in keys:
            data.append((key, countries[key][1]))
        nat = {
            "stype": "C",
            "titl": "Select the Required Country",
            "head": ("CD", "Country"),
            "data": data}
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": (("A", "Fees"), ("B", "Category"), ("C", "Section"))}
        cat = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["C", "mcc_type", 1, 4]]}
        occ = {
            "stype": "R",
            "tables": ("memcto",),
            "cols": (
                ("mco_code", "", 0, "Cd"),
                ("mco_desc", "", 0, "Description", "Y"))}
        kon = {
            "stype": "R",
            "tables": ("memctk",),
            "cols": (
                ("mck_code", "", 0, "Cd"),
                ("mck_desc", "", 0, "Description", "Y"))}
        r1s = (
            ("Male", "M"),
            ("Female", "F"))
        r2s = (
            ("Yes", "Y"),
            ("No", "N"))
        r3s = (
            ("Active", "A"),
            ("Deceased", "D"),
            ("Defaulted", "X"),
            ("Inactive", "I"),
            ("Resigned", "R"),
            ("Suspended", "S"))
        r4s = [
            ("Status", "U"),
            ("Transactions", "T")]
        tag = (
            ("Personal",self.doTags,None,("T",0,1)),
            ("Addresses",self.doTags,None,("T",0,1)),
            ("Contacts",self.doTags,None,("T",0,1)),
            ("Categories",self.doTags,None,("T",0,1)),
            ("Links",self.doTags,None,("T",0,1)),
            ("Movements",self.doTrans1,None,("T",0,1)),
            ("Photo",self.doPhoto,None,("T",0,1)))
        fld = [
            (("T",0,0,0),"I@mlm_memno",0,"","",
                "","N",self.doMemNo,mlm,None,None),
            (("T",0,0,0),"I@mlm_title",0,"","Title(noesc)",
                "","N",self.doTitle,None,None,("notblank",)),
            (("T",0,0,0),"O@mlm_initial",0,""),
            (("T",0,0,0),"ITX",30,"Surname","",
                "","N",self.doSurname,None,None,("notblank",)),
            (("T",1,0,0),"ITX",30,"Names","",
                "","N",self.doNames,None,None,("notblank",)),
            (("T",1,1,0),("IRB",r1s),0,"Gender","",
                "M","N",self.doGender,None,None,None),
            (("T",1,2,0),"I@mlm_nation",0,"","",
                "","N",self.doNation,nat,None,("efld",)),
            (("T",1,2,0),"ONA",50,""),
            (("T",1,3,0),"I@mlm_dob",0,"","",
                "","N",self.doDOB,None,None,("efld",)),
            (("T",1,3,37,40),"OUI",3,"Age"),
            (("T",1,4,0),"I@mlm_idnum",0,"","",
                "","N",self.doID,None,None,("idno",)),
            (("T",1,5,0),"I@mlm_occup",0,"","",
                "","N",self.doOccCode,occ,None,("efld",)),
            (("T",1,5,0),"INA",30,"","",
                "","N",self.doOccDesc,None,None,("notblank",)),
            (("T",1,6,0),"I@mlm_proposer",0,"","",
                "","N",self.doProposer,mlm,None,("efld",)),
            (("T",1,6,0),"ONA",40,""),
            (("T",1,7,0),"I@mlm_seconder",0,"","",
                "","N",self.doSeconder,mlm,None,("efld",)),
            (("T",1,7,0),"ONA",40,""),
            (("T",1,8,0),"I@mlm_entry",0,"","",
                "","N",self.doEntry,None,None,("notzero",)),
            (("T",1,8,35,40),"OUI",3,"Years"),
            (("T",1,9,0),("IRB",r2s),0,"Payment Plan","",
                "N","N",self.doPayPlan,None,None,None),
            (("T",1,10,0),"O@mlm_oldno",0,""),
            (("T",1,11,0),("IRB",r3s),0,"Status","",
                "A","N",self.doStatus,None,None,None),
            (("T",1,12,0),"I@mlm_sdate",0,"","",
                "","N",self.doDate,None,None,("notzero",)),
            (("T",1,12,33),"OSD",13.2,"Balance")]
        fld.extend([
            (("T",2,0,0,35),"ITX",30,"Postal      Address Line 1",
                "Postal Address Line 1","","N",None,None,None,("efld",)),
            (("T",2,1,0,35),"ITX",30,"            Address Line 2",
                "Postal Address Line 2","","N",None,None,None,("efld",)),
            (("T",2,2,0,35),"ITX",30,"            Address Line 3",
                "Postal Address Line 2","","N",None,None,None,("efld",)),
            (("T",2,3,0,35),"ITX",30,"            City","",
                "","N",None,None,None,("efld",)),
            (("T",2,4,0,35),"ITX",4,"            Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",2,5,0,35),"ITX",30,"            Region","",
                "","N",None,None,None,("efld",)),
            (("T",2,6,0,35),"ITX",30,"            Country","",
                "","N",None,None,None,("efld",)),
            (("T",2,7,0,35),("IRB",r2s),0,"Residential Same as Postal","",
                "Y","N",self.doSameAdd,None,None,None),
            (("T",2,8,0,35),"ITX",30,"Residential Address Line 1",
                "Residential Address Line 1","","N",None,None,None,("efld",)),
            (("T",2,9,0,35),"ITX",30,"            Address Line 2",
                "Residential Address Line 1","","N",None,None,None,("efld",)),
            (("T",2,10,0,35),"ITX",30,"            Address Line 3",
                "Residential Address Line 1","","N",None,None,None,("efld",)),
            (("T",2,11,0,35),"ITX",30,"            City","",
                "","N",None,None,None,("efld",)),
            (("T",2,12,0,35),"ITX",4,"            Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",2,13,0,35),"ITX",30,"            Region","",
                "","N",None,None,None,("efld",)),
            (("T",2,14,0,35),"ITX",30,"            Country","",
                "","N",None,None,None,("efld",)),
            (("T",3,0,0),"IUI",1,"Contacts Sequence","",
                "","N",self.doSequence,None,None,("between",0,9)),
            (("C",3,0,0),"OUI",1,"S"),
            (("C",3,0,1),"I@mck_code",0,"","",
                "","N",self.doConCod,kon,self.doDelete,("efld",)),
            (("C",3,0,2),"O@mck_desc",0,""),
            (("C",3,0,3),"ITX",35,"Contact Details","",
                "","N",None,None,None,("notblank",)),
            (("T",4,0,0),"IUI",1,"Category Sequence","",
                "","N",self.doSequence,None,None,("between",0,9)),
            (("C",4,0,0),"OUI",1,"S"),
            (("C",4,0,1),"I@mlc_type",0,"","",
               "","N",self.doCatTyp,typ,self.doDelete,
               ("in",("A","B","C","D"))),
            (("C",4,0,2),"I@mlc_code",0,"","",
                "","N",self.doCatCod,cat,None,("efld",)),
            (("C",4,0,3),"O@mcc_freq",0,""),
            (("C",4,0,4),"O@mcc_desc",35,""),
            (("C",4,0,5),"ITX",20,"Notes","",
                "","N",self.doCatNote,None,None,("efld",)),
            (("C",4,0,6),"I@mlc_start",0,"","",
                "","N",self.doCatStart,None,None,("efld",)),
            (("C",4,0,7),"I@mlc_end",0,"","",
                "","N",None,None,None,("efld",)),
            (("C",4,0,8),"O@mlc_last",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",5,0,0),"IUI",1,"Links Sequence","",
                "","N",self.doSequence,None,None,("between",0,9)),
            (("C",5,0,0),"OUI",1,"S"),
            (("C",5,0,1),"I@mll_lnkno",0,"","",
                "","N",self.doLnkNo,mlm,self.doDelete,("notzero",)),
            (("C",5,0,2),"O@mlm_title",0,""),
            (("C",5,0,3),"O@mlm_surname",0,""),
            (("C",5,0,4),"O@mlm_names",0,""),
            (("T",6,0,0),("IRB",r4s),0,"","Selection",
                "T","N",self.doTrans2,None,None,None,None)])
        row = [0, 0, 0, 10, 10, 10, 0, 0]
        tnd = (
            (self.doTopEnd,"n"),
            (self.doTopEnd,"y"),
            (self.doTopEnd,"y"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            (self.doTopEnd,"n"),
            None,
            None)
        txt = (
            self.doExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit,
            self.doTopExit)
        cnd = (
            None,
            None,
            None,
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            (self.doColEnd,"n"),
            None,
            None)
        cxt = (
            None,
            None,
            None,
            self.doColExit,
            self.doColExit,
            self.doColExit,
            None,
            None)
        if self.opts["level"] < 3:
            but = [("New",None,self.doNew,0,None,None,None,1)]
        else:
            but = [("New",None,self.doNew,0,("T",0,1),None,None,1)]
        but.extend([
            ("Edit",None,self.doEdit,2,None,None,None,1),
            ("Update",None,self.doUpdate,2,None,None,None,1),
            ("Notes",None,self.doNotes,2,None,None,None,1),
            ("Print",None,self.doPrint,2,None,None,None,1),
            ("Reset",None,self.doClear,2,None,None,None,2,3),
            ("Exit",None,self.doExit,1,None,None,None,2,2)])
        self.df = TartanDialog(self.opts["mf"], tops=False,
            tags=tag, eflds=fld, rows=row, tend=tnd, txit=txt, cend=cnd,
            cxit=cxt, butt=but, clicks=self.doClick, focus=False)
        self.df.focusField("T", 0, 1)

    def doClick(self, *opts):
        if not self.new and not self.edit:
            return
        if opts[0] == (1, 8):
            # Occupation Details
            return
        if opts[0] == (1, 20):
            # ACS Status
            return
        if self.new and opts[0][0] == 1 and opts[0][1] > 16:
            # Status, Status Date and Balance
            return
        if opts[0][0] == 2 and opts[0][1] > 7:
            # Residential Address
            if self.df.t_work[2][0][7] == "Y":
                # Residential same as Postal
                return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doTags(self):
        if not self.new and not self.edit:
            return
        if self.df.topq[self.df.pag]:
            self.df.focusField("T", self.df.pag, 1)
        else:
            self.df.focusField("C", self.df.pag, 1)

    def doNew(self):
        if self.df.pag == 0:
            self.doSetButtons((2, 5), (0, 1, 3, 4))
            self.new = True
            self.memcat = []
            self.df.focusField("T", 0, 2)

    def doEdit(self):
        if self.df.pag > 5:
            return
        self.edit = True
        self.newocc = False
        self.doAllTags(state="disabled", exclude=(0, 1, 2, 3, 4))
        self.doSetButtons((2, 5), (0, 1, 3, 4))
        if self.df.pag == 0:
            self.df.focusField("T", self.df.pag, 2)
        else:
            self.df.focusField("T", self.df.pag, 1)

    def doDelete(self):
        # Clear the Row
        self.df.clearLine(self.df.pag, self.df.row)
        # Resequence all Rows
        cnt = 0
        for row in self.df.c_work[self.df.pag]:
            if row[1]:
                pos = cnt * self.df.colq[self.df.pag]
                self.df.loadEntry("C", self.df.pag, pos, data=cnt)
                for num, fld in enumerate(row[1:]):
                    self.df.loadEntry("C", self.df.pag, pos+num+1, data=fld)
                cnt += 1
        for row in range(cnt, self.df.rows[self.df.pag]):
            self.df.clearLine(self.df.pag, row)
        # Return
        self.df.focusField("T", self.df.pag, 1)
        return "nf"

    def doMemNo(self, frt, pag, r, c, p, i, w):
        # Flags
        self.new = False
        self.edit = False
        # memmst table
        self.memmst = self.sql.getRec("memmst", where=[("mlm_cono",
            "=", self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not self.memmst:
            return "Invalid Membership Number"
        self.memno = w
        # save memcat table
        self.memcat = self.sql.getRec("memcat", where=[("mlc_cono",
            "=", self.opts["conum"]), ("mlc_memno", "=", self.memno)],
            order="mlc_type, mlc_code")
        self.title = self.memmst[self.sql.memmst_col.index("mlm_title")]
        self.initial = self.memmst[self.sql.memmst_col.index("mlm_initial")]
        self.surname = self.memmst[self.sql.memmst_col.index("mlm_surname")]
        names = self.memmst[self.sql.memmst_col.index("mlm_names")]
        gender = self.memmst[self.sql.memmst_col.index("mlm_gender")]
        self.nation = self.memmst[self.sql.memmst_col.index("mlm_nation")]
        self.dob = self.memmst[self.sql.memmst_col.index("mlm_dob")]
        self.idnum = self.memmst[self.sql.memmst_col.index("mlm_idnum")]
        self.occup = self.memmst[self.sql.memmst_col.index("mlm_occup")]
        self.proposer = self.memmst[self.sql.memmst_col.index("mlm_proposer")]
        self.seconder = self.memmst[self.sql.memmst_col.index("mlm_seconder")]
        self.entry = self.memmst[self.sql.memmst_col.index("mlm_entry")]
        payplan = self.memmst[self.sql.memmst_col.index("mlm_payplan")]
        oldno = self.memmst[self.sql.memmst_col.index("mlm_oldno")]
        self.oldsta = self.memmst[self.sql.memmst_col.index("mlm_state")]
        self.sdate = self.memmst[self.sql.memmst_col.index("mlm_sdate")]
        self.newsta = self.oldsta
        # Load All Fields
        self.df.loadEntry("T", 0, 1, data=self.title)
        self.df.loadEntry("T", 0, 2, data=self.initial)
        self.df.loadEntry("T", 0, 3, data=self.surname)
        self.df.loadEntry("T", 1, 0, data=names)
        self.df.loadEntry("T", 1, 1, data=gender)
        self.df.loadEntry("T", 1, 2, data=self.nation)
        self.df.loadEntry("T", 1, 3, data=countries[self.nation][1])
        self.df.loadEntry("T", 1, 4, data=self.dob)
        if not self.dob:
            self.age = 0
            self.df.loadEntry("T", 1, 5, data=0)
        else:
            self.age = dateDiff(self.dob, self.sysdt, "years")
            self.df.loadEntry("T", 1, 5, data=self.age)
        self.df.loadEntry("T", 1, 6, data=self.idnum)
        self.df.loadEntry("T", 1, 7, data=self.occup)
        acc = self.sql.getRec("memcto", cols=["mco_desc"],
            where=[("mco_code", "=", self.occup)], limit=1)
        self.df.loadEntry("T", 1, 8, data=acc[0])
        for x, f in enumerate(("mlm_proposer", "mlm_seconder")):
            idx = (x * 2) + 9
            cnt = self.sql.memmst_col.index(f)
            self.df.loadEntry("T", 1, idx, data=self.memmst[cnt])
            acc = self.sql.getRec("memmst", cols=["mlm_title",
                "mlm_initial", "mlm_surname"], where=[("mlm_cono", "=",
                self.opts["conum"]), ("mlm_memno", "=", self.memmst[cnt])],
                limit=1)
            if not acc:
                self.df.loadEntry("T", 1, (idx + 1), data="%s" % "Unknown")
            else:
                self.df.loadEntry("T", 1, (idx + 1), data="%s %s %s" % (acc[0],
                    acc[1], acc[2]))
        self.df.loadEntry("T", 1, 13, data=self.entry)
        if not self.entry or not self.sdate:
            self.years = 0
        elif self.oldsta == "A":
            self.years = dateDiff(self.entry, self.sysdt, "years")
        else:
            self.years = dateDiff(self.entry, self.sdate, "years")
        self.df.loadEntry("T", 1, 14, data=self.years)
        self.df.loadEntry("T", 1, 15, data=payplan)
        self.df.loadEntry("T", 1, 16, data=oldno)
        self.df.loadEntry("T", 1, 17, data=self.oldsta)
        self.df.loadEntry("T", 1, 18, data=self.sdate)
        # Outstanding Balance including pro-forma
        if self.oldsta == "A":
            self.raiseExtraTrans()
        bal = self.sql.getRec("memtrn", cols=["sum(mlt_tramt)"],
            where=[("mlt_cono", "=", self.opts["conum"]), ("mlt_memno", "=",
            self.memno)], limit=1)
        if not bal[0]:
            self.df.loadEntry("T", 1, 19, data=0)
        else:
            self.df.loadEntry("T", 1, 19, data=bal[0])
        # memadd table
        acc = self.sql.getRec("memadd", where=[("mla_cono", "=",
            self.opts["conum"]), ("mla_memno", "=", self.memno), ("mla_type",
            "=", "P")], limit=1)
        if acc:
            for n, f in enumerate(("mla_add1", "mla_add2", "mla_add3",
                    "mla_city", "mla_code", "mla_region", "mla_country")):
                cnt = self.sql.memadd_col.index(f)
                self.df.loadEntry("T", 2, n, data=acc[cnt])
        acc = self.sql.getRec("memadd", where=[("mla_cono", "=",
            self.opts["conum"]), ("mla_memno", "=", self.memno), ("mla_type",
            "=", "R")], limit=1)
        if not acc:
            self.df.loadEntry("T", 2, 7, data="Y")
        else:
            self.df.loadEntry("T", 2, 7, data="N")
            for n, f in enumerate(("mla_add1", "mla_add2", "mla_add3",
                    "mla_city", "mla_code", "mla_region", "mla_country")):
                cnt = self.sql.memadd_col.index(f)
                self.df.loadEntry("T", 2, n+8, data=acc[cnt])
        # memkon table
        acc = self.sql.getRec(tables=["memkon", "memctk"], cols=["mlk_code",
            "mck_desc", "mlk_detail"], where=[("mlk_cono", "=",
            self.opts["conum"]), ("mlk_memno", "=", self.memno),
            ("mck_code=mlk_code",)])
        for n, a in enumerate(acc):
            self.df.loadEntry("C", 3, (n * 4), data=n)
            self.df.loadEntry("C", 3, ((n * 4) + 1), data=a[0])
            self.df.loadEntry("C", 3, ((n * 4) + 2), data=a[1])
            self.df.loadEntry("C", 3, ((n * 4) + 3), data=a[2])
            self.df.loadEntry("T", 3, 0, data=n+1)
        # memcat table
        for n, m in enumerate(self.memcat):
            ctyp = m[self.sql.memcat_col.index("mlc_type")]
            code = m[self.sql.memcat_col.index("mlc_code")]
            note = m[self.sql.memcat_col.index("mlc_note")]
            start = m[self.sql.memcat_col.index("mlc_start")]
            end = m[self.sql.memcat_col.index("mlc_end")]
            last = m[self.sql.memcat_col.index("mlc_last")]
            acc = self.sql.getRec("memctc", cols=["mcc_freq",
                "mcc_desc"], where=[("mcc_cono", "=", self.opts["conum"]),
                ("mcc_type", "=", ctyp), ("mcc_code", "=", code)],
                limit=1)
            if not acc:
                showError(self.opts["mf"].body, "Invalid Category",
                    "There in an Incorrect Category on this Member's Record, "\
                    "Please Rectify It as a Matter of Urgency")
                acc = ["", "Unknown"]
            self.df.loadEntry("C", 4, (n * 9), data=n)
            self.df.loadEntry("C", 4, ((n * 9) + 1), data=ctyp)
            self.df.loadEntry("C", 4, ((n * 9) + 2), data=code)
            self.df.loadEntry("C", 4, ((n * 9) + 3), data=acc[0])
            self.df.loadEntry("C", 4, ((n * 9) + 4), data=acc[1])
            self.df.loadEntry("C", 4, ((n * 9) + 5), data=note)
            self.df.loadEntry("C", 4, ((n * 9) + 6), data=start)
            self.df.loadEntry("C", 4, ((n * 9) + 7), data=end)
            self.df.loadEntry("C", 4, ((n * 9) + 8), data=last)
            self.df.loadEntry("T", 4, 0, data=n+1)
        # memlnk table
        memlnk = self.sql.getRec("memlnk", cols=["mll_lnkno"],
            where=[("mll_cono", "=", self.opts["conum"]), ("mll_memno", "=",
            self.memno)], order="mll_lnkno")
        for n, k in enumerate(memlnk):
            acc = self.sql.getRec("memmst", cols=["mlm_title",
                "mlm_surname", "mlm_names"], where=[("mlm_cono", "=",
                self.opts["conum"]), ("mlm_memno", "=", k[0])], limit=1)
            if acc:
                self.df.loadEntry("C", 5, (n * 5), data=n)
                self.df.loadEntry("C", 5, ((n * 5) + 1), data=k[0])
                self.df.loadEntry("C", 5, ((n * 5) + 2), data=acc[0])
                self.df.loadEntry("C", 5, ((n * 5) + 3), data=acc[1])
                self.df.loadEntry("C", 5, ((n * 5) + 4), data=acc[2])
        # Set Tags and Buttons
        for num, tag in enumerate(self.df.tags):
            self.df.enableTag(num)
        if self.opts["level"] < 3:
            self.doSetButtons((3, 4, 5), (0, 1, 2))
        else:
            self.doSetButtons((1, 3, 4, 5), (0, 2))
        self.opts["mf"].updateStatus("")
        self.opts["mf"].status.focus_set()
        return "nd"

    def raiseExtraTrans(self):
        self.refno = 0
        acc = [self.memno]
        lnk = self.sql.getRec("memlnk", cols=["mll_lnkno"],
            where=[("mll_cono", "=", self.opts["conum"]), ("mll_memno", "=",
            self.memno)])
        for l in lnk:
            chk = self.sql.getRec("memmst", cols=["mlm_state"],
                where=[("mlm_cono", "=", self.opts["conum"]), ("mlm_memno",
                "=", l[0])], limit=1)
            if chk and chk[0] == "A":
                acc.append(l[0])
        for memno in acc:
            if self.ynd:
                data = doChkCatChg(self.opts["mf"], self.opts["conum"],
                    memno, self.nxtdt)
                if data:
                    if not data[3]:
                        self.doRaiseCharge(memno, "B", data[0], data[1],
                            data[2], data[3], data[4], data[5], skip=True)
                    self.sql.delRec("memcat", where=[("mlc_cono", "=",
                        self.opts["conum"]), ("mlc_memno", "=", memno),
                        ("mlc_type", "=", "B"), ("mlc_code", "=", data[0])])
                    self.sql.insRec("memcat", data=[self.opts["conum"], memno,
                        "B", data[7], "", self.nxtdt, 0, 0])
            cols = ["mlc_type", "mlc_code", "mcc_desc", "mcc_freq",
                "mlc_start", "mlc_end", "mlc_last"]
            wher = [
                ("mlc_cono", "=", self.opts["conum"]),
                ("mlc_memno", "=", memno),
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
                self.doRaiseCharge(memno, ctyp, code, start, end, last, freq,
                    desc)

    def doRaiseCharge(self, memno, ctyp, code, start, end, last, freq, desc, skip=False):
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
                self.doUpdateTables(memno, ctyp, code, desc, trdt, amt)
        if not skip and nxt:
            if end and self.nxtdt > end:
                return
            trdt = self.nxtdt
            amt = self.doGetCharge(ctyp, code, trdt)
            if amt:
                self.doUpdateTables(memno, ctyp, code, desc, trdt, amt)

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

    def doUpdateTables(self, memno, ctyp, code, desc, trdt, amt):
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
        self.sql.insRec("memtrn", data=[self.opts["conum"], memno, 1, refno,
            batch, trdt, amt, vat, curdt, ctyp, code, desc, self.taxdf,
            "", self.opts["capnm"], self.sysdt, 0], unique="mlt_refno")
        # Members Category Record (memcat)
        self.sql.updRec("memcat", cols=["mlc_last"], data=[trdt],
            where=[("mlc_cono", "=", self.opts["conum"]), ("mlc_memno", "=",
            memno), ("mlc_type", "=", ctyp), ("mlc_code", "=", code)])

    def doTitle(self, frt, pag, r, c, p, i, w):
        if not w[0].isupper():
            self.title = w.capitalize()
        else:
            self.title = w
        self.df.loadEntry(frt, pag, p, data=self.title)

    def doSurname(self, frt, pag, r, c, p, i, w):
        if not w[0].isupper():
            self.surname = w.capitalize()
        else:
            self.surname = w
        self.df.loadEntry(frt, pag, p, data=self.surname)

    def doNames(self, frt, pag, r, c, p, i, w):
        self.names = ""
        self.initial = ""
        for num, name in enumerate(w.split()):
            if num < 3:
                if not self.initial:
                    self.initial = name[0].upper()
                else:
                    self.initial = "%s %s" % (self.initial, name[0].upper())
            if not name[0].isupper():
                name = name.capitalize()
            if not self.names:
                self.names = name
            else:
                self.names = "%s %s" % (self.names, name)
        self.df.loadEntry("T", 0, 2, data=self.initial)
        self.df.loadEntry(frt, pag, p, data=self.names)

    def doGender(self, frt, pag, r, c, p, i, w):
        self.gender = w

    def doNation(self, frt, pag, r, c, p, i, w):
        self.nation = w
        try:
            self.df.loadEntry(frt, pag, p+1, data=countries[self.nation][1])
        except:
            return "Invalid Nationality"

    def doDOB(self, frt, pag, r, c, p, i, w):
        if not w and self.new:
            return "Invalid Date of Birth"
        self.dob = w
        if self.dob:
            self.age = dateDiff(w, self.sysdt, "years")
        else:
            self.age = 0
        self.df.loadEntry(frt, pag, p+1, data=self.age)

    def doID(self, frt, pag, r, c, p, i, w):
        if not w and self.nation == "ZA":
            return "Invalid Identity Number 1"
        if w:
            if self.dob % 1000000 != int(int(w) / 10000000):
                return "Invalid Identity Number 2"
            whr = [("mlm_cono", "=", self.opts["conum"])]
            if not self.new:
                whr.append(("mlm_memno", "<>", self.memno))
            whr.append(("mlm_nation", "=", self.nation))
            whr.append(("mlm_idnum", "=", w))
            chk = self.sql.getRec("memmst", where=whr, limit=1)
            if chk:
                showError(self.opts["mf"].body, "ID Number",
                    """A Member with this ID Number already Exists:

Number:  %s
Surname: %s
Names:   %s
""" % (chk[1], chk[4], chk[5]))
                return "rf"
        self.idnum = w

    def doOccCode(self, frt, pag, r, c, p, i, w):
        if not w:
            # Check for a Zero Record
            acc = self.sql.getRec("memcto", where=[("mco_code", "=",
                w)], limit=1)
            if not acc:
                # Get Next Number
                acc = self.sql.getRec("memcto", cols=["max(mco_code)"],
                    limit=1)
                if not acc or not acc[0]:
                    w = 1
                else:
                    w = acc[0] + 1
                self.df.loadEntry(frt, pag, p, data=w)
        acc = self.sql.getRec("memcto", cols=["mco_desc"],
            where=[("mco_code", "=", w)], limit=1)
        if not acc:
            ok = askQuestion(self.opts["mf"].body, "Occupation",
                "This Occupation Code Does Not Exist, Create It?")
            if ok == "no":
                return "Invalid Occupation Code"
            else:
                self.occup = w
        else:
            self.occup = w
            self.newocc = False
            self.df.loadEntry(frt, pag, p+1, data=acc[0])
            return "sk1"

    def doOccDesc(self, frt, pag, r, c, p, i, w):
        self.newocc = w

    def doProposer(self, frt, pag, r, c, p, i, w):
        if not w:
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="MEM", code="PropSec")
            if cf.flag == "no":
                return "Invalid Proposer"
            self.proposer = w
            return
        if self.seconder and w == self.seconder:
            return "Invalid Proposer, same as Seconder"
        acc = self.sql.getRec("memmst", cols=["mlm_title",
            "mlm_initial", "mlm_surname", "mlm_state"], where=[("mlm_cono",
            "=", self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not acc:
            return "Invalid Proposer"
        if acc[3] != "A":
            return "Invalid Proposer, Not Active"
        self.df.loadEntry(frt, pag, p+1, data="%s %s %s" % (acc[0],
            acc[1], acc[2]))
        self.proposer = w

    def doSeconder(self, frt, pag, r, c, p, i, w):
        if not w:
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="MEM", code="PropSec")
            if cf.flag == "no":
                return "Invalid Proposer"
            self.seconder = w
            return
        if self.proposer and w == self.proposer:
            return "Invalid Seconder, same as Proposer"
        acc = self.sql.getRec("memmst", cols=["mlm_title",
            "mlm_initial", "mlm_surname", "mlm_state"], where=[("mlm_cono",
            "=", self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not acc:
            return "Invalid Seconder"
        if acc[3] != "A":
            return "Invalid Seconder, Not Active"
        self.df.loadEntry(frt, pag, p+1, data="%s %s %s" % (acc[0],
            acc[1], acc[2]))
        self.seconder = w

    def doEntry(self, frt, pag, r, c, p, i, w):
        self.entry = w
        self.years = dateDiff(self.entry, self.sysdt, "years")
        self.df.loadEntry(frt, pag, p+1, data=self.years)

    def doPayPlan(self, frt, pag, r, c, p, i, w):
        self.pplan = w
        if self.new:
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.newsta = "A"
            self.df.loadEntry(frt, pag, p+2, data=self.newsta)
            self.sdate = self.entry
            self.df.loadEntry(frt, pag, p+3, data=self.sdate)
            self.df.loadEntry(frt, pag, p+4, data=0)
            return "sk4"

    def doStatus(self, frt, pag, r, c, p, i, w):
        self.newsta = w
        if self.newsta == self.oldsta:
            return "sk1"
        self.sdate = self.sysdt
        self.df.loadEntry(frt, pag, p+1, data=self.sdate)

    def doDate(self, frt, pag, r, c, p, i, w):
        self.sdate = w
        return "nd"

    def doSameAdd(self, frt, pag, r, c, p, i, w):
        if w == "Y":
            for x in range(p+1, p+8):
                self.df.loadEntry(frt, pag, x, data="")
            return "sk7"

    def doSequence(self, frt, pag, r, c, p, i, w):
        return self.doChkSeq(pag, w)

    def doConCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("memctk", cols=["mck_desc"],
            where=[("mck_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Contact Code"
        for line in self.df.c_work[pag]:
            if line[0] == r:
                break
            if line[1] == w:
                return "This Code Already Exists"
        self.koncod = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doConDel(self):
        self.sql.delRec("memkon", where=[("mlk_cono", "=", self.opts["conum"]),
            ("mlk_code", "=", self.koncod)])

    def doCatTyp(self, frt, pag, r, c, p, i, w):
        self.cattyp = w
        cnt = 0
        for cod in self.df.c_work[4]:
            if cod[1] == "B":
                cnt += 1
        if cnt > 1:
            return "Already a Type B Category Code"

    def doCatCod(self, frt, pag, r, c, p, i, w):
        self.catcod = w
        acc = self.sql.getRec("memctc", cols=["mcc_freq", "mcc_desc",
            "mcc_age_l", "mcc_and_s", "mcc_or_s"], where=[("mcc_cono", "=",
            self.opts["conum"]), ("mcc_type", "=", self.cattyp), ("mcc_code",
            "=", self.catcod)], limit=1)
        if not acc:
            return "Invalid Category Code"
        cnt = 0
        for cod in self.df.c_work[4]:
            if cod[1] == self.cattyp and cod[2] == self.catcod:
                cnt += 1
        if cnt > 1:
            return "Category Code Already Exists"
        if acc[2] and self.age > acc[2]:
            if acc[3] and self.years < acc[3]:
                pass
            else:
                return "Invalid Category, Over Age Limit"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.df.loadEntry(frt, pag, p+2, data=acc[1])

    def doCatNote(self, frt, pag, r, c, p, i, w):
        if self.new:
            self.df.loadEntry(frt, pag, p+1, data=self.sdate)

    def doCatStart(self, frt, pag, r, c, p, i, w):
        if w < self.opts["period"][1][0]:
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="MEM", code="FinPer")
            if cf == "no":
                return "Invalid Start Date, Before Start of Financial Period"

    def doLnkNo(self, frt, pag, r, c, p, i, w):
        if w == self.memno:
            return "Invalid, Cannot Link to Self"
        acc = self.sql.getRec("memmst", cols=["mlm_title",
            "mlm_surname", "mlm_names"], where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", w)], limit=1)
        if not acc:
            return "Invalid Membership Number"
        self.df.loadEntry(frt, pag, p+1, data=acc[0])
        self.df.loadEntry(frt, pag, p+2, data=acc[1])
        self.df.loadEntry(frt, pag, p+3, data=acc[2])

    def doChkSeq(self, pag, seq):
        if seq > 0 and not self.df.c_work[pag][seq-1][1]:
            return "Invalid Sequence"
        if not self.df.c_work[pag][seq][1]:
            self.newrow = "Y"
        else:
            self.newrow = "N"

    def doTopEnd(self):
        if not self.edit and not self.new:
            return
        if self.df.pag == 0:
            self.doSetNextSeq()
            self.df.selPage(self.df.tags[self.df.pag][0])
            if self.edit or self.new:
                self.df.focusField("T", 1, 1)
        elif self.df.pag == 1:
            self.df.selPage(self.df.tags[self.df.pag][0])
            self.df.focusField("T", 2, 1)
            for num in range(1, 5):
                self.df.enableTag(num)
        elif self.df.pag == 2:
            self.df.selPage(self.df.tags[self.df.pag][0])
            self.df.focusField("T", 3, 1)
        elif self.df.pag in (3, 4, 5):
            self.doAllTags(state="disabled")
            mx = self.df.colq[self.df.pag]
            seq = self.df.t_work[self.df.pag][0][0]
            self.df.loadEntry("C", self.df.pag, seq*mx, data=seq)
            self.df.focusField("C", self.df.pag, ((seq*mx)+1))

    def doTopExit(self):
        if not self.edit and not self.new:
            return
        if self.df.pag == 0:
            self.doExit()
        else:
            if self.df.pag == 1:
                pag = 5
            else:
                pag = self.df.pag - 1
            col = self.df.last[pag][0]
            if not col:
                col = 1
            else:
                for col in range(col, 1, -1):
                    if col in self.df.skip[pag]:
                        continue
                    if self.df.topf[pag][col-1][1][0] != "O":
                        break
            self.df.selPage(self.df.tags[pag-1][0])
            self.df.focusField("T", pag, col)

    def doColEnd(self):
        self.doAllTags(state="normal", exclude=(5, 6))
        self.doSetNextSeq()
        self.df.last[self.df.pag] = [0, 0]
        self.df.focusField("T", self.df.pag, 1)

    def doColExit(self):
        self.doAllTags(state="normal")
        if self.df.idx == 0:
            if self.newrow == "Y":
                self.df.clearLine(self.df.pag)
            self.df.last[self.df.pag] = [0, 0]
            self.df.focusField("T", self.df.pag, 1)

    def doAllTags(self, state="normal", exclude=()):
        for num, tag in enumerate(self.df.tags):
            if num in exclude:
                continue
            if state == "normal":
                self.df.enableTag(num)
            else:
                self.df.disableTag(num)

    def doSetNextSeq(self):
        for pag in range(3, 6):
            data = self.df.c_work[pag]
            for seq, dat in enumerate(data):
                if not dat[1]:
                    break
            self.df.loadEntry("T", pag, 0, data=seq)

    def doUpdate(self):
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        if self.new or self.edit:
            # Rollback all uncomitted transactions
            self.opts["mf"].dbm.rollbackDbase()
            if self.new:
                # Allocate New Member Number
                if self.mlint == "Y":
                    self.memno = self.getNextTab()
                else:
                    self.memno = getNextCode(self.sql, "memmst", "mlm_memno",
                        where=[("mlm_cono", "=", self.opts["conum"])],
                        start=1, last=999999)
                self.df.loadEntry("T", 0, 0, data=self.memno)
            # Check validity
            for pag in (("T", 0, None), ("T", 1, None)):
                frt, pag, pos, mes = self.df.doCheckFields(pag)
                if mes:
                    if pag > 0 and pag != self.df.pag:
                        if frt == "T":
                            self.df.last[pag][0] = pos+1
                        else:
                            self.df.last[pag][1] = pos+1
                        self.df.selPage(self.df.tags[pag - 1][0])
                    self.df.focusField(frt, pag, (pos+1), err=mes)
                    return
            if self.idnum and self.nation == "ZA" and \
                    self.dob % 1000000 != int(int(self.idnum) / 10000000):
                self.df.selPage("Personal")
                self.df.focusField("T", 1, 7, err="Invalid Identity Number")
                return
            cat = False
            seq = 0
            for fld in self.df.c_work[4]:
                if fld[1]:
                    seq += 1
                    if fld[1] in ("A", "B"):
                        cat = True
            if not cat and self.newsta == "A":
                showError(self.opts["mf"].body, "Missing Category",
                    "There Must be a Category Type B")
                self.df.selPage(self.df.tags[3][0])
                self.df.loadEntry("T", 4, 0, data=seq)
                self.df.focusField("T", 4, 1)
                return
            # memmst table
            memmst = [self.opts["conum"]]
            for fld in self.df.t_work[0][0]:
                memmst.append(fld)
            for num, fld in enumerate(self.df.t_work[1][0]):
                if num in (3, 5, 8, 10, 12, 14, 19, 20, 21):
                    continue
                memmst.append(fld)
            if self.new:
                self.sql.insRec("memmst", data=memmst)
            elif memmst != self.memmst[:len(memmst)]:
                col = self.sql.memmst_col
                memmst.append(self.memmst[col.index("mlm_xflag")])
                self.sql.updRec("memmst", data=memmst, where=[("mlm_cono",
                    "=", self.opts["conum"]), ("mlm_memno", "=", self.memno)])
                for num, dat in enumerate(self.memmst):
                    if dat != memmst[num]:
                        self.sql.insRec("chglog", data=["memmst", "U",
                            "%03i%06i" % (self.opts["conum"], self.memno),
                            col[num], dte, self.opts["capnm"], str(dat),
                            str(memmst[num]), "", 0])
            # memcto table
            if self.newocc:
                self.sql.insRec("memcto", data=[self.occup, self.newocc])
            # memsta table
            if self.new or self.oldsta != self.newsta:
                memsta = [self.opts["conum"], self.memno, self.newsta,
                    self.sdate, self.opts["capnm"], self.sysdt, 0]
                self.sql.insRec("memsta", data=memsta)
            # memadd table
            self.sql.delRec("memadd", where=[("mla_cono", "=",
                self.opts["conum"]), ("mla_memno", "=", self.memno)])
            for typ in ("P", "R"):
                data = [self.opts["conum"], self.memno, typ]
                if typ == "P":
                    idx = 0
                else:
                    idx = 8
                for x in range(idx, idx + 7):
                    data.append(self.df.t_work[2][0][x])
                self.sql.insRec("memadd", data=data)
                if typ == "P" and self.df.t_work[2][0][7] == "Y":
                    break
            # memkon table
            self.sql.delRec("memkon", where=[("mlk_cono", "=",
                self.opts["conum"]), ("mlk_memno", "=", self.memno)])
            for dat in self.df.c_work[3]:
                if not dat[1]:
                    break
                data = [self.opts["conum"], self.memno, dat[1], dat[3]]
                self.sql.insRec("memkon", data=data)
            # memcat table
            self.sql.delRec("memcat", where=[("mlc_cono", "=",
                self.opts["conum"]), ("mlc_memno", "=", self.memno)])
            for dat in self.df.c_work[4]:
                if not dat[1]:
                    break
                new = [self.opts["conum"], self.memno, dat[1], dat[2],
                    dat[5], dat[6], dat[7], 0]
                for old in self.memcat:
                    if old[:4] == new[:4]:
                        new[7] = old[7]
                        break
                self.sql.insRec("memcat", data=new)
            memcat = self.sql.getRec("memcat", where=[("mlc_cono", "=",
                self.opts["conum"]), ("mlc_memno", "=", self.memno)],
                order="mlc_type, mlc_code")
            if memcat != self.memcat:
                newcat = copyList(memcat)
                oldcat = copyList(self.memcat)
                for new in newcat:
                    ncono, nmemno, ntype, ncode, x, nstart, nend, y, z = new
                    for old in oldcat:
                        ocono, omemno, otype, ocode, x, ostart, oend, y, z = old
                        if old[:4] == new[:4]:
                            if ostart != nstart:
                                self.sql.insRec("chglog", data=["memcat",
                                    "U", "%03i%06i%1s%02i" % (ocono, omemno,
                                    otype, ocode), "mlc_start", dte,
                                    self.opts["capnm"], str(ostart),
                                    str(nstart), "", 0])
                            if oend != nend:
                                self.sql.insRec("chglog", data=["memcat",
                                    "U", "%03i%06i%1s%02i" % (ocono, omemno,
                                    otype, ocode), "mlc_end", dte,
                                    self.opts["capnm"], str(oend),
                                    str(nend), "", 0])
                            oldcat.remove(old)
                            memcat.remove(new)
                            break
                for cono, memno, ctype, code, note, start, end, x, y in oldcat:
                    self.sql.insRec("chglog", data=["memcat", "D",
                        "%03i%06i%1s%02i" % (cono, memno, ctype, code), "",
                        dte, self.opts["capnm"], str(start), str(end), "", 0])
                for cono, memno, ctype, code, note, start, end, x, y in memcat:
                    self.sql.insRec("chglog", data=["memcat", "N",
                        "%03i%06i%1s%02i" % (cono, memno, ctype, code), "",
                        dte, self.opts["capnm"], str(start), str(end), "", 0])
            # memlnk table
            self.sql.delRec("memlnk", where=[("mll_cono", "=",
                self.opts["conum"]), ("mll_memno", "=", self.memno)])
            if self.newsta == "A":
                for dat in self.df.c_work[5]:
                    if not dat[1]:
                        break
                    data = [self.opts["conum"], self.memno, dat[1]]
                    self.sql.insRec("memlnk", data=data)
            # Bowls Tables
            if self.mlint == "Y":
                whr = [("btb_cono", "=", self.opts["conum"])]
                if self.samen == "Y":
                    whr.append(("btb_tab", "=", self.memno))
                else:
                    whr.append(("btb_memno", "=", self.memno))
                tab = self.sql.getRec("bwltab", where=whr, limit=1)
                if not tab:
                    if self.samen == "Y":
                        newtab = True
                        tab = [self.opts["conum"], self.memno, self.memno,
                            "","","","","","","","","","","",1,0,1,0,0]
                    else:
                        newtab = None
                        showWarning(self.opts["mf"].body, "Bowls Tab",
                            "A Bowls Tab for this Member Does Not Exist.")
                elif not tab[2]:
                    newtab = None
                    showWarning(self.opts["mf"].body, "Bowls Tab",
                        "A Bowls Tab for this Member Does Not Exist.")
                else:
                    newtab = False
                if newtab is not None:
                    tab[3] = self.df.t_work[0][0][3]
                    tab[4] = self.df.t_work[1][0][0]
                    tab[5] = self.df.t_work[1][0][1]
                    for typ in ("A", "P"):
                        ad = self.sql.getRec("memadd", cols=["mla_add1",
                            "mla_add2", "mla_add3", "mla_code"],
                            where=[("mla_cono", "=", self.opts["conum"]),
                            ("mla_memno", "=", self.memno), ("mla_type",
                            "=", typ)], limit=1)
                        if ad:
                            break
                    if ad:
                        tab[6] = ad[0]
                        tab[7] = ad[1]
                        tab[8] = ad[2]
                        tab[9] = ad[3]
                    for num, cod in enumerate((1, 2, 3, 5)):
                        kk = self.sql.getRec("memkon",
                            cols=["mlk_detail"],
                            where=[("mlk_cono", "=", self.opts["conum"]),
                            ("mlk_memno", "=", self.memno), ("mlk_code",
                            "=", cod)], limit=1)
                        if kk:
                            tab[num + 10] = kk[0]
                    if newtab:
                        self.sql.insRec("bwltab", data=tab)
                    else:
                        self.sql.updRec("bwltab", data=tab,
                            where=[("btb_cono", "=", self.opts["conum"]),
                            ("btb_memno", "=", self.memno)])
            self.opts["mf"].dbm.commitDbase()
            # Flags
            self.new = False
            self.edit = False
        self.df.selPage(self.df.tags[0][0])
        self.df.focusField("T", 0, 1)
        self.df.loadEntry("T", 0, 0, data=self.memno)
        self.doMemNo("T", 0, 0, 1, 0, 0, self.memno)

    def getNextTab(self):
        cats = []
        for dat in self.df.c_work[4]:
            if not dat[1]:
                break
            cats.append(dat[1:3])
        if ["C", self.mscat] in cats:
            if self.gender == "M":
                start = self.mstart
                if self.mstart < self.fstart:
                    last = self.fstart
                else:
                    last = self.nstart
            else:
                start = self.fstart
                if self.mstart < self.fstart:
                    last = self.nstart
                else:
                    last = self.mstart
        else:
            start = self.nstart
            last = 900000
        return getNextCode(self.sql, "bwltab", "btb_tab",
            where=[("btb_cono", "=", self.opts["conum"])],
            start=start, last=last)


    def doTrans1(self):
        self.df.focusField("T", 6, 1)

    def doTrans2(self, frt, pag, r, c, p, i, w):
        self.select = w
        if self.select == "U":    # Status History
            self.doStatusHistory()
            return
        # Transactions
        whr = [("mlt_cono", "=", self.opts["conum"]),
            ("mlt_memno", "=", self.memno)]
        odr = "mlt_trdt"
        col, recs = getTrn(self.opts["mf"].dbm, "mem", whr=whr, odr=odr)
        if recs:
            data = []
            for dat in recs:
                data.append([
                    dat[col.index("mlt_trdt")],
                    dat[col.index("mlt_curdt")],
                    dat[col.index("mlt_batch")],
                    dat[col.index("mlt_type")],
                    dat[col.index("mlt_refno")],
                    dat[col.index("mlt_tramt")],
                    dat[col.index("paid")],
                    dat[col.index("balance")],
                    dat[col.index("mlt_ctyp")],
                    dat[col.index("mlt_ccod")],
                    dat[col.index("mlt_desc")]])
            tit = "Transactions for Account: %s - %s %s %s" % (self.memno,
                self.title, self.initial, self.surname)
            col = (
                ("mlt_trdt", "   Date", 10, "D1", "N"),
                ("mlt_curdt", "Curr-Dt", 7, "D2", "N"),
                ("mlt_batch", "Batch", 7, "Na", "N"),
                ("mlt_type", "Typ", 3, ("XX", mltrtp), "N"),
                ("mlt_refno", "Reference", 9, "Na", "Y"),
                ("mlt_tramt", "    Amount", 13.2, "SD", "N"),
                ("alloc", "      Paid", 13.2, "SD", "N"),
                ("balan", "   Balance", 13.2, "SD", "N"),
                ("mlt_ctyp", "T", 1, "UA", "N"),
                ("mlt_ccod", "Cd", 2, "UI", "N"),
                ("mlt_desc", "Details", 30, "NA", "N"))
            state = self.df.disableButtonsTags()
            while True:
                rec = SelectChoice(self.df.nb.Page6, tit, col, data,
                    sort=False)
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    whr = [
                        ("mlt_cono", "=", self.opts["conum"]),
                        ("mlt_memno", "=", self.memno),
                        ("mlt_type", "=", rec.selection[4]),
                        ("mlt_refno", "=", rec.selection[5])]
                    TabPrt(self.opts["mf"], tabs="memtrn", where=whr,
                        pdia=False)
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doStatusHistory(self):
        recs = self.sql.getRec("memsta", cols=["mls_capdt", "mls_date",
            "mls_status", "mls_capnm", "mls_capdt"], where=[("mls_cono", "=",
            self.opts["conum"]), ("mls_memno", "=", self.memno)],
            order="mls_seq")
        if not recs:
            return
        data = []
        for dat in recs:
            if not dat[0]:
                dat[0] = dat[1]
            if dat[2] == "A":
                stat = "Active"
            elif dat[2] == "D":
                stat = "Deceased"
            elif dat[2] == "X":
                stat = "Defaulted"
            elif dat[2] == "I":
                stat = "Inactive"
            elif dat[2] == "R":
                stat = "Resigned"
            elif dat[2] == "S":
                stat = "Suspended"
            capdt = CCD(dat[4], "d1", 10).disp
            data.append([dat[0], dat[1], stat, dat[3], capdt])
        tit = "Status History for Account: %s - %s %s %s" % \
            (self.memno, self.title, self.initial, self.surname)
        col = (
            ("mls_capdt", "Cap-Date", 10, "d1", "N"),
            ("mls_date", "Eff-Date", 10, "d1", "N"),
            ("mls_status", "Status", 9, "NA", "N"),
            ("mls_capnm", "Operator", 20, "NA", "N"),
            ("mls_capdt", "Chnge-Date", 10, "NA", "N"))
        state = self.df.disableButtonsTags()
        SelectChoice(self.df.nb.Page6, tit, col, data, sort=False)
        self.df.enableButtonsTags(state=state)
        self.doTrans1()

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "MEM", self.memno)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doPhoto(self):
        if self.image:
            return
        for ext in ("jpg", "JPG"):
            jpg = os.path.join(self.photo, "%s.%s" % (self.memno, ext))
            if os.path.isfile(jpg):
                break
            jpg = None
        if jpg:
            self.image = ShowImage(self.df.nb.Page7, jpg,
                wrkdir=self.opts["mf"].rcdic["wrkdir"],
                msiz=int(self.opts["mf"].body.winfo_height()*.75))

    def doPrint(self):
        mess = "Select the Required Print Option."
        butt = (
            ("Information", "I"),
            ("Transactions", "T"),
            ("Statement", "S"),
            ("Member Card", "C"),
            ("None", "N"))
        self.doPrintOption(askChoice(self.opts["mf"].body, "Print Options",
            mess, butt=butt))
        if self.new or self.edit:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrintOption(self, opt):
        if opt == "N":
            return
        self.opt = opt
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if opt == "I":
            table = "memmst"
            whr = [("mlm_cono", "=", self.opts["conum"]),
                ("mlm_memno", "=", self.memno)]
            TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
                name=self.__class__.__name__, tabs=table, where=whr,
                keys=[self.memno])
        elif opt == "T":
            name = "%s %s %s" % (self.title, self.initial, self.surname)
            heads = ["Member's Transactions",
                "Member: %s  Name: %s" % (self.memno, name)]
            whr = [("mlt_cono", "=", self.opts["conum"]),
                ("mlt_memno", "=", self.memno)]
            col, recs = getTrn(self.opts["mf"].dbm, "mem", whr=whr)
            cols = []
            data = []
            dic = self.sql.memtrn_dic
            for num, rec in enumerate(recs):
                dat = []
                for nam in ["mlt_refno", "mlt_trdt", "mlt_type",
                        "mlt_tramt", "paid", "balance", "mlt_desc"]:
                    if not num:
                        if nam == "paid":
                            cols.append(["paid", "SD", 13.2, "Paid"])
                        elif nam == "balance":
                            cols.append(["balance", "SD", 13.2, "Balance"])
                        else:
                            cols.append([nam, dic[nam][2], dic[nam][3],
                                dic[nam][5]])
                    dat.append(rec[col.index(nam)])
                data.append(dat)
            gtots = ["mlt_tramt", "paid", "balance"]
            prtdia = (("Y","V"),("Y","N"))
            RepPrt(self.opts["mf"], conum=self.opts["conum"],
                conam=self.opts["conam"], name=self.__class__.__name__,
                ttype="D", tables=data, heads=heads, cols=cols,
                trtp=["mlt_type", mltrtp], gtots=gtots, prtdia=prtdia,
                fromad=self.fromad)
        elif opt == "S":
            tit = ("Print Options",)
            fld = []
            self.pf = TartanDialog(self.opts["mf"], tops=True, title=tit,
                eflds=fld, tend=((self.doPrtEnd,"N"),), view=("N","V"),
                mail=("N","Y"))
            self.pf.mstFrame.wait_window()
            data = self.sql.getRec("memmst", where=[("mlm_cono",
                "=", self.opts["conum"]), ("mlm_memno", "=", self.memno)],
                limit=1)
            if self.ynd:
                date = self.nxtdt
            else:
                date = self.tme
            callModule(self.opts["mf"], None, "ml3040",
                coy=(self.opts["conum"], self.opts["conam"]),
                args=(data, date, self.pf.repprt, self.pf.repeml))
        else:
            cf = PwdConfirm(self.opts["mf"], conum=self.opts["conum"],
                system="MEM", code="MemCards")
            if cf.flag == "ok":
                self.doPrintCard()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doPrintCard(self):
        tit = ("Print Options",)
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title", "Y")),
            "where": [
                ("tpm_type", "=", "M"),
                ("tpm_system", "=", "MEM")],
            "order": "tpm_tname"}
        fld = (
            (("T",0,0,0),"INA",20,"Template Name - Front","",
                self.cftpl,"Y",self.doPrtTpl,tpm,None,("notblank",)),
            (("T",0,1,0),"INA",20,"Template Name - Back","",
                self.cbtpl,"Y",self.doPrtTpl,tpm,None,None))
        self.pf = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doPrtEnd,"N"),), view=("N","V"))
        self.pf.mstFrame.wait_window()
        self.df.nb.select(0)

    def doPrtTpl(self, frt, pag, r, c, p, i, w):
        if w and not self.sql.getRec("tplmst", where=[("tpm_tname", "=",
                w), ("tpm_type", "=", "M"), ("tpm_system", "=", "MEM")],
                limit=1):
            return "Invalid Template Name"
        if not p:
            self.tnamef = w
        elif w and w == self.tnamef:
            return "Back Template Same as Front Template"
        else:
            self.tnameb = w

    def doPrtEnd(self):
        self.pf.closeProcess()
        if self.opt == "S":
            return
        form = DrawForm(self.opts["mf"].dbm, self.tnamef, foot=False,
            wrkdir=self.opts["mf"].rcdic["wrkdir"])
        if self.logo and "club_logo" in form.tptp:
            form.tptp["club_logo"][1] = self.logo
        form.tptp["mlm_memno"][1] = self.memno
        snam = self.df.t_work[0][0][3].title()
        init = self.df.t_work[1][0][0].split()[0][0].upper()
        form.tptp["name_init"][1] = "%s %s" % (init, snam)
        for ext in ("jpg", "JPG"):
            jpg = os.path.join(self.photo,"%s.%s" % (self.memno,ext))
            if os.path.isfile(jpg):
                break
            jpg = None
        if jpg:
            if self.image:
                self.image.destroyImage()
                self.image = None
            self.opts["mf"].updateStatus("Select the Area to Crop with "\
                "Left Button. Use the Right Button to Clear the Area.")
            self.df.nb.select(6)
            self.df.setWidget(self.df.mstFrame, state="show")
            img = ShowImage(self.df.nb.Page7, jpg,
                wrkdir=self.opts["mf"].rcdic["wrkdir"],
                msiz=int(self.opts["mf"].body.winfo_height()*.75), crop=True)
            tmp = os.path.join(self.opts["mf"].rcdic["wrkdir"], "temp.jpg")
            siz = img.roi.size
            img.roi.save(tmp)
            form.tptp["member_photo"][1] = tmp
            self.opts["mf"].updateStatus("")
            img.destroyImage()
        for fld in self.df.c_work[4]:
            if fld[1] and fld[1] == "B":
                form.tptp["main_category"][1] = fld[4]
        form.doNewDetail()
        form.add_page()
        tdc = form.sql.tpldet_col
        for key in form.newkey:
            l = form.newdic[key]
            if l[tdc.index("tpd_detseq")] == "member_photo" and jpg:
                x1, x2 = l[tdc.index("tpd_x1")], l[tdc.index("tpd_x2")]
                y1, y2 = l[tdc.index("tpd_y1")], l[tdc.index("tpd_y2")]
                w1 = x2 - x1
                h1 = y2 - y1
                if siz[0] <= siz[1]:
                    w2 = (y2 - y1) * (siz[0] * 1.0 / siz[1])
                    if w2 <= w1:
                        l[tdc.index("tpd_x2")] = l[tdc.index("tpd_x1")] + w2
                else:
                    h2 = (x2 - x1) * (siz[1] * 1.0 / siz[0])
                    if h2 <= h1:
                        l[tdc.index("tpd_y1")] = l[tdc.index("tpd_y2")] - h2
            form.doDrawDetail(l)
        pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
            self.__class__.__name__, self.tnamef, ext="pdf")
        if form.saveFile(pdfnam, self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], pdfnam=pdfnam, splash=False,
                repprt=self.pf.repprt)
        if self.tnameb:
            doprint = False
            form = DrawForm(self.opts["mf"].dbm, self.tnameb,
                wrkdir=self.opts["mf"].rcdic["wrkdir"])
            if "debenture" in form.tptp:
                # Debentures
                debs = []
                for line in self.df.c_work[4]:
                    if not line[1]:
                        break
                    if line[1] == "D" and line[5].strip() and not line[7]:
                        debs = [line[4], line[5].strip()]
                        break
                if debs:
                    deb = debs[1].replace(" ", "")
                    deb = deb.replace("&", ",")
                    deb = deb.replace(":", ",")
                    deb = deb.replace(";", ",")
                    deb = deb.replace(".", ",")
                    if deb[-1] == ",":
                        deb = deb[:-1]
                    count = deb.count(",")
                    deb = deb.replace(",", " & ")
                    deb = deb.replace(" & ", ", ", count - 1)
                    form.tptp["debenture"][1] = deb
                    doprint = True
                else:
                    del form.tptp["debenture"]
            if "oaks_club" in form.tptp:
                oaks = None
                for line in self.df.c_work[4]:
                    if not line[1]:
                        break
                    if line[1] == "C" and line[2] == 8 and not line[7]:
                        try:
                            oaks = int(line[5].strip())
                        except:
                            pass
                        break
                if oaks:
                    form.tptp["oaks_club"][1] = oaks
                    doprint = True
                else:
                    del form.tptp["oaks_club"]
            if doprint:
                form.doNewDetail()
                form.add_page()
                for key in form.newkey:
                    l = form.newdic[key]
                    form.doDrawDetail(l)
                pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                    self.__class__.__name__, self.tnameb, ext="pdf")
                if form.saveFile(pdfnam, self.opts["mf"].body):
                    showWarning(self.opts["mf"].body, "Replace Card",
                        "In Order to Print the Back of the Card, Please "\
                        "Replace the Card, Reverse Side Up, in the "\
                        "Printer Tray.")
                    doPrinter(mf=self.opts["mf"], pdfnam=pdfnam, splash=False,
                        repprt=self.pf.repprt)

    def doClear(self):
        if self.new or self.edit:
            ok = askQuestion(self.opts["mf"].body, "Editing",
                "Are You Sure You Want to Exit?\n\nYou are busy "\
                "Editing this Record!", default="no")
            if ok == "no":
                return
        # Rollback Everything Not Committed
        self.opts["mf"].dbm.rollbackDbase()
        # Flags
        self.new = False
        self.edit = False
        if self.image:
            # Clear Photo
            self.image.destroyImage()
            self.image = None
        self.df.selPage(self.df.tags[0][0])
        self.doSetButtons((), (1, 2, 3, 4, 5))
        self.df.focusField("T", 0, 1)

    def doSetButtons(self, normal, disabled):
        for but in normal:
            wid = getattr(self.df, "B%s" % but)
            self.df.setWidget(wid, state="normal")
        for but in disabled:
            wid = getattr(self.df, "B%s" % but)
            self.df.setWidget(wid, state="disabled")

    def doExit(self):
        if self.new or self.edit:
            ok = askQuestion(self.opts["mf"].body, "Editing",
                "Are You Sure? You are busy Editing this Record!",
                default="no")
            if ok == "no":
                return
        # Rollback Everything Not Committed
        try:
            self.opts["mf"].dbm.rollbackDbase()
        except:
            pass
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
