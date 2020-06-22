from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class MaintenanceTask(models.Model):
    _name = 'maintenance.task'
    _description = 'Maintenance Task'

    name = fields.Char(string='Description', size=64, required=True, translate=True)
    category_id = fields.Many2one('maintenance.equipment.category', string='Equipment Category', ondelete='restrict', required=True)
    operations_description = fields.Text(string='Operations Description', translate=True)
    documentation_description = fields.Text(string='Documentation Description', translate=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment", track_visibility='always')
    comment = fields.Text()
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('delayed', 'Delayed'), ('done', 'Done'), ('cancel', 'Cancelled')], default='draft', string='State')
    request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
