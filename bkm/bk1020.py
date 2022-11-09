"""
SYNOPSIS
    Accommodation Bookings.

    This file is part of Tartan Systems (TARTAN).

    flags used:

        self.edit    - editing the booking
        self.trans   - created a transaction
        self.ender   - self.doEnd has been executed for page 2
        self.inv     - booking has been invoiced
        self.mprint  - print statement of movements
        self.newcon  - new contacts record
        self.newmst  - new booking
        self.quit    - self.doQuit has been selected
        self.fee     - cancellation fee is raised
        self.rev     - booking is cancelled and invoice reversed

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

import copy, time
from TartanClasses import ASD, CCD, DrawForm, GetCtl, NotesCreate
from TartanClasses import PrintBookingInvoice, SelectChoice, TartanDialog
from TartanClasses import Sql, TabPrt
from tartanFunctions import askQuestion, callModule, chkGenAcc, dateDiff
from tartanFunctions import doPrinter, genAccNum, getFileName, getModName
from tartanFunctions import getVatRate, projectDate, showError, textFormat
from tartanWork import bktrtp, mthnam

class bk1020(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            if "wait" in self.opts:
                self.df.mstFrame.wait_window()
            else:
                self.opts["mf"].startLoop()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        self.taxdf = ctlmst["ctm_taxdf"]
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        self.glint = bkmctl["cbk_glint"]
        self.bktpl = bkmctl["cbk_bkgtpl"]
        self.terms = bkmctl["cbk_terms"]
        self.ivtpl = bkmctl["cbk_invtpl"]
        self.fromad = bkmctl["cbk_emadd"]
        if self.glint == "Y":
            ctlctl = gc.getCtl("ctlctl", self.opts["conum"])
            if not ctlctl:
                return
            ctls = [
                "bank_1",
                "vat_ctl",
                "bkm_chq",
                "bkm_csh",
                "bkm_ccg",
                "bkm_ctl"]
            if gc.chkRec(self.opts["conum"], ctlctl, ctls):
                return
            self.bnkctl = ctlctl["bank_1"]
            self.vatctl = ctlctl["vat_ctl"]
            self.chqctl = ctlctl["bkm_chq"]
            self.cshctl = ctlctl["bkm_csh"]
            self.ccgctl = ctlctl["bkm_ccg"]
            self.bkmctl = ctlctl["bkm_ctl"]
        tabs = [
            "ctlmst", "chglog", "ctlnot", "ctlvmf", "ctlvtf", "bkmmst",
            "bkmcon", "bkmunm", "bkmtrn", "bkmrtm", "bkmrtr", "bkmrtt",
            "bkmlet", "tpldet"]
        if self.glint == "Y":
            tabs.extend(["genmst", "gentrn"])
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.curdt = int(self.sysdtw / 100)
        self.batno = "B%s" % self.curdt
        self.number = 0
        return True

    def mainProcess(self):
        bkm = {
            "stype": "R",
            "tables": ["bkmmst", "bkmcon"],
            "cols": [
                ("bkm_number", "", 0, "Number"),
                ("bkm_btype", "", 0, "B"),
                ("bkm_state", "", 0, "S"),
                ("bkc_sname", "", 20, "Surname", "Y"),
                ("bkc_names", "", 20, "Names", "F"),
                ("bkm_group", "", 20, "Group", "F"),
                ("bkm_arrive", "d1", 10, "Arrive-Dt", "F"),
                ("bkm_depart", "", 0, "Depart-Dt"),
                ("bkm_units", "", 0, "Units")],
            "where": [
                ("bkm_cono", "=", self.opts["conum"]),
                ("bkc_cono=bkm_cono",),
                ("bkc_ccode=bkm_ccode",)],
            "order": "bkc_sname, bkm_arrive"}
        bkc = {
            "stype": "R",
            "tables": ("bkmcon",),
            "cols": (
                ("bkc_ccode", "", 0, "Code"),
                ("bkc_title", "", 0, "Title"),
                ("bkc_sname", "", 0, "Surname", "Y"),
                ("bkc_names", "", 0, "Names", "F")),
            "where": [
                ("bkc_cono", "=", self.opts["conum"])],
            "order": "bkc_sname"}
        r1s = (
            ("Accommodation","A"),
            ("Other","O"))
        r2s = (
            ("Continue","C"),
            ("Edit","E"))
        r3s = (
            ("Enquiry","Q"),
            ("Confirmed","C"),
            ("Settled","S"),
            ("Cancelled","X"))
        tag = (
            ("Booking",self.chgPage,("T",1,1),None),
            ("Contact",self.chgPage,(("T",1,2),("T",1,0)),("T",1,1)))
        fld = [
            (("T",1,0,0),"IUI",7,"Booking Number","",
                0,"Y",self.doNumber,bkm,None,None),
            [("T",1,1,0),("IRB",r1s),0,"Booking Type","",
                "A","N",self.doType,None,None,None],
            (("T",1,2,0),"ITX",30,"Group Name","",
                "","N",self.doGroup,None,None,None),
            (("T",1,3,0),"IUI",3,"Number of Persons","",
                0,"N",self.doGuests,None,None,("notzero",)),
            (("T",1,4,0),"ID1",10,"Arrival (YYYYMMDD)","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",1,5,0),"ID1",10,"Departure (YYYYMMDD)","",
                0,"N",self.doDate,None,None,("efld",)),
            (("T",1,6,0),("IRB",r2s),0,"Units","",
                "C","N",self.doUnits,None,None,None),
            (("T",1,6,0),"OTv",45,""),
            (("T",1,7,0),"OSD",13.2,"Value"),
            (("T",1,8,0),"ISD",13.2,"Initial Deposit","",
                0,"N",self.doDeposit,None,None,None),
            (("T",1,9,0),"ID1",10,"Initial Dep Due","",
                0,"N",self.doDepdate,None,None,None),
            (("T",1,10,0),"ISD",13.2,"Additional Deposit","",
                0,"N",self.doDeposit,None,None,None),
            (("T",1,11,0),"Id1",10,"Additional Dep Due","",
                0,"N",self.doDepdate,None,None,None),
            (("T",1,12,0),"OSD",13.2,"Account Balance"),
            (("T",1,13,0),"ITX",65,"Remarks","",
                "","N",self.doRemarks,None,None,None),
            (("T",1,14,0),("ORB",r3s),0,"Booking Status"),
            (("T",2,0,0),"IUA",7,"Contact Code","",
                "","N",self.doContact,bkc,None,None),
            (("T",2,1,0),"ITX",6,"Title","",
                "","N",self.doTitle,None,None,("notblank",)),
            (("T",2,2,0),"ITX",30,"Surname","",
                "","N",self.doSurname,None,None,("notblank",)),
            (("T",2,3,0),"ITX",30,"Names","",
                "","N",self.doNames,None,None,("efld",)),
            (("T",2,4,0),"ITX",30,"Address Line 1","",
                "","N",None,None,None,("efld",)),
            (("T",2,5,0),"ITX",30,"Address Line 2","",
                "","N",None,None,None,("efld",)),
            (("T",2,6,0),"ITX",30,"Address Line 3","",
                "","N",None,None,None,("efld",)),
            (("T",2,7,0),"ITX",4,"Postal Code","",
                "","N",None,None,None,("efld",)),
            (("T",2,8,0),"ITX",20,"Telephone Number","",
                "","N",None,None,None,("efld",)),
            (("T",2,9,0),"ITX",20,"Fax Number","",
                "","N",None,None,None,("efld",)),
            (("T",2,10,0),"ITX",20,"Mobile Number","",
                "","N",None,None,None,("efld",)),
            (("T",2,11,0),"ITX",30,"E-Mail Address","",
                "","N",self.doEmail,None,None,("email",)),
            (("T",2,12,0),"IUI",10,"VAT Number","",
                "","N",None,None,None,None)]
        if "args" in self.opts:
            fld[1][3] += "(noesc)"
        on = (("T",1,0), ("T",1,2))
        off = ("T",1,1)
        but = (
            ("Edit",None,self.doEdit,0,("T",1,0),None,
                "Edit the current booking"),
            ("Transact",None,self.doTrans,0,("T",1,0),None,
                "Create transactions for the current booking"),
            ("Movements",None,self.doMoves,0,("T",1,0),None,
                "Display all movements for the current booking"),
            ("Notes",None,self.doNotes,0,("T",1,0),None,
                "Create/Amend Notes for the current booking"),
            ("Accept",None,self.doAccept,0,on,off,
                "Save/Print and Exit the current booking"),
            ("Quit",None,self.doQuit,1,None,("T",1,1),
                "Quit the current booking creation or amendment"))
        tnd = (None, (self.doEnd,"n"), (self.doEnd,"n"))
        txt = (None, self.doExit, None)
        self.df = TartanDialog(self.opts["mf"], tops=False,
            tags=tag, eflds=fld, butt=but, tend=tnd, txit=txt,
            clicks=self.doClick)
        if "args" in self.opts:
            self.number = self.opts["args"]
            self.df.doKeyPressed("T", 1, 0, data=self.number)

    def doEdit(self):
        if self.number and self.depart < self.sysdtw:
            ok = askQuestion(self.opts["mf"].body, "Departed",
                "Departure Date in the Past, are you Sure you want to Edit?",
                default="no")
            if ok == "no":
                return
        self.edit = True
        self.ender = False
        if self.df.pag == 1:
            self.df.focusField(self.df.frt, self.df.pag, 2)
        else:
            self.df.focusField(self.df.frt, self.df.pag, 1)

    def doClick(self, *opts):
        if not self.number or not self.edit:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doNumber(self, frt, pag, r, c, p, i, w):
        self.trans = False
        self.ender = False
        self.edit = False
        self.quit = False
        self.inv = False
        self.rev = False
        if not w:
            if "args" in self.opts:
                ok = "yes"
            else:
                ok = askQuestion(self.opts["mf"].window, "New Booking",
                    "Is This a New Booking?", default="yes")
            if ok == "no":
                return "Invalid Booking Number"
            else:
                self.number = 0
                self.state = "Q"
                self.newmst = True
                self.units = ""
                self.df.loadEntry("T", 1, 6, data="E")
                self.df.loadEntry(frt, pag, p + 15, data=self.state)
                return
        self.oldmst = self.sql.getRec("bkmmst", where=[("bkm_cono",
            "=", self.opts["conum"]), ("bkm_number", "=", w)], limit=1)
        if not self.oldmst:
            return "Invalid Booking Number"
        inv = self.sql.getRec("bkmtrn", where=[("bkt_cono", "=",
            self.opts["conum"]), ("bkt_number", "=", w), ("bkt_type", "=", 2)])
        if inv:
            self.inv = True
        self.number = w
        self.newmst = False
        self.newcon = False
        self.ender = True
        self.btype = self.oldmst[self.sql.bkmmst_col.index("bkm_btype")]
        self.df.loadEntry("T", 1, 1, data=self.btype)
        self.group = self.oldmst[self.sql.bkmmst_col.index("bkm_group")]
        self.df.loadEntry("T", 1, 2, data=self.group)
        self.guests = self.oldmst[self.sql.bkmmst_col.index("bkm_guests")]
        self.df.loadEntry("T", 1, 3, data=self.guests)
        self.arrive = self.oldmst[self.sql.bkmmst_col.index("bkm_arrive")]
        self.df.loadEntry("T", 1, 4, data=self.arrive)
        self.depart = self.oldmst[self.sql.bkmmst_col.index("bkm_depart")]
        self.df.loadEntry("T", 1, 5, data=self.depart)
        if self.btype == "A":
            self.bdays = dateDiff(self.arrive, self.depart, "days")
        else:
            self.bdays = dateDiff(self.arrive, self.depart, "days") + 1
        self.df.loadEntry("T", 1, 6, data="C")
        self.units = self.oldmst[self.sql.bkmmst_col.index("bkm_units")]
        self.df.loadEntry("T", 1, 7, data=self.units)
        self.value = self.oldmst[self.sql.bkmmst_col.index("bkm_value")]
        self.df.loadEntry("T", 1, 8, data=self.value)
        self.stddep = self.oldmst[self.sql.bkmmst_col.index("bkm_stddep")]
        self.df.loadEntry("T", 1, 9, data=self.stddep)
        self.stddte = self.oldmst[self.sql.bkmmst_col.index("bkm_stddte")]
        self.df.loadEntry("T", 1, 10, data=self.stddte)
        self.grpdep = self.oldmst[self.sql.bkmmst_col.index("bkm_grpdep")]
        self.df.loadEntry("T", 1, 11, data=self.grpdep)
        self.grpdte = self.oldmst[self.sql.bkmmst_col.index("bkm_grpdte")]
        self.df.loadEntry("T", 1, 12, data=self.grpdte)
        self.df.loadEntry("T", 1, 13, data=self.getBalance().work)
        self.remarks = self.oldmst[self.sql.bkmmst_col.index("bkm_remarks")]
        self.df.loadEntry("T", 1, 14, data=self.remarks)
        self.state = self.oldmst[self.sql.bkmmst_col.index("bkm_state")]
        self.df.loadEntry("T", 1, 15, data=self.state)
        self.ccode = self.oldmst[self.sql.bkmmst_col.index("bkm_ccode")]
        self.oldcon = self.sql.getRec("bkmcon", where=[("bkc_cono",
            "=", self.opts["conum"]), ("bkc_ccode", "=", self.ccode)], limit=1)
        self.title = self.oldcon[self.sql.bkmcon_col.index("bkc_title")]
        self.sname = self.oldcon[self.sql.bkmcon_col.index("bkc_sname")]
        self.names = self.oldcon[self.sql.bkmcon_col.index("bkc_names")]
        self.email = self.oldcon[self.sql.bkmcon_col.index("bkc_email")]
        for num, dat in enumerate(self.oldcon[1:-1]):
            self.df.loadEntry("T", 2, num, data=dat)
        return "nd"

    def doType(self, frt, pag, r, c, p, i, w):
        if self.state != "Q" and w != self.btype:
            self.df.loadEntry(frt, pag, p, data=self.btype)
            return "Invalid Type"
        if not self.newmst:
            if w != self.btype:
                ok = askQuestion(self.opts["mf"].window, "Change Type",
                    "Do You Want to Change the Type of the Booking?",
                    default="no")
                if ok == "no":
                    self.df.loadEntry(frt, pag, p, data=self.btype)
                    return "Invalid Type"
                self.doUnBook()
                for x in range(7, 15):
                    self.df.loadEntry("T", 1, x, data="")
        self.btype = w

    def doUnBook(self):
        self.sql.updRec("bkmmst", cols=["bkm_units"], data=[""],
            where=[("bkm_cono", "=", self.opts["conum"]), ("bkm_number",
            "=", self.number)])
        self.sql.delRec("bkmrtt", where=[("brt_cono", "=", self.opts["conum"]),
            ("brt_number", "=", self.number)])
        self.units = ""
        self.df.loadEntry("T", 1, 7, data=self.units)

    def doGroup(self, frt, pag, r, c, p, i, w):
        self.group = w

    def doGuests(self, frt, pag, r, c, p, i, w):
        self.guests = w

    def doDate(self, frt, pag, r, c, p, i, w):
        if p == 4:
            self.arrive = w
            if self.arrive < self.sysdtw:
                ok = askQuestion(self.opts["mf"].window, "Past Date",
                    "Date is in the Past, Accept?", default="no")
                if ok == "no":
                    return "rf"
        else:
            self.depart = w
            if self.depart < self.arrive:
                return "Invalid Date, Before Arrival Date"
            if self.btype == "A" and self.depart == self.arrive:
                return "Arrival and Departure Dates are the Same"
            if self.btype == "A":
                self.bdays = dateDiff(self.arrive, self.depart, "days")
            else:
                self.bdays = dateDiff(self.arrive, self.depart, "days") + 1

    def doUnits(self, frt, pag, r, c, p, i, w):
        if w == "E":
            col = self.sql.bkmunm_col
            where = [("bum_cono", "=", self.opts["conum"])]
            if self.btype == "O":
                where.append(("bum_btyp", "=", self.btype))
            recs = self.sql.getRec("bkmunm", where=where,
                order="bum_btyp, bum_code")
            self.aunits = {}
            whole = False
            for rec in recs:
                typ = rec[col.index("bum_btyp")]
                cod = rec[col.index("bum_code")]
                des = rec[col.index("bum_desc")]
                rms = rec[col.index("bum_room")]
                qty = rec[col.index("bum_maxg")]
                unt = "%s-%s" % (typ, cod)
                if typ == "A" and cod == "ALL":
                    whole = [des, qty]
                else:
                    self.aunits[unt] = {"desc": des, "qty": qty, "rms": {}}
                    if typ == "A":
                        for rr in range(1, rms + 1):
                            self.aunits[unt]["rms"][rr] = True
            bks = self.sql.getRec(tables=["bkmmst", "bkmrtt"],
                cols=[
                    "bkm_arrive",
                    "bkm_depart",
                    "brt_utype",
                    "brt_ucode",
                    "brt_uroom",
                    "brt_quant"],
                where=[
                    ("bkm_cono", "=", self.opts["conum"]),
                    ("bkm_number", "<>", self.number),
                    ("bkm_state", "<>", "X"),
                    ("brt_cono=bkm_cono",),
                    ("brt_number=bkm_number",)],
                order="bkm_arrive, brt_utype, brt_ucode, brt_uroom")
            self.used = []
            for bk in bks:
                cod = "%s-%s" % (bk[2], bk[3])
                if cod not in self.aunits:
                    continue
                u = False
                if self.btype == "A":
                    if bk[0] < self.depart and self.arrive < bk[1]:
                        u = True
                else:
                    if bk[0] <= self.depart and self.arrive <= bk[1]:
                        u = True
                if u:
                    if bk[2] == "A":
                        if bk[4]:
                            self.aunits[cod]["qty"] -= bk[5]
                            if cod in self.aunits:
                                if not self.aunits[cod]["qty"]:
                                    del self.aunits[cod]
                                else:
                                    self.aunits[cod]["rms"][bk[4]] = False
                        else:
                            del self.aunits[cod]
                        if whole and bk[2] == "A":
                            whole = False
                    elif self.aunits[cod]["qty"] != 999:
                        del self.aunits[cod]
            if whole:
                self.aunits["A-ALL"] = {"desc": whole[0], "qty": whole[1],
                    "rms": {1: True}}
            quant = 0
            units = copy.deepcopy(self.aunits)
            for unit in units:
                if unit[0] == "A":
                    rooms = False
                    for rm in units[unit]["rms"]:
                        if units[unit]["rms"][rm]:
                            rooms = True
                    if not rooms:
                        del self.aunits[unit]
                    quant += units[unit]["qty"]
            if not self.aunits:
                showError(self.opts["mf"].window, "No Vacancies",
                    "There are No Available Units for this Booking")
                self.df.focusField("T", 1, 5)
                return
            if unit[0] == "A" and quant < self.guests:
                showError(self.opts["mf"].window, "Quantity",
                    "There is Insufficient Capacity for this Booking")
                self.df.focusField("T", 1, 5)
                return
            # Enter Units
            tit = "Select Units and Rates"
            unt = {
                "stype": "M",
                "func": self.getUnits}
            rms = {
                "stype": "M",
                "func": self.getRooms}
            self.rt1 = {
                "stype": "R",
                "tables": ("bkmrtm","bkmrtr"),
                "cols": (
                    ("brm_code", "", 0, "Cod"),
                    ("brm_desc", "", 0, "Description"),
                    ("brm_base", "", 0, "B")),
                "where": [],
                "group": "brm_type, brm_code, brm_desc, brm_base",
                "order": "brm_type, brm_code"}
            fld = (
                (("T",0,0,0),"OUI",3,"Number of Guests"),
                (("C",0,0,0),"IUA",8,"Unit-Cod","Unit Combined Code",
                    "","Y",self.doUUnit,unt,None,("notblank",)),
                (("C",0,0,1),"ITX",25,"Description","",
                    "","N",self.doUDesc,None,None,("notblank",)),
                (("C",0,0,2),"IUI",3,"Rme","Room Number",
                    0,"N",self.doURme,rms,None,("efld",),None,
                    "Enter the room number or 0 for the whole unit"),
                (("C",0,0,3),"IUI",3,"Rte","Rate Code",
                    "r","N",self.doURate,self.rt1,None,("efld",)),
                (("C",0,0,4),"OTX",25,"Description"),
                (("C",0,0,5),"OUD",10.2,"Normal-Rte"),
                (("C",0,0,6),"IUI",3,"Ppl","Number of People",
                    0,"N",self.doUPpl,None,None,("notzero",),None,
                    "Enter the number of Guests or Items"),
                (("C",0,0,7),"IUI",3,"Per","Number of Periods",
                    0,"N",self.doUPer,None,None,("notzero",),None,
                    "Enter the number of Periods"),
                (("C",0,0,8),"IUD",6.2,"Disc-%","",
                    0,"N",self.doUDisc,None,None,None),
                (("C",0,0,9),"IUD",10.2,"Applied-Rt","Applied Rate",
                    0,"N",self.doUAmount,None,None,("efld",)))
            but = (
                ("Clear",None,self.doUClear,0,("C",0,1),("C",0,2),
                    "Remove All Units from the Booking"),
                ("Edit",None,self.doUEdit,0,("C",0,1),("C",0,2),
                    "Edit Existing Un-Invoiced Units"),
                ("Exit",None,self.doUExit,0,("C",0,1),("C",0,2)),
                ("Quit",None,self.doUQuit,1,None,None))
            cend = ((self.doUEnd,"y"),)
            cxit = (self.doUExit,)
            state = self.df.disableButtonsTags()
            widget = self.df.getWidget(self.df.frt, self.df.pag, self.df.pos)
            self.df.setWidget(widget, "disabled")
            self.df.setWidget(self.df.mstFrame, state="hide")
            self.rt = TartanDialog(self.opts["mf"], tops=True, title=tit,
                eflds=fld, tend=(None,), txit=(None,), cend=cend, cxit=cxit,
                butt=but)
            self.doLoadUnits()
            self.rt.mstFrame.wait_window()
            self.df.setWidget(self.df.mstFrame, state="show")
            self.df.enableButtonsTags(state=state)
        err = self.doCheckUnits()
        if err:
            return err
        self.df.loadEntry(frt, 1, 7, data=self.units)
        self.getBookingValue()
        self.df.loadEntry("T", 1, 8, data=self.value)
        self.stddep, self.stddte, self.grpdep, self.grpdte = self.getDeposit()
        self.df.loadEntry("T", 1, 9, data=self.stddep)
        self.df.loadEntry("T", 1, 10, data=self.stddte)
        self.df.loadEntry("T", 1, 11, data=self.grpdep)
        self.df.loadEntry("T", 1, 12, data=self.grpdte)
        self.df.loadEntry("T", 1, 13, data=self.getBalance().work)
        if not self.stddep:
            return "sk4"

    def doUClear(self):
        ok = askQuestion(self.opts["mf"].window, "Clear",
            "Are You Sure You Want to Clear All Un-Invoiced Units?",
            default="no")
        if ok == "no":
            self.rt.focusField(self.rt.frt, self.rt.pag, self.rt.col)
            return
        self.sql.delRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number),
            ("brt_invno", "=", 0)])
        self.doLoadUnits()

    def doUEdit(self):
        # Display units and allow editing
        recs = self.sql.getRec("bkmrtt",
            cols=["brt_utype", "brt_ucode", "brt_udesc", "brt_uroom",
                "brt_rcode", "brt_rdesc", "brt_nrate", "brt_quant",
                "brt_bdays", "brt_discp", "brt_arate", "brt_seq"],
            where=[
                ("brt_cono", "=", self.opts["conum"]),
                ("brt_number", "=", self.number),
                ("brt_invno", "=", 0)],
            order="brt_utype, brt_ucode, brt_uroom")
        if recs:
            data = []
            for rec in recs:
                d = ["%s-%s" % (rec[0], rec[1])]
                d.extend(rec[2:])
                data.append(d)
            titl = "Entered Units"
            head = ("Unit-Cod", "Description","Rme", "Rte", "Rate-Description",
                "Normal-Rte", "Ppl", "Per", "Disc-%", "Applied-Rt", "Seq")
            lin = {
                "stype": "C",
                "titl": titl,
                "head": head,
                "typs": (("UA", 6), ("NA", 30), ("UI", 3), ("UI", 3),
                    ("NA", 20), ("UD", 10.2), ("UI", 3), ("UI", 3),
                    ("UD", 6.2), ("UD", 10.2), ("UI", 5)),
                "data": data}
            state = self.rt.disableButtonsTags()
            self.opts["mf"].updateStatus("Select a Product to Edit")
            chg = self.rt.selChoice(lin)
            if chg and chg.selection:
                self.change = chg.selection
                self.cseq = int(self.change[-1])
                self.doChgChanges()
            self.rt.enableButtonsTags(state=state)
        self.doLoadUnits()

    def doChgChanges(self):
        tit = ("Change Unit",)
        self.rt2 = {
            "stype": "R",
            "tables": ("bkmrtm",),
            "cols": (
                ("brm_code", "", 0, "Cod"),
                ("brm_desc", "", 0, "Description"),
                ("brm_base", "", 0, "B")),
            "where": [],
            "order": "brm_type, brm_code"}
        fld = (
            (("T",0,0,0),"ONA",8,"Unit-Cod"),
            (("T",0,0,0),"OTX",30,""),
            (("T",0,1,0),"ONA",3,"Room Number"),
            (("T",0,2,0),"IUI",3,"Rate Code","",
                "","N",self.doChgRtc,self.rt2,None,("notzero",)),
            (("T",0,2,0),"OTX",30,""),
            (("T",0,3,0),"OUD",10.2,"Normal Rate"),
            (("T",0,4,0),"IUI",3,"Guests","",
                "","N",self.doChgPpl,None,None,("notzero",)),
            (("T",0,5,0),"IUI",3,"Periods","",
                "","N",self.doChgPer,None,None,("notzero",)),
            (("T",0,6,0),"IUD",6.2,"Discount","",
                "","N",self.doChgDsc,None,None,("efld",)),
            (("T",0,7,0),"IUD",10.2,"Applied Rate","",
                "","N",self.doChgRte,None,None,("efld",)))
        but = [["Delete",None,self.doChgDel,1,None,None]]
        self.cg = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, butt=but, tend=((self.doChgEnd,"n"),),
            txit=(self.doChgExit,))
        for x in range(10):
            self.cg.loadEntry("T", 0, x, data=self.change[x])
            if x == 0:
                self.ctyp, self.ccod = self.change[x].split("-")
            if x == 5:
                self.cnrate = CCD(self.change[x], "UD", 10.2).work
        self.rt2["where"] = [
            ("brm_cono", "=", self.opts["conum"]),
            ("brm_type", "=", self.ctyp)]
        self.cg.focusField("T", 0, 4, clr=False)
        self.dg.mstFrame.wait_window()

    def doChgRtc(self, frt, pag, r, c, p, i, w):
        racc = self.sql.getRec(tables=["bkmrtm", "bkmrtr"],
            cols=["brm_desc", "brm_base", "brr_rate"],
            where=[
                ("brm_cono", "=", self.opts["conum"]),
                ("brm_type", "=", self.ctyp),
                ("brm_code", "=", w),
                ("brr_cono=brm_cono",),
                ("brr_type=brm_type",),
                ("brr_code=brm_code",),
                ("brr_date", "<=", self.arrive)],
            order="brr_date desc", limit=1)
        if not racc:
            return "Invalid Rate Code"
        self.crtc = w
        self.crdesc = racc[0]
        self.crbase = racc[1]
        self.cnrate = racc[2]
        self.cg.loadEntry(frt, pag, p + 1, data=self.crdesc)
        self.cg.loadEntry(frt, pag, p + 2, data=self.cnrate)

    def doChgPpl(self, frt, pag, r, c, p, i, w):
        self.cppl = w

    def doChgPer(self, frt, pag, r, c, p, i, w):
        self.cper = w

    def doChgDsc(self, frt, pag, r, c, p, i, w):
        self.cdis = w
        if self.cdis:
            rte = int(self.cnrate * (100 - self.cdis) / 100)
            dif = rte % 5
            if dif:
                rte = rte + (5 - dif)
            self.cg.loadEntry(frt, pag, p + 1, data=rte)

    def doChgRte(self, frt, pag, r, c, p, i, w):
        self.carate = w

    def doChgDel(self):
        self.sql.delRec("bkmrtt", where=[("brt_cono", "=", self.opts["conum"]),
            ("brt_seq", "=", self.cseq)])
        self.doChgExit()

    def doChgEnd(self):
        self.sql.updRec("bkmrtt", cols=["brt_rcode", "brt_rdesc", "brt_rbase",
            "brt_nrate", "brt_quant", "brt_bdays", "brt_discp", "brt_arate"],
            data=[self.crtc, self.crdesc, self.crbase, self.cnrate, self.cppl,
            self.cper, self.cdis, self.carate], where=[("brt_seq", "=",
            self.cseq)])
        self.doChgExit()

    def doChgExit(self):
        self.cg.closeProcess()

    def getUnits(self):
        data = []
        for unit in self.aunits:
            typ, cod = unit.split("-")
            des = self.aunits[unit]["desc"]
            qty = self.aunits[unit]["qty"]
            bkt = self.sql.getRec("bkmrtt", cols=["sum(brt_quant)"],
                where=[("brt_cono", "=", self.opts["conum"]), ("brt_number",
                "=", self.number), ("brt_utype", "=", typ), ("brt_ucode", "=",
                cod)], limit=1)
            if not bkt or not bkt[0]:
                bkt = [0]
            data.append([unit, des, CCD(qty, "UI", 3).disp,
                CCD(bkt[0], "UI", 3).disp])
        data.sort()
        opts = {
            "stype": "C",
            "titl": "Select the Required Unit",
            "head": ("Unit-Cod", "Description", "Qty", "Bkd"),
            "data": data}
        rs = self.rt.selectItem(self.rt.pag, opts)
        return rs

    def getRooms(self):
        def getNum(num):
            w1 = {
                0: '', 1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
                6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
                11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen',
                15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen',
                19: 'Nineteen'}
            w2 = [
                None, None, 'Twenty', 'Thirty', 'Forty',
                'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
            if (num >= 0) and (num < 20):
                mess = (w1[num])
            elif (num > 19) and (num < 100):
                mess = (w2[int(num / 10)]) + " " + (w1[num % 10])
            elif (num > 99) and (num < 1000):
                mess = (w1[int(num / 100)]) + " Hundred and " + \
                    (w2[int((num - 100) / 10)]) + " " + (w1[num % 10])
            return mess

        data = []
        for room in self.aunits[self.ucod]["rms"]:
            if room:
                data.append((room, "Room Number %s" % getNum(room)))
        data.sort()
        opts = {
            "stype": "C",
            "titl": "Select the Required Room",
            "head": ("Num", "Description"),
            "data": data}
        rs = self.rt.selectItem(self.rt.pag, opts)
        return rs

    def doUUnit(self, frt, pag, r, c, p, i, w):
        if "-" not in w:
            return "Invalid Unit Code Combination"
        tp, cd = w.split("-")
        rec = self.sql.getRec("bkmunm", cols=["bum_desc", "bum_maxg",
            "bum_dflt"], where=[("bum_cono", "=", self.opts["conum"]),
            ("bum_btyp", "=", tp), ("bum_code", "=", cd)], limit=1)
        if not rec:
            return "Invalid Unit Code"
        if w not in self.aunits:
            return "Unit Not Available"
        self.ucod = w
        self.udes = rec[0]
        self.uqty = rec[1]
        self.dflt = rec[2]
        self.rt.loadEntry(frt, pag, p + 1, data=self.udes)
        self.rt.loadEntry(frt, pag, p + 3, data=self.dflt)
        self.rt1["where"] = [
            ("brm_cono", "=", self.opts["conum"]),
            ("brm_type", "=", tp), ("brr_cono=brm_cono",),
            ("brr_type=brm_type",), ("brr_code=brm_code",)]
        if tp == "A":
            return "sk1"

    def doUDesc(self, frt, pag, r, c, p, i, w):
        self.udes = w
        self.urme = 0
        self.rt.loadEntry(frt, pag, p + 1, data=self.urme)
        return "sk1"

    def doURme(self, frt, pag, r, c, p, i, w):
        if self.aunits[self.ucod]["rms"] != 999:
            if not w:
                for room in self.aunits[self.ucod]["rms"]:
                    if not self.aunits[self.ucod]["rms"][room]:
                        return "Unit Partly Booked"
            else:
                if w not in self.aunits[self.ucod]["rms"]:
                    return "Invalid Room"
                if not self.aunits[self.ucod]["rms"][w]:
                    return "Room Already Booked"
        self.urme = w

    def doURate(self, frt, pag, r, c, p, i, w):
        # New bkmrtt Record
        racc = self.sql.getRec(tables=["bkmrtm", "bkmrtr"],
            cols=["brm_desc", "brm_base", "brr_rate"],
            where=[
                ("brm_cono", "=", self.opts["conum"]),
                ("brm_type", "=", self.ucod[0]),
                ("brm_code", "=", w),
                ("brr_cono=brm_cono",),
                ("brr_type=brm_type",),
                ("brr_code=brm_code",),
                ("brr_date", "<=", self.arrive)],
            order="brr_date desc", limit=1)
        if not racc:
            return "Invalid Rate Code"
        self.rcode = w
        self.rdesc = racc[0]
        self.rbase = racc[1]
        self.nrate = racc[2]
        self.rt.loadEntry(frt, pag, p + 1, data=self.rdesc)
        self.rt.loadEntry(frt, pag, p + 2, data=self.nrate)
        if self.uqty == 999 or self.uqty > self.guests:
            self.rt.loadEntry(frt, pag, p + 3, data=self.guests)
        else:
            self.rt.loadEntry(frt, pag, p + 3, data=self.uqty)
        self.rt.loadEntry(frt, pag, p + 4, data=self.bdays)
        return "sk2"

    def doUPpl(self, frt, pag, r, c, p, i, w):
        if self.uqty and w > self.uqty:
            ok = askQuestion(self.opts["mf"].window, "Quantity",
                "Quantity Exceeds Unit Quantity", default="no")
            if ok == "no":
                return "rf"
        if w > self.guests:
            return "Invalid Quantity, Exceeds Booking Quantity"
        self.rqty = w

    def doUPer(self, frt, pag, r, c, p, i, w):
        if w > self.bdays:
            return "Invalid Period, Exceeds Booking Period"
        self.rper = w

    def doUDisc(self, frt, pag, r, c, p, i, w):
        self.rdisc = w
        if self.rdisc:
            self.arate = int(self.nrate * (100 - self.rdisc) / 100)
            dif = self.arate % 5
            if dif:
                self.arate = self.arate + (5 - dif)
        else:
            self.arate = self.nrate
        self.rt.loadEntry(frt, pag, p + 1, data=self.arate)

    def doUAmount(self, frt, pag, r, c, p, i, w):
        self.arate = w

    def doUEnd(self):
        tp, cd = self.ucod.split("-")
        self.sql.insRec("bkmrtt", data=[self.opts["conum"], self.number,
            tp, cd, self.udes, self.urme, self.rcode, self.rdesc,
            self.rbase, self.nrate, self.rqty, self.rdisc, self.arate,
            self.rper, 0, 0, 0, 0, 0, self.opts["capnm"], self.sysdtw, 0])
        self.rt.advanceLine(0)

    def doLoadUnits(self):
        self.rt.clearFrame("C", 0)
        self.rt.loadEntry("T", 0, 0, data=self.guests)
        recs = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number)],
            order="brt_utype, brt_ucode")
        if not recs:
            self.rt.focusField("C", 0, 1)
            return
        for num, rec in enumerate(recs):
            pos = num * 10
            ut = rec[self.sql.bkmrtt_col.index("brt_utype")]
            uc = rec[self.sql.bkmrtt_col.index("brt_ucode")]
            cc = "%s-%s" % (ut, uc)
            ud = rec[self.sql.bkmrtt_col.index("brt_udesc")]
            rm = rec[self.sql.bkmrtt_col.index("brt_uroom")]
            rc = rec[self.sql.bkmrtt_col.index("brt_rcode")]
            rd = rec[self.sql.bkmrtt_col.index("brt_rdesc")]
            nr = rec[self.sql.bkmrtt_col.index("brt_nrate")]
            qt = rec[self.sql.bkmrtt_col.index("brt_quant")]
            dy = rec[self.sql.bkmrtt_col.index("brt_bdays")]
            ds = rec[self.sql.bkmrtt_col.index("brt_discp")]
            ar = rec[self.sql.bkmrtt_col.index("brt_arate")]
            self.rt.loadEntry("C", 0, pos, data=cc)
            self.rt.loadEntry("C", 0, pos + 1, data=ud)
            self.rt.loadEntry("C", 0, pos+2, data=rm)
            self.rt.loadEntry("C", 0, pos+3, data=rc)
            self.rt.loadEntry("C", 0, pos+4, data=rd)
            self.rt.loadEntry("C", 0, pos+5, data=nr)
            self.rt.loadEntry("C", 0, pos+6, data=qt)
            self.rt.loadEntry("C", 0, pos+7, data=dy)
            self.rt.loadEntry("C", 0, pos+8, data=ds)
            self.rt.loadEntry("C", 0, pos+9, data=ar)
            if num == self.rt.rows[0] - 1:
                self.rt.scrollScreen(0)
            else:
                col = ((num + 1) * 10) + 1
                self.rt.focusField("C", 0, col)

    def doUExit(self):
        err = self.doCheckUnits()
        if err:
            self.rt.focusField(self.rt.frt, self.rt.pag, self.rt.col, err=err)
            return
        self.rt.closeProcess()
        recs = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number)],
            order="brt_utype, brt_ucode")
        self.units = ""
        for num, rec in enumerate(recs):
            ut = rec[self.sql.bkmrtt_col.index("brt_utype")]
            uc = rec[self.sql.bkmrtt_col.index("brt_ucode")]
            uc = "%s-%s" % (ut, uc)
            if not self.units:
                self.units = uc
            else:
                self.units = "%s:%s" % (self.units, uc)
        self.df.loadEntry("T", 1, 7, data=self.units)

    def doUQuit(self):
        self.rt.closeProcess()

    def doCheckUnits(self):
        if self.btype != "A":
            return
        cols = self.sql.bkmrtt_col
        recs = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number)])
        if not recs:
            return "No Units Selected"
        quant = 0
        for rec in recs:
            if rec[cols.index("brt_utype")] == "A":
                qty = rec[cols.index("brt_quant")]
                per = rec[cols.index("brt_bdays")]
                quant += (qty * per)
        if not quant:
            return "Missing Accomodation Unit"
        if quant > (self.guests * self.bdays):
            return "Accomodation Quantity Exceeds Booking Quantity"
        if quant < (self.guests * self.bdays):
            ok = askQuestion(self.opts["mf"].window, "Quantity",
                "Accommodation Quantity is Less than the Booked Quantity?",
                default="no")
            if ok == "no":
                return "rf"

    def getBookingValue(self):
        self.value = 0
        col = self.sql.bkmrtt_col
        recs = self.sql.getRec("bkmrtt", where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number)])
        for rec in recs:
            bas = rec[col.index("brt_rbase")]
            qty = rec[col.index("brt_quant")]
            per = rec[col.index("brt_bdays")]
            rte = rec[col.index("brt_arate")]
            if bas == "A":
                self.value = float(ASD(self.value) + ASD(qty * per * rte))
            elif bas == "B":
                self.value = float(ASD(self.value) + ASD(qty * rte))
            elif bas == "C":
                self.value = float(ASD(self.value) + ASD(per * rte))
            else:
                self.value = float(ASD(self.value) + ASD(rte))

    def doDeposit(self, frt, pag, r, c, p, i, w):
        if p == 9:
            self.stddep = w
            if not self.stddep:
                self.stddte = 0
                self.grpdep = 0
                self.grpdte = 0
                self.df.loadEntry(frt, pag, p + 1, data=self.stddte)
                self.df.loadEntry(frt, pag, p + 2, data=self.grpdep)
                self.df.loadEntry(frt, pag, p + 3, data=self.grpdte)
                return "sk3"
        else:
            self.grpdep = w
            if not self.grpdep:
                self.grpdte = 0
                self.df.loadEntry(frt, pag, p + 1, data=self.grpdte)
                return "sk1"

    def doDepdate(self, frt, pag, r, c, p, i, w):
        if p == 10:
            self.stddte = w
        else:
            self.grpdte = w

    def doRemarks(self, frt, pag, r, c, p, i, w):
        lines = len(self.units.split(":"))
        lines += len(textFormat(w, width=60, blong=False))
        if lines > 24:
            self.df.loadEntry(frt, pag, p, data=w)
            return "Remarks Too Long, Please Shorten"
        self.remarks = w

    def doContact(self, frt, pag, r, c, p, i, w):
        if w:
            self.oldcon = self.sql.getRec("bkmcon", where=[("bkc_cono",
                "=", self.opts["conum"]), ("bkc_ccode", "=", w)], limit=1)
            if not self.oldcon:
                return "Invalid Contact Code"
            self.newcon = False
            self.title = self.oldcon[self.sql.bkmcon_col.index("bkc_title")]
            self.sname = self.oldcon[self.sql.bkmcon_col.index("bkc_sname")]
            self.names = self.oldcon[self.sql.bkmcon_col.index("bkc_names")]
            self.email = self.oldcon[self.sql.bkmcon_col.index("bkc_email")]
            for num, dat in enumerate(self.oldcon[1:-1]):
                self.df.loadEntry("T", 2, num, data=dat)
        else:
            self.newcon = True
        self.ccode = w

    def doTitle(self, frt, pag, r, c, p, i, w):
        self.title = w

    def doSurname(self, frt, pag, r, c, p, i, w):
        self.sname = w

    def doNames(self, frt, pag, r, c, p, i, w):
        self.names = w
        if self.newcon:
            chk = self.sql.getRec("bkmcon", where=[("bkc_cono", "=",
                self.opts["conum"]), ("bkc_sname", "=", self.sname),
                ("bkc_names", "=", self.names)], limit=1)
            if chk:
                return "A Contact with this Surname and Name Already Exists"

    def doEmail(self, frt, pag, r, c, p, i, w):
        self.email = w

    def doEnd(self):
        if self.df.pag == 1:
            if self.newmst or self.edit:
                self.df.selPage("Contact", focus=False)
                self.df.focusField("T", 2, 1)
            else:
                self.opts["mf"].updateStatus("Select Button or Tag to Continue")
        elif self.df.pag == 2:
            self.ender = True
            self.opts["mf"].updateStatus("Select Button or Tag to Continue")

    def doUpdate(self):
        if self.newcon:
            for seq in range(1, 100):
                self.ccode = genAccNum(self.sname, seq)
                chk = self.sql.getRec("bkmcon", where=[("bkc_cono",
                    "=", self.opts["conum"]), ("bkc_ccode", "=", self.ccode)],
                    limit=1)
                if not chk:
                    break
            self.df.loadEntry("T", 2, 0, data=self.ccode)
        changed = False
        condat = [self.opts["conum"]]
        trdt = int("%04i%02i%02i%02i%02i%02i" % time.localtime()[:-3])
        for x in range(len(self.df.t_work[2][0])):
            condat.append(self.df.t_work[2][0][x])
        if self.newcon:
            changed = True
            self.sql.insRec("bkmcon", data=condat)
            self.newcon = False
        elif condat != self.oldcon[:len(condat)]:
            changed = True
            col = self.sql.bkmcon_col
            condat.append(self.oldcon[col.index("bkc_xflag")])
            self.sql.updRec("bkmcon", data=condat, where=[("bkc_cono", "=",
                self.opts["conum"]), ("bkc_ccode", "=", self.ccode)])
            for num, dat in enumerate(self.oldcon):
                if dat != condat[num]:
                    self.sql.insRec("chglog", data=["bkmcon", "U",
                        "%03i%-7s" % (self.opts["conum"], self.ccode),
                        col[num], trdt, self.opts["capnm"], str(dat),
                        str(condat[num]), "", 0])
        mstdat = [self.opts["conum"]]
        for x in range(len(self.df.t_work[1][0])):
            if x in (6, 13):
                continue
            if self.df.topf[1][x][1][1:] == "Tv":
                mstdat.append(self.df.t_work[1][0][x].strip())
            else:
                mstdat.append(self.df.t_work[1][0][x])
        mstdat.append(self.ccode)
        if self.newmst:
            changed = True
            acc = self.sql.getRec("bkmmst", cols=["max(bkm_number)"],
                where=[("bkm_cono", "=", self.opts["conum"])], limit=1)
            if not acc[0]:
                self.number = 1001
            else:
                self.number = int(acc[0]) + 1
            mstdat[1] = self.number
            self.sql.insRec("bkmmst", data=mstdat)
            self.sql.updRec("bkmrtt", cols=["brt_number"], data=[self.number],
                where=[("brt_cono", "=", self.opts["conum"]), ("brt_number",
                "=", 0)])
            self.sql.insRec("bkmtrn", data=[self.opts["conum"], self.number, 1,
                self.getRef(), self.batno, self.sysdtw, 0, 0, self.curdt,
                "Booking Enquiry", "", "", self.opts["capnm"], self.sysdtw, 0])
            self.df.loadEntry("T", 1, 0, data=self.number)
        elif mstdat != self.oldmst[:len(mstdat)]:
            changed = True
            col = self.sql.bkmmst_col
            mstdat.append(self.oldmst[col.index("bkm_xflag")])
            self.sql.updRec("bkmmst", data=mstdat, where=[("bkm_cono", "=",
                self.opts["conum"]), ("bkm_number", "=", self.number)])
            for num, dat in enumerate(self.oldmst):
                if dat != mstdat[num]:
                    self.sql.insRec("chglog", data=["bkmmst", "U",
                        "%03i%7s" % (self.opts["conum"], self.number),
                        col[num], trdt, self.opts["capnm"], str(dat),
                        str(mstdat[num]), "", 0])
        self.opts["mf"].dbm.commitDbase()
        if self.rev:
            self.df.setWidget(self.df.mstFrame, state="hide")
            PrintBookingInvoice(self.opts["mf"], self.opts["conum"],
                self.opts["conam"], "C", [self.crnno], tname=self.ivtpl,
                repprt=["N", "P", "Default"])
            self.df.setWidget(self.df.mstFrame, state="show")
        return changed

    def doAccept(self):
        self.df.setWidget(self.df.B4, "disabled")
        if not self.number and self.df.pag == 1:
            err = "Booking Not Yet Complete"
            self.df.focusField(self.df.frt, self.df.pag, self.df.col, err=err)
            return
        err = self.doCheckUnits()
        if err:
            self.df.focusField("T", 1, 7, err=err)
            return
        f, p, c, m = self.df.doCheckFields(fields=["T", 1, None])
        if m:
            self.df.selPage("Booking")
            self.df.focusField(f, p, (c + 1), err=m)
            return
        if not self.df.t_work[2][0][1]:
            self.df.selPage("Contact")
            self.df.focusField("T", 2, 1, err="Missing Contact")
            return
        f, p, c, m = self.df.doCheckFields(("T", 2, None))
        if m:
            self.df.selPage("Contact")
            self.df.focusField(f, p, (c + 1), err=m)
            return
        # Update Tables
        bal = self.getBalance().work
        self.setStatus(bal)
        changed = self.doUpdate()
        if changed:
            dflt = "yes"
        else:
            dflt = "no"
        # Print/Email Booking
        ok = askQuestion(self.opts["mf"].window, "Notify",
            "Print/Email Booking", default=dflt)
        if ok == "yes":
            self.doPrint()
        if "args" in self.opts:
            # Exit
            self.doExit()
        else:
            # Loop for Next Booking
            self.number = 0
            self.df.selPage("Booking")
            self.df.focusField("T", 1, 1)

    def getRef(self):
        rec = self.sql.getRec("bkmtrn", cols=["max(bkt_refno)"],
            where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
            "=", self.number), ("bkt_refno", "like", "%7s%s" % (self.number,
            "%"))], limit=1)
        if not rec or not rec[0]:
            num = 1
        else:
            num = (int(rec[0]) % 100) + 1
        return "%7s%02i" % (self.number, num)

    def doTrans(self):
        if not self.number:
            return
        tit = "Transaction Data Capture"
        if self.glint:
            glm = {
                "stype": "R",
                "tables": ("genmst",),
                "cols": (
                    ("glm_acno", "", 0, "Acc-Num"),
                    ("glm_desc", "", 0, "Description")),
                "where": [
                    ("glm_cono", "=", self.opts["conum"])],
                "order": "glm_desc"}
        r1s = (
            ("Receipt","1"),
            ("Refund","2"),
            ("Journal","3"),
            ("Cancel","4"),
            ("Reinstate","5"))
        r2s = (
            ("EFT","1"),
            ("Cash","2"),
            ("Cheque","3"))
        fld = [
            (("T",0,0,0),"OSD",13.2,"S-Deposit"),
            (("T",0,0,0),"OSD",13.2,"G-Deposit"),
            (("T",0,0,0),"OSD",13.2,"Balance"),
            (("T",0,1,0),("IRB",r1s),0,"Type","",
                "1","Y",self.doTType,None,None,None),
            (("T",0,2,0),("IRB",r2s),0,"Method","",
                "1","Y",self.doTMethod,None,None,None),
            (("T",0,3,0),"ID1",10,"Date","",
                self.sysdtw,"N",self.doTDate,None,None,("efld",)),
            (("T",0,4,0),"ONa",9,"Reference"),
            (("T",0,5,0),"ISD",13.2,"Amount","",
                0,"N",self.doTAmount,None,None,("notzero",)),
            (("T",0,6,0),"ITX",30,"Details","",
                "","N",self.doTDesc,None,None,None)]
        if self.glint:
            fld.extend([
                (("T",0,7,0),"IUI",7,"G/L-Acc","G/L Account Number",
                    0,"N",self.doTGacc,glm,None,None),
                (("T",0,7,0),"ONA",30,"")])
            idx = 8
        else:
            idx = 7
        fld.extend([
            (("T",0,idx,0),"IUA",1,"VAT Code","",
                0,"N",self.doTVcod,None,None,None),
            (("T",0,idx+1,0),"ISD",13.2,"VAT Amount","",
                0,"N",self.doTVamt,None,None,("efld",))])
        state = self.df.disableButtonsTags()
        widget = self.df.getWidget(self.df.frt, self.df.pag, self.df.pos)
        self.df.setWidget(widget, "disabled")
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.tr = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, tend=((self.doTEnd,"y"),), txit=(self.doTExit,))
        if self.state == "Q":
            self.tr.loadEntry("T", 0, 0, data=self.stddep)
            self.tr.loadEntry("T", 0, 1, data=self.grpdep)
            self.tr.loadEntry("T", 0, 2, data=self.value)
        else:
            self.tr.loadEntry("T", 0, 0, data=0)
            self.tr.loadEntry("T", 0, 2, data=self.getBalance().work)
        self.tr.focusField("T", 0, 3)
        self.tr.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doTType(self, frt, pag, r, c, p, i, w):
        self.ttype = int(w)
        self.tdte = self.sysdtw
        self.tcur = self.curdt
        if self.ttype == 3:                             # Journal
            return "sk1"
        if self.ttype == 4:                             # Cancellation
            if self.state == "X":
                return "Already Cancelled"
            self.fee = False
            self.rev = False
            if self.state == "Q":
                return "nd"
            trn = self.sql.getRec("bkmtrn", cols=["count(*)"],
                where=[("bkt_cono", "=", self.opts["conum"]),
                ("bkt_number", "=", self.number),
                ("bkt_type", "<>", 1)], limit=1)
            if trn[0]:
                ok = askQuestion(self.opts["mf"].body, "Transact",
                    "Transactions Exist for this Booking, Are you Sure "\
                    "that it must be Cancelled and that All Invoices "\
                    "be Reversed?", default="no")
                if ok == "yes":
                    self.rev = True
            else:
                ok = askQuestion(self.opts["mf"].body, "Status",
                    "This is a Confirmed Booking, Are you Sure "\
                    "that it must be Cancelled?", default="no")
            if ok == "no":
                return "Not Cancelled"
            ok = askQuestion(self.opts["mf"].body, "Charges",
                "Do You want to enter a Cancellation Charge?",
                default="no")
            if ok == "yes":
                self.fee = True
                self.tref = self.getRef()
                self.tr.loadEntry(frt, pag, p + 2, data=self.tdte)
                self.tr.loadEntry(frt, pag, p + 3, data=self.tref)
                return "sk3"
            else:
                return "nd"
        if self.ttype == 5:                             # Re-instate
            if self.state == "X":
                return "nd"
            else:
                return "Can Only Re-instate a Cancelled Booking"

    def doTMethod(self, frt, pag, r, c, p, i, w):
        self.mtype = w

    def doTDate(self, frt, pag, r, c, p, i, w):
        self.tdte = w
        self.tcur = int(w / 100)
        self.tref = self.getRef()
        self.tr.loadEntry(frt, pag, p + 1, data=self.tref)

    def doTRef(self, frt, pag, r, c, p, i, w):
        self.tref = w

    def doTAmount(self, frt, pag, r, c, p, i, w):
        if self.ttype == 2:                             # Refund
            chk = float(ASD(0) - ASD(w))
        else:
            chk = w
        ok = "yes"
        if self.ttype == 3:                             # Journal
            pass
        elif self.state == "Q":
            if self.ttype == 1 and w < self.stddep:     # Receipt
                ok = askQuestion(self.opts["mf"].window, "Deposit",
                    "This Amount is Less than the Deposit Amount, Confirm?")
            elif chk > self.value:
                ok = askQuestion(self.opts["mf"].window, "Value",
                    "This Amount Exceeds the Total Value, Confirm?")
        elif self.ttype == 4:                           # Cancellation
            chk = self.getBalance().work + w
            if chk > 0:
                ok = askQuestion(self.opts["mf"].window, "Balance",
                    "This Amount is More than the Balance, Confirm?")
        elif self.state == "C" and chk > self.getBalance().work:
            ok = askQuestion(self.opts["mf"].window, "Balance",
                "This Amount is More than the Balance, Confirm?")
        if ok == "no":
            return "Invalid Amount"
        self.tamount = w
        if self.ttype == 4:                             # Cancellation
            self.tr.loadEntry(frt, pag, p + 1, data="Cancellation Charge")

    def doTDesc(self, frt, pag, r, c, p, i, w):
        self.tdesc = w
        if self.ttype == 4 and self.glint == "Y":       # Cancellation
            self.tglac = self.ccgctl
            self.tvcod = self.taxdf
            vrte = getVatRate(self.sql, self.opts["conum"], self.tvcod,
                self.tdte)
            self.tvamt = round(self.tamount * vrte / (100 + vrte), 2)
            return "nd"
        elif self.ttype in (1, 2, 5):                   # Rec or Ref or Reins
            return "nd"

    def doTGacc(self, frt, pag, r, c, p, i, w):
        chk = chkGenAcc(self.opts["mf"], self.opts["conum"], w)
        if type(chk) is str:
            return chk
        self.tglac = w
        self.tvcod = chk[2]
        self.tr.loadEntry(frt, pag, p + 1, data=chk[0])
        self.tr.loadEntry(frt, pag, p + 2, data=chk[2])

    def doTVcod(self, frt, pag, r, c, p, i, w):
        rec = self.sql.getRec("ctlvmf", where=[("vtm_cono", "=",
            self.opts["conum"]), ("vtm_code", "=", w)], limit=1)
        if not rec:
            return "Invalid VAT Code"
        self.tvcod = w
        vrte = getVatRate(self.sql, self.opts["conum"], w, self.tdte)
        self.tvamt = round(self.tamount * vrte / (100 + vrte), 2)
        self.tr.loadEntry(frt, pag, p + 1, self.tvamt)

    def doTVamt(self, frt, pag, r, c, p, i, w):
        self.tvamt = w

    def doTEnd(self):
        self.trans = True
        if self.ttype in (4, 5):                        # Cancel or Re-instate
            if self.ttype == 4:                         # Cancellation
                desc = "Cancellation"
                amt = 0
                self.state = "X"
            else:
                desc = "Re-Instatement"
                amt = 0
                self.state = "Q"
            self.sql.insRec("bkmtrn", data=[self.opts["conum"], self.number,
                1, self.getRef(), self.batno, self.tdte, amt, 0, self.tcur,
                desc, "", "", self.opts["capnm"], self.sysdtw, 0])
            self.sql.updRec("bkmmst", cols=["bkm_state"], data=[self.state],
                where=[("bkm_cono", "=", self.opts["conum"]), ("bkm_number",
                "=", self.number)])
            if (self.ttype == 4 and not self.fee and not self.rev) \
                    or self.ttype == 5:
                self.df.loadEntry("T", 1, 13, data=self.getBalance().work)
                self.df.loadEntry("T", 1, 15, data=self.state)
                self.doTExit()
                return
        if self.ttype == 1:                             # Receipt
            ttype = 3
        elif self.ttype == 4:                           # Cancellation
            ttype = 5
        else:
            ttype = self.ttype + 2
        if self.ttype == 1:                             # Receipt
            tramt = float(ASD(0) - ASD(self.tamount))
            vatind = ""
            vatamt = 0
        elif self.ttype == 2:                           # Refund
            tramt = self.tamount
            vatind = ""
            vatamt = 0
        elif self.ttype == 4 and self.fee:              # Cancellation
            tramt = self.tamount
            vatind = self.tvcod
            vrte = getVatRate(self.sql, self.opts["conum"], vatind, self.tdte)
            vatamt = round(tramt * vrte / (100 + vrte), 2)
            excamt = float(ASD(tramt) - ASD(vatamt))
        elif self.ttype != 4:
            tramt = self.tamount
            vatind = self.tvcod
            vatamt = self.tvamt
            excamt = float(ASD(tramt) - ASD(vatamt))
        if self.ttype != 4 or self.fee:
            # Main Transaction
            data = [self.opts["conum"], self.number, ttype, self.tref,
                self.batno, self.tdte, tramt, vatamt, self.tcur, self.tdesc,
                vatind, "", self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("bkmtrn", data=data)
            if self.glint == "Y":
                if self.ttype == 1:                     # Receipt
                    gltyp = 6
                elif self.ttype == 2:                   # Refund
                    gltyp = 2
                else:
                    gltyp = 4
                data = [self.opts["conum"], self.bkmctl, self.tcur, self.tdte,
                    gltyp, self.tref, self.batno, tramt, 0, self.tdesc,
                    "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                tramt = float(ASD(0) - ASD(tramt))
                vatamt = float(ASD(0) - ASD(vatamt))
                excamt = float(ASD(tramt) - ASD(vatamt))
                if self.ttype in (1, 2):                # Receipt or Refund
                    if self.mtype == "1":
                        ctl = self.bnkctl
                    elif self.mtype == "2":
                        ctl = self.cshctl
                    else:
                        ctl = self.chqctl
                    data = [self.opts["conum"], ctl, self.tcur, self.tdte,
                        gltyp, self.tref, self.batno, tramt, 0, self.tdesc,
                        "", "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                else:
                    data = [self.opts["conum"], self.tglac, self.tcur,
                        self.tdte, gltyp, self.tref, self.batno, excamt,
                        vatamt, self.tdesc, "", "", 0, self.opts["capnm"],
                        self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)
                    if vatamt:
                        data = [self.opts["conum"], self.vatctl, self.tcur,
                            self.tdte, gltyp, self.tref, self.batno, vatamt,
                            0, self.tdesc, "", "", 0, self.opts["capnm"],
                            self.sysdtw, 0]
                        self.sql.insRec("gentrn", data=data)
            if self.ttype == 3:                         # Journal
                # VAT Transaction
                data = [self.opts["conum"], vatind, "O", self.tcur, "B",
                    ttype, self.batno, self.tref, self.tdte, self.number,
                    self.tdesc, excamt, vatamt, 0, self.opts["capnm"],
                    self.sysdtw, 0]
                self.sql.insRec("ctlvtf", data=data)
        if self.ttype == 4 and self.rev:
            recs = self.sql.getRec("bkmrtt", where=[("brt_cono",
                "=", self.opts["conum"]), ("brt_number", "=", self.number),
                ("brt_invno", "<>", 0), ("brt_crnno", "=", 0)])
            if recs:
                self.doCreditNote(recs)
        # Balance
        bal = self.getBalance().work
        self.df.loadEntry("T", 1, 13, data=bal)
        # Status
        self.setStatus(bal)
        self.sql.updRec("bkmmst", cols=["bkm_state"], data=[self.state],
            where=[("bkm_cono", "=", self.opts["conum"]), ("bkm_number",
            "=", self.number)])
        self.doTExit()

    def doCreditNote(self, recs):
        # Raise Credit Note
        incamt = 0
        vatamt = 0
        vdic = {}
        gdic = {}
        self.crnno = self.getRef()
        for rec in recs:
            utyp = rec[self.sql.bkmrtt_col.index("brt_utype")]
            ucod = rec[self.sql.bkmrtt_col.index("brt_ucode")]
            rbas = rec[self.sql.bkmrtt_col.index("brt_rbase")]
            quan = rec[self.sql.bkmrtt_col.index("brt_quant")]
            rate = rec[self.sql.bkmrtt_col.index("brt_arate")]
            rate = float(ASD(0) - ASD(rate))
            days = rec[self.sql.bkmrtt_col.index("brt_bdays")]
            vrte = rec[self.sql.bkmrtt_col.index("brt_vrate")]
            invn = rec[self.sql.bkmrtt_col.index("brt_invno")]
            invd = rec[self.sql.bkmrtt_col.index("brt_invdt")]
            curd = int(invd / 100)
            umst = self.sql.getRec("bkmunm", where=[("bum_cono",
                "=", self.opts["conum"]), ("bum_btyp", "=", utyp),
                ("bum_code", "=", ucod)], limit=1)
            vatc = umst[self.sql.bkmunm_col.index("bum_vatc")]
            if not vatc:
                vatc = self.taxdf
            if rbas == "A":
                inca = quan * days * rate
            elif rbas == "B":
                inca = quan * rate
            elif rbas == "C":
                inca = days * rate
            else:
                inca = rate
            vata = round(inca * vrte / (100 + vrte), 2)
            exca = float(ASD(inca) - ASD(vata))
            incamt = float(ASD(incamt) + ASD(inca))
            vatamt = float(ASD(vatamt) - ASD(vata))
            if vata:
                if vatc not in vdic:
                    vdic[vatc] = [0, 0]
                vdic[vatc][0] = float(ASD(vdic[vatc][0]) + ASD(exca))
                vdic[vatc][1] = float(ASD(vdic[vatc][1]) + ASD(vata))
            if self.glint == "Y":
                slsa = umst[self.sql.bkmunm_col.index("bum_slsa")]
                if slsa not in gdic:
                    gdic[slsa] = [0, 0, vatc]
                gdic[slsa][0] = float(ASD(gdic[slsa][0]) - ASD(exca))
                gdic[slsa][1] = float(ASD(gdic[slsa][1]) - ASD(vata))
            desc = "Booking %s-%s Cancelled" % (utyp, ucod)
            data = [self.opts["conum"], self.number, 6, self.crnno, self.batno,
                invd, inca, vata, curd, desc, vatc, "", self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("bkmtrn", data=data)
        self.sql.updRec("bkmrtt", cols=["brt_crnno", "brt_crndt"],
            data=[self.crnno, invd], where=[("brt_cono", "=",
            self.opts["conum"]), ("brt_number", "=", self.number),
            ("brt_invno", "=", invn)])
        desc = "Booking %s Cancelled" % self.number
        for cod in vdic:
            exc = float(ASD(0) - ASD(vdic[cod][0]))
            vat = float(ASD(0) - ASD(vdic[cod][1]))
            data = [self.opts["conum"], vatc, "O", curd, "B", 1, self.batno,
                self.crnno, invd, self.number, desc, exc, vat, 0,
                self.opts["capnm"], self.sysdtw, 0]
            self.sql.insRec("ctlvtf", data=data)
        if self.glint == "Y":
            data = [self.opts["conum"], self.bkmctl, curd, invd, 1, self.crnno,
                self.batno, incamt, 0, desc, "", "", 0, self.opts["capnm"],
                self.sysdtw, 0]
            self.sql.insRec("gentrn", data=data)
            for acc in gdic:
                data = [self.opts["conum"], acc, curd, invd, 1, self.crnno,
                    self.batno, gdic[acc][0], gdic[acc][1], desc, gdic[acc][2],
                    "", 0, self.opts["capnm"], self.sysdtw, 0]
                self.sql.insRec("gentrn", data=data)
                if gdic[acc][1]:
                    data = [self.opts["conum"], self.vatctl, curd, invd, 1,
                        self.crnno, self.batno, gdic[acc][1], 0, desc, "",
                        "", 0, self.opts["capnm"], self.sysdtw, 0]
                    self.sql.insRec("gentrn", data=data)

    def doTExit(self):
        self.tr.closeProcess()

    def doMoves(self):
        if not self.number or self.edit:
            return
        whr = [
            ("bkt_cono", "=", self.opts["conum"]),
            ("bkt_number", "=", self.number)]
        col = self.sql.bkmtrn_col
        recs = self.sql.getRec("bkmtrn", where=whr, order="bkt_seq")
        if recs:
            data = []
            for dat in recs:
                data.append([
                    dat[col.index("bkt_date")],
                    dat[col.index("bkt_curdt")],
                    dat[col.index("bkt_batch")],
                    dat[col.index("bkt_type")],
                    dat[col.index("bkt_refno")],
                    dat[col.index("bkt_tramt")],
                    dat[col.index("bkt_desc")]])
            tit = "Transactions for Booking: %s" % self.number
            col = (
                ("bkt_date", "   Date", 10, "D1", "N"),
                ("bkt_curdt", "Curr-Dt", 7, "D2", "N"),
                ("bkt_batch", "Batch", 7, "Na", "N"),
                ("bkt_type", "Typ", 3, ("XX", bktrtp), "N"),
                ("bkt_refno", "Reference", 9, "Na", "Y"),
                ("bkt_tramt", "    Amount", 13.2, "SD", "N"),
                ("bkt_desc", "Details", 30, "NA", "N"))
            state = self.df.disableButtonsTags()
            self.mprint = False
            while True:
                rec = SelectChoice(self.opts["mf"].window, tit, col,
                    data, butt=[("Print", self.doMPrint)])
                if self.mprint:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    callModule(self.opts["mf"], None, "bk3070",
                        coy=(self.opts["conum"], self.opts["conam"]),
                        args=[self.number])
                    self.df.setWidget(self.df.mstFrame, state="show")
                    break
                if rec.selection:
                    self.df.setWidget(self.df.mstFrame, state="hide")
                    if rec.selection[4] == 2:
                        PrintBookingInvoice(self.opts["mf"],
                            self.opts["conum"], self.opts["conam"], "I",
                            [rec.selection[5]], repprt=["N", "V", "view"],
                            copy="y")
                    else:
                        whr = [
                            ("bkt_cono", "=", self.opts["conum"]),
                            ("bkt_number", "=", self.number),
                            ("bkt_type", "=", rec.selection[4]),
                            ("bkt_refno", "=", rec.selection[5])]
                        TabPrt(self.opts["mf"], tabs="bkmtrn", where=whr,
                            pdia=False)
                    self.df.setWidget(self.df.mstFrame, state="show")
                else:
                    break
            self.df.enableButtonsTags(state=state)

    def doMPrint(self):
        self.mprint = True

    def doNotes(self):
        if not self.number or self.edit:
            return
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        NotesCreate(self.opts["mf"], self.opts["conum"], self.opts["conam"],
            self.opts["capnm"], "BKM", "%07i" % self.number)
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)

    def doPrint(self):
        if not self.number:
            return
        self.tit = "Print/Email Booking"
        fld = []
        view = ("N", "V")
        if self.email:
            mail = ("N", "Y", "N", "E-Mail Booking")
        else:
            mail = None
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.pr = TartanDialog(self.opts["mf"], tops=True, title=self.tit,
            eflds=fld, tend=((self.doPEnd,"n"),), txit=(self.doPExit,),
            view=view, mail=mail)
        self.pr.mstFrame.wait_window()
        self.doPBooking()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.mstFrame.focus_force()

    def doPEnd(self):
        self.pr.closeProcess()

    def doPExit(self):
        self.ptyp = None
        self.doPEnd()

    def doPBooking(self):
        if self.pr.repeml[1] == "Y":
            self.pr.repeml[2] = self.email
        self.form = DrawForm(self.opts["mf"].dbm, self.bktpl,
            wrkdir=self.opts["mf"].rcdic["wrkdir"])
        self.doLoadStatic()
        self.form.doNewDetail()
        self.doBookingDetails()
        self.form.add_page()
        tdc = self.form.sql.tpldet_col
        if self.names:
            nam = self.names.split()
            nam = "%s %s %s" % (self.title, nam[0], self.sname)
        else:
            nam = "%s %s" % (self.title, self.sname)
        error = False
        for key in self.form.newkey:
            ln = self.form.newdic[key]
            if ln[tdc.index("tpd_detseq")] == "booking_letter_C00":
                body = self.sql.getRec("bkmlet", cols=["bkl_body"],
                    where=[("bkl_cono", "=", self.opts["conum"]), ("bkl_code",
                    "=", self.state)], limit=1)
                if not body:
                    showError(self.opts["mf"].window, "Error",
                        "Missing Letter Record for %s" % self.state)
                    error = True
                    break
                ln[tdc.index("tpd_text")] = "Dear %s\n\n%s" % (nam, body[0])
                if self.pr.repeml[1] == "Y":
                    if self.state == "Q":
                        emess = ["Booking Enquiry - %s" % self.number,
                            "Dear %s\n\nAttached please find your booking "\
                            "enquiry" % nam]
                        if self.terms:
                            emess[1] += " as well as a copy of our Terms "\
                                "and Conditions."
                        else:
                            emess[1] += "."
                    elif self.state == "C":
                        emess = ("Booking Enquiry - %s" % self.number,
                            "Dear %s\n\nAttached please find your booking "\
                            "confirmation." % nam)
                    elif self.state == "S":
                        emess = ("Booking Settlement - %s" % self.number,
                            "Dear %s\n\nAttached please find your "\
                            "confirmation of settlement of your booking." % nam)
                    else:
                        emess = ("Booking Cancellation - %s" % self.number,
                            "Dear %s\n\nAttached please find the expiry of "\
                            "your booking enquiry." % nam)
                    self.pr.repeml[3] = emess
            if ln[tdc.index("tpd_detseq")] == 7:
                if self.state in ("Q", "C"):
                    ln[tdc.index("tpd_text")] = "%-20s%60s" % \
                        ("Banking Details:", "(Please use %s as the EFT or "\
                        "Deposit Slip Reference Code)" % self.number)
            self.form.doDrawDetail(ln)
        if not error:
            key = "%s_%s" % (self.opts["conum"], self.number)
            pdfnam = getModName(self.opts["mf"].rcdic["wrkdir"],
                self.__class__.__name__, key, ext="pdf")
            if self.terms:
                att = [getFileName(self.terms,
                    wrkdir=self.opts["mf"].rcdic["wrkdir"])]
            else:
                att = None
            if self.form.saveFile(pdfnam, self.opts["mf"].window):
                doPrinter(mf=self.opts["mf"], conum=self.opts["conum"],
                    pdfnam=pdfnam, header=self.tit, repprt=self.pr.repprt,
                    fromad=self.fromad, repeml=self.pr.repeml, attach=att)

    def doLoadStatic(self):
        cmc = self.sql.ctlmst_col
        ctm = self.sql.getRec("ctlmst", where=[("ctm_cono", "=",
            self.opts["conum"])], limit=1)
        for fld in cmc:
            dat = ctm[cmc.index(fld)]
            if fld in self.form.tptp:
                if fld == "ctm_logo":
                    self.form.letterhead(cmc, ctm, fld, dat)
                    continue
                self.form.tptp[fld][1] = dat
        if "letterhead" in self.form.tptp:
            self.form.letterhead(cmc, ctm, "letterhead", None)
        if "booking_number" in self.form.tptp:
            if self.state == "Q":
                text = "BOOKING ENQUIRY - %s" % self.number
            elif self.state == "C":
                text = "BOOKING CONFIRMATION/RECEIPT - %s" % self.number
            elif self.state == "S":
                text = "BOOKING SETTLEMENT/RECEIPT - %s" % self.number
            elif self.state == "X":
                text = "BOOKING CANCELLATION - %s" % self.number
            self.form.tptp["booking_number"][1] = text
        if "booking_date" in self.form.tptp:
            self.form.tptp["booking_date"][1] = self.getDate(self.sysdtw)
        if "company_name" in self.form.tptp:
            self.form.tptp["company_name"][1] = self.opts["conam"]

    def doBookingDetails(self):
        t = "booking_details"
        if t not in self.form.tptp:
            return
        s = 0
        nd = self.form.newdic
        tc = self.form.sql.tpldet_col
        bd = self.df.t_disp[1][0]
        bw = self.df.t_work[1][0]
        cd = self.df.t_disp[2][0]
        cw = self.df.t_work[2][0]
        if cd[4]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Address:"
            for x in range(3):
                if not cd[x+4]:
                    break
                nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[x+4]
                s += 1
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[7]
            s += 1
        if cw[8]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Phone:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[8]
            s += 1
        if cw[9]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Fax:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[9]
            s += 1
        if cw[10]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Mobile:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[10]
            s += 1
        if cw[11]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Email:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[11]
            s += 1
        if bw[2]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Group Name:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = bd[2]
            s += 1
        if cw[12]:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "V.A.T. Number:"
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = cd[12]
            s += 1
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Date of Arrival:"
        nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = self.getDate(bw[4])
        s += 1
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Date of Departure:"
        nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = self.getDate(bw[5])
        s += 1
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Number of Persons:"
        nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = self.guests
        # Booked facilities
        rtt = self.sql.getRec("bkmrtt", cols=["brt_utype", "brt_ucode",
            "brt_udesc", "brt_uroom", "brt_rbase", "brt_quant", "brt_bdays",
            "brt_arate"], where=[("brt_cono", "=", self.opts["conum"]),
            ("brt_number", "=", self.number)], order="brt_utype, brt_udesc")
        for n, u in enumerate(rtt):
            s += 1
            if not n:
                txt = "Facilities:"
            else:
                txt = ""
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = txt
            if u[0] == "A" and u[3]:
                u[2] = "%-s Room %3s" % (u[2], u[3])
            qty = CCD(u[5], "UI", 3)
            per = CCD(u[6], "UI", 3)
            rte = CCD(u[7], "UD", 10.2)
            if rte.work:
                if u[4] == "A":
                    txt = "%-35s %-3s x %-3s @ R%10s" % (u[2], qty.disp,
                        per.disp, rte.disp)
                elif u[4] == "B":
                    txt = "%-35s %-3s x       R%10s" % (u[2], qty.disp,
                        rte.disp)
                elif u[4] == "C":
                    txt = "%-35s       %-3s @ R%10s" % (u[2], per.disp,
                        rte.disp)
                else:
                    txt = "%-35s           @ R%10s" % (u[2], rte.disp)
            else:
                txt = "%-35s" % u[2]
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = txt
        # Remarks
        if bd[14]:
            s += 1
            lines = textFormat(bd[14], width=60, blong=False)
            for num, line in enumerate(lines):
                s += 1
                if not num:
                    nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Remarks:"
                nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = line
        # Values
        s += 2
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Value of Booking:"
        if not bd[8]:
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = "N/C"
            return
        else:
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = "R" + bd[8]
        if self.state == "X":
            return
        bl = self.getBalance()
        if self.state == "S":
            s += 2
            txt = "(Account Settled in Full)"
            nd["%s_T%02i" % (t, s)][tc.index("tpd_bold")] = "Y"
            nd["%s_T%02i" % (t, s)][tc.index("tpd_align")] = "C"
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = txt
            nd["%s_T%02i" % (t, s)][tc.index("tpd_x2")] = 200
            return
        if self.inv:
            rc = CCD(float(ASD(bl.work) - ASD(self.value)), "SD", 13.2)
        else:
            rc = bl
            bl = CCD(float(ASD(self.value) + ASD(rc.work)), "SD", 13.2)
        if self.state == "Q":
            od = CCD(float(ASD(bw[9]) + ASD(bw[11])), "SD", 13.2)
            da = CCD(float(ASD(self.value) - ASD(od.work)), "SD", 13.2)
        elif self.state == "C" and bw[11]:
            od = CCD(float(ASD(bw[9]) + ASD(bw[11]) + ASD(rc.work)), "SD", 13.2)
            da = CCD(float(ASD(self.value) + ASD(rc.work)), "SD", 13.2)
        else:
            od = CCD(0, "SD", 13.2)
            da = CCD(float(ASD(self.value) + ASD(rc.work)), "SD", 13.2)
        s += 1
        if self.state == "Q":
            if bw[11]:
                txt = "1st Deposit"
            else:
                txt = "Deposit"
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = txt
            txt = "R%s due by %s" % (bd[9], self.getDate(bw[10]))
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = txt
            if bw[11]:
                s += 1
                nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "2nd Deposit:"
                txt = "R%s due by %s" % (bd[11], self.getDate(bw[12]))
                nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = txt
        elif self.state == "C" and bw[11] and od.work > 0:
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Deposit:"
            txt = "R%s due by %s" % (od.disp, self.getDate(bw[12]))
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = txt
        elif bl.work:
            txt = "Receipts:"
            dp = CCD(float(ASD(self.value) - ASD(bl.work)), "SD", 13.2)
            nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = txt
            nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = "R" + dp.disp
        s += 1
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = "Balance:"
        txt = "R%s due Before Arrival" % da.disp
        nd["%s_C%02i" % (t, s)][tc.index("tpd_text")] = txt
        s += 2
        txt = "(No Credit Cards Please, Only Cash or EFT)"
        nd["%s_T%02i" % (t, s)][tc.index("tpd_bold")] = "Y"
        nd["%s_T%02i" % (t, s)][tc.index("tpd_align")] = "C"
        nd["%s_T%02i" % (t, s)][tc.index("tpd_text")] = txt
        nd["%s_T%02i" % (t, s)][tc.index("tpd_x2")] = 200

    def getDeposit(self):
        if not self.value:
            return 0, 0, 0, 0
        if not self.number:
            d1 = projectDate(self.sysdtw, 15)
        else:
            d1 = projectDate(self.sql.getRec("bkmtrn",
                cols=["bkt_capdt"], where=[("bkt_cono", "=",
                self.opts["conum"]), ("bkt_number", "=",
                self.number), ("bkt_type", "=", 1)],
                limit=1)[0], 15)
        if d1 > self.arrive:
            d1 = self.arrive
        if self.group:
            v1 = self.value * .10
            v2 = self.value * .50
            d2 = projectDate(self.arrive, -120)
        else:
            v1 = self.value * .50
            v2 = 0
            d2 = 0
        if d2 > self.arrive:
            d2 = self.arrive
        return v1, d1, v2, d2

    def getLines(self, nd, tc, t, s, text):
        fm = nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_font")]
        fs = nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_size")]
        self.form.set_font(fm, size=fs)
        w = nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_x2")]
        w -= nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_x1")]
        h = nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_y2")]
        h -= nd["%s_T%02i" % (t, s)][tc.index("tpd_mrg_y1")]
        txt = self.form.multi_cell(w=w, h=h, txt=text, split_only=True)
        return len(txt)

    def getBalance(self):
        bal = self.sql.getRec("bkmtrn", cols=["sum(bkt_tramt)"],
            where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
            "=", self.number), ("bkt_type", "<>", 1)], limit=1)
        if not bal[0]:
            return CCD(0, "SD", 13.2)
        else:
            return CCD(bal[0], "SD", 13.2)

    def setStatus(self, bal):
        if self.state == "X":
            self.df.loadEntry("T", 1, 15, data=self.state)
            return
        if self.inv:
            if not bal:
                self.state = "S"
            else:
                self.state = "C"
        else:
            if not bal and self.stddep:
                self.state = "Q"
            elif bal == float(ASD(0) - ASD(self.value)):
                self.state = "S"
            else:
                self.state = "C"
        self.df.loadEntry("T", 1, 15, data=self.state)

    def getDate(self, date):
        if type(date) == str:
            date = int(date.replace("-", ""))
        if not date:
            return None
        yy = int(date / 10000)
        mm = int(date / 100) % 100
        dd = date % 100
        return "%s %s %s" % (dd, mthnam[mm][1], yy)

    def doQuit(self):
        if self.newmst or self.edit or self.trans:
            ok = askQuestion(self.opts["mf"].window, "Quit",
                "Would You Like to Quit?\n\nYou Will Lose Any "\
                "Changes you might have Made.")
            if ok == "yes":
                self.quit = True
                if "args" in self.opts:
                    self.doExit()
                else:
                    self.number = 0
                    self.opts["mf"].dbm.rollbackDbase()
                    self.df.selPage("Booking", focus=False)
                    self.df.focusField("T", 1, 1)
        else:
            self.quit = True
            if "args" in self.opts:
                self.doExit()
            else:
                self.number = 0
                self.df.selPage("Booking", focus=False)
                self.df.focusField("T", 1, 1)

    def chgPage(self):
        if self.ender or self.quit:
            return
        if self.df.pag == 1 and (self.state == "Q" or self.edit):
            self.df.focusField("T", 1, 14)
        elif self.df.pag == 2 and (self.state == "Q" or self.edit):
            self.df.focusField("T", 2, 1)
        else:
            self.opts["mf"].updateStatus("Select Button or Tag to Continue")

    def doExit(self):
        self.df.closeProcess()
        if "wait" not in self.opts:
            self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
