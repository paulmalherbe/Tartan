"""
SYNOPSIS
    Rental Interest File Maintenance.

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
from TartanClasses import CCD, FileImport, Sql, TartanDialog
from tartanFunctions import showError

class rcc310(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["rcaint", "chglog"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def drawDialog(self):
        dat = {
            "stype": "R",
            "tables": ("rcaint",),
            "cols": (
                ("rci_date", "", 0, "Date-Chg"),
                ("rci_prime", "", 0, "Prime"),
                ("rci_bankr", "", 0, "BankR"),
                ("rci_admin", "", 0, "Admin")),
            "where": [("rci_cono", "=", self.opts["conum"])],
            "order": "rci_date"}
        self.fld = (
            (("T",0,0,0),"ID1",10,"Date of Change","",
                0,"N",self.doDate,dat,None,("efld",)),
            (("T",0,1,0),"IUD",5.2,"Prime Rate","",
                0,"N",None,None,self.doDelete,("notzero",)),
            (("T",0,2,0),"IUD",5.2,"Bank Rate","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,3,0),"IUD",5.2,"Comm Rate","",
                0,"N",None,None,None,("efld",)))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        but = (("_Import File",None,self.doImport,0,("T", 0, 1),("T", 0, 2),
            "Import a File with the Correct Format i.e. Date, Prime Rate, "\
            "Bank Rate, Fee Rate"),)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tend=tnd, txit=txt, butt=but)

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Interest File Import",)
        fle = {
            "stype":  "F",
            "types":  "fle",
            "ftype":  (("CSV & XLS Files", "*.[c,x][s,l][v,s]"),)}
        r1s = (("Yes", "Y"), ("No", "N"))
        fld = (
            (("T",0,0,0),"IFF",50,"File Name","",
                "","N",self.doImpFle,fle,None,("file",)),
            (("T",0,1,0),("IRB",r1s),0,"Delete Existing","",
                "N","N",self.doImpDel,None,None,None))
        tnd = ((self.doImpEnd,"n"), )
        txt = (self.doImpExit, )
        self.ip = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.ip.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doImpFle(self, frt, pag, r, c, p, i, w):
        self.impfle = w

    def doImpDel(self, frt, pag, r, c, p, i, w):
        self.impdel = w

    def doImpEnd(self):
        self.ip.closeProcess()
        if self.impdel == "Y":
            self.sql.delRec("rcaint", where=[("rci_cono", "=",
                self.opts["conum"])])
        impcol = [
            ["Date", 0, "D1", 10],
            ["Prime Rate", 1, "UD", 5.2],
            ["Bank Rate", 2, "UD", 5.2],
            ["Fee Rate", 3, "UD", 5.2]]
        fi = FileImport(self.opts["mf"], impfle=self.impfle, impcol=impcol)
        err = None
        for num, line in enumerate(fi.impdat):
            if len(line) != len(impcol):
                err = "Line %s: Invalid Number of Fields (S/B %s is %s)" % \
                    (num + 1, len(impcol), len(line))
                break
            date = CCD(line[0], "D1", 10)
            prime = CCD(line[1], "UD", 5.2)
            bank = CCD(line[2], "UD", 5.2)
            fees = CCD(line[3], "UD", 5.2)
            chk = self.sql.getRec("rcaint", where=[("rci_cono", "=",
                self.opts["conum"]), ("rci_date", "=", date.work)])
            if chk:
                err = "Line %s: A Record for Date, %s, Already Exists" % \
                    (num + 1, date.disp)
                break
            self.sql.insRec("rcaint", data=[self.opts["conum"], date.work,
                prime.work, bank.work, fees.work])
        if err:
            showError(self.opts["mf"].body, "Import Error", err)
        else:
            self.opts["mf"].dbm.commitDbase(ask=True,
                mess="Would you like to COMMIT All Imported Interest Rates?")

    def doImpExit(self):
        self.ip.closeProcess()

    def doDate(self, frt, pag, r, c, p, i, w):
        self.date = w
        self.acc = self.sql.getRec("rcaint", where=[("rci_cono", "=",
            self.opts["conum"]), ("rci_date", "=", self.date)], limit=1)
        if self.acc:
            self.new = False
            for n, f in enumerate(self.acc[1:-1]):
                self.df.loadEntry("T", 0, n, data=f)
        else:
            self.new = True

    def doDelete(self):
        self.sql.delRec("rcaint", where=[("rci_cono", "=", self.opts["conum"]),
            ("rci_date", "=", self.date)])
        dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        self.sql.insRec("chglog", data=["rcaint", "D", "%03i%8s" % \
            (self.opts["conum"], self.date), "", dte, self.opts["capnm"],
            "", "", "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        if self.new:
            self.sql.insRec("rcaint", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.rcaint_col
            data.append(self.acc[col.index("rci_xflag")])
            self.sql.updRec("rcaint", data=data, where=[("rci_cono",
                "=", self.opts["conum"]), ("rci_date", "=", self.date)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["rcaint", "U",
                        "%03i%8s" % (self.opts["conum"], self.date),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(data[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
