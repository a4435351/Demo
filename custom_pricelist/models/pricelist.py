# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    description = fields.Char(string='Description')
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    
    @api.depends('product_tmpl_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_tmpl_id:
                prod_ids = self.env['product.product'].search([('product_tmpl_id','=',pro.product_tmpl_id.id)])
                pro.customer_part_no = prod_ids.name
                pro.description = prod_ids.default_code

    @api.onchange('product_tmpl_id')
    def onchange_purchase_line_product(self):
        if self.product_tmpl_id:
            prod_ids = self.env['product.product'].search([('product_tmpl_id','=',pro.product_tmpl_id.id)])
            self.manufacturer_id = prod_ids.manufacturer_id