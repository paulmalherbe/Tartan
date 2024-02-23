"""
SYNOPSIS
    Create and maintain company records.

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

import time
from TartanClasses import TartanDialog, ShowImage, Sql, TabPrt
from tartanFunctions import askQuestion, callModule, dateDiff, getFileName
from tartanFunctions import mthendDate, showError
from tartanWork import allsys, tabdic

class ms1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlmst", "ctlynd", "ctlvmf",
            "ctlvrf", "chglog"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        cnt = self.sql.getRec("ctlmst", cols=["count(*)"], limit=1)
        if not cnt[0]:
            self.first = True
        else:
            self.first = False
        self.img = None
        return True

    def mainProcess(self):
        self.tit = ("Company Records File Maintenance",)
        ctm = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Num"),
                ("ctm_name", "", 0, "Name", "Y"))}
        log = {
            "stype": "F",
            "types": "fle",
            "ftype": (("Image", "*"),)}
        r1s = (("Yes", "Y"), ("No", "N"))
        tag = (
            ("General",None,("T",1,2),("T",1,1)),
            ("Banking",None,("T",1,2),("T",1,1)),
            ("Systems",None,("T",1,2),("T",1,1)),
            ("Logo",None,("T",1,2),("T",1,1)))
        fld = [
            [("T",1,0,0),"IUI",3,"Company Number","Number",
                "","Y",self.doCoyNum,ctm,None,("notzero",)],
            (("T",1,1,0),"INA",30,"Name","Company Name",
                "","N",self.doCoyNam,None,self.doDelete,("notblank",)),
            (("T",1,2,0),"INA",30,"Postal Address Line-1","Address Line-1",
                "","N",None,None,None,None),
            (("T",1,3,0),"INA",30,"               Line-2","Address Line-2",
                "","N",None,None,None,None),
            (("T",1,4,0),"INA",30,"               Line-3","Address Line-3",
                "","N",None,None,None,None),
            (("T",1,5,0),"INA",4,"Postal Code","",
                "","N",None,None,None,None),
            (("T",1,6,0),"INA",30,"Street Address Line-1",
                "Street Address Line-1","","N",None,None,None,None),
            (("T",1,7,0),"INA",30,"               Line-2","Address Line-2",
                "","N",None,None,None,None),
            (("T",1,8,0),"INA",30,"               Line-3","Address Line-3",
                "","N",None,None,None,None),
            (("T",1,9,0),"INA",4,"Street Code","",
                "","N",None,None,None,None),
            (("T",1,10,0),"INA",30,"Contact Name","",
                "","N",None,None,None,None),
            (("T",1,11,0),"INA",15,"Telephone","Telephone No",
                "","N",None,None,None,None),
            (("T",1,12,0),"INA",15,"Facsimile","Facsimile No",
                "","N",None,None,None,None),
            (("T",1,13,0),"INA",15,"Mobile","Mobile Number",
                "","N",None,None,None,None),
            (("T",1,14,0),"ITX",50,"E-Mail Address","",
                "","N",None,None,None,("email",)),
            (("T",1,15,0),"ITX",50,"Internet URL","",
                "","N",None,None,None,("efld",)),
            (("T",1,16,0),"INA",20,"Registration No","",
                "","N",None,None,None,None),
            (("T",1,17,0),"INA",20,"V.A.T. Number","",
                "","N",self.doVatNum,None,None,None),
            (("T",1,18,0),"IUA",1,"V.A.T. Default","",
                "","N",self.doVatCod,None,None,("notblank",)),
            (("T",2,0,0),"INA",30,"Bank Name","",
                "","N",None,None,None,None),
            (("T",2,1,0),"INA",30,"Bank Branch","",
                "","N",None,None,None,None),
            (("T",2,2,0),"INA",8,"Bank IBT","Bank IBT Number",
                "","N",None,None,None,None),
            (("T",2,3,0),"INA",16,"Bank Account","Bank Account Number",
                "","N",None,None,None,None)]
        pos = 1
        self.sys = []
        for x in range(len(allsys)):
            for sss in allsys:
                if allsys[sss][3] == pos:
                    self.sys.append(allsys[sss][1])
                    fld.append((("T",3,pos,0),("IRB",r1s),0,allsys[sss][0],"",
                        "N","N",None,None,None,None))
                    pos += 1
        fld.append((("T",4,0,0),"ITX",55,"Letterhead Image","",
                "","N",self.doLogo,log,None,("fle","blank")))
        but = (
            ("Accept",None,self.doAccept,0,("T",1,2),(("T",1,1),("T",4,0))),
            ("Print",None,self.doPrint,0,("T",1,2),(("T",1,1),("T",4,0))),
            ("Cancel",None,self.doCancel,0,("T",1,2),(("T",1,1),("T",4,0))),
            ("Quit",None,self.doExit1,1,None,None))
        tnd = (None, (self.doEnd, "n"), (self.doEnd, "n"), (self.doEnd, "n"),
            (self.doEnd, "y"))
        txt = (None, self.doExit1, self.doExit2, self.doExit3, self.doExit4)
        self.df = TartanDialog(self.opts["mf"], title=self.tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt, clicks=self.doClick)
        if self.first:
            self.opts["conum"] = 1
            self.new = True
            self.df.topf[1][0][1] = "OUI"
            self.df.loadEntry("T", 1, 0, data=self.opts["conum"])
            self.df.focusField("T", 1, 2)

    def doClick(self, *opts):
        if self.df.pag == 1 and self.df.col == 1:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doCoyNum(self, frt, pag, r, c, p, i, w):
        if w == 0:
            return "Invalid Company Number"
        elif w != 1:
            chk = self.sql.getRec("ctlmst", where=[("ctm_cono", "=", 1)],
                limit=1)
            if not chk:
                return "Company 1 Must First Exist"
        self.opts["conum"] = w
        self.old = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        if not self.old:
            self.new = True
        else:
            self.new = False
            self.opts["conam"] = self.old[self.sql.ctlmst_col.index("ctm_name")]
            for x in range(1, self.df.topq[pag]):
                data = self.old[x]
                self.df.loadEntry(frt, pag, x, data=data)
            for x in range(0, self.df.topq[pag+1]):
                data = self.old[x+self.df.topq[pag]]
                self.df.loadEntry(frt, pag+1, x, data=data)
            for x in range(0, self.df.topq[pag+2]):
                self.df.loadEntry(frt, pag+2, x, data="N")
            mods = self.old[self.sql.ctlmst_col.index("ctm_modules")].rstrip()
            for x in range(0, len(mods), 2):
                idx = self.sys.index(mods[x:x+2])
                self.df.loadEntry(frt, pag+2, idx, data="Y")
            self.logo = self.old[self.sql.ctlmst_col.index("ctm_logo")]
            self.df.loadEntry(frt, pag+3, 0, data=self.logo)
            if self.logo:
                self.displayLogo(self.logo)

    def doDelete(self):
        if self.opts["conum"] == 1:
            showError(self.opts["mf"].body, "Deletion Error",
                "Company 1 Cannot be Deleted")
            return
        err = False
        skp = {
            "ctlmst": "ctm_cono",
            "ctlynd": "cye_cono",
            "ctlvmf": "vtm_cono",
            "ctlvrf": "vtr_cono"}
        for tab in tabdic:
            if tab in skp:
                continue
            chk = tabdic[tab]["fld"][0][1]
            if chk.count("_cono"):
                sql = Sql(self.opts["mf"].dbm, tab,
                        prog=self.__class__.__name__)
                err = sql.getRec(tables=tab, where=[(chk, "=",
                    self.opts["conum"])])
                if err:
                    break
        if err:
            showError(self.opts["mf"].body, "Deletion Error",
                "%s Records Exist for This Company, Cannot Delete" % tab)
            return
        for tab in skp:
            self.sql.delRec(tab, where=[(skp[tab], "=", self.opts["conum"])])
        self.opts["mf"].dbm.commitDbase(ask=True)

    def doCoyNam(self, frt, pag, r, c, p, i, w):
        self.opts["conam"] = w
        chk = self.sql.getRec("ctlvmf", where=[("vtm_cono",
            "=", self.opts["conum"])], limit=1)
        if not chk:
            self.sql.insRec("ctlvmf", data=[self.opts["conum"],
                "N", "No VAT", "N"])
            self.sql.insRec("ctlvrf", data=[self.opts["conum"],
                "N", 0, 0])

    def doVatNum(self, frt, pag, r, c, p, i, w):
        self.vatnum = w
        if not self.vatnum:
            self.vat = "N"
            self.df.loadEntry(frt, pag, p+1, data=self.vat)
            return "sk1"

    def doVatCod(self, frt, pag, r, c, p, i, w):
        self.vat = w
        acc = self.doReadVat(self.vat)
        if not acc:
            ok = askQuestion(self.opts["mf"].body, "VAT Code",
                "This Code Does Not Exist, Do You Want to Create It?")
            if ok == "no":
                return "Invalid Code"
            state = self.df.disableButtonsTags()
            self.df.setWidget(self.df.mstFrame, state="hide")
            callModule(self.opts["mf"], None, "ms1040",
                coy=(self.opts["conum"], self.opts["conam"]),
                user=self.opts["capnm"], args=self.vat)
            self.df.setWidget(self.df.mstFrame, state="show")
            self.df.enableButtonsTags(state=state)
            acc = self.doReadVat(self.vat)
            if not acc:
                self.df.loadEntry(frt, pag, p, data="")
                return "Invalid Code"

    def doLogo(self, frt, pag, r, c, p, i, w):
        if not w:
            if self.img:
                self.img.destroyImage()
        else:
            nam = getFileName(w, wrkdir=self.opts["mf"].rcdic["wrkdir"])
            if self.displayLogo(nam):
                return "Invalid Logo Image"

    def displayLogo(self, logo):
        try:
            if self.img:
                try:
                    self.img.destroyImage()
                except:
                    pass
            self.img = ShowImage(self.df.nb.Page4, logo,
                wrkdir=self.opts["mf"].rcdic["wrkdir"], msiz=640)
        except Exception as err:
            return "error"

    def doReadVat(self, w):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            w)], limit=1)
        return acc

    def doEnd(self):
        if self.df.pag == 1:
            self.df.selPage("Banking")
            self.df.focusField("T", 2, 1)
        elif self.df.pag == 2:
            self.df.selPage("Systems")
            self.df.focusField("T", 3, 1)
        elif self.df.pag == 3:
            self.df.selPage("Logo")
            self.df.focusField("T", 4, 1)
        else:
            data = []
            mods = ""
            for x in range(0, len(self.df.t_work[1][0])):
                data.append(self.df.t_work[1][0][x])
            for x in range(0, len(self.df.t_work[2][0])):
                data.append(self.df.t_work[2][0][x])
            fin = False
            for x in range(0, len(self.df.t_work[3][0])):
                if self.df.t_work[3][0][x] == "Y":
                    mod = self.sys[x]
                    if mod not in ("BC", "BS", "SC"):
                        fin = True
                    mods = mods + mod
            data.append(mods)
            data.extend(self.df.t_work[4][0][0:2])
            if self.new:
                self.sql.insRec("ctlmst", data=data)
            elif data != self.old[:len(data)]:
                col = self.sql.ctlmst_col
                data.append(self.old[col.index("ctm_xflag")])
                self.sql.updRec("ctlmst", data=data, where=[("ctm_cono",
                    "=", self.opts["conum"])])
                dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
                for num, dat in enumerate(self.old):
                    if dat != data[num]:
                        self.sql.insRec("chglog", data=["ctlmst", "U",
                            "%03i" % self.opts["conum"], col[num], dte,
                            self.opts["capnm"], str(dat), str(data[num]),
                            "", 0])
            if fin:
                # Financial Systems
                ynd = self.sql.getRec("ctlynd", cols=["count(*)"],
                    where=[("cye_cono", "=", self.opts["conum"])], limit=1)
                if not ynd[0]:
                    self.doFinPeriod()
                    if self.xits == "y":
                        self.doCancel()
                        return True
            self.opts["mf"].dbm.commitDbase()
            if self.first:
                self.doExit1()
            else:
                self.df.selPage("General")
                self.df.focusField("T", 1, 1)

    def doFinPeriod(self):
        tit = ("Initial Financial Period",)
        fld = (
            (("T",0,0,0),"ID1",10,"Period Start Date","",
                "","N",self.doStartPer,None,None,("efld",)),
            (("T",0,1,0),"ID1",10,"Period End Date","",
                "","N",self.doEndPer,None,None,("efld",)))
        tnd = ((self.doPerEnd,"y"), )
        txt = (self.doPerExit,)
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.pf = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=tnd, txit=txt)
        self.pf.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.opts["mf"].head.configure(text=self.tit[0])

    def doStartPer(self, frt, pag, r, c, p, i, w):
        y = int(w / 10000) - 1
        m = int((w % 10000) / 100)
        if m == 2:
            if not y % 4:
                d = 29
            else:
                d = 28
        else:
            d = w % 100
        self.s0 = (y*10000) + (m*100) + d
        self.s1 = w
        y = int(w / 10000) + 1
        m -= 1
        if not m:
            m = 12
            y -= 1
        self.pf.t_work[0][0][1] = mthendDate((y*10000) + (m*100) + 1)

    def doEndPer(self, frt, pag, r, c, p, i, w):
        if w <= self.s1:
            return "Invalid End Period"
        if dateDiff(self.s1, w, "months") > 14:
            return "Invalid Date, More than 15 Months"
        y = int(w / 10000) - 1
        m = int((w % 10000) / 100)
        if m == 2:
            if not y % 4:
                d = 29
            else:
                d = 28
        else:
            d = w % 100
        self.e0 = (y*10000) + (m*100) + d
        self.e1 = w

    def doPerEnd(self):
        self.sql.insRec("ctlynd",data=[self.opts["conum"], 0, self.s0, self.e0,
            0, "N"])
        self.sql.insRec("ctlynd",data=[self.opts["conum"], 1, self.s1, self.e1,
            0, "N"])
        self.xits = "n"
        self.closeProcess()

    def doPerExit(self):
        self.xits = "y"
        self.closeProcess()

    def closeProcess(self):
        self.pf.closeProcess()

    def doAccept(self):
        for page in range(4):
            frt, pag, col, mes = self.df.doCheckFields(("T",page+1,None))
            if mes:
                break
        if mes:
            self.df.last[pag][0] = col+1
            self.df.selPage(self.df.tags[pag - 1][0])
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            mod = False
            for x in range(len(self.df.t_work[3][0])):
                if self.df.t_work[3][0][x] == "Y":
                    mod = True
                    break
            if not mod:
                self.df.selPage("Systems")
                self.df.focusField("T", 3, 1, err="Missing System Module")
            else:
                if self.img:
                    self.img.destroyImage()
                self.df.selPage("Logo")
                self.df.doEndFrame("T", 4, cnf="N")

    def doPrint(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        TabPrt(self.opts["mf"], self.opts["conum"],
            name=self.__class__.__name__, tabs="ctlmst",
            where=[("ctm_cono", "=", self.opts["conum"])])
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.selPage("General")
        self.df.focusField("T", 1, 1)

    def doExit1(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doExit2(self):
        self.df.selPage("General")

    def doExit3(self):
        self.df.selPage("Banking")

    def doExit4(self):
        self.df.selPage("Systems")

# vim:set ts=4 sw=4 sts=4 expandtab:
