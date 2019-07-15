# -*- coding: utf-8 -*-

from odoo import api, fields, models, _,tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import date
from odoo.exceptions import except_orm, Warning, RedirectWarning


class PettyCash(models.Model):

    _name = 'account.petty.cash'
    _inherit = ['mail.thread']
    _description = 'Petty Cash'
    
    @api.onchange('employee_id','payment_journal_id')
    def onchange_employee_id(self):
        res = {'domain': {'employee_id': "[('id', '!=', False)]",'payment_journal_id': "[('id', '!=', False)]"}}
        if self.employee_id:
            if self.employee_id.parent_id:
                self.approver_id = self.employee_id.parent_id.id
            else:
                raise UserError(_('Please select manager for employee.'))
        if self.payment_journal_id:
            if self.payment_journal_id.default_credit_account_id:
                self.account_id = self.payment_journal_id.default_credit_account_id.id
            else:
                raise UserError(_('Please select credit account for journal.'))
        all_employee_ids = []; journal_ids = []
        for all_employee in self.env['hr.employee'].search([('company_id','=',self.env.user.company_id.id)]):
            all_employee_ids.append(all_employee.id)
        res['domain']['employee_id'] = "[('id', 'in', %s)]" % all_employee_ids
        for journal in self.env['account.journal'].search([('company_id','=',self.env.user.company_id.id),('type', 'in', ('bank', 'cash'))]):
            journal_ids.append(journal.id)
        res['domain']['payment_journal_id'] = "[('id', 'in', %s)]" % journal_ids
        return res
          
    @api.depends('is_user')
    def _access_right(self):
        has_group = self.env.user.has_group('account.group_account_manager')
        if self.state == 'updated':
            if not has_group:
                self.is_user = True
                   
    name = fields.Char(string='Name', default='New', copy=False, track_visibility='always')
    create_date = fields.Date(string='Creation date', required=True, default=date.today(), track_visibility='always')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, track_visibility='always')
    created_user_id = fields.Many2one('res.users', string='Created User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, readonly=True)
    account_id = fields.Many2one('account.account', string='Account', track_visibility='always', readonly=True)
    from_date = fields.Date(string='From date', required=True, track_visibility='always')
    to_date = fields.Date(string='To date', required=True, track_visibility='always')
    amount = fields.Float(string='Petty Cash Amount', required=True, track_visibility='always')
    amount_setteld = fields.Float(string='Amount Setteld', compute='_compute_amount', currency_field='company_currency_id', store=True, readonly=True, track_visibility='always')
    company_currency_id = fields.Many2one('res.currency', related='employee_id.user_id.currency_id', readonly=True)
    approver_id = fields.Many2one('hr.employee', string='Approver', readonly=True, track_visibility='always')
    state = fields.Selection([('new', 'New'), ('send_approval', 'Send Approval'), ('approve', 'Approve'), ('paid', 'Paid'), ('in_progress', 'In progress'), ('updated', 'Updated'), ('done', 'Done')], default='new', track_visibility='always')
    expenses_ids = fields.One2many('petty.cash.expenses', 'expenses_id', string='Expenses', track_visibility='always')
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amount', currency_field='company_currency_id', store=True, readonly=True, track_visibility='always')
    to_pay = fields.Monetary(string='To pay', compute='_compute_amount', currency_field='company_currency_id', store=True, readonly=True, track_visibility='always')
    to_receive = fields.Monetary(string='To Receive', compute='_compute_amount', currency_field='company_currency_id', store=True, readonly=True, track_visibility='always')
    journal_entries_counts = fields.Integer(compute="_compute_journal_entries_counts", string='Journal Entries', copy=False, default=0)
    attached_doc_counts = fields.Integer(compute="_compute_attached_doc_counts", string='Attachments', copy=False, default=0)
    pettycash_journal_id = fields.Many2one('account.journal', string='Petty Cash Journal')
    payment_journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True)
    is_user = fields.Boolean("Is User", compute="_access_right")
    account_move_id = fields.Many2one('account.move', string='Journal', readonly=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.petty.cash') or _('New')
        res = super(PettyCash, self).create(vals)
        res.approver_id = res.employee_id.parent_id.id
        res.account_id = res.payment_journal_id.default_credit_account_id.id
        return res
    
    @api.multi
    def send_for_approval(self):  
#         if self.amount <= 0.00:
#             raise UserError(_('Please enter minimum of amount'))
#         else:
            return self.write({'state': 'send_approval'})
    
    @api.multi
    def approve_form(self):   
        return self.write({'state': 'approve'})
    
    @api.multi
    def pay_form(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({'act_id':self.id})
        return {
            'name': _('Payment Journal'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.petty.cash.paid',
            'context': context,
            'target': 'new'
        }   
    
    @api.multi
    def start_process(self):   
        return self.write({'state': 'in_progress'})
    
    @api.multi
    def updated_form(self):
        if not self.expenses_ids:
            raise ValidationError(_('Please create some expense details.'))
        return self.write({'state': 'updated'})   
    
    @api.multi
    def post_journal_entries(self):
        if not self.expenses_ids:
            raise ValidationError(_('Please create some expense details.'))
        if not self.employee_id.address_id.company_id.petty_cash_account_id:
            raise ValidationError(_('Employee Account is not configured.'))
        journal_line = [];journal_line_1 = [];journal_line_2 = []
        for line in self.expenses_ids:
            if line.expenses_category_id.account_id:
                credit_bal = {
                    'account_id': line.expenses_category_id.account_id.id,
                    'partner_id': self.employee_id.address_id.id,
                    'name': self.name,
                    'debit': line.exp_amount,
                    'credit': 0.00,
                    'date_maturity': date.today(),
                    'company_id': self.employee_id.address_id.company_id.id,
                    }
                journal_line.append((0, 0, credit_bal))
        debit_vals = {  
                'account_id': self.employee_id.address_id.company_id.petty_cash_account_id.id,
                'partner_id': self.employee_id.address_id.id,
                'name': self.name,
                'debit': 0.00,
                'credit': self.amount_total,
                'date_maturity': date.today(),
                'company_id': self.employee_id.address_id.company_id.id,
                }
        journal_line.append((0, 0, debit_vals))
        acc_move_id = self.env['account.move'].create({
            'date': self.create_date,
            'journal_id': self.pettycash_journal_id.id,
            'ref': self.name,
            'line_ids': journal_line
        })
        acc_move_id.post()
        if self.to_receive > 0:
            debit_vals_1 = {
                'account_id': self.employee_id.address_id.company_id.petty_cash_account_id.id,
                'partner_id': self.employee_id.address_id.id,
                'name': self.name,
                'debit': self.to_receive,
                'credit': 0.00,
                'date_maturity': date.today(),
                'company_id': self.employee_id.address_id.company_id.id,
                }
            journal_line_1.append((0, 0, debit_vals_1))
            credit_bal_1 = {  
                    'account_id': self.account_id.id,
                    'partner_id': self.employee_id.address_id.id,
                    'name': self.name,
                    'debit': 0.00,
                    'credit': self.to_receive,
                    'date_maturity': date.today(),
                    'company_id': self.employee_id.address_id.company_id.id,
                    }
            journal_line_1.append((0, 0, credit_bal_1))
            receive_acc_move_id = self.env['account.move'].create({
                'date': self.create_date,
                'journal_id': self.payment_journal_id.id,
                'ref': self.name,
                'line_ids': journal_line_1,
            })
            receive_acc_move_id.post()
        if self.to_pay > 0:
            credit_bal_2 = {
                'account_id': self.employee_id.address_id.company_id.petty_cash_account_id.id,
                'partner_id': self.employee_id.address_id.id,
                'name': self.name,
                'debit': 0.00,
                'credit': self.to_pay,
                'date_maturity': date.today(),
                'company_id': self.employee_id.address_id.company_id.id,
                }
            journal_line_2.append((0, 0, credit_bal_2))
            debit_vals_2 = {  
                    'account_id': self.account_id.id,
                    'partner_id': self.employee_id.address_id.id,
                    'name': self.name,
                    'debit': self.to_pay,
                    'credit': 0.00,
                    'date_maturity': date.today(),
                    'company_id': self.employee_id.address_id.company_id.id,
                    }
            journal_line_2.append((0, 0, debit_vals_2))
            pay_acc_move_id = self.env['account.move'].create({
                'date': self.create_date,
                'journal_id': self.payment_journal_id.id,
                'ref': self.name,
                'line_ids': journal_line_2,
            })
            pay_acc_move_id.post()
        if self.to_pay > 0:
            move_line_pay_id = self.env['account.move.line'].search([('move_id', '=', self.account_move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
            move_line_id = self.env['account.move.line'].search([('move_id', '=', acc_move_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
            self.trans_rec_reconcile(move_line_pay_id,move_line_id)
            to_pay_line_id = self.env['account.move.line'].search([('move_id', '=', pay_acc_move_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
            self.trans_rec_reconcile(move_line_pay_id,to_pay_line_id)
        if self.to_receive > 0:
            move_line_id = self.env['account.move.line'].search([('move_id', '=', acc_move_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
            move_line_pay_id = self.env['account.move.line'].search([('move_id', '=', self.account_move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
            self.trans_rec_reconcile(move_line_id,move_line_pay_id)
            to_recive_line_id = self.env['account.move.line'].search([('move_id', '=', receive_acc_move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
            self.trans_rec_reconcile(move_line_id,to_recive_line_id)
        return self.write({'state': 'done'})
    
    @api.multi
    def trans_rec_reconcile(self,line_to_reconcile,payment_line,writeoff_acc_id=False,writeoff_journal_id=False):
        return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)
    
    @api.depends('expenses_ids.exp_amount')
    def _compute_amount(self):
        amt_total = 0.00
        for line in self.expenses_ids:
            amt_total += line.exp_amount
#         if self.amount - amt_total < 0:
#             raise UserError(_('Please enter minimum of amount.'))    
        self.amount_total = amt_total
        self.amount_setteld = amt_total
        if self.amount > amt_total:
            self.to_pay = self.amount - amt_total
        if self.amount < amt_total:
            self.to_receive = amt_total - self.amount
     
    @api.multi
    def _compute_journal_entries_counts(self):
        journal_id = self.env['account.move'].search([('ref', '=', self.name)])
        if journal_id:
            self.journal_entries_counts = len(journal_id)
            
    @api.multi
    def _compute_attached_doc_counts(self):
        ir_id = self.env['ir.attachment'].search([('res_name', '=', self.name)])
        if ir_id:
            self.attached_doc_counts = len(ir_id)
            
    @api.multi
    def action_view_journal_entries(self):
        
        journal_id = self.env['account.move'].search([('ref', '=', self.name)]).ids
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if journal_id:
            action['domain'] = [('id', 'in', journal_id)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    @api.multi
    def action_view_attached_doc(self):
        
        ir_id = self.env['ir.attachment'].search([('res_name', '=', self.name)]).ids
        action = self.env.ref('base.action_attachment').read()[0]
        if ir_id:
            action['domain'] = [('id', 'in', ir_id)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

class ExpenseCategory(models.Model):
    _name = "expenses.category"
    _description = 'Expenses category'
    
    name = fields.Char("Name", required=True)
    account_id = fields.Many2one('account.account', string='Expense Account', required=True)
    
class PettyCashExpenses(models.Model):

    _name = 'petty.cash.expenses'
    _description = 'Petty Cash Expenses'
    
    date = fields.Date(string='Date', required=True)
    expenses_category_id = fields.Many2one('expenses.category', string='Expenses Category', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    exp_amount = fields.Float(string='Amount', required=True)
    ref_no = fields.Char(string='Ref No')
    remarks = fields.Char(string='Remarks')
    attachments = fields.Binary(string='Attachments')
    file_name = fields.Char(string='Filename')
    expenses_id = fields.Many2one('account.petty.cash', string='Expenses')
    
    @api.model
    def create(self, vals):
        res = super(PettyCashExpenses, self).create(vals)
        if res.attachments:
            res.env['ir.attachment'].create({
                    'name': res.file_name,
                    'res_model': 'account.petty.cash',
                    'res_name': res.expenses_id.name,
                    'res_id': res.expenses_id.id,
                    'datas': res.attachments,
                    'file_size': len(res.attachments.decode('base64'))
                    })
        return res
    
    @api.onchange('expenses_category_id')
    def _onchange_expenses_category_id(self):
        if self.expenses_category_id:
            cate_id = self.env['expenses.category'].search([('id', '=', self.expenses_category_id.id)])
            self.account_id = cate_id.account_id.id

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    petty_cash_account_id = fields.Many2one('account.account', readonly = False, related='company_id.petty_cash_account_id', string='Petty Cash Account')
 
class ResCompany(models.Model):
    _inherit = 'res.company'

    petty_cash_account_id = fields.Many2one('account.account', string='Petty Cash Account')
    
class PettyCashReport(models.Model):

    _name = 'petty.cash.report'
    _auto = False
    _description = 'Petty Cash Report'
    
    date = fields.Date(string='Date')
    expenses_category_id = fields.Many2one('expenses.category', string='Expenses Category',readonly=True)
    account_id = fields.Many2one('account.account', string='Account',readonly=True)
    exp_amount = fields.Float(string='Amount',readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    approver_id = fields.Many2one('res.users', string='Approver',readonly=True)
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW petty_cash_report as (
            select b.id,b.date,b.expenses_category_id,b.account_id,b.exp_amount,a.employee_id,a.approver_id
            FROM account_petty_cash a
            LEFT JOIN petty_cash_expenses b on b.expenses_id=a.id 
            )""")    
