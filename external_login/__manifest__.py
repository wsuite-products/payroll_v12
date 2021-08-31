# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Microsoft / W-admin Users - Odoo Integration Base Module',
    'version': '12.0.1.0.0',
    'category': 'Extra Tools',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': ['auth_oauth'],
    'data': [
        'views/res_config.xml',
        'views/oauth_provider.xml',
        'views/inherited_company_view.xml',
        'views/res_config_settings_views.xml',
        'data/auth_oauth_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
