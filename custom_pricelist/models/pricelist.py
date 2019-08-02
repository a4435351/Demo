# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    description = fields.Char(string='Description')
    pecko_part_no = fields.Char(string='Pecko Part No')
    customer_part_no = fields.Text(string='Part Number',compute="_compute_product_name",store=True)
    
    @api.depends('product_tmpl_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_tmpl_id:
                prod_ids = self.env['product.product'].search([('product_tmpl_id','=',pro.product_tmpl_id.id)])
                pro.customer_part_no = pro.product_tmpl_id.name
                pro.description = pro.product_tmpl_id.x_studio_field_mHzKJ

    @api.onchange('product_tmpl_id')
    def onchange_purchase_line_product(self):
        if self.product_tmpl_id:
            prod_ids = self.env['product.product'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
            self.manufacturer_id = prod_ids.manufacturer_id.id
            self.name = self.product_tmpl_id.default_code
            self.description = self.product_tmpl_id.x_studio_field_mHzKJ
            self.pecko_part_no = self.product_tmpl_id.default_code