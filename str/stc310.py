"""
SYNOPSIS
    Product Groups File Maintenance.

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

class stc310(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "genmst", "strmf1",
            "strgrp", "strgmu"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.glint = strctl["cts_glint"]
        self.plevs = strctl["cts_plevs"]
        self.automu = strctl["cts_automu"]
        return True

    def mainProcess(self):
        gpm = {
            "stype": "R",
            "tables": ("strgrp",),
            "cols": (
                ("gpm_group", "", 0, "Grp"),
                ("gpm_desc", "", 0, "Description", "Y")),
            "where": [("gpm_cono", "=", self.opts["conum"])]}
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
        self.fld = [
            (("T",0,0,0),"IUA",3,"Product Group","",
                "","N",self.doGroup,gpm,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),"IUA",1,"Vat Code","",
                "","N",self.doVat,vtm,None,("notblank",))]
        row = 3
        if self.glint == "Y":
            self.fld.append((("T",0,3,0),"IUI",7,"Sales Account","",
                "","N",self.doSales,glm,None,("notzero",)))
            self.fld.append((("T",0,3,0),"ONA",30,""))
            self.fld.append((("T",0,4,0),"IUI",7,"COS Account","",
                "","N",self.doCos,glm,None,("notzero",)))
            self.fld.append((("T",0,4,0),"ONA",30,""))
            row = 5
        if self.automu in ("A", "L"):
            self.fld.append((("T",0,row,0),"IUD",5.1,"Mark-Up    Lv1","",
                "","N",None,None,None,("efld",)))
            if self.plevs > 1:
                for x in range(1, self.plevs):
                    self.fld.append((("T",0,row,0),"IUD",5.1,"Lv%s" % (x+1),"",
                        "","N",None,None,None,("efld",)))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,0)),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,0)))
        tnd = ((self.doEnd,"Y"), )
        txt = (self.doCloseProcess, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w
        self.acc = self.sql.getRec("strgrp", where=[("gpm_cono", "=",
            self.opts["conum"]), ("gpm_group", "=", self.group)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            col = self.sql.strgrp_col
            self.df.loadEntry(frt, pag, p+1,
                    data=self.acc[col.index("gpm_desc")])
            self.df.loadEntry(frt, pag, p+2,
                    data=self.acc[col.index("gpm_vatcode")])
            p = 3
            if self.glint == "Y":
                self.df.loadEntry(frt, pag, p,
                        data=self.acc[col.index("gpm_sales")])
                des = self.getGenDesc(self.acc[col.index("gpm_sales")])
                if not des:
                    self.df.loadEntry(frt, pag, p+1,
                            data="Invalid Sales Code")
                else:
                    self.df.loadEntry(frt, pag, p+1,
                            data=des[0])
                self.df.loadEntry(frt, pag, p+2,
                        data=self.acc[col.index("gpm_costs")])
                des = self.getGenDesc(self.acc[col.index("gpm_costs")])
                if not des:
                    self.df.loadEntry(frt, pag, p+3,
                            data="Invalid Costs Code")
                else:
                    self.df.loadEntry(frt, pag, p+3,
                            data=des[0])
                p = 7
            if self.automu in ("A", "L"):
                for lev in range(self.plevs):
                    mup = self.sql.getRec("strgmu", cols=["smg_markup"],
                        where=[("smg_cono", "=", self.opts["conum"]),
                        ("smg_group", "=", self.group), ("smg_level",
                        "=", lev + 1)], limit=1)
                    if not mup:
                        mup = [0]
                    self.df.loadEntry(frt, pag, p+lev, data=mup[0])

    def doVat(self, frt, pag, r, c, p, i, w):
        vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            w)], limit=1)
        if not vat:
            return "Invalid VAT Code"
        self.code = w

    def doSales(self, frt, pag, r, c, p, i, w):
        acc = self.getGenDesc(w)
        if not acc:
            return "Invalid Sales Code"
        self.sales = w
        self.df.loadEntry("T", 0, 4, data=acc[0])

    def doCos(self, frt, pag, r, c, p, i, w):
        acc = self.getGenDesc(w)
        if not acc:
            return "Invalid COS Code"
        self.cos = w
        self.df.loadEntry("T", 0, 6, data=acc[0])

    def doDelete(self):
        st1 = self.sql.getRec("strmf1", cols=["count(*)"],
            where=[("st1_cono", "=", self.opts["conum"]), ("st1_group", "=",
            self.group)], limit=1)
        if st1[0]:
            return "Records Exist for this Group, Not Deleted"
        self.sql.delRec("strgrp", where=[("gpm_cono", "=", self.opts["conum"]),
            ("gpm_group", "=", self.group)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(0, len(self.df.t_work[0][0])):
            if x == 7:
                break
            if self.glint == "Y":
                # Account Names
                if x in (4, 6):
                    continue
            elif x == 3:
                data.append(0)
                data.append(0)
                break
            data.append(self.df.t_work[0][0][x])
        if self.new == "Y":
            self.sql.insRec("strgrp", data=data)
        elif data != self.acc[:len(data)]:
            col = self.sql.strgrp_col
            data.append(self.acc[col.index("gpm_xflag")])
            self.sql.updRec("strgrp", data=data, where=[("gpm_cono",
                "=", self.opts["conum"]), ("gpm_group", "=", self.group)])
        self.sql.delRec("strgmu", where=[("smg_cono", "=", self.opts["conum"]),
            ("smg_group", "=", self.group)])
        if self.automu in ("A", "L"):
            for lvl, mup in enumerate(self.df.t_work[0][0][x:]):
                if not mup:
                    continue
                self.sql.insRec("strgmu", data=[self.opts["conum"],
                    self.group, lvl + 1, mup])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def getGenDesc(self, acno):
        return self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]), ("glm_acno", "=",
            acno)], limit=1)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doCloseProcess(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
