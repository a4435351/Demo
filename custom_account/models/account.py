# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    currency_conv_rate = fields.Float('Currency Conversation Rate', copy=False, readonly=True, help='It will show the currency conversation value against the invoice currency id.')
    company_currency_id = fields.Many2one('res.currency', 'Invoice Rate Currency', copy=False, related='company_id.currency_id', readonly=True)
    exchange_rate = fields.Float('Exchange Rate', digits=(12,6), copy=False, readonly=True, help='The specific rate that will be used, in this invoice, between the selected currency (in \'Invoice Rate Currency\' field)  and the Invoice currency.')
    currency_help_label = fields.Text(string="Helping Sentence", copy=False, readonly=True, help="This sentence helps you to know how to specify the invoice rate by giving you the direct effect it has")
     
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.company_id.currency_id != res.currency_id:
            if res.date_invoice:
                rate_id = self.env['res.currency.rate'].search([('name','=',res.date_invoice),('currency_id','=',res.currency_id.id)])
                res.exchange_rate = rate_id.rate
                res.currency_conv_rate = (1/rate_id.rate)
                val = round(res.exchange_rate,2)
                res.currency_help_label = 'At the operation date, the exchange rate was \n'+res.currency_id.symbol+'1.00 = '+res.company_id.currency_id.symbol+' '+str(val)
            else:
                rate_id = self.env['res.currency'].search([('id','=',res.currency_id.id)])
                res.exchange_rate = rate_id.rate
                res.currency_conv_rate = (1/rate_id.rate)
                val = round(res.exchange_rate,2)
                res.currency_help_label = 'At the operation date, the exchange rate was \n'+res.currency_id.symbol+'1.00 = '+res.company_id.currency_id.symbol+' '+str(val)
        else:
            res.exchange_rate = 0.00
            res.currency_conv_rate = 0.00
            res.currency_help_label = ''
        return res
    
    @api.multi
    def currency_values(self):
        if self.company_id.currency_id != self.currency_id:
            if self.date_invoice:
                rate_id = self.env['res.currency.rate'].search([('name','=',self.date_invoice),('currency_id','=',self.currency_id.id)])
                if rate_id:
                    self.exchange_rate = rate_id.rate
                    self.currency_conv_rate = (1/rate_id.rate)
                    val = round(self.exchange_rate,2)
                    self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)
                else:
                    rate_id = self.env['res.currency'].search([('id','=',self.currency_id.id)])
                    self.exchange_rate = rate_id.rate
                    self.currency_conv_rate = (1/rate_id.rate)
                    val = round(self.exchange_rate,2)
                    self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)
            else:
                rate_id = self.env['res.currency'].search([('id','=',self.currency_id.id)])
                self.exchange_rate = rate_id.rate
                self.currency_conv_rate = (1/rate_id.rate)
                val = round(self.exchange_rate,2)
                self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)
        else:
            self.exchange_rate = 0.00
            self.currency_conv_rate = 0.00
            self.currency_help_label = ''
            
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product_id = self.env['product.product'].search([('id','=',vals.get('product_id'))])
            vals['manufacturer_id'] = product_id.manufacturer_id.id
        return super(AccountInvoiceLine, self).create(vals)
        
    @api.onchange('product_id')
    def onchange_invoice_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
