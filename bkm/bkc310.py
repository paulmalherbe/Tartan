"""
SYNOPSIS
    Bookings Unit File Maintenance.

    This file is part of Tartan Systems (TARTAN).

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2023 Paul Malherbe.

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

class bkc310(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.glint = bkmctl["cbk_glint"]
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "genmst", "bkmmst",
            "bkmunm", "bkmrtm", "bkmrtt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def drawDialog(self):
        unm = {
            "stype": "R",
            "tables": ("bkmunm",),
            "cols": [
                ("bum_code", "", 0, "Code"),
                ("bum_desc", "", 0, "Description"),
                ("bum_room", "", 0, "Rms"),
                ("bum_maxg", "", 0, "Qty"),
                ("bum_dflt", "", 0, "Rte")],
            "where": [
                ("bum_cono", "=", self.opts["conum"])],
            "whera": (("T", "bum_btyp", 0, 0),),
            "order": "bum_btyp, bum_code"}
        if self.glint == "Y":
            unm["cols"].append(("bum_slsa", "", 0, "Acc-Num"))
        rte = {
            "stype": "R",
            "tables": ("bkmrtm",),
            "cols": (
                ("brm_code", "", 0, "Cod"),
                ("brm_desc", "", 0, "Description"),
                ("brm_base", "", 0, "B")),
            "where": [],
            "order": "brm_type, brm_code"}
        vtm = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        r1s = (("Accomodation","A"), ("Other","O"))
        self.fld = [
            (("T",0,0,0),("IRB",r1s),0,"Booking Type","",
                "A","N",self.doBtype,None,None,None),
            (("T",0,1,0),"IUA",6,"Unit Code","",
                "","N",self.doUcode,unm,None,("notblank",)),
            (("T",0,2,0),"ITX",30,"Description","",
                "","N",self.doUDesc,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"IUI",3,"Number of Rooms","",
                0,"N",self.doURooms,None,None,("efld",)),
            (("T",0,4,0),"IUI",3,"Total Capacity","",
                0,"N",None,None,None,("notzero",)),
            (("T",0,5,0),"IUI",3,"Default Rate","",
                0,"N",self.doUrate,rte,None,("notzero",)),
            (("T",0,6,0),"IUA",1,"V.A.T. Code","",
                self.taxdf,"N",self.doVat,vtm,None,("notblank",))]
        if self.glint == "Y":
            self.fld.extend([
                (("T",0,7,0),"IUI",7,"Sales Account","",
                    "","N",self.doSales,glm,None,("notzero",)),
                (("T",0,7,0),"ONA",30,"")])
        but = (("Quit",None,self.doExit,1,None,None),)
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doBtype(self, frt, pag, r, c, p, i, w):
        self.btyp = w
        self.df.topf[0][5][8]["where"] = [
            ("brm_cono", "=", self.opts["conum"]),
            ("brm_type", "=", self.btyp)]

    def doUcode(self, frt, pag, r, c, p, i, w):
        self.ucod = w
        self.unm = self.sql.getRec("bkmunm", where=[("bum_cono",
            "=", self.opts["conum"]), ("bum_btyp", "=", self.btyp),
            ("bum_code", "=", self.ucod)], limit=1)
        if not self.unm:
            self.new = True
        else:
            self.new = False
            des = self.unm[self.sql.bkmunm_col.index("bum_desc")]
            rms = self.unm[self.sql.bkmunm_col.index("bum_room")]
            qty = self.unm[self.sql.bkmunm_col.index("bum_maxg")]
            vcd = self.unm[self.sql.bkmunm_col.index("bum_vatc")]
            dfr = self.unm[self.sql.bkmunm_col.index("bum_dflt")]
            sls = self.unm[self.sql.bkmunm_col.index("bum_slsa")]
            self.df.loadEntry(frt, pag, p+1, data=des)
            self.df.loadEntry(frt, pag, p+2, data=rms)
            self.df.loadEntry(frt, pag, p+3, data=qty)
            self.df.loadEntry(frt, pag, p+4, data=dfr)
            self.df.loadEntry(frt, pag, p+5, data=vcd)
            if self.glint == "Y":
                self.df.loadEntry(frt, pag, p+6,data=sls)
                des = self.getGenDesc(sls)
                if not des:
                    self.df.loadEntry(frt,pag,p+7,data="Invalid Sales Code")
                else:
                    self.df.loadEntry(frt,pag,p+7,data=des[0])

    def doUDesc(self, frt, pag, r, c, p, i, w):
        self.udes = w
        if self.btyp == "O":
            self.urms = 0
            self.df.loadEntry(frt, pag, p+1, data=self.urms)
            return "sk1"

    def doURooms(self, frt, pag, r, c, p, i, w):
        if self.btyp == "A" and not w:
            return "Invalid Number of Rooms"
        self.urms = w

    def doUrate(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("bkmrtm", where=[("brm_cono", "=",
            self.opts["conum"]), ("brm_type", "=", self.btyp),
            ("brm_code", "=", w)], limit=1)
        if not acc:
            return "Invalid Rate Code"

    def doVat(self, frt, pag, r, c, p, i, w):
        vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            w)], limit=1)
        if not vat:
            return "Invalid VAT Code"

    def doSales(self, frt, pag, r, c, p, i, w):
        acc = self.getGenDesc(w)
        if not acc:
            return "Invalid Sales Code"
        self.sales = w
        self.df.loadEntry("T", 0, p+1, data=acc[0])

    def getGenDesc(self, acno):
        return self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", acno)], limit=1)

    def doDelete(self):
        chk = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_utype", "=", self.btyp), ("brt_ucode",
            "=", self.ucod)])
        if chk:
            return "Unit Used, Not Deleted"
        self.sql.delRec("bkmunm", where=[("bum_cono", "=", self.opts["conum"]),
            ("bum_btyp", "=", self.btyp), ("bum_code", "=", self.ucod)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if self.glint == "Y" and x == 8:
                continue
            data.append(self.df.t_work[0][0][x])
        if self.glint == "N":
            data.append(0)
        if self.new:
            self.sql.insRec("bkmunm", data=data)
        elif data != self.unm[:len(data)]:
            col = self.sql.bkmunm_col
            data.append(self.unm[col.index("bum_xflag")])
            self.sql.updRec("bkmunm", data=data, where=[("bum_cono", "=",
                self.opts["conum"]), ("bum_btyp", "=", self.btyp),
                ("bum_code", "=", self.ucod)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
