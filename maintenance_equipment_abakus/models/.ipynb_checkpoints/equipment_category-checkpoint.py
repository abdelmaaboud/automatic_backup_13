from odoo import api, models, fields, _
from odoo import tools

class EquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    name = fields.Char('Name', required=True, translate=True)
    code = fields.Char('Code', required=False, help='Code used to set automatically ref to assets in this category', size=3)

