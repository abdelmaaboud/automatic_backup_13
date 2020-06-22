from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

class EquipmentCreatorLinesFromSaleWizard(models.TransientModel):
    _name = 'maintenance.equipment.creator.from.sale.wizard.line'

    CRITICALITY_SELECTION = [
        ('0', 'General'),
        ('1', 'Important'),
        ('2', 'Very important'),
        ('3', 'Critical')
    ]

    wizard_id = fields.Many2one('maintenance.equipment.creator.from.sale.wizard', string='Wizard')
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale order line")
    sale_partner_id = fields.Many2one('res.partner')
    equipment_category_id = fields.Many2one('maintenance.equipment.category', string="Category")
    partner_id = fields.Many2one('res.partner', string="Partner")
    name = fields.Char(required=True)
    serial = fields.Char()
    asset_number = fields.Char()
    model = fields.Char()
    criticality = fields.Selection(CRITICALITY_SELECTION)

    """"@api.one
    @api.onchange('partner_id', 'asset_category_id')
    def _pre_fill_asset_number(self):
        code = ""
        # Partner code
        if self.partner_id:
            partner_code = self.partner_id.parent_id.ref if self.partner_id.parent_id else self.partner_id.ref
            if partner_code:
                code = partner_code
            else:
                code = self.partner_id.parent_id.name[0:3] if self.partner_id.parent_id else self.partner_id.name[0:3]
        # Category code
        if self.equipment_category_id:
            code = code + "-" + self.equipment_category_id.code
        # Asset number
        equipment_ids = self.partner_id.parent_id.asset_ids if self.partner_id.parent_id else self.partner_id.equipment_ids
        same_category_equipment_count = len(equipment_ids.filtered(lambda r: r.category_id == self.equipment_category_id))
        number = same_category_equipment_count + 1 # +1 here because the system doesn't know the current created assets

        if number < 10:
            code = code + "-00" + str(number)
        elif number < 100:
            code = code + "-0" + str(number)
        elif number < 1000:
            code = code + "-" + str(number)
        self.asset_number = code"""

    @api.multi
    @api.onchange('partner_id', 'equipment_category_id')
    def _pre_fill_asset_number(self):
        for line in self:
            code = ""
            # Partner code
            partner_code = line.partner_id.parent_id.ref if line.partner_id.parent_id else line.partner_id.ref
            if partner_code:
                code = partner_code
            else:
                code = line.partner_id.parent_id.name[0:3] if line.partner_id.parent_id else line.partner_id.name[0:3]
            # Category code
            if line.equipment_category_id:
                code = code + "-" + (line.equipment_category_id.code if line.equipment_category_id.code else '')
            # Asset number
            equipment_ids = line.partner_id.parent_id.equipment_ids if line.partner_id.parent_id else line.partner_id.equipment_ids
            same_category_asset_count = len(equipment_ids.filtered(lambda r: r.category_id == line.equipment_category_id))
            number = same_category_asset_count # No +1 here because the system already counts the one we are creating as member of the recordset

            if number < 10:
                if number == 0:
                    number = 1
                code = code + "-00" + str(number)
            elif number < 100:
                code = code + "-0" + str(number)
            elif number < 1000:
                code = code + "-" + str(number)

            line.asset_number = code

class EquipmentCreatorFromSaleWizard(models.TransientModel):
    """ Main wizard class """

    _name = 'maintenance.equipment.creator.from.sale.wizard'
    _description = 'Equipments Creator from Sale Wizard'

    sale_order_id = fields.Many2one('sale.order')
    line_ids = fields.One2many('maintenance.equipment.creator.from.sale.wizard.line', 'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields):
        """ Make sure we pre-fill the sale order with the proper value passed through context """
        res = super(EquipmentCreatorFromSaleWizard, self).default_get(fields)
        if self.env.context['default_sale_order_id'] and self.env.context.get('active_model') == 'sale.order':
            order = self.env['sale.order'].browse(self.env.context['default_sale_order_id'])

            res['sale_order_id'] = order.id
            lines = []

            # Create the lines for each qty of each line of product 'stockable', create a line
            for line in order.order_line:
                if (len(line.equipment_ids) < line.product_uom_qty) and (line.product_id.type == 'product'):
                    for qty in range(0, int(line.product_uom_qty)):
                        lines.append((0, 0, {
                            'sale_order_line_id': line.id,
                            'sale_partner_id': order.partner_id.id,
                            'partner_id': order.partner_id.id,
                            'name': line.product_id.name,
                            'model': line.product_id.default_code,
                        }))
            res.update({'line_ids': lines})
        return res

    @api.multi
    def _create_equipments(self):
        # Create an equipment for each lone
        equipments_created = []
        for line in self.line_ids:
            equipment_id = self.env['maintenance.equipment'].create({
                'name': line.name,
                'equipment_assign_to': 'customer',
                'customer_id': line.partner_id.id,
                'category_id': line.equipment_category_id.id,
                'serial': line.serial,
                'asset_number': line.asset_number,
                'model': line.model,
                'criticality': line.criticality,
                'sale_order_id': self.sale_order_id.id,
                'sale_order_line_id': line.sale_order_line_id.id,
                'purchase_date': line.sale_order_line_id.order_id.confirmation_date,
            })
            equipments_created.append(equipment_id.id)

            self.sale_order_id.equipments_created = True
        return equipments_created


    @api.multi
    def create_equipments(self):
        equipments_created = []
        for wizard in self:
            equipments_created += wizard._create_equipments()

        return {
            'name': _('Created Equiments'),
            'view_type': 'form',
            'view_mode': 'tree,kanban,form',
            'res_model': 'maintenance.equipment',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', equipments_created)],
            'context': {},
        }

