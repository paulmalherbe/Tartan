Rentals Ledger (Standard)
-------------------------
File Maintenance (RT)
.....................
Control Record (RT)
+++++++++++++++++++
This routine is used to create or amend a member's ledger control record.

+ **G/L Integration** - Whether or not to integrate with the general ledger.
+ **Last Month End** - The date of the last month end.
+ **Statement Template** - The template to use for statements.

Premises Records (RT)
+++++++++++++++++++++
This routine is used to create or amend premises records.

+ **Premises Code** - A 7 character alphanumeric code.
+ **Description** - The description of the premises.
+ **Address Line 1-3** - The address of the premises.
+ **Postal Code** - The postal code.
+ **Rental Account** - If integrated with the general ledger this would be the control account.
+ **Income Account** - If integrated with the general ledger this would be the account to be credited with rentals raised.
+ **Email Address** - The email address of the person in charge of rentals, if not the default email address in the company record.

Masterfile Records (RT)
+++++++++++++++++++++++
This routine is used to create or amend tenants records.

+ **Premises Code** - The premises code being rented.
+ **Account Code** - A 7 character alphanumeric code for the tenant.
+ **Tenant Name** - The name of the tenant.
+ **Address Line 1-3** - The postal address of the tenant.
+ **Postal Code** - The postal code.
+ **Telephone Number** - The tenant's telephone number.
+ **E-Mail Number** - The tenant's email address.
+ **VAT Indicator** - The V.A.T. code.
+ **VAT Number** - The tenant's V.A.T. number, if applicable.
+ **Payment Frequency** - The frequency of rental payments.
+ **Start Date** - The starting date of the lease.
+ **Number of Periods** - The number of payment periods to run.
+ **Rental Amount** - The period rental amount, V.A.T. exclusive.
+ **Status** - The status of the lease.

Data Capture (RT)
.................
Receipts (RT)
+++++++++++++
This routine is used to capture receipts.

+ **Prm-Cod** - Enter the premises code.
+ **Acc-Num** - Enter the account number.
+ **Seq** - Enter the contract sequence number.
+ **Reference** - Enter the transaction reference number.
+ **Date** - Enter the transactions date.
+ **Amount** - Enter the transaction amount.
+ **Details** - Enter the transaction description.

Payments (RT)
+++++++++++++
This routine is used to capture payments.

+ **Prm-Cod** - Enter the premises code.
+ **Acc-Num** - Enter the account number.
+ **Seq** - Enter the contract sequence number.
+ **Reference** - Enter the transaction reference number.
+ **Date** - Enter the transactions date.
+ **Amount** - Enter the transaction amount.
+ **Details** - Enter the transaction description.

Journals (RT)
+++++++++++++
This routine is used to capture journal entries.

+ **Prm-Cod** - Enter the premises code.
+ **Acc-Num** - Enter the account number.
+ **Seq** - Enter the contract sequence number.
+ **Reference** - Enter the transaction reference number.
+ **Date** - Enter the transactions date.
+ **Amount** - Enter the transaction amount.
+ **V** - Enter the VAT Code, if applicable.
+ **V.A.T** - Enter the VAT Amount, if applicable.
+ **Details** - Enter the transaction description.

Reporting (RT)
..............
Batch Error Listing (RT)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (RT)
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

Master Listing (RT)
+++++++++++++++++++
This routine is used to produce a master listing.

+ **Report Date** - Enter the cut-off date for the report.
+ **Contracts** - Select which contracts to report on.
+ **Months to Expiry** - If *Expiring* was selected, enter the number of months.
+ **Consolidate** - Whether or not to consolidate all contracts.

Statements (RT)
+++++++++++++++
This routine is used to produce statements.

+ **Template Name** - The name of the template to use.
+ **Whole File** - Select whole file or individual accounts.
+ **Zero Balances** - Select whether to include accounts with zero balances.
+ **Minus Balances** - Select whether to include accounts with minus balances.
+ **Message Number** - The message number to print, if applicable.
+ **Statement Date** - The date to be used for the cut-off.

Notes Listing (RT)
++++++++++++++++++
This routine is used to produce a tenant's note listing.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Toolbox (RT)
............
Change Account Numbers (RT)
+++++++++++++++++++++++++++
This routine is used to change account numbers.

Interrogation (RT)
..................
This routine is used to interrogate records.

Month End Routine (RT)
......................
This routine is used to close off a month and raise rentals for the following month.

+ **Last Month End Date** - The last month-end date is displayed.
+ **This Month End Date** - Enter the required month-end date.
