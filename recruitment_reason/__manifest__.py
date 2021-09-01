# -*- coding: utf-8 -*-
# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Recruitment Reasons Destiny',
    'version': '12.0.1.0.0',
    'summary': 'Recruitment Reasons Customization for Destiny',
    'category': 'Human Resources',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
               'hr_recruitment',
    ],
    'data': [
        'views/recruitment_reason_view.xml',
        'views/inherited_recruitment_reason_view.xml',
        'views/job_position_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
