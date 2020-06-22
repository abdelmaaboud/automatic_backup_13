from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _get_default_project_id(self):
        if 'default_account_id' in self.env.context:
            account_id = self.env['account.analytic.account'].search([('id', '=', self.env.context.get('default_account_id'))])
            if account_id and len(account_id.project_ids) > 0:
                return account_id.project_ids[0]
        return False

    equipment_ids = fields.Many2many('maintenance.equipment', related='task_id.equipment_ids', string="Related Equipments")
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    # Redefinition of the field
    project_id = fields.Many2one('project.project', 'Project', domain=[('allow_timesheets', '=', True)], default=lambda self: self._get_default_project_id())
    # TODO : timesheets here does not appear in the timehseet App, need for a "Project_id" for that.
    # => need a project_id on the sale_subscription => maintenance_request (probably linked to account_analytic_account_improvements)
