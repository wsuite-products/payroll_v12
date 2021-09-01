# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'HR Contract Report',
    'version': '12.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'author': 'Destiny',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
                'hr_contract',
                'hr_recruitment',
    ],
    'data': [
        'views/contract_section_views.xml',
        'views/contract_format_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
