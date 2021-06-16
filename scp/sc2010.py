"""
SYNOPSIS
    District Competition Entries.

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

import os
from TartanClasses import RepPrt, ShowImage, Sql, TartanDialog
from tartanFunctions import askQuestion, callModule, getNextCode

class sc2010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["scpcmp", "scpmem", "scpclb",
            "scpsec", "scprnd", "scpent", "scpgme"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.img = None
        self.newent = False
        return True

    def mainProcess(self):
        com = {
            "stype": "R",
            "tables": ("scpcmp",),
            "cols": (
                ("scp_ccod", "", 0, "Cod"),
                ("scp_name", "", 0, "Name", "Y"),
                ("scp_tsiz", "", 0, "S"),
                ("scp_fmat", "", 0, "F")),
            "where": [("scp_cono", "=", self.opts["conum"])]}
        fmt = {
            "stype": "C",
            "titl": "Select the Required Format",
            "head": ("C", "Format"),
            "data": [
                ("R", "Round Robin"),
                ("K", "Knockout")]}
        log = {
            "stype": "F",
            "types": "fle",
            "ftype": (("Image", "*"),)}
        sk1 = {
            "stype": "R",
            "tables": ("scpmem",),
            "cols": (
                ("scm_scod", "", 0, "Cod"),
                ("scm_surname", "", 0, "Surname", "Y"),
                ("scm_names", "", 0, "Names")),
            "where": [("scm_cono", "=", self.opts["conum"])],
            "order": "scm_surname"}
        sk2 = {
            "stype": "R",
            "tables": ("scpent", "scpmem"),
            "cols": (
                ("scm_scod", "", 0, "Cod"),
                ("scm_surname", "", 0, "Surname", "Y"),
                ("scm_names", "", 0, "Names")),
            "where": [
                ("scm_cono", "=", self.opts["conum"]),
                ("scm_scod=sce_scod",)],
            "whera": [("T", "sce_ccod", 0, 0)],
            "order": "scm_surname",
            "butt": [
                ("Delete", self.doDelete, True),
                ("Print All", self.doPrint)]}
        r1s = (("Male","M"), ("Female","F"), ("Both","B"))
        r2s = (("Fours","4"), ("Trips","3"), ("Pairs","2"), ("Singles","1"))
        r3s = (("Knockout","K"), ("Round-Robin","R"))
        fld = (
            (("T",0,0,0),"I@scp_ccod",0,"Code","Competition Code",
                "","Y",self.doCmpCod,com,None,("efld",)),
            (("T",0,0,0),"I@scp_name",0,"Name","Competition Name",
                "","N",self.doCmpNam,None,None,("notblank",)),
            (("T",0,1,0),("IRB",r1s),0,"Gender","",
                "M","N",self.doCmpSex,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Team Size","",
                "4","N",self.doCmpSiz,None,None,None),
            (("T",0,3,0),("IRB",r3s),0,"Format","",
                "K","N",self.doCmpTyp,fmt,None,None),
            (("T",0,4,0),"I@scp_logo",0,"Logo","Sponsor's Logo",
                "","N",self.doCmpLogo,log,None,("fle","blank")),
            (("C",0,0,0),"I@scm_scod",0,"Skip  ","",
                "","Y",self.doSkpCod,sk1,None,("efld",)),
            (("C",0,0,1),"ONA",30,"Name"),
            (("C",0,0,2),"I@scm_scod",0,"Lead  ","",
                "","n",self.doSkpCod,sk1,None,("efld",)),
            (("C",0,0,3),"ONA",30,"Name"))
        but = (("Entered Players",sk2,None,0,("C",0,1),("T",0,1)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        cnd = ((self.doEnd,"n"),)
        cxt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doCmpCod(self, frt, pag, r, c, p, i, w):
        self.skips = []
        self.parts = []
        nxtcod = getNextCode(self.sql, "scpcmp", "scp_ccod",
            where=[("scp_cono", "=", self.opts["conum"])], last=999)
        if not w or w > nxtcod:
            self.ccod = nxtcod
            self.df.loadEntry(frt, pag, p, data=self.ccod)
        else:
            self.ccod = w
        self.old = self.sql.getRec("scpcmp", where=[("scp_cono", "=",
            self.opts["conum"]), ("scp_ccod", "=", self.ccod)], limit=1)
        if not self.old:
            ok = askQuestion(self.opts["mf"].body, head="New Competition",
                mess="Is This a New Competition?", default="no")
            if ok == "no":
                return "rf"
            self.newcmp = True
        else:
            state = self.old[self.sql.scpcmp_col.index("scp_state")]
            if state > 1:
                return "This Competition Has Already Started"
            if state == 1:
                ok = askQuestion(self.opts["mf"].window, "Already Drawn",
                    """This Competition Has Already Been Drawn.

Do You Want to Modify and Redraw It?""", default="no")
                if ok == "no":
                    return "rf"
                self.sql.updRec("scpcmp", cols=["scp_state"], data=[0],
                    where=[("scp_cono", "=", self.opts["conum"]), ("scp_ccod",
                    "=", self.ccod)])
                self.sql.delRec("scpgme", where=[("scg_cono", "=",
                    self.opts["conum"]), ("scg_ccod", "=", self.ccod)])
                self.sql.delRec("scprnd", where=[("scr_cono", "=",
                    self.opts["conum"]), ("scr_ccod", "=", self.ccod)])
                self.sql.delRec("scpsec", where=[("scs_cono", "=",
                    self.opts["conum"]), ("scs_ccod", "=", self.ccod)])
            self.newcmp = False
            self.cmpnam = self.old[self.sql.scpcmp_col.index("scp_name")]
            self.tsex = self.old[self.sql.scpcmp_col.index("scp_tsex")]
            self.tsiz = self.old[self.sql.scpcmp_col.index("scp_tsiz")]
            self.fmat = self.old[self.sql.scpcmp_col.index("scp_fmat")]
            self.logo = self.old[self.sql.scpcmp_col.index("scp_logo")]
            self.df.loadEntry(frt, pag, p+1, data=self.cmpnam)
            self.df.loadEntry(frt, pag, p+2, data=str(self.tsex))
            self.df.loadEntry(frt, pag, p+3, data=str(self.tsiz))
            self.df.loadEntry(frt, pag, p+4, data=self.fmat)
            self.df.loadEntry(frt, pag, p+5, data=self.logo)

    def doCmpNam(self, frt, pag, r, c, p, i, w):
        self.cmpnam = w

    def doCmpSex(self, frt, pag, r, c, p, i, w):
        self.tsex = w

    def doCmpSiz(self, frt, pag, r, c, p, i, w):
        self.tsiz = int(w)

    def doCmpTyp(self, frt, pag, r, c, p, i, w):
        self.fmat = w

    def doCmpLogo(self, frt, pag, r, c, p, i, w):
        if w and not os.path.isfile(w):
            return "Invalid Logo Path"
        self.logo = w
        try:
            if self.img:
                self.img.destroyImage()
            self.img = ShowImage(self.df.topPage0, self.logo,
                wrkdir=self.opts["mf"].rcdic["wrkdir"], msiz=100)
        except:
            pass

    def doSkpCod(self, frt, pag, r, c, p, i, w):
        if not w:
            ok = askQuestion(self.opts["mf"].body, head="New Player",
                mess="Is This a New Player?", default="yes")
            if ok == "no":
                return "Invalid Code"
            cod = getNextCode(self.sql, "scpmem", "scm_scod",
                where=[("scm_cono", "=", self.opts["conum"])], last=899999)
            callModule(self.opts["mf"], self.df, "sc1010",
                coy=[self.opts["conum"], self.opts["conam"]], args=(cod,))
            self.df.loadEntry(frt, pag, p, data=cod)
        else:
            cod = w
        if i == 0:
            if cod in self.parts:
                return "Invalid Skip, Already a Partner"
            self.skips.append(cod)
            self.scod = cod
        else:
            if cod in self.skips:
                return "Invalid Partner, Already a Skip"
            self.parts.append(cod)
            self.pcod = cod
        chk = self.sql.getRec("scpmem", cols=["scm_surname",
            "scm_names", "scm_gender"], where=[("scm_cono", "=",
            self.opts["conum"]), ("scm_scod", "=", cod)], limit=1)
        if not chk:
            return "Invalid Player Code"
        if self.tsex in ("M", "F") and chk[2] != self.tsex:
            return "Invalid Gender"
        self.df.loadEntry(frt, pag, p+1, data=self.getName(chk=chk))
        if i == 0:
            ent = self.sql.getRec("scpent", cols=["sce_pcod"],
                where=[("sce_cono", "=", self.opts["conum"]), ("sce_ccod", "=",
                self.ccod), ("sce_scod", "=", self.scod)], limit=1)
            if ent:
                self.newent = False
                if ent[0]:
                    ptr = self.sql.getRec("scpmem", cols=["scm_surname",
                        "scm_names"], where=[("scm_cono", "=",
                        self.opts["conum"]), ("scm_scod", "=", ent[0])],
                        limit=1)
                    self.df.loadEntry(frt, pag, p+2, data=ent[0])
                    self.df.loadEntry(frt, pag, p+3, data=self.getName(chk=ptr))
            else:
                self.newent = True
            if self.tsiz != 2:
                self.pcod = 0
                return "sk3"

    def getName(self, scod=None, chk=None):
        if scod:
            chk = self.sql.getRec("scpmem", cols=["scm_surname",
                "scm_names", "scm_gender"], where=[("scm_cono", "=",
                self.opts["conum"]), ("scm_scod", "=", scod)], limit=1)
        name = "%s," % chk[0]
        init = chk[1].split()
        for i in init:
            name = "%s %s" % (name, i.upper())
        return name

    def doDelete(self, args=None):
        self.scod = args[1]
        self.sql.delRec("scpent", where=[("sce_cono", "=", self.opts["conum"]),
            ("sce_ccod", "=", self.ccod), ("sce_scod", "=", self.scod)])
        self.sql.delRec("scpgme", where=[("scg_cono", "=", self.opts["conum"]),
            ("scg_ccod", "=", self.ccod), ("scg_scod", "=", self.scod)])
        self.loadButton()
        self.doLoadEntries()

    def doEnd(self):
        if self.df.frt == "T":
            data = [self.opts["conum"]] + self.df.t_work[0][0] + \
                [0,0,"","","",0,0,""]
            if self.newcmp:
                self.sql.insRec("scpcmp", data=data)
            elif data != self.old[:len(data)]:
                col = self.sql.scpcmp_col
                data.append(self.old[col.index("scp_xflag")])
                self.sql.updRec("scpcmp", data=data, where=[("scp_cono",
                    "=", self.opts["conum"]), ("scp_ccod", "=", self.ccod)])
            self.loadButton()
            if self.newcmp:
                self.df.focusField("C", 0, 1)
            else:
                self.doLoadEntries()
        else:
            if self.newent:
                self.sql.insRec("scpent", data=[self.opts["conum"], self.ccod,
                    self.scod, self.pcod])
                self.df.advanceLine(0)
            else:
                self.sql.updRec("scpent", cols=["sce_scod", "sce_pcod"],
                    data=[self.scod, self.pcod], where=[("sce_cono", "=",
                    self.opts["conum"]), ("sce_ccod", "=", self.ccod),
                    ("sce_scod", "=", self.scod)])
                self.doLoadEntries()
            self.loadButton()

    def doLoadEntries(self):
        self.skips = []
        ents = self.sql.getRec("scpent", cols=["sce_scod", "sce_pcod"],
            where=[("sce_cono", "=", self.opts["conum"]), ("sce_ccod",
            "=", self.ccod)])
        self.df.clearFrame("C", 0)
        self.df.focusField("C", 0, 1)
        for num, ent in enumerate(ents):
            self.skips.append(ent[0])
            self.df.loadEntry("C", 0, self.df.pos,
                    data=ent[0])
            self.df.loadEntry("C", 0, self.df.pos+1,
                    data=self.getName(ent[0]))
            if ent[1]:
                self.parts.append(ent[1])
                self.df.loadEntry("C", 0, self.df.pos+2,
                        data=ent[1])
                self.df.loadEntry("C", 0, self.df.pos+3,
                        data=self.getName(ent[1]))
            self.df.advanceLine(0)

    def loadButton(self):
        rec = self.sql.getRec("scpent", cols=["count(*)"],
            where=[("sce_cono", "=", self.opts["conum"]), ("sce_ccod", "=",
            self.ccod)], limit=1)
        self.df.B0.setLabel("Entered Players (%s)" % int(rec[0]), udl=0)

    def doPrint(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        hdr = ["Skips Entered for the %s" % self.cmpnam]
        tab = ["scpent", "scpmem"]
        col = ["scm_scod", "scm_surname", "scm_names", "scm_phone",
            ["scm_email", "TX", 30, "Email-Address"]]
        whr = [("sce_ccod", "=", self.ccod), ("scm_scod=sce_scod",)]
        odr = "scm_surname"
        RepPrt(self.opts["mf"], name=self.__class__.__name__, heads=hdr,
            tables=tab, cols=col, where=whr, order=odr, prtdia=(("Y","V"),
            ("Y","N")))
        self.df.setWidget(self.df.mstFrame, state="show")

    def doExit(self):
        if self.df.frt == "C":
            chk = self.sql.getRec("scpent", where=[("sce_cono", "=",
                self.opts["conum"]), ("sce_ccod", "=", self.ccod)])
            if chk:
                self.opts["mf"].dbm.commitDbase()
            else:
                self.opts["mf"].dbm.rollbackDbase()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
