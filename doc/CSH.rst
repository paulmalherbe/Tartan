Cash Analysis
-------------
Control Record (CS)
...................
Use this routine to create an asset's register control record.

+ **G/L Integration** - Yes to integrate else No.
+ **Email Address** - The email address of the person in charge of cash, if not the default email address in the company record.

Cash Records (CS)
.................
This routine is only available if the Cash Analysis is not integrated with the General Ledger and is used to maintain cash income and expenditure account records.

+ **Acc-Num** - The account number.
+ **Description** - The account description.
+ **Tax Default** - The default VAT code for this record.

Capture Takings (CS)
....................
This routine is used to facilitate cashing up e.g. Clubs.

+ **Type** - Select the type of the transaction.
+ **Captured Date** - This is the date of the data capture.

The following tabs will now become available:

+ **Expenses**
    + **Trans-Date** - The date of the expense.
    + **Acc-Num** - The account number of the expense. If not integrated with the General Ledger, entering a zero will launch the Cash Records routine.
    + **Description** - The description of the expense.
    + **V** - The VAT code.
    + **Inc-Amount** - The inclusive amount of the expense.
    + **VAT-Amount** - The vat amount of the expense or Enter to automatically calculate.
+ **Income**
    + **Trans-Date** - The date of the receipt.
    + **Acc-Num** - The account number of the receipt. Entering zero will enable the masterfile maintenance routine.
    + **Description** - The description of the receipt.
    + **V** - The VAT code.
    + **Inc-Amount** - The inclusive amount of the receipt.
    + **VAT-Amount** - The vat amount of the receipt or Enter to automatically calculate..
+ **Cash**
    + **Cheques** - The total value of cheques received.
    + **Quant** - The quantity of the denominations received.

Cash Merge (CS)
...............
This routine is only available if the Cash Analysis is integrated with the General Ledger.

+ **From Date** - The starting date to include in the merge.
+ **To Date** - The ending date to include in the merge.

Cash Report (CS)
................
This routine is used to generate a report of cash takings captured.

+ **From Date** - The starting date to take into account.
+ **To Date** - The ending date to take into account.
+ **Float** - The total float.
+ **Output** - Select whether to view or print the list.
+ **Printer Name** - If print was selected select the relevant printer.
+ **Email** - If email has been enabled in the system record the following will also be available:
    + **Email Document** - Select whether to email the completed list.
    + **Email Address** - Enter an email address or leave blank for all members.
    + **Email Message** - Select whether to change the default message.
    + **View/Print Emailed Document** - Select whether to view or print the emailed list.
