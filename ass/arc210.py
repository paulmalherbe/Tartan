"""
SYNOPSIS
    Depreciation Methods Maintenance.

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

class arc210(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["assdep", "assgrp", "assmst"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        assctl = gc.getCtl("assctl", self.opts["conum"])
        if not assctl:
            return
        self.glint = assctl["cta_glint"]
        self.rordp = assctl["cta_rordp"]
        return True

    def mainProcess(self):
        cod = {
            "stype": "R",
            "tables": ("assdep",),
            "cols": (
                ("asd_code", "", 0, "Cod"),
                ("asd_desc", "", 0, "Description", "Y")),
            "where": [("asd_cono", "=", self.opts["conum"])],
            "order": "asd_code"}
        r1s = (
            ("Straight Line","S"),
            ("Diminishing Balance","D"))
        fld = [
            (("T",0,0,0),"I@asd_code",0,"","",
                "","N",self.doCode,cod,None,("notblank",)),
            (("T",0,1,0),"I@asd_desc",0,"","",
                "","N",None,None,self.doDelete,("notblank",)),
            (("T",0,2,0),("IRB",r1s),0,"Type","",
                "S","N",self.doDepTyp,None,None,None)]
        if self.rordp == "Y":
            fld.append(
            (("T",0,3,0),("IRB",r1s),0,"Receiver Type","Receiver Type",
                "S","N",self.doRecTyp,None,None,None))
        fld.append(
            (("C",0,0,0),"IUD",12.2,"Company-Rate","Company Rate",
                "","N",self.doCoyRte,None,None,("efld",),("Period",7)))
        if self.rordp == "Y":
            fld.append(
            (("C",0,0,1),"IUD",12.2,"Receiver-Rate","Receiver Rate",
                "","N",self.doRecRte,None,None,("efld",)))
        but = (("Cancel",None,self.doCancel,0,("T",0,2),("T",0,1)),)
        tnd = ((self.doEnd,"n"), )
        txt = (self.doExit, )
        cnd = ((self.doEnd,"n"), )
        cxt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt, cend=cnd, cxit=cxt)
        for x in range(7):
            self.df.colLabel[0][x].configure(text="Year %s" % (x + 1))

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        self.acc = self.sql.getRec("assdep", where=[("asd_cono", "=",
            self.opts["conum"]), ("asd_code", "=", self.code)], limit=1)
        if not self.acc:
            self.new = "Y"
        else:
            self.new = "N"
            for x in range(self.df.topq[pag]):
                self.df.loadEntry("T", 0, x, data=self.acc[x+1])
            if self.rordp == "Y":
                inc = 1
            else:
                x += 1
                inc = 2
            for y in range(0, 14, inc):
                self.df.loadEntry("C", 0, int(y / inc), data=self.acc[x+y+2])

    def doDepTyp(self, frt, pag, r, c, p, i, w):
        self.ctyp = w

    def doRecTyp(self, frt, pag, r, c, p, i, w):
        self.rtyp = w

    def doCoyRte(self, frt, pag, r, c, p, i, w):
        if self.ctyp == "D" or not w:
            self.df.colf[pag][0][1] = "OUD"
            return
        if w and p != 0 and not self.df.c_work[0][r - 1][i]:
            return "Value Not Allowed after a Zero"

    def doRecRte(self, frt, pag, r, c, p, i, w):
        if self.rtyp == "D" or not w:
            self.df.colf[pag][1][1] = "OUD"
            return
        if w and p != 1 and not self.df.c_work[0][r - 1][i]:
            return "Value Not Allowed"

    def doDelete(self):
        ck1 = self.sql.getRec("assgrp", where=[("asg_cono", "=",
            self.opts["conum"]), ("asg_depcod", "=", self.code)])
        ck2 = self.sql.getRec("assmst", where=[("asm_cono", "=",
            self.opts["conum"]), ("asm_depcod", "=", self.code)])
        if ck1 or ck2:
            return "Code in Use, Not Deleted"
        self.sql.delRec("assdep", where=[("asd_cono", "=", self.opts["conum"]),
            ("asd_code", "=", self.df.t_work[0][0][0])])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        if self.df.frt == "T":
            self.df.focusField("C", 0, 1)
        elif self.df.col != len(self.df.colEntry[0]):
            self.df.focusField(self.df.frt, self.df.pag, self.df.col + 1)
        else:
            self.df.colf[0][0][1] = "IUD"
            if self.rordp == "Y":
                self.df.colf[0][1][1] = "IUD"
            if self.df.entryConfirm("", dflt="y") == "y":
                data = [self.opts["conum"]]
                for x in range(0, len(self.df.t_work[0][0])):
                    data.append(self.df.t_work[0][0][x])
                if self.rordp == "N":
                    data.append("N")
                for x in range(0, len(self.df.c_work[0])):
                    data.extend(self.df.c_work[0][x])
                    if self.rordp == "N":
                        data.append(0)
                if self.new == "Y":
                    self.sql.insRec("assdep", data=data)
                elif data != self.acc[:len(data)]:
                    col = self.sql.assdep_col
                    data.append(self.acc[col.index("asd_xflag")])
                    self.sql.updRec("assdep", data=data, where=[("asd_cono",
                        "=", self.opts["conum"]), ("asd_code", "=", self.code)])
                self.opts["mf"].dbm.commitDbase()
                self.df.focusField("T", 0, 1)
            else:
                self.df.focusField("C", 0, 1)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doExit(self):
        if self.df.frt == "T":
            self.df.closeProcess()
            self.opts["mf"].closeLoop()
        elif self.df.col == 1:
            self.doCancel()
        else:
            data = self.df.c_work[0][self.df.row][self.df.idx]
            self.df.loadEntry("C", 0, self.df.pos, data=data)
            self.df.focusField("C", 0, self.df.pos)

# vim:set ts=4 sw=4 sts=4 expandtab:
