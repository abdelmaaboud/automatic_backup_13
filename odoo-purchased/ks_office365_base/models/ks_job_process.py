from odoo import models, fields, api


class KsOfficeJob(models.Model):
    _name = "ks.office.job"
    _order = "id desc"
    _description = "Model to store record of number of records synced on each syncing"

    ks_records = fields.Integer(string="Records Processed", default=0)
    ks_status = fields.Selection([('in_process', 'In Process'), ('completed', 'Completed'), ('error', 'Error')],
                                 string="Status")
    ks_error_text = fields.Text("Error Message")
    ks_job = fields.Selection([('calendar_import', 'Office to Odoo'), ('calendar_export', 'Odoo to Office'),
                               ('contact_import', 'Office to Odoo'), ('contact_export', 'Odoo to Office'),
                               ('mail_import', 'Office to Odoo'), ('mail_export', 'Odoo to Office'),
                               ('task_import', 'Office to Odoo'), ('task_export', 'Odoo to Office')], string="Operation")
    ks_module = fields.Selection([('calendar', 'Calendar'), ('contact', 'Contact'), ('mail', 'Mail'), ('task', 'Task')],
                                 string="Module")

    def ks_complete_any_job(self):
        for job in self:
            job.write({'ks_status': 'completed'})
