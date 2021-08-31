# Copyright 2020-TODAY Anand Kansagra <anandkansagra@qdata.io>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Payroll Localization Colombia',
    'version': '12.0.1.0.0',
    'summary': 'Payroll Localization Colombia',
    'category': 'Human Resources',
    'author': 'Quadi',
    'license': 'AGPL-3',
    'maintainer': 'Quadi',
    'company': 'Quadi SAS',
    'website': 'https://quadi.co/',
    'depends': [
        'hr_payroll_income_withholding', 'hr_payroll_extended'
    ],
    'data': [
        'data/hr_salary_rule_category.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_value_uvt_rf_data.xml',
        'data/hr_value_uvt_range_rf_data.xml',
        'data/hr_value_uvt_input_not_rf_data.xml',
        'data/hr_value_uvt_input_rf_data.xml',
    ],
    'installable': True,
}
