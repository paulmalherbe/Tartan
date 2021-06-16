Bookings Manager
----------------
File Maintenance (BK)
.....................
Control Record (BK)
+++++++++++++++++++
Use this routine to maintain a bookings control record.

+ **G/L Integration** - Yes to integrate else No.
+ **Bookings Control** - If integrated, enter the general ledger account number for the `Bookings Control` account.
+ **Cheques Received** - If integrated, enter the general ledger account number for the `Cheques Received` account.
+ **Cash Received** - If integrated, enter the general ledger account number for the `Cash Received` account.
+ **Cancellation Fee** - If integrated, enter the general ledger account number for the `Cancellation Fee` account.
+ **Booking Template** - The template to use for the booking forms.
+ **Booking Template** - The template to use for the booking invoice.
+ **Statement Template** - The template to use for the booking statement.
+ **Terms and Conditions** - The terms and conditions file to attach to the booking query.
+ **Email Address** - The email address of the person in charge of bookings, if not the default email address in the company record.

Unit Records (BK)
+++++++++++++++++
Use this routine to maintain unit records.

+ **Booking Type** - Select the type of unit.
+ **Unit Code** - Enter a code which can be up to 6 alphanumeric characters.
+ **Description** - Enter a description for the unit.
+ **Number of Rooms** - Enter the number of bookable rooms in the unit.
+ **Total Capacity** - Enter the total booking capacity for the unit. Enter 999 for infinite capacity.
+ **Default Rate** - The default rate code for the unit.
+ **Vat Code** - Enter the vat code applicable to the unit.
+ **Sales Account** - Enter the G/L sales account, if integrated.

Rate Records (BK)
+++++++++++++++++
Use this routine to maintain rate records as follows:

+ **Unit Type** - Enter a type of unit this rate applies to.
+ **Code** - Enter a code which can be up to 3 numeric digits.
+ **Description** - Enter the description of the rate record.
+ **Rate Base** - Select the applicable base for the rate.
+ **Starting Date** - Enter the date this rate becomes applicable.
+ **Rate Amount** - Enter the rate amount.

Booking Letters (BK)
++++++++++++++++++++
Use this routine to maintain booking letters.

+ **Letter Type** - Select the type of letter.
+ **Body** - Enter body of the letter.

Contacts (BK)
+++++++++++++
Use this routine to maintain booking contacts. The fields are self explanatory with the exception of the following:

+ **Code** - Enter the code for the contact or blank for a new contact.

Calendar (BK)
.............
Use this routine to display a booking's calendar showing all bookings currently entered. Double Left Clicking on an existing booking will display the booking and allow modifications and all the normal booking features as per the `Bookings (BK)`_ below. Right Clicking on an existing booking will display short deatisl of the booking. While in the calendar the following buttons are available:

+ **New Booking** - Selecting this button will allow the creation of a new booking as per `Bookings (BK)`_ below.
+ **Search Bookings** Selecting this button will display all the current bookings and will allow you to search and display a specific booking.
+ **Deposits List** - Selecting this button will enter the `Deposits Listing (BK)`_ routine as detailed above.
+ **Arrivals List** - Selecting this button will enter the `Arrivals Listing (BK)`_ routine as detailed above.
+ **Exit** - Select this button to exit out of the calendar.

Bookings (BK)
.............
Use this routine to manage bookings.

Booking Tab (BK)
++++++++++++++++
This page contains all the relevant details of the booking.

+ **Booking Number** - The booking number or 0 for a new booking.
+ **Type** - Select the type of booking.
+ **Group Name** - The name of the group if applicable.
+ **Number of Persons** - The number of people.
+ **Arrival (YYYYMMDD)** - The date of arrival.
+ **Departure (YYYYMMDD)** - The date of departure.
+ **Units** - Select whether to Continue with the existing booking or Edit the units booked.
    + **Unit-Cod** - The unit's code made up of the unit type and the unit's code.
    + **Description** - The description of the unit.
    + **Rme** - The room code to allocate or zero for all rooms in the unit.
    + **Rte** - The rate code to apply to this unit.
    + **Ppl** - The number of guests.
    + **Per** - The periods, if applicable.
    + **Disc-%** - The discount percentage, if applicable.
    + **Applied-Rt** - The final applicable rate or zero for no charge.
+ **Value** - The total value of the booking.
+ **Initial Deposit** - The initial deposit if applicable. If no deposit is entered the status of the booking will immediately be upgraded to confirmed.
+ **Initial Dep Due** - The last date that the initial deposit must be received by.
+ **Additional Deposit** - The additional deposit if applicable.
+ **Additional Dep Due** - The last date that the additional deposit must be received by.
+ **Account Balance** - The balance of the account. This could be a minus amount if a deposit has been received and the invoice not yet raised.
+ **Remarks** - Any additional details.

Contact (BK)
++++++++++++
This page contains all the relevant contact details. All the fields are self explanatory with the exception of the following:

+ **Contact Code** - The contact's code or blank for a new contact.

Booking Buttons (BK)
++++++++++++++++++++
+ **Edit** - Select this button to alter an existing booking.
+ **Transact** - Select this button to capture a transaction. Valid transaction types are Receipt, Refund, Journal, Cancellation and Reinstatement. Some of the fields, depending on the type of transaction, will not be required.
    + **Type** - The type of transaction.
        + **Receipt** - Continue and enter the method, date, amount and details.
        + **Refund** - Continue and enter the method, date, amount and details
        + **Journal** - Continue and enter the date, amount and details. If integrated you must then enter the g/l-acc number, vat code and vat amount.
        + **Cancel** - In the case of cancellations for confirmed and settled bookings you will be prompted to confirm the cancellation and if in the affirmative you will then be asked if a charge must levied on the cancellation. For charges continue with the amount and details of the charge.
        + **Reinstate** - You can only re-instate a cancelled booking.
    + **Method** - The method of the transaction. This only applies to Receipts and Refunds.
    + **Date** - The date of the transaction.
    + **Reference** - The transaction's reference number. This is automatic.
    + **Amount** - The amount of the transaction.
    + **Details** - The details of the transaction.
    + **Acc-Num** - The general ledger account number, if integrated.
    + **VAT Code** - The applicable VAT code.
    + **VAT Amount** - The applicable VAT amount.
+ **Movements** - Select this button to display all movements on the account.
+ **Notes** - Select this button to maintain notes relating to this booking.
+ **Accept** - Select this button to accept the booking and to print a booking letter.
+ **Quit** - Select this button to terminate the current displayed booking.

Invoices (BK)
.............
Use this routine to generate invoices.

+ **Starting Date** - The starting date.
+ **Ending Date** - The ending date.
+ **Include Queries** - Whether or not to include queries.
+ **Bookings** - Whether to generate all outstanding invoices or to selectively choose individual bookings.
+ **Template Name** - The template to use for the invoices.

Reporting (BK)
..............
Deposits Listing (BK)
+++++++++++++++++++++
Use this routine to produce a listing of outstanding deposits.

+ **Expired Only** - Select whether to print all deposits or only expired ones.
+ **Order** - Select the required order of the listing.

Transaction Audit Trail (BK)
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

Arrivals Listing (BK)
+++++++++++++++++++++
Use this routine to print all arrivals for a particular period. This routine also has the choice to print a housekeeping report and raise the invoices.

+ **Period** - The relevant period type.
+ **Starting Date** - The starting period date.
+ **Ending Date** - The ending period date. This only applies if range was selected as the period type.
+ **Housekeeping Report** - Select whether to also print a housekeeping report.
+ **Generate Invoices** - Select whether to raise invoices for the arrivals.
+ **Print Invoices** - Select whether to print invoices for the arrivals.
+ **Template Name** - The template to be used for the invoice.

Balances Listing (BK)
+++++++++++++++++++++
Use this routine to print an outstanding balance report.

+ **Cut-Off Period** - The last month period to take into account.
+ **Status** - All statuses or only an individual status.

Name and Address Labels
+++++++++++++++++++++++
Use this report to print name and address labels.

+ **Whole File** - Select whole file or individual contacts.
+ **Sort Order** - Sort by contact code or surname or postal code.
+ **Avery A4 Code** - The Avery code for the label being used.
+ **First Label Row** - The row of the first available blank label, 1-24.
+ **First Label Column** - The column of the first available blank label, 1-24.

Notes Listing (BK)
++++++++++++++++++
Use this routine to print any notes on the asset records.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Account Statements (BK)
+++++++++++++++++++++++
Use this routine to print statements of bookings.

+ **Template Name** - The template to use for the statements.
+ **Whole File** - Select whether to print all or a range of statements.
+ **From Booking** - The first booking to include.
+ **To Booking** - The last booking to include.

Reprint Invoices (BK)
+++++++++++++++++++++
Use this routine to reprint raised invoices.

+ **Template Name** - The template to use for the invoices.
+ **Document Mode** - Select whether to print the invoices as copies or as originals.
+ **Documents** - Select whether to print a range or individual invoices.
+ **From Number** - The first invoice to include.
+ **To Number** - The last invoice to include.

Summary Report (BK)
+++++++++++++++++++
Use this routine to produce a graph of bookings for a period not exceeding 12 months.

+ **Starting Period** - The starting period.
+ **Ending Period** - The ending period.
+ **Report By** - Select whether to report by beds occupied or monetary value.

+ **Action** - Select the parameters of the graph.
    + **Automatic** - Produce the graph for all booking statuses.
    + **Manual** - Select your own statuses.
    + **Exit** - Exit from the routine.
+ **Select Chart** - The type of graph to print. Please note that a pie chart can only be produced if a single status has been selected.
+ **Use Colour** - Select whether to use colours if pie chart or multiple statuses are selected.
