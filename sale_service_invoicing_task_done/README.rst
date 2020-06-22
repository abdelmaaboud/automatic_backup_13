=====================================
Sale Service Invoicing Task Done
=====================================

This module is an add-on to ``sale``.

This module adjusts sale line delivered quantity to only if sale order line product has 'Invoice Base on Closed Task' as invoice policy

Installation notes
==================

Steps
------

* First Go to Product and set Invoice Policy as 'Invoice Base on Closed Task' and set 'Create a task and track hours' in Track Service

* Create Sale order using Configured Product and Confirm it.

* Go to Tasks From Sale Order and Change State of Task as Done which has 'is a close stage' as True.

* On change of state of task, it will set delivered quantity as total effective hours of task.

* Invoice will be create based on the Closed Task.

Credits
=======

Contributors
------------

* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>
* Paul Ntabuye Butera

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS
