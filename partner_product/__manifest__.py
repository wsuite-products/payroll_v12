# -*- coding: utf-8 -*-

{
    'name': 'Partner ERP Products needs',
    'summary': 'Add fields according to ERP Products needs',
    'version': '12.0.1.0.0',
    'category': 'Base',
    'website': 'https://quadi.co/',
    'author': 'Quadi',
    # 'license': 'LGPL',
    'application': False,
    'installable': True,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'depends': [
        'base',
    ],
    'data': [
        'views/res_partner_view.xml',
    ],
}
