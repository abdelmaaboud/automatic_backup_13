from odoo import api, models, fields, exceptions, _
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    name = fields.Char(string='Number', required=False)
    origin = fields.Char(string='Source Document', size=64, readonly=True, help="Reference of the document that generated this maintenance order.")
    operations_description = fields.Text(string='Operations Description', translate=True)
    documentation_description = fields.Text(string='Documentation Description', translate=True)
    problem_description = fields.Text(string='Problem Description')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.user.company_id)
    level_id = fields.Many2one('maintenance.level', string="Level", required=True, track_visibility='always')
    task_ids = fields.One2many('maintenance.task', 'request_id', string='Tasks')
    equipment_ids = fields.Many2many('maintenance.equipment', 'request_equipment_rel', 'op_request_id', 'op_equipment_id', string='Equipments')
    customer_id = fields.Many2one('res.partner', string='Customer', track_visibility='always')
    subscription_id = fields.Many2one('sale.subscription', string='Subscription', track_visibility='always')
    analytic_account_id = fields.Many2one(string="Analytic Account", related='subscription_id.analytic_account_id', readonly=True)
    analytic_line_ids = fields.One2many('account.analytic.line', 'maintenance_request_id', string='Timesheets')
    #project_task_id = fields.Many2one('project.task', string="Request Task") # task used to log timesheets, TODO : manage this correctly
    is_security_check = fields.Boolean(related='level_id.is_security_check', string="Security Check")
    security_check_id = fields.Many2one('security.check', string="Security Check")

    @api.multi
    def prepare_maintenance_requets(self):
        for request in self:
            if request.stage_id.done:
                raise exceptions.UserError("Not possible to prepare as this request is already done.")

            if request.is_security_check and not request.security_check_id:
               request.security_check_id = self.env['security.check'].create({
                   'partner_id': request.customer_id.id,
                   'subscription_id': request.subscription_id.id,
                   'analytic_account_id': request.analytic_account_id.id,
                   'maintenance_request_id': request.id,
               })
               return True
            else:
                # Associate equipments
                request.equipment_ids = request.customer_id.equipment_ids
                for child in request.customer_id.child_ids:
                    request.equipment_ids = request.equipment_ids + child.equipment_ids

                # Texts
                request.operations_description = request.level_id.description

                # Create tasks (regarding partner, level and assets)
                request.task_ids = [(5, _, _)]
                for task_model in request.level_id.task_model_ids:
                    for equipment in request.equipment_ids.filtered(lambda r: r.category_id in task_model.category_ids):
                        task_id = self.env['maintenance.task'].create({
                            'request_id': request.id,
                            'name': task_model.name,
                            'category_id': equipment.category_id.id,
                            'equipment_id': equipment.id,
                            'operations_description': task_model.operations_description,
                            'documentation_description': task_model.documentation_description,
                            'state': 'draft'
                        })

    @api.multi
    def action_prepare_maintenance_request(self):
        self.prepare_maintenance_requets()

    @api.multi
    def action_set_to_done(self):
        for request in self:
            # Tasks
            for task in request.task_ids:
                if task.state not in ('done', 'cancel'):
                    raise exceptions.ValidationError(_('One or more tasks in this maintenance order are not marked as done (or cancel), please finish the maintenance before marking it as complete.'))

            # Request status
            stage_id = self.env['maintenance.stage'].search([('done', '=', True)], limit=1)
            if len(stage_id) > 0:
                request.stage_id = stage_id[0]
            request.close_date = datetime.today()

    @api.multi
    def action_set_to_draft(self):
        for request in self:
            if request.stage_id.done:
                raise exceptions.ValidationError(_('You can not reset to draft a Maintenance Order that is marked as done.'))
            stage_id = self.env['maintenance.stage'].search([('done', '=', False)], limit=1)
            request.stage_id = stage_id

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = self.env.ref('maintenance_equipment_abakus.sequence_maintenance_order').next_by_id() + " - " + vals['name']
        elif vals.get('name','/') == '/':
            vals['name'] = self.env.ref('maintenance_equipment_abakus.sequence_maintenance_order').next_by_id()
        return super(MaintenanceRequest, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s - %s (%s)" % (record.name, record.customer_id.name, record.level_id.name)))
        return result

    @api.multi
    def unlink(self):
        for order in self:
            if order.stage_id.done == True:
                raise exceptions.ValidationError(_('You can not delete a Maintenance Order that is Done or Ready.'))
        return super(MaintenanceRequest, self).unlink()
