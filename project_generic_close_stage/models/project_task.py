# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)
    
    
class ProjectTask(models.Model):
    _inherit = 'project.task'

    is_closed = fields.Boolean(related='stage_id.close_stage')

    @api.one
    def action_close(self):
        stage_id = self.env['project.task.type'].search([('close_stage', '=', True)])
        if not stage_id:
            raise exceptions.ValidationError(_('No stage has been set as the close stage. Unable to close task.'))

        self.write({'stage_id': stage_id[-1].id})
