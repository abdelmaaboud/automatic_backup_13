from odoo import api, fields, models


class ProjectTaskMergeWizard(models.TransientModel):
    _inherit = 'project.task.merge.wizard'
    
    @api.multi
    def merge_tasks(self):
        res = super(ProjectTaskMergeWizard, self).merge_tasks()
        
        for task in self.task_ids:
            for timesheet in task.timesheet_ids:
                timesheet.write({'task_id': self.target_task_id.id})
        
        return res