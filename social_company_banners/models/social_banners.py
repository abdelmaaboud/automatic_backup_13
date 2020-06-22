from odoo import models, fields, api
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)

class social_banner(models.Model):
    _name = 'social.banner'

    name = fields.Char(string="Title", required=True)
    text = fields.Html(string="Text")
    state = fields.Selection([('new', 'New'), ('confirm', 'Published'), ('done', 'Ended')], default='new', string="State")
    valid_from = fields.Date(string="Visible from")
    valid_to = fields.Date(string="Visible till")
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], name="Priority", default="medium", required=True)
    visible_on = fields.Selection([('all', 'All places'), ('timesheet', 'Timesheet form'), ('holiday', 'Holidays form'), ('expense', 'Expenses form')], default='all', string="Visible on", required=True)
    visible_for = fields.Selection([('all', 'All employees'), ('department', 'Specified Departments'), ('company', 'Specified Companies')], default='all', string="Visible for", required=True)
    department_ids = fields.Many2many('hr.department', string="Selected Departments")
    company_ids = fields.Many2many('res.company', string="Selected companies")
    read_by_ids = fields.One2many('social.banner.read', 'banner_id', string="Read by")
    banner_representation = fields.Html(compute='_compute_banner_representation')

    @api.multi
    def _compute_banner_representation(self):
        for banner in self:
            representation = ''
            if banner.priority == 'low':
                representation += "<h2 style='color: green;'>" + banner.name + "</h2>"
            if banner.priority == 'medium':
                representation += "<h2 style='color: orange;'>" + banner.name + "</h2>"
            if banner.priority == 'high':
                representation += "<h2 style='color: red; font-weight: bold;'>" + banner.name + "</h2>"
            representation += banner.text + '<br />'
            banner.banner_representation = representation

    @api.multi
    def action_confirm(self):
        for banner in self:
            banner.state = 'confirm'

    @api.multi
    def action_stop(self):
        for banner in self:
            banner.state = 'done'

    @api.multi
    def action_renew(self):
        for banner in self:
            banner.state = 'new'

    def get_banner(self, visible_on):
        # search for banners that are online
        banner_ids = self.env['social.banner'].search([('state', '=', 'confirm'), '|', ('visible_on', '=', 'all'), ('visible_on', '=', visible_on)])

        text = ""
        for banner in banner_ids:
            # search for banners that are set to be visible from
            if banner.valid_from:
                if datetime.strftime(datetime.now(), '%Y-%m-%d') < banner.valid_from:
                    continue
            # search for banners that are set to be visible to
            if banner.valid_to:
                if banner.valid_to < datetime.strftime(datetime.now(), '%Y-%m-%d'):
                    continue
            # search for banners that are visible for this employee (department / company)
            if banner.visible_for != 'all':
                # boolean selector
                concerned = False
                # get employee
                employee = None
                user = self.env['res.users'].browse(self.env.uid)
                if len(user.employee_ids) > 1:
                    employee = user.employee_ids[0]
                # by department
                if banner.visible_for == 'department':
                    for department in banner.department_ids:
                        if user.employee_ids[0] in department.member_ids:
                            concerned = True
                # by company
                if banner.visible_for == 'company':
                    for company in banner.company_ids:
                        if user.employee_ids[0].company_id == company:
                            concerned = True
                if not concerned:
                    continue

            text += banner.banner_representation

            # Create a red entry
            read = self.env['social.banner.read'].search([('banner_id', '=', banner.id), ('user_id', '=', self.env.uid)])
            if len(read) < 1:
                self.env['social.banner.read'].create({
                        'banner_id': banner.id,
                        'user_id': self.env.uid,
                        'date': datetime.now(),
                    }
                )
        return text
