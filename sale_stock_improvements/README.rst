=====================================
   Sale Stock Improvements
=====================================

This module is an add-on to ``sale_stock``.

When a S.O. doesn't have a confirmation_date, it will use today as the datetime to get the planned_date.
It is used, for exemple, for freelance orders which create deliveries and they need a date (confirmation of the S.O.). 
And sometimes, there's no confirmation date which create an error. This module override this function.

Installation notes
==================

Credits
=======

Contributors
------------

* Arbi Ampukajev <arbi.ampukajev@abakusitsolutions.eu>

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS