# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'HR Contract Massive',
    'version': '12.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'author': 'Quadi',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
                'hr_contract_extended',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_contract_massive_data.xml',
        'views/hr_contract_massive_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
