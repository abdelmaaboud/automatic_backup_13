from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)


class MaintenanceTaskModel(models.Model):
    _name = 'maintenance.task.model'
    _description = 'Maintenance Task Model'

    name = fields.Char(string='Description', size=64, required=True, translate=True)
    category_ids = fields.Many2many('maintenance.equipment.category', string='Categories', ondelete='restrict', required=True)
    operations_description = fields.Text(string='Operations Description', translate=True)
    documentation_description = fields.Text(string='Documentation Description', translate=True)
    active = fields.Boolean(string='Active', default=True)
