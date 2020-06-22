============================================
   Additional infos in mail message notifications
============================================

This module adds methods in the 'mail.message' object that can be called from a mail template
to get informations like the partner's name from any object in Odoo (if the field exists).

To have it in the mail, you have to add a called for this method and HTML code to print it.
Example (added in the mail template for message discussion):
Customer name: ${object.get_partner_name()}

Installation notes
==================

Credits
=======

Contributors
------------

* Jason Pindat
* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS