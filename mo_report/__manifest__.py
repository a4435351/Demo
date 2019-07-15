# -*- coding: utf-8 -*-

{
    'name': 'MO Report',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'MRP',
    'description': """Manufacture PDF Report""",
    'depends': ['stock','account_tax_code','custom_mrp'],
    'data': [
        'report/mo_report.xml',
        'report/mo_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
