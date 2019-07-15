# -*- coding: utf-8 -*-

{
    'name': 'MRB BOM Component Find (Product Use Case)',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'mrp',
    'description': 'Know the case of multi-level use of a component from bom',
    'depends': ['base','mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mrp_bom_component_find_wizard.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application':True
}
