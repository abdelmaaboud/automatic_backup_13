from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    equipment_ids = fields.Many2many('maintenance.equipment', string="Related Equipments")
