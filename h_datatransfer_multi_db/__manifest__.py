# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Haresh Chavda <hareshchavda@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'H Datatransfer Multidb',
    'version': '12.0.1.0.0',
    'summary': 'H Datatransfer Multidb',
    'category': 'Human Resources',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co',
    'depends': [
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_transfer_employee_view.xml',
    ],
    'installable': True,
    'application': True,
}
