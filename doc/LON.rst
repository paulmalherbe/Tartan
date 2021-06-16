Loans Ledger
------------
File Maintenance (LN)
.....................
Control Record (LN)
+++++++++++++++++++
Use this routine to create and amend the loan's control record.

+ **G/L Integration** - Whether or not to integrate with the general ledger.
+ **Loans Control** - If integrated, enter the general ledger account number for the `Loans Control` account.
+ **Interest Received** - If integrated, enter the general ledger account number for the `Interest Received` account.
+ **Interest Paid** - If integrated, enter the general ledger account number for the `Interest Paid` account.
+ **Interest Method** - The method for raising interest as follows:
    + **Daily** - Interest is raised on daily balance.
    + **Monthly** - Interest is raised on monthly balance.
+ **Capitalisation Base** - What capitalisation of interest is based on:
    + **Anniversary** - Using the anniversary of the loan as the basis.
    + **Financial** - Using the financial period as the basis.
+ **Capitalisation Freq** - When capitalisation takes place:
    + **Annual** - Interest get capitalised every 12 months from the base.
    + **Bi-Annual** - Interest get capitalised every 6 months from the base.
+ **Debit Rate** - The default interest rate on debit balances.
+ **Credit Rate** - The default interest rate on credit balances.
+ **Last Interest Date** - The last date interest was raised.
+ **Email Address** - The email address of the person in charge of loans, if not the default email address in the company record.

Loans Masterfile (LN)
+++++++++++++++++++++
Use this routine to create and amend loan account records.

+ **Account Code** - The account code. Enter nothing for a new account.

The rest of the fields are self explanatory.

Data Capture (LN)
.................
Payments, Receipts, Journals and Interest Adjustments (LN)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Use this routine to capture all loans transactions.

+ **Acc-Num** - The account code. Enter nothing for a new account.
+ **Ln** -  The loan number for existing loans. Enter 0 for a new loan.
+ **Description** - The description of the loan for new loans.
+ **Date** - The transaction date.
+ **Reference** - The transaction reference.
+ **Amount** - The transaction amount.
+ **DRte%** - The rate of interest to be charged on the loan if in debit.
+ **CRte%** - The rate of interest to be charged on the loan if in credit.
+ **Mth** - The number of months for the loan to run or 0 for an open loan.

If the loans ledger is integrated with the general ledger the following applies in the case of Journal Entries.

+ **Coy** - The company number for integrated companies.
+ **Acc-Num** - The general ledger account to be debited or credited.
+ **All-Amt** - The amount to be allocated to this account.
+ **Details** - The details of the allocation.

Raise Interest (LN)
+++++++++++++++++++
Use this routine to raise interest on loans.

+ **Transaction Date** - The date on which the interest must be raised.

Rate Change (LN)
++++++++++++++++
Use this routine to change the interest rate of a loan.

+ **All Current Rates** - Select whether to globally change existing rates.

If All Current Rates was selected the following applies:

+ **Effective Date**  - The date of the rate change.
+ **Debit  Rate - Old** - The old debit rate to change.
+ **              New** - The new debit rate.
+ **Credit Rate - Old** - The old credit rate to change.
+ **              New** - The new credit rate.

else the following applies:

+ **Acc-Num** - The loan account number.
+ **Ln** - The loan number.
+ **Date** - The effective date of the change.
+ **DRte-%** - The new debit rate to apply.
+ **CRte-%** - The new credit rate to apply.

Reporting (LN)
..............
Batch Error Listing (LN)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (LN)
++++++++++++++++++++++++++++
Use this routine to print lists of transactions either by financial period or date of capture.

+ **Starting Period** - The first financial period to include in the report.
+ **Ending Period** - The last financial period to include in the report.
+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.
+ **Totals Only** - Yes or No.

Balances Listing (LN)
+++++++++++++++++++++
Use this routine to list all existing loans.

+ **Sort Order** - Select whether to sort by Number or Name.
+ **Include Zero Balances** - Select whether to include zero balance loans.
+ **Include Pending Interest** - Select whether to include pending interest.

Statements (LN)
+++++++++++++++
Use this routine to print loan statements as follows:

+ **Template Name** - The template to use.
+ **Maximum Pages** - Enter the maximum number of pages for the statement, 0 for all.
+ **Whole File** - Select whether to print all statements or only selected ones.
+ **Sort Order** - Select the order in which to print the statements.
+ **Include Zero Balances** - Select whether to include zero balance loans.
+ **Include Pending Interest** - Select whether to include pending interest.
+ **Statement Date** - The statement date.

Notes Listing (LN)
++++++++++++++++++
Use this routine to print any notes on the loan's ledger accounts.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Toolbox (LN)
............
Change Account Numbers (LN)
+++++++++++++++++++++++++++
Use this routine to change account numbers.

Interrogation (LN)
..................
This routine is for querying individual loans.
