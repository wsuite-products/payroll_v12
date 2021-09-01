# -*- coding: utf-8 -*-

{
    'name': 'Partner Neighborhood',
    'summary': 'Add a field to set the partner neighborhood in address block',
    'version': '12.0.1.0.0',
    'category': 'Base',
    'website': 'https://destiny.ws/',
    'author': 'Destiny',
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
