Rentals Ledger (Extended)
-------------------------
File Maintenance (RC)
.....................
Control Record (RC)
+++++++++++++++++++
This routine is used to create or amend a member's ledger control record.

+ **G/L Integration** - Whether or not to integrate with the general ledger.
+ **Commission Raised** - If integrated, enter the general ledger account number for the `Commission Raised` account.
+ **Deposits Control** - If integrated, enter the general ledger account number for the `Deposits Control` account.
+ **Contract Fees** - If integrated, enter the general ledger account number for the `Contract Fees` account.
+ **Owners Control** - If integrated, enter the general ledger account number for the `Owners Control` account.
+ **Owners Charges** - If integrated, enter the general ledger account number for the `Owners Charges` account.
+ **Tenants Control** - If integrated, enter the general ledger account number for the `Tenants Control` account.
+ **Tenants Charges** - If integrated, enter the general ledger account number for the `Tenants Charges` account.
+ **Bank Account** - If integrated, enter the general ledger account number for the `Bank Account`.
+ **Last Month End** - The date of the last month end.
+ **Owner Template** - The template to be used to print owner's statements.
+ **Tenant Template** - The template to be used to print tenant's statements.
+ **Email Address** - The email address of the person in charge of rentals, if not the default email address in the company record.

Owners Records (RC)
+++++++++++++++++++
This routine is used to create or amend owner's records.

+ **Account Number** - A 7 character alphanumeric code.
+ **Name** - The name of the owner.
+ **Address Line 1-3** - The postal address of the owner.
+ **Postal Code** - The postal code.
+ **Home Number** - The owner's home telephone number.
+ **Office Number** - The owner's office telephone number.
+ **Mobile Number** - The owner's mobile number.
+ **Fax Number** - The owner's facsimile number.
+ **E-Mail Address** - The owner's email address.
+ **VAT Number** - The owner's v.a.t. registration number, if applicable.
+ **VAT Default** - The default v.a.t. code applicable to the owner.
+ **Bank Name** - The owner's bank name.
+ **Bank Branch** - The owner's bank branch code.
+ **Bank Account** - The owner's bank account number.

Premises Records (RC)
+++++++++++++++++++++
This routine is used to create or amend premises records.

+ **Owner Code** - The owner's account number.
+ **Premises Code** - A 7 character alphanumeric code.
+ **Description** - The description of the premises.
+ **Address Line 1-3** - The address of the premises.
+ **Postal Code** - The postal code.
+ **Commission Rate** - The rate charged for managing these premises.

Tenants Records (RC)
++++++++++++++++++++
This routine is used to create or amend tenant's records.

+ **Owner Code** - The owner's account number.
+ **Premises Code** - The premises code being rented.
+ **Account Code** - A 7 character alphanumeric code for the tenant.
+ **Tenant Name** - The name of the tenant.
+ **Address Line 1-3** - The postal address of the tenant.
+ **Postal Code** - The postal code.
+ **Telephone Number** - The tenant's telephone number.
+ **E-Mail Number** - The tenant's email address.
+ **VAT Number** - The tenant's V.A.T. number, if applicable.
+ **Payment Frequency** - The frequency of rental payments.
+ **Start Date** - The starting date of the lease.
+ **Number of Periods** - The number of payment periods to run.
+ **Rental Amount** - The period rental amount, V.A.T. exclusive.
+ **Deposit Amount** - The deposit amount.
+ **Status** - The status of the lease.

Statement Messages (RC)
+++++++++++++++++++++++
This routine is used to create or amend statement message records.

Interest Rates (RC)
+++++++++++++++++++
This routine is used to create or amend interest rates used for calculating the value of deposits.

+ **Date of Change** - The date the rate became effective.
+ **Prime Rate** - The prime rate.
+ **Bank Rate** - The bank's rate.
+ **Comm Rate** - The rate of commission charged.

Data Capture (RC)
.................
This routine is used to capture all transactions.

+ **Prm-Cod** - The premises code foe which we are capturing transactions.

Owner (RC)
++++++++++

+ **Acc-Num** - The owner's account number. This is automatically obtained from the premises record.
+ **Reference** - The transaction reference number.
+ **Date** - The transaction date.
+ **T** - The transaction type i.e. receipt, payment or journal.
+ **Amount** - The transaction amount.
+ **V** - The v.a.t. code, if applicable.
+ **V.A.T.** - The v.a.t. amount, if applicable.
+ **Details** - The details of the transaction.

Tenant (RC)
+++++++++++

+ **Acc-Num** - The tenant's account number.
+ **Seq** - The lease sequence number being dealt with.
+ **Reference** - The transaction reference number.
+ **Date** - The transaction date.
+ **T** - The transaction type i.e. rental, receipt, payment or journal.
+ **Amount** - The transaction amount.
+ **Details** - The details of the transaction.

Allocation (RC)
+++++++++++++++
For all tenant transactions, excluding rentals raised, movement types must be allocated.

+ **M** - The movement type i.e. rental, deposit, contract fee, services or repairs.
+ **Amount** - The amount to be allocated to this allocation.
+ **V** - The v.a.t. code, if applicable.
+ **V.A.T.** - The v.a.t. amount, if applicable.
+ **Details** - The details of the allocation.

Reporting (RC)
..............
Owners Audit Trail (RC)
+++++++++++++++++++++++
This routine is used to produce an owner's transaction audit trail.

Owners Master Listing (RC)
++++++++++++++++++++++++++
This routine is used to produce an owner's master listing.

Owners Statements (RC)
++++++++++++++++++++++
This routine is used to produce owner's statements.

Owners Notes Listing (RC)
+++++++++++++++++++++++++
This routine is used to produce an owner's note listing.

Tenants Audit Trail (RC)
++++++++++++++++++++++++
This routine is used to produce a tenant's transaction audit trail.

Tenants Master Listing (RC)
+++++++++++++++++++++++++++
This routine is used to produce a tenant's master listing.

Tenants Statements (RC)
+++++++++++++++++++++++
This routine is used to produce tenant's statements.

Tenants Notes Listing (RC)
++++++++++++++++++++++++++
This routine is used to produce a tenant's note listing.

Tenants Deposit Listing (RC)
++++++++++++++++++++++++++++
This routine is used to produce a listing of deposits.

Statement Messages (RC)
+++++++++++++++++++++++
This routine is used to produce a listing of statement messages.

Interrogation (RC)
..................
Owners Interrogation (RC)
+++++++++++++++++++++++++
This routine is used to interrogate owner's records.

Tenants Interrogation (RC)
++++++++++++++++++++++++++
This routine is used to interrogate tenant's records.

Toolbox (RC)
............
CSV Masterfile Importing (RC)
+++++++++++++++++++++++++++++
This routine is used to import masterfile records from a comma separated file.

CSV Transaction Importing (RC)
++++++++++++++++++++++++++++++
This routine is used to import transactions from a comma separated file.

Check for Missing Records (RC)
++++++++++++++++++++++++++++++
This routine is used to check for missing records.

Month End Routine (RC)
......................
This routine is used to close off a month and raise rentals for the following month.
