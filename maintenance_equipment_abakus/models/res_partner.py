from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    equipment_count = fields.Integer(compute='_compute_equipment_count', string='# Equipments')
    equipment_ids = fields.One2many('maintenance.equipment', 'customer_id', string="Equipments")
    #on_premise_username = fields.Char(string="On Premise (AD) username") # For Security Check

    def _compute_equipment_count(self):
        for partner in self:
            if partner.company_type == 'person':
                partner.equipment_count = len(partner.equipment_ids)
            else:
                count = 0
                for child in partner.child_ids:
                    count = count + len(child.equipment_ids)
                partner.equipment_count = len(partner.equipment_ids) + count
