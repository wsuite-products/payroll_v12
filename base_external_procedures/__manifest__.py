# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Base External Procedures',
    'version': '12.0.1.0.0',
    'summary': 'Base External Procedures',
    'category': 'Human Resources',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
        'hr_payroll_extended',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/res_external_procedures_view.xml",
        'views/hr_payroll_view.xml',
    ],
    'installable': True,
}
