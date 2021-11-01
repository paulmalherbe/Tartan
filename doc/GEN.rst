General Ledger
--------------
File Maintenance (GL)
.....................
Masterfile Records (GL)
+++++++++++++++++++++++
This routine is used to create or amend general ledger account records. For a new company you can **automatically populate** the company with standard accounts and reports by selecting the `Populate` button. You can also import a chart of accounts by selecting the `Import` button in which case the file must be in `csv` or `xls` format and must contain all the fields as listed below.

+ **Acc-Num** - The account number of the record. This is a numeric field and can have up to 7 digits. There is nothing special about this number it is only used to access the record.
+ **Account Type** - Select the applicable account type for the record.
+ **Description** - The account's description up to 30 characters in length.
+ **Allow Postings** - Whether or not direct postings are allowed to this account. Normally direct postings are not allowed to control accounts of subsidiary ledgers, e.g. Debtor's as they should be generated in the subsidiary ledger.
+ **Tax Default** - The V.A.T. code normally associated with postings to this account.

Once all accounts have been created, you should print a list of them by selecting `Chart of Accounts (GL)`_ from the reporting menu, and check that all accounts have been created correctly.

Control Accounts (GL)
+++++++++++++++++++++
This routine is used to create control accounts for the company. Control accounts are accounts that the system needs to know about in order to create double sided entries. You must create at least one bank as well as the retained income control records but preferably most of the others as well.

If you elected to **automatically populate** while creating masterfile records this would already have been done for you.

+ **Code** - Enter a valid control code e.g. **bank_1**. If you press F1 you  will be given a list of available codes which you can select from.
+ **G/L Acc-Num** - Enter the applicable general ledger account number for this code.
+ **Bank Account** - If the code is a bank account then you can enter the bank's account number here. This is required for importing bank statements.
+ **Import Format** - If you are going to import bank statements you must select the format you will be downloading or else `None` for no imports. The preferred format for internet banking is the OFX, or Open Financial eXchange, format.
+ **Date Format** - If you entered an import format, select the applicable date format. The date format for OFX is CCYYMMDD.

Inter Company Records (GL)
++++++++++++++++++++++++++
This routine only applies to systems which have multiple companies. This allows one to capture transactions in one company directly into another company's accounts e.g. capture a payment made by company one for a telephone account for company two. For the purposes of simplicity lets assume that we are presently in company 1's ledger and want to integrate company 2.

+ **Coy-Num** - The other company's number i.e. 2
+ **Acc-Num-1** - Company 2's inter company loan account number in company 1.
+ **Acc-Num-2** - Company 1's inter company loan account number in company 2.

Standard Journals (GL)
++++++++++++++++++++++
Use this routine to create, amend and delete standard journals.

+ **Number** - This is the journals reference number.
+ **Description** - This is the description of the journal.
+ **Frequency** - This is the frequency with which this journal is raised:
    + **M** - Monthly
    + **3** - Quarterly
    + **6** - Biannually
    + **Y** - Annually
+ **Starting Period** - The first period this journal is to be raised, (CCYYMM)
+ **Ending Period** - The last period this journal is to be raised, (CCYYMM)

Now all the journal lines must be entered as follows:

+ **Seq** - The line number.
+ **Acc-Num** - The general ledger account number.
+ **V** - The VAT code.
+ **Value** - The value of the transaction. Enter credits as minus values.

Please note that you will not be able to end this routine until the debits equal the credits.

Report Generator (GL)
+++++++++++++++++++++
Use this routine to create, amend and delete `Financial Statements (GL)`_ report formats.

+ **Company** - The company number or a 0 to create a general report for all companies.
+ **Report** - The report number. After this point certain options are available.
    + **Re-Sequence** - This re-sequences the whole report starting from 1
    + **Copy** - This allows you to copy an existing report
        + **Company Number** - The company number of the existing report
        + **Report Number** - The number of the existing report
    + **Print** - This allows you to print the report layout
+ **Type** - The type of report to create:
    + **B** - Balance Sheet
    + **P** - Profit and Loss
    + **O** - Any Other type of report
+ **Heading** - The report heading.
+ **Sequence**
    + **Seq-Num** - The report sequence number. To insert lines use decimals.
    + **Sequence Type** - The sequence type as follows.
+ **Heading (H)**
    + **Description** - The heading detail.
    + **Highlight** - Whether to print the heading in bold characters.
    + **New Page** - Whether to print the heading on a new page.
    + **Ignore Account Type** - In the case of B and P report types, when the account type changes the heading will automatically also change. To ignore this action select this option.
+ **Ledger (L)**
    + **From Account** - The first account in a range of accounts.
    + **To Account** - The last account in a range or 0 for only the first account.
    + **Highlight** - Whether to print the line in bold characters.
    + **Include Opening Balance** - Whether to include the opening balance.
    + **Accumulate Month Values** - Whether to accumulate the month values. This only applies to (M)onthly report types.
    + **Print Values**
        + **Yes** - Print
        + **No** - Do not print
        + **Debit** - Only print if the value is positive
        + **Credit** - Only print of the value is negative
    + **Normal Sign**
        + **Positive** - The value for this account is normally positive
        + **Negative** - The value for this account is normally negative
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the totals
        + **Subtract** - Subtract the value from the totals
        + **Ignore** - Do not add nor subtract the value
    + **Ignore Account Type** - In the case of B and P report types, when the account type changes the heading will automatically also change. To ignore this action select this option.
    + **Store Amount** - Whether you want to store the value for later
    + **Storage Number** - The number to use when storing the value
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the storage
        + **Subtract** - Subtract the value from the storage
        + **Ignore** - Do not add nor subtract the value
+ **Group (G)** - This is used to group a number of accounts together
    + **Group Number** - The group number
    + **Description** - The group description
    + **From Account** - The first account in a range of accounts.
    + **To Account** - The last account in a range or 0 for only the first account.
    + **Highlight** - Whether to print the line in bold characters.
    + **Include Opening Balance** - Whether to include the opening balance.
    + **Accumulate Month Values** - Whether to accumulate the month values. This only applies to (M)onthly report types.
    + **Print Values**
        + **Yes** - Print
        + **No** - Do not print
        + **Debit** - Only print if the value is positive
        + **Credit** - Only print of the value is negative
    + **Normal Sign**
        + **Positive** - The value for this account is normally positive
        + **Negative** - The value for this account is normally negative
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the totals
        + **Subtract** - Subtract the value from the totals
        + **Ignore** - Do not add nor subtract the value
    + **Ignore Account Type** - In the case of B and P report types, when the account type changes the heading will automatically also change. To ignore this action select this option.
    + **Store Amount** - Whether you want to store the value for later
    + **Storage Number** - The number to use when storing the value
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the storage
        + **Subtract** - Subtract the value from the storage
        + **Ignore** - Do not add nor subtract the value
    + **Chart Label**
+ **Stored (S)**
    + **Description** - The description of the stored value
    + **Highlight** - Whether to print the line in bold characters.
    + **Print Values**
        + **Yes** - Print
        + **No** - Do not print
        + **Debit** - Only print if the value is positive
        + **Credit** - Only print of the value is negative
    + **Normal Sign**
        + **Positive** - The value for this account is normally positive
        + **Negative** - The value for this account is normally negative
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the totals
        + **Subtract** - Subtract the value from the totals
        + **Ignore** - Do not add nor subtract the value
    + **Clear Stored Value** - Whether to zero the stored amount
    + **Storage Number** - The stored value's number
    + **Percentage of Stored Value** - The percentage of the stored value to print
+ **Total (T)** - All values are automatically added into or subtracted from totals numbered from 1 to 9.
    + **Description** - To description of the total or blank
    + **Highlight** - Whether to print the line in bold characters.
    + **Total Level** - The total number to print
    + **Print Values**
        + **Yes** - Print
        + **No** - Do not print
        + **Debit** - Only print if the value is positive
        + **Credit** - Only print of the value is negative
    + **Normal Sign**
        + **Positive** - The value for this account is normally positive
        + **Negative** - The value for this account is normally negative
    + **Clear Total** - Whether to zero the total
    + **Store Amount** - Whether you want to store the value for later
    + **Storage Number** - The number to use when storing the value
    + **Add, Subtract or Ignore**
        + **Add** - Add the value to the storage
        + **Subtract** - Subtract the value from the storage
        + **Ignore** - Do not add nor subtract the value
    + **Chart Label**
+ **Uline (U)**
    + **Highlight** - Whether to print the line in bold characters.
    + **Underline Type**
        + **Single** - Single line
        + **Double** - Double line
        + **Blank** - Blank line
+ **Calc (C)** - This allows an amount to be calculated.
    + **Description** - The description of the calculation
    + **Highlight** - Whether to print the line in bold characters.
    + **Calculation Base**
        + **Percentage** - The calculated value is a percentage
        + **Amount** - The calculated value is with an entered value
        + **Store** - The calculated value is with a stored value
    + **Calculation Type (Amount and Store only)**
        + **Plus** - The calculated value an addition of two values
        + **Minus** - The calculated value a subtraction of two values
        + **Multiply** - The calculated value a multiplication of two values
        + **Divide** - The calculated value a division of two values
    + **Storage Number (Base)** - The base stored amount
    + **Amount** - The amount or percentage to use for the calculation
    + **Storage Number (Calc)** - The second stored amount, if applicable
+ **Percent (P)** - This is a percentage of one stored amount against another stored amount.
    + **Description** - The description of the percentage
    + **Highlight** - Whether to print the line in bold characters.
    + **Storage Number (Base)** - The first stored amount
    + **Storage Number (Calc)** - The second stored amount

Detail Records (GL)
+++++++++++++++++++
Use this routine to create, amend and delete detail records used by `Financial Statements (GL)`_ report formats.

+ **Code** - A sequential number for the detail record.
+ **Description** - A description of the detail.

For each month in the financial year enter the following:

+ **Period** - A financial period i.e. CCYYMM
+ **Value** - A value for the period.

Stream Records (GL)
+++++++++++++++++++
Use this routine to create, amend and delete stream records used by `Financial Statements (GL)`_ report formats.

+ **Stream Number** - A sequential number for the stream record.
+ **Description** - A description of the stream.

For each report in the stream enter the following:

+ **Seq** - A sequence number starting at 0.
+ **T** - The report type, S(mall), L(arge), M(onthly) or C(ustom).
+ **CN** - If the report type is a C then this is the custom report number.
+ **C** - Consolidation code, Y or N.
+ **Rep** - Report number.
+ **G** - General report, Y or N.
+ **V** - Report contents, V(alues), B(udgets), C(ombined) or D(etail).
+ **Cod** - For contents type D, enter the applicable detail code.
+ **Z** - Ignore zeros, Y or N.
+ **O** - Print the options line on report, Y or N.
+ **N** - Print account numbers on the report, Y or N.
+ **Printer Name** - The printer name to print on or None.
+ **E-Mail Address** - An email address to send the report to or leave blank.

Bank Import Control (GL)
++++++++++++++++++++++++
Use this routine to create, amend and delete bank import control records. These records are used when importing bank statements to automatically create transactions for recurring entries e.g. charges, fees, interest, stop orders etc.

+ **Bank Account** - The G/L account number for the bank.
+ **Memo Code** - This is a 5 digit sequential number of the record. Entering a zero will automatically allocated the next number.
+ **Memo Desc Contains** - This together with the next two fields are used to correctly identify the transaction using the description appearing on the bank statement.
+ **Transaction Type** - Payment or Deposit.
+ **Allocation Company** - The company number to be debited or credited.
+ **Allocation Account** - The account number to be debited or credited.
+ **Chn** - The chain store code if the account number is the debtor's control account.
+ **Acc-Num** - If the account number is the creditor's or debtor's account enter the relevant creditor's or debtor's account number.
+ **Ageing Code** - If the account number is the creditor's or debtor's account select how to age the amount.
+ **Vat Code** - Enter the applicable V.A.T. code.

Data Capture (GL)
.................
Opening Balances (GL)
+++++++++++++++++++++
Use this routine to capture initial opening balances. You can also import these balances by selecting the `Import File` button in which case the file must be in `csv` or `xls` format and must contain the account number and balance fields.

+ **Acc-Num** - The account number.
+ **Balance** - The opening balance.

Budgets (GL)
++++++++++++
Use this routine to capture monthly budgets for a specific financial period. You can also import budgets by selecting the `Import File` button in which case the file must be in `csv` or `xls` format and must contain all the fields as detailed in the prompt when you hover your cursor over the button. There is also an `Auto Populate` button which will create budgets based on the previous year's actual plus or minus a standard rate.

+ **Acc-Num** - The account number.
+ **F** - `M` to enter a monthly budget or `A` to enter an annual budget amount.
+ **Period** - If `M` was selected then enter the period i.e. YYYYMM.
+ **Budget** - The budget value.

*Auto Populate*

If the auto populate button is used the following screen will appear:

+ **Use Previous Year's** - Actual or Budgets.
+ **Standard Rate (+-)** - The rate to be used to increase or decrease the previous year's amounts.
+ **Rounding to Nearest** - Select the rounding requirement.

You are now able to enter exclusions to the above parameters as follows:

+ **Acc-Num** - The generals ledger account number.
+ **Rate** - The rate to apply to this account.

On exiting the the screen with the <Esc> key the budgets will be populated.

Sales, Payments, Petty Cash, Purchases and Receipts (GL)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++
These data capture routines are similar in operation and therefore I will handle them together. Please note that if subsidiary books are integrated i.e. creditors and debtors, purchases and sales will not be available and an error message will be displayed if you attempt to access them.

As with most data capture routines you will first have to enter the `Batch Details`_ after which the following screens and fields apply:

+ **Transaction**
    + **T** - The transaction type (Petty Cash Only), (P)ayment or (R)eceipt.
    + **Reference** - The document's reference number.
    + **Date** - The date of the document.
    + **Amount** - The total inclusive value of the document.
    + **Details** - The description of the document.
+ **Allocation**
    + **Coy** - The company number in multi company installations.
    + **Acc-Num** - The general ledger account number to debit or credit.
    + **Alloc-Amt** - The inclusive amount to be allocated to this account.
    + **V** - The applicable V.A.T. code to apply to this allocation.
    + **VAT-Amount** - The V.A.T. amount, which can be overridden.
    + **Details** - The description of the allocation.
+ **ASS** - This only applies if the `Acc-Num` is one of the asset control accounts and assets have been integrated.
    + **Grp** - The asset's group code.
    + **Cod-Num** - The asset's code.
    + **M** - The transaction type i.e. New purchase, improvement, write off, depreciation or sale of asset.
    + **Amount** - The amount of the allocation.
    + **Details** - The description of the allocation.
+ **BKM** - This only applies if the `Acc-Num` is the booking control account and bookings have been integrated.
    + **Bkm-Num** - The booking number.
    + **Amount** - The amount of the allocation.
+ **CRS** - This only applies if the `Acc-Num` is the creditor's control account and the transaction type is payments or receipts and creditors have been integrated.
    + **Acc-Num** - The creditor's account number.
    + **Ref-No2** - A further reference number if applicable.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this account.
+ **DRS** - This only applies if the `Acc-Num` is the debtor's control account and the transaction type is payments or receipts and debtors have been integrated.
    + **Chn** - The chain store code, if chain stores apply.
    + **Acc-Num** - The debtor's account number.
    + **Ref-No2** - A further reference number if applicable.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this account.
+ **LON** - This only applies if the `Acc-Num` is the staff loans control account and loans have been integrated.
    + **Acc-Num** - The account number.
    + **Ln** - The loan number.
    + **Description** - The description of the loan, new loans only.
    + **Amount** - The amount of the loan.
    + **Rate-%** - The new interest rate to apply to the loan.
    + **Mth** - The interest rate to apply to the loan.
    + **Repayment** - The new amount to be repaid monthly.
+ **MEM** - This only applies if the `Acc-Num` is the members control account and members have been integrated.
    + **Mem-Num** - The member's number.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this member.
+ **RCA** - This only applies if the `Acc-Num` is one of the extended rentals control accounts and extended rentals have been integrated.
    + **Prm-Cod** - The premises code.
    + **Own-Cod** - The owners code.
    + **Tnt-Cod** - The tenants code, if applicable.
    + **Seq** - The contract sequence number, if applicable.
    + **T** - The movement type, if applicable.
    + **Amount** - The transaction amount.
    + **Details** - The transaction details.
+ **RTL** - This only applies if the `Acc-Num` is one of the basic rentals control accounts and basic rentals have been integrated.
    + **Prm-Cod** - The premises code.
    + **Acc-Num** - The account number.
    + **Seq** - The contract sequence number.
    + **Amount** - The transaction amount.
    + **Details** - The transaction details.
+ **SLN** - This only applies if the `Acc-Num` is the staff loans control account and salaries have been integrated.
    + **EmpNo** - The employee number.
    + **Ln** - The loan number.
    + **Amount** - The amount of the loan.
    + **Cde** - The new deduction code to use to repay the loan.
    + **Intr-%** - The new interest rate to apply to the loan.
    + **Ded-Amt** - The new amount to be deducted from earnings to repay the loan.

If you have allocated the transaction to a creditor's, debtor's or member's account you might be required to age the amount as described in `Ageing Transactions`_ above.

Manual Journal Entries (GL)
+++++++++++++++++++++++++++
Use this routine to capture manual journal entries. You can also import journals by selecting the `Import File` button in which case the file must be in `csv` or `xls` format and must contain all the fields as detailed in the prompt when you hover your cursor over the button.

As with most data capture routines you will first have to enter the `Batch Details`_ after which the following fields apply:

+ **Ref-Num** - The journal number.
+ **Date** - The date of the journal.
+ **Coy** - The company number in multi company installations.
+ **Acc-Num** - The general ledger account number to debit or credit.
+ **Amount** - The inclusive amount of the journal.
+ **V** - The applicable V.A.T. code to apply to this journal.
+ **VAT-Amt** - The V.A.T. amount, which can be overridden.
+ **Details** - The description of the journal.
+ **ASS** - This only applies if the `Acc-Num` is one of the asset control accounts and assets have been integrated.
    + **Grp** - The asset's group code.
    + **Cod-Num** - The asset's code.
    + **M** - The transaction type i.e. New purchase, improvement, write off, depreciation or sale of asset.
    + **Amount** - The amount of the allocation.
    + **Details** - The description of the allocation.
+ **BKM** - This only applies if the `Acc-Num` is the booking control account and bookings have been integrated.
    + **Bkm-Num** - The booking number.
    + **Amount** - The amount of the allocation.
+ **CRS** - This only applies if the `Acc-Num` is the creditor's control account and the transaction type is payments or receipts and creditors have been integrated.
    + **Acc-Num** - The creditor's account number.
    + **Ref-No2** - A further reference number if applicable.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this account.
+ **DRS** - This only applies if the `Acc-Num` is the debtor's control account and the transaction type is payments or receipts and debtors have been integrated.
    + **Chn** - The chain store code, if chain stores apply.
    + **Acc-Num** - The debtor's account number.
    + **Ref-No2** - A further reference number if applicable.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this account.
+ **LON** - This only applies if the `Acc-Num` is the staff loans control account and loans have been integrated.
    + **Acc-Num** - The account number.
    + **Ln** - The loan number.
    + **Description** - The description of the loan, new loans only.
    + **Amount** - The amount of the loan.
    + **Rate-%** - The new interest rate to apply to the loan.
    + **Mth** - The interest rate to apply to the loan.
    + **Repayment** - The new amount to be repaid monthly.
+ **MEM** = This only applies if the `Acc-Num` is the members control account and members have been integrated.
    + **Mem-Num** - The members number.
    + **Discount** - A discount amount.
    + **Amount** - The amount to be allocated to this member.
+ **RCA** - This only applies if the `Acc-Num` is one of the extended rentals control accounts and extended rentals have been integrated.
    + **Prm-Cod** - The premises code.
    + **Own-Cod** - The owners code.
    + **Tnt-Cod** - The tenants code, if applicable.
    + **Seq** - The contract sequence number, if applicable.
    + **T** - The movement type, if applicable.
    + **Amount** - The transaction amount.
    + **Details** - The transaction details.
+ **RTL** - This only applies if the `Acc-Num` is one of the basic rentals control accounts and basic rentals have been integrated.
    + **Prm-Cod** - The premises code.
    + **Acc-Num** - The account number.
    + **Seq** - The contract sequence number.
    + **Amount** - The transaction amount.
    + **Details** - The transaction details.
+ **SLN** - This only applies if the `Acc-Num` is the staff loans control account and salaries have been integrated.
    + **EmpNo** - The employee number.
    + **Ln** - The loan number.
    + **Amount** - The amount of the loan.
    + **Cde** - The new deduction code to use to repay the loan.
    + **Intr-%** - The new interest rate to apply to the loan.
    + **Ded-Amt** - The new amount to be deducted from earnings to repay the loan.

*Import File* button is used to import manual journal entries from a csv or excel file.
*View Entries* button will show you all the postings captured, including those which have scrolled off the screen, for checking purposes.
*End Batch* button will end the batch if debits equal the credits.
*Abort Batch* button will abort the current entries for the batch.

Please note that you will not be able to exit this routine until the debits equal the credits. Credits are entered as minus amounts.

Standard Journal Entries (GL)
+++++++++++++++++++++++++++++
Use this routine to raise standard journal entries as created using `Standard Journals (GL)`_.

As with most data capture routines you will first have to enter the `Batch Details`_ after which the following fields apply:

+ **Frequency** - Select the frequency of the journals to be raised.
+ **All Journals** - Select whether to raise all journals for the selected frequency.
+ **All Periods** - Select whether to raise journals for all periods from the start of the current financial period up to and including the batch header period.

Bank Statements (GL)
++++++++++++++++++++
Use this routine to capture bank statements. This is to facilitate reconciling the bank accounts with the bank statements. This routine can also be used to capture receipts, payments and journal entries affecting the bank account e.g. all entries on the bank statement not yet entered into the bank account can be processed using this routine.

As with most data capture routines you will first have to enter the `Batch Details`_.  The following buttons will then be available:

+ **Exit** - This exits out of the capture routine as per using the <Escape> key.
+ **Import Bank File** - This routine is used to import a bank statement file as described under `Control Accounts (GL)`_.

    Once you have selected the file to import the system will automatically flag all transactions which already exist on your database.

    If there are more than one transaction satisfying the comparison criteria these transactions will be displayed and you will have to select the transaction to be flagged. Should none of the transactions be the correct one, click the `Quit` button to skip allocating it.

    While importing, if a duplicate record is detected, i.e. a possible duplication of the import file, a message will be displayed giving you the choice of importing it or not.

    At the end of the import process a screen will be displayed showing all unallocated transactions. You must now capture these transactions as per the next option i.e. `Process Bank Data`.

+ **Process Bank Data** - This routine is to continue an import which was suspended for whatever reason. This is also the procedure for capturing unallocated transactions from the previous option i.e. `Import Bank File`. A screen showing all the unallocated transactions will display.

  Select a transaction to process by clicking on it or moving the cursor to it. You can now either hit the `Enter` key and  Continue from the `Details` field in the following section or click *Create Import Record* and follow the same procedure as outlined above in *Bank Import Control* and then click *Process Bank Data* again.

+ **Manual Entries** - Use this procedure to enter the bank statement manually. If there are unallocated records from a previous import then this will be highlighted and you will first have to allocated these using the `Process Bank Data` routine, before continuing.

    + **T** - Enter the transaction type i.e. (P)ayment or (R)eceipt.
    + **Ref-Num** - Enter the reference number. If the transaction already exists on your database it will be flagged as either paid or received i.e. will not appear on the bank reconciliation statement. If the transaction does not already exist you can capture it by entering the following fields:

    + **Date** - Enter the transaction date.
    + **Amount** - Enter the transaction amount.
    + **Details** - The details for this transaction.

    You will then be asked to confirm your entry and if you do so you will be able to allocate the transaction as in `Sales, Payments, Petty Cash, Purchases and Receipts (GL)`_ above.

Reporting (GL)
..............
Batch Error Listing (GL)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (GL)
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
+ **Include Other Companies** - Whether or not to include other companies. If yes, you will be prompted at a later stage to select which other companies to include.

Account Statements (GL)
+++++++++++++++++++++++
Use this routine to produce statements for individual ledger accounts.

+ **Whole File** - `Yes` for all accounts, `Range` for a range of accounts or `Singles` to select individual accounts.
+ **From Account** - If range was selected enter the starting account number.
+ **To Account** - If range was selected enter the ending account number.
+ **Starting Period** - The starting financial period in the financial year.
+ **Ending Period** - The ending financial period in the financial year.
+ **Separate Pages** - Select whether or not to print each account on a new page.

Trial Balance (GL)
++++++++++++++++++
Use this routine to produce a trial balance.

+ **Opening Balances Only** - Select whether or not to only print opening balances.
+ **Include Opening Balances** - Select whether or not to include opening balances.
+ **Starting Period** - The starting financial period in the financial year.
+ **Ending Period** - The ending financial period in the financial year.
+ **Ignore Zero Balances** - Select whether or not to ignore zero balances.

Financial Statements (GL)
+++++++++++++++++++++++++
Use this routine to produce financial statements using the information as set up with `Report Generator (GL)`_.

+ **Ending Period** - The last period, in the financial year, to take into account.
+ **Stream Number** - To print the reports as enumerated in a stream record as created using `Stream Records (GL)`_.
+ **Report Type** - Select the relevant report type as follows:
    + **Short** - Last Year, Description, Actual, Budget, Variance
    + **History** - Description, Last 3 Years Actual, Budget, Variance
    + **Long** - Acc-Num, Description, Current Month, Year-to-Date
    + **Month** - Acc-Num, Description, Open-Bal, Months x 12, Close-Bal
    + **Custom** - Customised Report
+ **Consolidate Companies** - Select whether or not to print a consolidated report. This is only applicable in a multi company installation.
+ **Departments** - Select whether or not to Departmentalize the report using the Department Numbers as stipulated in the System Record.
+ **Report Number** - The relevant report number as created using `Report Generator (GL)`_.
+ **General Report** - Select whether or not the report is a general report i.e. applies to all companies.
+ **Contents** - Select which values to use in the report.
+ **Detail Code** - If `Detail` was selected above, enter the detail code as created using `Detail Records (GL)`_.
+ **Variance** - Select which values to use as a variance or None for no variances.
+ **Ignore Zeros** - Select whether or not to ignore lines with zero balances.
+ **Print Options** - Select whether or not to include the selected options on the report heading.
+ **Account Numbers** - Select whether or not to include the account numbers in the report.

Chart of Accounts (GL)
++++++++++++++++++++++
Use this routine to produce a chart of accounts.

+ **Sort Order** - Select the order by which the report must be sorted.

Notes Listing (GL)
++++++++++++++++++
Use this routine to print any notes on the general ledger accounts.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Bank Reconciliation (GL)
++++++++++++++++++++++++
Use this routine to produce a bank reconciliation statement.

+ **Bank Account** - The bank account number.
+ **Accounting Period** - The relevant period in the financial year.

Imported Bank Statements (GL)
+++++++++++++++++++++++++++++
Use this routine to produce a report of imported bank statements.

+ **Bank Account** - Bank account number.
+ **From Date** - The starting date.
+ **To Date** - The ending date.
+ **Unallocated Only** - Whether to only print entries which have not yet been allocated.

Toolbox (GL)
............
Change Account Numbers (GL)
+++++++++++++++++++++++++++
Use this routine to change account numbers within a company.

+ **Old Number** - The current account number to change.
+ **New Number** - The new account number. It must not already exist.

Copy Masterfile Records (GL)
++++++++++++++++++++++++++++
Use this routine to copy accounts from another company.

+ **Copy From Company** - The company number from which to copy.
+ **Include ...** - Select what additional data is to be copied.
+ **Equalise Year Ends** - Select whether to equalise year ends.

Integrated Controls Report (GL)
+++++++++++++++++++++++++++++++
Use this routine to produce a report showing the balance status of integrated systems and their respective control accounts.

+ **Cut Off Period** - The relevant period in the financial year.

Intercompany Accounts Report (GL)
+++++++++++++++++++++++++++++++++
Use this routine to produce a report showing the balance status of intercompany accounts in a multi company installation.

Initialise Bank Reconciliation (GL)
+++++++++++++++++++++++++++++++++++
Use this routine to initialise the bank reconciliation.

+ **Bank Account** - The bank account number.
+ **Last Period** - The last reconciled period.
+ **Clear History** - Select whether or not to mark all transactions up to the `Last Period` as being cleared through the bank.

Now capture all the outstanding transactions as at the `Last Period`.

+ **T** - Enter the transaction type i.e. (P)ayment or (R)eceipt.
+ **Ref-Num** - Enter the transaction reference number.

Delete Imported Bank Statements (GL)
++++++++++++++++++++++++++++++++++++
Use this routine to delete imported bank statements.

+ **Bank Account** - The bank account number.
+ **From Date** - The first date to take into account. Enter 0 for the beginning.
+ **To   Date** - The last date to take into account. Enter 0 for the end.
+ **Unallocated Only** - Only delete unallocated transactions.

Merge Accounts Into a Control (GL)
++++++++++++++++++++++++++++++++++
Use this routine to transfer all transactions of selected accounts into a control account and then delete the accounts e.g. Transfer individual loan accounts into a loan's control account.

+ **Control Number** - The control account number.

Interrogation (GL)
..................
Use this routine to interrogate accounts.

+ **Normal** - Use this routine for querying individual general ledger accounts.
+ **Financials** - Use this routine for querying individual general ledger accounts by report. The report will appear in spreadsheet format and individual month's transactions can be viewed by double clicking on the Actual balance.
