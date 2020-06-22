from odoo import models, fields, api

class IrActionsReport(models.Model):
    _inherit = ['ir.actions.report']
    
    preview = fields.Boolean(string="Preview")