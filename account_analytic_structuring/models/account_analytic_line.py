from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class account_analytic_account(models.Model):
    _inherit = ['account.analytic.line']

    move_journal_id = fields.Many2one('account.journal', string="Accounting journal linked to the move", related="move_id.journal_id", store=True)

    @api.multi
    @api.depends('move_id')
    def _computeMoveJournal(self):
        for line in self:
            if line.move_id:
                line.move_journal_id = line.move_id.journal_id
