# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class CurrencyRateUpdate(models.TransientModel):
    _name = 'stock.move.notes'
    _description = 'Stock move notes'
    
    def _action_additional_notes(self):
        context = dict(self.env.context or {})
        act_id = context.get('act_id', False)
        move_id = self.env['stock.move'].search([('id', '=', act_id)])
        return move_id.additional_notes
    
    additional_notes = fields.Char(string='Additional Notes', size=50, default=_action_additional_notes)
    
    @api.multi
    def done(self):
        context = dict(self.env.context or {})
        act_id = context.get('act_id', False)
        move_id = self.env['stock.move'].search([('id', '=', act_id)])
        move_id.write({
            'additional_notes': self.additional_notes
        })
        return {'type': 'ir.actions.act_window_close'}
    
