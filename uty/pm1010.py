"""
SYNOPSIS
    Password Manager

    This file is part of Tartan Systems (TARTAN).

    pyaes or pycrypto is a dependancy.

AUTHOR
    Written by Paul Malherbe, <paul@tartan.co.za>

COPYING
    Copyright (C) 2004-2025 Paul Malherbe.

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

import csv, os, shutil, struct, sys
from TartanClasses import MyFpdf, TartanDialog
from tartanFunctions import askChoice, askQuestion, doPrinter
from tartanFunctions import showError, showInfo
try:
    import pyaes
    PYAES = True
except:
    PYAES = False
try:
    from Crypto.Cipher import AES
    PYCRYPT = True
except:
    PYCRYPT = False

class pm1010(object):
    def __init__(self, **opts):
        if PYAES:
            self.opts = opts
            self.setVariables()
            self.getSecret()
            if self.ecb or self.ctr:
                self.mainProcess()
                self.opts["mf"].startLoop()
        else:
            showError(opts["mf"].body, "Error", "Missing pyaes Module")

    def setVariables(self):
        self.ecb = None
        self.ctr = None
        self.change = False
        home = os.path.expanduser("~")
        if sys.platform == "win32":
            self.flenam = os.path.join(home, "secrets.dat")
        else:
            self.flenam = os.path.join(home, ".secrets.dat")
        self.show = "*"

    def getSecret(self):
        tit = ("Secret Word",)
        if self.change:
            fld = [
                (("T",0,0,0),"IHA",32,"Old Secret Word","",
                    "","N",self.doSecret,None,None,("notblank",)),
                (("T",0,1,0),"IHA",32,"New Secret Word","",
                    "","N",self.doSecret,None,None,("notblank",))]
        else:
            fld = [
                (("T",0,0,0),"IHA",32,"Secret Word","",
                    "","N",self.doSecret,None,None,("notblank",))]
        if self.change:
            but = None
            tnd = ((self.doEndSecret,"y"), )
        else:
            but = (
                ("Change",None,self.doChange,0,("T",0,1),("T",0,2)),
                ("Exit",None,self.doExitSecret,0,("T",0,1),("T",0,2)))
            tnd = ((self.doEndSecret,"n"), )
        txt = (self.doExitSecret,)
        self.sw = TartanDialog(self.opts["mf"], tops=True, title=tit,
            eflds=fld, butt=but, tend=tnd, txit=txt)
        self.opts["mf"].startLoop()
        if self.change:
            self.change = False
            self.getSecret()

    def doSecret(self, frt, pag, r, c, p, i, w):
        self.doEncrypt(w)
        if self.change:
            if p == 0:
                self.doGetData()
            else:
                self.doWriteData()

    def doEncrypt(self, w):
        siz = len(w)
        if siz not in (16, 24, 32):
            if siz < 16:
                key = w + "*" * (16 - siz)
            elif siz < 24:
                key = w + "*" * (24 - siz)
            elif siz < 32:
                key = w + "*" * (32 - siz)
        self.key = key.encode()
        if PYCRYPT:
            self.ecb = AES.new(self.key, AES.MODE_ECB)
        if PYAES:
            self.ctr = pyaes.AESModeOfOperationCTR(self.key)

    def doChange(self):
        self.sw.closeProcess()
        self.change = True
        self.getSecret()

    def doEndSecret(self):
        self.doGetData()
        self.doExitSecret()

    def doExitSecret(self):
        self.sw.closeProcess()
        self.opts["mf"].closeLoop()

    def mainProcess(self):
        pwm = {
            "stype": "C",
            "titl": "Select the Secret to Change or <Esc> to Exit",
            "head": ("Code", "Clear-Text"),
            "typs": (("NA", 30, "Y"), ("NA", 50)),
            "data": self.doLoadCodes()}
        fld = (
            (("T",0,0,0),"INA",30,"Code","",
                "","Y",self.doCode,pwm,None,("notblank",)),
            (("T",0,1,0),"INA",50,"Clear-Text","Clear Text",
                "","N",self.doClear,None,self.doDelete,("efld",)),
            (("T",0,2,0),"IHA",50,"Encrypted-Text","Encrypted Text",
                "","N",self.doEncrypted,None,None,("efld",)))
        but = (
            ("Export",None,self.doExport,0,("T",0,1),("T",0,2)),
            ("Toggle",None,self.doShow,1,None,None),
            ("Print",None,self.doPrint,1,None,None),
            ("Quit",None,self.doQuit,1,None,None))
        tnd = ((self.doEnd,"y"), )
        txt = (self.doExit, )
        self.df = TartanDialog(self.opts["mf"], eflds=fld, butt=but,
            tend=tnd, txit=txt)

    def doCode(self, frt, pag, r, c, p, i, w):
        self.code = w
        if self.code not in self.data[self.opts["capnm"]]:
            self.data[self.opts["capnm"]][self.code] = ["", ""]
        self.login = self.data[self.opts["capnm"]][self.code][0]
        self.encrypt = self.data[self.opts["capnm"]][self.code][1]
        self.df.loadEntry(frt, pag, p+1, data=self.login)
        self.df.topEntry[pag][p+1].configure(state='normal')
        self.df.loadEntry(frt, pag, p+2, data=self.encrypt)
        self.df.topEntry[pag][p+2].configure(state='normal')

    def doClear(self, frt, pag, r, c, p, i, w):
        self.login = w

    def doEncrypted(self, frt, pag, r, c, p, i, w):
        self.encrypt = w

    def doQuit(self):
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doExport(self):
        self.df.setWidget(self.df.mstFrame, state="hide")
        typ = askChoice(self.opts["mf"].window, "Type", "Select the File Type",
            butt=(
                ("CSV", "C", "Export to a csv file for Importing "\
                    "into e.g. 'Password Safe'"),
                ("XML", "X", "Export to a xml file for Importing "\
                    "into e.g. 'KeePassX'")), default="CSV")
        self.df.setWidget(self.df.mstFrame, state="show")
        if typ == "C":
            fle = os.path.join(self.opts["mf"].rcdic["wrkdir"], "secrets.csv")
            csvwrt = csv.writer(open(fle, "w"), delimiter=";", quotechar='"',
               quoting=csv.QUOTE_MINIMAL)
            csvwrt.writerow(["Title", "Category", "Username", "Password",
                "Website","Comments"])
        else:
            fle = os.path.join(self.opts["mf"].rcdic["wrkdir"], "secrets.xml")
            xml = open(fle, "w")
            xml.write("""<!DOCTYPE KEEPASSX_DATABASE>
<database>
 <group>
  <title>Secrets</title>
  <icon>0</icon>""")
        codes = list(self.data[self.opts["capnm"]].keys())
        codes.sort()
        for code in codes:
            log, enc = self.data[self.opts["capnm"]][code]
            log = log.replace("&", "and").replace("<", "").replace(">","")
            enc = enc.replace("&", "and").replace("<", "").replace(">","")
            if typ == "C":
                csvwrt.writerow([code, "", log, enc, "", ""])
            else:
                xml.write("""
  <entry>
   <title>%s</title>
   <username>%s</username>
   <password>%s</password>
   <url></url>
   <comment></comment>
   <icon>0</icon>
   <creation>0</creation>
   <lastaccess>0</lastaccess>
   <lastmod>0</lastmod>
   <expire>Never</expire>
  </entry>""" % (code, log, enc))
        if typ == "X":
            xml.write("""
 </group>
</database>""")
            xml.close()
        showInfo(self.opts["mf"].body, "Export",
            """The following file has been created:

%s

Please Note that this file is Unencrypted.

This file will be treated as a Temporary File when Exiting Tartan.""" % fle)
        self.df.focusField("T", 0, 1)

    def doShow(self):
        if not self.show:
            self.show = "*"
        else:
            self.show = ""
        self.df.topEntry[0][2].configure(show=self.show)
        self.df.focusField("T", 0, self.df.col)

    def doPrint(self):
        self.fpdf = MyFpdf(name="pm1010", head=133, auto=True)
        self.fpdf.header = self.doHead
        self.fpdf.add_page()
        codes = list(self.data[self.opts["capnm"]].keys())
        codes.sort()
        for count, code in enumerate(codes):
            self.fpdf.drawText(code, w=31*self.fpdf.cwth, align="L",
                border="TLRB", ln=0)
            data = self.data[self.opts["capnm"]][code]
            for num, text in enumerate(data):
                if len(text) > 50:
                    ctyp = "M"
                else:
                    ctyp = "S"
                self.fpdf.drawText(text, w=51*self.fpdf.cwth, align="L",
                    border="TLRB", ctyp=ctyp, ln=num)
        if self.fpdf.saveFile("secrets.pdf", self.opts["mf"].window):
            doPrinter(mf=self.opts["mf"], pdfnam="secrets.pdf", splash=False,
                repprt=["N", "V", "view"])
        os.remove("secrets.pdf")

    def doHead(self):
        self.fpdf.setFont("Arial", "B", 15)
        self.fpdf.drawText("Information and Passwords for %s" %
            self.opts["capnm"], align="C")
        self.fpdf.drawText()
        self.fpdf.setFont("")
        for text in (("Description",31), ("Text",51), ("Secrets",51)):
            self.fpdf.drawText(text[0], w=text[1]*self.fpdf.cwth, align="L",
                border="TLRB", fill=True, ln=0)
        self.fpdf.drawText()

    def doDelete(self):
        del self.data[self.opts["capnm"]][self.code]
        self.df.topf[0][0][8]["data"] = self.doLoadCodes()
        self.df.focusField("T", 0, 1)

    def doEnd(self):
        if not self.show:
            self.doShow()
        self.data[self.opts["capnm"]][self.code] = [self.login, self.encrypt]
        self.df.topf[0][0][8]["data"] = self.doLoadCodes()
        self.df.focusField("T", 0, 1)

    def doLoadCodes(self):
        data = []
        codes = list(self.data[self.opts["capnm"]].keys())
        codes.sort()
        for code in codes:
            login, encrypt = self.data[self.opts["capnm"]][code]
            data.append((code, login))
        return data

    def doGetData(self):
        self.data = {}
        if os.path.isfile(self.flenam):
            codes = ["User", "Code", "Clear", "Fill"]
            of = open(self.flenam, "r")
            dt = of.readlines()
            if dt[0].endswith("Encrypt\n"):
                if not PYCRYPT:
                    self.doExit(ask=False)
                else:
                    self.cvt = False
                    codes.append("Encrypt")
            elif not PYAES:
                self.doExit(ask=False)
            else:
                self.cvt = True
                codes.append("EncryptCTR")
            for line in dt:
                data = []
                for code in codes:
                    f = len("Start%s" % code) + line.find("Start%s" % code)
                    t = line.find("End%s" % code)
                    data.append(line[f:t])
                user = data[0]
                if user not in self.data:
                    self.data[user] = {}
                code = data[1]
                login = data[2]
                fill = int(data[3])
                chrs = data[4].split(",")
                if not chrs[0]:
                    encrypt = ""
                else:
                    txt = b""
                    for c in chrs:
                        txt += struct.pack("B", int(c))
                    if self.cvt:
                        encrypt = self.ctr.decrypt(txt).decode("latin-1")
                    else:
                        encrypt = self.ecb.decrypt(txt).decode("latin-1")
                    if fill:
                        encrypt = encrypt[:-fill]
                self.data[user][code] = [login, encrypt]
        if self.opts["capnm"] not in self.data:
            self.data[self.opts["capnm"]] = {}

    def doExit(self, ask=True):
        if ask:
            ok = askQuestion(self.opts["mf"].body, "Save Changes",
                "Would you like to SAVE All Changes?", default="yes")
            if ok == "yes":
                self.doWriteData()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

    def doWriteData(self):
        ctr = pyaes.AESModeOfOperationCTR(self.key)
        if os.path.isfile(self.flenam):
            shutil.copy(self.flenam, self.flenam + "~")
        of = open(self.flenam, "w")
        users = list(self.data.keys())
        users.sort()
        for user in users:
            for code in self.data[user]:
                login = self.data[user][code][0]
                encrypt = self.data[user][code][1]
                fill = 16 - (len(encrypt) % 16)
                if fill:
                    encrypt = "%s%s" % (encrypt, ("*" * fill))
                hsh = ctr.encrypt(encrypt).decode("latin-1")
                txt = ""
                for n, c in enumerate(hsh):
                    if not n:
                        txt = ord(c)
                    else:
                        txt = "%s,%s" % (txt, ord(c))
                of.write(
                    "StartUser%sEndUser"\
                    "StartCode%sEndCode"\
                    "StartClear%sEndClear"\
                    "StartFill%sEndFill"\
                    "StartEncryptCTR%sEndEncryptCTR\n" % \
                    (user, code, login, fill, txt))
        of.close()

if __name__ == "__main__":
    import getopt, getpass
    from TartanClasses import MainFrame
    from tartanFunctions import loadRcFile
    try:
        opts, args = getopt.getopt(sys.argv[1:],"r:")
    except:
        print("")
        print("Usage: -r rcfile")
        print("")
        sys.exit()
    if opts:
        rcdic = loadRcFile(opts[0][1])
    else:
        rcdic = loadRcFile()
    mf = MainFrame(rcdic=rcdic)
    try:
        pm1010(**{"mf": mf, "capnm": getpass.getuser()})
    except:
        pass

# vim:set ts=4 sw=4 sts=4 expandtab:
