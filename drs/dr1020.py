"""
SYNOPSIS
    Debtors Ledger Recurring Charges Creation, Deletion and Amendments.

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
from tartanFunctions import chkGenAcc

class dr1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.buildScreen()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "drschn", "drsmst",
            "drsrcm", "drsrct", "genmst"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.gc = GetCtl(self.opts["mf"])
        ctlmst = self.gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        if not self.taxdf:
            self.taxdf = "N"
        drsctl = self.gc.getCtl("drsctl", self.opts["conum"])
        if not drsctl:
            return
        self.glint = drsctl["ctd_glint"]
        self.chains = drsctl["ctd_chain"]
        self.glac = 0
        if self.glint == "Y":
            ctlctl = self.gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = ["drs_ctl", "vat_ctl", "dis_all"]
            if self.gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        return True

    def buildScreen(self):
        num_sel = {
            "stype": "R",
            "tables": ("drsrcm",),
            "cols": (
                ("dcm_num", "", 0, "Number"),
                ("dcm_desc", "", 0, "Description", "Y"),
                ("dcm_freq", "", 0, "F")),
            "where": [("dcm_cono", "=", self.opts["conum"])]}
        seq_sel = {
            "stype": "R",
            "tables": ("drsrct",),
            "cols": (
                ("dct_seq", "", 0, "Seq"),
                ("dct_chain", "", 0, "Chn"),
                ("dct_acno", "", 0, "Acc-Num"),
                ("dct_detail", "", 0, "Charge Details"),
                ("dct_amnt", "", 0, "Amount"),
                ("dct_start", "", 0, "Start"),
                ("dct_end", "", 0, "End")),
            "where": [("dct_cono", "=", self.opts["conum"])],
            "whera": (("T", "dct_num", 0),)}
        chn_sel = {
            "stype": "R",
            "tables": ("drschn",),
            "cols": (
                ("chm_chain", "", 0, "Num"),
                ("chm_name", "", 0, "Name", "Y")),
            "where": [("chm_cono", "=", self.opts["conum"])]}
        drm_sel = {
            "stype": "R",
            "tables": ("drsmst",),
            "cols": (
                ("drm_acno", "", 0, "Acc-Num"),
                ("drm_name", "", 0, "Name", "Y")),
            "where": [
                ("drm_cono", "=", self.opts["conum"]),
                ("drm_stat", "<>", "X")],
            "whera": (("C", "drm_chain", 1, 0),)}
        glm_sel = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        vat_sel = {
            "stype": "R",
            "tables": ("ctlvmf",),
            "cols": (
                ("vtm_code", "", 0, "C"),
                ("vtm_desc", "", 0, "Description", "Y")),
            "where": [("vtm_cono", "=", self.opts["conum"])]}
        r1s = (
            ("Monthly","M"),
            ("Quarterly","3"),
            ("Bi-Annually","6"),
            ("Annually","Y"))
        fld = [
            (("T",0,0,0),"IUI",3, "Number","Charge Number",
                "","Y",self.doNum,num_sel,None,None),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",self.doDesc,None,self.doDelNum,("notblank",)),
            (("T",0,2,0),("IRB",r1s),0, "Frequency","",
                "M","N",self.doFreq,None,None,None),
            (("T",0,3,0),"IUI",2, "Day of the Month","Day of the Month",
                "","N",self.doDay,num_sel,None,("between",1,30),None,
                "Enter the day of the month when the entry must be raised. "\
                "Use 30 to denote the last day of the month.")]
        if self.glint == "Y":
            fld.append((("T",0,4,0),"IUI",7,"Charge Account","G/L Account",
                "","N",self.doGlAc,glm_sel,None,("notzero",)))
            fld.append((("T",0,4,0),"ONA",30,""))
            nxt = 5
        else:
            nxt = 4
        fld.append((("T",0,nxt,0),"IUA",1,"VAT Code","V.A.T. Code",
                self.taxdf,"N",self.doVat,vat_sel,None,("notblank",)))
        fld.append((("C",0,0,0),"IUI",3,"Seq","Sequence Number",
                "i","N",self.doSeq,seq_sel,None,("notzero",)))
        if self.chains == "Y":
            fld.append((("C",0,0,0),"IUI",3,"Chn","Chain Store",
                "","N",self.doChn,chn_sel,self.doDelSeq,("efld",)))
        else:
            self.chn = 0
            fld.append((("C",0,0,0),"OUI",3,"Chn"))
        fld.append((("C",0,0,1),"INA",7,"Acc-Num","Account Number",
            "","N",self.doAcc,drm_sel,self.doDelSeq,("efld",)))
        fld.extend((
            (("C",0,0,2),"ONA",30,"Name","",
                "","N",None,None,None,None),
            (("C",0,0,3),"ITX",30,"Charge-Details","Charge Details",
                "","N",self.doDetail,None,None,None),
            (("C",0,0,4),"ISD",13.2,"Excl-Value","Period Exclusive Value",
                "","N",self.doValue,None,None,("efld",)),
            (("C",0,0,5),"ID2",7, "Start","Starting Period",
                "","N",self.doStart,None,None,("efld",)),
            (("C",0,0,6),"ID2",7, "End","Ending Period",
                "","N",self.doEnd,None,None,("efld",))))
        but = (
            ("All Entries",seq_sel,None,0,
                ("C",0,1),(("T",0,1),("C",0,2))),
            ("Re-Sequence",None,self.doReSeq,0,
                ("C",0,1),(("T",0,1),("C",0,2))),
            ("Abort Changes",None,self.doAbort,0,
                ("C",0,1),("T",0,1)))
        tnd = ((self.endTop,"y"),)
        txt = (self.exitTop,)
        cnd = ((self.endCol,"y"),)
        cxt = (self.exitCol,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doNum(self, frt, pag, r, c, p, i, w):
        if not w:
            num = self.sql.getRec("drsrcm", cols=["max(dcm_num)"],
                where=[("dcm_cono", "=", self.opts["conum"])], limit=1)
            if not num or not num[0]:
                self.num = 1
            else:
                self.num = num[0] + 1
            self.df.loadEntry(frt, pag, p, data=self.num)
        else:
            self.num = w
        self.rcm = self.sql.getRec("drsrcm", where=[("dcm_cono", "=",
            self.opts["conum"]), ("dcm_num", "=", self.num)], limit=1)
        if not self.rcm:
            if self.num == 999:
                return "Invalid Number (999), Reserved for Sales Invoices"
            self.new_num = "y"
            self.nxt = 1
        else:
            d = self.sql.drsrcm_col
            self.new_num = "n"
            self.df.loadEntry(frt, pag, p+1,
                    data=self.rcm[d.index("dcm_desc")])
            self.df.loadEntry(frt, pag, p+2,
                    data=self.rcm[d.index("dcm_freq")])
            self.df.loadEntry(frt, pag, p+3,
                    data=self.rcm[d.index("dcm_day")])
            if self.glint == "Y":
                self.df.loadEntry(frt, pag, p+4,
                        data=self.rcm[d.index("dcm_glac")])
                self.df.loadEntry(frt, pag, p+5,
                        data=self.getAccount())
                self.df.loadEntry(frt, pag, p+6,
                        data=self.rcm[d.index("dcm_vat")])
            else:
                self.df.loadEntry(frt, pag, p+4,
                        data=self.rcm[d.index("dcm_vat")])
            for x in range(2):
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, "disabled")
        if self.num == 999:
            return "nd"

    def getAccount(self):
        return self.sql.getRec("genmst", cols=["glm_desc"],
            where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", self.df.t_work[0][0][4])], limit=1)[0]

    def doDelNum(self):
        if self.new_num == "y":
            return
        self.sql.delRec("drsrcm", where=[("dcm_cono", "=", self.opts["conum"]),
            ("dcm_num", "=", self.num)])
        try:
            self.sql.delRec("drsrct", where=[("dct_cono", "=",
                self.opts["conum"]), ("dct_num", "=", self.acc)])
        except:
            pass

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w
        if self.glint == "N":
            self.vcod = self.taxdf

    def doDay(self, frt, pag, r, c, p, i, w):
        self.day = w

    def doGlAc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        self.glac = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        if not chk[2]:
            self.vcod = self.taxdf
        else:
            self.vcod = chk[2]
        self.df.topf[0][4][8] = self.vcod

    def doVat(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=",
            w)], limit=1)
        if not acc:
            return "Invalid VAT Code"
        self.vcod = w

    def endTop(self):
        data = [self.opts["conum"], self.num, self.desc, self.freq, self.day,
            self.vcod, self.glac]
        if self.new_num == "y":
            self.sql.insRec("drsrcm", data=data)
            self.df.loadEntry("C", 0, 0, data=1)
            self.df.focusField("C", 0, self.nxt)
        else:
            if data != self.rcm[:len(data)]:
                col = self.sql.drsrcm_col
                data.append(self.rcm[col.index("dcm_last")])
                data.append(self.rcm[col.index("dcm_xflag")])
                self.sql.updRec("drsrcm", data=data, where=[("dcm_cono", "=",
                    self.opts["conum"]), ("dcm_num", "=", self.num)])
            self.doReload()

    def exitTop(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doSeq(self, frt, pag, r, c, p, i, w):
        self.seq = w
        self.rct = self.sql.getRec("drsrct", where=[("dct_cono", "=",
            self.opts["conum"]), ("dct_num", "=", self.num), ("dct_seq", "=",
            self.seq)], limit=1)
        if not self.rct:
            self.new_seq = "y"
        else:
            self.new_seq = "n"
            col = self.sql.drsrct_col
            self.df.loadEntry(frt, pag, p+1,
                    data=self.rct[col.index("dct_chain")])
            self.df.loadEntry(frt, pag, p+2,
                    data=self.rct[col.index("dct_acno")])
            acc = self.sql.getRec("drsmst", cols=["drm_name"],
                where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain",
                "=", self.rct[col.index("dct_chain")]), ("drm_acno", "=",
                self.rct[col.index("dct_acno")])], limit=1)
            self.df.loadEntry(frt, pag, p+3,
                    data=acc[0])
            self.df.loadEntry(frt, pag, p+4,
                    data=self.rct[col.index("dct_detail")])
            self.df.loadEntry(frt, pag, p+5,
                    data=self.rct[col.index("dct_amnt")])
            self.df.loadEntry(frt, pag, p+6,
                    data=self.rct[col.index("dct_start")])
            self.df.loadEntry(frt, pag, p+7,
                    data=self.rct[col.index("dct_end")])

    def doDelSeq(self):
        if self.new_seq == "y":
            return
        self.sql.delRec("drsrct", where=[("dct_cono", "=", self.opts["conum"]),
            ("dct_num", "=", self.num), ("dct_seq", "=", self.seq)])
        self.doReload()

    def doChn(self, frt, pag, r, c, p, i, w):
        if w:
            acc = self.sql.getRec("drschn", where=[("chm_cono", "=",
                self.opts["conum"]), ("chm_chain", "=", w)], limit=1)
            if not acc:
                return "Invalid Chain Store"
        self.chn = w

    def doAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("drsmst", cols=["drm_name", "drm_stat"],
            where=[("drm_cono", "=", self.opts["conum"]), ("drm_chain", "=",
            self.chn), ("drm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number"
        if acc[1] == "X":
            return "Invalid Account, Redundant"
        self.acc = w
        self.df.loadEntry(frt, pag, p+1, data=acc[0])

    def doDetail(self, frt, pag, r, c, p, i, w):
        self.det = w

    def doValue(self, frt, pag, r, c, p, i, w):
        self.val = w

    def doStart(self, frt, pag, r, c, p, i, w):
        self.start = w

    def doEnd(self, frt, pag, r, c, p, i, w):
        if w < self.start:
            return "Invalid End Date, Before Start"
        self.end = w

    def endCol(self):
        data = [self.opts["conum"], self.num, self.seq, self.chn, self.acc,
            self.det, self.val, self.start, self.end]
        if self.new_seq == "y":
            self.sql.insRec("drsrct", data=data)
        elif data != self.rct[:len(data)]:
            col = self.sql.drsrct_col
            data.append(self.rct[col.index("dct_xflag")])
            self.sql.updRec("drsrct", data=data, where=[("dct_cono", "=",
                self.opts["conum"]), ("dct_num", "=", self.num), ("dct_seq",
                "=", self.seq)])
        self.doReload()

    def exitCol(self):
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doReSeq(self):
        recs = self.sql.getRec("drsrct", where=[("dct_cono", "=",
            self.opts["conum"]), ("dct_num", "=", self.num)],
            order="dct_chain, dct_acno")
        self.sql.delRec("drsrct", where=[("dct_cono", "=", self.opts["conum"]),
            ("dct_num", "=", self.num)])
        seq = 0
        for rec in recs:
            seq += 1
            rec[2] = seq
            self.sql.insRec("drsrct", data=rec)
        self.doReload()

    def doAbort(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doReload(self):
        self.df.clearFrame("C", 0)
        last = (self.df.rows[0] - 1) * 8
        trn = self.sql.getRec(tables=["drsrct", "drsmst"], cols=["dct_seq",
            "dct_chain", "dct_acno", "drm_name", "dct_detail", "dct_amnt",
            "dct_start", "dct_end"], where=[("dct_cono", "=",
            self.opts["conum"]), ("dct_num", "=", self.num),
            ("drm_cono=dct_cono",), ("drm_chain=dct_chain",),
            ("drm_acno=dct_acno",)], order="dct_seq")
        if trn:
            for s, t in enumerate(trn):
                if s >= self.df.rows[0]:
                    self.df.scrollScreen(0)
                    p = last
                else:
                    p = s * 8
                self.df.loadEntry("C", 0, p, data=t[0])
                self.df.loadEntry("C", 0, p+1, data=t[1])
                self.df.loadEntry("C", 0, p+2, data=t[2])
                self.df.loadEntry("C", 0, p+3, data=t[3])
                self.df.loadEntry("C", 0, p+4, data=t[4])
                self.df.loadEntry("C", 0, p+5, data=t[5])
                self.df.loadEntry("C", 0, p+6, data=t[6])
                self.df.loadEntry("C", 0, p+7, data=t[7])
            if p == last:
                self.df.scrollScreen(0)
                self.nxt = last + 1
            else:
                self.nxt = p + 9
        else:
            self.nxt = 1
        self.df.focusField("C", 0, self.nxt)

# vim:set ts=4 sw=4 sts=4 expandtab:
