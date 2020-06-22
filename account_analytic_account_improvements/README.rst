=====================================
   ABAKUS Sale Contract Management
=====================================

This module is an add-on to ``sale_subscription``

It adds:
    - Team management for contracts, allows to create teams with users and link them to contracts
    - Type management for contracts (mandatory), allows to create types with a product, a price and link them to contracts
    - Minimum contractual amount in contract types, that is added to contracts also
    - BL invoicing: enable to invoice regarding the AbAKUS invoicing policy in BL Support contracts
    - New stages in contracts: negociation,open,pending,close,cancelled,refused
    - on_change_template refresh the new attributes: type, team, hourly rate
    - Invoicable factor on Timesheet in Tasks and Issues
    - "project auto create":
        - if you create a new contract then the default values come from the project of the contract template.
        - default values:
            - Project: team, stages, color, privacy_visibility, date_start, date and project_escalation_id.
        - followers:
            - project: none
            - task: Assigned to, Reviewer and task creator
            - issue: Assigned to, Contact and issue creator

    - Invoiceable field (model + view (task and issues) integration) (not exists in odooV9)
    - issue/task stage managment in project view
    - project color managment in projet view
    - first_subscription_id for account.analytic.account
    - sale_subscription_id for account.analytic.line
    - New model sale.subscription.shared that contains a common start and end date
    - Contracts types must contain a 'BL' in name in order to have some fields and groups shown in form
    - Adds a setting in the Accounting setting to specify some accounts for which move lines in them or their children have to contain an Analytic Account info
    - Contractual Factor : a field used to multiply the time by a factor
    - Adds a column for residual amount on the account.move.line list view

This module has been developed by ABAKUS IT-SOLUTIONS.

Installation notes
==================

Credits
=======

Contributors
------------

* Valentin Thirion <valentin.thirion@abakusitsolutions.eu>
* Bernard Delhez

Maintainer
-----------

.. image:: https://www.abakusitsolutions.eu/logos/abakus_logo_square_negatif.png
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS
