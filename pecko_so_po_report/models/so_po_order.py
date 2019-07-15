# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, SUPERUSER_ID, _

class Product(models.Model):   
    _inherit = "product.product"
     
    @api.multi
    def name_get(self):
        return [(template.id, '%s' % (template.default_code))
                for template in self]
        
    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
#         name = self.display_name
#         if self.description_sale:
#             name += '\n' + self.description_sale
        name = self.product_tmpl_id.x_studio_field_mHzKJ
        return name

class SaleOrder(models.Model):   
    _inherit = "sale.order"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No")
 
    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['attn'] = self.attn.id
        invoice_vals['customer_po_no'] = self.customer_po_no
        return invoice_vals
     
    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            for picking in rec.picking_ids:
                picking.write({'attn': self.attn.id,
                                      'customer_po_no' :self.customer_po_no})
        for loop in rec.picking_ids:
            for move in loop.move_ids_without_package:
                move.customer_part_no = move.product_id.name
        return res

class SaleOrderLine(models.Model):   
    _inherit = "sale.order.line"
    
    customer_part_no = fields.Text(string='Customer Part No')
    need_date = fields.Date(string="Need Date")
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.update({'customer_part_no':self.product_id.name,
                         'name':self.product_id.name})
            
class StockPicking(models.Model):   
    _inherit = "stock.picking"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No")   
    
    @api.model
    def create(self, vals):
        sale_id = self.env['sale.order'].search([('name','=',vals['origin'])])
        vals['customer_po_no'] = sale_id.customer_po_no
        return super(StockPicking, self).create(vals)
    
class StockMove(models.Model):   
    _inherit = "stock.move"
    
    customer_part_no = fields.Text(string='Part Number')
         
class AccountInvoice(models.Model):   
    _inherit = "account.invoice"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    customer_po_no = fields.Char(string="Customer PO No.")
    
class AccountInvoiceLine(models.Model):   
    _inherit = "account.invoice.line"
    
    customer_part_no = fields.Text(string='Customer Part No',compute="_compute_product_name")
    
    @api.depends('product_id')
    def _compute_product_name(self):
        for pro in self:
            if pro.product_id:
                pro.customer_part_no = pro.product_id.name
    
class PurchaseOrder(models.Model):   
    _inherit = "purchase.order"
    
    attn = fields.Many2one('res.partner',string="ATTN")
    
    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            rec.picking_ids.write({'attn': self.attn.id})
            
        for loop in rec.picking_ids.move_ids_without_package:
            loop.customer_part_no = loop.product_id.name
        return res

class PurchaseOrderLine(models.Model):   
    _inherit = "purchase.order.line"
    
    product_id = fields.Many2one('product.product', string='Pecko Part Number', domain=[('purchase_ok', '=', True)], change_default=True, required=True)
    customer_part_no = fields.Text(string='Part Number')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context(
            lang=self.partner_id.lang,
            partner_id=self.partner_id.id,
        )
#         self.name = product_lang.display_name
#         if product_lang.description_purchase:
#             self.name += '\n' + product_lang.description_purchase
        self.name = product_lang.x_studio_field_mHzKJ
        self.customer_part_no = self.product_id.name
        
        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

        self._suggest_quantity()
        self._onchange_quantity()

        return result

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].search([('id','=',vals['product_id'])])
        vals['customer_part_no'] = product_id.name
        return super(PurchaseOrderLine, self).create(vals)
    