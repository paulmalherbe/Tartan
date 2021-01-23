"""
SYNOPSIS
    Point of Sales Master File Maintenance.

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

import os, socket, sys, time
from TartanClasses import CCD, GetCtl, Sql, TartanDialog
from tartanFunctions import getPrinters

class psc110(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.drawDialog()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["posdev", "tplmst", "chglog",
            "strloc"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        gc = GetCtl(self.opts["mf"])
        strctl = gc.getCtl("strctl", self.opts["conum"])
        if not strctl:
            return
        self.locs = strctl["cts_locs"]
        self.hosts = self.doGetHosts()
        return True

    def doGetHosts(self):
        hosts = []
        if sys.platform == "win32":
            out = os.popen("net view").readlines()
            for line in out:
                if line.strip().startswith("\\"):
                    hh = line[2:line.find(" ")].strip()
                    try:
                        hosts.append([hh, socket.gethostbyname(hh), ""])
                    except:
                        pass
        else:
            hh = socket.gethostname()
            hosts.append([hh, socket.gethostbyname(hh), ""])
            out = os.popen("ip neigh").readlines()
            for line in out:
                ip = line.strip().split()[0]
                try:
                    hh = socket.gethostbyaddr(ip)[0]
                    hosts.append([hh, ip, ""])
                except:
                    pass
        hosts.sort()
        for host in hosts:
            chk = self.sql.getRec("posdev", where=[("psd_cono", "=",
                self.opts["conum"]), ("psd_host", "=", host[0])], limit=1)
            if chk:
                txt = " Yes"
            else:
                txt = "  No"
            host[0] = CCD(host[0], "NA", 15).disp
            host[1] = CCD(host[1], "NA", 20).disp
            host[2] = CCD(txt, "NA", 4).disp
        return hosts

    def drawDialog(self):
        hst = {
            "stype": "C",
            "titl": "Valid Terminals",
            "head": ["Terminal-Name", "IP-Address", "Used"],
            "data": self.hosts,
            "sort": True,
            "index": 0}
        loc = {
            "stype": "R",
            "tables": ("strloc",),
            "cols": (
                ("srl_loc", "", 0, "L"),
                ("srl_desc", "", 0, "Description", "Y")),
            "where": [("srl_cono", "=", self.opts["conum"])],
            "order": "srl_loc"}
        prts = getPrinters(wrkdir=self.opts["mf"].rcdic["wrkdir"])
        prt = {
            "stype": "C",
            "titl": "Valid Printers",
            "data": prts}
        tpl = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "where": [
                ("tpm_type", "=", "J"),
                ("tpm_system", "=", "POS")],
            "order": "tpm_tname"}
        r1s = (("Yes", "Y"), ("No", "N"))
        r2s = (("Yes", "Y"), ("No", "N"), ("Ask", "A"))
        r3s = (("Slip", "S"), ("Invoice", "I"))
        self.fld = (
            (("T",0,0,0),"ITX",15,"Terminal Name","",
                "","Y",self.doHstNam,hst,None,("notblank",)),
            (("T",0,1,0),"IUA",1,"Location","",
                "","N",self.doLocCod,loc,None,("notblank",)),
            (("T",0,1,0),"ONA",20,""),
            (("T",0,2,0),("IRB",r1s),0,"Full Screen","",
                "Y","N",None,None,None,None),
            (("T",0,3,0),("IRB",r2s),0,"Print Document","",
                "Y","N",self.doPrtDoc,None,None,None),
            (("T",0,4,0),("IRB",r3s),0,"Document Type","",
                "S","N",self.doDocTyp,None,None,None),
            (("T",0,5,0),"ITX",30,"Printer Name","",
                "Default","N",self.doPrtNam,prt,None,("in",prts)),
            (("T",0,6,0),"IUI",1,"Paper Width (8/6)","",
                8,"N",self.doPrtWid,None,None,("in", (8, 6))),
            (("T",0,7,0),"INa",3,"Cut Paper Code","",
                "","N",self.doDecCod,prt,None,None),
            (("T",0,7,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,7,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,7,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,7,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,8,0),"INa",3,"Open Draw Code","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,8,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,8,0),"INa",3,"","",
                "0","N",self.doDecCod,None,None,None),
            (("T",0,8,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,8,0),"INa",3,"","",
                "","N",self.doDecCod,None,None,None),
            (("T",0,9,0),"INA",20,"Document Template","",
                "pos_slip_8","N",self.doTplNam,tpl,None,None))
        but = (
            ("Accept",None,self.doAccept,0,("T",0,2),("T",0,1)),
            ("Quit",None,self.doExit,1,None,None))
        tnd = ((self.doEnd,"Y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doHstNam(self, frt, pag, r, c, p, i, w):
        found = False
        for host in self.hosts:
            if w == host[0].strip():
                found = True
                break
        if not found:
            return "Invalid Terminal"
        self.acc = self.sql.getRec("posdev", where=[("psd_cono",
            "=", self.opts["conum"]), ("psd_host", "=", w)], limit=1)
        if not self.acc:
            self.new = True
            if self.locs == "N":
                self.loc = "1"
                des = self.sql.getRec("strloc",
                    cols=["srl_desc"],
                    where=[
                        ("srl_cono", "=", self.opts["conum"]),
                        ("srl_loc", "=", "1")], limit=1)
                self.df.loadEntry(frt, pag, p+1, data=self.loc)
                self.df.loadEntry(frt, pag, p+2, data=des[0])
                return "sk2"
        else:
            self.new = False
            for num, dat in enumerate(self.acc[2:-1]):
                self.df.loadEntry(frt, pag, p+num+1, data=dat)

    def doLocCod(self, frt, pag, r, c, p, i, w):
        des = self.sql.getRec("strloc", cols=["srl_desc"],
            where=[("srl_cono", "=", self.opts["conum"]),
            ("srl_loc", "=", w)], limit=1)
        if not des:
            return "Invalid Location"
        self.loc = w
        self.df.loadEntry(frt, pag, p+1, data=des[0])

    def doPrtDoc(self, frt, pag, r, c, p, i, w):
        if w == "N":
            for x in range(14):
                self.df.loadEntry(frt, pag, p+1+x, data="")
            return "sk14"

    def doDocTyp(self, frt, pag, r, c, p, i, w):
        self.dtp = w

    def doPrtNam(self, frt, pag, r, c, p, i, w):
        if self.dtp == "I":
            self.df.t_work[0][0][18] = "pos_invoice"
            for x in range(11):
                self.df.loadEntry(frt, pag, p+1+x, data="")
            return "sk11"

    def doPrtWid(self, frt, pag, r, c, p, i, w):
        if w == "6":
            self.df.t_work[0][0][18] = "pos_slip_6"
        else:
            self.df.t_work[0][0][18] = "pos_slip_8"

    def doDecCod(self, frt, pag, r, c, p, i, w):
        if not w:
            if p < 13:
                m = 13
            else:
                m = 18
            skp = 0
            for x in range(p + 1, m):
                skp += 1
                self.df.loadEntry(frt, pag, x, data="")
            return "sk%s" % skp

    def doTplNam(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w),
            ("tpm_type", "=", "J"), ("tpm_system", "=", "POS")], limit=1)
        if not acc:
            return "Invalid Template Name"

    def doEnd(self):
        data = [self.opts["conum"]]
        for x in range(len(self.df.t_work[0][0])):
            data.append(self.df.t_work[0][0][x])
        self.sql.delRec("posdev", where=[("psd_cono", "=", data[0]),
            ("psd_host", "=", data[1])])
        if self.new:
            data.append("")
        else:
            col = self.sql.posdev_col
            data.append(self.acc[col.index("psd_xflag")])
        self.sql.insRec("posdev", data=data)
        if not self.new and data != self.acc:
            dte = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
            for num, dat in enumerate(self.acc):
                if dat != data[num]:
                    self.sql.insRec("chglog", data=["posdev", "U",
                        "%03i" % self.opts["conum"], col[num], dte,
                        self.opts["capnm"], str(dat), str(data[num]),
                        "", 0])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

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
