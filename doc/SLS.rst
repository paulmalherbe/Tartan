Sales Invoicing
---------------
File Maintenance (SI)
.....................
Control Record (SI)
+++++++++++++++++++
Use this routine to create or amend the sales invoicing control record.

+ **Delivery Notes** - Whether to print delivery notes.
+ **Print Values** - Whether to include values on delivery notes.
+ **Invoice Template** - Enter the template to be used for sales documents.
+ **Email Address** - The email address of the person in charge of sales, if not the default email address in the company record.

Sales Documents (SI)
....................
Use this routine to produce sales documents.

Date and Printer Selection (SI)
+++++++++++++++++++++++++++++++
+ **Document Date** - This is the actual date of the invoices.
+ **Delivery Notes** - Whether or not to print delivery notes.
+ **Print Choice** - Select whether to print, view or simply store the invoices without printing.
+ **Printer Name** - If printing was selected, this is the printer to use.
+ **E-Mail** - Whether to email the invoices. This will be dependent on a valid email address on the debtor's record as well as a valid `SMTP Server` in the `System Record Maintenance`_.

Sales Document (SI)
+++++++++++++++++++
+ **Type** - The document type.
+ **Mode** - The mode of payment. Cash invoices will automatically be debited to a debtor's account `CASHSLS`.
+ **Acc-Num** - The account code for account mode.
+ **Rep** - The salesman's code.
+ **Level** - The price level for this customer. It will default to whatever is on the debtor's masterfile.
+ **Grp** - The product group.
+ **Product-Code** - The product code.
+ **Description** - The product description and or details.
+ **L** - The location from which this item is being sold from.
+ **Quantity** - The quantity being sold.
+ **V** - The value added tax code.
+ **Price** - The inclusive or exclusive selling price depending on the method.
+ **Dis-%** - The trade discount percentage.
+ **Value** - The value of the sale. This is a display field only.
+ **Available Buttons**
    + **Cancel** - This button is for cancelling the current invoice.
    + **DelAdd** - This button is for entering a delivery address.
    + **Ribbon** - This button is for entering the ribbon line.
    + **Messag** - This button is for including an invoice message.
    + **Edit** - This button is for editing document lines.
    + **Reprint** - This button is for reprinting documents.
    + **DrsMaint** - This button is for creating new debtor's accounts.
    + **DrsQuery** - This button is for interrogating a debtor.
    + **StrMaint** - This button is for creating new store's accounts.
    + **StrQuery** - This button is for interrogating a stores item.
    + **Exit** - To exit the sales routine.
    + **Accept** - This button is to accept and complete the document.

Reporting (SI)
..............
Sales By Product (SI)
+++++++++++++++++++++
Use this routine to produce a sales by product report.

Period Sales By Product (SI)
++++++++++++++++++++++++++++
Use this routine to sales by product by period report.

Product Sales History (SI)
++++++++++++++++++++++++++
Use this routine to produce a product sales history report.

Sales By Customer By Product (SI)
+++++++++++++++++++++++++++++++++
Use this routine to produce a product sales by customer report.

Sales By Salesman (SI)
++++++++++++++++++++++
Use this routine to produce a product sales by salesman report.

Salesman's Sales History (SI)
+++++++++++++++++++++++++++++
Use this routine to produce a salesman's sales history report.

Toolbox (SI)
............
Change Customer Order Number (SI)
+++++++++++++++++++++++++++++++++
Use this routine to change the customer's order number on the invoice.

+ **Invoice Number** - The invoice number to be changed.
+ **Customer Order Number** - Change to the required order number.

Cancel Outstanding Documents (SI)
+++++++++++++++++++++++++++++++++
Use this routine to cancel all outstanding sales documents older than a number of months.

+ **Documents** - Select the Document Type to cancel or select All Types.
+ **Months Outstanding** - The number of months the documents must be older than.
