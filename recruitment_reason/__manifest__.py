# -*- coding: utf-8 -*-
# Copyright 2019-TODAY Darshan Patel <darshanp@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Recruitment Reasons Quadi',
    'version': '12.0.1.0.0',
    'summary': 'Recruitment Reasons Customization for Quadi',
    'category': 'Human Resources',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
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
