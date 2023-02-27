"""
SYNOPSIS
    Template Maintenance.
    This program is used to create and maintain template records.
    With these records, and fpdf, you can design your own document layouts.

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

import operator, os
from TartanClasses import ViewPDF, DrawForm, FileDialog, RepPrt, Sql
from TartanClasses import TartanDialog, tkfont
from tartanFunctions import askQuestion, showError, showInfo
from tartanWork import allsys, stdtpl, tptrtp

class tp1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if self.setVariables():
            self.mainProcess()
            self.opts["mf"].startLoop()
            self.opts["mf"].setThemeFont()

    def setVariables(self):
        self.sql = Sql(self.opts["mf"].dbm, ["ffield", "tplmst", "tpldet"],
            prog=self.__class__.__name__)
        if self.sql.error:
            return
        self.pags = ["", "Q", "R", "I", "L", "T", "C"]
        self.image_flds = [
            "tpd_x1", "tpd_x2", "tpd_y1", "tpd_lh", "tpd_y2", "tpd_text",
            "tpd_mrgcod"]
        self.rect_flds = [
            "tpd_x1", "tpd_x2", "tpd_y1", "tpd_lh", "tpd_y2", "tpd_thick"]
        self.line_flds = [
            "tpd_font", "tpd_size", "tpd_colour", "tpd_bold", "tpd_x1",
            "tpd_chrs", "tpd_x2", "tpd_y1", "tpd_lh", "tpd_y2", "tpd_thick"]
        self.text_flds = [
            "tpd_font", "tpd_size", "tpd_colour", "tpd_bold", "tpd_italic",
            "tpd_uline", "tpd_align", "tpd_border", "tpd_fill", "tpd_x1",
            "tpd_chrs", "tpd_x2", "tpd_y1", "tpd_lh", "tpd_y2", "tpd_text"]
        self.code_flds = [
            "tpd_ttyp", "tpd_text", "tpd_font", "tpd_size", "tpd_colour",
            "tpd_bold", "tpd_italic", "tpd_uline", "tpd_align", "tpd_border",
            "tpd_fill", "tpd_x1", "tpd_chrs", "tpd_x2", "tpd_y1", "tpd_lh",
            "tpd_y2", "tpd_mrgcod", "tpd_mrg_font", "tpd_mrg_size",
            "tpd_mrg_colour", "tpd_mrg_bold", "tpd_mrg_italic",
            "tpd_mrg_uline", "tpd_mrg_align", "tpd_mrg_border", "tpd_mrg_fill",
            "tpd_mrg_x1", "tpd_mrg_chrs", "tpd_mrg_x2", "tpd_mrg_y1",
            "tpd_mrg_lh", "tpd_mrg_y2", "tpd_lines", "tpd_repeat"]
        # Tables to ignore
        self.ignore = []
        self.fonts = ["courier", "helvetica", "times"]
        self.repeat = 0
        return True

    def mainProcess(self):
        tpm = {
            "stype": "R",
            "title": "Available Existing Templates",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_system", "", 0, "SYS"),
                ("tpm_type", "", 0, "T")),
            "order": "tpm_tname"}
        tpt = {
            "stype": "C",
            "titl": "Select the Template Type",
            "head": ("C", "Type"),
            "data": [
                ("B", "Booking"),
                ("C", "Competitions"),
                ("I", "Sales Document"),
                ("J", "Point of Sale"),
                ("M", "Membership Card"),
                ("O", "Purchase Order"),
                ("P", "Payslip"),
                ("R", "Remittance Advice"),
                ("S", "Statement")]}
        self.sys = {
            "stype": "C",
            "titl": "Select the System",
            "head": ("COD", "Description"),
            "data": []}
        self.stt = {
            "stype": "C",
            "titl": "Select the Statement Type",
            "head": ("COD", "Description"),
            "data": []}
        tpd = {
            "stype": "R",
            "tables": ("tpldet",),
            "cols": (
                ("tpd_detseq", "", 0, "Seq"),
                ("tpd_type", "", 0, "T"),
                ("tpd_place", "", 0, "P"),
                ("tpd_ttyp", "", 0, "T"),
                ("tpd_text", "", 0, "Text-Detail"),
                ("tpd_border", "", 0, "BRDR"),
                ("tpd_x1", "", 0, "X1"),
                ("tpd_chrs", "", 0, "Wth"),
                ("tpd_x2", "", 0, "X2"),
                ("tpd_y1", "", 0, "Y1"),
                ("tpd_lh", "", 0, "H"),
                ("tpd_y2", "", 0, "Y2"),
                ("tpd_mrgcod", "", 0, "Merge Code"),
                ("tpd_mrg_border", "", 0, "BRDR"),
                ("tpd_mrg_x1", "", 0, "X1"),
                ("tpd_mrg_chrs", "", 0, "Wth"),
                ("tpd_mrg_x2", "", 0, "X2"),
                ("tpd_mrg_y1", "", 0, "Y1"),
                ("tpd_mrg_lh", "", 0, "H"),
                ("tpd_mrg_y2", "", 0, "Y2")),
            "whera": (("T", "tpd_tname", 0, 0),)}
        typ = {
            "stype": "C",
            "titl": "Select the Required Type",
            "head": ("C", "Type"),
            "data": [
                ("R", "Rectangle"),
                ("I", "Image"),
                ("L", "Line"),
                ("T", "Text"),
                ("C", "Merge Code")]}
        fle = {
            "stype": "F",
            "types": "fle",
            "ftype": (("JPG Files", "*.[j,J][p,P][g,G]"),)}
        fnt = {
            "stype": "C",
            "titl": "Select the Required Font",
            "head": ("Family"),
            "data": self.fonts}
        col = {
            "stype": "X",
            "title": "Select Colour",
            "initc": "foreground"}
        bdr = {
            "stype": "C",
            "titl": "Select Combination",
            "head": ("C", "Borders"),
            "data": (
                ("", "None"),
                ("T", "Top Only"),
                ("L", "Left Only"),
                ("R", "Right Only"),
                ("B", "Bottom Only"),
                ("TL", "Top & Left"),
                ("TR", "Top & Right"),
                ("TB", "Top & Bottom"),
                ("LR", "Left & Right"),
                ("LB", "Left & Bottom"),
                ("RB", "Right & Bottom"),
                ("TLR", "Top, Left & Right"),
                ("TLB", "Top, Left & Bottom"),
                ("TRB", "Top, Right & Bottom"),
                ("LRB", "Left, Right & Bottom"),
                ("TLRB", "Top, Left, Right & Bottom"))}
        tlrb = []
        for b in bdr["data"]:
            tlrb.append(b[0])
        self.mrg = {
            "stype": "C",
            "titl": "Select the Merge Code",
            "head": ["Table", "Merge Code", "Tp", "Size", "Description"],
            "data": [],
            "index": 1}
        plc = (("Head","A"),("Body","B"),("Total","C"),("Tail","D"))
        ttp = (("Heading","H"),("Label","L"),("None","N"))
        ayn = (("Yes","Y"),("No","N"))
        aal = (("Left","L"),("Right","R"),("Centre","C"),("None",""))
        tag = [
            ("Sequence",None,None,None,False),
            ("Rectangle",None,None,None,False),
            ("Image",None,None,None,False),
            ("Line",None,None,None,False),
            ("Text",None,None,None,False),
            ("Code",None,None,None,False)]
        sizes = (
            "A4/A5/A6/CC/S8/S6",
            ("A4", "A5", "A6", "CC", "S8", "S6"))
        fld = (
            (("T",0,0,0),"I@tpm_tname",0,"Name","Template Name",
                "","Y",self.doTemplate,tpm,None,("notblank", "nospaces")),
            (("T",0,0,0),"I@tpm_title",0,"Title","Template Title",
                "","N",None,None,self.doDelTpt,("notblank",)),
            (("T",0,0,0),"I@tpm_type",0,"TT","Template Type",
                "","N",self.doTptTyp,tpt,None,("in",list(tptrtp.keys()))),
            (("T",0,0,0),"I@tpm_system",0,"Sys","Financial System",
                "","N",self.doSystem,self.sys,None,("notblank",)),
            (("T",0,0,0),"I@tpm_sttp",0,"ST","Statement Type",
                "","N",self.doSmtTyp,self.stt,None,("in",("N","O","T"))),
            (("T",0,0,0),"I@tpm_pgsize",0,"Size","Page Size (%s)" % sizes[0],
                "A4","N",None,None,None,("in",sizes[1])),
            (("T",0,0,0),"I@tpm_orient",0,"Orient","Orientation (P/L)",
                "P","N",None,None,None,("in",("P","L"))),
            (("T",1,0,0),"I@tpd_detseq",0,"","",
                "","N",self.doLineNo,tpd,None,("efld",)),
            (("T",1,1,0),"I@tpd_type",0,"","",
                "C","N",self.doSeqTyp,typ,self.doDelDet,
                ("in",("R","I","L","T","C"))),
            (("T",1,2,0),("IRB",plc),0,"Placement","",
                "A","N",self.doPlace,None,None,None),
            (("T",2,0,0),"I@tpd_x1",0,"","",
                "","N",self.doX1,None,None,("efld",)),
            (("T",2,0,0),"I@tpd_x2",0,"","",
                "","N",self.doX2,None,None,("notzero",)),
            (("T",2,1,0),"I@tpd_y1",0,"","",
                "","N",self.doY1,None,None,("efld",)),
            (("T",2,1,0),"I@tpd_lh",0,"RHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",2,1,0),"I@tpd_y2",0,"","",
                "","N",self.doY2,None,None,("efld",)),
            (("T",2,2,0),"I@tpd_thick",0,"Line Thickness","",
                0,"N",None,None,None,("efld",)),
            (("T",3,0,0),"I@tpd_x1",0,"","",
                0,"N",self.doX1,None,None,("efld",)),
            (("T",3,0,0),"I@tpd_x2",0,"","",
                0,"N",self.doX2,None,None,("efld",)),
            (("T",3,1,0),"I@tpd_y1",0,"","",
                0,"N",self.doY1,None,None,("efld",)),
            (("T",3,1,0),"I@tpd_lh",0,"IHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",3,1,0),"I@tpd_y2",0,"","",
                0,"N",self.doY2,None,None,("efld",)),
            (("T",3,2,0),"I@tpd_text",0,"File Name","",
                "","N",self.doFleNam,fle,None,None),
            (("T",3,3,0),"I@tpd_mrgcod",0,"","",
                "","N",self.doMrgCod,self.mrg,None,None),
            (("T",4,0,0),"I@tpd_font",0,"","",
                "courier","N",self.doFont,fnt,None,("in", self.fonts)),
            (("T",4,0,0),"I@tpd_size",0,"Size","",
                10,"N",self.doSize,None,None,("notzero",)),
            (("T",4,1,0),"I@tpd_colour",0,"Font Colour","",
                "#000000","N",self.doColour,col,None,("notblank",)),
            (("T",4,2,0),("IRB",ayn),0,"Bold","",
                "N","N",self.doBold,None,None,None),
            (("T",4,3,0),"I@tpd_x1",0,"","",
                0,"N",self.doX1,None,None,("efld",)),
            (("T",4,3,0),"I@tpd_chrs",0,"Chrs","Width in Charaters",
                0,"N",self.doChrs,None,None,("notzero",)),
            (("T",4,3,0),"I@tpd_x2",0,"","",
                0,"N",self.doX2,None,None,("notzero",)),
            (("T",4,4,0),"I@tpd_y1",0,"","",
                0,"N",self.doY1,None,None,("efld",)),
            (("T",4,4,0),"I@tpd_lh",0,"LHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",4,4,0),"I@tpd_y2",0,"","",
                "","N",self.doY2,None,None,("efld",)),
            (("T",4,5,0),"I@tpd_thick",0,"Line Thickness","",
                0,"N",None,None,None,("efld",)),
            (("T",5,0,0),"I@tpd_font",0,"","",
                "courier","N",self.doFont,fnt,None,("in", self.fonts)),
            (("T",5,0,0),"I@tpd_size",0,"Size","",
                10,"N",self.doSize,None,None,("notzero",)),
            (("T",5,1,0),"I@tpd_colour",0,"Font Colour","",
                "#000000","N",self.doColour,col,None,("notblank",)),
            (("T",5,2,0),("ICB","Bold"),0,"Font Options","",
                "N","N",self.doBold,None,None,None),
            (("T",5,2,0),("ICB","Italic"),0,"","",
                "N","N",None,None,None,None),
            (("T",5,2,0),("ICB","Underline"),0,"","",
                "N","N",None,None,None,None),
            (("T",5,3,0),("IRB",aal),0,"Alignment","",
                "L","N",None,None,None,None),
            (("T",5,4,0),"I@tpd_border",0,"Border","",
                "","N",None,bdr,None,("in",tlrb)),
            (("T",5,5,0),("IRB",ayn),0,"Fill Background","",
                "N","N",self.doFill,None,None,None),
            (("T",5,6,0),"I@tpd_x1",0,"X1 Co-Ordinate","",
                0,"N",self.doX1,None,None,("efld",)),
            (("T",5,6,0),"I@tpd_chrs",0,"Chrs","Width in Charaters",
                0,"N",self.doChrs,None,None,("notzero",)),
            (("T",5,6,0),"I@tpd_x2",0,"X2", "X2 Co-Ordinate",
                0,"N",self.doX2,None,None,("notzero",)),
            (("T",5,7,0),"I@tpd_y1",0,"","",
                0,"N",self.doY1,None,None,("efld",)),
            (("T",5,7,0),"I@tpd_lh",0,"LHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",5,7,0),"I@tpd_y2",0,"","",
                "","N",self.doY2,None,None,("notzero",)),
            (("T",5,8,0),"I@tpd_text",30,"Text Detail","",
                "","N",None,None,None,("notblank",)),
            (("T",6,0,0),("IRB",ttp),0,"Text Type","",
                "N","N",self.doTxtTyp,None,None,None),
            (("T",6,1,0),"I@tpd_text",0,"Text Detail","",
                "","N",self.doText,None,None,("efld",)),
            (("T",6,2,0),"I@tpd_font",0,"","",
                "courier","N",self.doFont,fnt,None,("in", self.fonts)),
            (("T",6,2,0),"I@tpd_size",0,"Size","",
                10,"N",self.doSize,None,None,("notzero",)),
            (("T",6,3,0),"I@tpd_colour",0,"Font Colour","",
                "#000000","N",self.doColour,col,None,("notblank",)),
            (("T",6,4,0),("ICB","Bold"),0,"Font Options","",
                "N","N",self.doBold,None,None,None),
            (("T",6,4,0),("ICB","Italic"),0,"","",
                "N","N",None,None,None,None),
            (("T",6,4,0),("ICB","Underline"),0,"","",
                "N","N",None,None,None,None),
            (("T",6,5,0),("IRB",aal),0,"Alignment","",
                "L","N",None,None,None,None),
            (("T",6,6,0),"I@tpd_border",0,"Border","",
                "","N",self.doBorder,bdr,None,("in",tlrb)),
            (("T",6,7,0),("IRB",ayn),0,"Fill Background","",
                "N","N",self.doFill,None,None,None),
            (("T",6,8,0),"I@tpd_x1",0,"X1 Co-Ordinate","",
                0,"N",self.doX1,None,None,("efld",)),
            (("T",6,8,0),"I@tpd_chrs",0,"Chrs","Width in Charaters",
                0,"N",self.doChrs,None,None,("notzero",)),
            (("T",6,8,0),"I@tpd_x2",0,"X2", "X2 Co-Ordinate",
                0,"N",self.doX2,None,None,("notzero",)),
            (("T",6,9,0),"I@tpd_y1",0,"Y1 Co-Ordinate","",
                0,"N",self.doY1,None,None,("efld",)),
            (("T",6,9,0),"I@tpd_lh",0,"LHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",6,9,0),"I@tpd_y2",0,"Y2","Y2 Co-Ordinate",
                "","N",self.doY2,None,None,("notzero",)),
            (("T",6,10,0),"I@tpd_mrgcod",0,"","",
                "","N",self.doMrgCod,self.mrg,None,("notblank",)),
            (("T",6,11,0),"I@tpd_mrg_font",0,"","",
                "courier","N",self.doFont,fnt,None,("in", self.fonts)),
            (("T",6,11,0),"I@tpd_mrg_size",0,"Size","",
                10,"N",self.doSize,None,None,("notzero",)),
            (("T",6,12,0),"I@tpd_mrg_colour",0,"Font Colour","",
                "#000000","N",self.doColour,col,None,("notblank",)),
            (("T",6,13,0),("ICB","Bold"),0,"Font Options","",
                "N","N",self.doBold,None,None,None),
            (("T",6,13,0),("ICB","Italic"),0,"","",
                "N","N",None,None,None,None),
            (("T",6,13,0),("ICB","Underline"),0,"","",
                "N","N",None,None,None,None),
            (("T",6,14,0),("IRB",aal),0,"Alignment","",
                "L","N",None,None,None,None),
            (("T",6,15,0),"I@tpd_mrg_border",0,"Border","",
                "","N",self.doBorder,bdr,None,("in",tlrb)),
            (("T",6,16,0),("IRB",ayn),0,"Fill Background","",
                "N","N",self.doFill,None,None,None),
            (("T",6,17,0),"I@tpd_mrg_x1",0,"X1 Co-Ordinate","",
                0,"N",self.doX1,None,None,("efld",)),
            (("T",6,17,0),"I@tpd_mrg_chrs",0,"Chrs","Width in Characters",
                0,"N",self.doChrs,None,None,("notzero",)),
            (("T",6,17,0),"I@tpd_mrg_x2",0,"X2", "X2 Co-Ordinate",
                0,"N",self.doX2,None,None,("notzero",)),
            (("T",6,18,0),"I@tpd_mrg_y1",0,"Y1 Co-Ordinate","",
                0,"N",self.doY1,None,None,("efld",)),
            (("T",6,18,0),"I@tpd_mrg_lh",0,"LHgt","",
                "","N",self.doLh,None,None,("efld",)),
            (("T",6,18,0),"I@tpd_mrg_y2",0,"Y2","Y2 Co-Ordinate",
                "","N",self.doY2,None,None,("notzero",)),
            (("T",6,19,0),"I@tpd_lines",0,"Number of Lines","",
                1,"N",self.doLines,None,None,("notzero",)),
            (("T",6,19,0),"I@tpd_repeat",0,"Repeats","",
                1,"N",self.doRepeat,None,None,("notzero",)))
        tnd = (
            (self.doT0End,"y"), (self.doT1End,"n"), (self.doT2End,"y"),
            (self.doT2End,"y"), (self.doT2End,"y"), (self.doT2End,"y"),
            (self.doT2End,"y"))
        txt = (
            self.doT0Exit, self.doT1Exit, self.doT2Exit, self.doT2Exit,
            self.doT2Exit, self.doT2Exit, self.doT2Exit)
        but = (
            ("Import",None,self.doImport,0,("T",0,1),(("T",0,0),("T",0,2))),
            ("Copy",None,self.doCpyTpt,0,("T",0,2),(("T",0,1),("T",0,3))),
            ("Export",None,self.doExport,0,("T",1,1),(("T",0,1),("T",1,2))),
            ("Re-Sequence",None,self.doReSeq,0,("T",1,1),(("T",0,1),("T",1,2))),
            ("Print",None,self.doPrint,0,("T",1,1),(("T",0,1),("T",1,2))),
            ("View PDF",None,self.doView,0,("T",1,1),(("T",0,1),("T",1,2))),
            ("Exit",None,self.doT1Exit,0,("T",1,1),(("T",0,1),("T",1,2))),
            ("Quit",None,self.doT0Exit,1,None,None))
        self.df = TartanDialog(self.opts["mf"], eflds=fld, tend=tnd,
            txit=txt, tags=tag, butt=but, clicks=self.doClick)

    def doClick(self, *opts):
        if self.df.pag in (0, 1):
            return
        if self.newdet:
            return
        if opts[0][0] == 6 and \
                self.df.t_work[6][0][0] == "N" and opts[0][1] < 17:
            return
        self.df.focusField("T", opts[0][0], opts[0][1] + 1)

    def doTemplate(self, frt, pag, r, c, p, i, w):
        self.template = w
        self.cpytpm = False
        tpm = self.sql.getRec("tplmst", where=[("tpm_tname", "=",
            self.template)], limit=1)
        if tpm:
            self.newtpm = False
            self.ttype = tpm[self.sql.tplmst_col.index("tpm_type")]
            self.sttyp = tpm[self.sql.tplmst_col.index("tpm_sttp")]
            for s, t in enumerate(tpm[1:]):
                self.df.loadEntry(frt, pag, p+s+1, data=t)
        else:
            self.newtpm = True
            self.ttype = None
            self.sttyp = None
        if self.template in stdtpl:
            self.nochg = True
            self.df.butt[1][4] = None
            return "nd"
        else:
            self.nochg = False
            self.df.butt[1][4] = ("T",0,2)

    def doTptTyp(self, frt, pag, r, c, p, i, w):
        if self.ttype and w != self.ttype:
            yn = askQuestion(self.opts["mf"].body, "Change Type?",
                "Are You Sure You Want to Change the Template Type?",
                default="no")
            if yn == "no":
                self.df.loadEntry(frt, pag, p, data=self.ttype)
                return "rf"
        self.ttype = w
        self.sys["data"] = []
        for s in tptrtp[self.ttype]["tables"]:
            self.sys["data"].append((s, allsys[s.upper()][0]))
        self.df.topf[0][3][5] = self.sys["data"][0][0]

    def doSystem(self, frt, pag, r, c, p, i, w):
        if w not in tptrtp[self.ttype]["tables"]:
            return "Invalid System Code"
        self.systyp = w
        self.tptrtp = tptrtp["G"]["codes"]
        for key in tptrtp[self.ttype]["codes"]:
            self.tptrtp[key] = tptrtp[self.ttype]["codes"][key]
        tabs = tptrtp["G"]["tables"]
        tabs.extend(tptrtp[self.ttype]["tables"][self.systyp])
        rec = self.sql.getRec("ffield", cols=["ff_tabl", "ff_name",
            "ff_type", "ff_size", "ff_desc"], where=[("ff_tabl", "in",
            tuple(tabs))])
        for rr in rec:
            if rr[1] != "ctm_cono" and rr[1][4:] == "cono":
                continue
            if rr[1] in self.ignore:
                continue
            self.tptrtp[rr[1]] = [[rr[0]] + rr[2:], []]
        data = []
        for key in self.tptrtp:
            data.append([self.tptrtp[key][0][0], key]+self.tptrtp[key][0][1:])
        self.mrg["data"] = sorted(data, key=operator.itemgetter(0, 1))
        if self.ttype != "S":
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"
        if self.systyp == "RCA":
            self.stt["data"] = [
                ("O", "Owner"),
                ("T", "Tenant")]
        else:
            self.stt["data"] = [
                ("N", "Normal Layout"),
                ("O", "Other Layout")]

    def doSmtTyp(self, frt, pag, r, c, p, i, w):
        if self.systyp == "RCA" and w not in ("O", "T"):
            return "Invalid Statement Type"
        elif self.systyp != "RCA" and w not in ("N", "O"):
            return "Invalid Statement Type"
        if self.sttyp and w != self.sttyp:
            yn = askQuestion(self.opts["mf"].body, "Change Type?",
                "Are You Sure You Want to Change the Statement Type?",
                default="no")
            if yn == "no":
                self.df.loadEntry(frt, pag, p, data=self.sttyp)
                return "rf"
        if w == "N":
            for txt in ("total_arrears", "month_exclusive", "month_tax"):
                for m in self.mrg["data"]:
                    if m[1] == txt:
                        self.mrg["data"].remove(m)
        else:
            for txt in ("current_balance", "30_day_balance", "60_day_balance",
                     "90_day_balance", "120_day_balance", "total_balance"):
                for m in self.mrg["data"]:
                    if m[1] == txt:
                        self.mrg["data"].remove(m)

    def doLineNo(self, frt, pag, r, c, p, i, w):
        if self.nochg:
            showInfo(self.opts["mf"].body, "Locked",
                "This is a Locked Template, No Changes are Allowed.")
            return "rf"
        if not w:
            rec = self.sql.getRec("tpldet", cols=["max(tpd_detseq)"],
                where=[("tpd_tname", "=", self.template)], limit=1)
            if not rec[0]:
                self.detseq = 1
            else:
                self.detseq = int(rec[0]) + 1
            self.df.loadEntry(frt, pag, p, data=self.detseq)
        else:
            self.detseq = w
        self.text = ""
        self.tpldet = self.doReadDet(self.template, self.detseq)
        if not self.tpldet:
            self.newdet = True
        else:
            self.newdet = False
            self.df.loadEntry(frt, pag, p+1,
                data=self.tpldet[self.sql.tpldet_col.index("tpd_type")])
            self.df.loadEntry(frt, pag, p+2,
                data=self.tpldet[self.sql.tpldet_col.index("tpd_place")])

    def doSeqTyp(self, frt, pag, r, c, p, i, w):
        self.dtype = w
        if self.newdet:
            return
        if self.dtype == self.tpldet[2]:
            return
        yn = askQuestion(self.opts["mf"].body, "Change Type?",
            "Change the Type?", default="no")
        if yn == "no":
            return "rf"

    def doPlace(self, frt, pag, r, c, p, i, w):
        self.place = w

    def doTxtTyp(self, frt, pag, r, c, p, i, w):
        self.ttyp = w
        if self.ttyp == "N":
            for x in range(p+2, p+18):
                self.df.clearEntry(frt, pag, x)
            return "sk16"

    def doText(self, frt, pag, r, c, p, i, w):
        self.text = w

    def doFleNam(self, frt, pag, r, c, p, i, w):
        self.text = w
        if self.text:
            if not os.path.isfile(self.text):
                return "Invalid File Name"
            ext = self.text.split(".")[-1]
            if ext not in ("jpg", "JPG", "jpeg", "JPEG", "png", "PNG"):
                return "Invalid Image File"
            self.df.loadEntry(frt, pag, p+1, data="")
            return "sk1"

    def doMrgCod(self, frt, pag, r, c, p, i, w):
        if self.dtype == "I" and not self.text and not w:
            return "Invalid, No File Name or Merge Code"
        if w and w not in self.tptrtp:
            return "Invalid Merge Code"
        self.mrgcod = w

    def doFont(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_font = w
        else:
            self.font = w

    def doSize(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_size = w
        else:
            self.size = w

    def doColour(self, frt, pag, r, c, p, i, w):
        if w[0] != "#":
            return "Invalid Color Code"
        if p in (2, 4):
            self.colour = w
        else:
            self.mrg_colour = w

    def doBold(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_bold = w
        else:
            self.bold = w

    def doBorder(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_border = w
        else:
            self.border = w

    def doFill(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_fill = w
            if self.ttyp == "N":
                return
            if self.ttyp == "H":
                self.mrg_x1 = self.x1
                self.df.loadEntry(frt, pag, p+1, data=self.mrg_x1)
                self.mrg_chrs = self.chrs
                self.df.loadEntry(frt, pag, p+2, data=self.mrg_chrs)
                self.mrg_x2 = self.x2
                self.df.loadEntry(frt, pag, p+3, data=self.mrg_x2)
                self.mrg_y1 = self.y2
                self.df.loadEntry(frt, pag, p+4, data=self.mrg_y1)
                self.mrg_lh = self.lh
                return "sk4"
            else:
                self.mrg_x1 = self.x2
                self.df.loadEntry(frt, pag, p+1, data=self.mrg_x1)
                return "sk1"
        else:
            self.fill = w

    def doX1(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_x1 = w
            if self.newdet:
                chrs = self.tptrtp[self.mrgcod][0][2]
                self.df.loadEntry(frt, pag, p+1, data=chrs)
        else:
            self.x1 = w
            if self.newdet and self.text:
                chrs = len(self.text)
                self.df.loadEntry(frt, pag, p+1, data=chrs)

    def doChrs(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_chrs = w
            if "L" or "R" in self.mrg_border:
                pad = 1
            else:
                pad = 0
            wdth = self.doGetWidth(self.mrg_chrs, self.mrg_font,
                self.mrg_size, self.mrg_bold, pad=pad)
            self.mrg_x2 = self.mrg_x1 + wdth
            self.df.loadEntry(frt, pag, p+1, data=self.mrg_x2)
        else:
            self.chrs = w
            if self.dtype != "L" and ("L" or "R" in self.border):
                pad = 1
            else:
                pad = 0
            wdth = self.doGetWidth(self.chrs, self.font,
                self.size, self.bold, pad=pad)
            self.x2 = self.x1 + wdth
            self.df.loadEntry(frt, pag, p+1, data=self.x2)

    def doX2(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            if w < self.mrg_x1:
                return "Invalid X2 Co-Ordinate, Less than X1"
            self.mrg_x2 = w
            if self.ttyp == "N":
                return
            if self.ttyp == "H":
                self.mrg_y1 = self.y2
            else:
                self.mrg_y1 = self.y1
            self.df.loadEntry(frt, pag, p+1, data=self.mrg_y1)
            return "sk1"
        else:
            if w and w < self.x1:
                return "Invalid X2 Co-Ordinate, Less than X1"
            self.x2 = w

    def doY1(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_y1 = w
            if not self.mrg_lh:
                if "T" or "B" in self.mrg_border:
                    self.mrg_lh = self.mrg_y1 + 5
                else:
                    self.mrg_lh = self.mrg_y1 + 4
                self.df.loadEntry(frt, pag, p+1, data=self.mrg_lh)
        else:
            self.y1 = w
            if not self.lh:
                if self.dtype == "L":
                    self.lh = self.y1
                elif "tpd_border" in self.flds and ("T" or "B" in self.border):
                    self.lh = self.y1 + 5
                else:
                    self.lh = self.y1 + 4
                self.df.loadEntry(frt, pag, p+1, data=self.lh)

    def doLh(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            self.mrg_lh = w
            self.mrg_y2 = self.mrg_y1 + self.mrg_lh
            self.df.loadEntry(frt, pag, p+1, data=self.mrg_y2)
        else:
            self.lh = w
            self.y2 = self.y1 + self.lh
            self.df.loadEntry(frt, pag, p+1, data=self.y2)

    def doY2(self, frt, pag, r, c, p, i, w):
        if pag == 6 and p > 17:
            if w < self.mrg_y1:
                return "Invalid Y2 Co-ordinate, less than Y1"
            self.mrg_y2 = w
        else:
            if w < self.y1:
                return "Invalid Y2 Co-ordinate, less than Y1"
            self.y2 = w

    def doLines(self, frt, pag, r, c, p, i, w):
        if w and w > 1 or self.place == "A":
            self.df.loadEntry(frt, pag, p+1, data=1)
            return "sk1"
        elif self.repeat > 1:
            self.df.loadEntry(frt, pag, p+1, data=self.repeat)
            return "sk1"

    def doRepeat(self, frt, pag, r, c, p, i, w):
        self.repeat = w

    def doDelTpt(self):
        self.sql.delRec("tplmst", where=[("tpm_tname", "=", self.template)])
        self.sql.delRec("tpldet", where=[("tpd_tname", "=", self.template)])
        self.opts["mf"].dbm.commitDbase()
        self.df.focusField("T", 0, 1)

    def doCpyTpt(self):
        if not self.newtpm:
            showError(self.opts["mf"].body, "Invalid Copy Request",
                "You can only Copy a template when Creating a New template, "\
                "not when Changing an Existing template!")
            self.df.focusField("T", 0, 2)
            return
        tit = ("Copy Existing Template",)
        tpm = {
            "stype": "R",
            "tables": ("tplmst",),
            "cols": (
                ("tpm_tname", "", 0, "Template"),
                ("tpm_title", "", 0, "Title"),
                ("tpm_type", "", 0, "T")),
            "order": "tpm_tname"}
        fld = (
            (("T",0,1,0),"INA",20,"Template Name","",
                "","N",self.doCpyNam,tpm,None,None),
            (("T",0,2,0),"ISI",3,"Adjust X Margin By","",
                "","N",self.doCpyXmg,None,None,None),
            (("T",0,3,0),"ISI",3,"Adjust Y Margin By","",
                "","N",self.doCpyYmg,None,None,None))
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.cp = TartanDialog(self.opts["mf"], title=tit, tops=True,
            eflds=fld, tend=((self.doCpyEnd, "n"),),
        txit=(self.doCpyExit,))
        self.cp.mstFrame.wait_window()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField("T", 0, 2)

    def doCpyNam(self, frt, pag, r, c, p, i, w):
        self.cpymst = self.sql.getRec("tplmst", where=[("tpm_tname", "=", w)],
            limit=1)
        if not self.cpymst:
            return "Invalid Template Name"
        self.cpynam = w
        for s, t in enumerate(self.cpymst[1:]):
            self.df.loadEntry(frt, pag, p+s+1, data=t)

    def doCpyXmg(self, frt, pag, r, c, p, i, w):
        self.chgx = w

    def doCpyYmg(self, frt, pag, r, c, p, i, w):
        self.chgy = w

    def doCpyEnd(self):
        self.cpymst[0] = self.template
        self.sql.insRec("tplmst", data=self.cpymst)
        det = self.sql.getRec("tpldet", where=[("tpd_tname", "=",
            self.cpynam)])
        for line in det:
            line[0] = self.template
            if self.chgx:
                if line[self.sql.tpldet_col.index("tpd_x1")]:
                    line[self.sql.tpldet_col.index("tpd_x1")] += self.chgx
                    line[self.sql.tpldet_col.index("tpd_x2")] += self.chgx
                if line[self.sql.tpldet_col.index("tpd_mrg_x1")]:
                    line[self.sql.tpldet_col.index("tpd_mrg_x1")] += self.chgx
                    line[self.sql.tpldet_col.index("tpd_mrg_x2")] += self.chgx
            if self.chgy:
                if line[self.sql.tpldet_col.index("tpd_y1")]:
                    line[self.sql.tpldet_col.index("tpd_y1")] += self.chgy
                    line[self.sql.tpldet_col.index("tpd_y2")] += self.chgy
                if line[self.sql.tpldet_col.index("tpd_mrg_y1")]:
                    line[self.sql.tpldet_col.index("tpd_mrg_y1")] += self.chgy
                    line[self.sql.tpldet_col.index("tpd_mrg_y2")] += self.chgy
            self.sql.insRec("tpldet", data=line)
        self.cpytpm = True
        self.newtpm = False
        self.doCpyCloseProcess()

    def doCpyExit(self):
        self.cpytpm = False
        self.doCpyCloseProcess()

    def doCpyCloseProcess(self):
        self.cp.closeProcess()

    def doT0End(self):
        if self.newtpm:
            self.sql.insRec("tplmst", data=self.df.t_work[0][0])
        else:
            self.sql.updRec("tplmst", data=self.df.t_work[0][0],
                where=[("tpm_tname", "=", self.template)])
        self.df.selPage("Sequence")
        self.df.focusField("T", 1, 1)

    def doReSeq(self):
        whr = [("tpd_tname", "=", self.template)]
        acc = self.sql.getRec("tpldet", where=whr, order="tpd_detseq")
        self.sql.delRec("tpldet", where=whr)
        for seq, line in enumerate(acc):
            rec = list(line)
            rec[1] = float(seq + 1)
            self.sql.insRec("tpldet", data=rec)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doImport(self):
        self.df.setWidget(self.df.mstFrame, "hide")
        sel = FileDialog(parent=self.opts["mf"].body, title="Import File",
            initd=self.opts["mf"].rcdic["wrkdir"],
            ftype=[("Template", "*.tpl")])
        nam = sel.askopenfilename()
        self.df.setWidget(self.df.mstFrame, "show")
        if nam:
            fle = open(nam, "r")
            for line in fle:
                dat = line.split("|")
                if dat[0] == "0":
                    chk = self.sql.getRec("tplmst",
                        where=[("tpm_tname", "=", dat[1])], limit=1)
                    if chk:
                        showError(self.opts["mf"].body, "Invalid Import",
                            "This Template Already Exists")
                        self.df.focusField(self.df.frt, self.df.pag, 1)
                        return
                    self.sql.insRec("tplmst", data=dat[1:])
                else:
                    self.sql.insRec("tpldet", data=dat[1:])
        self.opts["mf"].dbm.commitDbase()
        showInfo(self.opts["mf"].body, "Import",
            "The Template has been Imported.")
        self.df.focusField(self.df.frt, self.df.pag, 1)

    def doExport(self):
        fle = open(os.path.join(self.opts["mf"].rcdic["wrkdir"], "%s.tpl" %
            self.template), "w")
        ttt = open(os.path.join(self.opts["mf"].rcdic["wrkdir"], "%s.txt" %
            self.template), "w")
        mst = self.sql.getRec("tplmst", where=[("tpm_tname", "=",
            self.template)], limit=1)
        mes = "0"
        txt = ""
        for x in mst:
            mes = "%s|%s" % (mes, str(x))
            if not txt:
                txt = 'mst = [\n        ["%s"' % x
            else:
                txt += ', "%s"' % x
        fle.write("%s\n" % mes)
        ttt.write("%s]]\n" % txt)
        det = self.sql.getRec("tpldet", where=[("tpd_tname", "=",
            self.template)], order="tpd_detseq")
        for n, x in enumerate(det):
            mes = str(n + 1)
            txt = ""
            for c, y in enumerate(x):
                typ = self.sql.tpldet_dic[self.sql.tpldet_col[c]][2]
                mes = "%s|%s" % (mes, str(y))
                if typ[1].upper() in ("A", "V", "W", "X"):
                    if not txt:
                        if x == det[0]:
                            ttt.write("det = [\n")
                            txt = '        ["%s"' % y
                        else:
                            txt = '        ["%s"' % y
                    else:
                        chk = '%s, "%s"' % (txt, y)
                        if len(chk) > 76:
                            ttt.write("%s,\n" % txt)
                            txt = '            "%s"' % y
                        else:
                            txt = chk
                elif not txt:
                    if x == det[0]:
                        ttt.write("det = [\n")
                    txt = "        [%s" % y
                else:
                    chk = '%s, %s' % (txt, y)
                    if len(chk) > 76:
                        ttt.write("%s,\n" % txt)
                        txt = '            %s' % y
                    else:
                        txt = chk
            fle.write("%s\n" % mes)
            if x == det[-1]:
                ttt.write("%s]]\n" % txt)
            else:
                ttt.write("%s],\n" % txt)
        fle.close()
        ttt.close()
        showInfo(self.opts["mf"].body, "Export",
            "The Template has been Exported to:\n\n%s" %
            self.opts["mf"].rcdic["wrkdir"])
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doPrint(self):
        self.df.setWidget(self.df.topEntry[self.df.pag][self.df.pos],
            "disabled")
        table = ["tpldet"]
        heads = ["Template %s Details" % self.template]
        state = self.df.disableButtonsTags()
        self.df.setWidget(self.df.mstFrame, state="hide")
        RepPrt(self.opts["mf"], name="tp1010", tables=table, heads=heads,
            where=[("tpd_tname", "=", self.template)],
            order="tpd_detseq asc", prtdia=(("Y","V"), None))
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.enableButtonsTags(state=state)
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doView(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        self.frm = DrawForm(self.opts["mf"].dbm, self.template,
            wrkdir=self.opts["mf"].rcdic["wrkdir"])
        self.frm.doNewDetail()
        self.frm.add_page()
        for key in self.frm.newkey:
            line = self.frm.newdic[key]
            if line[self.sql.tpldet_col.index("tpd_type")] in ("C", "I"):
                mrgcod = line[self.sql.tpldet_col.index("tpd_mrgcod")]
            else:
                mrgcod = ""
            if mrgcod:
                dat = self.doGetData(mrgcod, line)
            else:
                dat = line[self.sql.tpldet_col.index("tpd_text")]
            if not dat:
                if line[self.sql.tpldet_col.index("tpd_type")] == "I":
                    line[self.sql.tpldet_col.index("tpd_type")] = "R"
                    dat = "Image"
                else:
                    dat = " "
            line[self.sql.tpldet_col.index("tpd_text")] = dat
            self.frm.doDrawDetail(line, fmat=False)
        pdfnam = os.path.join(self.opts["mf"].rcdic["wrkdir"], "test.pdf")
        self.frm.output(pdfnam, "F")
        ViewPDF(self.opts["mf"], pdfnam)
        self.opts["mf"].window.deiconify()
        self.df.setWidget(self.df.mstFrame, state="show")
        self.df.focusField(self.df.frt, self.df.pag, self.df.col)

    def doGetData(self, mrgcod, line):
        lines = line[self.sql.tpldet_col.index("tpd_lines")]
        chars = line[self.sql.tpldet_col.index("tpd_mrg_chrs")]
        if not self.frm.tptp[mrgcod][1]:
            txt = "X" * chars
        if lines > 1:
            text = ""
            for x in range(lines):
                text = "%s%s\n" % (text, txt)
            return text
        else:
            return txt

    def doDelDet(self):
        if self.newdet:
            showError(self.opts["mf"].body, "Invalid Delete Request",
                "You can only delete Existing template lines.")
            return
        self.sql.delRec("tpldet", where=[("tpd_tname", "=", self.template),
            ("tpd_detseq", "=", self.detseq)])
        self.df.clearFrame("T", 1)
        self.df.focusField("T", 1, 1)
        return "nf"

    def doT1End(self):
        for x in range(2, 7):
            self.df.clearFrame("T", x)
        pag = self.pags.index(self.dtype)
        self.doLoadTypes()
        for i, f in enumerate(self.flds):
            if self.newdet:
                if self.sql.tpldet_dic[f][2][1].lower() in ("a", "x"):
                    data = ""
                else:
                    data = 0
            else:
                data = self.tpldet[self.sql.tpldet_col.index(f)]
            self.df.loadEntry("T", pag, i, data=data)
            setattr(self, "%s" % f.split("tpd_")[1], data)
        self.df.selPage(self.df.tags[pag - 1][0])
        self.df.focusField("T", pag, 1)

    def doT2End(self):
        self.doLoadTypes()
        data = [self.template, self.detseq, self.dtype, self.place]
        for num, col in enumerate(self.sql.tpldet_col):
            if num < 4:
                continue
            if col in self.flds:
                pag = self.pags.index(self.dtype)
                data.append(self.df.t_work[pag][0][self.flds.index(col)])
            elif self.sql.tpldet_dic[col][2][1].lower() in ("a", "x"):
                data.append("")
            else:
                data.append(0)
        if not self.newdet:
            self.doDelDet()
        self.sql.insRec("tpldet", data=data)
        self.df.selPage("Sequence")
        if self.newdet:
            self.df.loadEntry("T", 1, 0, data=(self.detseq + 1))
        else:
            self.df.clearEntry("T", 1, 1)
        self.df.clearEntry("T", 1, 2)
        self.df.focusField("T", 1, 1)

    def doLoadTypes(self):
        for x in range(6):
            self.df.disableTag(x)
        if self.dtype == "I":
            self.flds = self.image_flds
        elif self.dtype == "L":
            self.flds = self.line_flds
        elif self.dtype == "R":
            self.flds = self.rect_flds
        elif self.dtype == "T":
            self.flds = self.text_flds
        elif self.dtype == "C":
            self.flds = self.code_flds

    def doGetWidth(self, data, font, size, bold, pad=0):
        if type(data) == str:
            chrs = len(data)
        else:
            chrs = data
        style = "normal"
        if bold == "Y":
            style = "bold"
        txt = tkfont.Font(family=font, size=size, weight=style)
        width = (txt.measure("X"*(chrs+pad)) / 96) * 25.4
        if width % 1:
            width = int(width) + 1
        else:
            width = int(width)
        return width

    def doT0Exit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doT1Exit(self):
        if not self.nochg:
            self.opts["mf"].dbm.commitDbase(ask=True, mess="Save All Changes?")
        self.df.focusField("T", 0, 1)

    def doT2Exit(self):
        self.df.selPage("Sequence")
        self.df.focusField("T", 1, 3)

    def doReadDet(self, template, detseq):
        return self.sql.getRec("tpldet", where=[("tpd_tname", "=",
            template), ("tpd_detseq", "=", detseq)], limit=1)

# vim:set ts=4 sw=4 sts=4 expandtab:
