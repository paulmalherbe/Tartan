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

Payments (RT)
+++++++++++++
This routine is used to capture payments.

Reporting (RT)
..............
Batch Error Listing (RT)
++++++++++++++++++++++++
This routine is used to produce a batch error listing.

Transaction Audit Trail (RT)
++++++++++++++++++++++++++++
This routine is used to produce a transaction audit trail.

Master Listing (RT)
+++++++++++++++++++
This routine is used to produce a master listing.

Statements (RT)
+++++++++++++++
This routine is used to produce statements.

Notes Listing (RT)
++++++++++++++++++
This routine is used to produce a tenant's note listing.

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
