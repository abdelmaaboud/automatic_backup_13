# -*- coding: utf-8 -*-
from odoo import models, api

import logging

_logger = logging.getLogger(__name__)


class HrApplicationsDuplicateCheckWizard(models.TransientModel):
    _name = "hr_applications_duplicate_check_wizard"

    @api.multi
    def mass_check_duplicates(self):
        # Run this check on all applicants of the DB
        applicants = self.env['hr.applicant'].search([])
        for applicant in applicants:
            applicants._search_duplicates(applicant)
        # Return to the list of duplicates
        return self.env.ref('hr_recruitment_duplicates_manager.list_hr_application_duplicate_suspects_action').read()[0]
