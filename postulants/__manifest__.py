# Copyright 2019-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Postulants',
    'version': '12.0.1.0.0',
    'summary': 'Postulants',
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
        'hr_recruitment', 'hr_curriculum_vitae', 'contacts'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherited_res_partner_view.xml',
        'views/inherited_hr_applicant_view.xml',
        'views/hr_referred_channel.xml',
        'views/inherited_hr_job.xml',
        'views/inherited_hr_cv_employee_view.xml',
    ],
    'installable': True,
    'application': True,
}
