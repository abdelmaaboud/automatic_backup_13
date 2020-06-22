=========================================
ABAKUS invoice improvements
=========================================

This module is an add-on to ``account``.

This modules adds some functionalities to the invoicing process for AbAKUS:
    - it adds a field in the invoice form with the next invoice number.
    - it auto copies the supplier ref number to the bank transfer communication field.
    - it checks if the supplier invoice number already exists.
    - it adds a group by in account.move.line that groups by journal entry.
    - it changes the fields order in the treeview of account.move.line.
    - it adds a filter that filters on customer account related move lines on lines.
    - it adds a filter that filters on supplier account related move lines on lines.
    - it checks if all the lines of the invoices contains exactly one tax.
    - it checks if the 'analytic account' field is set.
    - it moves the 'Accounting Date' field close to the 'Date' field.
    - it adds a warning when creating invoice from sale_order if warning is set on partner.

This module has been developed by Valentin THIRION @ AbAKUS it-solution.

Installation notes
==================

Credits
=======

Contributors
------------

* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>
* Francois Wyaime <francois.wyaime@abakusitsolutions.eu>

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS

