==========================================
ABAKUS Project Task Integration
==========================================

This module is an  add-on to ``project``.

This modules adds some functionalities to the tasks for AbAKUS.

Functionalities:
    - Adds a fiel 'customer feedback' in Tasks
    - Moves the project field on the upper side.
    - Replaces priority stars selection by a normal name selection in the issue form.
    - Replaces priority stars in kanban view by the priority name.
    - Removes "Issues" menuitem from the project module.

    - Adds "My Issues" and "Unassigned Issues" menuitems in Project.

    - Adds 2 server actions:
        - Project issue email matching. It sets the project from an email issue
        - Project issue email matching + email to SM
    
    - Adds a boolean field on project task types (to know if the task need an assignated user), if the task type need an assignation, an error is shown

odoo 9 Updates:
    - New organisation of fields in issue
    - sale_subscription_id


Odoo 11 Improvements:

   - Adds a tracking on planned_hours field
   - Adds a boolean on stages. Tick if the task must be estimated to be in that stage

This module has been developed by ABAKUS IT-SOLUTIONS

Installation notes
==================

Credits
=======

Contributors
------------

* Valentin Thirion (vt@abakusitsolutions.eu)
* Bernard Delhez

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS

