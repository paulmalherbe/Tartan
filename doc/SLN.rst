Staff Loans
-----------
File Maintenance (SL)
.....................
Loans Masterfile (SL)
+++++++++++++++++++++
Use this routine to amend loan records.

Data Capture (SL)
.................
New Loans (SL)
++++++++++++++
Use this routine to capture new or existing loans.

+ **EmpNo** - The employee number.
+ **Ln** -  This is automatically generated.
+ **Description** - The description of the loan e.g. Study Loan
+ **Date** - The date of the loan.
+ **Ref-No** - The reference number of the loan.
+ **Cde** - The salaries deduction code to use for repayments.
+ **Intr-%** - The rate of interest to be charged on the loan.
+ **Loan-Amt** - The capital amount of the loan.
+ **Ded-Amt** - The amount to be deducted from earnings to repay the loan.

Movements (SL)
++++++++++++++
Use this routine to capture movements to existing loans.

+ **EmpNo** - The employee number.
+ **Lon** - The loan number which was generated when creating a new loan.
+ **Trans-Date** - The movement date.
+ **T** - The type of movement as follows:
    + *1 Interest Adjustment*
    + *3 Further Advance*
    + *4 Loan Repayment*
    + *5 Loan Adjustment*
+ **Reference** - The reference number of the movement.
+ **Intr-%** - The new rate of interest to be charged on the loan.
+ **Interest** - The interest adjustment, if type 1.
+ **Amount** - The loan amount for types 3, 4 and 5.
+ **Deduct** - The new amount to be deducted from earnings to repay the loan.

Raise Interest (SL)
+++++++++++++++++++
Use this routine to raise interest on loans.

+ **Transaction Date** - The date on which the interest must be raised.

Reporting (SL)
..............
Batch Error Listing (SL)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (SL)
++++++++++++++++++++++++++++
Use this routine to print lists of transactions either by financial period or date of capture.

+ **Starting Period** - The first financial period to include in the report.
+ **Ending Period** - The last financial period to include in the report.
+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.
+ **Totals Only** - Yes or No.

Master Listing (SL)
+++++++++++++++++++
Use this routine to list all existing loans.

+ **Sort Order** - Select whether to sort by Number or Name.
+ **Ignore Zero Balances** - Select whether to exclude repaid loans.

Statements (SL)
+++++++++++++++
Use this routine to print loan statements as follows:

+ **Start Date** - Only include loans issued on or after this date.
+ **Last Date** - Only include loans issued on or before this date.
+ **Whole File** - Include all loans in the selected period or individuals.
+ **Ignore Paid Ups** - Select whether to exclude repaid loans.

Interrogation (SL)
..................
This routine is for querying individual loans.
