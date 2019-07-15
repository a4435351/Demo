# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError

class PettyCashPaid(models.TransientModel):
    _name = 'account.petty.cash.paid'
    _description = 'Petty Cash Amount Paid'
    
    comments = fields.Char('Comments') 
                       
    @api.multi
    def Done(self):
        context = dict(self.env.context or {})
        act_id = context.get('act_id', False)
        cash_id = self.env['account.petty.cash'].search([('id', '=', act_id)])
        journal_line = []
        if not cash_id.employee_id.address_id:
            raise ValidationError(_('Employee Working Address is not configured.'))
        if not cash_id.employee_id.address_id.company_id.petty_cash_account_id:
            raise ValidationError(_('Employee Account is not configured.'))
        if cash_id:
            credit_bal = {
                'account_id': cash_id.employee_id.address_id.company_id.petty_cash_account_id.id,
                'partner_id': cash_id.employee_id.address_id.id,
                'name': cash_id.name,
                'debit': cash_id.amount,
                'credit': 0.00,
                'date_maturity': date.today(),
                'company_id': cash_id.employee_id.address_id.company_id.id,
                }
            journal_line.append((0, 0, credit_bal))
            debit_vals = {  
                    'account_id': cash_id.account_id.id,
                    'partner_id': cash_id.employee_id.address_id.id,
                    'name': cash_id.name,
                    'debit': 0.00,
                    'credit': cash_id.amount,
                    'date_maturity': date.today(),
                    'company_id': cash_id.employee_id.address_id.company_id.id,
                    }
            journal_line.append((0, 0, debit_vals))
            acc_move_id = self.env['account.move'].create({
                'date': cash_id.create_date,
                'journal_id': cash_id.payment_journal_id.id,
                'ref': cash_id.name,
                'line_ids': journal_line,
                'narration': self.comments
            })
            acc_move_id.post()
        return cash_id.write({'state': 'paid','account_move_id':acc_move_id.id})
    
