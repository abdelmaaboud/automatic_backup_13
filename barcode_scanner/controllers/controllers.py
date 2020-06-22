# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import Response
import logging
import json
_logger = logging.getLogger(__name__)

class BarcodeScanner(http.Controller):
    @http.route(['/barcode_scanner/', '/barcode_scanner/<path:route>'], auth='public')
    def index(self, **kw):
        return http.request.render('barcode_scanner.barcode_scanner_login_page')