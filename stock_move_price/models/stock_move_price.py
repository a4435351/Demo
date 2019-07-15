# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date

# // Inherited Stock Move
class StockMove(models.Model):
    _inherit = "stock.move"
    
    create_date = fields.Date(string='Create Date', readonly=True)
    update_date = fields.Date(string='Update Date', readonly=True)
    cost_price = fields.Float("Cost Price(stock price)", readonly=True)
    cost_price_update = fields.Float("Cost Price Update", readonly=True)
    
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product_id = self.env['product.template'].browse(vals.get('product_id'))
            if product_id:
                vals['create_date'] = date.today()
                vals['cost_price'] = product_id.standard_price
        return super(StockMove, self).create(vals)
    
    @api.multi
    def write(self, vals):
        if vals.get('state')=='done':
            for val in self:
                if not val.update_date and val.product_id:
                    product_id = self.env['product.template'].browse(val.product_id.id)
                    if product_id:
                        val.update_date = date.today()
                        val.cost_price_update = product_id.standard_price
        return super(StockMove, self).write(vals)
    
    