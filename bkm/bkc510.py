"""
SYNOPSIS
    Booking Contacts Maintenance.

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
from TartanClasses import FileImport, GetCtl, ProgressBar, Sql, TabPrt
from TartanClasses import TartanDialog
from tartanFunctions import showError

class bkc510(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "bkmcon", "bkmmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        return True

    def mainProcess(self):
        con = {
            "stype": "R",
            "tables": ("bkmcon",),
            "cols": (
                ("bkc_ccode", "", 0, "Code"),
                ("bkc_title", "", 0, "Title"),
                ("bkc_sname", "", 0, "Surname", "Y"),
                ("bkc_names", "", 0, "Names", "F"),
                ("bkc_email", "", 0, "Email Address"))}
        self.fld = (
            (("T",0,0,0),"IUA",7,"Code","",
                "","Y",self.doCode,con,None,None),
            (("T",0,1,0),"ITX",6,"Title","",
                "","N",self.doTitle,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"ITX",30,"Surname","",
                "","N",self.doSurname,None,None,("notblank",)),
            (("T",0,3,0),"ITX",30,"Names","",
                "","N",self.doNames,None,None,("notblank",)),
            (("T",0,4,0),"ITX",30,"Address Line 1","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"ITX",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"ITX",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"ITX",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"ITX",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"ITX",20,"Fax Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"ITX",20,"Mobile Number","",
                "","N",None,None,None,("efld",)),
            (("T",0,11,0),"ITX",30,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",0,12,0),"INA",10,"V.A.T Number","",
                "","N",None,None,None,("efld",)))
        but = (
            ("Import",None,self.doImport,0,("T",0,1),("T",0,2),
                "Import Contact Details from a CSV or XLS File having "\
                "the following fields: Code, Title, Surname, Names, "\
                "Address Line1, Line2, Line3, Postal Code, Telephone Number, "\
                "Fax Number, Mobile Number, Email Address, VAT Number"),
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,1)),
            ("Print", None, self.doPrint,0,("T",0,2),("T",0,1)),
            ("Quit", None, self.doExit,1,None,None))
        tnd = ((self.doAccept,"N"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt, clicks=self.doClick)

    def doClick(self, *opts):
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.ccode = w
        if w:
            self.oldcon = self.sql.getRec("bkmcon", where=[("bkc_cono",
                "=", self.opts["conum"]), ("bkc_ccode", "=", w)], limit=1)
            if not self.oldcon:
                return "Invalid Contact Code"
            self.newcon = False
            self.title = self.oldcon[self.sql.bkmcon_col.index("bkc_title")]
            self.sname = self.oldcon[self.sql.bkmcon_col.index("bkc_sname")]
            self.names = self.oldcon[self.sql.bkmcon_col.index("bkc_names")]
            self.email = self.oldcon[self.sql.bkmcon_col.index("bkc_email")]
            for num, dat in enumerate(self.oldcon[1:-1]):
                self.df.loadEntry("T", 0, num, data=dat)
        else:
            self.newcon = True
        self.acno = w

    def doTitle(self, frt, pag, r, c, p, i, w):
        self.title = w

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        self.names = w

    def doEmail(self, frt, pag, r, c, p, i, w):
        self.email = w

    def doDelete(self):
        chk = self.sql.getRec("bkmmst", cols=["count(*)"],
            where=[("bkm_cono", "=", self.opts["conum"]), ("bkm_ccode",
            "=", self.ccode)], limit=1)
        if chk[0]:
            return "Bookings Exist, Not Deleted"
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.delRec("bkmcon", where=[("bkc_cono", "=", self.opts["conum"]),
            ("bkc_ccode", "=", self.ccode)])
        self.sql.insRec("chglog", data=["bkmcon", "D", "%03i%-7s" %
            (self.opts["conum"], self.ccode), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
            return
        # Create/Update Record
        if self.newcon:
            self.ccode = self.genCode(self.sname)
            self.df.loadEntry("T", 0, 0, data=self.ccode)
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        data = [self.opts["conum"]]
        for x in range(len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.newcon:
            self.sql.insRec("bkmcon", data=data)
        elif data != self.oldcon[:len(data)]:
            col = self.sql.bkmcon_col
            data.append(self.oldcon[col.index("bkc_xflag")])
            self.sql.updRec("bkmcon", data=data, where=[("bkc_cono", "=",
                self.opts["conum"]), ("bkc_ccode", "=", self.ccode)])
            for num, dat in enumerate(self.oldcon):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["bkmcon", "U",
                        "%03i%-7s" % (self.opts["conum"], self.ccode),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doImport(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        fi = FileImport(self.opts["mf"], imptab="bkmcon", impskp=["bkc_cono"])
        sp = ProgressBar(self.opts["mf"].body, typ="Importing Contacts",
            mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            if not line[0]:
                if not line[2]:
                    err = "Blank Code and Blank Surname"
                    break
                chk = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
                    self.opts["conum"]), ("bkc_sname", "=", line[2]),
                    ("bkc_names", "=", line[3])], limit=1)
                if chk:
                    err = "%s: %s %s: %s\n\nAlready Exists" % (fi.impcol[2][0],
                        line[2], fi.impcol[3][0], line[3])
                    break
                for _ in range(1, 100):
                    line[0] = self.genCode(line[2])
                    chk = self.sql.getRec("bkmcon", where=[("bkc_cono",
                        "=", self.opts["conum"]), ("bkc_ccode", "=", line[0])],
                        limit=1)
                    if not chk:
                        break
            else:
                chk = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
                    self.opts["conum"]), ("bkc_ccode", "=", line[0])], limit=1)
                if chk:
                    err = "%s: %s %s: %s\n\nAlready Exists" % (fi.impcol[0][0],
                        line[0], fi.impcol[2][0], line[2])
                    break
            if not line[1]:
                line[1] = "Ms"
            if not line[2]:
                err = "Blank Surname"
                break
            if not line[3]:
                err = "Blank Names"
                break
            line.insert(0, self.opts["conum"])
            self.sql.insRec("bkmcon", data=line)
        sp.closeProgress()
        if err:
            err = "Line %s: %s" % ((num + 1), err)
            showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrint(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        TabPrt(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            name=self.__class__.__name__, tabs="bkmcon",
            where=[("bkc_cono", "=", self.opts["conum"]),
            ("bkc_ccode", "=", self.ccode)])
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def genCode(self, sname):
        # Remove invalid characters
        sname = sname.replace(" ", "")
        for c in (" ", ".", ",", ";", ":", "'", '"'):
            sname = sname.replace(c, "")
        if len(sname) < 5:
            sname = sname + ("0" * (5 - len(sname)))
        ccod1 = ""
        for c in range(0, 5):
            ccod1 = (ccod1 + sname[c]).upper()
        ccod1 = ccod1.strip()
        text = "%s%0" + str((7 - len(ccod1))) + "d"
        for x in range(1, 100):
            ccod2 = text % (ccod1, x)
            chk = self.sql.getRec("bkmcon",
                where=[("bkc_cono", "=", self.opts["conum"]),
                ("bkc_ccode", "=", ccod2)], limit=1)
            if not chk:
                break
        return ccod2

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
