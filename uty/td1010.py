"""
SYNOPSIS
    Telephone Directory Maintenance.

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
from TartanClasses import CCD, NotesCreate, NotesPrint, ProgressBar, RepPrt
from TartanClasses import SelectChoice, SplashScreen, Sql, TabPrt, TartanDialog
from tartanFunctions import showWarning, textFormat

class td1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ctlnot", "telmst", "telgrp",
            "telcon"], prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = (t[0] * 10000) + (t[1] * 100) + t[2]
        self.name = ""
        return True

    def mainProcess(self):
        acc = self.sql.getRec("telmst", cols=["count(*)"], limit=1)
        if acc[0] > 500:
            autoc = False
        else:
            autoc = True
        tdm = {
            "stype": "R",
            "tables": ("telmst",),
            "cols": (
                ("tdm_name", "TX", 30, "Name","Y"),
                ("tdm_telno", "TX", 20, "Telephone"),
                ("tdm_mobile", "TX", 20, "Mobile"),
                ("tdm_email", "TX", 50, "Email-Address"),
                ("tdm_group", "UA", 12, "Grp")),
            "order": "tdm_name",
            "autoc": autoc,
            "sort": "n"}
        grp = {
            "stype": "S",
            "tables": "telgrp",
            "cols": ("tdg_group", "tdg_desc"),
            "order": "tdg_desc"}
        self.fld = (
            (("T",0,0,0),"I@tdm_name",50,"","",
                "","Y",self.doName,tdm,None,("notblank",)),
            (("T",0,1,0),"I@tdm_adr1",0,"","",
                "","N",None,None,self.doDelAll,("efld",)),
            (("T",0,2,0),"I@tdm_adr2",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,3,0),"I@tdm_adr3",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"I@tdm_pcode",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,5,0),"I@tdm_telno",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,6,0),"I@tdm_faxno",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,7,0),"I@tdm_mobile",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,8,0),"I@tdm_email",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,9,0),"I@tdm_group",0,"","",
                "","N",self.doGroup,grp,None,("efld",),None,
                "Comma separated groups which this contact belongs to."))
        but = (
            ("Back",None,self.doUp,1,None,("T",0,1),"",1),
            ("Forward",None,self.doDn,1,None,("T",0,1),"",1),
            ("Import",None,self.doImport,1,("T",0,1),("T",0,2),
                "Import Names, Addresses and Contact Details from "\
                "Booking, Creditor, Debtor and Member Records, if "\
                "Available",1),
            ("Notes",None,self.doNotes,1,("T",0,2),("T",0,1),"",1),
            ("Print",None,self.doPrint,1,None,None,"",1),
            ("Apply",None,self.doApply,0,("T",0,2),("T",0,1),"",1),
            ("Contacts",None,self.doContacts,0,("T",0,2),("T",0,1),"",2,2),
            ("Cancel",None,self.doCancel,0,("T",0,2),("T",0,1),"",2,2),
            ("Quit",None,self.doTopExit,1,None,None,"",2,2))
        tnd = ((self.doTopEnd,"y"),)
        txt = (self.doTopExit,)
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt, clicks=self.doClick)

    def doClick(self, *opts):
        if not self.name or opts[0][1] == 11:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doName(self, frt, pag, r, c, p, i, w):
        self.name = w
        self.acc = self.sql.getRec("telmst", where=[("tdm_name",
            "like", self.name + "%")], order="tdm_name asc", limit=1)
        if not self.acc:
            self.newmst = True
            self.con = 0
        else:
            self.newmst = False
            self.df.setWidget(self.df.B0, "normal")
            self.df.setWidget(self.df.B1, "normal")
            self.doLoadDetail(self.acc[:-1])

    def doGroup(self, frt, pag, r, c, p, i, w):
        try:
            grp = eval(w)
            self.group = ""
            for g in grp:
                if not self.group:
                    self.group = g[0]
                else:
                    self.group = "%s,%s" % (self.group, g[0])
        except:
            self.group = w
        self.df.loadEntry(frt, pag, p, data=self.group)
        if not self.group:
            return
        check = self.group.split(",")
        err = None
        for chk in check:
            acc = self.sql.getRec("telgrp", cols=["tdg_desc"],
                where=[("tdg_group", "=", chk)], limit=1)
            if not acc:
                err = "Invalid Group %s" % chk
                break
        return err

    def doDelAll(self):
        self.sql.delRec("telmst", where=[("tdm_name", "=", self.name)])
        self.sql.delRec("telcon", where=[("tdc_name", "=", self.name)])
        self.sql.delRec("ctlnot", where=[("not_cono", "=", 0),
            ("not_sys", "=", "TEL"), ("not_key", "=", self.name)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doTopEnd(self):
        data = self.df.t_work[0][0][:]
        if self.newmst:
            self.sql.insRec("telmst", data=data)
        elif data != self.acc[:len(data)]:
            tdm = self.sql.telmst_col
            data.append(self.acc[tdm.index("tdm_xflag")])
            self.sql.updRec("telmst", data=data, where=[("tdm_name",
                "=", self.name)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doTopExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doUp(self):
        acc = self.sql.getRec("telmst", where=[("tdm_name", "<",
            self.name)], order="tdm_name desc", limit=1)
        if acc:
            self.doLoadDetail(acc)
            self.df.focusField("T", 0, 2)
        else:
            showWarning(self.opts["mf"].body, "Beginning of File",
                "This is the beginning of the file.")
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doDn(self):
        acc = self.sql.getRec("telmst", where=[("tdm_name", ">",
            self.name)], order="tdm_name asc", limit=1)
        if acc:
            self.doLoadDetail(acc)
            self.df.focusField("T", 0, 2, "N")
        else:
            showWarning(self.opts["mf"].body, "End of File",
                "You have reached the end of the file.")
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doContacts(self):
        # Display contacts and allow adding, editing etc.
        recs = self.sql.getRec("telcon", cols=["tdc_contact",
            "tdc_desig", "tdc_telno", "tdc_celno", "tdc_email"],
            where=[("tdc_name", "=", self.name)], order="tdc_contact")
        if not recs:
            recs = [["", "", "", "", ""]]
        titl = "Contacts"
        cols = (
            ("a", "Name", 30, "NA"),
            ("b", "Designation", 20, "NA"),
            ("c", "Telephone", 20, "NA"),
            ("d", "Mobile", 20, "NA"),
            ("e", "Email-Address", 50, "TX"))
        butt = (
            ("Add", self.doConAdd),
            ("Exit", self.doConExit))
        state = self.df.disableButtonsTags()
        self.opts["mf"].updateStatus("Select a Contact to Edit or an Action")
        self.contyp = None
        self.chg = SelectChoice(self.df.mstFrame, titl=titl, cols=cols,
            data=recs, butt=butt, sort=False)
        self.df.enableButtonsTags(state=state)
        if not self.contyp and self.chg.selection:
            self.contyp = "chg"
            con = self.chg.selection[1].strip()
            self.conchg = self.sql.getRec("telcon", where=[("tdc_name",
                "=", self.name), ("tdc_contact", "=", con)], limit=1)
        if self.contyp in ("add", "chg"):
            self.doConChanges()
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doConAdd(self):
        self.contyp = "add"

    def doConExit(self):
        self.contyp = "quit"

    def doConChanges(self):
        fld = []
        if self.contyp == "chg":
            tit = ("Change Contact",)
            but = (
                ("Delete",None,self.doChgDelete,1,None,None),
                ("Apply",None,self.doChgEnd,1,None,None),
                ("Quit",None,self.doChgExit,1,None,None))
            self.contact = self.conchg[1]
        else:
            tit = ("Add Contact",)
            but = None
        fld = (
            (("T",0,0,0),"I@tdc_contact",0,"","",
                "","N",None,None,None,("notblank",)),
            (("T",0,1,0),"I@tdc_desig",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,2,0),"I@tdc_telno",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,3,0),"I@tdc_celno",0,"","",
                "","N",None,None,None,("efld",)),
            (("T",0,4,0),"I@tdc_email",0,"","",
                "","N",None,None,None,("efld",)))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.rp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doChgEnd,"n"),),
            txit=(self.doChgExit,))
        if self.contyp == "chg":
            for x in range(5):
                self.rp.loadEntry("T", 0, x, data=self.conchg[x+1])
            self.rp.focusField("T", 0, 1, clr=False)
        else:
            self.rp.focusField("T", 0, 1)
        self.rp.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doChgDelete(self):
        self.sql.delRec("telcon", where=[("tdc_name", "=", self.name),
            ("tdc_contact", "=", self.conchg[1])])
        self.opts["mf"].dbm.commitDbase()
        self.doChgExit()

    def doChgEnd(self):
        data = [self.name]
        data.extend(self.rp.t_work[0][0])
        if self.contyp == "add":
            self.sql.insRec("telcon", data=data)
            self.opts["mf"].dbm.commitDbase()
        elif self.contyp == "chg" and data != self.conchg[:len(data)]:
            tdc = self.sql.telcon_col
            data.append(self.conchg[tdc.index("tdc_xflag")])
            self.sql.updRec("telcon", data=data, where=[("tdc_name",
                "=", self.name), ("tdc_contact", "=", self.contact)])
            self.opts["mf"].dbm.commitDbase()
        self.doChgExit()

    def doChgExit(self):
        self.rp.closeProcess()

    def doImport(self):
        grps = []
        commit = False
        self.opts["mf"].updateStatus("")
        self.df.mstFrame.focus_force()
        self.df.mstFrame.winfo_toplevel().update()
        self.df.setWidget(self.df.mstFrame, state="hide")
        spl = SplashScreen(self.opts["mf"].body,
            "Importing Contact Details\n\nPlease Wait")
        sql = Sql(self.opts["mf"].dbm, tables="ftable",
            prog=self.__class__.__name__)
        bkm = sql.getRec("ftable", where=[("ft_tabl", "=", "bkmcon")],
            cols=["count(*)"], limit=1)
        if bkm and bkm[0]:
            commit = True
            sql = Sql(self.opts["mf"].dbm, tables="bkmcon",
                prog=self.__class__.__name__)
            bkc = sql.bkmcon_col
            recs = sql.getRec("bkmcon")
            for rec in recs:
                if not rec[bkc.index("bkc_telno")] and not \
                        rec[bkc.index("bkc_faxno")] and not \
                        rec[bkc.index("bkc_celno")] and not \
                        rec[bkc.index("bkc_email")]:
                    continue
                nam = rec[bkc.index("bkc_sname")]
                fnm = rec[bkc.index("bkc_names")]
                if fnm:
                    nam = "%s, %s" % (nam, fnm.split()[0])
                data = [
                    nam,
                    rec[bkc.index("bkc_addr1")],
                    rec[bkc.index("bkc_addr2")],
                    rec[bkc.index("bkc_addr3")],
                    rec[bkc.index("bkc_pcode")],
                    rec[bkc.index("bkc_telno")],
                    rec[bkc.index("bkc_faxno")],
                    rec[bkc.index("bkc_celno")],
                    rec[bkc.index("bkc_email")],
                    "BKM"]
                chk = self.sql.getRec("telmst", where=[("tdm_name",
                    "=", nam)], limit=1)
                if not chk:
                    self.sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    self.sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", nam)])
            grps.append(["BKM", "Bookings"])
        bwl = sql.getRec("ftable", where=[("ft_tabl", "=", "bwltab")],
            cols=["count(*)"], limit=1)
        if bwl and bwl[0]:
            commit = True
            sql = Sql(self.opts["mf"].dbm, tables="bwltab",
                prog=self.__class__.__name__)
            btb = sql.bwltab_col
            recs = sql.getRec("bwltab")
            for rec in recs:
                if not rec[btb.index("btb_home")] and not \
                        rec[btb.index("btb_work")] and not \
                        rec[btb.index("btb_cell")] and not \
                        rec[btb.index("btb_mail")]:
                    continue
                nam = rec[btb.index("btb_surname")]
                fnm = rec[btb.index("btb_names")]
                if fnm:
                    nam = "%s, %s" % (nam, fnm.split()[0])
                data = [
                    nam,
                    rec[btb.index("btb_add1")],
                    rec[btb.index("btb_add2")],
                    rec[btb.index("btb_add3")],
                    rec[btb.index("btb_pcod")],
                    rec[btb.index("btb_home")],
                    rec[btb.index("btb_work")],
                    rec[btb.index("btb_cell")],
                    rec[btb.index("btb_mail")],
                    "BWL"]
                chk = self.sql.getRec("telmst", where=[("tdm_name",
                    "=", nam)], limit=1)
                if not chk:
                    self.sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    self.sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", nam)])
            grps.append(["BWL", "Bowls"])
        crs = sql.getRec("ftable", where=[("ft_tabl", "=", "crsmst")],
            cols=["count(*)"], limit=1)
        if crs and crs[0]:
            commit = True
            sql = Sql(self.opts["mf"].dbm, tables="crsmst",
                prog=self.__class__.__name__)
            crm = sql.crsmst_col
            recs = sql.getRec("crsmst", where=[("crm_stat", "<>", "X")])
            for rec in recs:
                nam = "%s" % rec[crm.index("crm_name")]
                data = [
                    nam,
                    rec[crm.index("crm_add1")],
                    rec[crm.index("crm_add2")],
                    rec[crm.index("crm_add3")],
                    rec[crm.index("crm_pcod")],
                    rec[crm.index("crm_tel")],
                    rec[crm.index("crm_fax")],
                    "", "", "CRS"]
                chk = self.sql.getRec("telmst", where=[("tdm_name",
                    "=", nam)], limit=1)
                if not chk:
                    self.sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    self.sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", nam)])
                con = rec[crm.index("crm_mgr")]
                eml = rec[crm.index("crm_mgr_email")]
                if eml:
                    data = [nam, con, "Manager", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
                con = rec[crm.index("crm_acc")]
                eml = rec[crm.index("crm_acc_email")]
                if eml:
                    data = [nam, con, "Accounts", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
                con = rec[crm.index("crm_ord")]
                eml = rec[crm.index("crm_ord_email")]
                if eml:
                    data = [nam, con, "Orders", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
            grps.append(["CRS", "Creditors"])
        drs = sql.getRec("ftable", where=[("ft_tabl", "=", "drsmst")],
            cols=["count(*)"], limit=1)
        if drs and drs[0]:
            commit = True
            sql = Sql(self.opts["mf"].dbm, tables="drsmst",
                prog=self.__class__.__name__)
            drm = sql.drsmst_col
            recs = sql.getRec("drsmst", where=[("drm_stat", "<>", "X")])
            for rec in recs:
                nam = "%s" % rec[drm.index("drm_name")]
                data = [
                    nam,
                    rec[drm.index("drm_add1")],
                    rec[drm.index("drm_add2")],
                    rec[drm.index("drm_add3")],
                    rec[drm.index("drm_pcod")],
                    rec[drm.index("drm_tel")],
                    rec[drm.index("drm_fax")],
                    "", "", "DRS"]
                chk = self.sql.getRec("telmst", where=[("tdm_name",
                    "=", nam)], limit=1)
                if not chk:
                    self.sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    self.sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", nam)])
                con = rec[drm.index("drm_mgr")]
                eml = rec[drm.index("drm_mgr_email")]
                if eml:
                    data = [nam, con, "Manager", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
                con = rec[drm.index("drm_acc")]
                eml = rec[drm.index("drm_acc_email")]
                if eml:
                    data = [nam, con, "Accounts", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
                con = rec[drm.index("drm_sls")]
                eml = rec[drm.index("drm_sls_email")]
                if eml:
                    data = [nam, con, "Orders", "", "", eml]
                    chk = self.sql.getRec("telcon", where=[("tdc_name",
                        "=", nam), ("tdc_contact", "=", con)], limit=1)
                    if not chk:
                        self.sql.insRec("telcon", data=data)
                    elif data != chk[:len(data)]:
                        tdc = self.sql.telcon_col
                        data.append(chk[tdc.index("tdc_xflag")])
                        self.sql.updRec("telcon", data=data, where=[("tdc_name",
                            "=", nam), ("tdc_contact", "=", con)])
            grps.append(["DRS", "Debtors"])
        mem = sql.getRec("ftable", where=[("ft_tabl", "=", "memmst")],
            cols=["count(*)"], limit=1)
        if mem and mem[0]:
            commit = True
            sql = Sql(self.opts["mf"].dbm, tables=["memmst", "memadd",
                "memkon"], prog=self.__class__.__name__)
            mlm = sql.memmst_col
            mla = sql.memadd_col
            recs = sql.getRec("memmst", where=[("mlm_state", "=", "A")])
            for rec in recs:
                coy = rec[mlm.index("mlm_cono")]
                num = rec[mlm.index("mlm_memno")]
                nam = "%s, %s" % (rec[mlm.index("mlm_surname")],
                    rec[mlm.index("mlm_names")])
                add = sql.getRec("memadd", where=[("mla_cono",
                    "=", coy), ("mla_memno", "=", num), ("mla_type", "=",
                    "P")], limit=1)
                if not add:
                    add = [coy, num, "P", "", "", "", "", "", "", ""]
                add3 = add[mla.index("mla_add3")]
                city = add[mla.index("mla_city")]
                coun = add[mla.index("mla_country")]
                if not add3:
                    if city:
                        add3 = city
                        if coun:
                            add3 = "%s, %s" % (add3, coun)
                    elif coun:
                        add3 = coun
                kon = sql.getRec(tables=["memctk", "memkon"],
                    cols=["mck_type", "mlk_detail"], where=[("mlk_cono",
                    "=", coy), ("mlk_memno", "=", num),
                    ("mck_code=mlk_code",)])
                tel = ""
                fax = ""
                cel = ""
                eml = ""
                for k in kon:
                    if k[0] == "E" and not eml:
                        eml = k[1]
                    elif k[0] == "H":
                        tel = k[1]
                    elif k[0] == "W" and not tel:
                        tel = k[1]
                    elif k[0] == "M":
                        cel = k[1]
                data = [
                    nam,
                    add[mla.index("mla_add1")],
                    add[mla.index("mla_add2")],
                    add3,
                    add[mla.index("mla_code")],
                    tel, fax, cel, eml,
                    "MEM"]
                chk = self.sql.getRec("telmst", where=[("tdm_name",
                    "=", nam)], limit=1)
                if not chk:
                    self.sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    self.sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", nam)])
            grps.append(["MEM", "Members"])
        # Others
        tabs = {
            "BKS": ["Book Club", "bksown", None,
                ["bof_snam", "bof_fnam", "bof_add1", "bof_add2", "bof_add3",
                    "bof_pcod", "bof_home", "bof_work", "bof_cell",
                    "bof_mail"]],
            "LON": ["Loan Ledger", "lonmf1", "lm1_cono",
                ["lm1_name", "lm1_addr1", "lm1_addr2", "lm1_addr3", "lm1_pcode",
                    "lm1_telno", "lm1_faxno", "lm1_celno", "lm1_email"]],
            "OWN": ["Property Owners", "rcaowm", "rom_cono",
                ["rom_name", "rom_add1", "rom_add2", "rom_add3", "rom_pcod",
                    "rom_home", "rom_office", "rom_mobile", "rom_fax",
                    "rom_email"]],
            "TNT": ["Property Tenants", "rcatnm", "rtn_cono",
                ["rtn_name", "rtn_addr1", "rtn_addr2", "rtn_addr3", "rtn_pcode",
                    "rtn_telno", "rtn_email"]],
            "RTL": ["Rental Tenants", "rtlmst", "rtm_cono",
                ["rtm_name", "rtm_addr1", "rtm_addr2", "rtm_addr3", "rtm_pcode",
                    "rtm_telno", "rtm_email"]],
            "SCP": ["Sectional Competitions", "scpmem", "scm_cono",
                ["scm_surname", "scm_names", "scm_email", "scm_phone"]],
            "EMP": ["Employees", "wagmst", "wgm_cono",
                ["wgm_sname", "wgm_fname", "wgm_addr1", "wgm_addr2",
                    "wgm_addr3", "wgm_pcode", "wgm_telno", "wgm_emadd"]]}
        for grp in tabs:
            des = tabs[grp][0]
            tab = tabs[grp][1]
            coy = tabs[grp][2]
            col = tabs[grp][3]
            sql = Sql(self.opts["mf"].dbm, ["telmst", tab])
            if sql.error:
                continue
            rec = sql.getRec(tab, cols=col)
            for r in rec:
                snam = None
                data = ["", "", "", "", "", "", "", "", "", grp]
                for n, c in enumerate(col):
                    x = c.split("_")[1]
                    if r[n]:
                        if x == "name":
                            data[0] = r[n]
                        elif x in ("snam", "surname", "sname"):
                            snam = r[n]
                        elif snam and x in ("fnam", "names", "fname"):
                            data[0] = "%s, %s" % (snam, r[n].split()[0])
                            snam = None
                        elif x in ("add1", "addr1"):
                            data[1] = r[n]
                        elif x in ("add2", "addr2"):
                            data[2] = r[n]
                        elif x in ("add3", "addr3"):
                            data[3] = r[n]
                        elif x in ("pcod", "pcode"):
                            data[4] = r[n]
                        elif x in ("home", "work", "office", "phone"):
                            data[5] = r[n]
                        elif x in ("faxno", "fax"):
                            data[6] = r[n]
                        elif x in ("cell", "celno", "mobile"):
                            data[7] = r[n]
                        elif x in ("mail", "email", "emadd"):
                            data[8] = r[n]
                if not data[5] and not data[6] and not data[7] and not data[8]:
                    continue
                chk = sql.getRec("telmst", where=[("tdm_name",
                    "=", data[0])], limit=1)
                if not chk:
                    sql.insRec("telmst", data=data)
                elif data != chk[:len(data)]:
                    tdm = self.sql.telmst_col
                    data.append(chk[tdm.index("tdm_xflag")])
                    sql.updRec("telmst", data=data, where=[("tdm_name",
                        "=", data[0])])
            grps.append([grp, des])
        # Groups
        for g in grps:
            chk = self.sql.getRec("telgrp", where=[("tdg_group", "=",
                g[0])], limit=1)
            if not chk:
                self.sql.insRec("telgrp", data=g)
        spl.closeSplash()
        if commit:
            self.opts["mf"].dbm.commitDbase(ask=True)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.window.update_idletasks()
        self.df.focusField("T", 0, 1)

    def doLoadDetail(self, data):
        self.name = data[0]
        for num, fld in enumerate(data[:-1]):
            self.df.loadEntry(self.df.frt, self.df.pag, num, data=fld)

    def doNotes(self):
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], 0, "", self.opts["capnm"],
            "TEL", self.name)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrint(self):
        titl = "Select the Required Print Options"
        cols = (
            ("a", "C", 1, "UA", "N"),
            ("b", "Description", 30, "NA", "N"))
        if self.df.last[0][0] != 1:
            data = [("A", "Print Card")]
        else:
            data = []
        data.extend([
            ("B", "Print Directory"),
            ("C", "Print Contacts"),
            ("D", "Print Notes")])
        ss = SelectChoice(self.df.mstFrame, titl, cols, data, sort=False)
        self.opts["mf"].updateStatus("")
        if not ss.selection:
            self.df.focusField(self.df.frt, self.df.pag, self.df.col)
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        if ss.selection[1] == "A":
            head = ["Card for %s" % self.name]
            whr = [("tdm_name", "=", self.name)]
            TabPrt(self.opts["mf"], name=self.__class__.__name__,
                tabs="telmst", head=head, where=whr)
        elif ss.selection[1] == "D":
            self.notes = NotesPrint(self.opts["mf"], 0, "", "TEL", loop=False)
            if not self.notes.data:
                pass
            else:
                data = []
                p = ProgressBar(self.opts["mf"].body,
                    typ="Generating the Report",
                    mxs=len(self.notes.data), esc=True)
                for num, dat in enumerate(self.notes.data):
                    p.displayProgress(num)
                    if p.quit:
                        break
                    desc = textFormat(dat[5], width=50)
                    for n, d in enumerate(desc):
                        if not n:
                            data.append([dat[2], dat[4],
                            CCD(dat[3], "d1", 10).disp, dat[6],
                            CCD(dat[7], "d1", 10).disp, d])
                        else:
                            data.append(["", "", "", "", "", d])
                p.closeProgress()
                if not p.quit:
                    name = self.__class__.__name__
                    head = ["Telephone Directory Notes Listing"]
                    cols = [
                        ["a", "NA", 30, "Name",      "y"],
                        ["b", "NA", 20, "User-Name", "y"],
                        ["c", "NA", 10, "Cap-Date",  "y"],
                        ["d", "UA",  1, "F",         "y"],
                        ["e", "NA", 10, "Act-Date",  "y"],
                        ["f", "NA", 50, "Details",   "y"]]
                    RepPrt(self.opts["mf"], name=name, tables=data,
                        heads=head, cols=cols, ttype="D",
                        repprt=self.notes.df.repprt,
                        repeml=self.notes.df.repeml)
        else:
            tit = ["Telephone Directory"]
            grp = {
                "stype": "R",
                "tables": ("telgrp",),
                "cols": (
                    ("tdg_group", "UA", 3, "Grp"),
                    ("tdg_desc", "NA", 30, "Description")),
                "order": "tdg_desc"}
            fld = ((("T",0,0,0),"IUA",3,"Group","",
                "","N",self.prGrp,grp,None,("efld",)),)
            self.pr = TartanDialog(self.opts["mf"], tops=True,
                title=tit, eflds=fld, tend=((self.prEnd,"y"),),
                txit=(self.prExit,))
            self.pr.mstFrame.wait_window()
            if not self.prxit:
                if self.prgrp:
                    if ss.selection[1] == "B":
                        head = ["Details for Group %s" % self.prgrp]
                        whr = [("tdm_group", "=", self.prgrp)]
                    else:
                        head = ["Contacts for Group %s" % self.prgrp]
                        whr = [
                            ("tdm_group", "=", self.prgrp),
                            ("tdc_name=tdm_name",)]
                else:
                    if ss.selection[1] == "B":
                        head = ["Cards for All Groups"]
                        whr = []
                    else:
                        head = ["Contacts for All Groups"]
                        whr = []
                if ss.selection[1] == "B":
                    tab = ["telmst"]
                    col = ["tdm_name", "tdm_telno", "tdm_faxno",
                        "tdm_mobile", "tdm_email"]
                else:
                    tab = ["telmst", "telcon"]
                    col = ["tdm_name", "tdc_contact", "tdc_desig",
                        "tdc_telno", "tdc_celno", "tdc_email"]
                prtdia = (("Y","V"), ("Y","N"))
                RepPrt(self.opts["mf"], name=self.__class__.__name__,
                    tables=tab, heads=head, cols=col, where=whr,
                    order="tdm_name", prtdia=prtdia)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def prGrp(self, frt, pag, r, c, p, i, w):
        self.prgrp = w

    def prEnd(self):
        self.prxit = False
        self.pr.closeProcess()

    def prExit(self):
        self.prxit = True
        self.pr.closeProcess()

    def doApply(self):
        data = self.df.t_work[0][0][:]
        if self.df.frt == "T":
            if self.newmst:
                self.sql.insRec("telmst", data=data)
            else:
                data.append(self.acc[self.sql.telmst_col.index("tdm_xflag")])
                self.sql.updRec("telmst", data=data, where=[("tdm_name",
                    "=", self.name)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doCancel(self):
        self.opts["mf"].dbm.rollbackDbase()
        self.df.focusField("T", 0, 1)

# vim:set ts=4 sw=4 sts=4 expandtab:
