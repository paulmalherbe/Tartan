==================================
 Tartan Systems - Reference Manual
==================================
.. _GPL: http://www.gnu.org/licenses/gpl.html

:Version:   6.2
:Author:    Paul Malherbe
:Contact:   paul@tartan.co.za
:Home:      http://www.tartan.co.za
:Copyright: Paul Malherbe (C) 2004-2021.
:Licence:   Free use of this software and all it's modules is granted under the terms of the GNU General Public License (GPL_) as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

:Note: This document is not intended as an accounting manual. It is primarily a manual for people with some accounting expertise to learn how to use Tartan as an accounting tool.

.. contents:: **Table of Contents**

About
-----
Tartan Systems started out in 1981 as a suite of programs I wrote in COBOL and until 1994 ran on various platforms including CPM, RSX11M, MSDOS, AT&T UNIX and SCO.

In 1994 I discovered LINUX and when iBCS2 became available I modified the systems to run under LINUX.

In 2003 I started looking around for another programming language in which I could rewrite the systems to run under LINUX, as well as Windows, as I was getting irritated with having to compile using SCO.

Eventually I decided on the following:

+ Python_ as the programming language
+ Tkinter_ for the graphical user interface
+ Reportlab_ to generate reports
+ Pychart_ to generate charts and graphs
+ PostgreSQL_ and SQLite3_ as supported relational databases

In 2005, version 3, I changed the graphical user interface to PyGtk, a python wrapper for the Gtk library.

In 2011, version 4, I dropped support for windows 9x and also replaced reportlab with pyfpdf.

In 2015, version 5, I replaced PyGtk with Tkinter and ttk.

In 2021, version 6, I upgraded to Python 3 and dropped support for MySQL and Firebird databases.

.. _Python: http://www.python.org
.. _Tkinter: http://www.python.org/topics/tkinter
.. _Reportlab: http://www.reportlab.org
.. _Pychart: http://www.hpl.hp.com/personal/Yasushi_Saito/pychart
.. _PostgreSQL: http://www.postgresql.org
.. _SQLite3: http://code.google.com/p/pysqlite

Installation Procedure
----------------------
Source
.......
Ensure that python is installed on your system:

+ python >= 3.5

The following dependencies must be installed using pip:

+ fpdf                  # Used to create all documents
+ pillow                # Used by fpdf and imaging
+ pymupdf               # Used for viewing pdf files
+ pywin32               # Windows only

Additionally, the following dependencies should also be installed using pip:

+ beepy                 # Used to play a notification sound
+ docutils              # Used to display licence
+ importlib             # Used to import modules
+ markdown              # Bulk Mail - Enable Markdown Format
+ ofxtools              # OFX File Reader - bank statements
+ openpyxl              # XLSX File Reader and Writer
+ progress              # Curses Progress Bar
+ pyaes                 # Password Manager - pm1010
+ pycryptodome          # Password Manager - pm1010
+ pyexcel               # XLS File Reader
+ pyexcel-ods           # ODS File Reader
+ pygal                 # SVG Charts
+ pysmb                 # Netbios File Names
+ requests              # Web Scraping
+ send2trash            # Move Files to Recycle Bin
+ svglib                # SVG to PDF File Converter
+ tkcolorpicker         # Alternative to colorchooser for Tkinter
+ tkinterhtml           # HTML Viewer

And, depending on your database needs:

+ Postgresql            # psycopg2-binary

Then download the following file from ftp://ftp.tartan.co.za

+ Tartan_6.x.tar.gz

Extract Tartan_6.x.tar.gz into a directory of your choice as follows:

+ cd your.directory && tar -xvzf Tartan_6.x.tar.gz

Tartan should now be installed on your computer and you can continue with the `Startup Procedure`_.

Windows Binary
..............
Download the applicable file from ftp://ftp.tartan.co.za or if you are in possession of a CD this is not necessary.

+ Tartan_6.x-XP.exe for Windows prior to Windows-10
+ Tartan_6.x-32.exe for Windows-10 32 bit architecture.
+ Tartan_6.x-64.exe for Windows-10 64 bit architecture.

Install Tartan by browsing to the downloaded file and double clicking and then accepting the defaults, except, agree to creating an icon on your desktop.

Tartan should now be installed on your computer and you can continue with the `Startup Procedure`_.

Startup Procedure
-----------------
Linux and Source
................
Start Tartan by entering the following command:

    `python -OO program_path/ms0000.py [options]`

To find out what the available command line options are, use the -h option.

Windows Binary
..............
Start Tartan by clicking on the shortcut icon on the desktop or by navigating to the `C:\\Tartan\\prg` directory and double clicking on the `ms0000[.exe]` file.

Both
....
The first time you run Tartan you will automatically be taken to `Preferences`_ where you will have to enter various parameters relating to your installation. After saving the preferences and restarting Tartan you will be prompted to create the database. Once the database has been created you will have to create the System record as per `System Record Maintenance`_ as well as a Company record as per `Company Records Maintenance`_.

Status Line
-----------
.. NOTE::
  When using Tartan your available options will be highlighted on the status line at the bottom left hand side of the screen. Please read this carefully before asking for assistance.

Common Keyboard Functions
-------------------------
Throughout the various modules comprising **Tartan Systems** the following keys are used to perform certain functions. These options will always be highlighted in the `Status Line`_ at the bottom of the screen. The most common ones are:

+ **Enter**  - Accept keyboard input.
+ **Esc**    - Exit a module or go to a previous entry field.
+ **F1**     - Record Selection used with most data input routines.
+ **F5**     - Record Deletion used with record maintenance routines.
+ **F9**     - Input Termination used with multi-line text input.

In addition to the above keys all underlined characters on notebook tags and buttons can be used, in conjunction with the <Alt> key, as shortcuts e.g <Alt-s> to open the System menu.

Common Routines
---------------
There are various common routines. Rather than continually describing them they will be described once here only.

User Validation
...............
If no users have been created using the `User's Maintenance`_ routine on the `System`_ menu and no password has been allocated to the **admin** user, the system will automatically log in using **admin** as the user name. In all other cases a user must log in by entering a valid name and password. If no password exists for the **admin** user a password should be created as soon as possible using the `Change Password`_ routine on the System_ menu.

Company Selection
.................
For every routine which is company specific and where you have more than 1 company, you will be required to select the relevant company. In some cases you will also have to enter a financial period. Please note that you will not always be prompted for the financial period as this only applies to routines which require it. Also note that for both selections there is a `F1 Record Selection` option as per `Common Keyboard Functions`_.

Batch Details
.............
Most data capture routines require you to enter batch details. The reason for a batch is ease of balancing and the resolution of errors made during data capture. After you exit a data capture routine a totals summary will be displayed. If there is a discrepancy between the expected and entered values all the various systems have a routine to print the batch details thus enabling you to determine where the error is and therefore to correct it.

+ **Batch Number** - Any 7 character unique alphanumeric code.
+ **Current Period (CCYYMM)** - The financial period of this batch.
+ **Number of Entries** - The total number of entries comprising this batch, if known, else 0.
+ **Value of Entries** - The total value of entries comprising this batch, if known, else 0.
+ **Multiple Date Allocations** - Whether or not the postings are to be allocated according to the transaction date and not the current period.
+ **Bank Control** - For all batches in general ledger and other systems integrated with the general ledger, that affect the bank accounts, enter the bank control code.

Ageing Transactions
...................
While capturing transactions for various systems you will be required to allocate the amount to existing outstanding transactions for ageing purposes.

There are four different methods of ageing a transaction:

+ **Normal** - This will display a list of all outstanding transactions on the account and you will be able to allocate at random until the full amount has been allocated.

    + Select a transaction to allocate against by either clicking on the required line or moving the cursor to the required line and hitting the `Enter` key.
    + Enter the allocation amount.
    + Accept the allocation amount by either clicking on the `Apply` button or by hitting the `Enter` key.
    + The amount will be allocated and the `Balance` will show the unallocated portion.
    + Continue these steps until the full amount has been allocated. In the event of a balance remaining which cannot be allocated, hitting the `Esc` key or clicking on the `Exit` button will exit the routine leaving the balance as unallocated.

+ **History** - This is identical to `Normal` above but the available transactions will include previously fully allocated ones thus enabling you to reallocate transactions.
+ **Automatic** - This will automatically allocate the amount against outstanding transactions, starting from the oldest transaction, until either the amount has been fully allocated or there are no more outstanding transactions in which case the balance will remain as unallocated.
+ **Current** - This will leave the full transaction as unallocated.

Printer Selection
.................
Whenever a report is being produced you will have the opportunity of deciding on the output method i.e. viewing, printing, exporting and, in some cases, whether or not to email it.  Please note that the option to email the report will only be available if there is a valid `SMTP Server` in the `System Record Maintenance`_ record.

+ **Output** - Select the required output option.
+ **Printer Name** - If you selected `Print`, enter the printer name.
+ **E-Mail Report** - If available, select whether or not to email the report.
+ **E-Mail Address** - If available, enter the email address, if more than one, comma separate them.
+ **E-Mail Message** - If available, enter the email message as well as any additional attachments, if any.

Tartan PDF Viewer
.................
If no external pdf viewer is entered in the preferences and pymupdf is installed the Tartan PDF viewer will be used.

+ **Goto** - This button will alow you to enter a page number.
+ **Zoom** - This button, depending on whether the left or right mouse button is pressed, will increase or decrease the font and page size.
+ **Menu** - This button will display a menu with the following options:
    + **Email** - This button, if available, will enable the emailing of the document:
        + **From Address** - The email address of the sender.
        + **To Address** - A comma separated list of receiving email addresses.
    + **Print** - This button wile open a print dialog screen.
    + **Save as..** - This button wail enable the saving of the document with a different/same name and/or a different directory.
    + **Send to..** - This button will open the document using the system default pdf viewer e.g. Acrobat.
    + **Help** - This button will display the various key bindings.
    + **Exit** - This button will close the viewer. Escape can also be used.

Error Messages
..............
Should an error message occur and there is a file named *errors.txt* in the `Work Path` as created in `Preferences`_. Please email the file to errors@tartan.co.za after which you may delete it.

Menus and Sub Menus
-------------------
Please note that depending on the system modules selected when creating the company records, as detailed in `Company Records Maintenance`_, and the security level of the user, some of the menus detailed below might not appear.

System
------
Please note that depending on the security level of the user some of these routines might not be available.

Change User
...........
Use this routine to change the current user. Selecting it will log the current user out and the new user can then log in as per `User Validation`_.

Change Password
...............
Select this routine to change the logged in user's password. The user can change the password by first entering the old password followed by the new password twice, for confirmation.

User's Maintenance
..................
Use this routine to create or amend user's records, permissions etc.

+ **User Name** - You must enter the user's login name. In the case of existing users the screen will be populated with existing data.
+ **Full Name** - The full name of the user.
+ **Email Address** - The email address of the user.
+ **Mobile Number** - The mobile number of the user.
+ **User Password** - It is not necessary to enter passwords as users must change their own using `Change Password`_, after logging in.
+ **Copy Existing User** - Use this to copy all permissions of an existing user.
+ **Valid Companies** - The valid company's field is for limiting a user's access to specific companies and is a comma separated list of company numbers e.g. 1,2,3,4.
+ **Security Level** - The Security levels are as follows:

    + **0** - Enquiries Only
    + **1** - 0 plus Reporting
    + **2** - 1 plus Data Capture
    + **3** - 2 plus File Maintenance
    + **4** - 3 plus Month End Routines
    + **5** - 4 plus Control Routines
    + **6** - 5 plus Financial Year End Routine
    + **7** - 6 plus User and Module Password Maintenance
    + **8** - 7 plus Update File Formats
    + **9** - Supervisor level, Everything

+ The following fields are used to control which companies, systems and modules are available, only by password, to this user:

    + **Coy** - A company number or zero for all companies
    + **SS** - The system code
    + **Prog** - A program module or blank for all modules of a system
    + **Password** - The password. If the password is left blank it is the same as denying the selection i.e. The user will not be able to select the module(s).
    + **Check Password** - If the password is not blank then enter the password again for verification

**Examples**

.. csv-table::
  :header: "Coy", "SS", "Prog", "Password", "Meaning"
  :widths: 5, 5, 6, 10, 55

  "0", "gl", "    ", "    ", "All G/L modules for all companies would be denied."
  "0", "gl", "2032", "    ", "G/L payments data capture for all companies would be denied."
  "0", "gl", "    ", "abcd", "All G/L modules for all companies would require the password."
  "0", "gl", "2032", "abcd", "G/L payments data capture for all companies would require the password."

Upgrade System
..............
Select this routine to check if there are upgrades to Tartan and if so to install them.

+ **Update Type** - Select whether to check the Tartan ftp site or a local LAN location. If Local is selected you will be able to browse for a location which will default to whatever is set in the *Upgrade Path* directory as set during the `Preferences`_ routine.

* If there is an update and you want to upgrade, click on the `Update` button.

Update File Formats
...................
If you have performed an upgrade of Tartan you will have to perform this routine as well. This routine will automatically update all table formats in the database. If you have more than one database (rcfile), you must perform this routine for each database.

Copy Tables
...........
Use this routine to copy tables from one profile/database to another one.

+ **RC File From** - Enter the full path of the rcfile of the database to copy from.
+ **Whole Database** - Yes or No, If No is selected a list of tables will be displayed after confirmation. Tick all tables to be copied and then the Accept button.

Backup Database
...............
Select this routine to create a backup of the current database. These backups will reside in the *Backup Path* directory as created using the `Preferences`_ routine. Each backup will further reside in a sub directory named after the name of the database and a further sub directory named `arch`.

Restore Database
................
Select this routine to restore a previous backup.

+ **Type** - Select a Full or Partial restore.
+ **Archive** - Select the relevant archive to restore from.
+ **All Companies** - `Yes` or `Include/Exclude` some companies.
+ **Companies** - Comma separated list of companies to include or exclude.
+ **All Systems** - `Yes` or `Include/Exclude` some systems.
+ **Systems** - Comma separated list of systems to include or exclude.

Please note that unless you really know what you are doing it is very dangerous to restore individual systems as your data could become unbalanced because of integration and table relationships.

If you are doing a full restore and the database already exists you will be asked whether to drop it first. Unless you are sure of what you are doing select No.

Export Database
...............
Select this routine to export data to an external database in a chosen directory and name. The database name will default to *tartan001.db*. The word tartan will be replaced by the name of the source database name and the *001* will be replaced by the first company's number.

+ **Company(s)** - Select *Single* for a single company or *Multi* for multiple companies.
+ **Company Number** - Enter the single company number to export.

.. NOTE::
    If the selected company or companies is/are linked to other companies you will be asked if all linked companies should be exported.

+ **Directory** - Enter the directory where the exported file must be placed.
+ **Database Name** - Enter the name of the exported file or accept the default.

In order to use this exported database perform the following steps on the computer you will be using:

+ Copy the exported file to the target computer
+ Install Tartan on the target computer if it is not already installed
+ Execute Tartan with the following command:

    + c:\\Tartan\\prg\\ms0000.exe -r c:\\Tartan\\tartan001

+ You will now be in the Tartan Preferences Routine

    + Hit enter to accept the Configuration File e.g. tartan001
    + Hit enter to accept the Database Engine i.e. SQLite
    + Enter the Database Name i.e. the name of the exported file e.g. tartan001.db and hit enter.
    + Hit enter to accept the Host Name i.e. localhost
    + Enter the Files Directory i.e. the directory where the exported file has been copied to.
    + Click on the Save button and the the Close button.

+ The Tartan menu should now be displaying.
+ After exiting Tartan you can re-enter Tartan by executing the third step i.e. Execute Tartan with the following command:

Merge Database
..............
Select this routine to merge a database, that has been exported and worked on, back into the original database.

+ **Merge File** - Enter the full file path to the database file to be merged.

In order to merge the exported database perform the following steps on the original computer:

+ Copy the exported file to the original computer
+ Run Tartan and click on System --> Merge Database
+ Enter the Merge File. Use F1 to browse for the file.
+ At the end select whether to Commit all entries.

Preferences
...........
Use this routine to configure Tartan, however, depending on your security level, some of the options might not be available to you.

+ **Configuration File** - This is the full path of your configuration file. Every user can have his or her own file. This file, by default, is placed in the user's home directory or, in Windows, the root directory of the Tartan installation e.g. `C:\\Tartan`. If you want to change this default, you must set an environment variable as **TARTANRC=path-to-rcfile** or use the command line option **-r path-to-rcfile**.
+ **Database**
    + **Database Engine** - This is the database being used and must be one of PostgreSQL and SQLite. The recommended one for single-user installations is SQLite and PostgreSQL for multi-user installations.
    + **Database Name** - This can be any single word name which defaults to **tartan**.
    + **Files Directory** - This is only used for the SQLite database engine and is the directory where the database will be created.
    + **Host Name** - This is only used for PgSQL databases and is the host name of the Server which defaults to **localhost**.
    + **Port Number** - This is the port number to connect to the database. Leaving this blank will enable the default port.
    + **Administrator** - This is the name used to connect to the database.
    + **Password** - This is the password of the administrator.
+ **General**
    + **Backup Path** - This is the path where backups of the database will be stored.
    + **Work Path** - This is the path of the work directory. All temporary files will be created in this directory.
    + **Upgrade Path** - This is the path where any upgrades will be stored.
    + **PDF Viewer** - This is the full path of an External program used to display pdf files. The default is `Blank` for the built-in pdf viewer. Suggested programme for LINUX is **evince** and for Windows **SumatraPDF** or **Foxit Reader**.
    + **Print Command** - This is the full path of an External print program used to print pdf files. The default is `Blank` for the built-in pdf printer. Suggested LINUX default is **lpr** and Windows is **SumatraPDF**. Another recommended program for windows is **Foxit Reader**. If necessary use %p% for the printer name and %f% for the file name e.g. the print command for Sumatra could be `the-path-to\SumatraPDF.exe -print-to %p% %f%`.
    + **Spreadsheet Reader** - This is the full path of the program used to read xlsx, xls and csv files.
    + **Screen Geometry** - This defaults to the suggested geometry for your screen. Entering a zero will achieve the same result.
    + **Screen Placement** - Where the Tartan Window must be placed on the monitor i.e. Left, Centre or Right.
    + **Show Tartan Image** - Whether to display the Tartan image on the Main Menu screen.
    + **Enforce Confirm** - Whether confirmation is required on the completion of data entry.
    + **Auto-completion** - Whether auto-completion will be available. This means that as you enter data, and if there are available options, these will appear either `In-Line` or in a `List` below the entry field, for selection.
    + **Tool-tips** - Whether tool-tips will display as you hover your cursor over certain entry fields.
    + **Error Alarm** - Whether or not to sound an audible alarm with errors. This can be No, Yes or Multimedia. Use Multimedia if you do not have an internal speaker.
    + **Work Files** - Select the default action for work files when exiting Tartan.
        + **Trash** - Send the files to the *Recycle Bin*.
        + **Delete** - Delete the files.
        + **Keep** - Keep the files in the work directory.
+ **Dialog**
    + **Menu Font**
        + **Name** - This is the font family to be used for all menu items.
        + **Size** - This is font size to be used for all menu items.
    + **Default Font**
        + **Name** - This is the font family to be used in all other cases.
        + **Size** - This is font size to be used in all other cases.
    + **Theme** - The theme to be used. The default theme is `clam`.  To make more themes available download themes of your choice and install them in a folder named `thm` which must be in the Tartan root folder i.e. where the Tartan file ms0000.py or ms0000.exe resides.
    + **Colour Scheme** - The colour scheme to be used. The default scheme is `Red`.
    + **Normal**
        + **FG** - The normal label and button foreground colour.
        + **BG** - The normal label and button background colour.
    + **Focus**
        + **FG** - The focused button foreground colour.
        + **BG** - The focused button background colour.
    + **Disable**
        + **FG** - The disabled button foreground colour.
        + **BG** - The disabled button background colour.
    + **Booking Query**
        + **FG** - The booking manager calendar query foreground colour.
        + **BG** - The booking manager calendar query background colour.
    + **Booking Confirmed**
        + **FG** - The booking manager calendar confirm foreground colour.
        + **BG** - The booking manager calendar confirm background colour.
    + **Booking Settled**
        + **FG** - The booking manager calendar settle foreground colour.
        + **BG** - The booking manager calendar settle background colour.

|

If this is a new installation you will be prompted to Create the Database after which you will need to create a `System Record` and at least one `Company Record`.

Quit
....
Select this to exit Tartan.
