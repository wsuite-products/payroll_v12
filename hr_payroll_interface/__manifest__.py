# Copyright 2019-TODAY WSuite Products <wsuite-products@destiny.ws>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'HR Payroll Interface',
    'version': '12.0.1.0.0',
    'summary': 'HR Payroll Interface',
    'category': 'Payroll',
    'author': 'Destiny',
    'license': 'AGPL-3',
    'maintainer': 'Destiny',
    'company': 'Destiny SAS',
    'website': 'https://destiny.ws/',
    'depends': [
        'hr_extended',
        'hr_payroll_income_withholding',
    ],
    'data': [
        'security/hr_payroll_interface_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_interface_data.xml',
        'data/mail_template_data.xml',
        'views/hr_type_interface_view.xml',
        'views/hr_payroll_interface_view.xml',
        'report/entity_of_pay_report.xml',
        'report/concepts_period_report.xml',
        'report/hr_payroll_interface_templates.xml',
        'wizard/interfaz_seguridad_social_wizard_view.xml',
    ],
    'installable': True,
    'external_dependencies': {'python': ['xlsxwriter']},
}
