Salaries and Wages
------------------
File Maintenance (WG)
.....................
Control Record (WG)
+++++++++++++++++++
Use this routine to create and amend the control record.

+ **G/L Integration** - Whether or not to integrate with the general ledger.
+ **Salaries Control** - If integrated, enter the general ledger account number for the `Salaries Control` account.
+ **Staff Loans Control** - If integrated, enter the general ledger account number for the `Staff Loans Control` account.
+ **Staff Loans Interest** - If integrated, enter the general ledger account number for the `Staff Loans Interest` account.
+ **Registration Number** - Enter the SARS registration number.
+ **SDL Number** - Enter the SARS SDL registration number.
+ **UIF Number** - Enter the SARS UIF registration number.
+ **Trade Number** - Enter the SARS Trade registration number.
+ **Daily Hours** - Enter the normal daily hours worked e.g. 8
+ **Weekly Hours** - Enter the normal weekly hours worked e.g. 40
+ **Monthly Hours** - Enter the normal monthly hours worked e.g. 173.33
+ **Diplomatic Immunity** - Select if diplomatic immunity applies.
+ **S/L Interest Rate** - Enter the default interest rate on staff loans.
+ **Last Interest Date** - Enter the last date interest was raised.
+ **Best Account Code** - Enter the Standard bank Best Account Code.
+ **Best Account Type** - Enter the Standard bank Best Account Type.
+ **Payslip Template** - Enter the default template to use for payslips.
+ **Email Address** - The email address of the person in charge of salaries and wages, if not the default email address in the company record.

Receiver Codes (WG)
+++++++++++++++++++
Use this routine to create and amend the receiver of revenue irp5 codes.

Earning and Deduction Codes (WG)
++++++++++++++++++++++++++++++++
Use this routine to create and amend the earnings and deduction records.

**Detail-A**

+ **Type** - E for Earning and D for Deduction.
+ **Code** - The code's number. Certain earning codes are fixed i.e.
    + 1 for Normal Pay
    + 2-5 for Overtime Pay
+ **Description** - The code's description.
+ **Type** - The type of code:
    + **Variable** - If the code is a fixed rate for all employees
    + **Fixed** - If the code is different for each employee
+ **Employee Portion** - Amount if the portion is a monetary value or Rate if the portion is a rate.
    + **Base** - If you have indicated that the portion is a rate, you must now indicate the code of the base of the calculation, as follows:

        + **1** - X `times` Normal Rate of Pay `times` Value
        + **2** - Normal Pay `times` Value
        + **3** - Normal Pay `times` Value `divided` by 100
        + **4** - X `times` Daily Rate of Pay `times` Value
        + **5** - X `times` Hourly Rate of Pay `times` Value
        + **6** - U.I.F. Pay `times` Value
        + **Where:**
            + **X** refers to a data captured period e.g. hours or days.
            + **Value** refers to the 'Value' field below.
        + **Value** - The actual amount or rate to be used in the calculations.
        + **Limit** - The maximum amount allowed e.g. U.I.F. - 116.62.
        + **GL/Cono** - If integrated, the general ledger company number to be updated. This will take preference to the general ledger company number in the department record.
        + **GL/Acno** - If integrated, the general ledger account number to be updated. This will take preference to the general ledger account number in the department record.
+ **Earnings Type** - Salary if the earning is a salary amount or Commission if the earning is a commission amount.
+ **Employer Portion** - These are the same as for employee portion above.
+ **Tax Code** - Indicates whether the earning is taxable or not and if so what type of to apply as follows:
    + **Yes** - If the earning is taxable.
    + **No** - If the earning is not taxable
    + **Notional** - If the earning is only used in calculating the tax amount and is NOT in fact paid out as a salary
    + **One Time** - If the earning is a One time payment and must be annualised, e.g. an annual bonus
    + **Retrench** - If the earning is in respect of a retrenchment package.
+ **Tax Portion** - If taxable or tax deductible, the portion to be taxed.

**Detail-B**

+ **Rec Of Rev Code** - This is the code assigned by the receiver of revenue for this type of earning or deduction.
+ **Union Report** - Indicates whether the deduction must be included in a union report.
+ **Must Pay** - Indicates whether the deduction must be made irrespective of what the period earnings are.
+ **Balance Number** - This is used for a finite deduction e.g. If you want to deduct a total garnishee order of R1000 at a rate of R100 per month you would create a 'Garnishee' deduction record and enter a 1, 2 or 3 in this field. You would then edit the employee's record and under 'Balances' you would enter R1000 in the corresponding balance field. This deduction of R100 would then continue automatically until the full R1000 rand was deducted.
+ **Hourly Limit** - Indicates that a deduction is only applicable if the number of normal hours worked in a period, is less than or equal to the amount in this field.
+ **Monthly Deduction** - Indicates whether the deduction is to be deducted only once a month in the case of weekly or fortnightly paid employees.
+ **UIF Percentage** - What portion is liable for UIF e.g. 100
+ **SDL Percentage** - What portion is liable for SDL e.g. 100

Union Records (WG)
++++++++++++++++++
Use this routine to create and amend the salary's and wage's union records.

Payslip Messages (WG)
+++++++++++++++++++++
Use this routine to create and amend the payslip message records.

PAYE Tables (WG)
++++++++++++++++
Use this routine to maintain PAYE tax rates.

+ **Tax Year** - The applicable tax year.
+ **Rebate - Primary** - The primary rebate amount.
+ **Rebate - 65 and Older** - The 65-74 rebate amount.
+ **Rebate - 75 and Older** - The 75 and older rebate amount.
+ **Gratuity - Exemption** - The gratuity exemption amount.
+ **SITE Limit** - The SITE limit, if applicable.
+ **UIF Rates - Employee** - The employee's UIF rate.
+ **UIF Rates - Employer** - The employer's UIF rate.
+ **SDL Rates - Employee** - The employee's SDL rate.
+ **SDL Rates - Employer** - The employer's SDL rate.

The following columns refer to the basic tax rates:

+ **Inc-Fr** - The starting income bracket e.g. 0.
+ **Inc-To** - The ending income bracket e.g. 174550.
+ **Tax-Amt** - The initial tax amount for the Inc-Fr column e.g. 0.
+ **Rate** - The rate for the income up to the Inc-To column e.g. 18.00.

Employee Masterfile (WG)
++++++++++++++++++++++++
Use this routine to create, amend or delete employee masterfile records.

+ **Emp-Num** - The employee number.
+ **Department** - The department number.
+ **Class** - The class of employee.
+ **General**
    + **Surname**
    + **Names**
    + **Date of Birth**
    + **ID Number**
    + **Spouse Name**
    + **Spouse ID Number**
    + **Address Line 1**
    + **Address Line 2**
    + **Address Line 3**
    + **Postal Code**
    + **Telephone Number**
    + **E-Mail Address**
    + **Start Date**
    + **Salary/Rate**
    + **Pay Freq**
    + **Pay Type**
+ **Tax**
    + **P.A.Y.E.**
    + **Tax Office**
    + **Tax Number**
    + **Nature of Employee**
    + **Reg Number**
    + **Voluntary Excess**
    + **Fixed Rate**
    + **Directive**
+ **Bank**
    + **Account Type**
    + **Bank Name**
    + **Branch Code**
    + **Account Number**
    + **Account Holder's Name**
    + **Holder's Relationship**
+ **Earnings**
    + **Cod** - The code of the earning to be automatically raised.
    + **Amnt/Rate** - The value or rate of the earning to be raised.
+ **Deductions**
    + **Cod** - The code of the deduction to be automatically raised.
    + **Amnt/Rate** - The value or rate of the employee's portion of the deduction to be raised.
    + **Amnt/Rate** - The value or rate of the employer's portion of the deduction to be raised.
+ **Balances**
    + **Balance-1** - A balance to be deducted linked to the balance field in the deduction records.
    + **Balance-2** - A 2nd balance to be deducted linked to the balance field in the deduction records.
    + **Balance-3** - A 3rd balance to be deducted linked to the balance field in the deduction records.

Data Capture (WG)
.................
Clock Cards (WG)
++++++++++++++++
Use this routine to capture daily, weekly or monthly clock cards.

+ **EmpNo** - The employee's number.
+ **JobNo** - A job number if applicable.
+ **T** - The type of entry, either `E` for earning or `D` for deduction.
+ **Cde** - The earning or deduction code.
+ **P** - Whether or not to apply this earning or deduction.
+ **Amount** - The quantity or value of the earning or deduction.

Payslips (WG)
+++++++++++++
Use this routine to create weekly, fortnightly or monthly payslips.

+ **Template Name** - The template to be used for payslips.
+ **Pay-Run Date** - The actual pay-run date.
+ **Payment Date** - The date on which payment will be made.
+ **Message Code** - The message code to print on the payslips.
+ **Frequency** - The frequency, weekly, fortnightly or monthly, to process.
+ **Whole File** - The records to be processed. Either all records or individuals.
+ **Department** - The department, if applicable, to process.
+ **Ignore Standards** - Whether or not to ignore standard deductions.
+ **Include Monthly** - Whether or not to include once-off monthly deductions in the case of weekly paid employees.
+ **Exclude Minus Balances** - Whether or not to exclude payslips going into minus i.e. where the deductions exceed the earnings.
+ **Preview Only** - Whether or not to only preview the payslips i.e. the payslips will not be saved and the accounts will not be updated.

Terminations (WG)
+++++++++++++++++
Use this routine to capture employee terminations.

+ **Employee Number** - The employee's number.
+ **Termination Date** - The actual date of the termination.

Reporting (WG)
..............
Receiver Codes Listing (WG)
+++++++++++++++++++++++++++
Use this routine to print the receiver of revenue irp5 codes.

+ **Sort Order** - Select the print order of the codes.

Earning and Deduction Codes (WG)
++++++++++++++++++++++++++++++++
Use this routine to print earnings and deduction details.

+ **Report Type** - Select which codes to print.
+ **Sort Order** - Select the print order of the codes.

Union Records Listing (WG)
++++++++++++++++++++++++++
Use this routine to print a union report.

+ **Sort Order** - Select the print order of the records.

Payslip Messages Listing (WG)
+++++++++++++++++++++++++++++
Use this routine to print existing payslip messages.

Employee Master Listing (WG)
++++++++++++++++++++++++++++
Use this routine to print an employee master listing.

+ **Report Type** - Select the report format, either List or Card.
+ **Department Code** - The department, if applicable, to print.

Data Capture Listing (WG)
+++++++++++++++++++++++++
Use this routine to print clock cards captured.

+ **Reporting Date** - The date of the report.

SARS EMP201 Report (WG)
+++++++++++++++++++++++
Use this routine to print SARS EMP201 report.

+ **Start Date** - The starting pay-run date to use for the report.
+ **End Date** - The ending pay-run date to use for the report.

Earning and Deduction Values (WG)
+++++++++++++++++++++++++++++++++
Use this routine to list all earnings and deductions for pay-runs.

+ **Start Date** - The starting pay-run date to use for the report.
+ **End Date** - The ending pay-run date to use for the report.
+ **Type** - The type to print.
+ **Code per Page** - Select whether to print each code on a separate page.

IRP5 Statements (WG)
++++++++++++++++++++
Use this routine to print IRP5's and produce SARS import file.

+ **Submission Type** - Select the type of submission.
+ **Tax Year** - Enter the applicable tax year.
+ **Cut Off Date** - The last pay-run date to take into affect.
+ **Reprint** - Whether or not this is a reprint of a previous report.
+ **Preview** - Whether or not this is only a preview.
+ **Whole File** - Select the employees to process.
+ **Include Other Companies** - Whether or not to include other companies in the report.
+ **From Employee** - If range was selected above enter the first number of the range.
+ **To Employee** - If range was selected above enter the last number of the range.

Notes Listing (WG)
++++++++++++++++++
Use this routine to print notes.

+ **Action Flag** - Normal or Urgent.
+ **From Capture Date** - The starting creation date.
+ **To Capture Date** - The ending creation date.
+ **From Action Date** - The starting action date.
+ **To Action Date** - The ending action date.

Payslips Reprint (WG)
+++++++++++++++++++++
Use this routine to reprint payslips.

+ **Template Name** - The template to be used for payslips.
+ **Pay-Run Date** - The date of the pay-run to be reprinted.
+ **Frequency** - The frequency of the pay-run to be reprinted.
+ **Whole File** - The payslips to be printed. Either all payslips or individuals.
+ **Department** - The department, if applicable, to print.

Interrogation (WG)
..................
Use this routine to interrogate employee's details.
