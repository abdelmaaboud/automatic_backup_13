from odoo import _, models, fields, api
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = ['project.task']

    @api.multi
    def write(self, vals):
        for task in self:
            if 'stage_id' in vals and task.sale_line_id and task.sale_line_id.product_id.invoice_policy == 'task':
                # raise warning when user change in invoiced sale order line
                if task.sale_line_id.invoice_status == 'invoiced':
                    raise ValidationError(_("You can't modify task once it's related sale order line is invoiced."))
                # raise warning when sale order line is in done or cancel stage
                if task.sale_line_id.state in ['done', 'cancel']:
                    raise ValidationError(
                        _("You can't modify task once it's related sale order line is in done or cancel state."))
            res = super(ProjectTask, self).write(vals)
            if task.sale_line_id and task.sale_line_id.product_id.invoice_policy == 'task':
                # Onchange of stage_id if Task Stage is not is closed stage then it will set delivered qty as 0.00
                if task.stage_id and task.stage_id.closed:
                    task.sale_line_id.qty_delivered = task.sale_line_id.product_uom_qty
                else:
                    task.sale_line_id._compute_analytic()
            return res
