"""
SYNOPSIS
    Bookings Rate Records Maintenance.

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

from TartanClasses import Sql, TartanDialog

class bkc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bkmrtm", "bkmrtr", "bkmrtt"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def drawDialog(self):
        brm = {
            "stype": "R",
            "tables": ("bkmrtm",),
            "cols": (
                ("brm_code", "", 0, "Code"),
                ("brm_desc", "", 0, "Description"),
                ("brm_base", "", 0, "B")),
            "where": [("brm_cono", "=", self.opts["conum"])],
            "whera": [("T", "brm_type", 0, 0)],
            "order": "brm_code"}
        brr = {
            "stype": "R",
            "tables": ("bkmrtr",),
            "cols": (
                ("brr_date", "", 0, "Start-Date"),
                ("brr_rate", "", 0, "Rte-Amount")),
            "where": [("brr_cono", "=", self.opts["conum"])],
            "whera": [("T", "brr_type", 0, 0), ("T", "brr_code", 1, 0)],
            "order": "brr_date"}
        r1s = (
            ("Accomodation","A"),
            ("Other","O"))
        r2s = (
            ("/Unit/Person/Day","A"),
            ("/Unit/Person","B"),
            ("/Unit/Day","C"),
            ("/Unit","D"))
        self.fld = (
            (("T",0,0,0),("IRB",r1s),0,"Unit Type","",
                "A","Y",self.doType,None,None,None),
            (("T",0,1,0),"IUI",3,"Code","",
                "","N",self.doCode,brm,None,None),
            (("T",0,2,0),"ITX",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,3,0),("IRB",r2s),0,"Rate Base","",
                "A","N",self.doBase,None,None,None),
            (("T",0,4,0),"Id1",10.2,"Starting Date","",
                0,"N",self.doExpd,brr,None,("efld",)),
            (("T",0,5,0),"IUD",10.2,"Rate Amount","",
                0,"N",self.doRate,None,self.doDelete,("efld",)))
        but = (("Quit",None,self.doExit,1,None,None),)
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doType(self, frt, pag, r, c, p, i, w):
        self.rtype = w

    def doCode(self, frt, pag, r, c, p, i, w):
        if not w:
            acc = self.sql.getRec("bkmrtm", cols=["max(brm_code)"],
                where=[("brm_cono", "=", self.opts["conum"]), ("brm_type",
                "=", self.rtype)], limit=1)
            if not acc[0]:
                w = 1
            else:
                w = acc[0] + 1
            self.df.loadEntry(frt, pag, p, data=w)
        self.rcode = w
        self.rtm = self.sql.getRec("bkmrtm", where=[("brm_cono", "=",
            self.opts["conum"]), ("brm_type", "=", self.rtype), ("brm_code",
            "=", self.rcode)], limit=1)
        if not self.rtm:
            self.newr = True
        else:
            self.newr = False
            for num, dat in enumerate(self.rtm[3:-1]):
                self.df.loadEntry(frt, pag, p+num+1, data=dat)

    def doBase(self, frt, pag, r, c, p, i, w):
        self.rbase = w

    def doExpd(self, frt, pag, r, c, p, i, w):
        self.newx = True
        if not self.newr:
            self.rtr = self.sql.getRec("bkmrtr", where=[("brr_cono",
                "=", self.opts["conum"]), ("brr_type", "=", self.rtype),
                ("brr_code", "=", self.rcode), ("brr_date", "=", w)], limit=1)
            if self.rtr:
                self.newx = False
                rate = self.rtr[self.sql.bkmrtr_col.index("brr_rate")]
                self.df.loadEntry(frt, pag, p+1, data=rate)
        self.date = w

    def doRate(self, frt, pag, r, c, p, i, w):
        self.rate = w

    def doDelete(self):
        if self.df.col == 6:
            self.sql.delRec("bkmrtr", where=[("brr_cono", "=",
                self.opts["conum"]), ("brr_type", "=", self.rtype),
                ("brr_code", "=", self.rcode), ("brr_date", "=", self.date)])
            return
        chk = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_utype", "=", self.rtype), ("brt_rcode",
            "=", self.rcode)])
        if not chk:
            # Rate has been used, do not delete master record only rates
            self.sql.delRec("bkmrtm", where=[("brm_cono", "=",
                self.opts["conum"]), ("brm_type", "=", self.rtype),
                ("brm_code", "=", self.rcode)])
        self.sql.delRec("bkmrtr", where=[("brr_cono", "=", self.opts["conum"]),
            ("brr_type", "=", self.rtype), ("brr_code", "=", self.rcode)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        data.extend(self.df.t_work[0][0][:4])
        if self.newr:
            self.sql.insRec("bkmrtm", data=data)
        elif data != self.rtm[:len(data)]:
            col = self.sql.bkmrtm_col
            data.append(self.rtm[col.index("brm_xflag")])
            self.sql.updRec("bkmrtm", data=data, where=[("brm_cono", "=",
                self.opts["conum"]), ("brm_type", "=", self.rtype),
                ("brm_code", "=", self.rcode)])
        data = [self.opts["conum"]]
        data.extend(self.df.t_work[0][0][:2])
        data.extend(self.df.t_work[0][0][4:6])
        if self.newx:
            self.sql.insRec("bkmrtr", data=data)
        elif data != self.rtr[:len(data)]:
            col = self.sql.bkmrtr_col
            data.append(self.rtr[col.index("brr_xflag")])
            self.sql.updRec("bkmrtr", data=data, where=[("brr_cono",
                "=", self.opts["conum"]), ("brr_type", "=", self.rtype),
                ("brr_code", "=", self.rcode), ("brr_date", "=", self.date)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
