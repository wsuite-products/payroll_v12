# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Res Partner Extended',
    'version': '12.0.1.0.0',
    'category': 'Base',
    'author': 'Destiny',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': ['crm_lead_extended', 'account'],
    'data': [
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
