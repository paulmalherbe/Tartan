"""
SYNOPSIS
    Delete Records, gentrn, crstrn and drstrn.

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

import sys
sys.path.insert(0, "/home/paul/Tartan-6")
from TartanClasses import ASD, GetCtl, SChoice, Sql, TartanDialog
from tartanFunctions import chkGenAcc, copyList, showError
from tartanWork import crtrtp, drtrtp, gltrtp

class tb1050:
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        tabs = ["ctlmst", "ctlvtf", "gentrn", "crstrn", "crsage",
            "drstrn", "drsage"]
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        tit = "Delete Records"
        coy = {
            "stype": "R",
            "tables": ("ctlmst",),
            "cols": (
                ("ctm_cono", "", 0, "Coy"),
                ("ctm_name", "", 0, "Name")),
            "order": "ctm_cono"}
        sys = {
            "stype": "C",
            "titl": "Systems",
            "head": ("S", "Description"),
            "data": (
                ("C", "Creditor's Ledger"),
                ("D", "Debtor's Ledger"),
                ("G", "General Ledger"))}
        self.trntyp = None
        self.btt = {
            "stype": "C",
            "titl": "Valid Types",
            "data": []}
        self.btm = {
            "stype": "R",
            "tables": [],
            "cols": [],
            "where": [],
            "group": "",
            "order": "",
            "index": 1}
        fld = (
            (("T",0,0,0),"IUI",3,"Company Number","",
                1,"Y",self.doCoy,coy,None,("efld",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUA",1,"System","Originating System",
                "","N",self.doSys,sys,None,("in", ("C", "D", "G"))),
            (("T",0,1,0),"ONA",30,""),
            (("T",0,2,0),"IUI",1,"Type","Transaction Type",
                "","N",self.doRtn,self.btt,None,None),
            (("T",0,2,0),"ONA",30,""),
            (("T",0,3,0),"ID2",7,"Period","Financial Period",
                "","N",self.doCdt,None,None,("efld",)),
            (("T",0,4,0),"INa",7,"Batch","Batch Number",
                "","N",self.doBat,self.btm,None,None))
        but = (("Exit", None, self.doExit, 0, ("T",0,1), ("T",0,0)),)
        tnd = ((self.doEnd,"y"),)
        txt = (self.doExit,)
        self.df = TartanDialog(self.opts["mf"], tops=False, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt)

    def doCoy(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlmst", where=[("ctm_cono", "=", w)], limit=1)
        if not acc:
            return "Invalid Company"
        self.cono = w
        self.df.loadEntry(frt, pag, p+1,
            data=acc[self.sql.ctlmst_col.index("ctm_name")])
        gc = GetCtl(self.opts["mf"])
        ctlctl = gc.getCtl("ctlctl", self.cono)
        if not ctlctl:
            return
        self.ctls = []
        self.clint = bool(gc.getCtl("crsctl", self.cono)["ctc_glint"] == "Y")
        if self.clint:
            self.ctls.append(ctlctl["crs_ctl"])
        self.dlint = bool(gc.getCtl("drsctl", self.cono)["ctd_glint"] == "Y")
        if self.dlint:
            self.ctls.append(ctlctl["drs_ctl"])

    def doSys(self, frt, pag, r, c, p, i, w):
        self.sys = w
        if w == "C":
            self.table = "crstrn"
            self.trntyp = copyList(crtrtp)
            self.df.loadEntry(frt, pag, p+1, data="Creditors Ledger")
        elif w == "D":
            self.table = "drstrn"
            self.trntyp = copyList(drtrtp)
            self.df.loadEntry(frt, pag, p+1, data="Debtors Ledger")
        elif w == "G":
            self.table = "gentrn"
            self.trntyp = copyList(gltrtp)
            self.df.loadEntry(frt, pag, p+1, data="General Ledger")
        self.btt["data"] = []
        for seq, typ in enumerate(self.trntyp):
            self.btt["data"].append((seq+1, typ[1]))

    def doRtn(self, frt, pag, r, c, p, i, w):
        self.rtn = w
        self.df.loadEntry(frt, pag, p+1, data=self.trntyp[w-1][1])

    def doCdt(self, frt, pag, r, c, p, i, w):
        self.cdt = w
        if self.sys == "G" and self.rtn == 7:
            rtyp = (2, 6)
        else:
            rtyp = self.rtn
        if self.sys == "G":
            self.btm["tables"] = ["gentrn"]
            self.btm["cols"] = [
                    ("glt_curdt", "", 0, "Cur-Dte"),
                    ("glt_batch", "", 0, "Bat-Num")]
            self.btm["where"] = [
                    ("glt_cono", "=", self.cono),
                    ("glt_curdt", "=", self.cdt),
                    ("glt_type", "=", rtyp)]
            self.btm["group"] = "glt_curdt, glt_batch"
            self.btm["order"] = "glt_curdt, glt_batch"
        elif self.sys == "C":
            self.btm["tables"] = ["crstrn"]
            self.btm["cols"] = [
                    ("crt_curdt", "", 0, "Cur-Dte"),
                    ("crt_batch", "", 0, "Bat-Num")]
            self.btm["where"] = [
                    ("crt_cono", "=", self.cono),
                    ("crt_curdt", "=", self.cdt),
                    ("crt_type", "=", rtyp)]
            self.btm["group"] = "crt_curdt, crt_batch"
            self.btm["order"] = "crt_curdt, crt_batch"
        elif self.sys == "D":
            self.btm["tables"] = ["drstrn"]
            self.btm["cols"] = [
                    ("drt_curdt", "", 0, "Cur-Dte"),
                    ("drt_batch", "", 0, "Bat-Num")]
            self.btm["where"] = [
                    ("drt_cono", "=", self.cono),
                    ("drt_curdt", "=", self.cdt),
                    ("drt_type", "=", rtyp)]
            self.btm["group"] = "drt_curdt, drt_batch"
            self.btm["order"] = "drt_curdt, drt_batch"

    def doBat(self, frt, pag, r, c, p, i, w):
        self.bat = w
        head = []
        typs = []
        if self.sys == "C":
            col = self.sql.crstrn_col[:15]
            col.append("crt_seq")
            for key in col:
                head.append(self.sql.crstrn_dic[key][5])
                typs.append(self.sql.crstrn_dic[key][2:4])
            whr = [
                ("crt_cono", "=", self.cono),
                ("crt_type", "=", self.rtn),
                ("crt_batch", "=", self.bat),
                ("crt_curdt", "=", self.cdt)]
        elif self.sys == "D":
            col = self.sql.drstrn_col[:12]
            col.append("drt_seq")
            for key in col:
                head.append(self.sql.drstrn_dic[key][5])
                typs.append(self.sql.drstrn_dic[key][2:4])
            whr = [
                ("drt_cono", "=", self.cono),
                ("drt_type", "=", self.rtn),
                ("drt_batch", "=", self.bat),
                ("drt_curdt", "=", self.cdt)]
        elif self.sys == "G":
            col = self.sql.gentrn_col[:10]
            col.append("glt_seq")
            for key in col:
                head.append(self.sql.gentrn_dic[key][5])
                typs.append(self.sql.gentrn_dic[key][2:4])
            whr = [
                ("glt_cono", "=", self.cono),
                ("glt_curdt", "=", self.cdt)]
            if self.rtn == 7:
                whr.append(("glt_type", "in", (2, 6)))
            else:
                whr.append(("glt_type", "=", self.rtn))
            whr.append(("glt_batch", "=", self.bat))
        recs = self.sql.getRec(self.table, cols=col, where=whr)
        if not recs:
            return "No Records"
        typs.insert(0, ["CB", 0])
        sc = SChoice(self.opts["mf"], titl="Select Records", head=head,
            data=recs, typs=typs, mode="M")
        if sc.selection:
            self.recs = sc.selection
        else:
            return "Invalid Batch"

    def doEnd(self):
        self.df.closeProcess()
        qtot = 0
        gamt = 0
        for rec in self.recs:
            err = []
            if self.sys == "G":
                if not self.sql.getRec("gentrn",
                        where=[("glt_seq", "=", rec[-1])], limit=1):
                    continue
                acno = rec[self.sql.gentrn_col.index("glt_acno")]
                if acno not in self.ctls:
                    chk = chkGenAcc(self.opts["mf"], self.cono, acno, pwd=False)
                    if type(chk) is str:
                        err.append(chk)
                date = rec[self.sql.gentrn_col.index("glt_trdt")]
                docno = rec[self.sql.gentrn_col.index("glt_refno")]
                self.rtn = rec[self.sql.gentrn_col.index("glt_type")]
                gtyp = self.rtn
            elif self.sys == "C":
                date = rec[self.sql.crstrn_col.index("crt_trdt")]
                docno = rec[self.sql.crstrn_col.index("crt_ref1")]
                if self.rtn in (1, 4):
                    gtyp = 5                    # Purchase
                elif self.rtn == 2:
                    gtyp = 6                    # Receipt
                elif self.rtn == 3:
                    gtyp = 4                    # Journal
                elif self.rtn == 5:
                    gtyp = 2                    # Payment
            else:
                date = rec[self.sql.drstrn_col.index("drt_trdt")]
                docno = rec[self.sql.drstrn_col.index("drt_ref1")]
                if self.rtn in (1, 4):
                    gtyp = 1                    # Sale
                elif self.rtn == 2:
                    gtyp = 6                    # Receipt
                elif self.rtn == 3:
                    gtyp = 4                    # Journal
                elif self.rtn == 5:
                    gtyp = 2                    # Payment
            sqv = [
                ("vtt_cono", "=", self.cono),
                ("vtt_curdt", "=", self.cdt),
                ("vtt_styp", "=", self.sys),
                ("vtt_refno", "=", docno),
                ("vtt_refdt", "=", date),
                ("vtt_ttyp", "=", self.rtn),
                ("vtt_batch", "=", self.bat)]
            vrecs = self.sql.getRec("ctlvtf", where=sqv)
            texc = 0
            ttax = 0
            for vrec in vrecs:
                if vrec[self.sql.ctlvtf_col.index("vtt_exc")]:
                    err.append("Transactions in V.A.T. Return")
                    break
                texc = float(ASD(texc) + \
                    ASD(vrec[self.sql.ctlvtf_col.index("vtt_exc")]))
                ttax = float(ASD(ttax) + \
                    ASD(vrec[self.sql.ctlvtf_col.index("vtt_tax")]))
            if err:
                break
            ttot = float(ASD(texc) + ASD(ttax))
            if self.sys == "G" or self.clint or self.dlint:
                sqg = [
                    ("glt_cono", "=", self.cono),
                    ("glt_curdt", "=", self.cdt),
                    ("glt_batch", "=", self.bat),
                    ("glt_refno", "=", docno),
                    ("glt_trdt", "=", date),
                    ("glt_type", "=", gtyp)]
                if self.sys == "G":
                    grecs = self.sql.getRec("gentrn", where=sqg)
                    gtax = 0
                    for grec in grecs:
                        gtax = float(ASD(gtax) + ASD(grec[8]))
                    if gtax != ttax:
                        err.append("ctlvtf %s <> gentrn %s" % (ttax, gtax))
            if self.sys == "C" or (self.sys == "G" and self.clint):
                sct = [
                    ("crt_cono", "=", self.cono),
                    ("crt_type", "=", self.rtn),
                    ("crt_batch", "=", self.bat),
                    ("crt_curdt", "=", self.cdt),
                    ("crt_ref1", "=", docno),
                    ("crt_trdt", "=", date)]
                sca1 = [
                    ("cra_cono", "=", self.cono),
                    ("cra_type", "=", self.rtn),
                    ("cra_ref1", "=", docno)]
                sca2 = [
                    ("cra_cono", "=", self.cono),
                    ("cra_atyp", "=", self.rtn),
                    ("cra_aref", "=", docno)]
                if self.sys == "C":
                    crecs = self.sql.getRec("crstrn", where=sct)
                    camt = 0
                    ctax = 0
                    for crec in crecs:
                        camt = float(ASD(camt) + ASD(crec[7]))
                        ctax = float(ASD(ctax) + ASD(crec[8]))
                    if ctax != ttax:
                        err.append("tax ctlvtf %s <> crstrn %s" % (ttax, ctax))
                    if ctax and camt != ttot:
                        err.append("tot ctlvtf %s <> crstrn %s" % (ttot, camt))
            if self.sys == "D" or (self.sys == "G" and self.dlint):
                sdt = [
                    ("drt_cono", "=", self.cono),
                    ("drt_type", "=", self.rtn),
                    ("drt_batch", "=", self.bat),
                    ("drt_curdt", "=", self.cdt),
                    ("drt_ref1", "=", docno),
                    ("drt_trdt", "=", date)]
                sda1 = [
                    ("dra_cono", "=", self.cono),
                    ("dra_type", "=", self.rtn),
                    ("dra_ref1", "=", docno)]
                sda2 = [
                    ("dra_cono", "=", self.cono),
                    ("dra_atyp", "=", self.rtn),
                    ("dra_aref", "=", docno)]
                if self.sys == "D":
                    drecs = self.sql.getRec("drstrn", where=sdt)
                    damt = 0
                    dtax = 0
                    for drec in drecs:
                        damt = float(ASD(damt) - ASD(drec[8]))
                        dtax = float(ASD(dtax) - ASD(drec[9]))
                    if dtax != ttax:
                        err.append("tax ctlvtf %s <> drstrn %s" % (ttax, ctax))
                    if dtax and damt != ttot:
                        err.append("tot ctlvtf %s <> drstrn %s" % (ttot, damt))
            if err:
                break
            self.sql.delRec("ctlvtf", where=sqv)
            if self.sys == "G" or self.clint or self.dlint:
                if self.sys == "G":
                    qtot += self.sql.getRec("gentrn", cols=["count(*)"],
                        where=sqg, limit=1)[0]
                amnt = self.sql.getRec("gentrn", cols=["sum(glt_tramt)"],
                    where=sqg, limit=1)
                if amnt[0]:
                    gamt = float(ASD(gamt) + ASD(amnt[0]))
                self.sql.delRec("gentrn", where=sqg)
            if self.sys == "C" or (self.sys == "G" and self.clint):
                if self.sys == "C":
                    qtot += self.sql.getRec("crstrn", cols=["count(*)"],
                        where=sct, limit=1)[0]
                self.sql.delRec("crstrn", where=sct)
                self.sql.delRec("crsage", where=sca1)
                self.sql.delRec("crsage", where=sca2)
            if self.sys == "D" or (self.sys == "G" and self.dlint):
                if self.sys == "D":
                    qtot += self.sql.getRec("drstrn", cols=["count(*)"],
                        where=sdt, limit=1)[0]
                self.sql.delRec("drstrn", where=sdt)
                self.sql.delRec("drsage", where=sda1)
                self.sql.delRec("drsage", where=sda2)
        if gamt:
            err.append("gentrn debits <> credits")
        if err:
            mess = ""
            for txt in err:
                mess = "%s\n%s" % (mess, txt)
            mess = "%s\n\nNo Transactions Deleted." % mess
            showError(self.opts["mf"].window, "Error", mess)
            self.opts["mf"].dbm.rollbackDbase()
        else:
            mess = "%s Transactions are being Deleted\n\n"\
                "Would you like to COMMIT Deletions?" % qtot
            self.opts["mf"].dbm.commitDbase(ask=True, mess=mess, default="no")
        self.opts["mf"].closeLoop()
    
    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

if __name__ == "__main__":
    import getopt
    from TartanClasses import Dbase, MainFrame
    from tartanFunctions import loadRcFile
    rcf = "/home/paul/rcf/testrc"
    opts, args = getopt.getopt(sys.argv[1:], "r:")
    for o, v in opts:
        if o == "-r":
            rcf = v
    mf = MainFrame(rcdic=loadRcFile(rcf))
    mf.dbm = Dbase(rcdic=mf.rcdic, screen=mf.window)
    mf.dbm.openDbase()
    tb1050(**{"mf": mf})
    mf.dbm.closeDbase()

# vim:set ts=4 sw=4 sts=4 expandtab:
