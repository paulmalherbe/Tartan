"""
SYNOPSIS
    Bulk Mailing Utility.

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

import glob, imghdr, os, pathlib, time
try:
    import requests
    REQ = True
except:
    REQ = False
try:
    from markdown import markdown
    MARKDOWN = True
except:
    MARKDOWN = False
try:
    import pymupdf
    FITZ = True
except:
    FITZ = False

from TartanClasses import FileImport, GetCtl, Image, ShowEmail, SplashScreen
from TartanClasses import Sql, TartanDialog
from tartanFunctions import askQuestion, getSingleRecords, sendMail, showError

class bm1010(object):
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
        if REQ:
            self.sms = []
            for fld in ("ssvr", "snam", "spwd"):
                self.sms.append(ctlsys["sys_%s" % fld])
        else:
            self.sms = ["N"]
        if not self.smtp[0] and self.sms[0] == "N":
            showError(self.opts["mf"].body, "SMTP/SMS Error",
                "There is NO SMTP Server nor SMS Service Available.")
            return
        # Get Company Details
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.fadd = ctlmst["ctm_email"]
        self.urll = ctlmst["ctm_weburl"]
        if self.smtp and not self.fadd:
            showError(self.opts["mf"].body, "From Error",
                "There is NO Email Address on the Company Record!")
            return
        tab = ["emllog"]
        mod = []
        for x in range(0, len(ctlmst["ctm_modules"].rstrip()), 2):
            mod.append(ctlmst["ctm_modules"][x:x+2])
        if "BC" in mod:
            bwlctl = gc.getCtl("bwlctl", self.opts["conum"], error=False)
            if not bwlctl:
                mod.remove("BC")
            else:
                tab.append(("bwltab"))
                self.nstart = bwlctl["ctb_nstart"]
        if "BK" in mod:
            tab.append("bkmcon")
        if "BS" in mod:
            tab.append("bksown")
        if "CR" in mod:
            tab.append("crsmst")
        if "DR" in mod:
            tab.extend(["drsact", "drstyp", "drsmst"])
        if "ML" in mod:
            tab.extend(["memctc", "memmst", "memcat", "memkon"])
        if "LN" in mod:
            tab.append("lonmf1")
        if "RC" in mod:
            tab.extend(["rcaowm", "rcatnm"])
        if "RT" in mod:
            tab.append("rtlmst")
        if "SC" in mod:
            tab.append("scpmem")
        if "WG" in mod:
            tab.append("wagmst")
        tab.append("telmst")
        self.sql = Sql(self.opts["mf"].dbm, tables=tab,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        if "BC" in mod:
            self.tab = self.sql.getRec("bwltab", cols=["count(*)"],
                where=[("btb_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.tab = [0]
        if "BK" in mod:
            self.bkm = self.sql.getRec("bkmcon", cols=["count(*)"],
                where=[("bkc_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.bkm = [0]
        if "BS" in mod:
            self.bks = self.sql.getRec("bksown", cols=["count(*)"],
                limit=1)
        else:
            self.bks = [0]
        if "CR" in mod:
            self.crs = self.sql.getRec("crsmst", cols=["count(*)"],
                where=[("crm_cono", "=", self.opts["conum"]),
                ("crm_stat", "<>", "X")], limit=1)
        else:
            self.crs = [0]
        if "DR" in mod:
            self.drs = self.sql.getRec("drsmst", cols=["count(*)"],
                where=[("drm_cono", "=", self.opts["conum"]),
                ("drm_stat", "<>", "X")], limit=1)
        else:
            self.drs = [0]
        if "ML" in mod:
            self.mem = self.sql.getRec("memmst", cols=["count(*)"],
                where=[("mlm_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.mem = [0]
        if "LN" in mod:
            self.lon = self.sql.getRec("lonmf1", cols=["count(*)"],
                where=[("lm1_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.lon = [0]
        if "RC" in mod:
            self.own = self.sql.getRec("rcaowm", cols=["count(*)"],
                where=[("rom_cono", "=", self.opts["conum"])], limit=1)
            self.tnt = self.sql.getRec("rcatnm", cols=["count(*)"],
                where=[("rtn_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.own = [0]
            self.tnt = [0]
        if "RT" in mod:
            self.rtl = self.sql.getRec("rtlmst", cols=["count(*)"],
                where=[("rtm_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.rtl = [0]
        if "SC" in mod:
            self.scp = self.sql.getRec("scpmem", cols=["count(*)"],
                where=[("scm_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.scp = [0]
        if "WG" in mod:
            self.wag = self.sql.getRec("wagmst", cols=["count(*)"],
                where=[("wgm_cono", "=", self.opts["conum"])], limit=1)
        else:
            self.wag = [0]
        self.tel = self.sql.getRec("telmst", cols=["count(*)"], limit=1)
        self.mess = ""
        self.embed = []
        self.attach = []
        self.personal = "N"
        self.namdet = "N"
        return True

    def mainProcess(self):
        if not self.smtp[0]:
            self.dtyp = "S"
            r1s = (("SMS", "S"),)
        elif self.sms[0] == "N":
            self.dtyp = "E"
            r1s = (("E-Mail", "E"),)
        else:
            self.dtyp = ""
            r1s = (("E-Mail", "E"), ("SMS", "S"))
        self.fle = {
            "stype": "F",
            "types": "fle",
            "multi": True}
        self.r2s = []
        tip = ""
        if self.bkm[0]:
            self.r2s.append(("Bkm", "K"))
            tip = "%s%s" % (tip, "Bkm - Bookings Manager\n")
        if self.bks[0]:
            self.r2s.append(("Bks", "S"))
            tip = "%s%s" % (tip, "Bks - Book Club\n")
        if self.tab[0] or self.scp[0]:
            self.r2s.append(("Bwl", "B"))
            tip = "%s%s" % (tip, "Bwl - Bowls Club\n")
        if self.crs[0]:
            self.r2s.append(("Crs", "C"))
            tip = "%s%s" % (tip, "Crs - Creditors Ledger\n")
        if self.drs[0]:
            self.r2s.append(("Drs", "D"))
            tip = "%s%s" % (tip, "Drs - Debtors Ledger\n")
        if self.mem[0]:
            self.r2s.append(("Mem", "M"))
            tip = "%s%s" % (tip, "Mem - Members Ledger\n")
        if self.lon[0]:
            self.r2s.append(("Lon", "L"))
            tip = "%s%s" % (tip, "Lon - Loans Ledger\n")
        if self.own[0]:
            self.r2s.append(("Own", "O"))
            tip = "%s%s" % (tip, "Own - Collection Owners\n")
        if self.tnt[0]:
            self.r2s.append(("Tnt", "H"))
            tip = "%s%s" % (tip, "Tnt - Collection Tenants\n")
        if self.rtl[0]:
            self.r2s.append(("Rtl", "R"))
            tip = "%s%s" % (tip, "Rtl - Rentals Ledger\n")
        if self.scp[0]:
            self.r2s.append(("Scp", "P"))
            tip = "%s%s" % (tip, "Scp - District Members\n")
        if self.wag[0]:
            self.r2s.append(("Wag", "W"))
            tip = "%s%s" % (tip, "Wag - Employees\n")
        if self.tel[0]:
            self.r2s.append(("Tel", "T"))
            tip = "%s%s" % (tip, "Tel - Directory\n")
        self.r2s.append(("Import File", "X"))
        r3s = (("Yes", "Y"), ("No", "N"))
        if self.dtyp:
            fld = [(("T",0,0,0),("ORB",r1s),0,"Delivery Type")]
        else:
            fld = [(("T",0,0,0),("IRB",r1s),0,"Delivery Type","",
                "E","Y",self.doType,None,None,None)]
        fld.extend([
            (("T",0,1,0),("IRB",self.r2s),0,"List to Use","",
                self.r2s[0][1],"Y",self.doList,None,None,None,None,tip),
            (("T",0,2,0),("IRB",r3s),0,"Skip Delivery Errors","",
                "Y","N",self.doSkip,None,None,None),
            (("T",0,3,0),"INA",(75,100),"Subject","",
                "","N",self.doSubject,None,None,("notblank",)),
            (("T",0,4,0),"IFF",75,"In-line Attachment","",
                "","N",self.doEmbed,self.fle,None,("fle","blank")),
            (("T",0,5,0),("IRB",r3s),0,"Add Hyperlink","",
                "N","N",self.doLink,None,None,None),
            (("T",0,6,0),("IRB",r3s),0,"Add Link Text","",
                "Y","N",self.doText,None,None,None),
            (("T",0,7,0),"ITX",75,"Link URL","",
                "","N",self.doSite,None,None,("efld",),None,"Link URL."),
            (("T",0,8,0),"IFF",75,"Separate Attachment","",
                "","N",self.doAttach,self.fle,None,("fle","blank")),
            (("T",0,9,0),"ITV",(75,25),"Message","",
                "","N",self.doMessage,None,None,None,None,
                """If you selected Personalize then:

To include the recipient's name in the message use one of the following methods:

{{name}}     - Use this method if the recipient has a separete surname and name field
{{surname}}  - Use this method if the recipient has a combined surname, name field

Dear {{name}} or {{surname}} could then become

Dear John Smith ...""")])
        tnd = ((self.doEnd, "y"), )
        txt = (self.doExit, )
        but = (
            ("Preview",None,self.doPreview,0,("T",0,10),
                (("T",0,0),("T",0,2),("T",0,9))),
            ("Send",None,self.doExecute,0,("T",0,10),
                (("T",0,0),("T",0,2),("T",0,9))),
            ("Quit",None,self.doExit,1,None,None))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd, txit=txt,
            butt=but)
        if self.dtyp:
            self.df.loadEntry("T", 0, 0, data=self.dtyp)

    def doType(self, frt, pag, r, c, p, i, w):
        self.dtyp = w

    def doList(self, frt, pag, r, c, p, i, w):
        if self.dtyp == "S" and w in ("C", "D"):
            return "rf"
        self.ulist = w
        self.personal = "Y"
        if self.ulist == "X":
            self.impxit = False
            self.doImport()
            if self.impxit:
                return "rf"
        else:
            self.doFilter()
            if self.fltexit:
                return "rf"
            if self.dtyp == "S":
                return "sk4"

    def doFilter(self):
        tit = "Bulk Mail Filter"
        if self.ulist == "B":
            # Bowls Club
            r1s = (("All", "A"),("Members","B"),("Guests","G"))
            r2s = (("All", "A"),("Male","M"),("Female","F"))
            r3s = (("Yes", "Y"), ("No", "N"))
            fld = (
                (("T",0,0,0),("IRB",r1s),0,"Category","",
                    "A","Y",self.doFltCat,None,None,None),
                (("T",0,1,0),("IRB",r2s),0,"Gender","",
                    "A","Y",self.doFltGen,None,None,None),
                (("T",0,2,0),("IRB",r3s),0,"Individuals","",
                    "Y","Y",self.doFltInd,None,None,None))
        elif self.ulist in ("C", "D"):
            # Creditors or Debtors
            r1s = (("Manager","M"),("Accounts","A"),("Sales","S"))
            r2s = (("Yes", "Y"),("No","N"))
            fld = [
                (("T",0,0,0),("IRB",r1s),0,"Email To","",
                    "S","N",self.doFltTo,None,None,None)]
            if self.ulist == "D":
                daa = self.sql.getRec("drsmst",
                    cols=["drm_bus_activity", "count(*)"],
                    where=[("drm_cono", "=", self.opts["conum"]),
                    ("drm_stat", "<>", "X")], group="drm_bus_activity",
                    order="drm_bus_activity")
                act = {
                    "stype": "C",
                    "titl": "Valid Activities",
                    "head": ("Act", "Quantity"),
                    "data": daa,
                    "typs": (("NA", 3), ("UI", 8)),
                    "size": (400, 400)}
                dab = self.sql.getRec("drsmst", cols=["drm_bus_type",
                    "count(*)"], where=[("drm_cono", "=", self.opts["conum"]),
                    ("drm_stat", "<>", "X")], group="drm_bus_type",
                    order="drm_bus_type")
                typ = {
                    "stype": "C",
                    "titl": "Valid Types",
                    "head": ("Typ", "Quantity"),
                    "data": dab,
                    "typs": (("NA", 3), ("UI", 8)),
                    "size": (400, 400)}
                fld.append((("T",0,1,0),"INA",3,"Activity","Account Activity",
                    "","N",self.doFltAct,act,None,None))
                fld.append((("T",0,1,0),"ONA",30,""))
                fld.append((("T",0,2,0),"INA",3,"Type","Account Type",
                    "","N",self.doFltTyp,typ,None,None))
                fld.append((("T",0,2,0),"ONA",30,""))
                fld.append((("T",0,3,0),("IRB",r2s),0,"Include Stopped","",
                    "N","N",self.doFltStp,None,None,None))
                idx = 4
            else:
                idx = 1
            fld.append((("T",0,idx,0),("IRB",r2s),0,"Individuals","",
                "Y","Y",self.doFltInd,None,None,None))
        elif self.ulist in ("K", "L", "O", "H", "P", "R", "S", "W"):
            # All the Rest
            r1s = (("Yes", "Y"),("No","N"))
            fld = (
                (("T",0,0,0),("IRB",r1s),0,"Individuals","",
                    "Y","Y",self.doFltInd,None,None,None),)
        elif self.ulist == "M":
            # Members
            r1s = (("All", "A"),("Main","B"),("Sports","C"),("Debentures","D"))
            r2s = (("All", "A"),("Male","M"),("Female","F"))
            r3s = (("Yes", "Y"), ("No", "N"))
            r4s = (("First Name", "N"), ("First Initial", "I"))
            fld = (
                (("T",0,0,0),("IRB",r1s),0,"Category","",
                    "A","Y",self.doFltCat,None,None,None),
                (("T",0,1,0),("IRB",r2s),0,"Gender","",
                    "A","Y",self.doFltGen,None,None,None),
                (("T",0,2,0),("IRB",r3s),0,"Personalize","",
                    "N","N",self.doFltPP,None,None,None),
                (("T",0,3,0),("IRB",r4s),0,"Name Detail","",
                    "I","N",self.doFltND,None,None,None),
                (("T",0,4,0),("IRB",r3s),0,"Individuals","",
                    "Y","Y",self.doFltInd,None,None,None),)
        elif self.ulist == "T":
            # Telephone Directory
            r1s = (("All", "A"),("Group","G"))
            r2s = (("Yes", "Y"),("No","N"))
            fld = (
                (("T",0,0,0),("IRB",r1s),0,"Group Selection","",
                    "A","Y",self.doFltGrp,None,None,None),
                (("T",0,1,0),("IRB",r2s),0,"Include Contacts","",
                    "N","Y",self.doFltCon,None,None,None),
                (("T",0,2,0),("IRB",r2s),0,"Individuals","",
                    "Y","Y",self.doFltInd,None,None,None))
        else:
            # CSV or XLS File
            return
        state = self.df.disableButtonsTags()
        self.ff = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doFltEnd,"n"),), txit=(self.doFltExit,))
        self.ff.mstFrame.wait_window()
        self.df.enableButtonsTags(state=state)

    def doFltCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.fltcat = ""
            self.fltcod = []
            return
        self.fltcat = w
        if self.ulist == "B":
            return
        chk = self.sql.getRec("memctc", where=[("mcc_cono", "=",
            self.opts["conum"]), ("mcc_type", "=", self.fltcat)], limit=1)
        if not chk:
            return "Invalid Membership Category"
        codes = getSingleRecords(self.opts["mf"], "memctc", ("mcc_code",
            "mcc_desc"), where=[("mcc_cono", "=", self.opts["conum"]),
            ("mcc_type", "=", self.fltcat)], order="mcc_desc")
        if not codes:
            return "rf"
        self.fltcod = []
        for code in codes:
            self.fltcod.append(code[2])

    def doFltGen(self, frt, pag, r, c, p, i, w):
        self.fltgen = w

    def doFltPP(self, frt, pag, r, c, p, i, w):
        self.personal = w

    def doFltND(self, frt, pag, r, c, p, i, w):
        self.namdet = w

    def doFltTo(self, frt, pag, r, c, p, i, w):
        self.fltto = w
        if self.ulist == "C":
            self.flttyp = ""

    def doFltAct(self, frt, pag, r, c, p, i, w):
        self.fltact = w
        if not self.fltact:
            self.ff.loadEntry(frt, pag, p+1, data="All Activities")
        else:
            chk = self.sql.getRec("drsact", where=[("dac_code", "=",
                self.fltact)], limit=1)
            if not chk:
                return "Invalid Activity Code"
            self.ff.loadEntry(frt, pag, p+1, data=chk[1])

    def doFltTyp(self, frt, pag, r, c, p, i, w):
        self.flttyp = w
        if not self.flttyp:
            self.ff.loadEntry(frt, pag, p+1, data="All Types")
        else:
            chk = self.sql.getRec("drstyp", where=[("dtp_code", "=",
                self.flttyp)], limit=1)
            if not chk:
                return "Invalid Type Code"
            self.ff.loadEntry(frt, pag, p+1, data=chk[1])

    def doFltStp(self, frt, pag, r, c, p, i, w):
        self.fltstp = w

    def doFltGrp(self, frt, pag, r, c, p, i, w):
        self.fltgrp = []
        if w == "A":
            return
        dat = self.sql.getRec("telgrp", cols=["tdg_group",
            "tdg_desc"], order="tdg_group")
        dat.insert(0, ["", "Blank"])
        groups = getSingleRecords(self.opts["mf"], "telgrp", ("tdg_group",
            "tdg_desc"), where=dat, ttype="D")
        if not groups:
            return "rf"
        for group in groups:
            self.fltgrp.append(group[0])

    def doFltCon(self, frt, pag, r, c, p, i, w):
        self.fltcon = w

    def doFltInd(self, frt, pag, r, c, p, i, w):
        self.fltind = w

    def doFltEnd(self):
        self.fltexit = False
        self.ff.closeProcess()

    def doFltExit(self):
        self.fltexit = True
        self.ff.closeProcess()

    def doImport(self):
        # Fields
        r1s = (("Yes", "Y"), ("No", "N"))
        r2s = (("First Name", "N"), ("First Initial", "I"))
        impfld = [
            (("T",0,0,0),("IRB",r1s),0,"Personalize","",
                "N","N",self.doImpPP,None,None,None),
            (("T",0,1,0),("IRB",r1s),0,"Title","",
                "N","N",self.doImpTD,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Name Detail","",
                "I","N",self.doImpND,None,None,None)]
        # Columns
        if self.dtyp == "S":
            self.impcol = [["Mobile", 0, "NA", 20]]
        else:
            self.impcol = [["Email Address", 0, "TX", 50]]
        self.impcol.append(["Title", 0, "NA", 6])
        self.impcol.append(["Surname", 1, "NA", 30])
        self.impcol.append(["Names", 2, "NA", 30])
        # Import File
        err = ""
        self.impdat = []
        self.fi = FileImport(self.opts["mf"], impcol=self.impcol, impfld=impfld)
        for num, line in enumerate(self.fi.impdat):
            if len(line) != len(self.impcol):
                if self.fi.impign == "Y":
                    continue
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, len(self.impcol), len(line))
                break
            eml = line[0]
            if self.personal == "Y":
                if self.titdet:
                    tit = line[1]
                else:
                    tit = ""
                if line[2] == line[3]:
                    nam = line[2]
                else:
                    nam = line[3].split()[0]
                    if self.namdet == "I":
                        nam = nam[0].upper()
                    nam = "%s %s" % (nam, line[2])
            else:
                tit = nam = ""
            if self.dtyp == "E" and self.df.doCheckEmail(eml):
                if self.fi.impign == "Y":
                    continue
                err = "This '%s' is Not a Valid Email Address" % eml
                break
            self.loadData(tit, nam, eml)
        if self.fi.impdat == []:
            self.impxit = True
        elif err and self.fi.impign == "N":
            showError(self.opts["mf"].body, "Import Error", err)
            self.impdat = []
            self.impxit = True
        elif not self.impdat:
            showError(self.opts["mf"].body, "Error",
                "No Valid Records to Import")
            self.impxit = True

    def doImpPP(self, obj, w):
        self.personal = w
        if self.personal == "N":
            obj.topf[0][7][1] = "OUA"
            obj.topf[0][8][1] = "OUA"
            obj.topf[0][9][1] = "OUA"
            return "sk2"
        else:
            obj.topf[0][7][1] = "IUA"
            obj.topf[0][8][1] = "IUA"
            obj.topf[0][9][1] = "IUA"

    def doImpTD(self, obj, w):
        if w == "Y":
            self.titdet = True
            obj.topf[0][7][1] = "IUA"
        else:
            self.titdet = False
            obj.topf[0][7][1] = "OUA"
        if self.personal == "N":
            return "sk1"

    def doImpND(self, obj, w):
        self.namdet = w

    def loadData(self, tit, nam, eml):
        if self.personal:
            if tit:
                nam = "%s %s" % (tit, nam)
        self.impdat.append([eml, nam.title()])

    def doSkip(self, frt, pag, r, c, p, i, w):
        self.skip = w

    def doSubject(self, frt, pag, r, c, p, i, w):
        self.subj = w
        self.fle["ftype"] = (("All", "*"),)

    def doEmbed(self, frt, pag, r, c, p, i, w):
        if w:
            w = w.split(",")
            pdf = []
            for f in w:
                if pathlib.Path(f).suffix == ".pdf" and FITZ:
                    pdf.append(f)
                    continue
                if not imghdr.what(f):
                    showError(self.opts["mf"].body, "Invalid File Type",
                """Valid File Types are as Follows:

bmp   BMP files
gif   GIF 87a and 89a Files
jpeg  JPEG data in JFIF or Exif formats
pbm   Portable Bitmap Files
pdf   Portable Document Format (If pymupdf is installed)
pgm   Portable Graymap Files
png   Portable Network Graphics
ppm   Portable Pixmap Files
rast  Sun Raster Files
rgb   SGI ImgLib Files
tiff  TIFF Files
xbm   X Bitmap Files""")
                    return "Invalid File Type"
            self.embed = w
        else:
            self.embed = []
        if self.embed and pdf:
            sp = SplashScreen(self.df.mstFrame,
                "Converting PDF to Images\n\nPlease Wait")
            for fnam in pdf:
                try:
                    self.doFitz(fnam)
                except:
                    pass
            sp.closeSplash()
        if self.embed and Image:
            sp = SplashScreen(self.df.mstFrame,
                "Resizing Images for Mailing\n\nPlease Wait")
            for n, e in enumerate(self.embed):
                try:
                    img = Image.open(e)
                    siz = img.size
                    if siz[0] > 1024:
                        new = img.resize((1024, int((siz[1]*1024)/siz[0])), 1)
                        e = os.path.join(self.opts["mf"].rcdic["wrkdir"],
                            os.path.basename(e))
                        new.save(e)
                        self.embed[n] = e
                except:
                    pass
            sp.closeSplash()
        self.fle["ftype"] = (("Attachment", "*"),)
        if not self.embed:
            self.link = "N"
            self.df.loadEntry(frt, pag, p+1, data="N")
            self.df.loadEntry(frt, pag, p+2, data="N")
            self.df.loadEntry(frt, pag, p+3, data="")
            return "sk3"

    def doLink(self, frt, pag, r, c, p, i, w):
        self.link = w
        if self.link == "N":
            self.df.loadEntry(frt, pag, p+1, data="N")
            self.df.loadEntry(frt, pag, p+2, data="")
            return "sk2"

    def doText(self, frt, pag, r, c, p, i, w):
        self.lnktxt = w
        self.df.loadEntry(frt, pag, p+1, data=self.urll)

    def doSite(self, frt, pag, r, c, p, i, w):
        if w:
            try:
                requests.get(w)
            except:
                return "Invalid Link"
        self.lnkurl = w

    def doFitz(self, fnam):
        b = os.path.basename(fnam.replace(" ", "_"))
        o = os.path.join(self.opts["mf"].rcdic["wrkdir"],
            pathlib.Path(b).stem)
        f = o + "_%03i.jpg"
        doc = pymupdf.open(fnam)
        for num, pag in enumerate(doc):
            try:
                pix = pag.get_pixmap()
                pix.save(f % num)
            except:
                pix = pag.getPixmap()
                pix.writeImage(f % num)
        fls = glob.glob(o + "*.jpg")
        fls = sorted(fls, reverse=True)
        idx = self.embed.index(fnam)
        self.embed.remove(fnam)
        for nam in fls:
            self.embed.insert(idx, nam)

    def doAttach(self, frt, pag, r, c, p, i, w):
        self.attach = w.split(",")

    def doMessage(self, frt, pag, r, c, p, i, w):
        if not w and not self.embed and not self.attach:
            return "Invalid Message"
        if "{{" in w:
            if "{{name}}" not in w and "{{surname}}" not in w:
                return "Invalid {{ substitution in Message"
        self.mess = w
        if MARKDOWN:
            self.html = markdown(self.mess)
        else:
            self.html = self.mess

    def doPreview(self):
        mess = self.df.topEntry[0][9].get("1.0", "end")
        if not self.embed and not self.attach and not mess:
            return
        if self.personal == "Y":
            if "{{name}}" in mess:
                mess = mess.replace("{{name}}", "Tom Jones")
            else:
                mess = mess.replace("{{surname}}", "Tom Jones")
        state = self.df.disableButtonsTags()
        ShowEmail(self.df.window, mess, self.embed, self.attach)
        self.df.enableButtonsTags(state=state)

    def doExecute(self):
        wid, self.mess = self.df.getEntry("T", 0, 9, cr=True)
        if not self.embed and not self.attach and not self.mess:
            return
        if "{{" in self.mess:
            if "{{name}}" not in self.mess and "{{surname}}" not in self.mess:
                showError(self.opts["mf"].body, "Error",
                    "Invalid {{ substitution in Message")
                return
        if MARKDOWN:
            self.html = markdown(self.mess)
        else:
            self.html = self.mess
        self.doEnd()

    def doEnd(self):
        self.df.closeProcess()
        if self.dtyp == "S":
            self.doSendSMS()
        else:
            self.doSendEmail()
        self.closeProcess()

    def doSendSMS(self):
        self.url = "http://www.mymobileapi.com/api5/http5.aspx?"
        self.par = {"username": self.sms[1], "password": self.sms[2]}
        units = self.doExecuteSMS("credits")
        if units is None:
            showError(self.opts["mf"].body, "Error",
                "Please Check Username and/or Password")
            return
        elif not units:
            showError(self.opts["mf"].body, "Error", "No Credits")
            return
        if self.ulist == "B":
            if self.tab[0]:
                tab = ["bwltab"]
                whr = [("btb_cono", "=", self.opts["conum"])]
                if self.fltcat == "M":
                    whr.append(("btb_tab", "<", self.nstart))
                elif self.fltcat == "G":
                    whr.append(("btb_tab", ">=", self.nstart))
                if self.fltgen in ("M", "F"):
                    whr.append(("btb_gender", "=", self.fltgen))
                col = ["btb_surname", "btb_names", "btb_cell"]
                odr = "btb_surname, btb_names"
                sel = "btb_surname"
            else:
                tab = ["scpmem"]
                whr = [("scm_cono", "=", self.opts["conum"])]
                col = ["scm_surname", "scm_names", "scm_phone"]
                odr = "scm_surname, scm_names"
                sel = "scm_surname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[2], "%s %s" % (rec[1].split()[0], rec[0])))
        elif self.ulist == "K":
            tab = ["bkmcon"]
            col = ["bkc_title", "bkc_sname", "bkc_names", "bkc_celno"]
            whr = [
                ("bkc_cono", "=", self.opts["conum"]),
                ("bkc_celno", "<>", "")]
            odr = "bkm_sname, bkm_names"
            sel = "bkm_sname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[3], "%s %s" % (rec[2].split()[0], rec[1])))
        elif self.ulist == "M":
            tab = ["memmst", "memkon", "memctk"]
            col = ["mlm_title", "mlm_surname", "mlm_names"]
            whr = [
                ("mlm_cono", "=", self.opts["conum"]),
                ("mlm_state", "=", "A"),
                ("mlk_cono=mlm_cono",),
                ("mlk_memno=mlm_memno",),
                ("mck_code=mlk_code",),
                ("mck_type", "=", "M")]
            if self.fltgen in ("M", "F"):
                whr.append(("mlm_gender", "=", self.fltgen))
            if self.fltcat:
                tab.append("memcat")
                whr.append(("mlc_cono=mlm_cono",))
                whr.append(("mlc_memno=mlm_memno",))
                whr.append(("mlc_type", "=", self.fltcat))
                if self.fltcod:
                    whr.append(("mlc_code", "in", self.fltcod))
            odr = "mlm_surname, mlm_names"
            sel = "mlm_surname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[3], "%s %s" % (rec[2].split()[0], rec[1])))
        elif self.ulist == "S":
            tab = ["bksown"]
            col = ["bof_snam", "bof_fnam", "bof_cell"]
            whr = [("bof_cell", "<>", "")]
            odr = "bof_snam, bof_fnam"
            sel = "bof_snam"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[2], "%s %s" % (rec[1].split()[0], rec[0])))
        elif self.ulist == "T":
            tab = ["telmst"]
            col = ["tdm_name", "tdm_mobile", "tdm_group"]
            whr = [("tdm_mobile", "<>", "")]
            odr = "tdm_name"
            sel = "tdm_name"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[1], rec[0]))
                if self.fltcon == "Y":
                    con = self.sql.getRec("telcon", cols=["tdc_contact",
                        "tdc_mobile"], where=[("tdc_name", "=", rec[0]),
                        ("tdc_celno", "<>", "")])
                    if not con:
                        continue
                    for c in con:
                        accs.append((c[1], c[0]))
        elif self.ulist == "X":
            accs = self.impdat
        if units < len(accs):
            showError(self.opts["mf"].body, "Out of Units", "There Are "\
                "Insufficient Units, %s, in the Account for %s SMS's." %
                (units, len(accs)))
            return
        for acc in accs:
            cell = acc[0].strip().replace(" ", "")
            cell = cell.replace("(","").replace(")","")
            cell = cell.replace("{","").replace("}","")
            cell = cell.split(",")
            cont = acc[1].strip()
            if not cont:
                name = "Sir/Madam"
            else:
                name = self.doNames(cont)
            if self.personal == "Y":
                if self.mess.count("{{name}}"):
                    mess = self.mess.replace("{{name}}", name)
                elif self.mess.count("{{surname}}"):
                    nam = name.split(",")
                    if len(nam) > 1:
                        name = "%s %s" % (nam[1], nam[0])
                    mess = self.mess.replace("{{surname}}", name)
            else:
                mess = self.mess
            for num in cell:
                if len(num) == 10 or num.startswith("+"):
                    self.doExecuteSMS("sendparam", num, mess)

    def doNames(self, name):
        n = name.split()
        new = ""
        while n:
            new = new + n.pop(0).capitalize() + " "
        idx = new.find("-")
        if idx != -1:
            new = new.replace("-%s" % new[idx+1], "-%s" % new[idx+1].upper())
        return new.strip()

    def doExecuteSMS(self, stype, num=None, dat=None):
        par = self.par.copy()
        par["type"] = stype
        if dat:
            par["numto"] = num
            par["data1"] = dat
        try:
            f = requests.post(self.url, data=par, timeout=5)
            if stype == "credits":
                s = f.text
                s = s.split("<%s>" % stype)[1].split("</%s>" % stype)[0]
                return int(s)
        except:
            return

    def doSendEmail(self):
        if self.ulist == "B":
            if self.tab[0]:
                tab = ["bwltab"]
                whr = [
                    ("btb_cono", "=", self.opts["conum"]),
                    ("btb_mail", "<>", "")]
                if self.fltcat == "M":
                    whr.append(("btb_tab", "<", self.nstart))
                elif self.fltcat == "G":
                    whr.append(("btb_tab", ">=", self.nstart))
                if self.fltgen in ("M", "F"):
                    whr.append(("btb_gender", "=", self.fltgen))
                col = ["btb_surname", "btb_names", "btb_mail"]
                odr = "btb_surname, btb_names"
                sel = "btb_surname"
            else:
                tab = ["scpmem"]
                whr = [
                    ("scm_cono", "=", self.opts["conum"]),
                    ("btb_mail", "<>", "")]
                col = ["scm_surname", "scm_names", "scm_email"]
                odr = "scm_surname, scm_names"
                sel = "scm_surname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[2], "%s %s" % (rec[1].split()[0], rec[0])))
        elif self.ulist == "C":
            tab = "crsmst"
            whr = [("crm_cono", "=", self.opts["conum"])]
            if self.fltto == "M":
                whr.append(("crm_mgr_email", "<>", ""))
                col = ["crm_mgr", "crm_mgr_email"]
            elif self.fltto == "A":
                whr.append(("crm_acc_email", "<>", ""))
                col = ["crm_acc", "crm_acc_email"]
            else:
                whr.append(("crm_ord_email", "<>", ""))
                col = ["crm_ord", "crm_ord_email"]
            whr.append(("crm_stat", "<>", "X"))
            odr = col[0]
            sel = col[0]
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[1], rec[0]))
        elif self.ulist == "D":
            tab = ["drsmst"]
            whr = [("drm_cono", "=", self.opts["conum"])]
            if self.fltto == "M":
                whr.append(("drm_mgr_email", "<>", ""))
                col = ["drm_mgr", "drm_mgr_email"]
            elif self.fltto == "A":
                whr.append(("drm_acc_email", "<>", ""))
                col = ["drm_acc", "drm_acc_email"]
            else:
                whr.append(("drm_sls_email", "<>", ""))
                col = ["drm_sls", "drm_sls_email"]
            if self.fltact:
                whr.append(("drm_bus_activity", "=", self.fltact))
            if self.flttyp:
                whr.append(("drm_bus_type", "=", self.flttyp))
            if self.fltstp == "N":
                whr.append(("drm_stop", "=", "N"))
            whr.append(("drm_stat", "<>", "X"))
            odr = col[0]
            sel = col[0]
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[1], rec[0]))
        elif self.ulist == "K":
            tab = ["bkmcon"]
            col = ["bkc_title", "bkc_sname", "bkc_names", "bkc_email"]
            whr = [
                ("bkc_cono", "=", self.opts["conum"]),
                ("bkc_email", "<>", "")]
            odr = "bkc_sname, bkc_names"
            sel = "bkc_sname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                if self.personal == "Y":
                    tit = rec[0]
                    sur = rec[1]
                    nam = rec[2].split()[0].title()
                    if self.namdet == "I":
                        nam = nam[0].upper()
                    accs.append((rec[3], "%s %s %s" % (tit, nam, sur)))
                else:
                    accs.append((rec[3], ""))
        elif self.ulist == "M":
            tab = ["memmst", "memkon", "memctk"]
            col = ["mlm_title", "mlm_surname", "mlm_names"]
            whr = [
                ("mlm_cono", "=", self.opts["conum"]),
                ("mlm_state", "=", "A"),
                ("mlk_cono=mlm_cono",),
                ("mlk_memno=mlm_memno",),
                ("mck_code=mlk_code",),
                ("mck_type", "=", "E")]
            if self.fltgen in ("M", "F"):
                whr.append(("mlm_gender", "=", self.fltgen))
            whr.extend([
                ("mlk_cono=mlm_cono",),
                ("mlk_memno=mlm_memno",),
                ("mlk_code", "=", 5)])
            if self.fltcat:
                tab.append("memcat")
                whr.append(("mlc_cono=mlm_cono",))
                whr.append(("mlc_memno=mlm_memno",))
                whr.append(("mlc_type", "=", self.fltcat))
                if self.fltcod:
                    whr.append(("mlc_code", "in", self.fltcod))
            odr = "mlm_surname, mlm_names"
            sel = "mlm_surname"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                if self.personal == "Y":
                    tit = rec[0]
                    sur = rec[1]
                    nam = rec[2].split()[0].title()
                    if self.namdet == "I":
                        nam = nam[0].upper()
                    accs.append((rec[3], "%s %s %s" % (tit, nam, sur)))
                else:
                    accs.append((rec[3], ""))
        elif self.ulist == "S":
            tab = ["bksown"]
            col = ["bof_snam", "bof_fnam", "bof_mail"]
            whr = [("bof_mail", "<>", "")]
            odr = "bof_snam, bof_fnam"
            sel = "bof_snam"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                if self.personal == "Y":
                    sur = rec[0]
                    nam = rec[1].split()[0].title()
                    if self.namdet == "I":
                        nam = nam[0].upper()
                    accs.append((rec[2], "%s %s" % (nam, sur)))
                else:
                    accs.append((rec[2], ""))
        elif self.ulist == "T":
            tab = ["telmst"]
            col = ["tdm_name", "tdm_email", "tdm_group"]
            whr = [("tdm_email", "<>", "")]
            odr = "tdm_name"
            sel = "tdm_name"
            recs = self.doGetRecs(tab, col, whr, odr, sel)
            accs = []
            for rec in recs:
                accs.append((rec[1], rec[0]))
                if self.fltcon == "Y":
                    con = self.sql.getRec("telcon", cols=["tdc_contact",
                        "tdc_email"], where=[("tdc_name", "=", rec[0]),
                        ("tdc_email", "<>", "")])
                    if not con:
                        continue
                    for c in con:
                        accs.append((c[1], c[0]))
        elif self.ulist in ("H", "L", "O", "P", "R", "W"):
            tabs = {
                "H": ("rcatnm", "rtn_cono", ["rtn_name", "rtn_email"]),
                "L": ("lonmf1", "lm1_cono", ["lm1_name", "lm1_email"]),
                "O": ("rcaowm", "rom_cono", ["rom_name", "rom_email"]),
                "P": ("scpmem", "scm_cono", ["scm_surname", "scm_names",
                    "scm_email"]),
                "R": ("rtlmst", "rtm_cono", ["rtm_name", "rtm_email"]),
                "W": ("wagmst", "wgm_cono", ["wgm_sname", "wgm_fname",
                    "wgm_emadd"])}
            tab = tabs[self.ulist]
            col = tab[2]
            whr = [(tab[1], "=", self.opts["conum"])]
            odr = col[0]
            sel = col[0]
            recs = self.sql.getRec(tables=tab[0], cols=col, where=whr,
                order=odr)
            if self.fltind == "Y":
                recs = getSingleRecords(self.opts["mf"], tab[0], col,
                    where=recs, selcol=sel, ttype="D")
            accs = []
            for rec in recs:
                if len(rec) == 3:
                    accs.append((rec[2], "%s %s" % (rec[1].split()[0], rec[0])))
                else:
                    accs.append((rec[1], rec[0]))
        elif self.ulist == "X":
            accs = self.impdat
        sent = []
        for num, acc in enumerate(accs):
            mail = acc[0].strip().replace(" ", "").split(",")
            for add in mail:
                if add in sent:
                    mail.remove(add)
                else:
                    sent.append(add)
            if not mail:
                continue
            if not acc[1]:
                name = "Sir/Madam"
            else:
                name = self.doNames(acc[1])
            mess = self.mess
            html = self.html
            if self.personal == "Y":
                if mess.count("{{name}}"):
                    mess = self.mess.replace("{{name}}", name)
                    html = html.replace("{{name}}", name)
                elif mess.count("{{surname}}"):
                    nam = name.split(",")
                    if len(nam) > 1:
                        name = "%s %s" % (nam[1], nam[0])
                    mess = self.mess.replace("{{surname}}", name)
                    html = html.replace("{{surname}}", name)
            ok = False
            while not ok:
                sp = SplashScreen(self.opts["mf"].body, "E-Mailing the "\
                    "Message to %s\n\nPlease Wait........ (%s of %s)" %
                    (mail[0], num + 1, len(accs)))
                if self.link == "Y":
                    url = (self.lnktxt, self.lnkurl)
                else:
                    url = None
                err = sendMail(self.smtp, self.fadd, mail, self.subj,
                    mess=(mess, html), attach=self.attach, embed=self.embed,
                    lnkurl=url, wrkdir=self.opts["mf"].rcdic["wrkdir"])
                sp.closeSplash()
                if err:
                    if self.skip == "Y":
                        ok = "SKIPPED"
                    else:
                        ok = askQuestion(self.opts["mf"].body, "E-Mail Error",
                            "Problem Delivering This Message.\n\nTo: "\
                            "%s\nSubject: %s\n\n%s\n\nWould You Like to "\
                            "Retry?" % (mail, self.subj, err))
                    if ok == "yes":
                        ok = False
                    else:
                        ok = "FAILED"
                else:
                    ok = "OK"
            # Log the email attempt into table emllog.
            tadd = ""
            for t in mail:
                if not tadd:
                    tadd = t
                else:
                    tadd = tadd + ", " + t
            self.sql.insRec("emllog", data=[self.fadd.strip(), tadd.strip(),
                self.subj.strip(), "%04i-%02i-%02i %02i:%02i" % \
                time.localtime()[0:5], ok])
            self.opts["mf"].dbm.commitDbase()

    def doGetRecs(self, tab, col, whr, odr, sel):
        if self.ulist == "T" and self.fltgrp:
            accs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
            recs = []
            for acc in accs:
                grp = acc[col.index("tdm_group")].split(",")
                for g in grp:
                    if g in self.fltgrp:
                        recs.append(acc)
                        break
        else:
            recs = self.sql.getRec(tables=tab, cols=col, where=whr, order=odr)
        nrec = []
        if self.fltind == "Y":
            data = getSingleRecords(self.opts["mf"], tab, col, where=recs,
                selcol=sel, ttype="D")
            if self.ulist == "B":
                for dat in data:
                    if tab[0] == "bwltab":
                        snm = dat[col.index("btb_surname")]
                        nms = dat[col.index("btb_names")]
                        if self.dtyp == "S":
                            con = dat[col.index("btb_cell")]
                        else:
                            con = dat[col.index("btb_mail")]
                    else:
                        snm = dat[col.index("scm_surname")]
                        nms = dat[col.index("scm_names")]
                        if self.dtyp == "S":
                            con = dat[col.index("scm_phone")]
                        else:
                            con = dat[col.index("scm_email")]
                    nrec.append([snm, nms, con])
            elif self.ulist == "C":
                for dat in data:
                    acc = []
                    for c in col:
                        acc.append(dat[col.index(c)])
                    nrec.append(acc)
            elif self.ulist == "D":
                for dat in data:
                    acc = []
                    for c in col:
                        acc.append(dat[col.index(c)])
                    nrec.append(acc)
            elif self.ulist == "K":
                for dat in data:
                    tit = dat[col.index("bkc_title")]
                    snm = dat[col.index("bkc_sname")]
                    nms = dat[col.index("bkc_names")]
                    if self.dtyp == "S":
                        con = dat[col.index("bkc_celno")]
                    else:
                        con = dat[col.index("bkc_email")]
                    nrec.append([tit, snm, nms, con])
            elif self.ulist == "M":
                for dat in data:
                    if self.dtyp == "S":
                        typ = "M"
                    else:
                        typ = "E"
                    con = self.sql.getRec(tables=["memkon", "memctk"],
                        cols=["mlk_detail"], where=[("mlk_cono", "=", dat[0]),
                        ("mlk_memno", "=", dat[1]), ("mck_type", "=", typ),
                        ("mlk_code=mck_code",)])
                    if not con:
                        continue
                    add = con[0][0]
                    if len(con) > 1:
                        for a in con[1:]:
                            add = "%s,%s" % (add, a[0])
                    nrec.append([
                        dat[col.index("mlm_title")],
                        dat[col.index("mlm_surname")],
                        dat[col.index("mlm_names")], add])
            elif self.ulist == "S":
                for dat in data:
                    snm = dat[col.index("bof_snam")]
                    nms = dat[col.index("bof_fnam")]
                    if self.dtyp == "S":
                        con = dat[col.index("bof_cell")]
                    else:
                        con = dat[col.index("bof_mail")]
                    nrec.append([snm, nms, con])
            elif self.ulist == "T":
                for dat in data:
                    nam = dat[col.index("tdm_name")]
                    if self.dtyp == "S":
                        con = dat[col.index("tdm_mobile")]
                    else:
                        con = dat[col.index("tdm_email")]
                    grp = dat[col.index("tdm_group")]
                    nrec.append([nam, con, grp])
            return nrec
        else:
            return recs

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
