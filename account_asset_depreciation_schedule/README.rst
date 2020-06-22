=====================================
  Depreciation Schedule Report
=====================================

This module is an add-on to ``account_reports`` that allows creating a Depreciation Schedule report.

This financial report is a legal document required by Belgium accounting law.

Installation notes
==================

Alter entreprise code in order to register the new report:

file: ``./models/account_report_context_common.py``

in class

update methodes:

* def _report_name_to_report_model(self):

   add::
    'depreciation_schedule': 'account.depreciation.schedule',

* def _report_name_to_report_model(self):

   add::
    'account.depreciation.schedule': 'account.context.depreciation.schedule',

Credits
=======

Contributors
------------

* Paul Ntabuye Butera

Maintainer
-----------

.. image:: http://www.abakusitsolutions.eu/wp-content/themes/abakus/images/logo.gif
   :alt: ABAKUS IT-SOLUTIONS
   :target: http://www.abakusitsolutions.eu

This module is maintained by ABAKUS IT-SOLUTIONS