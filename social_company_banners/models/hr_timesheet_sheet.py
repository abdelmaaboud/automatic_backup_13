from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class TimesheetSheet(models.Model):
    _inherit = ['hr_timesheet.sheet']

    banner_text = fields.Html(string="Important Message", compute="_compute_banner_text", default=lambda self: self._get_default_banner())

    @api.model
    def _get_default_banner(self):
        return self.env['social.banner'].get_banner('timesheet')

    @api.multi
    def _compute_banner_text(self):
        for sheet in self:
           sheet.banner_text = self.env['social.banner'].get_banner('timesheet')
