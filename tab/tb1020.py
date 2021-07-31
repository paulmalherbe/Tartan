"""
SYNOPSIS
    Tables Alteration comparing New details with existing data in database.

    This file is part of Tartan Systems (TARTAN).

    This is used to change tables in a database.

    CLI Usage: python tb1020.py [options]

    mf               = The MainFrame object
    bar [True/False] = Show a progress bar
    cln [True/False] = Clean the DataBase i.e. remove unwanted tables etc
    pwd [password]   = Database Admin Password
    rcf [file]       = tartanrc file to use, defaults to ~/.tartanrc
    upd [True/False] = Force Update of all records, True or False
    usr [user]       = Database Admin User Name
    ver [x.x]        = The New version number

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

import copy, sys, time
from itertools import chain
from TartanClasses import CCD, Dbase, DBCreate, ProgressBar, SplashScreen
from TartanClasses import Sql
from tartanFunctions import copyList, loadRcFile, showError
from tartanWork import datdic, stdtpl, tabdic

class tb1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "tab" in self.opts and self.opts["tab"]:
                self.tabs = self.opts["tab"]
                self.old = []
                tab = self.sql.getRec("ftable", cols=["ft_tabl"],
                    where=[("ft_seq", "=", 1)], order="ft_tabl")
                for t in tab:
                    if t[0] not in ("ftable", "ffield"):
                        self.old.append(t[0])
                self.old.sort()
            else:
                self.doGetTables()
            self.doProcessTables()
            if self.opts["cln"]:
                self.doCleanDatabase()
            if self.opts["ver"]:
                sql = Sql(self.dbm, "verupd", error=False,
                    prog=self.__class__.__name__)
                if not sql.getRec("verupd"):
                    sql.insRec("verupd", data=[self.opts["ver"], self.sysdtw])
                else:
                    sql.updRec("verupd", data=[self.opts["ver"], self.sysdtw])
                self.dbm.commitDbase()
            self.doFixAge()
            self.doFinal()
            if self.dbm.dbase == "SQLite":
                self.dbm.commitDbase()
                self.dbm.cu.execute("PRAGMA JOURNAL_MODE=DELETE")
                self.dbm.cu.execute("PRAGMA SYNCHRONOUS=FULL")

    def setVariables(self):
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        if not self.opts["mf"]:
            try:
                rcdic = loadRcFile(rcfile=self.opts["rcf"])
                if rcdic == "error":
                    raise Exception
                self.dbm = Dbase(rcdic=rcdic)
                if self.dbm.err:
                    raise Exception
                self.dbm.openDbase()
            except:
                print("DB or RC File Error", "DB Error or RC File Not Found")
                return
        else:
            self.dbm = self.opts["mf"].dbm
        self.sql = Sql(self.dbm, ["ffield", "ftable", "verupd"], error=False,
            prog=self.__class__.__name__)
        if "verupd" in self.sql.error:
            self.oldver = (0, 0)
        elif self.sql.error:
            return
        else:
            v = self.sql.getRec("verupd", cols=["ver_version"], limit=1)
            if v[0]:
                ov = v[0].split(".")
                self.oldver = (int(ov[0]), int(ov[1].rstrip()))
            else:
                self.oldver = (0, 0)
        if self.oldver[0] and self.oldver[:2] < (5, 5):
            txt = "Your current version must be 5.5 or later before you "\
                    "can upgrade to this version. If you need help to "\
                    "upgrade please contact paul@tartan.co.za"
            if self.opts["mf"] and self.opts["mf"].window:
                showError(self.opts["mf"].body, "Version Error", txt)
            else:
                print(txt)
            return
        self.topts = [
            ("-u", self.opts["usr"]),
            ("-c", "t"),
            ("-w", False),
            ("-x", False)]
        if self.opts["pwd"]:
            self.topts.append(("-p", self.opts["pwd"]))
        self.tabord = {
            "asstrn": ["ast_capdt", "ast_seq"],
            "bkmrtt": ["brt_capdt", "brt_seq"],
            "bkmtrn": ["bkt_capdt", "bkt_seq"],
            "chglog": ["chg_dte", "chg_seq"],
            "crsage": ["cra_curdt", "cra_seq"],
            "crstrn": ["crt_capdt", "crt_seq"],
            "cshana": ["can_date", "can_seq"],
            "ctlnot": ["not_date", "not_seq"],
            "ctlvtf": ["vtt_capdt", "vtt_seq"],
            "drsage": ["dra_curdt", "dra_seq"],
            "drstrn": ["drt_capdt", "drt_seq"],
            "genrct": ["grt_seq", "grt_date"],
            "gentrn": ["glt_capdt", "glt_seq"],
            "ibttrn": ["ibt_capdt", "ibt_seq"],
            "lontrn": ["lnt_capdt", "lnt_seq"],
            "memage": ["mta_curdt", "mta_seq"],
            "memsta": ["mls_date", "mls_seq"],
            "memtrn": ["mlt_capdt", "mlt_seq"],
            "memtrs": ["mst_trdt", "mst_seq"],
            "rcaowt": ["rot_capdt", "rot_seq"],
            "rcatnt": ["rtu_capdt", "rtu_seq"],
            "rtltrn": ["rtt_capdt", "rtt_seq"],
            "slsiv3": ["si3_seqnum"],
            "strpot": ["pot_capdt", "pot_seq"],
            "strtrn": ["stt_capdt", "stt_seq"],
            "tpldet": ["tpd_name", "tpd_detseq"],
            "wagcap": ["wcp_capdt", "wcp_seq"],
            "wagltf": ["wlt_capdt", "wlt_seq"],
            "wagtf1": ["wt1_capdt", "wt1_seq"]}
        if self.dbm.dbase == "PgSQL":
            self.lmt = 5000
        elif self.dbm.dbase == "SQLite":
            self.lmt = 500
            self.dbm.commitDbase()
            self.dbm.cu.execute("PRAGMA JOURNAL_MODE=OFF")
            self.dbm.cu.execute("PRAGMA SYNCHRONOUS=OFF")
        else:
            return
        return True

    def doProcessTables(self):
        txt = "Updating Database ... Please Wait"
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus("")
            if self.opts["bar"]:
                self.p1 = ProgressBar(self.opts["mf"].body, typ=txt,
                    mxs=len(self.tabs))
        elif self.opts["bar"]:
            print(txt)
        for num, self.table in enumerate(self.tabs):
            if self.opts["bar"] and self.opts["mf"] and self.opts["mf"].window:
                self.p1.displayProgress(num)
            recs = False
            chk = self.doReadTables("idx")
            if not chk:
                chk = self.doReadTables("fld")
            if chk or self.opts["upd"]:
                if chk and chk == "skip":
                    continue
                recs = True
                self.doNewTable()
            elif self.oldfld != self.newfld:
                if len(self.oldfld) != len(self.newfld):
                    recs = True
                else:
                    for seq, fld in enumerate(self.oldfld):
                        for s, f in enumerate(fld):
                            if f != self.newfld[seq][s]:
                                if s in (1, 2, 3, 4):
                                    recs = True
                                    break
                        if recs:
                            break
                if recs:
                    self.doNewTable()
                else:
                    self.doUpdateTable()
            elif self.table == "strpom" and self.strpom:
                recs = True
                self.doNewTable()
            if not recs and self.oldidx != self.newidx:
                old = self.sql.getRec("ftable", where=[("ft_tabl",
                    "=", self.table)], order="ft_seq")
                for rec in old:
                    nam = "%s_key%s" % (self.table, str(rec[2]))
                    if self.doCheckIndex(self.table, nam):
                        self.sql.sqlRec("Drop index %s" % nam)
                DBCreate(dbm=self.dbm, opts=[
                    ("-u", self.opts["usr"]),
                    ("-c", "p"),
                    ("-t", self.table),
                    ("-w", True),
                    ("-x", False)])
        if self.opts["bar"] and self.opts["mf"] and self.opts["mf"].window:
            self.p1.closeProgress()

    def doGetTables(self):
        try:
            self.tabs = list(tabdic.keys())
            if "ffield" in self.tabs:
                self.tabs.remove("ffield")
            if "ftable" in self.tabs:
                self.tabs.remove("ftable")
            self.tabs.sort()
        except:
            if self.opts["mf"] and self.opts["mf"].window:
                showError(self.opts["mf"].body, "Error",
                    "Missing Tables Dictionary")
            else:
                print("Missing Tables Dictionary")
            return
        self.old = []
        tab = self.sql.getRec("ftable", cols=["ft_tabl"],
            where=[("ft_seq", "=", 1)], order="ft_tabl")
        for t in tab:
            if t[0] not in ("ftable", "ffield"):
                self.old.append(t[0])
        self.old.sort()
        return True

    def doReadTables(self, tipe=None):
        if self.table not in tabdic:
            return "skip"
        if tipe == "idx":
            tab = "ftable"
            old = self.sql.getRec("ftable", where=[("ft_tabl", "=",
                self.table)], order="ft_seq")
        else:
            tab = "ffield"
            old = self.sql.getRec("ffield", where=[("ff_tabl", "=",
                self.table)], order="ff_seq")
            if old and self.table == "strpom":
                self.strpom = False
                tmp = copyList(old)
                for num, rec in enumerate(tmp):
                    if rec[1] == 13 and rec[2] == "pom_mess":
                        self.strpom = True
                        old[num][1] = 14
                    elif rec[1] == 14 and rec[2] == "pom_delno":
                        old[num][1] = 15
                    elif rec[1] == 15 and rec[2] == "pom_deldt":
                        old[num][1] = 16
                    elif rec[1] == 16 and rec[2] == "pom_capnm":
                        old[num][1] = 17
                    elif rec[1] == 17 and rec[2] == "pom_capdt":
                        old[num][1] = 18
        if not old:
            if self.opts["mf"] and self.opts["mf"].window:
                self.opts["mf"].updateStatus("Table %s Not Found in %s" % \
                    (self.table, tab))
            else:
                print("Table %s Not Found in %s" % (self.table, tab))
            return tipe
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus("")
        setattr(self, "old%s" % tipe, old)
        new = []
        for t in tabdic[self.table][tipe]:
            n = copy.copy(t)
            n.insert(0, self.table)
            if tipe == "idx":
                n[2] = int(n[2])
                for _ in range(len(n), 14):
                    n.append("")
            else:
                n[1] = int(n[1])
                n[4] = float(n[4])
            new.append(n)
        setattr(self, "new%s" % tipe, new)

    def doUpdateTable(self):
        for seq, fld in enumerate(self.newidx):
            self.sql.updRec("ftable", where=[("ft_tabl", "=", fld[0]),
                ("ft_seq", "=", fld[2])], cols=["ft_desc"], data=[fld[1]])
        for seq, fld in enumerate(self.newfld):
            self.sql.updRec("ffield", where=[("ff_tabl", "=", fld[0]),
                ("ff_seq", "=", fld[1])], cols=["ff_desc", "ff_head"],
                data=[fld[5], fld[6]])
        self.dbm.commitDbase()

    def doNewTable(self):
        sql = Sql(self.dbm, self.table, error=False,
            prog=self.__class__.__name__)
        if sql.error:
            data = None
        else:
            # Read Existing Table
            cols = getattr(sql, "%s_col" % self.table)
            order = ""
            if self.table in self.tabord:
                ords = self.tabord[self.table]
                for fld in ords:
                    if fld in cols:
                        if not order:
                            order = fld
                        else:
                            order = "%s, %s" % (order, fld)
            data = sql.getRec(tables=self.table, order=order)
        # Create New Table
        opts = copyList(self.topts)
        opts.append(("-t", self.table))
        DBCreate(dbm=self.dbm, opts=opts)
        ndata = []
        if data:
            sql = Sql(self.dbm, self.table, error=False,
                prog=self.__class__.__name__)
            # Create Dictionaries
            olddic = {}
            for f in self.oldfld:
                olddic[f[2]] = f[1:]
            newdic = {}
            for f in self.newfld:
                newdic[f[2]] = f[1:]
            # Populate New Table
            mx1 = len(data)
            if self.opts["bar"] and self.opts["mf"] and self.opts["mf"].window:
                pbar = "w"
                p2 = ProgressBar(self.opts["mf"].body, inn=self.p1,
                    typ="Converting Table %s" % self.table, mxs=mx1)
            else:
                pbar = False
                p2 = None
            for num, old in enumerate(data):
                # Convert old data to new format
                if pbar:
                    p2.displayProgress(num)
                dat = []
                for csf in self.newfld:
                    nam = csf[2]
                    typ = csf[3]
                    if typ == "US":
                        continue
                    siz = csf[4]
                    if nam in olddic and typ == olddic[nam][2]:
                        new = old[olddic[nam][0]]
                    elif nam in olddic:
                        try:
                            ccd = CCD(old[olddic[nam][0]], typ, siz)
                            if ccd.err:
                                raise Exception
                            new = ccd.work
                        except:
                            if typ[1].lower() in ("a", "x"):
                                new = ""
                            else:
                                new = 0
                    elif self.table == "ctlrep" and nam == "rep_cono":
                        new = old[olddic["rpm_cono"][0]]
                    elif self.table == "ctlrep" and nam == "rep_code":
                        new = old[olddic["rpm_rep"][0]]
                    elif self.table == "ctlrep" and nam == "rep_name":
                        new = old[olddic["rpm_name"][0]]
                    elif self.table == "bksmst" and nam == "bmf_cono":
                        new = 1
                    elif self.table == "bksown" and nam == "bof_cono":
                        new = 1
                    elif self.table == "bwlctl" and nam == "ctb_mscat":
                        new = 0
                    elif self.table == "bwlgme" and nam == "bcg_sfor":
                        new = old[olddic["bcg_shots_for"][0]]
                    elif self.table == "bwlgme" and nam == "bcg_sagt":
                        new = old[olddic["bcg_shots_agt"][0]]
                    elif self.table == "bwlgme" and nam == "bcg_a_sfor":
                        new = old[olddic["bcg_a_shots_for"][0]]
                    elif self.table == "bwlgme" and nam == "bcg_a_sagt":
                        new = old[olddic["bcg_a_shots_agt"][0]]
                    elif self.table == "crsmst" and nam == "crm_stat":
                        new = "N"
                    elif self.table == "drsmst" and nam == "drm_stat":
                        new = "N"
                    elif typ[1].lower() in ("a", "x"):
                        new = ""
                    else:
                        new = 0
                    dat.append(new)
                ndata.append(dat)
            if ndata:
                # Populate new table
                if pbar:
                    txt = "Populating Table %s" % self.table
                    p2.mxp = 1
                    p2.mxs = len(ndata)
                    p2.txtlab.configure(text=txt)
                    p2.displayProgress()
                clm = ""
                fmt = ""
                for csf in self.newfld:
                    nam = csf[2]
                    typ = csf[3]
                    if typ == "US":
                        continue
                    if not clm:
                        clm = nam
                        fmt = self.dbm.dbf
                    else:
                        clm += ",%s" % nam
                        fmt = "%s,%s" % (fmt, self.dbm.dbf)
                nlim = int(self.lmt / len(self.newfld))
                for x in range(0, len(ndata), nlim):
                    if pbar:
                        p2.displayProgress(x)
                    y = x + nlim
                    tft = ",".join("(%s)" % fmt for _ in ndata[x:y])
                    dat = list(chain.from_iterable(ndata[x:y]))
                    cmd = "Insert into %s (%s) values %s" % (
                                        self.table, clm, tft)
                    sql.sqlRec((cmd, dat))
                    #self.dbm.commitDbase()
            if pbar:
                p2.closeProgress()
            # Update Report Writer for missing columns
            cols = []
            for csf in self.oldfld:
                if csf[2] not in newdic:
                    cols.append(csf[2])
            if cols:
                tabs = (
                    ("rptcol", "rpc_rnam", "rpc_detail"),
                    ("rptexc", "rpx_rnam", "rpx_exc"),
                    ("rptjon", "rpj_rnam", "rpj_col"),
                    ("rptord", "rpo_rnam", "rpo_column"))
                for tab in tabs:
                    sql = Sql(self.dbm, tab[0], error=False,
                        prog=self.__class__.__name__)
                    if sql.error:
                        continue
                    dat = sql.getRec(tables=tab[0], cols=[tab[1], tab[2]])
                    for d in dat:
                        for col in cols:
                            if d.count(col):
                                sql.delRec(tab[0], where=[(tab[1], "=", d[0]),
                                    (tab[2], "=", d[1])])
        self.dbm.commitDbase()

    def doCleanDatabase(self):
        txt = "Cleaning Database ... Please Wait"
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus(txt)
        elif self.opts["bar"]:
            print(txt)
        # Removing unused tables
        self.doGetTables()
        if self.opts["bar"] and self.opts["mf"] and self.opts["mf"].window:
            pb = ProgressBar(self.opts["mf"].body, mxs=(len(self.old) +
                len(self.tabs)), typ=txt)
        for n1, t in enumerate(self.old):
            if self.opts["mf"] and self.opts["mf"].window:
                self.opts["mf"].updateStatus(t)
                if self.opts["bar"]:
                    pb.displayProgress(n1)
            if t not in self.tabs:
                self.dbm.dropTable(t, True)
        self.dbm.commitDbase()
        # Creating new tables and/or indexes
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus("")
        for n2, t in enumerate(self.tabs):
            if self.opts["mf"] and self.opts["mf"].window:
                self.opts["mf"].updateStatus(t)
                if self.opts["bar"]:
                    pb.displayProgress(n1 + n2)
            if not self.dbm.checkTable(t):
                opts = copyList(self.topts)
                opts.append(("-t", t))
                DBCreate(dbm=self.dbm, opts=opts)
                self.tabs.append(t)
            else:
                self.doCreateIndexes(t)
        self.dbm.commitDbase()
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus("")
            if self.opts["bar"]:
                pb.closeProgress()
        # Fix ctlmst and Stores Markup
        tabs = ["ctlmst", "strctl", "strgrp", "strgmu", "strcmu"]
        sql = Sql(self.dbm, tabs)
        coys = sql.getRec("ctlmst", cols=["ctm_cono"])
        for coy in coys:
            mods = sql.getRec("ctlmst", cols=["ctm_modules"],
                where=[("ctm_cono", "=", coy[0])], limit=1)
            newm = ""
            for x in range(0, len(mods[0]), 2):
                if mods[0][x:x+2] != "PS":
                    newm += mods[0][x:x+2]
            sql.updRec("ctlmst", cols=["ctm_modules"], data=[newm])
            sctl = sql.getRec("strctl", cols=["cts_plevs", "cts_automu"],
                where=[("cts_cono", "=", coy[0])], limit=1)
            if sctl:
                if sctl[1] == "N":
                    sql.delRec("strgmu", where=[("smg_cono", "=", coy[0])])
                    sql.delRec("strcmu", where=[("smc_cono", "=", coy[0])])
                else:
                    if sctl[1] == "Y":
                        sql.updRec("strctl", cols=["cts_automu"], data=["L"],
                            where=[("cts_cono", "=", coy[0])])
                        sctl[1] = "L"
                    grps = sql.getRec("strgrp", cols=["gpm_group"],
                        where=[("gpm_cono", "=", coy[0])])
                    for grp in grps:
                        for lvl in range(1, sctl[0] + 1):
                            sql.delRec("strcmu", where=[("smc_cono", "=",
                                coy[0]), ("smc_group", "=", grp[0]),
                                ("smc_level", "=", lvl),
                                ("smc_markup", "=", 0)])
                            gmu = sql.getRec("strgmu", cols=["smg_markup"],
                                where=[("smg_cono", "=", coy[0]), ("smg_group",
                                "=", grp[0]), ("smg_level", "=", lvl)], limit=1)
                            if gmu:
                                if not gmu[0]:
                                    sql.delRec("strgmu", where=[("smg_cono",
                                        "=", coy[0]), ("smg_group", "=",
                                        grp[0]), ("smg_level", "=", lvl)])
                                sql.delRec("strcmu", where=[("smc_cono",
                                    "=", coy[0]), ("smc_group", "=", grp[0]),
                                    ("smc_level", "=", lvl), ("smc_markup",
                                    "=", gmu[0])])
        # Standard Records
        if self.opts["mf"] and self.opts["mf"].window:
            spl = SplashScreen(self.opts["mf"].body,
                "Creating Standard Records\n\nPlease Wait")
            self.opts["mf"].updateStatus("Creating Standard Records")
        elif self.opts["bar"]:
            print("Creating Standard Records .... Please Wait")
        sql = Sql(self.dbm, ["ffield", "frelat"], error=False,
            prog=self.__class__.__name__)
        if not sql.error:
            sql.sqlRec("Delete from frelat")
            self.doPopulate(sql, "frelat", "_cono")
        sql = Sql(self.dbm, "wagrcv", error=False,
            prog=self.__class__.__name__)
        if not sql.error:
            sql.sqlRec("Delete from wagrcv")
            self.doPopulate(sql, "wagrcv")
        sql = Sql(self.dbm, ["tplmst", "tpldet"], error=False,
            prog=self.__class__.__name__)
        if not sql.error:
            for tpl in stdtpl:
                sql.sqlRec("Delete from tplmst where tpm_tname = '%s'" % tpl)
                sql.sqlRec("Delete from tpldet where tpd_tname = '%s'" % tpl)
            for dat in datdic["tplmst"]:
                sql.insRec("tplmst", data=dat)
            for dat in datdic["tpldet"]:
                sql.insRec("tpldet", data=dat)
        sql = Sql(self.dbm, ["wagtxa", "wagtxr"], error=False,
            prog=self.__class__.__name__)
        if not sql.error:
            try:
                from tartanWork import payeRates, siteRates, uifRates, sdlRates
                for t in ("wagtxa", "wagtxr"):
                    if t == "wagtxa":
                        for year in payeRates:
                            sql.delRec(t, where=[("wta_year", "=", int(year))])
                            data = [int(year)]
                            for n, d in enumerate(payeRates[year]["allow"]):
                                data.append(d)
                                if n == 1 and \
                                        len(payeRates[year]["allow"]) == 3:
                                    data.append(d)
                            data.append(siteRates[year])
                            data.extend(uifRates[year])
                            data.extend(sdlRates[year])
                            sql.insRec("wagtxa", data=data)
                    elif t == "wagtxr":
                        for year in payeRates:
                            sql.delRec(t, where=[("wtr_year", "=", int(year))])
                            to = 9999999
                            for rate in payeRates[year]["rates"]:
                                dat = [int(year)]
                                if rate[0]:
                                    dat.append(rate[0] + 1)
                                    dat.append(to)
                                    dat.extend(rate[1:])
                                    to = rate[0]
                                else:
                                    dat.append(0)
                                    dat.append(to)
                                    dat.extend(rate[1:])
                                sql.insRec("wagtxr", data=dat)
            except:
                pass
        # Close Splash
        if self.opts["mf"] and self.opts["mf"].window:
            spl.closeSplash()
        self.dbm.commitDbase()

    def doPopulate(self, sql, table, cono=None):
        if cono:
            recs = sql.getRec("ffield", cols=["ff_tabl", "ff_name"],
                where=[("ff_name", "like", "%_cono")])
            for rec in recs:
                sql.insRec(table, data=[rec[0], rec[1], "ctlmst", "ctm_cono"])
        if table in datdic:
            for dat in datdic[table]:
                sql.insRec(table, data=dat)

    def doFixAge(self):
        for sss in ("crs", "drs"):
            sql = Sql(self.dbm, ["%smst" % sss, "%sage" % sss], prog=__name__)
            if sss == "drs":
                col = ["drm_cono", "drm_chain", "drm_acno"]
                whr = ["dra_seq", "="]
                idx = 10
            else:
                col = ["crm_cono", "crm_acno"]
                whr = ["cra_seq", "="]
                idx = 9
            accs = sql.getRec("%smst" % sss, cols=col)
            recs = sql.getRec("%sage" % sss)
            for rec in recs:
                if rec[:len(col)] not in accs:
                    w = whr[:]
                    w.append(rec[idx])
                    sql.delRec("%sage" % sss, where=[w])
            self.dbm.commitDbase()

    def doFinal(self):
        chg = False
        for tab in ("ffield", "ftable"):
            chks = self.sql.getRec("ffield",
                where=[("ff_tabl", "=", tab)])
            for num, chk in enumerate(chks):
                if chk[1:] != tabdic[tab]["fld"][num]:
                    chg = True
                    break
        for tab in ("ffield", "ftable"):
            chks = self.sql.getRec("ftable",
                where=[("ft_tabl", "=", tab)])
            for num, chk in enumerate(chks):
                sch = chk[1:4]
                for ft in chk[4:]:
                    if ft:
                        sch.append(ft)
                if sch != tabdic[tab]["idx"][num]:
                    chg = True
                    break
        if not chg:
            return
        if self.opts["mf"] and self.opts["mf"].window:
            spl = SplashScreen(self.opts["mf"].body,
                "Finishing Off, Please Wait ....")
            self.opts["mf"].updateStatus("")
        elif self.opts["bar"]:
            print("Finishing Off, Please Wait ....")
        # Drop Indexes
        for tab in ("ffield", "ftable"):
            self.doDropIndex(tab)
        # Delete Record
        self.sql.delRec("ffield", where=[("ff_tabl", "in",
            ("ffield", "ftable"))])
        self.sql.delRec("ftable", where=[("ft_tabl", "in",
            ("ffield", "ftable"))])
        # Populate and Create Indexes
        for tab in ("ffield", "ftable"):
            self.dbm.populateTable(tab)
            self.doCreateIndexes(tab)
        self.dbm.commitDbase()
        if self.opts["mf"] and self.opts["mf"].window:
            spl.closeSplash()

    def doCreateIndexes(self, table):
        keys = self.sql.getRec("ftable", where=[("ft_tabl","=", table)])
        if not keys:
            return
        if self.opts["mf"] and self.opts["mf"].window:
            self.opts["mf"].updateStatus("Creating New Indexes for %s" % table)
        for key in keys:
            nam = "%s_key%s" % (table, str(key[2]))
            idx = ""
            skip = False
            for k in key[4:]:
                if k:
                    if self.dbm.dbase == "SQLite":
                        if self.checkBlob(table, k):
                            skip = True
                            break
                    if idx:
                        idx = "%s,%s" % (idx, k)
                    else:
                        idx = k
            if skip:
                continue
            chk = self.doCheckIndex(table, nam)
            if chk != idx:
                if chk:
                    self.sql.sqlRec("Drop index %s" % nam)
                if key[3] == "N":
                    sql = "Create index"
                else:
                    sql = "Create unique index"
                sql = "%s %s on %s (%s)" % (sql, nam, table, idx)
                self.sql.sqlRec(sql)

    def doDropIndex(self, tab):
        old = self.sql.getRec("ftable", where=[("ft_tabl", "=", tab)],
            order="ft_seq")
        for rec in old:
            nam = "%s_key%s" % (tab, str(rec[2]))
            if self.doCheckIndex(tab, nam):
                self.sql.sqlRec("Drop index %s" % nam)

    def doCheckIndex(self, table, name):
        if self.dbm.dbase == "PgSQL":
            sel = "Select indexdef from pg_indexes where schemaname='public' "\
                "and tablename='%s' and indexname='%s'" % (table, name)
        else:
            sel = "Select sql from sqlite_master where type='index' "\
                "and tbl_name='%s' and name='%s'" % (table, name)
        dat = self.sql.sqlRec(sel, limit=1)
        if dat:
            return dat[0].split("(")[1].split(")")[0].replace(" ", "")

    def checkBlob(self, table, key):
        cols = tabdic[table]["fld"]
        for col in cols:
            if col[1] == key and col[2] == "TX":
                return True

if __name__ == "__main__":
    import getopt

    opts, args = getopt.getopt(sys.argv[1:], "bcfhp:r:t:u:v:")
    parg = {
        "mf": None,
        "bar": False,
        "cln": False,
        "pwd": "",
        "rcf": None,
        "tab": [],
        "upd": False,
        "usr": "",
        "ver": None}
    for o, v in opts:
        if o == "-h":
            print("""
This is used to change tables in a database.

Usage: python tb1020.py [options]

    -b              = Show a progress bar
    -c              = Clean the DataBase i.e. remove unwanted tables etc
    -f              = Force update of all records in a table
    -h              = Display Usage
    -p [password]   = Database Admin Password
    -r [file]       = tartanrc file to use, defaults to ~/.tartanrc
    -t [table]      = Table to update
    -u [user]       = Database Admin User Name
    -v [x.x]        = The New version number
""")
            sys.exit()
        elif o == "-b":
            parg["bar"] = True
        elif o == "-c":
            parg["cln"] = True
        elif o == "-f":
            parg["upd"] = True
        elif o == "-p":
            parg["pwd"] = v
        elif o == "-r":
            parg["rcf"] = v
        elif o == "-t":
            parg["tab"] = v.split(",")
        elif o == "-u":
            parg["usr"] = v
        elif o == "-v":
            parg["ver"] = v
    if not parg["ver"]:
        print("Invalid -v version_number")
    else:
        tb1020(**parg)

# vim:set ts=4 sw=4 sts=4 expandtab:
