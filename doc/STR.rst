Stores Ledger
-------------
File Maintenance (ST)
.....................
Control Record (ST)
+++++++++++++++++++
Use this routine to create and amend the store's control record.

+ **G/L Integration** - Select whether to integrate with the general ledger.
    + **Yes**
        + **Stock on Hand** - If integrated this is the general ledger account number for the `Stock on Hand` account.
        + **Stock Reconciliation** - If integrated this is the general ledger account number for the `Stock Reconciliation` account. This could also be referred to as the `Stock Adjustment` account.
        + **P.O.S. Cash** - If integrated this is the general ledger account number for the `Cash Payments` account.
        + **P.O.S. Credit Cards** - If integrated this is the general ledger account number for the `Credit Card Payments` account.
        + **P.O.S. Vouchers** - If integrated this is the general ledger account number for the `Vouchers Cashed` account.
+ **Multiple Locations** - Select whether to allow multiple stores locations or warehouses.
+ **Number of Price Levels** - Select the number of price levels up to a maximum of five.
+ **Automatic Markup** - Select whether to price items automatically based on percentages stored in the group and/or masterfile records. These can be overridden for specific items by creating a Price Record for the item by using `Fixed Selling Prices (ST)`_.
+ **Orders Template** - The template to use to purchases orders.
+ **Email Address** - The email address of the person in charge of stores, if not the default email address in the company record.

Units of Issue (ST)
+++++++++++++++++++
Use this routine to create, amend and delete units of issue records.

+ **Unit of Issue** - This is a unit of issue code.
+ **Description** - This is a further description of the unit of issue code.

Product Groups (ST)
+++++++++++++++++++
Use this routine to create, amend and delete product group records.

+ **Product Group** - This is a three character code for the product group.
+ **Description** - This is the description of the group.
+ **Vat Code** - This is the default VAT Code for the group.
+ **Sales Account** - If integrated with the general ledger this is the default sales account for the group.
+ **COS Account** - If integrated with the general ledger this is the default cost of sale account for the group.
+ **Mark-Up Percent** - This is the default mark-up percentage for the group.
+ **Re-Order Factor** - This is the percentage to alter the average monthly usage of items in the group to calculate a re-order level.

Locations (ST)
++++++++++++++
If multiple locations has been enabled in the control record, use this routine to create, amend and delete location records. The location code is a single digit or character. The default location is 1.

Masterfile Records (ST)
+++++++++++++++++++++++
Use this routine to create, amend and delete store's ledger records.

+ **Grp** - The product group.
+ **Code** - The product code up to 20 characters long.
+ **Loc** - The location where this item is stored.
+ **Basic-A**
    + **Type of Item** - Select whether the item is a normal item or a recipe.
    + **Description** - The description of the item.
    + **Unit of Issue** - The unit of issue code relating to the item.
    + **Units Per Pack** - The number of units making up the pack. If applicable, the price for a single item would be the purchase or selling price divided by this number.
    + **Value Indicator** - Select the cost price value indicator as follows:
        + **Average** - The cost price will be the value divided by the quantity.
        + **Standard** - The cost will be a fixed cost price.
        + **None** - The item will not have a cost print. This is normally used for goods which are not purchased and are not standard e.g. recipes, travelling, labour etc.
    + **VAT Code** - The default vat code for the item.
    + **Exclusive Chain Store** - If chain stores are enabled in the debtor's ledger and the item is exclusive to a Chain Store, this is the Chain Store code.
    + **Exclusive Account** - If the item is exclusive to a debtor's account, this is the debtor's account number.
+ **Sales Account** - If integrated with the general ledger this is the default sales account for the item.
+ **COS Account** - If integrated with the general ledger this is the default cost of sale account for the item.
+ **Basic-B**
    + **Bin Number** - The bin number for the item, if applicable.
    + **Re-Order Indicator** - Select how re-order levels are maintained:
        + **Manual** - Manually entered.
        + **Automatic** - Automatically generated.
        + **Zero** - No re-order level nor re-order quantity.
    + **Re-Order Level** - The initial re-order level.
    + **Re-Order Quantity** - The initial re-order quantity.
    + **Selling Price Markup** - The default mark-up to calculate selling price.
+ **Recipes**
    + **If the item is a recipe enter all the items making up the recipe**
        + **Grp** - The product group.
        + **Code** - The product code.
        + **Quantity** - The quantity of the item needed for the recipe.

Fixed Selling Prices (ST)
+++++++++++++++++++++++++
Use this routine to create and amend product selling prices. These prices will take preference where automatic markup selling prices have been enabled.

+ **Product Group** - The product group.
+ **Product Code** - The product code.
+ **Location** - The location code, if applicable.
+ **Price Level(s)** - The price for each applicable price level.

Data Capture (ST)
.................
Purchase Orders (ST)
++++++++++++++++++++
Use this routine to place purchase orders against suppliers.

+ **Printer Selection**
    + **Template Name** - The template to be used for the purchase orders.
    + **Order Date** - The date of the orders.

+ **Order Header**
    + **Action** - Select the applicable action to perform.
        + **New** - Create a new order.
        + **Amend** - Amend an existing order.
        + **Receive** - Receive an existing order.
        + **Cancel** - Cancel an existing order.
    + **Ord-No** - The order number of an existing order.
    + **Loc** - The location placing the order.
    + **Acc-No** - The creditor's account number.
    + **Ord-By** - The code of the representative placing the order.
    + **Del-No** - The delivery note number when receiving an order.
    + **Date** - The date of the delivery when receiving an order.

**Order Body**
    + **Grp** - The product group.
    + **Product-Code** - The product code.
    + **Description** - The product description to appear on the order.
    + **Quantity** - The quantity ordered.
    + **V** - The VAT code to apply.
    + **Price** - The exclusive cost price.
    + **Dis-%** - The percentage of discount allowed.

**Buttons**
    + **Cancel** - Cancel a new order whilst in the body.
    + **DelAdd** - Enter a delivery address.
    + **Ribbon** - Enter ribbon details e.g. Contact Person, VAT Number etc.
    + **Message** - Enter a message to print on the order.
    + **Edit** - Edit the body of the order.
    + **Reprint** - Reprint an existing order.
    + **CrsMaint** - Maintain creditor's records.
    + **CrsQuery** - Interrogate creditor's records.
    + **StrMaint** - Maintain store's records.
    + **StrQuery** - Interrogate store's records.
    + **Exit** - Exit purchase orders and return to the main menu.
    + **Accept** - Accept the order and print/email, if applicable.

Goods Received Notes (ST)
+++++++++++++++++++++++++
Use this routine to receive goods into stock without creating purchase orders.

+ **Header**
    + **GRN Number** - Goods received number.
    + **Date** - Date received.
    + **Order Number** - Order number, if applicable.
+ **Body**
    + **Grp** - The product group.
    + **Product Code** - The product code.
    + **L** - The location code, if applicable.
    + **Quantity** - The number of units ordered.
    + **Unit-Cost**- The cost price per unit.
    + **Dis-%** - The allowed discount, if applicable.
    + **Unit-Sell** - The selling price per unit.

Goods Issued Notes (ST)
+++++++++++++++++++++++
Use this routine to issue stock i.e. journalise stock out.

+ **Grp** - The product group.
+ **Product Code** - The product code.
+ **L** - the location code, if applicable.
+ **Quantity** - The number of items issued.
+ **Recipe Items** - If the product is a recipe the items in the recipe will be displayed and you can edit them by selecting the applicable item and changing the quantity. When ready to continue press the `Exit` button.
+ **G/L-Acc** - If integrated with the general ledger, enter the applicable general ledger account number and details.

Location Transfers (ST)
+++++++++++++++++++++++
Use this routine to transfer stock from one location to another, if applicable.

+ **Grp** - The product group.
+ **Product Code** - The product code.
+ **Quantity** - The quantity to transfer.
+ **F** - The location from where the items are being transferred.
+ **T** - The receiving location.
+ **Details** - The details of the transfer.

Stock Take (ST)
...............
Stock Take Report (ST)
++++++++++++++++++++++
Use this routine to produce a stock take report. This report is used to facilitate counting physical stock.

+ **Sort Order** - Select the order the items must appear on the report.
+ **Location** - The location code, if applicable.
+ **First Bin Number** - The starting bin number, if applicable.
+ **Last Bin Number** - The ending bin number, if applicable.
+ **Product Group** - The product group, if applicable.
+ **Quantity to Print** - The number of items to print, if applicable.
+ **Ignore Zero Balances** - Select whether to ignore items with zero balances.

Stock Take Returns (ST)
+++++++++++++++++++++++
Use this routine to enter physical stock count quantities.

+ **Header**
    + **Sort Order** - Select the order the items will be entered.
    + **Location** - The location code, if applicable.
    + **Auto Sequence** - Whether to automatically display the next item in order.
    + **First Bin Number** - The starting bin number, if applicable.
    + **First Group** - The starting product group, if applicable.
    + **First Code** - The starting product code, if applicable.
    + **Cost Prices**
        + **No** - Cost Prices will be shown but cannot be entered.
        + **Last** - Last Cost Prices will be displayed and can be altered.
        + **Average** - Average Cost Prices will be displayed and can be altered.
+ **Body**
    + **Grp** - The product group if not auto sequence.
    + **Product Code** - The product code if not auto sequence.
    + **Unit Cost** - The unit cost price, if applicable.
    + **Quantity** - The quantity in stock.

Stock Take Variance Report (ST)
+++++++++++++++++++++++++++++++
Use this routine to produce a report of variances between the stock in the ledger as opposed to the stock counted.

Stock Take Merge (ST)
+++++++++++++++++++++
Use this routine to create adjustments to the stock records to bring the ledger in line with the actual stock counted.

Reporting (ST)
..............
Units Of Issue Listing (ST)
+++++++++++++++++++++++++++
Use this routine to produce a list of all units of issue records.

Product Groups Listing (ST)
+++++++++++++++++++++++++++
Use this routine to produce a list of all product groups.

Locations Listing (ST)
++++++++++++++++++++++
Use this routine to produce a list of all locations.

Batch Error Listing (ST)
++++++++++++++++++++++++
Use this routine to print any unbalanced batches.

+ **Type** - The transaction type or 0 for all.
+ **Batch-Number** - The batch number or blank for all.

Transaction Audit Trail (ST)
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

Price Lists (ST)
++++++++++++++++
Use this routine to produce a list of selected products' prices.

+ **Product Group** - The product group, if applicable.
+ **Ignore Out of Stock** - Select whether to ignore items with zero balances.
+ **Report Type** - Select the applicable report type. If `Cost Price` is selected no more details will be required.
+ **Price Level** - If level prices are enabled select enter the required level or zero for all.
+ **Ignore Un-priced** - Select whether to ignore items without a selling price.
+ **VAT Inclusive** - Print VAT inclusive or exclusive selling prices.
+ **Show Cost Price** - Select whether to include the cost price on the report.

Master Code List (ST)
+++++++++++++++++++++
Use this routine to to produce a master list of products by type.

Recipe Listing (ST)
+++++++++++++++++++
Use this routine to to produce a listing of recipes.

+ **Product Group** - The product group, if applicable.
+ **Whole File** - Select whether to print all available records or individuals.
+ **Recipe per Page** - Select whether to print each recipe on a separate page.

Stock Movements (ST)
++++++++++++++++++++
Use this routine to produce a report of selected products' movements.

+ **Start Period** - Enter the starting financial period.
+ **End Period** - Enter the ending financial period.
+ **Location** - Enter the location code, if applicable.
+ **Product Group** - Enter the product group, if applicable.
+ **Exclude Zeros** - Select whether to include items with zero balances.

Purchase Orders (ST)
++++++++++++++++++++
Use this routine to produce a report of purchase orders.

+ **Location** - The location code, if applicable.
+ **Outstanding Only** - Select whether to only print outstanding orders.
+ **From Order Number** - Enter the starting order number, if applicable.
+ **To Order Number** - Enter the ending order number, if applicable.

Stock On Hand (ST)
++++++++++++++++++
Use this routine to produce a stock on hand report.

+ **Reporting Period** - Enter the relevant financial period.
+ **Location** - Enter the location code, if applicable.
+ **Product Group** - Enter the product group, if applicable.
+ **Ignore Zero Balances** - Select whether to ignore items with zero balances.

Stock Accounts (ST)
+++++++++++++++++++
Use this routine to produce product statements showing opening balances and movements.

+ **Start Period** - Enter the starting financial period.
+ **End Period** - Enter the ending financial period.
+ **Location** - Enter the location code, if applicable.
+ **Product Group** - Enter the product group, if applicable.
+ **New Account on New Page** - Select whether to start a new page for each item.

Notes Listing (ST)
++++++++++++++++++
Use this routine to print any notes on the store's ledger accounts.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Item Labels (ST)
++++++++++++++++
Use this routine to produce price tags for products.

+ **Reporting Date** - The report date.
+ **Location** - The location code, if applicable.
+ **Product Group** - The product group or blank for all.
+ **Product Code** - The product code or blank for all.
+ **Item Types** - Either Normal, Recipe or All.
+ **Value Indicator** - Either Yes, No or All.
+ **Include Out of Stock** - Whether to include items with zero balances.
+ **Cost Price Code** - The code to use for cost prices e.g. ABCDEFGHIJ representing 0123456789.
+ **Avery A4 Code** - The code of the Avery label to use.
+ **First Label Row** - The first available blank label row.
+ **First Label Column** - The first available blank label column.

Toolbox (ST)
............
Change Product Codes (ST)
+++++++++++++++++++++++++
Use this routine to change product codes.

Revalue Stock Records (ST)
++++++++++++++++++++++++++
Use this routine to revalue stock records by average or last cost. It also provides for the zeroing of items with negative balances.

Cancel Purchase Orders (ST)
+++++++++++++++++++++++++++
Use this routine to cancel outstanding purchases orders.

Stock Redundancy (ST)
+++++++++++++++++++++
Use this routine to flag store's items as redundant. The following buttons are available:

+ **Generate** - Automatically mark items, with a zero balance and are inactive, as redundant.
    + **Months Inactive** - The number of months the items have been inactive.
+ **Create** - Mark individual items, which have a zero balance, as redundant.
+ **Restore** - Mark individual items, which are redundant, as normal.
+ **Exit** - Exit the routine.

Interrogation (ST)
..................
This routine is for querying individual Store's Ledger Accounts.
