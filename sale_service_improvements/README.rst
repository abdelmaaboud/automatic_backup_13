

=====================================
   Create task on SO improvements
=====================================

This module is an add-on to ``sale``.

* It adds the field initial planned hours to the products.
* When changing the product in an Order Line, it will take the planned hours from the product
* When confirming the order and creating the task, it will use this number of hour to set the planned time on the created tasks multiplied by the quantity
* It changes the name of the created task in: 'sale order line desc' - 'sale order reference/description' ('sale order name')
* It changes the project name to : 'partner name' - 'sale order reference/description'
* It adds the 'New', 'Open' and 'Closed' stages to the project
* It sets the stage 'New' for the created tasks

Installation notes
==================

Credits
=======

Contributors
------------

* Bernard Delhez
* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>
* Paul Ntabuye Butera

Maintainer
-----------

.. image:: http://www.abakusitsolutions.eu/wp-content/themes/abakus/images/logo.gif
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS
