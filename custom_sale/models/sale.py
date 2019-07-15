# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_untaxed = fields.Monetary(string='Untaxed Amount', digits=dp.get_precision('Product Price'), store=True, readonly=True, compute='_amount_all', track_visibility='onchange', track_sequence=5)
    amount_tax = fields.Monetary(string='Taxes', digits=dp.get_precision('Product Price'), store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', digits=dp.get_precision('Product Price'), store=True, readonly=True, compute='_amount_all', track_visibility='always', track_sequence=6)
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    price_subtotal = fields.Monetary(compute='_compute_amount', digits=dp.get_precision('Product Price'), string='Subtotal', readonly=True, store=True)
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    requested_date = fields.Date(string='Customer Requested Date')
    
    @api.onchange('product_id')
    def onchange_sale_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id