Control
-------
System Record Maintenance
.........................
This routine is used to create or amend a system control record by entering the following:

+ **Years to Keep History** - Enter the number of years that historical data must be retained. Enter a 0 for infinity.
+ **Enforce Passwords** - Select Yes or No.
+ **Minimum Characters** - If you elected to enforce passwords enter the minimum number of characters that the passwords must consist of.
+ **Maximum Life (Days)** - If you elected to enforce passwords enter the maximum number of days that the passwords will be valid for.
+ **Backup History (Days)** - Enter the maximum number of days that backups will be retained. Enter 0 for infinity.
+ **SMTP Server** - If you have email then enter your SMTP server's address e.g. smtp.mweb.co.za or smtp.saix.net or smtp.vodacom.co.za
+ **SMTP Security** - Select the appropriate security method.
+ **SMTP Authentication** - Select the appropriate authentication method.
+ **SMTP Port Number** - Select the appropriate smtp port number.
+ **SMTP Username** - If your smtp server requires a username enter it here.
+ **SMTP Password** - If your smtp server requires a password enter it here.
+ **SMS Service** - Select Yes or No. In order to use the SMS facility. You will first have to register with www.smsportal.co.za in order to get a username and password.
+ **SMS Username** - Enter the user name for the service.
+ **SMS Password** - Enter the password for the service.
+ **G/L Departments** - Whether to allow departmental financial reporting.
+ **Number of Digits** - The number of digits the department code uses in the account numbers i.e. if you enter 3 then the first 3 digits of the 7 digit account number will be reserved for the department code.

Company Records Maintenance
...........................
This routine is used to create or amend company records, at least one company record, number 1, must be created.

While most of the fields are self explanatory the following are of note:

+ **E-Mail Address** - The company's default email address.
+ **V.A.T. Default** - Any alphanumeric character. If the code, except **N** which is used for no V.A.T., has not previously been created you will be prompted to create one as in `V.A.T. Records Maintenance`_.
+ **Systems** - You must tick all the systems that you would like to enable otherwise they will not appear on your menu.
+ **Logo** - You can select an image file to be used as the letterhead for invoices, statements and remittance advices. this file should be a jpg file.

After creating a **new** company record you will be prompted for the initial financial period's starting and ending dates e.g. 20060301 and 20070228.

Department Records Maintenance
..............................
Use this routine to create department records if departments were enabled in the Systems Record.

+ **Department** - The department code.
+ **Name** - The name of the department.

Module Passwords Maintenance
............................
Use this routine to set passwords to override certain security limitations e.g. locked general ledger account, inhibit the sale of items at prices under cost or inhibit sales to a debtor exceeding their credit limit.

+ **Company** - Enter the company number or 0 for all companies.
+ **System** - The relevant system code. F1 will show all system codes.
+ **Code** - The relevant restrictions code. F1 will show existing overrides and the `All Codes` button will show all available restrictions.
+ **Password** - The password required to override this restriction.

**Examples**

.. csv-table::
  :header: "System", "Code", "Description"
  :widths: 6, 20, 50

  "MST", "TarBck", "Allow Database Backup"
  "MST", "TarRes", "Allow Database Restore"

Module Passwords Listing
........................
Use this routine to produce a report of the modules and passwords created using `Module Passwords Maintenance`_.

V.A.T. Records Maintenance
..........................
Use this routine to create, amend or delete value added tax records. Please note that you can have multiple rate records for a code e.g. Code 'I' could have a rate record starting at 2014/01/01 @ 14% and another one starting at 2016/01/01 @ 15% etc. The system will then automatically apply the correct rate depending on the transaction date of entries.

+ **V,A.T. Code** - A single character V.A.T. code.
+ **Description** - A description of the code.
+ **Category** - The category of the code as follows:

    + **C** for Capital Items
    + **N** for Non Vattable Items
    + **S** for Standard V.A.T. Codes
    + **X** for X Rated Items
    + **Z** for Zero Rated Items

+ **Date** - The starting date of the current or new rate.
+ **Rate** - The current or new rate.

The following buttons are applicable:

+ **Print** - Click this button to produce a report of all codes.
+ **Add** - Use this button to add additional rate records.
+ **Edit** - Use this button to edit existing codes and or rates. Please note that no codes or dates can be modified if any transactions have already been created using the code.
+ **Exit** - Use this button to exit the selected code.

V.A.T. Statement
................
Use this routine to produce a value added tax statement for a specific period.

Enter all relevant details according to the prompts. The following fields need more explanation:

+ **Starting Period** - Enter the starting period or 0 to take all unflagged transactions into account.
+ **Flag Items as Paid** - This option is only available if the `Starting Period` is 0. If you select `Yes` then all transactions will be flagged as paid with the date in the next field. To reprint a previous report select `Reprint` with the date to be reprinted in the `Payment Date` field.

Email Log Report
................
Use this routine to print a report of emails sent by the system.

+ **Date From** - Enter the starting date or Enter for beginning of file.
+ **Date To** - Enter the cut-off date or Enter for end of file.
+ **Recipient** - Enter the recipient's email address or Enter for all.
+ **Date Order** - Select the date order of the report details.

Changes Log Report
..................
Use this routine to print a report of all changes effected on masterfile records.

+ **Date From** - Enter the starting date or Enter for beginning of file.
+ **Date To** - Enter the cut-off date or Enter for end of file.
+ **Table Name** - Enter the table name or Enter for all tables.
+ **User Login** - Enter the user login or Enter for all users.

Application Usage Report
........................
Use this routine to print a report of applications usage history.

+ **Date From** - Enter the starting date or Enter for beginning of file.
+ **Date To** - Enter the cut-off date or Enter for end of file.
+ **User Name** - Enter the user's name or Enter for all.
+ **Module** - Enter the module code or Enter for all.
+ **Date Order** - Select the date order of the report details.

Financial Year End Routine
..........................
Use this routine to end a financial period. This will create opening balances in the next financial period and if you elect to Finalise the period it will disable any further postings to the applicable period and any previous periods.

Change Year End Date
....................
Use this routine to change the financial year end date from a specific period.
