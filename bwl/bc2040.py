"""
SYNOPSIS
    Bowls Competition Entry Forms.

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

from TartanClasses import GetCtl, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, getNextCode, showError

class bc2040(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["bwlcmp", "bwltab",
            "bwlent", "bwltyp", "bwlgme"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.nstart = bwlctl["ctb_nstart"]
        self.dbase = bwlctl["ctb_dbase"]
        return True

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("bwlcmp",),
            "cols": (
                ("bcm_code", "", 0, "Cod"),
                ("bcm_name", "", 0, "Name", "Y"),
                ("bcm_date", "", 0, "Date")),
            "where": [("bcm_cono", "=", self.opts["conum"])]}
        typ = {
            "stype": "R",
            "tables": ("bwltyp",),
            "cols": (
                ("bct_code", "", 0, "Cod"),
                ("bct_desc", "", 0, "Description", "Y")),
            "where": [("bct_cono", "=", self.opts["conum"])]}
        sk1 = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": (
                ("btb_tab", "", 0, "Cod"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names")),
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname"}
        sk2 = {
            "stype": "R",
            "tables": ("bwlent", "bwltab"),
            "cols": (
                ("btb_tab", "", 0, "Cod"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names"),
                ("bce_tcod", "", 0, "T"),
                ("bce_paid", "", 0, "P")),
            "where": [
                ("btb_cono", "=", self.opts["conum"]),
                ("btb_tab=bce_scod",)],
            "whera": [("T", "bce_ccod", 0, 0)],
            "order": "btb_surname"}
        fld = (
            (("T",0,0,0),"I@bcm_code",0,"Code","Competition Code",
                "","Y",self.doCmpCod,com,None,("efld",)),
            (("T",0,0,0),"I@bcm_name",0,"Name","",
                "","N",self.doCmpNam,None,self.doDelCmp,("notblank",)),
            (("T",0,0,0),"I@bcm_date",0,"Date","",
                "","N",None,None,None,("efld",)),
            (("T",0,0,0),"I@bcm_type",0,"Type","",
                "","N",self.doCmpTyp,typ,None,("efld",)),
            (("C",0,0,0),"I@btb_tab",0,"P-Code","Player's Code",
                "","Y",self.doSkpCod,sk1,None,("efld",)),
            (("C",0,0,1),"ONA",30,"Name","",
                "","N",None,None,None,("notblank",)),
            (("C",0,0,2),"I@bce_tcod",0,"T","Team Code (H or V)",
                "H","n",self.doTeam,None,None,("in", ("H","V"))),
            (("C",0,0,4),"I@bce_paid",0,"","Paid Flag (Y or N)",
                "N","N",self.doPaid,None,self.doDelSkp,("in", ("Y","N"))))
        but = (("Entered Players",sk2,None,0,("C",0,1),("T",0,1)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"n"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        self.erase = False
        self.skips = []
        if not w:
            self.ccod = getNextCode(self.sql, "bwlcmp", "bcm_code",
                where=[("bcm_cono", "=", self.opts["conum"])], last=999)
            self.df.loadEntry(frt, pag, p, data=self.ccod)
        else:
            self.ccod = w
        self.cmp = self.sql.getRec("bwlcmp", where=[("bcm_cono", "=",
            self.opts["conum"]), ("bcm_code", "=", self.ccod)], limit=1)
        if not self.cmp:
            ok = askQuestion(self.opts["mf"].body, head="New Competition",
                mess="Is This a New Competition?", default="no")
            if ok == "no":
                return "rf"
            self.newcmp = True
        else:
            if self.cmp[self.sql.bwlcmp_col.index("bcm_poff")]:
                showError(self.opts["mf"].body, "Complete",
                    "This Sectional Competition Has Been Completed.")
                return "rf"
            gme = self.sql.getRec("bwlgme", cols=["count(*)"],
                where=[("bcg_cono", "=", self.opts["conum"]), ("bcg_ccod", "=",
                self.ccod), ("bcg_ocod", "<>", 0)], limit=1)
            if gme[0]:
                ok = askQuestion(self.opts["mf"].body, "Error",
                    """This Competition Has Already Been Drawn.

Do You Want to Erase All Draws and Results?""", default="no")
                if ok == "no":
                    return "rf"
                self.erase = True
            self.newcmp = False
            for num, fld in enumerate(self.cmp[1:-2]):
                self.df.loadEntry(frt, pag, p+num, data=fld)
            ent = self.sql.getRec("bwlent", cols=["bce_scod"],
                where=[("bce_cono", "=", self.opts["conum"]),
                ("bce_ccod", "=", self.ccod)])
            for e in ent:
                self.skips.append(e[0])

    def doDelCmp(self):
        if self.newcmp:
            showError(self.opts["mf"].body, "Delete", "New Competition")
            return
        if self.skips:
            ok = askQuestion(self.opts["mf"].body, "Delete", "Entries Exist "\
                "for this Competition, Are You Sure it must be Deleted?",
                default="no")
            if ok == "no":
                return
        self.sql.delRec("bwlcmp", where=[("bcm_cono", "=", self.opts["conum"]),
            ("bcm_code", "=", self.ccod)])
        if self.skips:
            self.sql.delRec("bwlent", where=[("bce_cono",
                "=", self.opts["conum"]), ("bce_ccod", "=", self.ccod)])
            self.sql.delRec("bwlgme", where=[("bcg_cono",
                "=", self.opts["conum"]), ("bcg_ccod", "=", self.ccod)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doCmpNam(self, frt, pag, r, c, p, i, w):
        self.cmpnam = w

    def doCmpTyp(self, frt, pag, r, c, p, i, w):
        if not w:
            ok = askQuestion(self.opts["mf"].body, head="New Type",
                mess="Is This a New Competition Type?")
            if ok == "yes":
                w = getNextCode(self.sql, "bwltyp", "bct_code",
                    where=[("bct_cono", "=", self.opts["conum"])], last=99)
                w = callModule(self.opts["mf"], self.df, "bc1040",
                    coy=(self.opts["conum"], self.opts["conam"]), args=w,
                    ret="ctype")
                self.df.loadEntry(frt, pag, p, data=w)
        self.typ = self.sql.getRec("bwltyp", where=[("bct_cono", "=",
            self.opts["conum"]), ("bct_code", "=", w)], limit=1)
        if not self.typ:
            return "Invalid Competition Type"
        self.cfmat = self.typ[self.sql.bwltyp_col.index("bct_cfmat")]
        self.tsize = self.typ[self.sql.bwltyp_col.index("bct_tsize")]

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        if not w:
            ok = askQuestion(self.opts["mf"].body, head="New Non-Member",
                mess="Is This a New Non-Member Player?", default="yes")
            if ok == "no":
                return "Invalid Skip Code"
            cod = self.doNewCode()
            if not cod:
                return "Invalid Skip Code"
            self.df.loadEntry(frt, pag, p, data=cod)
        else:
            cod = w
        if cod not in self.skips:
            self.skips.append(cod)
        self.scod = cod
        chk = self.sql.getRec("bwltab", cols=["btb_surname",
            "btb_names"], where=[("btb_cono", "=", self.opts["conum"]),
            ("btb_tab", "=", self.scod)], limit=1)
        if not chk:
            return "Invalid Player Code"
        self.df.loadEntry(frt, pag, p+1, data=self.getName(chk))
        ent = self.sql.getRec("bwlent", cols=["bce_tcod",
            "bce_paid"], where=[("bce_cono", "=", self.opts["conum"]),
            ("bce_ccod", "=", self.ccod), ("bce_scod", "=", self.scod)],
            limit=1)
        if ent:
            self.newent = False
            self.df.loadEntry(frt, pag, p+2, data=ent[0])
            self.df.loadEntry(frt, pag, p+3, data=ent[1])
        else:
            self.newent = True
        if self.cfmat == "X":
            if self.scod < self.nstart:
                self.tcod = "H"
            else:
                self.tcod = "V"
            self.df.loadEntry(frt, pag, p+2, data=self.tcod)
        else:
            self.tcod = ""
            return "sk2"

    def doTeam(self, frt, pag, r, c, p, i, w):
        self.tcod = w

    def doNewCode(self):
        r1s = (("Male","M"), ("Female","F"))
        r2s = (("Skip",4), ("Third",3), ("Second",2), ("Lead",1))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Gender","",
                "M","Y",None,None,None,None),
            (("T",0,1,0),"I@btb_surname",0,"","",
                "","Y",None,None,None,("notblank",)),
            (("T",0,2,0),"I@btb_names",0,"","",
                "","Y",None,None,None,("notblank",)),
            (("T",0,3,0),"I@btb_home",0,"","",
                "","Y",None,None,None,("efld",)),
            (("T",0,4,0),"I@btb_work",0,"","",
                "","Y",None,None,None,("efld",)),
            (("T",0,5,0),"I@btb_cell",0,"","",
                "","Y",None,None,None,("efld",)),
            (("T",0,6,0),"I@btb_mail",0,"","",
                "","Y",self.doNMail,None,None,("efld",)),
            (("T",0,7,0),("IRB",r2s),0,"Position","",
                4,"Y",self.doNPos,None,None,None),
            (("T",0,8,0),"I@btb_rate1",0,"Rating","",
                "","Y",None,None,None,("efld",)))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.new = TartanDialog(self.opts["mf"], eflds=fld,
            tend=((self.doNEnd,"y"),), txit=(self.doNExit,))
        self.new.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state)
        return self.newcod

    def doNMail(self, frt, pag, r, c, p, i, w):
        if self.cfmat in ("T", "K", "R", "X"):
            if self.dbase in ("C", "P"):
                self.new.loadEntry(frt, pag, p+1, data=4)
            else:
                self.new.loadEntry(frt, pag, p+1, data=0)
            if self.dbase in ("C", "R"):
                self.new.loadEntry(frt, pag, p+2, data=5)
            else:
                self.new.loadEntry(frt, pag, p+2, data=0)
            return "sk2"
        if self.dbase == "R":
            self.new.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doNPos(self, frt, pag, r, c, p, i, w):
        if self.dbase == "P":
            self.new.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doNEnd(self):
        self.new.closeProcess()
        self.newcod = getNextCode(self.sql, "bwltab", "btb_tab",
            where=[("btb_cono", "=", self.opts["conum"])],
            start=self.nstart, last=900000)
        data = [self.opts["conum"], self.newcod, 0]
        data.extend(self.new.t_work[0][0][1:3])
        data.extend([self.new.t_work[0][0][0], "", "", "", ""])
        data.extend(self.new.t_work[0][0][3:])
        data.extend(self.new.t_work[0][0][7:])
        data.append(0)
        self.sql.insRec("bwltab", data=data)

    def doNExit(self):
        self.new.closeProcess()
        self.newcod = None

    def getName(self, chk):
        name = chk[0]
        if chk[1]:
            name += ","
            for i in chk[1].split():
                name = "%s %s" % (name, i)
        return name.upper()

    def doPaid(self, frt, pag, r, c, p, i, w):
        self.paid = w

    def doDelSkp(self):
        self.sql.delRec("bwlent", where=[("bce_cono", "=",
            self.opts["conum"]), ("bce_ccod", "=", self.ccod),
            ("bce_scod", "=", self.scod)])
        self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
            self.opts["conum"]), ("bcg_ccod", "=", self.ccod),
            ("bcg_scod", "=", self.scod)])
        self.loadButton()

    def doEnd(self):
        if self.df.frt == "T":
            data = [self.opts["conum"]] + self.df.t_work[0][0] + [0]
            if self.newcmp:
                self.sql.insRec("bwlcmp", data=data)
            else:
                if self.erase:
                    self.sql.delRec("bwlgme", where=[("bcg_cono", "=",
                        self.opts["conum"]), ("bcg_ccod", "=", self.ccod)])
                    if self.cfmat in ("D", "K"):
                        self.sql.delRec("bwltms", where=[("btd_cono", "=",
                            self.opts["conum"]), ("btd_ccod", "=", self.ccod)])
                        self.sql.delRec("bwlrnd", where=[("bcr_cono", "=",
                            self.opts["conum"]), ("bcr_ccod", "=", self.ccod)])
                    if self.cfmat in ("T", "X"):
                        recs = self.sql.getRec("bwlent",
                            cols=["bce_scod"], where=[("bce_cono",
                            "=", self.opts["conum"]), ("bce_ccod",
                            "=", self.ccod)], order="bce_scod")
                        skips = []
                        for rec in recs:
                            skips.append(rec[0])
                        self.doPopulate(skips)
                data.append(self.cmp[self.sql.bwlcmp_col.index("bcm_xflag")])
                self.sql.updRec("bwlcmp", data=data, where=[("bcm_cono", "=",
                    self.opts["conum"]), ("bcm_code", "=", self.ccod)])
            self.loadButton()
            self.df.focusField("C", 0, 1)
        else:
            if self.newent:
                self.sql.insRec("bwlent", data=[self.opts["conum"], self.ccod,
                    self.scod, self.tcod, self.paid])
                if self.cfmat in ("T", "X"):
                    self.doPopulate([self.scod])
            else:
                self.sql.updRec("bwlent", cols=["bce_tcod", "bce_paid"],
                    data=[self.tcod, self.paid], where=[("bce_cono", "=",
                    self.opts["conum"]), ("bce_ccod", "=", self.ccod),
                    ("bce_scod", "=", self.scod)])
            self.loadButton()
            self.df.advanceLine(0)

    def doPopulate(self, scods):
        # Populate bwlgme records
        num = self.typ[self.sql.bwltyp_col.index("bct_games")]
        dgm = self.typ[self.sql.bwltyp_col.index("bct_drawn")]
        for scod in scods:
            data = [self.opts["conum"], self.ccod, scod, 0, "",
                0, 0, "", 0, 0, 0, 0, 0, 0, 0, "", 0, 0]
            for x in range(0, dgm):
                data[3] = x + 1
                data[4] = "D"
                self.sql.insRec("bwlgme", data=data)
            for x in range(dgm, num):
                data[3] = x + 1
                data[4] = "S"
                self.sql.insRec("bwlgme", data=data)

    def loadButton(self):
        rec = self.sql.getRec("bwlent", cols=["count(*)"],
            where=[("bce_cono", "=", self.opts["conum"]), ("bce_ccod", "=",
            self.ccod)], limit=1)
        self.df.B0.setLabel("Entered Players (%s)" % int(rec[0]), udl=0)

    def doExit(self):
        if self.df.frt == "C":
            self.opts["mf"].dbm.commitDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
