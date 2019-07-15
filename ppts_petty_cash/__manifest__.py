# -*- coding: utf-8 -*-

{
    "name": "Petty Cash",
    "version": "12.0",
    "category": "Accounting & Finance",
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'description': 'User based Petty cash application with approval process recording of transaction done by the user for company.',
    "depends": ['account', 'base', 'hr','account_accountant'],
    "data": [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/petty_cash.xml',        
        'views/petty_cash_view.xml',
        'wizard/petty_cash_wizard.xml'
    ],
    "installable": True,
    "active": True,
}