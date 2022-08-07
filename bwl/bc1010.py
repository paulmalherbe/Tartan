"""
SYNOPSIS
    Bowls Tabs Maintenance.

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
from TartanClasses import FileImport, GetCtl, ProgressBar, RepPrt
from TartanClasses import SimpleDialog, Sql, TartanDialog
from tartanFunctions import askChoice, askQuestion, getNextCode, showError
from tartanFunctions import showInfo

class bc1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "args" in self.opts:
                self.tabcvt = False
                self.gentab = False
                self.newtab = True
                self.tab = self.opts["args"]
                self.df.loadEntry("T", 0, 0, data=self.tab)
                self.df.topf[0][0][1] = "OUI"
                self.df.topf[0][1][1] = "OUI"
                self.df.focusField("T", 0, 2)
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["chglog", "bwlent", "bwlgme",
            "bwltab", "bwldrt", "bwlflm", "bwlflt", "memmst", "memkon",
            "memadd", "memcat"], prog=self.__class__.__name__)
        if self.sql.error:
            if self.sql.error == ["memmst", "memkon"]:
                self.memmst = False
            else:
                return
        else:
            self.memmst = True
        gc = GetCtl(self.opts["mf"])
        bwlctl = gc.getCtl("bwlctl", self.opts["conum"])
        if not bwlctl:
            return
        self.mlint = bwlctl["ctb_mlint"]
        self.samen = bwlctl["ctb_samen"]
        self.mscat = bwlctl["ctb_mscat"]
        self.mstart = bwlctl["ctb_mstart"]
        self.fstart = bwlctl["ctb_fstart"]
        self.nstart = bwlctl["ctb_nstart"]
        self.dbase = bwlctl["ctb_dbase"]
        self.order = bwlctl["ctb_order"]
        self.mixed = bwlctl["ctb_mixed"]
        self.fromad = bwlctl["ctb_emadd"]
        self.keys = (
            ("bwltab", "btb_cono", "btb_tab"),
            ("bwldrt", "bdt_cono", "bdt_tab"),
            ("bwlent", "bce_cono", "bce_scod"),
            ("bwlflt", "bft_cono", "bft_player"),
            ("bwlgme", "bcg_cono", "bcg_scod"),
            ("bwldrt", "bdt_cono", "bdt_team1"),
            ("bwldrt", "bdt_cono", "bdt_team2"),
            ("bwldrt", "bdt_cono", "bdt_team3"),
            ("bwlflt", "bft_cono", "bft_skip"),
            ("bwlgme", "bcg_cono", "bcg_ocod"))
        return True

    def mainProcess(self):
        tab = {
            "stype": "R",
            "tables": ("bwltab",),
            "cols": [
                ("btb_tab", "", 0, "Tab"),
                ("btb_surname", "", 0, "Surname", "Y"),
                ("btb_names", "", 0, "Names"),
                ("btb_bsano", "", 0, "BSA-No")],
            "where": [("btb_cono", "=", self.opts["conum"])],
            "order": "btb_surname"}
        if self.mlint == "N":
            mlm = None
        else:
            tab["cols"].insert(3, ("btb_memno", "", 0, "Mem-No"))
            mlm = {
                "stype": "R",
                "tables": ("memmst",),
                "cols": (
                    ("mlm_memno", "", 0, "Mem-No"),
                    ("mlm_oldno", "", 0, "Old-No"),
                    ("mlm_idnum", "", 0, "Identity-Numb"),
                    ("mlm_gender", "", 0, "G"),
                    ("mlm_state", "", 0, "S"),
                    ("mlm_surname", "", 0, "Surname", "Y"),
                    ("mlm_names", "", 0, "Names", "F")),
                "where": [("mlm_cono", "=", self.opts["conum"])],
                "order": "mlm_surname, mlm_names"}
        r1s = (("Male", "M"), ("Female", "F"))
        if self.dbase == "R":
            r2s = (("None", "0"),)
        else:
            r2s = (("Skip","4"), ("Third","3"), ("Second","2"), ("Lead","1"))
        fld = [
            (("T",0,0,0),"I@btb_tab",0,"","",
                "","Y",self.doTab,tab,None,("efld",),None,
                "Note: Tab numbers Must be Unique."),
            [("T",0,1,0),"I@btb_memno",0,"","",
                "","N",self.doMember,mlm,self.doDelete,("efld",)],
            (("T",0,2,0),"I@btb_surname",0,"","",
                "","N",self.doSurname,None,self.doDelete,("notblank",)),
            (("T",0,3,0),"I@btb_names",0,"","",
                "","N",self.doNames,None,None,("efld",)),
            (("T",0,4,0),("IRB",r1s),0,"Gender","",
                "M","N",self.doGender,None,None,None),
            (("T",0,5,0),"I@btb_add1",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"I@btb_add2",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"I@btb_add3",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"I@btb_pcod",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"I@btb_home",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,10,0),"I@btb_work",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,11,0),"I@btb_cell",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,12,0),"I@btb_mail",0,"","",
                "","N",self.doEmail,None,None,("efld",)),
            (("T",0,13,0),("IRB",r2s),0,"Position - Primary","",
                "1","N",self.doPos,None,self.doDelete,None),
            (("T",0,14,0),"I@btb_rate1",0,"","",
                "","N",self.doRate,None,None,("efld",)),
            (("T",0,15,0),("IRB",r2s),0,"Position - Mixed","",
                "1","N",self.doPos,None,None,None),
            (("T",0,16,0),"I@btb_rate2",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,17,0),"I@btb_bsano",0,"","",
                "","N",None,None,None,("efld",))]
        if self.mlint == "N":
            fld[1] = [("T",0,1,0),"O@btb_memno",0,""]
        if self.mlint == "Y":
            but = []
        else:
            but = [
            ("Import",None,self.doImport,0,("T",0,1),(("T",0,2),("T",0,3)),
                "Import Tabs and/or Ratings from a CSV or XLS File.")]
        but.extend([
            ("Accept",None,self.doEnd,0,("T",0,3),("T",0,0),
                "Accept All Fields and Continue"),
            ("Convert",None,self.doConvert,0,("T",0,3),("T",0,4),
                "Convert a Visitor's Tab to a Member's Tab"),
            ("Print",None,self.doPrint,1,None,None)])
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            eflds=fld, butt=but, tend=tnd, txit=txt, clicks=self.doClick)

    def doClick(self, *opts):
        if self.df.col == 1:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doTab(self, frt, pag, r, c, p, i, w):
        self.tab = w
        self.newvis = False
        self.tabcvt = False
        self.tabchg = False
        if not self.tab:
            if self.mlint == "Y" and self.samen == "Y":
                ok = askQuestion(self.opts["mf"].body, "New Tab",
                    "Is this TAB for a Visitor", default="no")
                if ok == "no":
                    return "New Member, Please Create in Ledger"
                self.newvis = True
            self.gentab = True
            self.newtab = True
        else:
            self.gentab = False
            self.oldtab = self.sql.getRec("bwltab", where=[("btb_cono",
                "=", self.opts["conum"]), ("btb_tab", "=", self.tab)], limit=1)
            if not self.oldtab:
                self.newtab = True
            else:
                self.newtab = False
                for num, fld in enumerate(self.oldtab[1:-1]):
                    if num == 2:
                        self.snam = fld
                    elif num == 3:
                        self.fnam = fld
                    elif num == 4:
                        self.gender = fld
                    elif num in (13, 15):
                        fld = str(fld)
                        if num == 13:
                            self.pos1 = fld
                    self.df.loadEntry(frt, pag, num, data=fld)
        if self.tab and self.mlint == "Y":
            if self.oldtab:
                memno = self.oldtab[self.sql.bwltab_col.index("btb_memno")]
            elif self.tab < self.nstart and self.samen == "Y":
                memno = self.tab
            else:
                memno = 0
        else:
            memno = 0
        if memno:
            chk = self.doLoadMember(memno)
            if chk:
                return chk
            if self.dbase == "R":
                return "sk13"
            return "sk12"
        if self.newvis or self.tab >= self.nstart:
            return "sk1"

    def doMember(self, frt, pag, r, c, p, i, w):
        if w:
            if self.newtab or not self.oldtab[2]:
                chk = self.sql.getRec("bwltab", where=[("btb_cono",
                    "=", self.opts["conum"]), ("btb_memno", "=", w)], limit=1)
                if chk:
                    return "Member Already Has a TAB"
            chk = self.doLoadMember(w)
            if chk:
                return chk
            if self.newtab and not self.tab:
                chk = self.getNextTab()
                if not chk:
                    return "Invalid Membership Number"
            if self.dbase == "R":
                return "sk12"
            return "sk11"
        elif self.tab and self.tab < self.nstart and self.mlint == "Y":
            return "Invalid Membership Number"

    def doLoadMember(self, memno):
        # Check member
        acc = self.sql.getRec("memmst", cols=["mlm_surname",
            "mlm_names", "mlm_gender"], where=[("mlm_cono", "=",
            self.opts["conum"]), ("mlm_memno", "=", memno)], limit=1)
        if not acc:
            return "Member %s Does Not Exist" % memno
        # Check category
        if self.mscat:
            cat = self.sql.getRec("memcat", where=[("mlc_cono", "=",
                self.opts["conum"]), ("mlc_memno", "=", memno),
                ("mlc_type", "=", "C"), ("mlc_code", "=", self.mscat)],
                limit=1)
            if not cat:
                return "Member %s is Not in the Bowls Category" % memno
        self.snam = acc[0]
        self.fnam = acc[1]
        self.gender = acc[2]
        self.df.loadEntry("T", 0, 1, data=memno)
        self.df.loadEntry("T", 0, 2, data=self.snam)
        self.df.loadEntry("T", 0, 3, data=self.fnam)
        self.df.loadEntry("T", 0, 4, data=self.gender)
        for typ in ("A", "P"):
            ad = self.sql.getRec("memadd", cols=["mla_add1", "mla_add2",
                "mla_add3", "mla_code"], where=[("mla_cono", "=",
                self.opts["conum"]), ("mla_memno", "=", memno), ("mla_type",
                "=", typ)], limit=1)
            if ad:
                break
        if ad:
            self.df.loadEntry("T", 0, 5, data=ad[0])
            self.df.loadEntry("T", 0, 6, data=ad[1])
            self.df.loadEntry("T", 0, 7, data=ad[2])
            self.df.loadEntry("T", 0, 8, data=ad[3])
        for num, cod in enumerate((1, 2, 3, 5)):
            kk = self.sql.getRec("memkon", cols=["mlk_detail"],
                where=[("mlk_cono", "=", self.opts["conum"]),
                ("mlk_memno", "=", memno), ("mlk_code", "=", cod)], limit=1)
            if kk:
                self.df.loadEntry("T", 0, num+9, data=kk[0])

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        if self.newtab:
            chk = self.sql.getRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_surname", "=", self.sname,
                "and", "btb_names", "=", w)], limit=1)
            if chk:
                tab = chk[self.sql.bwltab_col.index("btb_tab")]
                self.doTab(frt, pag, 0, 1, 0, 0, tab)
                return "ff3"
            if self.mstart < self.fstart and self.tab >= self.fstart:
                self.df.loadEntry(frt, pag, p+1, data="F")
            elif self.fstart < self.mstart and self.tab < self.mstart:
                self.df.loadEntry(frt, pag, p+1, data="F")
            return
        if self.sname != self.snam or w != self.fnam:
            but = [("Amendment", "A"), ("Re-Issue", "R"), ("Neither", "N")]
            ok = askChoice(self.opts["mf"].body, "Name Change",
                "Please Select the Reason for the Name Change",
                butt=but, default="Neither")
            if ok == "N":
                return "ff3"
            if ok == "R":
                self.tabchg = True
                for x in range(1, 15):
                    self.df.clearEntry(frt, pag, c + x)

    def doGender(self, frt, pag, r, c, p, i, w):
        self.gender = w
        if self.gentab:
            chk = self.getNextTab()
            if not chk:
                return "ff2|Invalid Membership Number"
        if self.tab < self.nstart:
            if self.mstart < self.fstart:
                if self.gender == "M" and self.tab >= self.fstart:
                    return "ff5|Invalid Gender for Tab Number"
                elif self.gender == "F" and self.tab < self.fstart:
                    return "ff5|Invalid Gender for Tab Number"
            else:
                if self.gender == "F" and self.tab >= self.mstart:
                    return "ff5|Invalid Gender for Tab Number"
                elif self.gender == "M" and self.tab < self.mstart:
                    return "ff5|Invalid Gender for Tab Number"

    def doEmail(self, frt, pag, r, c, p, i, w):
        if self.dbase in ("C","P") and self.df.t_work[0][0][13] == "0":
            self.df.t_work[0][0][13] = "1"
        if self.dbase == "R":
            self.pos1 = "0"
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"

    def doPos(self, frt, pag, r, c, p, i, w):
        if p == 13:
            self.pos1 = w
            self.df.loadEntry(frt, pag, p+2, data=w)
        if self.dbase == "P":
            self.df.loadEntry(frt, pag, p+1, data="")
            if p == 13:
                self.df.loadEntry(frt, pag, p+3, data="")
            if self.mixed == "N":
                return "sk3"
            else:
                return "sk1"

    def doRate(self, frt, pag, r, c, p, i, w):
        self.df.loadEntry(frt, pag, p+1, data=self.pos1)
        self.df.loadEntry(frt, pag, p+2, data=w)
        if self.dbase == "R":
            self.df.loadEntry(frt, pag, p+1, data="")
            if self.mixed == "N":
                return "sk2"
            else:
                return "sk1"
        if self.mixed == "N":
            return "sk2"

    def getNextTab(self):
        if self.newvis:
            ok = "yes"
        else:
            ok = askQuestion(self.opts["mf"].body, "Type",
                "Is this TAB for a Visitor", default="no")
        if ok == "no":
            if self.samen == "Y":
                return
            if self.gender == "M":
                start = self.mstart
                if self.mstart < self.fstart:
                    last = self.fstart
                else:
                    last = self.nstart
            else:
                start = self.fstart
                if self.mstart < self.fstart:
                    last = self.nstart
                else:
                    last = self.mstart
        else:
            start = self.nstart
            last = 900000
        self.tab = getNextCode(self.sql, "bwltab", "btb_tab",
            where=[("btb_cono", "=", self.opts["conum"])],
            start=start, last=last)
        self.df.loadEntry("T", 0, 0, data=self.tab)
        return True

    def doDelete(self):
        if self.newtab:
            return
        error = False
        for key in self.keys:
            if key[0] == "bwltab":
                continue
            chk = self.sql.getRec(tables=key[0], where=[(key[1], "=",
                self.opts["conum"]), (key[2], "=", self.tab)], limit=1)
            if chk:
                error = True
                break
        if error:
            if self.tab < self.nstart:
                # Member
                ok = askQuestion(self.opts["mf"].body, "Convert",
                    "Convert this Member to a Visitor", default="yes")
                if ok == "no":
                    return "Not Deleted nor Converted"
                tab = getNextCode(self.sql, "bwltab", "btb_tab",
                    where=[("btb_cono", "=", self.opts["conum"])],
                    start=self.nstart, last=900000)
                for key in self.keys:
                    self.sql.updRec(key[0], cols=[key[2]], data=[tab],
                        where=[(key[1], "=", self.opts["conum"]),
                        (key[2], "=", self.tab)])
            else:
                # Visitor
                chk = self.sql.getRec("bwlent", where=[("bce_cono",
                    "=", self.opts["conum"]), ("bce_scod", "=", self.tab)])
                if chk:
                    return "There is History for this Player, Not Deleted"
                self.sql.delRec("bwltab", where=[("btb_cono", "=",
                    self.opts["conum"]), ("btb_tab", "=", self.tab)])
        else:
            self.sql.delRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", self.tab)])
        self.opts["mf"].dbm.commitDbase()

    def doConvert(self):
        if self.tab < self.nstart:
            return
        titl = "Enter Member's Tab Number"
        ent = SimpleDialog(parent=self.df.window, title=titl,
            cols=(("a", "Tab Number          ", 6, "UI", "Tab"),))
        ent.sframe.wait_window()
        try:
            self.merge = False
            if self.gender == "M":
                start = self.mstart
                if self.mstart < self.fstart:
                    last = self.fstart - 1
                else:
                    last = self.nstart - 1
            else:
                start = self.fstart
                if self.mstart < self.fstart:
                    last = self.nstart - 1
                else:
                    last = self.mstart - 1
            tab = ent.data[0]
            if not tab:
                tab = getNextCode(self.sql, "bwltab", "btb_tab",
                    where=[("btb_cono", "=", self.opts["conum"])],
                    start=start, last=last)
            if tab < start or tab > last:
                showInfo(self.opts["mf"].body, "Error",
                    "Invalid Tab Number for Gender")
                raise Exception
            chk = self.sql.getRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", tab)], limit=1)
            if chk:
                ok = askQuestion(self.opts["mf"].body, "Invalid",
                    "This Tab is Already Allocated, Do You Want to Merge?")
                if ok == "no":
                    raise Exception
                self.merge = True
            self.tabcvt = True
            self.old = self.tab
            self.tab = tab
            self.df.loadEntry(self.df.frt, self.df.pag, 0, data=self.tab)
            self.df.focusField(self.df.frt, self.df.pag, 6)
        except:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrint(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if self.mlint == "Y":
            self.colsd = [["Membership Number", "N", "btb_memno"]]
        else:
            self.colsd = []
        self.colsd.extend([
            ["Surname & Initials", "Y", "name"],
            ["Surname", "N", "btb_surname"],
            ["First Names", "N", "btb_names"],
            ["Gender", "N", "btb_gender"],
            ["Address", "N", "address"],
            ["Telephone - Home", "N", "btb_home"],
            ["Telephone - Work", "N", "btb_work"],
            ["Telephone - Cell", "N", "btb_cell"],
            ["Email Address", "N", "btb_mail"],
            ["Ratings", "N", "ratings"],
            ["BSA Number", "N", "btb_bsano"],
            ["Order", "T", "order"]])
        r1s = (("Members", "M"), ("Guests", "G"), ("All", "A"))
        r2s = (("Males","M"), ("Females","F"), ("All","A"))
        r3s = (("Yes", "Y"), ("No", "N"))
        r4s = (("Tab", "T"), ("Surname", "S"), ("Rating", "R"))
        fld = [
            (("T",0,0,0),("IRB",r1s),0,"Tab Group","",
                "M","Y",self.doCGroup,None,None,None),
            (("T",0,1,0),("IRB",r2s),0,"Gender","",
                "A","Y",self.doCGender,None,None,None)]
        idx = 1
        for dat in self.colsd:
            idx += 1
            if dat == self.colsd[-1]:
                rb = r4s
            else:
                rb = r3s
            fld.append((("T",0,idx,0),("IRB",rb),0,dat[0],"",
                dat[1],"N",self.doCField,None,None,None))
        tnd = ((self.doCEnd,"Y"), )
        txt = (self.doCExit, )
        self.pr = TartanDialog(self.opts["mf"], eflds=fld,
            tend=tnd, txit=txt, view=("Y","V"), mail=("Y","Y"))
        self.pr.mstFrame.wait_window()
        if self.cols:
            cols = []
            dic = self.sql.bwltab_dic
            for col in self.cols:
                if col == "name":
                    cols.append(["name", "NA", 30, "Name"])
                elif col == "address":
                    cols.append(["btb_add1", dic["btb_add1"][2],
                        dic["btb_add1"][3], dic["btb_add1"][5]])
                    cols.append(["btb_add2", dic["btb_add2"][2],
                        dic["btb_add2"][3], dic["btb_add2"][5]])
                    cols.append(["btb_add3", dic["btb_add3"][2],
                        dic["btb_add3"][3], dic["btb_add3"][5]])
                    cols.append(["btb_pcod", dic["btb_pcod"][2],
                        dic["btb_pcod"][3], dic["btb_pcod"][5]])
                elif col == "ratings":
                    if self.dbase == "P":
                        cols.append(["btb_pos1", dic["btb_pos1"][2],
                            dic["btb_pos1"][3], dic["btb_pos1"][5]])
                        cols.append(["btb_pos2", dic["btb_pos2"][2],
                            dic["btb_pos2"][3], dic["btb_pos2"][5]])
                    elif self.dbase == "R":
                        cols.append(["btb_rate1", dic["btb_rate1"][2],
                            dic["btb_rate1"][3], dic["btb_rate1"][5]])
                        cols.append(["btb_rate2", dic["btb_rate2"][2],
                            dic["btb_rate2"][3], dic["btb_rate2"][5]])
                    else:
                        cols.append(["btb_pos1", dic["btb_pos1"][2],
                            dic["btb_pos1"][3], dic["btb_pos1"][5]])
                        cols.append(["btb_rate1", dic["btb_rate1"][2],
                            dic["btb_rate1"][3], dic["btb_rate1"][5]])
                        cols.append(["btb_pos2", dic["btb_pos2"][2],
                            dic["btb_pos2"][3], dic["btb_pos2"][5]])
                        cols.append(["btb_rate2", dic["btb_rate2"][2],
                            dic["btb_rate2"][3], dic["btb_rate2"][5]])
                else:
                    cols.append([col, dic[col][2], dic[col][3], dic[col][5]])
            whr = [("btb_cono", "=", self.opts["conum"])]
            if self.cgroup == "M":
                whr.append(("btb_tab", "<", self.nstart))
            elif self.cgroup == "G":
                whr.append(("btb_tab", ">=", self.nstart))
            if self.cgender in ("F", "M"):
                whr.append(("btb_gender", "=", self.cgender))
            if self.odr == "T":
                odr = "btb_tab"
            elif self.odr == "S":
                odr = "btb_surname, btb_names"
            else:
                odr = "btb_pos1 desc, btb_rate1 desc, btb_surname, btb_names"
            recs = self.sql.getRec("bwltab", where=whr, order=odr)
            data = []
            btc = self.sql.bwltab_col
            for rec in recs:
                dat = []
                for col in self.cols:
                    if col == "name":
                        snam = rec[btc.index("btb_surname")]
                        fnam = rec[btc.index("btb_names")]
                        if fnam:
                            fnam = fnam.split()
                            for num, nam in enumerate(fnam):
                                if not num:
                                    init = nam[0].upper()
                                else:
                                    init = "%s %s" % (init, nam[0].upper())
                            dat.append("%s, %s" % (snam, init))
                        else:
                            dat.append(snam)
                    elif col == "address":
                        dat.append(rec[btc.index("btb_add1")])
                        dat.append(rec[btc.index("btb_add2")])
                        dat.append(rec[btc.index("btb_add3")])
                        dat.append(rec[btc.index("btb_pcod")])
                    elif col == "ratings":
                        if self.dbase == "P":
                            dat.append(rec[btc.index("btb_pos1")])
                            dat.append(rec[btc.index("btb_pos2")])
                        elif self.dbase == "R":
                            dat.append(rec[btc.index("btb_rate1")])
                            dat.append(rec[btc.index("btb_rate2")])
                        else:
                            dat.append(rec[btc.index("btb_pos1")])
                            dat.append(rec[btc.index("btb_rate1")])
                            dat.append(rec[btc.index("btb_pos2")])
                            dat.append(rec[btc.index("btb_rate2")])
                    else:
                        dat.append(rec[btc.index(col)])
                data.append(dat)
            tit = "Tabs Lising for"
            if self.cgroup == "A":
                tit = "%s Members and Guests" % tit
            elif self.cgroup == "M":
                tit = "%s Members Only" % tit
            else:
                tit = "%s Guests Only" % tit
            if self.cgender == "A":
                tit = "%s (All Genders)" % tit
            elif self.cgender == "M":
                tit = "%s (Males Only)" % tit
            else:
                tit = "%s (Females Only)" % tit
            RepPrt(self.opts["mf"], name=self.__class__.__name__,
                conum=self.opts["conum"], conam=self.opts["conam"],
                heads=[tit], ttype="D", tables=data, cols=cols,
                repprt=self.pr.repprt, repeml=self.pr.repeml,
                fromad=self.fromad)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.window.focus_force()
        self.df.focusField("T", 0, 1)

    def doCGroup(self, frt, pag, r, c, p, i, w):
        self.cgroup = w

    def doCGender(self, frt, pag, r, c, p, i, w):
        self.cgender = w

    def doCField(self, frt, pag, r, c, p, i, w):
        if self.mlint == "N":
            idx = 2
        else:
            idx = 3
        if p == idx and w == "Y":
            self.pr.loadEntry(frt, pag, p+1, data="N")
            self.pr.loadEntry(frt, pag, p+2, data="N")
            return "sk2"

    def doCEnd(self):
        self.pr.closeProcess()
        self.cols = ["btb_tab"]
        if self.pr.repeml[0] == "N":
            end = -2
        else:
            end = -4
        for num, dat in enumerate(self.pr.t_work[0][0][2:end]):
            if dat == "Y":
                self.cols.append(self.colsd[num][2])
            elif dat in ("T", "S", "R"):
                self.odr = dat

    def doCExit(self):
        self.cols = []
        self.pr.closeProcess()

    def doEnd(self):
        if self.tabcvt:
            # Conversion to Member
            for key in self.keys:
                if key[0] == "bwltab" and self.merge:
                    self.sql.delRec(key[0], where=[(key[1], "=",
                        self.opts["conum"]), (key[2], "=", self.old)])
                    continue
                self.sql.updRec(key[0], cols=[key[2]], data=[self.tab],
                    where=[(key[1], "=", self.opts["conum"]),
                    (key[2], "=", self.old)])
        # Continue
        cols = []
        for x in range(18):
            cols.append(x)
        if self.dbase == "R":
            cols.remove(13)
            cols.remove(15)
        flds = ("T", 0, cols)
        frt, pag, col, mes = self.df.doCheckFields(flds)
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
            return
        tabdat = [self.opts["conum"]] + self.df.t_work[0][0]
        if self.newtab:
            self.sql.insRec("bwltab", data=tabdat)
        elif self.tabchg:
            tabdat.append("")
            self.doTabChg(tabdat)
        elif tabdat != self.oldtab[:len(tabdat)]:
            col = self.sql.bwltab_col
            tabdat.append(self.oldtab[col.index("btb_xflag")])
            self.sql.updRec("bwltab", data=tabdat, where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", self.tab)])
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.oldtab):
                if dat != tabdat[num]:
                    self.sql.insRec("chglog", data=["bwltab", "U",
                        "%03i%06s" % (self.opts["conum"], self.tab),
                        col[num], dte, self.opts["capnm"], str(dat),
                        str(tabdat[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        if "args" in self.opts:
            self.doExit()
        else:
            self.df.focusField("T", 0, 1)

    def doTabChg(self, tabdat):
        code = getNextCode(self.sql, "bwltab", "btb_tab",
            where=[("btb_cono", "=", self.opts["conum"])],
            start=self.nstart, last=900000)
        tables = (
            ("bwldrt","bdt_cono","bdt_tab","bdt_team1","bdt_team2","bdt_team3"),
            ("bwlent","bce_cono","bce_scod"),
            ("bwlflm","bfm_cono","bfm_captain"),
            ("bwlflt","bft_cono","bft_skip","bft_player"),
            ("bwlgme","bcg_cono","bcg_scod","bcg_ocod"),
            ("bwltab","btb_cono","btb_tab"))
        for tab in tables:
            for col in tab[2:]:
                self.sql.updRec(tab[0], cols=[col], data=[code],
                    where=[(tab[1], "=", self.opts["conum"]),
                    (col, "=", self.tab)])
        self.sql.insRec("bwltab", data=tabdat)

    def doImport(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        tit = ("Import Details",)
        r1s = (("Ratings Only", "R"), ("All Fields", "A"))
        fld = (
            (("T",0,0,0),("IRB",r1s),0,"Details","",
                "R","N",self.doImpDet,None,None,None),)
        self.ip = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doImpEnd,"y"),), txit=(self.doImpExit,))
        self.ip.mstFrame.wait_window()
        # Populate
        if self.impdet is None:
            self.df.setWidget(self.df.mstFrame, state="show")
            self.df.enableButtonsTags(state=state)
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        fi = FileImport(self.opts["mf"], imptab="bwltab", impskp=self.impskp)
        sp = ProgressBar(self.opts["mf"].body, typ="Importing Ratings",
            mxs=len(fi.impdat))
        err = None
        for num, line in enumerate(fi.impdat):
            sp.displayProgress(num)
            if self.mixed == "N":
                line.extend([0, ""])
            chk = self.sql.getRec("bwltab", where=[("btb_cono", "=",
                self.opts["conum"]), ("btb_tab", "=", line[0])], limit=1)
            if not chk:
                if self.impdet == "R":
                    err = "%s %s Does Not Exist" % (fi.impcol[0][0], line[0])
                    break
                line.insert(0, self.opts["conum"])
                if self.mlint == "N":
                    line.insert(2, 0)
                self.sql.insRec("bwltab", data=line)
            else:
                tmp = ["btb_pos1", "btb_rate1", "btb_pos2", "btb_rate2"]
                if self.impdet == "R":
                    cols = tmp
                else:
                    cols = ["btb_surname", "btb_names", "btb_gender",
                        "btb_add1", "btb_add2", "btb_add3", "btb_pcod",
                        "btb_home", "btb_work", "btb_cell",
                        "btb_mail"] + tmp + ["btb_bsano"]
                self.sql.updRec("bwltab", cols=cols, data=line[1:],
                    where=[("btb_cono", "=", self.opts["conum"]),
                    ("btb_tab", "=", line[0])])
        sp.closeProgress()
        if err:
            err = "Line %s: %s" % ((num + 1), err)
            showError(self.opts["mf"].body, "Import Error", """%s

Please Correct your Import File and then Try Again.""" % err)
            self.opts["mf"].dbm.rollbackDbase()
        else:
            self.opts["mf"].dbm.commitDbase()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doImpDet(self, frt, pag, r, c, p, i, w):
        self.impdet = w

    def doImpEnd(self):
        self.impskp = ["btb_cono"]
        if self.mlint == "N":
            self.impskp.append("btb_memno")
        if self.impdet == "R":
            self.impskp.extend(["btb_surname", "btb_names", "btb_gender",
                "btb_add1", "btb_add2", "btb_add3", "btb_pcod", "btb_home",
                "btb_work", "btb_cell", "btb_mail", "btb_bsano"])
        if self.mixed == "N":
            self.impskp.extend(["btb_pos2", "btb_rate2"])
        self.impskp.append("btb_xflag")
        self.ip.closeProcess()

    def doImpExit(self):
        self.impdet = None
        self.ip.closeProcess()

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
