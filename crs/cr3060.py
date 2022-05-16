"""
SYNOPSIS
    Creditors Ledger Master Listing.

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
from TartanClasses import CCD, GetCtl, RepPrt, Sql, TartanDialog
from tartanFunctions import showError

class cr3060(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "crsmst",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        crsctl = gc.getCtl("crsctl", self.opts["conum"])
        if not crsctl:
            return
        self.fromad = crsctl["ctc_emadd"]
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.sysdtd = "%i/%02i/%02i" % (t[0], t[1], t[2])
        self.sysdttm = "(Printed on: %i/%02i/%02i at %02i:%02i) %6s" % (t[0],
            t[1], t[2], t[3], t[4], self.__class__.__name__)
        return True

    def mainProcess(self):
        self.tit = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Creditors Master Listing (%s)" % self.__class__.__name__)
        r1s = (("Number", "N"), ("Name", "M"))
        r2s = (("Yes", "Y"), ("No", "N"))
        r3s = (("Manager", "M"), ("Accounts", "A"), ("Orders", "O"))
        r4s = (("Yes", "Y"), ("No", "N"), ("Only", "O"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Sort Order","",
                "N","Y",self.doSort,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Use Full Address","",
                "N","Y",self.doAddress,None,None,None),
            (("T",0,2,0),("IRB",r3s),0,"Contact Details","",
                "M","Y",self.doContact,None,None,None),
            (("T",0,3,0),("IRB",r4s),0,"Include Redundant","",
                "N","Y",self.doRedu,None,None,None))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], title=self.tit, eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","N"))

    def doSort(self, frt, pag, r, c, p, i, w):
        self.sort = w

    def doAddress(self, frt, pag, r, c, p, i, w):
        self.address = w

    def doContact(self, frt, pag, r, c, p, i, w):
        self.condet = w

    def doRedu(self, frt, pag, r, c, p, i, w):
        self.redu = w

    def doEnd(self):
        self.df.closeProcess()
        whr = [("crm_cono", "=", self.opts["conum"])]
        if self.redu == "N":
            whr.append(("crm_stat", "<>", "X"))
        elif self.redu == "O":
            whr.append(("crm_stat", "=", "X"))
        if self.sort == "N":
            odr = "crm_acno"
        else:
            odr = "crm_name"
        recs = self.sql.getRec("crsmst", where=whr, order=odr)
        if not recs:
            showError(self.opts["mf"].body, "Selection Error",
            "No Records Selected")
        else:
            self.printReport(recs)
        self.closeProcess()

    def printReport(self, recs):
        mnam = self.__class__.__name__
        head = ["Creditors Ledger Master List as at %s" % self.sysdtd]
        if self.df.repprt[2] == "export":
            head[0] += " %s" % self.sysdttm
        cols = [
            ["a", "NA", 7, "Acc-Num", "Y"],
            ["b", "NA", 30, "Name", "Y"],
            ["c", "NA", 30, "Address", "Y"],
            ["d", "NA", 4, "PCod", "Y"],
            ["e", "NA", 12, "Tel-Number", "Y"],
            ["f", "NA", 12, "Fax-Number", "Y"]]
        if self.condet == "M":
            det = "Manager's Contact Details"
        elif self.condet == "A":
            det = "Accounts Contact Details"
        else:
            det = "Orders Contact Details"
        cols.extend([
            ["g", "NA", 40, det, "Y"],
            ["h", "NA", 1, "P", "Y"],
            ["i", "UI", 3, "Trm", "Y"],
            ["j", "NA", 1, "B", "Y"],
            ["k", "UI", 2, "St", "Y"],
            ["l", "UI", 7, "CrLimit", "Y"],
            ["m", "UD", 6.2, "Tr-Dis", "Y"],
            ["n", "UD", 6.2, "Py-Dis", "Y"]])
        data = []
        col = self.sql.crsmst_col
        for num, dat in enumerate(recs):
            acno = CCD(dat[col.index("crm_acno")], "NA", 7)
            name = CCD(dat[col.index("crm_name")], "NA", 30)
            add1 = CCD(dat[col.index("crm_add1")], "NA", 30)
            add2 = CCD(dat[col.index("crm_add2")], "NA", 30)
            add3 = CCD(dat[col.index("crm_add3")], "NA", 30)
            pcod = CCD(dat[col.index("crm_pcod")], "NA", 4)
            tel = CCD(dat[col.index("crm_tel")], "NA", 12)
            fax = CCD(dat[col.index("crm_fax")], "NA", 12)
            if self.condet == "M":
                contact = dat[col.index("crm_mgr")]
                email = dat[col.index("crm_mgr_email")].split(",")
            elif self.condet == "A":
                contact = dat[col.index("crm_acc")]
                email = dat[col.index("crm_acc_email")].split(",")
            else:
                contact = dat[col.index("crm_ord")]
                email = dat[col.index("crm_ord_email")].split(",")
            nameml = CCD("%s <%s>" % (contact, email[0]), "NA", 40)
            pyind = CCD(dat[col.index("crm_pyind")], "NA", 1)
            terms = CCD(dat[col.index("crm_terms")], "UI", 3)
            termsb = CCD(dat[col.index("crm_termsb")], "NA", 1)
            stday = CCD(dat[col.index("crm_stday")], "UI", 2)
            limit = CCD(dat[col.index("crm_limit")], "UI", 7)
            trdis = CCD(dat[col.index("crm_trdis")], "UD", 6.2)
            pydis = CCD(dat[col.index("crm_pydis")], "UD", 6.2)
            data.append([acno.work, name.work, add1.work, pcod.work, tel.work,
                fax.work, nameml.work, pyind.work, terms.work, termsb.work,
                stday.work, limit.work, trdis.work, pydis.work])
            if self.address == "Y" and add2.work:
                data.append(["", "", add2.work] + [""] * 11)
            if self.address == "Y" and add3.work:
                data.append(["", "", add3.work] + [""] * 11)
        RepPrt(self.opts["mf"], conum=self.opts["conum"],
            conam=self.opts["conam"], name=mnam, tables=data, heads=head,
            cols=cols, ttype="D", repprt=self.df.repprt,
            repeml=self.df.repeml, fromad=self.fromad)

    def doExit(self):
        self.df.closeProcess()
        self.closeProcess()

    def closeProcess(self):
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
