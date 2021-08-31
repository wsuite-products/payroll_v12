# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Webhook Automated Action',
    'version': '12.0.1.0.0',
    'category': 'Server Tools',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'base_automation',
        'hr_payroll_account',
        'hr_novelty',
        'hr_contract_extended'],
    'data': [
        'security/ir.model.access.csv',
        'views/webhook_view.xml',
        'views/webhook_history_view.xml',
        'views/object_confg_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
