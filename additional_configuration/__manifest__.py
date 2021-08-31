# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'You Additional Configuration',
    'summary': 'Access rights for you',
    'version': '12.0.1.0.0',
    'category': 'base',
    'website': 'https://quadi.co/',
    'author': 'Quadi',
    'application': False,
    'installable': True,
    'depends': [
        'hr',
        'hr_curriculum_vitae',
        'hr_contract_extended',
        'hr_contract_report',
        'hr_extended',
        'hr_recruitment'
    ],
    'data': [
        'security/additional_configuration_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/menu_view.xml',
    ],
}
