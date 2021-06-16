Asset's Register
----------------
File Maintenance (AR)
.....................
Control Record (AR)
+++++++++++++++++++
Use this routine to create an asset's register control record.

+ **G/L Integration** - Yes to integrate else No.
+ **Sale of Assets** - If integrated, enter the general ledger account number for the `Sale of Assets` account.
+ **Receiver Dep** - Yes to have separate depreciation rates for the receiver.
+ **Last Dep Period** - Enter the last financial period that depreciation was raised.
+ **Email Address** - The email address of the person in charge of assets, if not the default email address in the company record.

Depreciation Codes (AR)
+++++++++++++++++++++++
Use this routine to create asset's register depreciation codes.

+ **Code** - Enter a code which can be up to 3 alphanumeric characters.
+ **Description** - Enter a description for the depreciation type.
+ **Type** - Select the type of depreciation, straight line or diminishing balance, for company and receiver, if applicable.
+ **Rates** - Enter the depreciation rates for company and receiver, if applicable, as follows:
    + **Year 1** - The first year's rate
    + **Years 2-7** - The following year's rates if applicable

Group Records (AR)
++++++++++++++++++
Use this routine to create group records as follows:

+ **Asset Group** - Enter a code which can be up to 3 alphanumeric characters.
+ **Description** - Enter a description for the group.
+ **Depreciation Code** - Enter a depreciation code, as created in `Depreciation Codes (AR)`_ above, for the group.
+ If integrated with general ledger you must enter the following account numbers:

    + **Asset Account** - This is the B/S Asset Account.
    + **Accum Account** - This is the B/S Accumulated Depreciation Account.
    + **Expense Account** - This is the P&L Depreciation Expense Account.

Masterfile Records (AR)
+++++++++++++++++++++++
Use this routine to edit an asset's description or depreciation code.

+ **Group** - Enter the asset group.
+ **Code** - Enter the asset code.
+ **Description** - Enter the asset description.
+ **Depreciation Code** - Enter the asset depreciation code.

Data Capture (AR)
.................
Opening Balances (AR)
+++++++++++++++++++++
Use this routine to capture all existing assets.

+ **Take-on Date** - This would normally be the end of the previous financial period but must always be the last day of the month otherwise there will be problems when the next depreciation run is made.
+ You can now either import a csv or xls file, in the correct format, by clicking on the `Import File` button or capture the assets manually.

    + **GRP** - Enter the asset group as created in `Group Records (AR)`_.
    + **Cod-Num** - Enter the asset code or number which can be up to 7 alphanumeric characters.
    + **Description** - Enter the description of the asset.
    + **Dep** - Enter the depreciation code to be applied to this asset. It will default to the group depreciation code but can also be a different one.
    + **Purch-Date** - Enter the original date of purchase of the asset.
    + **Cost** - Enter the total cost of the asset including any improvements and write-offs.
    + **Coy-Dep** - Enter the total company depreciation up to the take-on date,
    + **Rec-Dep** - Enter the total receiver depreciation, if applicable, up to the take-on date.

Payments, Receipts and Journal Entries (AR)
+++++++++++++++++++++++++++++++++++++++++++
Use these routines to capture all asset movements as and when required. In addition, if integrated with the G/L, assets can also be captured while capturing Payments and Receipts by allocating to the asset account as entered in `Group Records (AR)`_.

Depreciation (AR)
+++++++++++++++++
Use this routine to raise depreciation, as and when required.

+ **Cut-off Period** - Enter the last month period to take into account. Once you have confirmed the cut-off period the system will automatically determine the last period for which depreciation has been raised and then raise depreciation for each following month up to the cut-off period.

Reporting (AR)
..............
Groups Listing (AR)
+++++++++++++++++++
Use this routine to produce a report of all asset groups.

Batch Error Listing (AR)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (AR)
++++++++++++++++++++++++++++
Use this routine to print lists of transactions either by financial period or date of capture.

+ **Starting Period** - The first financial period to include in the report.
+ **Ending Period** - The last financial period to include in the report.
+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.
+ **Totals Only** - Yes or No.

Asset Statements (AR)
+++++++++++++++++++++
Use this routine to produce asset statements.

+ **Start Period** - The starting period.
+ **End Period** - The ending period.
+ **Product Group** - The asset group or blank for all.
+ **Asset per Page** - Whether or not to start each asset on a new page.

Asset Register (AR)
+++++++++++++++++++
Use this routine to print an asset register.

+ **Cut-Off Period** - The last month period to take into account.
+ **Report Type** - If applicable select either Company or Receiver.
+ **Asset Group** - Select an asset group or leave blank for all groups.
+ **Ignore Zero Items** - Select Yes to ignore all items sold or written off.

Notes Listing (AR)
++++++++++++++++++
Use this routine to print any notes on the asset records.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Toolbox (AR)
............
Change Asset Codes (AR)
+++++++++++++++++++++++
Use this routine to change existing asset groups and codes.

Interrogation (AR)
..................
This routine is for querying individual assets.
