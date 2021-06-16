Members Ledger
--------------
File Maintenance (ML)
.....................
Control Record (ML)
+++++++++++++++++++
This routine is used to create or amend a member's ledger control record.

+ **G/L Integration** - Whether or not to integrate with the general ledger.
+ **Members Control** - If integrated, enter the general ledger account number for the `Members Control` account.
+ **Members Penalties** - If integrated, enter the general ledger account number for the `Members Penalties` account.
+ **Bonus Days** - The number of days leeway for for raising charges.
+ **Last Month End** - The date the last month end was performed.
+ **Photo's Path** - Where the members photographs are stored.
+ **Club Logo Image** - The path to the club's logo file.
+ **Card Front Template** - The membership card's front template.
+ **Card Back Template** - The membership card's back template.
+ **Statement Template** - The member's statement template.
+ **Email Address** - The email address of the person in charge of members, if not the default email address in the company record.

Category Records (ML)
+++++++++++++++++++++
This routine is used to create or amend membership category records.

+ **Category Type** - Select the type of category record.

    + **Fees** - Used for once off charges e.g. Entrance Fee.
    + **Category** - Used for main membership category e.g. Full member.
    + **Sports** - - Used for sub categories e.g. Bowls, Tennis etc.
    + **Debentures** - Used for debenture holders.

+ **Code** - A numeric code for the category.
+ **Description** - The category's description.
+ **Report Group** - This is used for sports categories only and is a method to group various categories together for reporting purposes.
+ **Frequency** - How often the charge must be repeated.
+ **Limits** - The following three conditions determine when a member's category might change.

    + **Age Limit** - The maximum age limit for the category or 0 for none.
    + **And Mship** - The number of years membership the age limit also depends on or 0 for none.
    + **Or Mship** - Or the number of years membership which qualifies or 0 for none.

+ **Next Code** - The category code the member will progress to when the limit conditions have been met.
+ **G/L Account Number** - If integrated with the general ledger, the account to be credited with the charges raised.
+ **Effective Date** - The date the following rates become effective. Every time a new date is entered a new record is created.
+ **Penalty Rate** - The rate that penalties will be charged on overdue fees.
+ **Pro-Rata** - Whether or not the fees are to be pro-rata'd based on months till anniversary. This can be either No, the number of months to skip or Manual.
+ **Month 1-12** - The V.A.T. inclusive fee to be raised. In the case of manual pro-rata, you must calculate the various splits manually.

Message Records (ML)
++++++++++++++++++++
Use this routine to create, amend or delete message records. These records are used by `Statements (ML)`_.

Contact Records (ML)
++++++++++++++++++++
Use this routine to create, amend or delete message records. These records are used to parameterise the contact details of members.

+ **Code** - Numeric code.
+ **Contact Type (E,F,M,T)** - The type of contact code i.e. E-mail, Fax, Mobile or Telephone.
+ **Contact Description** - The description on the contact code.

Data Capture (ML)
.................
For all data capture routines first enter the batch details using `Batch Details`_.

Invoices (ML)
+++++++++++++
For each invoice enter the following fields:

+ **Mem-No** - The membership number.
+ **Reference** - The invoice number.
+ **Date** - The date of the invoice.
+ **Amount** - The inclusive total of the invoice.

If not integrated with the general ledger enter these two additional fields:

+ **V** - The applicable V.A.T. code.
+ **V.A.T.** - The applicable V.A.T. amount.

Then enter:

+ **Details** - The detail summary of the invoice.

If integrated with the general ledger enter these additional fields, on the next frame, for all allocations of the total amount.

+ **Acc-Num** - The general ledger account number to allocate an amount to.
+ **V** - The applicable V.A.T. code.
+ **All-Amt** - The exclusive amount to be allocated to this account.
+ **Details** - The details of this allocation.

Payments (ML)
+++++++++++++
For each payment enter the following fields:

+ **Mem-No** - The membership number.
+ **Reference** - The payment number.
+ **Date** - The date of the payment.
+ **Amount** - The amount of the payment.
+ **Discount** - The discount amount.
+ **Details** - The details of the payment.
+ Age the payment using `Ageing Transactions`_.

Journals (ML)
+++++++++++++
For each journal enter enter all fields as per `Invoices (ML)`_ above except that you will have to age the journal using `Ageing Transactions`_ after the first *Details* field.

Credit Notes (ML)
+++++++++++++++++
For each credit note enter all fields as per `Invoices (ML)`_ above except that you will have to age the credit note using `Ageing Transactions`_ after the first *Details* field.

Receipts (ML)
+++++++++++++
For each receipt or deposit slip enter the following:

+ **Reference** - The receipt or deposit slip number.
+ **Date** - The date of the receipt or deposit.
+ **Amount** - The total amount of the receipt or deposit.
+ **Details** - The details of the receipt or deposit.

For each receipt enter the following until the total of the receipt or deposit has been captured.

+ **Mem-No** - The membership number.
+ **Receipt** - The receipt amount for this member.
+ **Discount** - The discount amount for this member.
+ Age the receipt using `Ageing Transactions`_.

Reporting (ML)
..............
Batch Error Listing (ML)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (ML)
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

Age Analysis (ML)
+++++++++++++++++
Use this routine to print an aged analysis of all member's accounts.

+ **Cut Off Period** - The last period to include in the report.
+ **Status** - The member's status to filter the report.
+ **Category** - The membership category to further filter the report.
+ **Code** - The category code, 0 for all, to further filter the report.
+ **Totals Only** - Yes or No.
+ **Sort Order** - Sort by membership number or surname.
+ **First Member Number** - To only print a selected range of members.
+ **Last Member Number** - To only print a selected range of members.
+ **Lower Balance Limit** - To exclude all members whose outstanding balance is less than this amount.
+ **Include Credit Balances** - Whether to include members with credit balances.
+ **Ignore Zero Balances** - Whether to include members with zero balances.

Statements (ML)
+++++++++++++++
Use this routine to print or email member's statements.

+ **Status** - The membership status to filter the report.
+ **Whole File** - Select to print all statements, a range of statements, individual statements, statements without email addresses or statements with email addresses only.
+ **Member Start** - If printing a range enter the starting membership number.
+ **End** - If printing a range enter the ending membership number.
+ **Zero Balances** - Whether to print statements for paid up accounts.
+ **Minus Balances** - Whether to print statements for accounts in credit.
+ **Message Number** - The number of a message to print on the statement.
+ **Statement Date** - The date of the statement, normally the end of a month.
+ **Sort Order** - Sort by membership number or surname.

Notes Listing (ML)
++++++++++++++++++
Use this routine to print any notes on the member's ledger accounts.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Category Changes (ML)
+++++++++++++++++++++
Use this report to print any membership category changes.

+ **Report Type** - Actual or pending changes.
+ **Starting Date** - The starting date of the changes.
+ **Ending Date** - The ending date of the changes.
+ **Change Type** - The type of change to print or all.
+ **Category** - The membership category to print or all.
+ **Code** - The code of the selected category or all.

Master Report (ML)
++++++++++++++++++
Use this report to print a selective master list of members.

+ **Report Date** - The date of the report.
+ **Status** - The member's status to filter the report.
+ **Category** - The membership category to further filter the report.
+ **Report Group** - The report group for sports categories.
+ **Code** - The category code, 0 for all if no report group specified, to further filter the report.
+ **Gender** - All, male or female.
+ **Sort Order** - Sort by membership number or surname.
+ **From Entry** - Include members who joined on or after this date.
+ **To Entry** - Include members who joined on or before this date.
+ **From Status** - If a status was selected include members who's status was effective on or after this date.
+ **To Status** - If a status was selected include members who's status was effective on or before this date.
+ Once you have selected the output options you will be able to select what data you would like on your report.

Suspension Report (ML)
++++++++++++++++++++++
Use this report to print a list of potential suspensions due to non payment.

+ **Sort Order** - Sort by membership number or surname.
+ **Include Pay Plan** - Include members who have arranged terms.

Update Details Request (ML)
+++++++++++++++++++++++++++
Use this report to email requests to all members to update their details.

+ **Category** - The membership category to further filter the report.
+ **Code** - The category code, 0 for all.
+ **First Member Number** - To only print a selected range of members.
+ **Last Member Number** - To only print a selected range of members.

Birthday Report (ML)
++++++++++++++++++++
Use this report to print a list of members whose birthday falls between two dates.

+ **Category** - The membership category to further filter the report.
+ **Code** - The category code, 0 for all.
+ **Sort Order** - Sort by membership number or surname.
+ **From Date** - Include members who's birthday is on or after this date.
+ **To Date** - Include members who's birthday is on or before this date.

Name and Address Labels (ML)
++++++++++++++++++++++++++++
Use this report to print name and address labels.

+ **Status** - The member's status to filter the report.
+ **Category** - The membership category to further filter the report.
+ **Code** - The category code, 0 for all.
+ **Sort Order** - Sort by membership number or surname or postal code.
+ **Avery A4 Code** - The Avery code for the label being used. At this stage only L7159, (3x8), is supported.
+ **First Label Row** - The first available blank label row.
+ **First Label Column** - The first available blank label column.

Toolbox (ML)
............
Transaction Reallocations (ML)
++++++++++++++++++++++++++++++
Use this routine to reallocate and age transactions.

Member Records (ML)
...................
Use this routine to create, edit and interrogate member's records.

New Records (ML)
++++++++++++++++
Click on the **New** button to create a new member's record and then enter all relevant fields on all the available pages:

+ **Personal**
+ **Addresses**
+ **Contacts**
+ **Categories**
+ **Links**

Once all available data has been entered click on the **Update** button to create the new record or the **Reset** button to exit without creating the record.

Edit Records (ML)
+++++++++++++++++
Enter a valid membership number followed by the Enter key. All details of the member will be displayed. Click on the **Edit** button to edit the member's record. Once all details have been altered click on the **Update** button to update the record or the **Reset** button to exit without updating the record.

Month End Routine (ML)
......................
This routine must be run at the end of each and every month as it is the routine which raises charges and controls membership categories.

+ **This Month End Date** - The last day of the relevant month. If it is the financial year end you will be asked for confirmation.
+ **Raise Penalties** - Whether or not to raise penalties on overdue amounts.
+ **Cut-off Date** - The cut-off date for raising penalties.

You will be asked whether you want to print certain reports and finally whether you want to save all entries. Please read the relevant questions and answer appropriately. Please note that if you do not save the entries it will be as if the month end was never run.
