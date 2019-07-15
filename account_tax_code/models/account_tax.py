# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    code = fields.Char(size=5)

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)',
         'The code of the Tax must be unique per company !')
    ]
