# -*- encoding: utf-8 -*-

{
    'name': 'Stock move price',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': "http://www.pptssolutions.com",
    'category': 'Inventory',
    'description': """Tracking stock move price, created date and updated date""",
    'depends': ['base','stock'],
    'data': [
        'views/stock_move_price_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
