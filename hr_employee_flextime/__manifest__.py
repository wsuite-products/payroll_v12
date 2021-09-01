# Copyright 2020-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Hr Employee Flextime',
    'version': '12.0.1.0.0',
    'summary': 'Hr Employee Flextime',
    'category': 'Human Resources',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_employee_flextime_data.xml',
        'views/hr_employee_flextime_view.xml',
        'views/inherited_hr_employee_view.xml',
    ],
    'installable': True,
}
