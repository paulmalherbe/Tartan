==============================
 Tartan Systems - Quick Start
==============================

Once Tartan Systems has been installed, the following procedures have to be performed before any meaningful work can be done. These procedures obviously depend on which modules are going to be used but this will be explained as we progress.

+ Start Tartan by either clicking on the icon on the desktop or from the command line as follows:

    + **Linux** - `program_path/ms0000.py [options]`
    + **Windows** - `program_path\\ms0000.exe [options]`

  To find out what the available command line options are, use the -h option.

+ The first time Tartan is started you will be taken to `Preferences` where you will have to set up your preferences regarding database, paths, utilities and various other choices. You will then have to enter the System record as well as a Company/Club record. For most SOHO installations there will only be one Company, however there is provision for up to 999 integrated companies. While creating the Company record you will be able to choose which systems you want to activate.

|

General Ledger
..............
If you are going to use the `General Ledger` you must perform the following procedures in order:

+ Create the chart of accounts using `File Maintenance -> Masterfile Records`.
    + Select the `Populate` button to automatically populate a company's set of accounts.
+ Create control accounts using `File Maintenance -> Control Accounts`.
+ Capture account's opening balances using `Data Caspture -> Opening Balances`.
+ Print a trial balance using `Reporting -> Trial Balance` and ensure that your accounts balance. If not, recapture the incorrect ones.
+ Capture budgets using `Data Capture -> Budgets`, if required.

The General Ledger system is at this stage fully functional and you can capture postings, produce basic reports and do interrogations etc.

Asset's Ledger
..............
If you are going to use the `Asset's Register` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ Create depreciation codes using `File Maintenance -> Depreciation Codes`.
+ Create group records using `File Maintenance -> Group Records`.
+ Create masterfile records and take on opening balances for existing assets using `Data Capture -> Opening Balances`.

The Asset's Register system is at this stage fully functional and you can capture payments, receipts and journal entries. Please note that new assets are captured via the data capture routines i.e. Payments and/or Journal Entries.

Bookings Manager
................
If you are going to use the `Booking's Manager` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ Create unit records using `File Maintenance -> Unit Records`.
+ Create rate records using `File Maintenance -> Rate Records`.
+ Create booking letters using `File Maintenance -> Booking Letters`.

The Booking's Manager system is at this stage fully functional and you can capture bookings and booking's movements.

Bowling Clubs
.............
If you are going to use `Bowling Clubs` the following options are available.

+ **Tabs**
    * Create a Control record by selecting `Control Record` from the menu.
    * Create Tab records by selecting `Tabs Maintenance` from the menu.
    * Do a draw by selecting `Tabs-In Draw` from the menu.
    * Reprint a draw by selecting `Reprint Draw` from the menu.
    * Print a Draw Summary by selecting `Draws Summary` from the menu.
+ **League**
    * Create a league format record by selecting `League Formats` from the menu.
    * Create Tab records by selecting `Tabs Maintenance` from the Tabs menu.
    * Create side records by selecting `Side's Maintenance` from the menu.
    * Enter team selections by selecting `Capture Selections` from the menu.
    * To print `Assessment Forms` select Assessment Forms from the menu.
    * To print flag `Declaration Forms` select Declaration Forms from the menu.
    * To capture the completed `Assessment Forms` select `Capture Assessments` from the menu.
    * To print the `Match Assessment Report` select Match Assessment Report from the menu.
    * To print the `Assessment Summary` select `Assessment Summary` from the menu.
    * To clear historical selections select `Clear League History` from the toolbox menu.
+ **Competitions**
    * Create a Competition Type record by selecting `Competition Types` from the menu.
    * Capture Competition Entries by selecting `Capture Entries` from the menu.
    * List entries by selecting `List Entries` from the menu.
    * Print the format of the competition by selecting `Competition Format` from the menu.
    * Print a Draw and Match Cards by selecting `Competition Draw` from the menu.
    * Print a Draw Summary by selecting `Draw Summary` from the menu. This report is a running summary of all draws.
    * To change the Draw select `Change Draw` from the menu. After changing the draw you must reprint them as per above. Please note that to only reprint certain cards you must select `All Cards No`.
    * After the games have been played enter the results by selecting `Capture Game Results` from the menu.
    * Print the game and match results by selecting `Match Results Report` from the menu.

Creditor's Ledger
.................
If you are going to use the `Creditor's Ledger` you must perform the following procedures in order:

+ Create a control record for the company using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `crs_ctl` and `dis_rec` control accounts as per above.
+ Create Creditor's accounts using `File Maintenance -> Masterfile Records`.
+ Capture the account's opening balances using `Data Capture -> Journals`.
+ Print an aged analysis using `Reporting -> Age Analysis` and ensure that your totals balance. If not, recapture the incorrect ones.

Please remember that if you are integrating the Creditors and General Ledger systems, the control account must balance with the age analysis.

The Creditor's Ledger system is at this stage fully functional and you can capture postings, produce basic reports and do interrogations etc.

Please also note that within the Creditor's system all balances are stored as positive even though they are stored as credits in the General Ledger.  Therefore to increase a supplier's balance you would capture a Journal Credit and to decrease a supplier's balance you would capture a Journal Debit.

Debtor's Ledger
...............
If you are going to use the `Debtor's Ledger` you must perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `drs_ctl` and `dis_all` controls as per above.
+ If you are going to make use of chain stores, i.e. the facility to have separate accounts for branches within a chain with a consolidated statement. You would have to create the necessary chain store records using `File Maintenance -> Chain Stores`.
+ If you are going to group your accounts by business activity, create the necessary records using `File Maintenance -> Business Activities`.
+ If you are going to group your accounts by business types, create the necessary records using `File Maintenance -> Business Types`.
+ If you are going to group your accounts by area, create the necessary records using `File Maintenance -> Areas`.
+ If you are going to group your accounts by salesman, create the necessary records using `Salesmen`.
+ Create Debtor's accounts using `File Maintenance -> Masterfile Records`.
+ Capture the account's opening balances using `Data Capture -> Journals`.
+ Print an aged analysis using `Reporting -> Age Analysis` and ensure that your totals balance. If not, recapture the incorrect ones.

Please remember that if you are integrating the Debtors and General Ledger systems, the control account must balance with the age analysis.

The Debtor's Ledger system is at this stage fully functional and you can capture postings, produce basic reports and do interrogations etc.

Loan's Ledger
.............
If you are going to use the `Loan's Ledger` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `lon_ctl` controls as per above.
+ Create existing or new loans using `Data Capture` and just entering on the `Acc-Num` iand `LN` fields.

The Loan's Ledger system is at this stage fully functional and you can capture postings, produce basic reports and do interrogations etc.

Member's Ledger
...............
If you are going to use the `Member's Ledger` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `mem_ctl` and `mem_pen` controls as per above.
+ Create category records using `File Maintenance -> Category Records`.
+ Create contact records using `File Maintenance -> Contact Records`.

The Member's Ledger system is at this stage fully functional and you can add members, edit member details, capture postings, produce basic reports and do interrogations etc.

Rental's Ledger - Standard
..........................
If you are going to use the `Rental's Ledger (Standard)` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ Create premises records using `File Maintenance -> Premises Records`.
+ Create masterfile records using `File Maintenance -> Masterfile Records`.

The Rental's Ledger (Standard) system is at this stage fully functional and you can capture payments, receipts and journal entries.

Rental's Ledger - Extended
..........................
If you are going to use the `Rental's Ledger (Extended)` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ Create owners records using `File Maintenance -> Owners Records`.
+ Create premises records using `File Maintenance -> Premises Records`.
+ Create tenants records using `File Maintenance -> Tenants Records`.

The Rental's Ledger (Standard) system is at this stage fully functional and you can capture payments, receipts and journal entries.

Store's Ledger
..............
If you are going to use the `Store's Ledger` you must perform the following procedures in order:

+ Create a control record for the company using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `stk_soh` and `stk_susp` controls as per above.
+ Create units of issue records using `File Maintenance -> Units of Issue`.
+ Create product groups using `File Maintenance -> Product Groups`.
+ Create stock records for the company by selecting `File Maintenance -> Masterfile Records`.
+ Enter the current stock on hand for the company by selecting `Stock Take -> Returns`.
+ Print a variance report using `Stock Take -> Variance Report` and ensure that all the quantities have been entered correctly. Correct any errors by redoing the previous step for the incorrect ones only.
+ Update the stock items using `Stock Take -> Merge`.
+ Print a stock on hand report using `Reporting -> Stock on Hand`.

Please remember that if you are integrating the Stores and General Ledger systems, the control account must balance with the stock on hand report.

The Store's Ledger system is at this stage fully functional and you can capture postings, produce basic reports and do interrogations etc.

Sales Invoicing
...............
If you are going to use `Sales Invoicing` you must perform the following procedures in order:

+ Setup the Debtor's System as in 8) above ensuring that you create at least one salesman's record.
+ Setup the Store's System as in 9) above.
+ Create a control record using `File Maintenance -> Control Record`.

The Sale's Invoicing system is at this stage fully functional and you can capture invoices, credit notes, sales orders and quotations.

Salaries and Wages
..................
If you are going to use `Salaries and Wages` you must at least perform the following procedures in order:

+ Create a control record using `File Maintenance -> Control Record`.
+ If you elected to integrate with the General Ledger you must create the `wag_ctl`, `wag_slc` and `wag_sli` controls as per above.
+ Create at least one branch record using `File Maintenance -> Branch Records`.
+ Create at least one department record using `File Maintenance -> Department Records`.
+ Create all necessary earnings and deduction records using `File Maintenance -> Earning and Deduction Codes`.
+ Create employee records using `File Maintenance -> Employee Masterfile`.

The Salaries and Wages system is at this stage fully functional and you can capture clock cards and produce payslips etc.

Staff Loans
...........
If you are going to use `Staff Loans` you must first of all set up `Salaries and Wages` as in 14) above and then, at least, perform the following procedures in order:

+ Ensure that there is a deduction record, in the salaries system, for loan repayments.
+ Ensure that all employees with loans have the deduction record included in their masterfile records as a deduction, without values.
+ Capture existing loans using `New Loans`. If Salaries are integrated with the general ledger un-integrate salaries to capture loans balances. Once all opening balances have been captured re-integrate salaries.

The Staff Loans system is at this stage functional.
