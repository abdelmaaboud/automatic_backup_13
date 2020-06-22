# -*- coding: utf-8 -*-
from odoo import http
import logging
#import cups
import base64
_logger = logging.getLogger(__name__)
import requests

class PrintController(http.Controller):
    @http.route('/barcode_scanner/report/move/label/<int:move_id>/<int:quantity>', methods=['POST', 'GET'], csrf=False, type='http', auth="public", website=True)
    def render_product_move_pdf(self, move_id, quantity=1 ,**kw):
        if move_id:
            move = http.request.env["stock.move"].sudo().search([ ('id', '=', move_id) ])
            if move:
                pdf = http.request.env.ref('barcode_scanner.abakus_move_single_label_internal_report').sudo().with_context(quantity=quantity).render_qweb_pdf([move.id])[0]
                if(move.picking_code == 'outgoing'):
                    pdf = http.request.env.ref('barcode_scanner.abakus_move_single_label_outgoing_report').sudo().with_context(quantity=quantity).render_qweb_pdf([move.id])[0]
                pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
                _logger.info("\n\nDownloaded")
                return http.request.make_response(pdf, headers=pdfhttpheaders)
    
    @http.route('/barcode_scanner/print/move/label/', auth="public", methods=['POST'], website=True, type="json")
    def print_product_move(self, move_id, quantity=1, **kw):
        if move_id:
            move = http.request.env["stock.move"].sudo().search([ ('id', '=', move_id) ])
            if move:
                pdf = http.request.env.ref('barcode_scanner.abakus_move_single_label_internal_report').sudo().with_context(quantity=quantity).render_qweb_pdf([move.id])[0]
                if(move.picking_code == 'outgoing'):
                    pdf = http.request.env.ref('barcode_scanner.abakus_move_single_label_outgoing_report').sudo().with_context(quantity=quantity).render_qweb_pdf([move.id])[0]
                attachment = http.request.env['ir.attachment'].sudo().create({'name': 'test', 'type': 'binary', 'res_id':move.id, 'res_model':'stock.move',
                'datas':base64.b64encode(pdf), 'mimetype': 'application/x-pdf', 'datas_fname':"" +(move.display_name)+".pdf" })
                file_path = attachment._full_path(attachment.store_fname)
                #conn = cups.Connection (host="212.166.27.34", port=631)
                try:
                    _logger.info("Printing")
                    url = 'https://abakus-printer.herokuapp.com/print'
                    myobj = base64.b64encode(pdf)

                    x = requests.post(url, data = myobj, headers={"content-type":"application/json;charset=UTF-8"})
                    #for i in range(quantity):
                    #    conn.printFile("zebra_gk420d", file_path, " ", {'fit-to-page':'True'})
                    #conn.printFiles("zebra_gk420d", 1, [base64.b64encode(pdf)], {'fit-to-page':'True'})
                finally:
                    attachment.unlink()
                return {
                    "result": {
                        
                    }
                }


    @http.route('/barcode_scanner/print/picking/delivery/<int:picking_id>', methods=['POST', 'GET'], csrf=False, type='http', auth="public", website=True)
    def render_delivery_slip(self, picking_id ,**kw):
        if picking_id:
            picking = http.request.env["stock.picking"].sudo().search([ ("id", "=", picking_id) ])
            if picking:
                pdf = http.request.env.ref('stock.action_report_picking').sudo().render_qweb_pdf([picking.id])[0]
                pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
                return http.request.make_response(pdf, headers=pdfhttpheaders)