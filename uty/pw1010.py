"""
SYNOPSIS
    User Administration with ssh, paramiko and crypt.

    Please remember to allow root access in /etc/ssh/sshd_config as follows:

        AllowUsers root@192.168.1.* ..... (any other users)

    This file is part of Tartan Systems (TARTAN).

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

import random
try:
    import crypt
    CRYPT = True
except:
    CRYPT = False
if CRYPT:
    try:
        import paramiko
    except:
        CRYPT = False
from TartanClasses import TartanDialog
from tartanFunctions import askQuestion, showError

class pw1010(object):
    def __init__(self, **opts):
        self.opts = opts
        if not CRYPT:
            showError(self.opts["mf"].body, "Missing Module",
                "Either the CRYPT or PARAMIKO module is Missing")
        else:
            self.setVariables()
            self.mainProcess()
            self.opts["mf"].startLoop()

    def setVariables(self):
        self.saltchrs = "abcdefghijklmnopqrstuvwxyz"\
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"\
                        "0123456789./"
        self.server = self.opts["mf"].rcdic["dbhost"]
        self.client = None
        random.seed()

    def mainProcess(self):
        tit = ("User Administration",)
        r1s = (("Mail", "M"), ("Client", "C"))
        fld = (
            (("T",1,0,0),"ITX",50,"Server","",
                self.server,"N",self.doServer,None,None,("notblank",)),
            (("T",1,1,0),"ITX",20,"Admin Name","",
                "root","N",self.doAdmNam,None,None,("notblank",)),
            (("T",1,1,0),"IHA",20,"Password","",
                "","N",self.doAdmPwd,None,None,("notblank",)),
            (("T",2,0,0),"ITX",50,"User Name","",
                "","N",self.doUsrNam,None,None,("notblank",)),
            (("T",2,1,0),("IRB",r1s),0,"Type of Account","",
                "M","N",self.doUsrTyp,None,None,None),
            (("T",2,2,0),"IHA",20,"New Password","",
                "","N",self.doNewPwd,None,None,("notblank",)),
            (("T",2,3,0),"IHA",20,"Check Password","",
                "","N",self.doCheckPwd,None,None,("notblank",)))
        but = (
            ("New",None,self.doNew,0,None,None),
            ("Amend",None,self.doAmend,0,None,None),
            ("Delete",None,self.doDelete,0,None,None),
            ("Quit",None,self.doQuit,0,None,None))
        tag = (("Server",None,None,None), ("Accounts",None,None,None))
        tnd = (None, (self.doEnd,"n"), (self.doEnd,"y"))
        txt = (None, self.doExit, self.doExit)
        self.df = TartanDialog(self.opts["mf"], tops=True, title=tit, tags=tag,
            eflds=fld, butt=but, tend=tnd, txit=txt, focus=True)

    def doNew(self):
        self.opt = "N"
        self.df.focusField("T", 2, 1)

    def doAmend(self):
        self.opt = "A"
        self.df.focusField("T", 2, 1)

    def doDelete(self):
        self.opt = "D"
        self.df.focusField("T", 2, 1)

    def doServer(self, frt, pag, r, c, p, i, w):
        self.server = w

    def doAdmNam(self, frt, pag, r, c, p, i, w):
        self.admnam = w

    def doAdmPwd(self, frt, pag, r, c, p, i, w):
        self.admpwd = w
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.server, username=self.admnam,
                password=self.admpwd)
        except:
            showError(self.opts["mf"].body, "SSH Error",
                "Cannot Open the Connection")
            return "ff1"

    def doUsrNam(self, frt, pag, r, c, p, i, w):
        self.usrnam = w
        self.usrpwd = None
        for x in range(4):
            wid = getattr(self.df, "B%s" % x)
            self.df.setWidget(wid, state="disabled")
        if self.opt == "A":
            return "sk1"
        if self.opt == "D":
            return "nd"

    def doUsrTyp(self, frt, pag, r, c, p, i, w):
        self.usrtyp = w

    def doNewPwd(self, frt, pag, r, c, p, i, w):
        self.usrpwd = w

    def doCheckPwd(self, frt, pag, r, c, p, i, w):
        if w != self.usrpwd:
            return "Passwords Do Not Agree"
        self.usrpwd = crypt.crypt(w, random.choice(self.saltchrs) +
            random.choice(self.saltchrs))

    def doEnd(self):
        if self.df.pag == 1:
            self.df.selPage("Accounts")
            for x in range(4):
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, state="normal")
            self.opts["mf"].updateStatus("Click the Required Option Button")
            self.df.setWidget(self.df.topEntry[2][0], state="disabled")
            return
        if self.opt == "A":
            cmd = ["usermod -p %s %s" % (self.usrpwd, self.usrnam)]
        elif self.opt == "D":
            ask = askQuestion(self.opts["mf"].body, "Remove Directory",
                "Must the User's Home Directory Also be Deleted", default="no")
            if ask == "yes":
                cmd = ["userdel -r %s" % self.usrnam]
            else:
                cmd = ["userdel %s" % self.usrnam]
        elif self.opt == "N":
            cmd = [
                "useradd -g users -m %s -p %s" % (self.usrnam, self.usrpwd)]
            if self.usrtyp == "M":
                cmd.extend([
                    "cp -r /etc/skel/Maildir /home/%s/" % self.usrnam,
                    "maildirmake /home/%s/.maildir" % self.usrnam,
                    "chown -R %s:users /home/%s" % (self.usrnam, self.usrnam),
                    "chmod -R 700 /home/%s/Maildir" % self.usrnam])
        err = self.executeCommand(cmd)
        if err:
            showError(self.opts["mf"].body, "SSH Error", err)
        self.doExit()

    def executeCommand(self, cmd):
        err = ""
        for c in cmd:
            try:
                chan = self.client.get_transport().open_session()
                chan.get_pty()
                try:
                    if self.admnam != "root":
                        chan.exec_command("sudo %s\n" % c)
                        if chan.recv(4096).count("password"):
                            chan.send("%s\n" % self.admpwd)
                    else:
                        chan.exec_command("%s\n" % c)
                except:
                    err = "%s\n%s" % (err,
                        "ERROR: Failed to Run Command %s" % c)
                chan.close()
            except:
                err = "Failed to Open a Channel to the Server"
        return err

    def doExit(self):
        if self.df.pag == 2:
            self.df.clearFrame("T", 2)
            for x in range(4):
                wid = getattr(self.df, "B%s" % x)
                self.df.setWidget(wid, state="normal")
            self.opts["mf"].updateStatus("Click the Required Option Button")
            self.df.setWidget(self.df.topEntry[2][0], state="disabled")
            return
        self.doQuit()

    def doQuit(self):
        if self.client:
            self.client.close()
        self.df.closeProcess()
        self.opts["mf"].closeLoop()

# vim:set ts=4 sw=4 sts=4 expandtab:
