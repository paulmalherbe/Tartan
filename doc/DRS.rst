Debtor's Ledger
---------------
File Maintenance (DR)
.....................
Control Record (DR)
+++++++++++++++++++
Use this routine to create and amend the debtor's control record.

+ **G/L Integration** - Select whether to integrate the general ledger.
+ **Debtors Control** - If integrated, enter the general ledger account number for the `Debtors Control` account.
+ **Discount Allowed** - If integrated, enter the general ledger account number for the `Discount Allowed` account.
+ **G/L Input Method** - If integrated, select whether allocations to general ledger accounts are entered inclusive or exclusive of VAT.
+ **Chain Stores** - Select whether to enable chain store groups.
+ **Statement Template** - The default template to use for statements.
+ **Statement Ageing** - Select whether to print Aged Balances on the Statement or only an Account Balance.
+ **Email Address** - The email address of the person in charge of debtors, if not the default email address in the company record.

Chain Stores (DR)
+++++++++++++++++
Use this routine to create, amend or delete chain store records if enabled. All fields are self explanatory with the exception of the following:

+ **Chn** - The chain store code.
+ **Vat Code** - The default VAT code to use for accounts in the chain.

Business Activities (DR)
++++++++++++++++++++++++
Use this routine to create, amend or delete business activity records.

Business Types (DR)
+++++++++++++++++++
Use this routine to create, amend or delete business type records.

Salesmen (DR)
+++++++++++++
Use this routine to create, amend or delete salesman's records.

Delivery Addresses (DR)
+++++++++++++++++++++++
Use this routine to create, amend or delete delivery address records.

Messages (DR)
+++++++++++++
Use this routine to create, amend or delete message records. These records are used by `Statements (DR)`_ or `Sales Document (SI)`_.

Masterfile Records (DR)
+++++++++++++++++++++++
Use this routine to create or amend debtor's ledger account records. You can import records by selecting the `Import` button in which case the file to be imported must be in `csv` or `xls` format and must contain all the fields as listed below. If the `Account Number` field is left blank an account number will be generated using the `Name` field.

+ **Chn-Num** - The chain store number.
+ **Acc-Num** - The account number.
+ **Name** - The account name.
+ **Address Line 1** - The first line of the postal address.
+ **Address Line 2** - The second line of the postal address.
+ **Address Line 3** - The third line of the postal address.
+ **Postal Code** - The postal code.
+ **Telephone Number** - The telephone number.
+ **Fax Number** - The facsimile number.
+ **Manager** - The manager's name.
+ **Manager Email** - The manager's email address.
+ **Accounts** - The account's contact name.
+ **Accounts E-mail** - The account's contact email address.
+ **Sales Contact** - The buyer's contact name.
+ **Sales E-mail** - The buyer's contact email address.
+ **Date Opened** - The date the account was opened.
+ **Date Registered** - The date the account was registered.
+ **V.A.T. Number** - The creditor's V.A.T. number.
+ **Delivery Code** - The delivery address code.
+ **Area** - The area code.
+ **Business Activity** - The business activity code.
+ **Business Type** - The business type code.
+ **Price Level** - The price level for this account.
+ **Discount Percentage** - The sale's discount enjoyed by this account.
+ **Interest Percentage** - The interest charged on overdue balances.
+ **Referral Terms** - The maximum terms, in days, before referral.
+ **Rejected Terms** - The maximum terms, in days, before rejection.
+ **Credit Limit** - The credit limit.
+ **Stop Indicator** - A flag to stop all access to this account.
+ **Invoice Message** - The code of the message to print on invoices.
+ **Statement Message** - The code of the message to print on statements.
+ **Credit Rating** - The accounts rating (N/G/F/B).

Recurring Charges Records (DR)
++++++++++++++++++++++++++++++
Use this routine to create recurring charges records. These are charges which occur periodically e.g. rent, levies etc.

+ **Header**
    + **Number** - A sequential number of the charge record.
    + **Description** - The description of the charge.
    + **Frequency** - How often the charge is to be raised.
    + **Day of the Month** - When the charge must be raised.
    + **Charge Account** - The G/L account to be credited if integrated.
    + **VAT Code** - The V.A.T. code.
+ **Body**
    + **Seq** - A sequential number of the entry.
    + **Chn** - The debtor's chain store code, if applicable.
    + **Acc-Num** - The debtor's account number.
    + **Charge Details** - A further description of the charge for the debtor.
    + **Excl-Value** - The exclusive value of the charge for the debtor.
    + **Start** - The starting period of the charge for the debtor.
    + **End** - The ending period of the charge for the debtor.
    + Continue entering until all applicable charges have been entered.

Data Capture (DR)
.................
Sales, Journals and Credit Notes (CR)
+++++++++++++++++++++++++++++++++++++
These data capture routines are similar in operation and therefore I will handle them together.

As with most data capture routines you will first have to enter the `Batch Details`_ after which the following screens and fields apply:

+ **Transaction**
    + **Chn** - The debtor's chain store code, if applicable.
    + **Acc-Num** - The debtor's account number.
    + **Reference** - The transaction reference number.
    + **Date** - The date of the transaction.
    + **Amount** - The total amount of the transaction.
    + **Details** - The details of the transaction.
    + You might now be required to age the transaction using `Ageing Transactions`_.

+ **Allocation** - This screen only applies if integrated with the G/L.
    + **Coy** - The company number.
    + **Acc-Num** - The G/L account number.
    + **V** - The V.A.T. code.
    + **Exc-Amount** - The exclusive amount of the allocation.
    + **V.A.T.** - The V.A.T. amount of the allocation.
    + **Details** - The details of the allocation.
    + Continue allocating the transaction until fully allocated.

Receipts (DR)
+++++++++++++
As with most data capture routines you will first have to enter the `Batch Details`_ after which the following screens and fields apply:

+ **Deposit**
    + **Reference** - The deposit reference number.
    + **Date** - The date of the deposit.
    + **Amount** - The total amount of the deposit.
    + **Details** - The details of the deposit.
+ **Allocation**
    + **Coy** - The company number.
    + **Chn** - The debtor's chain store code, if applicable.
    + **Acc-Num** - The debtor's account number.
    + **Receipt** - The amount for this debtor.
    + **Discount** - Any discount allowed.
    + You might now be required to age the transaction using `Ageing Transactions`_.
    + Continue allocating the deposit until fully allocated.

Payments (DR)
+++++++++++++
As with most data capture routines you will first have to enter the `Batch Details`_ after which the following screen and fields apply:

+ **Transaction**
    + **Chn** - The debtor's chain store code, if applicable.
    + **Acc-Num** - The debtor's account number.
    + **Reference** - The transaction reference number.
    + **Date** - The date of the transaction.
    + **Amount** - The total amount of the transaction.
    + **Discount** - Any settlement discount.
    + **Details** - The details of the transaction.
    + You might now be required to age the transaction using `Ageing Transactions`_.

Recurring Charges (DR)
++++++++++++++++++++++
Use this routine to raise recurring charges as created using `Recurring Charges Records (DR)`_.

As with most data capture routines you will first have to enter the `Batch Details`_ after which the following screen and fields apply:

+ **Frequency** - The frequency of the charges to be raised.
+ **All Charges** - Whether or not all charges for the selected frequency must be raised.
+ **2nd Reference** - A second reference number for the charges.
+ **Invoices** - Whether or not to produce invoices for the charges.

If you selected `No` to `All Charges` a list of available charges will be displayed and you will able to mark the ones to raise.

Reporting (DR)
..............
Chain Stores Listing (DR)
+++++++++++++++++++++++++
Use this routine to produce a listing of chain stores.

Areas Listing (DR)
++++++++++++++++++
Use this routine to produce a listing of areas.

Salesmen Listing (DR)
+++++++++++++++++++++
Use this routine to produce a listing of salesmen.

Delivery Address Listing (DR)
+++++++++++++++++++++++++++++
Use this routine to produce a listing of delivery addresses.

Messages Listing (DR)
+++++++++++++++++++++
Use this routine to produce a listing of invoice and statement messages.

Batch Error Listing (DR)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (DR)
++++++++++++++++++++++++++++
Use this routine to print lists of transactions either by financial period or date of capture.

+ **Period Type** - Financial or Capture.
+ **Starting Period** - The first financial period to include in the report.
+ **Ending Period** - The last financial period to include in the report.
+ **Starting Date** - The from date to include in the report.
+ **Ending Date** - The to date to include in the report.
+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.
+ **Totals Only** - Yes or No.

Due for Payment Listing (DR)
++++++++++++++++++++++++++++
Use this routine to produce a listing of debtor's due to pay at a specific cut off date,

+ **Payment Date** - Enter the cut off date.

Outstanding Transactions (DR)
+++++++++++++++++++++++++++++
Use this routine to produce a report of outstanding transactions by debtor.

+ **Report Period** - Enter the financial period for the report.
+ **Account per Page** - Select whether to start a new page for each account.

Age Analysis (DR)
+++++++++++++++++
Use this routine to produce a debtor's age analysis.

+ **Base** - The basis to use for the report.
    + **Agedt** - Produce a report based on Ageing Period, this will not necessarily balance with the control account.
    + **Curdt** - Produce a report based on Financial Period, this will always balance with the control account.
+ **Cut-Off Period** - The financial period.
+ **Totals Only** - Select totals only or all individual accounts.
+ **Business Activity** - Enter the business activity, if applicable.
+ **Business Type** - Enter the business type, if applicable.
+ **Lower Balance Limit** - Enter the minimum balance amount to include.
+ **Include Credit Balances** - Select whether to include accounts with credit balances.

Master Listing (DR)
+++++++++++++++++++
Use this routine to produce a debtor's master listing.

+ **Activity** - The business activity, if applicable.
+ **Type** - The business type, if applicable.
+ **Sort Order** - Select the print order of the accounts.
+ **Use Full Address** - Select whether to print the account's full address.
+ **Contact Details** - Select which contact details are to be printed.

Statements (DR)
+++++++++++++++
Use this routine to produce debtor's statements.

+ **Template Name** - The name of the template to use.
+ **Open Item** - If a non-standard template is selected you can choose to print the statement in open item or balance forward format.
+ **Maximum Pages** - If a non-standard template is selected you can choose the maximum number of pages per account.
+ **Whole File** - Select whole file, range or individual accounts.
+ **From Account** - If range was selected enter the starting account code.
+ **To   Account** - If range was selected enter the ending account code.
+ **Sort Order** - Select the sorting order.
+ **Include Zero Balances** - Select whether to include accounts with zero balances.
+ **Include Negative Balances** - Select whether to include accounts with credit balances.
+ **Include Stopped Balances** - Select whether to include stopped accounts.
+ **Include Allocated Transactions** - Select whether to include allocated transactions.
+ **Statement Date** - The date to be used for the cut-off.
+ **Message Number** - The message number to print, if applicable.

Name and Address Labels (DR)
++++++++++++++++++++++++++++
Use this routine to produce debtor's name and address labels.

+ **Whole File** - Select whole file or individual accounts.
+ **Sort Order** - Sort by account number, name or postal code.
+ **Avery A4 Code** - The Avery code for the label being used.
+ **First Label Row** - The first available blank label row.
+ **First Label Column** - The first available blank label column.

Notes Listing (DR)
++++++++++++++++++
Use this routine to print any notes on the debtor's ledger accounts.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Sales History (DR)
++++++++++++++++++
Use this routine to produce a sales history report by debtor.

Toolbox (DR)
............
Change Account Numbers (DR)
+++++++++++++++++++++++++++
Use this routine to change account numbers.

Transaction Reallocations (DR)
++++++++++++++++++++++++++++++
Use this routine to reallocate and age transactions.

Account Redundancy (DR)
+++++++++++++++++++++++
Use this routine to flag debtor's accounts as redundant. The following buttons are available:

+ **Generate** - Automatically mark accounts with a zero balance and are inactive, as redundant.
    + **Months Inactive** - The number of months the accounts have been inactive.
+ **Create** - Mark individual accounts, which have a zero balance, as redundant.
    + **Chain Store** - The chain store number if applicable.
    + **Acc-Num** - The account number.
+ **Restore** - Mark individual accounts, which are redundant, as normal.
    + **Chain Store** - The chain store number if applicable.
    + **Acc-Num** - The account number.
+ **Exit** - Exit the routine.

Populate Credit Ratings (DR)
++++++++++++++++++++++++++++
Use this routine to generate credit ratings, based on payment history, for accounts.

+ **Current Period** - Enter the current financial period YYYYMM.
+ **Ignore Zero Balances** - Select whether to ignore zero balance accounts.

Interrogation (DR)
..................
This routine is for querying individual debtor's accounts.
