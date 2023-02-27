"""
SYNOPSIS
    General Ledger Standard Journal Creation, Deletion and Amendments.

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

from TartanClasses import CCD, Sql, TartanDialog
from tartanFunctions import chkGenAcc, showInfo

class gl1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.buildScreen()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlvmf", "genmst", "genjlm",
            "genjlt"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.s_per = int(self.opts["period"][1][0] / 100)
        self.e_per = int(self.opts["period"][2][0] / 100)
        return True

    def buildScreen(self):
        num_sel = {
            "stype": "R",
            "tables": ("genjlm",),
            "cols": (
                ("gjm_num", "", 0, "Number"),
                ("gjm_desc", "", 0, "Description", "Y"),
                ("gjm_freq", "", 0, "Freq"),
                ("gjm_start", "", 0, "Start"),
                ("gjm_end", "", 0, "End")),
            "where": [("gjm_cono", "=", self.opts["conum"])]}
        seq_sel = {
            "stype": "R",
            "tables": ("genjlt",),
            "cols": (
                ("gjt_seq", "", 0, "Seq"),
                ("gjt_acno", "", 0, "Acc-Num"),
                ("gjt_amnt", "", 0, "Amount")),
            "where": [("gjt_cono", "=", self.opts["conum"])],
            "whera": (("T", "gjt_num", 0),)}
        acc_sel = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        fld = (
            (("T",0,0,0),"INa",9, "Number","Journal Number",
                "","Y",self.doNum,num_sel,None,("notblank",)),
            (("T",0,1,0),"INA",30,"Description","",
                "","N",self.doDesc,None,self.doDelNum,("notblank",)),
            (("T",0,2,0),"IUA",1, "Frequency","Frequency (M/3/6/Y)",
                "","N",self.doFreq,None,None,("in",("M","3","6","Y"))),
            (("T",0,3,0),"ID2",7, "Starting Period","",
                "","N",self.doStart,None,None,("efld",)),
            (("T",0,3,0),"ID2",7, "Ending Period","",
                "","N",self.doEnd,None,None,("efld",)),
            (("C",0,0,0),"IUI",3,"Seq","Sequence Number",
                "i","N",self.doSeq,seq_sel,None,("notzero",)),
            (("C",0,0,0),"IUI",7,"Acc-Num","Account Number",
                "","N",self.doAcc,acc_sel,self.doDelSeq,("efld",)),
            (("C",0,0,0),"ONA",30,"Description","",
                "","N",None,None,None,None),
            (("C",0,0,0),"IUA",1,"V","V.A.T. Indicator",
                "","N",self.doVat,None,None,("notblank",)),
            (("C",0,0,0),"ISD",13.2,"Value","Period Value",
                "","N",self.doValue,None,None,("efld",)))
        but = (
            ("Show Entries",seq_sel,None,0,("C",0,1),("C",0,2)),
            ("Show Total",None,self.doTotal,0,("C",0,1),("C",0,2)),
            ("Abort Journal",None,self.doAbort,0,("C",0,1),("T",0,1)))
        tnd = ((self.endTop,"y"),)
        txt = (self.exitTop,)
        cnd = ((self.endCol,"y"),)
        cxt = (self.exitCol,)
        self.df = TartanDialog(self.opts["mf"], eflds=fld,
            butt=but, tend=tnd, txit=txt, cend=cnd, cxit=cxt)

    def doNum(self, frt, pag, r, c, p, i, w):
        self.num = w
        self.old = self.sql.getRec("genjlm", where=[("gjm_cono", "=",
            self.opts["conum"]), ("gjm_num", "=", self.num)], limit=1)
        if not self.old:
            self.new_num = "y"
            self.nxtcol = 1
        else:
            d = self.sql.genjlm_col
            self.new_num = "n"
            self.df.loadEntry(frt, pag, p+1,
                    data=self.old[d.index("gjm_desc")])
            self.df.loadEntry(frt, pag, p+2,
                    data=self.old[d.index("gjm_freq")])
            self.df.loadEntry(frt, pag, p+3,
                    data=self.old[d.index("gjm_start")])
            self.df.loadEntry(frt, pag, p+4, data=self.old[d.index("gjm_end")])
            for x in range(3):
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, "disabled")

    def doDelNum(self):
        if self.new_num == "y":
            return
        self.sql.delRec("genjlm", where=[("gjm_cono", "=", self.opts["conum"]),
            ("gjm_num", "=", self.num)])
        try:
            self.sql.delRec("genjlt", where=[("gjt_cono", "=",
                self.opts["conum"]), ("gjt_num", "=", self.acc)])
        except:
            pass
        self.opts["mf"].dbm.commitDbase()

    def doDesc(self, frt, pag, r, c, p, i, w):
        self.desc = w

    def doFreq(self, frt, pag, r, c, p, i, w):
        self.freq = w

    def doStart(self, frt, pag, r, c, p, i, w):
        if w < self.s_per or w > self.e_per:
            return "Invalid Start Date"
        self.start = w

    def doEnd(self, frt, pag, r, c, p, i, w):
        if w < self.start or w > self.e_per:
            return "Invalid End Date"
        self.end = w

    def endTop(self):
        data = [self.opts["conum"], self.num, self.desc, self.freq, self.start,
            self.end, 0]
        if self.new_num == "y":
            self.sql.insRec("genjlm", data=data)
            self.df.loadEntry("C", 0, 0, data=1)
        else:
            if data != self.old[:len(data)]:
                col = self.sql.genjlm_col
                data.append(self.old[col.index("gjm_xflag")])
                self.sql.updRec("genjlm", data=data, where=[("gjm_cono",
                    "=", self.opts["conum"]), ("gjm_num", "=", self.num)])
            self.doReload()
        self.df.focusField("C", 0, self.nxtcol)

    def exitTop(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doSeq(self, frt, pag, r, c, p, i, w):
        self.seq = w
        self.seqdat = self.sql.getRec("genjlt", where=[("gjt_cono", "=",
            self.opts["conum"]), ("gjt_num", "=", self.num), ("gjt_seq", "=",
            self.seq)], limit=1)
        if not self.seqdat:
            self.new_seq = "y"
        else:
            self.new_seq = "n"
            col = self.sql.genjlt_col
            acc = self.seqdat[col.index("gjt_acno")]
            des = self.sql.getRec("genmst", cols=["glm_desc"],
                where=[("glm_cono", "=", self.opts["conum"]),
                ("glm_acno", "=", acc)], limit=1)[0]
            self.df.loadEntry(frt, pag, p+1,
                    data=acc)
            self.df.loadEntry(frt, pag, p+2,
                    data=des)
            self.df.loadEntry(frt, pag, p+3,
                    data=self.seqdat[col.index("gjt_vatc")])
            self.df.loadEntry(frt, pag, p+4,
                    data=self.seqdat[col.index("gjt_amnt")])

    def doDelSeq(self):
        if self.new_seq == "y":
            return
        self.sql.delRec("genjlt", where=[("gjt_cono", "=", self.opts["conum"]),
            ("gjt_num", "=", self.num), ("gjt_seq", "=", self.seq)])
        self.doReload()
        self.df.focusField("C", 0, self.nxtcol)

    def doAcc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        self.acc = w
        self.df.loadEntry(frt, pag, p+1, data=chk[0])
        self.df.loadEntry(frt, pag, p+2, data=chk[2])

    def doVat(self, frt, pag, r, c, p, i, w):
        vat = self.sql.getRec("ctlvmf", cols=["vtm_desc"],
            where=[
                ("vtm_cono", "=", self.opts["conum"]), ("vtm_code", "=", w)],
            limit=1)
        if not vat:
            return "Invalid VAT Code"
        self.vat = w

    def doValue(self, frt, pag, r, c, p, i, w):
        self.val = w

    def endCol(self):
        data = [self.opts["conum"], self.num,
            self.seq, self.acc, self.vat, self.val]
        if self.new_seq == "y":
            self.sql.insRec("genjlt", data=data)
        else:
            col = self.sql.genjlt_col
            data.append(self.seqdat[col.index("gjt_xflag")])
            self.sql.updRec("genjlt", data=data, where=[("gjt_cono",
                "=", self.opts["conum"]), ("gjt_num", "=", self.num),
                ("gjt_seq", "=", self.seq)])
        self.doReload()
        self.df.focusField("C", 0, self.nxtcol)

    def exitCol(self):
        tot = self.sql.getRec("genjlt", cols=["count(*)",
            "round(sum(gjt_amnt), 2)"], where=[("gjt_cono", "=",
            self.opts["conum"]), ("gjt_num", "=", self.num)], limit=1)
        if tot[0] and not tot[1]:
            self.opts["mf"].dbm.commitDbase()
            self.df.focusField("T", 0, 1)
        elif tot[1]:
            self.df.focusField("C", 0, self.df.col,
            err="Debits Not Equal Credits")
        else:
            self.opts["mf"].dbm.rollbackDbase()
            self.df.focusField("T", 0, 1)

    def doAbort(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

    def doReload(self):
        self.df.clearFrame("C", 0)
        last = (self.df.rows[0] - 1) * 5
        trn = self.sql.getRec(tables=["genjlt", "genmst"], cols=["gjt_seq",
            "gjt_acno", "glm_desc", "gjt_vatc", "gjt_amnt"],
            where=[("gjt_cono", "=", self.opts["conum"]), ("gjt_num", "=",
            self.num), ("glm_cono=gjt_cono",), ("glm_acno=gjt_acno",)],
            order="gjt_seq")
        if trn:
            for s, t in enumerate(trn):
                if s >= self.df.rows[0]:
                    self.df.scrollScreen(0)
                    p = last
                else:
                    p = s * 5
                self.df.loadEntry("C", 0, p, data=t[0])
                self.df.loadEntry("C", 0, p+1, data=t[1])
                self.df.loadEntry("C", 0, p+2, data=t[2])
                self.df.loadEntry("C", 0, p+3, data=t[3])
                self.df.loadEntry("C", 0, p+4, data=t[4])
        if p == last:
            self.df.scrollScreen(0)
            self.nxtcol = last + 1
        else:
            self.nxtcol = p + 6

    def doTotal(self):
        tot = self.sql.getRec("genjlt", cols=["round(sum(gjt_amnt),2)"],
            where=[("gjt_cono", "=", self.opts["conum"]), (
                "gjt_num", "=", self.num)],
            limit=1)
        if not tot[0]:
            tot = CCD(0, "SD", 15.2)
        else:
            tot = CCD(tot[0], "SD", 15.2)
        showInfo(self.opts["mf"].body, "Journal Total", tot.disp)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

# vim:set ts=4 sw=4 sts=4 expandtab:
