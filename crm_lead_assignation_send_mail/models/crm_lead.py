# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def write(self, vals):

        if 'user_id' in vals:
            if vals['user_id'] != self.env.user.id:
                template = self.env.ref('crm_lead_assignation_send_mail.email_template_crm_lead_assignation')
                self.env['mail.template'].browse(template.id).send_mail(self.id)
       
        return super(Lead, self).write(vals)
