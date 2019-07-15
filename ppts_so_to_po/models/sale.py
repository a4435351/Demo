# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
#     @api.multi
#     def action_confirm(self):
#         for order in self:
#             for line in self.order_line:
#                 if not line.vendor_id:
#                     raise UserError(
#                         _('Vendor is empty in one of the sale order line'))
#         return super(SaleOrder, self).action_confirm()
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    po_id = fields.Many2one('purchase.order', string='PO Reference', store=True, copy=False)
    vendor_ids = fields.Many2many('product.supplierinfo', 'sale_line_prod_suppliers_rel' ,string='Vendor', store=True, copy=True)        
    vendor_id = fields.Many2one('product.supplierinfo', string='Vendor', store=True, copy=True)
    
    @api.multi
    @api.onchange('product_id')
    def product_id_onchange(self):
        vals = {}
        if self.product_id.seller_ids:
            suppliers=[]
            count=1
            for line in self.product_id.seller_ids:
                suppliers.append(line.id)
                if count==1:
                    vals.update({'vendor_id': line.id})
                count=count+1
            vals.update({'vendor_ids': [(6, 0, suppliers)]})
        self.update(vals)
        
class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        cache = {}
        suppliers = product_id.seller_ids\
            .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (not r.product_id or r.product_id == product_id))
        if not suppliers:
            msg = _('There is no vendor associated to the product %s. Please define a vendor for this product.') % (product_id.display_name,)
            raise UserError(msg)   
        supplier = self._make_po_select_supplier(values, suppliers)
        
        # Changed Partner 
        stock_id = self.env['stock.move'].search([('id','=',values['move_dest_ids'].id)])
        partner = stock_id.sale_line_id.vendor_id.name
        
        # we put `supplier_info` in values for extensibility purposes
        values['supplier'] = supplier

        domain = self._make_po_get_domain(values, partner)
        if domain in cache:
            po = cache[domain]
        else:
            po = self.env['purchase.order'].sudo().search([dom for dom in domain])
            po = po[0] if po else False
            cache[domain] = po
        if not po:
            vals = self._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
            company_id = values.get('company_id') and values['company_id'].id or self.env.user.company_id.id
            po = self.env['purchase.order'].with_context(force_company=company_id).sudo().create(vals)
            cache[domain] = po
        elif not po.origin or origin not in po.origin.split(', '):
            if po.origin:
                if origin:
                    po.write({'origin': po.origin + ', ' + origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': origin})

        # Create Line
        po_line = False
        for line in po.order_line:
            if line.product_id == product_id and line.product_uom == product_id.uom_po_id:
                if line._merge_in_existing_line(product_id, product_qty, product_uom, location_id, name, origin, values):
                    vals = self._update_purchase_order_line(product_id, product_qty, product_uom, values, line, partner)
                    po_line = line.write(vals)
                    break
        if not po_line:
            vals = self._prepare_purchase_order_line(product_id, product_qty, product_uom, values, po, partner)
            self.env['purchase.order.line'].sudo().create(vals)
            
        # Sale order line 
        stock_id.sale_line_id.po_id = po.id
        