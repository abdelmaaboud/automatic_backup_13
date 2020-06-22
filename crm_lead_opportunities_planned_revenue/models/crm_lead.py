from odoo import models, fields, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    planned_revenue_periodically = fields.Float(string="Expected periodical revenue")
    planned_revenue_period = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly')
    planned_revenue_yearly = fields.Float(string="Yearly periodical revenue", compute='_compute_revenue_yearly')
    planned_revenue_fixed = fields.Float(string="Planned FIXED revenue")
    panned_margin = fields.Float(string="Planned margin")

    @api.onchange('planned_revenue_periodically', 'planned_revenue_period')
    def _compute_revenue_yearly(self):
        for record in self:
            if (record.planned_revenue_period == 'daily'):
                record.planned_revenue_yearly = 20 * 12 * record.planned_revenue_periodically
            if (record.planned_revenue_period == 'monthly'):
                record.planned_revenue_yearly = 12 * record.planned_revenue_periodically
            if (record.planned_revenue_period == 'yearly'):
                record.planned_revenue_yearly = record.planned_revenue_periodically
            record.planned_revenue = record.planned_revenue_yearly + record.planned_revenue_fixed
    
    @api.onchange('planned_revenue_fixed')
    def _compute_revenue_total_first_year(self):
        self.planned_revenue = self.planned_revenue_fixed + self.planned_revenue_yearly
