"""
SYNOPSIS
    Tables Data Maintenance i.e. Facility to change information in the
    database.

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

from TartanClasses import ASD, CCD, SChoice, Sql, TartanDialog
from tartanFunctions import askQuestion, showError

class tb1030(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.doReset()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, "ftable",
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.doGetTable()
        if not self.table:
            return
        self.sql = Sql(self.opts["mf"].dbm, ["ftable", self.table],
            prog=self.__class__.__name__)
        self.sqi = Sql(self.opts["mf"].dbm, self.table,
            prog=self.__class__.__name__)
        self.read = "N"
        return True

    def doGetTable(self):
        tit = ("Table to Fix/Amend",)
        tbl = {
            "stype": "R",
            "tables": ("ftable",),
            "cols": (
                ("ft_tabl", "", 0, "Table"),
                ("ft_desc", "", 0, "Description", "Y")),
            "where": [("ft_seq", "=", 1)],
            "screen": self.opts["mf"].body}
        fld = (
            (("T",0,0,0),"I@ft_tabl",0,"","",
                "","N",self.doTabNam,tbl,None,None),)
        tnd = ((self.doTabEnd,"y"), )
        txt = (self.doTabExit, )
        self.tb = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=tnd, txit=txt)
        self.tb.mstFrame.wait_window()

    def doTabNam(self, frt, pag, r, c, p, i, w):
        desc = self.sql.getRec("ftable", cols=["ft_desc"],
            where=[("ft_tabl", "=", w)], limit=1)
        if not desc:
            return "Invalid Table"
        self.table = w
        self.desc = desc[0]

    def doTabExit(self):
        self.table = None
        self.doTabEnd()

    def doTabEnd(self):
        self.tb.closeProcess()

    def mainProcess(self):
        self.dics = getattr(self.sql, "%s_dic" % self.table)
        self.lcol = getattr(self.sql, "%s_col" % self.table)
        self.pgs = int((len(self.lcol) - 1) / 15) + 1
        fld = []
        cnt = 0
        lpg = 0
        for num, col in enumerate(self.lcol):
            if self.pgs == 1:
                pag = 0
            else:
                pag = int(num / 15) + 1
            if pag != lpg:
                lpg = pag
                cnt = 0
            if self.dics[col][2][0] == "D":
                typ = "I%s" % self.dics[col][2].lower()
            else:
                typ = "I%s" % self.dics[col][2]
            siz = self.dics[col][3]
            if siz > 50:
                siz = 50
            fld.append([["T", pag, cnt, 0], typ, siz, self.dics[col][4],
                self.dics[col][4], "", "N", None, None, None, None])
            cnt += 1
        but = (
            ("Display",None,self.doDisplay,None,None,None),
            ("Update",None,self.doUpdate,None,None,None),
            ("Create",None,self.doCreate,1,None,None),
            ("Delete",None,self.doDelete,None,None,None),
            ("Cancel",None,self.doReset,None,None,None),
            ("Exit",None,self.doExit,1,None,None))
        if self.pgs == 1:
            tag = None
            tnd = ((self.doEnd, "n"), )
            txt = (self.doExit, )
        else:
            tag = []
            tnd = [None]
            txt = [None]
            for pag in range(1, (self.pgs + 1)):
                tag.append(["Page-_%s" % pag, self.chgPage, ("T", 1, 1), None])
                tnd.append([self.doEnd, "n"])
                txt.append(self.doExit)
        if self.pgs == 1:
            self.df = TartanDialog(self.opts["mf"], tops=True, title=self.desc,
                eflds=fld, tags=tag, tend=tnd, txit=txt, butt=but,
                clicks=self.doClick)
        else:
            self.df = TartanDialog(self.opts["mf"], eflds=fld, tags=tag,
                tend=tnd, txit=txt, butt=but, clicks=self.doClick)

    def doClick(self, *opts):
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def chgPage(self):
        self.df.focusField("T", self.df.pag, 1, clr=False)

    def doDisplay(self):
        whr = []
        hed = []
        pos = 0
        for pag in range(self.df.pgs + 1):
            for num, fld in enumerate(self.df.t_work[pag][0]):
                hed.append(self.dics[self.lcol[pos]][5])
                if fld:
                    if type(fld) == str and fld.count("%"):
                        eql = "like"
                    else:
                        eql = "="
                    if self.dics[self.lcol[pos]][2][1] in ("A", "a"):
                        whr.append((self.lcol[pos], eql, fld))
                    else:
                        whr.append((self.lcol[pos], eql, fld))
                pos += 1
        keys = self.sql.getRec("ftable", where=[("ft_tabl", "=",
            self.table), ("ft_seq", "=", 1)], limit=1)
        odr = ""
        for x in range(4, 14):
            if keys[x]:
                odr = "%s%s," % (odr, keys[x])
        odr = odr[:-1]
        recs = self.sql.getRec(tables=self.table, where=whr, order=odr)
        if recs:
            titl = "Available Records"
            dat = []
            for rec in recs:
                a = []
                for n, c in enumerate(self.lcol):
                    d = CCD(rec[n], self.dics[c][2], self.dics[c][3])
                    a.append(d.disp)
                dat.append(a)
            state = self.df.disableButtonsTags()
            sc = SChoice(self.opts["mf"], scrn=self.opts["mf"].body, titl=titl,
                head=hed, data=dat, retn="I", mode="S")
            self.df.enableButtonsTags(state=state)
            if sc.selection is not None:
                self.read = "Y"
                self.olddata = recs[sc.selection]
                for num, dat in enumerate(self.olddata):
                    if self.pgs == 1:
                        pag = 0
                        idx = num
                    else:
                        pag = int(num / 15) + 1
                        idx = num - ((pag - 1) * 15)
                    self.df.loadEntry("T", pag, idx, data=dat)
                self.df.setWidget(self.df.B0, "disabled")
                self.df.setWidget(self.df.B1, "normal")
                self.df.setWidget(self.df.B3, "normal")
                self.df.setWidget(self.df.B4, "normal")
            else:
                self.read = "N"
            frt, pag, row, col = self.df.first
            self.df.focusField(frt, pag, 1, clr=False)

    def doUpdate(self):
        if self.read == "N":
            return
        self.sql.delRec(self.table, data=self.olddata)
        self.olddata = []
        newdata = []
        for pag in range((self.df.pgs + 1)):
            newdata.extend(self.df.t_work[pag][0])
        self.sqi.insRec(self.table, data=newdata)
        self.doReset()

    def doCreate(self):
        newdata = []
        for pag in range((self.df.pgs + 1)):
            newdata.extend(self.df.t_work[pag][0])
        keys = self.sql.getRec("ftable", where=[("ft_tabl", "=",
            self.table), ("ft_type", "=", "U")])
        for key in keys:
            col = []
            dat = []
            for fld in key[4:]:
                if fld:
                    col.append(fld)
                    idx = getattr(self.sqi, "%s_col" % self.table)
                    dat.append(newdata[idx.index(fld)])
            whr = []
            for num, ccc in enumerate(col):
                whr.append((ccc, "=", dat[num]))
            chk = self.sqi.getRec(tables=self.table, where=whr)
            if chk:
                showError(self.opts["mf"].body, "Duplicate Key",
                    "A Record like this Already Exists")
                return
        self.sqi.insRec(self.table, data=newdata)
        self.doReset()

    def doDelete(self):
        if self.read == "N":
            return
        if self.table in ("gentrn", "crstrn", "drstrn"):
            ask = askQuestion(self.opts["mf"].body, "Delete",
                "Delete All Associated Records?", default="no")
        else:
            ask = "no"
        if ask == "yes":
            err = ""
            tabs = ["gentrn", "ctlvtf", "crsctl", "crstrn", "drsctl", "drstrn"]
            sql = Sql(self.opts["mf"].dbm, tables=tabs)
            conum = self.olddata[0]
            if self.table == "gentrn":
                system = "G"
                docno = CCD(self.olddata[5], "Na", 9).work
                date = CCD(self.olddata[3], "D1", 10).work
                dtyp = CCD(self.olddata[4], "UI", 2).work
                gtyp = dtyp
            elif self.table == "crstrn":
                system = "C"
                acno = CCD(self.olddata[1], "NA", 7).work
                dtyp = CCD(self.olddata[2], "UI", 2).work
                docno = CCD(self.olddata[3], "Na", 9).work
                date = CCD(self.olddata[5], "D1", 10).work
                if dtyp in (1, 4):
                    gtyp = 5                        # Purchase
                elif dtyp == 2:
                    gtyp = 6                        # Receipt
                elif dtyp == 3:
                    gtyp = 4                        # Journal
                elif dtyp == 5:
                    gtyp = 2                        # Payment
                glint = sql.getRec("crsctl", cols=["ctc_glint"],
                    where=[("ctc_cono", "=", conum)], limit=1)[0]
            else:
                system = "D"
                chain = CCD(self.olddata[1], "UI", 3).work
                acno = CCD(self.olddata[2], "NA", 7).work
                dtyp = CCD(self.olddata[3], "UI", 2).work
                docno = CCD(self.olddata[4], "Na", 9).work
                date = CCD(self.olddata[6], "D1", 10).work
                if dtyp in (1, 4):
                    gtyp = 1                        # Sale
                elif dtyp == 2:
                    gtyp = 6                        # Receipt
                elif dtyp == 3:
                    gtyp = 4                        # Journal
                elif dtyp == 5:
                    gtyp = 2                        # Payment
                glint = sql.getRec("drsctl", cols=["ctd_glint"],
                    where=[("ctd_cono", "=", conum)], limit=1)[0]
            sqv = [
                ("vtt_cono", "=", conum),
                ("vtt_styp", "=", system),
                ("vtt_refno", "=", docno),
                ("vtt_refdt", "=", date),
                ("vtt_ttyp", "=", dtyp)]
            recs = sql.getRec("ctlvtf", where=sqv)
            if len(recs) > 1:
                err = "ctlvtf recs %s\n" % len(recs)
            texc = 0
            ttax = 0
            for rec in recs:
                texc = float(ASD(texc) + ASD(rec[11]))
                ttax = float(ASD(ttax) + ASD(rec[12]))
            ttot = float(ASD(texc) + ASD(ttax))
            ok = "yes"
            if system == "G" or glint == "Y":
                sqg = [
                    ("glt_cono", "=", conum),
                    ("glt_refno", "=", docno),
                    ("glt_trdt", "=", date),
                    ("glt_type", "=", gtyp)]
                recs = sql.getRec("gentrn", where=sqg)
                gamt = 0
                gtax = 0
                for rec in recs:
                    gamt = float(ASD(gamt) + ASD(rec[7]))
                    gtax = float(ASD(gtax) + ASD(rec[8]))
                if gtax != ttax:
                    err = "%sctlvtf %s <> gentrn %s\n" % (err, ttax, gtax)
                if gamt:
                    err = "%sgentrn debits <> credits" % err
            if system == "C":
                sqc = [
                    ("crt_cono", "=", conum),
                    ("crt_acno", "=", acno),
                    ("crt_ref1", "=", docno),
                    ("crt_trdt", "=", date),
                    ("crt_type", "=", dtyp)]
                recs = sql.getRec("crstrn", where=sqc)
                if len(recs) > 1:
                    err = "%scrstrn recs %s\n" % (err, len(recs))
                camt = 0
                ctax = 0
                for rec in recs:
                    camt = float(ASD(camt) + ASD(rec[7]))
                    ctax = float(ASD(ctax) + ASD(rec[8]))
                if ctax != ttax:
                    err = "%sctlvtf %s <> crstrn %s\n" % (err, ttax, ctax)
                if camt != ttot:
                    err = "%sctlvtf tot %s <> crstrn tot %s" % (err, ttot, camt)
            if system == "D":
                sqd = [
                    ("drt_cono", "=", conum),
                    ("drt_chain", "=", chain),
                    ("drt_acno", "=", acno),
                    ("drt_ref1", "=", docno),
                    ("drt_trdt", "=", date),
                    ("drt_type", "=", dtyp)]
                recs = sql.getRec("drstrn", where=sqd)
                if len(recs) > 1:
                    err = "%sdrstrn recs %s\n" % (err, len(recs))
                damt = 0
                dtax = 0
                for rec in recs:
                    damt = float(ASD(damt) - ASD(rec[8]))
                    dtax = float(ASD(dtax) - ASD(rec[9]))
                if dtax != ttax:
                    err = "%sctlvtf %s <> drstrn %s\n" % (err, ttax, dtax)
                if damt != ttot:
                    err = "%sctlvtf tot %s <> drstrn tot %s" % (err, ttot, damt)
            if err:
                ok = askQuestion(self.opts["mf"].body, "Error",
                    "%s\n\nDelete transaction (y/n)?" % err)
            if ok == "yes":
                sql.delRec("ctlvtf", where=sqv)
                if system == "G" or glint == "Y":
                    sql.delRec("gentrn", where=sqg)
                if system == "C":
                    sql.delRec("crstrn", where=sqc)
                if system == "D":
                    sql.delRec("drstrn", where=sqd)
        else:
            self.sql.delRec(self.table, data=self.olddata)
        self.olddata = []
        self.doReset()

    def doEnd(self):
        self.df.focusField(self.df.frt, self.df.pag, 1, clr=False)

    def doReset(self):
        self.read = "N"
        if self.pgs == 1:
            self.df.focusField("T", 0, 1)
        else:
            self.df.selPage(self.df.tags[0][0])
            self.df.focusField("T", 1, 1)
        self.df.setWidget(self.df.B0, "normal")
        self.df.setWidget(self.df.B1, "disabled")
        self.df.setWidget(self.df.B3, "disabled")
        self.df.setWidget(self.df.B4, "disabled")

    def doExit(self):
        mes = None
        dft = "yes"
        if self.table == "gentrn":
            bals = self.sql.getRec("gentrn", cols=["sum(glt_tramt)"],
                limit=1)
            if bals[0]:
                amt = CCD(bals[0], "SD", 13.2)
                mes = "General Ledger Out of Balance by %s\n\n"\
                    "Commit Anyway?" % amt.disp.lstrip()
                dft = "no"
        self.opts["mf"].dbm.commitDbase(ask=True, mess=mes, default=dft)
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
