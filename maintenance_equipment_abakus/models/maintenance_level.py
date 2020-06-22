from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class MaintelanceLevel(models.Model):
    _name = 'maintenance.level'
    _description = 'Maintenance Level'

    name = fields.Char(string='Description', size=64, required=True, translate=True)
    description = fields.Text(string='Description',translate=True)
    active = fields.Boolean(string='Active', default=True)
    task_model_ids = fields.Many2many('maintenance.task.model', string="Tasks")
    is_security_check = fields.Boolean(string="Is Security Check", default=False)
