Utilities
---------
Telephone Directory
...................
Use this routine to manage a telephone directory.

All the fields are self explanatory with the exception of the following:

+ **Directory Groups** - These are 3 letter group codes. If the code does not exist you will have to also enter the group description. This code can also be used in the bulk mailing module.

+ **Directory Entries** - These are the individual directory entries. All the fields are self explanatory with the exception of the 'Contact Groups' which is a comma separated list of directory groups.

+ **Buttons**
    + **Back** - Select this button to display the previous directory entry.
    + **Forward** - Select this button to display the next directory entry.
    + **Import** - Select this button to import all contacts from other sources e.g. Creditors, Debtors, Members, Bookings etc.
    + **Notes** - Select this button to maintain notes relating to this entry.
    + **Print** - Select this button to print all entries or the current entry.
    + **Apply** - Select this button to apply current addition or change.
    + **Contacts** - Select this button to maintain contacts of the current entry.
    + **Cancel** - Select this button to cancel any current additions or changes.
    + **Quit** - Select this button to quit the application.

Bulk Mail Utility
.................
Use this routine to send bulk MAIL or bulk SMSes. In order to use the MAIL facility you must enter a valid SMTP server in the `System Record`. In order to use the SMS facility you must register with www.smsportal.co.za and then enter your username and password in the `System Record` using `System Record Maintenance`_.

+ **Delivery Type** - The available delivery types will depend on what is entered in the `System Record` and can be either E-Mail, SMS or both.
+ **List to Use** - The available lists will depend on the systems being used and can contain Bookings, Bowls, Creditors, Debtors, Members and Directory (Telephone). In addition to the lists, CSV or XLS files can also be used, as long as they contain a name and an email address and or a cell number. Please note that Creditors and Debtors do not have SMS capabilities.
    + **Bookings** - This list accesses the tartan booking's contacts.
        + **Individuals** - Allow selection of individual recipients.
    + **Bowls** - This list accesses the tartan bowl's tabs.
        + **Category** - Allow selection by category.
        + **Gender** - Allow selection by gender.
        + **Individuals** - Allow selection of individual recipients.
    + **Creditors** - This list accesses the tartan creditor's masterfile.
        + **Email To** - Select the recipient.
        + **Individuals** - Allow selection of individual recipients.
    + **Debtors** - This list accesses the tartan debtor's masterfile.
        + **Email To** - Select the recipient.
        + **Activity** - Allow selection by business activity.
        + **Type** - Allow selection by business type.
        + **Individuals** - Allow selection of individual recipients.
    + **Members** - This list accesses the tartan member's masterfile.
        + **Category** - Allow selection by membership category.
        + **Gender** - Allow selection by gender.
        + **Personalise** - Allow personalising of the recipient.
        + **Name Detail** - Select whether to use the names or initials.
        + **Individuals** - Allow selection of individual recipients.
    + **Directory** - This list accesses the tartan telephone directory.
        + **Group Selection** - Allow selection by group.
        + **Include Contacts** - Include the recipient's contacts.
        + **Individuals** - Allow selection of individual recipients.
    + **Import File** - This is a csv, xls or ods file containing title, surname, names, email address and/or a mobile number, 
        + **Personalise** - Allow penalisation of the recipient.
        + **Title** - Select whether or not to use titles.
        + **Name Detail** - Select whether to use the names or initials.
        + **Import File Parameters**
            + **File Name** - The file name to import
            + **Sheet Name** - The sheet name in the case of spreadsheets.
            + **Ignore Invalid Lines** - Select Yes or No to ignore invalid lines.
            + **Columns** - Depending on your selections the following columns could appear:
                + **Email Address** - The column containing the email address.
                + **Title** - The column containing the title.
                + **Surname** - The column containing the surname.
                + **Names** - The column containing the names.
+ **Skip Delivery Errors** - Select whether or not to skip invalid email addresses.
+ **Subject** - The subject of the email.
+ **In-line Attachment** - Any in-line image to be included in the email.
+ **Separate Attachment** - Any attachment to be attached to the email.
+ **Message** - Any text message. In order to get the recipients name in the message use one of the following methods:
    + **{{name}}** - Use this method if the recipient has separate surname and names fields.
    + **{{surname}}** - Use this method if the recipient has a single name field where the surname and names are comma separated e.g. Malherbe, Paul.

Report Generator
................
Use this routine to generate ad hoc SQL reports. It is not necessary to know the SQL language but it is beneficial.

+ **Name** - A name for the report.
+ **Description** - A description of the report.
+ **Heading-1** - The first heading of the report.
+ **Heading-2** - A second heading, if applicable.

The following screens are now available:

+ **Tables** - These are the tables to be used to generate the report. At least one table must be selected.
    + **Table Sequence** - A sequential number of the line to enter or edit.
        + **Tables** - The table name. F1 will give a list of available tables.
+ **Joins** - These are further tables to be joined to the ones selected in `Tables`.
    + **T** - The type of join. F1 gives a list of available types.
    + **Tables** - The table which must be joined.
    + **Join Columns** - The columns to be used for the join.
+ **Columns** - These are the table columns to show in the report. If no columns are selected, all columns will be used.
    + **Column Sequence** - A sequential number of the line to enter or edit.
        + **T** - The type of column.
            + **C** - An actual column in the table.
                + **Label** - The column name. You will be shown a list of columns to select from.
            + **E** - An expression e.g. Sum, Avg, Count etc.
                + **Label** - You will have to type a name for the expression. You will then be offered a selection of expression types and depending on your choice a further selection of options.
                + **Expression** - The generated expression will now be displayed and you can either accept or edit it.
        + **Heading** - The column heading.
        + **TP** - The type of column. F1 will show all available types.
        + **Size** - The width of the column in characters.
        + **G** - Whether or not to group the report on this column.
        + **S** - Whether or not to print sub totals for this column.
        + **Narration** - If sub totals was selected, enter the narration of the sub total.
        + **P** - If sub totals was selected, select whether or not to start a new page after each sub total.
        + **G** - If the column type is numeric, select whether or not to print a grand total for the column.
        + **D** - Whether or not to actually display the column in the report or simply to use it for totals etc.
+ **Variables**
+ **Exceptions**
+ **Order**

Report Stream
.............
Use this routine to print or mail various selected reports.

+ **Report Group** - Enter a *Report Group* name.
+ **Output** - Select whether to E-Mail or Print the reports.
+ **Printer Name** - Select the printer on which to print the reports.
+ **From Address** - The mail address for replies.
+ **To   Address** - The mail address(es), comma separated, to send the reports to.

A list of available reports will be displayed. Select the reports to generate and then click on *Accept*.

Each report dialog will be displayed and at the end of the last report you will be prompted whether to actually *Print* or *Mail* the reports.

In the event of Financial Statements (gl3050), if there are available Report Streams, you will be asked if you want to apply a report stream.

Template Manager
................
Use this routine to create, edit or delete templates.

+ **Name** - The name of the template.
+ **Title** - The title of the template.
+ **TT** - The template type as follows:
    + **I** - Sales Document
    + **O** - Purchase Order
    + **P** - Payslip
    + **R** - Remittance Advice
    + **S** - Statement
+ **Sys** - The relevant system code relating to the type.
+ **ST** - This only applies to statements and is the type of statement as follows:
    + **N** - Normal
    + **O** - Other
+ **Size** - The page size i.e. A4, A5 or A6
+ **Orient** - The page orientation i.e. Portrait or Landscape.
+ **Sequence**
    + **Line Number** - The line number to edit or 0 for the next available number.
    + **Line Type** - The line type as follows:
        + **C Merge Code** - Use this code for lines that will be populated with data.
        + **I Image** - Use this code to display an image.
        + **L Line** - Use this code to draw a line.
        + **R Rectangle** - Use this code to draw a rectangle.
        + **T Text** - Use this code to print some fixed text.
    + **Placement** - Where to place this line.
+ **Rectangle**
    + **X1 Co-Ordinate** - The left hand position of the rectangle in mm.
    + **X2 Co-Ordinate** - The right hand position of the rectangle in mm.
    + **Y1 Co-Ordinate** - The top position of the rectangle in mm.
    + **Y2 Co-Ordinate** - The bottom position of the rectangle in mm.
    + **Line Thickness** - The thickness of the line.
+ **Image**
    + **X1 Co-Ordinate** - The left hand position of the image in mm.
    + **X2 Co-Ordinate** - The right hand position of the image in mm.
    + **Y1 Co-Ordinate** - The top position of the image in mm.
    + **Y2 Co-Ordinate** - The bottom position of the image in mm.
    + **File name** - The full path of the file name of the image.
    + **Merge Code** - The merge code containing the path to the image e.g. ctlmst ctm_logo.
+ **Line**
    + **Font Name** - The name of the font to use.
    + **Size** - The font size to use.
    + **Colour** - The line colour.
    + **Bold** - Whether to display the line in bold format.
    + **X1 Co-Ordinate** - The left hand position of the line in mm.
    + **Chrs** - The number of characters the line should extend.
    + **X2** - The right hand position of the line in mm.
    + **Y1 Co-Ordinate** - The top position of the line in mm.
    + **Y2 Co-Ordinate** - The bottom position of the line in mm.
    + **Line Thickness** - The thickness of the line.
+ **Text**
    + **Font Name** - The name of the font to use.
    + **Size** - The font size to use.
    + **Colour** - The text colour.
    + **Bold** - Whether to display the text in bold format.
    + **Italic** - Whether to display the text in italic format.
    + **Underline** - Whether to underline the text.
    + **Alignment** - How to align the text.
    + **Border** - Whether to draw borders around the text, TLRB.
    + **Fill Background** - Whether to fill the background of the text.
    + **X1 Co-Ordinate** - The left hand position of the text in mm.
    + **Chrs** - The number of characters the text should extend.
    + **X2** - The right hand position of the text in mm.
    + **Y1 Co-Ordinate** - The top position of the text in mm.
    + **Y2 Co-Ordinate** - The bottom position of the text in mm.
    + **Text Detail** - The text.
+ **Code**
    + **Text Type** - The text type. Heading, Label of a Column or No text.
    + **Text Detail** - The text.
    + **Font Name** - The name of the font to use.
    + **Size** - The font size to use.
    + **Colour** - The text colour.
    + **Bold** - Whether to display the text in bold format.
    + **Italic** - Whether to display the text in italic format.
    + **Underline** - Whether to underline the text.
    + **Alignment** - How to align the text.
    + **Border** - Whether to draw borders around the text, TLRB.
    + **Fill Background** - Whether to fill the background of the text.
    + **X1 Co-Ordinate** - The left hand position of the text in mm.
    + **Chrs** - The number of characters the text should extend.
    + **X2** - The right hand position of the text in mm.
    + **Y1 Co-Ordinate** - The top position of the text in mm.
    + **Y2** - The bottom position of the text in mm.
    + **Merge Code** - The code to use to import data.
    + **Font Name** - The name of the font to use for the imported data.
    + **Size** - The font size to use for the imported data.
    + **Colour** - The text colour.
    + **Bold** - Whether to display the imported data in bold format.
    + **Italic** - Whether to display the imported data in italic format.
    + **Underline** - Whether to underline the imported data.
    + **Alignment** - How to align the imported data.
    + **Border** - Whether to draw borders around the imported data, TLRB.
    + **Fill Background** - Whether to fill the background of the imported data.
    + **X1 Co-Ordinate** - The left hand position of the imported data in mm.
    + **Chrs** - The number of characters the imported data should extend.
    + **X2** - The right hand position of the imported data in mm.
    + **Y1 Co-Ordinate** - The top position of the imported data in mm.
    + **Y2 Co-Ordinate** - The bottom position of the imported data in mm.
    + **Number of Lines** - The number of lines the imported data can contain e.g. a name and address could be 5 lines.
    + **Repeats** - The number of times to repeat the imported data e.g. the number of lines in the body of a statement could be 30.

+ **Buttons**
    + **Import** - Use this button to import a template file.
    + **Copy** - Use this button to copy a template.
    + **Export** - Use this button to export a template to a file.
    + **Re-Sequence** - Use this button to re-sequence the line numbers of a template.
    + **Print** - Use this button to print the lines of the template.
    + **View PDF** - Use this button to get a preview of the document.
    + **Exit** - Use this button to save and exit the template maintenance routine.
    + **Quit** - Use this button to quit the template maintenance routine without saving it.
