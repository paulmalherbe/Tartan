"""
SYNOPSIS
    Accommodation Bookings Calendar.

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

import time
from TartanClasses import CCD, GetCtl, ScrollGrid, SelectChoice, Sql
from tartanFunctions import callModule, dateDiff, projectDate, showError
from tartanFunctions import showInfo

class bk1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.quit = False
            while not self.quit:
                self.opts["mf"].window.withdraw()
                self.doCalendar()

    def setVariables(self):
        gc = GetCtl(self.opts["mf"])
        ctlmst = gc.getCtl("ctlmst", self.opts["conum"])
        if not ctlmst:
            return
        bkmctl = gc.getCtl("bkmctl", self.opts["conum"])
        if not bkmctl:
            return
        tabs = ["bkmmst", "bkmcon", "bkmunm", "bkmrtt", "bkmtrn"]
        self.sql = Sql(self.opts["mf"].dbm, tables=tabs,
            prog=self.__class__.__name__)
        t = time.localtime()
        self.sysdtw = ((t[0] * 10000) + (t[1] * 100) + t[2])
        self.tt = None
        return True

    def doCalendar(self):
        self.number = 0
        self.ptyp = None
        self.newb = False
        udics = {}
        self.start = projectDate(self.sysdtw, -7)
        bkm = self.sql.getRec("bkmmst", cols=["max(bkm_depart)"],
            where=[("bkm_cono", "=", self.opts["conum"]), ("bkm_state",
            "<>", "X")], limit=1)
        if not bkm or bkm[0] is None:
            days = 15
        else:
            days = dateDiff(self.start, bkm[0], "days") + 1
            if days < 15:
                days = 15
        bkmunm = self.sql.getRec("bkmunm", where=[("bum_cono",
            "=", self.opts["conum"]), ("bum_maxg", "<>", 999)],
            order="bum_btyp, bum_code")
        if not bkmunm:
            showError(self.opts["mf"].body, "Units", "No Units in the Database")
            self.quit = True
            return
        col = self.sql.bkmunm_col
        for num, unit in enumerate(bkmunm):
            t = unit[col.index("bum_btyp")]
            c = unit[col.index("bum_code")]
            d = unit[col.index("bum_desc")]
            m = unit[col.index("bum_maxg")]
            if t == "A" and c == "ALL":
                continue
            udics["%s-%s" % (t, c)] = [d, CCD(m, "UI", 3).disp] + [""] * days
        for x in range(num, 10):
            t = "X"
            c = x - num
            d = ""
            m = "   "
            udics["%s-%s" % (t, c)] = [d, m] + [""] * days
        books = self.sql.getRec(tables="bkmmst",
            cols=[
                "bkm_number",
                "bkm_btype",
                "bkm_arrive",
                "bkm_depart",
                "bkm_state"],
            where=[
                ("bkm_cono", "=", self.opts["conum"]),
                ("bkm_depart", ">=", self.start),
                ("bkm_state", "<>", "X")])
        for book in books:
            if book[2] < self.start:
                book[2] = self.start
            sday = dateDiff(self.start, book[2], "days")
            eday = dateDiff(self.start, book[3], "days")
            if book[1] == "O":
                eday += 1
            bkmrtt = self.sql.getRec("bkmrtt", cols=["brt_utype",
                "brt_ucode"], where=[("brt_cono", "=", self.opts["conum"]),
                ("brt_number", "=", book[0])])
            units = []
            for rtt in bkmrtt:
                units.append("%s-%s" % tuple(rtt))
            if "A-ALL" in units:
                units.remove("A-ALL")
                for unit in udics:
                    if unit[0] == "A":
                        units.append(unit)
            for unit in units:
                if unit not in udics:
                    continue
                for d in range(sday, eday):
                    if book[4] == "Q":
                        udics[unit][d+2] = "Query|%s" % book[0]
                    elif book[4] == "C":
                        udics[unit][d+2] = "Confirmed|%s" % book[0]
                    elif book[4] == "S":
                        udics[unit][d+2] = "Settled|%s" % book[0]
        titl = ("%03i %s" % (self.opts["conum"], self.opts["conam"]),
            "Lodging and Function Bookings Calendar (bk1010)")
        labs = (
            ("Code", 8),
            ("Description", 30),
            ("Qty", 4))
        tags = [
            ("blank", (
                "black", "white")),
            ("label", (
                "black", "lightgray")),
            ("query", (
                self.opts["mf"].rcdic["qfg"], self.opts["mf"].rcdic["qbg"])),
            ("confirm", (
                self.opts["mf"].rcdic["cfg"], self.opts["mf"].rcdic["cbg"])),
            ("settle", (
                self.opts["mf"].rcdic["sfg"], self.opts["mf"].rcdic["sbg"]))]
        cols = [[]]
        for x in range(days):
            d1 = CCD(projectDate(self.start, x), "D1", 10)
            d2 = time.strftime("%A", time.strptime(str(d1.work), "%Y%m%d"))
            txt = "%s\n%s" % ("{:^10}".format(d2), d1.disp)
            cols[0].append((txt, 10))
        keys = list(udics.keys())
        keys.sort()
        data = []
        for row, key in enumerate(keys):
            cod = ("%s" % key, "label")
            des = ("%s" % udics[key][0], "label")
            qty = ("%-s" % udics[key][1], "label")
            lab = (cod, des, qty)
            col = []
            lst = None
            tag = ""
            spn = 1
            for c, d in enumerate(udics[key][2:]):
                if d == lst:
                    spn += 1
                    continue
                if lst is not None:
                    col.append((txt, tag, spn))
                    spn = 1
                lst = d
                if not d:
                    num = 0
                    txt = "\n"
                    tag = "blank"
                else:
                    sta, num = d.split("|")
                    txt = "%s\n%s" % (num, sta)
                    if sta == ("Query"):
                        tag = "query"
                    elif sta == ("Confirmed"):
                        tag = "confirm"
                    elif sta == ("Settled"):
                        tag = "settle"
            if spn > 300:
                col.append((txt, tag, 300))
                col.append((txt, tag, spn - 300))
            else:
                col.append((txt, tag, spn))
            data.append((lab, col))
        butt = [
            ("New Booking", self.doNew),
            ("Search Bookings", self.doSch),
            ("Deposits List", (self.doRep, "D")),
            ("Arrivals List", (self.doRep, "L")),
            ("Quit", self.doQuit)]
        cmds = [
            ("<Double-1>", self.doBkm),
            ("<Button-3>", self.doEnq)]
        self.cal = ScrollGrid(**{
            "mf": self.opts["mf"],
            "titl": titl,
            "chgt": 2,
            "tags": tags,
            "labs": labs,
            "cols": cols,
            "data": data,
            "butt": butt,
            "cmds": cmds,
            "font": (
                self.opts["mf"].rcdic["mft"],
                self.opts["mf"].rcdic["dfs"]),
            "wait": False,
            "minc": 14})
        self.opts["mf"].startLoop(deicon=False)
        if self.tt:
            self.tt.hideTip()
            self.tt = None
        self.cal.window.destroy()
        self.opts["mf"].setThemeFont()
        self.opts["mf"].window.deiconify()
        if not self.ptyp and not self.quit:
            callModule(self.opts["mf"], None, "bk1020",
                coy=(self.opts["conum"], self.opts["conam"]),
                user=self.opts["capnm"], args=self.number)
        elif self.ptyp == "D":
            callModule(self.opts["mf"], None, "bk3010",
                coy=(self.opts["conum"], self.opts["conam"]),
                args=True)
        elif self.ptyp == "L":
            callModule(self.opts["mf"], None, "bk3030",
                coy=(self.opts["conum"], self.opts["conam"]),
                user=self.opts["capnm"], args=True)

    def doQuit(self, event=None):
        self.quit = True
        self.opts["mf"].closeLoop()

    def doNew(self):
        self.newb = True
        self.opts["mf"].closeLoop()

    def doSch(self):
        cols = [
            ("bkno", "Number", 7, "UI", "F"),
            ("sname", "Surname", 20, "TX", "Y"),
            ("names", "Names", 20, "TX", "F"),
            ("group", "Group", 30, "TX", "F"),
            ("arrive", "Arrival-Dt", 10, "d1", "F"),
            ("state", "Status", 1, "UA", "F")]
        data = self.sql.getRec(
            tables=["bkmmst", "bkmcon"],
            cols=[
                "bkm_number", "bkc_sname", "bkc_names",
                "bkm_group", "bkm_arrive", "bkm_state"],
            where=[
                ("bkm_cono", "=", self.opts["conum"]),
                ("bkc_cono=bkm_cono",),
                ("bkc_ccode=bkm_ccode",)],
            order="bkc_sname, bkc_names")
        sc = SelectChoice(self.cal.window, "Select Booking", cols, data,
            fltr=True)
        if sc.selection:
            self.number = int(sc.selection[1])
            self.opts["mf"].closeLoop()
        else:
            self.number = None

    def doRep(self, *args):
        self.ptyp = args[0]
        self.opts["mf"].closeLoop()

    def doEnq(self, *args):
        number = args[1].split("\n")
        if number[0]:
            number = int(number[0])
        else:
            return
        data = self.sql.getRec(tables=["bkmmst", "bkmcon"], cols=["bkc_sname",
            "bkc_names", "bkm_group", "bkm_guests", "bkm_state", "bkm_value",
            "bkm_stddep", "bkm_remarks"], where=[("bkm_cono", "=",
            self.opts["conum"]), ("bkm_number", "=", number),
            ("bkc_cono=bkm_cono",), ("bkc_ccode=bkm_ccode",)], limit=1)
        name = "%s, %s" % (data[0], data[1])
        text = "%-10s %s" % ("Name:", name)
        if data[2]:
            text = "%s\n%-10s %s" % (text, "Group:", data[2])
        text = "%s\n%-10s %s" % (text, "Guests:", data[3])
        val = CCD(data[5], "SD", 13.2).disp
        text = "%s\n\n%-10s R%s" % (text, "Value:", val)
        if data[4] == "Q":
            dep = CCD(data[6], "SD", 13.2).disp
            text = "%s\n%-10s R%s" % (text, "Deposit:", dep)
        else:
            bal = self.sql.getRec("bkmtrn", cols=["sum(bkt_tramt)"],
                where=[("bkt_cono", "=", self.opts["conum"]), ("bkt_number",
                "=", number), ("bkt_type", "<>", 1)], limit=1)
            if bal[0] is None:
                if data[4] == "C":
                    bal = CCD(data[5], "SD", 13.2).disp
                else:
                    bal = CCD(0, "SD", 13.2).disp
            elif not bal[0] and data[4] == "C":
                bal = CCD(data[5], "SD", 13.2).disp
            else:
                bal = CCD(bal[0], "SD", 13.2).disp
            text = "%s\n%-10s R%s" % (text, "Balance:", bal)
            if data[7]:
                text = "%s\n\n%s" % (text, data[7])
        # cp = list(args[2][1])
        showInfo(args[2][0], "Booking %s" % number, text)

    def doBkm(self, *args):
        number = args[1].split("\n")
        if number[0]:
            self.number = int(number[0])
            self.opts["mf"].closeLoop()
        else:
            self.number = None

# vim:set ts=4 sw=4 sts=4 expandtab:
