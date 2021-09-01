# Copyright 2020-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Hr Employee Update',
    'version': '12.0.1.0.0',
    'summary': 'Hr Employee Update',
    'category': 'Administration',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
        'hr',
    ],
    'data': [
        "wizard/hr_employee_update_wizard_view.xml",
        "wizard/hr_employee_update_wizard_one_view.xml",
    ],
    'installable': True,
}
