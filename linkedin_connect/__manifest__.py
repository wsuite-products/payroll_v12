# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'LinkedIn Connect',
    'version': '12.0.1.0.0',
    'summary': 'LinkedIn Connect',
    'category': 'Human Resources',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'external_dependencies': {
        'python': ['mechanize', 'linkedin']
    },
    'depends': [
        'postulants',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/linkedin_data_configuration_views.xml',
        'views/inherited_hr_applicant_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
