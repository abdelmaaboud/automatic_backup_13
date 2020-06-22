from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = ['hr.expense']

    banner_text = fields.Html(string="Important Message", default=lambda self: self._get_default_banner())

    @api.model
    def _get_default_banner(self):
        return self.env['social.banner'].get_banner('expense')

    @api.multi
    def _compute_banner_text(self):
        for sheet in self:
           sheet.banner_text = self.env['social.banner'].get_banner('timesheet')
