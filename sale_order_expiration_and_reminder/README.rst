
=====================================
   Sale order expiration and reminder
=====================================

This module is an add-on to ``sale``.

For Regular SO

* Adds a cron task to check the expired Sales Orders and send a summary to the salesmen.
* Adds a setting in the Sales Settings page
* Cancels SO if they have not been edited since the number of days specified.

For contract consultancy

* Adds an expiration date in sale order.
* Adds a selection for the expiration management.
* Adds a computed field of the number of days of the expiration date.
* Adds a cron task to remind the expiration < 30 days every monday.


Installation notes
==================

Credits
=======

Contributors
------------

* Jason Pindat
* Bernard Delhez
* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>
* Paul Ntabuye Butera

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS
