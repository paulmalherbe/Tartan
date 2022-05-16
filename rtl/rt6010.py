"""
SYNOPSIS
    Rentals's Ledger Key Change.

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

from TartanClasses import GetCtl, Sql, TartanDialog

class rt6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.tables = (
            ("ctlnot", "not_key"),
            ("ctlvtf", "vtt_cono", "vtt_acno", "vtt_styp"),
            ("rtlmst", "rtm_cono", "rtm_code", "rtm_acno"),
            ("rtlcon", "rtc_cono", "rtc_code", "rtc_acno"),
            ("rtltrn", "rtt_cono", "rtt_code", "rtt_acno"))
        tabs = ["rtlprm"]
        for tab in self.tables:
            tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        rtlctl = gc.getCtl("rtlctl", self.opts["conum"])
        if not rtlctl:
            return
        return True

    def mainProcess(self):
        prm = {
            "stype": "R",
            "tables": ("rtlprm",),
            "cols": (
                ("rtp_code", "", 0, "Cod"),
                ("rtp_desc", "", 0, "Description", "Y")),
            "where": [("rtp_cono", "=", self.opts["conum"])]}
        rtm = {
            "stype": "R",
            "tables": ("rtlmst",),
            "cols": [
                ("rtm_code", "", 0, "Cod"),
                ("rtm_acno", "", 0, "Acc-Num"),
                ("rtm_name", "", 0, "Name", "Y")],
            "where": [("rtm_cono", "=", self.opts["conum"])],
            "whera": [["T", "rtm_code", 0]],
            "index": 1}
        fld = [
            (("T",0,0,0),"IRW",7,"Old Code","Old Premises Code",
                "","Y",self.doOldCod,prm,None,("notblank",)),
            (("T",0,0,0),"O@rtp_desc",0,""),
            (("T",0,1,0),"IRW",7,"Old Account","Old Account Number",
                "","Y",self.doOldAcc,rtm,None,("notblank",)),
            (("T",0,1,0),"O@rtm_name",0,""),
            (("T",0,2,0),"I@rtp_code",0,"New Code","New Premises Code",
                "","Y",self.doNewCod,prm,None,("notblank",)),
            (("T",0,2,0),"O@rtp_desc",0,""),
            (("T",0,3,0),"I@rtm_acno",0,"New Account","New Account Number",
                "","Y",self.doNewAcc,None,None,("notblank",))]
        tnd = ((self.doProcess,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt)

    def doOldCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlprm", cols=["rtp_desc"],
            where=[("rtp_cono", "=", self.opts["conum"]),
            ("rtp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises Number, Does Not exist"
        self.oldprm = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doOldAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlmst", cols=["rtm_name"],
            where=[("rtm_cono", "=", self.opts["conum"]), ("rtm_code",
            "=", self.oldprm), ("rtm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.oldacc = w
        self.oldnot = "%7s%s" % (self.oldprm, self.oldacc)
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doNewCod(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlprm", cols=["rtp_desc"],
            where=[("rtp_cono", "=", self.opts["conum"]),
            ("rtp_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Premises Number, Does Not exist"
        self.newprm = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doNewAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("rtlmst", where=[("rtm_cono", "=",
            self.opts["conum"]), ("rtm_code", "=", self.newprm), ("rtm_acno",
            "=", w)], limit=1)
        if acc:
            return "Invalid Account Number, Already Exists"
        self.newacc = w
        self.newnot = "%7s%s" % (self.newprm, w)

    def doProcess(self, focus=True):
        for tab in self.tables:
            if tab[0] == "ctlnot":
                whr = [
                    ("not_cono", "=", self.opts["conum"]),
                    ("not_sys", "=", "RTL"),
                    (tab[1], "=", self.oldnot)]
                dat = [self.newnot]
                col = [tab[1]]
            elif tab[0] == "ctlvtf":
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldacc),
                    (tab[3], "=", "R")]
                dat = [self.newacc]
                col = [tab[2]]
            else:
                whr = [
                    (tab[1], "=", self.opts["conum"]),
                    (tab[2], "=", self.oldprm),
                    (tab[3], "=", self.oldacc)]
                dat = [self.newprm, self.newacc]
                col = [tab[2], tab[3]]
            self.sql.updRec(tab[0], where=whr, data=dat, cols=col)
        if focus:
            self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
