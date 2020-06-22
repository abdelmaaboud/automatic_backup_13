# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class project_task_assign_itself(models.Model):
    _inherit = ['project.task']

    @api.multi
    def assign_to_me(self):
        for task in self:
            task.user_id = self.env.user.id
