"""
SYNOPSIS
    General Ledger Merge Accounts into a Control Account.

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

from TartanClasses import ASD, Sql, TartanDialog
from tartanFunctions import copyList, getSingleRecords, showError

class gl6070(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            if "args" in self.opts:
                self.gtype = "B"
                self.ctlacc = self.opts["args"][0]
                for rec in self.opts["args"][1]:
                    self.doMerge(rec)
            else:
                self.mainProcess()
                self.opts["mf"].startLoop()

    def setVariables(self):
        sql = Sql(self.opts["mf"].dbm, "ftable", prog=self.__class__.__name__)
        if sql.error:
            return
        self.unique = ("genbal", "genbud", "genmst", "genrcc", "genrct")
        self.tables = [
            ("assgrp", "asg_cono", "asg_assacc"),
            ("assgrp", "asg_cono", "asg_depacc"),
            ("assgrp", "asg_cono", "asg_expacc"),
            ("bkmunm", "bum_cono", "bum_slsa"),
            ("crsctl", "ctc_cono", "ctc_bankac"),
            ("crsmst", "crm_cono", "crm_glac"),
            ("ctlctl", "ctl_cono", "ctl_conacc"),
            ("ctldep", "dep_dr_coy", "dep_dr_sal"),
            ("ctldep", "dep_dr_coy", "dep_dr_com"),
            ("ctldep", "dep_cr_coy", "dep_cr_sal"),
            ("ctldep", "dep_cr_coy", "dep_cr_com"),
            ("ctlnot", "not_cono", "not_key"),
            ("ctlvtf", "vtt_cono", "vtt_acno", "vtt_styp"),
            ("drsrcm", "dcm_cono", "dcm_glac"),
            ("genbal", "glo_cono", "glo_acno"),
            ("genbud", "glb_cono", "glb_acno"),
            ("genint", "cti_cono", "cti_acno"),
            ("genjlt", "gjt_cono", "gjt_acno"),
            ("genmst", "glm_cono", "glm_acno"),
            ("genrcc", "grc_cono", "grc_acno"),
            ("genrcc", "grc_acoy", "grc_aacc"),
            ("genrct", "grt_cono", "grt_acno"),
            ("genrpt", "glr_cono", "glr_from"),
            ("genrpt", "glr_cono", "glr_to"),
            ("gentrn", "glt_cono", "glt_acno"),
            ("memctc", "mcc_cono", "mcc_glac"),
            ("rcactl", "cte_cono", "cte_glbnk"),
            ("rtlprm", "rtp_cono", "rtp_rtlacc"),
            ("rtlprm", "rtp_cono", "rtp_incacc"),
            ("strgrp", "gpm_cono", "gpm_sales"),
            ("strgrp", "gpm_cono", "gpm_costs"),
            ("strmf1", "st1_cono", "st1_sls"),
            ("strmf1", "st1_cono", "st1_cos"),
            ("wagedc", "ced_eglco", "ced_eglno"),
            ("wagedc", "ced_rglco", "ced_rglno"),
            ("wagtf2", "wt2_gl_econo", "wt2_gl_eacno"),
            ("wagtf2", "wt2_gl_rcono", "wt2_gl_racno")]
        tabs = []
        tables = copyList(self.tables)
        for tab in tables:
            chk = sql.getRec("ftable", where=[("ft_tabl", "=", tab[0])])
            if not chk:
                self.tables.remove(tab)
                continue
            if tab[0] not in tabs:
                tabs.append(tab[0])
        self.sql = Sql(self.opts["mf"].dbm, tabs, prog=self.__class__.__name__)
        if self.sql.error:
            return
        return True

    def mainProcess(self):
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])],
            "order": "glm_desc"}
        self.fld = (
            (("T",0,0,0),"IUI",7,"Control Number","Control Account Number",
                "","Y",self.doCtlAcc,glm,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            tend=tnd, txit=txt)

    def doCtlAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", where=[("glm_cono", "=",
            self.opts["conum"]), ("glm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.ctlacc = w
        desc = acc[self.sql.genmst_col.index("glm_desc")]
        self.gtype = acc[self.sql.genmst_col.index("glm_type")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doEnd(self):
        self.df.closeProcess()
        recs = getSingleRecords(self.opts["mf"], "genmst", ("glm_acno",
            "glm_desc"), where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "<>", self.ctlacc), ("glm_type", "=", self.gtype)])
        if not recs:
            showError(self.opts["mf"].body, "Error", "No Accounts Selected")
            self.opts["mf"].closeLoop()
            return
        for rec in recs:
            self.doMerge(rec[self.sql.genmst_col.index("glm_acno")])
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

    def doMerge(self, oldacc):
        # Delete Record
        self.sql.delRec("genmst", where=[("glm_cono", "=", self.opts["conum"]),
            ("glm_acno", "=", oldacc)])
        # Create and Delete genbal and genbud
        recs = self.sql.getRec("genbal", where=[("glo_cono", "=",
            self.opts["conum"]), ("glo_acno", "=", oldacc)])
        for rec in recs:
            trdt = rec[self.sql.genbal_col.index("glo_trdt")]
            cyr = rec[self.sql.genbal_col.index("glo_cyr")]
            acc = self.sql.getRec("genbal", where=[("glo_cono", "=",
                self.opts["conum"]), ("glo_acno", "=", self.ctlacc),
                ("glo_trdt", "=", trdt)], limit=1)
            if acc:
                bal = acc[self.sql.genbal_col.index("glo_cyr")]
                bal = float(ASD(bal) + ASD(cyr))
                self.sql.updRec("genbal", cols=["glo_cyr"], data=[bal],
                    where=[("glo_cono", "=", self.opts["conum"]),
                    ("glo_acno", "=", self.ctlacc),
                    ("glo_trdt", "=", trdt)])
            else:
                self.sql.insRec("genbal", data=[self.opts["conum"],
                    self.ctlacc, trdt, cyr])
            self.sql.delRec("genbal", data=rec)
        recs = self.sql.getRec("genbud", where=[("glb_cono", "=",
            self.opts["conum"]), ("glb_acno", "=", oldacc)])
        for rec in recs:
            curdt = rec[self.sql.genbud_col.index("glb_curdt")]
            tramt = rec[self.sql.genbud_col.index("glb_tramt")]
            acc = self.sql.getRec("genbud", where=[("glb_cono", "=",
                self.opts["conum"]), ("glb_acno", "=", self.ctlacc),
                ("glb_curdt", "=", curdt)], limit=1)
            if acc:
                bal = acc[self.sql.genbud_col.index("glb_tramt")]
                bal = float(ASD(bal) + ASD(tramt))
                self.sql.updRec("genbud", cols=["glb_curdt"], data=[bal],
                    where=[("glb_cono", "=", self.opts["conum"]),
                    ("glb_acno", "=", self.ctlacc),
                    ("glb_curdt", "=", curdt)])
            else:
                self.sql.insRec("genbud", data=[self.opts["conum"],
                    self.ctlacc, curdt, tramt])
            self.sql.delRec("genbud", data=rec)
        # Change All tables
        for num, tab in enumerate(self.tables):
            new = []
            if tab[0] == "genrpt":
                whr = [(tab[1], "in", (0, self.opts["conum"]))]
            else:
                whr = [(tab[1], "=", self.opts["conum"])]
            if tab[0] == "ctlnot":
                whr.extend([
                    ("not_sys", "=", "GEN"),
                    (tab[2], "=", str(oldacc))])
            elif tab[0] == "ctlvtf":
                whr.extend([
                    (tab[2], "=", str(oldacc)),
                    (tab[3], "=", "G")])
            else:
                whr.append((tab[2], "=", oldacc))
            recs = self.sql.getRec(tables=tab[0], where=whr)
            if not recs:
                continue
            # Delete records
            self.sql.delRec(tab[0], where=whr)
            # Make changes
            col = getattr(self.sql, "%s_col" % tab[0])
            pos = col.index(tab[2])
            cpy = copyList(recs)
            for rec in cpy:
                rec[pos] = self.ctlacc
                new.append(rec)
            if new:
                self.sql.insRec(tab[0], data=new)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
