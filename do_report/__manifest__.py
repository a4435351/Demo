# -*- coding: utf-8 -*-

{
    'name': 'DO Report',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Inventory',
    'description': """Delivery Order PDF Report""",
    'depends': ['stock','account_tax_code'],
    'data': [
        'report/do_report.xml',
        'report/do_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
