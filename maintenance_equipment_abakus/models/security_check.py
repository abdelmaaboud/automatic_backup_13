# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class SecurityCheck(models.Model):
    _name = 'security.check'
    _inherit = ['mail.thread']
    _description = 'Security Check'
    _order = 'date_end DESC'

    name = fields.Char(string='Titre', index=True, required=True, track_visibility='always', compute='_compute_name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('waiting', 'Waiting validation'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], default='draft', required=True, track_visibility='always')
    date_end = fields.Date(string='Planned End Date', track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True, states={'draft': [('readonly', False)]})
    subscription_id = fields.Many2one('sale.subscription', string='Contract', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    analytic_account_id = fields.Many2one(string="Account", related='subscription_id.analytic_account_id', copy=True)
    maintenance_request_id = fields.Many2one('maintenance.request', string="Maintenance Request")

    external_access_ids = fields.One2many('security.check.external.access', 'check_id', string="External Accesses", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    external_access_attachment_ids = fields.Many2many('ir.attachment', 'ea_attachment_id', string='Signed Report')
    external_access_check_date = fields.Date(string='Check Date')
    external_access_free_text = fields.Text(string="Comments on External Access")

    backups_ids = fields.One2many('security.check.backup', 'check_id', string="Backups", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    backups_attachment_ids = fields.Many2many('ir.attachment', 'ba_attachment_id', string='Signed Report')
    backups_check_date = fields.Date(string='Check Date')
    backups_free_text = fields.Text(string="Comments on Backups", copy=True)

    access_rights_ids = fields.One2many('security.check.access.rights', 'check_id', string="Access Rights", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    access_rights_attachment_ids = fields.Many2many('ir.attachment', 'ar_attachment_id', string='Signed Report')
    access_rights_check_date = fields.Date(string='Check Date')
    access_rights_free_text = fields.Text(string="Comments on Access Rights", copy=True)

    gate_access_ids = fields.One2many('security.check.gate.access', 'check_id', string="Gate Accesses", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    gate_access_attachment_ids = fields.Many2many('ir.attachment', 'ga_attachment_id', string='Signed Report')
    gate_access_check_date = fields.Date(string='Check Date')
    gate_access_free_text = fields.Text(string="Comments on Gate Access", copy=True)

    server_security_ids = fields.One2many('security.check.server.security', 'check_id', string="Servers Security", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    server_security_attachment_ids = fields.Many2many('ir.attachment', 'ss_attachment_id', string='Signed Report')
    server_security_check_date = fields.Date(string='Check Date')
    server_security_free_text = fields.Text(string="Comments on Server Security", copy=True)

    network_security_ids = fields.One2many('security.check.network.security', 'check_id', string="Network Security", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    network_security_attachment_ids = fields.Many2many('ir.attachment', 'ns_attachment_id', string='Signed Report')
    network_security_check_date = fields.Date(string='Check Date')
    network_security_free_text = fields.Text(string="Comments on Network Security", copy=True)

    workstation_security_ids = fields.One2many('security.check.workstation.security', 'check_id', string="Workstations Security", readonly=True, states={'open': [('readonly', False)]}, copy=True)
    workstation_security_attachment_ids = fields.Many2many('ir.attachment', 'ws_attachment_id', string='Signed Report')
    workstation_security_check_date = fields.Date(string='Check Date')
    workstation_security_free_text = fields.Text(string="Comments on Workstation Security", copy=True)

    todo_ids = fields.One2many('security.check.todo', 'check_id', string="Todos", copy=True)
    todos_attachment_ids = fields.Many2many('ir.attachment', 'ws_attachment_id', string='Signed Report')
    todos_date = fields.Date(string='Date')
    todos_free_text = fields.Text(string="Comments on Todos", copy=True)

    @api.multi
    def action_confirm(self):
        self.state = 'open'

    @api.multi
    def action_done(self):
        self.state = 'waiting'

    @api.multi
    def action_validate(self):
        self.state = 'closed'

    @api.multi
    def action_refuse(self):
        self.state = 'open'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_redraft(self):
        self.state = 'draft'

    @api.multi
    def action_duplicate(self):
        for check in self:
            new_check_id = check.copy(default={'partner_id': check.partner_id.id, 'state': 'draft'})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'res_model': 'security.check',
                'view_mode': 'form',
                'res_id': new_check_id.id,
                'target': 'current',
            }

    @api.multi
    @api.depends('partner_id', 'date_end')
    def _compute_name(self):
        for check in self:
            check.name = "SC - %s - %s" % (check.partner_id.name, check.date_end)

    @api.multi
    def print_external_access(self):
        return self.env.ref('maintenance_equipment_abakus.report_external_access').report_action(self)

    @api.multi
    def print_backups(self):
        return self.env.ref('maintenance_equipment_abakus.report_backups').report_action(self)

    @api.multi
    def print_access_rights(self):
        return self.env.ref('maintenance_equipment_abakus.report_access_rights').report_action(self)

    @api.multi
    def print_gate_access(self):
        return self.env.ref('maintenance_equipment_abakus.report_gate_access').report_action(self)

    @api.multi
    def print_servers_security(self):
        return self.env.ref('maintenance_equipment_abakus.report_servers_security').report_action(self)

    @api.multi
    def print_network_security(self):
        return self.env.ref('maintenance_equipment_abakus.report_network_security').report_action(self)

    @api.multi
    def print_workstations_security(self):
        return self.env.ref('maintenance_equipment_abakus.report_workstations_security').report_action(self)

    @api.multi
    def import_gate_access_users(self):
        # is company set ?
        if not self.partner_id:
            return ValidationError(_("Please set a Customer first"))

        if len(self.gate_access_ids) > 0:
            return ValidationError(_("Please empty user list first"))

        # get all company contacts, filter by in_portal
        users = self.env['res.users'].search([
            '|',
            ('partner_id.parent_id', '=', self.partner_id.id),
            ('partner_id', '=', self.partner_id.id)
        ])

        for user in users:
            # look for associated user
            #user = self.env['res.users'].search([('partner_id', '=', partner.id)])
            self.gate_access_ids.create({
                'check_id': self.id,
                'username': user.partner_id.name,
                'sales_ku': user.partner_id.keyuser_sales,
                'accounting_ku': user.partner_id.keyuser_accounting,
                'project_ku': user.partner_id.keyuser_project,
                'date_last_connection': user.login_date or _('never connected'),
            })
        return

    @api.multi
    def print_todos_report(self):
        return self.env['report'].get_action(self, 'maintenance_service_security_check.report_todos_template')
    @api.multi
    def action_print_complete(self):
        return self.env['report'].get_action(self, 'maintenance_service_security_check.security_check_report_complete_template')

class AccessRights(models.Model):
    _name = 'security.check.access.rights'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    username = fields.Char(string='User Name', required=True)
    groups = fields.Char(required=True)
    shares = fields.Char(required=True)
    rights = fields.Char(required=True)

class Backup(models.Model):
    _name = 'security.check.backup'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    source = fields.Char(required=True)
    destination = fields.Char(required=True)
    frequency = fields.Char(required=True)
    date_last_successful_restore = fields.Date(string='Last Successful Restore', required=True)
    report_monitoring = fields.Char(required=True)
    type_id = fields.Many2one('backup.type', string="Type", required=True)

class ExternalAccess(models.Model):
    _name = 'security.check.external.access'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    partner_id = fields.Many2one('res.partner', string="User", required=True)
    on_premise_username = fields.Char(string='On Premise (AD) username') # related='partner_id.on_premise_username',
    connection_mode_ids = fields.Many2many('connection.mode', string="Connection Mode")
    comment = fields.Char()

class GateAccess(models.Model):
    _name = 'security.check.gate.access'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    username = fields.Char(string='User Name', required=True)
    sales_ku = fields.Boolean(string='Sales KU')
    accounting_ku = fields.Boolean(string='Accounting KU')
    project_ku = fields.Boolean(string='Project KU')
    date_last_connection = fields.Char(string='Last Connection', default="never connected")

class NetworkSecurity(models.Model):
    _name = 'security.check.network.security'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    firewall = fields.Char(required=True)
    firewall_licences_ok = fields.Boolean(string='Firewall Licenses OK')
    firewall_rules_ok = fields.Boolean(string='Firewall Rules OK')
    wlan = fields.Char(string='WLAN', required=True)
    complex_passwords = fields.Boolean()

class ServerSecurity(models.Model):
    _name = 'security.check.server.security'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    server = fields.Char(required=True)
    hardware_ok = fields.Boolean(string='Hardware OK')
    maintenance = fields.Boolean(string='Apps & OS Maintenance')
    shadow_copies = fields.Boolean(string='Shadow Copies Turned On')
    resources_ok = fields.Boolean(string='Resources OK')
    irmc_ok = fields.Boolean(string='IRMC OK')
    monitoring_probes = fields.Text(required=True)

class Todo(models.Model):
    _name = 'security.check.todo'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    name = fields.Char(required=True)
    description = fields.Text()
    project_id = fields.Many2one('project.project', string="Project")
    task_id = fields.Many2one('project.task', string="Task")
    task_state_id = fields.Many2one(related='task_id.stage_id', string="Task State")

class WorkstationSecurity(models.Model):
    _name = 'security.check.workstation.security'

    check_id = fields.Many2one('security.check', string='Security Check', required=True)
    workstation = fields.Char(required=True)
    description = fields.Text(string="Description")
    antivirus_ok = fields.Boolean(string='Antivirus OK')

class ConfigBackupType(models.Model):
    _name = 'backup.type'
    _order = 'name'

    name = fields.Char()
    active = fields.Boolean(default=True)
    description = fields.Char()

class ConfigConnectionMode(models.Model):
    _name = 'connection.mode'
    _order = 'name'

    name = fields.Char()
    active = fields.Boolean(default=True)
    description = fields.Char()
