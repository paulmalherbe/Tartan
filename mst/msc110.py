"""
SYNOPSIS
    System Control Record Maintenance.

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
from TartanClasses import Sql, TartanDialog
from tartanFunctions import chkMod, copyList, sendMail, showError

class msc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlsys", "ctlpwu", "chglog",
            "genmst"], prog=self.__class__.__name__)
        if self.sql.error:
            if self.sql.error == ["genmst"]:
                self.gl = False
            else:
                return
        else:
            self.gl = True
        self.acc = self.sql.getRec("ctlsys", limit=1)
        if not self.acc:
            self.new = True
            self.acc = [0, "N", 0, 0, 0, "", 0, 0, 0, "",
                "", "N", "", "", "N", 0]
        else:
            self.new = False
        return True

    def drawDialog(self):
        r1s = (("Yes","Y"),("No","N"))
        r2s = (("None","0"),("STARTTLS","1"),("SSL/TLS","2"))
        r3s = (("None","0"),("Normal","1"),("Encrypted","2"))
        self.fld = (
            (("T",0,0,0),"IUI",2,"Years to Keep History","",
                self.acc[0],"N",self.doHist,None,None,None,None,
                "The number of years that historical data must be kept, "\
                "Use 0 for No Limit"),
            (("T",0,1,0),("IRB",r1s),0,"Enforce Passwords","",
                self.acc[1],"N",self.doMust,None,None,None),
            (("T",0,2,0),"IUI",2,"Minimum Characters","",
                self.acc[2],"N",None,None,None,None),
            (("T",0,3,0),"IUI",2,"Maximum Life (Days)","",
                self.acc[3],"N",None,None,None,None),
            (("T",0,4,0),"IUI",3,"Backup History (Days)","",
                self.acc[4],"N",None,None,None,None,None,
                "0 for No Limit"),
            (("T",0,5,0),"ITX",30,"SMTP Server","",
                self.acc[5],"N",self.doSmtp,None,None,None),
            (("T",0,6,0),("IRB",r2s),0,"SMTP Security","",
                self.acc[6],"N",None,None,None,None),
            (("T",0,7,0),("IRB",r3s),0,"SMTP Authentication","",
                self.acc[7],"N",self.doAuth,None,None,None),
            (("T",0,8,0),"IUI",4,"SMTP Port","",
                self.acc[8],"N",None,None,None,None),
            (("T",0,9,0),"ITX",20,"SMTP Username","",
                self.acc[9],"N",self.doUsr,None,None,None),
            (("T",0,10,0),"IHA",20,"SMTP Password","",
                self.acc[10],"N",None,None,None,None),
            (("T",0,11,0),("IRB",r1s),0,"SMS Service","",
                self.acc[11],"N",self.doSms,None,None,None),
            (("T",0,12,0),"ITX",20,"SMS Username","",
                self.acc[12],"N",self.doSmsUsr,None,None,None),
            (("T",0,13,0),"IHA",20,"SMS Password","",
                self.acc[13],"N",self.doSmsPwd,None,None,None),
            (("T",0,14,0),("IRB",r1s),0,"G/L Departments","",
                self.acc[14],"N",self.doGlDept,None,None,None,None,
                "G/L Account Numbers include Department Numbers"),
            (("T",0,15,0),"IUI",1,"Number of Digits","",
                self.acc[15],"N",None,None,None,None,None,
                "The Number of Digits used for Department Numbers"))
        but = (
            ("Accept",None,self.doAccept,0,(("T",0,1),("T",0,6)),("T",0,0)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt, focus=False)
        for n, f in enumerate(self.acc):
            self.df.loadEntry("T", 0, n, data=f)
        self.df.focusField("T", 0, 1, clr=False)

    def doHist(self, frt, pag, r, c, p, i, w):
        if w and w < 7:
            return "At least 7 Years of History should be kept"

    def doMust(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            self.df.loadEntry(frt, pag, p+2, data=0)
            return "sk2"

    def doSmtp(self, frt, pag, r, c, p, i, w):
        if not w:
            self.df.loadEntry(frt, pag, p+1, data="0")
            self.df.loadEntry(frt, pag, p+2, data="0")
            self.df.loadEntry(frt, pag, p+3, data="")
            self.df.loadEntry(frt, pag, p+4, data="")
            self.df.loadEntry(frt, pag, p+5, data="")
            return "sk5"

    def doAuth(self, frt, pag, r, c, p, i, w):
        if not int(w):
            self.df.loadEntry(frt, pag, p+1, 25)
            self.df.loadEntry(frt, pag, p+2, "")
            self.df.loadEntry(frt, pag, p+3, "")
            return "sk3"
        elif int(self.df.t_work[0][0][6]) == 1:
            self.df.loadEntry(frt, pag, p+1, 587)
        elif int(self.df.t_work[0][0][6]) == 2:
            self.df.loadEntry(frt, pag, p+1, 465)

    def doUsr(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid SMTP Name"

    def doSms(self, frt, pag, r, c, p, i, w):
        if w == "Y" and not chkMod("requests"):
            showError(self.opts["mf"].body, "Error", "Missing requests Module")
            w = "N"
            self.df.loadEntry(frt, pag, p, data=w)
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data="")
            self.df.loadEntry(frt, pag, p+2, data="")
            if not self.gl:
                self.df.loadEntry(frt, pag, p+3, data="N")
                self.df.loadEntry(frt, pag, p+4, data=0)
                return "sk4"
            return "sk2"

    def doSmsUsr(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid SMS User Name"

    def doSmsPwd(self, frt, pag, r, c, p, i, w):
        if not w:
            return "Invalid SMS Password"

    def doGlDept(self, frt, pag, r, c, p, i, w):
        if w == "N":
            self.df.loadEntry(frt, pag, p+1, data=0)
            return "sk1"

    def doEnd(self):
        svr = self.df.t_work[0][0][5]
        if svr:
            prt = self.df.t_work[0][0][8]
            sec = self.df.t_work[0][0][6]
            aut = self.df.t_work[0][0][7]
            nam = self.df.t_work[0][0][9]
            pwd = self.df.t_work[0][0][10]
            err = sendMail([svr, prt, sec, aut, nam, pwd], "", "", "",
                check=True, wrkdir=self.opts["mf"].rcdic["wrkdir"])
            if err:
                showError(self.opts["mf"].body, "Error",
                    "Invalid SMTP Server or Authentication.\n\n%s" % err)
                self.df.focusField("T", 0, 6)
                return
        tme = time.localtime()
        data = copyList(self.df.t_work[0][0])
        if self.new:
            self.sql.insRec("ctlsys", data=data)
        elif data != self.acc[:len(data)]:
            self.sql.updRec("ctlsys", data=data)
            dte = int("%04i%02i%02i%02i%02i%02i" % tme[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["ctlsys", "U",
                        "%03i" % 0, self.sql.ctlsys_col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        # Reset all password dates to current date (Temporary Fix)
        dte = (tme[0] * 10000) + (tme[1] * 100) + tme[2]
        self.sql.updRec("ctlpwu", cols=["usr_last"], data=[dte])
        self.opts["mf"].dbm.commitDbase()
        self.doExit()

    def doAccept(self):
        frt, pag, col, mes = self.df.doCheckFields()
        if mes:
            self.df.focusField(frt, pag, (col+1), err=mes)
        else:
            self.df.doEndFrame("T", 0, cnf="N")

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
