from odoo import models, fields, api


class KsSyncDeletedRecords(models.Model):
    _name = "ks.deleted"
    _description = "Keeps records of office 365 deleted records in odoo databases"

    name = fields.Char()
    ks_odoo_id = fields.Char()
    ks_office_id = fields.Char()
    ks_module = fields.Selection([('calendar', 'Calendar'), ('contact', 'Contact'), ('mail', 'Mail'), ('task', 'Task')])
    ks_user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id)
