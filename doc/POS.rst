Point of Sale
-------------
Terminal Records (PS)
.....................
Use this routine to create or amend the point of sale terminal records.

+ **Terminal Name** - The name of the terminal or ip address.
+ **Location** - The stores location if there are more than 1 location.
+ **Full Screen** - Whether to use the full screen or only the current screen.
+ **Print Document** - Whether to print a sales document.
+ **Document Type** - Select the relevant document type.
+ **Printer Name** - The printer to use for the sales slip.
+ **Paper Width** - The width of the sales slip printer roll, in the case of a document type 'Slip'.
+ **Cut Paper Code** - The code for cutting the paper, in the case of a document type 'Slip'.
+ **Open Draw Code** - The code for opening the cash drawer, in the case of a document type 'Slip'.
+ **Document Template** - The template to use for the sales document if applicable.

Data Capture (PS)
.................
Use this routine to capture cash and account sales.

Account Sale (PS)
+++++++++++++++++
Enter the account details as follows:

+ **Account Number** - The account number.
+ **Price Level** - If more than one price level is in use select the appropriate one.

Cash and Account Sales (PS)
+++++++++++++++++++++++++++
The point of sales screen's buttons and actions are for the most part self explanatory however the normal procedure would be as follows:

Item Selection Screen (PS)
~~~~~~~~~~~~~~~~~~~~~~~~~~
+ Select the relevant pink group button. If necessary select the Left or Right button to show more groups.
+ Select the relevant blue item button. If necessary select the Left or Right button to show more items.
+ In both cases a search facility is available by clicking in the Description column on the left hand side of the screen.
+ Once an item has been entered the Quantity can be changed by clicking in the Quantity column on the left hand side of the screen.
+ Similarly the Price can be changed by clicking in the Price column on the left hand side of the screen.
+ In addition once an item is entered the *Refund*, *Void*, *Payment* and *Undo* buttons become available.
+ Continue until all items have been entered.
+ Select the required button. In the case of all buttons, excepting *Void*, the payment allocation screen will appear.

Payment Allocation Screen (PS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+ **Discount** - To enter a discount select the discount button and then enter the percentage by selecting the relevant numeral buttons and ending by selecting the *Enter* button.
+ **Voucher** - To enter a voucher select the voucher button and then enter the voucher value by selecting the relevant numeral buttons and ending by selecting the *Enter* button.
+ **C/Card** - To pay by credit card select the c/card button.
+ **Cash** - To pay by cash select the cash button and then enter the amount tendered by selecting the relevant numeral buttons and ending by selecting the *Enter* button.
+ **Account Sales** only require the *Enter* button.

Cash Up (PS)
++++++++++++
Select this button to go to the Cash Declaration routine.

Cash Declaration (PS)
.....................
Select this routine to enter the cash, voucher and credit card takings.

+ **Date** - The date of the declaration.
+ **Float** - The starting float.
+ **Vouchers** - The total of the vouchers tendered.
+ **C/Cards** - The total of the credit card slips tendered.
+ **Output** - Select whether to view or print the declaration.
+ **Quant** - Enter the cash takings by entering the quantity by denomination.

In order to correct an incorrect entry re-enter the Cash declaration routine and enter the date. The declaration will be displayed and changes can be made by re-entering the various fields.

Cash Reconciliation (PS)
........................
This routine is used to compare the cash declaration with the actual entries.

+ **Host name** - The relevant terminal name.
+ **Cashier Name** - The cashier's name.
+ **Declaration date** - The date of the declaration.
+ **Output** - Whether to view or print the reconciliation.
+ **Printer name** - The printer device name, if relevant.
