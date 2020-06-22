from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)

class product_supplier_reorderer(models.Model):
    _inherit = ['product.product']
    
    def _cron_supplier_reorderer(self):
        _logger.debug("Reorder supplier pricelists !")

        # get all products that are saleable
        product_obj = self.env['product.product']
        product_ids = product_obj.search([('sale_ok', '=', True)])

        for product in product_ids:

            # if more than one supplier, reorder them 
            if len(product.seller_ids) > 1:

                supplier_with_min_price = []

                for seller in product.seller_ids:
                    #_logger.debug("Min Q: %s | Price: %s", first_list.min_quantity, first_list.price)
                    # Add the info to the list
                    supplier_with_min_price.append({'partner_id': seller.name.id, 'min_price': seller.price, 'sequence': 0})
                        
                #_logger.debug("Prices: %s", supplier_with_min_price)
                supplier_with_min_price = sorted(supplier_with_min_price, key=lambda r:r['min_price'])
                sequence = 5
                for supp in supplier_with_min_price:
                    supp['sequence'] = sequence
                    sequence = sequence + 5
                #_logger.debug("Prices: %s", supplier_with_min_price)

                # set back the new sequences
                for seller in product.seller_ids:
                    seller_id = seller.name.id
                    if seller.price == None or seller.price == 0:
                        seller.sequence = 1000
                    else:
                        for p in supplier_with_min_price:
                            if p['partner_id'] == seller_id:
                                seller.sequence = p['sequence']
                                break

