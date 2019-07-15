# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

# import models
from odoo import api, models,fields


class AccountMove(models.Model):
    _inherit = "account.move"

    post_user = fields.Many2one('res.users')

    @api.multi
    def total_debit_credit(self):
        res = {}
        for move in self:
            dr_total = 0.00
            cr_total = 0.00
            partner_list = []
            for line in move.line_ids:
                dr_total += line.debit
                cr_total += line.credit
                if not line.partner_id.name in partner_list:
                    partner_list.append(line.partner_id.name)
            if move.currency_id.name == 'INR':
                self._cr.execute(''' SELECT f_amount_to_words('%s','%s') '''%(cr_total,move.company_id.id))
                rows = self._cr.dictfetchall()
                amount_in_word = rows[0]['f_amount_to_words']
                amount_in_word = amount_in_word.replace(',','')
            else:
                amount_in_word = move.currency_id.amount_to_text(cr_total)
                amount_in_word = str(amount_in_word) + ' only'
                amount_in_word = amount_in_word.replace(',','')
            partner = partner_list[0]
            res.update({'dr_total': dr_total, 'cr_total': cr_total, 'currency':move.currency_id.symbol,'amt_in_words':amount_in_word,'partner':partner})
        return res
    
    @api.multi
    def post(self, invoice=False):
        self.post_user = self.env.user.id
        return super(AccountMove, self).post()