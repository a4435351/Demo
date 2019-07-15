# -*- coding: utf-8 -*-

{
    'name': 'Sale Order to Purchase Order',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Sale,Purchase',
    'description': """Conformed Sale Order for creating a Purchase Order based on partner""",
    'depends': ['sale','purchase','product'],
    'data': [
        'views/sale_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
