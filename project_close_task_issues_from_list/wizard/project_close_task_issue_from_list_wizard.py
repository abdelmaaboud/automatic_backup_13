from odoo import models
import logging
_logger = logging.getLogger(__name__)


class project_close_task_issue(models.Model):
    _name = "project.close.task.issue"
    _description = "Project Close Task and Issues Batch"

    def batch_close_tasks(self):
        if self.env.context is None:
            self = self.with_context({})
        active_ids = self.env.context.get('active_ids', []) or []
        task_ids = self.env['project.task'].browse(active_ids)
        for task in task_ids:
            for stage in task.project_id.type_ids:
                if stage.name == "Closed":
                    task.write({'stage_id': stage.id})
                    break
                if stage.close_stage and stage.name != "Cancelled":
                    task.write({'stage_id': stage.id})
                    break
        return {'type': 'ir.actions.act_window_close'}
