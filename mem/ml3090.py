"""
SYNOPSIS
    Members Ledger Update Request Email.

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

import time
from TartanClasses import CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import askChoice, sendMail, showError
from tartanWork import countries

class ml3090(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "memctk", "memmst",
            "memadd", "memkon", "memctc", "memctk"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        ctlsys = gc.getCtl("ctlsys")
        if not ctlsys:
            return
        self.smtp = []
        for fld in ("msvr", "mprt", "msec", "maut", "mnam", "mpwd"):
            self.smtp.append(ctlsys["sys_%s" % fld])
        if not self.smtp[0]:
            showError(self.opts["mf"].body, "SMTP Error",
                "There is NO SMTP Server in the System Record!")
            return
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.fadd = ctlmst["ctm_email"]
        if not self.fadd:
            showError(self.opts["mf"].body, "From Error",
                "There is NO Email Address on the Company Record!")
            return
        memctl = gc.getCtl("memctl", self.opts["conum"])
        if not memctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        self.head = ("%03u %-30s %s" % (self.opts["conum"], self.opts["conam"],
            "%s"))
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Members Ledger Update Request (%s)" % self.__class__.__name__)
        cod = {
            "stype": "R",
            "tables": ("memctc",),
            "cols": (
                ("mcc_code", "", 0, "Cd"),
                ("mcc_desc", "", 0, "Description", "Y")),
            "where": [("mcc_cono", "=", self.opts["conum"])],
            "whera": [["T", "mcc_type", 2]],
            "order": "mcc_code",
            "size": (400, 600)}
        mlm = {
            "stype": "R",
            "tables": ("memmst",),
            "cols": (
                ("mlm_memno", "", 0, "Mem-No"),
                ("mlm_oldno", "", 0, "Old-No"),
                ("mlm_gender", "", 0, "G"),
                ("mlm_state", "", 0, "S"),
                ("mlm_surname", "", 0, "Surname", "Y"),
                ("mlm_names", "", 0, "Names", "F")),
            "where": [("mlm_cono", "=", self.opts["conum"])],
            "order": "mlm_surname, mlm_names",
            "sort": False}
        r1s = (
            ("All", "A"),
            ("Main","B"),
            ("Sports","C"),
            ("Debentures","D"))
        r2s = (("Yes","Y"),("No","N"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Category","",
                "A","Y",self.doCat,None,None,None),
            (("T",0,1,0),"IUI",2,"Code","",
                0,"Y",self.doCod,cod,None,None),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),"IUI",6,"First Member Number","",
                "","Y",self.doAcc1,mlm,None,None),
            (("T",0,3,0),"IUI",6,"Last Member Number","",
                "","Y",self.doAcc2,mlm,None,None),
            (("T",0,4,0),("IRB",r2s),0,"Ignore Errors","",
                "Y","Y",self.doIgn,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt)

    def doCat(self, frt, pag, r, c, p, i, w):
        if w == "A":
            self.cat = ""
            self.cod = ""
            self.df.loadEntry(frt, pag, p+2, data="All Categories and Codes")
            return "sk2"
        self.cat = w

    def doCod(self, frt, pag, r, c, p, i, w):
        self.cod = w
        if self.cod:
            self.chk = self.sql.getRec("memctc", cols=["mcc_desc"],
                where=[("mcc_cono", "=", self.opts["conum"]), ("mcc_type", "=",
                self.cat), ("mcc_code", "=", self.cod)], limit=1)
            if not self.chk:
                return "Invalid Category Code"
            self.df.loadEntry(frt, pag, p+1, data=self.chk[0])
        else:
            self.df.loadEntry(frt, pag, p+1, "All Codes")

    def doAcc1(self, frt, pag, r, c, p, i, w):
        self.acc1 = w

    def doAcc2(self, frt, pag, r, c, p, i, w):
        if w:
            if w < self.acc1:
                return "Invalid Last Member < First Member"
            self.acc2 = w
        else:
            self.acc2 = 999999

    def doIgn(self, frt, pag, r, c, p, i, w):
        self.ignore = w

    def doEnd(self):
        self.df.closeProcess()
        tab = ["memmst"]
        whr = [
            ("mlm_cono", "=", self.opts["conum"]),
            ("mlm_memno", ">=", self.acc1),
            ("mlm_memno", "<=", self.acc2),
            ("mlm_state", "=", "A")]
        if self.cat:
            tab.append("memcat")
            whr.append(("mlc_cono=mlm_cono",))
            whr.append(("mlc_memno=mlm_memno",))
            whr.append(("mlc_type", "=", self.cat))
            if self.cod:
                whr.append(("mlc_code", "=", self.cod))
        odr = "mlm_memno"
        mems = self.sql.getRec(tables=tab, cols=["mlm_memno", "mlm_title",
            "mlm_initial", "mlm_surname", "mlm_names", "mlm_nation",
            "mlm_dob"], where=whr, order=odr)
        if not mems:
            showError(self.opts["mf"].body, "Selection Error",
                "No Members Selected")
        self.printReport(mems)
        self.closeProcess()

    def printReport(self, mems):
        ktypes = {}
        ctk = self.sql.getRec("memctk")
        for c in ctk:
            ktypes[c[1]] = c[2]
        for mem in mems:
            text = """Dear %s %s %s

Here are your details as stored on the club's database. Please could you be so kind as to check them and let us have any changes by return email so that we can update our records.

%-30s%s
%-30s%s
%-30s%s
%-30s%s""" % (mem[1], mem[2], mem[3], "Membership Number:", mem[0], "Names:", mem[4], "Nationality:", countries[mem[5]][1], "Date of Birth:", CCD(mem[6], "D1", 10).disp)
            add = self.sql.getRec("memadd", cols=["mla_type",
                "mla_add1", "mla_add2", "mla_add3", "mla_city", "mla_code"],
                where=[("mla_cono", "=", self.opts["conum"]), ("mla_memno",
                "=", mem[0])])
            for a in add:
                if a[0] == "P":
                    text = """%s
%-30s%s""" % (text, "Postal Address:", a[1])
                else:
                    text = """%s
%-30s%s""" % (text, "Street Address:", a[1])
                for n in a[2:]:
                    if n:
                        text = """%s, %s""" % (text, n)
            kon = self.sql.getRec(tables=["memctk", "memkon"],
                cols=["mck_code", "mck_type", "mlk_detail"],
                where=[("mlk_cono", "=", self.opts["conum"]), ("mlk_memno",
                "=", mem[0]), ("mck_code=mlk_code",)])
            mail = []
            for e in kon:
                if e[0] == 5:
                    ktyp = "E-Mail Address:"
                else:
                    ktyp = "%s:" % ktypes[e[1]]
                text = """%s
%-30s%s""" % (text, ktyp, e[2])
                if e[1] == "E" and e[2][:2] != "08":
                    mail.append(e[2])
            if not mail:
                continue
            text = """%s

With Thanks

Membership Secretary
%s""" % (text, self.opts["conam"])
            ok = sendMail(self.smtp, self.fadd, mail, "Member's Details",
                mess=text, wrkdir=self.opts["mf"].rcdic["wrkdir"])
            if not ok and self.ignore == "N":
                ok = askChoice(self.opts["mf"].body, "SMTP Server Error",
                    "Mail to %s Could Not be Sent" % mail,
                    butt=(("Continue","C"), ("Quit","Q")),
                    default="Continue")
                if ok == "Q":
                    self.doExit()
                    break

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
