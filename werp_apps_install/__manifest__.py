# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Werp Apps Install',
    'version': '12.0.1.0.0',
    'summary': 'Werp Apps Install',
    'category': 'Administration',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'views/inherited_res_config_settings_view.xml',
    ],
    'installable': True,
    'application': True,
}
