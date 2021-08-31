# -*- coding: utf-8 -*-

{
    'name': 'HR Employee',
    'summary': 'HR Employee Customization',
    'version': '12.0.1.0.0',
    'category': 'Human Resources',
    'website': 'https://quadi.co/',
    'author': 'Quadi',
    # 'license': 'LGPL',
    'application': False,
    'installable': True,
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'depends': [
        'base_address_city',
        'hr_payroll_extended',
        'l10n_co',
    ],
    'data': [
        'views/hr_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_contract_batch_view.xml',
        'views/inherited_partner_view.xml',
        'views/inherited_company_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
    ],
}
