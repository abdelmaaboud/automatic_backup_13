# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import append_content_to_html

import base64
import logging
_logger = logging.getLogger(__name__)


class IrActionsReport(models.AbstractModel):
    _inherit = 'ir.actions.report'
    
    @api.model
    def _run_wkhtmltopdf(self, bodies, header=None, footer=None, landscape=False, specific_paperformat_args=None, set_viewport_size=False):
        if 'force_portrait' in self.env.context:
            landscape = not self.env.context.get('force_portrait', False)
        return super(IrActionsReport, self)._run_wkhtmltopdf(bodies, header, footer, landscape, specific_paperformat_args, set_viewport_size)