from odoo import models, fields, api


class KsOfficeOdooLogs(models.Model):
    _name = "ks_office365.logs"
    _rec_name = 'ks_date'
    _order = "ks_date desc"
    _description = "Model to store log of every record being synced"

    ks_user = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
    ks_module_type = fields.Selection([("calendar", "Calendar"), ("contact", "Contact"), ("task", "Task"), ("mail", "Mail"),
                                       ("authentication", "Authentication")], string="Office365 Module")
    ks_record_name = fields.Char("Record Name")
    ks_odoo_id = fields.Char("Odoo Id")
    ks_office_id = fields.Char("Office Id")
    ks_date = fields.Datetime("Log Date")
    ks_operation = fields.Selection([("odoo_to_office", "Odoo to Office"), ("office_to_odoo", "Office to Odoo"),
                                     ("authentication", "Authentication")], string="Operation")
    ks_operation_type = fields.Selection([("create", "Create"), ("update", "Update"), ("delete", "Delete"),
                                          ("authentication", "Authentication")], string="Operation Type")
    ks_status = fields.Selection([("success", "Success"), ("failed", "Failed")], string="Status")
    ks_message = fields.Text("Message")
