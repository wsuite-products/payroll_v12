# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Kunjal Patel <kunjalpatel@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Mail Extended',
    'version': '12.0.1.0.0',
    'category': 'Mail',
    'author': 'Quadi',
    'description': """
        Disable Send Mail
    """,
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': ['base', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
