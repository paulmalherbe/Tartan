"""
SYNOPSIS
    General Ledger Key Change.

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

from TartanClasses import CCD, FileImport, ProgressBar, Sql, TartanDialog
from tartanFunctions import askQuestion, copyList

class gl6010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
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
            ("cshana", "can_cono", "can_code"),
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
        self.doimp = False
        return True

    def mainProcess(self):
        glm = {
            "stype": "R",
            "tables": ("genmst",),
            "cols": (
                ("glm_acno", "", 0, "Acc-Num"),
                ("glm_desc", "", 0, "Description", "Y")),
            "where": [("glm_cono", "=", self.opts["conum"])]}
        self.fld = (
            (("T",0,0,0),"IUI",7,"Old Number","Old Account Number",
                "","Y",self.doOldAcc,glm,None,("notzero",)),
            (("T",0,0,0),"ONA",30,""),
            (("T",0,1,0),"IUI",7,"New Number","New Account Number",
                "","Y",self.doNewAcc,None,None,("notzero",)))
        but = (
            ("Import File",None,self.doImport,0,("T",0,1),("T",0,2),
            "Import a CSV or XLS File with the Correct Format i.e. "\
            "Old Code, New Code. If the New Code is left Blank the "\
            "Old Code will be Retained."),)
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=self.fld,
            butt=but, tend=tnd, txit=txt)

    def doImport(self):
        self.df.closeProcess()
        self.doimp = True
        impcol = []
        pos = 0
        for num, fld in enumerate(self.fld):
            if num == 1:
                continue
            if type(fld[2]) in (tuple, list):
                size = fld[2][1]
            else:
                size = fld[2]
            impcol.append([fld[4], pos, fld[1][1:], size])
            pos += 1
        fi = FileImport(self.opts["mf"], impcol=impcol)
        chgs = fi.impdat
        if chgs:
            chgs.sort()
            self.doChange(chgs)
        self.opts["mf"].closeLoop()

    def doOldAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", where=[("glm_cono", "=",
            self.opts["conum"]), ("glm_acno", "=", w)], limit=1)
        if not acc:
            return "Invalid Account Number, Does Not exist"
        self.oldacc = w
        desc = acc[self.sql.genmst_col.index("glm_desc")]
        self.df.loadEntry(frt, pag, p+1, data=desc)

    def doNewAcc(self, frt, pag, r, c, p, i, w):
        acc = self.sql.getRec("genmst", where=[("glm_cono", "=",
            self.opts["conum"]), ("glm_acno", "=", w)], limit=1)
        if acc:
            return "Invalid Account Number, Already Exists"
        self.newacc = w

    def doEnd(self):
        self.doChange([[self.oldacc, self.newacc]])
        self.df.focusField("T", 0, 1)

    def doChange(self, chgs):
        if self.doimp:
            p1 = ProgressBar(self.opts["mf"].body, typ="",
                mxs=len(self.tables))
            genrpt = "no"
        else:
            genrpt = askQuestion(self.opts["mf"].body, head="Report Generator",
                mess="Apply this Change to the Report Generator as well?",
                default="no")
        for num, tab in enumerate(self.tables):
            if tab[0] == "genrpt" and genrpt == "no":
                continue
            if self.doimp:
                p1.txtlab.configure(text="Changing %s Table" % tab[0])
                p1.displayProgress(num)
            new = []
            if self.doimp:
                p2 = ProgressBar(self.opts["mf"].body, inn=p1, typ="",
                    mxs=len(chgs))
            for seq, chg in enumerate(chgs):
                if self.doimp:
                    p2.txtlab.configure(text="Changing Number %s to %s" %
                        (chg[0], chg[1]))
                    p2.displayProgress(seq)
                # Get records for this change
                oldacc, newacc = chg
                if tab[0] == "genrpt":
                    whr = [(tab[1], "in", (0, self.opts["conum"]))]
                else:
                    whr = [(tab[1], "=", self.opts["conum"])]
                if tab[0] == "ctlnot":
                    whr.extend([
                        ("not_sys", "=", "GEN"),
                        (tab[2], "=", str(oldacc))])
                elif tab[0] == "ctlvtf":
                    oldacc = CCD(oldacc, "Na", 7).work
                    newacc = CCD(newacc, "Na", 7).work
                    whr.extend([
                        (tab[2], "=", oldacc),
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
                    rec[pos] = newacc
                    new.append(rec)
            if self.doimp:
                p2.closeProgress()
            if new:
                self.sql.insRec(tab[0], data=new)
        if self.doimp:
            p1.closeProgress()
            self.opts["mf"].dbm.commitDbase(ask=True)

    def doExit(self):
        self.df.closeProcess()
        self.opts["mf"].dbm.commitDbase(ask=True)
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
